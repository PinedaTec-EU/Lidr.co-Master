from __future__ import annotations

from app.embedding_pipeline.query_rewrite import rewrite_query
from app.embedding_pipeline.schemas import QueryFusionStrategy, QueryRewriteStrategy


def test_rewrite_query_leaves_original_query_when_disabled() -> None:
    result = rewrite_query(
        query="Please find OAuth authentication for banking",
        strategy=QueryRewriteStrategy.DISABLED,
    )

    assert result.effective_query == "Please find OAuth authentication for banking"
    assert result.effective_queries == ["Please find OAuth authentication for banking"]
    assert result.notes == []


def test_rewrite_query_normalize_removes_conversational_prefix_and_whitespace() -> None:
    result = rewrite_query(
        query=" por favor\nbuscar OAuth authentication for banking ",
        strategy=QueryRewriteStrategy.NORMALIZE,
    )

    assert result.effective_query == "OAuth authentication for banking"
    assert "removed conversational prefix" in result.notes


def test_rewrite_query_expand_generates_keyword_variants() -> None:
    result = rewrite_query(
        query="mobile dashboard billing",
        strategy=QueryRewriteStrategy.EXPAND,
    )

    assert len(result.effective_queries) >= 2
    assert result.fusion_strategy == QueryFusionStrategy.CONSENSUS
    assert "generated" in " ".join(result.notes)


def test_rewrite_query_decompose_splits_multi_topic_queries() -> None:
    result = rewrite_query(
        query="catalog and billing integration, admin reporting",
        strategy=QueryRewriteStrategy.DECOMPOSE,
    )

    assert result.effective_queries == [
        "catalog",
        "billing integration",
        "admin reporting",
    ]
    assert result.fusion_strategy == QueryFusionStrategy.COVERAGE
