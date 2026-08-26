# Resumen de conceptos por sesión

Este documento no pretende sustituir las lecciones. Es un mapa de estudio de los conceptos que deberías comprender y ser capaz de relacionar después de cada sesión del máster.

> Las referencias a modelos, precios y límites de contexto cambian con rapidez. Conviene memorizar los criterios de decisión y comprobar los datos concretos en la documentación vigente del proveedor.

## Cómo usar este resumen

Para cada sesión:

1. Lee la **idea central**.
2. Comprueba si puedes explicar con tus palabras los **conceptos imprescindibles**.
3. Intenta responder la **pregunta de control** sin consultar el material.
4. Si no puedes justificar una decisión o un trade-off, vuelve a la lección correspondiente.

## El recorrido completo

| Sesión | Pregunta central |
|---|---|
| [1](./01-session/) | ¿Cómo se integra y controla un LLM desde código? |
| [2](./02-session/) | ¿Cómo se convierte una llamada a un LLM en un servicio CAG bien estructurado? |
| [3](./03-session/) | ¿Cómo se desacopla el producto del proveedor y se opera de forma observable? |
| [4](./04-session/) | ¿Cómo se transforma una demo conversacional en un producto fiable? |
| [5](./05-session/) | ¿Cómo se añaden memoria, contexto dinámico, personalización y evaluación? |
| [6](./06-session/) | ¿Cómo se preparan datos empresariales para que sean utilizables por sistemas de IA? |
| [7](./07-session/) | ¿Cómo se transforma contenido en representaciones vectoriales útiles? |
| [8](./08-session/) | ¿Cómo se almacenan y recuperan vectores con rendimiento y criterio? |
| [9](./09-session/) | ¿Cómo se construye un flujo RAG completo y seguro? |
| [10](./10-session/) | ¿Cómo se mejora el retrieval cuando la similitud vectorial no basta? |
| [11](./11-session/) | ¿Cómo se consigue que una respuesta RAG sea verificable y medible? |
| [12](./12-session/) | ¿Cuándo hace falta un agente y cómo funciona su bucle? |
| [13](./13-session/) | ¿Cómo se orquesta un flujo agéntico con estado, persistencia y recuperación? |
| [14](./14-session/) | ¿Cuándo compensa un sistema multiagente y cómo se controla? |
| [15](./15-session/) | ¿Qué frontera, servicios e infraestructura necesita un sistema para llegar a producción? |
| [16](./16-session/) | ¿Cómo se mide, observa y mejora un sistema de IA ya desplegado? |

---

## Sesión 1 — LLMs y entorno de trabajo

### Idea central

Un LLM deja de ser una aplicación externa y pasa a ser un componente de software cuando lo invocas mediante una API, controlas sus entradas y parámetros, interpretas su respuesta y mides sus errores, tokens, latencia y coste.

### Conceptos imprescindibles

- **Anatomía de una llamada**: credenciales, cliente, modelo, instrucciones del sistema, mensajes del usuario, parámetros, respuesta y metadatos.
- **Roles y jerarquía de instrucciones**: las instrucciones definen comportamiento y límites; los mensajes contienen la conversación. Cada proveedor expresa este contrato con pequeñas diferencias.
- **Tokens**: el modelo procesa tokens, no palabras. La tokenización afecta al límite de contexto, al coste y a tareas con números, idiomas o formato.
- **Ventana de contexto**: incluye instrucciones, entrada, historial, herramientas y salida reservada. Un contexto grande no elimina la necesidad de presupuestarlo.
- **Modelos de razonamiento**: pueden usar parámetros y tokens de razonamiento específicos; no siempre aceptan los mismos controles que un modelo convencional.
- **Selección de proveedor y modelo**: se decide por calidad para la tarea, coste, latencia, contexto, privacidad, disponibilidad y capacidades, no por una clasificación universal.
- **Fiabilidad básica**: hay que distinguir errores de autenticación, límites de cuota, rate limits, timeouts, errores del servidor y respuestas truncadas.
- **Coste operativo**: los tokens de entrada y salida suelen tener precios distintos; caching y procesamiento batch pueden cambiar mucho la economía.

### Debes poder explicar

Por qué una llamada válida técnicamente aún no es una integración de producción: faltan manejo de errores, trazabilidad, control de tokens, evaluación de calidad y una decisión consciente sobre el modelo.

### Pregunta de control

Si dos modelos producen una respuesta parecida, ¿qué datos adicionales necesitarías para elegir cuál poner en producción?

---

## Sesión 2 — Arquitectura CAG y conversaciones

### Idea central

CAG carga conocimiento acotado y relativamente estable en el contexto de la petición. Es una opción más simple que RAG cuando el material cabe, cambia poco y no exige buscar dinámicamente entre grandes volúmenes.

### Conceptos imprescindibles

