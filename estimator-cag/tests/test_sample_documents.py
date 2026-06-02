from app.context.sample_documents import list_sample_documents, resolve_sample_document_paths


def test_list_sample_documents_includes_repo_fixtures() -> None:
    documents = list_sample_documents()

    assert "session-01-marketplace-discovery.txt" in documents
    assert "session-02-ops-automation.md" in documents
    assert "session-03-clinic-modernization.pdf" in documents


def test_resolve_sample_document_paths_returns_absolute_paths() -> None:
    paths = resolve_sample_document_paths(["session-01-marketplace-discovery.txt"])

    assert len(paths) == 1
    assert paths[0].endswith("session-01-marketplace-discovery.txt")
    assert paths[0].startswith("/")
