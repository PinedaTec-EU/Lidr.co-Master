from app.prompts.loader import render_estimation_prompt
from app.schemas import DetailLevel, EstimationRequest, OutputFormat, ProjectType


def _request(
    output_format: OutputFormat = OutputFormat.PHASES_TABLE,
    detail_level: DetailLevel = DetailLevel.MEDIUM,
) -> EstimationRequest:
    return EstimationRequest(
        description=(
            "Necesitamos una plataforma SaaS para coordinar reservas, pagos y "
            "panel operativo con reglas de disponibilidad."
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
    phases_system, _user = render_estimation_prompt(_request(output_format=OutputFormat.PHASES_TABLE))
    narrative_system, _user = render_estimation_prompt(_request(output_format=OutputFormat.NARRATIVE))

    assert "phases_table" in phases_system
    assert "confidence_pct" in phases_system
    assert "phases_table" not in narrative_system
    assert "confidence_pct" not in narrative_system


def test_detailed_includes_assumptions_by_phase_but_summary_does_not() -> None:
    detailed_system, _user = render_estimation_prompt(_request(detail_level=DetailLevel.DETAILED))
    summary_system, _user = render_estimation_prompt(_request(detail_level=DetailLevel.SUMMARY))

    assert "Lista supuestos por fase" in detailed_system
    assert "Lista supuestos por fase" not in summary_system
