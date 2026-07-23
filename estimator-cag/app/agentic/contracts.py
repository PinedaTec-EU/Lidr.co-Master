from __future__ import annotations

from typing import Annotated, Literal, TypedDict
import operator

from app.schemas import AgentTraceStep, CitationVerificationReport, EvidenceCitation
from app.schemas import DetailLevel, OutputFormat, ProjectType, RetrievalPromptContext


AgentName = Literal[
    "supervisor",
    "requirements_extractor",
    "budget_searcher",
    "estimate_generator",
    "coherence_validator",
    "human_review_gate",
]


class EstimationGraphState(TypedDict, total=False):
    estimation_id: str
    transcript: str
    project_type: ProjectType
    detail_level: DetailLevel
    output_format: OutputFormat
    retrieval_context: RetrievalPromptContext | None
    requirements: list[str]
    source_refs: list[str]
    retrieved: bool
    retrieved_citations: Annotated[list[EvidenceCitation], operator.add]
    text: str
    model_result: dict
    confidence: float
    citations: CitationVerificationReport
    status: str
    human_decision: dict
    trace: Annotated[list[AgentTraceStep], operator.add]


AGENT_PRIVILEGES: dict[AgentName, frozenset[str]] = {
    "supervisor": frozenset(),
    "requirements_extractor": frozenset(),
    "budget_searcher": frozenset({"search_budgets"}),
    "estimate_generator": frozenset({"generate_estimate"}),
    "coherence_validator": frozenset({"validate_estimate"}),
    "human_review_gate": frozenset(),
}
