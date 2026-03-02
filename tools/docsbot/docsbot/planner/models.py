from __future__ import annotations

from datetime import UTC, datetime

from pydantic import BaseModel, Field


class DiffBucket(BaseModel):
    added: list[str] = Field(default_factory=list)
    removed: list[str] = Field(default_factory=list)
    changed: list[str] = Field(default_factory=list)


class DiffResult(BaseModel):
    packages: DiffBucket = Field(default_factory=DiffBucket)
    nodes: DiffBucket = Field(default_factory=DiffBucket)
    interfaces: DiffBucket = Field(default_factory=DiffBucket)
    topics: DiffBucket = Field(default_factory=DiffBucket)
    services: DiffBucket = Field(default_factory=DiffBucket)
    parameters: DiffBucket = Field(default_factory=DiffBucket)

    def has_changes(self) -> bool:
        for bucket in [
            self.packages,
            self.nodes,
            self.interfaces,
            self.topics,
            self.services,
            self.parameters,
        ]:
            if bucket.added or bucket.removed or bucket.changed:
                return True
        return False


class Task(BaseModel):
    action: str
    entity_type: str
    entity_id: str
    target_path: str
    reason: str


class TaskPlan(BaseModel):
    created_at: str = Field(default_factory=lambda: datetime.now(UTC).isoformat())
    tasks: list[Task] = Field(default_factory=list)

    def summary(self) -> dict[str, int]:
        counts = {"create": 0, "update": 0, "delete": 0, "skip": 0}
        for task in self.tasks:
            counts[task.action] = counts.get(task.action, 0) + 1
        return counts
