---
title: "✍️ Migración a pgvector + endpoint de búsqueda 🔴"
source_url: "https://training.lidr.co/posts/ai-engineering-202604-✍️-migracion-a-pgvector-endpoint-de-busqueda-🔴"
archived_at: "2026-06-12T09:06:35.111Z"
group: "08-session"
---

# ✍️ Migración a pgvector + endpoint de búsqueda 🔴

![Antonio Perez](./assets/c3eccac37426c36f.jpg)

[Antonio Perez](https://training.lidr.co/members/36030888)

⏱**La fecha límite es martes 9 de junio al final del día.**

## Objetivo

Persistir el pipeline construido en la Sesión 07 en PostgreSQL + pgvector y exponer un endpoint de búsqueda semántica funcional sobre los presupuestos históricos. Al terminar, el servicio IA debe:

1. 

Levantar un Postgres con pgvector como dependencia declarada del proyecto.

1. 

Tener un esquema relacional propio (tablasdocumentsychunks) gestionado con migraciones Alembic.

1. 

Persistir cada presupuesto ingestado como undocumentcon sus correspondienteschunks(cada uno con su embedding)**en una sola transacción**.

1. 

Resolver una query semántica vía SQL devolviendo los k chunks más cercanos por distancia coseno.

## Lo que NO se hace en este ejercicio

Estos cuatro temas se abordan deliberadamente en directo. Si los adelantas, te pierdes la mitad del valor de la sesión en vivo:

- 

**Índices vectoriales**(HNSW, IVFFlat). El sequential scan es el baseline contra el que mediremos el impacto del índice en directo.

- 

**Filtros por metadata**(WHERE chunk_type = 'budget_component',WHERE metadata->>'sector' = 'fintech'). Los exploramos en directo, comparando planes de ejecución con y sin filtros selectivos.

- 

**Búsqueda híbrida**(full-text search + vector). Se construye en directo sobre tu código.

- 

**Tuning de parámetros**(shared_buffers,maintenance_work_mem,ef_search). Defaults durante todo el ejercicio.

Resiste la tentación de "ir más allá": la disciplina de scoping es parte del ejercicio.

## Stack y dependencias

Añade alpyproject.tomldel servicio IA:

toml

sqlalchemy>=2.0 asyncpg>=0.29 pgvector>=0.3 alembic>=1.13

asyncpges el driver async oficial recomendado por SQLAlchemy 2.0 para Postgres.pgvectores el paquete Python que registra el tipovectoren SQLAlchemy y expone los operadores de distancia (l2_distance,cosine_distance,max_inner_product) como métodos invocables desde el ORM.

## Paso 1 — Postgres con pgvector en docker-compose

Añade aldocker-compose.ymlun serviciopostgrescon la imagen oficial de pgvector. Esta imagen es Postgres 16 con la extensiónvectorprecompilada e instalable con un soloCREATE EXTENSION.

yaml
services: postgres: image: pgvector/pgvector:pg16 environment: POSTGRES_DB: estimator POSTGRES_USER: estimator POSTGRES_PASSWORD: estimator ports: - "5432:5432" volumes: - postgres_data:/var/lib/postgresql/data healthcheck: test: ["CMD-SHELL", "pg_isready -U estimator -d estimator"] interval: 5s timeout: 5s retries: 10 ai_service: # ... configuración existente ... depends_on: postgres: condition: service_healthy environment: DATABASE_URL: postgresql+asyncpg://estimator:estimator@postgres:5432/estimator volumes: postgres_data:

**Verifica antes de continuar:**

bash

docker compose up postgres docker compose exec postgres psql -U estimator -d estimator -c "SELECT version();"

Si esto no funciona, no avances al Paso 2.

## Paso 2 — Configurar Alembic en el servicio IA

Inicializa Alembic con plantilla async:

bash

docker compose run --rm ai_service alembic init -t async alembic

Configuraalembic.iniyalembic/env.pypara que tomen la URL de conexión de la variable de entornoDATABASE_URLy para que reconozcan el tipovectorde pgvector. Sin esto,alembic checkno detecta correctamente las columnas vector y produce migraciones inconsistentes.

Enenv.py, dentro dedo_run_migrations:

python
import pgvector.sqlalchemy def do_run_migrations(connection): connection.dialect.ischema_names["vector"] = pgvector.sqlalchemy.Vector context.configure( connection=connection, target_metadata=target_metadata, ) with context.begin_transaction(): context.run_migrations()
## Paso 3 — Esquema de base de datos

Crea la primera migración con la extensiónvectormás dos tablas. Los nombres de columnas son los que esperan los pasos siguientes; si los cambias, ajusta todo el código del ejercicio en consecuencia.

python
# alembic/versions/0001_initial_schema.py from alembic import op import sqlalchemy as sa from sqlalchemy.dialects import postgresql from pgvector.sqlalchemy import Vector def upgrade(): op.execute("CREATE EXTENSION IF NOT EXISTS vector") op.create_table( "documents", sa.Column("id", sa.BigInteger, primary_key=True), sa.Column("source_path", sa.Text, nullable=False), sa.Column("document_type", sa.String(50), nullable=False), sa.Column("ingested_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False), sa.Column("metadata", postgresql.JSONB, server_default="{}", nullable=False), ) op.create_index("ix_documents_source_path", "documents", ["source_path"]) op.create_table( "chunks", sa.Column("id", sa.BigInteger, primary_key=True), sa.Column("document_id", sa.BigInteger, sa.ForeignKey("documents.id", ondelete="CASCADE"), nullable=False), sa.Column("chunk_type", sa.String(50), nullable=False), sa.Column("content", sa.Text, nullable=False), sa.Column("embedding", Vector(1536), nullable=True), sa.Column("metadata", postgresql.JSONB, server_default="{}", nullable=False), sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False), ) op.create_index("ix_chunks_document_id", "chunks", ["document_id"]) op.create_index("ix_chunks_chunk_type", "chunks", ["chunk_type"]) op.create_index("ix_chunks_metadata_gin", "chunks", ["metadata"], postgresql_using="gin")

Ejecuta la migración:

bash

docker compose run --rm ai_service alembic upgrade head

**Decisiones de schema que vas a tener que justificar en el README**(las defenderás en directo si te tocan):

- 

**Dos tablas en vez de una.**Un presupuesto produce N chunks. Una sola tabla con la metadata del documento duplicada en cada fila pierde integridad referencial y duplica datos. Con dos tablas yON DELETE CASCADE, eliminar un presupuesto elimina automáticamente todos sus chunks.

- 

metadata JSONB**en ambas tablas.**Metadata estable (tipo de documento, tipo de chunk, fechas) en columnas tipadas; metadata variable o que el chunker puede enriquecer (tags, scope, tecnologías mencionadas) en JSONB. El índice GIN sobre el JSONB permite consultar por claves arbitrarias sin migrar el schema cada vez.

- 

vector(1536)**.**Dimensionalidad detext-embedding-3-small. Está hardcodeada porque cambiarla implica re-embedear todo el corpus, así que no es una decisión que vaya a cambiar dinámicamente.

- 

embedding nullable**.**Permite insertar un chunk en una transacción y rellenar el embedding después si el cálculo fallase. En este ejercicio no lo usaremos así (ingestaremos chunk+embedding atómicamente), pero deja la puerta abierta a la ingesta asíncrona que veremos en sesiones posteriores.

- 

**No hay índice vectorial.**Deliberado. El directo lo añade.

## Paso 4 — RefactorizarPOST /embeddings/ingest

El endpoint pasa de devolver chunks+vectores en la respuesta a persistirlos en una transacción y devolver únicamente los identificadores y métricas de la ingesta.

**Contrato final del endpoint:**

Request:

json
{ "source_path": "data/budgets/budget_2024_q1_fintech.json", "document_type": "historical_budget", "content": { /* JSON completo del presupuesto, tal cual viene del chunker */ } }

Response (200 OK):

json
{ "document_id": 42, "chunks_created": 17, "embedding_dimension": 1536, "ingestion_time_ms": 1240 }

Response (409 Conflict) si ya existe un documento con esesource_path:

json
{ "detail": "Document already ingested", "document_id": 42 }

**Implementación.**Dentro de una sola sesión async de SQLAlchemy:

1. 

Verifica que no existe ya un documento con esesource_path.

1. 

Crea la fila endocuments.

1. 

Ejecuta el chunker estructural sobre el JSON.

1. 

Llama al embedder por lotes (no chunk a chunk — un únicoembeddings.createcon un array de inputs).

1. 

Crea todas las filas enchunksconadd_all.

1. 

Commit.

La transacción única garantiza que un fallo en el embedder no dejadocumentshuérfanos sin chunks.

## Paso 5 — Nuevo endpointPOST /search

**Contrato:**

Request:

json
{ "query": "REST API with OAuth authentication for fintech sector", "k": 5 }

Response:

json
{ "query": "REST API with OAuth authentication for fintech sector", "k": 5, "search_time_ms": 87, "results": [ { "chunk_id": 156, "document_id": 12, "chunk_type": "budget_component", "content": "Backend service implementation with JWT-based authentication...", "distance": 0.231, "metadata": { "scope": "backend", "technologies": ["python", "fastapi"] } } ] }

**Implementación de la query.**Embedea la query con el mismo modelo que se usó en ingesta (text-embedding-3-small) y ejecuta vía SQLAlchemy:

python
from sqlalchemy import select stmt = ( select( Chunk.id, Chunk.document_id, Chunk.chunk_type, Chunk.content, Chunk.metadata, Chunk.embedding.cosine_distance(query_vector).label("distance"), ) .order_by(Chunk.embedding.cosine_distance(query_vector)) .limit(k) ) result = await session.execute(stmt)

**Por qué**cosine_distance**(operador**<=>**).**Los embeddings de OpenAI están normalizados, así quecosine_distanceeinner_productdarían resultados equivalentes. Usamos cosine por consistencia con la convención más común en literatura RAG y para que, cuando en el directo añadamos el índice HNSW convector_cosine_ops, los operadores y la operator class del índice estén alineados. Esta alineación es importante: si la query usa un operador y el índice está construido con otra operator class, Postgres ignora el índice silenciosamente y cae a sequential scan sin avisar. Lo veremos en vivo.

**Nota sobre rendimiento.**En esta fase no hay índice. Postgres hace sequential scan completo. Para el volumen del corpus de ejemplo del programa (decenas de documentos, cientos de chunks), eso es perfectamente aceptable y el endpoint responde en pocos cientos de ms. No te preocupes por la latencia — observarla sin índice es justamente uno de los puntos de partida del directo.

## Paso 6 — Scriptquery_examples.py

Reemplaza elcompare.pyde la Sesión 07 (que medía similitud entre pares de textos sueltos) por un script que invoca el endpoint/searchcon cinco queries representativas y formatea los resultados.

Las cinco queries deben ejercitar el dataset desde ángulos distintos:

1. 

**Componente directo conocido.**Una query que sabes que debería tener un match casi perfecto contra al menos un chunk del corpus. Sanity check.

- 

Ejemplo:"REST API development with JWT authentication for financial sector"

1. 

**Reformulación semántica.**La misma idea conceptual con vocabulario distinto al del corpus. Mide si los embeddings capturan significado o solo palabras.

- 

Ejemplo:"secure backend service with token-based access control for banking applications"

1. 

**Dominio distinto.**Una query sobre algo que no debería estar en el corpus. Los resultados deberían tener distancia alta o ser claramente irrelevantes.

- 

Ejemplo:"mobile application for restaurant reservations"

1. 

**Consulta ambigua.**Corta y genérica, que muchos chunks podrían matchear parcialmente. Útil para observar cómo se comporta el ranking en ausencia de un match dominante.

- 

Ejemplo:"integration with external system"

1. 

**Consulta muy específica.**Vocabulario técnico preciso. Pone a prueba si el modelo distingue entre tecnologías relacionadas.

- 

Ejemplo:"migration from monolith to microservices architecture using Kubernetes"

Para cada query, imprime el top-5 de resultados con:chunk_id,distance(4 decimales),chunk_typey los primeros ~120 caracteres delcontent. Formato libre, pero legible en terminal.

## Entregable

Repositorio que contenga:

1. 

docker-compose.ymlactualizado con el serviciopostgres.

1. 

Migración Alembic con la creación del schema (extensión + dos tablas + índices no-vectoriales).

1. 

EndpointPOST /embeddings/ingestrefactorizado para persistir, con manejo del caso de documento duplicado.

1. 

EndpointPOST /searchnuevo, funcional.

1. 

Scriptquery_examples.pyejecutable condocker compose run --rm ai_service python query_examples.py.

1. 

Archivooutput_examples.txtcon el output del script ejecutado contra el corpus de ejemplo del programa.

1. 

Sección nueva en el README del proyecto, máximo una página, justificando: (a) por qué dos tablas y no una, (b) por quémetadatacomo JSONB en lugar de columnas, (c) por quécosine_distancey no L2 ni inner product, (d) por qué deliberadamente no hay índice vectorial todavía.

## Cómo entregar

Envía por mail a[lia@lidr.co](mailto:lia@lidr.co), el enlace a la rama (URL completa de GitHub, GitLab o el servicio que uses). El plazo es estricto: necesitamos margen para revisar las entregas y preparar el material de la sesión basándonos en los problemas reales que hayáis encontrado.

Asegúrate de que la rama es accesible (público o, si es privado, con permisos para el revisor que se te indicará en el canal del programa).

Si llegas a la sesión sin haber entregado, podrás seguir el directo igualmente, pero los bloques hands-on darán por sentado que el pipeline básico funciona. No es el lugar ni el momento para depurar problemas de setup.
