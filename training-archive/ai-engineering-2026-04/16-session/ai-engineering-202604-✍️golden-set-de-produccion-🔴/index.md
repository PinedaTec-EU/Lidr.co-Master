---
title: "✍️Golden set de producción 🔴"
source_url: "https://training.lidr.co/posts/ai-engineering-202604-%E2%9C%8D%EF%B8%8Fgolden-set-de-produccion-%F0%9F%94%B4"
archived_at: "2026-08-26T16:26:46.874Z"
group: "16-session"
---

# ✍️Golden set de producción 🔴

⏳Tiempo estimado: 5 min

🚨La fecha límite: martes 25 de agosto a las 23:59 de tu hora local

## 

## Contexto

Tras la Sesión 15, vuestro sistema de estimación está desplegado en producción: documentado, containerizado, con pipeline y con la frontera público/privado sobre redes reales. Está*vivo*—el smoke test lo confirma— pero ahora mismo opera a ciegas. No sabéis si estima con acierto, si empezó a alucinar tras el último cambio de prompt, ni cuánto os cuesta cada respuesta. El smoke test os dice que el sistema*responde*; no os dice si responde*bien*.

Este ejercicio pone al sistema bajo medición. Vais a construir tres cosas que son la base de todo lo que veremos en la sesión: un**conjunto de referencia**contra el que medir la calidad, un**arnés**que ejecute esa medición de forma automática, y un**dashboard**que muestre el estado del sistema en producción.

Recordatorio de la Sesión 15: en CI se mockea el modelo porque CI testea*vuestro código*. Este ejercicio es lo contrario:**evalúa el modelo**, así que sí llama al modelo de verdad. Por eso no corre en cada commit, sino de forma deliberada contra el sistema desplegado. Evaluar y testear son cosas distintas; aquí estáis en el lado de evaluar.

## Objetivo

Al terminar debéis tener:

1. 

Un**golden test set**con al menos 5 transcripciones de referencia, cada una con su estimación esperada.

1. 

Un**evaluation harness**que ejecute el set contra el servicio IA desplegado y produzca métricas.

1. 

Un**dashboard básico de monitorización**con las señales clave del sistema en producción.

## Requisitos previos

- 

El sistema de estimación desplegado en la Sesión 15 (staging o producción), o al menos levantado condocker compose.

- 

Acceso al servicio IA a través del backend de negocio, o directamente al endpoint/v1/estimatecon el token de servicio.

- 

Vuestra clave de LLM disponible: este ejercicio**consume tokens**, porque llama al modelo real. Es un gasto pequeño y deliberado; tenedlo en cuenta.

## Paso 1 — Construir el golden test set

Un golden test set es un conjunto de casos de referencia: entradas para las que vosotros —no el modelo— habéis decidido cuál es una buena respuesta. Es la vara de medir. Sin él, "el sistema estima bien" es una opinión; con él, es un número.

Cread un fichero versionado en el repositorio (ai-service/eval/golden_set.json) con**al menos 5 casos**. Cada caso lleva la entrada, la estimación esperada y un rango aceptable —porque una estimación no es una cifra exacta, sino un intervalo razonable—.

json
[ { "id": "case-001", "task_description": "Add OAuth2 login with Google and GitHub providers", "project_id": "proj-crm", "expected_points": 8, "acceptable_range": [5, 13], "expected_sources_include": ["task-142"], "notes": "Common auth task with clear historical precedents" }, { "id": "case-002", "task_description": "Migrate the reporting module from MySQL to PostgreSQL", "project_id": "proj-crm", "expected_points": 13, "acceptable_range": [8, 21], "expected_sources_include": [], "notes": "Data migration, medium-high effort" }, { "id": "case-003", "task_description": "Integrate with an in-house ERP that has no public documentation", "project_id": "proj-crm", "expected_points": null, "acceptable_range": null, "expect_abstention": true, "notes": "No historical precedent -> the system should abstain, not invent a number" } ]

Recomendaciones para que el set sea útil de verdad:

- 

**Cubrid dificultades distintas.**Un caso fácil y frecuente (hay precedentes claros), uno de esfuerzo medio-alto, y al menos uno**de borde**.

