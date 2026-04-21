"""Build LLM chat messages from DB history and in-run working memory."""

from __future__ import annotations

import json
from typing import Any

from manolo.llm_client.base import ChatMessage, MessageRole, ToolSpec
from manolo.models.dto import MessageOut
from manolo.tools.base import Tool


def tool_specs(tools: dict[str, Tool]) -> list[ToolSpec]:
    """Convert tools to LLM tool definitions."""
    return [
        ToolSpec(name=t.name, description=t.description, parameters=t.input_schema)
        for t in tools.values()
    ]


def history_to_chat(messages: list[MessageOut]) -> list[ChatMessage]:
    """Map persisted messages to provider messages."""
    out: list[ChatMessage] = []
    for m in messages:
        role = m.role
        if role == "tool":
            out.append(
                ChatMessage(
                    role=MessageRole.TOOL,
                    content=m.content,
                    tool_call_id=m.tool_call_id,
                ),
            )
            continue
        if role == "assistant" and m.content.startswith("{") and "tool_calls" in m.content:
            try:
                payload = json.loads(m.content)
                tcalls = payload.get("tool_calls")
                text = payload.get("text")
                if isinstance(tcalls, list):
                    out.append(
                        ChatMessage(
                            role=MessageRole.ASSISTANT,
                            content=text if isinstance(text, str) else None,
                            tool_calls=tcalls,
                        ),
                    )
                    continue
            except json.JSONDecodeError:
                pass
        r = MessageRole.USER if role == "user" else MessageRole.ASSISTANT
        out.append(ChatMessage(role=r, content=m.content))
    return out


def system_prompt() -> ChatMessage:
    """Default system instructions."""
    text = (
        "You are a helpful assistant. Use tools when they help answer accurately. "
        "Be concise. When using calendar_tool or usd_price_tool, pass valid JSON arguments."
    )
    return ChatMessage(role=MessageRole.SYSTEM, content=text)


def append_user(text: str) -> ChatMessage:
    """User turn."""
    return ChatMessage(role=MessageRole.USER, content=text)


def assistant_with_tool_calls(
    *,
    text: str | None,
    tool_calls: list[dict[str, Any]],
) -> ChatMessage:
    """Assistant message that requests tools."""
    return ChatMessage(
        role=MessageRole.ASSISTANT,
        content=text,
        tool_calls=tool_calls,
    )


def tool_result_message(tool_call_id: str, content: dict[str, Any]) -> ChatMessage:
    """Tool output message."""
    return ChatMessage(
        role=MessageRole.TOOL,
        content=json.dumps(content),
        tool_call_id=tool_call_id,
    )


def serialize_assistant_for_db(tool_calls: list[dict[str, Any]], text: str | None) -> str:
    """Persist assistant row that invoked tools."""
    return json.dumps({"tool_calls": tool_calls, "text": text})