- **CAG frente a RAG**: CAG “lleva el conocimiento encima”; RAG recupera en tiempo de consulta solo lo que parece relevante.
- **Presupuesto de contexto**: hay que reservar espacio para instrucciones, conocimiento, ejemplos, historial, petición y respuesta.
- **Calidad del contexto**: añadir más texto puede empeorar la respuesta. Importan la relevancia, el formato, los delimitadores, el orden y la ausencia de contradicciones.
- **Single-turn y multi-turn**: una conversación multi-turno requiere reenviar o recuperar el estado; el modelo no conserva memoria por sí mismo entre llamadas independientes.
- **Gestión del historial**: historial completo, ventana deslizante, resumen acumulativo o estrategia híbrida. Cada opción intercambia fidelidad, coste y longitud.
- **Arquitectura por responsabilidades**: transporte, servicio de negocio, schemas, configuración y datos de contexto deben evolucionar sin quedar mezclados en un único archivo.
- **Contratos y configuración**: los schemas estabilizan entradas y salidas; los secretos se gestionan mediante variables de entorno y nunca dentro del código.
- **Evolución gradual**: empezar con CAG evita introducir retrieval e infraestructura antes de demostrar que son necesarios.

### Debes poder explicar

Qué condiciones hacen que CAG sea suficiente y qué síntomas indican que el corpus, la actualización del conocimiento o el coste del contexto justifican migrar a RAG.

### Pregunta de control

¿Cómo repartirías una ventana de contexto limitada entre instrucciones, conocimiento, historial y respuesta, y qué recortarías primero?

---

## Sesión 3 — Wrappers, resiliencia y observabilidad

### Idea central

El proveedor del LLM debe quedar detrás de una interfaz propia. El producto necesita un contrato estable aunque cambien el SDK, el modelo, el proveedor o la forma de entregar la respuesta.

### Conceptos imprescindibles

- **Wrapper o capa de abstracción**: normaliza mensajes, parámetros, respuestas, errores y telemetría sin esconder las capacidades que realmente importan.
- **Acoplamiento y portabilidad**: desacoplar no significa fingir que todos los proveedores son idénticos; significa aislar sus diferencias.
- **Fallback con criterio**: autenticación inválida no se resuelve cambiando de modelo; un rate limit, timeout o error temporal puede admitir retry, backoff o rotación.
- **Routing por complejidad**: tareas simples y complejas pueden enviarse a modelos distintos para equilibrar coste y calidad.
- **Streaming**: mejora el tiempo percibido hasta el primer token. SSE suele encajar en respuestas unidireccionales; WebSockets, en interacción bidireccional.
- **Logging estructurado**: cada invocación debe correlacionar petición, modelo, proveedor, latencia, tokens, coste estimado, resultado y error sin registrar secretos o datos sensibles.
- **Trazabilidad**: hay que poder reconstruir qué ocurrió en una petición, no solo conservar mensajes sueltos.
- **Cache de respuestas**: exact match es seguro pero limitado; la similitud semántica amplía hits y también el riesgo de reutilizar una respuesta incorrecta.
- **Interfaz de prototipo**: Streamlit, Gradio o Chainlit aceleran validación, pero la elección depende del tipo de interacción y del camino previsto hacia producción.

### Debes poder explicar

La diferencia entre retry, fallback y routing, y por qué aplicarlos indiscriminadamente puede ocultar errores, duplicar costes o producir resultados inconsistentes.

### Pregunta de control

¿Qué campos mínimos registrarías para diagnosticar una respuesta lenta, cara o incorrecta sin exponer información sensible?

---

## Sesión 4 — De chat a producto de IA

### Idea central

Un producto de IA no es un chat con mejor diseño. Es un flujo con una interfaz adecuada a la tarea, prompts versionables, resultados estructurados, validaciones y políticas de fallo explícitas.

### Conceptos imprescindibles

- **Interfaz orientada a la tarea**: chat, formulario, asistente por pasos o resultado directo son decisiones de producto. La conversación no debe imponerse por defecto.
- **Prompt como artefacto de software**: instrucciones, contexto y formato de salida deben separarse, versionarse, probarse y componerse mediante plantillas.
- **Structured output**: JSON Schema o modelos tipados convierten texto probabilístico en un contrato que el backend puede validar y consumir.
- **Guardrails de entrada y salida**: pueden ser deterministas o basados en modelos. Deben aplicarse en capas, no confiar toda la seguridad a un único prompt.
- **Defense in depth**: validación de schema, reglas de negocio, límites, filtros de seguridad y revisión humana cubren fallos distintos.
- **Políticas de fallo**: rechazar, reparar/reintentar o degradar el resultado. La política depende del riesgo del caso de uso.
- **Cache semántica**: el umbral de similitud es una decisión de producto. Debe incluir en la clave las dimensiones que cambian la respuesta y almacenar solo salidas ya validadas.
- **Falsos positivos y coste**: más guardrails pueden añadir latencia, gasto y rechazos legítimos. También necesitan evaluación.

