"""CalendarService erase."""

from __future__ import annotations

import uuid

import pytest

from manolo.repositories.sqlite.calendar_repo import SqliteCalendarRepository
from manolo.services.calendar_service import CalendarService


@pytest.mark.asyncio
async def test_erase_true(sqlite_conn) -> None:
    """erase returns True when row removed."""
    cal = SqliteCalendarRepository(sqlite_conn)
    svc = CalendarService(cal)
    eid = str(uuid.uuid4())
    await cal.save_event(
        eid,
        "X",
        "2025-01-01T10:00:00+00:00",
        None,
        None,
        None,
        "2025-01-01T09:00:00+00:00",
    )
    assert await svc.erase(eid) is True


@pytest.mark.asyncio
async def test_calendar_tool_erase_ok(sqlite_conn) -> None:
    """calendar_tool erase success."""
    from manolo.tools.calendar_tool import CalendarTool

    cal = SqliteCalendarRepository(sqlite_conn)
    svc = CalendarService(cal)
    tool = CalendarTool(svc)
    saved = await tool.execute(
        {
            "action": "save",
            "title": "t",
            "starts_at": "2025-01-01T10:00:00+00:00",
        },
    )
    eid = str(saved["data"]["event_id"])
    out = await tool.execute({"action": "erase", "event_id": eid})
    assert out["ok"] is True
