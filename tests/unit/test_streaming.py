"""Streaming normalization tests."""

from __future__ import annotations

from manolo.llm_client.streaming import normalize_sse_line


def test_normalize_sse_token() -> None:
    """Parses token delta."""
    line = 'data: {"choices":[{"delta":{"content":"hi"}}]}'
    chunks = normalize_sse_line(line)
    assert len(chunks) == 1
    assert chunks[0].kind == "token"
    assert chunks[0].text == "hi"
