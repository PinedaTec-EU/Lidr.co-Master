from __future__ import annotations

from pathlib import Path

from evals.session_10_retrieval_eval import (
    GoldenSetDefinition,
    RetrievalVariant,
    VariantCaseObservation,
    load_golden_set,
    precision_at_k,
    render_report,
    summarize_variant,
)


def test_precision_at_k_uses_top_k_window() -> None:
    assert precision_at_k(
        ["BUD-2024-001::AUTH-001", "BUD-2024-003::VID-001", "BUD-2024-002::CAT-001"],
        ("BUD-2024-001::AUTH-001", "BUD-2024-002::CAT-001"),
        2,
    ) == 0.5


def test_load_golden_set_reads_versioned_cases(tmp_path: Path) -> None:
    golden_set_path = tmp_path / "golden-set.json"
    golden_set_path.write_text(
        """
{
  "annotation_criterion": "Relevant if it serves as direct estimation reference.",
  "top_k": 4,
  "runs_per_query": 2,
  "queries": [
    {
      "id": "q01",
      "query": "oauth backend finance",
      "relevant_chunk_ids": ["BUD-2024-001::AUTH-001"]
    }
  ]
}
""".strip()
    )

    loaded = load_golden_set(golden_set_path)

    assert loaded.annotation_criterion == "Relevant if it serves as direct estimation reference."
    assert loaded.top_k == 4
    assert loaded.runs_per_query == 2
    assert loaded.cases[0].case_id == "q01"


def test_render_report_compares_variants_against_baseline() -> None:
    observations = [
        VariantCaseObservation(
            variant="semantic-baseline",
            case_id="q01",
            query="oauth backend finance",
            relevant_chunk_ids=("BUD-2024-001::AUTH-001",),
            retrieved_chunk_ids=("BUD-2024-001::AUTH-001",),
            precision_at_k=1.0,
            recall_at_k=1.0,
            median_latency_ms=35.0,
            top_ref="BUD-2024-001::AUTH-001",
        ),
        VariantCaseObservation(
            variant="semantic-reranked",
            case_id="q01",
            query="oauth backend finance",
            relevant_chunk_ids=("BUD-2024-001::AUTH-001",),
            retrieved_chunk_ids=("BUD-2024-001::AUTH-001",),
            precision_at_k=1.0,
            recall_at_k=1.0,
            median_latency_ms=57.0,
            top_ref="BUD-2024-001::AUTH-001",
        ),
    ]
    summaries = [
        summarize_variant(RetrievalVariant("semantic-baseline", {}), observations),
        summarize_variant(RetrievalVariant("semantic-reranked", {}), observations),
    ]

    report = render_report(
        base_url="http://localhost:8000",
        model="text-embedding-3-small",
        golden_set_path=Path("evals/session-10-golden-set.json"),
        golden_set=GoldenSetDefinition(
            annotation_criterion="Relevant if it serves as direct estimation reference.",
            top_k=5,
            runs_per_query=3,
            cases=(),
        ),
        observations=observations,
        summaries=summaries,
    )

    assert "# Session 10 Retrieval Evaluation" in report
    assert "## Resumen por variante" in report
    assert "| semantic-reranked | 1.0000 | 1.0000 | 57.00 | +0.0000 | +22.00 |" in report
    assert "Este arnes artesanal busca responder una pregunta de arquitectura" in report
