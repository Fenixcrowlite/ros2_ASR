"""Merge static and runtime graphs with anti-gap policy."""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path
from typing import Any

from tools.archviz.graph import dedupe_sorted, new_graph

EntityKeyFn = Callable[[dict[str, Any]], str]


def _state(in_static: bool, in_runtime: bool) -> str:
    if in_static and in_runtime:
        return "both"
    if in_static:
        return "expected_only"
    return "observed_only"


def _choose_type(static_val: Any, runtime_val: Any) -> str:
    static_type = str(static_val or "")
    runtime_type = str(runtime_val or "")
    if static_type in ("", "unknown"):
        return runtime_type or "unknown"
    if runtime_type in ("", "unknown"):
        return static_type
    if "/" not in static_type and "/" in runtime_type:
        return runtime_type
    if static_type in runtime_type and len(runtime_type) > len(static_type):
        return runtime_type
    return static_type


def _merge_item(
    static_item: dict[str, Any], runtime_item: dict[str, Any], state: str
) -> dict[str, Any]:
    merged = dict(runtime_item)
    merged.update(static_item)
    merged["state"] = state
    merged["evidence"] = dedupe_sorted(
        [
            str(ev)
            for ev in list(static_item.get("evidence", [])) + list(runtime_item.get("evidence", []))
        ]
    )

    for field in ("type", "package", "executable", "namespace", "name", "id", "kind", "direction"):
        static_val = static_item.get(field)
        runtime_val = runtime_item.get(field)
        if field == "type":
            merged[field] = _choose_type(static_val, runtime_val)
            continue
        if static_val in (None, "", "unknown"):
            merged[field] = runtime_val
        else:
            merged[field] = static_val

    if merged.get("type") in (None, ""):
        merged["type"] = "unknown"

    return merged


def _merge_entities(
    static_items: list[dict[str, Any]],
    runtime_items: list[dict[str, Any]],
    key_fn: EntityKeyFn,
) -> list[dict[str, Any]]:
    static_map = {key_fn(item): item for item in static_items if key_fn(item)}
    runtime_map = {key_fn(item): item for item in runtime_items if key_fn(item)}

    all_keys = sorted(set(static_map) | set(runtime_map))
    merged_items: list[dict[str, Any]] = []

    for key in all_keys:
        static_item = static_map.get(key, {})
        runtime_item = runtime_map.get(key, {})
        merged_items.append(
            _merge_item(
                static_item=static_item,
                runtime_item=runtime_item,
                state=_state(key in static_map, key in runtime_map),
            )
        )

    return merged_items


def _edge_key(edge: dict[str, Any]) -> str:
    return "|".join(
        [
            str(edge.get("kind", "")),
            str(edge.get("direction", "")),
            str(edge.get("node", "")),
            str(edge.get("name", "")),
        ]
    )


def merge_graphs(static_graph: dict[str, Any], runtime_graph: dict[str, Any]) -> dict[str, Any]:
    """Merge static and runtime graphs preserving all static entities."""
    workspace = str(
        static_graph.get("meta", {}).get("workspace")
        or runtime_graph.get("meta", {}).get("workspace")
        or ""
    )
    merged = new_graph(source="merged", workspace=workspace)

    merged["packages"] = sorted(
        {
            str(pkg.get("name", "")): pkg
            for pkg in list(static_graph.get("packages", []))
            + list(runtime_graph.get("packages", []))
        }.values(),
        key=lambda item: str(item.get("name", "")),
    )

    merged["launches"] = sorted(
        {
            f"{item.get('package', '')}::{item.get('file', '')}": item
            for item in list(static_graph.get("launches", []))
            + list(runtime_graph.get("launches", []))
        }.values(),
        key=lambda item: (str(item.get("package", "")), str(item.get("file", ""))),
    )

    merged["nodes"] = _merge_entities(
        static_items=list(static_graph.get("nodes", [])),
        runtime_items=list(runtime_graph.get("nodes", [])),
        key_fn=lambda item: str(item.get("id", "")),
    )

    merged["topics"] = _merge_entities(
        static_items=list(static_graph.get("topics", [])),
        runtime_items=list(runtime_graph.get("topics", [])),
        key_fn=lambda item: str(item.get("name", "")),
    )

    merged["services"] = _merge_entities(
        static_items=list(static_graph.get("services", [])),
        runtime_items=list(runtime_graph.get("services", [])),
        key_fn=lambda item: str(item.get("name", "")),
    )

    merged["actions"] = _merge_entities(
        static_items=list(static_graph.get("actions", [])),
        runtime_items=list(runtime_graph.get("actions", [])),
        key_fn=lambda item: str(item.get("name", "")),
    )

    merged["edges"] = _merge_entities(
        static_items=list(static_graph.get("edges", [])),
        runtime_items=list(runtime_graph.get("edges", [])),
        key_fn=_edge_key,
    )

    merged["runtime_errors"] = dedupe_sorted(
        [str(err) for err in list(runtime_graph.get("runtime_errors", []))]
    )
    merged["snapshots"] = list(runtime_graph.get("snapshots", []))

    merged["meta"]["sources"] = {
        "static_nodes": len(static_graph.get("nodes", [])),
        "runtime_nodes": len(runtime_graph.get("nodes", [])),
        "merged_nodes": len(merged.get("nodes", [])),
    }
    return merged


def merge_from_files(static_path: Path, runtime_path: Path) -> dict[str, Any]:
    """Load input JSON files and return merged graph."""
    import json

    static_graph = json.loads(static_path.read_text(encoding="utf-8"))
    runtime_graph = json.loads(runtime_path.read_text(encoding="utf-8"))
    return merge_graphs(static_graph, runtime_graph)
