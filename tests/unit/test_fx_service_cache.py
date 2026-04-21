"""FxService cache behavior."""

from __future__ import annotations

import httpx
import pytest
import respx

from manolo.providers.fx_http_provider import FxHttpProvider
from manolo.repositories.sqlite.fx_cache_repo import SqliteFxCacheRepository
from manolo.services.fx_service import FxService


@pytest.mark.asyncio
@respx.mock
async def test_fx_service_uses_cache_second_call(sqlite_conn) -> None:
    """Second call hits SQLite cache."""
    route = respx.get("https://open.er-api.com/v6/latest/USD").mock(
        return_value=httpx.Response(
            200,
            json={"result": "success", "base_code": "USD", "rates": {"EUR": 0.5}},
        ),
    )
    async with httpx.AsyncClient() as client:
        fx = FxService(
            SqliteFxCacheRepository(sqlite_conn),
            FxHttpProvider(client, "https://open.er-api.com/v6/latest/USD"),
        )
        first = await fx.get_usd_reference()
        second = await fx.get_usd_reference()
        assert first["cached"] is False
        assert second["cached"] is True
        assert route.call_count == 1
