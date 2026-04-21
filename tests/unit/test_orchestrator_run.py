"""Orchestrator run loop tests."""

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


class _FakeLLM:
    """Deterministic LLM for tests."""

    def __init__(self) -> None:
        self.calls = 0

    async def complete(self, _request: ChatRequest) -> ChatResponse:
        self.calls += 1
        return ChatResponse(
            content="final answer",
            tool_calls=[],
            finish_reason="stop",
            raw={},
        )

    async def aclose(self) -> None:
        """No-op."""


@pytest.mark.asyncio
async def test_run_chat_finishes(monkeypatch, sqlite_conn) -> None:
    """One LLM turn returns final answer."""
    fake = _FakeLLM()

    def _factory(*_a, **_k):  # noqa: ANN002
        return fake

    monkeypatch.setattr("manolo.orchestrator.runner.create_llm_provider", _factory)

    settings = Settings(
        llm_provider="openai",
        openai_api_key="test-key",
        openai_base_url="https://api.openai.com/v1",
        max_steps=10,
        max_tool_calls=10,
    )
    cal = CalendarService(SqliteCalendarRepository(sqlite_conn))
    async with httpx.AsyncClient() as client:
        fx = FxService(SqliteFxCacheRepository(sqlite_conn), FxHttpProvider(client, settings.fx_api_url))
        tools = build_default_tools(cal, fx)
        ex = ToolExecutor(tools, allowed=set(settings.allowed_tools_list()))

        conv = SqliteConversationsRepository(sqlite_conn)
        cid = "00000000-0000-0000-0000-000000000001"
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
        async for ev in run_chat(deps, conversation_id=cid, user_message="hello"):
            events.append(ev)

        assert any(e.get("event") == "done" for e in events)
        assert fake.calls == 1
