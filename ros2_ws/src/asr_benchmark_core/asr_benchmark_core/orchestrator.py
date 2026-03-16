"""Benchmark orchestrator with reproducible run artifacts."""

from __future__ import annotations

import csv
import json
import platform
from datetime import datetime, timezone
from pathlib import Path
from statistics import mean
from typing import Any

from asr_benchmark_core.executor import BatchExecutor
from asr_benchmark_core.models import BenchmarkRunRequest, BenchmarkRunSummary
from asr_benchmark_core.noise import apply_noise_to_wav, resolve_noise_plan
from asr_config import resolve_profile, validate_benchmark_payload
from asr_core import make_run_id
from asr_datasets import DatasetRegistry, load_manifest
from asr_metrics.engine import MetricEngine
from asr_provider_base import ProviderManager
from asr_provider_base.catalog import resolve_provider_execution
from asr_storage import ArtifactStore

QUALITY_METRICS = {"wer", "cer", "sample_accuracy"}
RESOURCE_METRICS = {
    "total_latency_ms",
    "per_utterance_latency_ms",
    "real_time_factor",
    "estimated_cost_usd",
    "first_partial_latency_ms",
    "finalization_latency_ms",
    "partial_count",
}


def _deep_merge(base: dict[str, Any], patch: dict[str, Any]) -> dict[str, Any]:
    merged = dict(base)
    for key, value in patch.items():
        if isinstance(value, dict) and isinstance(merged.get(key), dict):
            merged[key] = _deep_merge(merged[key], value)
        else:
            merged[key] = value
    return merged


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

        benchmark_settings = _deep_merge(
            {
                "batch": dict(benchmark_cfg.data.get("batch", {})) if isinstance(benchmark_cfg.data.get("batch", {}), dict) else {},
                "noise": dict(benchmark_cfg.data.get("noise", {})) if isinstance(benchmark_cfg.data.get("noise", {}), dict) else {},
                "streaming": dict(benchmark_cfg.data.get("streaming", {})) if isinstance(benchmark_cfg.data.get("streaming", {}), dict) else {},
            },
            request.benchmark_settings or {},
        )
        execution_mode = str(benchmark_settings.get("execution_mode", "batch") or "batch").strip() or "batch"
        if execution_mode not in {"batch", "streaming"}:
            raise ValueError(f"Unsupported benchmark execution_mode: {execution_mode}")
        max_samples = int(benchmark_settings.get("batch", {}).get("max_samples", 0) or 0)
        if max_samples > 0:
            samples = samples[:max_samples]

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
        enabled_metrics = sorted(set(enabled_metrics)) or [
            "wer",
            "cer",
            "sample_accuracy",
            "total_latency_ms",
            "per_utterance_latency_ms",
            "real_time_factor",
            "success_rate",
            "failure_rate",
        ]

        scenario = str(request.scenario or "").strip() or str((benchmark_cfg.data.get("scenarios") or ["clean_baseline"])[0])
        noise_plan = resolve_noise_plan(
            scenario=scenario,
            benchmark_settings=benchmark_settings,
            profile_scenarios=[str(item) for item in benchmark_cfg.data.get("scenarios", [])],
        )

        provider_snapshots: dict[str, str] = {}
        provider_execution: dict[str, dict[str, Any]] = {}
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
            overrides = dict((request.provider_overrides or {}).get(provider_profile, {}))
            preset_id = str(overrides.pop("preset_id", "") or "").strip()
            execution = resolve_provider_execution(
                provider_cfg.data,
                preset_id=preset_id,
                settings_overrides=overrides.get("settings", {}) if isinstance(overrides.get("settings", {}), dict) else {},
            )
            provider_snapshots[provider_profile] = provider_cfg.snapshot_path
            provider_execution[provider_profile] = {
                "preset_id": execution.get("selected_preset", ""),
                "preset": execution.get("preset", {}),
                "settings": execution.get("settings", {}),
            }

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
            "scenario": scenario,
            "benchmark_settings": benchmark_settings,
            "noise_plan": noise_plan,
            "provider_execution": provider_execution,
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
        derived_audio_root = run_dir / "derived_audio"

        for provider_profile in provider_profiles:
            execution = provider_execution.get(provider_profile, {})
            provider = self.provider_manager.create_from_profile(
                provider_profile,
                preset_id=str(execution.get("preset_id", "") or ""),
                settings_overrides=dict(execution.get("settings", {})),
            )
            caps = provider.discover_capabilities()
            provider_cost_per_minute = float(execution.get("preset", {}).get("estimated_cost_usd_per_min", 0.0) or 0.0)
            try:
                for sample in samples:
                    for variant in noise_plan:
                        sample_audio_path = sample.audio_path
                        if variant.get("noise_level") != "clean":
                            variant_name = f"{sample.sample_id}__{variant['noise_level']}.wav"
                            sample_audio_path = apply_noise_to_wav(
                                source_path=sample.audio_path,
                                output_path=str(derived_audio_root / variant_name),
                                snr_db=float(variant["snr_db"]),
                                seed=int(variant["seed"]),
                            )
                        estimated_cost_usd = 0.0
                        if provider_cost_per_minute > 0:
                            duration_min = max(float(sample.duration_sec or 0.0), 0.0) / 60.0
                            estimated_cost_usd = duration_min * provider_cost_per_minute
                        execution_meta = {
                            **variant,
                            "provider_preset": execution.get("preset_id", ""),
                            "provider_label": execution.get("preset", {}).get("label", ""),
                            "quality_tier": execution.get("preset", {}).get("quality_tier", "balanced"),
                            "resource_tier": execution.get("preset", {}).get("resource_tier", "medium"),
                            "estimated_cost_usd": estimated_cost_usd,
                            "execution_mode": execution_mode,
                            "streaming_mode": caps.streaming_mode if execution_mode == "streaming" else "none",
                            "streaming_chunk_ms": int(benchmark_settings.get("streaming", {}).get("chunk_ms", 500) or 500),
                        }
                        if execution_mode == "streaming":
                            if not caps.supports_streaming:
                                raise ValueError(f"Provider does not support streaming benchmark mode: {provider_profile}")
                            record = executor.run_sample_streaming(
                                run_id=run_id,
                                provider=provider,
                                provider_profile=provider_profile,
                                sample=sample,
                                session_id=session_id,
                                sample_audio_path=sample_audio_path,
                                execution_meta=execution_meta,
                            )
                        else:
                            record = executor.run_sample(
                                run_id=run_id,
                                provider=provider,
                                provider_profile=provider_profile,
                                sample=sample,
                                session_id=session_id,
                                sample_audio_path=sample_audio_path,
                                execution_meta=execution_meta,
                            )
                        results.append(record)
                        sample_key = "__".join(
                            [
                                provider_profile.replace("/", "_"),
                                str(execution.get("preset_id", "default") or "default"),
                                str(variant.get("noise_level", "clean") or "clean"),
                                sample.sample_id,
                            ]
                        )
                        self.artifact_store.save_raw_output(run_dir, sample_key, record)
                        self.artifact_store.save_normalized_output(
                            run_dir,
                            sample_key,
                            record.get("normalized_result", {}),
                        )
            finally:
                provider.teardown()

        self.artifact_store.save_json(run_dir / "metrics" / "results.json", results)
        self._save_csv(run_dir / "metrics" / "results.csv", results)

        summary = self._build_summary(
            run_id=run_id,
            benchmark_profile=request.benchmark_profile,
            dataset_id=dataset_id,
            providers=provider_profiles,
            results=results,
            scenario=scenario,
            execution_mode=execution_mode,
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
                "scenario": scenario,
                "execution_mode": execution_mode,
                "provider_execution": provider_execution,
            },
        )

    @staticmethod
    def _save_csv(path: Path, rows: list[dict[str, Any]]) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        fieldnames = [
            "run_id",
            "scenario",
            "noise_level",
            "noise_mode",
            "noise_snr_db",
            "provider_profile",
            "provider_preset",
            "provider_id",
            "execution_mode",
            "streaming_mode",
            "sample_id",
            "success",
            "text",
            "error_code",
            "error_message",
            "audio_duration_sec",
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
        scenario: str,
        execution_mode: str,
    ) -> dict[str, Any]:
        total = len(results)
        success = sum(1 for item in results if item.get("success"))
        failed = total - success

        metric_values: dict[str, list[float]] = {}
        by_provider: dict[str, dict[str, Any]] = {}
        by_noise: dict[str, dict[str, Any]] = {}
        for item in results:
            provider_key = f"{item.get('provider_profile', '')}:{item.get('provider_preset', '')}"
            row_metrics = item.get("metrics", {})
            by_provider.setdefault(provider_key, {"samples": 0, "metrics": {}})
            by_provider[provider_key]["samples"] += 1
            noise_key = str(item.get("noise_level", "clean"))
            by_noise.setdefault(noise_key, {"samples": 0, "metrics": {}})
            by_noise[noise_key]["samples"] += 1
            for key, value in row_metrics.items():
                metric_values.setdefault(key, []).append(float(value))
                by_provider[provider_key]["metrics"].setdefault(key, []).append(float(value))
                by_noise[noise_key]["metrics"].setdefault(key, []).append(float(value))

        mean_metrics = {
            key: (mean(values) if values else 0.0)
            for key, values in sorted(metric_values.items())
        }
        quality_metrics = {key: value for key, value in mean_metrics.items() if key in QUALITY_METRICS}
        resource_metrics = {key: value for key, value in mean_metrics.items() if key in RESOURCE_METRICS or key not in QUALITY_METRICS}

        return {
            "run_id": run_id,
            "benchmark_profile": benchmark_profile,
            "dataset_id": dataset_id,
            "providers": providers,
            "scenario": scenario,
            "execution_mode": execution_mode,
            "total_samples": total,
            "successful_samples": success,
            "failed_samples": failed,
            "mean_metrics": mean_metrics,
            "quality_metrics": quality_metrics,
            "resource_metrics": resource_metrics,
            "providers_summary": {
                key: {
                    "samples": value["samples"],
                    "mean_metrics": {
                        metric: (mean(series) if series else 0.0)
                        for metric, series in sorted(value["metrics"].items())
                    },
                }
                for key, value in sorted(by_provider.items())
            },
            "noise_summary": {
                key: {
                    "samples": value["samples"],
                    "mean_metrics": {
                        metric: (mean(series) if series else 0.0)
                        for metric, series in sorted(value["metrics"].items())
                    },
                }
                for key, value in sorted(by_noise.items())
            },
        }

    @staticmethod
    def _to_markdown(summary: dict[str, Any]) -> str:
        lines = [
            f"# Benchmark Summary: {summary['run_id']}",
            "",
            f"- benchmark_profile: `{summary['benchmark_profile']}`",
            f"- dataset_id: `{summary['dataset_id']}`",
            f"- providers: `{', '.join(summary['providers'])}`",
            f"- scenario: `{summary['scenario']}`",
            f"- execution_mode: `{summary.get('execution_mode', 'batch')}`",
            f"- total_samples: `{summary['total_samples']}`",
            f"- successful_samples: `{summary['successful_samples']}`",
            f"- failed_samples: `{summary['failed_samples']}`",
            "",
            "## Quality Metrics",
        ]
        for key, value in sorted(summary.get("quality_metrics", {}).items()):
            lines.append(f"- {key}: `{value}`")
        lines.append("")
        lines.append("## Resource Metrics")
        for key, value in sorted(summary.get("resource_metrics", {}).items()):
            lines.append(f"- {key}: `{value}`")
        lines.append("")
        lines.append("## Noise Summary")
        for noise_level, payload in sorted(summary.get("noise_summary", {}).items()):
            lines.append(f"- {noise_level}: `{json.dumps(payload.get('mean_metrics', {}), ensure_ascii=True)}`")
        return "\n".join(lines) + "\n"
