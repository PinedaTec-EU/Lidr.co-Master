from __future__ import annotations

from collections import defaultdict

RRF_SMOOTHING_K = 60


def reciprocal_rank_fusion(
    rankings: list[list[int]],
    *,
    smoothing_k: int = RRF_SMOOTHING_K,
) -> dict[int, float]:
    scores: dict[int, float] = defaultdict(float)
    for ranking in rankings:
        for rank, chunk_id in enumerate(ranking, start=1):
            scores[chunk_id] += 1.0 / (smoothing_k + rank)
    return dict(scores)
