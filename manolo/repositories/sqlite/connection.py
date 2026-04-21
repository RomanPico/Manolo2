"""SQLite connection helpers."""

from __future__ import annotations

import importlib.resources
from pathlib import Path
from typing import TYPE_CHECKING

import aiosqlite

if TYPE_CHECKING:
    pass


def _schema_sql() -> str:
    pkg = importlib.resources.files("manolo.repositories.sqlite")
    schema = pkg.joinpath("schema.sql").read_text(encoding="utf-8")
    return schema


async def connect_database(database_path: str) -> aiosqlite.Connection:
    """Open SQLite, apply schema, enable WAL where applicable."""
    if database_path == ":memory:":
        uri = "file:manolo_shared_mem?mode=memory&cache=shared"
        conn = await aiosqlite.connect(uri, uri=True)
    else:
        path = Path(database_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        conn = await aiosqlite.connect(str(path))

    await conn.execute("PRAGMA foreign_keys = ON;")
    await conn.execute("PRAGMA journal_mode = WAL;")

    await conn.executescript(_schema_sql())
    await conn.commit()
    return conn
