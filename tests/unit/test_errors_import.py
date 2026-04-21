"""Orchestrator error type."""

from __future__ import annotations

import pytest

from manolo.orchestrator.errors import OrchestratorError


def test_orchestrator_error_is_exception() -> None:
    """Can raise OrchestratorError."""
    with pytest.raises(OrchestratorError):
        raise OrchestratorError("x")
