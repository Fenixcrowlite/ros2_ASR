"""Helpers for robust ROS node shutdown in launch-managed processes."""

from __future__ import annotations

import signal
from signal import Handlers, Signals
from threading import Event
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


def spin_node_until_shutdown(*, node: Any, rclpy_module: Any, timeout_sec: float = 0.2) -> None:
    """Spin a node while reacting promptly to SIGINT/SIGTERM from ros2 launch."""
    context = getattr(node, "context", None)
    if context is None:
        return

    stop_requested = Event()
    previous_handlers: dict[Signals, Any] = {}

    def _request_stop(signum: int, _frame: Any) -> None:
        _ = signum
        stop_requested.set()

    for sig in (signal.SIGINT, signal.SIGTERM):
        try:
            previous_handlers[sig] = signal.getsignal(sig)
            signal.signal(sig, _request_stop)
        except (AttributeError, ValueError):
            continue

    try:
        while not stop_requested.is_set():
            if not _context_ok(context) or not _rclpy_ok(rclpy_module, context):
                break
            try:
                rclpy_module.spin_once(node, timeout_sec=timeout_sec)
            except KeyboardInterrupt:
                stop_requested.set()
            except RuntimeError as exc:
                if _is_double_shutdown_error(exc):
                    break
                raise
    finally:
        for sig, previous in previous_handlers.items():
            try:
                signal.signal(sig, previous)
            except (AttributeError, ValueError):
                continue
