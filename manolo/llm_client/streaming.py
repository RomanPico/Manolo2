"""SSE / NDJSON streaming normalization for OpenAI-compatible APIs."""

from __future__ import annotations

import json
from typing import Any, Iterator

from manolo.llm_client.base import StreamChunk, ToolCall


def _parse_data_payload(payload: str) -> Iterator[StreamChunk]:
    payload = payload.strip()
    if not payload or payload == "[DONE]":
        return
    try:
        data: dict[str, Any] = json.loads(payload)
    except json.JSONDecodeError:
        return
    choices = data.get("choices") or []
    if not choices:
        return
    delta = choices[0].get("delta") or {}
    content = delta.get("content")
    if isinstance(content, str) and content:
        yield StreamChunk(kind="token", text=content)
    tool_calls = delta.get("tool_calls") or []
    for tc in tool_calls:
        fn = tc.get("function") or {}
        name = fn.get("name")
        args = fn.get("arguments")
        tid = str(tc.get("id") or "")
        if name:
            yield StreamChunk(
                kind="tool_call",
                tool_call=ToolCall(
                    id=tid or "call",
                    name=str(name),
                    arguments_json=str(args) if args is not None else "{}",
                ),
            )


def normalize_sse_line(line: str) -> list[StreamChunk]:
    """Parse one SSE line into zero or more StreamChunks."""
    line = line.strip()
    if not line.startswith("data:"):
        return []
    payload = line[5:].strip()
    if payload == "[DONE]":
        return []
    return list(_parse_data_payload(payload))
