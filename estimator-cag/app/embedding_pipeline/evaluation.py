from __future__ import annotations

from math import log2

from app.embedding_pipeline.schemas import RetrievalEvalCaseResult


def recall_at_k(retrieved_chunk_ids: list[str], relevant_chunk_ids: list[str], k: int) -> float:
    relevant = set(relevant_chunk_ids)
    if not relevant:
        return 0.0
    hits = sum(1 for chunk_id in retrieved_chunk_ids[:k] if chunk_id in relevant)
    return round(hits / len(relevant), 4)


def ndcg_at_k(retrieved_chunk_ids: list[str], relevant_chunk_ids: list[str], k: int) -> float:
    relevant = set(relevant_chunk_ids)
    dcg = 0.0
    for index, chunk_id in enumerate(retrieved_chunk_ids[:k], start=1):
        if chunk_id in relevant:
            dcg += 1 / log2(index + 1)

    ideal_hits = min(len(relevant), k)
    ideal_dcg = sum(1 / log2(index + 1) for index in range(1, ideal_hits + 1))
    if ideal_dcg == 0:
        return 0.0
    return round(dcg / ideal_dcg, 4)


def summarize_case(query: str, relevant_chunk_ids: list[str], retrieved_chunk_ids: list[str], k: int) -> RetrievalEvalCaseResult:
    return RetrievalEvalCaseResult(
        query=query,
        relevant_chunk_ids=relevant_chunk_ids,
        retrieved_chunk_ids=retrieved_chunk_ids[:k],
        recall_at_k=recall_at_k(retrieved_chunk_ids, relevant_chunk_ids, k),
        ndcg_at_k=ndcg_at_k(retrieved_chunk_ids, relevant_chunk_ids, k),
    )
