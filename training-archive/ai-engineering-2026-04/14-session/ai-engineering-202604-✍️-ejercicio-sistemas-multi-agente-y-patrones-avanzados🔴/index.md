---
title: "✍️ Ejercicio: Sistemas multi-agente y patrones avanzados🔴"
source_url: "https://training.lidr.co/posts/ai-engineering-202604-%E2%9C%8D%EF%B8%8F-ejercicio-sistemas-multi-agente-y-patrones-avanzados%F0%9F%94%B4"
archived_at: "2026-07-22T22:50:29.688Z"
group: "14-session"
---

# ✍️ Ejercicio: Sistemas multi-agente y patrones avanzados🔴

![Antonio Perez](./assets/c3eccac37426c36f.jpg)

[Antonio Perez](https://training.lidr.co/members/36030888)

⏳Tiempo estimado: 19 min

Tenéis un grafo de estimación que funciona. Recibe una transcripción, extrae requisitos, clasifica componentes, busca presupuestos históricos, genera una estimación y la valida. Cinco nodos, estado tipado, checkpointer sobre Postgres, trazas limpias. Hace lo que promete.

Y ahora alguien os dice que hay que convertirlo en un sistema multi-agente.

La pregunta correcta ante esa frase no es "¿cómo?". Es "¿por qué?". Porque desde fuera, y esto es lo primero que conviene desactivar un sistema multi-agente se parece bastante a un grafo con más nodos y nombres más ambiciosos. Si la única diferencia fuese llamarbudget_searchera lo que antes erasearch_budgets, estaríamos haciendo teatro de arquitectura. Y el teatro de arquitectura se paga en latencia, en coste por token y en madrugadas depurando por qué el sistema tomó una decisión que nadie escribió.

Este artículo trata de la frontera. De qué límite concreto tiene que haberos golpeado para que multiplicar agentes deje de ser una complicación gratuita y pase a ser la respuesta correcta.

## El techo del grafo único

Empecemos por lo que sí funciona, porque el grafo de la sesión anterior no es un borrador que haya que superar. Es una arquitectura legítima que resuelve una clase entera de problemas, y muchos sistemas en producción no necesitan pasar de ahí.

Lo que hace un grafo dirigido con nodos-función es fijar el*control flow*en el código. Vosotros decidís, en tiempo de escritura, que después de extraer requisitos se clasifican componentes y que después se buscan presupuestos. Las aristas condicionales dan flexibilidad, pero la flexibilidad está acotada: son ramas que alguien previó y escribió. El modelo rellena huecos; no elige el camino.

Esa propiedad es una ventaja enorme. Un flujo determinista es predecible, barato de trazar y fácil de testear. Cuando el proceso de negocio que estáis modelando tiene una secuencia estable, y estimar software, en su forma canónica, la tiene el grafo lineal es la respuesta correcta. Empezar por multi-agente cuando el flujo es fijo es como montar una arquitectura de microservicios para un CRUD de tres tablas: no está mal por ser complejo, está mal porque la complejidad no compra nada.

El techo aparece cuando ese modelo mental deja de sostenerse. Y aparece de formas bastante reconocibles.

**El prompt de un nodo empieza a acumular reglas de dominios distintos.**Mirad el nodo que genera la estimación. Si su*system prompt*dice cómo calcular horas, y además cómo interpretar presupuestos históricos de proyectos que no encajan del todo, y además cómo ajustar por la seniority del equipo del cliente, y además cómo reaccionar si la transcripción menciona una integración con un ERP legacy... ese nodo ya no es un paso. Es un agente sobrecargado con cuatro responsabilidades peleándose dentro de una misma ventana de contexto. El síntoma clásico: tocáis una regla del prompt para arreglar un caso y se rompe otro que no tiene nada que ver. Es acoplamiento, exactamente el mismo que reconoceríais en una clase de 800 líneas.

**El conjunto de tools crece dentro de un único espacio de decisión.**Si un solo nodo tiene acceso a seis, ocho, doce herramientas, el modelo tiene que discriminar entre todas ellas en cada llamada. La tasa de elección incorrecta de tool sube con el número de opciones, igual que subiría la de un humano al que le das doce botones sin etiquetar bien. Repartir esas tools entre agentes con menos opciones cada uno no es solo higiene de seguridad: mejora la precisión.

**El orden deja de ser conocido de antemano.**Esta es la señal más definitiva, y merece detenerse. En vuestro grafo, el orden lo fijasteis vosotros. Pero imaginad una transcripción donde el cliente describe tres módulos independientes: uno es un CRUD conocido, otro es una integración con un sistema del que no hay precedente, y el tercero es una migración de datos. El camino óptimo para cada módulo es distinto. Para el CRUD basta con buscar presupuestos y calcular. Para la integración sin precedente hay que extraer requisitos con mucho más detalle, buscar por analogía, y probablemente no fiarse del resultado. Codificar todas esas ramas como aristas condicionales es posible, pero el grafo se convierte en un árbol de decisión escrito a mano que envejece mal.

Cuando quien decide qué se ejecuta a continuación deja de ser el código y pasa a ser el modelo, habéis cruzado la frontera.**Eso es lo que separa un workflow de un sistema agéntico**: no la cantidad de nodos, sino quién es dueño del control flow.

**Las responsabilidades evolucionan a ritmos distintos.**Argumento puramente de ingeniería de software, y probablemente el más familiar. Si el equipo de datos itera semanalmente sobre cómo se buscan presupuestos y el equipo de negocio toca las reglas de validación una vez al trimestre, tenerlos en el mismo nodo es un problema organizativo antes que técnico. Los ejes de cambio distintos piden componentes distintos. Esto lo lleváis aplicando toda la vida; aquí no cambia.

Mostrar imagen

Fijaos en lo que la figura*no*muestra. No hay infraestructura nueva. El estado compartido es el mismo estado tipado. Los nodos son las mismas funciones. Lo único que ha cambiado es que hay un nodo que decide y unos nodos que solo ven sus propias herramientas. Un sistema multi-agente, en la forma que os va a servir en producción, es vuestro grafo reorganizado.

## Dos formas de repartir el trabajo

Cuando la decisión de ir a multi-agente está justificada, hay una segunda decisión que la gente se salta y que determina el coste y el comportamiento del sistema entero:**¿los agentes cooperan o compiten?**

### Cooperación: cada agente aporta una pieza distinta

Es el reparto por especialización. El extractor produce requisitos, el buscador produce presupuestos análogos, el generador produce horas, el validador produce un veredicto. Ninguno hace el trabajo de otro; el resultado es la composición de todos.

Esta es la topología que tiene sentido por defecto para la estimación, y por una razón concreta:**las contribuciones son ortogonales**. Extraer requisitos de una transcripción y validar la coherencia de costes son tareas que no compiten entre sí, se necesitan. Pedirle a dos agentes que extraigan requisitos en paralelo para quedarse con el mejor sería gastar el doble para obtener, casi siempre, lo mismo.

El coste es una pasada por el flujo. El riesgo es el clásico de las cadenas: un eslabón débil contamina todo lo que viene detrás. Si el extractor se deja un requisito, ni el buscador ni el generador ni el validador tienen forma de saberlo. Ninguno vio la transcripción original con esa responsabilidad.

### Competición: varios agentes proponen y alguien sintetiza

Aquí dos o más agentes atacan**la misma tarea**con criterios distintos, y un tercero decide. En estimación el ejemplo es casi demasiado natural: un agente estima en modo conservador (asume fricción, integraciones que se tuercen, requisitos que crecen) y otro en modo agresivo (asume equipo competente y alcance estable). Un sintetizador recibe ambas propuestas y produce el resultado final.

Lo interesante no es que el sintetizador "elija la buena". Lo interesante es que**la divergencia entre las dos propuestas es información que no teníais**. Si el conservador dice 340 horas y el agresivo dice 190, esa separación os está diciendo que el proyecto tiene mucha incertidumbre estructural. Si ambos convergen en 250 y 270, el caso es predecible. En el grafo con un único estimador esa señal no existe: obtenéis un número y no sabéis cuánto confiar en él.

Mostrar imagen

La competición se paga literalmente al doble o al triple: dos generaciones más una síntesis. Y tiene una trampa sutil. Si los dos agentes que compiten comparten el mismo contexto, el mismo modelo y prompts que solo se diferencian en un adjetivo, sus salidas van a correlacionar mucho más de lo que esperáis, y estaréis pagando tres llamadas por la ilusión de una segunda opinión. La competición aporta señal**cuando los criterios divergen de verdad**: distinto prompt, distinto conjunto de evidencias, idealmente distinto modelo.

Regla de bolsillo: cooperación para descomponer trabajo; competición para atacar incertidumbre. Y no las mezcléis por defecto, porque la competición aplicada a todo os multiplica la factura sin multiplicar la calidad.

## Lo que os va a costar

Un sistema multi-agente es una decisión de arquitectura con contrapartidas reales. Merecen estar sobre la mesa antes de escribir la primera línea.

**Coste y latencia.**Cada salto de enrutado del supervisor es una llamada al modelo que no produce trabajo útil: solo decide. En una topología con supervisor central, una tarea que toque dos especialistas implica cuatro llamadas (supervisor → agente A → supervisor → agente B) donde el grafo lineal hacía dos. Estáis pagando enrutado. Puede merecer la pena; lo que no puede es que lo descubráis en la factura.

**Pérdida de contexto en las transiciones.**Cuando un agente pasa el testigo, ¿qué se lleva el siguiente? Si le pasáis todo el historial de mensajes, el contexto crece sin control y volvéis al problema que queríais evitar. Si le pasáis solo un resumen, ese resumen se convierte en un cuello de botella semántico: lo que no esté ahí, no existe para el agente que viene. No hay respuesta universal. Hay una decisión explícita que tenéis que tomar, y que ninguna librería toma bien por vosotros.

**No-determinismo en el control flow.**Es la contrapartida directa de la ventaja principal. Si el supervisor decide la ruta, dos ejecuciones sobre la misma transcripción pueden recorrer caminos distintos. Eso complica los tests, complica la reproducción de bugs y complica explicarle a un cliente por qué la estimación de ayer no coincide con la de hoy. Es gestionable, trazas, checkpoints, temperatura baja en el enrutado, tests sobre el resultado y no sobre el camino, pero es un impuesto permanente.

**Superficie de fallo mayor.**Cinco agentes son cinco sitios donde el modelo puede alucinar, cinco conjuntos de tools que pueden invocarse mal y un enrutador que puede quedarse en bucle. El grafo lineal, con toda su rigidez, tenía una propiedad valiosa: si fallaba, sabíais exactamente dónde.

**Y el coste que nadie cuenta: el cognitivo.**El siguiente desarrollador que abra el repositorio tiene que entender cinco prompts, un protocolo de enrutado y una pizarra de estado compartida, en lugar de leer cinco funciones en orden. Si el sistema no está resolviendo un problema que justifique eso, le habéis hecho un flaco favor.

### Cuándo*no*hacerlo

Sed honestos con estas tres:

- 

**Si el flujo es fijo, no necesitáis un supervisor.**Un supervisor cuya única política es "primero A, luego B, luego C" es una arista condicional cara, con una llamada al modelo de más y una fuente de aleatoriedad gratis. El grafo lineal ya expresaba eso, y mejor.

- 

**Si el problema real es un prompt malo, arreglad el prompt.**Repartir un prompt mediocre entre cuatro agentes os deja cuatro prompts mediocres y un problema de coordinación encima.

- 

**Si no tenéis observabilidad, no añadáis agentes.**Un sistema multi-agente sin trazas por nodo no es un sistema: es una caja negra con opiniones. La instrumentación no es un extra que se añade después; es la precondición para que esta arquitectura sea depurable.

## Lo que queda por decidir

Si habéis llegado hasta aquí con la sensación de que multi-agente se parece sospechosamente a lo que ya sabéis hacer, separar responsabilidades, limitar lo que cada componente puede tocar, definir contratos entre piezas, es que lo habéis entendido. No hay un paradigma nuevo. Hay una capa nueva y pequeña sobre principios que lleváis años aplicando.

Pero justificar la arquitectura es la parte fácil. Lo que queda abierto es más duro y más concreto:

Alguien tiene que**enrutar**, y ese alguien es un nodo que decide en runtime qué especialista actúa. ¿Cómo se construye para que cada una de sus decisiones sea visible y no un acto de fe? Los agentes tienen que**comunicarse**, y la forma en que lo hagan, estado compartido, testigo directo, mensajes, cambia el coste y la trazabilidad del sistema entero. Habrá casos en los que el sistema**no deba decidir solo**, y la pausa para que entre una persona no puede ser unifimprovisado: tiene que ser un estado persistido y un contrato hacia fuera. Y cada agente va a tener herramientas en la mano, lo que convierte una pregunta de arquitectura en una pregunta de**privilegio**: quién puede hacer qué, y qué pasa si intenta hacer más.

Esas cuatro preguntas, enrutado, comunicación, intervención humana y privilegio, son el resto del camino.

## Objetivo

Reorganizar el proceso de estimación como un**sistema multi-agente**: un agente supervisor que coordina agentes especializados, cada uno con acceso solo a las tools que necesita, y un punto de**intervención humana**que pausa el flujo cuando la confianza de la estimación es baja y lo reanuda con la decisión de una persona.

Todo vive dentro del**servicio IA**(Python + FastAPI). El contrato hacia el backend de negocio se mantiene, salvo la superficie nueva del human-in-the-loop.

## Contexto arquitectónico

Partes de la S13. No montas infraestructura nueva:

- 

El**estado tipado**de la S13 es tu pizarra compartida: todos los agentes leen y escriben sobre él.

- 

El**checkpointer**(AsyncPostgresSaver) de la S13 es lo que hace posible pausar y reanudar en el Nivel 2.

- 

Las**tools**son las de la S12 (search_budgets,calculate_estimate,validate_estimate). No creas tools nuevas: las**repartes**.

Idea de fondo: un sistema multi-agente aquí es tu grafo de la S13 reorganizado con un nodo que enruta y agentes que solo ven sus herramientas. Nada mágico.

## Nivel 1 (obligatorio): Supervisor + agentes especializados

Convierte el grafo lineal en una topología supervisor/workers.

Agentes y su privilegio de tools:

Agent Tools que puede usarrequirements_extractorninguna tool de negocio (solo el modelo)budget_searchersearch_budgetsestimate_generatorcalculate_estimatecoherence_validatorvalidate_estimatesupervisorninguna: solo enruta

Requisitos:

1. 

**Supervisor construido a mano**conStateGraph+Command: recibe el estado, decide el siguiente agente y consolida. Nada decreate_supervisor(queremos ver el enrutado en las trazas).

1. 

**Estado tipado**extendido desde el de la S13 (al menos un reducer acumulador para las contribuciones de los agentes).

1. 

Cada agente es una**función pura**que devuelve una actualización parcial del estado.

1. 

El endpoint**mantiene el contrato**: transcripción → estimación +status.

Firma orientativa (todo el código en inglés):

python
from typingimport Literal, Annotatedimport operatorfrom typing_extensionsimport TypedDictfrom langgraph.typesimport CommandclassEstimationState(TypedDict): transcript:str requirements:list[str] budget_matches: Annotated[list[dict], operator.add] estimate:dict|None validation:dict|None confidence:float|None status:strdefsupervisor( state: EstimationState,)-> Command[Literal["requirements_extractor","budget_searcher","estimate_generator","coherence_validator","__end__"]]:# Decide the next specialist based on the current state.# Return Command(goto=..., update={...}) so every routing decision shows up in traces....
## Nivel 2 (obligatorio): Human-in-the-loop

Añade un punto de intervención humana que pausa el grafo cuando la estimación no es fiable.

1. 

**Señal de disparo**(calcúlala en el validador o en el supervisor): la pausa se activa si se cumple alguna condición — confianza por debajo del umbral, estimación fuera del rango histórico, o transcripción sin precedente en presupuestos. Umbral por defecto configurable.

1. 

**Pausa**coninterrupt()sobre el checkpointer de la S13. El estado queda persistido en el checkpoint; la ejecución se detiene esperando decisión.

1. 

**Superficie de contrato**: cuando el grafo se pausa, el endpoint responde constatus = "awaiting_human_review"en lugar de la estimación final. Expón un endpoint de reanudación que reciba la decisión y continúe el grafo desde el checkpoint.

1. 

**Reanudación**: la decisión humana (aprobar / ajustar / rechazar) se pliega en el estado y el grafo continúa hasta el final.

Firma orientativa del lado servicio IA:

python
from langgraph.typesimport interrupt, Commanddefhuman_review_gate(state: EstimationState)-> Command:if state["confidence"]isnotNoneand state["confidence"]>= CONFIDENCE_THRESHOLD:return Command(goto="finalize") decision= interrupt({"reason":"low_confidence_estimate","estimate": state["estimate"],"confidence": state["confidence"],})return Command(goto="finalize", update={"human_decision": decision})

Lado cliente en el backend de negocio (Ruby/Rails de la referencia; cualquier cliente HTTP sirve):

ruby
# When the AI service returns status "awaiting_human_review", surface the case# to a reviewer, then resume the run with their decision.response= ai_service.post("/estimations",body:{transcript: transcript})if response["status"]=="awaiting_human_review" decision= ReviewInbox.await_decision(response["estimation_id"]) ai_service.post("/estimations/#{response['estimation_id']}/resume",body:{decision: decision})end
## Nivel 3 (ampliación) — Validación de acciones y auditoría

Para quien vaya sobrado. Prepara el terreno de seguridad del directo.

1. 

**Validación antes de ejecutar**: cada agente valida la acción que va a realizar contra su privilegio declarado; si intenta algo fuera de su conjunto de tools, se rechaza y se registra.

1. 

**Auditoría**: registra cada acción de agente (qué agente, qué tool, con qué input, con qué resultado) constructlog, de forma que una ejecución completa sea reconstruible desde el log.

## Scaffolding (si vienes flojo de la S13)

Enscaffolding/session_14/tienes el estado tipado base, un supervisor vacío con las firmas anteriores, y unsample_transcript_edge_case.txtdiseñado para disparar la baja confianza. Rellena la lógica de enrutado y de disparo; no toques el contrato del endpoint.

## Qué se defiere al directo (no entra en la entrega)

- 

**Patrón de competición**: agente conservador vs agresivo + sintetizador.

- 

**Hardening de sandboxing**: acotar acciones potencialmente destructivas más allá del mínimo privilegio básico.

- 

**Testing del flujo HITL**con varias transcripciones edge case (fuera de rango, sin precedente).

## Cómo entregar

Sube la ramasession-14/pre-workcon el sistema multi-agente implementado.

Envía por mail a[lia@lidr.co](mailto:lia@lidr.co)el enlace a la rama (URL completa de GitHub) y el enlace a la traza de una ejecución que dispare la pausa humana sobresample_transcript_edge_case.txt, al menos dos días antes de la sesión en vivo. Las entregas posteriores no entran en la revisión grupal del inicio del directo.

La rama debe:

- 

Ejecutar de principio a fin sin errores

- 

Contener los Niveles 1 y 2 completos: supervisor construido a mano con enrutado visible en traza, agentes con mínimo privilegio de tools, estado tipado con reducer acumulador, pausa humana persistida en checkpoint y endpoint de reanudación funcionando

- 

Ser accesible (repositorio público o con permisos)

## Criterios de "hecho"

- 

El supervisor está construido a mano conStateGraph+Command; cada decisión de enrutado aparece en la traza.

- 

Cada agente accede**solo**a sus tools (mínimo privilegio); el extractor no usa ninguna tool de negocio.

- 

El estado es tipado, extendido desde el de la S13, con al menos un reducer acumulador.

- 

El grafo corre de principio a fin y el endpoint devuelve la estimación con sustatus; el contrato hacia el backend de negocio es el de siempre.

- 

La pausa humana se dispara con la señal de confianza y persiste en el checkpoint; el endpoint devuelvestatus = "awaiting_human_review".

- 

El endpoint de reanudación continúa el grafo desde el checkpoint con la decisión humana en el estado.

- 

Existe una traza completa de una ejecución que pasa por la pausa y se reanuda.

## Documentación de referencia

- 

LangGraph — multi-agente (supervisor, swarm, subgrafos):https://docs.langchain.com/oss/python/langgraph/multi-agent

- 

LangGraph —Commandy enrutado:https://docs.langchain.com/oss/python/langgraph/graph-api

- 

LangGraph — human-in-the-loop einterrupt:https://docs.langchain.com/oss/python/langgraph/human-in-the-loop

- 

LangGraph — persistencia y checkpointers (Postgres):https://docs.langchain.com/oss/python/langgraph/persistence
