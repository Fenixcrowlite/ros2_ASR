"""Shared graph data model helpers for architecture extraction pipeline."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


def utc_now_iso() -> str:
    """Return deterministic UTC timestamp string."""
    return datetime.now(tz=UTC).isoformat()


def normalize_node_name(name: str, namespace: str = "") -> str:
    """Normalize ROS2 node names to fully-qualified format with leading slash."""
    clean_name = (name or "unknown_node").strip()
    if clean_name.startswith("/"):
        return clean_name

    clean_ns = (namespace or "").strip()
    if not clean_ns or clean_ns == "/":
        return f"/{clean_name}"

    if not clean_ns.startswith("/"):
        clean_ns = f"/{clean_ns}"
    return f"{clean_ns.rstrip('/')}/{clean_name}"


def ensure_list(value: Any) -> list[Any]:
    """Convert nullable value to list."""
    if value is None:
        return []
    if isinstance(value, list):
        return value
    return [value]


def dedupe_sorted(values: list[str]) -> list[str]:
    """Return sorted list of unique non-empty strings."""
    return sorted({item for item in values if item})


def new_graph(source: str, workspace: str) -> dict[str, Any]:
    """Create empty graph document scaffold."""
    return {
        "meta": {
            "source": source,
            "workspace": workspace,
            "generated_at": utc_now_iso(),
            "schema_version": 1,
        },
        "packages": [],
        "launches": [],
        "nodes": [],
        "topics": [],
        "services": [],
        "actions": [],
        "edges": [],
        "runtime_errors": [],
        "snapshots": [],
    }


def _merge_scalar(primary: Any, secondary: Any) -> Any:
    """Prefer non-empty primary value, fallback to secondary."""
    if primary not in (None, "", "unknown"):
        return primary
    return secondary


@dataclass
class GraphBuilder:
    """Mutable helper around graph document with dedupe indexes."""

    graph: dict[str, Any]
    _pkg_index: dict[str, dict[str, Any]] = field(default_factory=dict)
    _launch_index: dict[tuple[str, str], dict[str, Any]] = field(default_factory=dict)
    _node_index: dict[str, dict[str, Any]] = field(default_factory=dict)
    _topic_index: dict[str, dict[str, Any]] = field(default_factory=dict)
    _service_index: dict[str, dict[str, Any]] = field(default_factory=dict)
    _action_index: dict[str, dict[str, Any]] = field(default_factory=dict)
    _edge_index: dict[tuple[str, str, str, str], dict[str, Any]] = field(default_factory=dict)

    def _merge_with_evidence(
        self, target: dict[str, Any], data: dict[str, Any], evidence: list[str]
    ) -> None:
        for key, value in data.items():
            if key == "evidence":
                continue
            if key not in target:
                target[key] = value
                continue
            if isinstance(value, list):
                target[key] = dedupe_sorted(
                    [str(v) for v in ensure_list(target.get(key)) + ensure_list(value)]
                )
                continue
            target[key] = _merge_scalar(target.get(key), value)
        current_evidence = [str(e) for e in ensure_list(target.get("evidence"))]
        target["evidence"] = dedupe_sorted(current_evidence + evidence)

    def add_package(self, package: dict[str, Any], evidence: list[str]) -> None:
        key = str(package.get("name", ""))
        if not key:
            return
        existing = self._pkg_index.get(key)
        if existing is None:
            obj = dict(package)
            obj["evidence"] = dedupe_sorted([str(e) for e in evidence])
            self.graph["packages"].append(obj)
            self._pkg_index[key] = obj
            return
        self._merge_with_evidence(existing, package, evidence)

    def add_launch(self, launch: dict[str, Any], evidence: list[str]) -> None:
        key = (str(launch.get("package", "")), str(launch.get("file", "")))
        if not all(key):
            return
        existing = self._launch_index.get(key)
        if existing is None:
            obj = dict(launch)
            obj["evidence"] = dedupe_sorted([str(e) for e in evidence])
            self.graph["launches"].append(obj)
            self._launch_index[key] = obj
            return
        self._merge_with_evidence(existing, launch, evidence)

    def add_node(self, node: dict[str, Any], evidence: list[str]) -> None:
        node_id = normalize_node_name(
            str(node.get("id") or node.get("name") or "unknown_node"),
            str(node.get("namespace", "")),
        )
        node_data = dict(node)
        node_data["id"] = node_id
        node_data.setdefault("name", node_id.rsplit("/", maxsplit=1)[-1])
        node_data.setdefault("namespace", "/")
        existing = self._node_index.get(node_id)
        if existing is None:
            node_data["evidence"] = dedupe_sorted([str(e) for e in evidence])
            self.graph["nodes"].append(node_data)
            self._node_index[node_id] = node_data
            return
        self._merge_with_evidence(existing, node_data, evidence)

    def add_topic(self, topic: dict[str, Any], evidence: list[str]) -> None:
        key = str(topic.get("name", ""))
        if not key:
            return
        data = dict(topic)
        data.setdefault("type", "unknown")
        existing = self._topic_index.get(key)
        if existing is None:
            data["evidence"] = dedupe_sorted([str(e) for e in evidence])
            self.graph["topics"].append(data)
            self._topic_index[key] = data
            return
        self._merge_with_evidence(existing, data, evidence)

    def add_service(self, service: dict[str, Any], evidence: list[str]) -> None:
        key = str(service.get("name", ""))
        if not key:
            return
        data = dict(service)
        data.setdefault("type", "unknown")
        existing = self._service_index.get(key)
        if existing is None:
            data["evidence"] = dedupe_sorted([str(e) for e in evidence])
            self.graph["services"].append(data)
            self._service_index[key] = data
            return
        self._merge_with_evidence(existing, data, evidence)

    def add_action(self, action: dict[str, Any], evidence: list[str]) -> None:
        key = str(action.get("name", ""))
        if not key:
            return
        data = dict(action)
        data.setdefault("type", "unknown")
        existing = self._action_index.get(key)
        if existing is None:
            data["evidence"] = dedupe_sorted([str(e) for e in evidence])
            self.graph["actions"].append(data)
            self._action_index[key] = data
            return
        self._merge_with_evidence(existing, data, evidence)

    def add_edge(self, edge: dict[str, Any], evidence: list[str]) -> None:
        kind = str(edge.get("kind", "unknown"))
        direction = str(edge.get("direction", "unknown"))
        node = normalize_node_name(str(edge.get("node", "unknown_node")))
        channel_name = str(edge.get("name", ""))
        channel_type = str(edge.get("type", "unknown"))
        if not channel_name:
            return

        data = dict(edge)
        data["kind"] = kind
        data["direction"] = direction
        data["node"] = node
        data["type"] = channel_type

        key = (kind, direction, node, channel_name)
        existing = self._edge_index.get(key)
        if existing is None:
            data["evidence"] = dedupe_sorted([str(e) for e in evidence])
            self.graph["edges"].append(data)
            self._edge_index[key] = data
            return
        self._merge_with_evidence(existing, data, evidence)

    def add_runtime_error(self, error: str) -> None:
        if not error:
            return
        errors = [str(e) for e in ensure_list(self.graph.get("runtime_errors"))]
        if error not in errors:
            errors.append(error)
        self.graph["runtime_errors"] = errors

    def add_snapshot(self, snapshot: dict[str, Any]) -> None:
        snapshots = ensure_list(self.graph.get("snapshots"))
        snapshots.append(snapshot)
        self.graph["snapshots"] = snapshots


def write_json(path: Path, payload: dict[str, Any]) -> None:
    """Write JSON graph with stable indentation."""
    import json

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")


def read_json(path: Path) -> dict[str, Any]:
    """Read JSON graph document."""
    import json

    return json.loads(path.read_text(encoding="utf-8"))
