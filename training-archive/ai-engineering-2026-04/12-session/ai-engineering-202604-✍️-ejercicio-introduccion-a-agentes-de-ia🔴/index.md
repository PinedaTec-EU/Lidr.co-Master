---
title: "✍️ Ejercicio: Introducción a agentes de IA🔴"
source_url: "https://training.lidr.co/posts/ai-engineering-202604-%E2%9C%8D%EF%B8%8F-ejercicio-introduccion-a-agentes-de-ia%F0%9F%94%B4"
archived_at: "2026-07-22T16:22:27.731Z"
group: "12-session"
---

# ✍️ Ejercicio: Introducción a agentes de IA🔴

![Antonio Perez](./assets/c3eccac37426c36f.jpg)

[Antonio Perez](https://training.lidr.co/members/36030888)

⏱**La fecha límite es Martes 7 de Julio, al final del día.**

El sistema de estimación que venimos construyendo funciona bien con un**pipeline fijo**: reformulas, recuperas, generas. Pero una transcripción de reunión real no siempre encaja en un camino único. Un proyecto que mezcla, por ejemplo, un backend de negocio, una integración con un ERP y una app móvil obliga a**buscar presupuestos históricos por separado para cada componente**, calcular estimaciones parciales y consolidar. No sabes de antemano cuántas búsquedas harás ni en qué orden: depende de lo que diga la transcripción.

Ahí es donde una**capa agéntica**aporta algo que el pipeline fijo no tiene: la capacidad de**decidir qué hacer en cada paso**. En este ejercicio construyes ese agente y lo construyes a mano, sin framework, para ver exactamente de qué está hecho.

La idea central de la sesión: un agente no es magia. Es un bucle que llama a un LLM que**decide**, ejecuta**tools**y para cuando ha terminado. Nada que un desarrollador senior no reconozca.

## Qué vas a construir

Un agente que:

1. 

Recibe una**transcripción de reunión**.

1. 

Descompone el problema (identifica los componentes a estimar).

1. 

Usa**dos tools**para actuar:

- 

search_budgetsbusca presupuestos históricos por componente.

- 

calculate_estimatecalcula el coste a partir de los componentes y sus referencias.

1. 

Itera en un**bucle manual**(razona → actúa → observa → repite) hasta producir una estimación estructurada.

1. 

Devuelve, junto a la estimación, una**traza**que muestra su razonamiento en cada decisión.

El agente vive en el**servicio IA**(Python + FastAPI). Las tools envuelven infraestructura que ya tienes:search_budgetsreutiliza tu pipeline de recuperación de S9–S10, ycalculate_estimatees una función determinista de Python. El**backend de negocio**no ve el bucle: sigue enviando la transcripción y recibiendo la estimación estructurada, igual que en S9.

## Antes de empezar

- 

**Punto de partida:**tu propio proyecto tal como quedó tras la Sesión 11. Añadirás el agente dentro del servicio IA.

- 

**Stack:**Python 3.11+, la Responses API de OpenAI (client.responses.create) congpt-5, esfuerzo de razonamientomedium. Todo el código en inglés (variables, funciones, descripciones, docstrings, logs), sin excepción.

- 

**Material de la rama**session_12**:**ahí tienes:

- 

sample_transcript_simple.txtysample_transcript_complex.txtdos transcripciones para probar.

- 

reference_retrieval.pyun stub de recuperación que puedes usar si tu pipeline de S9–S10 no está listo.**Úsalo solo como red de seguridad**: lo ideal es que envuelvas el tuyo.

- 

calculate_estimate_skeleton.pyun esqueleto del cálculo determinista para que no pierdas tiempo en el modelo de costes y te centres en el bucle.

## Las dos tools

Defínelas con JSON Schema ystrict: true. Los nombres, descripciones y parámetros van**en inglés**.

search_budgets

- 

Propósito: recuperar presupuestos históricos relevantes para un componente o requisito concreto.

- 

Parámetros:query(string, obligatorio),filters(object, opcional: p. ej.component_type,date_range).

- 

Devuelve: lista de ítems históricos con su importe y metadatos.

- 

Implementación: envuelve tu retrieval híbrido + reranking de S9–S10.**No lo reimplementes**: el agente solo lo invoca.

calculate_estimate

- 

Propósito: calcular la estimación (parcial o total) a partir de un conjunto de componentes y sus importes de referencia.

- 

Parámetros:components(array de objetos, cada uno connameyreference_amounts).

- 

Devuelve: estructura con el desglose por componente y el total.

- 

Implementación: función determinista de Python (parte del esqueleto). No llama al LLM.

La**calidad de las descripciones importa**: son lo único que el modelo lee para decidir cuándo usar cada tool. Escríbelas pensando en un modelo que no ve tu código, solo el schema. En el directo optimizaremos precisamente esto.

## Paso a paso

1. 

**Define las tools**como una lista de schemas para la Responses API. Recuerda que en la Responses API el schema es plano ({"type": "function", "name": ..., "description": ..., "parameters": {...}}), a diferencia de Chat Completions. Los detalles exactos están en el material asíncrono de function calling.

1. 

**Escribe el system prompt del agente.**Dale un rol claro y un método: descomponer la transcripción en componentes, buscar presupuestos por cada uno, calcular estimaciones parciales y consolidar. Que sepa que dispone de las dos tools.

1. 

**Arranca el bucle.**Llama aclient.responses.create(...)pasando el system prompt, la transcripción como input y las tools, conreasoning={"effort": "medium"}.

1. 

**Conduce el bucle tú mismo.**Al usar tus propias*function tools*, la API devuelve itemsfunction_call(concall_id,nameyarguments) y**se detiene esperándote**. Ese ida-y-vuelta*es*el bucle:

- 

Recorreresponse.outputbuscando itemsfunction_call.

- 

Ejecuta la función correspondiente con losarguments(parseados desde JSON).

- 

Devuelve el resultado como un itemfunction_call_outputcon el**mismo**call_id.

- 

Vuelve a llamar a la API encadenando conprevious_response_id(o reenviando los items tú mismo).

- 

Repite mientras hayafunction_call. Sal cuando el modelo devuelva la respuesta final sin más llamadas.

No delegues el encadenamiento al comportamiento agéntico interno de la Responses API. Conduce el bucle a mano: es la única forma de capturar y mostrar cada paso, que es medio ejercicio.

1. 

**Captura la traza.**En cada iteración registra: el razonamiento del modelo (la Responses API puede emitir*reasoning summaries*, útiles aquí), la tool invocada con sus argumentos, y la observación (el resultado). Guárdalo en una lista ordenada.

1. 

**Devuelve**la estimación estructurada final**y**la traza.

## Requisito de traza

La salida debe dejar ver el razonamiento paso a paso. Un formato mínimo aceptable por iteración:

STEP 1 reasoning: <what the agent decided and why> action: search_budgets(query="...", filters={...}) observation: <summary of returned items>

No hace falta UI: una traza legible por consola o en un fichero es suficiente para la entrega.

## Criterios de aceptación

Tu agente está listo cuando, consample_transcript_complex.txt:

- 

Identifica**más de un componente**y hace**más de una**llamada asearch_budgets(si resuelve todo en una sola búsqueda, o el prompt es demasiado directivo, o la transcripción no es lo bastante compleja).

- 

Llama acalculate_estimatecon los componentes y sus referencias.

- 

Termina por sí solo (no se queda en bucle infinito ni corta a mitad).

- 

Produce una estimación estructurada coherente.

- 

La traza muestra, para cada paso, razonamiento + acción + observación.

## Entregable

Envía a Lia, antes del directo:

1. 

El**enlace a tu repositorio**con el agente dentro del servicio IA.

1. 

La**traza de ejecución**parasample_transcript_complex.txt.

Trae tu agente al directo: compararemos su comportamiento con el del pipeline fijo sobre la misma transcripción y analizaremos su razonamiento.

## Pitfalls comunes

- 

**Confundir el schema de Responses con el de Chat Completions.**En Responses eltype/namevan al mismo nivel; no anides bajo una clavefunction.

- 

**Olvidar el**call_idal devolver el resultado. Cadafunction_call_outputdebe referenciar elcall_idde sufunction_call.

- 

**No poner condición de parada.**Define un máximo de iteraciones como salvaguarda, además de la salida natural del bucle.

- 

**Descripciones de tools vagas.**Si el agente elige mal la tool o inventa argumentos, casi siempre es la descripción, no el modelo.

- 

**Reimplementar la recuperación.**search_budgetsenvuelve tu pipeline; no lo reconstruyas.

## Extensión opcional

Añade una tercera tool,validate_estimate, que aplique guardrails de verificación sobre la estimación final (los que trabajamos en S4): rangos razonables, componentes sin presupuesto de referencia, totales incoherentes. Haz que el agente la invoque como último paso antes de devolver el resultado. La veremos en el directo, así que tenerla explorada te dará ventaja.

## Cómo entregar

Sube la ramasession-12/pre-workcon tu agente implementado.

Envía por mail a[lia@lidr.co](mailto:lia@lidr.co)el enlace a la rama
(URL completa de GitHub) hasta dos días antes de la sesión en vivo.

La rama debe:

- 

Ejecutar sin errores

- 

Contener el código del agente

- 

Ser accesible (repositorio público o con permisos)

## Nota de coste de API

Depura primero la**mecánica del bucle**congpt-5-miniy la transcripción simple: es más barato y rápido para verificar que el ida-y-vuelta funciona. Cuando el bucle sea sólido, cambia agpt-5con esfuerzomediumpara la ejecución real sobre la transcripción compleja. Iterar así mantiene el gasto de este ejercicio por debajo de un par de dólares.
