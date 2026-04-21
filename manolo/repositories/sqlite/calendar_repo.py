"""SQLite calendar_events repository."""

from __future__ import annotations

from typing import Any

import aiosqlite


class SqliteCalendarRepository:
    """Calendar events storage."""

    def __init__(self, conn: aiosqlite.Connection) -> None:
        self._conn = conn

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
        await self._conn.execute(
            """
            INSERT OR REPLACE INTO calendar_events
            (id, title, starts_at, ends_at, description, location, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (event_id, title, starts_at, ends_at, description, location, created_at),
        )
        await self._conn.commit()

    async def lookup(
        self,
        start_from: str | None,
        end_to: str | None,
        limit: int,
    ) -> list[dict[str, Any]]:
        """Return events in optional ISO range."""
        query = (
            "SELECT id, title, starts_at, ends_at, description, location, created_at "
            "FROM calendar_events WHERE 1=1"
        )
        params: list[Any] = []
        if start_from is not None:
            query += " AND starts_at >= ?"
            params.append(start_from)
        if end_to is not None:
            query += " AND starts_at <= ?"
            params.append(end_to)
        query += " ORDER BY starts_at ASC LIMIT ?"
        params.append(limit)
        cur = await self._conn.execute(query, tuple(params))
        rows = await cur.fetchall()
        return [
            {
                "id": str(r[0]),
                "title": str(r[1]),
                "starts_at": str(r[2]),
                "ends_at": r[3],
                "description": r[4],
                "location": r[5],
                "created_at": str(r[6]),
            }
            for r in rows
        ]

    async def erase(self, event_id: str) -> bool:
        """Delete by id; return True if deleted."""
        cur = await self._conn.execute("DELETE FROM calendar_events WHERE id = ?", (event_id,))
        await self._conn.commit()
        return cur.rowcount > 0
