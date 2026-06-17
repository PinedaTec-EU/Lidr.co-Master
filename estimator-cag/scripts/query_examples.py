from __future__ import annotations

import argparse
from dataclasses import dataclass, field
from pathlib import Path
import sys
from typing import Any

import httpx
from dotenv import load_dotenv

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from app.embedding_pipeline.schemas import EmbeddingModelName


@dataclass(frozen=True)
class QueryExample:
    label: str
    query: str


DEFAULT_QUERY_EXAMPLES = [
    QueryExample(
        label="direct-match",
        query="REST API development with JWT authentication for financial sector",
    ),
    QueryExample(
        label="semantic-rephrase",
        query="secure backend service with token-based access control for banking applications",
    ),
    QueryExample(
        label="out-of-domain",
        query="mobile application for restaurant reservations",
    ),
    QueryExample(
        label="ambiguous",
        query="integration with external system",
    ),
    QueryExample(
        label="very-specific",
        query="migration from monolith to microservices architecture using Kubernetes",
    ),
]


@dataclass(frozen=True)
class SearchHit:
    chunk_id: int
    distance: float
    chunk_type: str
    content: str
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def semantic_ref(self) -> str:
        budget_id = self.metadata.get("budget_id")
        component_id = self.metadata.get("component_id")
        if isinstance(budget_id, str) and isinstance(component_id, str):
            return f"{budget_id}::{component_id}"
        return str(self.chunk_id)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run representative semantic-search queries.")
    parser.add_argument(
        "--base-url",
        default="http://localhost:8000",
        help="Base URL where estimator-cag API is running.",
    )
    parser.add_argument(
        "--k",
        type=int,
        default=5,
        help="Number of search results to request per query.",
    )
    parser.add_argument(
        "--model",
        default=EmbeddingModelName.TEXT_EMBEDDING_3_SMALL.value,
        choices=[model.value for model in EmbeddingModelName],
        help="Embedding model used to embed the query.",
    )
    return parser.parse_args()


def shorten(text: str, limit: int = 120) -> str:
    normalized = " ".join(text.split())
    if len(normalized) <= limit:
        return normalized
    return normalized[: limit - 3].rstrip() + "..."


def format_hits(hits: list[SearchHit]) -> list[str]:
    lines: list[str] = []
    for index, hit in enumerate(hits, start=1):
        lines.append(
            f"  {index}. chunk_id={hit.chunk_id} | ref={hit.semantic_ref} | distance={hit.distance:.4f} | "
            f"chunk_type={hit.chunk_type}"
        )
        lines.append(f"     {shorten(hit.content)}")
    return lines


def fetch_results(
    *,
    client: httpx.Client,
    base_url: str,
    query: str,
    k: int,
    model: str,
) -> list[SearchHit]:
    response = client.post(
        f"{base_url.rstrip('/')}/api/v1/search",
        json={
            "query": query,
            "k": k,
            "embedding_model": model,
        },
        timeout=30.0,
    )
    response.raise_for_status()
    payload = response.json()
    return [
        SearchHit(
            chunk_id=item["chunk_id"],
            distance=item["distance"],
            chunk_type=item["chunk_type"],
            content=item["content"],
            metadata=item.get("metadata", {}),
        )
        for item in payload["results"]
    ]


def render_report(
    *,
    base_url: str,
    k: int,
    model: str,
    results_by_query: list[tuple[str, str, list[SearchHit]]],
) -> str:
    lines = [
        "Session 8 semantic search examples",
        f"Base URL: {base_url}",
        f"Model: {model}",
        f"Top K: {k}",
        "",
    ]
    for label, query, hits in results_by_query:
        lines.append(f"## {label}")
        lines.append(f"Query: {query}")
        if not hits:
            lines.append("  No results returned.")
        else:
            lines.extend(format_hits(hits))
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def main() -> None:
    load_dotenv()
    args = parse_args()

    try:
        model = EmbeddingModelName(args.model).value
    except ValueError as exc:
        raise SystemExit(str(exc)) from exc

    with httpx.Client() as client:
        try:
            results_by_query = [
                (
                    example.label,
                    example.query,
                    fetch_results(
                        client=client,
                        base_url=args.base_url,
                        query=example.query,
                        k=args.k,
                        model=model,
                    ),
                )
                for example in DEFAULT_QUERY_EXAMPLES
            ]
        except httpx.HTTPError as exc:
            raise SystemExit(f"Search request failed: {exc}") from exc

    sys.stdout.write(
        render_report(
            base_url=args.base_url,
            k=args.k,
            model=model,
            results_by_query=results_by_query,
        )
    )


if __name__ == "__main__":
    main()