- 

**Incluid un caso de abstención.**Elcase-003del ejemplo no tiene precedente histórico: la respuesta correcta no es un número, es que el sistema reconozca que**no tiene datos suficientes**. Medir esto es medir la seguridad del sistema, no solo su acierto —y enlaza directamente con el bloque de safety de la sesión—.

- 

**Fijad los valores esperados con criterio, no a ojo.**Basadlos en los datos históricos reales que pobláis en la base de datos vectorial. El golden set es tan bueno como el criterio que hay detrás.

## Paso 2 — El evaluation harness

El harness es el programa que coge el golden set, lo lanza contra el servicio IA desplegado y compara cada respuesta con lo esperado. Va en el servicio IA (ai-service/eval/run_eval.py) y llama al sistema**real**, no a un mock.

python
# ai-service/eval/run_eval.py import json import time from pathlib import Path import httpx AI_SERVICE_URL = "<https://ai-service.internal>" # deployed AI service SERVICE_TOKEN = "..." # from the secret manager / env def load_golden_set(path: str) -> list[dict]: return json.loads(Path(path).read_text()) def call_estimate(case: dict) -> dict: started = time.perf_counter() response = httpx.post( f"{AI_SERVICE_URL}/v1/estimate", headers={"X-Service-Token": SERVICE_TOKEN}, json={ "task_description": case["task_description"], "project_id": case["project_id"], }, timeout=30, ) latency_ms = (time.perf_counter() - started) * 1000 return {"status": response.status_code, "body": response.json(), "latency_ms": latency_ms} def evaluate_case(case: dict, result: dict) -> dict: body = result["body"] # Abstention case: the system must recognise it has no data if case.get("expect_abstention"): abstained = body.get("estimate_points") is None or body.get("confidence", 1) < 0.3 return {"id": case["id"], "type": "abstention", "passed": abstained} # Estimation case: the estimate must fall within the acceptable range predicted = body.get("estimate_points") low, high = case["acceptable_range"] within_range = predicted is not None and low <= predicted <= high abs_error = abs(predicted - case["expected_points"]) if predicted is not None else None return { "id": case["id"], "type": "estimation", "passed": within_range, "predicted": predicted, "expected": case["expected_points"], "abs_error": abs_error, }

Fijaos en la lógica de la comparación: un caso de estimación pasa si el resultado cae**dentro del rango aceptable**, no si acierta la cifra exacta. Un caso de abstención pasa si el sistema**reconoce que no sabe**. Estáis codificando vuestra definición de "bueno".

## Paso 3 — Producir métricas

El harness no termina en pasa/falla por caso: agrega todo en un puñado de métricas que resumen el estado del sistema. Añadid la parte final que recorre el set y calcula el informe.

python
def run() -> dict: cases = load_golden_set("ai-service/eval/golden_set.json") evaluations = [] for case in cases: result = call_estimate(case) evaluation = evaluate_case(case, result) evaluation["latency_ms"] = result["latency_ms"] evaluations.append(evaluation) estimation_cases = [e for e in evaluations if e["type"] == "estimation"] within_range = [e for e in estimation_cases if e["passed"]] errors = [e["abs_error"] for e in estimation_cases if e["abs_error"] is not None] return { "within_range_rate": len(within_range) / len(estimation_cases), "mean_absolute_error": sum(errors) / len(errors) if errors else None, "abstention_correct": all(e["passed"] for e in evaluations if e["type"] == "abstention"), "mean_latency_ms": sum(e["latency_ms"] for e in evaluations) / len(evaluations), "cases": evaluations, } if __name__ == "__main__": report = run() print(json.dumps(report, indent=2))

Las métricas mínimas que debe devolver el informe:

- 

within_range_rate— fracción de estimaciones que caen en el rango aceptable. Es vuestra "tasa de acierto".

- 

mean_absolute_error— error medio en puntos frente a lo esperado. Dice*cuánto*falla, no solo*si*falla.

- 

abstention_correct— si el sistema abstuvo correctamente en los casos sin datos. Es una señal de seguridad.

