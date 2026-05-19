from __future__ import annotations

import inspect
import json
from typing import Any

import httpx
from fastapi import UploadFile

from app.config import settings


SUPPORTED_ATTACHMENT_EXTENSIONS = {
    ".pdf",
    ".docx",
    ".pptx",
    ".html",
    ".htm",
    ".png",
    ".jpg",
    ".jpeg",
    ".tiff",
    ".bmp",
    ".txt",
    ".md",
}


async def extract_attachments_text(attachments: list[UploadFile] | None) -> list[str]:
    if not attachments:
        return []

    extracted_sections: list[str] = []
    for attachment in attachments:
        filename = getattr(attachment, "filename", None) or getattr(attachment, "name", None) or "attachment"
        read_fn = getattr(attachment, "read")
        read_result = read_fn()
        content = await read_result if inspect.isawaitable(read_result) else read_result
        text = await _extract_text_from_bytes(filename, content, getattr(attachment, "content_type", None))
        if text.strip():
            extracted_sections.append(f"--- attachment: {filename} ---\n{text.strip()}")
    return extracted_sections


async def _extract_text_from_bytes(filename: str, content: bytes, content_type: str | None) -> str:
    lower_name = filename.lower()
    if lower_name.endswith(".txt") or lower_name.endswith(".md"):
        return content.decode("utf-8", errors="ignore").strip()

    if not is_supported_attachment(filename):
        raise ValueError(f"Unsupported attachment type for '{filename}'")

    return await _convert_with_docling(filename, content, content_type)


async def _convert_with_docling(filename: str, content: bytes, content_type: str | None) -> str:
    endpoint = f"{settings.docling_serve_url.rstrip('/')}/v1/convert/file"
    files = {"files": (filename, content, content_type or "application/octet-stream")}
    data = {
        "to_formats": "md",
        "do_ocr": "false",
    }

    async with httpx.AsyncClient(timeout=settings.docling_timeout_seconds) as client:
        response = await client.post(endpoint, files=files, data=data)

    if response.status_code >= 400:
        raise ValueError(
            f"Docling conversion failed for '{filename}' with status {response.status_code}: {response.text}"
        )

    return _extract_markdown_from_docling_response(response.json())


def _extract_markdown_from_docling_response(payload: dict[str, Any]) -> str:
    document = payload.get("document")
    if not isinstance(document, dict):
        raise ValueError("Docling response did not include a valid 'document' object")

    for key in ("md_content", "markdown", "text", "text_content"):
        value = document.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()

    outputs = document.get("outputs")
    if isinstance(outputs, dict):
        markdown = outputs.get("markdown")
        if isinstance(markdown, str) and markdown.strip():
            return markdown.strip()

    raise ValueError(
        "Docling response did not include Markdown/text content: "
        + json.dumps({"keys": sorted(document.keys())}, ensure_ascii=True)
    )


def is_supported_attachment(filename: str) -> bool:
    lower_name = filename.lower()
    return any(lower_name.endswith(extension) for extension in SUPPORTED_ATTACHMENT_EXTENSIONS)


def supported_attachment_extensions() -> list[str]:
    return sorted(SUPPORTED_ATTACHMENT_EXTENSIONS)
