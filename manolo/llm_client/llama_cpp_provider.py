"""Llama.cpp server via OpenAI-compatible HTTP."""

from __future__ import annotations

from manolo.llm_client.openai_provider import OpenAICompatibleProvider


class LlamaCppProvider(OpenAICompatibleProvider):
    """Same as OpenAI-compatible; constructed with llama-server base URL."""
