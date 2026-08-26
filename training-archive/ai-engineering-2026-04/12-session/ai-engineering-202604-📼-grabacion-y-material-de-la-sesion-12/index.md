---
title: "📼 Grabación y material de la sesión 12"
source_url: "https://training.lidr.co/posts/ai-engineering-202604-%F0%9F%93%BC-grabacion-y-material-de-la-sesion-12"
archived_at: "2026-07-22T16:22:23.506Z"
group: "12-session"
---

# 📼 Grabación y material de la sesión 12

![Antonio Perez](./assets/c3eccac37426c36f.jpg)

[Antonio Perez](https://training.lidr.co/members/36030888)

¡Muchas gracias por tu participación en esta gran sesión de IA4Devs!

Obtén las diapositivas y la grabación a continuación👇

## **Grabación disponible**

[Video](https://player.vimeo.com/video/1208601087?h=cc546b749f)

## **Diapositivas**
[Sesio_n_12.pdf](https://media2-production.mightynetworks.com/asset/cb52252f-3b3a-4096-bfe9-783dc05f32a2/Sesio_n_12.pdf)

## **Qué cubrimos en la sesión**

**Parte 1: El problema del One Shot con agentes**

- 

El ejercicio estaba planteado para resolverse en one shot — un solo agente generando toda la estimación — y muchos estudiantes ya detectaron que ese no es el approach correcto

- 

Meter un agente que decida cuándo llama al RAG y cuándo no da un paso atrás: los resultados son menos consistentes que el flujo determinista que ya teníamos (ejemplo: 3.600 horas de estimación con 6 pasos y referencias cruzadas sin control)

- 

Principio clave: arquitectura agéntica no significa mejor. Un agente tiene que estar acotado, especializado, y su valor tiene que estar claro antes de implementarlo — no se mete agente porque sí

**Parte 2: Dónde entra el agente y dónde no**

- 

El flujo se mantiene exactamente igual: transcripción → reformulación → estructura de módulos/tareas (Fase 1) → revisión humana → estimación de horas por tarea (Fase 2) → revisión humana final

- 

El agente interviene solo en Fase 1 (generación de estructura) y Fase 2 (análisis de resultados problemáticos del RAG) — las puertas humanas quedan intactas

- 

La búsqueda vectorial es determinista: misma query siempre devuelve los mismos resultados — meter un agente ahí solo añade ruido, latencia y coste

- 

El agente no rompe los contratos: la lógica de negocio y los modelos de datos se mantienen igual; el agente se adapta a la estructura de la aplicación, no al revés

- 

Costes reales de los agentes: latencia, precio por llamada, complejidad y pérdida de control — hay que estar muy seguro de que aportan valor antes de incluirlos

**Parte 3: Anatomía del bucle agéntico**

- 

El agente (llamado "Neo" en la demo) tiene dos endpoints acotados: generación de estructura y cálculo de horas — dos llamadas separadas con contextos independientes

- 

En Fase 1 el agente trabaja sin tools: genera la estructura de módulos y tareas en un solo step usando el modelo de razonamiento (GPT-5 en la demo), sin necesidad de bucle

- 

En Fase 2 el agente sí aplica el patrón ReAct completo: recibe las tareas ya recuperadas por el RAG determinista, las analiza, flagea las problemáticas (sin datos, con discrepancias, con fiabilidad baja) y solo sobre esas ejecuta el bucle agéntico con llamadas al modelo

- 

Resultado: en la demo el agente ejecutó 47-58 pasos en 1-2 minutos detectando todas las tareas sin datos, discrepancias de scope y conflictos de estimación entre vecinos

**Parte 4: Trazas — la herramienta de control del agente**

- 

Una traza no es un log: es la información de qué decidió el agente, cómo llegó a esa decisión y qué tools utilizó en cada paso

- 

Estructura de cada step: resumen de razonamiento, acción tomada, tools usadas con sus argumentos, y observación del resultado

- 

Las trazas son ultra-importantes para auditar y mejorar agentes — sin trazas es imposible controlar qué está haciendo un sistema que toma decisiones en decenas de pasos

- 

En producción las trazas no las puede gestionar un humano: hay que tener un agente específico que las evalúe; en desarrollo sí son legibles manualmente

- 

Almacenamiento en producción: las trazas deben ir a un backend de S3 o similar en formato estructurado (Markdown, JSON), no a base de datos como objeto

**Parte 5: Tools — diseño y funcionamiento**

- 

Las tools no son para la aplicación sino para el modelo: se definen con tipo, nombre, descripción y parámetros tipados, y el propio agente decide cuándo usarlas

- 

La descripción de una tool es casi un prompt — define qué hace y cuándo tiene sentido usarla; hay que ser muy específico

- 

Las tres tools del caso de uso:search_budgets(busca tareas análogas en histórico),derive_task(analiza fiabilidad y dispersión de vecinos),validate_estimate(sanity check / guardrails sobre horas recuperadas)

- 

Se pueden mezclar tools propias con tools genéricas del proveedor (websearch, filesystem) en el mismo array — el patrón es flexible

- 

Los prompts del agente deben estar versionados fuera del código, organizados por agente, preferiblemente con Jinja2 si son dinámicos

**Parte 6: Orquestación — lo que viene**

- 

Lo correcto para este caso sería tener dos agentes distintos con handover entre ellos, cada uno con su propio contexto, sus propias tools y sus propios prompts — en esta sesión se unificaron en uno por simplicidad pedagógica

- 

Regla práctica: máximo dos niveles de profundidad en jerarquía de agentes — a partir del tercer nivel el efecto "teléfono descompuesto" hace el sistema ineficiente e inauditable

- 

El handover entre agentes con contexto sintetizado es más barato que seguir iterando dentro de la misma conversación con contexto completo creciente

- 

Siempre de menos a más: empezar con un agente que haga pocas cosas bien, añadir otro solo cuando el primero funciona de forma estable

- 

MCP servers: útiles pero con precaución — su punto débil es seguridad y control de permisos; preferible usar APIs propias salvo que el entorno esté totalmente controlado

**Preguntas del chat + respuestas**

**P: ¿Un agente es básicamente una función recursiva con acceso a tools?**→ Sí. El bucle agéntico es eso: una función que se repite comprobando en cada iteración si tiene que salir (condición de break) para evitar deriva infinita. Un agente que entra en bucle infinito intentando usar una tool rota es un agente mal hecho.

**P: ¿Cómo se acota qué decide el agente y qué no?**→ Con endpoints separados. Cada endpoint define el alcance exacto del agente: generación de estructura en uno, estimación de horas en otro. Lo que queda fuera del endpoint, el agente no lo toca.

**P: ¿Por qué dos prompts para el mismo agente en lugar de uno genérico?**→ En realidad deberían ser dos agentes distintos. En la sesión se unificó por simplificar. Mezclar roles en un solo agente con contexto compartido hace que empiece a mezclar información entre tareas.

**P: ¿Los prompts del agente conviene versionarlos aparte?**→ Sí, siempre. Lo correcto es sacarlos del código, organizarlos por carpeta de agente, y usar sistemas de plantillas (Jinja2) si son dinámicos.

**P: ¿Cuál es la división óptima entre agentes?**→ La da la experiencia, pero el criterio es: cada agente autosuficiente con el contexto mínimo necesario. Pasar contexto sintetizado entre agentes es más barato que ampliar el contexto dentro del mismo. Más de dos niveles jerárquicos es señal de que algo está mal diseñado.

**P: ¿El porcentaje de fiabilidad lo calcula el agente o el RAG?**→ Ahora mismo lo calcula el agente basándose en la distancia coseno. Es una primera iteración — en sesiones futuras habrá un agente específico para calcular ese score con criterios más ricos y auditables.

**P: ¿Qué se hace cuando no hay datos históricos para una tarea?**→ El agente lo detecta, lo flagea y lo reporta. La solución más sólida es completar esas tareas manualmente y re-indexarlas en el corpus para que las siguientes estimaciones las encuentren. Generar datos sintéticos es posible pero añade complejidad y requiere evaluación de calidad.

**P: ¿Tiene sentido integrar MCP servers como tools del agente?**→ Sí, pero con cuidado. El punto débil de MCP es el control de permisos y qué datos quedan expuestos. Preferible usar APIs propias con permisos explícitos, salvo que el MCP esté dentro de un entorno completamente controlado.
