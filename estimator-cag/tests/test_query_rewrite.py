from __future__ import annotations

from app.embedding_pipeline.query_rewrite import rewrite_query
from app.embedding_pipeline.schemas import QueryRewriteStrategy


def test_rewrite_query_leaves_original_query_when_disabled() -> None:
    result = rewrite_query(
        query="Please find OAuth authentication for banking",
        strategy=QueryRewriteStrategy.DISABLED,
    )

    assert result.effective_query == "Please find OAuth authentication for banking"
    assert result.notes == []


def test_rewrite_query_normalize_removes_conversational_prefix_and_whitespace() -> None:
    result = rewrite_query(
        query="  por favor\nbuscar   OAuth authentication for banking   ",
        strategy=QueryRewriteStrategy.NORMALIZE,
    )

    assert result.effective_query == "OAuth authentication for banking"
    assert "removed conversational prefix" in result.notes

