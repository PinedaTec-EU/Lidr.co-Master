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
    assert "openai" in response.json()["friendly_names"]


def test_estimate_rejects_blank_transcription() -> None:
    response = client.post("/api/v1/estimate", json={"transcription": "   "})

    assert response.status_code == 400
    assert response.json()["detail"] == "La transcripción no puede estar vacía"


def test_estimate_returns_llm_result(monkeypatch) -> None:
    async def fake_get_estimation(transcription: str, **_: str | None) -> dict:
        assert transcription == "Necesitamos un portal B2B con autenticación."
        return {
            "estimation": "## Estimación de prueba",
            "model": "openai/gpt-4o-mini",
            "provider": "openai",
            "tokens_used": {"prompt": 10, "completion": 20, "total": 30},
        }

    monkeypatch.setattr(estimations, "get_estimation", fake_get_estimation)

    response = client.post(
        "/api/v1/estimate",
        json={"transcription": "Necesitamos un portal B2B con autenticación."},
    )

    body = response.json()
    assert response.status_code == 200
    assert body["estimation"] == "## Estimación de prueba"
    assert body["model"] == "openai/gpt-4o-mini"
    assert body["provider"] == "openai"
    assert body["tokens_used"] == {"prompt": 10, "completion": 20, "total": 30}
    assert body["timestamp"]
