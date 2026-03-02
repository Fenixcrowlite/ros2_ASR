from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

from pydantic import BaseModel, Field


class RepoMeta(BaseModel):
    repo_name: str
    repo_root: str
    workspace_root: str
    commit: str
    generated_at: str = Field(default_factory=lambda: datetime.now(UTC).isoformat())


class PackageInfo(BaseModel):
    name: str
    path: str
    dependencies: list[str] = Field(default_factory=list)
    console_scripts: dict[str, str] = Field(default_factory=dict)


class LaunchNode(BaseModel):
    launch_file: str
    package: str
    executable: str
    node_name: str
    namespace: str = ""
    parameters: list[str] = Field(default_factory=list)
    remappings: list[str] = Field(default_factory=list)


class Endpoint(BaseModel):
    name: str
    type_name: str
    direction: str


class ParameterInfo(BaseModel):
    name: str
    default: str = "unknown"
    source_file: str
    node_id: str


class NodeInfo(BaseModel):
    node_id: str
    package: str
    file: str
    class_name: str
    publishers: list[Endpoint] = Field(default_factory=list)
    subscribers: list[Endpoint] = Field(default_factory=list)
    services: list[Endpoint] = Field(default_factory=list)
    clients: list[Endpoint] = Field(default_factory=list)
    parameters: list[ParameterInfo] = Field(default_factory=list)
    timers: int = 0


class InterfaceField(BaseModel):
    name: str
    type_name: str
    section: str = "main"


class InterfaceDefinition(BaseModel):
    kind: str
    package: str
    name: str
    file: str
    fields: list[InterfaceField] = Field(default_factory=list)

    @property
    def fq_name(self) -> str:
        return f"{self.package}/{self.name}"


class DependencyInfo(BaseModel):
    name: str
    source: str


class ProjectIndex(BaseModel):
    repo: RepoMeta
    packages: list[PackageInfo] = Field(default_factory=list)
    launch_nodes: list[LaunchNode] = Field(default_factory=list)
    nodes: list[NodeInfo] = Field(default_factory=list)
    interfaces: list[InterfaceDefinition] = Field(default_factory=list)
    dependencies: list[DependencyInfo] = Field(default_factory=list)

    def known_entities(self) -> set[str]:
        entities: set[str] = {self.repo.repo_name, self.repo.commit}
        for package in self.packages:
            entities.add(package.name)
        for node in self.nodes:
            entities.add(node.node_id)
            entities.add(node.class_name)
            for endpoint in [*node.publishers, *node.subscribers, *node.services, *node.clients]:
                entities.add(endpoint.name)
                entities.add(endpoint.type_name)
            for param in node.parameters:
                entities.add(param.name)
        for interface in self.interfaces:
            entities.add(interface.fq_name)
            entities.add(interface.name)
        return entities

    def to_json_path(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(self.model_dump_json(indent=2), encoding="utf-8")
