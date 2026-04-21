"""Plain key/value memory facade."""

from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone

from manolo.repositories.interfaces import MemoryRepository


class MemoryService:
    """Optional memory persistence."""

    def __init__(self, repo: MemoryRepository) -> None:
        self._repo = repo

    def _now_iso(self) -> str:
        return datetime.now(timezone.utc).replace(microsecond=0).isoformat()

    async def store(self, key: str, value: object, tags: str | None = None) -> str:
        """Persist JSON-serializable value."""
        item_id = str(uuid.uuid4())
        payload = json.dumps(value)
        await self._repo.upsert(
            item_id=item_id,
            key=key,
            tags=tags,
            value_json=payload,
            created_at=self._now_iso(),
        )
        return item_id

    async def load(self, key: str) -> object | None:
        """Load JSON value or None."""
        raw = await self._repo.get_by_key(key)
        if raw is None:
            return None
        return json.loads(raw)
