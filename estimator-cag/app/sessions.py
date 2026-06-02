from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, Field

from app.config import settings
from app.schemas import UserTier


MAX_TURNS = 6
KNOWN_TECHNOLOGIES = (
    "react",
    "next.js",
    "node",
    "python",
    "fastapi",
    "django",
    "postgresql",
    "mysql",
    "mongodb",
    "redis",
    "docker",
    "kubernetes",
    "aws",
    "azure",
    "gcp",
    "stripe",
)


class ProjectMetadata(BaseModel):
    project_name: str | None = None
    client_name: str | None = None
    assumed_team_size: int | None = Field(default=None, ge=1)
    mentioned_technologies: list[str] = Field(default_factory=list)
    agreed_scope: str | None = None

    def merge_from_interaction(self, transcript: str, response_text: str) -> "ProjectMetadata":
        merged_text = f"{transcript}\n{response_text}"
        lower_text = merged_text.lower()

        project_name = self.project_name
        if project_name is None:
            for marker in ("proyecto ", "project "):
                index = lower_text.find(marker)
                if index >= 0:
                    candidate = merged_text[index + len(marker) :].splitlines()[0].strip(" :.-")
                    if candidate:
                        project_name = candidate[:80]
                        break

        client_name = self.client_name
        if client_name is None:
            for marker in ("cliente ", "client "):
                index = lower_text.find(marker)
                if index >= 0:
                    candidate = merged_text[index + len(marker) :].splitlines()[0].strip(" :.-")
                    if candidate:
                        client_name = candidate[:80]
                        break

        assumed_team_size = self.assumed_team_size
        if assumed_team_size is None:
            import re

            team_match = re.search(r"equipo\s+de\s+(\d+)", lower_text)
            if team_match:
                assumed_team_size = int(team_match.group(1))

        technologies = list(self.mentioned_technologies)
        seen = {item.lower() for item in technologies}
        for technology in KNOWN_TECHNOLOGIES:
            if technology in lower_text and technology not in seen:
                technologies.append(technology)
                seen.add(technology)

        return ProjectMetadata(
            project_name=project_name,
            client_name=client_name,
            assumed_team_size=assumed_team_size,
            mentioned_technologies=technologies,
            agreed_scope=transcript.strip()[:500] or self.agreed_scope,
        )


class ExternalContextItem(BaseModel):
    source: str
    title: str
    content: str
    url: str | None = None
    updated_at: str | None = None
    relevance_reason: str | None = None


class ExternalContextConfig(BaseModel):
    notion_page_ids: list[str] = Field(default_factory=list)
    notion_search_terms: list[str] = Field(default_factory=list)


class TurnObservation(BaseModel):
    turn_index: int = Field(ge=1)
    session_id: str
    enriched_transcript_chars: int = Field(ge=0)
    attachments_total_chars: int = Field(ge=0)
    messages_in_window: int = Field(ge=0)
    anchors_count: int = Field(ge=0)
    summary_chars: int = Field(ge=0)
    tokens_in: int = Field(ge=0)
    tokens_out: int = Field(ge=0)
    cost_usd: float = Field(ge=0.0)
    latency_ms: float = Field(ge=0.0)
    cache_hit_kind: Literal["none", "exact", "semantic"] = "none"
    last_resolved_tier: UserTier
    model: str = ""
    provider: str = ""
    project_metadata: dict = Field(default_factory=dict)
    assistant_text: str = ""
    summary_text: str = ""
    anchors: list[str] = Field(default_factory=list)
    transcript_excerpt: str = ""


@dataclass
class ConversationHistory:
    max_turns: int = MAX_TURNS
    turns: list[tuple[str, str]] = field(default_factory=list)

    def add_turn(self, user_message: str, assistant_message: str) -> None:
        self.turns.append((user_message, assistant_message))
        if len(self.turns) > self.max_turns:
            overflow = len(self.turns) - self.max_turns
            del self.turns[:overflow]

    def to_messages_list(self, system_prompt: str) -> list[dict[str, str]]:
        messages = [{"role": "system", "content": system_prompt}]
        for user_message, assistant_message in self.turns:
            messages.append({"role": "user", "content": user_message})
            messages.append({"role": "assistant", "content": assistant_message})
        return messages

    def to_turn_messages(self) -> list[dict[str, str]]:
        messages: list[dict[str, str]] = []
        for user_message, assistant_message in self.turns:
            messages.append({"role": "user", "content": user_message})
            messages.append({"role": "assistant", "content": assistant_message})
        return messages

    def to_dict(self) -> dict:
        return {"max_turns": self.max_turns, "turns": self.turns}

    @classmethod
    def from_dict(cls, payload: dict) -> "ConversationHistory":
        return cls(
            max_turns=int(payload.get("max_turns", MAX_TURNS)),
            turns=[(user, assistant) for user, assistant in payload.get("turns", [])],
        )


