from __future__ import annotations

import ulid
import structlog

from app.errors import NotFoundError
from app.prompts.loader import render_estimation_prompt
from app.schemas import DetailLevel, EstimationRequest, OutputFormat, ProjectType, UserTier
from app.services.attachment_extraction import (
    extract_attachments_text,
    extract_document_paths_text,
)
from app.services.external_context_service import resolve_external_context
from app.services.llm_service import get_estimation
from app.sessions import ProjectMetadata, Session, SessionStore, TurnObservation


session_store = SessionStore()
logger = structlog.get_logger()


def create_session(
    user_tier: UserTier | None = UserTier.DEVELOPER,
    user_display_name: str | None = None,
) -> str:
    session_id = str(ulid.new())
    session_store.create(
        session_id,
        user_tier=user_tier,
        user_display_name=user_display_name,
    )
    return session_id


def get_session(session_id: str) -> Session | None:
    return session_store.get(session_id)


def set_session_user_profile(
    session_id: str,
    *,
    user_tier: UserTier,
    user_display_name: str,
) -> None:
    session = session_store.get(session_id)
    if session is None:
        raise NotFoundError(f"Session not found: {session_id}")

    session.set_user_profile(user_tier, user_display_name)
    session_store.save_session(session_id)


def update_external_context_config(
    session_id: str,
    *,
    notion_page_ids: list[str],
    notion_search_terms: list[str],
) -> None:
    session = session_store.get(session_id)
    if session is None:
        raise NotFoundError(f"Session not found: {session_id}")

    session.set_external_context_config(
        notion_page_ids=notion_page_ids,
        notion_search_terms=notion_search_terms,
    )
    session_store.save_session(session_id)


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
        raise NotFoundError(f"Session not found: {session_id}")

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


def _build_turn_observation(
    *,
    session_id: str,
    session: Session,
    request_description: str,
    transcript: str,
    document_context_sections: list[str],
    result: dict,
) -> TurnObservation:
    messages_in_window = len(session.history.to_turn_messages())
    tokens_used = result.get("tokens_used", {})
    return TurnObservation(
        turn_index=(len(session.conversation_messages) // 2),
        session_id=session_id,
        enriched_transcript_chars=len(request_description),
        attachments_total_chars=sum(len(item) for item in document_context_sections),
        messages_in_window=messages_in_window,
        anchors_count=0,
        summary_chars=0,
        tokens_in=int(tokens_used.get("prompt", 0)),
        tokens_out=int(tokens_used.get("completion", 0)),
        cost_usd=float(result.get("cost_usd", 0.0)),
        latency_ms=float(result.get("latency_ms", 0.0)),
        cache_hit_kind="none",
        last_resolved_tier=session.user_tier or UserTier.DEVELOPER,
        model=str(result.get("model", "")),
        provider=str(result.get("provider", "")),
        project_metadata=session.project_metadata.model_dump(),
        assistant_text=str(result.get("text", "")),
        summary_text="",
        anchors=[],
        transcript_excerpt=transcript.strip()[:280],
    )


def _log_turn_observation(observation: TurnObservation) -> None:
    payload = observation.model_dump(mode="json")
    for noisy_field in ("assistant_text", "project_metadata", "summary_text", "anchors", "transcript_excerpt"):
        payload.pop(noisy_field, None)
    logger.info("turn_observed", **payload)


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
        raise NotFoundError(f"Session not found: {session_id}")
    if session.user_tier is None:
        raise ValueError("Session tier not configured.")

    attachment_sections = await extract_attachments_text(attachments)
    path_sections = await extract_document_paths_text(document_paths)
    document_context_sections = attachment_sections + path_sections
    request = EstimationRequest(
        description=compose_description(transcript, document_context_sections),
        project_type=project_type,
        detail_level=detail_level,
        output_format=output_format,
    )
    external_context = await resolve_external_context(session=session, transcript=transcript)

    result = await get_estimation(
        request,
        friendly_name=friendly_name,
        provider=provider,
        model=model,
        history_messages=session.history.to_turn_messages(),
        project_metadata=session.project_metadata,
        external_context=external_context,
        user_tier=session.user_tier,
        user_display_name=session.user_display_name,
    )

    _system_prompt, user_prompt = render_estimation_prompt(
        request,
        version=result["prompt_version"],
        project_metadata=session.project_metadata,
        external_context=external_context,
        user_tier=session.user_tier,
        user_display_name=session.user_display_name,
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
    session.set_last_external_context(external_context)
    session.set_last_run_info(
        provider=result.get("provider", ""),
        model=result.get("model", ""),
        tokens_used=result.get("tokens_used", {"prompt": 0, "completion": 0, "total": 0}),
        response_time=float(result.get("latency_ms", 0.0)),
    )
    observation = _build_turn_observation(
        session_id=session_id,
        session=session,
        request_description=request.description,
        transcript=transcript,
        document_context_sections=document_context_sections,
        result=result,
    )
    session.add_turn_observation(observation)
    _log_turn_observation(observation)
    session_store.save_session(session_id)
    return result, session.project_metadata, document_context_sections
