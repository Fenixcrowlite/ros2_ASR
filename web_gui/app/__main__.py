"""CLI entry point for Web GUI server."""

from __future__ import annotations

import os

import uvicorn


def main() -> None:
    host = os.environ.get("WEB_GUI_HOST", "127.0.0.1")
    port = int(os.environ.get("WEB_GUI_PORT", "8765"))
    uvicorn.run("web_gui.app.main:app", host=host, port=port, reload=True)


if __name__ == "__main__":
    main()
