from __future__ import annotations

from io import BytesIO

from fastapi import UploadFile


async def extract_attachments_text(attachments: list[UploadFile] | None) -> list[str]:
    if not attachments:
        return []

    extracted_sections: list[str] = []
    for attachment in attachments:
        content = await attachment.read()
        text = _extract_text_from_bytes(attachment.filename or "attachment", content)
        if text.strip():
            extracted_sections.append(
                f"--- attachment: {attachment.filename or 'attachment'} ---\n{text.strip()}"
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
