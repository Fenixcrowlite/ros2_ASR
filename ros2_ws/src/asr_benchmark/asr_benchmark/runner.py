"""Legacy compatibility benchmark runner.

This module preserves the original backend-centric benchmark flow for older ROS2
launch wrappers and flat exports. Canonical benchmarking now lives in
`asr_benchmark_core` and `asr_benchmark_nodes`.
"""

from __future__ import annotations

import argparse
import logging
import tempfile
import uuid
from pathlib import Path

from asr_core.audio import wav_info, wav_pcm_chunks
from asr_core.config import load_runtime_config
from asr_core.factory import create_backend
from asr_core.language import normalize_language_code
from asr_core.models import AsrRequest, AsrResponse
from asr_metrics.collector import MetricsCollector
from asr_metrics.io import save_benchmark_csv, save_benchmark_json
from asr_metrics.models import BenchmarkRecord
from asr_metrics.plotting import generate_all_plots

from asr_benchmark.dataset import DatasetItem, load_manifest_csv
from asr_benchmark.noise import add_white_noise_snr

LOG = logging.getLogger(__name__)


def _scenario_wav(item: DatasetItem, scenario: str) -> tuple[str, list[str]]:
    """Return scenario-specific WAV path and list of temp files to cleanup."""
    source_wav = item.resolved_wav_path or item.wav_path
    temp_files: list[str] = []
    if scenario == "clean":
        return source_wav, temp_files
    if scenario.startswith("snr"):
        try:
            snr = float(scenario.replace("snr", ""))
        except ValueError as exc:
            raise ValueError(f"Invalid SNR scenario format: {scenario}") from exc
        tmp = tempfile.NamedTemporaryFile(suffix=".wav", prefix=f"noise_{int(snr)}_", delete=False)
        tmp.close()
        add_white_noise_snr(source_wav, tmp.name, snr_db=snr)
        temp_files.append(tmp.name)
        return tmp.name, temp_files
    raise ValueError(f"Unsupported scenario: {scenario}")


def _normalize_scenarios(raw: object) -> list[str]:
    """Normalize benchmark scenarios from YAML into deterministic list of labels."""
    values: list[str] = []
    if isinstance(raw, str):
        values = [chunk.strip() for chunk in raw.split(",")]
    elif isinstance(raw, list):
        values = [str(chunk).strip() for chunk in raw]
    elif raw is None:
        values = []
    else:
        raise ValueError("benchmark.scenarios must be a list or comma-separated string")

    normalized = [item for item in values if item]
    if not normalized:
        raise ValueError("No benchmark scenarios configured")
    for scenario in normalized:
        if scenario == "clean":
            continue
        if scenario.startswith("snr"):
            try:
                float(scenario.replace("snr", ""))
                continue
            except ValueError as exc:
                raise ValueError(f"Invalid SNR scenario format: {scenario}") from exc
        raise ValueError(f"Unsupported scenario: {scenario}")
    return normalized


def _run_single(
    backend,
    backend_name: str,
    item: DatasetItem,
    scenario: str,
    collector: MetricsCollector,
) -> BenchmarkRecord:
    """Run single recognize-once benchmark sample."""
    wav_path, temp_files = _scenario_wav(item, scenario)
    try:
        response = backend.recognize_once(
            AsrRequest(
                wav_path=wav_path,
                language=normalize_language_code(item.language, fallback="en-US"),
                enable_word_timestamps=True,
            )
        )
        return collector.record(
            backend=backend_name,
            scenario=scenario,
            wav_path=item.wav_path,
            language=normalize_language_code(item.language, fallback="en-US"),
            reference_text=item.transcript,
            response=response,
            request_id=str(uuid.uuid4()),
        )
    finally:
        for path in temp_files:
            Path(path).unlink(missing_ok=True)


