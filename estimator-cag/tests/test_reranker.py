from __future__ import annotations

from app.embedding_pipeline.reranker import rerank_candidates


def test_reranker_boosts_joint_query_document_overlap() -> None:
    scores = rerank_candidates(
        query="oauth authentication banking",
        alpha=0.7,
        candidates=[
            {
                "chunk_id": 1,
                "semantic_score": 0.82,
                "content": "Generic backend workflows and reporting exports.",
            },
            {
                "chunk_id": 2,
                "semantic_score": 0.79,
                "content": "OAuth authentication backend for banking applications and audit flows.",
            },
        ],
    )

    assert scores[2] > scores[1]


def test_reranker_preserves_semantic_score_when_query_is_empty_after_cleanup() -> None:
    scores = rerank_candidates(
        query="  ",
        alpha=0.7,
        candidates=[
            {"chunk_id": 1, "semantic_score": 0.62, "content": "Anything"},
        ],
    )

    assert scores[1] == 0.62
