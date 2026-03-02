from __future__ import annotations

import re
from pathlib import Path

MERMAID_BLOCK_RE = re.compile(r"```mermaid\n(.*?)\n```", re.DOTALL)
VALID_HEADERS = (
    "graph",
    "flowchart",
    "sequenceDiagram",
    "mindmap",
    "classDiagram",
    "stateDiagram",
    "erDiagram",
    "journey",
    "gantt",
)


def _balanced(text: str, left: str, right: str) -> bool:
    count = 0
    for char in text:
        if char == left:
            count += 1
        elif char == right:
            count -= 1
            if count < 0:
                return False
    return count == 0


def check_mermaid(base: Path) -> list[str]:
    errors: list[str] = []
    for path in sorted(base.rglob("*.md")):
        text = path.read_text(encoding="utf-8")
        for block in MERMAID_BLOCK_RE.findall(text):
            stripped = block.strip()
            if not stripped:
                errors.append(f"empty mermaid block in {path}")
                continue
            first_line = stripped.splitlines()[0].strip()
            if not first_line.startswith(VALID_HEADERS):
                errors.append(f"invalid mermaid header in {path}: {first_line}")
            if not _balanced(stripped, "(", ")"):
                errors.append(f"unbalanced parentheses in {path}")
            if not _balanced(stripped, "[", "]"):
                errors.append(f"unbalanced brackets in {path}")
            if not _balanced(stripped, "{", "}"):
                errors.append(f"unbalanced braces in {path}")
    return sorted(set(errors))
