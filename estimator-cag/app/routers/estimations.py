from fastapi import APIRouter, Depends, HTTPException

from app.application.estimation import EstimationService
from app.dependencies import get_estimation_service
from app.schemas import EstimationRequest, EstimationResponse
from app.services.llm_service import get_available_friendly_names

router = APIRouter()


@router.post("/estimate", response_model=EstimationResponse)
async def estimate(
    request: EstimationRequest,
    estimation_service: EstimationService = Depends(get_estimation_service),
):
    try:
        result = await estimation_service.estimate(request)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    return result


@router.get("/estimate/friendly-names")
async def estimate_friendly_names():
    return {"friendly_names": get_available_friendly_names()}
