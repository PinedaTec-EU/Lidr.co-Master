from app.domain.models import FailureType, RunStatus
from app.domain.scoring import HealthScorer
from tests.builders import run, stage


def test_score_penalizes_failed_run_and_failed_stage():
    scorer = HealthScorer()
    current = run(
        status=RunStatus.FAILED,
        stages=(stage("create-order", status=RunStatus.FAILED, error_type=FailureType.CONTRACT_VALIDATION),),
    )

    assert scorer.score(current, []) == 53


def test_score_penalizes_duration_regression_against_passed_history():
    scorer = HealthScorer()
    current = run(duration_ms=1800)
    history = [run(run_id="previous-1", duration_ms=1000), run(run_id="previous-2", duration_ms=950)]

    assert scorer.score(current, history) == 80


def test_dominant_failure_type_returns_none_when_run_passed():
    assert HealthScorer().dominant_failure_type(run()) == FailureType.NONE

