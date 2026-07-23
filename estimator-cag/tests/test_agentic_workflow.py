from __future__ import annotations

import asyncio

from langgraph.checkpoint.memory import InMemorySaver
from langgraph.types import Command

from app.agentic import workflow
from app.schemas import DetailLevel, OutputFormat, ProjectType


def test_low_confidence_run_pauses_and_resumes(monkeypatch) -> None:
    async def fake_estimation(*_args, **_kwargs) -> dict:
        return {
            "text": "Estimación pendiente de revisión.",
            "prompt_version": "v1",
            "model": "test-model",
            "provider": "test",
            "tokens_used": {"prompt": 1, "completion": 1, "total": 2},
            "latency_ms": 1.0,
            "cost_usd": 0.0,
        }

    monkeypatch.setattr(workflow, "get_estimation", fake_estimation)

    async def run() -> None:
        graph = workflow.build_estimation_graph(InMemorySaver())
        config = {"configurable": {"thread_id": "agent-workflow-test"}}
        state = {
            "estimation_id": "agent-workflow-test",
            "transcript": "Necesitamos una plataforma con requisitos ambiguos que deben revisarse antes de aprobar el presupuesto final.",
            "project_type": ProjectType.WEB_SAAS,
            "detail_level": DetailLevel.MEDIUM,
            "output_format": OutputFormat.NARRATIVE,
            "source_refs": [],
            "trace": [],
            "retrieved_citations": [],
        }
        paused = await graph.ainvoke(state, config)
        assert paused["__interrupt__"]

        resumed = await graph.ainvoke(Command(resume={"decision": "approve"}), config)
        assert resumed["status"] == "reviewed"
        assert resumed["human_decision"] == {"decision": "approve"}

    asyncio.run(run())