### Debes poder explicar

Por qué validar únicamente que la salida sea JSON no demuestra que sea correcta, segura ni coherente con las reglas del negocio.

### Pregunta de control

¿Qué controles pondrías antes y después del modelo en un estimador que devuelve horas y precios?

---

## Sesión 5 — Memoria, contexto dinámico y evaluación

### Idea central

La calidad de un sistema conversacional depende de gestionar explícitamente qué recuerda, qué fuentes consulta, cómo adapta el comportamiento y cómo demuestra que una modificación mejora el resultado.

### Conceptos imprescindibles

- **Historial frente a memoria**: el historial conserva turnos; la memoria mantiene hechos o decisiones relevantes de forma compacta. No son intercambiables.
- **Actualización y olvido**: la memoria puede extraerse con heurísticas o con un LLM, pero necesita reglas de vigencia, contradicción, sustitución y eliminación.
- **Contexto estático y dinámico**: archivos, web y datos del negocio cambian el contexto de cada petición y requieren procedencia, permisos y límites.
- **Adjuntos**: enviarlos directamente a un modelo multimodal simplifica el flujo; extraerlos localmente ofrece más control, normalización y reutilización.
- **Separación de datos**: el servicio de IA no debería acceder sin mediación a la base de datos del negocio; debe consumir contratos autorizados del backend.
- **Prompts por perfil o tier**: una variante de producto puede cambiar instrucciones, herramientas, pipeline y schema, no solamente el tono.
- **Actor–Critic–Boss**: un rol genera, otro cuestiona y un tercero decide. Aumenta calidad en tareas difíciles, pero multiplica coste y no arregla criterios mal definidos.
- **Tres familias de tests**: invariantes deterministas, métricas/tolerancias deterministas y evaluación subjetiva o LLM-as-judge.
- **Golden dataset**: conjunto versionado de casos representativos y resultados esperados con el que comparar cambios.

### Debes poder explicar

Cuándo conviene usar memoria compacta en lugar del historial completo y cómo evitar que un hecho antiguo o incorrecto se convierta en una instrucción permanente.

### Pregunta de control

¿Cómo demostrarías que un nuevo prompt mejora la estimación sin depender de “parece que responde mejor”?

---

## Sesión 6 — Datos empresariales e ingestión

### Idea central

La arquitectura de IA está limitada por la calidad, el linaje y la gobernanza de los datos. Vectorizar datos sin auditarlos solo hace que los defectos sean más difíciles de ver.

### Conceptos imprescindibles

- **Inventario antes de ingestión**: identificar fuentes, propietarios, formatos, volumen, frecuencia de actualización, sensibilidad y restricciones de acceso.
- **Calidad multidimensional**: completitud, consistencia, actualidad, fiabilidad y representatividad afectan de forma distinta a la utilidad de una fuente.
- **Linaje**: saber de dónde salió un dato, qué transformaciones sufrió y cuál es su fuente de verdad.
- **Decisión incluir/revisar/excluir**: no toda fuente disponible debe entrar en el sistema.
- **Documento canónico**: distintos parsers deben producir una representación común con contenido, metadatos, procedencia y errores.
- **Pipeline modular de ingestión**: extracción, limpieza, normalización, validación, enriquecimiento y persistencia son etapas separables y observables.
- **Normalización**: unificar formatos, unidades, fechas, identificadores y schemas sin borrar significado útil.
- **PII y GDPR**: minimización, base legítima, control de acceso, retención, anonimización o seudonimización y capacidad de borrado deben diseñarse antes de indexar.
- **Offline frente a online**: ingestión y enriquecimiento pesado suelen ocurrir fuera de la petición; retrieval y generación tienen presupuestos estrictos de latencia.
- **CAG, RAG o fine-tuning**: la elección depende del volumen, estabilidad, necesidad de actualización, trazabilidad y naturaleza del conocimiento.

### Debes poder explicar

Por qué un dataset grande, bien parseado y vectorizado puede seguir siendo una mala base para IA si carece de actualidad, permisos, linaje o consistencia.

### Pregunta de control

¿Qué información mínima incluirías en un catálogo de datos antes de autorizar una fuente para RAG?

---

## Sesión 7 — Embeddings y chunking

### Idea central

Un embedding representa significado como un vector. La utilidad de la búsqueda depende tanto del modelo de embeddings como de la unidad semántica que se decide vectorizar.

### Conceptos imprescindibles

