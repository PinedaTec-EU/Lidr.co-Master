---
title: "✍️ Ejercicio: Técnicas avanzadas de recuperación 🔴"
source_url: "https://training.lidr.co/posts/ai-engineering-202604-✍️-ejercicio-tecnicas-avanzadas-de-recuperacion-🔴"
archived_at: "2026-06-25T17:23:42.886Z"
group: "10-session"
---

# ✍️ Ejercicio: Técnicas avanzadas de recuperación 🔴

![Antonio Perez](./assets/c3eccac37426c36f.jpg)

[Antonio Perez](https://training.lidr.co/members/36030888)

⏱**La fecha límite es martes 23 de junio al final del día.**

Vuestro pipeline RAG ya funciona de extremo a extremo: reformula la consulta, recupera presupuestos por similitud vectorial y genera una estimación con ese contexto. El problema es que "similar" no siempre significa "relevante": a veces el sistema recupera un presupuesto de una app de pagos cuando la consulta describe una plataforma de e-commerce. Cercano en el espacio vectorial, inútil para estimar.

En este ejercicio vais a atacar ese problema con dos técnicas, búsqueda híbrida y reranking, y, sobre todo, vais a**medir**si compensan. El objetivo no es solo que la recuperación mejore: es que podáis demostrar con números cuánto mejora y a qué coste.

## Lectura previa imprescindible

Antes de empezar, leed los artículos 1, 2 y 3 del material de esta sesión (reranking, medición de relevancia y búsqueda híbrida). El ejercicio se apoya directamente en ellos. Los artículos 4, 5 y 6 preparan la sesión en vivo y podéis leerlos después de entregar.

## Qué necesitaís

Si no los tenéis en vuestro repo personal, hacéd un fork de[https://github.com/LIDR-academy/ai-engineering](https://github.com/LIDR-academy/ai-engineering), checkouteáis la ramasession-10, y lo sacáis de ahí.

**Incluye**:

- 

El pipeline RAG de la sesión anterior, funcionando (desde vuestro repo personal)

- 

Un wrapper de cross-encoder ya construido enapp/generation/rag/retrieval/(carga del modelo, scoring de pares consulta-documento).**No tenéis que implementar el reranker: tenéis que integrarlo.**

- 

El dataset de presupuestos históricos ya ingerido y vectorizado.

**Verificación antes de empezar**

Levantad el entorno y aseguraos de que el modelo de reranking descarga y carga correctamente:

bash
git clone <https://github.com/LIDR-academy/ai-engineering.git> cd ai-engineering git checkout session-10 docker compose up -d docker compose exec ai-service python -m app.generation.rag.retrieval.verify_reranker

Si este paso falla, no sigáis adelante: revisad la guía de troubleshooting en la ramasession-10y, si no lo resolvéis, traedlo al bloque de resolución de errores de la sesión en vivo (pero avisad antes por el canal para que lo tengamos localizado).

## Alcance - importante

Este ejercicio cubre**únicamente**búsqueda híbrida y reranking. No implementéis expansión de consultas, routing multi-índice ni filtrado por metadatos aunque hayáis leído sobre ellos: los construiremos juntos en la sesión en vivo sobre lo que traigáis hecho.

## Pasos

### 1. Búsqueda full-text en PostgreSQL

Cread una migración de Alembic que añada a la tabla de chunks una columnatsvectorgenerada a partir del contenido, con su índice GIN. Los presupuestos del dataset están en español: tenedlo en cuenta al elegir la configuración de text search de la columna. Recordad que, como siempre, todo el código, nombres, comentarios, mensajes de log, va en inglés.

### 2. Rama léxica y fusión RRF

Implementad la búsqueda por palabras clave sobre la nueva columna y combinad sus resultados con los de la búsqueda vectorial existente mediante Reciprocal Rank Fusion. El resultado debe ser una función de búsqueda híbrida que devuelva un ranking único fusionado.

Decisiones libres: cómo estructuráis el módulo, cómo parametrizáis la constante de suavizado de RRF, y cómo exponéis el modo de búsqueda (parámetro del endpoint, configuración, o script, lo que prefiráis, mientras las cuatro configuraciones del paso 4 sean invocables de forma reproducible).

### 3. Integración del reranker

Conectad el wrapper de cross-encoder al pipeline siguiendo el patrón recall-then-rerank: recuperación amplia (top-50) y reordenación fina para quedaros con los mejores (top-5). El reranking debe poder activarse y desactivarse sin tocar código.

### 4. Golden set y medición

Construid un golden set de**5 consultas**representativas del dominio (descripciones de proyectos a estimar) y anotad a mano, para cada una, qué presupuestos del dataset son realmente relevantes. Después ejecutad las cuatro configuraciones contra el golden set:

Configuración Búsqueda Reranking A Vectorial No B Híbrida No C Vectorial Sí D Híbrida Sí

Para cada configuración, medid la precisión sobre los 5 primeros resultados y la latencia de la consulta. Recoged los resultados en una tabla comparativa.

### 5. Conclusiones

Cerrad con un párrafo breve respondiendo: ¿qué configuración usaríais en el proyecto y por qué? ¿La ganancia de relevancia del reranking justifica su latencia en este caso de uso concreto? No hay respuesta correcta única: hay respuestas bien y mal argumentadas.

## Entregable

Abrid un PR en**vuestro repo personal**con ramasession-10/pre-worky enviad por mail a[lia@lidr.co](mailto:lia@lidr.co):

- 

Enlace completo al PR en GitHub (URL de vuestro repo, no del oficial, o fork si no tenéis)

- 

Tabla comparativa con Configuraciones A, B, C, D (precisión y latencia)

El plazo es estricto: necesitamos margen para revisar las implementaciones, validar los golden sets y preparar el material de la sesión basándonos en los números reales que obtengáis.

Aseguraos de que:

- 

El PR es accesible (repo público o permisos para el revisor)

- 

El mail incluye enlace + tabla

Si llegáis a la sesión sin haber entregado, podréis seguir el directo igualmente, pero los bloques de casos avanzados asumirán que ya tuvisteis cifras de vuestro setup.
Explore More PostsReady to move on to the next Lesson?[Mark as Complete](#)[PreviousSesión 10: Técnicas de recuperación — 129 min](https://training.lidr.co/posts/ai-engineering-202604-sesion-10-tecnicas-de-recuperacion-129-min)[Next📄 Reranking: cuando el top-k vectorial no es suficiente 🔴— 24 min](https://training.lidr.co/posts/ai-engineering-202604-📄-reranking-cuando-el-top-k-vectorial-no-es-suficiente-🔴-24-min)[Previous Comments](#)

[More Comments](#)

Drag photo, video or file here[](#)[](#)[](#)[Comment](#)[Cancel](#)
