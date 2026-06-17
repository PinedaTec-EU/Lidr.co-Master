---
title: "✍️ Ejercicio: Diagnóstico arquitectónico del sistema RAG actual 🔴"
source_url: "https://training.lidr.co/posts/ai-engineering-202604-✍️-ejercicio-diagnostico-arquitectonico-del-sistema-rag-actual-🔴"
archived_at: "2026-06-17T17:33:15.804Z"
group: "09-session"
---

# ✍️ Ejercicio: Diagnóstico arquitectónico del sistema RAG actual 🔴

![Antonio Perez](./assets/c3eccac37426c36f.jpg)

[Antonio Perez](https://training.lidr.co/members/36030888)

⏱**La fecha límite es martes 16 de junio al final del día.**

Al cierre de la Sesión 08 tu servicio IA ya puede hacer dos cosas: vectorizar presupuestos históricos y devolver los más similares a un vector de consulta. Lo que**todavía no puede**hacer es lo que el proyecto persigue desde el primer día: recibir la transcripción de una reunión y devolver una estimación fundamentada en esos presupuestos. Entre lo que tienes y lo que el sistema necesita hay un hueco, y la Sesión 09 entra precisamente a llenarlo introduciendo el flujo RAG end-to-end (Query → Retrieval → Augmentation → Generation).

Antes de construir nada nuevo, conviene mirar despacio lo que ya hay y lo que falta. Este ejercicio no pide código nuevo: pide que ejecutes lo que tienes contra una transcripción realista, observes qué pasa, y razones sobre los gaps. El objetivo es que llegues al directo con un mapa mental claro de tu propio sistema y con preguntas concretas formuladas desde la evidencia, no desde la intuición.

## Objetivo

Producir un único documento de diagnóstico arquitectónico que (a) describa el estado actual del servicio IA tras Sesiones 06–08, (b) registre el comportamiento observable del sistema cuando se le pasa una transcripción cruda, (c) identifique los fallos concretos del comportamiento actual y (d) proponga, a nivel de cajas y flechas, cómo debe evolucionar la arquitectura para cerrar el bucle hasta la estimación generada.

## Material proporcionado

Tu repositorio del proyectoestimatoren el estado en que quedó al cierre de Sesión 08: servicio IA con los módulosingest/,embedding_pipeline/ystorage/operativos, base de datos PostgreSQL + pgvector inicializada con el seed de presupuestos históricos, y los endpoints HTTP construidos hasta esta sesión (encode de embeddings y búsqueda semántica).

Tres transcripciones de ejemplo enexamples/transcripts/:

- 

01_clear.txt— un cliente describe con claridad lo que necesita y menciona explícitamente tecnologías y sector.

- 

02_ambiguous.txt— un cliente divaga sobre necesidades, mezcla temas, y solo en un par de frases da pistas concretas de qué quiere construir.**Esta es la transcripción que vas a usar para el trace.**

- 

03_hard.txt— un cliente menciona varias features posibles, cambia de opinión a mitad de la conversación y termina sin cerrar el alcance.

Un ficheroTEMPLATE.mdcon la estructura del entregable y los headers de las cuatro secciones obligatorias, para que puedas escribir directamente sobre él.

## Trabajo a realizar

### 1. Diagrama de la arquitectura actual

Dibuja la arquitectura de tres capas (frontend, backend de negocio, servicio IA) con los módulos del servicio IA que existen al cierre de Sesión 08. Para el servicio IA, baja un nivel: muestraingest/,embedding_pipeline/,storage/, y los endpoints HTTP expuestos hoy. Marca con sombreado, color o anotación dónde**acaba**lo que tienes implementado. No dibujes lo que falta — eso es trabajo de la sección 4.

El formato es libre: ASCII, Mermaid en un bloque de código del Markdown, captura de un boceto a mano, o imagen exportada de cualquier herramienta. Lo que importa es que se entienda qué módulo habla con cuál, qué dato fluye entre ellos, y en qué punto el flujo se queda corto si llegara una transcripción.

### 2. Trace anotado de una transcripción

Coge la transcripción02_ambiguous.txty haz un trace manual a través del sistema tal como está. El trace debe contener los siguientes pasos, cada uno con la llamada que has ejecutado, la respuesta cruda, y un comentario tuyo de una o dos frases razonando lo que ves:

1. 

Embebea la transcripción completa contra el endpoint o módulo de embeddings de tu servicio IA. Pega la primera y última componente del vector resultante, su norma o dimensionalidad, y comenta qué representa ese vector dado lo que sabes del contenido de la transcripción.

1. 

Llama al endpoint de búsqueda semántica con ese vector (o con la transcripción, según cómo lo hayas implementado en S08) pidiendo los 5 chunks más similares. Pega la respuesta cruda con los chunks devueltos y sus distancias o similitudes.

1. 

Para cada chunk devuelto, comenta brevemente: a qué presupuesto histórico pertenece, de qué sector es, y si te parece relevante para lo que el cliente está pidiendo en la transcripción. Sé honesto: si el resultado es bueno, dilo; si no lo es, también.

Usacurl,httpie, un script corto en Python, o una colección de Postman. Pega los comandos exactos para que el resultado sea reproducible. El código de las llamadas, los payloads y los nombres de campo van en inglés; tus observaciones van en español.

### 3. Diagnóstico: cinco fallos identificados

A partir del trace de la sección 2 y de tu conocimiento del estado actual del sistema, enumera**cinco fallos**que impiden hoy que la transcripción se convierta en una estimación de calidad. Para cada fallo redacta tres líneas:

- 

**Problema observado**— qué ves que pasa, idealmente referenciando lo que has visto en el trace.

- 

**Causa probable**— qué decisión arquitectónica o ausencia de pieza está provocándolo.

- 

**Propuesta de solución**— qué pieza, etapa o cambio crees que lo resolvería, sin entrar en cómo implementarlo.

Los fallos deben ser concretos y verificables, no genéricos. "El sistema no es bueno" no es un fallo. "Cuando embebeo una transcripción de 4.000 tokens y comparo con chunks de 300 tokens, las distancias coseno comprimen mucho y todos los chunks devuelven scores parecidos" sí lo es. Apunta hacia problemas reales que veas; si encuentras más de cinco, escoge los cinco más relevantes y deja los demás para una sección de "otros" al final.

### 4. Propuesta de evolución arquitectónica

Dibuja un segundo diagrama de la misma arquitectura de tres capas, pero ahora con las cajas y módulos que añadirías al servicio IA para que el flujo desde la transcripción hasta la estimación generada esté completo. No es una propuesta de implementación: son cajas, flechas y nombres. Marca claramente cuáles son nuevas respecto al diagrama de la sección 1.

Acompáñalo de un párrafo breve, no más de diez líneas, que responda a tres preguntas: ¿cuál es la responsabilidad de cada módulo nuevo?, ¿qué dato fluye entre ellos?, y ¿qué pieza es la más crítica para que el sistema mejore — la que atacarías primero si solo pudieras construir una?

## Entregable

Un único archivoarquitectura-actual.mden la raíz del repositorio, con las cuatro secciones anteriores. Sube el archivo al repo en una rama nueva llamadasession-09/pre-worky abre PR contramain(la convención que hemos venido usando desde Sesión 02). No es necesario que el PR se merge antes de la sesión en vivo, el branch basta.

## Criterios de aceptación

El entregable está completo si las cuatro secciones existen, el trace de la sección 2 incluye comandos ejecutables y respuestas reales del sistema, los cinco fallos de la sección 3 referencian observaciones del trace y no afirmaciones genéricas, y los dos diagramas (sección 1 y sección 4) son distinguibles entre sí y muestran claramente qué cambia entre el estado actual y el estado propuesto.

## Tiempo estimado

Entre 1 hora y 1 hora y media. Si te lleva más de dos horas, probablemente estás bajando a un nivel de detalle que no necesita esta fase del trabajo; vuelve al nivel de cajas y flechas.

## Qué NO hay que hacer

No implementes reformulación de queries, ni reranking, ni un nuevo retriever, ni modifiques el endpoint de búsqueda actual. No escribas el módulo de generación. No crees nuevos endpoints. Si en algún momento te encuentras escribiendo Python que va más allá de un script de cliente para hacer las llamadas del trace, para — eso es trabajo para el directo y para las próximas sesiones.

Tampoco busques en internet la arquitectura RAG canónica para copiarla en la sección 4. La propuesta tiene que salir de tu observación del trace y de tu razonamiento sobre los fallos, no de un diagrama de IBM. Si la sección 4 acaba siendo "Query → Retrieval → Augmentation → Generation" sin más, no estás haciendo el ejercicio: estás repitiendo terminología.

## Cómo entregar

Además de subir la ramasession-09/pre-worky abrir el PR,**envía por mail a****[lia@lidr.co](mailto:lia@lidr.co)****el enlace a la rama**(URL completa de GitHub)**hasta dos días antes de la sesión en vivo,**es decir, la fecha límite indicada al inicio de este documento. El plazo es estricto: necesitamos margen para revisar las entregas y preparar el material de la sesión basándonos en los problemas reales que hayas encontrado en tu trace.

Asegúrate de que la rama es accesible: repositorio público o, si es privado, con permisos para el revisor que se te indicará en el canal del programa.

Si llegas a la sesión sin haber entregado, podrás seguir el directo igualmente, pero los bloques hands-on darán por sentado que el pipeline básico funciona. La sesión en vivo no es el lugar ni el momento para depurar problemas de setup.

Repositorio:[**https://github.com/LIDR-academy/ai-engineering/tree/session_09**](https://github.com/LIDR-academy/ai-engineering/tree/session_09)
Explore More PostsReady to move on to the next Lesson?[Mark as Complete](#)[PreviousSesión 9: Fundamentos de RAG y técnicas de recuperación — 144 min](https://training.lidr.co/posts/ai-engineering-202604-sesion-9-fundamentos-de-rag-y-tecnicas-de-recuperacion-144-min)[Next📋 Del CAG estático al flujo RAG: las cuatro etapas y por qué el retrieval domina 🔴 — 25 min](https://training.lidr.co/posts/ai-engineering-202604-📋-del-cag-estatico-al-flujo-rag-las-cuatro-etapas-y-por-que-el-retrieval-domina-🔴-25-min)[Previous Comments](#)

[More Comments](#)

Drag photo, video or file here[](#)[](#)[](#)[Comment](#)[Cancel](#)
