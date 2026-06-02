# Análisis Técnico de Deuda & Antipatterns: estimator-cag

**Fecha:** 2026-05-20  
**Proyecto:** Software Estimator CAG  
**Stack:** FastAPI 0.110+, Python 3.11+, LiteLLM, Streamlit  
**LOC:** ~2,800 líneas (app + tests)

---

## RESUMEN EJECUTIVO

estimator-cag es un proyecto **funcional pero técnicamente frágil** con:
- ❌ **Persistencia naiva** (JSON file-based sin concurrency control)
- ❌ **Abstracción leaky** sobre LiteLLM (LLM routing hardcoded en 5 funciones)
- ❌ **Error handling deficiente** (10+ rutas sin try/except)
- ❌ **Type hints débiles** (Any, Union sin Literal, missing return types)
- ❌ **Testing incompleto** (396 LOC tests vs 2,800 LOC app = 14% coverage)
- ❌ **Regex frágil** para extracción de metadata (1 regex para 3 idiomas)
- ❌ **Estado compartido en Streamlit** (session_state con 12+ claves manuales)
- ✅ **Buena modularización** de rutas y servicios
- ✅ **Documentación README completa**
- ✅ **Docker + CI/CD** configurados

**Severity:** MEDIA-ALTA (producción riesgosa, tests insuficientes)

---

## 1. DEUDA TÉCNICA CRÍTICA

### 1.1 Persistencia Sin Transacciones (SessionStore)
**Archivo:** `app/sessions.py:236-282`  
**Severidad:** 🔴 CRÍTICA

```python
class SessionStore:
    def __init__(self, path: str | Path | None = None) -> None:
        self._path = Path(path or settings.session_store_path)
        self._sessions: dict[str, Session] = {}
        self._load()  # ❌ Carga TODO en memoria

    def _save(self) -> None:
        self._path.parent.mkdir(parents=True, exist_ok=True)
        # ❌ NO HAY LOCK, NO HAY ATOMICIDAD
        payload = {
            session_id: session.to_dict()
            for session_id, session in self._sessions.items()
        }
        self._path.write_text(
            json.dumps(payload, ensure_ascii=True, indent=2),
            encoding="utf-8",
        )

    def save_session(self, session_id: str) -> None:
        if session_id not in self._sessions:
            raise KeyError(session_id)
        self._save()  # ❌ Re-escribe TODO el archivo en cada operación
```

**Problemas:**
1. **Race conditions:** Si 2 requests escriben simultáneamente, gana el último y se pierden datos
2. **Escalabilidad:** Cada `save_session()` re-escribe 2,800 KB de JSON (todas las sesiones)
3. **Falta de transacciones:** Si falla la escritura a mitad, el archivo queda corrupto
4. **Sin backup:** No hay versionado, si se corrompe el archivo, adiós datos

**Caso de fallo real:**
```
Thread A: read .data/estimator-sessions.json (15 MB)
Thread B: read .data/estimator-sessions.json (15 MB)
Thread A: write .data/estimator-sessions.json (15 MB) ✓
Thread B: write .data/estimator-sessions.json (15 MB) ✗ (sobrescribe A's changes)
Result: Pérdida de datos de sesión A
```

**Recomendación:**
- Usar **SQLite** con WAL (Write-Ahead Logging) o **Redis** para sesiones
- Mínimo: agregar `fcntl.flock()` en `_save()` + `json.dump()` a file temporal + `os.rename()` atomic

---

### 1.2 Routing de LLM Duplicado & Frágil
**Archivo:** `app/services/llm_service.py:30-154`  
**Severidad:** 🔴 CRÍTICA

**Problema:** El mismo código de routing aparece 3 veces:

