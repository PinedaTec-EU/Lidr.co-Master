from app.services import llm_service


def test_system_prompt_includes_examples_and_output_contract() -> None:
    prompt = llm_service.get_system_prompt()

    assert "Eres un estimador de software experto" in prompt
    assert "### Ejemplo 1" in prompt
    assert "Responde siempre en español y en formato Markdown." in prompt


def test_context_summary_matches_examples() -> None:
    summary = llm_service.get_context_summary()

    assert summary["examples_count"] == 10
    assert len(summary["examples"]) == 10
    assert summary["examples"][0]["estimation_preview"].startswith("## Estimación:")


def test_resolve_route_for_friendly_name_anthropic() -> None:
    route = llm_service._resolve_route(friendly_name="anthropic")

    assert route.provider == "anthropic"
    assert route.model == "anthropic/claude-haiku-4-5-20251001"


def test_resolve_route_for_provider_override_ollama() -> None:
    route = llm_service._resolve_route(provider="ollama", model="llama3.2")

    assert route.provider == "ollama"
    assert route.model == "ollama/llama3.2"


def test_tokens_used_defaults_total_when_missing() -> None:
    usage = {"prompt_tokens": 12, "completion_tokens": 7}

    assert llm_service._tokens_used(usage) == {
        "prompt": 12,
        "completion": 7,
        "total": 19,
    }
