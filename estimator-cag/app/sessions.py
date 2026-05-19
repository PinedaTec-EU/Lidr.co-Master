from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path

from pydantic import BaseModel, Field

from app.config import settings


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
            assumed_team_size=assumed_team_size,
            mentioned_technologies=technologies,
            agreed_scope=transcript.strip()[:500] or self.agreed_scope,
        )


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
    history: ConversationHistory = field(default_factory=ConversationHistory)
    project_metadata: ProjectMetadata = field(default_factory=ProjectMetadata)
    document_sources: list[str] = field(default_factory=list)
    conversation_messages: list[dict[str, str]] = field(default_factory=list)

    def remember_document_sources(self, source_paths: list[str]) -> None:
        normalized_existing = {item for item in self.document_sources}
        for source_path in source_paths:
            if source_path not in normalized_existing:
                self.document_sources.append(source_path)
                normalized_existing.add(source_path)

    def add_conversation_message(self, role: str, content: str) -> None:
        self.conversation_messages.append({"role": role, "content": content})

    def to_dict(self) -> dict:
        return {
            "history": self.history.to_dict(),
            "project_metadata": self.project_metadata.model_dump(),
            "document_sources": self.document_sources,
            "conversation_messages": self.conversation_messages,
        }

    @classmethod
    def from_dict(cls, payload: dict) -> "Session":
        return cls(
            history=ConversationHistory.from_dict(payload.get("history", {})),
            project_metadata=ProjectMetadata.model_validate(payload.get("project_metadata", {})),
            document_sources=list(payload.get("document_sources", [])),
            conversation_messages=list(payload.get("conversation_messages", [])),
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

    def create(self, session_id: str) -> Session:
        session = Session()
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