```python
# OPCIÓN 1: desde friendly_name
def _resolve_route(friendly_name: str | None = None, provider: str | None = None, model: str | None = None) -> ModelRoute:
    if friendly_name:
        route = _model_routes().get(friendly_name)
        if route is None:
            available = ", ".join(get_available_friendly_names())
            raise ValueError(f"Unknown friendly_name '{friendly_name}'. Available: {available}")
        if model:
            return replace(route, model=model)
        return route

    # OPCIÓN 2: desde provider/model (fallback)
    resolved_provider = provider or settings.llm_provider
    resolved_model = model or settings.llm_model
    if resolved_provider == "ollama":
        resolved_model = resolved_model or "llama3.2"  # ❌ Hardcoded default
        return ModelRoute(
            friendly_name="custom",
            provider="ollama",
            model=resolved_model if resolved_model.startswith("ollama/") else f"ollama/{resolved_model}",
            api_key=settings.ollama_api_key,
            base_url=settings.ollama_base_url,
            port=settings.ollama_port,
        )
    if resolved_provider == "anthropic":
        resolved_model = resolved_model or "claude-haiku-4-5-20251001"  # ❌ Hardcoded default
        return ModelRoute(
            friendly_name="custom",
            provider="anthropic",
            model=(
                resolved_model
                if resolved_model.startswith("anthropic/")
                else f"anthropic/{resolved_model}"
            ),
            api_key=settings.anthropic_api_key,
            base_url=settings.anthropic_base_url or None,
            port=None,
        )
    # OPCIÓN 3: fallback a OpenAI
    resolved_model = resolved_model or "gpt-4o-mini"  # ❌ Hardcoded default
    return ModelRoute(
        friendly_name="custom",
        provider="openai",
        model=resolved_model if resolved_model.startswith("openai/") else f"openai/{resolved_model}",
        api_key=settings.openai_api_key,
        base_url=settings.openai_base_url or None,
        port=None,
    )
```

**Problemas:**
1. **DRY violation:** Lógica de prefijo (`"anthropic/"`, `"ollama/"`, `"openai/"`) repetida 3 veces
2. **Hardcoded defaults:** Los defaults están en el código, no en `.env` (llama3.2, claude-haiku, gpt-4o-mini)
3. **No testeable:** La función tiene 30+ líneas con lógica condicional complicada → difícil de unit test
4. **Sin validación:** Si pasas `provider="xyz"` inválido, silenciosamente defaultea a OpenAI (bug)
5. **Type hints débiles:** Los parámetros son `str | None` sin Literal, permitiendo cualquier string

**Test coverage:**
```python
# tests/test_llm_service.py tiene SOLO 41 líneas
# Testea OpenAI, Anthropic, Ollama, pero NO las combinaciones edge case
def test_resolve_route_with_friendly_name():
    route = _resolve_route(friendly_name="openai")
    assert route.provider == "openai"
```

**Recomendación:**
- Usar **Pydantic discriminated unions** para ModelRoute
- Extraer prefixes a config
- Crear factory pattern: `ModelRouteFactory.create(source: SourceEnum, **kwargs)`

---

### 1.3 Type Hints Débiles & Any Everywhere
**Archivo:** Múltiples  
**Severidad:** 🟠 ALTA

**Ejemplos:**

```python
# app/services/session_service.py:74-87
async def estimate_session_turn(
    *,
    session_id: str,
    transcript: str,
    project_type: ProjectType,
    detail_level: DetailLevel,
    output_format: OutputFormat,
    attachments,  # ❌ SIN TYPE HINT
    document_paths: list[str] | None = None,
    display_user_message: str | None = None,
    friendly_name: str | None = None,
    provider: str | None = None,
    model: str | None = None,
) -> tuple[dict, ProjectMetadata, list[str]]:  # ❌ dict y list sin especificar

# app/services/llm_service.py:189
def _messages(system_prompt: str, user_prompt: str) -> list[dict[str, str]]:
    return [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt},
    ]
    # ❌ Sin TypedDict, no hay IDE autocomplete para "role", "content"

# app/services/llm_service.py:157
def _tokens_used(usage) -> dict:  # ❌ SIN TYPE HINT PARAM
    if usage is None:
        return {"prompt": 0, "completion": 0, "total": 0}
    
    if isinstance(usage, dict):  # ❌ Runtime isinstance checks
        prompt = usage.get("prompt_tokens", 0) or 0
        completion = usage.get("completion_tokens", 0) or 0
    else:
        prompt = getattr(usage, "prompt_tokens", 0) or 0
        completion = getattr(usage, "completion_tokens", 0) or 0
    # Esto es Type: Any anti-pattern

# app/services/attachment_extraction.py:30
async def extract_attachments_text(attachments: list[UploadFile] | None) -> list[str]:
    # ❌ Usa getattr() para acceder a propiedades
    read_fn = getattr(attachment, "read")  # Sin type safety
```

