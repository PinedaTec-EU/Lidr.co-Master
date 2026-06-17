---
title: "✍️ Ejercicio - del chat a la interfaz de producto 🔴"
source_url: "https://training.lidr.co/posts/ai-engineering-202604-✍️-ejercicio-del-chat-a-la-interfaz-de-producto-🔴"
archived_at: "2026-06-12T09:22:36.851Z"
group: "04-session"
---

# ✍️ Ejercicio - del chat a la interfaz de producto 🔴

![Antonio Perez](./assets/c3eccac37426c36f.jpg)

[Antonio Perez](https://training.lidr.co/members/36030888)

Elestimatorque dejamos al final de la sesión 03 es funcional pero tiene dos problemas que nacen de la misma decisión: hemos dejado el prompting en manos del usuario y el prompt vive como un string dentro del código.

Antes del directo, vamos a corregir las dos cosas a la vez. Cuando llegues a la sesión, tuestimatorya no será un chat: el frontend habrá pasado a ser un formulario que produce parámetros tipados, y el servicio IA habrá sacado el prompt del código a templates Jinja2 versionados. Sobre esa base trabajaremos en directo el resto del temario de la sesión.

El ejercicio es deliberadamente exigente. Si te quedas en la mitad, llega a la sesión con lo que tengas: el directo arranca con un breve repaso de soluciones y a partir de ahí seguimos juntos. Pero quien acabe completo va a poder concentrarse en lo nuevo en lugar de hacer ingeniería estándar mientras se intenta seguir el directo.

## Punto de partida

Lo que tienes al final de la sesión 03:

- 

Servicio IA en FastAPI con un wrapper de proveedores que abstrae OpenAI y Anthropic.

- 

Cliente Streamlit con interfaz de chat conversacional (textarea + botón "Enviar").

- 

Caching exact-match, streaming y observabilidad básica con structlog.

- 

Prompt de estimación construido como f-string dentro del endpoint o del wrapper.

Si en sesión 03 elegiste un stack distinto a Streamlit para el cliente (te recordamos que frontend y backend de negocio son libres), traduce los pasos de cliente a tu stack: el patrón es idéntico, solo cambian las APIs.

## Objetivos de aprendizaje

Al terminar este ejercicio deberías poder defender en una conversación técnica:

- 

Por qué un formulario tipado produce mejor producto que un textarea libre cuando el espacio de tareas es acotado.

- 

Por qué un prompt en un archivo.j2con un loader es más mantenible que un f-string en el endpoint.

- 

Cómo se versiona un prompt y por qué la convenciónv1/,v2/no es opcional.

- 

Qué cubre un test de template y qué no.

## Tareas

### Parte 1 — Schemas y formulario en el cliente

Define el contrato entre cliente y servicio IA con Pydantic v2 en el servicio, y el formulario equivalente en el cliente.

En el servicio IA, enapp/schemas.py:

python
from enum import Enum from pydantic import BaseModel, Field class ProjectType(str, Enum): MOBILE_APP = "mobile_app" WEB_SAAS = "web_saas" INTERNAL_TOOL = "internal_tool" DATA_PIPELINE = "data_pipeline" class DetailLevel(str, Enum): SUMMARY = "summary" MEDIUM = "medium" DETAILED = "detailed" class OutputFormat(str, Enum): PHASES_TABLE = "phases_table" LINE_ITEMS = "line_items" NARRATIVE = "narrative" class EstimationRequest(BaseModel): description: str = Field(min_length=20, max_length=2000) project_type: ProjectType detail_level: DetailLevel output_format: OutputFormat class EstimationResponse(BaseModel): text: str prompt_version: str

En el cliente Streamlit, sustituye el chat por un formulario const.form. La idea es que el envío produzca unEstimationRequesty hagaPOST /estimateal servicio IA con ese JSON. La respuesta sigue siendo texto libre por ahora; la estructuraremos en el directo.

Si quieres tipar también en el cliente, puedes reutilizar la clase Pydantic; o definir el equivalente en tu stack si has elegido otro. No es obligatorio, pero ayuda.

### Parte 2 — Estructura de prompts y loader en el servicio IA

Crea la siguiente estructura dentro del servicio IA:
app/ ├── prompts/ │ ├── loader.py │ └── estimation/ │ └── v1/ │ ├── system.j2 │ ├── user.j2 │ └── examples.j2

Los tres.j2deben contener:

- 

system.j2: rol del modelo, instrucciones generales, bloque condicional segúnoutput_format(cómo formatear la salida), bloque condicional segúndetail_level(qué nivel de detalle dar). Incluyeexamples.j2con{% include %}.

- 

user.j2: el bloque que envuelve la descripción del proyecto del usuario.

- 

examples.j2: dos o tres ejemplos few-shot de estimaciones bien formadas. Inventa proyectos plausibles, no copies del enunciado.

Elloader.pydebe exponer una funciónrender_estimation_prompt(request, version="v1") -> tuple[str, str]que devuelve(system, user)listos para enviar al modelo. UsaEnvironmentde Jinja2 conStrictUndefined,trim_blocks=Trueylstrip_blocks=True. La firma debe permitir cambiar la versión sin tocar el resto del código.

Pista mínima sobre Jinja2 si no lo has usado:{{ var }}interpola,{% if %}...{% endif %}condiciona,{% include "ruta" %}inserta otro template. La sintaxis se aprende en cinco minutos en la[documentación oficial](https://jinja.palletsprojects.com/en/stable/templates/).

### Parte 3 — Refactor del endpoint

Cambia el endpointPOST /estimatepara que:

1. 

Acepte un body de tipoEstimationRequest.

1. 

Llame arender_estimation_prompt(request)para obtener(system, user).

1. 

Llame al modelo conrole: "system"yrole: "user"separados (no concatenados en un único mensaje).

1. 

Devuelva unEstimationResponsecon el texto yprompt_version="v1".

Mantén el wrapper de proveedor de la sesión 03. La llamada al LLM no debería cambiar más allá de pasar dos mensajes en lugar de uno.

Modelo por defecto sugerido:gpt-4o-minioclaude-haiku-4-5-20251001.

### Parte 4 — Test del template

Entests/prompts/test_estimation_v1.py(o donde tengas tu suite), añade al menos tres tests que verifiquen:

1. 

Que el render incluye literalmente el contenido dedescriptiondentro del bloque<project_description>(o## Project descriptionsi optas por Markdown).

1. 

Que cuandooutput_format=phases_tableel system contiene la palabra clave del formato (por ejemplo,"phases_table"o"confidence_pct"si lo mencionas en las instrucciones), y que cuando esnarrativeno la contiene.

1. 

Que cuandodetail_level=detailedel system incluye la instrucción extra de listar asunciones por fase, y que cuando essummaryesa instrucción no aparece.

Estos tests deben correr en milisegundos, sin tocar APIs externas. Son tests del template, no del modelo.

## Bonus opcional (si acabas pronto)

Para quien quiera ir más allá antes del directo, hay tres extensiones naturales que vamos a tocar igualmente, pero adelantarlas no estorba:

- 

**Versionado real:**crea unv2/al lado delv1/con una variación deliberada del prompt (por ejemplo, un tono distinto, o un set de ejemplos diferente) y haz que el endpoint acepte?prompt_version=v2como query param.

- 

**Contexto de proyectos similares:**añade al schema un campo opcionalreference_projects: list[ReferenceProject] | Noney haz que el template lo recorra con un{% for %}cuando esté presente.

- 

**Logging del prompt renderizado:**añade structlog al loader para que cada render emita un evento con la versión del prompt y un hash del contenido. Útil para depurar en producción.

## Si te atascas

- 

**Jinja2:**la[documentación oficial](https://jinja.palletsprojects.com/en/stable/templates/)cubre el 95% de lo que vas a usar (variables,if,for,include).

- 

**Streamlit forms:**st.formyst.form_submit_buttonson los dos componentes que necesitas.

- 

**Pydantic v2 con enums:**losEnumde Python se serializan automáticamente al string del valor cuando se hace.model_dump(). Si tu cliente no es Python, recuerda que el JSON enviado debe tener los strings exactos ("mobile_app", no"MOBILE_APP").

- 

StrictUndefined**:**se importa desdejinja2. Si te empieza a romper por una variable que sí pasas, revisa que no haya un typo entre el nombre en el template y el nombre en el contexto del render.

## Lo que no entra en este ejercicio

Tres temas que quedan reservados para el directo, no intentes adelantarlos:

- 

**Forzar JSON estructurado en la salida del LLM.**De momento la respuesta sigue siendo texto libre.

- 

**Validación del output con guardrails.**

- 

**Cacheo semántico de respuestas.**El cache exact-match de la sesión 03 sigue funcionando.

Estos tres temas requieren contexto y APIs que se introducen en directo. Si te lanzas a implementarlos por tu cuenta, no es un problema, pero ten en cuenta que la solución que veremos en clase puede diferir y tendrás que reconciliar.

## Entregable

- 

Una ramapre-session-04en tu repositorio con todos los cambios.

- 

README breve actualizando cómo se levanta y cómo se ejecutan los tests.

- 

Captura o GIF de la nueva interfaz funcionando (opcional, pero ayuda en la review en directo).

**Plazo de entrega.**Envía el enlace a tu rama a Lia con al menos dos días de antelación a la sesión en vivo. Las entregas posteriores no se podrán incluir en la revisión grupal del inicio del directo.
