from collections.abc import AsyncIterator
from dataclasses import dataclass, replace
import time
from typing import Any

from litellm import acompletion

from app.config import settings
from app.context.examples import ESTIMATION_EXAMPLES
from app.prompts.loader import render_estimation_prompt
from app.schemas import (
    DetailLevel,
    EstimationRequest,
    OutputFormat,
    ProjectType,
    RetrievalPromptContext,
    UserTier,
)
from app.services.retrieval_prompt_context_service import resolve_retrieval_prompt_context
from app.sessions import ExternalContextItem, ProjectMetadata

MAX_COMPLETION_TOKENS = 400
DEFAULT_PROMPT_VERSION = "v1"
MODEL_COSTS: dict[str, tuple[float, float]] = {
    "openai/gpt-4o-mini": (0.15, 0.60),
    "anthropic/claude-haiku-4-5-20251001": (0.80, 4.00),
    "ollama/gemma4:e2b": (0.0, 0.0),
}


@dataclass(frozen=True)
class ModelRoute:
    friendly_name: str
    provider: str
    model: str
    api_key: str
    base_url: str | None = None
    port: int | None = None


def _model_routes() -> dict[str, ModelRoute]:
    return {
        "openai": ModelRoute(
            friendly_name="openai",
            provider="openai",
            model="openai/gpt-4o-mini",
            api_key=settings.openai_api_key,
            base_url=settings.openai_base_url or None,
            port=None,
        ),
        "anthropic": ModelRoute(
            friendly_name="anthropic",
            provider="anthropic",
            model="anthropic/claude-haiku-4-5-20251001",
            api_key=settings.anthropic_api_key,
            base_url=settings.anthropic_base_url or None,
            port=None,
        ),
        "ollama": ModelRoute(
            friendly_name="ollama",
            provider="ollama",
            model="ollama/gemma4:e2b",
            api_key=settings.ollama_api_key,
            base_url=settings.ollama_base_url,
            port=settings.ollama_port,
        ),
    }


def _normalize_model_name(provider: str, model: str) -> str:
    return model if model.startswith(f"{provider}/") else f"{provider}/{model}"


def _default_prompt_request() -> EstimationRequest:
    return EstimationRequest(
        description=(
            "Aplicación web para equipos internos con autenticación, panel operativo, "
            "reporting y notificaciones por email para procesos diarios."
        ),
        project_type=ProjectType.INTERNAL_TOOL,
        detail_level=DetailLevel.MEDIUM,
        output_format=OutputFormat.NARRATIVE,
    )


def get_system_prompt(
    request: EstimationRequest | None = None,
    version: str = DEFAULT_PROMPT_VERSION,
    project_metadata: ProjectMetadata | None = None,
    external_context: list[ExternalContextItem] | None = None,
    user_tier: UserTier = UserTier.DEVELOPER,
    user_display_name: str | None = None,
) -> str:
    effective_request = request or _default_prompt_request()
    system, _user = render_estimation_prompt(
        effective_request,
        version=version,
        project_metadata=project_metadata,
        external_context=external_context,
        user_tier=user_tier,
        user_display_name=user_display_name,
    )
    return system


def get_context_summary() -> dict:
    return {
        "examples_count": len(ESTIMATION_EXAMPLES),
        "examples": [
            {
                "title": example["meeting_summary"],
                "transcription": example["meeting_summary"],
                "estimation": example["estimation"].strip(),
                "estimation_preview": example["estimation"].strip().splitlines()[0],
            }
            for example in ESTIMATION_EXAMPLES
        ],
    }


def get_available_friendly_names() -> list[str]:
    return list(_model_routes().keys())


def _resolve_route(
    friendly_name: str | None = None,
    provider: str | None = None,
    model: str | None = None,
) -> ModelRoute:
    routes = _model_routes()

    if friendly_name:
        route = routes.get(friendly_name)
        if route is None:
            available = ", ".join(get_available_friendly_names())
            raise ValueError(f"Unknown friendly_name '{friendly_name}'. Available: {available}")

        if model:
            return replace(route, model=_normalize_model_name(route.provider, model))
        return route

    resolved_provider = provider or settings.llm_provider
    route = routes.get(resolved_provider)
    if route is None:
        available = ", ".join(routes.keys())
        raise ValueError(f"Unknown provider '{resolved_provider}'. Available: {available}")

    resolved_model = model or settings.llm_model or route.model
    return replace(
        route,
        friendly_name="custom",
        model=_normalize_model_name(route.provider, resolved_model),
    )


def _tokens_used(usage) -> dict:
    if usage is None:
        return {"prompt": 0, "completion": 0, "total": 0}

    if isinstance(usage, dict):
        prompt = usage.get("prompt_tokens", 0) or 0
        completion = usage.get("completion_tokens", 0) or 0
        total = usage.get("total_tokens")
    else:
        prompt = getattr(usage, "prompt_tokens", 0) or 0
        completion = getattr(usage, "completion_tokens", 0) or 0
        total = getattr(usage, "total_tokens", None)
    return {
        "prompt": prompt,
        "completion": completion,
        "total": total if total is not None else prompt + completion,
    }


