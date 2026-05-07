from collections.abc import AsyncIterator
from dataclasses import dataclass, replace
from typing import Any

from app.config import settings
from app.context.examples import ESTIMATION_EXAMPLES

MAX_COMPLETION_TOKENS = 1200


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
        "ollama": ModelRoute(
            friendly_name="ollama",
            provider="ollama",
            model="ollama/gemma4:e2b",
            api_key=settings.ollama_api_key,
            base_url=settings.ollama_base_url,
            port=settings.ollama_port,
        ),
    }


def _build_system_prompt() -> str:
    examples_text = ""
    for i, example in enumerate(ESTIMATION_EXAMPLES, 1):
        examples_text += f"""
### Ejemplo {i}
**Resumen de reunión:**
{example['meeting_summary']}

**Estimación generada:**
{example['estimation']}
---
"""

    return f"""Eres un estimador de software experto con años de experiencia en proyectos de desarrollo web y mobile.

Tu tarea es analizar la transcripción de una reunión con un cliente y generar una estimación detallada del proyecto de software.

La estimación debe incluir:
- Desglose de tareas con horas estimadas para cada una
- Total de horas estimadas
- Equipo recomendado (roles y nivel de dedicación)
- Duración estimada del proyecto en semanas

A continuación tienes ejemplos de estimaciones previas que debes usar como referencia de estilo, formato y calibración:

{examples_text}

Usa estos ejemplos para calibrar la complejidad y granularidad de tus respuestas. Responde siempre en español y en formato Markdown."""


def get_system_prompt() -> str:
    return _build_system_prompt()


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
    if friendly_name:
        route = _model_routes().get(friendly_name)
        if route is None:
            available = ", ".join(get_available_friendly_names())
            raise ValueError(f"Unknown friendly_name '{friendly_name}'. Available: {available}")

        if model:
            return replace(route, model=model)
        return route

    resolved_provider = provider or settings.llm_provider
    resolved_model = model or settings.llm_model
    if resolved_provider == "ollama":
        resolved_model = resolved_model or "llama3.2"
        return ModelRoute(
            friendly_name="custom",
            provider="ollama",
            model=resolved_model if resolved_model.startswith("ollama/") else f"ollama/{resolved_model}",
            api_key=settings.ollama_api_key,
            base_url=settings.ollama_base_url,
            port=settings.ollama_port,
        )
    if resolved_provider == "anthropic":
        resolved_model = resolved_model or "claude-haiku-4-5-20251001"
        return ModelRoute(
            friendly_name="custom",
            provider="anthropic",
            model=(
                resolved_model
                if resolved_model.startswith("anthropic/")
                else f"anthropic/{resolved_model}"
            ),
            api_key=settings.anthropic_api_key,
            base_url=settings.anthropic_base_url or None,
            port=None,
        )
    resolved_model = resolved_model or "gpt-4o-mini"
    return ModelRoute(
        friendly_name="custom",
        provider="openai",
        model=resolved_model if resolved_model.startswith("openai/") else f"openai/{resolved_model}",
        api_key=settings.openai_api_key,
        base_url=settings.openai_base_url or None,
        port=None,
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


def _messages(system_prompt: str, transcription: str) -> list[dict[str, str]]:
    return [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": transcription},
    ]


def _chunk_delta_content(chunk) -> str | None:
    if not chunk.choices:
        return None

    delta = chunk.choices[0].delta
    if isinstance(delta, dict):
        return delta.get("content")
    return getattr(delta, "content", None)


async def get_estimation(
    transcription: str,
    friendly_name: str | None = None,
    provider: str | None = None,
    model: str | None = None,
) -> dict:
    system_prompt = _build_system_prompt()
    route = _resolve_route(friendly_name, provider, model)

    return await _call_litellm(system_prompt, transcription, route)


async def stream_estimation(
    transcription: str,
    friendly_name: str | None = None,
    provider: str | None = None,
    model: str | None = None,
) -> AsyncIterator[dict]:
    system_prompt = _build_system_prompt()
    route = _resolve_route(friendly_name, provider, model)

    async for event in _stream_litellm(system_prompt, transcription, route):
        yield event


async def _call_litellm(system_prompt: str, transcription: str, route: ModelRoute) -> dict:
    from litellm import acompletion

    response = await acompletion(
        **_litellm_kwargs(route),
        max_tokens=MAX_COMPLETION_TOKENS,
        messages=_messages(system_prompt, transcription),
    )
    return {
        "estimation": response.choices[0].message.content,
        "model": route.model,
        "provider": route.provider,
        "tokens_used": _tokens_used(response.usage),
    }


async def _stream_litellm(
    system_prompt: str,
    transcription: str,
    route: ModelRoute,
) -> AsyncIterator[dict]:
    from litellm import acompletion

    stream = await acompletion(
        **_litellm_kwargs(route),
        max_tokens=MAX_COMPLETION_TOKENS,
        messages=_messages(system_prompt, transcription),
        stream=True,
    )

    async for chunk in stream:
        delta = _chunk_delta_content(chunk)
        if delta:
            yield {"type": "delta", "content": delta}
        if chunk.usage:
            yield {
                "type": "metadata",
                "model": route.model,
                "provider": route.provider,
                "tokens_used": _tokens_used(chunk.usage),
            }
