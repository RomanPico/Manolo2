"""usd_price_tool implementation."""

from __future__ import annotations

from typing import Any

from manolo.services.fx_service import FxService
from manolo.tools.base import Tool

USD_PRICE_INPUT_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {"action": {"type": "string", "enum": ["get_price"]}},
    "required": ["action"],
}


class UsdPriceTool(Tool):
    """Fetch USD reference FX via external API."""

    name = "usd_price_tool"
    description = "Get a USD-based FX reference rate (EUR cross), with optional cache."
    input_schema = USD_PRICE_INPUT_SCHEMA

    def __init__(self, fx: FxService) -> None:
        self._fx = fx

    async def execute(self, arguments: dict[str, Any]) -> dict[str, Any]:
        """Return FX snapshot."""
        _ = arguments
        data = await self._fx.get_usd_reference()
        return {"ok": True, "action": "get_price", "data": data}
