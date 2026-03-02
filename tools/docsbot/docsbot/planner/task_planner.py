from __future__ import annotations

from pathlib import Path

from docsbot.indexer.models import ProjectIndex

from .diff_engine import compute_diff
from .models import Task, TaskPlan
from .slugger import message_filename, parameter_filename, service_filename, topic_filename

ALWAYS_UPDATED = [
    "00_Home.md",
    "01_Project/Overview.md",
    "01_Project/Glossary.md",
    "02_Architecture/Layered Architecture.md",
    "02_Architecture/Dataflow.md",
    "02_Architecture/ROS Graph.md",
    "02_Architecture/Module Map.md",
    "90_Auto/_Index.md",
    "90_Auto/_Generated Graph.md",
    "90_Auto/_Changelog.md",
    "90_Auto/_Errors.md",
]


def _task(action: str, entity_type: str, entity_id: str, target_path: str, reason: str) -> Task:
    return Task(
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
        target_path=target_path,
        reason=reason,
    )


def build_task_plan(
    current: ProjectIndex, previous: ProjectIndex | None, docs_subfolder: str
) -> TaskPlan:
    diff = compute_diff(previous, current)
    plan = TaskPlan()

    for path in ALWAYS_UPDATED:
        plan.tasks.append(
            _task(
                action="update",
                entity_type="page",
                entity_id=path,
                target_path=f"{docs_subfolder}/{path}",
                reason="core wiki structure",
            )
        )

    for interface in current.interfaces:
        if interface.kind == "msg":
            rel = f"03_API/Messages/{message_filename(f'{interface.package}-{interface.name}')}"
            plan.tasks.append(
                _task(
                    "update",
                    "message",
                    interface.fq_name,
                    f"{docs_subfolder}/{rel}",
                    "interface index sync",
                )
            )

    topics = sorted(
        {
            endpoint.name
            for node in current.nodes
            for endpoint in [*node.publishers, *node.subscribers]
        }
    )
    for topic in topics:
        rel = f"03_API/Topics/{topic_filename(topic)}"
        plan.tasks.append(
            _task("update", "topic", topic, f"{docs_subfolder}/{rel}", "topic index sync")
        )

    services = sorted(
        {endpoint.name for node in current.nodes for endpoint in [*node.services, *node.clients]}
    )
    for service in services:
        rel = f"03_API/Services/{service_filename(service)}"
        plan.tasks.append(
            _task("update", "service", service, f"{docs_subfolder}/{rel}", "service index sync")
        )

    parameters = sorted({param.name for node in current.nodes for param in node.parameters})
    for param in parameters:
        rel = f"03_API/Parameters/{parameter_filename(param)}"
        plan.tasks.append(
            _task("update", "parameter", param, f"{docs_subfolder}/{rel}", "parameter index sync")
        )

    for package in current.packages:
        rel = f"04_Modules/{package.name}/{package.name}.md"
        plan.tasks.append(
            _task("update", "module", package.name, f"{docs_subfolder}/{rel}", "module map sync")
        )

    if previous is not None and diff.has_changes():
        for entity, bucket in [
            ("package", diff.packages),
            ("node", diff.nodes),
            ("interface", diff.interfaces),
            ("topic", diff.topics),
            ("service", diff.services),
            ("parameter", diff.parameters),
        ]:
            for removed_id in bucket.removed:
                deletion_path = (
                    f"{docs_subfolder}/90_Auto/deleted_{entity}_{removed_id.replace('/', '_')}.md"
                )
                plan.tasks.append(
                    _task(
                        "delete",
                        entity,
                        removed_id,
                        deletion_path,
                        f"removed from source index ({entity})",
                    )
                )

    # Deduplicate by target path + entity_id.
    unique: dict[tuple[str, str], Task] = {}
    for task in plan.tasks:
        unique[(task.target_path, task.entity_id)] = task
    plan.tasks = list(unique.values())

    # Keep deterministic order.
    plan.tasks.sort(key=lambda item: (item.entity_type, item.target_path, item.entity_id))
    return plan


def tasks_to_json(plan: TaskPlan, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(plan.model_dump_json(indent=2), encoding="utf-8")
