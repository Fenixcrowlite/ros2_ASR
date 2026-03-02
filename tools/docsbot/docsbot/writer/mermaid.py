from __future__ import annotations

from docsbot.indexer.models import ProjectIndex


def _node_id(text: str) -> str:
    return "n_" + "".join(ch if ch.isalnum() else "_" for ch in text)


def render_ros_graph(index: ProjectIndex) -> str:
    lines = ["graph LR"]
    for node in index.nodes:
        node_id = _node_id(node.node_id)
        lines.append(f'  {node_id}["{node.node_id}"]')
        for endpoint in node.publishers:
            topic_id = _node_id(f"topic_{endpoint.name}")
            label = endpoint.type_name or "unknown"
            lines.append(f'  {topic_id}["{endpoint.name}\\n{label}"]')
            lines.append(f"  {node_id} -->|pub| {topic_id}")
        for endpoint in node.subscribers:
            topic_id = _node_id(f"topic_{endpoint.name}")
            label = endpoint.type_name or "unknown"
            lines.append(f'  {topic_id}["{endpoint.name}\\n{label}"]')
            lines.append(f"  {topic_id} -->|sub| {node_id}")
        for endpoint in node.services:
            service_id = _node_id(f"service_{endpoint.name}")
            label = endpoint.type_name or "unknown"
            lines.append(f'  {service_id}["{endpoint.name}\\n{label}"]')
            lines.append(f"  {node_id} -->|srv| {service_id}")
        for endpoint in node.clients:
            service_id = _node_id(f"service_{endpoint.name}")
            label = endpoint.type_name or "unknown"
            lines.append(f'  {service_id}["{endpoint.name}\\n{label}"]')
            lines.append(f"  {node_id} -->|client| {service_id}")
    if len(lines) == 1:
        lines.append('  empty["No nodes detected"]')
    return "\n".join(lines)


def render_module_map(index: ProjectIndex) -> str:
    lines = ["graph TD"]
    for package in index.packages:
        package_id = _node_id(f"pkg_{package.name}")
        lines.append(f'  {package_id}["Package: {package.name}"]')
        matched_nodes = [node for node in index.nodes if node.package == package.name]
        if not matched_nodes:
            leaf_id = _node_id(f"leaf_{package.name}")
            lines.append(f'  {leaf_id}["No Node classes detected"]')
            lines.append(f"  {package_id} --> {leaf_id}")
        for node in matched_nodes:
            node_id = _node_id(node.node_id)
            lines.append(f'  {node_id}["{node.class_name}"]')
            lines.append(f"  {package_id} --> {node_id}")
    if len(lines) == 1:
        lines.append('  empty["No packages detected"]')
    return "\n".join(lines)


def render_dataflow(index: ProjectIndex) -> str:
    lines = ["flowchart LR"]
    for node in index.nodes:
        node_id = _node_id(node.node_id)
        lines.append(f'  {node_id}["{node.node_id}"]')
    for node in index.nodes:
        node_id = _node_id(node.node_id)
        for endpoint in node.publishers:
            topic_id = _node_id(endpoint.name)
            lines.append(f'  {topic_id}(("{endpoint.name}"))')
            lines.append(f"  {node_id} --> {topic_id}")
        for endpoint in node.subscribers:
            topic_id = _node_id(endpoint.name)
            lines.append(f'  {topic_id}(("{endpoint.name}"))')
            lines.append(f"  {topic_id} --> {node_id}")
    if len(lines) == 1:
        lines.append('  empty(["No flow detected"])')
    return "\n".join(lines)


def render_wiki_map(page_paths: list[str], title: str = "Wiki-ASR") -> str:
    lines = ["mindmap", f"  root(({title}))"]
    for rel in sorted(page_paths):
        parts = rel.split("/")
        indent = "  "
        for part in parts:
            clean = part.replace(".md", "")
            indent += "  "
            lines.append(f"{indent}{clean}")
    return "\n".join(lines)
