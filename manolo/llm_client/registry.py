"""Factory for LLM providers from settings."""

from __future__ import annotations

import httpx

from manolo.llm_client.llama_cpp_provider import LlamaCppProvider
from manolo.llm_client.openai_provider import OpenAICompatibleProvider
from manolo.settings import Settings


def create_llm_provider(
    settings: Settings,
    *,
    client: httpx.AsyncClient | None = None,
) -> OpenAICompatibleProvider | LlamaCppProvider:
    """Return configured provider."""
    name = settings.llm_provider.lower().strip()
    if name == "llama_cpp":
        return LlamaCppProvider(
            base_url=settings.llama_cpp_base_url,
            api_key="",
            client=client,
        )
    return OpenAICompatibleProvider(
        base_url=settings.openai_base_url,
        api_key=settings.openai_api_key,
        client=client,
    )
