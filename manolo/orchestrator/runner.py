"""Main orchestration loop."""

from __future__ import annotations

import json
import uuid
from collections.abc import AsyncIterator
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

import httpx

from manolo.llm_client.base import ChatMessage, ChatRequest, ToolCall
from manolo.llm_client.registry import create_llm_provider
from manolo.orchestrator import context_builder as cb
from manolo.orchestrator.policies import should_stop
from manolo.orchestrator.state import OrchestrationState
from manolo.repositories.interfaces import (
    ConversationsRepository,
    MessagesRepository,
    RunStepsRepository,
    RunsRepository,
)
from manolo.settings import Settings
from manolo.tools.base import Tool
from manolo.tools.executor import ToolExecutor


def _now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _tool_calls_to_api(tc_list: list[ToolCall]) -> list[dict[str, Any]]:
    return [
        {
            "id": tc.id,
            "type": "function",
            "function": {"name": tc.name, "arguments": tc.arguments_json},
        }
        for tc in tc_list
    ]


@dataclass
class RunDeps:
    """Per-request dependencies."""

    settings: Settings
    http_client: httpx.AsyncClient
    conversations: ConversationsRepository
    messages: MessagesRepository
    runs: RunsRepository
    run_steps: RunStepsRepository
    tool_executor: ToolExecutor
    tools: dict[str, Tool]


async def run_chat(
    deps: RunDeps,
    *,
    conversation_id: str,
    user_message: str,
) -> AsyncIterator[dict[str, Any]]:
    """Execute one user turn; yield SSE-friendly dict events."""
    run_id = str(uuid.uuid4())
    state = OrchestrationState(
        run_id=run_id,
        conversation_id=conversation_id,
        user_message=user_message,
        max_steps=deps.settings.max_steps,
        max_tool_calls=deps.settings.max_tool_calls,
    )
    yield {"event": "run_started", "run_id": run_id, "conversation_id": conversation_id}

    llm = None
    try:
        await deps.runs.create(run_id, conversation_id, "running", _now_iso())

        user_id = str(uuid.uuid4())
        await deps.messages.append(
            user_id,
            conversation_id,
            "user",
            user_message,
            None,
            _now_iso(),
        )

        history = await deps.messages.list_for_conversation(conversation_id)
        working: list[ChatMessage] = [cb.system_prompt(), *cb.history_to_chat(history)]

        llm = create_llm_provider(deps.settings, client=deps.http_client)
        allowed_tools = set(deps.settings.allowed_tools_list())
        specs = [s for s in cb.tool_specs(deps.tools) if s.name in allowed_tools]

        step_idx = 0
        while True:
            state.step_count += 1
            if should_stop(state):
                state.status = "failed"
                state.last_error = "policy limit reached"
                await deps.runs.finalize(run_id, "failed", None, state.last_error, _now_iso())
                yield {"event": "error", "message": state.last_error}
                return

            req = ChatRequest(model=deps.settings.llm_model, messages=working, tools=specs)
            step_idx += 1
            await deps.run_steps.append(
                str(uuid.uuid4()),
                run_id,
                step_idx,
                "llm_request",
                json.dumps({"model": req.model, "messages_len": len(working)}),
                _now_iso(),
            )

            assert llm is not None
            resp = await llm.complete(req)
            await deps.run_steps.append(
                str(uuid.uuid4()),
                run_id,
                step_idx,
                "llm_response",
                json.dumps(
                    {
                        "finish_reason": resp.finish_reason,
                        "tool_calls": [tc.name for tc in resp.tool_calls],
                    },
                ),
                _now_iso(),
            )

            if resp.tool_calls:
                if state.tool_calls_made + len(resp.tool_calls) > state.max_tool_calls:
                    state.status = "failed"
                    state.last_error = "max tool calls would be exceeded"
                    await deps.runs.finalize(run_id, "failed", None, state.last_error, _now_iso())
                    yield {"event": "error", "message": state.last_error}
                    return
                api_calls = _tool_calls_to_api(resp.tool_calls)
                asst_id = str(uuid.uuid4())
                await deps.messages.append(
                    asst_id,
                    conversation_id,
                    "assistant",
                    cb.serialize_assistant_for_db(api_calls, resp.content),
                    None,
                    _now_iso(),
                )
                working.append(
                    cb.assistant_with_tool_calls(
                        text=resp.content,
                        tool_calls=api_calls,
                    ),
                )
                for tc in resp.tool_calls:
                    yield {"event": "tool_call", "name": tc.name, "id": tc.id}

                for tc in resp.tool_calls:
                    state.tool_calls_made += 1
                    result = await deps.tool_executor.run(tc.name, tc.arguments_json)
                    yield {"event": "tool_result", "name": tc.name, "result": result}
                    tid = str(uuid.uuid4())
                    await deps.messages.append(
                        tid,
                        conversation_id,
                        "tool",
                        json.dumps(result),
                        tc.id,
                        _now_iso(),
                    )
                    working.append(cb.tool_result_message(tc.id, result))

                continue

            final = (resp.content or "").strip()
            aid = str(uuid.uuid4())
            await deps.messages.append(
                aid,
                conversation_id,
                "assistant",
                final,
                None,
                _now_iso(),
            )
            state.final_answer = final
            state.status = "completed"
            for chunk in _chunk_text(final):
                yield {"event": "token", "text": chunk}
            await deps.runs.finalize(run_id, "completed", final, None, _now_iso())
            yield {"event": "done", "answer": final}
            return

    except Exception as exc:  # noqa: BLE001
        state.status = "failed"
        state.last_error = str(exc)
        await deps.runs.finalize(run_id, "failed", None, state.last_error, _now_iso())
        yield {"event": "error", "message": state.last_error}
    finally:
        if llm is not None:
            await llm.aclose()


def _chunk_text(text: str, size: int = 48) -> list[str]:
    """Split assistant text into small chunks for nicer SSE."""
    if not text:
        return []
    return [text[i : i + size] for i in range(0, len(text), size)]
