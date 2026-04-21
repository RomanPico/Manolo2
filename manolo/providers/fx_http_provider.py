"""HTTP client for open.er-api.com (or compatible) FX JSON."""

from __future__ import annotations

from typing import Any

import httpx


class FxHttpProvider:
    """Fetches latest FX data for a base currency."""

    def __init__(self, client: httpx.AsyncClient, fx_api_url: str) -> None:
        self._client = client
        self._fx_api_url = fx_api_url

    async def fetch_latest(self) -> dict[str, Any]:
        """Return parsed JSON body."""
        resp = await self._client.get(self._fx_api_url)
        resp.raise_for_status()
        data = resp.json()
        if not isinstance(data, dict):
            msg = "FX API returned non-object JSON"
            raise ValueError(msg)
        return data