- **Espacio vectorial**: textos semánticamente próximos tienden a ocupar posiciones cercanas; el vector no es una explicación ni una copia reversible del texto.
- **Similitud y distancia**: cosine, producto interno o distancia euclídea solo son comparables si el modelo y la configuración usan la métrica prevista.
- **Modelo de embeddings**: calidad, idioma, dominio, dimensionalidad, coste, latencia, ejecución local y licencias condicionan la elección.
- **Consistencia del modelo**: consulta y documentos deben estar embebidos en el mismo espacio; cambiar de modelo exige reindexar.
- **Chunking**: tamaño, solapamiento y fronteras determinan si cada fragmento contiene una idea recuperable con suficiente contexto.
- **Estrategias de chunking**: fijo, por estructura, semántico o específico de dominio. La estructura natural suele ser mejor que cortar por un número arbitrario.
- **JSON y datos estructurados**: hay que preservar identidad, campos relevantes y relaciones; serializar un objeto completo no siempre produce el mejor chunk.
- **Transcripciones**: turnos, hablantes, temas y ventanas de conversación ayudan a conservar el sentido.
- **Metadatos**: origen, documento, sección, fechas, permisos y posición permiten filtrar, citar y reconstruir contexto.
- **Evaluación**: la mejor estrategia es la que recupera fragmentos útiles para consultas reales, no la que genera más vectores.

### Debes poder explicar

Cómo un chunk demasiado pequeño pierde significado y uno demasiado grande diluye relevancia, aumenta coste y puede empeorar el ranking.

### Pregunta de control

¿Qué estrategia distinta aplicarías a un presupuesto JSON y a una transcripción, y qué metadatos conservarías en ambos?

---

## Sesión 8 — Bases de datos vectoriales

### Idea central

Una base vectorial aporta persistencia, filtrado, concurrencia e índices de búsqueda. No es necesaria por tener embeddings, sino cuando el volumen y los requisitos operativos superan una comparación en memoria.

### Conceptos imprescindibles

- **KNN exacto frente a ANN**: la búsqueda exacta prioriza precisión; la aproximada sacrifica algo de recall para reducir latencia a escala.
- **Esquema relacional**: separar documentos y chunks evita duplicación y permite mantener procedencia, permisos y versiones.
- **Métrica coherente**: la función de distancia del índice y de la consulta debe coincidir con la recomendada para el embedding.
- **HNSW**: grafo multicapa con buen rendimiento de consulta y coste notable de memoria y construcción.
- **IVFFlat**: particiona el espacio; requiere entrenamiento y ajuste del número de listas y probes.
- **DiskANN**: orientado a colecciones que ya no caben cómodamente en memoria y a uso intensivo de disco.
- **pgvector**: buena elección cuando Postgres ya forma parte del sistema y el volumen no justifica separar otra plataforma.
- **Tuning**: los parámetros de construcción y consulta equilibran memoria, latencia, velocidad de ingestión y recall.
- **Cuantización/halfvec**: reduce almacenamiento y memoria a cambio de una posible pérdida de precisión.
- **Verificación operativa**: `EXPLAIN ANALYZE`, latencias, recall, tamaño del índice, cache hit ratio y uso real del plan permiten detectar índices inútiles.
- **Señales de migración**: volumen, presión de memoria, latencia, throughput, multi-tenancy o capacidades de búsqueda pueden justificar una base especializada.

### Debes poder explicar

Por qué crear un índice ANN no garantiza que la consulta lo utilice ni que el sistema sea mejor que una búsqueda exacta para un corpus pequeño.

### Pregunta de control

¿Qué medirías para decidir entre búsqueda exacta, HNSW e IVFFlat en un caso real?

---

## Sesión 9 — Fundamentos de RAG

### Idea central

RAG separa el conocimiento del prompt y recupera contexto en tiempo de consulta. Su calidad está dominada por lo que recupera y por cómo convierte esos fragmentos en evidencia utilizable.

### Conceptos imprescindibles

- **Cuatro etapas**: ingestión/indexación, retrieval, augmentation y generación.
- **CAG frente a RAG**: RAG compensa cuando el corpus es grande, cambia con frecuencia o cada usuario solo puede acceder a una parte.
- **Query reformulation**: limpiar, expandir o estructurar la intención mejora la búsqueda, pero puede deformarla si el modelo inventa detalles.
- **Top-K**: controla cuántos candidatos entran; un K alto aumenta recall y ruido, coste y riesgo de contradicción.
- **Threshold**: permite abstenerse cuando ningún resultado supera una relevancia mínima.
- **Filtros de metadatos**: permisos, tenant, tipo, fecha o dominio reducen el universo antes o durante la búsqueda.
- **Precision frente a recall**: recuperar más evidencia relevante y evitar evidencia irrelevante son objetivos en tensión.
- **Augmentation**: los chunks necesitan delimitadores, identidad, procedencia, orden y un presupuesto de tokens.
- **Lost in the middle**: la posición del contexto influye; la evidencia crítica no debe quedar enterrada.
- **Truncamiento defensivo**: es preferible excluir un chunk completo que cortar una idea y presentarla como evidencia válida.
- **Grounding y abstención**: el prompt debe obligar a usar las fuentes, distinguir inferencias y admitir que no hay evidencia.
- **Capa de datos como servicio**: retrieval debe tener un contrato aislado, autenticación, rate limits, idempotencia y logging por etapa.

