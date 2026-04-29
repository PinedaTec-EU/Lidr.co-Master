from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.services.llm_service import get_estimation

router = APIRouter()


class EstimationRequest(BaseModel):
    transcription: str


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

    result = await get_estimation(request.transcription)
    return EstimationResponse(
        **result,
        timestamp=datetime.now(timezone.utc).isoformat(),
    )
