from __future__ import annotations

import json

from docsbot.indexer.models import ProjectIndex
from docsbot.planner.models import Task

from .provider import LLMProvider


class MockProvider(LLMProvider):
    """Deterministic provider used when OPENAI_API_KEY is missing."""

    def name(self) -> str:
        return "mock"

    def generate_markdown(
        self,
        *,
        task: Task,
        index: ProjectIndex,
        entity_payload: dict,
        existing_content: str | None,
    ) -> str:
        lines = [
            f"# {task.entity_type.title()}: {task.entity_id}",
            "",
            "This page is generated in deterministic MockProvider mode.",
            "",
            "## Scope",
            f"- Action: `{task.action}`",
            f"- Reason: {task.reason}",
            f"- Source commit: `{index.repo.commit}`",
            "",
            "## Entity Payload",
            "```json",
            json.dumps(entity_payload, ensure_ascii=False, indent=2),
            "```",
            "",
            "## Notes",
            "- TODO: Extend details when OpenAI provider is enabled.",
        ]
        if existing_content:
            lines.extend(["", "## Previous Snapshot", existing_content[:800]])
        return "\n".join(lines).strip() + "\n"
