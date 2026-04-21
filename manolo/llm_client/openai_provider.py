"""OpenAI-compatible HTTP provider (also used for llama-server)."""

from __future__ import annotations

from typing import Any, AsyncIterator

import httpx

from manolo.llm_client.base import (
    ChatMessage,
    ChatRequest,
    ChatResponse,
    StreamChunk,
    ToolCall,
    ToolSpec,
)
from manolo.llm_client.exceptions import LLMHTTPError, LLMResponseError
from manolo.llm_client.streaming import normalize_sse_line


def _role_str(role: ChatMessage) -> str:
    r = role.role
    if hasattr(r, "value"):
        return str(r.value)
    return str(r)


def _messages_to_openai(messages: list[ChatMessage]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for m in messages:
        item: dict[str, Any] = {"role": _role_str(m)}
        if m.content is not None:
            item["content"] = m.content
        if m.name:
            item["name"] = m.name
        if m.tool_call_id:
            item["tool_call_id"] = m.tool_call_id
        if m.tool_calls:
            item["tool_calls"] = m.tool_calls
        out.append(item)
    return out


def _tools_to_openai(tools: list[ToolSpec]) -> list[dict[str, Any]]:
    return [
        {
            "type": "function",
            "function": {
                "name": t.name,
                "description": t.description,
                "parameters": t.parameters,
            },
        }
        for t in tools
    ]


def _parse_choice(data: dict[str, Any]) -> ChatResponse:
    choices = data.get("choices")
    if not choices:
        raise LLMResponseError("missing choices")
    ch0 = choices[0]
    msg = ch0.get("message") or {}
    content = msg.get("content")
    tool_calls_raw = msg.get("tool_calls") or []
    tool_calls: list[ToolCall] = []
    for tc in tool_calls_raw:
        fn = tc.get("function") or {}
        tid = str(tc.get("id") or "")
        name = str(fn.get("name") or "")
        args = fn.get("arguments")
        tool_calls.append(
            ToolCall(id=tid, name=name, arguments_json=str(args) if args is not None else "{}"),
        )
    finish_reason = ch0.get("finish_reason")
    return ChatResponse(
        content=content if isinstance(content, str) else None,
        tool_calls=tool_calls,
        finish_reason=str(finish_reason) if finish_reason is not None else None,
        raw=data,
    )


class OpenAICompatibleProvider:
    """httpx client for /v1/chat/completions."""

    def __init__(
        self,
        *,
        base_url: str,
        api_key: str,
        client: httpx.AsyncClient | None = None,
        timeout: float = 120.0,
    ) -> None:
        self._base_url = base_url.rstrip("/")
        self._api_key = api_key
        self._owns_client = client is None
        self._client = client or httpx.AsyncClient(timeout=timeout)

    async def aclose(self) -> None:
        """Close underlying client if owned."""
        if self._owns_client:
            await self._client.aclose()

    def _headers(self) -> dict[str, str]:
        h: dict[str, str] = {"Content-Type": "application/json"}
        if self._api_key:
            h["Authorization"] = f"Bearer {self._api_key}"
        return h

    async def complete(self, request: ChatRequest) -> ChatResponse:
        """POST chat/completions JSON."""
        url = f"{self._base_url}/chat/completions"
        body: dict[str, Any] = {
            "model": request.model,
            "messages": _messages_to_openai(request.messages),
            "temperature": request.temperature,
        }
        if request.tools:
            body["tools"] = _tools_to_openai(request.tools)
        resp = await self._client.post(url, headers=self._headers(), json=body)
        if resp.status_code >= 400:
            raise LLMHTTPError(resp.text, status_code=resp.status_code)
        data = resp.json()
        return _parse_choice(data)

    async def stream(self, request: ChatRequest) -> AsyncIterator[StreamChunk]:
        """Stream SSE from chat/completions."""
        url = f"{self._base_url}/chat/completions"
        body: dict[str, Any] = {
            "model": request.model,
            "messages": _messages_to_openai(request.messages),
            "temperature": request.temperature,
            "stream": True,
        }
        if request.tools:
            body["tools"] = _tools_to_openai(request.tools)

        async with self._client.stream(
            "POST",
            url,
            headers=self._headers(),
            json=body,
        ) as resp:
            if resp.status_code >= 400:
                text = await resp.aread()
                raise LLMHTTPError(text.decode("utf-8", errors="replace"), status_code=resp.status_code)

            buffer = ""
            async for chunk in resp.aiter_text():
                buffer += chunk
                while "\n" in buffer:
                    line, buffer = buffer.split("\n", 1)
                    for sc in normalize_sse_line(line):
                        yield sc

            if buffer.strip():
                for sc in normalize_sse_line(buffer):
                    yield sc

            yield StreamChunk(kind="done")


async def collect_stream_text(stream: AsyncIterator[StreamChunk]) -> tuple[str, list[ToolCall]]:
    """Accumulate token chunks into final text; tool calls if emitted."""
    parts: list[str] = []
    tool_calls: list[ToolCall] = []
    async for ch in stream:
        if ch.kind == "token" and ch.text:
            parts.append(ch.text)
        if ch.kind == "tool_call" and ch.tool_call:
            tool_calls.append(ch.tool_call)
        if ch.kind == "error" and ch.error:
            raise LLMResponseError(ch.error)
    return "".join(parts), tool_calls
