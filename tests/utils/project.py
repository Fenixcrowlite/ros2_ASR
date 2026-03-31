from __future__ import annotations

import json
import shutil
from pathlib import Path


def clone_project_layout(repo_root: Path, target_root: Path) -> Path:
    for rel in ("configs", "datasets", "secrets", "web_ui/frontend", "data/sample"):
        src = repo_root / rel
        dst = target_root / rel
        if src.is_dir():
            shutil.copytree(src, dst, dirs_exist_ok=True)
    for rel in (
        "artifacts/runtime_sessions",
        "artifacts/benchmark_runs",
        "artifacts/comparisons",
        "artifacts/exports",
        "artifacts/temp",
        "logs/runtime",
        "logs/benchmark",
        "logs/gateway",
        "logs/gui",
    ):
        (target_root / rel).mkdir(parents=True, exist_ok=True)

    registry_path = target_root / "datasets" / "registry" / "datasets.json"
    manifest_path = target_root / "datasets" / "manifests" / "sample_dataset.jsonl"
    if registry_path.exists():
        try:
            payload = json.loads(registry_path.read_text(encoding="utf-8"))
        except Exception:
            payload = {"datasets": []}
    else:
        payload = {"datasets": []}
    payload.setdefault("datasets", [])
    if manifest_path.exists() and not any(
        row.get("dataset_id") == "sample_dataset" for row in payload["datasets"]
    ):
        payload["datasets"].append(
            {
                "dataset_id": "sample_dataset",
                "manifest_ref": str(manifest_path),
                "sample_count": 1,
                "metadata": {"seeded_by": "tests.utils.project"},
            }
        )
    registry_path.parent.mkdir(parents=True, exist_ok=True)
    registry_path.write_text(json.dumps(payload, ensure_ascii=True, indent=2), encoding="utf-8")
    return target_root


def seed_logs(project_root: Path) -> None:
    (project_root / "logs" / "runtime" / "runtime.log").write_text(
        "INFO runtime started\nWARNING sample warning\nERROR sample error\n",
        encoding="utf-8",
    )
    (project_root / "logs" / "gateway" / "gateway.log").write_text(
        "INFO gateway ready\n",
        encoding="utf-8",
    )


