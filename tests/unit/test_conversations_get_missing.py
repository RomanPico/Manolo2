"""Conversations get missing id."""

from __future__ import annotations

import pytest

from manolo.repositories.sqlite.conversations_repo import SqliteConversationsRepository


@pytest.mark.asyncio
async def test_get_missing_returns_none(sqlite_conn) -> None:
    """Unknown id returns None."""
    repo = SqliteConversationsRepository(sqlite_conn)
    assert await repo.get("00000000-0000-0000-0000-000000000000") is None
