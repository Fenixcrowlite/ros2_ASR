from __future__ import annotations

import re
from pathlib import Path

from docsbot.indexer.models import ProjectIndex

ENTITY_MARKER_RE = re.compile(r"<!--\s*docsbot-entities:\s*([^>]+)\s*-->")


ALLOWLIST = {
    "architecture",
    "dataflow",
    "module_map",
    "glossary",
    "index",
    "changelog",
    "errors",
    "generated-graph",
    "ros_graph",
    "home",
}


def check_hallucinations(base: Path, index: ProjectIndex) -> list[str]:
    known = index.known_entities() | ALLOWLIST
    errors: list[str] = []
    for path in sorted(base.rglob("*.md")):
        text = path.read_text(encoding="utf-8")
        for marker in ENTITY_MARKER_RE.findall(text):
            entities = [item.strip() for item in marker.split(",") if item.strip()]
            for entity in entities:
                if entity not in known:
                    rel = path.resolve().relative_to(base.resolve())
                    errors.append(f"unknown entity marker in {rel}: {entity}")
    return sorted(set(errors))
