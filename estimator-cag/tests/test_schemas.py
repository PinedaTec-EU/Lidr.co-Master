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
        "retrieval": {
            "enabled": False,
            "query_override": None,
            "k": 5,
            "score_threshold": None,
            "rewrite_strategy": "disabled",
            "max_chunks": 3,
            "max_context_chars": 1800,
            "include_scores": True,
        },
    }


def test_estimation_request_rejects_short_description() -> None:
    with pytest.raises(ValidationError):
        EstimationRequest(
            description="Muy corto",
            project_type=ProjectType.WEB_SAAS,
            detail_level=DetailLevel.SUMMARY,
            output_format=OutputFormat.PHASES_TABLE,
        )


def test_estimation_request_accepts_max_length_description() -> None:
    request = EstimationRequest(
        description="x" * 2000,
        project_type=ProjectType.DATA_PIPELINE,
        detail_level=DetailLevel.DETAILED,
        output_format=OutputFormat.LINE_ITEMS,
    )

    assert len(request.description) == 2000


def test_estimation_request_rejects_description_above_max_length() -> None:
    with pytest.raises(ValidationError):
        EstimationRequest(
            description="x" * 2001,
            project_type=ProjectType.DATA_PIPELINE,
            detail_level=DetailLevel.DETAILED,
            output_format=OutputFormat.LINE_ITEMS,
        )
