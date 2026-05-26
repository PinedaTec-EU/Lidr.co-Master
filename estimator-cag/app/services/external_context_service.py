from __future__ import annotations

from app.config import settings
from app.services.notion_context_provider import fetch_page_context, search_pages
from app.sessions import ExternalContextItem, ProjectMetadata, Session


def infer_notion_search_terms(
    *,
    transcript: str,
    project_metadata: ProjectMetadata,
    explicit_terms: list[str],
) -> list[str]:
    terms: list[str] = []
    seen = set()

    def add_term(value: str | None) -> None:
        if not value:
            return
        normalized = value.strip()
        key = normalized.lower()
        if not normalized or key in seen:
            return
        seen.add(key)
        terms.append(normalized)

    for item in explicit_terms:
        add_term(item)

    add_term(project_metadata.project_name)
    add_term(project_metadata.client_name)

    if project_metadata.client_name and project_metadata.project_name:
        add_term(f"{project_metadata.client_name} {project_metadata.project_name}")

    lower_transcript = transcript.lower()
    if any(keyword in lower_transcript for keyword in ("roadmap", "kickoff", "requirements", "discovery", "alcance")):
        add_term(project_metadata.project_name)

    return terms


async def resolve_external_context(
    *,
    session: Session,
    transcript: str,
) -> list[ExternalContextItem]:
    if not settings.notion_api_key:
        return []

    items: list[ExternalContextItem] = []

    for page_id in session.external_context_config.notion_page_ids[: settings.notion_max_items]:
        items.append(
            await fetch_page_context(
                page_id,
                relevance_reason="Explicit notion_page_id configured in the session.",
            )
        )

    if items:
        return items

    search_terms = infer_notion_search_terms(
        transcript=transcript,
        project_metadata=session.project_metadata,
        explicit_terms=session.external_context_config.notion_search_terms,
    )
    if not search_terms:
        return []

    candidates_by_page: dict[str, dict[str, str]] = {}
    for term in search_terms:
        for candidate in await search_pages(term, limit=settings.notion_max_items):
            page_id = candidate.get("page_id")
            if page_id and page_id not in candidates_by_page:
                candidates_by_page[page_id] = candidate

    for candidate in list(candidates_by_page.values())[: settings.notion_max_items]:
        items.append(
            await fetch_page_context(
                candidate["page_id"],
                relevance_reason=f"Matched inferred Notion search term for '{candidate['title']}'.",
            )
        )
    return items
