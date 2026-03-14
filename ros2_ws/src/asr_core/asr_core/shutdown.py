"""Helpers for robust ROS node shutdown in launch-managed processes."""

from __future__ import annotations

from typing import Any


def _is_double_shutdown_error(exc: BaseException) -> bool:
    text = str(exc).strip().lower()
    return "rcl_shutdown already called" in text


def _context_ok(context: Any) -> bool:
    try:
        return bool(context.ok())
    except RuntimeError as exc:
        if _is_double_shutdown_error(exc):
            return False
        raise


def _rclpy_ok(rclpy_module: Any, context: Any) -> bool:
    try:
        return bool(rclpy_module.ok(context=context))
    except RuntimeError as exc:
        if _is_double_shutdown_error(exc):
            return False
        raise


def safe_shutdown_node(*, node: Any, rclpy_module: Any) -> None:
    """Destroy node + shutdown context while tolerating launch shutdown races."""
    context = getattr(node, "context", None)
    if context is None:
        return

    if _context_ok(context):
        try:
            node.destroy_node()
        except RuntimeError as exc:
            if not _is_double_shutdown_error(exc):
                raise

    if _rclpy_ok(rclpy_module, context):
        try:
            rclpy_module.shutdown(context=context)
        except RuntimeError as exc:
            if not _is_double_shutdown_error(exc):
                raise
