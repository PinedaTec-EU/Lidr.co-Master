from __future__ import annotations

import re
from dataclasses import dataclass

from app.embedding_pipeline.schemas import QueryRewriteStrategy

_LEADING_PATTERNS = (
    re.compile(r"^\s*(please|por favor)\s+", re.IGNORECASE),
    re.compile(r"^\s*(i need|need|find|search for|show me)\s+", re.IGNORECASE),
    re.compile(r"^\s*(necesito|busca|buscar|mu[eé]strame|ens[eé][ñn]ame)\s+", re.IGNORECASE),
    re.compile(r"^\s*(presupuesto de|proyecto de)\s+", re.IGNORECASE),
)
_PUNCTUATION_PATTERN = re.compile(r"[\t\r\n]+")
_SPACE_PATTERN = re.compile(r"\s+")


@dataclass(frozen=True)
class QueryRewriteResult:
    effective_query: str
    notes: list[str]


def rewrite_query(*, query: str, strategy: QueryRewriteStrategy) -> QueryRewriteResult:
    normalized = query.strip()
    if strategy is QueryRewriteStrategy.DISABLED:
        return QueryRewriteResult(effective_query=normalized, notes=[])

    notes: list[str] = []
    rewritten = _PUNCTUATION_PATTERN.sub(" ", normalized)
    if rewritten != normalized:
        notes.append("collapsed line breaks and tabs")

    removed_prefix = False
    while True:
        previous = rewritten
        for pattern in _LEADING_PATTERNS:
            updated = pattern.sub("", rewritten)
            if updated != rewritten:
                rewritten = updated
                removed_prefix = True
                break
        if rewritten == previous:
            break

    if removed_prefix:
        notes.append("removed conversational prefix")

    compact = _SPACE_PATTERN.sub(" ", rewritten).strip(" .,;:-")
    if compact != rewritten:
        notes.append("normalized whitespace and edge punctuation")

    return QueryRewriteResult(
        effective_query=compact or normalized,
        notes=notes,
    )
