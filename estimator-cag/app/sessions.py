from __future__ import annotations

from dataclasses import dataclass, field

from pydantic import BaseModel, Field


MAX_TURNS = 6


class ProjectMetadata(BaseModel):
    project_name: str | None = None
    assumed_team_size: int | None = Field(default=None, ge=1)
    mentioned_technologies: list[str] = Field(default_factory=list)
    agreed_scope: str | None = None


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


@dataclass
class Session:
    """
    Session state is intentionally process-local in this phase.

    The course only requires conversational continuity during a single app run,
    so accepting volatility keeps the implementation simple before adding
    persistence infrastructure in later phases.
    """

    history: ConversationHistory = field(default_factory=ConversationHistory)
    project_metadata: ProjectMetadata = field(default_factory=ProjectMetadata)


class SessionStore:
    def __init__(self) -> None:
        self._sessions: dict[str, Session] = {}

    def create(self, session_id: str) -> Session:
        session = Session()
        self._sessions[session_id] = session
        return session

    def get(self, session_id: str) -> Session | None:
        return self._sessions.get(session_id)

    def get_or_create(self, session_id: str) -> Session:
        session = self.get(session_id)
        if session is not None:
            return session
        return self.create(session_id)