def _litellm_kwargs(route: ModelRoute) -> dict[str, Any]:
    kwargs: dict[str, Any] = {"model": route.model}
    if route.api_key:
        kwargs["api_key"] = route.api_key
    if route.base_url:
        kwargs["api_base"] = (
            route.base_url.removesuffix("/v1")
            if route.provider == "ollama"
            else route.base_url
        )
    return kwargs


def _estimate_cost_usd(model: str, tokens_used: dict) -> float:
    prompt_cost_per_million, completion_cost_per_million = MODEL_COSTS.get(model, (0.0, 0.0))
    prompt_cost = (tokens_used["prompt"] / 1_000_000) * prompt_cost_per_million
    completion_cost = (tokens_used["completion"] / 1_000_000) * completion_cost_per_million
    return round(prompt_cost + completion_cost, 8)


def _messages(system_prompt: str, user_prompt: str) -> list[dict[str, str]]:
    return [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt},
    ]


def _chunk_delta_content(chunk) -> str | None:
    if not chunk.choices:
        return None

    delta = chunk.choices[0].delta
    if isinstance(delta, dict):
        return delta.get("content")
    return getattr(delta, "content", None)


async def get_estimation(
    request: EstimationRequest,
    friendly_name: str | None = None,
    provider: str | None = None,
    model: str | None = None,
    prompt_version: str = DEFAULT_PROMPT_VERSION,
    history_messages: list[dict[str, str]] | None = None,
    project_metadata: ProjectMetadata | None = None,
    external_context: list[ExternalContextItem] | None = None,
    retrieval_context: RetrievalPromptContext | None = None,
    user_tier: UserTier = UserTier.DEVELOPER,
    user_display_name: str | None = None,
) -> dict:
    effective_retrieval_context = retrieval_context or await resolve_retrieval_prompt_context(request)
    system_prompt, user_prompt = render_estimation_prompt(
        request,
        version=prompt_version,
        project_metadata=project_metadata,
        external_context=external_context,
        retrieval_context=effective_retrieval_context,
        user_tier=user_tier,
        user_display_name=user_display_name,
    )
    route = _resolve_route(friendly_name, provider, model)
    return await _call_litellm(
        system_prompt,
        user_prompt,
        route,
        prompt_version,
        history_messages=history_messages,
    )


async def stream_estimation(
    request: EstimationRequest,
    friendly_name: str | None = None,
    provider: str | None = None,
    model: str | None = None,
    prompt_version: str = DEFAULT_PROMPT_VERSION,
    history_messages: list[dict[str, str]] | None = None,
    project_metadata: ProjectMetadata | None = None,
    external_context: list[ExternalContextItem] | None = None,
    retrieval_context: RetrievalPromptContext | None = None,
    user_tier: UserTier = UserTier.DEVELOPER,
    user_display_name: str | None = None,
) -> AsyncIterator[dict]:
    effective_retrieval_context = retrieval_context or await resolve_retrieval_prompt_context(request)
    system_prompt, user_prompt = render_estimation_prompt(
        request,
        version=prompt_version,
        project_metadata=project_metadata,
        external_context=external_context,
        retrieval_context=effective_retrieval_context,
        user_tier=user_tier,
        user_display_name=user_display_name,
    )
    route = _resolve_route(friendly_name, provider, model)
    async for event in _stream_litellm(
        system_prompt,
        user_prompt,
        route,
        prompt_version,
        history_messages=history_messages,
    ):
        yield event


async def _call_litellm(
    system_prompt: str,
    user_prompt: str,
    route: ModelRoute,
    prompt_version: str,
    history_messages: list[dict[str, str]] | None = None,
) -> dict:
    started_at = time.perf_counter()
    response = await acompletion(
        **_litellm_kwargs(route),
        max_tokens=MAX_COMPLETION_TOKENS,
        messages=[{"role": "system", "content": system_prompt}, *(history_messages or []), {"role": "user", "content": user_prompt}],
    )
    tokens_used = _tokens_used(response.usage)
    latency_ms = round((time.perf_counter() - started_at) * 1000, 2)
    return {
        "text": response.choices[0].message.content,
        "prompt_version": prompt_version,
        "model": route.model,
        "provider": route.provider,
        "tokens_used": tokens_used,
        "latency_ms": latency_ms,
        "cost_usd": _estimate_cost_usd(route.model, tokens_used),
    }


async def _stream_litellm(
    system_prompt: str,
    user_prompt: str,
    route: ModelRoute,
    prompt_version: str,
    history_messages: list[dict[str, str]] | None = None,
) -> AsyncIterator[dict]:
    stream = await acompletion(
        **_litellm_kwargs(route),
        max_tokens=MAX_COMPLETION_TOKENS,
        messages=[{"role": "system", "content": system_prompt}, *(history_messages or []), {"role": "user", "content": user_prompt}],
        stream=True,
    )

    async for chunk in stream:
        delta = _chunk_delta_content(chunk)
        if delta:
            yield {"type": "delta", "content": delta}
        if chunk.usage:
            yield {
                "type": "metadata",
                "prompt_version": prompt_version,
                "model": route.model,
                "provider": route.provider,
                "tokens_used": _tokens_used(chunk.usage),
            }
