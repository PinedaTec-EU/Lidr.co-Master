from __future__ import annotations

import inspect
from io import BytesIO

from fastapi import UploadFile


async def extract_attachments_text(attachments: list[UploadFile] | None) -> list[str]:
    if not attachments:
        return []

    extracted_sections: list[str] = []
    for attachment in attachments:
        filename = getattr(attachment, "filename", None) or getattr(attachment, "name", None) or "attachment"
        read_fn = getattr(attachment, "read")
        read_result = read_fn()
        content = await read_result if inspect.isawaitable(read_result) else read_result
        text = _extract_text_from_bytes(filename, content)
        if text.strip():
            extracted_sections.append(
                f"--- attachment: {filename} ---\n{text.strip()}"
            )
    return extracted_sections


def _extract_text_from_bytes(filename: str, content: bytes) -> str:
    lower_name = filename.lower()
    if lower_name.endswith(".pdf"):
        from pypdf import PdfReader

        reader = PdfReader(BytesIO(content))
        return "\n".join((page.extract_text() or "").strip() for page in reader.pages).strip()

    if lower_name.endswith(".docx"):
        from docx import Document

        document = Document(BytesIO(content))
        return "\n".join(paragraph.text for paragraph in document.paragraphs).strip()

    if lower_name.endswith(".txt") or lower_name.endswith(".md"):
        return content.decode("utf-8", errors="ignore").strip()

    raise ValueError(f"Unsupported attachment type for '{filename}'")
