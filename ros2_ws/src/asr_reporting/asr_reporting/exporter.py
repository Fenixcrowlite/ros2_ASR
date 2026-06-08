"""Report export helpers for benchmark runs."""

from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any


def export_json(path: str, payload: dict[str, Any]) -> str:
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(payload, ensure_ascii=True, indent=2), encoding="utf-8")
    return str(output)


def export_csv(path: str, rows: list[dict[str, Any]]) -> str:
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        output.write_text("", encoding="utf-8")
        return str(output)
    fieldnames = sorted({key for row in rows for key in row.keys()})
    with output.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)
    return str(output)


def export_markdown(path: str, title: str, bullet_items: list[str]) -> str:
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    lines = [f"# {title}", ""]
    for item in bullet_items:
        lines.append(f"- {item}")
    output.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return str(output)
