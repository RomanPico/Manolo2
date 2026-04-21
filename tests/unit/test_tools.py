"""Tool unit tests."""

from __future__ import annotations

import pytest

from manolo.repositories.sqlite.calendar_repo import SqliteCalendarRepository
from manolo.repositories.sqlite.fx_cache_repo import SqliteFxCacheRepository
from manolo.services.calendar_service import CalendarService
from manolo.services.fx_service import FxService
from manolo.providers.fx_http_provider import FxHttpProvider
from manolo.tools.calendar_tool import CalendarTool
from manolo.tools.executor import ToolExecutor
from manolo.tools.usd_price_tool import UsdPriceTool
import httpx
import respx


@pytest.mark.asyncio
async def test_calendar_tool_save_and_lookup(sqlite_conn) -> None:
    """calendar_tool saves and lists."""
    cal = CalendarService(SqliteCalendarRepository(sqlite_conn))
    tool = CalendarTool(cal)
    out = await tool.execute(
        {
            "action": "save",
            "title": "A",
            "starts_at": "2025-06-01T12:00:00+00:00",
        },
    )
    assert out["ok"] is True
    out2 = await tool.execute({"action": "lookup", "limit": 5})
    assert out2["ok"] is True
    assert len(out2["data"]["events"]) == 1


@pytest.mark.asyncio
async def test_tool_executor_blocks_unknown() -> None:
    """Executor rejects unknown tools."""
    ex = ToolExecutor({}, allowed={"a"})
    res = await ex.run("nope", "{}")
    assert res["ok"] is False


@pytest.mark.asyncio
@respx.mock
async def test_usd_price_tool(sqlite_conn) -> None:
    """usd_price_tool hits API when cache empty."""
    respx.get("https://open.er-api.com/v6/latest/USD").mock(
        return_value=httpx.Response(
            200,
            json={
                "result": "success",
                "base_code": "USD",
                "rates": {"EUR": 0.91},
            },
        ),
    )
    async with httpx.AsyncClient() as client:
        fx = FxService(SqliteFxCacheRepository(sqlite_conn), FxHttpProvider(client, "https://open.er-api.com/v6/latest/USD"))
        tool = UsdPriceTool(fx)
        out = await tool.execute({"action": "get_price"})
        assert out["ok"] is True
        assert out["data"]["rate"] == 0.91
