from __future__ import annotations

import re
from statistics import median

from app.agentic.contracts import AGENT_PRIVILEGES, AgentName
from app.schemas import CitationVerificationReport, EvidenceCitation


class ToolPrivilegeError(ValueError):
    pass


def require_tool_privilege(agent: AgentName, tool_name: str) -> None:
    if tool_name not in AGENT_PRIVILEGES[agent]:
        raise ToolPrivilegeError(f"Agent '{agent}' cannot execute tool '{tool_name}'.")


def extract_requirements(transcript: str) -> list[str]:
    parts = re.split(r"[\n,;]|\by\b", transcript, flags=re.IGNORECASE)
    return [part.strip() for part in parts if len(part.strip()) >= 12][:12]


def build_citations(source_refs: list[str]) -> list[EvidenceCitation]:
    return [
        EvidenceCitation(chunk_id=source_ref, locator=f"retrieval chunk {source_ref}", excerpt="Retrieved estimation evidence")
        for source_ref in source_refs
    ]


def verify_citations(citations: list[EvidenceCitation], source_refs: list[str]) -> CitationVerificationReport:
    available = set(source_refs)
    dangling = [citation.chunk_id for citation in citations if citation.chunk_id not in available]
    return CitationVerificationReport(
        verified=bool(citations) and not dangling,
        verified_citations=[citation for citation in citations if citation.chunk_id in available],
        dangling_chunk_ids=dangling,
        abstained=not citations,
    )


def synthesize_competing_estimates(hours: list[float], *, minimum: float | None = None, maximum: float | None = None) -> dict[str, float]:
    if len(hours) < 2:
        raise ValueError("Competitive synthesis requires at least two independent estimates.")
    low = min(hours) if minimum is None else minimum
    high = max(hours) if maximum is None else maximum
    if low > high:
        raise ValueError("The lower bound cannot exceed the upper bound.")
    return {"low_hours": low, "high_hours": high, "recommended_hours": float(median(hours))}
