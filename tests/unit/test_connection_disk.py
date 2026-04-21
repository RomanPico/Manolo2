"""SQLite connection on disk."""

from __future__ import annotations

from pathlib import Path

import pytest

from manolo.repositories.sqlite.connection import connect_database


@pytest.mark.asyncio
async def test_connect_file_db(tmp_path: Path) -> None:
    """Creates file-backed DB."""
    dbfile = tmp_path / "t.sqlite3"
    conn = await connect_database(str(dbfile))
    try:
        await conn.execute("SELECT 1")
    finally:
        await conn.close()
    assert dbfile.exists()
