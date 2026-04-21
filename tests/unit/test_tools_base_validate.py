"""tools.base validate_schema."""

from __future__ import annotations

import jsonschema

import pytest

from manolo.tools.base import validate_schema


def test_validate_schema_ok() -> None:
    """Valid instance passes."""
    validate_schema({"x": 1}, {"type": "object", "properties": {"x": {"type": "integer"}}})


def test_validate_schema_raises() -> None:
    """Invalid instance raises."""
    with pytest.raises(jsonschema.ValidationError):
        validate_schema({"x": "a"}, {"type": "object", "properties": {"x": {"type": "integer"}}})
