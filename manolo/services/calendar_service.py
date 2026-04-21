"""Calendar domain service."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from manolo.repositories.interfaces import CalendarRepository


class CalendarService:
    """Business logic for calendar events."""

    def __init__(self, repo: CalendarRepository) -> None:
        self._repo = repo

    def _now_iso(self) -> str:
        return datetime.now(timezone.utc).replace(microsecond=0).isoformat()

    async def save(
        self,
        *,
        title: str,
        starts_at: str,
        ends_at: str | None,
        description: str | None,
        location: str | None,
    ) -> dict[str, Any]:
        """Create a new event."""
        event_id = str(uuid.uuid4())
        created_at = self._now_iso()
        await self._repo.save_event(
            event_id=event_id,
            title=title,
            starts_at=starts_at,
            ends_at=ends_at,
            description=description,
            location=location,
            created_at=created_at,
        )
        return {"event_id": event_id, "created_at": created_at}

    async def lookup(
        self,
        *,
        start_from: str | None,
        end_to: str | None,
        limit: int,
    ) -> list[dict[str, Any]]:
        """List events in range."""
        lim = max(1, min(limit, 500))
        return await self._repo.lookup(start_from, end_to, lim)

    async def erase(self, event_id: str) -> bool:
        """Delete an event."""
        return await self._repo.erase(event_id)
