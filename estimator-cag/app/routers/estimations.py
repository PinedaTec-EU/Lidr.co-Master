from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.services.llm_service import get_estimation

router = APIRouter()


class EstimationRequest(BaseModel):
    transcript: str


class EstimationResponse(BaseModel):
    estimation: str


@router.post("/estimate", response_model=EstimationResponse)
async def estimate(request: EstimationRequest):
    if not request.transcript.strip():
        raise HTTPException(status_code=400, detail="La transcripción no puede estar vacía")

    estimation = await get_estimation(request.transcript)
    return EstimationResponse(estimation=estimation)
