from __future__ import annotations

from typing import Any

import httpx

from app.config import settings
from app.errors import UpstreamBadResponseError, UpstreamTimeoutError
from app.sessions import ExternalContextItem


def _headers() -> dict[str, str]:
    if not settings.notion_api_key:
        raise RuntimeError("NOTION_API_KEY is not configured")

    return {
        "Authorization": f"Bearer {settings.notion_api_key}",
        "Notion-Version": settings.notion_api_version,
        "Content-Type": "application/json",
    }


def _plain_rich_text(items: list[dict[str, Any]]) -> str:
    return "".join(item.get("plain_text", "") for item in items)


def _extract_page_title(payload: dict[str, Any]) -> str:
    properties = payload.get("properties", {})
    for value in properties.values():
        if value.get("type") == "title":
            title = _plain_rich_text(value.get("title", []))
            if title:
                return title
    return payload.get("id", "Untitled")


def _block_text(block: dict[str, Any]) -> str:
    block_type = block.get("type", "")
    block_payload = block.get(block_type, {})
    rich_text = block_payload.get("rich_text", [])
    text = _plain_rich_text(rich_text).strip()
    if not text:
        return ""

    prefixes = {
        "bulleted_list_item": "- ",
        "numbered_list_item": "1. ",
        "to_do": "- [ ] ",
        "heading_1": "# ",
        "heading_2": "## ",
        "heading_3": "### ",
        "quote": "> ",
        "callout": "> ",
    }
    return f"{prefixes.get(block_type, '')}{text}".strip()


async def _fetch_page_payload(page_id: str) -> dict[str, Any]:
    try:
        async with httpx.AsyncClient(timeout=settings.notion_timeout_seconds) as client:
            response = await client.get(
                f"{settings.notion_api_base_url}/pages/{page_id}",
                headers=_headers(),
            )
            response.raise_for_status()
    except httpx.TimeoutException as exc:
        raise UpstreamTimeoutError(f"Notion page fetch timed out for '{page_id}'") from exc
    except httpx.HTTPError as exc:
        raise UpstreamBadResponseError(f"Notion page fetch failed for '{page_id}'") from exc

    try:
        return response.json()
    except ValueError as exc:
        raise UpstreamBadResponseError(f"Notion page payload was not valid JSON for '{page_id}'") from exc


async def _fetch_block_children(block_id: str) -> list[dict[str, Any]]:
    try:
        async with httpx.AsyncClient(timeout=settings.notion_timeout_seconds) as client:
            response = await client.get(
                f"{settings.notion_api_base_url}/blocks/{block_id}/children?page_size=100",
                headers=_headers(),
            )
            response.raise_for_status()
    except httpx.TimeoutException as exc:
        raise UpstreamTimeoutError(f"Notion block fetch timed out for '{block_id}'") from exc
    except httpx.HTTPError as exc:
        raise UpstreamBadResponseError(f"Notion block fetch failed for '{block_id}'") from exc

    try:
        payload = response.json()
    except ValueError as exc:
        raise UpstreamBadResponseError(f"Notion block payload was not valid JSON for '{block_id}'") from exc
    return payload.get("results", [])


async def fetch_page_context(page_id: str, relevance_reason: str) -> ExternalContextItem:
    page_payload = await _fetch_page_payload(page_id)
    title = _extract_page_title(page_payload)
    blocks = await _fetch_block_children(page_id)
    lines = [line for line in (_block_text(block) for block in blocks) if line]
    content = "\n".join(lines).strip() or f"Página de Notion sin bloques de texto legibles: {title}"

    return ExternalContextItem(
        source="notion",
        title=title,
        content=content[:4000],
        url=page_payload.get("url"),
        updated_at=page_payload.get("last_edited_time"),
        relevance_reason=relevance_reason,
    )


async def search_pages(query: str, limit: int | None = None) -> list[dict[str, str]]:
    try:
        async with httpx.AsyncClient(timeout=settings.notion_timeout_seconds) as client:
            response = await client.post(
                f"{settings.notion_api_base_url}/search",
                headers=_headers(),
                json={
                    "query": query,
                    "filter": {"property": "object", "value": "page"},
                    "page_size": limit or settings.notion_max_items,
                },
            )
            response.raise_for_status()
    except httpx.TimeoutException as exc:
        raise UpstreamTimeoutError(f"Notion search timed out for query '{query}'") from exc
    except httpx.HTTPError as exc:
        raise UpstreamBadResponseError(f"Notion search failed for query '{query}'") from exc

    try:
        payload = response.json()
    except ValueError as exc:
        raise UpstreamBadResponseError(f"Notion search payload was not valid JSON for query '{query}'") from exc

    results: list[dict[str, str]] = []
    for item in payload.get("results", []):
        results.append(
            {
                "page_id": item.get("id", ""),
                "title": _extract_page_title(item),
                "url": item.get("url", ""),
                "updated_at": item.get("last_edited_time", ""),
            }
        )
    return results
