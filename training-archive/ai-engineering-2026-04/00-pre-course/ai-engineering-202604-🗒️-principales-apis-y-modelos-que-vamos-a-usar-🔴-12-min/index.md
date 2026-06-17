---
title: "🗒️ Principales APIs y modelos que vamos a usar 🔴 — 12 min"
source_url: "https://training.lidr.co/posts/ai-engineering-202604-🗒️-principales-apis-y-modelos-que-vamos-a-usar-🔴-12-min"
archived_at: "2026-06-12T09:20:51.424Z"
group: "00-pre-course"
---

# 🗒️ Principales APIs y modelos que vamos a usar 🔴 — 12 min

![Antonio Perez](./assets/c3eccac37426c36f.jpg)

[Antonio Perez](https://training.lidr.co/members/36030888)

⏳Tiempo estimado: 12 min

# Modelos de IA que Usaremos en el Programa

A lo largo del programa trabajarás principalmente con modelos de inteligencia artificial de dos tipos fundamentales:**modelos de lenguaje (LLMs)**para generar texto, razonar y ejecutar tareas, y**modelos de embeddings**para convertir texto en representaciones numéricas que permiten la búsqueda semántica. Aprenderemos como conectar y comunicar con las distintas APIs necesarias y utilizaremos también herramientas que unifican el acceso a todos estos modelos desde una sola interfaz.

Este documento te presenta los modelos con los que trabajaremos. No necesitas conocerlos en profundidad antes de empezar — los iremos explorando a medida que el programa avance — pero tener una visión general del panorama te ayudará a entender las decisiones que tomaremos.

## Modelos de Lenguaje (LLMs)

Los LLMs son el núcleo de todo lo que construiremos. Son modelos capaces de entender instrucciones en lenguaje natural, generar texto, analizar documentos, extraer datos estructurados y ejecutar tareas complejas mediante razonamiento. En el programa trabajaremos principalmente con dos proveedores: OpenAI y Anthropic.

### OpenAI

Sus modelos se organizan en familias según su capacidad y coste.

**GPT-5.4**— El modelo flagship de OpenAI y el más avanzado disponible actualmente. Ofrece la mayor capacidad de razonamiento, coding y tareas agénticas de toda la familia, con una ventana de contexto de 1 millón de tokens y soporte para múltiples niveles de razonamiento. Será nuestro modelo de referencia cuando necesitemos máxima calidad en tareas complejas.

**GPT-5.4 mini**— Una versión más compacta y económica de GPT-5.4 que mantiene un rendimiento excelente para la mayoría de tareas cotidianas. Ideal para coding, computer use y subagentes donde la latencia y el coste importan más que la capacidad máxima de razonamiento. Será nuestro modelo principal durante los módulos de CAG y las primeras fases de RAG por su equilibrio entre calidad y coste.

**GPT-5.4 nano**— El modelo más rápido y barato de la familia. Pensado para tareas ligeras como autocompletado, clasificación de intenciones o enrutamiento de consultas. Lo usaremos como ejemplo de cómo elegir el modelo adecuado según el caso de uso.

**Modelos de generaciones anteriores (GPT-4.1, GPT-4o)**— Aunque el programa se centrará en la familia GPT-5.4, es importante conocer los modelos anteriores porque muchos proyectos en producción todavía los utilizan. GPT-4.1 sigue siendo una opción sólida para muchas tareas con un coste inferior, y lo mencionaremos cuando hablemos de estrategias de optimización de costes.

**Documentación y recursos:**

- 

Catálogo de modelos de OpenAI:[developers.openai.com/api/docs/models](https://developers.openai.com/api/docs/models)

- 

Guía de la API (quickstart):[platform.openai.com/docs/quickstart](https://platform.openai.com/docs/quickstart)

- 

Precios:[openai.com/api/pricing](https://openai.com/api/pricing/)

### Anthropic (Claude)

Anthropic es el segundo gran proveedor que usaremos. Sus modelos Claude destacan por su capacidad de seguir instrucciones complejas, manejar documentos extensos y generar texto de alta calidad. Al igual que OpenAI, organiza sus modelos en varias familias.

**Claude Sonnet 4.6**— El modelo equilibrado de última generación de Anthropic. Combina velocidad e inteligencia para tareas cotidianas, con un rendimiento excelente en búsqueda agéntica y un consumo de tokens optimizado. Soporta extended thinking y una ventana de contexto de 1 millón de tokens. Será una de las opciones principales que usaremos en el programa, especialmente para mostrar cómo abstraer la dependencia de un proveedor concreto.

**Claude Opus 4.6**— El modelo más avanzado e inteligente de Anthropic, con un rendimiento excepcional en coding y razonamiento complejo. La gama más alta para tareas que requieren máxima calidad: generación de código extenso, análisis profundo, y tareas agénticas de larga duración. Lo usaremos como referencia cuando necesitemos máxima calidad y el coste no sea la prioridad.

**Claude Haiku 4.5**— El modelo más rápido y económico de Anthropic, diseñado para aplicaciones de alto volumen y baja latencia. Ideal para clasificación, moderación de contenido y procesamiento masivo donde la velocidad de respuesta es crítica.

**Documentación y recursos:**

- 

Visión general de modelos Claude:[platform.claude.com/docs/en/about-claude/models/overview](https://platform.claude.com/docs/en/about-claude/models/overview)

- 

Guía de inicio rápido:[platform.claude.com/docs/en/api/getting-started](https://platform.claude.com/docs/en/api/getting-started)

- 

SDK de Python:[github.com/anthropics/anthropic-sdk-python](https://github.com/anthropics/anthropic-sdk-python)

- 

Precios:[anthropic.com/pricing](https://www.anthropic.com/pricing)

- 

Anthropic Cookbook (ejemplos prácticos):[github.com/anthropics/anthropic-cookbook](https://github.com/anthropics/anthropic-cookbook)

## Modelos de Embeddings

Los modelos de embeddings son fundamentales para todo el módulo de RAG (sesiones 7-11). A diferencia de los LLMs, estos modelos no generan texto: transforman texto en vectores numéricos (listas de números) que capturan el significado semántico de las palabras. Dos textos con significado similar producirán vectores cercanos en el espacio, lo que permite hacer búsqueda semántica — encontrar información relevante por significado, no por coincidencia exacta de palabras.

### OpenAI Embeddings

Los modelos de embeddings de OpenAI son los que usaremos como opción principal por su facilidad de integración (misma API key, mismo SDK) y su excelente rendimiento multilingüe.

**text-embedding-3-small**— El modelo recomendado para la mayoría de casos de uso. Genera vectores de 1.536 dimensiones por defecto, con la opción de reducirlos a tamaños más pequeños para ahorrar almacenamiento. Ofrece un rendimiento muy bueno a un coste muy bajo.

**text-embedding-3-large**— El modelo de embeddings más capaz de OpenAI, con hasta 3.072 dimensiones. Proporciona mayor precisión en tareas de búsqueda y clasificación, especialmente en escenarios multilingües. Lo usaremos cuando necesitemos máxima calidad de recuperación o como punto de comparación frente al modelo small.

Ambos modelos soportan el parámetrodimensions, que permite reducir el tamaño del vector sin perder la mayor parte de su capacidad representativa. Esto es particularmente útil cuando trabajamos con bases de datos vectoriales donde el almacenamiento y la velocidad de búsqueda importan.

**Documentación y recursos:**

- 

Guía de embeddings de OpenAI:[platform.openai.com/docs/guides/embeddings](https://platform.openai.com/docs/guides/embeddings)

- 

Documentación de text-embedding-3-small:[platform.openai.com/docs/models/text-embedding-3-small](https://platform.openai.com/docs/models/text-embedding-3-small)

- 

Documentación de text-embedding-3-large:[platform.openai.com/docs/models/text-embedding-3-large](https://platform.openai.com/docs/models/text-embedding-3-large)

- 

Artículo de lanzamiento (en español):[openai.com/es-ES/index/new-embedding-models-and-api-updates](https://openai.com/es-ES/index/new-embedding-models-and-api-updates/)

- 

Precios de embeddings:[openai.com/api/pricing](https://openai.com/api/pricing/)

### Sentence Transformers (open-source)

Como complemento a los modelos de OpenAI, en la sesión de teoría de embeddings (sesión 07) también exploraremos**Sentence Transformers**, una librería open-source de Hugging Face que permite ejecutar modelos de embeddings de forma local, sin depender de una API externa. Esto es útil para entender cómo funcionan los embeddings por dentro y para escenarios donde la privacidad de los datos o los costes de API son una preocupación.

**Documentación y recursos:**

- 

Documentación de Sentence Transformers:[sbert.net](http://sbert.net)

- 

Repositorio en GitHub:[github.com/UKPLab/sentence-transformers](https://github.com/UKPLab/sentence-transformers)

- 

Modelos disponibles en Hugging Face:[huggingface.co/models?library=sentence-transformers](https://huggingface.co/models?library=sentence-transformers)

## Agregadores: LiteLLM

En un proyecto real rara vez trabajas con un solo proveedor de modelos. Necesitas poder cambiar entre proveedores según el coste, la disponibilidad o las capacidades específicas de cada modelo. Para eso usaremos**LiteLLM**.

LiteLLM es una librería open-source que proporciona una interfaz unificada para llamar a más de 100 modelos de diferentes proveedores (OpenAI, Anthropic, Mistral, Groq, Ollama y muchos más) usando exactamente el mismo formato de llamada. Esto significa que puedes cambiar degpt-5.4-miniaclaude-sonnet-4.6modificando un solo string, sin tocar el resto de tu código.

Además de la unificación de APIs, LiteLLM ofrece funcionalidades que veremos a lo largo del programa: estrategias de fallback entre proveedores (si OpenAI falla, usa Anthropic automáticamente), balanceo de carga entre múltiples deployments del mismo modelo, y tracking de costes por llamada.

En el programa usaremos LiteLLM tanto como librería Python dentro de nuestro servicio FastAPI como en su modo proxy (un gateway HTTP que centraliza todas las llamadas a LLMs).

**Documentación y recursos:**

- 

Documentación oficial de LiteLLM:[docs.litellm.ai](http://docs.litellm.ai)

- 

Getting started:[docs.litellm.ai/docs](https://docs.litellm.ai/docs/)

- 

Repositorio en GitHub:[github.com/BerriAI/litellm](https://github.com/BerriAI/litellm)

- 

Lista de proveedores soportados:[docs.litellm.ai/docs/providers](https://docs.litellm.ai/docs/providers)

## ¿Qué cuentas necesito crear?

Para seguir el programa necesitarás crear cuentas y obtener API keys en al menos dos proveedores. El coste total estimado a lo largo del programa es bajo (en torno a 10-20€ dependiendo del uso), ya que trabajaremos principalmente con los modelos más eficientes y los proveedores ofrecen créditos gratuitos iniciales.

Las cuentas necesarias y los pasos para darlas de alta se cubrirán en detalle en la**Sesión 01: LLMs y setup de entorno de trabajo**.
