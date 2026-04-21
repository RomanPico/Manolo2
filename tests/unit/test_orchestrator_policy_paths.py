"""Orchestrator policy and error paths."""

from __future__ import annotations

import pytest

from manolo.llm_client.base import ChatRequest, ChatResponse
from manolo.orchestrator.runner import RunDeps, run_chat
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


class _BoomLLM:
    async def complete(self, _request: ChatRequest) -> ChatResponse:
        msg = "boom"
        raise RuntimeError(msg)

    async def aclose(self) -> None:
        """No-op."""


@pytest.mark.asyncio
async def test_run_chat_policy_steps_zero(monkeypatch, sqlite_conn) -> None:
    """max_steps=1 triggers policy error before LLM."""
    fake = _BoomLLM()

    def _factory(*_a, **_k):
        return fake

    monkeypatch.setattr("manolo.orchestrator.runner.create_llm_provider", _factory)

    settings = Settings(
        llm_provider="openai",
        openai_api_key="test-key",
        max_steps=1,
        max_tool_calls=10,
    )
    cal = CalendarService(SqliteCalendarRepository(sqlite_conn))
    async with httpx.AsyncClient() as client:
        fx = FxService(SqliteFxCacheRepository(sqlite_conn), FxHttpProvider(client, settings.fx_api_url))
        tools = build_default_tools(cal, fx)
        ex = ToolExecutor(tools, allowed=set(settings.allowed_tools_list()))
        conv = SqliteConversationsRepository(sqlite_conn)
        cid = "00000000-0000-0000-0000-000000000003"
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
        assert any(e.get("event") == "error" for e in events)


@pytest.mark.asyncio
async def test_run_chat_llm_raises(monkeypatch, sqlite_conn) -> None:
    """LLM exception becomes error event."""
    boom = _BoomLLM()

    def _factory(*_a, **_k):
        return boom

    monkeypatch.setattr("manolo.orchestrator.runner.create_llm_provider", _factory)

    settings = Settings(
        llm_provider="openai",
        openai_api_key="test-key",
        max_steps=10,
        max_tool_calls=10,
    )
    cal = CalendarService(SqliteCalendarRepository(sqlite_conn))
    async with httpx.AsyncClient() as client:
        fx = FxService(SqliteFxCacheRepository(sqlite_conn), FxHttpProvider(client, settings.fx_api_url))
        tools = build_default_tools(cal, fx)
        ex = ToolExecutor(tools, allowed=set(settings.allowed_tools_list()))
        conv = SqliteConversationsRepository(sqlite_conn)
        cid = "00000000-0000-0000-0000-000000000004"
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
        assert any(e.get("event") == "error" for e in events)