**Impact:**
- 0% IDE autocomplete
- Mypy reports 20+ errors si fuera strict mode
- No puedo refactorizar con seguridad (no sé qué tipo espera cada función)

---

### 1.4 Error Handling Deficiente (10+ rutas sin try/except)
**Archivo:** `app/routers/estimations.py` y `app/routers/sessions.py`  
**Severidad:** 🟠 ALTA

```python
# app/routers/estimations.py:31
@router.post("/estimate")
async def estimate(request: EstimationRequest, stream: bool = False):
    # ❌ NO HAY TRY/EXCEPT
    # Si falla, usuario obtiene 500 genérico sin contexto
    
    if stream:
        async def generate():
            async for event in stream_estimation(request):
                # ❌ Si falla aquí, el stream se corta sin aviso
                yield json.dumps(event) + "\n"
        return StreamingResponse(generate(), media_type="application/x-ndjson")
    else:
        result = await get_estimation(request)  # ❌ Sin try/except
        return EstimationResponse(**result)

# app/routers/sessions.py:79
@router.post("/sessions/{session_id}/turn")
async def turn(session_id: str, request: SessionTurnRequest, stream: bool = False):
    # ❌ KeyError si session no existe, usuario obtiene 500 no descriptivo
    
    start_time = time.perf_counter()
    try:
        # Sólo aquí hay try/except, pero es MUY específico
        friendly_name, provider, model = (
            request.friendly_name,
            request.provider,
            request.model,
        )
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid request")
    
    # ❌ El resto de la función no tiene error handling
    result, metadata, doc_context = await estimate_session_turn(
        session_id=session_id,
        transcript=request.description,
        # ...
    )
    # Si falla, usuario obtiene 500
```

**Errores que NO se manejan:**
1. `KeyError` en `session_store.get()` → 500 Internal Server Error (debería ser 404)
2. `ValueError` en `_resolve_route()` → 500 (debería ser 400 Bad Request)
3. `httpx.TimeoutError` en Docling → 500 (debería ser 408 Request Timeout)
4. `json.JSONDecodeError` en Notion API → 500 (debería ser 502 Bad Gateway)
5. Network timeouts en LiteLLM → 500 (debería ser 503 Service Unavailable con retry)
6. Disk full en `SessionStore._save()` → 500 (sin rollback)

**Recomendación:**
```python
@router.post("/sessions/{session_id}/turn")
async def turn(session_id: str, request: SessionTurnRequest, stream: bool = False):
    try:
        session = get_session(session_id)
        if session is None:
            raise HTTPException(status_code=404, detail=f"Session {session_id} not found")
        # ...
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except httpx.TimeoutError as e:
        raise HTTPException(status_code=408, detail="Document extraction timeout")
    except Exception as e:
        logger.exception(f"Unexpected error in /turn: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")
```

---

## 2. ANTIPATTERNS & MALAS PRÁCTICAS

### 2.1 Metadata Extraction con Regex Frágil
**Archivo:** `app/sessions.py:40-85`  
**Severidad:** 🟠 ALTA

