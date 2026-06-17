---
title: "🎥 Software 3.0 in the era of AI - Andrej Karpathy 🔴 — 50 min"
source_url: "https://training.lidr.co/posts/ai-engineering-202604-🎥-software-30-in-the-era-of-ai-andrej-karpathy-🔴-50-min"
archived_at: "2026-06-12T09:20:39.953Z"
group: "00-pre-course"
---

# 🎥 Software 3.0 in the era of AI - Andrej Karpathy 🔴 — 50 min

![Antonio Perez](./assets/c3eccac37426c36f.jpg)

[Antonio Perez](https://training.lidr.co/members/36030888)

⏳Tiempo estimado: 50 min

# Software en la Era de la IA

El software está atravesando una transformación que no veíamos en 70 años — y este es un momento extraordinario para entrar en la industria. En este contenido se exploran las razones y las oportunidades que se abren.

[Video](https://www.youtube.com/embed/LCEmiRjPEtQ?controls=0&modestbranding=1&rel=0&showinfo=0&loop=0&fs=0&hl=en&enablejsapi=1&origin=https%3A%2F%2Ftraining.lidr.co&widgetid=1&forigin=https%3A%2F%2Ftraining.lidr.co%2Fposts%2Fai-engineering-202604-%25F0%259F%258E%25A5-software-30-in-the-era-of-ai-andrej-karpathy-%25F0%259F%2594%25B4-50-min&aoriginsup=1&vf=6)

Video Player is loading.Play VideoPlayMuteLoaded:0.00%00:00Remaining Time-39:321xPlayback Rate

- 2x
- 1.5x
- 1.25x
- 1x, selected
- 0.75x
- 0.5x
- 0.25x
Fullscreen

This is a modal window.

[Slides](https://docs.google.com/presentation/d/1sZqMAoIJDxz79cbC5ap5v9jknYH4Aa9cFFaWL8Rids4/edit?slide=id.g33d19f2dc57_0_424#slide=id.g33d19f2dc57_0_424)de la presentación.

## Los Tres Paradigmas del Software

El software ha evolucionado en tres capas que coexisten y se complementan:

**Software 1.0**es el código tradicional que escribimos para el ordenador: Python, C++, JavaScript. Instrucciones explícitas, deterministas, escritas por humanos.

**Software 2.0**son los pesos de las redes neuronales. Aquí no escribes el programa directamente; diseñas datasets, ejecutas un optimizador y obtienes los parámetros que definen el comportamiento. Hugging Face se convierte en el GitHub de este paradigma.

**Software 3.0**es el salto más reciente y quizás el más radical: programar mediante prompts en lenguaje natural. Con los LLMs, el inglés (o el español) se convierte literalmente en un lenguaje de programación. Los prompts son programas que configuran el comportamiento de una nueva clase de ordenador.

La implicación práctica es clara: los profesionales del software necesitan fluidez en los tres paradigmas, porque cada uno tiene ventajas según el problema que estés resolviendo.

## Los LLMs Como Sistemas Operativos

Una de las analogías más potentes: los LLMs no son simplemente una utilidad como la electricidad. Son**sistemas operativos emergentes**.

El LLM actúa como CPU, la ventana de contexto funciona como memoria RAM, y el modelo orquesta herramientas, capacidades multimodales y acceso a información para resolver problemas. Igual que descargamos apps que funcionan en Windows, Linux o macOS, ya existen aplicaciones (como Cursor) que funcionan indistintamente sobre GPT, Claude o Gemini — un simple desplegable.

El momento actual se sitúa en torno a los**años 60 de la computación**: el cómputo LLM es caro, centralizado en la nube, y nosotros somos terminales ligeros que acceden mediante*timesharing*. La revolución del ordenador personal de los LLMs aún no ha llegado, aunque hay señales tempranas con hardware como los Mac Mini ejecutando modelos en local.

## La Psicología de los LLMs: Espíritus de Personas

Los LLMs pueden entenderse como**"simulaciones estocásticas de personas"**— espíritus humanos generados por un transformador autoregresivo entrenado con textos de toda la humanidad. Esto produce una psicología emergente fascinante y contradictoria:

Tienen una**memoria enciclopédica**que supera a cualquier individuo, capaces de recordar hashes SHA o detalles oscuros de documentación. Pero al mismo tiempo sufren de**amnesia anterógrada**: cada conversación empieza de cero, sin acumulación real de contexto a lo largo del tiempo. La analogía es inevitable con las películas*Memento*y*50 First Dates*, donde los protagonistas despiertan cada día sin recuerdos del anterior.

Exhiben una**inteligencia irregular**: sobrehumanos en ciertos dominios de razonamiento, pero capaces de cometer errores que ningún humano haría — como insistir en que 9.11 es mayor que 9.9. Son además**crédulos**, vulnerables a inyecciones de prompt y problemas de seguridad.

## Productos de Autonomía Parcial

El corazón práctico se centra en una idea: las mejores aplicaciones LLM no son agentes totalmente autónomos, sino**productos de autonomía parcial**con un diseño muy deliberado.

Las apps LLM exitosas como Cursor o Perplexity comparten cuatro características:

1. 

**Gestión inteligente del contexto**, alimentando al LLM con la información relevante en cada momento.

1. 

**Orquestación de múltiples llamadas**a distintos modelos (embeddings, chat, aplicación de diffs).

1. 

**GUI específica para la tarea**, porque la interfaz visual permite auditar el trabajo del LLM mucho más rápido que leer texto plano. Ver un diff en rojo y verde es infinitamente más eficiente que que el modelo te lo explique con palabras.

1. 

**El slider de autonomía**: desde autocompletado sutil hasta un agente que modifica un repositorio entero. El usuario elige cuánta autonomía ceder según la complejidad de la tarea.

La lección clave: el bucle**generación → verificación**entre humano e IA debe ser lo más rápido posible. Para eso necesitamos GUIs que aprovechen nuestro sistema visual (leer texto es lento; ver imágenes es instantáneo) y mantener la IA "con la correa puesta" — diffs pequeños, cambios incrementales, tareas concretas.

## Vibe Coding y la Democratización del Software

El término**"vibe coding"**nació casi por accidente, en un tweet que nadie esperaba que fuera viral. Hoy tiene página en Wikipedia. La idea: programar guiándote por la intuición y dejando que el LLM genere el código, sin necesidad de dominar el lenguaje subyacente.

Se muestra cómo se construyó una app iOS en Swift sin saber Swift. También se presenta[**menuGen.app**](http://menuGen.app)— una aplicación que fotografía el menú de un restaurante y genera imágenes de los platos — creada en unas pocas horas de vibe coding. Pero hay una verdad incómoda: el código fue la parte fácil. Lo que consumió una semana entera fue el DevOps: autenticación, pagos, dominios, despliegue. Todo eso sigue siendo "hacer clic en el navegador siguiendo instrucciones" — trabajo que los agentes deberían poder hacer, pero que aún no resuelven bien.

## Construir Para los Agentes

La última parte mira hacia adelante: hay un nuevo consumidor de información digital que no es humano ni es una API tradicional. Son los**agentes LLM**, y nuestra infraestructura necesita adaptarse a ellos.

Se destacan iniciativas concretas: archivosllms.txtque describen un dominio en markdown legible para LLMs; documentación técnica convertida a formatos amigables para modelos (como están haciendo Vercel y Stripe); herramientas como**GitIngest**que transforman un repositorio en un texto concatenado listo para copiar a un LLM; o**DeepWiki**, que genera documentación analítica de cualquier repo de GitHub.

Y por supuesto, protocolos como el**Model Context Protocol (MCP)**de Anthropic, diseñados específicamente para que los agentes interactúen con servicios digitales de forma nativa.

## La Metáfora Final: El Traje de Iron Man

El contenido cierra con la imagen que mejor captura toda la filosofía expuesta: el traje de Iron Man es simultáneamente una**aumentación**(Tony Stark lo pilota) y un**agente**(puede volar solo). Eso es exactamente lo que debemos construir: productos que amplifiquen las capacidades humanas hoy, con un slider de autonomía que iremos deslizando hacia la derecha a lo largo de la próxima década.

El mensaje para quienes entran en la industria: estamos reescribiendo las reglas del software. Hay una cantidad inmensa de código por escribir y reescribir. Y es un privilegio poder hacerlo.
