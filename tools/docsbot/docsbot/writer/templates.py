from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

from docsbot.indexer.models import ProjectIndex
from docsbot.planner.models import TaskPlan
from docsbot.planner.slugger import message_filename, stable_id

from .mermaid import render_dataflow, render_module_map, render_ros_graph, render_wiki_map


def _now_iso() -> str:
    return datetime.now(UTC).isoformat()


def frontmatter(*, page_id: str, title: str, index: ProjectIndex, generated: bool = True) -> str:
    generated_flag = "true" if generated else "false"
    return "\n".join(
        [
            "---",
            f"id: {page_id}",
            f"title: {title}",
            f"generated: {generated_flag}",
            f"source_repo: {index.repo.repo_name}",
            f"source_commit: {index.repo.commit}",
            f"updated_at: {_now_iso()}",
            "tags: [asr, ros2, docsbot]",
            "---",
            "",
        ]
    )


def _entity_marker(*entities: str) -> str:
    clean = [item for item in entities if item]
    return f"<!-- docsbot-entities: {','.join(clean)} -->"


def home_page(index: ProjectIndex) -> str:
    body = [
        "# Wiki Home",
        "",
        _entity_marker(index.repo.repo_name),
        "",
        "## Navigation",
        "- [[01_Project/Overview]]",
        "- [[01_Project/Glossary]]",
        "- [[02_Architecture/Layered Architecture]]",
        "- [[02_Architecture/Dataflow]]",
        "- [[02_Architecture/ROS Graph]]",
        "- [[02_Architecture/Module Map]]",
        "- [[90_Auto/_Index]]",
        "- [[90_Auto/_Generated Graph]]",
        "",
        "## Repository Snapshot",
        f"- Packages: `{len(index.packages)}`",
        f"- Node classes: `{len(index.nodes)}`",
        f"- Interfaces: `{len(index.interfaces)}`",
        f"- Launch node declarations: `{len(index.launch_nodes)}`",
    ]
    return (
        frontmatter(page_id=stable_id("home", "home"), title="Wiki Home", index=index)
        + "\n".join(body)
        + "\n"
    )


def overview_page(index: ProjectIndex) -> str:
    lines = [
        "# Project Overview",
        "",
        _entity_marker(index.repo.repo_name, *[package.name for package in index.packages]),
        "",
        "## Packages",
    ]
    for package in sorted(index.packages, key=lambda item: item.name):
        lines.append(f"- `{package.name}` -> [[04_Modules/{package.name}/{package.name}]]")

    lines.extend(["", "## ROS Nodes"])
    for node in sorted(index.nodes, key=lambda item: item.node_id):
        lines.append(f"- `{node.node_id}` ({Path(node.file).name})")

    lines.extend(["", "## Interfaces"])
    for interface in sorted(
        index.interfaces, key=lambda item: (item.kind, item.package, item.name)
    ):
        if interface.kind == "msg":
            msg_file = message_filename(f"{interface.package}-{interface.name}").replace(".md", "")
            message_link = (
                f"- `{interface.kind}` `{interface.package}/{interface.name}` -> "
                f"[[03_API/Messages/{msg_file}]]"
            )
            lines.append(message_link)
        else:
            lines.append(f"- `{interface.kind}` `{interface.package}/{interface.name}`")

    return (
        frontmatter(
            page_id=stable_id("project", "overview"),
            title="Project Overview",
            index=index,
        )
        + "\n".join(lines)
        + "\n"
    )


def glossary_page(index: ProjectIndex) -> str:
    lines = [
        "# Glossary",
        "",
        _entity_marker("glossary"),
        "",
        "- **ASR**: Automatic Speech Recognition.",
        "- **ROS2 node**: Runtime process unit communicating via topics/services/actions.",
        "- **Topic**: Asynchronous pub/sub channel.",
        "- **Service**: Request-response RPC in ROS2.",
        "- **Action**: Long-running goal-feedback-result interface.",
        "- **WER/CER**: Word/Character error rate metrics.",
        "- **RTF**: Real-time factor (`processing_time / audio_duration`).",
    ]
    return (
        frontmatter(page_id=stable_id("project", "glossary"), title="Glossary", index=index)
        + "\n".join(lines)
        + "\n"
    )


