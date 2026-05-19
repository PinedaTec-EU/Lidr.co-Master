from typing import Annotated

from fastapi import APIRouter, File, Form, HTTPException, Query, UploadFile

from app.schemas import DetailLevel, EstimationResponse, OutputFormat, ProjectType, SessionCreateResponse
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


@router.post("/sessions/{session_id}/estimate", response_model=EstimationResponse)
async def estimate_session(
    session_id: str,
    transcript: Annotated[str, Form(...)],
    project_type: Annotated[ProjectType, Form(...)],
    detail_level: Annotated[DetailLevel, Form(...)],
    output_format: Annotated[OutputFormat, Form(...)],
    attachments: Annotated[list[UploadFile] | None, File()] = None,
    friendly_name: str | None = Query(default=None),
    provider: str | None = Query(default=None),
    model: str | None = Query(default=None),
):
    if get_session(session_id) is None:
        raise HTTPException(status_code=404, detail="Session not found")

    try:
        result, _project_metadata = await estimate_session_turn(
            session_id=session_id,
            transcript=transcript,
            project_type=project_type,
            detail_level=detail_level,
            output_format=output_format,
            attachments=attachments or [],
            friendly_name=friendly_name,
            provider=provider,
            model=model,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    return EstimationResponse(text=result["text"], prompt_version=result["prompt_version"])
