from pathlib import Path

from fastapi.testclient import TestClient

from app import main as main_module
from app.errors import UpstreamBadResponseError, UpstreamTimeoutError
from app.embedding_pipeline.db import get_async_session
from app.main import app
from app import rate_limit as rate_limit_module
from app.routers import estimate_runtime as estimate_runtime_router
from app.routers import retrieval as retrieval_router
from app.routers import estimations
from app.schemas import UserTier
from app.services import session_service
from app.sessions import ExternalContextItem, MAX_TURNS, SessionStore


client = TestClient(app)


def test_health_endpoint() -> None:
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
        "service": "estimator-cag",
        "version": "0.1.0",
    }


def test_estimate_from_transcript_endpoint_returns_request_headers(monkeypatch) -> None:
    async def fake_estimate_from_transcript(**kwargs) -> tuple[dict, str]:
        return (
            {
                "text": "Estimación RAG operativa.",
                "prompt_version": "v1",
                "model": "openai/gpt-4o-mini",
                "provider": "openai",
                "tokens_used": {"prompt": 20, "completion": 30, "total": 50},
                "latency_ms": 321.0,
                "cost_usd": 0.0002,
                "request_id": "req-123",
                "idempotency_cache_hit": True,
                "retrieval_context_included": True,
                "retrieved_results_count": 3,
                "included_chunks_count": 2,
            },
            "req-123",
        )

    monkeypatch.setattr(estimate_runtime_router, "estimate_from_transcript", fake_estimate_from_transcript)
    rate_limit_module.limiter._events.clear()

    response = client.post(
        "/api/v1/estimate/from-transcript",
        json={
            "transcript": (
                "Necesitamos un portal B2B con autenticación, reporting, pagos, "
                "panel de proveedores y automatización operativa para un contexto regulado."
            ),
        },
    )

    assert response.status_code == 200
    assert response.headers["X-Request-ID"] == "req-123"
    assert response.headers["X-Idempotency-Cache"] == "hit"
    assert response.json()["retrieval_context_included"] is True


