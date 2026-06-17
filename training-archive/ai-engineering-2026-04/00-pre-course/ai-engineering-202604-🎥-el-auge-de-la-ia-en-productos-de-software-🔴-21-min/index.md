---
title: "🎥 El auge de la IA en productos de software 🔴 — 21 min"
source_url: "https://training.lidr.co/posts/ai-engineering-202604-🎥-el-auge-de-la-ia-en-productos-de-software-🔴-21-min"
archived_at: "2026-06-12T09:20:31.225Z"
group: "00-pre-course"
---

# 🎥 El auge de la IA en productos de software 🔴 — 21 min

![Antonio Perez](./assets/c3eccac37426c36f.jpg)

[Antonio Perez](https://training.lidr.co/members/36030888)

⏳Tiempo estimado: 21 min

## **Hace 3 años, ¿cuántos productos que usabas a diario tenían IA integrada? ¿Y hoy?**

Algo ha cambiado radicalmente en la industria del software. La inteligencia artificial ha dejado de ser un diferenciador para convertirse en una expectativa. Hoy esperamos que los productos tengan generación de texto, búsqueda inteligente, asistentes, automatizaciones o análisis automático de datos.

En esta lección vamos a ver qué ha provocado este cambio, por qué ahora cualquier producto puede integrar inteligencia artificial y qué significa esto para los ingenieros de software.

[Video](https://player.vimeo.com/video/1179858759?h=1a8993dab5)

## La IA antes de la explosión: machine learning en producción desde hace más de una década

Conviene empezar por lo que muchos olvidan: la inteligencia artificial ya estaba integrada en productos de software mucho antes de que ChatGPT existiera. Lo que ocurre es que era invisible para la mayoría de los usuarios — y para la mayoría de los ingenieros de software.

### Sistemas de recomendación

El ejemplo más conocido. Netflix lleva desde 2006 usando machine learning para personalizar qué contenido te muestra. Su algoritmo Cinematch, basado en filtrado colaborativo y filtrado por contenido, es responsable de que el 80% de lo que ven sus más de 200 millones de suscriptores venga de recomendaciones, no de búsquedas. Spotify, Amazon, YouTube — todos construyeron sus propios sistemas de recomendación con ML clásico: modelos que analizan patrones de comportamiento y predicen qué te va a gustar.

### Detección de fraude

Los bancos y procesadores de pago llevan años usando modelos de ML para analizar transacciones en tiempo real y detectar anomalías. Stripe procesa millones de pagos identificando patrones fraudulentos con scoring de riesgo en milisegundos. Netflix usa ML para detectar compartición de cuentas, credential stuffing y bots analizando patrones de login y comportamiento de streaming.

### Otros casos consolidados antes de 2022

Los filtros de spam de Gmail, la detección de objetos en fotos de Google Photos, el reconocimiento de voz de Siri y Alexa, los coches autónomos, el diagnóstico médico por imagen, el pricing dinámico de Uber — todo esto funcionaba con machine learning tradicional: modelos entrenados para clasificar, predecir o detectar patrones en datos.

### Lo que todos estos sistemas tienen en común

Requieren**equipos especializados de ML**para entrenar y mantener los modelos. Necesitan**datos propios**etiquetados y curados. Exigen**infraestructura dedicada**(GPUs, pipelines de datos, plataformas como Michelangelo de Uber o Metaflow de Netflix). Y tienen**ciclos de desarrollo largos**: meses de iteración entre data scientists, ML engineers y equipos de ingeniería.

Solo las empresas grandes podían permitírselo. Para una empresa mediana o una startup, integrar capacidades inteligentes en su producto era prohibitivo en coste, tiempo y talento.

## 2022–2023: el punto de inflexión de la IA generativa

Lo que cambió no fue la IA en sí — fue quién puede usarla y cómo.

### De entrenar modelos a consumir APIs

Con la llegada de los modelos fundacionales accesibles vía API (GPT-3.5 en noviembre 2022, GPT-4 en marzo 2023, Claude, Gemini), la ecuación se invirtió por completo. Ya no necesitas un equipo de ML dedicado, meses de entrenamiento ni infraestructura de GPUs. Necesitas saber hacer una llamada HTTP a una API y diseñar bien el contexto que le envías al modelo.

Shawn Wang (swyx) lo expresó así: tareas que antes requerían equipos de investigación y años de trabajo ahora requieren una llamada a una API y una tarde.

### La diferencia fundamental: generar vs. predecir

El ML tradicional**predice y clasifica**: ¿es esta transacción fraudulenta? ¿Le gustará esta película al usuario? ¿Es este email spam? Trabaja con datos estructurados y produce decisiones binarias o scores numéricos.

La IA generativa**crea contenido nuevo**: texto, código, imágenes, audio, vídeo. Puede mantener conversaciones, resumir documentos, analizar texto no estructurado, generar código funcional y razonar sobre problemas complejos. Esto abre una categoría completamente nueva de funcionalidades que antes eran imposibles de automatizar.

### El cambio de modelo económico

Con ML tradicional, el coste principal está en el entrenamiento del modelo (meses de compute en GPUs). Con IA generativa vía API, el coste se traslada al uso: pagas por token consumido en cada llamada. Esto convierte un gasto de capital (CAPEX) en un gasto operativo (OPEX) predecible y escalable, similar a lo que ya ocurrió con el cloud computing.

## 2024–2026: la adopción masiva en números

La velocidad de adopción no tiene precedentes en la historia del software empresarial.

### Datos de adopción

El gasto empresarial en IA generativa se triplicó en un solo año: de $11.500 millones en 2024 a $37.000 millones en 2025, convirtiéndolo en uno de los segmentos de software de mayor crecimiento de la historia. El 92% de las empresas del Fortune 500 ya utiliza productos de IA generativa de OpenAI. El 88% de las organizaciones a nivel global usa IA en al menos una función de negocio, y el 71% utiliza IA generativa de forma regular. En 2025, la IA generativa capturó más del 50% de toda la inversión global de venture capital — la primera vez que un sector tecnológico lo consigue.

### El estado real: adopción amplia, resultados desiguales

El dato más revelador para entender el momento actual: pese a la adopción casi universal, solo el 7% de las empresas ha escalado IA generativa a nivel empresarial. El 62% sigue en fase de experimentación. Más del 80% no reporta impacto medible en su EBIT.

Esto significa que hay una enorme brecha entre "usar IA generativa" y "generar valor real con ella". Las empresas que generan retorno son las que despliegan en tres o más funciones de negocio de forma integrada — no las que tienen un piloto aislado. Aquí es exactamente donde entran los AI Engineers: los profesionales que saben llevar estas integraciones de piloto a producción.

## Lo que ha cambiado para los ingenieros de software

### La nueva capa en la arquitectura

Antes, la arquitectura típica de un producto de software era: Frontend → Backend → Base de datos. Ahora se ha añadido una capa intermedia que conecta la lógica de negocio con capacidades de IA: APIs de LLMs, embeddings, bases de datos vectoriales, sistemas de recuperación de información (RAG) y orquestación de agentes.

Esta capa no se construye sola. Necesita ingenieros que la diseñen, la implementen y la operen. Ingenieros que entiendan tanto las particularidades de trabajar con modelos no deterministas (gestión de contexto, evaluación de calidad, detección de alucinaciones) como los fundamentos de ingeniería de software que ya conocen (APIs, bases de datos, despliegue, testing, observabilidad).

### ML tradicional e IA generativa conviven — no se sustituyen

Un error común es pensar que la IA generativa reemplaza al ML tradicional. No es así. Son complementarios:

- 

**ML tradicional**sigue siendo superior para tareas predictivas bien definidas con datos estructurados: detección de fraude, recomendación de contenido, forecasting de demanda, scoring de riesgo, diagnóstico médico por imagen. Estos sistemas requieren modelos entrenados específicamente con datos propios.

- 

**IA generativa**excele en tareas que involucran lenguaje natural, creación de contenido, razonamiento sobre información no estructurada y augmentación de flujos existentes: asistentes conversacionales, búsqueda semántica sobre documentación, generación de resúmenes, análisis de textos, generación de código.

En la práctica, los productos más sofisticados combinan ambos. Un sistema de atención al cliente puede usar ML clásico para clasificar y priorizar tickets (predicción) y un LLM para generar respuestas personalizadas (generación). Un sistema antifraude puede usar ML para el scoring en tiempo real y un LLM para explicar al analista por qué una transacción ha sido marcada.

### De especialistas a generalistas con nueva especialización

Con ML tradicional, integrar IA en un producto requería data scientists y ML engineers — perfiles que la mayoría de equipos de desarrollo no tenían. Con IA generativa, el punto de partida es un ingeniero de software senior que aprende la nueva capa. Las habilidades base (construir APIs, gestionar bases de datos, diseñar arquitecturas, desplegar servicios) son directamente transferibles. Lo nuevo es aprender a trabajar con las particularidades de los modelos: gestión de contexto, arquitecturas de recuperación, orquestación de agentes y evaluación de calidad.

## Ejemplos del cambio: IA generativa como funcionalidad integrada en productos existentes

Lo más significativo no son los productos de IA (ChatGPT, Midjourney) sino cómo productos que ya existían han integrado IA generativa como funcionalidad core:

**Notion**— Búsqueda semántica sobre tus documentos, asistente de escritura, Q&A sobre tu base de conocimiento. Construido por un equipo de unos 70 AI engineers sobre modelos existentes, no entrenando modelos propios.

**GitHub Copilot**— Autocompletado contextual integrado directamente en el editor. No es un producto aparte, es una funcionalidad dentro del IDE que ya usas.

**Stripe**— Detección de fraude en tiempo real integrada en el flujo de pagos (ML clásico), combinada ahora con capacidades generativas para análisis y explicación de patrones.

**Cualquier SaaS moderno**— Resúmenes automáticos de reuniones, clasificación inteligente de emails, generación de informes, asistentes de búsqueda sobre datos internos. Funcionalidades que hace tres años habrían sido impensables y que hoy son expectativas de los usuarios.

El patrón común: ninguno de estos productos entrena sus propios modelos de lenguaje. Todos construyen sobre APIs de modelos existentes y arquitecturas de integración. El valor diferencial no está en el modelo — está en cómo lo integras en tu producto, con tus datos y para tus usuarios.

## ¿Qué viene después? La era de los agentes

La siguiente ola ya está aquí. Según Gartner, las aplicaciones empresariales con agentes de IA específicos pasarán del 5% en 2025 al 40% a finales de 2026. Los agentes no solo generan contenido — ejecutan acciones: reservan vuelos, gestionan incidencias, procesan devoluciones, coordinan tareas entre sistemas.

Esto amplifica aún más la necesidad de AI Engineers: profesionales que sepan diseñar flujos de ejecución multi-paso, gestionar estado entre agentes, implementar mecanismos de supervisión humana y operar estos sistemas de forma segura en producción.

## Implicaciones para este programa

Todo lo anterior define el terreno en el que vamos a trabajar. Durante el programa construiremos un sistema que integra IA generativa en un producto real, pasando por las tres fases que refleja la evolución del mercado:

1. 

**CAG (Cache Augmented Generation):**Integración directa con LLMs vía API, inyectando contexto estático en cada llamada. El punto de entrada más sencillo y el patrón correcto cuando los datos son acotados.

1. 

**RAG (Retrieval Augmented Generation):**Conexión del modelo con datos persistentes mediante embeddings, búsqueda semántica y bases de datos vectoriales. El patrón dominante en producción hoy, presente en el 35.9% de las ofertas de empleo para AI Engineers.

1. 

**Agentes:**Orquestación de múltiples modelos y herramientas para resolver tareas complejas de forma autónoma. La frontera actual donde la demanda crece más rápido.

Cada fase construye sobre la anterior, reproduciendo exactamente la evolución que ha seguido la industria.
