from __future__ import annotations

from langgraph.graph import END, START, StateGraph
from langgraph.types import Command, interrupt

from app.agentic.contracts import EstimationGraphState
from app.agentic.tools import build_citations, extract_requirements, require_tool_privilege, verify_citations
from app.config import settings
from app.schemas import AgentTraceStep, EstimationRequest, RetrievalContextConfig
from app.services.llm_service import get_estimation


def _trace(agent: str, action: str, outcome: str, tool_name: str | None = None) -> list[AgentTraceStep]:
    return [AgentTraceStep(agent=agent, action=action, outcome=outcome, tool_name=tool_name)]


def supervisor(state: EstimationGraphState) -> Command:
    if not state.get("requirements"):
        target = "requirements_extractor"
    elif "retrieved" not in state:
        target = "budget_searcher"
    elif not state.get("model_result"):
        target = "estimate_generator"
    elif not state.get("citations"):
        target = "coherence_validator"
    elif state.get("confidence", 0) < settings.agent_confidence_threshold and not state.get("human_decision"):
        target = "human_review_gate"
    else:
        target = END
    return Command(goto=target, update={"trace": _trace("supervisor", "route", str(target))})


def requirements_extractor(state: EstimationGraphState) -> dict:
    requirements = extract_requirements(state["transcript"])
    return {"requirements": requirements, "trace": _trace("requirements_extractor", "extract_requirements", str(len(requirements)))}


def budget_searcher(state: EstimationGraphState) -> dict:
    require_tool_privilege("budget_searcher", "search_budgets")
    citations = build_citations(state.get("source_refs", []))
    return {
        "retrieved_citations": citations,
        "retrieved": True,
        "trace": _trace("budget_searcher", "search_retrieval_context", str(len(citations)), "search_budgets"),
    }


async def estimate_generator(state: EstimationGraphState) -> dict:
    require_tool_privilege("estimate_generator", "generate_estimate")
    request = EstimationRequest(
        description=state["transcript"],
        project_type=state["project_type"],
        detail_level=state["detail_level"],
        output_format=state["output_format"],
        retrieval=RetrievalContextConfig(enabled=False),
    )
    result = await get_estimation(request, retrieval_context=state.get("retrieval_context"))
    return {"text": result["text"], "model_result": result, "trace": _trace("estimate_generator", "generate", "completed", "generate_estimate")}


def coherence_validator(state: EstimationGraphState) -> dict:
    require_tool_privilege("coherence_validator", "validate_estimate")
    report = verify_citations(state.get("retrieved_citations", []), state.get("source_refs", []))
    confidence = 0.9 if report.verified and len(report.verified_citations) >= 2 else 0.45
    status = "validated" if confidence >= settings.agent_confidence_threshold else "needs_review"
    return {"citations": report, "confidence": confidence, "status": status, "trace": _trace("coherence_validator", "verify_citations", status, "validate_estimate")}


def human_review_gate(state: EstimationGraphState) -> dict:
    decision = interrupt({"reason": "low_confidence_estimate", "confidence": state.get("confidence"), "estimate": state.get("text")})
    return {"human_decision": decision, "status": "reviewed", "trace": _trace("human_review_gate", "human_review", str(decision))}


def build_estimation_graph(checkpointer):
    graph = StateGraph(EstimationGraphState)
    graph.add_node("supervisor", supervisor)
    graph.add_node("requirements_extractor", requirements_extractor)
    graph.add_node("budget_searcher", budget_searcher)
    graph.add_node("estimate_generator", estimate_generator)
    graph.add_node("coherence_validator", coherence_validator)
    graph.add_node("human_review_gate", human_review_gate)
    graph.add_edge(START, "supervisor")
    for node in ("requirements_extractor", "budget_searcher", "estimate_generator", "coherence_validator", "human_review_gate"):
        graph.add_edge(node, "supervisor")
    return graph.compile(checkpointer=checkpointer)
