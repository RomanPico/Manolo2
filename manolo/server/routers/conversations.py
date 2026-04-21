"""Conversation CRUD."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException, Request

from manolo.models.dto import ConversationCreate, ConversationOut, MessageOut

router = APIRouter(prefix="/conversations", tags=["conversations"])


def _now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


@router.get("")
async def list_conversations(request: Request) -> list[ConversationOut]:
    """List conversations."""
    repo = request.app.state.conversations
    return await repo.list_all()


@router.post("")
async def create_conversation(
    request: Request,
    body: ConversationCreate | None = None,
) -> ConversationOut:
    """Create a conversation."""
    cid = str(uuid.uuid4())
    title = body.title if body and body.title else "New chat"
    repo = request.app.state.conversations
    await repo.create(cid, title, _now_iso())
    row = await repo.get(cid)
    if row is None:
        raise HTTPException(status_code=500, detail="failed to create conversation")
    return row


@router.get("/{conversation_id}")
async def get_conversation(conversation_id: str, request: Request) -> ConversationOut:
    """Get one conversation."""
    repo = request.app.state.conversations
    row = await repo.get(conversation_id)
    if row is None:
        raise HTTPException(status_code=404, detail="not found")
    return row


@router.get("/{conversation_id}/messages")
async def list_messages(conversation_id: str, request: Request) -> list[MessageOut]:
    """List messages in a conversation."""
    repo = request.app.state.messages
    return await repo.list_for_conversation(conversation_id)
