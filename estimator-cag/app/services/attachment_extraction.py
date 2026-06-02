from __future__ import annotations

import inspect
import json
from typing import Any
from pathlib import Path

import httpx
from fastapi import UploadFile
from pydantic import BaseModel

from app.config import settings
from app.errors import BadRequestError, UpstreamBadResponseError, UpstreamTimeoutError


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


class DoclingOutputs(BaseModel):
    markdown: str | None = None


class DoclingDocument(BaseModel):
    md_content: str | None = None
    markdown: str | None = None
    text: str | None = None
    text_content: str | None = None
    outputs: DoclingOutputs | None = None

    def markdown_content(self) -> str:
        for value in (self.md_content, self.markdown, self.text, self.text_content):
            if value and value.strip():
                return value.strip()

        if self.outputs and self.outputs.markdown and self.outputs.markdown.strip():
            return self.outputs.markdown.strip()

        raise UpstreamBadResponseError(
            "Docling response did not include Markdown/text content"
        )


class DoclingResponse(BaseModel):
    document: DoclingDocument


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


async def extract_document_paths_text(document_paths: list[str] | None) -> list[str]:
    if not document_paths:
        return []

    extracted_sections: list[str] = []
    for raw_path in document_paths:
        path = Path(raw_path).expanduser().resolve()
        if not path.exists() or not path.is_file():
            raise BadRequestError(f"Document path does not exist or is not a file: {raw_path}")
        content = path.read_bytes()
        text = await _extract_text_from_bytes(path.name, content, None)
        if text.strip():
            extracted_sections.append(f"--- document_path: {path} ---\n{text.strip()}")
    return extracted_sections


async def _extract_text_from_bytes(filename: str, content: bytes, content_type: str | None) -> str:
    lower_name = filename.lower()
    if lower_name.endswith(".txt") or lower_name.endswith(".md"):
        return content.decode("utf-8", errors="ignore").strip()

    if not is_supported_attachment(filename):
        raise BadRequestError(f"Unsupported attachment type for '{filename}'")

    return await _convert_with_docling(filename, content, content_type)


async def _convert_with_docling(filename: str, content: bytes, content_type: str | None) -> str:
    endpoint = f"{settings.docling_serve_url.rstrip('/')}/v1/convert/file"
    files = {"files": (filename, content, content_type or "application/octet-stream")}
    data = {
        "to_formats": "md",
        "do_ocr": "false",
    }

    try:
        async with httpx.AsyncClient(timeout=settings.docling_timeout_seconds) as client:
            response = await client.post(endpoint, files=files, data=data)
    except httpx.TimeoutException as exc:
        raise UpstreamTimeoutError(
            f"Docling conversion timed out for '{filename}'"
        ) from exc

    if response.status_code >= 400:
        raise UpstreamBadResponseError(
            f"Docling conversion failed for '{filename}' with status {response.status_code}: {response.text}"
        )

    try:
        payload = response.json()
    except ValueError as exc:
        raise UpstreamBadResponseError(
            f"Docling returned invalid JSON for '{filename}'"
        ) from exc

    return _extract_markdown_from_docling_response(payload)


def _extract_markdown_from_docling_response(payload: dict[str, Any]) -> str:
    try:
        document = DoclingResponse.model_validate(payload).document
    except Exception as exc:
        raw_document = payload.get("document")
        details = json.dumps(
            {
                "has_document": isinstance(raw_document, dict),
                "document_keys": sorted(raw_document.keys()) if isinstance(raw_document, dict) else [],
            },
            ensure_ascii=True,
        )
        raise UpstreamBadResponseError(
            "Docling response did not include a valid 'document' object: " + details
        ) from exc

    try:
        return document.markdown_content()
    except UpstreamBadResponseError as exc:
        details = json.dumps(payload.get("document", {}), ensure_ascii=True, default=str)
        raise UpstreamBadResponseError(f"{exc.message}: {details}") from exc


def is_supported_attachment(filename: str) -> bool:
    lower_name = filename.lower()
    return any(lower_name.endswith(extension) for extension in SUPPORTED_ATTACHMENT_EXTENSIONS)


def supported_attachment_extensions() -> list[str]:
    return sorted(SUPPORTED_ATTACHMENT_EXTENSIONS)
