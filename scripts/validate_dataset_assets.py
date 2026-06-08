#!/usr/bin/env python3
"""Validate dataset registry portability and manifest audio assets."""

from __future__ import annotations

import argparse
import json
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

REQUIRED_MANIFEST_FIELDS = (
    "sample_id",
    "audio_path",
    "transcript",
    "language",
    "duration_sec",
)


@dataclass(slots=True)
class DatasetValidation:
    dataset_id: str
    manifest_ref: str
    manifest_path: str
    declared_sample_count: int
    actual_sample_count: int = 0
    missing_audio_count: int = 0
    absolute_audio_path_count: int = 0
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    @property
    def passed(self) -> bool:
        return not self.errors

    def as_dict(self) -> dict[str, Any]:
        return {
            "dataset_id": self.dataset_id,
            "manifest_ref": self.manifest_ref,
            "manifest_path": self.manifest_path,
            "declared_sample_count": self.declared_sample_count,
            "actual_sample_count": self.actual_sample_count,
            "missing_audio_count": self.missing_audio_count,
            "absolute_audio_path_count": self.absolute_audio_path_count,
            "passed": self.passed,
            "errors": self.errors,
            "warnings": self.warnings,
        }


def _load_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise SystemExit(f"Invalid JSON in {path}: {exc}") from exc


def _repo_relative(path: Path, root: Path) -> str:
    resolved = path.resolve()
    try:
        return str(resolved.relative_to(root.resolve()))
    except ValueError:
        return str(path)


def _resolve_path(root: Path, raw_path: str) -> Path:
    candidate = Path(raw_path).expanduser()
    if candidate.is_absolute():
        return candidate
    return root / candidate


def _is_home_absolute_path(raw_path: str) -> bool:
    candidate = Path(raw_path).expanduser()
    return candidate.is_absolute() and str(candidate).startswith("/home/")


def _validate_duration(value: Any) -> bool:
    try:
        return float(value) > 0.0
    except (TypeError, ValueError):
        return False


def _validate_manifest_row(
    *,
    row: Any,
    line_no: int,
    manifest_path: Path,
    result: DatasetValidation,
) -> None:
    if not isinstance(row, dict):
        result.errors.append(f"line {line_no}: row must be a JSON object")
        return

    for field_name in REQUIRED_MANIFEST_FIELDS:
        if field_name not in row:
            result.errors.append(f"line {line_no}: missing required field {field_name}")

    sample_id = str(row.get("sample_id", "") or "").strip()
    if not sample_id:
        result.errors.append(f"line {line_no}: sample_id is empty")

    transcript = str(row.get("transcript", "") or "").strip()
    if not transcript:
        result.errors.append(f"line {line_no}: transcript is empty")

    language = str(row.get("language", "") or "").strip()
    if not language:
        result.errors.append(f"line {line_no}: language is empty")

    if "duration_sec" in row and not _validate_duration(row.get("duration_sec")):
        result.errors.append(f"line {line_no}: duration_sec must be > 0")

    raw_audio_path = str(row.get("audio_path", "") or "").strip()
    if not raw_audio_path:
        result.errors.append(f"line {line_no}: audio_path is empty")
        return

    audio_path = Path(raw_audio_path).expanduser()
    if audio_path.is_absolute():
        result.absolute_audio_path_count += 1
        resolved_audio_path = audio_path
        if _is_home_absolute_path(raw_audio_path):
            result.warnings.append(
                f"line {line_no}: audio_path is absolute under /home and is not portable"
            )
    else:
        resolved_audio_path = manifest_path.parent / audio_path

    if not resolved_audio_path.exists():
        result.missing_audio_count += 1
        result.errors.append(f"line {line_no}: audio_path does not exist: {raw_audio_path}")


