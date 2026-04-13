"""Typed ROS parameter access helpers.

Avoids the untyped `.value` shortcut so nodes read the underlying
`ParameterValue` fields explicitly and predictably.
"""

from __future__ import annotations

from typing import Any

_PARAMETER_NOT_SET = 0
_PARAMETER_BOOL = 1
_PARAMETER_INTEGER = 2
_PARAMETER_DOUBLE = 3
_PARAMETER_STRING = 4


def parameter_scalar(node: Any, name: str) -> Any:
    """Read a parameter and return a plain Python scalar when possible."""
    value = node.get_parameter(name).get_parameter_value()
    param_type = int(getattr(value, "type", _PARAMETER_NOT_SET) or _PARAMETER_NOT_SET)
    if param_type == _PARAMETER_BOOL:
        return bool(value.bool_value)
    if param_type == _PARAMETER_INTEGER:
        return int(value.integer_value)
    if param_type == _PARAMETER_DOUBLE:
        return float(value.double_value)
    if param_type == _PARAMETER_STRING:
        return value.string_value
    return None


def parameter_string(node: Any, name: str, *, default: str = "") -> str:
    """Read a parameter as string with a fallback default."""
    value = parameter_scalar(node, name)
    if value is None:
        return default
    return str(value)


def parameter_bool(node: Any, name: str, *, default: bool = False) -> bool:
    """Read a parameter as bool, accepting common string spellings."""
    value = parameter_scalar(node, name)
    if value is None:
        return default
    if isinstance(value, str):
        normalized = value.strip().lower()
        if normalized in {"1", "true", "yes", "on"}:
            return True
        if normalized in {"0", "false", "no", "off"}:
            return False
        return default
    return bool(value)


def parameter_int(node: Any, name: str, *, default: int = 0) -> int:
    """Read a parameter as int with permissive scalar coercion."""
    value = parameter_scalar(node, name)
    if value is None:
        return default
    if isinstance(value, bool):
        return int(value)
    if isinstance(value, int):
        return value
    if isinstance(value, float):
        return int(value)
    try:
        return int(str(value).strip())
    except (TypeError, ValueError):
        return default


def parameter_float(node: Any, name: str, *, default: float = 0.0) -> float:
    """Read a parameter as float with permissive scalar coercion."""
    value = parameter_scalar(node, name)
    if value is None:
        return default
    if isinstance(value, bool):
        return float(value)
    if isinstance(value, (int, float)):
        return float(value)
    try:
        return float(str(value).strip())
    except (TypeError, ValueError):
        return default
