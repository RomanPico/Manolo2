"""LLM provider protocol and core types."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Literal, Protocol


class MessageRole(str, Enum):
    """Chat message roles."""

    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"
    TOOL = "tool"


@dataclass(frozen=True)
class ChatMessage:
    """OpenAI-style message."""

    role: MessageRole | str
    content: str | None
    name: str | None = None
    tool_call_id: str | None = None
    tool_calls: list[dict[str, Any]] | None = None


@dataclass(frozen=True)
class ToolSpec:
    """Tool definition for the chat API."""

    name: str
    description: str
    parameters: dict[str, Any]


@dataclass(frozen=True)
class ToolCall:
    """Parsed tool invocation."""

    id: str
    name: str
    arguments_json: str


@dataclass(frozen=True)
class ChatRequest:
    """Non-streaming chat completion request."""

    model: str
    messages: list[ChatMessage]
    tools: list[ToolSpec] = field(default_factory=list)
    temperature: float = 0.2


@dataclass(frozen=True)
class ChatResponse:
    """Normalized completion result."""

    content: str | None
    tool_calls: list[ToolCall]
    finish_reason: str | None
    raw: dict[str, Any]


class LLMProvider(Protocol):
    """Provider-agnostic LLM API."""

    async def complete(self, request: ChatRequest) -> ChatResponse:
        """Return a full assistant message (optionally with tool calls)."""


@dataclass(frozen=True)
class StreamChunk:
    """Normalized streaming event."""

    kind: Literal["token", "tool_call", "done", "error"]
    text: str | None = None
    tool_call: ToolCall | None = None
    error: str | None = None
