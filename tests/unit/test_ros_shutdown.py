from __future__ import annotations

import pytest
from asr_core import shutdown as shutdown_module
from asr_ros.shutdown import safe_shutdown_node


pytestmark = pytest.mark.legacy


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


class _FakeSpinRclpy(_FakeRclpy):
    def __init__(self, *, on_spin=None) -> None:
        super().__init__(ok_value=True)
        self.on_spin = on_spin
        self.spin_once_calls = 0

    def spin_once(self, node: object, timeout_sec: float) -> None:
        _ = node
        _ = timeout_sec
        self.spin_once_calls += 1
        if self.on_spin is not None:
            self.on_spin()


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


def test_spin_node_until_shutdown_stops_on_signal_request(monkeypatch) -> None:
    handlers: dict[int, object] = {}

    def fake_getsignal(sig: int) -> object:
        return handlers.get(sig, object())

    def fake_signal(sig: int, handler: object) -> object:
        handlers[sig] = handler
        return handler

    node = _FakeNode(context=_FakeContext(ok_value=True))
    fake_rclpy = _FakeSpinRclpy()

    monkeypatch.setattr(shutdown_module.signal, "getsignal", fake_getsignal)
    monkeypatch.setattr(shutdown_module.signal, "signal", fake_signal)

    def trigger_sigterm() -> None:
        handler = handlers[shutdown_module.signal.SIGTERM]
        handler(shutdown_module.signal.SIGTERM, None)

    fake_rclpy.on_spin = trigger_sigterm

    shutdown_module.spin_node_until_shutdown(node=node, rclpy_module=fake_rclpy, timeout_sec=0.01)

    assert fake_rclpy.spin_once_calls == 1


def test_spin_node_until_shutdown_exits_when_context_is_not_ok(monkeypatch) -> None:
    handlers: dict[int, object] = {}

    monkeypatch.setattr(shutdown_module.signal, "getsignal", lambda sig: handlers.get(sig, object()))
    monkeypatch.setattr(
        shutdown_module.signal,
        "signal",
        lambda sig, handler: handlers.setdefault(sig, handler),
    )

    context = _FakeContext(ok_value=True)
    node = _FakeNode(context=context)

    def mark_context_stopped() -> None:
        context._ok_value = False

    fake_rclpy = _FakeSpinRclpy(on_spin=mark_context_stopped)

    shutdown_module.spin_node_until_shutdown(node=node, rclpy_module=fake_rclpy, timeout_sec=0.01)

    assert fake_rclpy.spin_once_calls == 1
