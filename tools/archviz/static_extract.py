"""Static architecture extractor.

Builds architecture graph from repository source files without executing ROS nodes.
"""

from __future__ import annotations

import ast
import configparser
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from defusedxml import ElementTree

from tools.archviz.graph import GraphBuilder, dedupe_sorted, new_graph, normalize_node_name

PACKAGE_DEP_TAGS = {
    "depend",
    "exec_depend",
    "build_depend",
    "buildtool_depend",
    "test_depend",
}


@dataclass
class LaunchNodeSpec:
    """Launch `Node(...)` call parsed from `.launch.py` file."""

    package: str
    executable: str
    name: str
    namespace: str
    parameters: list[str]
    remappings: list[str]


@dataclass
class LaunchFileSpec:
    """Launch file metadata used by runtime profiles."""

    package: str
    file: str
    path: str
    declared_args: list[str]
    nodes: list[LaunchNodeSpec]


def _package_dirs(ws_path: Path) -> list[Path]:
    src = ws_path / "src"
    if not src.exists():
        return []
    return sorted(path for path in src.iterdir() if path.is_dir())


def _parse_package_xml(package_xml: Path) -> tuple[str, list[str]]:
    root = ElementTree.parse(package_xml).getroot()
    name = (root.findtext("name") or package_xml.parent.name).strip()
    deps: list[str] = []
    for child in root:
        if child.tag in PACKAGE_DEP_TAGS and child.text:
            deps.append(child.text.strip())
    return name, dedupe_sorted(deps)


def _extract_console_scripts_setup_py(setup_py: Path) -> list[str]:
    source = setup_py.read_text(encoding="utf-8")
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return []

    scripts: list[str] = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        func_name = ""
        if isinstance(node.func, ast.Name):
            func_name = node.func.id
        elif isinstance(node.func, ast.Attribute):
            func_name = node.func.attr
        if func_name != "setup":
            continue

        for kw in node.keywords:
            if kw.arg != "entry_points" or not isinstance(kw.value, ast.Dict):
                continue
            for key_node, val_node in zip(kw.value.keys, kw.value.values, strict=False):
                if not isinstance(key_node, ast.Constant) or key_node.value != "console_scripts":
                    continue
                if not isinstance(val_node, (ast.List, ast.Tuple)):
                    continue
                for item in val_node.elts:
                    if isinstance(item, ast.Constant) and isinstance(item.value, str):
                        scripts.append(item.value.strip())
    return dedupe_sorted(scripts)


def _extract_console_scripts_setup_cfg(setup_cfg: Path) -> list[str]:
    parser = configparser.ConfigParser()
    parser.read(setup_cfg, encoding="utf-8")
    if not parser.has_section("options.entry_points"):
        return []
    raw = parser.get("options.entry_points", "console_scripts", fallback="")
    lines = [line.strip() for line in raw.splitlines()]
    return dedupe_sorted([line for line in lines if line and not line.startswith("#")])


def _parse_interface_file(path: Path, kind: str) -> dict[str, Any]:
    content = path.read_text(encoding="utf-8")
    fields = [
        line.strip()
        for line in content.splitlines()
        if line.strip() and not line.strip().startswith("#")
    ]
    if kind in {"srv", "action"}:
        sections: list[list[str]] = [[]]
        for line in fields:
            if line == "---":
                sections.append([])
                continue
            sections[-1].append(line)
        if kind == "srv":
            return {
                "name": path.stem,
                "kind": kind,
                "request_fields": sections[0] if sections else [],
                "response_fields": sections[1] if len(sections) > 1 else [],
            }
        return {
            "name": path.stem,
            "kind": kind,
            "goal_fields": sections[0] if sections else [],
            "result_fields": sections[1] if len(sections) > 1 else [],
            "feedback_fields": sections[2] if len(sections) > 2 else [],
        }
    return {
        "name": path.stem,
        "kind": kind,
        "fields": fields,
    }


def _literal_string(node: ast.AST | None) -> str:
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return node.value
    return "unknown"