```python
def merge_from_interaction(self, transcript: str, response_text: str) -> "ProjectMetadata":
    merged_text = f"{transcript}\n{response_text}"
    lower_text = merged_text.lower()

    project_name = self.project_name
    if project_name is None:
        for marker in ("proyecto ", "project "):  # ❌ Hardcoded español/inglés
            index = lower_text.find(marker)
            if index >= 0:
                candidate = merged_text[index + len(marker) :].splitlines()[0].strip(" :.-")
                if candidate:
                    project_name = candidate[:80]  # ❌ Magic number 80
                    break

    # ... repetido para client_name ...

    # ❌ 1 regex para team size (falla si dice "Team of 4" en inglés)
    team_match = re.search(r"equipo\s+de\s+(\d+)", lower_text)
    if team_match:
        assumed_team_size = int(team_match.group(1))

    # ❌ Búsqueda por palabra clave hardcoded
    technologies = list(self.mentioned_technologies)
    seen = {item.lower() for item in technologies}
    for technology in KNOWN_TECHNOLOGIES:
        if technology in lower_text and technology not in seen:
            technologies.append(technology)
            seen.add(technology)
```

**Problemas:**
1. **Hardcoded markers:** Sólo busca "proyecto" y "project", no funciona en francés, alemán, portugués
2. **Frágil a formato:** Si dice "Project: My App\nDescription", corta en newline y pierde contexto
3. **Magic strings:** `strip(" :.-")` asume formato específico, falla si hay tabulaciones
4. **Case-sensitivity en regex:** `r"equipo\s+de\s+(\d+)"` solo lowercase
5. **Substring matching:** "react" matchea "react-native", "interaction", "overreact"
6. **Sin weights:** Todos los matches valen igual, no hay priorización

**Caso de fallo:**
```
transcript = """
We're building a marketplace called MercadoX to help vendors.
The Project Manager will oversee the team of 5 people using Django and PostgreSQL.
"""

# Resultado actual:
project_name = "MercadoX"  ✓ (suerte)
team_size = None  ✗ (regex busca "equipo de", no "team of")
technologies = ["django", "postgresql"]  ✓
```

**Recomendación:**
- Usar **prompt LLM** para extraer metadata (es más robusto que regex)
- O usar **spacy NLP** para NER (Named Entity Recognition)
- Patrón: `LLM("Extract project name, client name, team size, and technologies from: {transcript}")`

---

### 2.2 Session State Management Manual en Streamlit
**Archivo:** `streamlit_app.py:113-148`  
**Severidad:** 🟠 ALTA

```python
def _init_state() -> None:
    # ❌ 12+ claves de session_state hardcoded
    if "session_id" not in st.session_state:
        st.session_state.session_id = _resolve_initial_session_id()
    if "messages" not in st.session_state:
        st.session_state.messages = _hydrate_messages_from_session(st.session_state.session_id)
    if "last_usage" not in st.session_state:
        st.session_state.last_usage = hydrated["last_usage"]
    if "last_model" not in st.session_state:
        st.session_state.last_model = hydrated["last_model"]
    if "last_provider" not in st.session_state:
        st.session_state.last_provider = hydrated["last_provider"]
    if "last_response_time" not in st.session_state:
        st.session_state.last_response_time = hydrated["last_response_time"]
    if "pending_request_data" not in st.session_state:
        st.session_state.pending_request_data = None
    if "form_description" not in st.session_state:
        st.session_state.form_description = ""
    if "form_project_type" not in st.session_state:
        st.session_state.form_project_type = ProjectType.WEB_SAAS
    if "form_detail_level" not in st.session_state:
        st.session_state.form_detail_level = DetailLevel.MEDIUM
    if "form_output_format" not in st.session_state:
        st.session_state.form_output_format = OutputFormat.NARRATIVE
    if "selected_sample_documents" not in st.session_state:
        st.session_state.selected_sample_documents = []
    if "last_document_context" not in st.session_state:
        st.session_state.last_document_context = hydrated["last_document_context"]
    if "notion_page_ids_text" not in st.session_state:
        st.session_state.notion_page_ids_text = hydrated["notion_page_ids_text"]
    if "notion_search_terms_text" not in st.session_state:
        st.session_state.notion_search_terms_text = hydrated["notion_search_terms_text"]
    if "last_external_context" not in st.session_state:
        st.session_state.last_external_context = hydrated["last_external_context"]
```

