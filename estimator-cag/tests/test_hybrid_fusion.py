from __future__ import annotations

from app.embedding_pipeline.hybrid_fusion import reciprocal_rank_fusion


def test_reciprocal_rank_fusion_rewards_consensus() -> None:
    scores = reciprocal_rank_fusion(
        [
            [10, 20, 30],
            [20, 30, 10],
        ],
        smoothing_k=60,
    )

    assert scores[20] > scores[10]
    assert scores[10] > scores[30]


def test_reciprocal_rank_fusion_keeps_single_list_when_no_overlap() -> None:
    scores = reciprocal_rank_fusion([[101, 102, 103]], smoothing_k=60)

    assert scores[101] > scores[102] > scores[103]
