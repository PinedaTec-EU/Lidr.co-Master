from app.config import settings
from app.context.examples import ESTIMATION_EXAMPLES


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


async def get_estimation(transcription: str) -> dict:
    system_prompt = _build_system_prompt()

    if settings.llm_provider == "anthropic":
        return await _call_anthropic(system_prompt, transcription)
    return await _call_openai(system_prompt, transcription)


async def _call_openai(system_prompt: str, transcription: str) -> dict:
    from openai import AsyncOpenAI

    client = AsyncOpenAI(api_key=settings.openai_api_key)
    model = settings.llm_model or "gpt-4o-mini"

    response = await client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": transcription},
        ],
    )
    usage = response.usage
    return {
        "estimation": response.choices[0].message.content,
        "model": model,
        "provider": "openai",
        "tokens_used": {
            "prompt": usage.prompt_tokens,
            "completion": usage.completion_tokens,
            "total": usage.total_tokens,
        },
    }


async def _call_anthropic(system_prompt: str, transcription: str) -> dict:
    import anthropic

    client = anthropic.AsyncAnthropic(api_key=settings.anthropic_api_key)
    model = settings.llm_model or "claude-haiku-4-5-20251001"

    response = await client.messages.create(
        model=model,
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
        "model": model,
        "provider": "anthropic",
        "tokens_used": {
            "prompt": usage.input_tokens,
            "completion": usage.output_tokens,
            "total": usage.input_tokens + usage.output_tokens,
        },
    }
