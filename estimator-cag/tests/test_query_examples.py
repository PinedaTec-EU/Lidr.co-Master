from __future__ import annotations

from scripts.query_examples import SearchHit, render_report, shorten


def test_shorten_truncates_long_content() -> None:
    text = "A " * 100
    shortened = shorten(text, limit=20)
    assert shortened.endswith("...")
    assert len(shortened) == 20


def test_render_report_lists_hits_in_terminal_friendly_format() -> None:
    report = render_report(
        base_url="http://localhost:8000",
        k=5,
        model="text-embedding-3-small",
        results_by_query=[
            (
                "direct-match",
                "REST API development with JWT authentication for financial sector",
                [
                    SearchHit(
                        chunk_id=12,
                        distance=0.123456,
                        chunk_type="budget_component",
                        content="OAuth 2.0 authentication backend with JWT tokens for a banking application",
                    )
                ],
            )
        ],
    )

    assert "Session 8 semantic search examples" in report
    assert "## direct-match" in report
    assert "distance=0.1235" in report
    assert "chunk_type=budget_component" in report
    assert "OAuth 2.0 authentication backend" in report
