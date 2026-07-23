from pathlib import Path

from evals.session_11_ragas_eval import build_ragas_rows, load_golden_set


GOLDEN_SET_PATH = Path(__file__).parents[1] / "evals/session-11-golden-set.json"


def test_session_11_golden_set_has_five_cases_and_abstention_case() -> None:
    cases = load_golden_set(GOLDEN_SET_PATH)

    assert len(cases) == 5
    assert next(case for case in cases if case.case_id == "ambiguous").required_contexts == ()


def test_ragas_rows_keep_question_answer_contexts_and_ground_truth() -> None:
    cases = load_golden_set(GOLDEN_SET_PATH)[:1]
    rows = build_ragas_rows(cases, {"auth-platform": {"answer": "answer", "contexts": ["context"]}})

    assert rows[0]["answer"] == "answer"
    assert rows[0]["contexts"] == ["context"]
    assert rows[0]["ground_truth"]
