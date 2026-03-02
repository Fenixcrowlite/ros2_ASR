from __future__ import annotations

import ast
from dataclasses import dataclass, field
from pathlib import Path

from .models import Endpoint, NodeInfo, ParameterInfo


@dataclass
class _NodeDraft:
    class_name: str
    file: str
    package: str
    publishers: list[Endpoint] = field(default_factory=list)
    subscribers: list[Endpoint] = field(default_factory=list)
    services: list[Endpoint] = field(default_factory=list)
    clients: list[Endpoint] = field(default_factory=list)
    parameters: list[ParameterInfo] = field(default_factory=list)
    timers: int = 0


class _NodeVisitor(ast.NodeVisitor):
    def __init__(self, file_path: Path, package: str) -> None:
        self.file_path = file_path
        self.package = package
        self.nodes: dict[str, _NodeDraft] = {}
        self._current_class: str | None = None
        self._is_node_class: bool = False

    @staticmethod
    def _name_of(expr: ast.AST) -> str:
        if isinstance(expr, ast.Name):
            return expr.id
        if isinstance(expr, ast.Attribute):
            return expr.attr
        return "unknown"

    @staticmethod
    def _string_of(expr: ast.AST) -> str:
        if isinstance(expr, ast.Constant) and isinstance(expr.value, str):
            return expr.value
        if isinstance(expr, ast.JoinedStr):
            return "fstring"
        return "unknown"

    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        previous_class = self._current_class
        previous_is_node = self._is_node_class

        base_names = {self._name_of(base) for base in node.bases}
        self._current_class = node.name
        self._is_node_class = "Node" in base_names or "LifecycleNode" in base_names
        if self._is_node_class:
            self.nodes[node.name] = _NodeDraft(
                class_name=node.name,
                file=str(self.file_path),
                package=self.package,
            )

        self.generic_visit(node)
        self._current_class = previous_class
        self._is_node_class = previous_is_node

    def _current(self) -> _NodeDraft | None:
        if not self._current_class:
            return None
        return self.nodes.get(self._current_class)

    def visit_Call(self, node: ast.Call) -> None:
        current = self._current()
        if not current or not isinstance(node.func, ast.Attribute):
            self.generic_visit(node)
            return

        method = node.func.attr
        args = node.args

        def endpoint(direction: str, name_idx: int = 1, type_idx: int = 0) -> Endpoint:
            type_name = self._name_of(args[type_idx]) if len(args) > type_idx else "unknown"
            name = self._string_of(args[name_idx]) if len(args) > name_idx else "unknown"
            return Endpoint(name=name, type_name=type_name, direction=direction)

        if method == "create_publisher":
            current.publishers.append(endpoint("pub"))
        elif method == "create_subscription":
            current.subscribers.append(endpoint("sub"))
        elif method == "create_service":
            current.services.append(endpoint("srv"))
        elif method == "create_client":
            current.clients.append(endpoint("client"))
        elif method == "create_timer":
            current.timers += 1
        elif method == "declare_parameter":
            name = self._string_of(args[0]) if args else "unknown"
            default = (
                repr(args[1].value)
                if len(args) > 1 and isinstance(args[1], ast.Constant)
                else "unknown"
            )
            current.parameters.append(
                ParameterInfo(
                    name=name,
                    default=default,
                    source_file=str(self.file_path),
                    node_id=f"{self.package}:{current.class_name}",
                )
            )
        elif method == "declare_parameters" and len(args) > 1 and isinstance(args[1], ast.List):
            for item in args[1].elts:
                if isinstance(item, ast.Tuple) and item.elts:
                    name = self._string_of(item.elts[0])
                    default = (
                        repr(item.elts[1].value)
                        if len(item.elts) > 1 and isinstance(item.elts[1], ast.Constant)
                        else "unknown"
                    )
                    current.parameters.append(
                        ParameterInfo(
                            name=name,
                            default=default,
                            source_file=str(self.file_path),
                            node_id=f"{self.package}:{current.class_name}",
                        )
                    )

        self.generic_visit(node)


def extract_nodes_from_python(file_path: Path, package: str) -> list[NodeInfo]:
    try:
        tree = ast.parse(file_path.read_text(encoding="utf-8"), filename=str(file_path))
    except (OSError, SyntaxError, UnicodeDecodeError):
        return []

    visitor = _NodeVisitor(file_path=file_path, package=package)
    visitor.visit(tree)

    result: list[NodeInfo] = []
    for draft in visitor.nodes.values():
        result.append(
            NodeInfo(
                node_id=f"{package}:{draft.class_name}",
                package=package,
                file=draft.file,
                class_name=draft.class_name,
                publishers=draft.publishers,
                subscribers=draft.subscribers,
                services=draft.services,
                clients=draft.clients,
                parameters=draft.parameters,
                timers=draft.timers,
            )
        )
    return result