@dataclass
class Session:
    user_tier: UserTier | None = None
    user_display_name: str | None = None
    history: ConversationHistory = field(default_factory=ConversationHistory)
    project_metadata: ProjectMetadata = field(default_factory=ProjectMetadata)
    external_context_config: ExternalContextConfig = field(default_factory=ExternalContextConfig)
    document_sources: list[str] = field(default_factory=list)
    conversation_messages: list[dict[str, str]] = field(default_factory=list)
    last_document_context: list[str] = field(default_factory=list)
    last_external_context: list[dict] = field(default_factory=list)
    last_run_info: dict = field(
        default_factory=lambda: {
            "provider": "",
            "model": "",
            "tokens_used": {"prompt": 0, "completion": 0, "total": 0},
            "response_time": 0.0,
        }
    )
    turn_observations: list[dict] = field(default_factory=list)
    last_tier_rule: str = "session_profile_locked"

    def remember_document_sources(self, source_paths: list[str]) -> None:
        normalized_existing = {item for item in self.document_sources}
        for source_path in source_paths:
            if source_path not in normalized_existing:
                self.document_sources.append(source_path)
                normalized_existing.add(source_path)

    def add_conversation_message(self, role: str, content: str) -> None:
        self.conversation_messages.append({"role": role, "content": content})

    def set_user_profile(self, user_tier: UserTier, user_display_name: str) -> None:
        self.user_tier = user_tier
        self.user_display_name = user_display_name.strip()

    def set_external_context_config(
        self,
        *,
        notion_page_ids: list[str],
        notion_search_terms: list[str],
    ) -> None:
        self.external_context_config = ExternalContextConfig(
            notion_page_ids=notion_page_ids,
            notion_search_terms=notion_search_terms,
        )

    def set_last_document_context(self, sections: list[str]) -> None:
        self.last_document_context = list(sections)

    def set_last_external_context(self, items: list[ExternalContextItem]) -> None:
        self.last_external_context = [item.model_dump() for item in items]

    def set_last_run_info(
        self,
        *,
        provider: str,
        model: str,
        tokens_used: dict,
        response_time: float,
    ) -> None:
        self.last_run_info = {
            "provider": provider,
            "model": model,
            "tokens_used": tokens_used,
            "response_time": response_time,
        }

    def add_turn_observation(self, observation: TurnObservation) -> None:
        self.turn_observations.append(observation.model_dump())

    def last_turn_observed(self) -> dict | None:
        if not self.turn_observations:
            return None
        return self.turn_observations[-1]

    def message_count(self) -> int:
        return len(self.conversation_messages)

    def to_dict(self) -> dict:
        return {
            "user_tier": self.user_tier.value if self.user_tier else None,
            "user_display_name": self.user_display_name,
            "history": self.history.to_dict(),
            "project_metadata": self.project_metadata.model_dump(),
            "external_context_config": self.external_context_config.model_dump(),
            "document_sources": self.document_sources,
            "conversation_messages": self.conversation_messages,
            "last_document_context": self.last_document_context,
            "last_external_context": self.last_external_context,
            "last_run_info": self.last_run_info,
            "turn_observations": self.turn_observations,
            "last_tier_rule": self.last_tier_rule,
        }

    @classmethod
    def from_dict(cls, payload: dict) -> "Session":
        return cls(
            user_tier=(
                UserTier(payload["user_tier"])
                if payload.get("user_tier")
                else None
            ),
            user_display_name=payload.get("user_display_name"),
            history=ConversationHistory.from_dict(payload.get("history", {})),
            project_metadata=ProjectMetadata.model_validate(payload.get("project_metadata", {})),
            external_context_config=ExternalContextConfig.model_validate(
                payload.get("external_context_config", {})
            ),
            document_sources=list(payload.get("document_sources", [])),
            conversation_messages=list(payload.get("conversation_messages", [])),
            last_document_context=list(payload.get("last_document_context", [])),
            last_external_context=list(payload.get("last_external_context", [])),
            last_run_info=dict(
                payload.get(
                    "last_run_info",
                    {
                        "provider": "",
                        "model": "",
                        "tokens_used": {"prompt": 0, "completion": 0, "total": 0},
                        "response_time": 0.0,
                    },
                )
            ),
            turn_observations=list(payload.get("turn_observations", [])),
            last_tier_rule=payload.get("last_tier_rule", "session_profile_locked"),
        )


class SessionStore:
    def __init__(self, path: str | Path | None = None) -> None:
        self._path = Path(path or settings.session_store_path)
        self._sessions: dict[str, Session] = {}
        self._load()

    def _load(self) -> None:
        if not self._path.exists():
            return

        payload = json.loads(self._path.read_text(encoding="utf-8"))
        self._sessions = {
            session_id: Session.from_dict(session_payload)
            for session_id, session_payload in payload.items()
        }

    def _save(self) -> None:
        self._path.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            session_id: session.to_dict()
            for session_id, session in self._sessions.items()
        }
        self._path.write_text(
            json.dumps(payload, ensure_ascii=True, indent=2),
            encoding="utf-8",
        )

    def create(
        self,
        session_id: str,
        user_tier: UserTier | None = None,
        user_display_name: str | None = None,
    ) -> Session:
        session = Session(user_tier=user_tier, user_display_name=user_display_name)
        self._sessions[session_id] = session
        self._save()
        return session

    def get(self, session_id: str) -> Session | None:
        return self._sessions.get(session_id)

    def get_or_create(self, session_id: str) -> Session:
        session = self.get(session_id)
        if session is not None:
            return session
        return self.create(session_id)

    def save_session(self, session_id: str) -> None:
        if session_id not in self._sessions:
            raise KeyError(session_id)
        self._save()
