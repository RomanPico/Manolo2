"""Build tool registry from services."""

from __future__ import annotations

from manolo.services.calendar_service import CalendarService
from manolo.services.fx_service import FxService
from manolo.tools.base import Tool
from manolo.tools.calendar_tool import CalendarTool
from manolo.tools.usd_price_tool import UsdPriceTool


def build_default_tools(
    calendar: CalendarService,
    fx: FxService,
) -> dict[str, Tool]:
    """All built-in tools keyed by name."""
    cal = CalendarTool(calendar)
    usd = UsdPriceTool(fx)
    return {
        cal.name: cal,
        usd.name: usd,
    }