def test_estimate_from_transcript_requires_api_key_when_configured(monkeypatch) -> None:
    monkeypatch.setattr(estimate_runtime_router.settings, "estimate_api_key", "secret-estimate")
    rate_limit_module.limiter._events.clear()

    response = client.post(
        "/api/v1/estimate/from-transcript",
        json={
            "transcript": (
                "Necesitamos un portal B2B con autenticación, reporting, pagos, "
                "panel de proveedores y automatización operativa para un contexto regulado."
            ),
        },
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid API key"

    monkeypatch.setattr(estimate_runtime_router.settings, "estimate_api_key", "")


def test_retrieval_search_rate_limit_returns_429(monkeypatch) -> None:
    async def fake_search(self, *, session, request):
        from app.embedding_pipeline.schemas import SearchResponse

        return SearchResponse(
            query=request.query,
            effective_query=request.query,
            k=request.k,
            score_threshold=request.score_threshold,
            rewrite_strategy=request.rewrite_strategy,
            rewrite_notes=[],
            search_time_ms=1.0,
            low_confidence=True,
            total_candidates_considered=0,
            results=[],
        )

    monkeypatch.setattr(retrieval_router.settings, "retrieval_rate_limit_per_minute", 1)
    monkeypatch.setattr(retrieval_router.SemanticSearchService, "search", fake_search)
    rate_limit_module.limiter._events.clear()

    async def fake_get_async_session():
        yield object()

    app.dependency_overrides[get_async_session] = fake_get_async_session

    payload = {"query": "oauth banking portal", "k": 3}
    first = client.post("/api/v1/retrieval/search", json=payload)
    second = client.post("/api/v1/retrieval/search", json=payload)

    assert first.status_code == 200
    assert second.status_code == 429
    assert second.headers["Retry-After"]
    assert second.json()["detail"]["error"] == "rate_limit_exceeded"

    monkeypatch.setattr(retrieval_router.settings, "retrieval_rate_limit_per_minute", 120)
    app.dependency_overrides.clear()


def test_lifespan_reconciles_managed_metadata_indexes(monkeypatch) -> None:
    calls: list[object] = []

    async def fake_reconcile(engine) -> None:
        calls.append(engine)

    monkeypatch.setattr(main_module, "reconcile_managed_metadata_indexes", fake_reconcile)
    monkeypatch.setattr(main_module.settings, "vector_db_initialize_on_start", True)
    monkeypatch.setattr(main_module, "async_engine", object())

    with TestClient(app):
        pass

    assert len(calls) == 1


def test_lifespan_skips_index_reconciliation_without_engine(monkeypatch) -> None:
    calls: list[object] = []

    async def fake_reconcile(engine) -> None:
        calls.append(engine)

    monkeypatch.setattr(main_module, "reconcile_managed_metadata_indexes", fake_reconcile)
    monkeypatch.setattr(main_module.settings, "vector_db_initialize_on_start", True)
    monkeypatch.setattr(main_module, "async_engine", None)

    with TestClient(app):
        pass

    assert calls == []


def test_friendly_names_endpoint() -> None:
    response = client.get("/api/v1/estimate/friendly-names")

    assert response.status_code == 200
    assert set(response.json()["friendly_names"]) == {"openai", "anthropic", "ollama"}


def test_create_session_returns_uuid_and_stores_session() -> None:
    response = client.post("/api/v1/sessions")

    assert response.status_code == 200
    body = response.json()
    assert isinstance(body["session_id"], str)
    assert len(body["session_id"]) == 26
    session = session_service.session_store.get(body["session_id"])
    assert session is not None
    assert session.user_tier == UserTier.DEVELOPER
    assert session.user_display_name is None


def test_get_session_detail_returns_persisted_state(tmp_path: Path, monkeypatch) -> None:
    store = SessionStore(path=tmp_path / "sessions.json")
    monkeypatch.setattr(session_service, "session_store", store)

    session_id = session_service.create_session()
    session = store.get(session_id)
    assert session is not None
    session.history.add_turn("user one", "assistant one")
    session.remember_document_sources(["/tmp/spec.md"])
    session.set_external_context_config(
        notion_page_ids=["page-123"],
        notion_search_terms=["Atlas"],
    )
    session.add_conversation_message("user", "Solicitud visible")
    session.set_last_document_context(["--- document_path: /tmp/spec.md ---\n# Spec"])
    session.set_last_external_context([])
    session.set_last_run_info(
        provider="openai",
        model="openai/gpt-4o-mini",
        tokens_used={"prompt": 5, "completion": 7, "total": 12},
        response_time=0.42,
    )
    store.save_session(session_id)

    response = client.get(f"/api/v1/sessions/{session_id}")

    assert response.status_code == 200
    body = response.json()
    assert body["session_id"] == session_id
    assert body["user_tier"] == "developer"
    assert body["user_display_name"] is None
    assert body["turns"] == [["user one", "assistant one"]]
    assert body["message_count"] == 1
    assert body["anchors_count"] == 0
    assert body["summary_chars"] == 0
    assert body["last_resolved_tier"] == "developer"
    assert body["last_tier_rule"] == "session_profile_locked"
    assert body["external_context_config"] == {
        "notion_page_ids": ["page-123"],
        "notion_search_terms": ["Atlas"],
    }
    assert body["document_sources"] == ["/tmp/spec.md"]
    assert body["conversation_messages"] == [{"role": "user", "content": "Solicitud visible"}]
    assert body["last_document_context"] == ["--- document_path: /tmp/spec.md ---\n# Spec"]
    assert body["last_external_context"] == []
    assert body["last_run_info"] == {
        "provider": "openai",
        "model": "openai/gpt-4o-mini",
        "tokens_used": {"prompt": 5, "completion": 7, "total": 12},
        "response_time": 0.42,
    }
    assert body["turn_observations"] == []
    assert body["last_turn_observed"] is None


def test_estimate_rejects_short_description() -> None:
    response = client.post(
        "/api/v1/estimate",
        json={
            "description": "Muy corta",
            "project_type": "web_saas",
            "detail_level": "summary",
            "output_format": "narrative",
        },
    )

    assert response.status_code == 422


def test_estimate_returns_llm_result(monkeypatch) -> None:
    async def fake_get_estimation(request, **_: str | None) -> dict:
        assert request.description == "Necesitamos un portal B2B con autenticación y panel operativo."
        return {
            "text": "## Estimación de prueba",
            "prompt_version": "v1",
            "model": "openai/gpt-4o-mini",
            "provider": "openai",
            "tokens_used": {"prompt": 10, "completion": 20, "total": 30},
        }

    monkeypatch.setattr(estimations, "get_estimation", fake_get_estimation)

    response = client.post(
        "/api/v1/estimate",
        json={
            "description": "Necesitamos un portal B2B con autenticación y panel operativo.",
            "project_type": "web_saas",
            "detail_level": "medium",
            "output_format": "narrative",
        },
    )

    body = response.json()
    assert response.status_code == 200
    assert body == {"text": "## Estimación de prueba", "prompt_version": "v1"}


def test_estimate_passes_query_overrides_to_service(monkeypatch) -> None:
    captured: dict[str, object] = {}

    async def fake_get_estimation(request, **kwargs: str | None) -> dict:
        captured["request"] = request
        captured["kwargs"] = kwargs
        return {
            "text": "## Estimación de prueba",
            "prompt_version": "v1",
            "model": "anthropic/claude-haiku-4-5-20251001",
            "provider": "anthropic",
            "tokens_used": {"prompt": 11, "completion": 22, "total": 33},
        }

    monkeypatch.setattr(estimations, "get_estimation", fake_get_estimation)

    response = client.post(
        "/api/v1/estimate?friendly_name=anthropic&provider=anthropic&model=claude-haiku-4-5-20251001",
        json={
            "description": "Necesitamos una herramienta interna para operaciones con auditoría y reportes semanales.",
            "project_type": "internal_tool",
            "detail_level": "detailed",
            "output_format": "line_items",
        },
    )

    assert response.status_code == 200
    assert captured["request"].project_type.value == "internal_tool"
    assert captured["kwargs"] == {
        "friendly_name": "anthropic",
        "provider": "anthropic",
        "model": "claude-haiku-4-5-20251001",
    }


def test_estimate_accepts_retrieval_config_in_request(monkeypatch) -> None:
    captured: dict[str, object] = {}

    async def fake_get_estimation(request, **kwargs: str | None) -> dict:
        captured["request"] = request
        return {
            "text": "## Estimación con retrieval opcional",
            "prompt_version": "v1",
            "model": "openai/gpt-4o-mini",
            "provider": "openai",
            "tokens_used": {"prompt": 11, "completion": 22, "total": 33},
        }

    monkeypatch.setattr(estimations, "get_estimation", fake_get_estimation)

    response = client.post(
        "/api/v1/estimate",
        json={
            "description": "Necesitamos un portal B2B con autenticación, reporting y notificaciones automáticas por email.",
            "project_type": "web_saas",
            "detail_level": "medium",
            "output_format": "narrative",
            "retrieval": {
                "enabled": True,
                "k": 4,
                "score_threshold": 0.72,
                "rewrite_strategy": "normalize",
                "max_chunks": 2,
                "max_context_chars": 1200,
                "include_scores": False,
            },
        },
    )

    assert response.status_code == 200
    assert captured["request"].retrieval.enabled is True
    assert captured["request"].retrieval.k == 4
    assert captured["request"].retrieval.rewrite_strategy.value == "normalize"


def test_estimate_rejects_unknown_friendly_name(monkeypatch) -> None:
    async def fake_get_estimation(request, **kwargs: str | None) -> dict:
        raise ValueError("Unknown friendly_name 'bedrock'. Available: openai, anthropic, ollama")

    monkeypatch.setattr(estimations, "get_estimation", fake_get_estimation)

    response = client.post(
        "/api/v1/estimate?friendly_name=bedrock",
        json={
            "description": "Necesitamos un portal de soporte interno con bandeja de tickets y métricas.",
            "project_type": "internal_tool",
            "detail_level": "medium",
            "output_format": "narrative",
        },
    )

    assert response.status_code == 400
    assert "Unknown friendly_name 'bedrock'" in response.json()["detail"]


def test_session_estimate_updates_project_metadata(monkeypatch) -> None:
    async def fake_get_estimation(request, **kwargs: str | None) -> dict:
        return {
            "text": "Proyecto Atlas estimado para un equipo de 4 con React y PostgreSQL.",
            "prompt_version": "v1",
            "model": "openai/gpt-4o-mini",
            "provider": "openai",
            "tokens_used": {"prompt": 10, "completion": 20, "total": 30},
            "latency_ms": 123.0,
            "cost_usd": 0.0001,
        }

    monkeypatch.setattr(session_service, "get_estimation", fake_get_estimation)

    session_id = client.post("/api/v1/sessions").json()["session_id"]
    response = client.post(
        f"/api/v1/sessions/{session_id}/estimate",
        data={
            "transcript": "Necesitamos el proyecto Atlas con React, PostgreSQL y un equipo de 4 personas.",
            "project_type": "web_saas",
            "detail_level": "medium",
            "output_format": "narrative",
        },
    )

    assert response.status_code == 200
    metadata = session_service.session_store.get(session_id).project_metadata
    assert metadata.project_name is not None
    assert "react" in metadata.mentioned_technologies
    assert "postgresql" in metadata.mentioned_technologies
    assert metadata.assumed_team_size == 4
    observed = session_service.session_store.get(session_id).last_turn_observed()
    assert observed is not None
    assert observed["turn_index"] == 1
    assert observed["tokens_in"] == 10
    assert observed["tokens_out"] == 20
    assert observed["latency_ms"] == 123.0


def test_session_estimate_passes_external_context_to_service(monkeypatch) -> None:
    captured: dict[str, object] = {}

    async def fake_get_estimation(request, **kwargs: str | None) -> dict:
        captured["external_context"] = kwargs.get("external_context")
        return {
            "text": "Estimación enriquecida con contexto externo.",
            "prompt_version": "v1",
            "model": "openai/gpt-4o-mini",
            "provider": "openai",
            "tokens_used": {"prompt": 10, "completion": 20, "total": 30},
        }

    async def fake_resolve_external_context(*, session, transcript: str):
        return [
            ExternalContextItem(
                source="notion",
                title="Atlas kickoff",
                content="Roadmap y restricciones aprobadas.",
                url="https://notion.so/atlas",
                updated_at="2026-05-19T10:00:00Z",
                relevance_reason="Explicit notion_page_id configured in the session.",
            )
        ]

    monkeypatch.setattr(session_service, "get_estimation", fake_get_estimation)
    monkeypatch.setattr(session_service, "resolve_external_context", fake_resolve_external_context)

    session_id = client.post("/api/v1/sessions").json()["session_id"]
    response = client.post(
        f"/api/v1/sessions/{session_id}/estimate",
        data={
            "transcript": "Necesitamos el proyecto Atlas con contexto desde Notion.",
            "project_type": "web_saas",
            "detail_level": "medium",
            "output_format": "narrative",
        },
    )

    assert response.status_code == 200
    assert [item.model_dump() for item in captured["external_context"]] == [
        {
            "source": "notion",
            "title": "Atlas kickoff",
            "content": "Roadmap y restricciones aprobadas.",
            "url": "https://notion.so/atlas",
            "updated_at": "2026-05-19T10:00:00Z",
            "relevance_reason": "Explicit notion_page_id configured in the session.",
        }
    ]


def test_session_estimate_attachment_text_reaches_request(monkeypatch) -> None:
    captured: dict[str, object] = {}

    async def fake_get_estimation(request, **kwargs: str | None) -> dict:
        captured["description"] = request.description
        return {
            "text": "Estimación con adjunto procesado.",
            "prompt_version": "v1",
            "model": "openai/gpt-4o-mini",
            "provider": "openai",
            "tokens_used": {"prompt": 10, "completion": 20, "total": 30},
        }

    monkeypatch.setattr(session_service, "get_estimation", fake_get_estimation)
    async def fake_convert_with_docling(filename: str, content: bytes, content_type: str | None) -> str:
        assert filename == "requirements.docx"
        assert content_type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        return "Integrar Stripe y SSO corporativo."

    monkeypatch.setattr(
        "app.services.attachment_extraction._convert_with_docling",
        fake_convert_with_docling,
    )

    session_id = client.post("/api/v1/sessions").json()["session_id"]
    response = client.post(
        f"/api/v1/sessions/{session_id}/estimate",
        data={
            "transcript": "Necesitamos una plataforma B2B.",
            "project_type": "web_saas",
            "detail_level": "medium",
            "output_format": "narrative",
        },
        files={"attachments": ("requirements.docx", b"fake-docx", "application/vnd.openxmlformats-officedocument.wordprocessingml.document")},
    )

    assert response.status_code == 200
    assert "Stripe" in captured["description"]
    assert "requirements.docx" in captured["description"]


def test_session_estimate_document_paths_reach_request(tmp_path: Path, monkeypatch) -> None:
    captured: dict[str, object] = {}

    async def fake_get_estimation(request, **kwargs: str | None) -> dict:
        captured["description"] = request.description
        return {
            "text": "Estimación con documento por ruta.",
            "prompt_version": "v1",
            "model": "openai/gpt-4o-mini",
            "provider": "openai",
            "tokens_used": {"prompt": 10, "completion": 20, "total": 30},
        }

    monkeypatch.setattr(session_service, "get_estimation", fake_get_estimation)

    doc_path = tmp_path / "requirements.md"
    doc_path.write_text("# Requisitos\n\nIntegrar SSO y reporting.", encoding="utf-8")

    session_id = client.post("/api/v1/sessions").json()["session_id"]
    response = client.post(
        f"/api/v1/sessions/{session_id}/estimate",
        data={
            "transcript": "Necesitamos una plataforma B2B.",
            "project_type": "web_saas",
            "detail_level": "medium",
            "output_format": "narrative",
            "document_paths": str(doc_path),
        },
    )

    assert response.status_code == 200
    assert "Integrar SSO y reporting." in captured["description"]
    persisted_session = session_service.session_store.get(session_id)
    assert str(doc_path) in persisted_session.document_sources
    assert any("Integrar SSO y reporting." in item for item in persisted_session.last_document_context)


def test_session_estimate_history_respects_max_turns(monkeypatch) -> None:
    async def fake_get_estimation(request, **kwargs: str | None) -> dict:
        return {
            "text": "Respuesta de estimación.",
            "prompt_version": "v1",
            "model": "openai/gpt-4o-mini",
            "provider": "openai",
            "tokens_used": {"prompt": 10, "completion": 20, "total": 30},
        }

    monkeypatch.setattr(session_service, "get_estimation", fake_get_estimation)

    session_id = client.post("/api/v1/sessions").json()["session_id"]
    for index in range(8):
        response = client.post(
            f"/api/v1/sessions/{session_id}/estimate",
            data={
                "transcript": (
                    f"Turno {index}: necesitamos refinar alcance del proyecto Atlas con React y reporting."
                ),
                "project_type": "web_saas",
                "detail_level": "medium",
                "output_format": "narrative",
            },
        )
        assert response.status_code == 200

    history = session_service.session_store.get(session_id).history
    assert len(history.turns) == MAX_TURNS
    assert "Turno 0" not in history.turns[0][0]


def test_session_estimate_returns_404_for_unknown_session() -> None:
    response = client.post(
        "/api/v1/sessions/01UNKNOWNSESSION000000000000/estimate",
        data={
            "transcript": "Necesitamos una plataforma B2B.",
            "project_type": "web_saas",
            "detail_level": "medium",
            "output_format": "narrative",
        },
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Session not found"


def test_session_estimate_rejects_unsupported_attachment_type(monkeypatch) -> None:
    async def fake_get_estimation(request, **kwargs: str | None) -> dict:
        raise AssertionError("No debería llegar al LLM con un adjunto inválido")

    monkeypatch.setattr(session_service, "get_estimation", fake_get_estimation)

    session_id = client.post("/api/v1/sessions").json()["session_id"]
    response = client.post(
        f"/api/v1/sessions/{session_id}/estimate",
        data={
            "transcript": "Necesitamos una plataforma B2B.",
            "project_type": "web_saas",
            "detail_level": "medium",
            "output_format": "narrative",
        },
        files={"attachments": ("payload.exe", b"fake-binary", "application/octet-stream")},
    )

    assert response.status_code == 400
    assert "Unsupported attachment type" in response.json()["detail"]


def test_session_estimate_maps_docling_timeout_to_408(monkeypatch) -> None:
    async def fake_extract_attachments_text(_attachments) -> list[str]:
        raise UpstreamTimeoutError("Docling conversion timed out for 'requirements.docx'")

    monkeypatch.setattr(session_service, "extract_attachments_text", fake_extract_attachments_text)

    session_id = client.post("/api/v1/sessions").json()["session_id"]
    response = client.post(
        f"/api/v1/sessions/{session_id}/estimate",
        data={
            "transcript": "Necesitamos una plataforma B2B.",
            "project_type": "web_saas",
            "detail_level": "medium",
            "output_format": "narrative",
        },
    )

    assert response.status_code == 408
    assert "Docling conversion timed out" in response.json()["detail"]


def test_session_estimate_maps_notion_bad_response_to_502(monkeypatch) -> None:
    async def fake_get_estimation(request, **kwargs: str | None) -> dict:
        raise AssertionError("No debería llegar al LLM si Notion falla antes")

    async def fake_resolve_external_context(*, session, transcript: str):
        raise UpstreamBadResponseError("Notion search payload was not valid JSON for query 'Atlas'")

    monkeypatch.setattr(session_service, "get_estimation", fake_get_estimation)
    monkeypatch.setattr(session_service, "resolve_external_context", fake_resolve_external_context)

    session_id = client.post("/api/v1/sessions").json()["session_id"]
    response = client.post(
        f"/api/v1/sessions/{session_id}/estimate",
        data={
            "transcript": "Necesitamos contexto Atlas desde Notion.",
            "project_type": "web_saas",
            "detail_level": "medium",
            "output_format": "narrative",
        },
    )

    assert response.status_code == 502
    assert "Notion search payload was not valid JSON" in response.json()["detail"]
