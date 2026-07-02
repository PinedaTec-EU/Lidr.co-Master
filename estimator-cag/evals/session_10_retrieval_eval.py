from __future__ import annotations

import argparse
import json
import statistics
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import httpx
from dotenv import load_dotenv

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from app.embedding_pipeline.schemas import EmbeddingModelName

DEFAULT_GOLDEN_SET_PATH = Path("evals/session-10-golden-set.json")
DEFAULT_REPORT_PATH = Path("evals/session-10-retrieval-eval.md")


@dataclass(frozen=True)
class GoldenSetCase:
    case_id: str
    query: str
    relevant_chunk_ids: tuple[str, ...]


@dataclass(frozen=True)
class GoldenSetDefinition:
    annotation_criterion: str
    top_k: int
    runs_per_query: int
    cases: tuple[GoldenSetCase, ...]


@dataclass(frozen=True)
class RetrievalVariant:
    label: str
    payload: dict[str, object]


@dataclass(frozen=True)
class VariantCaseObservation:
    variant: str
    case_id: str
    query: str
    relevant_chunk_ids: tuple[str, ...]
    retrieved_chunk_ids: tuple[str, ...]
    precision_at_k: float
    recall_at_k: float
    median_latency_ms: float
    top_ref: str


@dataclass(frozen=True)
class VariantSummary:
    variant: str
    mean_precision_at_k: float
    mean_recall_at_k: float
    median_latency_ms: float


DEFAULT_VARIANTS = (
    RetrievalVariant(label="semantic-baseline", payload={}),
    RetrievalVariant(
        label="semantic-reranked",
        payload={
            "candidate_pool_k": 12,
            "rerank_strategy": "token_overlap",
            "rerank_alpha": 0.7,
        },
    ),
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Artisanal retrieval evaluation for session 10 variants."
    )
    parser.add_argument("--base-url", default="http://localhost:8000")
    parser.add_argument(
        "--model",
        default=EmbeddingModelName.TEXT_EMBEDDING_3_SMALL.value,
        choices=[item.value for item in EmbeddingModelName],
    )
    parser.add_argument("--api-key", default="", help="Optional retrieval API key.")
    parser.add_argument(
        "--golden-set",
        default=str(DEFAULT_GOLDEN_SET_PATH),
        help="Path to the hand-annotated golden set JSON.",
    )
    parser.add_argument(
        "--output",
        default=str(DEFAULT_REPORT_PATH),
        help="Markdown report output path.",
    )
    parser.add_argument(
        "--top-k",
        type=int,
        default=None,
        help="Override top-k from the golden set file.",
    )
    parser.add_argument(
        "--runs-per-query",
        type=int,
        default=None,
        help="Override number of runs per query from the golden set file.",
    )
    return parser.parse_args()


def load_golden_set(path: Path) -> GoldenSetDefinition:
    payload = json.loads(path.read_text())
    cases = tuple(
        GoldenSetCase(
            case_id=str(item["id"]),
            query=str(item["query"]),
            relevant_chunk_ids=tuple(str(chunk_id) for chunk_id in item["relevant_chunk_ids"]),
        )
        for item in payload["queries"]
    )
    return GoldenSetDefinition(
        annotation_criterion=str(payload["annotation_criterion"]),
        top_k=int(payload.get("top_k", 5)),
        runs_per_query=int(payload.get("runs_per_query", 3)),
        cases=cases,
    )


def precision_at_k(retrieved_chunk_ids: list[str], relevant_chunk_ids: tuple[str, ...], k: int) -> float:
    top = retrieved_chunk_ids[:k]
    if not top:
        return 0.0
    relevant = set(relevant_chunk_ids)
    hits = sum(1 for chunk_id in top if chunk_id in relevant)
    return round(hits / len(top), 4)


def recall_at_k(retrieved_chunk_ids: list[str], relevant_chunk_ids: tuple[str, ...], k: int) -> float:
    relevant = set(relevant_chunk_ids)
    if not relevant:
        return 0.0
    hits = sum(1 for chunk_id in retrieved_chunk_ids[:k] if chunk_id in relevant)
    return round(hits / len(relevant), 4)


def semantic_ref_from_result(result: dict[str, Any]) -> str:
    metadata = result.get("metadata") or {}
    budget_id = metadata.get("budget_id")
    component_id = metadata.get("component_id")
    if isinstance(budget_id, str) and isinstance(component_id, str):
        return f"{budget_id}::{component_id}"
    chunk_id = result.get("chunk_id")
    return str(chunk_id) if chunk_id is not None else "n/a"


def summarize_variant_case(
    *,
    variant: RetrievalVariant,
    case: GoldenSetCase,
    responses: list[dict[str, Any]],
    top_k: int,
) -> VariantCaseObservation:
    first_response = responses[0]
    retrieved_chunk_ids = [
        semantic_ref_from_result(result) for result in first_response.get("results", [])[:top_k]
    ]
    latency_samples = [float(response.get("search_time_ms", 0.0)) for response in responses]
    return VariantCaseObservation(
        variant=variant.label,
        case_id=case.case_id,
        query=case.query,
        relevant_chunk_ids=case.relevant_chunk_ids,
        retrieved_chunk_ids=tuple(retrieved_chunk_ids),
        precision_at_k=precision_at_k(retrieved_chunk_ids, case.relevant_chunk_ids, top_k),
        recall_at_k=recall_at_k(retrieved_chunk_ids, case.relevant_chunk_ids, top_k),
        median_latency_ms=round(statistics.median(latency_samples), 2),
        top_ref=retrieved_chunk_ids[0] if retrieved_chunk_ids else "n/a",
    )


