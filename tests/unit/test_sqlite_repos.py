"""SQLite repository tests."""

from __future__ import annotations

import uuid

import pytest

from manolo.repositories.sqlite.calendar_repo import SqliteCalendarRepository
from manolo.repositories.sqlite.conversations_repo import SqliteConversationsRepository
from manolo.repositories.sqlite.fx_cache_repo import SqliteFxCacheRepository
from manolo.repositories.sqlite.memory_repo import SqliteMemoryRepository
from manolo.repositories.sqlite.messages_repo import SqliteMessagesRepository
from manolo.repositories.sqlite.run_steps_repo import SqliteRunStepsRepository
from manolo.repositories.sqlite.runs_repo import SqliteRunsRepository


@pytest.mark.asyncio
async def test_conversations_crud(sqlite_conn) -> None:
    """Create and list conversations."""
    repo = SqliteConversationsRepository(sqlite_conn)
    cid = str(uuid.uuid4())
    await repo.create(cid, "t", "2020-01-01T00:00:00+00:00")
    all_c = await repo.list_all()
    assert len(all_c) == 1
    got = await repo.get(cid)
    assert got is not None
    assert got.title == "t"


@pytest.mark.asyncio
async def test_messages_append(sqlite_conn) -> None:
    """Append messages."""
    conv = SqliteConversationsRepository(sqlite_conn)
    msg = SqliteMessagesRepository(sqlite_conn)
    cid = str(uuid.uuid4())
    await conv.create(cid, None, "2020-01-01T00:00:00+00:00")
    mid = str(uuid.uuid4())
    await msg.append(mid, cid, "user", "hi", None, "2020-01-01T00:00:01+00:00")
    rows = await msg.list_for_conversation(cid)
    assert len(rows) == 1
    assert rows[0].content == "hi"


@pytest.mark.asyncio
async def test_runs_finalize(sqlite_conn) -> None:
    """Runs lifecycle."""
    conv = SqliteConversationsRepository(sqlite_conn)
    runs = SqliteRunsRepository(sqlite_conn)
    cid = str(uuid.uuid4())
    await conv.create(cid, None, "2020-01-01T00:00:00+00:00")
    rid = str(uuid.uuid4())
    await runs.create(rid, cid, "running", "2020-01-01T00:00:00+00:00")
    await runs.finalize(rid, "completed", "ok", None, "2020-01-01T00:00:01+00:00")


@pytest.mark.asyncio
async def test_run_steps_append(sqlite_conn) -> None:
    """Run steps."""
    conv = SqliteConversationsRepository(sqlite_conn)
    runs = SqliteRunsRepository(sqlite_conn)
    steps = SqliteRunStepsRepository(sqlite_conn)
    cid = str(uuid.uuid4())
    await conv.create(cid, None, "2020-01-01T00:00:00+00:00")
    rid = str(uuid.uuid4())
    await runs.create(rid, cid, "running", "2020-01-01T00:00:00+00:00")
    await steps.append(str(uuid.uuid4()), rid, 1, "x", "{}", "2020-01-01T00:00:00+00:00")


@pytest.mark.asyncio
async def test_calendar_repo(sqlite_conn) -> None:
    """Calendar CRUD."""
    cal = SqliteCalendarRepository(sqlite_conn)
    eid = str(uuid.uuid4())
    await cal.save_event(
        eid,
        "Meet",
        "2025-01-01T10:00:00+00:00",
        None,
        None,
        None,
        "2025-01-01T09:00:00+00:00",
    )
    rows = await cal.lookup(None, None, 10)
    assert len(rows) == 1
    assert await cal.erase(eid) is True


@pytest.mark.asyncio
async def test_fx_cache(sqlite_conn) -> None:
    """FX cache upsert."""
    fx = SqliteFxCacheRepository(sqlite_conn)
    await fx.set("USD_EUR", 0.9, "2025-01-01T00:00:00+00:00")
    got = await fx.get("USD_EUR")
    assert got is not None
    assert got[0] == 0.9


@pytest.mark.asyncio
async def test_memory_repo(sqlite_conn) -> None:
    """Memory KV."""
    mem = SqliteMemoryRepository(sqlite_conn)
    await mem.upsert(str(uuid.uuid4()), "k", "t", "{}", "2025-01-01T00:00:00+00:00")
    assert await mem.get_by_key("k") == "{}"
