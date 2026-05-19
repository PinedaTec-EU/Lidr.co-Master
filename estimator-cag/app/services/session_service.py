from __future__ import annotations

import ulid

from app.prompts.loader import render_estimation_prompt
from app.schemas import DetailLevel, EstimationRequest, OutputFormat, ProjectType
from app.services.attachment_extraction import (
    extract_attachments_text,
    extract_document_paths_text,
)
from app.services.llm_service import get_estimation
from app.sessions import ProjectMetadata, Session, SessionStore


session_store = SessionStore()


def create_session() -> str:
    session_id = str(ulid.new())
    session_store.create(session_id)
    return session_id


def get_session(session_id: str) -> Session | None:
    return session_store.get(session_id)


def persist_last_run_info(
    session_id: str,
    *,
    provider: str,
    model: str,
    tokens_used: dict,
    response_time: float,
) -> None:
    session = session_store.get(session_id)
    if session is None:
        raise KeyError(session_id)

    session.set_last_run_info(
        provider=provider,
        model=model,
        tokens_used=tokens_used,
        response_time=response_time,
    )
    session_store.save_session(session_id)


def compose_description(transcript: str, attachment_sections: list[str], max_chars: int = 2000) -> str:
    combined = transcript.strip()
    if attachment_sections:
        combined = f"{combined}\n\n" + "\n\n".join(attachment_sections)
    return combined[:max_chars].strip()


async def estimate_session_turn(
    *,
    session_id: str,
    transcript: str,
    project_type: ProjectType,
    detail_level: DetailLevel,
    output_format: OutputFormat,
    attachments,
    document_paths: list[str] | None = None,
    display_user_message: str | None = None,
    friendly_name: str | None = None,
    provider: str | None = None,
    model: str | None = None,
) -> tuple[dict, ProjectMetadata, list[str]]:
    session = session_store.get(session_id)
    if session is None:
        raise KeyError(session_id)

    attachment_sections = await extract_attachments_text(attachments)
    path_sections = await extract_document_paths_text(document_paths)
    document_context_sections = attachment_sections + path_sections
    request = EstimationRequest(
        description=compose_description(transcript, document_context_sections),
        project_type=project_type,
        detail_level=detail_level,
        output_format=output_format,
    )

    result = await get_estimation(
        request,
        friendly_name=friendly_name,
        provider=provider,
        model=model,
        history_messages=session.history.to_turn_messages(),
        project_metadata=session.project_metadata,
    )

    _system_prompt, user_prompt = render_estimation_prompt(
        request,
        version=result["prompt_version"],
        project_metadata=session.project_metadata,
    )
    session.history.add_turn(user_prompt, result["text"])
    session.add_conversation_message("user", display_user_message or transcript.strip())
    session.add_conversation_message("assistant", result["text"])
    session.project_metadata = session.project_metadata.merge_from_interaction(
        request.description,
        result["text"],
    )
    session.remember_document_sources(document_paths or [])
    session.set_last_document_context(document_context_sections)
    session_store.save_session(session_id)
    return result, session.project_metadata, document_context_sections
