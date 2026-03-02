from __future__ import annotations

import threading
import time
from collections.abc import Callable
from pathlib import Path

from watchdog.events import FileSystemEvent, FileSystemEventHandler
from watchdog.observers import Observer


class _DebouncedHandler(FileSystemEventHandler):
    def __init__(self, on_trigger: Callable[[], None], debounce_sec: float = 1.2) -> None:
        self._on_trigger = on_trigger
        self._debounce_sec = debounce_sec
        self._timer: threading.Timer | None = None
        self._lock = threading.Lock()

    def on_any_event(self, event: FileSystemEvent) -> None:  # noqa: D401
        path = event.src_path
        if any(part in path for part in ["/.git/", "/.docsbot/", "__pycache__", ".pytest_cache"]):
            return
        if path.endswith((".pyc", ".swp", "~")):
            return

        with self._lock:
            if self._timer:
                self._timer.cancel()
            self._timer = threading.Timer(self._debounce_sec, self._on_trigger)
            self._timer.daemon = True
            self._timer.start()


def watch(repo_root: Path, callback: Callable[[], None]) -> None:
    observer = Observer()
    handler = _DebouncedHandler(on_trigger=callback)
    observer.schedule(handler, str(repo_root), recursive=True)
    observer.start()

    try:
        while True:
            time.sleep(0.3)
    except KeyboardInterrupt:
        pass
    finally:
        observer.stop()
        observer.join(timeout=5)
