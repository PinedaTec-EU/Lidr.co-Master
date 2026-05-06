from app.application.rag_semantic_analysis import SemanticRunsAnalyzer
from app.domain.models import FailureType, RunStatus
from tests.builders import InMemoryRunRepository, run, stage


def test_semantic_analyzer_retrieves_similar_failure_from_full_history():
    current = run(
        run_id="current",
        day=5,
        status=RunStatus.FAILED,
        stages=(
            stage(
                "create-order",
                status=RunStatus.FAILED,
                http_status=400,
                error_type=FailureType.CONTRACT_VALIDATION,
                message="payment.method missing",
            ),
        ),
    )
    similar = run(
        run_id="similar-old",
        day=1,
        status=RunStatus.FAILED,
        stages=(
            stage(
                "create-order",
                status=RunStatus.FAILED,
                http_status=400,
                error_type=FailureType.CONTRACT_VALIDATION,
                message="payment.method missing after contract change",
            ),
        ),
    )
    unrelated = run(
        run_id="unrelated",
        day=2,
        stages=(stage("login", status=RunStatus.PASSED, http_status=200),),
    )

    retrieved = SemanticRunsAnalyzer(InMemoryRunRepository([similar, unrelated])).retrieve_similar(current, top_k=2)

    assert retrieved[0][0].run_id == "similar-old"
    assert retrieved[0][1] > retrieved[1][1]

