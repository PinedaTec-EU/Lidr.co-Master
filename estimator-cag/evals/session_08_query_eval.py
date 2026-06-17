from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path
from statistics import mean

import httpx
from dotenv import load_dotenv

from app.embedding_pipeline.schemas import EmbeddingModelName
from scripts.query_examples import DEFAULT_QUERY_EXAMPLES, QueryExample, SearchHit, fetch_results

DEFAULT_REPORT_PATH = Path("evals/session-08-query-eval.md")


@dataclass(frozen=True)
class ExpectedChunk:
    budget_id: str
    component_id: str

    @property
    def semantic_ref(self) -> str:
        return f"{self.budget_id}::{self.component_id}"


@dataclass(frozen=True)
class QueryAssessment:
    example: QueryExample
    expectation: str
    expected_rank: int | None
    expected_chunks: tuple[ExpectedChunk, ...] = ()
    observed_rank: int | None = None
    observed_top_ref: str = ""
    observed_top_distance: float | None = None
    status: str = "review"
    takeaway: str = ""


DIRECT_MATCH = ExpectedChunk("BUD-2024-001", "AUTH-001")
LIKELY_INTEGRATION_CHUNKS = (
    ExpectedChunk("BUD-2024-001", "API-002"),
    ExpectedChunk("BUD-2024-010", "AVL-001"),
    ExpectedChunk("BUD-2024-013", "PUB-002"),
)


