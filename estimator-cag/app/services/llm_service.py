from dataclasses import dataclass, replace

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
            model="gpt-4o-mini",
            api_key=settings.openai_api_key,
            base_url=settings.openai_base_url or None,
            port=None,
        ),
        "ollama": ModelRoute(
            friendly_name="ollama",
            provider="ollama",
            model="gemma4:e2b",
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
        return ModelRoute(
            friendly_name="custom",
            provider="ollama",
            model=resolved_model or "llama3.2",
            api_key=settings.ollama_api_key,
            base_url=settings.ollama_base_url,
            port=settings.ollama_port,
        )
    if resolved_provider == "anthropic":
        return ModelRoute(
            friendly_name="custom",
            provider="anthropic",
            model=resolved_model or "claude-haiku-4-5-20251001",
            api_key=settings.anthropic_api_key,
            base_url=settings.anthropic_base_url or None,
            port=None,
        )
    return ModelRoute(
        friendly_name="custom",
        provider="openai",
        model=resolved_model or "gpt-4o-mini",
        api_key=settings.openai_api_key,
        base_url=settings.openai_base_url or None,
        port=None,
    )


def _tokens_used(usage) -> dict:
    if usage is None:
        return {"prompt": 0, "completion": 0, "total": 0}

    prompt = getattr(usage, "prompt_tokens", 0) or 0
    completion = getattr(usage, "completion_tokens", 0) or 0
    total = getattr(usage, "total_tokens", None)
    return {
        "prompt": prompt,
        "completion": completion,
        "total": total if total is not None else prompt + completion,
    }


async def get_estimation(
    transcription: str,
    friendly_name: str | None = None,
    provider: str | None = None,
    model: str | None = None,
) -> dict:
    system_prompt = _build_system_prompt()
    route = _resolve_route(friendly_name, provider, model)

    if route.provider == "anthropic":
        return await _call_anthropic(system_prompt, transcription, route)
    if route.provider == "ollama":
        return await _call_ollama(system_prompt, transcription, route)
    return await _call_openai(system_prompt, transcription, route)


async def _call_openai(system_prompt: str, transcription: str, route: ModelRoute) -> dict:
    from openai import AsyncOpenAI

    client_kwargs = {"api_key": route.api_key}
    if route.base_url:
        client_kwargs["base_url"] = route.base_url

    client = AsyncOpenAI(**client_kwargs)

    response = await client.chat.completions.create(
        model=route.model,
        max_tokens=MAX_COMPLETION_TOKENS,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": transcription},
        ],
    )
    return {
        "estimation": response.choices[0].message.content,
        "model": route.model,
        "provider": "openai",
        "tokens_used": _tokens_used(response.usage),
    }


async def _call_ollama(system_prompt: str, transcription: str, route: ModelRoute) -> dict:
    from openai import AsyncOpenAI

    client = AsyncOpenAI(base_url=route.base_url, api_key=route.api_key)

    response = await client.chat.completions.create(
        model=route.model,
        max_tokens=MAX_COMPLETION_TOKENS,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": transcription},
        ],
    )
    return {
        "estimation": response.choices[0].message.content,
        "model": route.model,
        "provider": "ollama",
        "tokens_used": _tokens_used(response.usage),
    }


async def _call_anthropic(system_prompt: str, transcription: str, route: ModelRoute) -> dict:
    import anthropic

    client_kwargs = {"api_key": route.api_key}
    if route.base_url:
        client_kwargs["base_url"] = route.base_url

    client = anthropic.AsyncAnthropic(**client_kwargs)

    response = await client.messages.create(
        model=route.model,
        max_tokens=2048,
        system=[{
            "type": "text",
            "text": system_prompt,
            "cache_control": {"type": "ephemeral"},
        }],
        messages=[
            {"role": "user", "content": transcription},
        ],
    )
    usage = response.usage
    return {
        "estimation": response.content[0].text,
        "model": route.model,
        "provider": "anthropic",
        "tokens_used": {
            "prompt": usage.input_tokens,
            "completion": usage.output_tokens,
            "total": usage.input_tokens + usage.output_tokens,
        },
    }
