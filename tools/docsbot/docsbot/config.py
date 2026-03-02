from __future__ import annotations

import json
import os
import subprocess
from collections.abc import Iterable
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

DEFAULT_DOCS_SUBFOLDER = "Wiki-ASR"


@dataclass(slots=True)
class DocsbotConfig:
    repo_root: Path
    vault_root: Path
    docs_subfolder: str
    docs_root: Path
    cache_dir: Path
    logs_dir: Path
    backups_dir: Path
    openai_api_key: str | None
    docsbot_model: str


@dataclass(slots=True)
class DetectionResult:
    repo_root: Path
    vault_root: Path
    docs_root: Path
    docs_subfolder: str


def _run_checked(cmd: list[str], cwd: Path | None = None) -> str | None:
    try:
        result = subprocess.run(
            cmd,
            cwd=str(cwd) if cwd else None,
            check=True,
            capture_output=True,
            text=True,
        )
        return result.stdout.strip()
    except (OSError, subprocess.CalledProcessError):
        return None


def detect_repo_root(start: Path | None = None) -> Path:
    """Detect repository root with git-first strategy and ROS2/Python fallback."""
    start_path = (start or Path.cwd()).resolve()

    git_root = _run_checked(["git", "rev-parse", "--show-toplevel"], cwd=start_path)
    if git_root:
        return Path(git_root).resolve()

    for base in [start_path, *start_path.parents]:
        if (base / ".git").exists():
            return base
        if any(
            (base / marker).exists() for marker in ("package.xml", "setup.py", "pyproject.toml")
        ):
            if (base / "ros2_ws").exists() or (base / "src").exists():
                return base

    return start_path


def _vault_candidates(home: Path) -> Iterable[Path]:
    common = [
        home / "Desktop",  # user-specified priority in this environment
        home / "Obsidian",
        home / "Documents",
        home / "vault",
        home / "Vault",
        home / "obsidian",
        home / "Notes",
    ]
    seen: set[Path] = set()
    for root in common:
        if root in seen:
            continue
        seen.add(root)
        yield root


def _find_obsidian_vaults(home: Path) -> list[Path]:
    candidates: list[Path] = []
    for root in _vault_candidates(home):
        if not root.exists():
            continue

        if (root / ".obsidian").is_dir():
            candidates.append(root)

        # Scan one level below each common root to keep detection fast and deterministic.
        for child in root.iterdir():
            if child.is_dir() and (child / ".obsidian").is_dir():
                candidates.append(child)

    # Last fallback: shallow scan in home for hidden-agnostic vaults.
    for child in home.iterdir():
        if child.is_dir() and (child / ".obsidian").is_dir():
            candidates.append(child)

    unique: dict[Path, float] = {}
    for vault in candidates:
        obs = vault / ".obsidian"
        try:
            unique[vault.resolve()] = obs.stat().st_mtime
        except OSError:
            continue

    return sorted(unique.keys(), key=lambda p: unique[p], reverse=True)


def detect_vault_root(home: Path | None = None) -> Path:
    home_dir = (home or Path.home()).resolve()
    vaults = _find_obsidian_vaults(home_dir)
    if vaults:
        return vaults[0]

    # Create a safe default vault.
    fallback = home_dir / "Obsidian" / "Vault-ASR"
    (fallback / ".obsidian").mkdir(parents=True, exist_ok=True)
    return fallback


def resolve_docs_subfolder(vault_root: Path, subfolder: str | None = None) -> str:
    name = (subfolder or os.getenv("DOCSBOT_OBSIDIAN_SUBFOLDER") or DEFAULT_DOCS_SUBFOLDER).strip()
    if not name:
        name = DEFAULT_DOCS_SUBFOLDER
    (vault_root / name).mkdir(parents=True, exist_ok=True)
    return name


def load_config(
    repo_root: Path | None = None,
    vault_root: Path | None = None,
    docs_subfolder: str | None = None,
) -> DocsbotConfig:
    repo = detect_repo_root(repo_root)
    vault = detect_vault_root() if vault_root is None else Path(vault_root).resolve()
    subfolder = resolve_docs_subfolder(vault, docs_subfolder)

    docs_root = vault / subfolder
    docs_root.mkdir(parents=True, exist_ok=True)

    docsbot_root = repo / ".docsbot"
    cache_dir = docsbot_root / "cache"
    logs_dir = docsbot_root / "logs"
    backups_dir = docsbot_root / "backups"
    cache_dir.mkdir(parents=True, exist_ok=True)
    logs_dir.mkdir(parents=True, exist_ok=True)
    backups_dir.mkdir(parents=True, exist_ok=True)

    model = os.getenv("DOCSBOT_MODEL", "gpt-4.1-mini")

    return DocsbotConfig(
        repo_root=repo,
        vault_root=vault,
        docs_subfolder=subfolder,
        docs_root=docs_root,
        cache_dir=cache_dir,
        logs_dir=logs_dir,
        backups_dir=backups_dir,
        openai_api_key=os.getenv("OPENAI_API_KEY"),
        docsbot_model=model,
    )


def detect(
    repo_root: Path | None = None, vault_root: Path | None = None, docs_subfolder: str | None = None
) -> DetectionResult:
    cfg = load_config(repo_root=repo_root, vault_root=vault_root, docs_subfolder=docs_subfolder)
    return DetectionResult(
        repo_root=cfg.repo_root,
        vault_root=cfg.vault_root,
        docs_root=cfg.docs_root,
        docs_subfolder=cfg.docs_subfolder,
    )


def repo_commit(repo_root: Path) -> str:
    commit = _run_checked(["git", "rev-parse", "HEAD"], cwd=repo_root)
    return commit if commit else "no-git"


def write_detection_snapshot(cfg: DocsbotConfig) -> Path:
    payload = {
        "repo_root": str(cfg.repo_root),
        "vault_root": str(cfg.vault_root),
        "docs_root": str(cfg.docs_root),
        "docs_subfolder": cfg.docs_subfolder,
        "commit": repo_commit(cfg.repo_root),
        "timestamp": datetime.now(UTC).isoformat(),
    }
    out = cfg.cache_dir / "detection.json"
    out.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return out
