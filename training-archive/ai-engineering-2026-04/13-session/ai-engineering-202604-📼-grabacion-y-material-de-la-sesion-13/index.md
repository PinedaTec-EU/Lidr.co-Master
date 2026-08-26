---
title: "📼 Grabación y material de la sesión 13"
source_url: "https://training.lidr.co/posts/ai-engineering-202604-%F0%9F%93%BC-grabacion-y-material-de-la-sesion-13"
archived_at: "2026-07-22T16:22:55.786Z"
group: "13-session"
---

# 📼 Grabación y material de la sesión 13

![Antonio Perez](./assets/c3eccac37426c36f.jpg)

[Antonio Perez](https://training.lidr.co/members/36030888)

## Video

[Video](https://player.vimeo.com/video/1210814198?h=924773b9d8)

#### Diapositivas
[Sesi_n_13_slides.pdf](https://media2-production.mightynetworks.com/asset/20ef388c-a1ac-4957-907c-b9a20415586f/Sesi_n_13_slides.pdf)

Ya tenéis disponible la grabación de la sesión 13. Antes de verla (o mientras la repasáis), os dejamos algunas aclaraciones y recursos que os van a servir para aprovecharla mejor.

### 1⃣Sobre el ejercicio y el temario

Si preparasteis el pre-work de "Orquestación de agentes" y esperabais LangGraph en esta sesión: la sesión 13 se centró en**cuándo y dónde conviene usar un agente dentro de un flujo ya construido**, antes de entrar en la orquestación multiagente propiamente dicha. Antonio confirmó en vivo que LangGraph, StateGraph, checkpointers y la orquestación con varios agentes se ven en las próximas dos sesiones. Si ya adelantasteis ese contenido, no se pierde: se retoma ahí.

### 2⃣Las 4 reglas de arquitectura que dejó Antonio

Vale la pena anotarlas, porque van a ser la base de las próximas sesiones:

- 

Un agente se justifica solo donde aporta valor real (ambigüedad, criterio, síntesis). Si el paso ya es determinista y funciona (por ejemplo, una búsqueda vectorial), no metas un agente ahí: solo se suma coste, latencia y menos control.

- 

Máximo 2 niveles de jerarquía de agentes (un agente que orquesta a otro). Más de eso, para Antonio, suele ser señal de que el problema está mal planteado.

- 

Aislar el contexto de cada agente: no reutilizar el mismo agente cambiándole de tarea a mitad de conversación ("ponerle otro sombrero"). Si necesitás que haga dos cosas distintas, son dos agentes distintos, cada uno con su propio prompt y su propia ventana de contexto.

- 

El agente se adapta a los modelos de datos de tu aplicación, nunca al revés. Incorporar un agente no debería romper los contratos ni la estructura de datos que ya tenías.

### 3⃣Por qué las trazas (traces) son obligatorias

Una traza no es un log, es el registro de qué decidió el agente, con qué herramienta y por qué. Sin trazas es imposible auditar o mejorar un agente, porque un agente puede ejecutar decenas de pasos en segundos (en el ejemplo de la clase, uno de 47 pasos) y ningún humano puede revisar eso a ojo. Si estás armando tu propio agente para el ejercicio, asegurate de que cada paso quede registrado con: el paso, el razonamiento, la acción/tool usada y el resultado (observación).

### 4⃣Aclaración importante: el "score de fiabilidad"

Si en vuestra estimación ven un porcentaje de fiabilidad y se preguntan de dónde sale: hoy ese número**es la distancia coseno de la búsqueda vectorial, mostrada como porcentaje**(si la distancia es 0,55, el sistema muestra 55%). No es todavía una evaluación cualitativa hecha por el agente. Se reconoció como una simplificación de esta primera iteración y adelantó que más adelante habrá un agente dedicado a calcular ese score de forma más completa. Tenlo en cuenta antes de sacar conclusiones sobre la calidad de una estimación solo por ese número.

### 5⃣Preguntas que quedaron respondidas en la sesión

- 

*¿Cómo se decide cuál es la "división óptima" de tareas entre agentes?*No hay una fórmula fija: se ajusta con la práctica. Un criterio útil es que un agente sintetice información y se la pase ya resumida a otro, en vez de que ambos compartan toda la conversación, así se reduce contexto y coste.

- 

*¿El formato de los esquemas de tools cambia según el proveedor (OpenAI vs. Anthropic)?*Está bastante estandarizado, aunque puede variar levemente entre proveedores. Si te da dudas en tu implementación, una alternativa válida es definir dos esquemas de tools y usar el que corresponda según el modelo.

- 

*¿Tiene sentido combinar tools propias con servidores MCP?*Sí. Antonio prefiere usar API directa para integraciones internas (más control de permisos) y reserva MCP para casos de documentación pública o entornos totalmente controlados, ya que el punto débil de MCP hoy es la seguridad y el control de permisos.
