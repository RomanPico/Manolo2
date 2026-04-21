"""Execute tools with policy checks."""

from __future__ import annotations

import asyncio
import json
from typing import Any

from manolo.tools.base import Tool, validate_schema


class ToolExecutor:
    """Routes tool calls to implementations."""

    def __init__(
        self,
        tools: dict[str, Tool],
        *,
        allowed: set[str],
        timeout_seconds: float = 60.0,
    ) -> None:
        self._tools = tools
        self._allowed = allowed
        self._timeout = timeout_seconds

    async def run(self, name: str, arguments_json: str) -> dict[str, Any]:
        """Parse JSON args, validate schema, execute tool."""
        if name not in self._allowed:
            return {"ok": False, "error": f"tool not allowed: {name}"}
        tool = self._tools.get(name)
        if tool is None:
            return {"ok": False, "error": f"unknown tool: {name}"}
        try:
            args = json.loads(arguments_json) if arguments_json.strip() else {}
        except json.JSONDecodeError as exc:
            return {"ok": False, "error": f"invalid tool arguments JSON: {exc}"}
        if not isinstance(args, dict):
            return {"ok": False, "error": "tool arguments must be a JSON object"}
        try:
            validate_schema(args, tool.input_schema)
        except Exception as exc:  # noqa: BLE001 - jsonschema errors
            return {"ok": False, "error": f"schema validation failed: {exc}"}
        try:
            return await asyncio.wait_for(tool.execute(args), timeout=self._timeout)
        except asyncio.TimeoutError:
            return {"ok": False, "error": "tool execution timed out"}
        except Exception as exc:  # noqa: BLE001
            return {"ok": False, "error": str(exc)}
