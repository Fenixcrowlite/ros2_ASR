from __future__ import annotations

import json

from docsbot.indexer.models import ProjectIndex
from docsbot.planner.models import Task

SYSTEM_PROMPT = (
    "You are a ROS2 documentation assistant.\n"
    "Only describe entities that exist in provided project index payload.\n"
    "If information is missing, state that it is unavailable instead of inventing facts.\n"
    "Return markdown only, no code fences around whole output."
)


def build_prompt(
    task: Task, index: ProjectIndex, entity_payload: dict, existing_content: str | None
) -> str:
    context = {
        "task": task.model_dump(),
        "entity": entity_payload,
        "repo": index.repo.model_dump(),
    }
    parts = [
        "Generate or update one markdown page.",
        "Use this context JSON:",
        json.dumps(context, ensure_ascii=False, indent=2),
    ]
    if existing_content:
        parts.append("Existing content:")
        parts.append(existing_content[:12000])
    return "\n\n".join(parts)