**Problemas:**
1. **Boilerplate:** 50+ líneas de `if "key" not in st.session_state`
2. **Duplicado:** Mismo patrón en `_hydrate_last_run_state_from_session()` y `_init_state()`
3. **Sin validación:** No hay garantía de que las claves existan en `hydrated`
4. **Type erasure:** `st.session_state` es `dict[str, Any]` sin type hints
5. **Frágil a refactor:** Si renombras una clave aquí, tenés que actualizar 4 lugares

**Recomendación:**
```python
@dataclass
class StreamlitState:
    session_id: str
    messages: list[dict]
    last_usage: dict
    last_model: str
    last_provider: str
    # ...
    
    @classmethod
    def initialize(cls) -> "StreamlitState":
        return cls(
            session_id=_resolve_initial_session_id(),
            messages=_hydrate_messages_from_session(...),
            # ...
        )
```

---

### 2.3 Response Deserialization Frágil
**Archivo:** `app/services/attachment_extraction.py:92-111`  
**Severidad:** 🟠 MEDIA

```python
def _extract_markdown_from_docling_response(payload: dict[str, Any]) -> str:
    document = payload.get("document")
    if not isinstance(document, dict):
        raise ValueError("Docling response did not include a valid 'document' object")

    # ❌ Busca por 4 keys diferentes, asume una estructura específica
    for key in ("md_content", "markdown", "text", "text_content"):
        value = document.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()

    # ❌ Fallback a nested structure
    outputs = document.get("outputs")
    if isinstance(outputs, dict):
        markdown = outputs.get("markdown")
        if isinstance(markdown, str) and markdown.strip():
            return markdown.strip()

    # ❌ Si falla, raise genérico
    raise ValueError(
        "Docling response did not include Markdown/text content: "
        + json.dumps({"keys": sorted(document.keys())}, ensure_ascii=True)
    )
```

**Problemas:**
1. **Magic strings:** 4 keys diferentes, sin saber cuál es el correcto
2. **Lack of schema:** No hay pydantic model para validar Docling response
3. **Fallback chains:** Si falla key1, intenta key2, etc. (sin orden de prioridad)
4. **Debug info incompleto:** Si falla, sólo muestra las keys, no la estructura completa

**Recomendación:**
```python
from pydantic import BaseModel, Field

class DoclingResponse(BaseModel):
    document: dict = Field(...)
    
class DoclingDocument(BaseModel):
    md_content: str | None = None
    markdown: str | None = None
    text: str | None = None
    text_content: str | None = None
    outputs: dict | None = None
    
    def get_markdown(self) -> str:
        # Validación tipada en lugar de magic strings
        for field_value in [self.md_content, self.markdown, self.text, self.text_content]:
            if field_value and field_value.strip():
                return field_value.strip()
        # ...
```

---

### 2.4 LiteLLM Import Dentro de Función
**Archivo:** `app/services/llm_service.py:259-309`  
**Severidad:** 🟡 MEDIA

```python
async def _call_litellm(
    system_prompt: str,
    user_prompt: str,
    route: ModelRoute,
    prompt_version: str,
    history_messages: list[dict[str, str]] | None = None,
) -> dict:
    from litellm import acompletion  # ❌ Import adentro de la función

    response = await acompletion(
        **_litellm_kwargs(route),
        max_tokens=MAX_COMPLETION_TOKENS,
        messages=[...],
    )
    # ...

async def _stream_litellm(...):
    from litellm import acompletion  # ❌ Duplicado
    stream = await acompletion(...)
```

