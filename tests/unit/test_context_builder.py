"""Context builder tests."""

from __future__ import annotations

import json

from manolo.llm_client.base import MessageRole
from manolo.models.dto import MessageOut
from manolo.orchestrator import context_builder as cb


def test_history_roundtrip_tool_assistant() -> None:
    """history_to_chat restores assistant tool_calls."""
    msgs = [
        MessageOut(
            id="1",
            conversation_id="c",
            role="assistant",
            content=json.dumps(
                {
                    "tool_calls": [
                        {
                            "id": "x",
                            "type": "function",
                            "function": {"name": "calendar_tool", "arguments": "{}"},
                        },
                    ],
                    "text": None,
                },
            ),
            tool_call_id=None,
            created_at="t",
        ),
        MessageOut(
            id="2",
            conversation_id="c",
            role="tool",
            content='{"ok": true}',
            tool_call_id="x",
            created_at="t",
        ),
    ]
    out = cb.history_to_chat(msgs)
    assert len(out) == 2
    assert out[0].tool_calls is not None
    assert out[1].role in ("tool", MessageRole.TOOL)
