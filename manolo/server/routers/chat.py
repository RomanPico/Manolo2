"""SSE chat endpoint."""

from __future__ import annotations

import json
from typing import Any

from fastapi import APIRouter, HTTPException, Request
from sse_starlette.sse import EventSourceResponse

from manolo.models.dto import ChatRequestBody
from manolo.orchestrator.runner import RunDeps, run_chat

router = APIRouter(tags=["chat"])


@router.post("/chat")
async def chat_sse(request: Request, body: ChatRequestBody) -> EventSourceResponse:
    """Stream orchestration events as SSE."""
    settings = request.app.state.settings
    if not body.conversation_id:
        raise HTTPException(status_code=400, detail="conversation_id is required")
    conv = await request.app.state.conversations.get(body.conversation_id)
    if conv is None:
        raise HTTPException(status_code=404, detail="conversation not found")

    deps = RunDeps(
        settings=settings,
        http_client=request.app.state.http,
        conversations=request.app.state.conversations,
        messages=request.app.state.messages,
        runs=request.app.state.runs,
        run_steps=request.app.state.run_steps,
        tool_executor=request.app.state.tool_executor,
        tools=request.app.state.tools,
    )

    async def event_gen() -> Any:
        async for ev in run_chat(
            deps,
            conversation_id=body.conversation_id,
            user_message=body.message,
        ):
            yield {"data": json.dumps(ev)}

    return EventSourceResponse(event_gen())
