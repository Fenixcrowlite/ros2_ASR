from __future__ import annotations

import pytest
from asr_ros.shutdown import safe_shutdown_node


class _FakeContext:
    def __init__(self, *, ok_value: bool = True, ok_error: RuntimeError | None = None) -> None:
        self._ok_value = ok_value
        self._ok_error = ok_error

    def ok(self) -> bool:
        if self._ok_error is not None:
            raise self._ok_error
        return self._ok_value


class _FakeNode:
    def __init__(self, *, context: _FakeContext, destroy_error: RuntimeError | None = None) -> None:
        self.context = context
        self.destroy_called = 0
        self._destroy_error = destroy_error

    def destroy_node(self) -> None:
        self.destroy_called += 1
        if self._destroy_error is not None:
            raise self._destroy_error


class _FakeRclpy:
    def __init__(
        self,
        *,
        ok_value: bool = True,
        ok_error: RuntimeError | None = None,
        shutdown_error: RuntimeError | None = None,
    ) -> None:
        self._ok_value = ok_value
        self._ok_error = ok_error
        self._shutdown_error = shutdown_error
        self.shutdown_called = 0

    def ok(self, *, context: object) -> bool:
        _ = context
        if self._ok_error is not None:
            raise self._ok_error
        return self._ok_value

    def shutdown(self, *, context: object) -> None:
        _ = context
        self.shutdown_called += 1
        if self._shutdown_error is not None:
            raise self._shutdown_error


def test_safe_shutdown_node_runs_destroy_and_shutdown() -> None:
    node = _FakeNode(context=_FakeContext(ok_value=True))
    fake_rclpy = _FakeRclpy(ok_value=True)

    safe_shutdown_node(node=node, rclpy_module=fake_rclpy)

    assert node.destroy_called == 1
    assert fake_rclpy.shutdown_called == 1


def test_safe_shutdown_node_suppresses_double_shutdown_runtime_error() -> None:
    node = _FakeNode(
        context=_FakeContext(ok_value=True),
        destroy_error=RuntimeError("failed to shutdown: rcl_shutdown already called"),
    )
    fake_rclpy = _FakeRclpy(
        ok_value=True,
        shutdown_error=RuntimeError("failed to shutdown: rcl_shutdown already called"),
    )

    safe_shutdown_node(node=node, rclpy_module=fake_rclpy)

    assert node.destroy_called == 1
    assert fake_rclpy.shutdown_called == 1


def test_safe_shutdown_node_propagates_unexpected_runtime_error() -> None:
    node = _FakeNode(
        context=_FakeContext(ok_value=True),
        destroy_error=RuntimeError("unexpected destroy error"),
    )
    fake_rclpy = _FakeRclpy(ok_value=True)

    with pytest.raises(RuntimeError, match="unexpected destroy error"):
        safe_shutdown_node(node=node, rclpy_module=fake_rclpy)
