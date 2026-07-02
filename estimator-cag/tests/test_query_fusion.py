from __future__ import annotations

from app.embedding_pipeline.query_fusion import interleave_rankings


def test_interleave_rankings_preserves_topic_coverage() -> None:
    merged = interleave_rankings(
        [
            [10, 11, 12],
            [20, 21, 22],
            [10, 30, 31],
        ],
        top_k=5,
    )

    assert merged == [10, 20, 11, 21, 30]
