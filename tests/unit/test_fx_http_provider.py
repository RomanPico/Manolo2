"""Fx HTTP provider."""

from __future__ import annotations

import httpx
import pytest
import respx

from manolo.providers.fx_http_provider import FxHttpProvider


@pytest.mark.asyncio
@respx.mock
async def test_fetch_latest_ok() -> None:
    """Parses JSON object."""
    respx.get("https://x.test/latest").mock(return_value=httpx.Response(200, json={"a": 1}))
    async with httpx.AsyncClient() as client:
        p = FxHttpProvider(client, "https://x.test/latest")
        data = await p.fetch_latest()
        assert data["a"] == 1


@pytest.mark.asyncio
@respx.mock
async def test_fetch_latest_not_object() -> None:
    """Raises on non-object JSON."""
    respx.get("https://x.test/latest").mock(return_value=httpx.Response(200, json=[1]))
    async with httpx.AsyncClient() as client:
        p = FxHttpProvider(client, "https://x.test/latest")
        with pytest.raises(ValueError):
            await p.fetch_latest()
