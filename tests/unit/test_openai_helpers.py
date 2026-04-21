"""Internal OpenAI helper coverage."""

from __future__ import annotations

import json

import httpx
import pytest
import respx

from manolo.llm_client.base import ChatMessage, ChatRequest, MessageRole, ToolSpec
from manolo.llm_client.exceptions import LLMResponseError
from manolo.llm_client.openai_provider import (
    OpenAICompatibleProvider,
    _messages_to_openai,
    _parse_choice,
    _tools_to_openai,
)


def test_parse_choice_missing_choices() -> None:
    """Raises when choices absent."""
    with pytest.raises(LLMResponseError):
        _parse_choice({})


def test_role_str_plain_string() -> None:
    """_role_str supports string roles."""
    m = ChatMessage(role="user", content="hi")
    out = _messages_to_openai([m])[0]
    assert out["role"] == "user"


def test_messages_to_openai_optional_fields() -> None:
    """Includes optional OpenAI fields."""
    m = ChatMessage(
        role=MessageRole.USER,
        content="hi",
        name="n",
        tool_call_id="tc",
        tool_calls=[{"id": "1", "type": "function", "function": {"name": "x", "arguments": "{}"}}],
    )
    out = _messages_to_openai([m])[0]
    assert out["name"] == "n"
    assert out["tool_call_id"] == "tc"
    assert "tool_calls" in out


def test_tools_to_openai_maps() -> None:
    """Tool specs map to OpenAI tool objects."""
    specs = [
        ToolSpec(name="t", description="d", parameters={"type": "object"}),
    ]
    out = _tools_to_openai(specs)
    assert out[0]["type"] == "function"
    assert out[0]["function"]["name"] == "t"


@pytest.mark.asyncio
@respx.mock
async def test_complete_includes_tools() -> None:
    """complete() sends tools in body when provided."""
    captured: dict = {}

    def _handler(request: httpx.Request) -> httpx.Response:
        captured["body"] = json.loads(request.content.decode())
        return httpx.Response(
            200,
            json={"choices": [{"message": {"role": "assistant", "content": "ok"}}]},
        )

    respx.post("https://api.example.com/v1/chat/completions").mock(side_effect=_handler)
    async with httpx.AsyncClient() as client:
        p = OpenAICompatibleProvider(base_url="https://api.example.com/v1", api_key="k", client=client)
        req = ChatRequest(
            model="m",
            messages=[ChatMessage(role=MessageRole.USER, content="hi")],
            tools=[ToolSpec(name="t", description="d", parameters={"type": "object"})],
        )
        await p.complete(req)
        assert "tools" in captured["body"]
        await p.aclose()


@pytest.mark.asyncio
@respx.mock
async def test_stream_includes_tools() -> None:
    """stream() sends tools in body."""
    captured: dict = {}

    def _handler(request: httpx.Request) -> httpx.Response:
        captured["body"] = json.loads(request.content.decode())
        return httpx.Response(
            200,
            content="data: [DONE]\n\n".encode(),
            headers={"content-type": "text/event-stream"},
        )

    respx.post("https://api.example.com/v1/chat/completions").mock(side_effect=_handler)
    async with httpx.AsyncClient() as client:
        p = OpenAICompatibleProvider(base_url="https://api.example.com/v1", api_key="k", client=client)
        req = ChatRequest(
            model="m",
            messages=[ChatMessage(role=MessageRole.USER, content="hi")],
            tools=[ToolSpec(name="t", description="d", parameters={"type": "object"})],
        )
        async for _ in p.stream(req):
            pass
        assert "tools" in captured["body"]
        await p.aclose()


@pytest.mark.asyncio
@respx.mock
async def test_owned_client_closed() -> None:
    """Provider without injected client closes internal httpx client."""
    respx.post("https://api.example.com/v1/chat/completions").mock(
        return_value=httpx.Response(
            200,
            json={"choices": [{"message": {"role": "assistant", "content": "x"}}]},
        ),
    )
    p = OpenAICompatibleProvider(base_url="https://api.example.com/v1", api_key="k")
    req = ChatRequest(model="m", messages=[ChatMessage(role=MessageRole.USER, content="hi")])
    await p.complete(req)
    await p.aclose()
