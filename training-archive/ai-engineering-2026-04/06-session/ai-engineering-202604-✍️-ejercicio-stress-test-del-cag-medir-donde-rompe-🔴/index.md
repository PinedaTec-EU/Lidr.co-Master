---
title: "✍️ Ejercicio: Stress test del CAG: Medir donde rompe 🔴"
source_url: "https://training.lidr.co/posts/ai-engineering-202604-✍️-ejercicio-stress-test-del-cag-medir-donde-rompe-🔴"
archived_at: "2026-06-12T09:24:02.485Z"
group: "06-session"
---

# ✍️ Ejercicio: Stress test del CAG: Medir donde rompe 🔴

![Antonio Perez](./assets/c3eccac37426c36f.jpg)

[Antonio Perez](https://training.lidr.co/members/36030888)

# Guía del ejercicio previo

Hasta la sesión 5 hemos construido un sistema**CAG (Cache-Augmented Generation)**: cada turno inyecta en el prompt[summary] + anchors + ventana_deslizante + ProjectMetadata + tier + transcript + texto_extraído_de_adjuntos. Todo cabe en el contexto del LLM, por construcción. Eso funciona mientras los proyectos son cortos y los adjuntos modestos.

Nunca lo hemos puesto a prueba en serio.**No sabemos a qué turno empieza a olvidar el nombre del proyecto, ni cuánto cuesta el turno 10 frente al turno 1, ni a qué tamaño de adjunto la latencia P95 supera el SLA del cliente.**El módulo 3 (sesión 6 en directo) introduce RAG como respuesta a esas limitaciones, pero el alumno tiene que ver con sus propios datos qué limitación existe antes de aceptar la solución.

Este ejercicio es ese trabajo: instrumentas tu CAG, lo sometes a tres escenarios de carga (multi-turno largo, adjuntos grandes, ráfagas), produces unREPORT.mdcon tres curvas y dos párrafos de lectura. Llegas al directo con un baseline cuantitativo del CAG; sobre él comparamos RAG.

## Punto de partida

Tras la sesión 5 ya tienes:

- 

**Servicio IA conversacional**con sesiones en memoria, ventana deslizante (MAX_CONVERSATION_TURNS=6), anclas heurísticas, summarizer acumulativo,ProjectMetadataextraído turno a turno, tier dinámico, Actor-Critic-Boss opcional.

- 

**Adjuntos PDF/DOCX**víamultipart/form-datacon extracción local de texto (camino B).

- 

**Framework de evals**con 16 casos golden (evals/golden_dataset.json), tres métricas binarias (SchemaAdherenceMetric,CostBoundsMetric,ContentRecallMetric) y un runner CLI (evals/run.py) con modosactoryacb.

- 

**Wrapper LLM observable**: cada llamada devuelvelatency_ms,tokens_in,tokens_out,cost_usd,model,provider. Tabla de precios enapp/services/llm_wrapper.py(MODEL_COSTS).

- 

**Endpoint de debug**GET /sessions/{id}que exponemessage_count,anchors_count,summary_chars,last_resolved_tier,last_tier_rule— la mitad de las observaciones que el ejercicio necesita ya están emitidas.

Todo lo que añadirás se apoya en esta base. No se reescribe nada.

## Objetivos de aprendizaje

Al terminar deberías poder defender en una conversación técnica:

- 

La diferencia entre**fallar duro**(el esquema rompe, salta una excepción, el CI te avisa) y**degradar silenciosamente**(el recall baja del 90 al 60% sin que ningún test rojo se entere). Cuál es más peligroso en un sistema CAG y por qué.

- 

Cómo**extender un framework de evals existente**con métricas nuevas sin reescribirlo: el patrónMetricResult+run_all_metricsya está, añadir una métrica es ~15 líneas.

- 

Por qué los**presupuestos**(token budget, latency budget, cost budget) son contratos de diseño, no banderas a observar a posteriori. Una métricaLatencyBudgetMetric(budget_ms=4000)convierte el SLA en un test.

- 

Las**tres curvas canónicas**de cualquier sistema basado en contexto al escalar: latencia vs tokens, coste acumulado vs turnos, recall de hechos vs longitud del historial. Saber leerlas.

- 

Cuándo “el contexto está lleno” no es un error del LLM sino**una decisión arquitectónica**: el momento exacto en el que CAG empieza a perder frente a RAG.

## Lo que entra en el ejercicio

Cinco bloques con dificultad escalonada. Los cinco son medibles — el deliverable es un reporte con números, no código de producción.

### Bloque 1 — Unificar la observación por turno

Hoy el sistema emite logs sueltos a lo largo de cada estimación:cache_hit,llm_call_completed,history_compressed,summarizer_completed,session_estimate_received. Para extraer un CSV de una pasada necesitas que cada llamada deje**un único evento**turn_observedcon todo lo relevante junto.

Campos mínimos del evento:
turn_index # 1-based, contado dentro de la sesión session_id enriched_transcript_chars # transcript + adjuntos concatenados attachments_total_chars # 0 si no hay messages_in_window # len(history.messages) tras compresión anchors_count summary_chars tokens_in tokens_out cost_usd latency_ms cache_hit_kind # "none" | "exact" | "semantic" last_resolved_tier

La mayoría ya circula por el código en eventos separados; el ejercicio es**agregarlos**enEstimationService.estimate_conversational()justo antes delreturn.

### Bloque 2 — Escenario sintético multi-turno

Un scriptevals/stress/scenarios.pyque genera conversaciones de N turnos (N ∈ {1, 3, 6, 10, 20}) sobre un mismo proyecto. Tres perfiles, cada uno diseñado para forzar un comportamiento del sistema:

- 

**Proyecto que crece**— turno a turno se añaden requisitos coherentes (autenticación, multi-tenant, audit log, exporte CSV…). Mide la curva de coste y si elproject_nameoriginal sobrevive al turno 20.

- 

**Proyecto que pivota**— el turno 5 cambia el stack (de React a Flutter, por ejemplo). Mide si la metadata se actualiza limpiamente o simentioned_technologiesacumula ambas.

- 

**Proyecto que se contradice**— el turno 3 dice “presupuesto 30k€”, el turno 8 dice “presupuesto 80k€”. Mide cuál se preserva, cuál se promueve a ancla, cuál acaba en el summary.

Cada perfil declara un**fact-tracker**: para cada turno, qué afirmación deberían recordar las llamadas posteriores. Ese tracker alimenta aMemoryDriftMetricdel bloque 4.

### Bloque 3 — Escenario de adjuntos grandes

Un script que produce PDFs sintéticos de tamaños calibrados (puede usarreportlab,fpdf2, o un PDF de Lorem Ipsum repetido). Cinco puntos:
0 KB (no attachment, baseline) 5 KB (≈ 2 páginas de texto plano) 20 KB (≈ 8 páginas) 50 KB (≈ 20 páginas) 100 KB (cerca del cap MAX_ATTACHMENT_CHARS=60.000; medirás cómo trunca)

Para cada tamaño, ejecuta la misma estimación inicial (mismotranscriptcorto, mismoproject_type). El stress está en el adjunto. Mide las tres curvas: latencia, coste, recall del contenido del adjunto en elsummaryde la respuesta.

### Bloque 4 — Tres métricas nuevas

Añade al framework existente (evals/metrics.pyo módulo paraleloevals/stress/metrics.py, justifica la elección):
class LatencyBudgetMetric: """1.0 si latency_ms ≤ budget_ms; 0.0 si no.""" def __init__(self, budget_ms: int): ... def evaluate(self, observation) -> MetricResult: ... class CostBudgetMetric: """1.0 si cost_usd ≤ budget_usd; 0.0 si no.""" def __init__(self, budget_usd: float): ... def evaluate(self, observation) -> MetricResult: ... class MemoryDriftMetric: """1.0 si el fact declarado del turno k aparece en summary, anchors, o ProjectMetadata del turno N (con N > k); 0.0 si no.""" def __init__(self, fact: str, where: list[str] = ["summary","anchors","metadata"]): ... def evaluate(self, session_snapshot) -> MetricResult: ...

Replica el patrónMetricResult(name,score,passed,details) que ya usaevals/metrics.py.**Determinismo > sofisticación**: nada de embeddings ni LLM-as-judge. Match exacto (case-insensitive) sobre los campos del snapshot.

### Bloque 5 — Runner + reporte

Un nuevo móduloevals/stress/run.pyque orquesta:
uv run python -m evals.stress.run --http <http://localhost:8000> \\ --scenarios growing,pivot,contradiction \\ --attachment-sizes 0,5,20,50,100 \\ --repeats 3 \\ --output evals/stress/results.csv

Reusa el patrón deevals/run.py(httpx en modo--http,TestClienten modo in-process). Vuelca**un CSV con una fila por turno**y todas las columnas delturn_observedmás una por métrica binaria.

Sobre ese CSV escribeevals/stress/REPORT.md— el deliverable que traes al directo. Estructura mínima:

1. 

**Tabla resumen**con P50/P95 delatency_ms, coste acumulado por escenario, hit rate de ambas caches, recall medio del fact-tracker.

1. 

**Tres curvas**(en ASCII / Markdown table, sin gráficos): latencia vs tokens, coste acumulado vs turno, recall vs N.

1. 

**Dos párrafos de lectura**: “Dónde empieza a romperse mi CAG y por qué”.

## Lo que NO entra

Tentación Por qué no Implementar RAG. Es el directo. La gracia es comparar contra el baseline que produces aquí. Optimizar el CAG (acortar el system, comprimir más agresivo, bajarMAX_CONVERSATION_TURNS). El ejercicio mide, no optimiza. Mover una constante invalida la comparación. Comparación entre proveedores (gpt-4o-mini vs claude-haiku-4-5). Fuera de scope. Mantén un único proveedor para que las curvas sean comparables. Notebook Jupyter con matplotlib. El deliverable es Markdown + CSV. Evitamos añadir dependencias gráficas. Las tres curvas se pueden representar como tabla. Persistir resultados a Postgres / SQLite. CSV enevals/stress/results.csv. LLM-as-judge paraMemoryDriftMetric. Determinismo > sofisticación. Match case-insensitive contra el snapshot. UI / panel nuevo para visualizar. El reporte en Markdown sobra para el directo.

No habrá ramasolutions/session-06con solución de referencia. Cada alumno producirá un reporte distinto — la “lectura ejemplar” se enseña en directo a partir de los reportes que lleguen.

## Pasos guiados

Cada paso enuncia el objetivo; las decisiones de implementación las tomas tú.

### Paso 1 — Decidir el shape deturn_observedy emitirlo

Editaapp/services/estimation.py::EstimationService.estimate_conversational(). Justo antes delreturn, agrega los campos que ya viajan por el método (algunos los recibe del wrapper, otros delsession.history) y emite un único eventostructlog.get_logger().info("turn_observed", ...)con los 13 campos del bloque 1.

Pregúntate por qué un evento agregado es más útil que cinco logs sueltos. (Pista: parseo en CSV de una pasada, correlación trivial entremessages_in_windowycost_usd, no hay que reconciliar timestamps.)

### Paso 2 — Diseñar los tres perfiles multi-turno

Creaevals/stress/scenarios.py. Define cada perfil como una lista de tuplas(turn_index, transcript, fact_to_remember). Los facts pueden ser strings cortos (“project name: Nimbus”, “stack includes Flutter”, “budget locked: 30000 EUR”). Son los queMemoryDriftMetricbuscará en el snapshot de turnos posteriores.

### Paso 3 — Generar el corpus de adjuntos sintéticos

Scriptevals/stress/fixtures/build_pdfs.pyque produceattach_5kb.pdf,attach_20kb.pdf,attach_50kb.pdf,attach_100kb.pdf(attach_0kbno hace falta — es ausencia de adjunto).reportlabofpdf2valen.**No comites los PDFs**: comitea el script y deja que el runner los regenere — son determinísticos.

### Paso 4 — Añadir las tres métricas

LatencyBudgetMetric,CostBudgetMetric,MemoryDriftMetric. ReusaMetricResult(name,score,passed,details). Si las metes enevals/metrics.py, re-expórtalas desdeevals/__init__.py. Si prefieresevals/stress/metrics.py(porque dependen del shape deturn_observed, no deEstimationResult), justifícalo en el reporte. Tests unitarios mínimos entests/test_stress_metrics.py: una métrica que pasa, una que falla, una con datos límite.

### Paso 5 — Implementar el runner

evals/stress/run.py. Estructura:
async def main(): for scenario in scenarios: for attachment_size in attachment_sizes: for repeat in range(repeats): session_id = await client.post("/sessions") for turn in scenario.turns: response = await client.post( f"/sessions/{session_id}/estimate", data={...}, files={...}, ) # extraer turn_observed del log o del response # evaluar las tres métricas con el snapshot GET /sessions/{id} # escribir fila al CSV

Leeturn_observedparseando stdout del estimator (docker compose logs -f estimator | grep turn_observed) o, más simple, expón una versión enriquecida víaGET /sessions/{id}con el último turno embebido. Tú decides — justifica.

### Paso 6 — EscribirREPORT.md

evals/stress/REPORT.md. Markdown corto (1-2 páginas). Contenido mínimo:

- 

**Tabla resumen**(una fila por escenario × tamaño de adjunto, columnas: P50 latency, P95 latency, total cost USD, exact cache hit rate, semantic cache hit rate, mean recall del fact-tracker).

- 

**Tres curvas**representadas como tabla:

- 

latency_msvstokens_in

- 

cost_usdacumulado vsturn_index(por escenario)

- 

MemoryDriftMetricvsN(turnos)

- 

**Dos párrafos de lectura**que respondan, con tus datos, a:*¿a partir de qué turno empieza a romperse mi CAG? ¿qué dimensión domina la degradación — latencia, coste, o pérdida de memoria? ¿qué constituiría un caso límite que justifica saltar a RAG?*

## Criterios de “hecho”

El ejercicio está completo cuando:

- 

Cada llamada aPOST /sessions/{id}/estimateemite un eventoturn_observedcon los 13 campos del bloque 1.

- 

uv run python -m evals.stress.run --http http://localhost:8000corre end-to-end sin errores y deja un CSV con**≥ 50 filas**(3 escenarios × 5 tamaños × ≥ 3 repeticiones × N turnos, ajustando los floor para llegar al mínimo).

- 

evals/stress/metrics.py(o el lugar elegido) exponeLatencyBudgetMetric,CostBudgetMetric,MemoryDriftMetriccon tests unitarios verdes.

- 

evals/stress/REPORT.mdcontiene la tabla resumen, las tres curvas (en tabla), y los dos párrafos de lectura con al menos una afirmación cuantitativa concreta del tipo*“a partir del turno N=12, el recall del project_name cae bajo el 60%”*o*“el coste del turno 20 multiplica por X.X el del turno 1”*.

- 

Todo está en el repo (no en tu local). El reporte es el deliverable.

## Entrega

Debes entregar:

- 

evals/stress/REPORT.md

- 

evals/stress/results.csv

Formato de entrega:

- 

Subir los archivos a tu repositorio del proyecto

- 

Compartir el link al repositorio o Pull Request por mail a[lia@lidr.co](mailto:lia@lidr.co)

No se aceptarán entregas por:

- 

capturas

- 

documentos sueltos

- 

mensajes por chat
