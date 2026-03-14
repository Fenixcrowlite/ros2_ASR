"""Benchmark orchestrator with reproducible run artifacts."""

from __future__ import annotations

import csv
import json
import platform
from datetime import datetime, timezone
from pathlib import Path
from statistics import mean
from typing import Any

from asr_config import resolve_profile, validate_benchmark_payload
from asr_core import make_run_id
from asr_datasets import DatasetRegistry, load_manifest
from asr_metrics.engine import MetricEngine
from asr_provider_base import ProviderManager
from asr_storage import ArtifactStore

from asr_benchmark_core.executor import BatchExecutor
from asr_benchmark_core.models import BenchmarkRunRequest, BenchmarkRunSummary


class BenchmarkOrchestrator:
    def __init__(
        self,
        *,
        configs_root: str = "configs",
        artifact_root: str = "artifacts",
        registry_path: str = "datasets/registry/datasets.json",
    ) -> None:
        self.configs_root = configs_root
        self.artifact_store = ArtifactStore(root=artifact_root)
        self.provider_manager = ProviderManager(configs_root=configs_root)
        self.dataset_registry = DatasetRegistry(registry_path=registry_path)

    def run(self, request: BenchmarkRunRequest) -> BenchmarkRunSummary:
        benchmark_profile_id = request.benchmark_profile
        if benchmark_profile_id.startswith("benchmark/"):
            benchmark_profile_id = benchmark_profile_id.split("/", 1)[1]

        benchmark_cfg = resolve_profile(
            profile_type="benchmark",
            profile_id=benchmark_profile_id,
            configs_root=self.configs_root,
        )
        errors = validate_benchmark_payload(benchmark_cfg.data)
        if errors:
            joined = "; ".join(errors)
            raise ValueError(f"Benchmark profile validation failed: {joined}")

        dataset_profile = request.dataset_profile or str(benchmark_cfg.data.get("dataset_profile", ""))
        if dataset_profile.startswith("datasets/"):
            dataset_profile = dataset_profile.split("/", 1)[1]
        if not dataset_profile:
            raise ValueError("dataset_profile is required")

        dataset_cfg = resolve_profile(
            profile_type="datasets",
            profile_id=dataset_profile,
            configs_root=self.configs_root,
        )
        dataset_id = str(dataset_cfg.data.get("dataset_id", dataset_profile))
        manifest_path = str(dataset_cfg.data.get("manifest_path", "")).strip()
        if not manifest_path:
            raise ValueError("Dataset profile is missing manifest_path")

        samples = load_manifest(manifest_path)
        if not samples:
            raise ValueError(f"Dataset manifest has no samples: {manifest_path}")

        provider_profiles = request.providers or [
            str(item) for item in benchmark_cfg.data.get("providers", []) if str(item).strip()
        ]
        if not provider_profiles:
            raise ValueError("No providers selected for benchmark run")

        enabled_metrics: list[str] = []
        metric_profiles = [str(item) for item in benchmark_cfg.data.get("metric_profiles", [])]
        metric_snapshots: dict[str, str] = {}
        for metric_profile in metric_profiles:
            metric_id = metric_profile.split("/", 1)[1] if metric_profile.startswith("metrics/") else metric_profile
            metric_cfg = resolve_profile(
                profile_type="metrics",
                profile_id=metric_id,
                configs_root=self.configs_root,
            )
            enabled_metrics.extend([str(item) for item in metric_cfg.data.get("metrics", [])])
            metric_snapshots[metric_profile] = metric_cfg.snapshot_path
        enabled_metrics = sorted(set(enabled_metrics)) or ["wer", "cer", "total_latency_ms", "success_rate"]

        provider_snapshots: dict[str, str] = {}
        for provider_profile in provider_profiles:
            provider_id = (
                provider_profile.split("/", 1)[1]
                if provider_profile.startswith("providers/")
                else provider_profile
            )
            provider_cfg = resolve_profile(
                profile_type="providers",
                profile_id=provider_id,
                configs_root=self.configs_root,
            )
            provider_snapshots[provider_profile] = provider_cfg.snapshot_path

        run_id = request.run_id or make_run_id("bench")
        run_dir = self.artifact_store.make_benchmark_run(run_id)

        run_manifest = {
            "run_id": run_id,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "benchmark_profile": request.benchmark_profile,
            "dataset_profile": request.dataset_profile or str(benchmark_cfg.data.get("dataset_profile", "")),
            "providers": provider_profiles,
            "metric_profiles": metric_profiles,
            "enabled_metrics": enabled_metrics,
            "config_snapshots": {
                "benchmark": benchmark_cfg.snapshot_path,
                "dataset": dataset_cfg.snapshot_path,
                "providers": provider_snapshots,
                "metrics": metric_snapshots,
            },
            "environment": {
                "python": platform.python_version(),
                "platform": platform.platform(),
            },
            "dataset_manifest": manifest_path,
            "sample_count": len(samples),
        }
        manifest_ref = self.artifact_store.save_manifest(run_dir, run_manifest)

        metric_engine = MetricEngine(enabled_metrics=enabled_metrics)
        executor = BatchExecutor(metric_engine=metric_engine)

        results: list[dict[str, Any]] = []
        session_id = f"benchmark_{run_id}"

        for provider_profile in provider_profiles:
            provider = self.provider_manager.create_from_profile(provider_profile)
            for sample in samples:
                record = executor.run_sample(
                    run_id=run_id,
                    provider=provider,
                    provider_profile=provider_profile,
                    sample=sample,
                    session_id=session_id,
                )
                results.append(record)
                sample_key = f"{provider_profile.replace('/', '_')}__{sample.sample_id}"
                self.artifact_store.save_raw_output(run_dir, sample_key, record)
                self.artifact_store.save_normalized_output(
                    run_dir,
                    sample_key,
                    record.get("normalized_result", {}),
                )
            provider.teardown()

        self.artifact_store.save_json(run_dir / "metrics" / "results.json", results)
        self._save_csv(run_dir / "metrics" / "results.csv", results)

        summary = self._build_summary(
            run_id=run_id,
            benchmark_profile=request.benchmark_profile,
            dataset_id=dataset_id,
            providers=provider_profiles,
            results=results,
        )

        summary_ref = self.artifact_store.save_json(run_dir / "reports" / "summary.json", summary)
        md_ref = self.artifact_store.save_report(
            run_dir,
            "summary.md",
            self._to_markdown(summary),
        )

        return BenchmarkRunSummary(
            run_id=run_id,
            benchmark_profile=request.benchmark_profile,
            dataset_id=dataset_id,
            providers=provider_profiles,
            total_samples=summary["total_samples"],
            successful_samples=summary["successful_samples"],
            failed_samples=summary["failed_samples"],
            mean_metrics=summary["mean_metrics"],
            artifacts={
                "run_manifest": manifest_ref.path,
                "summary_json": summary_ref.path,
                "summary_md": md_ref.path,
            },
            metadata={
                "run_dir": str(run_dir),
                "enabled_metrics": enabled_metrics,
            },
        )

    @staticmethod
    def _save_csv(path: Path, rows: list[dict[str, Any]]) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        fieldnames = [
            "run_id",
            "provider_profile",
            "provider_id",
            "sample_id",
            "success",
            "text",
            "error_code",
            "error_message",
            "metrics",
        ]
        with path.open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=fieldnames)
            writer.writeheader()
            for row in rows:
                out = dict(row)
                out["metrics"] = json.dumps(out.get("metrics", {}), ensure_ascii=True)
                writer.writerow({k: out.get(k, "") for k in fieldnames})

    @staticmethod
    def _build_summary(
        *,
        run_id: str,
        benchmark_profile: str,
        dataset_id: str,
        providers: list[str],
        results: list[dict[str, Any]],
    ) -> dict[str, Any]:
        total = len(results)
        success = sum(1 for item in results if item.get("success"))
        failed = total - success

        metric_values: dict[str, list[float]] = {}
        for item in results:
            for key, value in item.get("metrics", {}).items():
                metric_values.setdefault(key, []).append(float(value))

        mean_metrics = {
            key: (mean(values) if values else 0.0)
            for key, values in sorted(metric_values.items())
        }

        return {
            "run_id": run_id,
            "benchmark_profile": benchmark_profile,
            "dataset_id": dataset_id,
            "providers": providers,
            "total_samples": total,
            "successful_samples": success,
            "failed_samples": failed,
            "mean_metrics": mean_metrics,
        }

    @staticmethod
    def _to_markdown(summary: dict[str, Any]) -> str:
        lines = [
            f"# Benchmark Summary: {summary['run_id']}",
            "",
            f"- benchmark_profile: `{summary['benchmark_profile']}`",
            f"- dataset_id: `{summary['dataset_id']}`",
            f"- providers: `{', '.join(summary['providers'])}`",
            f"- total_samples: `{summary['total_samples']}`",
            f"- successful_samples: `{summary['successful_samples']}`",
            f"- failed_samples: `{summary['failed_samples']}`",
            "",
            "## Mean Metrics",
            "",
        ]
        for key, value in sorted(summary.get("mean_metrics", {}).items()):
            lines.append(f"- {key}: `{value:.6f}`")
        return "\n".join(lines) + "\n"