def _run_streaming_sim(
    backend,
    backend_name: str,
    item: DatasetItem,
    chunk_sec: float,
    collector: MetricsCollector,
) -> BenchmarkRecord:
    """Run streaming simulation benchmark for one sample."""
    source_wav = item.resolved_wav_path or item.wav_path
    chunks = wav_pcm_chunks(source_wav, chunk_sec)
    sample_rate, _, _, _ = wav_info(source_wav)
    response: AsrResponse = backend.streaming_recognize(
        chunks,
        language=normalize_language_code(item.language, fallback="en-US"),
        sample_rate=sample_rate,
    )
    return collector.record(
        backend=backend_name,
        scenario="streaming_sim",
        wav_path=item.wav_path,
        language=normalize_language_code(item.language, fallback="en-US"),
        reference_text=item.transcript,
        response=response,
        request_id=str(uuid.uuid4()),
    )


def _backend_supports_streaming(backend: object) -> bool:
    """Return True only when backend advertises real streaming support."""
    capabilities = getattr(backend, "capabilities", None)
    return bool(getattr(capabilities, "supports_streaming", False))


def run_benchmark(
    *,
    config_path: str,
    dataset_path: str,
    output_json: str,
    output_csv: str,
    backends: list[str] | None = None,
) -> list[BenchmarkRecord]:
    """Entry point for programmatic benchmark execution."""
    cfg = load_runtime_config(config_path, "configs/commercial.yaml")
    dataset = load_manifest_csv(dataset_path)
    if not dataset:
        raise ValueError(f"Dataset manifest is empty: {dataset_path}")

    selected_backends = [str(item).strip() for item in (backends or []) if str(item).strip()]
    if not selected_backends:
        selected_backends = [str(cfg.get("asr", {}).get("backend", "mock")).strip()]
    if not selected_backends or any(not backend for backend in selected_backends):
        raise ValueError("No backend selected for benchmark run")

    scenarios = _normalize_scenarios(cfg.get("benchmark", {}).get("scenarios", ["clean"]))
    chunk_sec = float(cfg.get("benchmark", {}).get("chunk_sec", 0.8))
    if chunk_sec <= 0:
        raise ValueError("benchmark.chunk_sec must be > 0")
    collector = MetricsCollector(pricing_per_minute=cfg.get("benchmark", {}).get("pricing", {}))

    records: list[BenchmarkRecord] = []

    for backend_name in selected_backends:
        backend_cfg = cfg.get("backends", {}).get(backend_name, {})
        try:
            backend = create_backend(backend_name, config=backend_cfg)
        except Exception as exc:
            raise ValueError(f"Unable to create backend '{backend_name}': {exc}") from exc
        backend_supports_streaming = _backend_supports_streaming(backend)
        for item in dataset:
            for scenario in scenarios:
                records.append(_run_single(backend, backend_name, item, scenario, collector))
            if backend_supports_streaming:
                records.append(_run_streaming_sim(backend, backend_name, item, chunk_sec, collector))

    save_benchmark_json(records, output_json)
    save_benchmark_csv(records, output_csv)
    generate_all_plots(records, str(Path(output_json).parent / "plots"))
    return records


def main() -> None:
    """CLI wrapper for benchmark runner module."""
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    parser = argparse.ArgumentParser(description="Run ASR benchmark scenarios")
    parser.add_argument("--config", required=True)
    parser.add_argument("--dataset", required=True)
    parser.add_argument("--output-json", required=True)
    parser.add_argument("--output-csv", required=True)
    parser.add_argument("--backends", default="")
    args = parser.parse_args()

    backends = [b.strip() for b in args.backends.split(",") if b.strip()] if args.backends else None
    records = run_benchmark(
        config_path=args.config,
        dataset_path=args.dataset,
        output_json=args.output_json,
        output_csv=args.output_csv,
        backends=backends,
    )
    success = sum(1 for r in records if r.success)
    LOG.info("Benchmark done: %s/%s successful", success, len(records))


if __name__ == "__main__":
    main()
