---
title: "Sesión 16. Puesta en producción II - Calidad y observabilidad — 77 min"
source_url: "https://training.lidr.co/posts/ai-engineering-202604-sesion-16-puesta-en-produccion-ii-calidad-y-observabilidad-77-min"
archived_at: "2026-08-26T16:26:43.670Z"
group: "16-session"
---

# Sesión 16. Puesta en producción II - Calidad y observabilidad — 77 min
[

![image](./assets/DGM0LPkWaen-eHycAp8Bi_33154bad111b478d8b822b2d98058d8c.jpg)

![image](./assets/c3eccac37426c36f.jpg)

2 Mentors](https://training.lidr.co/posts/ai-engineering-202604-sesion-16-puesta-en-produccion-ii-calidad-y-observabilidad-77-min/instructors)

⏳Tiempo estimado: 2 min

[Video](https://player.vimeo.com/video/1200715792?h=d4075ef446)

Tu RAG ya funciona: recupera presupuestos parecidos a lo que buscas. Pero parecido no es lo mismo que útil, y cuando el sistema te devuelve una app de pagos al pedirle una plataforma de e-commerce, estás a un paso de una mala estimación. En esta sesión convertimos una recuperación aceptable en una recuperación precisa — y lo demostramos con números, no con sensaciones.

**En esta sesión descubrirás:**

→ Por qué la búsqueda vectorial ordena mal los resultados finos y cómo el reranking con cross-encoders reordena los candidatos leyendo consulta y documento juntos

→ Cómo combinar búsqueda semántica y búsqueda por palabras exactas con full-text search en PostgreSQL, y cómo fusionar ambos rankings con Reciprocal Rank Fusion

→ Cómo medir con un golden set propio si cada técnica compensa su coste en latencia, antes de llevarla a producción

→ Cómo descomponer consultas complejas en sub-búsquedas y dirigir cada una al índice correcto mediante routing

→ Cómo el filtrado por metadatos y el decaimiento temporal evitan que un presupuesto obsoleto contamine tus estimaciones

Para finalizar, añade tu opinión sobre el contenido y el ejercicio de este módulo:
🆙Evalúa el contenido y el ejercicio de este Módulo

### 
❗Obtén los recursos completos en las siguientes lecciones👇

- 

![image](./assets/default_header_10-890fb563acf29a72599952197f03937504db0f59f25b84895b429a363ddaa9ac.jpg)

![image](./assets/default_header_10-890fb563acf29a72599952197f03937504db0f59f25b84895b429a363ddaa9ac-2.jpg)

[✍️Golden set de producción 🔴

- Visibility: Visible
- Unlocking: None
- Completion: Button
- Comments: On
- Thumbnail: Default
](https://training.lidr.co/posts/ai-engineering-202604-✍️golden-set-de-produccion-🔴)⏳ Tiempo estimado: 5 min 🚨 La fecha límite: martes 25 de agosto a las 23:59 de tu hora local Contexto Tras la Sesión...
- 

![image](./assets/articulo-16-1-diagrama-determinista-vs-no.png)

![image](./assets/articulo-16-1-diagrama-determinista-vs-no-2.png)

[📄 Introducción LLMOps 🔴 — 11 min

- Visibility: Visible
- Unlocking: None
- Completion: Button
- Comments: On
- Thumbnail: Default
](https://training.lidr.co/posts/ai-engineering-202604-📄-introduccion-llmops-🔴-11-min)⏳ Tiempo estimado: 11 min Cerrasteis la sesión anterior con una pequeña victoria legítima: el sistema de estimación...
- 

![image](./assets/articulo-16-2-diagrama-guardrails.png)

![image](./assets/articulo-16-2-diagrama-guardrails-2.png)

[📄 Un sistema debe saber decir “No lo sé” 🔴 — 14 min

- Visibility: Visible
- Unlocking: None
- Completion: Button
- Comments: On
- Thumbnail: Default
](https://training.lidr.co/posts/ai-engineering-202604-📄-un-sistema-debe-saber-decir-no-lo-se-🔴-14-min)⏳ Tiempo estimado: 14 min Imaginad una petición cualquiera de las que le llegan a vuestro sistema en producción. Un...
- 

![image](./assets/articulo-16-3-diagrama-golden-set.png)

![image](./assets/articulo-16-3-diagrama-golden-set-2.png)

[📄 Evaluacion en producción 🔴 — 13 min

- Visibility: Visible
- Unlocking: None
- Completion: Button
- Comments: On
- Thumbnail: Default
](https://training.lidr.co/posts/ai-engineering-202604-📄-evaluacion-en-produccion-🔴-13-min)⏳ Tiempo estimado: 13 min Cambiáis una palabra en el prompt de estimación. Lanzáis tres o cuatro transcripciones de...
- 

![image](./assets/articulo-16-4-diagrama-regresion.png)

![image](./assets/articulo-16-4-diagrama-regresion-2.png)

[📄 Tratamiento de regresiones 🔴 — 12 min

- Visibility: Visible
- Unlocking: None
- Completion: Button
- Comments: On
- Thumbnail: Default
](https://training.lidr.co/posts/ai-engineering-202604-📄-tratamiento-de-regresiones-🔴-12-min)⏳ Tiempo estimado: 12 min Un usuario se queja: las estimaciones para tareas de autenticación se le quedan cortas....
- 

![image](./assets/articulo-16-5-diagrama-dashboard.png)

![image](./assets/articulo-16-5-diagrama-dashboard-2.png)

[📄 Observabilidad 🔴 — 12 min

- Visibility: Visible
- Unlocking: None
- Completion: Button
- Comments: On
- Thumbnail: Default
](https://training.lidr.co/posts/ai-engineering-202604-📄-observabilidad-🔴-12-min)⏳ Tiempo estimado: 12 min El golden set está en verde. La última evaluación fue buena, los KPIs aguantan, el...
- 

![image](./assets/articulo-16-6-diagrama-modelo-cache.png)

![image](./assets/articulo-16-6-diagrama-modelo-cache-2.png)

[📄Coste, latencia y A/B Testing 🔴 — 13 min

- Visibility: Visible
- Unlocking: None
- Completion: Button
- Comments: On
- Thumbnail: Default
](https://training.lidr.co/posts/ai-engineering-202604-📄coste-latencia-y-ab-testing-🔴-13-min)⏳ Tiempo estimado: 13 min La observabilidad del artículo anterior os ha puesto delante la factura y el reloj: ahora...
- 

![image](./assets/articulo-16-7-diagrama-donde-vive.png)

![image](./assets/articulo-16-7-diagrama-donde-vive-2.png)

[📄Modelos en local 🔴 — 14 min

- Visibility: Visible
- Unlocking: None
- Completion: Button
- Comments: On
- Thumbnail: Default
](https://training.lidr.co/posts/ai-engineering-202604-📄modelos-en-local-🔴-14-min)⏳ Tiempo estimado: 14 min Durante toda la sesión, cuando el servicio IA ha necesitado un modelo, ha hecho lo mismo:...
- 

![image](./assets/default_header_4-de4f3d8e600083d23109949668b79ee6f45ed38bb1de63dd002c537db52671a6.jpg)

![image](./assets/default_header_4-de4f3d8e600083d23109949668b79ee6f45ed38bb1de63dd002c537db52671a6-2.jpg)

[🆙 Evalúa el contenido de este Módulo

- Visibility: Visible
- Unlocking: None
- Completion: None
- Comments: On
- Thumbnail: Default
](https://training.lidr.co/posts/ai-engineering-202604-🆙-evalua-el-contenido-de-este-modulo-105244643)Evalúa del 1 al 5 el valor aportado por el contenido del módulo actual. Si al enviar la encuesta te aparece algún...
Explore More Posts[Previous🆙 Evalúa el contenido de este Módulo](https://training.lidr.co/posts/ai-engineering-202604-🆙-evalua-el-contenido-de-este-modulo-98724399)[Next✍️Golden set de producción 🔴](https://training.lidr.co/posts/ai-engineering-202604-✍️golden-set-de-produccion-🔴)
