"""Diff utility for architecture graphs."""

from __future__ import annotations

from pathlib import Path
from typing import Any


def _as_map(items: list[dict[str, Any]], key_field: str) -> dict[str, dict[str, Any]]:
    return {str(item.get(key_field, "")): item for item in items if str(item.get(key_field, ""))}


def _edge_key(edge: dict[str, Any]) -> str:
    return "|".join(
        [
            str(edge.get("kind", "")),
            str(edge.get("direction", "")),
            str(edge.get("node", "")),
            str(edge.get("name", "")),
            str(edge.get("type", "unknown")),
        ]
    )


def _edge_map(items: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    return {_edge_key(edge): edge for edge in items}


def _md_list(items: list[str], empty_text: str = "- None") -> list[str]:
    if not items:
        return [empty_text]
    return [f"- {item}" for item in items]


def build_arch_diff(previous: dict[str, Any], current: dict[str, Any]) -> str:
    """Create markdown changelog between two merged graphs."""
    prev_nodes = _as_map(list(previous.get("nodes", [])), "id")
    curr_nodes = _as_map(list(current.get("nodes", [])), "id")
    prev_topics = _as_map(list(previous.get("topics", [])), "name")
    curr_topics = _as_map(list(current.get("topics", [])), "name")
    prev_services = _as_map(list(previous.get("services", [])), "name")
    curr_services = _as_map(list(current.get("services", [])), "name")

    prev_edges = _edge_map(list(previous.get("edges", [])))
    curr_edges = _edge_map(list(current.get("edges", [])))

    added_nodes = sorted(set(curr_nodes) - set(prev_nodes))
    removed_nodes = sorted(set(prev_nodes) - set(curr_nodes))
    added_topics = sorted(set(curr_topics) - set(prev_topics))
    removed_topics = sorted(set(prev_topics) - set(curr_topics))
    added_services = sorted(set(curr_services) - set(prev_services))
    removed_services = sorted(set(prev_services) - set(curr_services))

    changed_types: list[str] = []
    for name in sorted(set(curr_topics) & set(prev_topics)):
        prev_type = str(prev_topics[name].get("type", "unknown"))
        curr_type = str(curr_topics[name].get("type", "unknown"))
        if prev_type != curr_type:
            changed_types.append(f"topic {name}: {prev_type} -> {curr_type}")

    for name in sorted(set(curr_services) & set(prev_services)):
        prev_type = str(prev_services[name].get("type", "unknown"))
        curr_type = str(curr_services[name].get("type", "unknown"))
        if prev_type != curr_type:
            changed_types.append(f"service {name}: {prev_type} -> {curr_type}")

    added_edges = sorted(set(curr_edges) - set(prev_edges))
    removed_edges = sorted(set(prev_edges) - set(curr_edges))

    runtime_errors = [str(err) for err in current.get("runtime_errors", [])]

    lines: list[str] = [
        "# Architecture Changelog",
        "",
        "## Added",
        "",
        "### Nodes",
        *_md_list(added_nodes),
        "",
        "### Topics",
        *_md_list(added_topics),
        "",
        "### Services",
        *_md_list(added_services),
        "",
        "## Removed",
        "",
        "### Nodes",
        *_md_list(removed_nodes),
        "",
        "### Topics",
        *_md_list(removed_topics),
        "",
        "### Services",
        *_md_list(removed_services),
        "",
        "## Changed Types",
        *_md_list(changed_types),
        "",
        "## Connectivity",
        "",
        "### Added edges",
        *_md_list(added_edges),
        "",
        "### Removed edges",
        *_md_list(removed_edges),
        "",
        "## Runtime Errors",
        f"- Count: {len(runtime_errors)}",
        "- See [runtime_errors.md](runtime_errors.md)",
    ]

    if runtime_errors:
        lines.append("- Latest errors:")
        lines.extend(f"  - {err}" for err in runtime_errors[:10])

    return "\n".join(lines) + "\n"


def diff_graph_files(previous_path: Path, current_path: Path) -> str:
    """Load graphs from files and return markdown diff."""
    import json

    previous = json.loads(previous_path.read_text(encoding="utf-8"))
    current = json.loads(current_path.read_text(encoding="utf-8"))
    return build_arch_diff(previous, current)
