"""Memory service tests."""

from __future__ import annotations

import pytest

from manolo.repositories.sqlite.memory_repo import SqliteMemoryRepository
from manolo.services.memory_service import MemoryService


@pytest.mark.asyncio
async def test_memory_roundtrip(sqlite_conn) -> None:
    """Store and load JSON."""
    svc = MemoryService(SqliteMemoryRepository(sqlite_conn))
    await svc.store("k", {"a": 1})
    got = await svc.load("k")
    assert got == {"a": 1}


@pytest.mark.asyncio
async def test_memory_missing_key(sqlite_conn) -> None:
    """Missing key returns None."""
    svc = MemoryService(SqliteMemoryRepository(sqlite_conn))
    assert await svc.load("missing") is None
