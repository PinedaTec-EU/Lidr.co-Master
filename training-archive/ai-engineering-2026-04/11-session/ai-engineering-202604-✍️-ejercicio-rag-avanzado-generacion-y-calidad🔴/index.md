---
title: "✍️ Ejercicio: RAG avanzado: generación y calidad🔴"
source_url: "https://training.lidr.co/posts/ai-engineering-202604-✍️-ejercicio-rag-avanzado-generacion-y-calidad🔴"
archived_at: "2026-07-02T12:43:50.268Z"
group: "11-session"
---

# ✍️ Ejercicio: RAG avanzado: generación y calidad🔴

![Antonio Perez](./assets/c3eccac37426c36f.jpg)

[Antonio Perez](https://training.lidr.co/members/36030888)

⏱**La fecha límite es Martes 30 de Junio, al final del día.**

La recuperación ya funciona bien. Tras las sesiones 9 y 10 el servicio IA reformula la query, recupera con búsqueda híbrida, aplica reranking, expansión, routing multi-índice y filtrado temporal, y ensambla el contexto antes de generar. El generador estructurado de la Sesión 9 ya produce una estimación en JSON con citación**obligatoria**y política de*insufficient context*.

El problema es que esa citación es**gruesa y no verificable**: cita a nivel de estimación global, y nada garantiza que la fuente que el modelo dice haber usado exista realmente en el contexto recuperado. Una citación que apunta a un presupuesto que no se le pasó al LLM no es una citación: es una alucinación con apariencia de rigor.

En este ejercicio subes la citación a**nivel de línea de estimación**y la haces**verificable programáticamente**, y montas una primera**evaluación objetiva con RAGAS**sobre tu golden set.

## Objetivo

1. 

Que cada línea de la estimación (cada componente: "módulo de pagos", "autenticación", etc.) referencie el presupuesto histórico concreto del que se derivó, de forma verificable.

1. 

Detectar y rechazar citaciones colgantes (a fuentes que no están en el contexto recuperado).

1. 

Medir la calidad de la generación con las cuatro métricas de RAGAS sobre un conjunto de consultas con respuesta de referencia.

Todo el código en inglés (nombres, comentarios, logs, literales, prompts). La prosa de tus notas y el golden set pueden ir en español.

## Parte 1 - Citación verificable a nivel de línea

### 1.1 Extiende el schema de salida

Amplía el modelo Pydantic v2 de la estimación para que**cada línea**transporte sus fuentes. El generador sigue usando la Responses API (client.responses.parse) context.formatestricto. Forma objetivo (adáptala a tu modelo actual):

python
class SourceReference(BaseModel): chunk_id: str # id of the retrieved chunk supporting this line document_id: str # historical budget document the chunk belongs to evidence: str # verbatim span or figure from the source backing the line class EstimateLineItem(BaseModel): component: str hours: float rationale: str grounded: bool # False => no sufficient source data sources: list[SourceReference] # non-empty iff grounded is True

Regla de integridad (impleméntala como validador o como verificación posterior): una línea congrounded=Truedebe tener al menos una fuente; una línea congrounded=Falseno puede inventar horas a partir de la nada y debe marcarse explícitamente como sin datos suficientes.

### 1.2 Fuerza la atribución por línea en el prompt

Modifica el prompt de generación para que el modelo:

- 

Atribuya cada línea a uno o máschunk_id**del contexto que se le ha pasado**(los chunks recuperados ya llegan identificados al ensamblador; propágalos al prompt con su id).

- 

Copie enevidenceel fragmento o la cifra concreta de la fuente que respalda la línea, en lugar de parafrasear.

- 

Marquegrounded=Falsecuando no encuentre soporte, en vez de estimar a ojo.

### 1.3 Verifica las citaciones tras la generación

Implementa una verificación post-generación que recorra todas las líneas y compruebe que**cada**chunk_id**citado existe en el conjunto de chunks recuperados**que se le entregó al LLM. Firma orientativa:

python
def verify_citations( estimate: Estimate, retrieved_chunk_ids: set[str], ) -> CitationReport: """Flag any line whose cited chunk_id was never in the retrieved context."""

El informe debe distinguir, como mínimo: líneas correctamente fundamentadas, líneas con citación colgante (id inventado) y líneas marcadas como sin datos suficientes. Loguea el resultado con structlog correlacionado porrequest_id. Una citación colgante es un fallo de calidad, no un detalle cosmético: déjalo visible.

## Parte 2 - Evaluación RAGAS básica

### 2.1 Extiende el golden set de la Sesión 10

Parte de las 5 consultas que construiste en el ejercicio de la Sesión 10. Para cada una, añade una**respuesta de referencia**(ground_truth): la estimación correcta o esperada para esa transcripción, según el criterio de un experto. No partes de cero: enriqueces el set que ya tienes.

### 2.2 Configura RAGAS

Monta una evaluación que, para cada consulta, registre las cuatro entradas que RAGAS necesita y calcule las cuatro métricas:

python
# Per query, RAGAS expects: # question -> the estimation request # answer -> the estimate your pipeline generated (as text) # contexts -> the retrieved chunks passed to the generator # ground_truth -> the reference estimate from your extended golden set # # Metrics to compute: # faithfulness, answer_relevancy, context_precision, context_recall

RAGAS usa un LLM como juez y un modelo de embeddings para algunas métricas: configúralo con tu clave de OpenAI,text-embedding-3-smallpara los embeddings y el modelo de chat que prefieras como juez. El corpus está en español; el juez evalúa en español sin problema.

### 2.3 Produce la tabla de métricas

Genera una tabla con una fila por consulta y una fila de promedio, con las cuatro métricas. Esta tabla es tu**baseline de calidad de generación**: la traes al directo y la extendemos midiendo el efecto de la detección de alucinaciones y del pipeline de evaluación completo.

## Entregables

1. 

Código del schema extendido, el prompt de atribución por línea y la funciónverify_citations(en inglés).

1. 

El golden set extendido conground_truthpor consulta.

1. 

El script de evaluación RAGAS y la**tabla de métricas**(4 métricas × 5 consultas + promedio).

1. 

Una nota breve (2–3 frases) con lo que más te chirría de tus números: ¿faithfulness baja con citación gruesa?, ¿context recall flojo en alguna consulta?

## Criterios de aceptación

- 

Cada línea congrounded=Truecita al menos una fuente real del contexto recuperado.

- 

La verificación detecta una citación colgante si la introduces a propósito para probarla.

- 

Las líneas sin soporte se marcan como sin datos suficientes, no se rellenan con cifras inventadas.

- 

RAGAS devuelve las cuatro métricas para las cinco consultas y un promedio.

## Qué traer al directo

- 

La**tabla RAGAS**(será el baseline que extendemos en vivo).

- 

Tu informe de verificación de citaciones sobre al menos una estimación real.

- 

La nota con tus números más llamativos: trabajaremos sobre ellos en el bloque de casos avanzados.

**Nota sobre el stack:**Python 3.11+, FastAPI, SQLAlchemy 2.0 async, Pydantic v2, OpenAI Responses API (client.responses.parse), structlog, RAGAS. La verificación de citaciones es lógica de tu servicio IA; si en tu implementación de referencia el backend de negocio (Rails) consume la estimación citada, recuerda que el contrato HTTP no cambia: solo se enriquece el cuerpo de la respuesta con las fuentes por línea.

## 👉Cómo entregar

Además de subir la ramasession-11/pre-worky abrir el PR, envía por mail a[lia@lidr.co](mailto:lia@lidr.co)el enlace a la rama (URL completa de GitHub) hasta dos días antes de la sesión en vivo. El plazo es estricto: necesitamos margen para revisar las implementaciones, validar los golden sets y preparar el material de la sesión basándonos en los números reales que obtengáis.

Si llegas a la sesión sin haber entregado, podrás seguir el directo igualmente, pero los bloques de casos avanzados asumirán que ya tuviste cifras de tu setup.
Explore More PostsReady to move on to the next Lesson?[Mark as Complete](#)[PreviousSesión 11: RAG Avanzado - Generación y calidad — 114 min](https://training.lidr.co/posts/ai-engineering-202604-sesion-11-rag-avanzado-generacion-y-calidad-114-min)[Next📄 Content augmentation: preparar el contexto recuperado antes de generar 🔴 — 19 min](https://training.lidr.co/posts/ai-engineering-202604-📄-content-augmentation-preparar-el-contexto-recuperado-antes-de-generar-🔴-19-min)[Previous Comments](#)

[More Comments](#)

Drag photo, video or file here[](#)[](#)[](#)[Comment](#)[Cancel](#)
