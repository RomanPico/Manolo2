"""Calendar repo erase edge cases."""

from __future__ import annotations

import uuid

import pytest

from manolo.repositories.sqlite.calendar_repo import SqliteCalendarRepository


@pytest.mark.asyncio
async def test_calendar_erase_missing_returns_false(sqlite_conn) -> None:
    """Deleting missing id returns False."""
    cal = SqliteCalendarRepository(sqlite_conn)
    assert await cal.erase(str(uuid.uuid4())) is False
