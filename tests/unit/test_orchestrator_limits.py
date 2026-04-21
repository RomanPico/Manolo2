"""Orchestrator max_steps / max_tool_calls edge cases."""

from __future__ import annotations

import pytest

from manolo.llm_client.base import ChatRequest, ChatResponse, ToolCall
from manolo.orchestrator.runner import RunDeps, _chunk_text, run_chat
from manolo.repositories.sqlite.calendar_repo import SqliteCalendarRepository
from manolo.repositories.sqlite.conversations_repo import SqliteConversationsRepository
from manolo.repositories.sqlite.fx_cache_repo import SqliteFxCacheRepository
from manolo.repositories.sqlite.messages_repo import SqliteMessagesRepository
from manolo.repositories.sqlite.run_steps_repo import SqliteRunStepsRepository
from manolo.repositories.sqlite.runs_repo import SqliteRunsRepository
from manolo.services.calendar_service import CalendarService
from manolo.services.fx_service import FxService
from manolo.providers.fx_http_provider import FxHttpProvider
from manolo.settings import Settings
from manolo.tools.executor import ToolExecutor
from manolo.tools.registry import build_default_tools
import httpx


class _ToolOnlyLLM:
    """Always requests one tool."""

    async def complete(self, _request: ChatRequest) -> ChatResponse:
        return ChatResponse(
            content=None,
            tool_calls=[
                ToolCall(
                    id="c1",
                    name="calendar_tool",
                    arguments_json='{"action":"lookup","limit":1}',
                ),
            ],
            finish_reason="tool_calls",
            raw={},
        )

    async def aclose(self) -> None:
        """No-op."""


@pytest.mark.asyncio
async def test_policy_limit_after_tool_iteration(monkeypatch, sqlite_conn) -> None:
    """max_steps=2 stops before second LLM call after tools."""
    fake = _ToolOnlyLLM()

    def _factory(*_a, **_k):
        return fake

    monkeypatch.setattr("manolo.orchestrator.runner.create_llm_provider", _factory)

    settings = Settings(
        llm_provider="openai",
        openai_api_key="test-key",
        max_steps=2,
        max_tool_calls=10,
    )
    cal = CalendarService(SqliteCalendarRepository(sqlite_conn))
    async with httpx.AsyncClient() as client:
        fx = FxService(SqliteFxCacheRepository(sqlite_conn), FxHttpProvider(client, settings.fx_api_url))
        tools = build_default_tools(cal, fx)
        ex = ToolExecutor(tools, allowed=set(settings.allowed_tools_list()))
        conv = SqliteConversationsRepository(sqlite_conn)
        cid = "00000000-0000-0000-0000-000000000005"
        await conv.create(cid, "t", "2020-01-01T00:00:00+00:00")
        deps = RunDeps(
            settings=settings,
            http_client=client,
            conversations=conv,
            messages=SqliteMessagesRepository(sqlite_conn),
            runs=SqliteRunsRepository(sqlite_conn),
            run_steps=SqliteRunStepsRepository(sqlite_conn),
            tool_executor=ex,
            tools=tools,
        )
        events: list[dict] = []
        async for ev in run_chat(deps, conversation_id=cid, user_message="hi"):
            events.append(ev)
        assert any(e.get("message") == "policy limit reached" for e in events if e.get("event") == "error")


class _ManyToolsLLM:
    """Returns more tool calls than allowed."""

    async def complete(self, _request: ChatRequest) -> ChatResponse:
        calls = [
            ToolCall(id="a", name="calendar_tool", arguments_json='{"action":"lookup","limit":1}'),
            ToolCall(id="b", name="calendar_tool", arguments_json='{"action":"lookup","limit":1}'),
        ]
        return ChatResponse(content=None, tool_calls=calls, finish_reason="tool_calls", raw={})

    async def aclose(self) -> None:
        """No-op."""


@pytest.mark.asyncio
async def test_max_tool_calls_gate(monkeypatch, sqlite_conn) -> None:
    """Too many tool calls in one response fails."""
    monkeypatch.setenv("MAX_TOOL_CALLS", "1")
    fake = _ManyToolsLLM()

    def _factory(*_a, **_k):
        return fake

    monkeypatch.setattr("manolo.orchestrator.runner.create_llm_provider", _factory)

    settings = Settings(
        llm_provider="openai",
        openai_api_key="test-key",
        max_steps=10,
    )
    cal = CalendarService(SqliteCalendarRepository(sqlite_conn))
    async with httpx.AsyncClient() as client:
        fx = FxService(SqliteFxCacheRepository(sqlite_conn), FxHttpProvider(client, settings.fx_api_url))
        tools = build_default_tools(cal, fx)
        ex = ToolExecutor(tools, allowed=set(settings.allowed_tools_list()))
        conv = SqliteConversationsRepository(sqlite_conn)
        cid = "00000000-0000-0000-0000-000000000006"
        await conv.create(cid, "t", "2020-01-01T00:00:00+00:00")
        deps = RunDeps(
            settings=settings,
            http_client=client,
            conversations=conv,
            messages=SqliteMessagesRepository(sqlite_conn),
            runs=SqliteRunsRepository(sqlite_conn),
            run_steps=SqliteRunStepsRepository(sqlite_conn),
            tool_executor=ex,
            tools=tools,
        )
        events: list[dict] = []
        async for ev in run_chat(deps, conversation_id=cid, user_message="hi"):
            events.append(ev)
        assert any(
            e.get("message") == "max tool calls would be exceeded"
            for e in events
            if e.get("event") == "error"
        )


class _EmptyFinalLLM:
    async def complete(self, _request: ChatRequest) -> ChatResponse:
        return ChatResponse(content="   ", tool_calls=[], finish_reason="stop", raw={})

    async def aclose(self) -> None:
        """No-op."""


@pytest.mark.asyncio
async def test_run_chat_empty_final_text(monkeypatch, sqlite_conn) -> None:
    """Whitespace-only final answer yields done with empty string."""
    fake = _EmptyFinalLLM()

    def _factory(*_a, **_k):
        return fake

    monkeypatch.setattr("manolo.orchestrator.runner.create_llm_provider", _factory)

    settings = Settings(llm_provider="openai", openai_api_key="test-key")
    cal = CalendarService(SqliteCalendarRepository(sqlite_conn))
    async with httpx.AsyncClient() as client:
        fx = FxService(SqliteFxCacheRepository(sqlite_conn), FxHttpProvider(client, settings.fx_api_url))
        tools = build_default_tools(cal, fx)
        ex = ToolExecutor(tools, allowed=set(settings.allowed_tools_list()))
        conv = SqliteConversationsRepository(sqlite_conn)
        cid = "00000000-0000-0000-0000-000000000007"
        await conv.create(cid, "t", "2020-01-01T00:00:00+00:00")
        deps = RunDeps(
            settings=settings,
            http_client=client,
            conversations=conv,
            messages=SqliteMessagesRepository(sqlite_conn),
            runs=SqliteRunsRepository(sqlite_conn),
            run_steps=SqliteRunStepsRepository(sqlite_conn),
            tool_executor=ex,
            tools=tools,
        )
        events: list[dict] = []
        async for ev in run_chat(deps, conversation_id=cid, user_message="hi"):
            events.append(ev)
        done = [e for e in events if e.get("event") == "done"]
        assert done and done[0].get("answer") == ""


def test_chunk_text_empty() -> None:
    """_chunk_text empty input."""
    assert _chunk_text("") == []
