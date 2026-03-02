"""CLI entry point for Web GUI server."""

from __future__ import annotations

import uvicorn


def main() -> None:
    uvicorn.run("web_gui.app.main:app", host="0.0.0.0", port=8765, reload=True)


if __name__ == "__main__":
    main()
