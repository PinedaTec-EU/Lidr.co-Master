from __future__ import annotations

import json
import time
import uuid
from contextlib import contextmanager

import structlog

from app.config import settings
from app.idempotency_store import build_request_hash, idempotency_store
from app.schemas import (
    DetailLevel,
    EstimationRequest,
    OutputFormat,
    ProjectType,
    RetrievalContextConfig,
    RetrievalPromptContext,
)
from app.services.llm_service import get_estimation
from app.services.retrieval_prompt_context_service import resolve_retrieval_prompt_context

logger = structlog.get_logger()


@contextmanager
def log_stage(stage: str, request_id: str, **context):
    started_at = time.perf_counter()
    log = logger.bind(stage=stage, request_id=request_id, **context)
    log.info("stage.started")
    try:
        yield log
        duration_ms = round((time.perf_counter() - started_at) * 1000, 2)
        log.info("stage.completed", duration_ms=duration_ms)
    except Exception as exc:
        duration_ms = round((time.perf_counter() - started_at) * 1000, 2)
        log.exception("stage.failed", duration_ms=duration_ms, error=str(exc))
        raise


def _default_retrieval_config() -> RetrievalContextConfig:
    return RetrievalContextConfig(
        enabled=True,
        rewrite_strategy="normalize",
        score_threshold=0.72,
        k=8,
        max_chunks=4,
        max_context_chars=2400,
        include_scores=True,
    )


async def estimate_from_transcript(
    *,
    transcript: str,
    idempotency_key: str | None = None,
    project_type: ProjectType = ProjectType.WEB_SAAS,
    detail_level: DetailLevel = DetailLevel.MEDIUM,
    output_format: OutputFormat = OutputFormat.NARRATIVE,
    retrieval: RetrievalContextConfig | None = None,
    friendly_name: str | None = None,
    provider: str | None = None,
    model: str | None = None,
) -> tuple[dict, str]:
    request_id = str(uuid.uuid4())
    request_hash = build_request_hash(transcript=transcript)
    now = time.time()

    if idempotency_key:
        cached = idempotency_store.get(key=idempotency_key, request_hash=request_hash, now=now)
        if cached is not None:
            payload = json.loads(cached)
            payload["request_id"] = request_id
            payload["idempotency_cache_hit"] = True
            return payload, request_id

    request = EstimationRequest(
        description=transcript.strip(),
        project_type=project_type,
        detail_level=detail_level,
        output_format=output_format,
        retrieval=retrieval or _default_retrieval_config(),
    )

    retrieval_context: RetrievalPromptContext | None = None
    with log_stage("reformulation", request_id, rewrite_strategy=request.retrieval.rewrite_strategy.value):
        if request.retrieval.enabled:
            with log_stage("retrieval", request_id, score_threshold=request.retrieval.score_threshold, k=request.retrieval.k):
                retrieval_context = await resolve_retrieval_prompt_context(request)

    with log_stage(
        "context_assembly",
        request_id,
        included_chunks=(retrieval_context.included_chunks_count if retrieval_context else 0),
    ):
        pass

    with log_stage("generation", request_id, confidence_target="evidence_first"):
        result = await get_estimation(
            request,
            friendly_name=friendly_name,
            provider=provider,
            model=model,
            retrieval_context=retrieval_context,
        )

    payload = {
        **result,
        "request_id": request_id,
        "idempotency_cache_hit": False,
        "retrieval_context_included": retrieval_context is not None,
        "retrieved_results_count": retrieval_context.retrieved_results_count if retrieval_context else 0,
        "included_chunks_count": retrieval_context.included_chunks_count if retrieval_context else 0,
    }

    if idempotency_key:
        idempotency_store.set(
            key=idempotency_key,
            request_hash=request_hash,
            payload=payload,
            ttl_seconds=settings.idempotency_ttl_seconds,
            now=now,
        )

    return payload, request_id
