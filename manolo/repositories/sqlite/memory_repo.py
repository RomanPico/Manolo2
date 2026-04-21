"""SQLite memory_items repository."""

from __future__ import annotations

import aiosqlite


class SqliteMemoryRepository:
    """Plain KV memory."""

    def __init__(self, conn: aiosqlite.Connection) -> None:
        self._conn = conn

    async def upsert(
        self,
        item_id: str,
        key: str,
        tags: str | None,
        value_json: str,
        created_at: str,
    ) -> None:
        """Insert or replace."""
        await self._conn.execute(
            """
            INSERT OR REPLACE INTO memory_items (id, key, tags, value_json, created_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            (item_id, key, tags, value_json, created_at),
        )
        await self._conn.commit()

    async def get_by_key(self, key: str) -> str | None:
        """Return value_json or None."""
        cur = await self._conn.execute(
            "SELECT value_json FROM memory_items WHERE key = ? ORDER BY created_at DESC LIMIT 1",
            (key,),
        )
        row = await cur.fetchone()
        if row is None:
            return None
        return str(row[0])
