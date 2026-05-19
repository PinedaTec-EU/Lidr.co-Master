from pathlib import Path

from fastapi.testclient import TestClient

from app.main import app
from app.routers import estimations
from app.services import session_service
from app.sessions import MAX_TURNS, SessionStore


client = TestClient(app)


def test_health_endpoint() -> None:
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
        "service": "estimator-cag",
        "version": "0.1.0",
    }


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
    assert session_service.session_store.get(body["session_id"]) is not None


def test_get_session_detail_returns_persisted_state(tmp_path: Path, monkeypatch) -> None:
    store = SessionStore(path=tmp_path / "sessions.json")
    monkeypatch.setattr(session_service, "session_store", store)

    session_id = session_service.create_session()
    session = store.get(session_id)
    assert session is not None
    session.history.add_turn("user one", "assistant one")
    session.remember_document_sources(["/tmp/spec.md"])
    session.add_conversation_message("user", "Solicitud visible")
    store.save_session(session_id)

    response = client.get(f"/api/v1/sessions/{session_id}")

    assert response.status_code == 200
    body = response.json()
    assert body["session_id"] == session_id
    assert body["turns"] == [["user one", "assistant one"]]
    assert body["document_sources"] == ["/tmp/spec.md"]
    assert body["conversation_messages"] == [{"role": "user", "content": "Solicitud visible"}]


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
    assert str(doc_path) in session_service.session_store.get(session_id).document_sources


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
