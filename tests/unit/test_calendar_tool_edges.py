"""Calendar tool edge cases."""

from __future__ import annotations

import pytest

from manolo.repositories.sqlite.calendar_repo import SqliteCalendarRepository
from manolo.services.calendar_service import CalendarService
from manolo.tools.calendar_tool import CalendarTool


@pytest.mark.asyncio
async def test_calendar_save_missing_fields(sqlite_conn) -> None:
    """save without required fields."""
    tool = CalendarTool(CalendarService(SqliteCalendarRepository(sqlite_conn)))
    out = await tool.execute({"action": "save", "title": "x"})
    assert out["ok"] is False


@pytest.mark.asyncio
async def test_calendar_erase_missing_id(sqlite_conn) -> None:
    """erase without event_id."""
    tool = CalendarTool(CalendarService(SqliteCalendarRepository(sqlite_conn)))
    out = await tool.execute({"action": "erase"})
    assert out["ok"] is False


@pytest.mark.asyncio
async def test_calendar_unknown_action(sqlite_conn) -> None:
    """Unknown action string."""
    tool = CalendarTool(CalendarService(SqliteCalendarRepository(sqlite_conn)))
    out = await tool.execute({"action": "nope"})
    assert out["ok"] is False
