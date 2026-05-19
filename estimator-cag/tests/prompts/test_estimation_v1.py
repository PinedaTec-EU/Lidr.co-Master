from app.prompts.loader import render_estimation_prompt
from app.schemas import DetailLevel, EstimationRequest, OutputFormat, ProjectType


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
