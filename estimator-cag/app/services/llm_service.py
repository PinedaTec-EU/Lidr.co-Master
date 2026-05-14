from dataclasses import dataclass, replace
from typing import Any

from app.config import settings
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


def _messages(system_prompt: str, user_prompt: str) -> list[dict[str, str]]:
    return [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt},
    ]


class LiteLlmEstimationGateway:
    def __init__(
        self,
        friendly_name: str | None = None,
        provider: str | None = None,
        model: str | None = None,
    ) -> None:
        self._friendly_name = friendly_name
        self._provider = provider
        self._model = model

    async def generate(self, *, system_prompt: str, user_prompt: str) -> str:
        from litellm import acompletion

        route = _resolve_route(self._friendly_name, self._provider, self._model)
        response = await acompletion(
            **_litellm_kwargs(route),
            max_tokens=MAX_COMPLETION_TOKENS,
            messages=_messages(system_prompt, user_prompt),
        )
        return response.choices[0].message.content