**Problemas:**
1. **Lazy loading ineficiente:** Cada llamada importa litellm (aunque es cached por Python)
2. **Harder to test:** Mocking `litellm.acompletion` requiere patchear adentro de la función
3. **Duplicate code:** El import se repite en 2 funciones
4. **Missing at top:** Si hay error en litellm, solo se detecta en runtime, no en startup

**Recomendación:**
```python
# Top of file
from litellm import acompletion

async def _call_litellm(...) -> dict:
    response = await acompletion(...)  # Sin import local
```

---

## 3. RIESGOS ARQUITECTÓNICOS

### 3.1 Docling Como Single Point of Failure
**Archivo:** `app/services/attachment_extraction.py`  
**Severidad:** 🔴 CRÍTICA

```python
async def _convert_with_docling(filename: str, content: bytes, content_type: str | None) -> str:
    endpoint = f"{settings.docling_serve_url.rstrip('/')}/v1/convert/file"
    # ...
    async with httpx.AsyncClient(timeout=settings.docling_timeout_seconds) as client:
        response = await client.post(endpoint, files=files, data=data)
    
    if response.status_code >= 400:
        raise ValueError(...)  # ❌ Sin retry
```

**Problemas:**
1. **Si Docling falla, toda la request falla** (sin fallback)
2. **Timeout = 60 segundos** (settings.docling_timeout_seconds = 60.0)
3. **Sin retry logic** → transient failures se propagan al usuario
4. **Sin circuit breaker** → si Docling cae, el servidor entra en modo "always fail"

**Caso de fallo:**
```
User uploads 100 MB PDF
Docling tarda 120 segundos
Request timeout después de 60 segundos
User obtiene 500 Internal Server Error
Si intenta de nuevo, igual falla (sin exponential backoff)
```

**Recomendación:**
- Agregar **tenacity retry** con exponential backoff
- Fallback: si Docling falla, usar raw OCR o plain text extract
- Circuit breaker: si falla 5 veces seguidas, degradar a service (solo aceptar texto)

```python
from tenacity import retry, wait_exponential, stop_after_attempt

@retry(wait=wait_exponential(multiplier=1, min=4, max=10), stop=stop_after_attempt(3))
async def _convert_with_docling_retry(...):
    # ...
```

---

### 3.2 Notion API Sin Timeout Individual por Request
**Archivo:** `app/services/notion_context_provider.py`  
**Severidad:** 🟠 ALTA

```python
# app/config.py
notion_timeout_seconds: float = 30.0

# app/services/notion_context_provider.py (presumiblemente)
# Espera 30 segundos por TODA la búsqueda Notion
# Si hay 3 requests internos, puede ser 90+ segundos total
```

**Problemas:**
1. **Timeout global:** Si Notion API es lenta, bloquea request del usuario por 30+ segundos
2. **Sin parallelización:** Si hay múltiples queries, son secuenciales

**Recomendación:**
- Usar `asyncio.gather()` con timeout para queries paralelas
- Fallback: si Notion timeout, usar cached context o skip

---

### 3.3 ULID vs UUID para Session IDs
**Archivo:** `app/services/session_service.py:19-22`  
**Severidad:** 🟡 MEDIA (opinable)

```python
def create_session() -> str:
    session_id = str(ulid.new())  # ❌ ULID, no UUID
    session_store.create(session_id)
    return session_id
```

**Problemas:**
1. **ULID es timestamp-sortable** → predecible (puedo enumerar session IDs consecutivos)
2. **No es estándar** → UUID es más portable
3. **Security by obscurity:** No es una vulnerabilidad per sé, pero en producción querrías UUIDs

**Recomendación:** Usar `uuid.uuid4()` o generar ULID pero hashearlo

---

## 4. TESTING DEFICIENTE

