from fastapi.testclient import TestClient

from app.main import app
from app.routers import estimations


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
