from fastapi.testclient import TestClient

from app.application.estimation import EstimationService
from app.application.estimation_jobs import EstimationJobService
from app.dependencies import get_estimation_job_service, get_estimation_service
from app.main import app
from app.schemas import (
    DetailLevel,
    EstimationJob,
    EstimationJobStatus,
    EstimationRequest,
    EstimationResponse,
    OutputFormat,
    ProjectType,
)


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


def test_estimate_rejects_too_short_description() -> None:
    response = client.post(
        "/api/v1/estimate",
        json={
            "description": "demasiado corto",
            "project_type": "web_saas",
            "detail_level": "medium",
            "output_format": "phases_table",
        },
    )

    assert response.status_code == 422


def test_estimate_returns_llm_result() -> None:
    class FakeEstimationService(EstimationService):
        def __init__(self) -> None:
            pass

        async def estimate(
            self,
            request: EstimationRequest,
            prompt_version: str = "v1",
        ) -> EstimationResponse:
            assert request.description == "Necesitamos un portal B2B con autenticación y catálogo privado."
            assert request.project_type is ProjectType.WEB_SAAS
            return EstimationResponse(text="## Estimación de prueba", prompt_version=prompt_version)

    app.dependency_overrides[get_estimation_service] = FakeEstimationService

    response = client.post(
        "/api/v1/estimate",
        json={
            "description": "Necesitamos un portal B2B con autenticación y catálogo privado.",
            "project_type": ProjectType.WEB_SAAS.value,
            "detail_level": DetailLevel.MEDIUM.value,
            "output_format": OutputFormat.PHASES_TABLE.value,
        },
    )

    body = response.json()
    assert response.status_code == 200
    assert body["text"] == "## Estimación de prueba"
    assert body["prompt_version"] == "v1"
    app.dependency_overrides.clear()


def test_create_estimation_job_returns_pending_job() -> None:
    class FakeEstimationJobService:
        async def submit(
            self,
            request: EstimationRequest,
            prompt_version: str = "v1",
        ) -> EstimationJob:
            assert request.project_type is ProjectType.WEB_SAAS
            return EstimationJob(
                id="job-123",
                status=EstimationJobStatus.PENDING,
                created_at="2026-05-14T00:00:00+00:00",
                updated_at="2026-05-14T00:00:00+00:00",
                request=request,
                prompt_version=prompt_version,
            )

    app.dependency_overrides[get_estimation_job_service] = FakeEstimationJobService

    response = client.post(
        "/api/v1/estimate-jobs",
        json={
            "description": "Necesitamos un portal B2B con autenticación y catálogo privado.",
            "project_type": ProjectType.WEB_SAAS.value,
            "detail_level": DetailLevel.MEDIUM.value,
            "output_format": OutputFormat.PHASES_TABLE.value,
        },
    )

    body = response.json()
    assert response.status_code == 202
    assert body["id"] == "job-123"
    assert body["status"] == "pending"
    app.dependency_overrides.clear()


def test_list_estimation_jobs_returns_history() -> None:
    class FakeEstimationJobService:
        async def list(self) -> list[EstimationJob]:
            return [
                EstimationJob(
                    id="job-1",
                    status=EstimationJobStatus.SUCCEEDED,
                    created_at="2026-05-14T00:00:00+00:00",
                    updated_at="2026-05-14T00:01:00+00:00",
                    request=EstimationRequest(
                        description="Necesitamos una app móvil para reservas y pagos con panel administrativo.",
                        project_type=ProjectType.MOBILE_APP,
                        detail_level=DetailLevel.MEDIUM,
                        output_format=OutputFormat.PHASES_TABLE,
                    ),
                    prompt_version="v1",
                    response=EstimationResponse(text="## Estimación", prompt_version="v1"),
                )
            ]

    app.dependency_overrides[get_estimation_job_service] = FakeEstimationJobService

    response = client.get("/api/v1/estimate-jobs")

    body = response.json()
    assert response.status_code == 200
    assert len(body) == 1
    assert body[0]["status"] == "succeeded"
    app.dependency_overrides.clear()