QUERY_EXPECTATIONS = {
    "direct-match": {
        "expectation": "El chunk AUTH-001 debería aparecer en top-1.",
        "expected_rank": 1,
        "expected_chunks": (DIRECT_MATCH,),
    },
    "semantic-rephrase": {
        "expectation": "La misma idea debería seguir recuperando AUTH-001 en top-3.",
        "expected_rank": 3,
        "expected_chunks": (DIRECT_MATCH,),
    },
    "out-of-domain": {
        "expectation": "No debería aparecer un match fuerte; la distancia top-1 debería empeorar claramente.",
        "expected_rank": 6,
        "expected_chunks": (),
    },
    "ambiguous": {
        "expectation": "Es normal ver varios candidatos parciales; lo importante es observar mezcla y ranking.",
        "expected_rank": None,
        "expected_chunks": LIKELY_INTEGRATION_CHUNKS,
    },
    "very-specific": {
        "expectation": "No debería existir un match fuerte si el corpus no cubre microservicios + Kubernetes.",
        "expected_rank": 6,
        "expected_chunks": (),
    },
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate a fast-glance report for session 08 search queries.")
    parser.add_argument("--base-url", default="http://localhost:8000")
    parser.add_argument("--k", type=int, default=5)
    parser.add_argument(
        "--model",
        default=EmbeddingModelName.TEXT_EMBEDDING_3_SMALL.value,
        choices=[model.value for model in EmbeddingModelName],
    )
    parser.add_argument("--report-path", default=str(DEFAULT_REPORT_PATH))
    return parser.parse_args()


def _chunk_matches(hit: SearchHit, expected: ExpectedChunk) -> bool:
    budget_id = hit.metadata.get("budget_id")
    component_id = hit.metadata.get("component_id")
    return budget_id == expected.budget_id and component_id == expected.component_id


def _find_expected_rank(hits: list[SearchHit], expected_chunks: tuple[ExpectedChunk, ...]) -> int | None:
    if not expected_chunks:
        return None
    for index, hit in enumerate(hits, start=1):
        if any(_chunk_matches(hit, expected) for expected in expected_chunks):
            return index
    return None


def _assess_query(
    *,
    example: QueryExample,
    hits: list[SearchHit],
    direct_match_distance: float | None,
) -> QueryAssessment:
    config = QUERY_EXPECTATIONS[example.label]
    observed_rank = _find_expected_rank(hits, config["expected_chunks"])
    top_hit = hits[0] if hits else None
    top_ref = top_hit.semantic_ref if top_hit else "no-result"
    top_distance = top_hit.distance if top_hit else None

    if example.label == "direct-match":
        status = "ok" if observed_rank == 1 else "warn"
        takeaway = "Baseline retrieval fuerte." if status == "ok" else "El sanity check principal no queda en top-1."
    elif example.label == "semantic-rephrase":
        status = "ok" if observed_rank is not None and observed_rank <= 3 else "warn"
        takeaway = (
            "La semántica aguanta reformulación."
            if status == "ok"
            else "La query reformulada pierde demasiada precisión respecto al caso directo."
        )
    elif example.label in {"out-of-domain", "very-specific"}:
        if direct_match_distance is None or top_distance is None:
            status = "review"
            takeaway = "No hay baseline suficiente para comparar distancias."
        else:
            ratio = top_distance / max(direct_match_distance, 1e-9)
            status = "ok" if ratio >= 1.35 else "warn"
            takeaway = (
                "La distancia empeora claramente frente al caso fácil."
                if status == "ok"
                else "El sistema sigue viendo demasiado parecido un caso que debería alejarse."
            )
    else:
        status = "review"
        takeaway = (
            "Consulta ambigua: sirve para observar mezcla de candidatos, no para aprobar o suspender automáticamente."
        )

    return QueryAssessment(
        example=example,
        expectation=config["expectation"],
        expected_rank=config["expected_rank"],
        expected_chunks=config["expected_chunks"],
        observed_rank=observed_rank,
        observed_top_ref=top_ref,
        observed_top_distance=top_distance,
        status=status,
        takeaway=takeaway,
    )


def _rank_for_chart(assessment: QueryAssessment, *, fallback_rank: int) -> int:
    if assessment.observed_rank is not None:
        return assessment.observed_rank
    if assessment.expected_rank == 6:
        return fallback_rank
    return fallback_rank


def _render_chart(assessments: list[QueryAssessment], *, fallback_rank: int) -> str:
    chart_cases = [item for item in assessments if item.expected_rank is not None]
    labels = ", ".join(f'"{item.example.label}"' for item in chart_cases)
    expected = ", ".join(str(item.expected_rank) for item in chart_cases)
    observed = ", ".join(str(_rank_for_chart(item, fallback_rank=fallback_rank)) for item in chart_cases)
    y_max = max([fallback_rank, *[item.expected_rank or fallback_rank for item in chart_cases]])
    return "\n".join(
        [
            "```mermaid",
            "xychart-beta",
            '    title "Expected Rank vs Observed Rank"',
            f"    x-axis [{labels}]",
            f'    y-axis "Rank (6 = fuera del top-5)" 1 --> {y_max}',
            f'    bar "Expected" [{expected}]',
            f'    bar "Observed" [{observed}]',
            "```",
        ]
    )


def render_report(
    *,
    base_url: str,
    k: int,
    model: str,
    assessments: list[QueryAssessment],
) -> str:
    ok_count = sum(1 for item in assessments if item.status == "ok")
    warn_count = sum(1 for item in assessments if item.status == "warn")
    review_count = sum(1 for item in assessments if item.status == "review")
    top_distances = [item.observed_top_distance for item in assessments if item.observed_top_distance is not None]
    mean_distance = mean(top_distances) if top_distances else 0.0

    quick_rows = [
        "| query | status | expected | observed | top-1 ref | lectura rápida |",
        "|---|---|---:|---:|---|---|",
    ]
    detail_rows = [
        "| query | expectation | expected_chunks | expected_rank | observed_rank | top-1 ref | top-1 distance | takeaway |",
        "|---|---|---|---:|---:|---|---:|---|",
    ]

    for item in assessments:
        expected_chunks = ", ".join(chunk.semantic_ref for chunk in item.expected_chunks) or "n/a"
        expected_rank = str(item.expected_rank) if item.expected_rank is not None else "review"
        observed_rank = str(item.observed_rank) if item.observed_rank is not None else "n/a"
        top_distance = f"{item.observed_top_distance:.4f}" if item.observed_top_distance is not None else "n/a"
        quick_rows.append(
            f"| {item.example.label} | {item.status} | {expected_rank} | {observed_rank} | {item.observed_top_ref} | {item.takeaway} |"
        )
        detail_rows.append(
            f"| {item.example.label} | {item.expectation} | {expected_chunks} | {expected_rank} | "
            f"{observed_rank} | {item.observed_top_ref} | {top_distance} | {item.takeaway} |"
        )

    report = "\n".join(
        [
            "# Session 08 Query Evaluation",
            "",
            "## Lectura en 10 segundos",
            "",
            f"- Base URL: `{base_url}`",
            f"- Modelo: `{model}`",
            f"- Top K: `{k}`",
            f"- Queries evaluadas: `{len(assessments)}`",
            f"- Estado rápido: `{ok_count} ok`, `{warn_count} warn`, `{review_count} review`",
            f"- Distancia media top-1 observada: `{mean_distance:.4f}`",
            "",
            "\n".join(quick_rows),
            "",
            "## Desvío visual",
            "",
            _render_chart(assessments, fallback_rank=k + 1),
            "",
            "## Detalle",
            "",
            "\n".join(detail_rows),
            "",
            "## Conclusiones",
            "",
            (
                "Este artefacto no es todavía un golden dataset formal. Sirve para responder rápido si el retrieval "
                "acierta en el caso fácil, aguanta una reformulación semántica y se aleja lo suficiente cuando la query "
                "sale del dominio esperado."
            ),
            "",
            (
                "Los casos `out-of-domain` y `very-specific` se juzgan por contraste con la distancia del caso directo, "
                "no por una verdad absoluta. Eso deja visible si el sistema necesita un umbral explícito de rechazo."
            ),
            "",
            (
                "La query `ambiguous` se mantiene como inspección guiada: su valor está en mostrar mezcla de candidatos, "
                "no en forzar un pass/fail artificial."
            ),
        ]
    )
    return report + "\n"


def main() -> None:
    load_dotenv()
    args = parse_args()
    report_path = Path(args.report_path)

    with httpx.Client() as client:
        results = {
            example.label: fetch_results(
                client=client,
                base_url=args.base_url,
                query=example.query,
                k=args.k,
                model=args.model,
            )
            for example in DEFAULT_QUERY_EXAMPLES
        }

    direct_match_hits = results.get("direct-match", [])
    direct_match_distance = direct_match_hits[0].distance if direct_match_hits else None
    assessments = [
        _assess_query(
            example=example,
            hits=results[example.label],
            direct_match_distance=direct_match_distance,
        )
        for example in DEFAULT_QUERY_EXAMPLES
    ]

    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(
        render_report(
            base_url=args.base_url,
            k=args.k,
            model=args.model,
            assessments=assessments,
        ),
        encoding="utf-8",
    )
    print(f"Wrote session 08 query evaluation to {report_path}")


if __name__ == "__main__":
    main()
