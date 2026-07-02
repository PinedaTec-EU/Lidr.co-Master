from __future__ import annotations

from app.embedding_pipeline.schemas import SearchTarget
from app.embedding_pipeline.search_routing import route_search_targets


def test_route_search_targets_defaults_estimation_queries_to_budgets() -> None:
    decision = route_search_targets(
        query="How many hours did the SAP integration cost in previous projects?",
        explicit_targets=None,
    )

    assert decision.targets == [SearchTarget.BUDGETS]


def test_route_search_targets_respects_explicit_collections() -> None:
    decision = route_search_targets(
        query="architecture notes about SAP connectors",
        explicit_targets=[SearchTarget.TECHNICAL_DOCS, SearchTarget.TRANSCRIPTS],
    )

    assert decision.targets == [SearchTarget.TECHNICAL_DOCS, SearchTarget.TRANSCRIPTS]
    assert decision.reason == "caller provided explicit target collections"
