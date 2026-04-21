"""FX quote service with optional SQLite cache."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from manolo.providers.fx_http_provider import FxHttpProvider
from manolo.repositories.interfaces import FxCacheRepository


class FxService:
    """Cache-first FX reads."""

    def __init__(self, cache: FxCacheRepository, http: FxHttpProvider) -> None:
        self._cache = cache
        self._http = http

    def _now_iso(self) -> str:
        return datetime.now(timezone.utc).replace(microsecond=0).isoformat()

    async def get_usd_reference(self) -> dict[str, Any]:
        """Return USD-based FX snapshot (uses EUR cross as primary rate)."""
        pair = "USD_EUR"
        cached = await self._cache.get(pair)
        if cached is not None:
            rate, fetched_at = cached
            return {
                "ok": True,
                "pair": pair,
                "rate": rate,
                "fetched_at": fetched_at,
                "cached": True,
            }

        data = await self._http.fetch_latest()
        rates = data.get("rates")
        if not isinstance(rates, dict):
            msg = "FX API missing rates"
            raise ValueError(msg)
        eur = rates.get("EUR")
        if eur is None:
            msg = "FX API missing EUR rate"
            raise ValueError(msg)
        rate = float(eur)
        fetched_at = self._now_iso()
        await self._cache.set(pair, rate, fetched_at)
        return {
            "ok": True,
            "pair": pair,
            "rate": rate,
            "fetched_at": fetched_at,
            "cached": False,
        }
