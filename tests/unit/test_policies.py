"""Policy tests."""

from __future__ import annotations

from manolo.orchestrator.policies import should_stop
from manolo.orchestrator.state import OrchestrationState


def test_should_stop_at_limit() -> None:
    """Stop when step cap reached."""
    s = OrchestrationState(
        run_id="r",
        conversation_id="c",
        user_message="m",
        step_count=10,
        max_steps=10,
    )
    assert should_stop(s) is True


def test_should_not_stop_under_limit() -> None:
    """Continue when under cap."""
    s = OrchestrationState(
        run_id="r",
        conversation_id="c",
        user_message="m",
        step_count=3,
        max_steps=10,
    )
    assert should_stop(s) is False
