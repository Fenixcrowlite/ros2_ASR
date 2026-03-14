"""Artifact storage layout and persistence utilities."""

from __future__ import annotations

import hashlib
import json
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from asr_storage.models import ArtifactRef


class ArtifactStore:
    """Create and manage runtime/benchmark artifact structures."""

    def __init__(self, root: str = "artifacts") -> None:
        self.root = Path(root)
        self.runtime_root = self.root / "runtime_sessions"
        self.benchmark_root = self.root / "benchmark_runs"
        self.comparisons_root = self.root / "comparisons"
        self.exports_root = self.root / "exports"
        self.temp_root = self.root / "temp"
        for folder in (
            self.runtime_root,
            self.benchmark_root,
            self.comparisons_root,
            self.exports_root,
            self.temp_root,
        ):
            folder.mkdir(parents=True, exist_ok=True)

    @staticmethod
    def _timestamp() -> str:
        return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")

    def make_runtime_session(self, session_id: str) -> Path:
        session_dir = self.runtime_root / session_id
        for child in ("raw", "normalized", "metrics", "logs"):
            (session_dir / child).mkdir(parents=True, exist_ok=True)
        return session_dir

    def make_benchmark_run(self, run_id: str) -> Path:
        run_dir = self.benchmark_root / run_id
        for child in (
            "manifest",
            "resolved_configs",
            "raw_outputs",
            "normalized_outputs",
            "metrics",
            "reports",
            "logs",
        ):
            (run_dir / child).mkdir(parents=True, exist_ok=True)
        return run_dir

    def build_run_id(self, prefix: str = "run") -> str:
        return f"{prefix}_{self._timestamp()}_{uuid.uuid4().hex[:8]}"

    @staticmethod
    def _checksum(data: bytes) -> str:
        return hashlib.sha256(data).hexdigest()

    @staticmethod
    def _infer_run_id(path: Path) -> str:
        parts = list(path.parts)
        for marker in ("benchmark_runs", "runtime_sessions", "comparisons", "exports"):
            if marker in parts:
                index = parts.index(marker)
                if index + 1 < len(parts):
                    return parts[index + 1]
        return ""

    def save_json(self, path: Path, payload: Any) -> ArtifactRef:
        path.parent.mkdir(parents=True, exist_ok=True)
        encoded = json.dumps(payload, ensure_ascii=True, indent=2).encode("utf-8")
        path.write_bytes(encoded)
        return ArtifactRef(
            run_id=self._infer_run_id(path),
            artifact_type="json",
            path=str(path),
            checksum=self._checksum(encoded),
            size_bytes=len(encoded),
        )

    def save_text(self, path: Path, text: str) -> ArtifactRef:
        path.parent.mkdir(parents=True, exist_ok=True)
        data = text.encode("utf-8")
        path.write_bytes(data)
        return ArtifactRef(
            run_id=self._infer_run_id(path),
            artifact_type="text",
            path=str(path),
            checksum=self._checksum(data),
            size_bytes=len(data),
        )

    def save_manifest(self, run_dir: Path, payload: dict[str, Any]) -> ArtifactRef:
        return self.save_json(run_dir / "manifest" / "run_manifest.json", payload)

    def save_raw_output(self, run_dir: Path, name: str, payload: dict[str, Any]) -> ArtifactRef:
        return self.save_json(run_dir / "raw_outputs" / f"{name}.json", payload)

    def save_normalized_output(
        self,
        run_dir: Path,
        name: str,
        payload: dict[str, Any],
    ) -> ArtifactRef:
        return self.save_json(run_dir / "normalized_outputs" / f"{name}.json", payload)

    def save_metric(self, run_dir: Path, name: str, payload: dict[str, Any]) -> ArtifactRef:
        return self.save_json(run_dir / "metrics" / f"{name}.json", payload)

    def save_report(self, run_dir: Path, name: str, content: str) -> ArtifactRef:
        return self.save_text(run_dir / "reports" / name, content)
