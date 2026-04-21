"""Integration smoke tests."""

from __future__ import annotations

import pytest
from starlette.testclient import TestClient

from manolo.server.app import create_app


@pytest.mark.integration
def test_health_ok() -> None:
    """GET /health returns JSON."""
    with TestClient(create_app()) as client:
        res = client.get("/health")
        assert res.status_code == 200
        assert res.json() == {"status": "ok"}
