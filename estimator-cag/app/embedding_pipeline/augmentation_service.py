from __future__ import annotations

from app.embedding_pipeline.schemas import (
    ContextAssemblyItem,
    ContextAssemblyRequest,
    ContextAssemblyResponse,
    SearchResponse,
    SearchResult,
)
from app.embedding_pipeline.search_service import SemanticSearchService
from sqlalchemy.ext.asyncio import AsyncSession


class RetrievalAugmentationService:
    def __init__(self, search_service: SemanticSearchService | None = None) -> None:
        self.search_service = search_service or SemanticSearchService()

    async def assemble_context(
        self,
        *,
        session: AsyncSession,
        request: ContextAssemblyRequest,
    ) -> ContextAssemblyResponse:
        search_response = await self.search_service.search(session=session, request=request)
        included_chunks, context_text, truncated = _assemble_context(
            search_response=search_response,
            max_chunks=request.max_chunks,
            max_context_chars=request.max_context_chars,
            include_scores=request.include_scores,
        )
        return ContextAssemblyResponse(
            search=search_response,
            context_text=context_text,
            included_chunks=included_chunks,
            truncated=truncated,
        )


def _assemble_context(
    *,
    search_response: SearchResponse,
    max_chunks: int,
    max_context_chars: int,
    include_scores: bool,
) -> tuple[list[ContextAssemblyItem], str, bool]:
    sections: list[str] = []
    included_chunks: list[ContextAssemblyItem] = []
    consumed_chars = 0
    truncated = False

    for result in search_response.results[:max_chunks]:
        excerpt = _compact_excerpt(result.content, limit=420)
        header = _render_header(result, include_scores=include_scores)
        section = f"{header}\n{excerpt}\n</source>"

        projected = consumed_chars + len(section) + (2 if sections else 0)
        if sections and projected > max_context_chars:
            truncated = True
            break
        if not sections and len(section) > max_context_chars:
            section = section[: max_context_chars - 3].rstrip() + "..."
            excerpt = section.split("\n", 1)[1] if "\n" in section else section
            truncated = True

        sections.append(section)
        consumed_chars += len(section) + (2 if len(sections) > 1 else 0)
        included_chunks.append(
            ContextAssemblyItem(
                chunk_id=result.chunk_id,
                document_id=result.document_id,
                chunk_type=result.chunk_type,
                score=result.score,
                metadata=result.metadata,
                excerpt=excerpt,
            )
        )

    return included_chunks, "\n\n".join(sections), truncated


def _render_header(result: SearchResult, *, include_scores: bool) -> str:
    metadata = result.metadata or {}
    budget_id = metadata.get("budget_id", "n/a")
    component_id = metadata.get("component_id", "n/a")
    technology = metadata.get("main_technology", "n/a")
    sector = metadata.get("client_sector", "n/a")
    year = metadata.get("year", "n/a")
    chunk_type = result.chunk_type or "n/a"
    distance = f"{result.distance:.3f}"
    score_part = f' score="{result.score:.3f}"' if include_scores else ""
    return (
        f'<source id="{result.chunk_id}" budget_id="{budget_id}" component_id="{component_id}" '
        f'sector="{sector}" project_year="{year}" chunk_type="{chunk_type}" '
        f'tech="{technology}" distance="{distance}"{score_part}>'
    )


def _compact_excerpt(text: str, *, limit: int) -> str:
    normalized = " ".join(text.split())
    if len(normalized) <= limit:
        return normalized
    return normalized[: limit - 3].rstrip() + "..."