### Debes poder explicar

Por qué mejorar el modelo generador no corrige un retriever que trae documentos irrelevantes o deja fuera la evidencia necesaria.

### Pregunta de control

Si una consulta no supera el threshold, ¿qué debería hacer el sistema y qué información debería devolver al usuario o al operador?

---

## Sesión 10 — Retrieval avanzado

### Idea central

La relevancia no es únicamente cercanía semántica. Un retrieval robusto combina señales y añade complejidad solo cuando una evaluación muestra que la mejora justifica latencia y coste.

### Conceptos imprescindibles

- **Búsqueda híbrida**: combina recuperación léxica, buena para términos exactos, con recuperación vectorial, buena para equivalencia semántica.
- **Reciprocal Rank Fusion (RRF)**: fusiona rankings por posición sin asumir que sus puntuaciones están en la misma escala.
- **Bi-encoder frente a cross-encoder**: el primero codifica por separado y recupera rápido; el segundo lee consulta y candidato juntos y ordena mejor a mayor coste.
- **Recall-then-rerank**: recuperar una lista amplia y barata, reordenarla y devolver un top-K pequeño.
- **Expansión de consulta**: genera formulaciones alternativas de la misma intención.
- **Descomposición**: divide una pregunta compuesta en subconsultas cuyas respuestas se combinan después.
- **Filtrado contextual**: reglas de negocio, tenant, tecnología o tipo de proyecto pueden importar más que la similitud textual.
- **Relevancia temporal**: fecha, vigencia y decaimiento permiten que evidencia obsoleta no domine por parecerse más.
- **Multiíndice y routing**: colecciones heterogéneas pueden requerir índices separados y una decisión explícita sobre dónde buscar.
- **Golden set de retrieval**: consultas reales con documentos relevantes anotados para medir precision@K, recall y errores.
- **Trade-off medible**: la ganancia de calidad debe compararse con latencia, coste y complejidad operativa.

### Debes poder explicar

Por qué no se deben mezclar directamente scores de búsqueda léxica y vectorial y cómo RRF evita ese problema.

### Pregunta de control

¿En qué orden aplicarías filtros, búsqueda híbrida, fusión y reranking, y qué coste añade cada etapa?

---

## Sesión 11 — Generación y calidad en RAG

### Idea central

Una respuesta RAG útil debe estar anclada en evidencia, reconocer contradicciones, citar fuentes resolubles, abstenerse cuando corresponda y someterse a evaluación continua.

### Conceptos imprescindibles

- **Content augmentation**: limpiar, deduplicar, comprimir, ordenar y priorizar el contexto recuperado antes de generar.
- **Compresión extractiva y abstractiva**: extraer conserva fidelidad; resumir ahorra más tokens, pero puede introducir distorsión.
- **Síntesis de fuentes**: las fuentes pueden contradecirse. Conviene ponderarlas por actualidad, similitud, calidad y autoridad antes de pedir una conclusión.
- **Rango e incertidumbre**: una síntesis honesta no oculta divergencias detrás de una media.
- **Citas verificables**: deben referenciar un identificador y localizador existentes; el backend resuelve enlaces aplicando permisos.
- **Integridad referencial**: ninguna cita debería apuntar a una fuente inexistente, no recuperada o no autorizada.
- **Alucinación factual, numérica y de atribución**: cada tipo requiere controles distintos.
- **Detección escalonada**: primero invariantes y anclaje numérico baratos; después verificación semántica o consistencia cuando el riesgo lo exige.
- **Mitigación**: mejor contexto, salida estructurada, validación, reintento acotado, degradación y abstención.
- **RAGAS**: separa dimensiones como fidelidad al contexto, relevancia de respuesta y precisión/recall del contexto.
- **Golden set**: sin referencias de calidad, algunas métricas solo son proxies y no una verdad absoluta.
- **Versionado de embeddings**: cada vector debe identificar modelo, versión, dimensión y estrategia de chunking.
- **Reindexación segura**: construir una versión paralela, validarla y cambiar tráfico evita mezclar espacios incompatibles.

### Debes poder explicar

La diferencia entre una respuesta fluida, una respuesta fiel a las fuentes y una respuesta realmente correcta.

### Pregunta de control

¿Qué comprobarías antes de mostrar una cifra y su cita como resultado definitivo de una estimación?

---

## Sesión 12 — Introducción a agentes

### Idea central

Un agente es adecuado cuando el modelo debe decidir dinámicamente qué acción ejecutar a continuación. Si la secuencia ya es conocida, un workflow determinista suele ser más barato, predecible y fácil de probar.

### Conceptos imprescindibles

