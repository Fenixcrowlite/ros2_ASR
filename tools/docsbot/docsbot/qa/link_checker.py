from __future__ import annotations

import re
from pathlib import Path

LINK_RE = re.compile(r"\[\[([^\]]+)\]\]")


def _normalize_target(link: str) -> str:
    clean = link.split("|", 1)[0].split("#", 1)[0].strip()
    if not clean:
        return ""
    return clean if clean.endswith(".md") else f"{clean}.md"


def _resolve_by_basename(base: Path, target: str) -> bool:
    basename = Path(target).name
    for file_path in base.rglob("*.md"):
        if file_path.name == basename:
            return True
    return False


def check_links(base: Path) -> list[str]:
    errors: list[str] = []
    markdown_files = sorted(base.rglob("*.md"))
    for path in markdown_files:
        text = path.read_text(encoding="utf-8")
        for match in LINK_RE.finditer(text):
            raw_target = match.group(1)
            target = _normalize_target(raw_target)
            if not target:
                continue

            abs_target = (base / target).resolve()
            if abs_target.exists():
                continue

            if _resolve_by_basename(base, target):
                continue

            rel = path.resolve().relative_to(base.resolve())
            errors.append(f"broken link in {rel}: [[{raw_target}]]")
    return sorted(set(errors))
