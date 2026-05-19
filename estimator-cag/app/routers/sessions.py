from typing import Annotated

from fastapi import APIRouter, File, Form, HTTPException, Query, UploadFile

from app.schemas import (
    DetailLevel,
    EstimationResponse,
    OutputFormat,
    ProjectType,
    SessionCreateResponse,
    SessionDetailResponse,
)
from app.services.session_service import (
    create_session as create_session_record,
    estimate_session_turn,
    get_session,
)

router = APIRouter()


@router.post("/sessions", response_model=SessionCreateResponse)
async def create_session():
    session_id = create_session_record()
    return SessionCreateResponse(session_id=session_id)


@router.get("/sessions/{session_id}", response_model=SessionDetailResponse)
async def get_session_detail(session_id: str):
    session = get_session(session_id)
    if session is None:
        raise HTTPException(status_code=404, detail="Session not found")

    return SessionDetailResponse(
        session_id=session_id,
        turns=session.history.turns,
        project_metadata=session.project_metadata.model_dump(),
        external_context_config=session.external_context_config.model_dump(),
        document_sources=session.document_sources,
        conversation_messages=session.conversation_messages,
        last_document_context=session.last_document_context,
        last_external_context=session.last_external_context,
        last_run_info=session.last_run_info,
    )


@router.post("/sessions/{session_id}/estimate", response_model=EstimationResponse)
async def estimate_session(
    session_id: str,
    transcript: Annotated[str, Form(...)],
    project_type: Annotated[ProjectType, Form(...)],
    detail_level: Annotated[DetailLevel, Form(...)],
    output_format: Annotated[OutputFormat, Form(...)],
    attachments: Annotated[list[UploadFile] | None, File()] = None,
    document_paths: Annotated[list[str] | None, Form()] = None,
    friendly_name: str | None = Query(default=None),
    provider: str | None = Query(default=None),
    model: str | None = Query(default=None),
):
    if get_session(session_id) is None:
        raise HTTPException(status_code=404, detail="Session not found")

    try:
        result, _project_metadata, _document_context_sections = await estimate_session_turn(
            session_id=session_id,
            transcript=transcript,
            project_type=project_type,
            detail_level=detail_level,
            output_format=output_format,
            attachments=attachments or [],
            document_paths=document_paths or [],
            friendly_name=friendly_name,
            provider=provider,
            model=model,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    return EstimationResponse(text=result["text"], prompt_version=result["prompt_version"])
