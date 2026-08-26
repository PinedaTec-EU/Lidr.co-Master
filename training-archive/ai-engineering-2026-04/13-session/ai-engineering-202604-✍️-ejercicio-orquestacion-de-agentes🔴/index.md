---
title: "✍️ Ejercicio: Orquestación de agentes🔴"
source_url: "https://training.lidr.co/posts/ai-engineering-202604-%E2%9C%8D%EF%B8%8F-ejercicio-orquestacion-de-agentes%F0%9F%94%B4"
archived_at: "2026-07-22T16:22:59.908Z"
group: "13-session"
---

# ✍️ Ejercicio: Orquestación de agentes🔴

![Antonio Perez](./assets/c3eccac37426c36f.jpg)

[Antonio Perez](https://training.lidr.co/members/36030888)

🚨La fecha límite:**Martes 14 de Julio a las 23:59 de tu hora local.**

## Objetivo

Reexpresar el flujo de estimación del proyecto como un**grafo de LangGraph**dentro del servicio IA, con estado compartido tipado, persistencia y observabilidad. Debes llegar al directo con el grafo**corriendo de principio a fin en secuencial**y con**una traza completa**de una ejecución.

El directo parte de ahí: lo haremos paralelo, robusto y con intervención humana. Por eso en la pre-sesión**no**tienes que resolver ni el paralelismo ni el manejo de errores avanzado (ver "Lo que NO toca todavía").

## Contexto

En la Sesión 12 construiste, a mano, un bucle agéntico sobre el pipeline RAG: decidía entresearch_budgets,calculate_estimateyvalidate_estimatey exponía su traza de razonamiento. Funciona, pero se vuelve incómodo en cuanto el flujo tiene varios pasos, ramas condicionales o necesita volver atrás.

En esta sesión ese bucle pasa a ser un**grafo explícito**. Nada cambia de puertas afuera: el**servicio IA**sigue recibiendo una transcripción y devolviendo una estimación estructurada con su campostatus. El**backend de negocio**ni se entera de qué hay debajo. El grafo vive**dentro del servicio IA**.

## Punto de partida y dependencias

Construyes sobre tu propio servicio IA (S9–S12). Si tu agente de la S12 quedó flojo, usa las funciones de referencia del pack de scaffolding: te basta con envolverlas como nodos.

Dependencias nuevas (gestoruv):
uv add langgraph langgraph-checkpoint-postgres logfire

Reutiliza el**mismo PostgreSQL del proyecto**(el que ya tiene pgvector). El checkpointer crea sus propias tablas y convive sin problema con las de embeddings. No levantes infraestructura nueva.

## El grafo que vas a construir

Cinco nodos, de momento**en secuencial**:
START → extract_requirements → classify_components → search_budgets → generate_estimate → validate_and_consolidate → END

- 

extract_requirements: de la transcripción a una lista de requisitos.

- 

classify_components: agrupa los requisitos en componentes con su categoría.

- 

search_budgets: para cada componente, recupera presupuestos de referencia (por ahora, uno tras otro).

- 

generate_estimate: consolida los presupuestos en una estimación.

- 

validate_and_consolidate: revisa la estimación y fija elstatusde salida.

## Niveles

### Nivel 1 - El grafo, cableado y secuencial*(obligatorio)*

1. 

Define un**estado tipado**(TypedDict) con al menos**un reducer acumulador**(Annotated[..., operator.add]) para un campo que crezca a lo largo del flujo (por ejemplo, los presupuestos encontrados o los errores).

1. 

Implementa los cinco nodos como**funciones puras**: reciben el estado y devuelven una actualización parcial. Reutiliza tu lógica de S9–S12 (o el scaffolding) dentro de cada nodo.

1. 

Cablea el grafo con aristas directas y compílalo.

1. 

El endpoint del servicio IA sigue devolviendo la estimación estructurada con sustatus.**El contrato hacia el backend de negocio no cambia.**

### Nivel 2 - Persistencia y observabilidad*(obligatorio)*

1. 

Añade un**checkpointer**sobre el Postgres del proyecto y pasa unthread_idpor ejecución (usa el identificador de la estimación).

1. 

Instrumenta con**Logfire**y consigue**una traza completa**de una ejecución sobresample_transcript_complex.txt, con un span por nodo. (Si prefieres LangSmith porque te vas a apoyar mucho en LangChain, es válido; documenta cuál usaste.)

### Nivel 3 - Primera arista condicional*(opcional)*

Sustituye la arista fijavalidate_and_consolidate → ENDpor una**arista condicional**: si la validación falla, enruta a un final constatus = "needs_review"; si pasa, aENDconstatus = "validated". Nada más: el reintento serio, el fallback y la intervención humana los montamos en el directo.

## Lo que NO toca todavía (lo vemos en el directo)

Para que no sobre-construyas, esto queda**fuera**de la pre-sesión:

- 

**Ejecución paralela**desearch_budgetspor componente (Send API): en la pre-sesión va secuencial. Medir el coste de lo secuencial y paralelizarlo es el caso estrella del directo.

- 

**Manejo de errores avanzado**: reintentos con backoff, nodo de fallback, timeouts, circuit breakers.

- 

**Intervención humana (HITL)**coninterrupt()en la validación.

- 

**Optimización a partir de la traza**: la lectura fina de las trazas para decidir qué tocar la hacemos juntos.

## Esqueleto de referencia

Punto de partida (con huecos marcados comoTODO). Todo el código en inglés, como siempre.

python
# graph/state.pyfrom typingimport Annotated, Optional, TypedDictimport operatorclassComponent(TypedDict): name:str category:strclassBudgetMatch(TypedDict): component:str reference_budget_id:str amount:floatclassEstimationState(TypedDict): transcript:str requirements:list[str] components:list[Component]# Accumulator field: grows as each component is searched. budget_matches: Annotated[list[BudgetMatch], operator.add] estimate: Optional[dict] status: Optional[str]# "validated" | "needs_review" errors: Annotated[list[str], operator.add]

python
# graph/build.pyfrom langgraph.graphimport StateGraph, START, ENDfrom graph.stateimport EstimationStatefrom graph.nodesimport( extract_requirements, classify_components, search_budgets, generate_estimate, validate_and_consolidate,)defbuild_graph(checkpointer): builder= StateGraph(EstimationState) builder.add_node("extract_requirements", extract_requirements) builder.add_node("classify_components", classify_components) builder.add_node("search_budgets", search_budgets)# sequential for now builder.add_node("generate_estimate", generate_estimate) builder.add_node("validate_and_consolidate", validate_and_consolidate) builder.add_edge(START,"extract_requirements") builder.add_edge("extract_requirements","classify_components") builder.add_edge("classify_components","search_budgets") builder.add_edge("search_budgets","generate_estimate") builder.add_edge("generate_estimate","validate_and_consolidate") builder.add_edge("validate_and_consolidate", END)return builder.compile(checkpointer=checkpointer)

python
# graph/nodes.py (one node shown; the rest follow the same shape)import logfiredefsearch_budgets(state): matches=[]with logfire.span("node: search_budgets"):for componentin state["components"]:# TODO: reuse your S9-S12 retrieval (or the scaffolding stub).match= retrieve_budget_for(component)# noqa: F821 matches.append(match)# Partial state update; the reducer merges into the accumulator field.return{"budget_matches": matches}

python
# app startup (checkpointer on the project Postgres + observability)import logfirefrom langgraph.checkpoint.postgres.aioimport AsyncPostgresSaverlogfire.configure()logfire.instrument_fastapi(app)# noqa: F821 (app defined elsewhere)logfire.instrument_asyncpg()logfire.instrument_httpx()# captures the OpenAI Responses API calls (SDK uses httpx)# The FastAPI async stack pairs with the async checkpointer.# On first run, call `await checkpointer.setup()` once to create its tables.

python
# invoking the graph from your endpointconfig={"configurable":{"thread_id": estimation_id}}# noqa: F821result=await graph.ainvoke({"transcript": transcript}, config)# noqa: F821# Return result["estimate"] and result["status"] to keep the existing contract.

Nota: el checkpointer asíncrono (AsyncPostgresSaver) es el que casa con el stack async del servicio IA (FastAPI + asyncpg). Para el span por nodo basta con envolver el cuerpo de cada nodo en unwith logfire.span(...), como ensearch_budgets. Para la instrumentación concreta de LangGraph con tu observabilidad, sigue la documentación vigente de la herramienta que elijas.

## Entrega

No hay entrega formal más allá de lo que Lia recoge: enlace a tu repo y enlace a la traza de una ejecución completa sobresample_transcript_complex.txt. Debes llegar al directo con los**Niveles 1 y 2**funcionando. La**solución de referencia**se abre en la ramasession_13al cierre del directo.

### Cómo entregar

Sube la ramasession-13/pre-workcon el grafo implementado.

Envía por mail a[lia@lidr.co](mailto:lia@lidr.co)el enlace a la rama (URL completa de GitHub) al menos dos días antes de la sesión en vivo. Las entregas posteriores no entran en la revisión grupal del inicio del directo.

La rama debe:

- 

Ejecutar de principio a fin sin errores

- 

Contener los Niveles 1 y 2 completos: grafo cableado, persistencia en Postgres y una traza completa con un span por nodo

- 

Ser accesible (repositorio público o con permisos)

## Criterios de "hecho"

- 

El grafo corre de principio a fin y el endpoint devuelve la estimación con sustatus; el contrato hacia el backend de negocio es el de siempre.

- 

El estado es tipado y tiene al menos un reducer acumulador.

- 

Los cinco nodos son funciones puras que devuelven actualizaciones parciales.

- 

El checkpointer persiste en el Postgres del proyecto y cada ejecución lleva suthread_id.

- 

Existe una traza completa de una ejecución, con un span por nodo.

## Documentación de referencia

- 

LangGraph - StateGraph, nodos, aristas y estado:https://docs.langchain.com/oss/python/langgraph

- 

LangGraph - persistencia y checkpointers (Postgres):https://docs.langchain.com/oss/python/langgraph/persistence

- 

Logfire - primeros pasos e instrumentación:https://pydantic.dev/docs/logfire/get-started/

- 

LangSmith (si optas por ella):https://docs.smith.langchain.com/