def _type_name(node: ast.AST | None) -> str:
    if node is None:
        return "unknown"
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        parts: list[str] = []
        cur: ast.AST | None = node
        while isinstance(cur, ast.Attribute):
            parts.append(cur.attr)
            cur = cur.value
        if isinstance(cur, ast.Name):
            parts.append(cur.id)
        return ".".join(reversed(parts))
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return node.value
    try:
        return ast.unparse(node)
    except Exception:
        return "unknown"


def _call_name(node: ast.Call) -> str:
    if isinstance(node.func, ast.Name):
        return node.func.id
    if isinstance(node.func, ast.Attribute):
        return node.func.attr
    return ""


def _extract_launch_nodes(launch_path: Path, package_name: str) -> LaunchFileSpec:
    source = launch_path.read_text(encoding="utf-8")
    tree = ast.parse(source)
    declared_args: list[str] = []
    nodes: list[LaunchNodeSpec] = []

    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        name = _call_name(node)
        if name == "DeclareLaunchArgument" and node.args:
            declared_args.append(_literal_string(node.args[0]))
            continue
        if name != "Node":
            continue

        kw = {k.arg: k.value for k in node.keywords if k.arg}
        node_package = _literal_string(kw.get("package"))
        executable = _literal_string(kw.get("executable"))
        node_name = _literal_string(kw.get("name"))
        namespace = _literal_string(kw.get("namespace"))

        if node_name == "unknown":
            node_name = executable if executable != "unknown" else launch_path.stem
        if node_package == "unknown":
            node_package = package_name

        parameter_keys: list[str] = []
        params = kw.get("parameters")
        if isinstance(params, (ast.List, ast.Tuple)):
            for param_item in params.elts:
                if isinstance(param_item, ast.Dict):
                    for key_node in param_item.keys:
                        if isinstance(key_node, ast.Constant) and isinstance(key_node.value, str):
                            parameter_keys.append(key_node.value)

        remappings: list[str] = []
        remap_node = kw.get("remappings")
        if isinstance(remap_node, (ast.List, ast.Tuple)):
            for remap_item in remap_node.elts:
                if isinstance(remap_item, ast.Tuple) and len(remap_item.elts) == 2:
                    left = _literal_string(remap_item.elts[0])
                    right = _literal_string(remap_item.elts[1])
                    remappings.append(f"{left}->{right}")

        nodes.append(
            LaunchNodeSpec(
                package=node_package,
                executable=executable,
                name=node_name,
                namespace=namespace if namespace != "unknown" else "/",
                parameters=dedupe_sorted(parameter_keys),
                remappings=dedupe_sorted(remappings),
            )
        )

    return LaunchFileSpec(
        package=package_name,
        file=launch_path.name,
        path=str(launch_path),
        declared_args=dedupe_sorted(declared_args),
        nodes=nodes,
    )


def _extract_node_name_from_class(class_node: ast.ClassDef) -> str:
    for inner in ast.walk(class_node):
        if not isinstance(inner, ast.Call):
            continue
        if not isinstance(inner.func, ast.Attribute):
            continue
        if inner.func.attr != "__init__":
            continue
        if not isinstance(inner.func.value, ast.Call):
            continue
        if not isinstance(inner.func.value.func, ast.Name):
            continue
        if inner.func.value.func.id != "super":
            continue
        if (
            inner.args
            and isinstance(inner.args[0], ast.Constant)
            and isinstance(inner.args[0].value, str)
        ):
            return inner.args[0].value
    return class_node.name


def _iter_class_calls(class_node: ast.ClassDef, method_names: set[str]) -> list[ast.Call]:
    calls: list[ast.Call] = []
    for inner in ast.walk(class_node):
        if not isinstance(inner, ast.Call):
            continue
        if not isinstance(inner.func, ast.Attribute):
            continue
        if inner.func.attr in method_names:
            calls.append(inner)
    return calls


def _class_looks_like_ros_node(class_node: ast.ClassDef) -> bool:
    for base in class_node.bases:
        base_name = _type_name(base)
        if base_name.endswith("Node"):
            return True
    return False


