"""Benchmark orchestrator with reproducible run artifacts.

This is the control-plane module for canonical benchmark execution. Its job is
to turn a high-level benchmark request into a fully resolved and reproducible
run plan:

- resolve dataset/provider/metric profiles
- derive scenario and noise variants
- execute the provider x sample x variant matrix
- persist manifests, metrics, and reports
"""

from __future__ import annotations

import csv
import json
import platform
from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from asr_config import resolve_profile, validate_benchmark_payload
from asr_core import make_run_id
from asr_datasets import DatasetRegistry, load_manifest
from asr_metrics.definitions import validate_metric_names
from asr_metrics.engine import MetricEngine
from asr_metrics.quality import has_quality_reference
from asr_metrics.summary import summarize_result_rows
from asr_observability import FileTraceExporter, ObservabilityConfig, load_observability_config
from asr_provider_base import ProviderManager
from asr_provider_base.catalog import resolve_provider_execution
from asr_storage import ArtifactStore

from asr_benchmark_core.executor import BatchExecutor
from asr_benchmark_core.models import BenchmarkRunRequest, BenchmarkRunSummary
from asr_benchmark_core.noise import (
    apply_noise_to_wav,
    canonicalize_scenario_name,
    resolve_noise_plan,
)


@dataclass(slots=True)
class ResolvedBenchmarkPlan:
    """Fully expanded benchmark execution plan.

    Every field here is meant to be stable enough to persist into the run
    manifest so a completed benchmark can be understood without re-resolving
    profiles from scratch.
    """
    run_id: str
    dataset_id: str
    dataset_profile_ref: str
    manifest_path: str
    samples: list[Any]
    benchmark_settings: dict[str, Any]
    execution_mode: str
    provider_profiles: list[str]
    metric_profiles: list[str]
    enabled_metrics: list[str]
    scenario: str
    noise_plan: list[dict[str, Any]]
    provider_execution: dict[str, dict[str, Any]]
    config_snapshots: dict[str, Any]


def _deep_merge(base: dict[str, Any], patch: dict[str, Any]) -> dict[str, Any]:
    merged = dict(base)
    for key, value in patch.items():
        if isinstance(value, dict) and isinstance(merged.get(key), dict):
            merged[key] = _deep_merge(merged[key], value)
        else:
            merged[key] = value
    return merged


def _as_bool(value: Any, *, default: bool) -> bool:
    if value is None:
        return default
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return bool(value)
    normalized = str(value).strip().lower()
    if not normalized:
        return default
    if normalized in {"1", "true", "yes", "on"}:
        return True
    if normalized in {"0", "false", "no", "off"}:
        return False
    return default


def _quality_metrics_enabled(enabled_metrics: list[str] | tuple[str, ...] | set[str]) -> bool:
    return any(metric_name in {"wer", "cer", "sample_accuracy"} for metric_name in enabled_metrics)


def _coerce_float(value: Any) -> float | None:
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _normalize_noise_key(noise_mode: Any, noise_level: Any) -> str:
    normalized_level = str(noise_level or "clean").strip().lower() or "clean"
    normalized_mode = str(noise_mode or "none").strip().lower() or "none"
    if normalized_level == "clean" or normalized_mode == "none":
        return "clean"
    return f"{normalized_mode}:{normalized_level}"


def _provider_key_from_result(result: dict[str, Any]) -> str:
    provider_profile = str(result.get("provider_profile", "") or "").strip()
    provider_preset = str(result.get("provider_preset", "") or "").strip()
    provider_id = str(result.get("provider_id", "") or "").strip()
    base = provider_profile or provider_id or "unknown"
    return f"{base}:{provider_preset}" if provider_preset else base


def _metric_from_summary(payload: dict[str, Any], metric_name: str) -> float | None:
    for section_name in (
        "quality_metrics",
        "latency_metrics",
        "reliability_metrics",
        "cost_metrics",
        "cost_totals",
        "streaming_metrics",
        "resource_metrics",
        "diagnostic_metrics",
        "mean_metrics",
    ):
        section = payload.get(section_name, {})
        if not isinstance(section, dict):
            continue
        value = _coerce_float(section.get(metric_name))
        if value is not None:
            return value

    statistic = payload.get("metric_statistics", {}).get(metric_name, {})
    if isinstance(statistic, dict):
        for key in ("value", "mean", "sum", "max"):
            value = _coerce_float(statistic.get(key))
            if value is not None:
                return value
    return None


