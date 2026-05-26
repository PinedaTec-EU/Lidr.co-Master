from app.services import attachment_extraction


def test_extract_markdown_from_docling_response_prefers_md_content() -> None:
    payload = {
        "document": {
            "filename": "requirements.pdf",
            "md_content": "# Proyecto\n\nTexto convertido.",
            "text": "fallback",
        }
    }

    assert (
        attachment_extraction._extract_markdown_from_docling_response(payload)
        == "# Proyecto\n\nTexto convertido."
    )


def test_extract_markdown_from_docling_response_accepts_outputs_markdown() -> None:
    payload = {
        "document": {
            "filename": "requirements.pdf",
            "outputs": {"markdown": "## Contenido\n\nConvertido"},
        }
    }

    assert (
        attachment_extraction._extract_markdown_from_docling_response(payload)
        == "## Contenido\n\nConvertido"
    )


def test_supported_attachment_extensions_are_public_and_sorted() -> None:
    assert attachment_extraction.supported_attachment_extensions() == sorted(
        attachment_extraction.SUPPORTED_ATTACHMENT_EXTENSIONS
    )


def test_is_supported_attachment_rejects_unknown_extensions() -> None:
    assert attachment_extraction.is_supported_attachment("notes.exe") is False


def test_extract_markdown_from_docling_response_requires_document_payload() -> None:
    try:
        attachment_extraction._extract_markdown_from_docling_response({"result": {}})
    except ValueError as exc:
        assert "document" in str(exc)
    else:
        raise AssertionError("Expected ValueError when Docling omits document payload")
