"""Mermaid renderers for architecture graphs."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any


def _sanitize(identifier: str) -> str:
    return re.sub(r"[^a-zA-Z0-9_]", "_", identifier.strip("/")) or "root"


def _state_text(item: dict[str, Any]) -> str:
    return str(item.get("state", "both"))


def _escape_text(value: str) -> str:
    escaped = value.replace('"', "'").replace("|", "/").strip()
    escaped = escaped.replace("<", "&lt;").replace(">", "&gt;")
    return escaped


def _edge_arrow(state: str, direction: str) -> str:
    if state == "expected_only":
        return "-.->"
    if direction == "sub":
        return "-->"
    return "-->"


def render_mindmap(graph: dict[str, Any], out_path: Path) -> None:
    """Render package -> nodes -> channels hierarchy in broadly compatible Mermaid syntax.

    Note: some Mermaid renderers/extensions do not support native `mindmap` syntax.
    We intentionally render the "mind-map layer" as a top-down flowchart tree
    to maximize compatibility across VS Code plugins and CI renderers.
    """
    nodes_by_package: dict[str, list[dict[str, Any]]] = {}
    for node in graph.get("nodes", []):
        pkg = str(node.get("package", "unknown"))
        nodes_by_package.setdefault(pkg, []).append(node)

    edges_by_node: dict[str, list[dict[str, Any]]] = {}
    for edge in graph.get("edges", []):
        edges_by_node.setdefault(str(edge.get("node", "")), []).append(edge)

    lines: list[str] = [
        "flowchart TB",
        "  classDef expectedOnly stroke-dasharray: 5 5,stroke:#666,fill:#fff8dc;",
        "  classDef observedOnly stroke:#1e88e5,fill:#e3f2fd;",
        '  ROOT(["ASR Architecture"])',
    ]

    def apply_state_class(node_id: str, state: str) -> None:
        if state == "expected_only":
            lines.append(f"  class {node_id} expectedOnly;")
        elif state == "observed_only":
            lines.append(f"  class {node_id} observedOnly;")

    for package_name in sorted(nodes_by_package):
        package_id = f"P_{_sanitize(package_name)}"
        package_label = _escape_text(f"package: {package_name}")
        lines.append(f'  {package_id}["{package_label}"]')
        lines.append(f"  ROOT --> {package_id}")
        for node in sorted(nodes_by_package[package_name], key=lambda n: str(n.get("id", ""))):
            node_id = str(node.get("id", ""))
            node_mermaid_id = f"N_{_sanitize(node_id)}"
            node_label = _escape_text(f"node: {node_id} / state={_state_text(node)}")
            lines.append(f'  {node_mermaid_id}["{node_label}"]')
            lines.append(f"  {package_id} --> {node_mermaid_id}")
            apply_state_class(node_mermaid_id, _state_text(node))

            for edge in sorted(
                edges_by_node.get(node_id, []),
                key=lambda e: (str(e.get("kind", "")), str(e.get("name", ""))),
            ):
                channel_name = str(edge.get("name", "unknown"))
                direction = str(edge.get("direction", "unknown"))
                edge_kind = str(edge.get("kind", "unknown"))
                edge_type = str(edge.get("type", "unknown"))
                edge_id = f"M_{_sanitize(f'{node_id}_{edge_kind}_{direction}_{channel_name}')}"
                edge_state = _state_text(edge)
                edge_label = _escape_text(
                    f"{edge_kind} {direction}: {channel_name} / {edge_type} / state={edge_state}"
                )
                lines.append(f'  {edge_id}["{edge_label}"]')
                lines.append(f"  {node_mermaid_id} --> {edge_id}")
                apply_state_class(edge_id, edge_state)

    out_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def render_flow(graph: dict[str, Any], out_path: Path) -> None:
    """Render node/channel flowchart with expected-only dashed styling."""
    lines = [
        "flowchart LR",
        "  classDef expectedOnly stroke-dasharray: 5 5,stroke:#666,fill:#fff8dc;",
        "  classDef observedOnly stroke:#1e88e5,fill:#e3f2fd;",
    ]

    node_declared: set[str] = set()
    channel_declared: set[str] = set()

    def declare_node(item: dict[str, Any]) -> str:
        node_name = str(item.get("id", "unknown_node"))
        mermaid_id = f"N_{_sanitize(node_name)}"
        if mermaid_id in node_declared:
            return mermaid_id
        label = _escape_text(f"{node_name}<br/>[{item.get('package', 'unknown')}]")
        lines.append(f'  {mermaid_id}["{label}"]')
        state = str(item.get("state", "both"))
        if state == "expected_only":
            lines.append(f"  class {mermaid_id} expectedOnly;")
        elif state == "observed_only":
            lines.append(f"  class {mermaid_id} observedOnly;")
        node_declared.add(mermaid_id)
        return mermaid_id

    def declare_channel(kind: str, name: str, state: str) -> str:
        prefix = "T" if kind == "topic" else "S" if kind == "service" else "A"
        channel_id = f"{prefix}_{_sanitize(name)}"
        if channel_id in channel_declared:
            return channel_id
        label = _escape_text(name)
        shape = '(["' + label + '"])' if kind == "topic" else '{{"' + label + '"}}'
        lines.append(f"  {channel_id}{shape}")
        if state == "expected_only":
            lines.append(f"  class {channel_id} expectedOnly;")
        elif state == "observed_only":
            lines.append(f"  class {channel_id} observedOnly;")
        channel_declared.add(channel_id)
        return channel_id

    node_index = {str(node.get("id", "")): node for node in graph.get("nodes", [])}
    topic_index = {str(topic.get("name", "")): topic for topic in graph.get("topics", [])}
    service_index = {str(service.get("name", "")): service for service in graph.get("services", [])}
    action_index = {str(action.get("name", "")): action for action in graph.get("actions", [])}

    for edge in sorted(
        graph.get("edges", []),
        key=lambda e: (
            str(e.get("kind", "")),
            str(e.get("name", "")),
            str(e.get("direction", "")),
            str(e.get("node", "")),
        ),
    ):
        kind = str(edge.get("kind", ""))
        if kind not in {"topic", "service", "action"}:
            continue

        edge_state = str(edge.get("state", "both"))
        direction = str(edge.get("direction", ""))
        node_name = str(edge.get("node", ""))
        channel_name = str(edge.get("name", ""))
        channel_type = str(edge.get("type", "unknown"))

        node_obj = node_index.get(
            node_name, {"id": node_name, "package": "unknown", "state": edge_state}
        )
        node_id = declare_node(node_obj)

        channel_obj = {}
        if kind == "topic":
            channel_obj = topic_index.get(channel_name, {"name": channel_name, "state": edge_state})
        elif kind == "service":
            channel_obj = service_index.get(
                channel_name, {"name": channel_name, "state": edge_state}
            )
        else:
            channel_obj = action_index.get(
                channel_name, {"name": channel_name, "state": edge_state}
            )
        channel_state = str(channel_obj.get("state", edge_state))
        channel_id = declare_channel(kind, channel_name, channel_state)

        arrow = _edge_arrow(edge_state, direction)
        label = _escape_text(f"{direction}: {channel_name}<br/>{channel_type}")
        if kind == "topic" and direction == "sub":
            lines.append(f"  {channel_id} {arrow}|{label}| {node_id}")
        elif kind in {"service", "action"} and direction == "client":
            lines.append(f"  {channel_id} {arrow}|{label}| {node_id}")
        else:
            lines.append(f"  {node_id} {arrow}|{label}| {channel_id}")

    out_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def render_sequence_recognize_once(graph: dict[str, Any], out_path: Path) -> None:
    """Render request-response sequence for `/asr/recognize_once`."""
    recognize_edges = [
        edge
        for edge in graph.get("edges", [])
        if str(edge.get("kind", "")) == "service"
        and str(edge.get("name", "")) == "/asr/recognize_once"
        and str(edge.get("direction", "")) == "server"
    ]

    if recognize_edges:
        server_node = str(recognize_edges[0].get("node", "/asr_server_node"))
        service_type = str(recognize_edges[0].get("type", "asr_interfaces/srv/RecognizeOnce"))
    else:
        server_node = "/asr_server_node"
        service_type = "asr_interfaces/srv/RecognizeOnce"

    has_text_publish = any(
        str(edge.get("kind", "")) == "topic"
        and str(edge.get("direction", "")) == "pub"
        and str(edge.get("name", "")) == "/asr/text"
        for edge in graph.get("edges", [])
    )
    has_metrics_publish = any(
        str(edge.get("kind", "")) == "topic"
        and str(edge.get("direction", "")) == "pub"
        and str(edge.get("name", "")) == "/asr/metrics"
        for edge in graph.get("edges", [])
    )

    lines = [
        "sequenceDiagram",
        '  participant Client as "Recognize Client"',
        f'  participant Server as "{_escape_text(server_node)}"',
        '  participant TextTopic as "/asr/text"',
        '  participant MetricsTopic as "/asr/metrics"',
        f"  Client->>Server: {_escape_text(f'/asr/recognize_once request ({service_type})')}",
        "  Server-->>Client: RecognizeOnce response",
    ]

    if has_text_publish:
        lines.append("  Server-)TextTopic: publish AsrResult")
    else:
        lines.append("  Note over Server,TextTopic: /asr/text publish not observed")

    if has_metrics_publish:
        lines.append("  Server-)MetricsTopic: publish AsrMetrics")
    else:
        lines.append("  Note over Server,MetricsTopic: /asr/metrics publish not observed")

    out_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def render_mermaid(graph: dict[str, Any], out_dir: str) -> dict[str, Path]:
    """Render all Mermaid outputs and return generated file paths."""
    out_path = Path(out_dir)
    out_path.mkdir(parents=True, exist_ok=True)

    files = {
        "mindmap": out_path / "mindmap.mmd",
        "flow": out_path / "flow.mmd",
        "sequence": out_path / "seq_recognize_once.mmd",
    }

    render_mindmap(graph, files["mindmap"])
    render_flow(graph, files["flow"])
    render_sequence_recognize_once(graph, files["sequence"])

    return files
