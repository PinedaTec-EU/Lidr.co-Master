import pytest
from pydantic import ValidationError

from app.schemas import (
    DetailLevel,
    EstimationRequest,
    OutputFormat,
    ProjectType,
)


def test_estimation_request_accepts_valid_payload() -> None:
    request = EstimationRequest(
        description="Aplicación móvil con login, chat y notificaciones push para equipos de ventas.",
        project_type=ProjectType.MOBILE_APP,
        detail_level=DetailLevel.MEDIUM,
        output_format=OutputFormat.NARRATIVE,
    )

    assert request.model_dump(mode="json") == {
        "description": "Aplicación móvil con login, chat y notificaciones push para equipos de ventas.",
        "project_type": "mobile_app",
        "detail_level": "medium",
        "output_format": "narrative",
    }


def test_estimation_request_rejects_short_description() -> None:
    with pytest.raises(ValidationError):
        EstimationRequest(
            description="Muy corto",
            project_type=ProjectType.WEB_SAAS,
            detail_level=DetailLevel.SUMMARY,
            output_format=OutputFormat.PHASES_TABLE,
        )
