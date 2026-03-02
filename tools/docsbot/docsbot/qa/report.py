from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

from pydantic import BaseModel, Field


class QAReport(BaseModel):
    timestamp: str = Field(default_factory=lambda: datetime.now(UTC).isoformat())
    passed: bool = True
    errors: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)


def write_errors_page(path: Path, errors: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    header = [
        "---",
        "id: auto-errors",
        "title: Auto Errors",
        "generated: true",
        "source_repo: docsbot",
        "source_commit: no-git",
        f"updated_at: {datetime.now(UTC).isoformat()}",
        "tags: [asr, ros2, docsbot]",
        "---",
        "",
    ]
    if errors:
        body = "\n".join(
            [*header, "# Auto Errors", "", "## Errors", *[f"- {item}" for item in errors], ""]
        )
    else:
        body = "\n".join([*header, "# Auto Errors", "", "No errors detected.", ""])
    path.write_text(body, encoding="utf-8")
