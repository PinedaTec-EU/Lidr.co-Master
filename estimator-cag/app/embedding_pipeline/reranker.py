from __future__ import annotations

import math
import re
from dataclasses import dataclass


_TOKEN_PATTERN = re.compile(r"\w+", flags=re.UNICODE)


@dataclass(frozen=True)
class RerankedCandidate:
    chunk_id: int
    rerank_score: float


def rerank_candidates(
    *,
    query: str,
    candidates: list[dict[str, object]],
    alpha: float,
) -> dict[int, float]:
    query_terms = _tokenize(query)
    normalized_query = " ".join(query.lower().split())
    if not query_terms:
        return {
            int(candidate["chunk_id"]): _clamp_score(float(candidate.get("semantic_score") or 0.0))
            for candidate in candidates
        }

    reranked: dict[int, float] = {}
    for candidate in candidates:
        chunk_id = int(candidate["chunk_id"])
        semantic_score = _clamp_score(float(candidate.get("semantic_score") or 0.0))
        content = str(candidate.get("content") or "")
        lexical_score = _lexical_overlap_score(
            query_terms=query_terms,
            normalized_query=normalized_query,
            content=content,
        )
        reranked[chunk_id] = round((alpha * semantic_score) + ((1 - alpha) * lexical_score), 6)
    return reranked


def _lexical_overlap_score(*, query_terms: set[str], normalized_query: str, content: str) -> float:
    content_terms = _tokenize(content)
    if not content_terms:
        return 0.0

    overlap = len(query_terms & content_terms) / len(query_terms)
    precision = len(query_terms & content_terms) / len(content_terms)
    harmonic = 0.0
    if overlap > 0 and precision > 0:
        harmonic = (2 * overlap * precision) / (overlap + precision)

    phrase_bonus = 0.0
    normalized_content = " ".join(content.lower().split())
    if len(query_terms) >= 2 and normalized_query and normalized_query in normalized_content:
        phrase_bonus = 0.05

    return _clamp_score(harmonic + phrase_bonus)


def _tokenize(value: str) -> set[str]:
    return {token.lower() for token in _TOKEN_PATTERN.findall(value) if len(token) >= 3}


def _clamp_score(value: float) -> float:
    return max(0.0, min(1.0, value))
