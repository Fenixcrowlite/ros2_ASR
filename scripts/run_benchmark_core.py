#!/usr/bin/env python3
"""Run canonical benchmark core and print schema v2 artifact references."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


def _bootstrap_imports() -> Path:
    current = Path(__file__).resolve()
    project_root = current.parent.parent
    src_root = project_root / "ros2_ws" / "src"

    paths = [project_root]
    if src_root.is_dir():
        paths.extend(path for path in src_root.iterdir() if path.is_dir())

    for candidate in reversed(paths):
        text = str(candidate)
        if text not in sys.path:
            sys.path.insert(0, text)
    return project_root


PROJECT_ROOT = _bootstrap_imports()

from asr_benchmark_core import BenchmarkOrchestrator, BenchmarkRunRequest  # noqa: E402


def _normalize_profile_ref(value: str, *, prefix: str) -> str:
    normalized = str(value or "").strip()
    if not normalized:
        return ""
    if normalized.startswith(f"{prefix}/"):
        return normalized
    return f"{prefix}/{normalized}"


def _parse_provider_refs(raw: str) -> list[str]:
    provider_refs: list[str] = []
    for chunk in str(raw or "").split(","):
        normalized = _normalize_profile_ref(chunk, prefix="providers")
        if normalized:
            provider_refs.append(normalized)
    return provider_refs


def _load_json(path: Path) -> object:
    return json.loads(path.read_text(encoding="utf-8"))


def _load_provider_overrides(raw: str) -> dict[str, dict[str, object]]:
    text = str(raw or "").strip()
    if not text:
        return {}
    candidate = Path(text)
    if candidate.exists():
        payload = _load_json(candidate)
    else:
        payload = json.loads(text)
    if not isinstance(payload, dict):
        raise SystemExit("Provider overrides must be a JSON object")
    normalized: dict[str, dict[str, object]] = {}
    for provider, value in payload.items():
        if not isinstance(value, dict):
            raise SystemExit(f"Provider override for {provider!r} must be an object")
        normalized[_normalize_profile_ref(str(provider), prefix="providers")] = dict(value)
    return normalized


def _load_run_payloads(run_dir: Path) -> tuple[dict[str, object], list[dict[str, object]]]:
    summary_path = run_dir / "reports" / "summary.json"
    results_path = run_dir / "metrics" / "results.json"
    summary_payload = _load_json(summary_path)
    results_payload = _load_json(results_path)
    if not isinstance(summary_payload, dict):
        raise SystemExit(f"Canonical summary JSON root must be an object: {summary_path}")
    if not isinstance(results_payload, list):
        raise SystemExit(f"Canonical results JSON root must be a list: {results_path}")
    normalized_results: list[dict[str, object]] = []
    for row in results_payload:
        if not isinstance(row, dict):
            raise SystemExit(f"Canonical benchmark result row must be an object: {results_path}")
        normalized_results.append(row)
    return summary_payload, normalized_results


def main() -> None:
    parser = argparse.ArgumentParser(description="Run canonical ASR benchmark orchestrator")
    parser.add_argument("--benchmark-profile", default="default_benchmark")
    parser.add_argument("--dataset-profile", default="")
    parser.add_argument("--providers", default="")
    parser.add_argument("--run-id", default="")
    parser.add_argument("--configs-root", default=str(PROJECT_ROOT / "configs"))
    parser.add_argument(
        "--artifact-root",
        default=str(PROJECT_ROOT / "artifacts"),
    )
    parser.add_argument(
        "--registry-path",
        default=str(PROJECT_ROOT / "datasets" / "registry" / "datasets.json"),
    )
    parser.add_argument(
        "--provider-overrides-json",
        default="",
        help="JSON object or path with provider-specific preset/settings overrides",
    )
    args = parser.parse_args()

    orchestrator = BenchmarkOrchestrator(
        configs_root=str(Path(args.configs_root)),
        artifact_root=str(Path(args.artifact_root)),
        registry_path=str(Path(args.registry_path)),
    )
    request = BenchmarkRunRequest(
        benchmark_profile=_normalize_profile_ref(args.benchmark_profile, prefix="benchmark"),
        dataset_profile=_normalize_profile_ref(args.dataset_profile, prefix="datasets"),
        providers=_parse_provider_refs(args.providers),
        provider_overrides=_load_provider_overrides(args.provider_overrides_json),
        run_id=str(args.run_id or "").strip(),
    )
    summary = orchestrator.run(request)
    run_dir = Path(str(summary.metadata.get("run_dir", "") or "")).resolve()
    if not run_dir.exists():
        raise SystemExit(f"Benchmark run directory not found: {run_dir}")

    summary_payload, results_payload = _load_run_payloads(run_dir)

    result = {
        "run_id": summary.run_id,
        "total_samples": summary.total_samples,
        "successful_samples": summary.successful_samples,
        "failed_samples": summary.failed_samples,
        "result_rows": len(results_payload),
        "metrics_semantics_version": summary_payload.get("metrics_semantics_version", 2),
        "run_dir": str(run_dir),
        "canonical_summary_json": str(run_dir / "reports" / "summary.json"),
        "canonical_results_json": str(run_dir / "metrics" / "results.json"),
    }
    print(json.dumps(result, ensure_ascii=True, indent=2))


if __name__ == "__main__":
    main()
