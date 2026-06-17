from __future__ import annotations

from evals.session_08_query_eval import QueryAssessment, render_report
from scripts.query_examples import QueryExample


def test_render_report_prioritizes_fast_glance_summary() -> None:
    assessments = [
        QueryAssessment(
            example=QueryExample(
                label="direct-match",
                query="REST API development with JWT authentication for financial sector",
            ),
            expectation="AUTH-001 debería aparecer en top-1.",
            expected_rank=1,
            observed_rank=1,
            observed_top_ref="BUD-2024-001::AUTH-001",
            observed_top_distance=0.1234,
            status="ok",
            takeaway="Baseline retrieval fuerte.",
        ),
        QueryAssessment(
            example=QueryExample(
                label="out-of-domain",
                query="mobile application for restaurant reservations",
            ),
            expectation="No debería aparecer un match fuerte.",
            expected_rank=6,
            observed_rank=None,
            observed_top_ref="BUD-2024-003::VID-001",
            observed_top_distance=0.4012,
            status="warn",
            takeaway="El sistema sigue viendo demasiado parecido un caso fuera de dominio.",
        ),
    ]

    report = render_report(
        base_url="http://localhost:8000",
        k=5,
        model="text-embedding-3-small",
        assessments=assessments,
    )

    assert "# Session 08 Query Evaluation" in report
    assert "## Lectura en 10 segundos" in report
    assert "| direct-match | ok | 1 | 1 | BUD-2024-001::AUTH-001 |" in report
    assert 'title "Expected Rank vs Observed Rank"' in report
    assert "Este artefacto no es todavía un golden dataset formal." in report
