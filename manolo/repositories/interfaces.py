"""Repository protocols (ports)."""

from __future__ import annotations

from typing import Any, Protocol

from manolo.models import dto as dto_mod


class ConversationsRepository(Protocol):
    """Persist conversations."""

    async def create(self, conversation_id: str, title: str | None, created_at: str) -> None:
        """Insert a conversation."""

    async def list_all(self) -> list[dto_mod.ConversationOut]:
        """Return all conversations."""

    async def get(self, conversation_id: str) -> dto_mod.ConversationOut | None:
        """Return one conversation or None."""


class MessagesRepository(Protocol):
    """Persist chat messages."""

    async def append(
        self,
        message_id: str,
        conversation_id: str,
        role: str,
        content: str,
        tool_call_id: str | None,
        created_at: str,
    ) -> None:
        """Append a message."""

    async def list_for_conversation(self, conversation_id: str) -> list[dto_mod.MessageOut]:
        """Messages ordered by created_at."""


class RunsRepository(Protocol):
    """Persist orchestration runs."""

    async def create(
        self,
        run_id: str,
        conversation_id: str,
        status: str,
        started_at: str,
    ) -> None:
        """Create a run row."""

    async def finalize(
        self,
        run_id: str,
        status: str,
        final_answer: str | None,
        last_error: str | None,
        ended_at: str,
    ) -> None:
        """Set final state."""


class RunStepsRepository(Protocol):
    """Persist run steps for traceability."""

    async def append(
        self,
        step_id: str,
        run_id: str,
        idx: int,
        kind: str,
        payload_json: str,
        created_at: str,
    ) -> None:
        """Append a step."""


class CalendarRepository(Protocol):
    """Calendar event storage."""

    async def save_event(
        self,
        event_id: str,
        title: str,
        starts_at: str,
        ends_at: str | None,
        description: str | None,
        location: str | None,
        created_at: str,
    ) -> None:
        """Insert or replace an event."""

    async def lookup(
        self,
        start_from: str | None,
        end_to: str | None,
        limit: int,
    ) -> list[dict[str, Any]]:
        """Return events in range."""

    async def erase(self, event_id: str) -> bool:
        """Delete by id; return True if deleted."""


class FxCacheRepository(Protocol):
    """Optional FX rate cache."""

    async def get(self, pair: str) -> tuple[float, str] | None:
        """Return (rate, fetched_at) or None."""

    async def set(self, pair: str, rate: float, fetched_at: str) -> None:
        """Upsert cache row."""


class MemoryRepository(Protocol):
    """Plain KV memory."""

    async def upsert(
        self,
        item_id: str,
        key: str,
        tags: str | None,
        value_json: str,
        created_at: str,
    ) -> None:
        """Insert or replace."""

    async def get_by_key(self, key: str) -> str | None:
        """Return value_json or None."""
