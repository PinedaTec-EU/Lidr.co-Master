from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class GoldenCase:
    case_id: str
    question: str
    ground_truth: str
    required_contexts: tuple[str, ...]


def load_golden_set(path: Path) -> list[GoldenCase]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    return [
        GoldenCase(
            case_id=item["id"],
            question=item["question"],
            ground_truth=item["ground_truth"],
            required_contexts=tuple(item["required_contexts"]),
        )
        for item in payload["cases"]
    ]


def build_ragas_rows(cases: list[GoldenCase], observations: dict[str, dict]) -> list[dict]:
    return [
        {
            "question": case.question,
            "answer": observations[case.case_id]["answer"],
            "contexts": observations[case.case_id]["contexts"],
            "ground_truth": case.ground_truth,
        }
        for case in cases
    ]


def evaluate_rows(rows: list[dict]) -> dict:
    from datasets import Dataset
    from ragas import evaluate
    from ragas.metrics import answer_relevancy, context_precision, context_recall, faithfulness

    result = evaluate(
        Dataset.from_list(rows),
        metrics=[faithfulness, answer_relevancy, context_precision, context_recall],
    )
    return result.to_pandas().to_dict(orient="records")


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the Session 11 RAGAS baseline from recorded observations.")
    parser.add_argument("--golden-set", default="evals/session-11-golden-set.json")
    parser.add_argument("--observations", required=True, help="JSON object keyed by golden-set id with answer and contexts.")
    parser.add_argument("--report", help="Write per-case RAGAS metrics as JSON.")
    args = parser.parse_args()
    cases = load_golden_set(Path(args.golden_set))
    observations = json.loads(Path(args.observations).read_text(encoding="utf-8"))
    missing = [case.case_id for case in cases if case.case_id not in observations]
    if missing:
        raise SystemExit(f"Missing observations for: {', '.join(missing)}")
    rows = build_ragas_rows(cases, observations)
    if not args.report:
        print(json.dumps(rows, ensure_ascii=False, indent=2))
        return
    report = evaluate_rows(rows)
    Path(args.report).write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
