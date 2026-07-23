from __future__ import annotations

import ulid

from app.agentic.workflow import build_estimation_graph
from app.schemas import DetailLevel, OutputFormat, ProjectType, RetrievalPromptContext


async def run_agent_estimation(
    *,
    transcript: str,
    project_type: ProjectType,
    detail_level: DetailLevel,
    output_format: OutputFormat,
    retrieval_context: RetrievalPromptContext | None,
    checkpointer,
    estimation_id: str | None = None,
) -> dict:
    run_id = estimation_id or ulid.new().str
    graph = build_estimation_graph(checkpointer)
    result = await graph.ainvoke(
        {
            "estimation_id": run_id,
            "transcript": transcript,
            "project_type": project_type,
            "detail_level": detail_level,
            "output_format": output_format,
            "retrieval_context": retrieval_context,
            "source_refs": retrieval_context.source_refs if retrieval_context else [],
            "trace": [],
            "retrieved_citations": [],
        },
        {"configurable": {"thread_id": run_id}},
    )
    if result.get("__interrupt__"):
        return {"estimation_id": run_id, "status": "awaiting_human_review", "interrupt": result["__interrupt__"], **result}
    return {"estimation_id": run_id, **result}


async def resume_agent_estimation(*, estimation_id: str, decision: dict, checkpointer) -> dict:
    from langgraph.types import Command

    graph = build_estimation_graph(checkpointer)
    result = await graph.ainvoke(Command(resume=decision), {"configurable": {"thread_id": estimation_id}})
    return {"estimation_id": estimation_id, **result}
