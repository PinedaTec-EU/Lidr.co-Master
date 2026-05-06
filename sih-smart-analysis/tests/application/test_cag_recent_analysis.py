from app.application.cag_recent_analysis import RecentRunsAnalyzer
from app.domain.models import FailureType, RunStatus, Severity
from tests.builders import InMemoryRunRepository, run, stage


def test_recent_analyzer_uses_latest_run_as_current_and_detects_stage_failure_regression():
    history = [
        run(run_id="old-1", day=1, stages=(stage("create-order", duration_ms=1000),)),
        run(run_id="old-2", day=2, stages=(stage("create-order", duration_ms=1100),)),
        run(
            run_id="current",
            day=3,
            status=RunStatus.FAILED,
            duration_ms=3000,
            stages=(
                stage(
                    "create-order",
                    status=RunStatus.FAILED,
                    duration_ms=2200,
                    http_status=400,
                    error_type=FailureType.CONTRACT_VALIDATION,
                ),
            ),
        ),
    ]

    result = RecentRunsAnalyzer(InMemoryRunRepository(history)).analyze("checkout-smoke", "staging", limit=3)

    assert result.mode == "recent-cag"
    assert result.current_run_id == "current"
    assert result.failure_type == FailureType.CONTRACT_VALIDATION
    assert result.regressions[0].severity == Severity.HIGH
    assert result.sources == ("current", "old-2", "old-1")
    assert "contract validation" in result.recommendations[0]


def test_recent_analyzer_rejects_limit_without_history_window():
    analyzer = RecentRunsAnalyzer(InMemoryRunRepository([]))

    try:
        analyzer.analyze("checkout-smoke", "staging", limit=1)
    except ValueError as exc:
        assert "at least 2" in str(exc)
    else:
        raise AssertionError("expected ValueError")

