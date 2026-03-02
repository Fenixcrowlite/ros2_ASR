from __future__ import annotations

import shutil
from datetime import UTC, datetime
from pathlib import Path


class BackupManager:
    def __init__(self, root: Path) -> None:
        timestamp = datetime.now(UTC).strftime("%Y%m%d_%H%M%S")
        self.backup_root = root / timestamp
        self.backup_root.mkdir(parents=True, exist_ok=True)

    def backup(self, path: Path, anchor: Path) -> Path | None:
        if not path.exists():
            return None
        relative = path.resolve().relative_to(anchor.resolve())
        destination = self.backup_root / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(path, destination)
        return destination
