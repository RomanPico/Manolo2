"""Additional context_builder coverage."""

from __future__ import annotations

import json

import pytest

from manolo.models.dto import MessageOut
from manolo.orchestrator import context_builder as cb


def test_history_invalid_json_falls_back() -> None:
    """Malformed JSON assistant message falls back to plain assistant."""
    msgs = [
        MessageOut(
            id="1",
            conversation_id="c",
            role="assistant",
            content='{"tool_calls":',
            tool_call_id=None,
            created_at="t",
        ),
    ]
    out = cb.history_to_chat(msgs)
    assert len(out) == 1
    assert out[0].content == '{"tool_calls":'


def test_history_tool_calls_not_list_falls_back() -> None:
    """tool_calls not a list uses plain assistant path."""
    msgs = [
        MessageOut(
            id="1",
            conversation_id="c",
            role="assistant",
            content=json.dumps({"tool_calls": "nope", "text": None}),
            tool_call_id=None,
            created_at="t",
        ),
    ]
    out = cb.history_to_chat(msgs)
    assert len(out) == 1


def test_helpers_smoke() -> None:
    """Small helper constructors."""
    u = cb.append_user("hi")
    assert u.content == "hi"
    a = cb.assistant_with_tool_calls(text=None, tool_calls=[])
    assert a.tool_calls == []
    t = cb.tool_result_message("id", {"ok": True})
    assert t.tool_call_id == "id"
    s = cb.serialize_assistant_for_db([], None)
    assert "tool_calls" in s


@pytest.mark.parametrize(
    ("role", "expected"),
    [("user", "user"), ("assistant", "assistant")],
)
def test_history_plain_roles(role: str, expected: str) -> None:
    """User and assistant plain messages."""
    msgs = [
        MessageOut(
            id="1",
            conversation_id="c",
            role=role,
            content="x",
            tool_call_id=None,
            created_at="t",
        ),
    ]
    out = cb.history_to_chat(msgs)
    r = out[0].role
    val = r.value if hasattr(r, "value") else str(r)
    assert val == expected
