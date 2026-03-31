#!/usr/bin/env python3
"""Run direct and API benchmark checks for external subset profiles."""

from __future__ import annotations

import argparse
import json
import sys
import time
from collections import defaultdict
from datetime import UTC, datetime
from pathlib import Path
from statistics import mean
from typing import Any

import requests  # type: ignore[import-untyped]


def _bootstrap_imports() -> tuple[Path, Path]:
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
    return project_root, src_root


PROJECT_ROOT, _SRC_ROOT = _bootstrap_imports()


def _load_project_deps() -> tuple[Any, Any, Any, Any]:
    from asr_benchmark_core import BenchmarkOrchestrator, BenchmarkRunRequest
    from asr_config import resolve_profile
    from asr_datasets import load_manifest

    return BenchmarkOrchestrator, BenchmarkRunRequest, resolve_profile, load_manifest


BenchmarkOrchestrator, BenchmarkRunRequest, resolve_profile, load_manifest = _load_project_deps()


RESULTS_DIR = PROJECT_ROOT / "results"


def _suite_profile_ids() -> list[str]:
    return sorted(
        path.stem for path in (PROJECT_ROOT / "configs" / "benchmark").glob("*_subset_whisper.yaml")
    )


def _dataset_context(benchmark_profile_id: str) -> dict[str, Any]:
    benchmark_cfg = resolve_profile(
        profile_type="benchmark",
        profile_id=benchmark_profile_id,
        configs_root=str(PROJECT_ROOT / "configs"),
    )
    dataset_profile_ref = str(benchmark_cfg.data.get("dataset_profile", "")).strip()
    dataset_profile_id = (
        dataset_profile_ref.split("/", 1)[1]
        if dataset_profile_ref.startswith("datasets/")
        else dataset_profile_ref
    )
    dataset_cfg = resolve_profile(
        profile_type="datasets",
        profile_id=dataset_profile_id,
        configs_root=str(PROJECT_ROOT / "configs"),
    )
    samples = load_manifest(str(dataset_cfg.data.get("manifest_path", "")))
    if not samples:
        raise ValueError(f"Dataset profile `{dataset_profile_id}` resolved to an empty manifest")
    metadata = dict(samples[0].metadata)
    return {
        "benchmark_profile": benchmark_profile_id,
        "dataset_profile": dataset_profile_id,
        "dataset_profile_ref": dataset_profile_ref or f"datasets/{dataset_profile_id}",
        "language": samples[0].language,
        "sample_count": len(samples),
        "source": metadata.get("source", ""),
        "source_ref": metadata.get("source_ref", ""),
        "source_url": metadata.get("source_url", ""),
        "acoustic_profile": metadata.get("acoustic_profile", ""),
        "split": samples[0].split,
        "tags": samples[0].tags,
    }


def _mean_metric(items: list[dict[str, Any]], metric: str) -> float:
    values = [float(item["mean_metrics"].get(metric, 0.0) or 0.0) for item in items]
    return float(mean(values)) if values else 0.0


