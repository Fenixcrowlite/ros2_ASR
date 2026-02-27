from __future__ import annotations

import argparse
import tempfile
import uuid
from pathlib import Path

from asr_core.audio import wav_pcm_chunks
from asr_core.config import load_runtime_config
from asr_core.factory import create_backend
from asr_core.models import AsrRequest, AsrResponse
from asr_metrics.collector import MetricsCollector
from asr_metrics.io import save_benchmark_csv, save_benchmark_json
from asr_metrics.models import BenchmarkRecord
from asr_metrics.plotting import generate_all_plots

from asr_benchmark.dataset import DatasetItem, load_manifest_csv
from asr_benchmark.noise import add_white_noise_snr


def _scenario_wav(item: DatasetItem, scenario: str) -> tuple[str, list[str]]:
    temp_files: list[str] = []
    if scenario == "clean":
        return item.wav_path, temp_files
    if scenario.startswith("snr"):
        snr = float(scenario.replace("snr", ""))
        tmp = tempfile.NamedTemporaryFile(suffix=".wav", prefix=f"noise_{int(snr)}_", delete=False)
        tmp.close()
        add_white_noise_snr(item.wav_path, tmp.name, snr_db=snr)
        temp_files.append(tmp.name)
        return tmp.name, temp_files
    raise ValueError(f"Unsupported scenario: {scenario}")


def _run_single(
    backend,
    backend_name: str,
    item: DatasetItem,
    scenario: str,
    collector: MetricsCollector,
) -> BenchmarkRecord:
    wav_path, temp_files = _scenario_wav(item, scenario)
    try:
        response = backend.recognize_once(
            AsrRequest(wav_path=wav_path, language=item.language, enable_word_timestamps=True)
        )
        return collector.record(
            backend=backend_name,
            scenario=scenario,
            wav_path=item.wav_path,
            language=item.language,
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
    chunks = wav_pcm_chunks(item.wav_path, chunk_sec)
    sample_rate = 16000
    response: AsrResponse = backend.streaming_recognize(
        chunks,
        language=item.language,
        sample_rate=sample_rate,
    )
    return collector.record(
        backend=backend_name,
        scenario="streaming_sim",
        wav_path=item.wav_path,
        language=item.language,
        reference_text=item.transcript,
        response=response,
        request_id=str(uuid.uuid4()),
    )


def run_benchmark(
    *,
    config_path: str,
    dataset_path: str,
    output_json: str,
    output_csv: str,
    backends: list[str] | None = None,
) -> list[BenchmarkRecord]:
    cfg = load_runtime_config(config_path, "configs/commercial.yaml")
    dataset = load_manifest_csv(dataset_path)

    selected_backends = backends or [cfg.get("asr", {}).get("backend", "mock")]
    scenarios = list(cfg.get("benchmark", {}).get("scenarios", ["clean"]))
    chunk_sec = float(cfg.get("benchmark", {}).get("chunk_sec", 0.8))
    collector = MetricsCollector(pricing_per_minute=cfg.get("benchmark", {}).get("pricing", {}))

    records: list[BenchmarkRecord] = []

    for backend_name in selected_backends:
        backend_cfg = cfg.get("backends", {}).get(backend_name, {})
        backend = create_backend(backend_name, config=backend_cfg)
        for item in dataset:
            for scenario in scenarios:
                records.append(_run_single(backend, backend_name, item, scenario, collector))
            records.append(_run_streaming_sim(backend, backend_name, item, chunk_sec, collector))

    save_benchmark_json(records, output_json)
    save_benchmark_csv(records, output_csv)
    generate_all_plots(records, str(Path(output_json).parent / "plots"))
    return records


def main() -> None:
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
    print(f"Benchmark done: {success}/{len(records)} successful")


if __name__ == "__main__":
    main()
