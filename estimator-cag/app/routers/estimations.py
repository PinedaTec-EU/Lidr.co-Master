from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.services.llm_service import get_available_friendly_names, get_estimation

router = APIRouter()


class EstimationRequest(BaseModel):
    transcription: str
    friendly_name: str | None = None
    provider: str | None = None
    model: str | None = None


class TokensUsed(BaseModel):
    prompt: int
    completion: int
    total: int


class EstimationResponse(BaseModel):
    estimation: str
    model: str
    provider: str
    tokens_used: TokensUsed
    timestamp: str


@router.post("/estimate", response_model=EstimationResponse)
async def estimate(request: EstimationRequest):
    if not request.transcription.strip():
        raise HTTPException(status_code=400, detail="La transcripción no puede estar vacía")

    try:
        result = await get_estimation(
            request.transcription,
            friendly_name=request.friendly_name,
            provider=request.provider,
            model=request.model,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    return EstimationResponse(
        **result,
        timestamp=datetime.now(timezone.utc).isoformat(),
    )


@router.get("/estimate/friendly-names")
async def estimate_friendly_names():
    return {"friendly_names": get_available_friendly_names()}
