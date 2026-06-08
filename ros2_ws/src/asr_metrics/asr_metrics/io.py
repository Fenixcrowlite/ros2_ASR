"""Persistence helpers for benchmark artifacts (CSV/JSON)."""

from __future__ import annotations

import csv
import json
from pathlib import Path

from asr_metrics.models import BenchmarkRecord

_FIELDS = list(BenchmarkRecord.__dataclass_fields__.keys())


def save_benchmark_csv(records: list[BenchmarkRecord], output_path: str) -> None:
    """Save benchmark records into tabular CSV format."""
    out = Path(output_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=_FIELDS)
        writer.writeheader()
        for rec in records:
            writer.writerow(rec.to_dict())


def save_benchmark_json(records: list[BenchmarkRecord], output_path: str) -> None:
    """Save benchmark records into pretty JSON."""
    out = Path(output_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    payload = [r.to_dict() for r in records]
    with out.open("w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, ensure_ascii=False)


def load_benchmark_json(input_path: str) -> list[BenchmarkRecord]:
    """Load JSON report back into strongly-typed benchmark records."""
    path = Path(input_path)
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8") as f:
        payload = json.load(f)
    records: list[BenchmarkRecord] = []
    for row in payload:
        row.setdefault("audio_id", Path(str(row.get("wav_path", ""))).stem)
        row.setdefault("snr_db", None)
        row.setdefault("duration_sec", float(row.get("audio_duration_sec", 0.0)))
        row.setdefault("text", str(row.get("transcript_hyp", "")))
        records.append(BenchmarkRecord(**row))
    return records