- **Tarea, workflow y agente**: una tarea es una ejecución; un workflow codifica una secuencia; un agente decide parte de esa secuencia en runtime.
- **Bucle agéntico**: razonar/planificar, actuar, observar el resultado y repetir hasta terminar, delegar o detenerse.
- **Function calling**: el modelo propone una llamada estructurada; la aplicación valida y ejecuta. El modelo no ejecuta código ni obtiene permisos por declarar una tool.
- **Contrato de una tool**: nombre, descripción, schema de parámetros, resultado, errores y efectos laterales.
- **Diseño de tools**: herramientas pequeñas, inequívocas, con nombres claros y el mínimo conjunto necesario mejoran selección y seguridad.
- **Resultado estructurado**: el agente necesita una condición de salida y un contrato final consumible por el sistema.
- **Patrones**: un paso o iterativo; reactivo o proactivo; plan fijo o dinámico. La forma debe ajustarse a la incertidumbre de la tarea.
- **Límites de ejecución**: máximo de pasos, tiempo, tokens, coste, retries y herramientas autorizadas.
- **Handover humano**: el agente debe saber cuándo no dispone de evidencia, permiso o confianza suficiente.
- **Coste multiplicativo**: cada vuelta añade tokens de historial, decisión y observación. La autonomía puede costar varias veces una llamada simple.
- **Trazas**: optimizar un agente exige observar cada decisión, tool, resultado, coste y motivo de parada.

### Debes poder explicar

Qué capacidad concreta compra el bucle agéntico y por qué envolver un pipeline fijo en un agente añade autonomía aparente, no valor.

### Pregunta de control

¿Qué condiciones de parada impedirían que un agente quede en bucle o siga gastando después de perder la capacidad de avanzar?

---

## Sesión 13 — Orquestación con grafos

### Idea central

Cuando un bucle manual acumula ramas, paralelismo, pausas y reanudación, un grafo explícito hace visibles el estado y el control flow. El framework ayuda a orquestar; no decide una buena arquitectura por ti.

### Conceptos imprescindibles

- **Cuándo usar un framework**: cuando persistencia, branching, ciclos, reanudación u observabilidad justifican su impuesto de abstracción.
- **StateGraph**: combina estado tipado, nodos que producen actualizaciones y aristas que definen secuencia o decisiones.
- **Estado mínimo**: debe contener lo necesario para continuar y auditar; guardar todo aumenta coste, acoplamiento y exposición de datos.
- **Nodos**: conviene que tengan responsabilidad clara, entradas/salidas tipadas y efectos laterales controlados.
- **Reducers**: definen cómo se combinan actualizaciones, especialmente en listas y ramas paralelas. Una mala política puede perder o duplicar estado.
- **Checkpointer**: persiste snapshots por ejecución/thread para reanudar, depurar y soportar intervención humana.
- **Memoria corta y larga**: el checkpoint recupera una ejecución; la memoria entre ejecuciones es otra responsabilidad.
- **Fan-out/fan-in**: ramas independientes pueden ejecutarse en paralelo y luego reducir sus resultados.
- **Enrutado condicional**: el estado determina el siguiente nodo. Los ciclos deben tener contador, condición de progreso y salida.
- **Errores diferenciados**: retry para fallos transitorios, fallback para alternativas válidas, timeout para límites y revisión humana para riesgo o ambigüedad.
- **Observabilidad**: hay que ver ruta, estado relevante, tool calls, latencia, tokens, excepciones y reanudaciones.
- **LangSmith y observabilidad full-stack**: una herramienta centrada en LLM ayuda con trazas agénticas; una full-stack conecta el flujo con API, infraestructura y negocio.

### Debes poder explicar

La diferencia entre estado, checkpoint y memoria, y por qué persistir el estado completo sin diseño puede ser caro y peligroso.

### Pregunta de control

¿Qué parte de un flujo ejecutarías en paralelo y cómo definirías la combinación determinista de sus resultados?

---

## Sesión 14 — Sistemas multiagente y patrones avanzados

### Idea central

Un sistema multiagente está justificado cuando varias responsabilidades necesitan decisiones, herramientas, contextos o ritmos de evolución propios. La diferencia esencial no es tener más nodos, sino quién controla el siguiente paso.

### Conceptos imprescindibles

