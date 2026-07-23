from app.agentic.tools import ToolPrivilegeError, build_citations, extract_requirements, require_tool_privilege, verify_citations


def test_citations_are_verified_only_against_retrieved_sources() -> None:
    citations = build_citations(["101", "102"])

    report = verify_citations(citations, ["101", "102"])

    assert report.verified is True
    assert report.dangling_chunk_ids == []
    assert [citation.chunk_id for citation in report.verified_citations] == ["101", "102"]


def test_unknown_citation_is_reported_as_dangling() -> None:
    citation = build_citations(["999"])

    report = verify_citations(citation, ["101"])

    assert report.verified is False
    assert report.dangling_chunk_ids == ["999"]


def test_agent_cannot_use_unassigned_tool() -> None:
    try:
        require_tool_privilege("requirements_extractor", "search_budgets")
    except ToolPrivilegeError:
        pass
    else:
        raise AssertionError("The extractor must not access retrieval tools.")


def test_requirement_extraction_keeps_meaningful_fragments() -> None:
    requirements = extract_requirements("Portal B2B con autenticación, pagos y reporting operativo para equipos de finanzas.")

    assert requirements
