#!/usr/bin/env python3
"""Run reproducible self-audit benchmark iterations and runtime API probes."""

from __future__ import annotations

import argparse
import json
import sys
import threading
import time
from contextlib import contextmanager
from datetime import UTC, datetime
from pathlib import Path
from statistics import mean
from typing import Any


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
REPORTS_ROOT = PROJECT_ROOT / "reports"

from fastapi.testclient import TestClient  # noqa: E402

import rclpy  # noqa: E402
from asr_benchmark_core import BenchmarkOrchestrator, BenchmarkRunRequest  # noqa: E402
from asr_gateway.ros_client import GatewayRosClient  # noqa: E402
from asr_runtime_nodes.asr_orchestrator_node import AsrOrchestratorNode  # noqa: E402
from asr_runtime_nodes.audio_input_node import AudioInputNode  # noqa: E402
from asr_runtime_nodes.audio_preprocess_node import AudioPreprocessNode  # noqa: E402
from asr_runtime_nodes.vad_segmenter_node import VadSegmenterNode  # noqa: E402
from rclpy.executors import MultiThreadedExecutor  # noqa: E402

import asr_gateway.api as gateway_api  # noqa: E402


def _now_utc() -> str:
    return datetime.now(UTC).isoformat()


def _load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=True, indent=2) + "\n", encoding="utf-8")


def _write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text.rstrip() + "\n", encoding="utf-8")


def _mean_metric(results: list[dict[str, Any]], metric_name: str) -> float:
    values = [
        float((row.get("metrics", {}) or {}).get(metric_name, 0.0) or 0.0)
        for row in results
        if isinstance(row, dict)
    ]
    return float(mean(values)) if values else 0.0


def _group_by(rows: list[dict[str, Any]], key: str) -> dict[str, list[dict[str, Any]]]:
    grouped: dict[str, list[dict[str, Any]]] = {}
    for row in rows:
        group = str(row.get(key, "") or "")
        grouped.setdefault(group, []).append(row)
    return grouped


def _benchmark_record(summary: dict[str, Any], results: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "run_id": str(summary.get("run_id", "") or ""),
        "benchmark_profile": str(summary.get("benchmark_profile", "") or ""),
        "dataset_id": str(summary.get("dataset_id", "") or ""),
        "scenario": str(summary.get("scenario", "") or ""),
        "providers": list(summary.get("providers", []) or []),
        "total_samples": int(summary.get("total_samples", 0) or 0),
        "successful_samples": int(summary.get("successful_samples", 0) or 0),
        "failed_samples": int(summary.get("failed_samples", 0) or 0),
        "mean_metrics": dict(summary.get("mean_metrics", {}) or {}),
        "results_count": len(results),
        "results": results,
    }


def _run_benchmark(
    orchestrator: BenchmarkOrchestrator,
    *,
    run_id: str,
    benchmark_profile: str,
    dataset_profile: str,
    scenario: str,
    provider_overrides: dict[str, dict[str, Any]] | None = None,
    benchmark_settings: dict[str, Any] | None = None,
) -> dict[str, Any]:
    summary = orchestrator.run(
        BenchmarkRunRequest(
            benchmark_profile=benchmark_profile,
            dataset_profile=dataset_profile,
            providers=["providers/whisper_local"],
            scenario=scenario,
            provider_overrides=provider_overrides or {},
            benchmark_settings=benchmark_settings or {},
            run_id=run_id,
        )
    )
    run_report_dir = REPORTS_ROOT / "benchmarks" / run_id
    summary_payload = _load_json(run_report_dir / "summary.json")
    results_payload = _load_json(run_report_dir / "results.json")
    if not isinstance(summary_payload, dict):
        raise RuntimeError(f"Unexpected benchmark summary payload: {run_report_dir / 'summary.json'}")
    if not isinstance(results_payload, list):
        raise RuntimeError(f"Unexpected benchmark result payload: {run_report_dir / 'results.json'}")
    record = _benchmark_record(summary_payload, results_payload)
    record["orchestrator_summary"] = {
        "run_id": summary.run_id,
        "successful_samples": summary.successful_samples,
        "failed_samples": summary.failed_samples,
        "mean_metrics": dict(summary.mean_metrics),
        "metadata": dict(summary.metadata),
    }
    return record


