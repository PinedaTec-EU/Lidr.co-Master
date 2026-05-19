# estimator-cag

Servicio FastAPI para estimar proyectos software con prompts versionados en Jinja2, ejecución asíncrona de peticiones e histórico visible desde el portal.

## Qué hace ahora

- mantiene el endpoint síncrono `POST /api/v1/estimate`
- expone una cola ligera en memoria para crear jobs asíncronos
- permite listar histórico, peticiones pendientes, en ejecución, completadas y fallidas
- deja la UI libre: crear una petición devuelve `202 Accepted` y el frontend consulta estados aparte

## Arquitectura

```mermaid
flowchart LR
    UI["Streamlit portal de peticiones"]
    API["FastAPI"]
    JOBS["EstimationJobService"]
    STORE["InMemoryEstimationJobStore"]
    USECASE["EstimationService"]
    PROMPTS["Jinja prompts v1"]
    LLM["LiteLLM gateway"]

    UI -->|POST /estimate-jobs| API
    UI -->|GET /estimate-jobs| API
    UI -->|GET /estimate-jobs/{id}| API
    API --> JOBS
    JOBS --> STORE
    JOBS --> USECASE
    USECASE --> PROMPTS
    USECASE --> LLM
```

## Estructura relevante

```text
app/
├── application/
│   ├── estimation.py
│   └── estimation_jobs.py
├── prompts/
│   ├── loader.py
│   └── estimation/
│       └── v1/
│           ├── examples.j2
│           ├── system.j2
│           └── user.j2
├── routers/
│   └── estimations.py
├── services/
│   ├── job_store.py
│   └── llm_service.py
├── dependencies.py
└── schemas.py
```

## API

### `GET /health`

```json
{
  "status": "ok",
  "service": "estimator-cag",
  "version": "0.1.0"
}
```

### `POST /api/v1/estimate`

Sigue disponible para ejecución síncrona.

Request:

```json
{
  "description": "Necesitamos una plataforma SaaS para reservas con pagos, roles y panel operativo.",
  "project_type": "web_saas",
  "detail_level": "medium",
  "output_format": "phases_table"
}
```

Response:

```json
{
  "text": "## Estimación...\n",
  "prompt_version": "v1"
}
```

### `POST /api/v1/estimate-jobs`

Crea una petición asíncrona.

Response `202`:

```json
{
  "id": "c927f6d0d6df4f4ea99d7ab9f3a7ec68",
  "status": "pending",
  "created_at": "2026-05-14T18:00:00+00:00",
  "updated_at": "2026-05-14T18:00:00+00:00",
  "request": {
    "description": "Necesitamos una plataforma SaaS para reservas con pagos, roles y panel operativo.",
    "project_type": "web_saas",
    "detail_level": "medium",
    "output_format": "phases_table"
  },
  "prompt_version": "v1",
  "response": null,
  "error_message": null
}
```

### `GET /api/v1/estimate-jobs`

Devuelve el histórico completo de jobs, ordenado del más reciente al más antiguo.

### `GET /api/v1/estimate-jobs/{job_id}`

Devuelve el detalle de una petición concreta.

### `GET /api/v1/estimate/friendly-names`

Lista aliases de proveedor disponibles.

## Contrato tipado

### Request

`EstimationRequest`
- `description`
- `project_type`: `mobile_app | web_saas | internal_tool | data_pipeline`
- `detail_level`: `summary | medium | detailed`
- `output_format`: `phases_table | line_items | narrative`

### Job

`EstimationJob`
- `id`
- `status`: `pending | running | succeeded | failed`
- `created_at`
- `updated_at`
- `request`
- `prompt_version`
- `response`
- `error_message`

## Prompts versionados

```text
app/prompts/
├── loader.py
└── estimation/
    └── v1/
        ├── system.j2
        ├── user.j2
        └── examples.j2
```

El loader usa:
- `Environment`
- `StrictUndefined`
- `trim_blocks=True`
- `lstrip_blocks=True`

## Portal Streamlit

El portal muestra:
- formulario para crear peticiones
- contadores de total, pending, running y completed
- listas separadas de pendientes y en ejecución
- histórico expandible con resultado o error

La UI no queda bloqueada esperando al LLM: envía el job y luego consulta estado.

Variable opcional:

```bash
export ESTIMATOR_API_BASE_URL=http://localhost:8000/api/v1
```

## Instalación

```bash
cd estimator-cag
python3.11 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

## Arranque

API:

```bash
uvicorn app.main:app --reload
```

Portal:

```bash
streamlit run streamlit_app.py
```

## Prueba manual

Crear job:

```bash
curl -X POST http://localhost:8000/api/v1/estimate-jobs \
  -H "Content-Type: application/json" \
  -d '{
    "description": "Necesitamos una herramienta interna para gestionar solicitudes de compra, aprobaciones y auditoría operativa para tres departamentos.",
    "project_type": "internal_tool",
    "detail_level": "detailed",
    "output_format": "phases_table"
  }'
```

Listar histórico:

```bash
curl http://localhost:8000/api/v1/estimate-jobs
```

## Persistencia actual

El histórico vive en memoria de proceso.

Eso implica:
- sirve para desarrollo y demos
- se pierde al reiniciar la API
- no coordina múltiples réplicas

Si después quieres llevarlo a producción, el siguiente paso natural es extraer `InMemoryEstimationJobStore` a una persistencia real.

## Tests

Incluye:
- tests del contrato HTTP
- tests del render de templates
- tests de endpoints de jobs

Ejecución:

```bash
cd estimator-cag
source .venv/bin/activate
pytest
```
