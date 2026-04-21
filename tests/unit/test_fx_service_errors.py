"""FxService error paths."""

from __future__ import annotations

import httpx
import pytest
import respx

from manolo.providers.fx_http_provider import FxHttpProvider
from manolo.repositories.sqlite.fx_cache_repo import SqliteFxCacheRepository
from manolo.services.fx_service import FxService


@pytest.mark.asyncio
@respx.mock
async def test_fx_missing_rates(sqlite_conn) -> None:
    """Raises when rates missing."""
    respx.get("https://open.er-api.com/v6/latest/USD").mock(
        return_value=httpx.Response(200, json={"result": "success"}),
    )
    async with httpx.AsyncClient() as client:
        fx = FxService(
            SqliteFxCacheRepository(sqlite_conn),
            FxHttpProvider(client, "https://open.er-api.com/v6/latest/USD"),
        )
        with pytest.raises(ValueError):
            await fx.get_usd_reference()


@pytest.mark.asyncio
@respx.mock
async def test_fx_missing_eur(sqlite_conn) -> None:
    """Raises when EUR missing."""
    respx.get("https://open.er-api.com/v6/latest/USD").mock(
        return_value=httpx.Response(200, json={"result": "success", "rates": {}}),
    )
    async with httpx.AsyncClient() as client:
        fx = FxService(
            SqliteFxCacheRepository(sqlite_conn),
            FxHttpProvider(client, "https://open.er-api.com/v6/latest/USD"),
        )
        with pytest.raises(ValueError):
            await fx.get_usd_reference()
