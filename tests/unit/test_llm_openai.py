"""OpenAI-compatible provider tests."""

from __future__ import annotations

import httpx
import pytest
import respx

from manolo.llm_client.base import ChatMessage, ChatRequest, MessageRole
from manolo.llm_client.openai_provider import OpenAICompatibleProvider


@pytest.mark.asyncio
@respx.mock
async def test_openai_complete_parses_tool_calls() -> None:
    """complete() maps JSON to ChatResponse."""
    respx.post("https://api.example.com/v1/chat/completions").mock(
        return_value=httpx.Response(
            200,
            json={
                "choices": [
                    {
                        "message": {
                            "role": "assistant",
                            "content": None,
                            "tool_calls": [
                                {
                                    "id": "call_1",
                                    "type": "function",
                                    "function": {
                                        "name": "calendar_tool",
                                        "arguments": '{"action":"lookup"}',
                                    },
                                },
                            ],
                        },
                        "finish_reason": "tool_calls",
                    },
                ],
            },
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
            tools=[],
        )
        out = await p.complete(req)
        assert len(out.tool_calls) == 1
        assert out.tool_calls[0].name == "calendar_tool"
        await p.aclose()