def _validate_dataset_entry(root: Path, entry: Any) -> DatasetValidation:
    if not isinstance(entry, dict):
        return DatasetValidation(
            dataset_id="",
            manifest_ref="",
            manifest_path="",
            declared_sample_count=0,
            errors=["dataset registry entry must be an object"],
        )

    dataset_id = str(entry.get("dataset_id", "") or "").strip()
    manifest_ref = str(entry.get("manifest_ref", "") or "").strip()
    declared_sample_count = int(entry.get("sample_count", 0) or 0)
    manifest_path = _resolve_path(root, manifest_ref) if manifest_ref else root
    result = DatasetValidation(
        dataset_id=dataset_id,
        manifest_ref=manifest_ref,
        manifest_path=_repo_relative(manifest_path, root),
        declared_sample_count=declared_sample_count,
    )

    if not dataset_id:
        result.errors.append("dataset_id is empty")
    if not manifest_ref:
        result.errors.append("manifest_ref is empty")
        return result
    if Path(manifest_ref).expanduser().is_absolute():
        result.errors.append("manifest_ref must be relative for repository portability")
    if _is_home_absolute_path(manifest_ref):
        result.errors.append("manifest_ref must not contain an absolute /home/... path")
    if not manifest_path.exists():
        result.errors.append(f"manifest file does not exist: {manifest_ref}")
        return result

    seen_sample_ids: set[str] = set()
    with manifest_path.open("r", encoding="utf-8") as handle:
        for line_no, line in enumerate(handle, start=1):
            stripped = line.strip()
            if not stripped:
                continue
            try:
                row = json.loads(stripped)
            except json.JSONDecodeError as exc:
                result.errors.append(f"line {line_no}: invalid JSON: {exc.msg}")
                continue
            result.actual_sample_count += 1
            if isinstance(row, dict):
                sample_id = str(row.get("sample_id", "") or "").strip()
                if sample_id:
                    if sample_id in seen_sample_ids:
                        result.errors.append(f"line {line_no}: duplicate sample_id: {sample_id}")
                    seen_sample_ids.add(sample_id)
            _validate_manifest_row(
                row=row,
                line_no=line_no,
                manifest_path=manifest_path,
                result=result,
            )

    if declared_sample_count != result.actual_sample_count:
        result.errors.append(
            "sample_count mismatch: "
            f"declared={declared_sample_count}, actual={result.actual_sample_count}"
        )
    return result


def _write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=True, indent=2) + "\n", encoding="utf-8")


def _write_markdown(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# Dataset Asset Validation",
        "",
        f"Created: `{payload['created_at']}`",
        f"Registry: `{payload['registry']}`",
        f"Root: `{payload['root']}`",
        f"Status: `{'PASS' if payload['passed'] else 'FAIL'}`",
        "",
        "| Dataset | Declared | Actual | Missing Audio | Absolute Audio Paths | Status |",
        "|---|---:|---:|---:|---:|---|",
    ]
    for item in payload["datasets"]:
        status = "PASS" if item["passed"] else "FAIL"
        lines.append(
            "| "
            + " | ".join(
                [
                    item["dataset_id"] or "(missing)",
                    str(item["declared_sample_count"]),
                    str(item["actual_sample_count"]),
                    str(item["missing_audio_count"]),
                    str(item["absolute_audio_path_count"]),
                    status,
                ]
            )
            + " |"
        )
    lines.append("")
    lines.append("## Findings")
    lines.append("")
    any_findings = False
    for item in payload["datasets"]:
        if item["errors"] or item["warnings"]:
            any_findings = True
            lines.append(f"### {item['dataset_id'] or '(missing dataset_id)'}")
            for error in item["errors"]:
                lines.append(f"- ERROR: {error}")
            for warning in item["warnings"]:
                lines.append(f"- WARNING: {warning}")
            lines.append("")
    if not any_findings:
        lines.append("- No dataset registry or asset issues found.")
    path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Validate dataset registry and JSONL assets")
    parser.add_argument("--registry", default="datasets/registry/datasets.json")
    parser.add_argument("--root", default=".")
    parser.add_argument("--output-md", default="reports/datasets/dataset_asset_validation.md")
    parser.add_argument("--output-json", default="reports/datasets/dataset_asset_validation.json")
    args = parser.parse_args()

    root = Path(args.root).resolve()
    registry_path = _resolve_path(root, args.registry).resolve()
    if not registry_path.exists():
        raise SystemExit(f"Dataset registry not found: {registry_path}")

    registry_payload = _load_json(registry_path)
    if not isinstance(registry_payload, dict):
        raise SystemExit("Dataset registry root must be a JSON object")
    entries = registry_payload.get("datasets", [])
    if not isinstance(entries, list):
        raise SystemExit("Dataset registry key 'datasets' must be a list")

    results = [_validate_dataset_entry(root, entry) for entry in entries]
    report = {
        "created_at": datetime.now(UTC).isoformat(),
        "root": ".",
        "registry": _repo_relative(registry_path, root),
        "passed": all(item.passed for item in results),
        "dataset_count": len(results),
        "valid_dataset_count": sum(1 for item in results if item.passed),
        "datasets": [item.as_dict() for item in results],
    }

    _write_json(Path(args.output_json), report)
    _write_markdown(Path(args.output_md), report)

    print(json.dumps({"passed": report["passed"], "dataset_count": len(results)}, indent=2))
    if not report["passed"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
