from fastapi.testclient import TestClient

from app.api.analysis import repository
from app.main import app
from tests.builders import InMemoryRunRepository, run


def test_health_endpoint():
    client = TestClient(app)

    response = client.get("/health")

    assert response.status_code == 200
    assert response.json()["service"] == "sih-smart-analysis"


def test_recent_endpoint_returns_analysis():
    app.dependency_overrides[repository] = lambda: InMemoryRunRepository(
        [run(run_id="old", day=1), run(run_id="current", day=2)]
    )
    client = TestClient(app)

    response = client.post(
        "/api/v1/analysis/recent",
        json={"workflow": "checkout-smoke", "environment": "staging", "limit": 2},
    )

    app.dependency_overrides.clear()
    assert response.status_code == 200
    assert response.json()["current_run_id"] == "current"

