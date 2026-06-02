from pathlib import Path


SAMPLE_DOCUMENTS_DIR = Path(__file__).resolve().parents[2] / "sample-documents"


def list_sample_documents() -> list[str]:
    if not SAMPLE_DOCUMENTS_DIR.exists():
        return []

    return sorted(
        path.name
        for path in SAMPLE_DOCUMENTS_DIR.iterdir()
        if path.is_file() and path.suffix in {".txt", ".md", ".pdf"}
    )


def resolve_sample_document_paths(filenames: list[str]) -> list[str]:
    resolved_paths: list[str] = []
    for filename in filenames:
        path = SAMPLE_DOCUMENTS_DIR / filename
        if not path.exists() or path.suffix not in {".txt", ".md", ".pdf"}:
            raise ValueError(f"Unknown sample document '{filename}'")
        resolved_paths.append(str(path.resolve()))
    return resolved_paths
