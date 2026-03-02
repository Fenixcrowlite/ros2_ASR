from __future__ import annotations

from abc import ABC, abstractmethod

from docsbot.indexer.models import ProjectIndex
from docsbot.planner.models import Task


class LLMProvider(ABC):
    @abstractmethod
    def name(self) -> str:
        raise NotImplementedError

    @abstractmethod
    def generate_markdown(
        self,
        *,
        task: Task,
        index: ProjectIndex,
        entity_payload: dict,
        existing_content: str | None,
    ) -> str:
        raise NotImplementedError
