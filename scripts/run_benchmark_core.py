#!/usr/bin/env python3
"""Run canonical benchmark core and export operator-facing compatibility artifacts."""

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
from asr_metrics.io import save_benchmark_csv, save_benchmark_json  # noqa: E402
from asr_metrics.models import BenchmarkRecord  # noqa: E402
from asr_metrics.plotting import generate_all_plots  # noqa: E402


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


def _provider_backend_label(row: dict[str, object]) -> str:
    provider_profile = str(row.get("provider_profile", "") or "")
    provider_preset = str(row.get("provider_preset", "") or "")
    provider_id = str(row.get("provider_id", "") or "")
    if provider_profile and provider_preset:
        return f"{provider_profile}:{provider_preset}"
    if provider_profile:
        return provider_profile
    if provider_preset and provider_id:
        return f"{provider_id}:{provider_preset}"
    return provider_id or "unknown"


def _canonical_row_to_legacy_record(row: dict[str, object]) -> BenchmarkRecord:
    metrics = row.get("metrics", {})
    normalized_result = row.get("normalized_result", {})
    metric_values = metrics if isinstance(metrics, dict) else {}
    normalized_payload = normalized_result if isinstance(normalized_result, dict) else {}
    latency_payload = normalized_payload.get("latency", {})
    latency = latency_payload if isinstance(latency_payload, dict) else {}

    def _metric_float(name: str, default: float = 0.0) -> float:
        value = metric_values.get(name, default)
        return float(value) if isinstance(value, (int, float, str)) else default

    def _row_float(name: str, default: float = 0.0) -> float:
        value = row.get(name, default)
        return float(value) if isinstance(value, (int, float, str)) else default

    request_id = str(normalized_payload.get("request_id", "") or "").strip()
    if not request_id:
        request_id = (
            f"{str(row.get('run_id', '') or '')}:"
            f"{str(row.get('sample_id', '') or '')}:"
            f"{_provider_backend_label(row)}"
        )

    total_latency_ms = float(metric_values.get("total_latency_ms", 0.0) or 0.0)
    inference_ms = float(latency.get("total_ms", total_latency_ms) or total_latency_ms)

    return BenchmarkRecord(
        request_id=request_id,
        audio_id=str(row.get("sample_id", "") or ""),
        backend=_provider_backend_label(row),
        scenario=str(row.get("scenario", "clean_baseline") or "clean_baseline"),
        snr_db=_row_float("noise_snr_db") if row.get("noise_snr_db") is not None else None,
        wav_path=str(row.get("input_audio_path", "") or ""),
        language=str(normalized_payload.get("language", "") or ""),
        duration_sec=_row_float("audio_duration_sec"),
        text=str(row.get("text", "") or ""),
        transcript_ref=str(row.get("reference_text", "") or ""),
        transcript_hyp=str(row.get("text", "") or ""),
        wer=_metric_float("wer"),
        cer=_metric_float("cer"),
        latency_ms=total_latency_ms,
        preprocess_ms=0.0,
        inference_ms=inference_ms,
        postprocess_ms=0.0,
        audio_duration_sec=_row_float("audio_duration_sec"),
        rtf=_metric_float("real_time_factor"),
        cpu_percent=0.0,
        ram_mb=0.0,
        gpu_util_percent=0.0,
        gpu_mem_mb=0.0,
        success=bool(row.get("success", False)),
        error_code=str(row.get("error_code", "") or ""),
        error_message=str(row.get("error_message", "") or ""),
        cost_estimate=_metric_float("estimated_cost_usd"),
    )


def _export_compatibility_artifacts(
    *,
    summary_payload: dict[str, object],
    results_payload: list[dict[str, object]],
    results_dir: Path,
) -> dict[str, str]:
    results_dir.mkdir(parents=True, exist_ok=True)
    compat_records = [_canonical_row_to_legacy_record(row) for row in results_payload]

    compat_json = results_dir / "benchmark_results.json"
    compat_csv = results_dir / "benchmark_results.csv"
    plots_dir = results_dir / "plots"
    latest_summary = results_dir / "latest_benchmark_summary.json"
    latest_run = results_dir / "latest_benchmark_run.json"

    save_benchmark_json(compat_records, str(compat_json))
    save_benchmark_csv(compat_records, str(compat_csv))
    plots_dir.mkdir(parents=True, exist_ok=True)
    if compat_records:
        generate_all_plots(compat_records, str(plots_dir))

    latest_summary.write_text(
        json.dumps(summary_payload, ensure_ascii=True, indent=2) + "\n",
        encoding="utf-8",
    )
    latest_run.write_text(
        json.dumps(
            {
                "run_id": summary_payload.get("run_id", ""),
                "benchmark_profile": summary_payload.get("benchmark_profile", ""),
                "dataset_id": summary_payload.get("dataset_id", ""),
                "providers": summary_payload.get("providers", []),
                "summary_json": str(latest_summary),
                "compat_results_json": str(compat_json),
                "compat_results_csv": str(compat_csv),
                "plots_dir": str(plots_dir),
            },
            ensure_ascii=True,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    return {
        "compat_json": str(compat_json),
        "compat_csv": str(compat_csv),
        "plots_dir": str(plots_dir),
        "latest_summary": str(latest_summary),
        "latest_run": str(latest_run),
    }


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
    parser.add_argument("--results-dir", default=str(PROJECT_ROOT / "results"))
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
        run_id=str(args.run_id or "").strip(),
    )
    summary = orchestrator.run(request)
    run_dir = Path(str(summary.metadata.get("run_dir", "") or "")).resolve()
    if not run_dir.exists():
        raise SystemExit(f"Benchmark run directory not found: {run_dir}")

    summary_payload, results_payload = _load_run_payloads(run_dir)
    compat_paths = _export_compatibility_artifacts(
        summary_payload=summary_payload,
        results_payload=results_payload,
        results_dir=Path(args.results_dir),
    )

    result = {
        "run_id": summary.run_id,
        "total_samples": summary.total_samples,
        "successful_samples": summary.successful_samples,
        "failed_samples": summary.failed_samples,
        "run_dir": str(run_dir),
        "canonical_summary_json": str(run_dir / "reports" / "summary.json"),
        "canonical_results_json": str(run_dir / "metrics" / "results.json"),
        **compat_paths,
    }
    print(json.dumps(result, ensure_ascii=True, indent=2))


if __name__ == "__main__":
    main()
