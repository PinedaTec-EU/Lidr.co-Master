from __future__ import annotations


def interleave_rankings(rankings: list[list[int]], *, top_k: int) -> list[int]:
    merged: list[int] = []
    seen: set[int] = set()
    max_length = max((len(ranking) for ranking in rankings), default=0)

    for position in range(max_length):
        for ranking in rankings:
            if position >= len(ranking):
                continue
            chunk_id = ranking[position]
            if chunk_id in seen:
                continue
            merged.append(chunk_id)
            seen.add(chunk_id)
            if len(merged) == top_k:
                return merged
    return merged