def summarize_variant(variant: RetrievalVariant, observations: list[VariantCaseObservation]) -> VariantSummary:
    relevant_items = [item for item in observations if item.variant == variant.label]
    return VariantSummary(
        variant=variant.label,
        mean_precision_at_k=round(
            statistics.mean(item.precision_at_k for item in relevant_items), 4
        ),
        mean_recall_at_k=round(statistics.mean(item.recall_at_k for item in relevant_items), 4),
        median_latency_ms=round(
            statistics.median(item.median_latency_ms for item in relevant_items), 2
        ),
    )


def render_report(
    *,
    base_url: str,
    model: str,
    golden_set_path: Path,
    golden_set: GoldenSetDefinition,
    observations: list[VariantCaseObservation],
    summaries: list[VariantSummary],
) -> str:
    baseline = summaries[0]
    summary_rows = [
        "| variant | mean precision@k | mean recall@k | median latency ms | delta precision vs baseline | delta latency ms |",
        "|---|---:|---:|---:|---:|---:|",
    ]
    for item in summaries:
        summary_rows.append(
            f"| {item.variant} | {item.mean_precision_at_k:.4f} | {item.mean_recall_at_k:.4f} | "
            f"{item.median_latency_ms:.2f} | "
            f"{item.mean_precision_at_k - baseline.mean_precision_at_k:+.4f} | "
            f"{item.median_latency_ms - baseline.median_latency_ms:+.2f} |"
        )

    detail_rows = [
        "| variant | case | top ref | precision@k | recall@k | median latency ms | relevant refs | retrieved refs |",
        "|---|---|---|---:|---:|---:|---|---|",
    ]
    for item in observations:
        detail_rows.append(
            f"| {item.variant} | {item.case_id} | {item.top_ref} | {item.precision_at_k:.4f} | "
            f"{item.recall_at_k:.4f} | {item.median_latency_ms:.2f} | "
            f"{', '.join(item.relevant_chunk_ids)} | {', '.join(item.retrieved_chunk_ids) or 'n/a'} |"
        )

    return "\n".join(
        [
            "# Session 10 Retrieval Evaluation",
            "",
            "## Lectura en 10 segundos",
            "",
            f"- Base URL: `{base_url}`",
            f"- Modelo: `{model}`",
            f"- Golden set: `{golden_set_path}`",
            f"- Criterio de anotacion: `{golden_set.annotation_criterion}`",
            f"- Casos: `{len(golden_set.cases)}`",
            f"- top_k medido: `{golden_set.top_k}`",
            f"- Repeticiones por query: `{golden_set.runs_per_query}`",
            "",
            "## Resumen por variante",
            "",
            "\n".join(summary_rows),
            "",
            "## Detalle por caso",
            "",
            "\n".join(detail_rows),
            "",
            "## Conclusiones",
            "",
            (
                "Este arnes artesanal busca responder una pregunta de arquitectura muy concreta: "
                "si una tecnica de retrieval mejora el top-k util lo suficiente como para justificar su latencia."
            ),
            "",
            (
                "El golden set vive versionado junto al codigo porque cambiar las consultas o el criterio de "
                "anotacion cambia la vara de medir. La comparacion solo es defendible si todas las variantes se "
                "miden contra la misma referencia."
            ),
            "",
        ]
    )


def fetch_search_response(
    *,
    client: httpx.Client,
    base_url: str,
    api_key: str,
    query: str,
    model: str,
    top_k: int,
    variant: RetrievalVariant,
) -> dict[str, Any]:
    headers = {"x-api-key": api_key} if api_key else {}
    payload = {
        "query": query,
        "k": top_k,
        "embedding_model": model,
        **variant.payload,
    }
    response = client.post(
        f"{base_url.rstrip('/')}/api/v1/retrieval/search",
        json=payload,
        headers=headers,
    )
    response.raise_for_status()
    return response.json()


def main() -> None:
    load_dotenv()
    args = parse_args()
    golden_set_path = Path(args.golden_set)
    golden_set = load_golden_set(golden_set_path)
    top_k = args.top_k or golden_set.top_k
    runs_per_query = args.runs_per_query or golden_set.runs_per_query

    effective_golden_set = GoldenSetDefinition(
        annotation_criterion=golden_set.annotation_criterion,
        top_k=top_k,
        runs_per_query=runs_per_query,
        cases=golden_set.cases,
    )

    observations: list[VariantCaseObservation] = []
    with httpx.Client(timeout=30.0) as client:
        for variant in DEFAULT_VARIANTS:
            for case in effective_golden_set.cases:
                responses = [
                    fetch_search_response(
                        client=client,
                        base_url=args.base_url,
                        api_key=args.api_key,
                        query=case.query,
                        model=args.model,
                        top_k=effective_golden_set.top_k,
                        variant=variant,
                    )
                    for _ in range(effective_golden_set.runs_per_query)
                ]
                observations.append(
                    summarize_variant_case(
                        variant=variant,
                        case=case,
                        responses=responses,
                        top_k=effective_golden_set.top_k,
                    )
                )

    summaries = [summarize_variant(variant, observations) for variant in DEFAULT_VARIANTS]
    report = render_report(
        base_url=args.base_url,
        model=args.model,
        golden_set_path=golden_set_path,
        golden_set=effective_golden_set,
        observations=observations,
        summaries=summaries,
    )
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(report)


if __name__ == "__main__":
    main()
