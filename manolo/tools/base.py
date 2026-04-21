"""Tool base types."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

import jsonschema


class Tool(ABC):
    """LLM-callable tool."""

    name: str
    description: str
    input_schema: dict[str, Any]

    @abstractmethod
    async def execute(self, arguments: dict[str, Any]) -> dict[str, Any]:
        """Run tool with validated arguments."""


def validate_schema(instance: dict[str, Any], schema: dict[str, Any]) -> None:
    """Raise if instance does not match JSON Schema."""
    jsonschema.validate(instance=instance, schema=schema)