def seed_benchmark_run(
    project_root: Path,
    run_id: str,
    *,
    wer: float,
    cer: float,
    sample_accuracy: float | None = None,
) -> Path:
    run_dir = project_root / "artifacts" / "benchmark_runs" / run_id
    for rel in (
        "manifest",
        "resolved_configs",
        "raw_outputs",
        "normalized_outputs",
        "metrics",
        "reports",
        "logs",
    ):
        (run_dir / rel).mkdir(parents=True, exist_ok=True)

    run_manifest = {
        "run_id": run_id,
        "benchmark_profile": "default_benchmark",
        "dataset_profile": "datasets/sample_dataset",
        "providers": ["providers/whisper_local"],
        "execution_mode": "batch",
        "sample_count": 1,
        "created_at": "2026-03-12T00:00:00+00:00",
    }
    resolved_sample_accuracy = (
        float(sample_accuracy)
        if sample_accuracy is not None
        else (1.0 if wer == 0.0 and cer == 0.0 else 0.0)
    )
    mean_metrics = {
        "wer": wer,
        "cer": cer,
        "sample_accuracy": resolved_sample_accuracy,
        "total_latency_ms": 15.0,
        "per_utterance_latency_ms": 15.0,
        "real_time_factor": 0.25,
        "estimated_cost_usd": 0.0,
        "success_rate": 1.0,
        "failure_rate": 0.0,
    }
    provider_summaries = [
        {
            "provider_key": "providers/whisper_local",
            "provider_profile": "providers/whisper_local",
            "provider_id": "whisper",
            "provider_preset": "",
            "provider_label": "",
            "total_samples": 1,
            "successful_samples": 1,
            "failed_samples": 0,
            "mean_metrics": mean_metrics,
            "metric_statistics": {
                "estimated_cost_usd": {
                    "aggregator": "mean",
                    "count": 1,
                    "sum": 0.0,
                    "mean": 0.0,
                    "min": 0.0,
                    "max": 0.0,
                    "p50": 0.0,
                    "p95": 0.0,
                }
            },
            "quality_metrics": {
                "wer": wer,
                "cer": cer,
                "sample_accuracy": resolved_sample_accuracy,
            },
            "latency_metrics": {
                "total_latency_ms": 15.0,
                "per_utterance_latency_ms": 15.0,
                "real_time_factor": 0.25,
            },
            "reliability_metrics": {
                "success_rate": 1.0,
                "failure_rate": 0.0,
            },
            "cost_metrics": {
                "estimated_cost_usd": 0.0,
            },
            "cost_totals": {
                "estimated_cost_usd": 0.0,
            },
            "streaming_metrics": {},
            "resource_metrics": {},
        }
    ]
    summary = {
        "run_id": run_id,
        "benchmark_profile": "default_benchmark",
        "dataset_id": "sample_dataset",
        "providers": ["providers/whisper_local"],
        "scenario": "clean_baseline",
        "execution_mode": "batch",
        "total_samples": 1,
        "successful_samples": 1,
        "failed_samples": 0,
        "mean_metrics": mean_metrics,
        "metric_statistics": {
            "wer": {
                "aggregator": "corpus_rate",
                "count": 1,
                "numerator": wer,
                "denominator": 1,
                "value": wer,
            },
            "cer": {
                "aggregator": "corpus_rate",
                "count": 1,
                "numerator": cer,
                "denominator": 1,
                "value": cer,
            },
            "sample_accuracy": {
                "aggregator": "rate",
                "count": 1,
                "numerator": 1 if resolved_sample_accuracy >= 1.0 else 0,
                "denominator": 1,
                "value": resolved_sample_accuracy,
            },
            "total_latency_ms": {
                "aggregator": "mean",
                "count": 1,
                "sum": 15.0,
                "mean": 15.0,
                "min": 15.0,
                "max": 15.0,
                "p50": 15.0,
                "p95": 15.0,
            },
            "per_utterance_latency_ms": {
                "aggregator": "mean",
                "count": 1,
                "sum": 15.0,
                "mean": 15.0,
                "min": 15.0,
                "max": 15.0,
                "p50": 15.0,
                "p95": 15.0,
            },
            "real_time_factor": {
                "aggregator": "mean",
                "count": 1,
                "sum": 0.25,
                "mean": 0.25,
                "min": 0.25,
                "max": 0.25,
                "p50": 0.25,
                "p95": 0.25,
            },
            "estimated_cost_usd": {
                "aggregator": "mean",
                "count": 1,
                "sum": 0.0,
                "mean": 0.0,
                "min": 0.0,
                "max": 0.0,
                "p50": 0.0,
                "p95": 0.0,
            },
            "success_rate": {
                "aggregator": "rate",
                "count": 1,
                "numerator": 1,
                "denominator": 1,
                "value": 1.0,
            },
            "failure_rate": {
                "aggregator": "rate",
                "count": 1,
                "numerator": 0,
                "denominator": 1,
                "value": 0.0,
            },
        },
        "quality_metrics": {
            "wer": wer,
            "cer": cer,
            "sample_accuracy": resolved_sample_accuracy,
        },
        "latency_metrics": {
            "total_latency_ms": 15.0,
            "per_utterance_latency_ms": 15.0,
            "real_time_factor": 0.25,
        },
        "reliability_metrics": {
            "success_rate": 1.0,
            "failure_rate": 0.0,
        },
        "cost_metrics": {
            "estimated_cost_usd": 0.0,
        },
        "cost_totals": {
            "estimated_cost_usd": 0.0,
        },
        "streaming_metrics": {},
        "resource_metrics": {},
        "provider_summaries": provider_summaries,
        "providers_summary": {},
        "noise_summary": {
            "clean": {
                "samples": 1,
                "mean_metrics": {
                    "wer": wer,
                    "cer": cer,
                    "total_latency_ms": 15.0,
                },
            }
        },
    }
    summary["providers_summary"] = {
        str(provider_summary["provider_key"]): provider_summary
        for provider_summary in provider_summaries
    }
    rows = [
        {
            "run_id": run_id,
            "provider_profile": "providers/whisper_local",
            "provider_id": "whisper",
            "execution_mode": "batch",
            "streaming_mode": "none",
            "sample_id": "sample_000",
            "success": True,
            "text": "hello world",
            "error_code": "",
            "error_message": "",
            "metrics": summary["mean_metrics"],
        }
    ]
    (run_dir / "manifest" / "run_manifest.json").write_text(
        json.dumps(run_manifest, ensure_ascii=True, indent=2),
        encoding="utf-8",
    )
    (run_dir / "reports" / "summary.json").write_text(
        json.dumps(summary, ensure_ascii=True, indent=2),
        encoding="utf-8",
    )
    (run_dir / "reports" / "summary.md").write_text("# Summary\n", encoding="utf-8")
    (run_dir / "metrics" / "results.json").write_text(
        json.dumps(rows, ensure_ascii=True, indent=2),
        encoding="utf-8",
    )
    (run_dir / "metrics" / "results.csv").write_text("run_id,provider_id\n", encoding="utf-8")
    return run_dir
