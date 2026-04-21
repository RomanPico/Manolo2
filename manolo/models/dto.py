"""Shared data transfer objects."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class ConversationCreate(BaseModel):
    """Create conversation request."""

    title: str | None = None


class ConversationOut(BaseModel):
    """Conversation row."""

    id: str
    title: str | None
    created_at: str


class MessageOut(BaseModel):
    """Message row."""

    id: str
    conversation_id: str
    role: str
    content: str
    tool_call_id: str | None
    created_at: str


class ChatRequestBody(BaseModel):
    """POST /v1/chat body."""

    conversation_id: str | None = None
    message: str = Field(..., min_length=1)


class CalendarToolRequest(BaseModel):
    """HTTP body for calendar tool."""

    action: str
    title: str | None = None
    starts_at: str | None = None
    ends_at: str | None = None
    description: str | None = None
    location: str | None = None
    event_id: str | None = None
    start_from: str | None = None
    end_to: str | None = None
    limit: int | None = None


class CalendarToolResponse(BaseModel):
    """Normalized calendar tool response."""

    ok: bool
    action: str
    data: dict[str, Any] = Field(default_factory=dict)
    error: str | None = None


class FxToolResponse(BaseModel):
    """Normalized FX tool response."""

    ok: bool
    pair: str
    rate: float | None = None
    fetched_at: str | None = None
    cached: bool = False
    error: str | None = None