def _provider_noise_summaries(results: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    provider_meta: dict[str, dict[str, str]] = {}
    for item in results:
        provider_key = _provider_key_from_result(item)
        noise_key = _normalize_noise_key(item.get("noise_mode"), item.get("noise_level"))
        grouped[(provider_key, noise_key)].append(item)
        provider_meta.setdefault(
            provider_key,
            {
                "provider_key": provider_key,
                "provider_profile": str(item.get("provider_profile", "") or ""),
                "provider_id": str(item.get("provider_id", "") or ""),
                "provider_preset": str(item.get("provider_preset", "") or ""),
                "provider_label": str(item.get("provider_label", "") or ""),
            },
        )

    payload: list[dict[str, Any]] = []
    for (provider_key, noise_key), rows in sorted(grouped.items()):
        first = rows[0] if rows else {}
        payload.append(
            {
                **provider_meta.get(provider_key, {}),
                "noise_key": noise_key,
                "noise_mode": str(first.get("noise_mode", "none") or "none"),
                "noise_level": str(first.get("noise_level", "clean") or "clean"),
                **summarize_result_rows(rows, exclude_corrupted=True),
            }
        )
    return payload


def _provider_tradeoff_snapshot(provider_summaries: list[dict[str, Any]]) -> list[dict[str, Any]]:
    snapshot: list[dict[str, Any]] = []
    for provider_summary in provider_summaries:
        snapshot.append(
            {
                "provider_key": str(provider_summary.get("provider_key", "") or ""),
                "provider_profile": str(provider_summary.get("provider_profile", "") or ""),
                "provider_id": str(provider_summary.get("provider_id", "") or ""),
                "provider_preset": str(provider_summary.get("provider_preset", "") or ""),
                "wer": _metric_from_summary(provider_summary, "wer"),
                "cer": _metric_from_summary(provider_summary, "cer"),
                "sample_accuracy": _metric_from_summary(provider_summary, "sample_accuracy"),
                "end_to_end_latency_ms": _metric_from_summary(provider_summary, "end_to_end_latency_ms")
                or _metric_from_summary(provider_summary, "time_to_final_result_ms")
                or _metric_from_summary(provider_summary, "total_latency_ms")
                or _metric_from_summary(provider_summary, "per_utterance_latency_ms"),
                "end_to_end_rtf": _metric_from_summary(provider_summary, "end_to_end_rtf")
                or _metric_from_summary(provider_summary, "real_time_factor")
                or _metric_from_summary(provider_summary, "provider_compute_rtf"),
                "estimated_cost_usd": _metric_from_summary(provider_summary, "estimated_cost_usd"),
                "success_rate": _metric_from_summary(provider_summary, "success_rate"),
                "total_samples": int(provider_summary.get("total_samples", 0) or 0),
                "warning_samples": int(provider_summary.get("warning_samples", 0) or 0),
            }
        )
    snapshot.sort(
        key=lambda item: (
            float(item.get("wer")) if item.get("wer") is not None else float("inf"),
            float(item.get("end_to_end_latency_ms"))
            if item.get("end_to_end_latency_ms") is not None
            else float("inf"),
            float(item.get("estimated_cost_usd"))
            if item.get("estimated_cost_usd") is not None
            else float("inf"),
        )
    )
    return snapshot


def _sample_error_summary(results: list[dict[str, Any]]) -> dict[str, Any]:
    total_rows = len(results)
    failed_rows = sum(1 for item in results if not bool(item.get("success")))
    noisy_rows = sum(
        1 for item in results if _normalize_noise_key(item.get("noise_mode"), item.get("noise_level")) != "clean"
    )
    high_wer_rows = sum(1 for item in results if (_coerce_float(item.get("metrics", {}).get("wer")) or 0.0) >= 0.25)
    high_cer_rows = sum(1 for item in results if (_coerce_float(item.get("metrics", {}).get("cer")) or 0.0) >= 0.15)
    exact_match_rows = sum(
        1 for item in results if (_coerce_float(item.get("metrics", {}).get("sample_accuracy")) or 0.0) >= 1.0
    )
    error_codes = Counter(
        str(item.get("error_code", "") or "").strip()
        for item in results
        if str(item.get("error_code", "") or "").strip()
    )
    return {
        "total_rows": total_rows,
        "failed_rows": failed_rows,
        "noisy_rows": noisy_rows,
        "clean_rows": total_rows - noisy_rows,
        "high_wer_rows": high_wer_rows,
        "high_cer_rows": high_cer_rows,
        "exact_match_rows": exact_match_rows,
        "top_error_codes": [
            {"error_code": code, "count": count}
            for code, count in error_codes.most_common(6)
        ],
    }


def _available_analysis_sections(
    provider_summaries: list[dict[str, Any]],
    provider_noise_summaries: list[dict[str, Any]],
    sample_error_summary: dict[str, Any],
) -> dict[str, bool]:
    return {
        "provider_comparison": bool(provider_summaries),
        "noise_robustness": len({item.get("noise_key", "") for item in provider_noise_summaries}) > 1,
        "sample_explorer": bool(sample_error_summary.get("total_rows", 0)),
        "latency_breakdown": bool(provider_summaries),
        "reliability": any(bool(item.get("reliability_metrics")) for item in provider_summaries),
        "cost": any(bool(item.get("cost_metrics")) for item in provider_summaries),
        "streaming": any(bool(item.get("streaming_metrics")) for item in provider_summaries),
        "resource": any(bool(item.get("resource_metrics")) for item in provider_summaries),
        "diagnostics": bool(sample_error_summary),
    }


def _validate_quality_reference_samples(
    samples: list[Any],
    *,
    enabled_metrics: list[str] | tuple[str, ...] | set[str],
) -> None:
    if not _quality_metrics_enabled(enabled_metrics):
        return

    invalid_sample_ids = [
        str(getattr(sample, "sample_id", "") or "")
        for sample in samples
        if not has_quality_reference(str(getattr(sample, "transcript", "") or ""))
    ]
    if not invalid_sample_ids:
        return

    preview = ", ".join(invalid_sample_ids[:8])
    if len(invalid_sample_ids) > 8:
        preview += f" (+{len(invalid_sample_ids) - 8} more)"
    raise ValueError(
        "Benchmark quality metrics require non-empty normalized reference transcripts. "
        f"Invalid samples: {preview}"
    )


class BenchmarkOrchestrator:
    """Own the canonical benchmark lifecycle from request to stored artifacts."""

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
        self.observability_config: ObservabilityConfig | None = None
        self.trace_exporter: FileTraceExporter | None = None
        self.observability_init_error = ""
        try:
            self.observability_config = load_observability_config(configs_root=configs_root)
            self.trace_exporter = FileTraceExporter(self.observability_config)
        except Exception as exc:
            self.observability_init_error = str(exc)
            self.observability_config = None
            self.trace_exporter = None

    @staticmethod
    def _default_enabled_metrics() -> list[str]:
        return [
            "wer",
            "cer",
            "sample_accuracy",
            "provider_compute_latency_ms",
            "end_to_end_latency_ms",
            "provider_compute_rtf",
            "end_to_end_rtf",
            "success_rate",
            "failure_rate",
        ]

    def _resolve_benchmark_profile(self, request: BenchmarkRunRequest) -> tuple[Any, str]:
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
        return benchmark_cfg, benchmark_profile_id

    def _resolve_dataset_plan(
        self,
        request: BenchmarkRunRequest,
        benchmark_cfg: Any,
    ) -> tuple[str, Any, str, list[Any]]:
        dataset_profile_ref = request.dataset_profile or str(
            benchmark_cfg.data.get("dataset_profile", "")
        )
        dataset_profile_id = dataset_profile_ref
        if dataset_profile_id.startswith("datasets/"):
            dataset_profile_id = dataset_profile_id.split("/", 1)[1]
        if not dataset_profile_id:
            raise ValueError("dataset_profile is required")

        dataset_cfg = resolve_profile(
            profile_type="datasets",
            profile_id=dataset_profile_id,
            configs_root=self.configs_root,
        )
        manifest_path = str(dataset_cfg.data.get("manifest_path", "")).strip()
        if not manifest_path:
            raise ValueError("Dataset profile is missing manifest_path")

        samples = load_manifest(manifest_path)
        if not samples:
            raise ValueError(f"Dataset manifest has no samples: {manifest_path}")
        return dataset_profile_ref, dataset_cfg, manifest_path, samples

    def _resolve_benchmark_settings(
        self,
        benchmark_cfg: Any,
        request: BenchmarkRunRequest,
        samples: list[Any],
    ) -> tuple[dict[str, Any], str, list[Any]]:
        benchmark_settings = _deep_merge(
            {
                "execution_mode": str(
                    benchmark_cfg.data.get("execution_mode", "batch") or "batch"
                ).strip()
                or "batch",
                "save_raw_outputs": _as_bool(
                    benchmark_cfg.data.get("save_raw_outputs", True), default=True
                ),
                "save_normalized_outputs": _as_bool(
                    benchmark_cfg.data.get("save_normalized_outputs", True), default=True
                ),
                "batch": dict(benchmark_cfg.data.get("batch", {}))
                if isinstance(benchmark_cfg.data.get("batch", {}), dict)
                else {},
                "noise": dict(benchmark_cfg.data.get("noise", {}))
                if isinstance(benchmark_cfg.data.get("noise", {}), dict)
                else {},
                "streaming": dict(benchmark_cfg.data.get("streaming", {}))
                if isinstance(benchmark_cfg.data.get("streaming", {}), dict)
                else {},
            },
            request.benchmark_settings or {},
        )
        execution_mode = (
            str(benchmark_settings.get("execution_mode", "batch") or "batch").strip() or "batch"
        )
        if execution_mode not in {"batch", "streaming"}:
            raise ValueError(f"Unsupported benchmark execution_mode: {execution_mode}")
        validation_payload = dict(benchmark_cfg.data)
        validation_payload["execution_mode"] = execution_mode
        validation_payload["batch"] = (
            dict(benchmark_settings.get("batch", {}))
            if isinstance(benchmark_settings.get("batch", {}), dict)
            else benchmark_settings.get("batch", {})
        )
        validation_payload["streaming"] = (
            dict(benchmark_settings.get("streaming", {}))
            if isinstance(benchmark_settings.get("streaming", {}), dict)
            else benchmark_settings.get("streaming", {})
        )
        errors = validate_benchmark_payload(validation_payload)
        if errors:
            raise ValueError(f"Benchmark settings validation failed: {'; '.join(errors)}")
        max_samples = int(benchmark_settings.get("batch", {}).get("max_samples", 0) or 0)
        if max_samples > 0:
            samples = samples[:max_samples]
        return benchmark_settings, execution_mode, samples

    def _resolve_metric_plan(
        self, benchmark_cfg: Any
    ) -> tuple[list[str], dict[str, str], list[str]]:
        enabled_metrics: list[str] = []
        metric_profiles = [str(item) for item in benchmark_cfg.data.get("metric_profiles", [])]
        metric_snapshots: dict[str, str] = {}
        for metric_profile in metric_profiles:
            metric_id = (
                metric_profile.split("/", 1)[1]
                if metric_profile.startswith("metrics/")
                else metric_profile
            )
            metric_cfg = resolve_profile(
                profile_type="metrics",
                profile_id=metric_id,
                configs_root=self.configs_root,
            )
            enabled_metrics.extend([str(item) for item in metric_cfg.data.get("metrics", [])])
            metric_snapshots[metric_profile] = metric_cfg.snapshot_path
        enabled_metrics = sorted(set(enabled_metrics)) or self._default_enabled_metrics()
        errors = validate_metric_names(enabled_metrics)
        if errors:
            raise ValueError("; ".join(errors))
        return metric_profiles, metric_snapshots, enabled_metrics

    def _resolve_provider_profiles(
        self, request: BenchmarkRunRequest, benchmark_cfg: Any
    ) -> list[str]:
        provider_profiles = request.providers or [
            str(item) for item in benchmark_cfg.data.get("providers", []) if str(item).strip()
        ]
        if not provider_profiles:
            raise ValueError("No providers selected for benchmark run")
        return provider_profiles

    def _resolve_provider_execution_plan(
        self,
        *,
        provider_profiles: list[str],
        provider_overrides: dict[str, dict[str, Any]] | None,
    ) -> tuple[dict[str, str], dict[str, dict[str, Any]]]:
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
            overrides = dict((provider_overrides or {}).get(provider_profile, {}))
            preset_id = str(overrides.pop("preset_id", "") or "").strip()
            settings = (
                overrides.get("settings", {})
                if isinstance(overrides.get("settings", {}), dict)
                else {}
            )
            execution = resolve_provider_execution(
                provider_cfg.data,
                preset_id=preset_id,
                settings_overrides=settings,
            )
            provider_snapshots[provider_profile] = provider_cfg.snapshot_path
            provider_execution[provider_profile] = {
                "preset_id": execution.get("selected_preset", ""),
                "preset": execution.get("preset", {}),
                "settings": execution.get("settings", {}),
            }
        return provider_snapshots, provider_execution

    def _resolve_run_plan(self, request: BenchmarkRunRequest) -> ResolvedBenchmarkPlan:
        """Resolve everything needed before the first provider call happens.

        This separates configuration/validation failure from execution failure
        and makes the resulting run manifest deterministic and debuggable.
        """
        benchmark_cfg, _benchmark_profile_id = self._resolve_benchmark_profile(request)
        dataset_profile_ref, dataset_cfg, manifest_path, samples = self._resolve_dataset_plan(
            request, benchmark_cfg
        )
        benchmark_settings, execution_mode, samples = self._resolve_benchmark_settings(
            benchmark_cfg,
            request,
            samples,
        )
        provider_profiles = self._resolve_provider_profiles(request, benchmark_cfg)
        metric_profiles, metric_snapshots, enabled_metrics = self._resolve_metric_plan(
            benchmark_cfg
        )
        _validate_quality_reference_samples(samples, enabled_metrics=enabled_metrics)

        scenario = canonicalize_scenario_name(
            str(request.scenario or "").strip()
            or str((benchmark_cfg.data.get("scenarios") or ["clean_baseline"])[0])
        )
        noise_plan = resolve_noise_plan(
            scenario=scenario,
            benchmark_settings=benchmark_settings,
            profile_scenarios=[str(item) for item in benchmark_cfg.data.get("scenarios", [])],
        )
        scenario = str(noise_plan[0].get("scenario", scenario) if noise_plan else scenario)
        cfg_provider_overrides = benchmark_cfg.data.get("provider_overrides", {})
        provider_overrides = (
            cfg_provider_overrides if isinstance(cfg_provider_overrides, dict) else {}
        )
        if request.provider_overrides:
            provider_overrides = _deep_merge(provider_overrides, request.provider_overrides)
        provider_snapshots, provider_execution = self._resolve_provider_execution_plan(
            provider_profiles=provider_profiles,
            provider_overrides=provider_overrides,
        )

        return ResolvedBenchmarkPlan(
            run_id=request.run_id or make_run_id("bench"),
            dataset_id=str(dataset_cfg.data.get("dataset_id", dataset_profile_ref)),
            dataset_profile_ref=dataset_profile_ref,
            manifest_path=manifest_path,
            samples=samples,
            benchmark_settings=benchmark_settings,
            execution_mode=execution_mode,
            provider_profiles=provider_profiles,
            metric_profiles=metric_profiles,
            enabled_metrics=enabled_metrics,
            scenario=scenario,
            noise_plan=noise_plan,
            provider_execution=provider_execution,
            config_snapshots={
                "benchmark": benchmark_cfg.snapshot_path,
                "dataset": dataset_cfg.snapshot_path,
                "providers": provider_snapshots,
                "metrics": metric_snapshots,
            },
        )

    def _build_run_manifest(
        self,
        request: BenchmarkRunRequest,
        plan: ResolvedBenchmarkPlan,
        *,
        started_at: str,
        completed_at: str = "",
    ) -> dict[str, Any]:
        return {
            "run_id": plan.run_id,
            "created_at": datetime.now(UTC).isoformat(),
            "started_at": started_at,
            "completed_at": completed_at,
            "benchmark_profile": request.benchmark_profile,
            "dataset_profile": plan.dataset_profile_ref,
            "providers": plan.provider_profiles,
            "metric_profiles": plan.metric_profiles,
            "enabled_metrics": plan.enabled_metrics,
            "scenario": plan.scenario,
            "benchmark_settings": plan.benchmark_settings,
            "noise_plan": plan.noise_plan,
            "provider_execution": plan.provider_execution,
            "config_snapshots": plan.config_snapshots,
            "environment": {
                "python": platform.python_version(),
                "platform": platform.platform(),
            },
            "dataset_manifest": plan.manifest_path,
            "sample_count": len(plan.samples),
        }

    @staticmethod
    def _estimate_provider_cost_per_minute(execution: dict[str, Any]) -> float:
        provider_cost_per_minute = float(
            execution.get("preset", {}).get("estimated_cost_usd_per_min", 0.0) or 0.0
        )
        return provider_cost_per_minute if provider_cost_per_minute > 0 else 0.0

    @staticmethod
    def _resolve_sample_audio_path(
        *, sample: Any, variant: dict[str, Any], derived_audio_root: Path
    ) -> str:
        if variant.get("noise_level") == "clean":
            return sample.audio_path
        noise_mode = str(variant.get("noise_mode", "white") or "white")
        variant_name = f"{sample.sample_id}__{noise_mode}__{variant['noise_level']}.wav"
        return apply_noise_to_wav(
            source_path=sample.audio_path,
            output_path=str(derived_audio_root / variant_name),
            snr_db=float(variant["snr_db"]),
            seed=int(variant["seed"]),
            noise_mode=noise_mode,
        )

    def _build_execution_meta(
        self,
        *,
        plan: ResolvedBenchmarkPlan,
        execution: dict[str, Any],
        caps: Any,
        sample: Any,
        variant: dict[str, Any],
    ) -> dict[str, Any]:
        return {
            **variant,
            "provider_preset": execution.get("preset_id", ""),
            "provider_label": execution.get("preset", {}).get("label", ""),
            "quality_tier": execution.get("preset", {}).get("quality_tier", "balanced"),
            "resource_tier": execution.get("preset", {}).get("resource_tier", "medium"),
            "estimated_cost_usd_per_min": self._estimate_provider_cost_per_minute(execution),
            "execution_mode": plan.execution_mode,
            "streaming_mode": caps.streaming_mode if plan.execution_mode == "streaming" else "none",
            "streaming_chunk_ms": int(
                plan.benchmark_settings.get("streaming", {}).get("chunk_ms", 500) or 500
            ),
            "streaming_replay_rate": float(
                plan.benchmark_settings.get("streaming", {}).get("replay_rate", 1.0) or 0.0
            ),
        }

    def _execute_provider_matrix(
        self,
        *,
        plan: ResolvedBenchmarkPlan,
        executor: BatchExecutor,
        run_dir: Path,
    ) -> list[dict[str, Any]]:
        """Execute the cartesian product of providers, samples, and noise variants."""
        results: list[dict[str, Any]] = []
        session_id = f"benchmark_{plan.run_id}"
        derived_audio_root = run_dir / "derived_audio"
        save_raw_outputs = _as_bool(
            plan.benchmark_settings.get("save_raw_outputs", True), default=True
        )
        save_normalized_outputs = _as_bool(
            plan.benchmark_settings.get("save_normalized_outputs", True), default=True
        )

        for provider_profile in plan.provider_profiles:
            execution = plan.provider_execution.get(provider_profile, {})
            provider = self.provider_manager.create_from_profile(
                provider_profile,
                preset_id=str(execution.get("preset_id", "") or ""),
                settings_overrides=dict(execution.get("settings", {})),
            )
            caps = provider.discover_capabilities()
            if plan.execution_mode == "streaming" and not caps.supports_streaming:
                provider.teardown()
                raise ValueError(
                    f"Provider does not support streaming benchmark mode: {provider_profile}"
                )
            try:
                for sample in plan.samples:
                    for variant in plan.noise_plan:
                        sample_audio_path = self._resolve_sample_audio_path(
                            sample=sample,
                            variant=variant,
                            derived_audio_root=derived_audio_root,
                        )
                        execution_meta = self._build_execution_meta(
                            plan=plan,
                            execution=execution,
                            caps=caps,
                            sample=sample,
                            variant=variant,
                        )
                        if plan.execution_mode == "streaming":
                            record = executor.run_sample_streaming(
                                run_id=plan.run_id,
                                provider=provider,
                                provider_profile=provider_profile,
                                sample=sample,
                                session_id=session_id,
                                sample_audio_path=sample_audio_path,
                                execution_meta=execution_meta,
                            )
                        else:
                            record = executor.run_sample(
                                run_id=plan.run_id,
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
                        if save_raw_outputs:
                            self.artifact_store.save_raw_output(run_dir, sample_key, record)
                        if save_normalized_outputs:
                            self.artifact_store.save_normalized_output(
                                run_dir,
                                sample_key,
                                record.get("normalized_result", {}),
                            )
            finally:
                provider.teardown()
        return results

    def run(self, request: BenchmarkRunRequest) -> BenchmarkRunSummary:
        plan = self._resolve_run_plan(request)
        run_dir = self.artifact_store.make_benchmark_run(plan.run_id)
        started_at = datetime.now(UTC).isoformat()
        manifest_ref = self.artifact_store.save_manifest(
            run_dir,
            self._build_run_manifest(request, plan, started_at=started_at),
        )

        metric_engine = MetricEngine(enabled_metrics=plan.enabled_metrics)
        executor = BatchExecutor(
            metric_engine=metric_engine,
            observability_config=self.observability_config,
            trace_exporter=self.trace_exporter,
            run_dir=str(run_dir),
        )
        results = self._execute_provider_matrix(plan=plan, executor=executor, run_dir=run_dir)

        self.artifact_store.save_json(run_dir / "metrics" / "results.json", results)
        self._save_csv(run_dir / "metrics" / "results.csv", results)

        summary = self._build_summary(
            run_id=plan.run_id,
            benchmark_profile=request.benchmark_profile,
            dataset_id=plan.dataset_id,
            providers=plan.provider_profiles,
            results=results,
            scenario=plan.scenario,
            execution_mode=plan.execution_mode,
        )
        completed_at = datetime.now(UTC).isoformat()
        self.artifact_store.save_manifest(
            run_dir,
            self._build_run_manifest(
                request,
                plan,
                started_at=started_at,
                completed_at=completed_at,
            ),
        )

        summary_ref = self.artifact_store.save_json(run_dir / "reports" / "summary.json", summary)
        md_ref = self.artifact_store.save_report(
            run_dir,
            "summary.md",
            self._to_markdown(summary),
        )
        self._export_reports_copy(
            run_id=plan.run_id,
            summary=summary,
            results=results,
            summary_markdown=self._to_markdown(summary),
        )

        return BenchmarkRunSummary(
            run_id=plan.run_id,
            benchmark_profile=request.benchmark_profile,
            dataset_id=plan.dataset_id,
            providers=plan.provider_profiles,
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
                "enabled_metrics": plan.enabled_metrics,
                "scenario": plan.scenario,
                "execution_mode": plan.execution_mode,
                "provider_execution": plan.provider_execution,
            },
        )

    def _export_reports_copy(
        self,
        *,
        run_id: str,
        summary: dict[str, Any],
        results: list[dict[str, Any]],
        summary_markdown: str,
    ) -> None:
        reports_root = Path("reports") / "benchmarks" / run_id
        reports_root.mkdir(parents=True, exist_ok=True)
        (reports_root / "summary.json").write_text(
            json.dumps(summary, ensure_ascii=True, indent=2),
            encoding="utf-8",
        )
        (reports_root / "summary.md").write_text(summary_markdown, encoding="utf-8")
        (reports_root / "results.json").write_text(
            json.dumps(results, ensure_ascii=True, indent=2),
            encoding="utf-8",
        )
        self._save_csv(reports_root / "results.csv", results)

    @staticmethod
    def _save_csv(path: Path, rows: list[dict[str, Any]]) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        base_fieldnames = [
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
            "reference_text",
            "normalized_reference_text",
            "normalized_hypothesis_text",
            "error_code",
            "error_message",
            "audio_duration_sec",
            "metrics_json",
        ]
        metric_fieldnames = sorted(
            {
                str(name)
                for row in rows
                for name in (row.get("metrics", {}) or {}).keys()
                if str(name).strip()
            }
        )
        quality_fieldnames = [
            "quality_reference_word_count",
            "quality_reference_char_count",
            "quality_word_edits",
            "quality_char_edits",
            "quality_exact_match",
            "quality_wer",
            "quality_cer",
        ]
        fieldnames = [*base_fieldnames, *metric_fieldnames, *quality_fieldnames]
        with path.open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=fieldnames)
            writer.writeheader()
            for row in rows:
                out = dict(row)
                metric_values = dict(out.get("metrics", {}) or {})
                quality_support = dict(out.get("quality_support", {}) or {})
                out["metrics_json"] = json.dumps(metric_values, ensure_ascii=True)
                for metric_name in metric_fieldnames:
                    out[metric_name] = metric_values.get(metric_name, "")
                out["quality_reference_word_count"] = quality_support.get(
                    "reference_word_count", ""
                )
                out["quality_reference_char_count"] = quality_support.get(
                    "reference_char_count", ""
                )
                out["quality_word_edits"] = quality_support.get("word_edits", "")
                out["quality_char_edits"] = quality_support.get("char_edits", "")
                out["quality_exact_match"] = quality_support.get("exact_match", "")
                out["quality_wer"] = quality_support.get("wer", "")
                out["quality_cer"] = quality_support.get("cer", "")
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
        by_provider: dict[str, list[dict[str, Any]]] = {}
        by_noise: dict[str, list[dict[str, Any]]] = {}
        for item in results:
            provider_profile = str(item.get("provider_profile", "") or "")
            provider_preset = str(item.get("provider_preset", "") or "")
            provider_key = (
                f"{provider_profile}:{provider_preset}" if provider_preset else provider_profile
            )
            by_provider.setdefault(provider_key, []).append(item)
            noise_level = str(item.get("noise_level", "clean") or "clean")
            noise_mode = str(item.get("noise_mode", "none") or "none")
            noise_key = noise_level if noise_mode == "none" else f"{noise_mode}:{noise_level}"
            by_noise.setdefault(noise_key, []).append(item)

        aggregate = summarize_result_rows(results, exclude_corrupted=True)
        provider_summaries: list[dict[str, Any]] = []
        for provider_key, provider_rows in sorted(by_provider.items()):
            first_row = provider_rows[0] if provider_rows else {}
            provider_summaries.append(
                {
                    "provider_key": provider_key,
                    "provider_profile": str(first_row.get("provider_profile", "") or ""),
                    "provider_id": str(first_row.get("provider_id", "") or ""),
                    "provider_preset": str(first_row.get("provider_preset", "") or ""),
                    "provider_label": str(first_row.get("provider_label", "") or ""),
                    **summarize_result_rows(provider_rows, exclude_corrupted=True),
                }
            )
        if len(provider_summaries) > 1:
            aggregate = {
                "metrics_semantics_version": aggregate.get("metrics_semantics_version", 2),
                "legacy_metrics": aggregate.get("legacy_metrics", False),
                "mixed_semantics": aggregate.get("mixed_semantics", False),
                "samples": aggregate["samples"],
                "total_samples": aggregate["total_samples"],
                "successful_samples": aggregate["successful_samples"],
                "failed_samples": aggregate["failed_samples"],
                "aggregate_samples": aggregate["aggregate_samples"],
                "warning_samples": aggregate.get("warning_samples", 0),
                "mean_metrics": {},
                "metric_counts": {},
                "metric_statistics": {},
                "metric_metadata": {},
                "aggregate_excludes_corrupted": aggregate["aggregate_excludes_corrupted"],
                "corrupted_samples": aggregate["corrupted_samples"],
                "quality_metrics": {},
                "latency_metrics": {},
                "reliability_metrics": {},
                "cost_metrics": {},
                "cost_totals": {},
                "streaming_metrics": {},
                "resource_metrics": {},
                "diagnostic_metrics": {},
            }
        provider_noise_summaries = _provider_noise_summaries(results)
        provider_tradeoff_snapshot = _provider_tradeoff_snapshot(provider_summaries)
        sample_error_summary = _sample_error_summary(results)

        summary = {
            "run_id": run_id,
            "benchmark_profile": benchmark_profile,
            "dataset_id": dataset_id,
            "providers": providers,
            "scenario": scenario,
            "execution_mode": execution_mode,
            "noise_levels": sorted(
                {str(item.get("noise_level", "clean") or "clean") for item in results}
            ),
            "noise_modes": sorted(
                {str(item.get("noise_mode", "none") or "none") for item in results}
            ),
            "aggregate_scope": "single_provider"
            if len(provider_summaries) <= 1
            else "provider_only",
            **aggregate,
            "provider_summaries": provider_summaries,
            "providers_summary": {entry["provider_key"]: entry for entry in provider_summaries},
            "noise_summary": {
                key: summarize_result_rows(value, exclude_corrupted=True)
                for key, value in sorted(by_noise.items())
            },
            "provider_noise_summaries": provider_noise_summaries,
            "provider_tradeoff_snapshot": provider_tradeoff_snapshot,
            "sample_error_summary": sample_error_summary,
            "available_analysis_sections": _available_analysis_sections(
                provider_summaries,
                provider_noise_summaries,
                sample_error_summary,
            ),
        }
        return summary

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
            f"- noise_modes: `{', '.join(summary.get('noise_modes', []))}`",
            f"- noise_levels: `{', '.join(summary.get('noise_levels', []))}`",
            f"- aggregate_scope: `{summary.get('aggregate_scope', 'provider_only')}`",
            f"- total_samples: `{summary['total_samples']}`",
            f"- successful_samples: `{summary['successful_samples']}`",
            f"- failed_samples: `{summary['failed_samples']}`",
            f"- aggregate_samples: `{summary.get('aggregate_samples', summary['total_samples'])}`",
            f"- corrupted_samples: `{summary.get('corrupted_samples', 0)}`",
            "",
            "## Per-Provider Summary",
        ]
        if summary.get("provider_summaries"):
            for provider_summary in summary.get("provider_summaries", []):
                provider_name = str(
                    provider_summary.get("provider_profile")
                    or provider_summary.get("provider_id")
                    or provider_summary.get("provider_key")
                    or "unknown"
                )
                provider_preset = str(provider_summary.get("provider_preset", "") or "")
                lines.append("")
                lines.append(
                    f"### {provider_name}"
                    + (f" (preset: `{provider_preset}`)" if provider_preset else "")
                )
                lines.append(f"- samples: `{provider_summary.get('total_samples', 0)}`")
                lines.append(
                    f"- successful_samples: `{provider_summary.get('successful_samples', 0)}`"
                )
                lines.append(f"- failed_samples: `{provider_summary.get('failed_samples', 0)}`")
                for section_name, metrics in (
                    ("quality_metrics", provider_summary.get("quality_metrics", {})),
                    ("latency_metrics", provider_summary.get("latency_metrics", {})),
                    ("reliability_metrics", provider_summary.get("reliability_metrics", {})),
                    ("cost_metrics", provider_summary.get("cost_metrics", {})),
                    ("cost_totals", provider_summary.get("cost_totals", {})),
                    ("streaming_metrics", provider_summary.get("streaming_metrics", {})),
                ):
                    if not metrics:
                        continue
                    lines.append(f"- {section_name}: `{json.dumps(metrics, ensure_ascii=True)}`")
                provider_cost_stats = provider_summary.get("metric_statistics", {}).get(
                    "estimated_cost_usd", {}
                )
                if isinstance(provider_cost_stats, dict) and "sum" in provider_cost_stats:
                    lines.append(f"- estimated_cost_total_usd: `{provider_cost_stats['sum']}`")
            lines.append("")
        lines.append("## Noise Summary")
        for noise_level, payload in sorted(summary.get("noise_summary", {}).items()):
            metrics_json = json.dumps(payload.get("mean_metrics", {}), ensure_ascii=True)
            lines.append(f"- {noise_level}: `{metrics_json}`")
        return "\n".join(lines) + "\n"
