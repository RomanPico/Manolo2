"""Calendar tool HTTP facade."""

from __future__ import annotations

from fastapi import APIRouter, Request

from manolo.models.dto import CalendarToolRequest, CalendarToolResponse
from manolo.tools.calendar_tool import CalendarTool

router = APIRouter(prefix="/tools/calendar", tags=["tools"])


@router.post("")
async def calendar_tool_endpoint(
    request: Request,
    body: CalendarToolRequest,
) -> CalendarToolResponse:
    """Invoke calendar_tool."""
    tool = CalendarTool(request.app.state.calendar_service)
    payload = body.model_dump(exclude_none=True)
    result = await tool.execute(payload)
    ok = bool(result.get("ok"))
    action = str(result.get("action") or body.action)
    data = result.get("data") if isinstance(result.get("data"), dict) else {}
    err = result.get("error")
    return CalendarToolResponse(
        ok=ok,
        action=action,
        data=data,
        error=str(err) if err is not None else None,
    )
