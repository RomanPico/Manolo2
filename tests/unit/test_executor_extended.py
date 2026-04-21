"""ToolExecutor edge cases."""

from __future__ import annotations

import asyncio
from typing import Any

import pytest

from manolo.tools.base import Tool
from manolo.tools.executor import ToolExecutor


class _EchoTool(Tool):
    name = "echo"
    description = "echo"
    input_schema = {"type": "object", "properties": {"x": {"type": "integer"}}, "required": ["x"]}

    async def execute(self, arguments: dict[str, Any]) -> dict[str, Any]:
        return {"ok": True, "x": arguments["x"]}


class _SlowTool(Tool):
    name = "slow"
    description = "slow"
    input_schema = {"type": "object", "properties": {}, "required": []}

    async def execute(self, arguments: dict[str, Any]) -> dict[str, Any]:
        await asyncio.sleep(5)
        return {"ok": True}


@pytest.mark.asyncio
async def test_executor_runs_tool() -> None:
    """Happy path."""
    ex = ToolExecutor({"echo": _EchoTool()}, allowed={"echo"})
    out = await ex.run("echo", '{"x": 1}')
    assert out["ok"] is True


@pytest.mark.asyncio
async def test_executor_invalid_json() -> None:
    """Bad JSON."""
    ex = ToolExecutor({"echo": _EchoTool()}, allowed={"echo"})
    out = await ex.run("echo", "{")
    assert out["ok"] is False


@pytest.mark.asyncio
async def test_executor_not_dict_json() -> None:
    """JSON must be object."""
    ex = ToolExecutor({"echo": _EchoTool()}, allowed={"echo"})
    out = await ex.run("echo", "[1]")
    assert out["ok"] is False


@pytest.mark.asyncio
async def test_executor_schema_error() -> None:
    """Schema validation failure."""
    ex = ToolExecutor({"echo": _EchoTool()}, allowed={"echo"})
    out = await ex.run("echo", "{}")
    assert out["ok"] is False


@pytest.mark.asyncio
async def test_executor_timeout() -> None:
    """Tool timeout."""
    ex = ToolExecutor({"slow": _SlowTool()}, allowed={"slow"}, timeout_seconds=0.01)
    out = await ex.run("slow", "{}")
    assert out["ok"] is False


@pytest.mark.asyncio
async def test_executor_unknown_tool_allowed_but_missing() -> None:
    """Allowed name but not registered in tools map."""
    ex = ToolExecutor({}, allowed={"ghost"})
    out = await ex.run("ghost", "{}")
    assert out["ok"] is False
    assert "unknown tool" in str(out["error"])


@pytest.mark.asyncio
async def test_executor_tool_raises() -> None:
    """Tool raises exception."""

    class _Bad(Tool):
        name = "bad"
        description = "bad"
        input_schema = {"type": "object", "properties": {}, "required": []}

        async def execute(self, arguments: dict[str, Any]) -> dict[str, Any]:
            msg = "boom"
            raise RuntimeError(msg)

    ex = ToolExecutor({"bad": _Bad()}, allowed={"bad"})
    out = await ex.run("bad", "{}")
    assert out["ok"] is False
