from app.sessions import ConversationHistory, ProjectMetadata, SessionStore


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
        "assumed_team_size": None,
        "mentioned_technologies": [],
        "agreed_scope": None,
    }


def test_session_store_get_or_create_reuses_existing_session() -> None:
    store = SessionStore()

    first = store.get_or_create("abc")
    second = store.get_or_create("abc")

    assert first is second
