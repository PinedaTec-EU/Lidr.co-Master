from __future__ import annotations

import re
from dataclasses import dataclass

from app.embedding_pipeline.schemas import QueryFusionStrategy, QueryRewriteStrategy

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
    effective_queries: list[str]
    fusion_strategy: QueryFusionStrategy | None
    notes: list[str]


def rewrite_query(*, query: str, strategy: QueryRewriteStrategy) -> QueryRewriteResult:
    normalized = query.strip()
    if strategy == QueryRewriteStrategy.DISABLED:
        return QueryRewriteResult(
            effective_query=normalized,
            effective_queries=[normalized],
            fusion_strategy=None,
            notes=[],
        )

    notes: list[str] = []
    rewritten = _normalize_query(normalized, notes)

    if strategy == QueryRewriteStrategy.NORMALIZE:
        return QueryRewriteResult(
            effective_query=rewritten,
            effective_queries=[rewritten],
            fusion_strategy=None,
            notes=notes,
        )

    if strategy == QueryRewriteStrategy.EXPAND:
        variants = _expand_query(rewritten)
        if len(variants) > 1:
            notes.append(f"generated {len(variants)} query variants")
        return QueryRewriteResult(
            effective_query=variants[0],
            effective_queries=variants,
            fusion_strategy=QueryFusionStrategy.CONSENSUS,
            notes=notes,
        )

    sub_queries = _decompose_query(rewritten)
    if len(sub_queries) > 1:
        notes.append(f"decomposed query into {len(sub_queries)} sub-queries")
    return QueryRewriteResult(
        effective_query=sub_queries[0],
        effective_queries=sub_queries,
        fusion_strategy=QueryFusionStrategy.COVERAGE if len(sub_queries) > 1 else None,
        notes=notes,
    )


def _normalize_query(query: str, notes: list[str]) -> str:
    rewritten = _PUNCTUATION_PATTERN.sub(" ", query)
    if rewritten != query:
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
    return compact or query


def _expand_query(query: str) -> list[str]:
    variants = [query]

    keyword_variant = " ".join(_extract_keywords(query))
    if keyword_variant and keyword_variant != query:
        variants.append(keyword_variant)

    synonym_variant = keyword_variant or query
    for source, target in (
        ("mobile", "smartphone responsive"),
        ("dashboard", "kpi reporting"),
        ("billing", "invoicing"),
        ("catalog", "product inventory pricing"),
        ("authentication", "oauth jwt access control"),
    ):
        if source in synonym_variant.lower() and target not in synonym_variant.lower():
            synonym_variant = f"{synonym_variant} {target}".strip()
    if synonym_variant not in variants:
        variants.append(synonym_variant)

    return variants[:4]


def _decompose_query(query: str) -> list[str]:
    parts = re.split(
        r"\s*(?:,|;|\band\b|\by\b|\bplus\b|\badem[aá]s\b|\bincluding\b)\s*",
        query,
        flags=re.IGNORECASE,
    )
    cleaned: list[str] = []
    for part in parts:
        candidate = _SPACE_PATTERN.sub(" ", part).strip(" .,;:-")
        if len(candidate) >= 4 and candidate not in cleaned:
            cleaned.append(candidate)
    return cleaned[:4] or [query]


def _extract_keywords(query: str) -> list[str]:
    stopwords = {
        "the",
        "a",
        "an",
        "for",
        "with",
        "and",
        "or",
        "de",
        "la",
        "el",
        "los",
        "las",
        "con",
        "para",
        "por",
        "del",
    }
    keywords: list[str] = []
    seen: set[str] = set()
    for token in re.findall(r"[A-Za-z0-9_+-]+", query):
        lowered = token.lower()
        if lowered in stopwords or lowered in seen:
            continue
        keywords.append(token)
        seen.add(lowered)
    return keywords
