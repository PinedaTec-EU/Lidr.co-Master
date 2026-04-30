# estimator-cag

Servicio FastAPI de estimación de software basado en arquitectura **CAG** (Context Augmented Generation). Recibe la transcripción de una reunión con un cliente, inyecta un conjunto de estimaciones previas directamente en el prompt del modelo y devuelve una estimación detallada de esfuerzo en formato Markdown.

No hay base de datos, no hay retrieval: todo el contexto viaja en cada llamada al LLM.

---

## Descripción

El servicio actúa como un estimador experto entrenado por contexto estático. Al recibir una transcripción, construye un `system prompt` que incluye 10 ejemplos de proyectos reales con sus estimaciones — desglose de tareas, horas, equipo recomendado y duración — y envía la petición al LLM configurado (OpenAI o Anthropic).

El modelo devuelve una estimación calibrada en el mismo estilo y formato que los ejemplos, garantizando consistencia sin fine-tuning.

**Proveedores soportados:**
- OpenAI (`gpt-4o-mini` por defecto)
- Anthropic (`claude-haiku-4-5-20251001` por defecto, con prompt caching activado)

---

## Estructura del proyecto

```
estimator-cag/
├── app/
│   ├── config.py              # Settings desde variables de entorno
│   ├── main.py                # Aplicación FastAPI + router + health
│   ├── context/
│   │   └── examples.py        # 10 ejemplos de estimaciones (contexto CAG)
│   ├── routers/
│   │   └── estimations.py     # Endpoint POST /api/v1/estimate
│   └── services/
│       └── llm_service.py     # Lógica de llamada a OpenAI / Anthropic
├── pyproject.toml
└── .env                       # Variables de entorno (no comitear)
```

---

## Endpoints

### `GET /health`

Comprueba que el servicio está activo.

**Respuesta:**
```json
{
  "status": "ok",
  "service": "estimator-cag",
  "version": "0.1.0"
}
```

---

### `POST /api/v1/estimate`

Genera una estimación de software a partir de la transcripción de una reunión.

**Request body:**
```json
{
  "transcription": "El cliente necesita una app web para gestión de reservas..."
}
```

**Respuesta:**
```json
{
  "estimation": "## Estimación: ...\n\n### Desglose de tareas:\n...",
  "model": "gpt-4o-mini",
  "provider": "openai",
  "tokens_used": {
    "prompt": 2840,
    "completion": 512,
    "total": 3352
  },
  "timestamp": "2026-04-30T10:23:45.123456+00:00"
}
```

**Errores:**
| Código | Causa |
|--------|-------|
| `400`  | `transcription` vacía o solo espacios |
| `500`  | Error en la llamada al LLM |

---

### `GET /docs`

Swagger UI con documentación interactiva de la API.

### `GET /redoc`

Documentación alternativa en formato ReDoc.

---

## Flujo de la petición

```
Cliente
  │
  │  POST /api/v1/estimate  { transcription: "..." }
  ▼
Router (estimations.py)
  │  Valida que transcription no esté vacía
  ▼
LLM Service (llm_service.py)
  │  _build_system_prompt()
  │    └─ Inyecta 10 ejemplos de estimaciones (ESTIMATION_EXAMPLES)
  │
  ├─ provider = "openai"    → AsyncOpenAI.chat.completions.create()
  └─ provider = "anthropic" → AsyncAnthropic.messages.create()
                               (con cache_control ephemeral en system prompt)
  ▼
Router
  │  Construye EstimationResponse con timestamp UTC
  ▼
Cliente
     { estimation, model, provider, tokens_used, timestamp }
```

El `system_prompt` se construye en cada llamada concatenando los ejemplos estáticos. En Anthropic, el system prompt se marca con `cache_control: ephemeral` para aprovechar el prompt caching y reducir latencia y coste en llamadas sucesivas.

---

## Instalación y arranque

### Requisitos

- Python 3.11 o superior

### Configuración

Crea un archivo `.env` en la raíz del proyecto:

```env
# Proveedor activo: openai | anthropic
LLM_PROVIDER=openai

# Claves de API (solo la del proveedor activo es obligatoria)
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...

# Modelo concreto (opcional — usa el default del proveedor si se omite)
LLM_MODEL=

APP_ENV=development
LOG_LEVEL=info
```

### Instalar dependencias y arrancar

```bash
cd estimator-cag
python -m venv .venv && source .venv/bin/activate
pip install -e .
uvicorn app.main:app --reload
```

El servicio queda disponible en `http://localhost:8000`.

---

## Validación con SIH (Sphere Integration Hub)

SIH permite ejecutar y validar los endpoints del servicio mediante workflows declarativos sin necesidad de herramientas externas.

### 1. Listar workflows disponibles

```
mcp__sphere-integration-hub__list_available_workflows
```

Muestra los workflows registrados para este proyecto. Busca los que incluyan `estimator` o `estimate`.

### 2. Inspeccionar el workflow de estimación

```
mcp__sphere-integration-hub__get_workflow_inputs_outputs
  workflow: "estimate-workflow"
```

Devuelve los campos de entrada requeridos (`transcription`) y la estructura de salida esperada.

### 3. Planificar la ejecución antes de lanzarla

```
mcp__sphere-integration-hub__plan_workflow_execution
  workflow: "estimate-workflow"
  inputs:
    transcription: "Startup de salud necesita app móvil para gestión de citas médicas y historial clínico básico."
```

Muestra los pasos que se ejecutarán y las llamadas HTTP que se realizarán contra el servicio.

### 4. Validar el workflow

```
mcp__sphere-integration-hub__validate_workflow
  workflow: "estimate-workflow"
```

Comprueba que la estructura del workflow es correcta y que los campos de entrada/salida están bien definidos antes de ejecutarlo.

### 5. Ejecutar y leer el reporte

Tras la ejecución, lista los reportes disponibles:

```
mcp__sphere-integration-hub__list_execution_reports
```

Y lee el último:

```
mcp__sphere-integration-hub__read_execution_report
  report: "<id-del-reporte>"
```

El reporte incluye el resultado de cada stage, los tokens consumidos y el Markdown de estimación generado.

### Ejemplo de payload para prueba manual (curl)

```bash
curl -X POST http://localhost:8000/api/v1/estimate \
  -H "Content-Type: application/json" \
  -d '{
    "transcription": "Startup de salud necesita app móvil para gestión de citas médicas y historial clínico básico. El equipo del cliente no tiene desarrolladores propios y quieren lanzar en 3 meses."
  }'
```

---

## Variables de entorno de referencia

| Variable | Valores posibles | Default |
|----------|-----------------|---------|
| `LLM_PROVIDER` | `openai` \| `anthropic` | `openai` |
| `LLM_MODEL` | cualquier model ID | vacío (usa default del proveedor) |
| `OPENAI_API_KEY` | `sk-...` | — |
| `ANTHROPIC_API_KEY` | `sk-ant-...` | — |
| `APP_ENV` | `development` \| `production` | `development` |
| `LOG_LEVEL` | `debug` \| `info` \| `warning` | `info` |
