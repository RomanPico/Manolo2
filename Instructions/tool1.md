# Calendar Tool

## Purpose

The calendar tool is responsible for managing local calendar events.

It supports three operations:

- save an event
- look up events
- erase an event

This tool should not know anything about SQLite directly.  
Storage must live behind a repository or service adapter.

---

## Tool Name

`calendar_tool`

---

## Responsibilities

The calendar tool should:

- validate the requested action
- validate the required fields for that action
- delegate business logic to a calendar service
- return a normalized response

It should **not**:

- run raw SQL
- know table names
- know database connection details
- contain orchestration logic

---

## Supported Actions

- `save`
- `lookup`
- `erase`

---

## Input Schema

```python id="b8g0mm"
{
    "type": "object",
    "properties": {
        "action": {
            "type": "string",
            "enum": ["save", "lookup", "erase"]
        },
        "title": {"type": "string"},
        "starts_at": {"type": "string"},
        "ends_at": {"type": "string"},
        "description": {"type": "string"},
        "location": {"type": "string"},
        "event_id": {"type": "string"},
        "start_from": {"type": "string"},
        "end_to": {"type": "string"},
        "limit": {"type": "integer"}
    },
    "required": ["action"]
}