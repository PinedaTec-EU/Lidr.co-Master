import pytest

from app.prompts.loader import render_estimation_prompt
from app.schemas import DetailLevel, EstimationRequest, OutputFormat, ProjectType
from app.sessions import ExternalContextItem, ProjectMetadata


def _request(
    *,
    detail_level: DetailLevel = DetailLevel.MEDIUM,
    output_format: OutputFormat = OutputFormat.NARRATIVE,
) -> EstimationRequest:
    return EstimationRequest(
        description=(
            "Portal B2B para clientes corporativos con autenticación, reporting de consumo "
            "y notificaciones automáticas por email."
        ),
        project_type=ProjectType.WEB_SAAS,
        detail_level=detail_level,
        output_format=output_format,
    )


def test_render_includes_description_inside_project_description_block() -> None:
    request = _request()

    _system, user = render_estimation_prompt(request)

    assert "<project_description>" in user
    assert request.description in user
    assert "</project_description>" in user


def test_phases_table_instructions_change_with_output_format() -> None:
    phases_request = _request(output_format=OutputFormat.PHASES_TABLE)
    narrative_request = _request(output_format=OutputFormat.NARRATIVE)

    phases_system, _user = render_estimation_prompt(phases_request)
    narrative_system, _user = render_estimation_prompt(narrative_request)

    assert "confidence_pct" in phases_system
    assert "confidence_pct" not in narrative_system


def test_detailed_instructions_change_with_detail_level() -> None:
    detailed_request = _request(detail_level=DetailLevel.DETAILED)
    summary_request = _request(detail_level=DetailLevel.SUMMARY)

    detailed_system, _user = render_estimation_prompt(detailed_request)
    summary_system, _user = render_estimation_prompt(summary_request)

    assert "asunciones por fase" in detailed_system
    assert "asunciones por fase" not in summary_system


def test_render_rejects_unknown_prompt_version() -> None:
    request = _request()

    with pytest.raises(Exception):
        render_estimation_prompt(request, version="v999")


def test_render_injects_project_metadata_block() -> None:
    request = _request()
    metadata = ProjectMetadata(
        project_name="Atlas",
        assumed_team_size=4,
        mentioned_technologies=["react", "postgresql"],
        agreed_scope="Portal B2B con reporting y automatizaciones.",
    )

    system, _user = render_estimation_prompt(request, project_metadata=metadata)

    assert "<project_metadata>" in system
    assert "project_name: Atlas" in system
    assert "mentioned_technologies: react, postgresql" in system


def test_render_injects_external_context_block() -> None:
    request = _request()
    external_context = [
        ExternalContextItem(
            source="notion",
            title="Atlas kickoff",
            content="Roadmap inicial, restricciones y objetivos del cliente.",
            url="https://notion.so/atlas",
            updated_at="2026-05-19T10:00:00Z",
            relevance_reason="Explicit notion_page_id configured in the session.",
        )
    ]

    system, _user = render_estimation_prompt(request, external_context=external_context)

    assert "<external_context>" in system
    assert 'source=notion title="Atlas kickoff"' in system
    assert "Roadmap inicial, restricciones y objetivos del cliente." in system