def layered_architecture_page(index: ProjectIndex) -> str:
    lines = [
        "# Layered Architecture",
        "",
        _entity_marker("architecture", *[package.name for package in index.packages]),
        "",
        "## Layers",
        "1. Interfaces (`asr_interfaces`)",
        "2. Core/backends (`asr_core`, `asr_backend_*`)",
        "3. ROS application (`asr_ros`, launch, runtime services)",
        "4. Evaluation (`asr_benchmark`, `asr_metrics`, scripts)",
        "",
        "```mermaid",
        "flowchart TB",
        "  UI[ROS2 Clients] --> ROS[asr_ros]",
        "  ROS --> CORE[asr_core]",
        "  CORE --> BACKENDS[local/cloud backends]",
        "  ROS --> METRICS[asr_metrics]",
        "  METRICS --> BENCH[asr_benchmark/results]",
        "```",
    ]
    return (
        frontmatter(page_id=stable_id("arch", "layered"), title="Layered Architecture", index=index)
        + "\n".join(lines)
        + "\n"
    )


def dataflow_page(index: ProjectIndex) -> str:
    lines = [
        "# Dataflow",
        "",
        _entity_marker("dataflow", *[node.node_id for node in index.nodes]),
        "",
        "```mermaid",
        render_dataflow(index),
        "```",
    ]
    return (
        frontmatter(page_id=stable_id("arch", "dataflow"), title="Dataflow", index=index)
        + "\n".join(lines)
        + "\n"
    )


def ros_graph_page(index: ProjectIndex) -> str:
    lines = [
        "# ROS Graph",
        "",
        _entity_marker("ros_graph", *[node.node_id for node in index.nodes]),
        "",
        "```mermaid",
        render_ros_graph(index),
        "```",
    ]
    return (
        frontmatter(page_id=stable_id("arch", "ros-graph"), title="ROS Graph", index=index)
        + "\n".join(lines)
        + "\n"
    )


def module_map_page(index: ProjectIndex) -> str:
    lines = [
        "# Module Map",
        "",
        _entity_marker("module_map", *[package.name for package in index.packages]),
        "",
        "```mermaid",
        render_module_map(index),
        "```",
    ]
    return (
        frontmatter(page_id=stable_id("arch", "module-map"), title="Module Map", index=index)
        + "\n".join(lines)
        + "\n"
    )


def topic_page(index: ProjectIndex, topic: str) -> str:
    pubs = sorted(
        node.node_id for node in index.nodes if any(ep.name == topic for ep in node.publishers)
    )
    subs = sorted(
        node.node_id for node in index.nodes if any(ep.name == topic for ep in node.subscribers)
    )
    type_names = sorted(
        {
            ep.type_name
            for node in index.nodes
            for ep in [*node.publishers, *node.subscribers]
            if ep.name == topic
        }
    )
    publisher_lines = [f"- `{node}`" for node in pubs] if pubs else ["- none"]
    subscriber_lines = [f"- `{node}`" for node in subs] if subs else ["- none"]
    lines = [
        f"# Topic `{topic}`",
        "",
        _entity_marker(topic, *pubs, *subs),
        "",
        "## Type",
        f"- `{', '.join(type_names) if type_names else 'unknown'}`",
        "",
        "## Publishers",
        *publisher_lines,
        "",
        "## Subscribers",
        *subscriber_lines,
    ]
    return (
        frontmatter(page_id=stable_id("topic", topic), title=f"Topic {topic}", index=index)
        + "\n".join(lines)
        + "\n"
    )


def service_page(index: ProjectIndex, service: str) -> str:
    providers = sorted(
        node.node_id for node in index.nodes if any(ep.name == service for ep in node.services)
    )
    clients = sorted(
        node.node_id for node in index.nodes if any(ep.name == service for ep in node.clients)
    )
    type_names = sorted(
        {
            ep.type_name
            for node in index.nodes
            for ep in [*node.services, *node.clients]
            if ep.name == service
        }
    )
    provider_lines = [f"- `{node}`" for node in providers] if providers else ["- none"]
    client_lines = [f"- `{node}`" for node in clients] if clients else ["- none"]
    lines = [
        f"# Service `{service}`",
        "",
        _entity_marker(service, *providers, *clients),
        "",
        "## Type",
        f"- `{', '.join(type_names) if type_names else 'unknown'}`",
        "",
        "## Servers",
        *provider_lines,
        "",
        "## Clients",
        *client_lines,
    ]
    return (
        frontmatter(page_id=stable_id("service", service), title=f"Service {service}", index=index)
        + "\n".join(lines)
        + "\n"
    )


def message_page(
    index: ProjectIndex, package: str, name: str, fields: list[tuple[str, str, str]]
) -> str:
    lines = [
        f"# Message `{package}/{name}`",
        "",
        _entity_marker(f"{package}/{name}"),
        "",
        "## Fields",
    ]
    for field_name, type_name, section in fields:
        lines.append(f"- `{section}` `{type_name} {field_name}`")
    if not fields:
        lines.append("- none")

    return (
        frontmatter(
            page_id=stable_id("msg", f"{package}/{name}"),
            title=f"Message {package}/{name}",
            index=index,
        )
        + "\n".join(lines)
        + "\n"
    )