def _write_outputs(payload: dict[str, Any], suite_id: str) -> None:
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    json_path = RESULTS_DIR / f"{suite_id}.json"
    md_path = RESULTS_DIR / f"{suite_id}.md"
    json_path.write_text(json.dumps(payload, ensure_ascii=True, indent=2) + "\n", encoding="utf-8")

    direct_runs = payload.get("direct_runs", [])
    api_runs = payload.get("api_runs", [])
    direct_completed = [item for item in direct_runs if item.get("status") == "completed"]
    by_acoustic: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for item in direct_completed:
        by_acoustic[str(item.get("acoustic_profile", "") or "unknown")].append(item)

    lines: list[str] = [
        "# External Dataset Benchmark Suite",
        "",
        f"- suite_id: `{suite_id}`",
        f"- generated_at: `{payload.get('generated_at', '')}`",
        f"- benchmark_profiles: `{len(payload.get('profiles', []))}`",
        f"- direct_runs_completed: `{len(direct_completed)}`",
        f"- api_runs_recorded: `{len(api_runs)}`",
        "",
        "## Direct Runs",
        "",
        (
            "| Benchmark | Dataset | Acoustic Profile | Lang | Samples | Success | "
            "WER | CER | Exact Match Rate | Latency ms | RTF |"
        ),
        "|---|---|---|---|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for item in direct_runs:
        mean_metrics = dict(item.get("mean_metrics", {}))
        lines.append(
            "| "
            + " | ".join(
                [
                    str(item.get("benchmark_profile", "")),
                    str(item.get("dataset_profile", "")),
                    str(item.get("acoustic_profile", "")),
                    str(item.get("language", "")),
                    str(item.get("total_samples", 0)),
                    str(item.get("successful_samples", 0)),
                    f"{float(mean_metrics.get('wer', 0.0) or 0.0):.4f}",
                    f"{float(mean_metrics.get('cer', 0.0) or 0.0):.4f}",
                    f"{float(mean_metrics.get('sample_accuracy', 0.0) or 0.0):.4f}",
                    f"{float(mean_metrics.get('total_latency_ms', 0.0) or 0.0):.2f}",
                    f"{float(mean_metrics.get('real_time_factor', 0.0) or 0.0):.4f}",
                ]
            )
            + " |"
        )

    lines.extend(["", "## Acoustic Groups", ""])
    for acoustic_profile, items in sorted(by_acoustic.items()):
        lines.append(
            f"- `{acoustic_profile}`: WER `{_mean_metric(items, 'wer'):.4f}`, "
            f"CER `{_mean_metric(items, 'cer'):.4f}`, "
            f"exact_match_rate `{_mean_metric(items, 'sample_accuracy'):.4f}`, "
            f"latency `{_mean_metric(items, 'total_latency_ms'):.2f}` ms, "
            f"RTF `{_mean_metric(items, 'real_time_factor'):.4f}`"
        )

    if api_runs:
        lines.extend(
            [
                "",
                "## API Runs",
                "",
                (
                    "| Benchmark | State | Success Samples | Failed Samples | "
                    "Mean WER | Mean Latency ms | Message |"
                ),
                "|---|---|---:|---:|---:|---:|---|",
            ]
        )
        for item in api_runs:
            result = dict(item.get("result", {}))
            summary_value = result.get("summary", {})
            summary = dict(summary_value) if isinstance(summary_value, dict) else {}
            lines.append(
                "| "
                + " | ".join(
                    [
                        str(item.get("benchmark_profile", "")),
                        str(item.get("state", "")),
                        str(summary.get("successful_samples", 0)),
                        str(summary.get("failed_samples", 0)),
                        f"{float(summary.get('mean_wer', 0.0) or 0.0):.4f}",
                        f"{float(summary.get('mean_latency_ms', 0.0) or 0.0):.2f}",
                        str(item.get("message", "")).replace("|", "/"),
                    ]
                )
                + " |"
            )

    md_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _run_direct_suite(profiles: list[str], suite_stamp: str) -> list[dict[str, Any]]:
    orchestrator = BenchmarkOrchestrator(
        configs_root=str(PROJECT_ROOT / "configs"),
        artifact_root=str(PROJECT_ROOT / "artifacts"),
        registry_path=str(PROJECT_ROOT / "datasets" / "registry" / "datasets.json"),
    )
    runs: list[dict[str, Any]] = []
    for benchmark_profile_id in profiles:
        context = _dataset_context(benchmark_profile_id)
        run_id = f"extsuite_core_{benchmark_profile_id}_{suite_stamp}"
        summary = orchestrator.run(
            BenchmarkRunRequest(
                benchmark_profile=benchmark_profile_id,
                dataset_profile=context["dataset_profile_ref"],
                providers=["providers/whisper_local"],
                run_id=run_id,
            )
        )
        runs.append(
            {
                **context,
                "status": "completed",
                "run_id": summary.run_id,
                "total_samples": summary.total_samples,
                "successful_samples": summary.successful_samples,
                "failed_samples": summary.failed_samples,
                "mean_metrics": dict(summary.mean_metrics),
            }
        )
        print(
            f"DIRECT {benchmark_profile_id}: "
            f"success={summary.successful_samples}/{summary.total_samples}"
        )
    return runs


def _poll_api_status(
    base_url: str,
    run_id: str,
    *,
    timeout_sec: int,
    poll_sec: float,
) -> dict[str, Any]:
    deadline = time.monotonic() + float(timeout_sec)
    last_payload: dict[str, Any] = {}
    while time.monotonic() < deadline:
        response = requests.get(f"{base_url}/api/benchmark/status/{run_id}", timeout=60)
        response.raise_for_status()
        last_payload = response.json()
        state = str(last_payload.get("state", ""))
        if state in {"completed", "failed"}:
            return last_payload
        time.sleep(poll_sec)
    raise TimeoutError(f"Timed out waiting for API benchmark run `{run_id}`")


def _run_api_suite(
    profiles: list[str],
    suite_stamp: str,
    *,
    base_url: str,
    timeout_sec: int,
    poll_sec: float,
) -> list[dict[str, Any]]:
    health = requests.get(f"{base_url}/api/health", timeout=30)
    health.raise_for_status()
    datasets_response = requests.get(f"{base_url}/api/datasets", timeout=60)
    datasets_response.raise_for_status()
    datasets_payload = datasets_response.json()
    available_ids = {
        str(item.get("dataset_id", "")): bool(item.get("valid", False))
        for item in datasets_payload.get("datasets", [])
    }

    runs: list[dict[str, Any]] = []
    for benchmark_profile_id in profiles:
        context = _dataset_context(benchmark_profile_id)
        if not available_ids.get(context["dataset_profile"], False):
            raise RuntimeError(
                f"Live API does not expose dataset `{context['dataset_profile']}` as valid"
            )
        run_id = f"extsuite_api_{benchmark_profile_id}_{suite_stamp}"
        payload = {
            "benchmark_profile": benchmark_profile_id,
            "dataset_profile": context["dataset_profile_ref"],
            "providers": ["providers/whisper_local"],
            "run_id": run_id,
        }
        response = requests.post(f"{base_url}/api/benchmark/run", json=payload, timeout=60)
        response.raise_for_status()
        status_payload = _poll_api_status(
            base_url,
            run_id,
            timeout_sec=timeout_sec,
            poll_sec=poll_sec,
        )
        runs.append(
            {
                **context,
                "run_id": run_id,
                "accepted": bool(response.json().get("accepted", False)),
                "state": status_payload.get("state", ""),
                "message": status_payload.get("message", ""),
                "result": status_payload.get("result", {}),
            }
        )
        print(f"API {benchmark_profile_id}: state={status_payload.get('state', '')}")
    return runs


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run external subset benchmark suite")
    parser.add_argument("--mode", choices=["core", "api", "both"], default="core")
    parser.add_argument("--api-base-url", default="http://127.0.0.1:8088")
    parser.add_argument("--api-timeout-sec", type=int, default=900)
    parser.add_argument("--api-poll-sec", type=float, default=2.0)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    profiles = _suite_profile_ids()
    suite_stamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    payload: dict[str, Any] = {
        "generated_at": datetime.now(UTC).isoformat(),
        "profiles": profiles,
        "direct_runs": [],
        "api_runs": [],
        "api_base_url": args.api_base_url,
    }
    if args.mode in {"core", "both"}:
        payload["direct_runs"] = _run_direct_suite(profiles, suite_stamp)
    if args.mode in {"api", "both"}:
        payload["api_runs"] = _run_api_suite(
            profiles,
            suite_stamp,
            base_url=args.api_base_url.rstrip("/"),
            timeout_sec=args.api_timeout_sec,
            poll_sec=args.api_poll_sec,
        )

    suite_id = f"external_dataset_suite_{suite_stamp}"
    _write_outputs(payload, suite_id)
    print(f"SUITE {suite_id}")


if __name__ == "__main__":
    main()
