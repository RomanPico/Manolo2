"""SQLite conversations repository."""

from __future__ import annotations

import aiosqlite

from manolo.models.dto import ConversationOut


class SqliteConversationsRepository:
    """Conversations table access."""

    def __init__(self, conn: aiosqlite.Connection) -> None:
        self._conn = conn

    async def create(self, conversation_id: str, title: str | None, created_at: str) -> None:
        """Insert a conversation."""
        await self._conn.execute(
            "INSERT INTO conversations (id, title, created_at) VALUES (?, ?, ?)",
            (conversation_id, title, created_at),
        )
        await self._conn.commit()

    async def list_all(self) -> list[ConversationOut]:
        """Return all conversations."""
        cur = await self._conn.execute(
            "SELECT id, title, created_at FROM conversations ORDER BY created_at DESC",
        )
        rows = await cur.fetchall()
        return [
            ConversationOut(id=str(r[0]), title=r[1], created_at=str(r[2]))
            for r in rows
        ]

    async def get(self, conversation_id: str) -> ConversationOut | None:
        """Return one conversation or None."""
        cur = await self._conn.execute(
            "SELECT id, title, created_at FROM conversations WHERE id = ?",
            (conversation_id,),
        )
        row = await cur.fetchone()
        if row is None:
            return None
        return ConversationOut(id=str(row[0]), title=row[1], created_at=str(row[2]))
