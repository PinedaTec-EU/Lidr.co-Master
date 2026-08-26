---
title: "Sesión 12: Introducción a agentes de IA — 123 min"
source_url: "https://training.lidr.co/posts/ai-engineering-202604-sesion-12-introduccion-a-agentes-de-ia-123-min"
archived_at: "2026-07-22T16:22:25.615Z"
group: "12-session"
---

# Sesión 12: Introducción a agentes de IA — 123 min

![Antonio Perez](./assets/c3eccac37426c36f.jpg)

[Antonio Perez](https://training.lidr.co/members/36030888)

⏳Tiempo estimado: 1 min

[Video](https://player.vimeo.com/video/1200715792?h=d4075ef446)

Tu RAG ya funciona: recupera presupuestos parecidos a lo que buscas. Pero parecido no es lo mismo que útil, y cuando el sistema te devuelve una app de pagos al pedirle una plataforma de e-commerce, estás a un paso de una mala estimación. En esta sesión convertimos una recuperación aceptable en una recuperación precisa y lo demostramos con números, no con sensaciones.

**En esta sesión descubrirás:**

→ Por qué la búsqueda vectorial ordena mal los resultados finos y cómo el reranking con cross-encoders reordena los candidatos leyendo consulta y documento juntos

→ Cómo combinar búsqueda semántica y búsqueda por palabras exactas con full-text search en PostgreSQL, y cómo fusionar ambos rankings con Reciprocal Rank Fusion

→ Cómo medir con un golden set propio si cada técnica compensa su coste en latencia, antes de llevarla a producción

→ Cómo descomponer consultas complejas en sub-búsquedas y dirigir cada una al índice correcto mediante routing

→ Cómo el filtrado por metadatos y el decaimiento temporal evitan que un presupuesto obsoleto contamine tus estimaciones

Al finalizar, recuerda añadir tu opinión sobre el contenido y el ejercicio de este módulo:
🆙Evalúa el contenido y el ejercicio de este Módulo

### 
❗Obtén los recursos👇

- 

![image](./assets/default_header_10-890fb563acf29a72599952197f03937504db0f59f25b84895b429a363ddaa9ac.jpg)

![image](./assets/default_header_10-890fb563acf29a72599952197f03937504db0f59f25b84895b429a363ddaa9ac-2.jpg)

[✍️ Ejercicio: Introducción a agentes de IA🔴

- Visibility: Visible
- Unlocking: None
- Completion: Button
- Comments: On
- Thumbnail: Default
](https://training.lidr.co/posts/ai-engineering-202604-✍️-ejercicio-introduccion-a-agentes-de-ia🔴)⏱ La fecha límite es Martes 7 de Julio, al final del día. El sistema de estimación que venimos construyendo funciona...
- 

![image](./assets/S12-fig-01-pipeline-vs-agente.jpg)

![image](./assets/S12-fig-01-pipeline-vs-agente-2.jpg)

[📄 De pipeline a agente: cuándo tu sistema RAG necesita una capa de decisión 🔴 — 23 min

- Visibility: Visible
- Unlocking: None
- Completion: Button
- Comments: On
- Thumbnail: Default
](https://training.lidr.co/posts/ai-engineering-202604-📄-de-pipeline-a-agente-cuando-tu-sistema-rag-necesita-una-capa-de-decision-🔴-23-min)⏳ Tiempo estimado: 23 min Nuestro sistema de estimación funciona. Le pasas una transcripción de reunión, reformula la...
- 

![image](./assets/S12-fig-02a-anatomia-bucle.jpg)

![image](./assets/S12-fig-02a-anatomia-bucle-2.jpg)

[📄 Anatomía de un agente: qué ocurre dentro del bucle 🔴 — 22 min

- Visibility: Visible
- Unlocking: None
- Completion: Button
- Comments: On
- Thumbnail: Default
](https://training.lidr.co/posts/ai-engineering-202604-📄-anatomia-de-un-agente-que-ocurre-dentro-del-bucle-🔴-22-min)⏳ Tiempo estimado: 22 min Un agente, reducido a su forma más honesta, es un bucle: el modelo decide una acción, tu...
- 

![image](./assets/S12-fig-03a-contrato-function-calling.jpg)

![image](./assets/S12-fig-03a-contrato-function-calling-2.jpg)

[📄 Function calling en la práctica: tools, schemas y contrato con el modelo🔴 — 21 min

- Visibility: Visible
- Unlocking: None
- Completion: Button
- Comments: On
- Thumbnail: Default
](https://training.lidr.co/posts/ai-engineering-202604-📄-function-calling-en-la-practica-tools-schemas-y-contrato-con-el-modelo🔴-21-min)⏳ Tiempo estimado: 21 min Un agente que solo razona no sirve de mucho. Para estimar un proyecto necesita hacer cosas:...
- 

![image](./assets/S12-fig-04a-ejecucion-bucle.jpg)

![image](./assets/S12-fig-04a-ejecucion-bucle-2.jpg)

[📄 El bucle agéntico paso a paso🔴 — 18 min

- Visibility: Visible
- Unlocking: None
- Completion: Button
- Comments: On
- Thumbnail: Default
](https://training.lidr.co/posts/ai-engineering-202604-📄-el-bucle-agentico-paso-a-paso🔴-18-min)⏳ Tiempo estimado: 18 min Vamos a construir el agente a mano. Sin LangChain, sin ningún framework de orquestación. No...
- 

![image](./assets/S12-fig-05a-ejes-de-patrones.jpg)

![image](./assets/S12-fig-05a-ejes-de-patrones-2.jpg)

[📄 Patrones de agentes y diseño de tools de calidad 🔴 — 21 min

- Visibility: Visible
- Unlocking: None
- Completion: Button
- Comments: On
- Thumbnail: Default
](https://training.lidr.co/posts/ai-engineering-202604-📄-patrones-de-agentes-y-diseno-de-tools-de-calidad-🔴-21-min)⏳ Tiempo estimado: 21 min "Agente" no es una cosa. Bajo esa palabra caben formas muy distintas de resolver un...
- 

![image](./assets/S12-fig-06a-coste-por-vuelta.jpg)

![image](./assets/S12-fig-06a-coste-por-vuelta-2.jpg)

[📄 Cuánto cuesta un agente🔴 — 18 min

- Visibility: Visible
- Unlocking: None
- Completion: Button
- Comments: On
- Thumbnail: Default
](https://training.lidr.co/posts/ai-engineering-202604-📄-cuanto-cuesta-un-agente🔴-18-min)⏳ Tiempo estimado: 18 min Un agente hace el mismo trabajo que un pipeline producir una estimación a partir de una...
- 

![image](./assets/default_header_9-526c01a8bc9398cff8c25e2432d3b3836bf0d1a6ecf75c71a802f10919117bcb.jpg)

![image](./assets/default_header_9-526c01a8bc9398cff8c25e2432d3b3836bf0d1a6ecf75c71a802f10919117bcb-2.jpg)

[🆙 Evalúa el contenido de este Módulo

- Visibility: Visible
- Unlocking: None
- Completion: None
- Comments: On
- Thumbnail: Default
](https://training.lidr.co/posts/ai-engineering-202604-🆙-evalua-el-contenido-de-este-modulo-104106618)Evalúa del 1 al 5 el valor aportado por el contenido del módulo actual. Si al enviar la encuesta te aparece algún...
