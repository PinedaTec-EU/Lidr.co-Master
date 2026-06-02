from pathlib import Path

from app.schemas import UserTier
from app.sessions import ConversationHistory, ExternalContextItem, ProjectMetadata, SessionStore


def test_conversation_history_keeps_only_latest_turns() -> None:
    history = ConversationHistory(max_turns=2)

    history.add_turn("u1", "a1")
    history.add_turn("u2", "a2")
    history.add_turn("u3", "a3")

    assert history.turns == [("u2", "a2"), ("u3", "a3")]


def test_conversation_history_preserves_system_message_in_rendered_messages() -> None:
    history = ConversationHistory(max_turns=2)
    history.add_turn("Necesitamos login.", "Estimación parcial.")

    messages = history.to_messages_list("SYSTEM PROMPT")

    assert messages[0] == {"role": "system", "content": "SYSTEM PROMPT"}
    assert messages[1:] == [
        {"role": "user", "content": "Necesitamos login."},
        {"role": "assistant", "content": "Estimación parcial."},
    ]


def test_project_metadata_defaults_to_empty_shape() -> None:
    metadata = ProjectMetadata()

    assert metadata.model_dump() == {
        "project_name": None,
        "client_name": None,
        "assumed_team_size": None,
        "mentioned_technologies": [],
        "agreed_scope": None,
    }


def test_session_store_get_or_create_reuses_existing_session() -> None:
    store = SessionStore()

    first = store.get_or_create("abc")
    second = store.get_or_create("abc")

    assert first is second


def test_session_store_persists_sessions_to_disk(tmp_path: Path) -> None:
    store_path = tmp_path / "sessions.json"
    store = SessionStore(path=store_path)

    session = store.create(
        "01TESTSESSION00000000000000",
        user_tier=UserTier.EXECUTIVE,
        user_display_name="pineda",
    )
    session.history.add_turn("u1", "a1")
    session.remember_document_sources(["/tmp/requirements.pdf"])
    session.set_external_context_config(
        notion_page_ids=["page-123"],
        notion_search_terms=["Atlas"],
    )
    session.add_conversation_message("user", "Solicitud visible")
    session.set_last_document_context(["--- attachment: requirements.pdf ---\nTexto"])
    session.set_last_external_context(
        [
            ExternalContextItem(
                source="notion",
                title="Atlas kickoff",
                content="Roadmap, alcance y stakeholders.",
                url="https://notion.so/atlas",
                updated_at="2026-05-19T10:00:00Z",
                relevance_reason="Explicit notion_page_id configured in the session.",
            )
        ]
    )
    session.set_last_run_info(
        provider="openai",
        model="openai/gpt-4o-mini",
        tokens_used={"prompt": 10, "completion": 20, "total": 30},
        response_time=1.23,
    )
    store.save_session("01TESTSESSION00000000000000")

    reloaded = SessionStore(path=store_path)
    persisted = reloaded.get("01TESTSESSION00000000000000")

    assert persisted is not None
    assert persisted.user_tier == UserTier.EXECUTIVE
    assert persisted.user_display_name == "pineda"
    assert persisted.history.turns == [("u1", "a1")]
    assert persisted.document_sources == ["/tmp/requirements.pdf"]
    assert persisted.external_context_config.notion_page_ids == ["page-123"]
    assert persisted.external_context_config.notion_search_terms == ["Atlas"]
    assert persisted.conversation_messages == [{"role": "user", "content": "Solicitud visible"}]
    assert persisted.last_document_context == ["--- attachment: requirements.pdf ---\nTexto"]
    assert persisted.last_external_context == [
        {
            "source": "notion",
            "title": "Atlas kickoff",
            "content": "Roadmap, alcance y stakeholders.",
            "url": "https://notion.so/atlas",
            "updated_at": "2026-05-19T10:00:00Z",
            "relevance_reason": "Explicit notion_page_id configured in the session.",
        }
    ]
    assert persisted.last_run_info == {
        "provider": "openai",
        "model": "openai/gpt-4o-mini",
        "tokens_used": {"prompt": 10, "completion": 20, "total": 30},
        "response_time": 1.23,
    }
