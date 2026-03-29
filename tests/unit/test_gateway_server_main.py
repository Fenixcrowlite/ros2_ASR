from __future__ import annotations

from asr_gateway.main import main


def test_gateway_main_defaults_to_loopback(monkeypatch) -> None:
    captured: dict[str, object] = {}

    monkeypatch.delenv("ASR_GATEWAY_HOST", raising=False)
    monkeypatch.delenv("ASR_GATEWAY_PORT", raising=False)
    monkeypatch.delenv("ASR_GATEWAY_RELOAD", raising=False)
    monkeypatch.setattr(
        "asr_gateway.main.uvicorn.run",
        lambda app, host, port, reload: captured.update(
            {"app": app, "host": host, "port": port, "reload": reload}
        ),
    )

    main()

    assert captured["app"] == "asr_gateway.api:app"
    assert captured["host"] == "127.0.0.1"
    assert captured["port"] == 8088
    assert captured["reload"] is False
