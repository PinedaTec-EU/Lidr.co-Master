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


async def get_estimation(transcript: str) -> str:
    system_prompt = _build_system_prompt()

    if settings.llm_provider == "anthropic":
        return await _call_anthropic(system_prompt, transcript)
    return await _call_openai(system_prompt, transcript)


async def _call_openai(system_prompt: str, transcript: str) -> str:
    from openai import AsyncOpenAI

    client = AsyncOpenAI(api_key=settings.openai_api_key)
    model = settings.llm_model or "gpt-4o-mini"

    response = await client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": transcript},
        ],
    )
    return response.choices[0].message.content


async def _call_anthropic(system_prompt: str, transcript: str) -> str:
    import anthropic

    client = anthropic.AsyncAnthropic(api_key=settings.anthropic_api_key)
    model = settings.llm_model or "claude-haiku-4-5-20251001"

    response = await client.messages.create(
        model=model,
        max_tokens=2048,
        system=system_prompt,
        messages=[
            {"role": "user", "content": transcript},
        ],
    )
    return response.content[0].text
