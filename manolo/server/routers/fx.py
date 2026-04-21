"""USD price tool HTTP facade."""

from __future__ import annotations

from fastapi import APIRouter, Request

from manolo.models.dto import FxToolResponse
from manolo.tools.usd_price_tool import UsdPriceTool

router = APIRouter(prefix="/tools/fx", tags=["tools"])


@router.get("/usd")
async def usd_price(request: Request) -> FxToolResponse:
    """Invoke usd_price_tool.get_price."""
    tool = UsdPriceTool(request.app.state.fx_service)
    result = await tool.execute({"action": "get_price"})
    data = result.get("data") if isinstance(result.get("data"), dict) else {}
    ok = bool(result.get("ok"))
    if not ok:
        return FxToolResponse(ok=False, pair="USD_EUR", error=str(result.get("error") or "unknown"))
    return FxToolResponse(
        ok=True,
        pair=str(data.get("pair") or "USD_EUR"),
        rate=float(data["rate"]) if data.get("rate") is not None else None,
        fetched_at=str(data["fetched_at"]) if data.get("fetched_at") else None,
        cached=bool(data.get("cached")),
    )