- 

mean_latency_ms— latencia media por petición.

Guardad la salida de cada ejecución (por ejemplo enai-service/eval/reports/): esa serie de informes es lo que os permitirá, en la sesión, detectar si un cambio ha degradado la calidad.

## Paso 4 — Dashboard básico de monitorización

El golden set mide la calidad*cuando vosotros lanzáis la evaluación*. El dashboard mide lo que pasa*en producción, todo el rato*. Son complementarios: uno es la prueba de laboratorio, el otro es el monitor de constantes vitales.

Para que haya algo que mostrar, primero hay que**emitir las señales**. Instrumentad el servicio IA para que, en cada petición de estimación, registre las métricas clave:

python
# ai-service/app/observability.py (sketch) import logging logger = logging.getLogger("ai-service.metrics") def record_request_metrics(request_id: str, latency_ms: float, prompt_tokens: int, completion_tokens: int, status: str) -> None: # Cost is derived from token counts and the provider's price per token estimated_cost = estimate_cost(prompt_tokens, completion_tokens) logger.info( "estimate_request", extra={ "request_id": request_id, "latency_ms": latency_ms, "prompt_tokens": prompt_tokens, "completion_tokens": completion_tokens, "estimated_cost": estimated_cost, "status": status, }, )

Con esas señales saliendo del servicio IA, montad un**dashboard básico**que muestre, como mínimo:

- 

**Latencia**por petición (media y p95).

- 

**Coste por petición**(derivado del recuento de tokens).

- 

**Tasa de error**(proporción de respuestas no200).

Para la herramienta, el camino más corto es reutilizar lo que ya visteis en la Sesión 13 (**Logfire**o**Langsmith**), que ingieren estas trazas y os dan los paneles casi hechos. Si preferís algo autocontenido, vale un panel mínimo que lea los logs estructurados y pinte las tres señales. Lo importante del ejercicio no es la herramienta: es tener claro**qué**se vigila y por qué.

Ojo con una trampa que veremos en la sesión: el/healthdel servicio IA**no**debe llamar al modelo. La comprobación de que el modelo responde con calidad es trabajo de este dashboard y del golden set, no del healthcheck.

## Entregables

Subid a vuestro repositorio del Proyecto 2:

- 

ai-service/eval/golden_set.jsoncon al menos 5 casos, incluyendo uno de abstención.

- 

ai-service/eval/run_eval.py(harness ejecutable) y una ejecución de ejemplo enai-service/eval/reports/.

- 

La instrumentación de métricas en el servicio IA y el**dashboard**(una captura + la configuración o el código del panel).

- 

UnREADMEcorto (docs/evaluation.md) explicando cómo se lanza la evaluación y cómo se lee el dashboard.

No subáis claves reales ni el token de servicio: van por variable de entorno, como siempre.

## Cómo llegar preparado al directo

Traed**vuestros números**: la salida del harness sobre vuestro golden set y una captura del dashboard. Y traed anotado**qué casos falla**el sistema y qué señal del dashboard os llama la atención (una latencia alta, un coste por petición mayor del esperado, un caso de abstención que no abstiene).

En el directo ejecutaremos el test suite completo sobre el entorno desplegado, haremos A/B testing entre dos versiones del sistema para ver cuál mide mejor, y analizaremos los costes reales de operación. Todo eso se apoya en lo que montéis aquí: sin golden set no hay con qué comparar versiones, y sin dashboard no hay con qué ver el coste.

Si os bloqueáis, en el repositorio de la solución tenéis una versión funcional de referencia; intentadlo primero por vuestra cuenta y usadla para contrastar.

Explore More PostsThis Lesson is complete.[PreviousSesión 16. Puesta en producción II - Calidad y observabilidad — 77 min](https://training.lidr.co/posts/ai-engineering-202604-sesion-16-puesta-en-produccion-ii-calidad-y-observabilidad-77-min)[Next📄 Introducción LLMOps 🔴 — 11 min](https://training.lidr.co/posts/ai-engineering-202604-📄-introduccion-llmops-🔴-11-min)
