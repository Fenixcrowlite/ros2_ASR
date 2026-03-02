from __future__ import annotations

import hashlib
import json
from collections.abc import Callable

from docsbot.indexer.models import NodeInfo, ProjectIndex

from .models import DiffBucket, DiffResult


def _hash_obj(data: dict) -> str:
    payload = json.dumps(data, sort_keys=True, ensure_ascii=False)
    return hashlib.sha1(payload.encode("utf-8")).hexdigest()


def _map_entities(items: list, key_fn: Callable, dump_fn: Callable) -> dict[str, str]:
    result: dict[str, str] = {}
    for item in items:
        key = key_fn(item)
        result[key] = _hash_obj(dump_fn(item))
    return result


def _bucket(old_map: dict[str, str], new_map: dict[str, str]) -> DiffBucket:
    old_keys = set(old_map)
    new_keys = set(new_map)

    added = sorted(new_keys - old_keys)
    removed = sorted(old_keys - new_keys)
    changed = sorted(key for key in (new_keys & old_keys) if old_map[key] != new_map[key])
    return DiffBucket(added=added, removed=removed, changed=changed)


def _node_topics(nodes: list[NodeInfo]) -> dict[str, dict]:
    topics: dict[str, dict] = {}
    for node in nodes:
        for endpoint in [*node.publishers, *node.subscribers]:
            topics.setdefault(endpoint.name, {"type_name": endpoint.type_name, "directions": set()})
            topics[endpoint.name]["directions"].add(endpoint.direction)
    normalized = {}
    for key, value in topics.items():
        normalized[key] = {
            "type_name": value["type_name"],
            "directions": sorted(value["directions"]),
        }
    return normalized


def _node_services(nodes: list[NodeInfo]) -> dict[str, dict]:
    services: dict[str, dict] = {}
    for node in nodes:
        for endpoint in [*node.services, *node.clients]:
            services.setdefault(
                endpoint.name, {"type_name": endpoint.type_name, "directions": set()}
            )
            services[endpoint.name]["directions"].add(endpoint.direction)
    normalized = {}
    for key, value in services.items():
        normalized[key] = {
            "type_name": value["type_name"],
            "directions": sorted(value["directions"]),
        }
    return normalized


def _node_parameters(nodes: list[NodeInfo]) -> dict[str, dict]:
    params: dict[str, dict] = {}
    for node in nodes:
        for parameter in node.parameters:
            params.setdefault(parameter.name, {"default": parameter.default, "nodes": set()})
            params[parameter.name]["nodes"].add(node.node_id)
    normalized = {}
    for key, value in params.items():
        normalized[key] = {
            "default": value["default"],
            "nodes": sorted(value["nodes"]),
        }
    return normalized


def compute_diff(old_index: ProjectIndex | None, new_index: ProjectIndex) -> DiffResult:
    if old_index is None:
        return DiffResult(
            packages=DiffBucket(added=sorted(package.name for package in new_index.packages)),
            nodes=DiffBucket(added=sorted(node.node_id for node in new_index.nodes)),
            interfaces=DiffBucket(
                added=sorted(
                    f"{interface.kind}:{interface.package}/{interface.name}"
                    for interface in new_index.interfaces
                )
            ),
            topics=DiffBucket(added=sorted(_node_topics(new_index.nodes).keys())),
            services=DiffBucket(added=sorted(_node_services(new_index.nodes).keys())),
            parameters=DiffBucket(added=sorted(_node_parameters(new_index.nodes).keys())),
        )

    old_packages = _map_entities(
        old_index.packages,
        key_fn=lambda item: item.name,
        dump_fn=lambda item: item.model_dump(),
    )
    new_packages = _map_entities(
        new_index.packages,
        key_fn=lambda item: item.name,
        dump_fn=lambda item: item.model_dump(),
    )

    old_nodes = _map_entities(
        old_index.nodes,
        key_fn=lambda item: item.node_id,
        dump_fn=lambda item: item.model_dump(),
    )
    new_nodes = _map_entities(
        new_index.nodes,
        key_fn=lambda item: item.node_id,
        dump_fn=lambda item: item.model_dump(),
    )

    old_interfaces = _map_entities(
        old_index.interfaces,
        key_fn=lambda item: f"{item.kind}:{item.package}/{item.name}",
        dump_fn=lambda item: item.model_dump(),
    )
    new_interfaces = _map_entities(
        new_index.interfaces,
        key_fn=lambda item: f"{item.kind}:{item.package}/{item.name}",
        dump_fn=lambda item: item.model_dump(),
    )

    old_topics = _map_entities(
        [{"name": key, **value} for key, value in _node_topics(old_index.nodes).items()],
        key_fn=lambda item: item["name"],
        dump_fn=lambda item: item,
    )
    new_topics = _map_entities(
        [{"name": key, **value} for key, value in _node_topics(new_index.nodes).items()],
        key_fn=lambda item: item["name"],
        dump_fn=lambda item: item,
    )

    old_services = _map_entities(
        [{"name": key, **value} for key, value in _node_services(old_index.nodes).items()],
        key_fn=lambda item: item["name"],
        dump_fn=lambda item: item,
    )
    new_services = _map_entities(
        [{"name": key, **value} for key, value in _node_services(new_index.nodes).items()],
        key_fn=lambda item: item["name"],
        dump_fn=lambda item: item,
    )

    old_params = _map_entities(
        [{"name": key, **value} for key, value in _node_parameters(old_index.nodes).items()],
        key_fn=lambda item: item["name"],
        dump_fn=lambda item: item,
    )
    new_params = _map_entities(
        [{"name": key, **value} for key, value in _node_parameters(new_index.nodes).items()],
        key_fn=lambda item: item["name"],
        dump_fn=lambda item: item,
    )

    return DiffResult(
        packages=_bucket(old_packages, new_packages),
        nodes=_bucket(old_nodes, new_nodes),
        interfaces=_bucket(old_interfaces, new_interfaces),
        topics=_bucket(old_topics, new_topics),
        services=_bucket(old_services, new_services),
        parameters=_bucket(old_params, new_params),
    )
