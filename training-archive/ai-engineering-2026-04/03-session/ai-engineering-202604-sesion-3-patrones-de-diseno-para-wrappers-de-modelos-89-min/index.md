---
title: "Sesión 3: Patrones de diseño para wrappers de modelos — 89 min"
source_url: "https://training.lidr.co/posts/ai-engineering-202604-sesion-3-patrones-de-diseno-para-wrappers-de-modelos-89-min"
archived_at: "2026-06-12T09:08:36.817Z"
group: "03-session"
---

# Sesión 3: Patrones de diseño para wrappers de modelos — 89 min

![Antonio Perez](./assets/c3eccac37426c36f.jpg)

[Antonio Perez](https://training.lidr.co/members/36030888)

⏳Tiempo estimado: 1 min

¡Hola!

En la sesión anterior construiste un sistema funcional basado en CAG. Tenías un endpoint que respondía, entendías cómo gestionar el contexto y empezabas a tomar decisiones de arquitectura.

Ahora toca dar el siguiente paso.

En esta sesión vas a transformar ese prototipo en algo que empieza a parecer un producto real.

Porque en el mundo real, no basta con que “funcione”. Tiene que ser robusto, eficiente, observable y usable por otros.

Durante la sesión trabajarás sobre varias capas clave que aparecen en cualquier sistema con LLMs en producción: abstraer proveedores para evitar dependencias rígidas, optimizar el rendimiento evitando llamadas innecesarias, mejorar la experiencia del usuario con respuestas en tiempo real y entender qué está pasando en cada llamada al modelo.

Además, añadirás una interfaz conversacional que elimina la necesidad de herramientas técnicas como Postman o curl, acercando tu sistema a un entorno de uso real.

Este es el punto en el que tu sistema deja de ser un experimento técnico y empieza a comportarse como un producto.

**Contenidos obligatorios**🔴
🎥Introducción: De prototipo a producto
🗒Interfaces conversacionales, frameworks y librerías
🗒Abstracción de proveedores y estrategias de fallback
🗒Cacheo inteligente de respuestas
🗒Streaming y manejo de respuestas largas
🗒Observabilidad, logging y trazabilidad

**Ejercicios prácticos**✍
✍Interfaz conversacional con Streamlit para el Proyecto 1

Para finalizar, añade tu opinión sobre el contenido de este módulo:
🆙Evalúa el contenido de este Módulo

### 
❗Obtén los recursos completos en las siguientes lecciones👇

- 

![image](./assets/2152586640-d68b588a4e933211b636a42464ad91a37c7f6bfabbb1d7e0d0a37b65866c1d17-d_1280.jpg)

![image](./assets/2152586640-d68b588a4e933211b636a42464ad91a37c7f6bfabbb1d7e0d0a37b65866c1d17-d_1280-2.jpg)

[🎥 Introducción: De prototipo a producto: wrappers, streaming y trazabilidad 🔴 — 3 min

- Visibility: Visible
- Unlocking: None
- Completion: Button
- Comments: On
- Thumbnail: Default
](https://training.lidr.co/posts/ai-engineering-202604-🎥-introduccion-de-prototipo-a-producto-wrappers-streaming-y-trazabilidad-🔴-3-min)⏳ Tiempo estimado: 3 min En la sesión 02 dejamos el Proyecto 1 con un endpoint CAG funcional. En esta sesión lo...
- 

![image](./assets/default_header_6-83bf10e1beb19f6de0f2cf99a92a0eeafcab7362c5efd3312f5213733a044658.jpg)

![image](./assets/default_header_6-83bf10e1beb19f6de0f2cf99a92a0eeafcab7362c5efd3312f5213733a044658-2.jpg)

[✍️ Ejercicio - Wrapper de interfaz conversacional 🔴

- Visibility: Visible
- Unlocking: None
- Completion: Button
- Comments: On
- Thumbnail: Default
](https://training.lidr.co/posts/ai-engineering-202604-✍️-ejercicio-wrapper-de-interfaz-conversacional-🔴)Interfaz conversacional con Streamlit para el Proyecto 1 Objetivo Añadir una interfaz conversacional web al Proyecto...
- 

![image](./assets/d53fca2c9d611a91.png)

![image](./assets/d53fca2c9d611a91-2.png)

[📄 Interfaces conversacionales, frameworks y librerías 🔴— 13 min

- Visibility: Visible
- Unlocking: None
- Completion: Button
- Comments: On
- Thumbnail: Default
](https://training.lidr.co/posts/ai-engineering-202604-📄-interfaces-conversacionales-frameworks-y-librerias-🔴-13-min)⏳ Tiempo estimado: 13 min El problema que resuelven estos frameworks Tienes un endpoint que recibe texto y devuelve...
- 

![image](./assets/default_header_2-b21b4bc82a7b9ce22d87f6130c94965ea67a9ff44e4e3a3157f7ebc7948b9270.jpg)

![image](./assets/default_header_2-b21b4bc82a7b9ce22d87f6130c94965ea67a9ff44e4e3a3157f7ebc7948b9270-2.jpg)

[📄 Abstracción de proveedores y estrategias de fallback 🔴 — 20 min

- Visibility: Visible
- Unlocking: None
- Completion: Button
- Comments: On
- Thumbnail: Default
](https://training.lidr.co/posts/ai-engineering-202604-📄-abstraccion-de-proveedores-y-estrategias-de-fallback-🔴-20-min)⏳ Tiempo estimado: 20 min El problema: acoplamiento a un proveedor En la sesión 02 montamos un endpoint FastAPI que...
- 

![image](./assets/default_header_4-de4f3d8e600083d23109949668b79ee6f45ed38bb1de63dd002c537db52671a6.jpg)

![image](./assets/default_header_4-de4f3d8e600083d23109949668b79ee6f45ed38bb1de63dd002c537db52671a6-2.jpg)

[📄 Cacheo inteligente de respuestas de LLMs 🔴 — 19 min

- Visibility: Visible
- Unlocking: None
- Completion: Button
- Comments: On
- Thumbnail: Default
](https://training.lidr.co/posts/ai-engineering-202604-📄-cacheo-inteligente-de-respuestas-de-llms-🔴-19-min)⏳ Tiempo estimado: 19 min Por qué cachear respuestas de un LLM En el Proyecto 1, nuestro estimador de software recibe...
- 

![image](./assets/default_header_5-c2b477a36512c3a4627ed52ccbc0e62f4fb4a5e010a2da6c65979aa5b4c816ac.jpg)

![image](./assets/default_header_5-c2b477a36512c3a4627ed52ccbc0e62f4fb4a5e010a2da6c65979aa5b4c816ac-2.jpg)

[📄 Streaming y manejo de respuestas largas 🔴 — 18 min

- Visibility: Visible
- Unlocking: None
- Completion: Button
- Comments: On
- Thumbnail: Default
](https://training.lidr.co/posts/ai-engineering-202604-📄-streaming-y-manejo-de-respuestas-largas-🔴-18-min)⏳ Tiempo estimado: 18 min El problema de la respuesta monolítica Cuando nuestro estimador de software del Proyecto 1...
- 

![image](./assets/default_header_6-83bf10e1beb19f6de0f2cf99a92a0eeafcab7362c5efd3312f5213733a044658.jpg)

![image](./assets/default_header_6-83bf10e1beb19f6de0f2cf99a92a0eeafcab7362c5efd3312f5213733a044658-2.jpg)

[📄 Observabilidad, logging y trazabilidad 🔴 — 16 min

- Visibility: Visible
- Unlocking: None
- Completion: Button
- Comments: On
- Thumbnail: Default
](https://training.lidr.co/posts/ai-engineering-202604-📄-observabilidad-logging-y-trazabilidad-🔴-16-min)⏳ Tiempo estimado: 16 min Por qué el logging estándar no es suficiente Si vienes de desarrollo web, tienes un hábito...
- 

![image](./assets/default_header_3-268b66a85721efdf8a53ad2dea20ca2f6c6f252491a7c3f60aa140a6d9b7cce0.jpg)

![image](./assets/default_header_3-268b66a85721efdf8a53ad2dea20ca2f6c6f252491a7c3f60aa140a6d9b7cce0-2.jpg)

[🆙 Evalúa el contenido y el ejercicio de este Módulo

- Visibility: Visible
- Unlocking: None
- Completion: None
- Comments: On
- Thumbnail: Default
](https://training.lidr.co/posts/ai-engineering-202604-🆙-evalua-el-contenido-y-el-ejercicio-de-este-modulo-98724212)Evalúa del 1 al 5 el valor aportado por el contenido de este módulo. ⚠ Importante: Debido a una limitación técnica de...