def _collect_python_ast_bindings(builder: GraphBuilder, ws_path: Path) -> None:
    src_root = ws_path / "src"
    for py_file in sorted(src_root.rglob("*.py")):
        if "/launch/" in py_file.as_posix() or py_file.name == "setup.py":
            continue
        rel = py_file.relative_to(src_root)
        parts = rel.parts
        if len(parts) < 2:
            continue
        package_name = parts[0]

        try:
            tree = ast.parse(py_file.read_text(encoding="utf-8"))
        except SyntaxError:
            continue

        for class_node in [node for node in tree.body if isinstance(node, ast.ClassDef)]:
            calls = _iter_class_calls(
                class_node,
                {
                    "create_publisher",
                    "create_subscription",
                    "create_service",
                    "create_client",
                    "create_timer",
                },
            )
            if not calls and not _class_looks_like_ros_node(class_node):
                continue

            node_name = _extract_node_name_from_class(class_node)
            node_id = normalize_node_name(node_name)
            builder.add_node(
                {
                    "id": node_id,
                    "name": node_name,
                    "namespace": "/",
                    "package": package_name,
                    "executable": "unknown",
                    "source_file": str(py_file),
                },
                evidence=["static_ast"],
            )

            for call in calls:
                method = call.func.attr if isinstance(call.func, ast.Attribute) else ""
                if method in {"create_publisher", "create_subscription"}:
                    msg_type = _type_name(call.args[0]) if call.args else "unknown"
                    topic_name = _literal_string(call.args[1]) if len(call.args) > 1 else "unknown"
                    builder.add_topic(
                        {
                            "name": topic_name,
                            "type": msg_type,
                        },
                        evidence=["static_ast"],
                    )
                    builder.add_edge(
                        {
                            "kind": "topic",
                            "direction": "pub" if method == "create_publisher" else "sub",
                            "node": node_id,
                            "name": topic_name,
                            "type": msg_type,
                            "source_file": str(py_file),
                        },
                        evidence=["static_ast"],
                    )
                    continue

                if method in {"create_service", "create_client"}:
                    srv_type = _type_name(call.args[0]) if call.args else "unknown"
                    service_name = (
                        _literal_string(call.args[1]) if len(call.args) > 1 else "unknown"
                    )
                    builder.add_service(
                        {
                            "name": service_name,
                            "type": srv_type,
                        },
                        evidence=["static_ast"],
                    )
                    builder.add_edge(
                        {
                            "kind": "service",
                            "direction": "server" if method == "create_service" else "client",
                            "node": node_id,
                            "name": service_name,
                            "type": srv_type,
                            "source_file": str(py_file),
                        },
                        evidence=["static_ast"],
                    )
                    continue

                if method == "create_timer":
                    period = _type_name(call.args[0]) if call.args else "unknown"
                    builder.add_edge(
                        {
                            "kind": "timer",
                            "direction": "internal",
                            "node": node_id,
                            "name": f"timer:{period}",
                            "type": "timer",
                            "source_file": str(py_file),
                        },
                        evidence=["static_ast"],
                    )


def _collect_interfaces(
    package_dir: Path, package_name: str, builder: GraphBuilder
) -> list[dict[str, Any]]:
    interfaces: list[dict[str, Any]] = []
    for kind in ("msg", "srv", "action"):
        interface_dir = package_dir / kind
        if not interface_dir.exists():
            continue
        pattern = f"*.{kind}"
        for interface_file in sorted(interface_dir.glob(pattern)):
            parsed = _parse_interface_file(interface_file, kind)
            parsed["package"] = package_name
            parsed["path"] = str(interface_file)
            interfaces.append(parsed)

            full_name = f"/{package_name}/{parsed['name']}"
            if kind == "msg":
                builder.add_topic(
                    {
                        "name": full_name,
                        "type": f"{package_name}/msg/{parsed['name']}",
                        "declared_interface": True,
                    },
                    evidence=["static_interfaces"],
                )
            elif kind == "srv":
                builder.add_service(
                    {
                        "name": full_name,
                        "type": f"{package_name}/srv/{parsed['name']}",
                        "declared_interface": True,
                    },
                    evidence=["static_interfaces"],
                )
            else:
                builder.add_action(
                    {
                        "name": full_name,
                        "type": f"{package_name}/action/{parsed['name']}",
                        "declared_interface": True,
                    },
                    evidence=["static_interfaces"],
                )
    return interfaces