def _preset_iteration_markdown(title: str, rows: list[dict[str, Any]]) -> str:
    lines = [
        f"# {title}",
        "",
        "| Preset | Samples | Success | Mean WER | Mean CER | Mean Latency ms | Mean RTF | Mean CPU % | Mean RAM MB |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    best_latency: tuple[str, float] | None = None
    best_wer: tuple[str, float] | None = None
    for row in rows:
        preset = str(
            (
                row.get("results", [{}])[0].get("provider_preset", "default")
                if row.get("results")
                else "default"
            )
        )
        metrics = dict(row.get("mean_metrics", {}) or {})
        latency = float(metrics.get("total_latency_ms", 0.0) or 0.0)
        wer = float(metrics.get("wer", 0.0) or 0.0)
        if best_latency is None or latency < best_latency[1]:
            best_latency = (preset, latency)
        if best_wer is None or wer < best_wer[1]:
            best_wer = (preset, wer)
        lines.append(
            "| "
            + " | ".join(
                [
                    preset,
                    str(row.get("total_samples", 0)),
                    str(row.get("successful_samples", 0)),
                    f"{wer:.4f}",
                    f"{float(metrics.get('cer', 0.0) or 0.0):.4f}",
                    f"{latency:.2f}",
                    f"{float(metrics.get('real_time_factor', 0.0) or 0.0):.4f}",
                    f"{_mean_metric(row.get('results', []), 'cpu_percent'):.2f}",
                    f"{_mean_metric(row.get('results', []), 'memory_mb'):.2f}",
                ]
            )
            + " |"
        )
    if best_latency is not None and best_wer is not None:
        lines.extend(
            [
                "",
                f"- Lowest latency preset: `{best_latency[0]}` at `{best_latency[1]:.2f}` ms",
                f"- Lowest WER preset: `{best_wer[0]}` at `{best_wer[1]:.4f}`",
            ]
        )
    return "\n".join(lines)


def _noise_iteration_markdown(title: str, rows: list[dict[str, Any]]) -> str:
    grouped = _group_by(rows, "noise_level")
    lines = [
        f"# {title}",
        "",
        "| Noise Level | Samples | Mean WER | Mean CER | Mean Latency ms | Mean RTF |",
        "|---|---:|---:|---:|---:|---:|",
    ]
    for noise_level in ["clean", "light", "medium", "heavy", "extreme"]:
        group_rows = grouped.get(noise_level, [])
        if not group_rows:
            continue
        lines.append(
            "| "
            + " | ".join(
                [
                    noise_level,
                    str(len(group_rows)),
                    f"{_mean_metric(group_rows, 'wer'):.4f}",
                    f"{_mean_metric(group_rows, 'cer'):.4f}",
                    f"{_mean_metric(group_rows, 'total_latency_ms'):.2f}",
                    f"{_mean_metric(group_rows, 'real_time_factor'):.4f}",
                ]
            )
            + " |"
        )
    return "\n".join(lines)


def _multilingual_iteration_markdown(title: str, rows: list[dict[str, Any]]) -> str:
    lines = [
        f"# {title}",
        "",
        "| Dataset | Language | Samples | Mean WER | Mean CER | Mean Latency ms | Mean RTF |",
        "|---|---|---:|---:|---:|---:|---:|",
    ]
    for row in rows:
        dataset = str(row.get("dataset_id", "") or "")
        first_result = row.get("results", [{}])[0] if row.get("results") else {}
        language = str(first_result.get("language", "") or "")
        metrics = dict(row.get("mean_metrics", {}) or {})
        lines.append(
            "| "
            + " | ".join(
                [
                    dataset,
                    language,
                    str(row.get("total_samples", 0)),
                    f"{float(metrics.get('wer', 0.0) or 0.0):.4f}",
                    f"{float(metrics.get('cer', 0.0) or 0.0):.4f}",
                    f"{float(metrics.get('total_latency_ms', 0.0) or 0.0):.2f}",
                    f"{float(metrics.get('real_time_factor', 0.0) or 0.0):.4f}",
                ]
            )
            + " |"
        )
    return "\n".join(lines)


@contextmanager
def _runtime_stack() -> Any:
    if not rclpy.ok():
        rclpy.init(args=None)

    executor = MultiThreadedExecutor(num_threads=8)
    nodes = [
        AudioInputNode(),
        AudioPreprocessNode(),
        VadSegmenterNode(),
        AsrOrchestratorNode(),
    ]
    for node in nodes:
        executor.add_node(node)

    spin_thread = threading.Thread(target=executor.spin, name="self-audit-runtime", daemon=True)
    spin_thread.start()
    time.sleep(1.0)

    try:
        try:
            gateway_api.ros.close()
        except Exception:
            pass
        gateway_api.ros = GatewayRosClient(timeout_sec=30.0)
        gateway_api._RUNTIME_RESULTS.clear()
        gateway_api._RUNTIME_EVENTS.clear()
        yield gateway_api
    finally:
        try:
            gateway_api.ros.close()
        except Exception:
            pass
        try:
            executor.shutdown(timeout_sec=1.0)
        except Exception:
            pass
        for node in nodes:
            try:
                node.destroy_node()
            except Exception:
                pass
        spin_thread.join(timeout=1.0)
        if rclpy.ok():
            rclpy.shutdown()


def _poll_live_result(
    client: TestClient,
    *,
    session_id: str,
    timeout_sec: float,
) -> tuple[dict[str, Any], dict[str, Any], float]:
    started = time.perf_counter()
    deadline = started + timeout_sec
    last_live: dict[str, Any] = {}
    while time.perf_counter() < deadline:
        response = client.get("/api/runtime/live")
        response.raise_for_status()
        last_live = response.json()
        for row in list(last_live.get("recent_results", []) or []):
            if str(row.get("session_id", "") or "") == session_id:
                return row, last_live, (time.perf_counter() - started) * 1000.0
        time.sleep(0.5)
    raise TimeoutError(f"Timed out waiting for runtime result for session `{session_id}`")


def _run_runtime_api_probe(suite_id: str) -> dict[str, Any]:
    payload: dict[str, Any] = {"suite_id": suite_id, "generated_at": _now_utc()}
    session_id = f"{suite_id}_runtime_session"

    with _runtime_stack():
        with TestClient(gateway_api.app) as client:
            noise_res = client.post(
                "/api/runtime/generate_noise",
                json={"source_wav": "data/sample/vosk_test.wav", "snr_levels": [30, 10]},
            )
            noise_res.raise_for_status()
            noise_payload = noise_res.json()

            recognize_res = client.post(
                "/api/runtime/recognize_once",
                json={
                    "wav_path": "data/sample/vosk_test.wav",
                    "language": "en-US",
                    "session_id": f"{suite_id}_recognize_once",
                    "provider_profile": "providers/whisper_local",
                    "provider_preset": "balanced",
                    "provider_settings": {},
                },
            )
            recognize_res.raise_for_status()
            recognize_payload = recognize_res.json()

            start_res = client.post(
                "/api/runtime/start",
                json={
                    "runtime_profile": "default_runtime",
                    "provider_profile": "providers/whisper_local",
                    "provider_preset": "light",
                    "provider_settings": {},
                    "session_id": session_id,
                    "audio_source": "file",
                    "processing_mode": "segmented",
                    "audio_file_path": "data/sample/vosk_test.wav",
                    "language": "en-US",
                    "mic_capture_sec": 4.0,
                },
            )
            start_res.raise_for_status()
            start_payload = start_res.json()

            final_result, live_snapshot, wall_time_ms = _poll_live_result(
                client,
                session_id=session_id,
                timeout_sec=45.0,
            )

            stop_res = client.post("/api/runtime/stop", json={"session_id": session_id})
            try:
                stop_payload = stop_res.json()
            except Exception:
                stop_payload = {"raw": stop_res.text}

    payload["noise_generation"] = noise_payload
    payload["recognize_once"] = recognize_payload
    payload["runtime_session"] = {
        "start": start_payload,
        "final_result": final_result,
        "live_snapshot": live_snapshot,
        "wall_time_to_result_ms": wall_time_ms,
        "stop": {
            "status_code": int(stop_res.status_code),
            "payload": stop_payload,
        },
    }
    payload["trace_refs"] = {
        "recognize_once": str(recognize_payload.get("raw_metadata_ref", "") or ""),
        "runtime_session": str(final_result.get("raw_metadata_ref", "") or ""),
    }
    recognize_trace = str(recognize_payload.get("raw_metadata_ref", "") or "")
    if recognize_trace and Path(recognize_trace).exists():
        payload["recognize_once_trace"] = _load_json(Path(recognize_trace))
    return payload


def _run_suite(suite_id: str) -> dict[str, Any]:
    orchestrator = BenchmarkOrchestrator(
        configs_root=str(PROJECT_ROOT / "configs"),
        artifact_root=str(PROJECT_ROOT / "artifacts"),
        registry_path=str(PROJECT_ROOT / "datasets" / "registry" / "datasets.json"),
    )

    preset_runs = [
        _run_benchmark(
            orchestrator,
            run_id=f"{suite_id}_iter01_light",
            benchmark_profile="benchmark/default_benchmark",
            dataset_profile="datasets/sample_dataset",
            scenario="clean_baseline",
            provider_overrides={"providers/whisper_local": {"preset_id": "light"}},
            benchmark_settings={"batch": {"max_samples": 1}},
        ),
        _run_benchmark(
            orchestrator,
            run_id=f"{suite_id}_iter01_balanced",
            benchmark_profile="benchmark/default_benchmark",
            dataset_profile="datasets/sample_dataset",
            scenario="clean_baseline",
            provider_overrides={"providers/whisper_local": {"preset_id": "balanced"}},
            benchmark_settings={"batch": {"max_samples": 1}},
        ),
        _run_benchmark(
            orchestrator,
            run_id=f"{suite_id}_iter01_accurate",
            benchmark_profile="benchmark/default_benchmark",
            dataset_profile="datasets/sample_dataset",
            scenario="clean_baseline",
            provider_overrides={"providers/whisper_local": {"preset_id": "accurate"}},
            benchmark_settings={"batch": {"max_samples": 1}},
        ),
    ]

    noise_run = _run_benchmark(
        orchestrator,
        run_id=f"{suite_id}_iter02_noise_balanced",
        benchmark_profile="benchmark/default_benchmark",
        dataset_profile="datasets/sample_dataset",
        scenario="noise_robustness",
        provider_overrides={"providers/whisper_local": {"preset_id": "balanced"}},
        benchmark_settings={
            "batch": {"max_samples": 1},
            "noise": {"mode": "white", "levels": ["clean", "light", "medium", "heavy"]},
        },
    )

    multilingual_runs = [
        _run_benchmark(
            orchestrator,
            run_id=f"{suite_id}_iter03_fr_balanced",
            benchmark_profile="benchmark/fleurs_fr_fr_test_subset_whisper",
            dataset_profile="datasets/fleurs_fr_fr_test_subset",
            scenario="clean_baseline",
            provider_overrides={"providers/whisper_local": {"preset_id": "balanced"}},
        ),
        _run_benchmark(
            orchestrator,
            run_id=f"{suite_id}_iter03_sk_balanced",
            benchmark_profile="benchmark/fleurs_sk_sk_test_subset_whisper",
            dataset_profile="datasets/fleurs_sk_sk_test_subset",
            scenario="clean_baseline",
            provider_overrides={"providers/whisper_local": {"preset_id": "balanced"}},
        ),
        _run_benchmark(
            orchestrator,
            run_id=f"{suite_id}_iter03_ja_balanced",
            benchmark_profile="benchmark/fleurs_ja_jp_test_subset_whisper",
            dataset_profile="datasets/fleurs_ja_jp_test_subset",
            scenario="clean_baseline",
            provider_overrides={"providers/whisper_local": {"preset_id": "balanced"}},
        ),
    ]

    api_probe = _run_runtime_api_probe(suite_id)

    return {
        "suite_id": suite_id,
        "generated_at": _now_utc(),
        "iterations": {
            "iteration_01_preset_comparison": preset_runs,
            "iteration_02_noise_robustness": noise_run,
            "iteration_03_multilingual_probe": multilingual_runs,
        },
        "runtime_api_probe": api_probe,
    }


def _write_suite_reports(payload: dict[str, Any]) -> None:
    suite_id = str(payload.get("suite_id", "") or "")
    improvements_root = REPORTS_ROOT / "improvements"
    audit_root = REPORTS_ROOT / "audit"

    _write_json(improvements_root / f"{suite_id}_suite.json", payload)

    preset_rows = list(payload.get("iterations", {}).get("iteration_01_preset_comparison", []) or [])
    noise_record = dict(payload.get("iterations", {}).get("iteration_02_noise_robustness", {}) or {})
    multilingual_rows = list(payload.get("iterations", {}).get("iteration_03_multilingual_probe", []) or [])

    _write_text(
        improvements_root / "iteration_01_preset_comparison.md",
        _preset_iteration_markdown("Iteration 01: Whisper Preset Comparison", preset_rows),
    )
    _write_text(
        improvements_root / "iteration_02_noise_robustness.md",
        _noise_iteration_markdown(
            "Iteration 02: Noise Robustness",
            list(noise_record.get("results", []) or []),
        ),
    )
    _write_text(
        improvements_root / "iteration_03_multilingual_probe.md",
        _multilingual_iteration_markdown(
            "Iteration 03: Multilingual Probe",
            multilingual_rows,
        ),
    )

    runtime_probe = dict(payload.get("runtime_api_probe", {}) or {})
    recognize_once = dict(runtime_probe.get("recognize_once", {}) or {})
    runtime_session = dict(runtime_probe.get("runtime_session", {}) or {})
    final_result = dict(runtime_session.get("final_result", {}) or {})
    audit_lines = [
        "# Runtime API Probe",
        "",
        f"- suite_id: `{suite_id}`",
        f"- generated_at: `{payload.get('generated_at', '')}`",
        f"- recognize_once latency_ms: `{float(recognize_once.get('latency_ms', 0.0) or 0.0):.2f}`",
        f"- recognize_once service_latency_ms: `{float(recognize_once.get('service_latency_ms', 0.0) or 0.0):.2f}`",
        f"- runtime session wall_time_to_result_ms: `{float(runtime_session.get('wall_time_to_result_ms', 0.0) or 0.0):.2f}`",
        f"- runtime session transcript: `{str(final_result.get('text', '') or '')}`",
        f"- recognize_once trace ref: `{str(recognize_once.get('raw_metadata_ref', '') or '')}`",
        f"- runtime session trace ref: `{str(final_result.get('raw_metadata_ref', '') or '')}`",
    ]
    _write_text(audit_root / "runtime_api_probe.md", "\n".join(audit_lines))
    _write_json(audit_root / "runtime_api_probe.json", runtime_probe)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run self-audit ASR benchmark suite")
    parser.add_argument(
        "--suite-id",
        default=f"thesis_{datetime.now(UTC).strftime('%Y%m%dT%H%M%SZ')}",
        help="Stable prefix used for benchmark run IDs and report files.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    payload = _run_suite(args.suite_id)
    _write_suite_reports(payload)
    print(json.dumps(payload, ensure_ascii=True, indent=2))


if __name__ == "__main__":
    main()
