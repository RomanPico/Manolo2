"""OpenAI provider HTTP errors and streaming."""

from __future__ import annotations

import httpx
import pytest
import respx

from manolo.llm_client.base import ChatMessage, ChatRequest, MessageRole
from manolo.llm_client.exceptions import LLMHTTPError, LLMResponseError
from manolo.llm_client.openai_provider import OpenAICompatibleProvider, collect_stream_text


@pytest.mark.asyncio
@respx.mock
async def test_complete_http_error() -> None:
    """Raises LLMHTTPError on 4xx."""
    respx.post("https://api.example.com/v1/chat/completions").mock(
        return_value=httpx.Response(400, text="bad"),
    )
    async with httpx.AsyncClient() as client:
        p = OpenAICompatibleProvider(
            base_url="https://api.example.com/v1",
            api_key="k",
            client=client,
        )
        req = ChatRequest(
            model="m",
            messages=[ChatMessage(role=MessageRole.USER, content="hi")],
        )
        with pytest.raises(LLMHTTPError):
            await p.complete(req)
        await p.aclose()


@pytest.mark.asyncio
@respx.mock
async def test_stream_http_error() -> None:
    """Stream raises on 4xx."""
    respx.post("https://api.example.com/v1/chat/completions").mock(
        return_value=httpx.Response(400, text="bad"),
    )
    async with httpx.AsyncClient() as client:
        p = OpenAICompatibleProvider(
            base_url="https://api.example.com/v1",
            api_key="k",
            client=client,
        )
        req = ChatRequest(
            model="m",
            messages=[ChatMessage(role=MessageRole.USER, content="hi")],
        )
        with pytest.raises(LLMHTTPError):
            async for _ in p.stream(req):
                pass
        await p.aclose()


@pytest.mark.asyncio
@respx.mock
async def test_stream_collects_tokens() -> None:
    """collect_stream_text merges token chunks."""
    respx.post("https://api.example.com/v1/chat/completions").mock(
        return_value=httpx.Response(
            200,
            content=(
                'data: {"choices":[{"delta":{"content":"he"}}]}\n\n'
                'data: {"choices":[{"delta":{"content":"llo"}}]}\n\n'
                "data: [DONE]\n\n"
            ).encode(),
            headers={"content-type": "text/event-stream"},
        ),
    )
    async with httpx.AsyncClient() as client:
        p = OpenAICompatibleProvider(
            base_url="https://api.example.com/v1",
            api_key="k",
            client=client,
        )
        req = ChatRequest(
            model="m",
            messages=[ChatMessage(role=MessageRole.USER, content="hi")],
        )
        text, tcalls = await collect_stream_text(p.stream(req))
        assert text == "hello"
        assert tcalls == []
        await p.aclose()


@pytest.mark.asyncio
async def test_collect_stream_error_event() -> None:
    """collect_stream_text raises on error chunk."""
    from manolo.llm_client.base import StreamChunk

    async def gen():
        yield StreamChunk(kind="error", error="x")

    with pytest.raises(LLMResponseError):
        await collect_stream_text(gen())
