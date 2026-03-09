from __future__ import annotations

from web_gui.app.preflight import run_preflight_checks


def test_preflight_shape() -> None:
    payload = run_preflight_checks()
    assert "ok" in payload
    assert "checks" in payload
    checks = payload["checks"]
    assert "modules" in checks
    assert "microphone" in checks
    assert "ros" in checks
    assert "fastapi" in checks["modules"]
    assert "asr_server_python" in checks["ros"]
    assert "asr_server_faster_whisper" in checks["ros"]
