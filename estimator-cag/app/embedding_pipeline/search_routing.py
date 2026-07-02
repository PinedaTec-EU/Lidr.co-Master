from __future__ import annotations

from dataclasses import dataclass

from app.embedding_pipeline.schemas import SearchTarget

DOCUMENT_TYPES_BY_TARGET = {
    SearchTarget.BUDGETS: ("historical_budget",),
    SearchTarget.TRANSCRIPTS: ("meeting_transcript", "session_transcript"),
    SearchTarget.TECHNICAL_DOCS: ("technical_doc", "technical_docs", "architecture_doc"),
}


@dataclass(frozen=True)
class RoutingDecision:
    targets: list[SearchTarget]
    reason: str


def route_search_targets(
    *,
    query: str,
    explicit_targets: list[SearchTarget] | None,
) -> RoutingDecision:
    if explicit_targets:
        return RoutingDecision(
            targets=explicit_targets,
            reason="caller provided explicit target collections",
        )

    lowered = query.lower()
    if any(token in lowered for token in ("cost", "hours", "budget", "estimate", "estimacion")):
        return RoutingDecision(
            targets=[SearchTarget.BUDGETS],
            reason="cost and effort wording routes to historical budgets",
        )
    if any(token in lowered for token in ("meeting", "transcript", "call notes", "reunion")):
        return RoutingDecision(
            targets=[SearchTarget.TRANSCRIPTS],
            reason="conversation wording routes to transcripts",
        )
    if any(token in lowered for token in ("architecture", "technical", "design doc", "runbook")):
        return RoutingDecision(
            targets=[SearchTarget.TECHNICAL_DOCS],
            reason="technical reference wording routes to technical docs",
        )
    return RoutingDecision(
        targets=[SearchTarget.BUDGETS],
        reason="estimation workflow defaults to budgets when no stronger signal exists",
    )
