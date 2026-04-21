"""calendar_tool implementation."""

from __future__ import annotations

from typing import Any

from manolo.services.calendar_service import CalendarService
from manolo.tools.base import Tool

CALENDAR_INPUT_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "action": {"type": "string", "enum": ["save", "lookup", "erase"]},
        "title": {"type": "string"},
        "starts_at": {"type": "string"},
        "ends_at": {"type": "string"},
        "description": {"type": "string"},
        "location": {"type": "string"},
        "event_id": {"type": "string"},
        "start_from": {"type": "string"},
        "end_to": {"type": "string"},
        "limit": {"type": "integer"},
    },
    "required": ["action"],
}


class CalendarTool(Tool):
    """Local calendar CRUD."""

    name = "calendar_tool"
    description = "Manage local calendar events (save, lookup, erase)."
    input_schema = CALENDAR_INPUT_SCHEMA

    def __init__(self, service: CalendarService) -> None:
        self._service = service

    async def execute(self, arguments: dict[str, Any]) -> dict[str, Any]:
        """Dispatch by action."""
        action = str(arguments["action"])
        if action == "save":
            title = arguments.get("title")
            starts_at = arguments.get("starts_at")
            if not title or not starts_at:
                return {"ok": False, "action": action, "error": "save requires title and starts_at"}
            data = await self._service.save(
                title=str(title),
                starts_at=str(starts_at),
                ends_at=str(arguments["ends_at"]) if arguments.get("ends_at") else None,
                description=str(arguments["description"]) if arguments.get("description") else None,
                location=str(arguments["location"]) if arguments.get("location") else None,
            )
            return {"ok": True, "action": action, "data": data}
        if action == "lookup":
            limit = int(arguments.get("limit") or 50)
            rows = await self._service.lookup(
                start_from=str(arguments["start_from"]) if arguments.get("start_from") else None,
                end_to=str(arguments["end_to"]) if arguments.get("end_to") else None,
                limit=limit,
            )
            return {"ok": True, "action": action, "data": {"events": rows}}
        if action == "erase":
            event_id = arguments.get("event_id")
            if not event_id:
                return {"ok": False, "action": action, "error": "erase requires event_id"}
            deleted = await self._service.erase(str(event_id))
            return {"ok": deleted, "action": action, "data": {"deleted": deleted}}
        return {"ok": False, "action": action, "error": f"unknown action: {action}"}
