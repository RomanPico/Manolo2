"""SQLite FX cache repository."""

from __future__ import annotations

import aiosqlite


class SqliteFxCacheRepository:
    """FX rate cache."""

    def __init__(self, conn: aiosqlite.Connection) -> None:
        self._conn = conn

    async def get(self, pair: str) -> tuple[float, str] | None:
        """Return (rate, fetched_at) or None."""
        cur = await self._conn.execute(
            "SELECT rate, fetched_at FROM fx_cache WHERE pair = ?",
            (pair,),
        )
        row = await cur.fetchone()
        if row is None:
            return None
        return float(row[0]), str(row[1])

    async def set(self, pair: str, rate: float, fetched_at: str) -> None:
        """Upsert cache row."""
        await self._conn.execute(
            """
            INSERT INTO fx_cache (pair, rate, fetched_at)
            VALUES (?, ?, ?)
            ON CONFLICT(pair) DO UPDATE SET
                rate = excluded.rate,
                fetched_at = excluded.fetched_at
            """,
            (pair, rate, fetched_at),
        )
        await self._conn.commit()
