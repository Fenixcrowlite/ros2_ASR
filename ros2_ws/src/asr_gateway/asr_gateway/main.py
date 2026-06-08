"""ASR gateway server entrypoint."""

from __future__ import annotations

import os

import uvicorn


def main() -> None:
    host = os.getenv("ASR_GATEWAY_HOST", "127.0.0.1").strip() or "127.0.0.1"
    try:
        port = int(os.getenv("ASR_GATEWAY_PORT", "8088").strip() or "8088")
    except ValueError:
        port = 8088

    reload_enabled = os.getenv("ASR_GATEWAY_RELOAD", "").strip().lower() in {"1", "true", "yes", "on"}
    uvicorn.run("asr_gateway.api:app", host=host, port=port, reload=reload_enabled)


if __name__ == "__main__":
    main()
