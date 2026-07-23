from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request, Response

from app.agentic.service import resume_agent_estimation, run_agent_estimation
from app.config import settings
from app.rate_limit import enforce_rate_limit
from app.schemas import AgentEstimateRequest, AgentEstimateResponse, EstimationRequest, HumanReviewDecision
from app.security import require_estimate_key
from app.services.retrieval_prompt_context_service import resolve_retrieval_prompt_context

router = APIRouter(tags=["agent-estimate"])


def _response_payload(result: dict) -> dict:
    model_result = result.get("model_result", {})
    return {
        "model": "pending",
        "provider": "pending",
        "tokens_used": {"prompt": 0, "completion": 0, "total": 0},
        "latency_ms": 0,
        "cost_usd": 0,
        "prompt_version": "agentic-v1",
        **model_result,
        "text": result.get("text", ""),
        "request_id": result["estimation_id"],
        "idempotency_cache_hit": False,
        "retrieval_context_included": bool(result.get("source_refs")),
        "retrieved_results_count": len(result.get("source_refs", [])),
        "included_chunks_count": len(result.get("source_refs", [])),
        "status": result["status"],
        "confidence": result.get("confidence", 0),
        "citations": result.get("citations", {"verified": False, "abstained": True}),
        "trace": result.get("trace", []),
        "estimation_id": result["estimation_id"],
    }


@router.post("/agent-estimate", response_model=AgentEstimateResponse)
async def agent_estimate(
    request: Request,
    response: Response,
    payload: AgentEstimateRequest,
    x_api_key: str = Depends(require_estimate_key),
) -> AgentEstimateResponse:
    enforce_rate_limit(request=request, x_api_key=x_api_key, limit=settings.estimate_rate_limit_per_minute, namespace="agent-estimate")
    try:
        checkpointer = getattr(request.app.state, "agent_checkpointer", None)
        if checkpointer is None:
            raise HTTPException(status_code=503, detail="Agent checkpoint persistence is not configured.")
        retrieval_context = await resolve_retrieval_prompt_context(EstimationRequest(
            description=payload.transcript,
            project_type=payload.project_type,
            detail_level=payload.detail_level,
            output_format=payload.output_format,
            retrieval=payload.retrieval.model_copy(update={"enabled": True}),
        ))
        result = await run_agent_estimation(
            transcript=payload.transcript,
            project_type=payload.project_type,
            detail_level=payload.detail_level,
            output_format=payload.output_format,
            retrieval_context=retrieval_context,
            estimation_id=payload.estimation_id,
            checkpointer=checkpointer,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    response.headers["X-Request-ID"] = result["estimation_id"]
    return AgentEstimateResponse(**_response_payload(result))


@router.post("/agent-estimate/{estimation_id}/resume", response_model=AgentEstimateResponse)
async def resume_agent_estimate(
    request: Request,
    estimation_id: str,
    payload: HumanReviewDecision,
    x_api_key: str = Depends(require_estimate_key),
) -> AgentEstimateResponse:
    try:
        checkpointer = getattr(request.app.state, "agent_checkpointer", None)
        if checkpointer is None:
            raise HTTPException(status_code=503, detail="Agent checkpoint persistence is not configured.")
        result = await resume_agent_estimation(estimation_id=estimation_id, decision=payload.model_dump(), checkpointer=checkpointer)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return AgentEstimateResponse(**_response_payload(result))
