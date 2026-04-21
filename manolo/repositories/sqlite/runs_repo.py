"""SQLite runs repository."""

from __future__ import annotations

import aiosqlite


class SqliteRunsRepository:
    """Runs table access."""

    def __init__(self, conn: aiosqlite.Connection) -> None:
        self._conn = conn

    async def create(
        self,
        run_id: str,
        conversation_id: str,
        status: str,
        started_at: str,
    ) -> None:
        """Create a run row."""
        await self._conn.execute(
            """
            INSERT INTO runs (id, conversation_id, status, started_at)
            VALUES (?, ?, ?, ?)
            """,
            (run_id, conversation_id, status, started_at),
        )
        await self._conn.commit()

    async def finalize(
        self,
        run_id: str,
        status: str,
        final_answer: str | None,
        last_error: str | None,
        ended_at: str,
    ) -> None:
        """Set final state."""
        await self._conn.execute(
            """
            UPDATE runs
            SET status = ?, final_answer = ?, last_error = ?, ended_at = ?
            WHERE id = ?
            """,
            (status, final_answer, last_error, ended_at, run_id),
        )
        await self._conn.commit()
