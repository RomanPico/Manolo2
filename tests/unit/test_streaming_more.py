"""streaming.py extra branches."""

from __future__ import annotations

from manolo.llm_client.streaming import normalize_sse_line


def test_normalize_done() -> None:
    """[DONE] yields nothing."""
    assert normalize_sse_line("data: [DONE]") == []


def test_normalize_bad_json() -> None:
    """Invalid JSON yields nothing."""
    assert normalize_sse_line('data: {"choices":') == []


def test_normalize_tool_call_delta() -> None:
    """Tool call delta yields tool_call chunk."""
    line = (
        'data: {"choices":[{"delta":{"tool_calls":['
        '{"id":"1","function":{"name":"calendar_tool","arguments":"{}"}}'
        "]}}]}"
    )
    chunks = normalize_sse_line(line)
    assert any(c.kind == "tool_call" for c in chunks)


def test_normalize_empty_choices() -> None:
    """No choices returns empty."""
    assert normalize_sse_line('data: {"choices":[]}') == []


def test_normalize_bad_payload() -> None:
    """Invalid JSON returns empty."""
    assert normalize_sse_line("data: not-json") == []


def test_normalize_not_data_line() -> None:
    """Non-data lines ignored."""
    assert normalize_sse_line("event: ping") == []
