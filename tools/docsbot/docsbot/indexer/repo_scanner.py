from __future__ import annotations

import ast
import re
from pathlib import Path

from defusedxml import ElementTree

from .models import DependencyInfo, LaunchNode, PackageInfo


def _extract_console_scripts_from_setup_py(setup_py: Path) -> dict[str, str]:
    scripts: dict[str, str] = {}
    try:
        text = setup_py.read_text(encoding="utf-8")
    except OSError:
        return scripts

    # Works for common patterns: 'name = module:main'.
    for match in re.finditer(
        r"['\"]([a-zA-Z0-9_\-]+)\s*=\s*([a-zA-Z0-9_\.]+:[a-zA-Z0-9_]+)['\"]", text
    ):
        scripts[match.group(1)] = match.group(2)
    return scripts


def _extract_console_scripts_from_setup_cfg(setup_cfg: Path) -> dict[str, str]:
    scripts: dict[str, str] = {}
    try:
        text = setup_cfg.read_text(encoding="utf-8")
    except OSError:
        return scripts

    in_console = False
    for raw in text.splitlines():
        line = raw.strip()
        if line.startswith("[options.entry_points]"):
            in_console = True
            continue
        if in_console and line.startswith("[") and not line.startswith("[options.entry_points]"):
            break
        if in_console and "=" in line:
            key, value = [part.strip() for part in line.split("=", 1)]
            if key and value and ":" in value:
                scripts[key] = value
    return scripts


def _parse_launch_node_call(call: ast.Call, launch_file: Path) -> LaunchNode | None:
    if isinstance(call.func, ast.Name):
        fn_name = call.func.id
    elif isinstance(call.func, ast.Attribute):
        fn_name = call.func.attr
    else:
        return None

    if fn_name != "Node":
        return None

    kwargs: dict[str, str] = {
        "package": "unknown",
        "executable": "unknown",
        "name": launch_file.stem,
        "namespace": "",
    }
    parameters: list[str] = []
    remappings: list[str] = []

    for kw in call.keywords:
        if not kw.arg:
            continue
        if isinstance(kw.value, ast.Constant) and isinstance(kw.value.value, str):
            kwargs[kw.arg] = kw.value.value
        elif kw.arg == "parameters":
            parameters.append(ast.unparse(kw.value) if hasattr(ast, "unparse") else "<parameters>")
        elif kw.arg == "remappings":
            remappings.append(ast.unparse(kw.value) if hasattr(ast, "unparse") else "<remappings>")

    return LaunchNode(
        launch_file=str(launch_file),
        package=kwargs.get("package", "unknown"),
        executable=kwargs.get("executable", "unknown"),
        node_name=kwargs.get("name", launch_file.stem),
        namespace=kwargs.get("namespace", ""),
        parameters=parameters,
        remappings=remappings,
    )


def parse_launch_file(launch_file: Path) -> list[LaunchNode]:
    try:
        tree = ast.parse(launch_file.read_text(encoding="utf-8"), filename=str(launch_file))
    except (OSError, SyntaxError, UnicodeDecodeError):
        return []

    launch_nodes: list[LaunchNode] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            parsed = _parse_launch_node_call(node, launch_file)
            if parsed:
                launch_nodes.append(parsed)
    return launch_nodes


def scan_packages(workspace_root: Path) -> tuple[list[PackageInfo], dict[str, Path]]:
    packages: list[PackageInfo] = []
    package_paths: dict[str, Path] = {}

    for package_xml in sorted(workspace_root.glob("src/**/package.xml")):
        package_path = package_xml.parent
        try:
            root = ElementTree.fromstring(package_xml.read_text(encoding="utf-8"))
        except ElementTree.ParseError:
            continue

        name = root.findtext("name", default=package_path.name).strip()
        dependencies = sorted(
            {
                dep.text.strip()
                for dep in root.findall("depend")
                + root.findall("exec_depend")
                + root.findall("build_depend")
                if dep.text and dep.text.strip()
            }
        )

        console_scripts = {}
        setup_py = package_path / "setup.py"
        setup_cfg = package_path / "setup.cfg"
        if setup_py.exists():
            console_scripts.update(_extract_console_scripts_from_setup_py(setup_py))
        if setup_cfg.exists():
            console_scripts.update(_extract_console_scripts_from_setup_cfg(setup_cfg))

        packages.append(
            PackageInfo(
                name=name,
                path=str(package_path),
                dependencies=dependencies,
                console_scripts=console_scripts,
            )
        )
        package_paths[name] = package_path

    return packages, package_paths


def scan_launch_nodes(workspace_root: Path) -> list[LaunchNode]:
    launch_nodes: list[LaunchNode] = []
    for launch_file in sorted(workspace_root.glob("src/**/launch/*.launch.py")):
        launch_nodes.extend(parse_launch_file(launch_file))
    return launch_nodes


def scan_python_dependencies(repo_root: Path) -> list[DependencyInfo]:
    deps: list[DependencyInfo] = []
    requirements = repo_root / "requirements.txt"
    if requirements.exists():
        for line in requirements.read_text(encoding="utf-8").splitlines():
            dep = line.strip()
            if dep and not dep.startswith("#"):
                deps.append(DependencyInfo(name=dep, source="requirements.txt"))
    return deps
