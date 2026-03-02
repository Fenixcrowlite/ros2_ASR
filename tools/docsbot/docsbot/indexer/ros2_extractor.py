from __future__ import annotations

from pathlib import Path

from docsbot.config import repo_commit

from .interfaces_extractor import extract_interfaces
from .models import ProjectIndex, RepoMeta
from .python_ast_extractor import extract_nodes_from_python
from .repo_scanner import scan_launch_nodes, scan_packages, scan_python_dependencies


def _python_sources(package_path: Path, package_name: str) -> list[Path]:
    candidates: list[Path] = []
    for root in [package_path / package_name, package_path]:
        if not root.exists():
            continue
        for py_file in root.rglob("*.py"):
            if py_file.name == "setup.py" or "/test" in str(py_file):
                continue
            candidates.append(py_file)
    # Deduplicate while preserving order.
    unique: dict[Path, None] = {}
    for item in candidates:
        unique[item] = None
    return list(unique.keys())


def build_project_index(repo_root: Path, workspace_root: Path) -> ProjectIndex:
    packages, package_paths = scan_packages(workspace_root)
    launch_nodes = scan_launch_nodes(workspace_root)
    dependencies = scan_python_dependencies(repo_root)

    nodes = []
    interfaces = []
    for package in packages:
        package_path = package_paths[package.name]
        interfaces.extend(extract_interfaces(package.name, package_path))
        for py_file in _python_sources(package_path, package.name):
            nodes.extend(extract_nodes_from_python(py_file, package.name))

    return ProjectIndex(
        repo=RepoMeta(
            repo_name=repo_root.name,
            repo_root=str(repo_root),
            workspace_root=str(workspace_root),
            commit=repo_commit(repo_root),
        ),
        packages=packages,
        launch_nodes=launch_nodes,
        nodes=nodes,
        interfaces=interfaces,
        dependencies=dependencies,
    )
