"""Application lifespan wiring."""

from __future__ import annotations

from contextlib import asynccontextmanager
from typing import Any

import httpx
from fastapi import FastAPI

from manolo.providers.fx_http_provider import FxHttpProvider
from manolo.repositories.sqlite.calendar_repo import SqliteCalendarRepository
from manolo.repositories.sqlite.connection import connect_database
from manolo.repositories.sqlite.conversations_repo import SqliteConversationsRepository
from manolo.repositories.sqlite.fx_cache_repo import SqliteFxCacheRepository
from manolo.repositories.sqlite.memory_repo import SqliteMemoryRepository
from manolo.repositories.sqlite.messages_repo import SqliteMessagesRepository
from manolo.repositories.sqlite.run_steps_repo import SqliteRunStepsRepository
from manolo.repositories.sqlite.runs_repo import SqliteRunsRepository
from manolo.services.calendar_service import CalendarService
from manolo.services.fx_service import FxService
from manolo.services.memory_service import MemoryService
from manolo.settings import get_settings
from manolo.tools.executor import ToolExecutor
from manolo.tools.registry import build_default_tools


@asynccontextmanager
async def lifespan(app: FastAPI) -> Any:
    """Open DB and HTTP client; close on shutdown."""
    settings = get_settings()
    conn = await connect_database(settings.database_path)
    http = httpx.AsyncClient(timeout=120.0)

    conversations = SqliteConversationsRepository(conn)
    messages = SqliteMessagesRepository(conn)
    runs = SqliteRunsRepository(conn)
    run_steps = SqliteRunStepsRepository(conn)
    calendar_repo = SqliteCalendarRepository(conn)
    fx_cache = SqliteFxCacheRepository(conn)
    memory_repo = SqliteMemoryRepository(conn)

    calendar_service = CalendarService(calendar_repo)
    fx_http = FxHttpProvider(http, settings.fx_api_url)
    fx_service = FxService(fx_cache, fx_http)
    memory_service = MemoryService(memory_repo)
    tools = build_default_tools(calendar_service, fx_service)
    tool_executor = ToolExecutor(
        tools,
        allowed=set(settings.allowed_tools_list()),
    )

    app.state.settings = settings
    app.state.conn = conn
    app.state.http = http
    app.state.conversations = conversations
    app.state.messages = messages
    app.state.runs = runs
    app.state.run_steps = run_steps
    app.state.calendar_service = calendar_service
    app.state.fx_service = fx_service
    app.state.memory_service = memory_service
    app.state.tools = tools
    app.state.tool_executor = tool_executor

    yield

    await conn.close()
    await http.aclose()