- **Workflow frente a sistema agéntico**: en un workflow el código posee el control flow; en un sistema agéntico el modelo decide parte de la ruta en ejecución.
- **Señales para separar agentes**: prompts con dominios mezclados, demasiadas tools en un único espacio de decisión, orden no predecible y responsabilidades que evolucionan de manera independiente.
- **Cuándo no hacerlo**: flujo fijo, prompt deficiente, ausencia de observabilidad o complejidad sin beneficio medible.
- **Cooperación**: cada especialista aporta una pieza ortogonal. Es eficiente, pero un error temprano puede contaminar el resto.
- **Competición**: varios agentes resuelven la misma tarea con criterios realmente distintos y un sintetizador compara. La divergencia es una señal de incertidumbre.
- **Falsa diversidad**: mismos datos, mismo modelo y prompts casi idénticos producen errores correlacionados; pagar varias llamadas no crea una segunda opinión real.
- **Síntesis**: no debe promediar a ciegas. Debe explicar desacuerdos, usar evidencia y devolver rango, confianza o escalado cuando la divergencia es alta.
- **Supervisor**: decide el siguiente trabajador mediante una salida tipada. Cada trabajador devuelve control o finaliza según un contrato visible.
- **Supervisor híbrido**: reglas deterministas para rutas conocidas y modelo solo para decisiones ambiguas reducen coste y no determinismo.
- **Topologías**: plana para pocos especialistas; jerárquica cuando el número o los dominios crecen, aceptando más latencia y complejidad.
- **Comunicación por estado compartido**: simple y trazable dentro de un proceso, pero puede producir un estado grande y muy acoplado.
- **Handoff directo**: un agente transfiere control y un digest mínimo al siguiente; reduce el cuello de botella central, pero complica la trazabilidad global.
- **Mensajes/eventos**: desacoplan procesos y escalan mejor; exigen contratos versionados, correlación, idempotencia y consistencia eventual.
- **Human-in-the-loop**: `interrupt` debe persistir una pausa en el checkpointer y exponer un contrato de estado pendiente, decisión humana y reanudación.
- **Qué debe detener el sistema**: acciones irreversibles, coste alto, baja confianza, contradicción fuerte o falta de permisos. No cada decisión rutinaria.
- **Mínimo privilegio**: cada agente recibe únicamente las tools y recursos necesarios. El prompt no es un control de seguridad.
- **Validación de acciones**: incluso una tool permitida debe validar argumentos, ámbito, límites y autorización antes de ejecutar.
- **Auditoría**: identidad del agente, decisión, tool, argumentos seguros, resultado, timestamp, correlación y aprobación humana deben quedar registrados.
- **Costes estructurales**: routing adicional, pérdida de contexto en handoffs, no determinismo, mayor superficie de fallo y carga cognitiva.
- **Testing**: comprobar decisiones tipadas, invariantes, permisos, límites y resultado; no exigir siempre una ruta exacta si varias son válidas.

### Debes poder explicar

1. Qué límite del grafo de un solo agente obliga realmente a separar responsabilidades.
2. Por qué cooperación sirve para descomponer trabajo y competición para hacer visible la incertidumbre.
3. Qué patrón de comunicación elegirías y qué información mínima transferirías.
4. Cómo se pausa y reanuda una ejecución sin perder estado ni repetir efectos.
5. Por qué mínimo privilegio, validación y auditoría son capas distintas.

### Pregunta de control

Diseña de palabra un sistema multiagente para estimación: ¿qué agentes tendría, quién enruta, qué estado comparten, qué tools recibe cada uno, qué acciones requieren aprobación y cómo medirías si el sistema mejora al grafo anterior?

---

## Sesión 15 — Puesta en producción, arquitectura e infraestructura

### Idea central

Producción no es un entorno al que se copia una demo: es una promesa de comportamiento, disponibilidad, seguridad y operación. Llegar a ella exige hacer explícitas las fronteras del sistema, empaquetar servicios reproducibles y desplegar solo lo que se puede verificar y mantener.

### Conceptos imprescindibles

- **Producción como contrato**: define qué mira a la calle, qué disponibilidad promete y qué ocurre cuando una dependencia falla.
- **Frontera pública e interna**: el backend de negocio puede ser público mientras el servicio IA, la base vectorial y la base relacional permanecen en la red privada.
- **Separación con criterio**: partir en servicios compra aislamiento, escalado o ciclos de cambio independientes; no justifica microservicios por sí mismo.
- **Contrato entre servicios**: endpoints, schemas, errores, timeouts, autenticación y versionado forman la frontera hecha código.
- **Contenedores reproducibles**: un `Dockerfile` debe fijar runtime y dependencias, aprovechar caché de capas y exponer un healthcheck barato.
- **Configuración y secretos**: variables de entorno y un gestor de secretos separan configuración por entorno de la imagen; ningún secreto debe entrar en la imagen o el repositorio.
- **Dependencias de arranque**: `docker compose` y los healthchecks expresan orden y disponibilidad real, no solo que un proceso haya arrancado.
- **Autenticación servicio a servicio**: una red privada no sustituye la autorización; el servicio IA debe validar identidad, alcance y límites de cada llamada.
- **CI/CD seguro**: los tests unitarios mockean el modelo para probar el código propio; un smoke test acotado comprueba la integración real sin exponer credenciales.
- **Cloud y red**: subredes, security groups, DNS interno, TLS y egress convierten la arquitectura dibujada en una frontera operable.
- **Síncrono hasta que duela**: mantener una petición síncrona reduce complejidad; colas y asincronía se introducen cuando el tiempo de trabajo o la resiliencia lo exige.
- **Runbook y documentación viva**: quien opera necesita síntomas, comandos seguros, causas frecuentes, rollback y criterios de escalado; el código y el contrato deben ser la fuente de verdad.