def _collect_launches(
    package_dir: Path, package_name: str, builder: GraphBuilder
) -> list[LaunchFileSpec]:
    launches: list[LaunchFileSpec] = []
    launch_dir = package_dir / "launch"
    if not launch_dir.exists():
        return launches

    for launch_file in sorted(launch_dir.glob("*.launch.py")):
        try:
            launch_spec = _extract_launch_nodes(launch_file, package_name)
        except SyntaxError:
            continue
        launches.append(launch_spec)
        builder.add_launch(
            {
                "package": launch_spec.package,
                "file": launch_spec.file,
                "path": launch_spec.path,
                "declared_args": launch_spec.declared_args,
                "nodes": [
                    {
                        "package": node.package,
                        "executable": node.executable,
                        "name": node.name,
                        "namespace": node.namespace,
                        "parameters": node.parameters,
                        "remappings": node.remappings,
                    }
                    for node in launch_spec.nodes
                ],
            },
            evidence=["static_launch"],
        )

        for launch_node in launch_spec.nodes:
            node_id = normalize_node_name(launch_node.name, launch_node.namespace)
            builder.add_node(
                {
                    "id": node_id,
                    "name": launch_node.name,
                    "namespace": launch_node.namespace,
                    "package": launch_node.package,
                    "executable": launch_node.executable,
                    "launch_file": str(launch_file),
                    "parameters": launch_node.parameters,
                    "remappings": launch_node.remappings,
                },
                evidence=["static_launch"],
            )
    return launches


def extract_static_graph(ws: str) -> dict[str, Any]:
    """Extract architecture graph from workspace source tree."""
    ws_path = Path(ws).resolve()
    graph = new_graph(source="static", workspace=str(ws_path))
    builder = GraphBuilder(graph)

    for package_dir in _package_dirs(ws_path):
        package_xml = package_dir / "package.xml"
        if not package_xml.exists():
            continue

        package_name, deps = _parse_package_xml(package_xml)

        console_scripts: list[str] = []
        setup_py = package_dir / "setup.py"
        setup_cfg = package_dir / "setup.cfg"
        if setup_py.exists():
            console_scripts.extend(_extract_console_scripts_setup_py(setup_py))
        if setup_cfg.exists():
            console_scripts.extend(_extract_console_scripts_setup_cfg(setup_cfg))

        interfaces = _collect_interfaces(package_dir, package_name, builder)
        launches = _collect_launches(package_dir, package_name, builder)

        builder.add_package(
            {
                "name": package_name,
                "path": str(package_dir),
                "dependencies": deps,
                "entry_points": dedupe_sorted(console_scripts),
                "interfaces": interfaces,
                "launch_files": [spec.file for spec in launches],
            },
            evidence=["static_package"],
        )

    _collect_python_ast_bindings(builder, ws_path)

    # Normalize unknown values from AST when string literal was not available.
    for edge in graph["edges"]:
        if edge.get("name") == "unknown":
            edge["name"] = f"unknown::{edge.get('kind')}::{edge.get('direction')}"

    return graph


def discover_launches(ws: str) -> list[dict[str, Any]]:
    """Return lightweight launch index used by runtime profile generation."""
    graph = extract_static_graph(ws)
    launches = [dict(item) for item in graph.get("launches", [])]

    # Keep deterministic order: package + file.
    launches.sort(key=lambda item: (str(item.get("package", "")), str(item.get("file", ""))))
    return launches


def get_package_by_launch_path(path: Path) -> str:
    """Best-effort package name extraction from launch file path."""
    pattern = re.compile(r".*/src/([^/]+)/launch/[^/]+\.launch\.py$")
    match = pattern.match(path.as_posix())
    if not match:
        return "unknown"
    return match.group(1)