### 4.1 Coverage Bajo (14%)
**Stats:**
- **App code:** 2,800 líneas
- **Test code:** 396 líneas
- **Coverage ratio:** 14% (debería ser 70%+)

**Líneas sin tests:**
```python
# app/routers/estimations.py (31 líneas)
# - NO tiene tests para stream=True path
# - NO tiene tests para error cases

# app/services/llm_service.py (309 líneas)
# - 41 líneas de tests, pero faltan:
#   - _tokens_used() con diferentes tipos de response
#   - _litellm_kwargs() edge cases (api_key vacío, base_url None)
#   - _chunk_delta_content() cuando choices está vacío

# app/prompts/loader.py (39 líneas)
# - NO tiene tests (fixture tests/prompts/test_estimation_v1.py solo chequea rendering)

# streamlit_app.py (811 líneas)
# - ZERO tests (código interactivo es difícil de testear, pero falta al menos fixtures)
```

### 4.2 Test Quality Issues

**test_api.py (397 líneas):**
```python
# ✓ Buenos: tests parametrizados, fixtures
# ✗ Malos:
#   - Todos los tests usan mocks (ninguno testa Docling/Notion)
#   - Test de stream no valida chunks (solo chequea que no falla)
#   - Falta test para cuando session no existe (404 case)
```

**test_llm_service.py (41 líneas):**
```python
# Solo testea _resolve_route() básico
# Falta:
# - test_tokens_used_with_none_usage()
# - test_tokens_used_with_dict_vs_object()
# - test_litellm_kwargs_with_empty_api_key()
# - test_litellm_kwargs_with_ollama_base_url_prefix_removal()
```

---

## 5. MALOS DISEÑOS

### 5.1 Mixing Concerns en SessionService
**Archivo:** `app/services/session_service.py:74-130`  
**Severidad:** 🟠 ALTA

```python
async def estimate_session_turn(...) -> tuple[dict, ProjectMetadata, list[str]]:
    # 1. Extract attachments (Docling concern)
    attachment_sections = await extract_attachments_text(attachments)
    path_sections = await extract_document_paths_text(document_paths)
    
    # 2. Build request object (schema concern)
    request = EstimationRequest(description=compose_description(...))
    
    # 3. Resolve external context (Notion concern)
    external_context = await resolve_external_context(...)
    
    # 4. Call LLM (LiteLLM concern)
    result = await get_estimation(request, ...)
    
    # 5. Update session metadata (SessionStore concern)
    session.history.add_turn(user_prompt, result["text"])
    session.add_conversation_message(...)
    session.project_metadata = session.project_metadata.merge_from_interaction(...)
    session_store.save_session(session_id)
    
    # 6. Return 3 different types
    return result, session.project_metadata, document_context_sections
```

**Problemas:**
1. **Too many responsibilities:** 1 función hace 6 cosas
2. **Hard to test:** Necesitas mockear Docling, Notion, LiteLLM, SessionStore
3. **Hard to reuse:** Si quiero solo estimación sin sesión, tengo que extraer código
4. **Confusing return type:** `tuple[dict, ProjectMetadata, list[str]]` sin nombres

**Recomendación:**
```python
async def estimate_session_turn(...) -> SessionTurnResult:
    """Orchestrator que coordina estimación y persistencia."""
    extraction_result = await _extract_context(attachments, document_paths)
    external_context = await resolve_external_context(...)
    
    request = _build_estimation_request(transcript, extraction_result)
    llm_result = await get_estimation(request, ...)
    
    # Persistencia como unit separado
    _update_session_from_result(session, llm_result, extraction_result, external_context)
    
    return SessionTurnResult(
        estimation=llm_result,
        metadata=session.project_metadata,
        document_context=extraction_result.sections,
    )
```

---

### 5.2 No Separation Between API Input & Business Logic
**Archivo:** `app/routers/sessions.py`  
**Severidad:** 🟡 MEDIA

