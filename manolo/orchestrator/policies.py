"""Execution policy helpers."""

from __future__ import annotations

from manolo.orchestrator.state import OrchestrationState


def should_stop(state: OrchestrationState) -> bool:
    """Return True if limits exceeded."""
    return state.step_count >= state.max_steps or state.tool_calls_made >= state.max_tool_calls
