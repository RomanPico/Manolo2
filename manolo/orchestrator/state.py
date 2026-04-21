"""Orchestrator execution state."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class OrchestrationState:
    """Tracks one assistant run."""

    run_id: str
    conversation_id: str
    user_message: str
    messages: list[dict[str, Any]] = field(default_factory=list)
    step_count: int = 0
    max_steps: int = 10
    tool_calls_made: int = 0
    max_tool_calls: int = 10
    status: str = "running"
    final_answer: str | None = None
    last_error: str | None = None
