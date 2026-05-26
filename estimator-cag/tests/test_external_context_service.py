import asyncio

from app.services.external_context_service import infer_notion_search_terms, resolve_external_context
from app.sessions import ExternalContextConfig, ProjectMetadata, Session


def test_infer_notion_search_terms_prioritizes_explicit_and_metadata_terms() -> None:
    terms = infer_notion_search_terms(
        transcript="Necesitamos roadmap y alcance del proyecto Atlas para cliente Acme.",
        project_metadata=ProjectMetadata(project_name="Atlas", client_name="Acme"),
        explicit_terms=["Atlas discovery", "Acme"],
    )

    assert terms == ["Atlas discovery", "Acme", "Atlas", "Acme Atlas"]


def test_resolve_external_context_returns_empty_without_notion_key(monkeypatch) -> None:
    session = Session(
        project_metadata=ProjectMetadata(project_name="Atlas", client_name="Acme"),
        external_context_config=ExternalContextConfig(
            notion_page_ids=["page-123"],
            notion_search_terms=["Atlas"],
        ),
    )

    monkeypatch.setattr("app.services.external_context_service.settings.notion_api_key", "")

    items = asyncio.run(resolve_external_context(session=session, transcript="Roadmap del proyecto Atlas"))

    assert items == []