def parameter_page(index: ProjectIndex, parameter: str) -> str:
    owners = sorted(
        node.node_id for node in index.nodes if any(p.name == parameter for p in node.parameters)
    )
    defaults = sorted(
        {p.default for node in index.nodes for p in node.parameters if p.name == parameter}
    )
    default_lines = [f"- `{value}`" for value in defaults] if defaults else ["- unknown"]
    owner_lines = [f"- `{owner}`" for owner in owners] if owners else ["- none"]
    lines = [
        f"# Parameter `{parameter}`",
        "",
        _entity_marker(parameter, *owners),
        "",
        "## Default Values",
        *default_lines,
        "",
        "## Declared By",
        *owner_lines,
    ]
    return (
        frontmatter(
            page_id=stable_id("param", parameter),
            title=f"Parameter {parameter}",
            index=index,
        )
        + "\n".join(lines)
        + "\n"
    )


def module_page(index: ProjectIndex, package_name: str) -> str:
    package = next((pkg for pkg in index.packages if pkg.name == package_name), None)
    nodes = sorted(node.node_id for node in index.nodes if node.package == package_name)
    lines = [
        f"# Module `{package_name}`",
        "",
        _entity_marker(package_name, *nodes),
        "",
        f"- Path: `{package.path if package else 'unknown'}`",
        "",
        "## Dependencies",
    ]
    if package and package.dependencies:
        lines.extend(f"- `{dep}`" for dep in package.dependencies)
    else:
        lines.append("- none")

    lines.extend(["", "## Node Classes"])
    lines.extend(f"- `{node}`" for node in nodes)
    if not nodes:
        lines.append("- none")

    return (
        frontmatter(
            page_id=stable_id("module", package_name),
            title=f"Module {package_name}",
            index=index,
        )
        + "\n".join(lines)
        + "\n"
    )


def auto_index_page(index: ProjectIndex, page_paths: list[str], autogen_paths: list[str]) -> str:
    lines = [
        "# Auto Index",
        "",
        _entity_marker("index"),
        "",
        "## Generated Pages",
    ]
    for path in sorted(page_paths):
        lines.append(f"- [[{path.replace('.md', '')}]]")

    lines.extend(["", "## Autogen Fallback Pages"])
    if autogen_paths:
        for path in sorted(autogen_paths):
            lines.append(f"- [[{path.replace('.md', '')}]]")
    else:
        lines.append("- none")

    return (
        frontmatter(page_id=stable_id("auto", "index"), title="Auto Index", index=index)
        + "\n".join(lines)
        + "\n"
    )


def changelog_page(index: ProjectIndex, plan: TaskPlan) -> str:
    summary = plan.summary()
    lines = [
        "# Auto Changelog",
        "",
        _entity_marker("changelog"),
        "",
        f"- Created: `{plan.created_at}`",
        f"- create: `{summary.get('create', 0)}`",
        f"- update: `{summary.get('update', 0)}`",
        f"- delete: `{summary.get('delete', 0)}`",
        f"- skip: `{summary.get('skip', 0)}`",
        "",
        "## Tasks",
    ]
    for task in plan.tasks:
        task_line = (
            f"- `{task.action}` `{task.entity_type}` `{task.entity_id}` -> "
            f"`{task.target_path}` ({task.reason})"
        )
        lines.append(task_line)

    return (
        frontmatter(
            page_id=stable_id("auto", "changelog"),
            title="Auto Changelog",
            index=index,
        )
        + "\n".join(lines)
        + "\n"
    )


def errors_page(index: ProjectIndex, errors: list[str]) -> str:
    lines = ["# Auto Errors", "", _entity_marker("errors"), ""]
    if errors:
        lines.append("## Errors")
        lines.extend(f"- {error}" for error in errors)
    else:
        lines.append("No errors detected.")

    return (
        frontmatter(page_id=stable_id("auto", "errors"), title="Auto Errors", index=index)
        + "\n".join(lines)
        + "\n"
    )


def generated_graph_page(index: ProjectIndex, page_paths: list[str]) -> str:
    lines = [
        "# Generated Graph",
        "",
        _entity_marker("generated-graph"),
        "",
        "```mermaid",
        render_wiki_map(page_paths=page_paths, title=index.repo.repo_name),
        "```",
    ]
    return (
        frontmatter(
            page_id=stable_id("auto", "generated-graph"),
            title="Generated Graph",
            index=index,
        )
        + "\n".join(lines)
        + "\n"
    )