### Debes poder explicar

Qué debe quedar público, qué debe quedar interno y qué comprobaciones demostrarían que los contenedores, contratos, secretos y healthchecks están listos para operar.

### Pregunta de control

Si separaras el backend de negocio y el servicio IA, ¿qué contrato mínimo, autenticación, healthcheck, timeout y prueba de despliegue impedirían que una caída o una imagen mal configurada se propagase al usuario?

---

## Sesión 16 — Calidad, observabilidad y LLMOps

### Idea central

Desplegar un sistema de IA solo inicia su vida operativa. La calidad debe definirse con casos representativos, medirse con un harness reproducible, vigilarse en producción y equilibrarse continuamente con coste, latencia, seguridad y capacidad de abstención.

### Conceptos imprescindibles

- **LLMOps**: versiona y opera modelos, prompts, datos de evaluación, configuración y comportamiento, no solo el código de la aplicación.
- **Golden set**: conjunto versionado de casos reales y límites, con rangos aceptables, casos de abstención y criterios explícitos de “bueno”.
- **Evaluation harness**: ejecuta el golden set de forma repetible y registra resultado, error, latencia, coste y versión para comparar cambios.
- **Regresión multidimensional**: una mejora en acierto puede empeorar cobertura, abstención, latencia, coste o seguridad; hay que observar el conjunto de KPIs.
- **“No lo sé”**: la abstención es un resultado correcto cuando falta evidencia, la confianza cae o la petición está fuera de alcance.
- **Guardrails en capas**: filtros de entrada, validación de salida, reglas de negocio y autorización son controles distintos; una frase en el prompt no es seguridad.
- **Compliance-by-design**: minimización, permisos, retención, trazabilidad y revisión humana se incorporan al flujo desde el diseño.
- **Observabilidad frente a evaluación**: evaluar compara respuestas con un criterio; observar explica qué ocurre con el sistema real, sus rutas, dependencias y usuarios.
- **Trace completo**: correlaciona petición, modelo, prompt, retrieval, tools, tokens, coste, latencia, errores y decisión final sin registrar secretos innecesarios.
- **Feedback loops**: feedback humano, errores y casos difíciles alimentan el golden set y priorizan nuevas evaluaciones; no se optimiza a partir de anécdotas.
- **Coste y latencia**: cachear, enrutar a modelos adecuados y medir por operación puede abaratar sin degradar calidad; el precio aislado del token no basta.
- **A/B testing**: compara variantes con tráfico controlado y métricas de calidad y negocio, con criterios de parada y rollback.
- **Self-hosting**: modelos locales o en GPU propia aportan privacidad y control, pero trasladan al equipo la operación, capacidad, actualizaciones y coste fijo.

### Debes poder explicar

Cómo demostrarías que una nueva versión conserva la calidad del golden set, sabe abstenerse, no rompe un KPI, y puede investigarse cuando en producción aparece una petición lenta o incorrecta.

### Pregunta de control

¿Qué casos incluirías en un golden set de estimación y qué señales del trace usarías para decidir entre mantener una variante, hacer rollback, escalar a una persona o cambiar de modelo?

---

## Las ideas que conectan todas las sesiones

Al terminar las 16 sesiones deberías reconocer estos principios transversales:

- **La complejidad debe comprarse con una necesidad demostrable**: CAG antes que RAG si basta; workflow antes que agente si la ruta es fija; un agente antes que varios si la especialización no aporta.
- **El contexto es un producto diseñado**: seleccionar, ordenar, delimitar, versionar y presupuestar contexto importa tanto como elegir modelo.
- **Los contratos reducen incertidumbre**: schemas de entrada/salida, tools tipadas, estado tipado, citas resolubles y eventos versionados convierten probabilidades en sistemas operables.
- **Los datos mandan**: calidad, procedencia, permisos y actualización limitan el techo del sistema más que el modelo.
- **La evaluación precede a la optimización**: golden sets, métricas de retrieval, evals de generación, latencia y coste deben justificar cada capa nueva.
- **La seguridad no vive en el prompt**: autenticación, autorización, mínimo privilegio, validación, aislamiento, auditoría e intervención humana pertenecen al sistema.
- **La observabilidad es parte de la arquitectura**: sin trazas no se pueden explicar decisiones, reproducir fallos ni controlar costes.
- **Toda autonomía necesita límites**: pasos, tiempo, tokens, dinero, permisos, condiciones de salida y escalado humano.

Si puedes defender estas decisiones con sus trade-offs —no solo definir los términos— habrás entendido el núcleo del programa.