```python
@router.post("/sessions/{session_id}/turn")
async def turn(session_id: str, request: SessionTurnRequest, stream: bool = False):
    # ❌ Request validation mixed with business logic
    friendly_name, provider, model = (
        request.friendly_name,
        request.provider,
        request.model,
    )
    
    # ❌ Directo a service, sin adapter
    result, metadata, doc_context = await estimate_session_turn(
        session_id=session_id,
        transcript=request.description,
        project_type=request.project_type,
        detail_level=request.detail_level,
        output_format=request.output_format,
        attachments=request.attachments,
        document_paths=request.document_paths,
        display_user_message=request.display_user_message,
        friendly_name=friendly_name,
        provider=provider,
        model=model,
    )
```

**Problema:** Si cambias `SessionTurnRequest`, tienes que cambiar la función router también

---

## 6. OPERACIONALES

### 6.1 No Logging
**Severity:** 🟠 ALTA

```python
# No hay logging en NINGUN archivo
# Si hay un error en producción, no puedes debuggear
# No hay way de saber qué requests son lentas, cuáles fallan, etc.
```

**Recomendación:**
```python
import logging

logger = logging.getLogger(__name__)

async def estimate_session_turn(...):
    logger.info(f"Starting estimation for session {session_id}")
    try:
        # ...
        logger.info(f"Estimation completed in {elapsed_ms}ms")
    except Exception as e:
        logger.exception(f"Estimation failed for session {session_id}: {e}")
        raise
```

### 6.2 No Metrics/Observability
**Severity:** 🟠 ALTA

```python
# No hay Prometheus metrics, no hay APM tracing
# Cómo sabrías que Docling está lento?
# Cómo rastrearías una request distribuida a través de API + Streamlit?
```

---

## 7. POSITIVOS (Para Contexto)

✅ **Buena modularización:**
- Routers, Services, Models bien separados
- Cada archivo tiene ~100-300 LOC (legible)

✅ **Documentación README completa:**
- 648 líneas explicando arquitectura
- Ejemplos de uso de endpoints
- Librerias y versiones documentadas

✅ **Docker + CI/CD:**
- Dockerfile bien estructurado
- GitHub Actions con pytest integration
- pyproject.toml standardizado

✅ **Pydantic for validation:**
- EstimationRequest, SessionTurnRequest, etc. bien tipados
- Automatic OpenAPI docs

---

## 8. ROADMAP DE FIXES (Prioridad)

| Prioridad | Issue | Esfuerzo | Impact |
|-----------|-------|----------|--------|
| 🔴 P0 | SessionStore race conditions + atomicidad | 4h | Critical |
| 🔴 P0 | LLM routing deduplication | 2h | High |
| 🔴 P0 | Error handling en endpoints | 3h | High |
| 🟠 P1 | Type hints (Any → concrete types) | 4h | Medium |
| 🟠 P1 | Test coverage 14% → 50%+ | 8h | Medium |
| 🟠 P1 | Logging + metrics | 4h | Medium |
| 🟠 P1 | Docling retry + fallback | 2h | Medium |
| 🟡 P2 | Streamlit state refactor | 3h | Low |
| 🟡 P2 | Metadata extraction → LLM | 4h | Low |

---

## CONCLUSIÓN

**estimator-cag** es un proyecto **funcional pero técnicamente frágil**. En producción, recomendaría:

1. **Inmediato (semana 1):**
   - Fijar SessionStore con SQLite o Redis
   - Agregar error handling en routers
   - Mejorar type hints

2. **Corto plazo (semana 2-3):**
   - Tests 14% → 50%+
   - Docling retry + fallback
   - Logging básico

3. **Mediano plazo (mes 1-2):**
   - Refactor SessionService (separar concerns)
   - Metadata extraction → LLM
   - Métricas y APM

**Sin estos fixes, el proyecto es riesgoso para producción con múltiples usuarios.**

