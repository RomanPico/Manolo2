"""Calendar lookup with date filters."""

from __future__ import annotations

import uuid

import pytest

from manolo.repositories.sqlite.calendar_repo import SqliteCalendarRepository


@pytest.mark.asyncio
async def test_lookup_with_start_and_end(sqlite_conn) -> None:
    """Both start_from and end_to apply."""
    cal = SqliteCalendarRepository(sqlite_conn)
    eid = str(uuid.uuid4())
    await cal.save_event(
        eid,
        "Mid",
        "2025-06-15T12:00:00+00:00",
        None,
        None,
        None,
        "2025-06-01T00:00:00+00:00",
    )
    rows = await cal.lookup("2025-06-01T00:00:00+00:00", "2025-06-30T00:00:00+00:00", 10)
    assert len(rows) == 1
