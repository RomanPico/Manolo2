"""SQLite messages repository."""

from __future__ import annotations

import aiosqlite

from manolo.models.dto import MessageOut


class SqliteMessagesRepository:
    """Messages table access."""

    def __init__(self, conn: aiosqlite.Connection) -> None:
        self._conn = conn

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
        await self._conn.execute(
            """
            INSERT INTO messages (id, conversation_id, role, content, tool_call_id, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (message_id, conversation_id, role, content, tool_call_id, created_at),
        )
        await self._conn.commit()

    async def list_for_conversation(self, conversation_id: str) -> list[MessageOut]:
        """Messages ordered by created_at."""
        cur = await self._conn.execute(
            """
            SELECT id, conversation_id, role, content, tool_call_id, created_at
            FROM messages
            WHERE conversation_id = ?
            ORDER BY created_at ASC
            """,
            (conversation_id,),
        )
        rows = await cur.fetchall()
        return [
            MessageOut(
                id=str(r[0]),
                conversation_id=str(r[1]),
                role=str(r[2]),
                content=str(r[3]),
                tool_call_id=r[4],
                created_at=str(r[5]),
            )
            for r in rows
        ]
