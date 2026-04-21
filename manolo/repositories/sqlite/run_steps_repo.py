"""SQLite run_steps repository."""

from __future__ import annotations

import aiosqlite


class SqliteRunStepsRepository:
    """Run steps table access."""

    def __init__(self, conn: aiosqlite.Connection) -> None:
        self._conn = conn

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
        await self._conn.execute(
            """
            INSERT INTO run_steps (id, run_id, idx, kind, payload_json, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (step_id, run_id, idx, kind, payload_json, created_at),
        )
        await self._conn.commit()
