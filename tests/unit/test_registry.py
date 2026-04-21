"""LLM registry tests."""

from __future__ import annotations

import httpx
import pytest

from manolo.llm_client.llama_cpp_provider import LlamaCppProvider
from manolo.llm_client.openai_provider import OpenAICompatibleProvider
from manolo.llm_client.registry import create_llm_provider
from manolo.settings import Settings


@pytest.mark.asyncio
async def test_registry_openai() -> None:
    """openai provider."""
    s = Settings(
        llm_provider="openai",
        openai_api_key="k",
        openai_base_url="https://x/v1",
    )
    async with httpx.AsyncClient() as client:
        p = create_llm_provider(s, client=client)
        assert isinstance(p, OpenAICompatibleProvider)
        await p.aclose()


@pytest.mark.asyncio
async def test_registry_llama(monkeypatch: pytest.MonkeyPatch) -> None:
    """llama_cpp provider."""
    monkeypatch.setenv("LLM_PROVIDER", "llama_cpp")
    monkeypatch.setenv("LLAMA_CPP_BASE_URL", "http://127.0.0.1:1/v1")
    s = Settings()
    async with httpx.AsyncClient() as client:
        p = create_llm_provider(s, client=client)
        assert isinstance(p, LlamaCppProvider)
        await p.aclose()
