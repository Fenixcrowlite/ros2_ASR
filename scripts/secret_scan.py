#!/usr/bin/env python3
"""Fast release-oriented secret scanner."""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

SECRET_RE = re.compile(
    r"AKIA[0-9A-Z]{16}|"
    r"ASIA[0-9A-Z]{16}|"
    r"AIza[0-9A-Za-z_-]{35}|"
    r"-----BEGIN\s+[^-]*PRIVATE KEY-----|"
    r"aws_secret_access_key\s*[:=]\s*['\"]?[A-Za-z0-9/+=]{16,}|"
    r"speech_key\s*[:=]\s*['\"]?[A-Za-z0-9]{16,}|"
    r"subscription_key\s*[:=]\s*['\"]?[A-Za-z0-9]{16,}|"
    r"xox[baprs]-[0-9A-Za-z-]{10,}",
    re.IGNORECASE,
)

DEFAULT_ROOTS = (".ai", "reports", "results", "artifacts", "scripts", "configs", "datasets", "docs")
SKIP_SUFFIXES = {
    ".wav",
    ".mp3",
    ".flac",
    ".png",
    ".jpg",
    ".jpeg",
    ".gif",
    ".webp",
    ".onnx",
    ".pt",
    ".pth",
    ".bin",
    ".safetensors",
    ".tar",
    ".gz",
    ".zip",
}
SKIP_PARTS = {
    ".git",
    ".venv",
    "__pycache__",
    "derived_audio",
    "dist",
    "secrets",
}
SKIP_EXACT_SUFFIXES = (
    "artifacts/benchmark_runs/metrics/results.json",
    "artifacts/benchmark_runs/reports/summary.json",
    "artifacts/benchmark_runs/metrics/results.csv",
)
MAX_TEXT_BYTES = 2_000_000


def _repo_path(path: Path, root: Path) -> str:
    try:
        return path.resolve().relative_to(root.resolve()).as_posix()
    except ValueError:
        return path.as_posix()


def _should_skip(path: Path, root: Path) -> bool:
    rel = _repo_path(path, root)
    parts = set(Path(rel).parts)
    if parts & SKIP_PARTS:
        return True
    if path.suffix.lower() in SKIP_SUFFIXES:
        return True
    if rel.endswith(".env") or path.name == ".env":
        return False
    if path.name.endswith((".example", ".example.yaml", ".example.yml", ".example.json")):
        return True
    if "/artifacts/benchmark_runs/" in f"/{rel}/":
        if rel.endswith(("/metrics/results.json", "/reports/summary.json", "/metrics/results.csv")):
            return True
    return any(rel.endswith(suffix) for suffix in SKIP_EXACT_SUFFIXES)


def _iter_files(root: Path, scan_roots: list[str]) -> list[Path]:
    files: list[Path] = []
    for raw in scan_roots:
        base = root / raw
        if not base.exists():
            continue
        if base.is_file():
            files.append(base)
            continue
        for path in base.rglob("*"):
            if path.is_file() and not _should_skip(path, root):
                files.append(path)
    return sorted(files)


def _scan_file(path: Path, root: Path) -> list[str]:
    findings: list[str] = []
    rel = _repo_path(path, root)
    if path.name == ".env" or rel.endswith(".env"):
        findings.append(f"tracked env file path: {rel}")
    if path.suffix.lower() in {".pem", ".p12", ".key"}:
        findings.append(f"tracked key-like file path: {rel}")
    if re.search(r"service.?account.*\.json$", path.name, re.IGNORECASE):
        findings.append(f"tracked service-account json file path: {rel}")
    try:
        data = path.read_bytes()
    except OSError as exc:
        findings.append(f"could not read {rel}: {exc}")
        return findings
    if len(data) > MAX_TEXT_BYTES:
        return findings
    text = data.decode("utf-8", errors="ignore")
    for line_no, line in enumerate(text.splitlines(), start=1):
        if SECRET_RE.search(line):
            findings.append(f"{rel}:{line_no}:{line[:160]}")
    return findings


def main() -> int:
    parser = argparse.ArgumentParser(description="Fast secret scan for release evidence")
    parser.add_argument("--root", default=".")
    parser.add_argument("--scan-root", action="append", default=[])
    args = parser.parse_args()

    root = Path(args.root).resolve()
    scan_roots = args.scan_root or list(DEFAULT_ROOTS)
    files = _iter_files(root, scan_roots)
    findings: list[str] = []
    for path in files:
        findings.extend(_scan_file(path, root))

    print(f"Scanned files: {len(files)}")
    if findings:
        print("FAIL: potential secrets detected:")
        for finding in findings:
            print(f" - {finding}")
        return 1
    print("PASS: no obvious secrets found")
    return 0


if __name__ == "__main__":
    sys.exit(main())
