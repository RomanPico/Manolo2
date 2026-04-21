"""Pytest fixtures."""

from __future__ import annotations

import aiosqlite
import pytest_asyncio

from manolo.repositories.sqlite.connection import connect_database


@pytest_asyncio.fixture
async def sqlite_conn() -> aiosqlite.Connection:
    """Shared in-memory SQLite connection."""
    conn = await connect_database(":memory:")
    yield conn
    await conn.close()
