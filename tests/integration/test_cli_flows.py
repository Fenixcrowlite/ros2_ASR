from __future__ import annotations

import csv
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path


def _pythonpath(repo_root: Path) -> str:
    src_root = repo_root / "ros2_ws" / "src"
    parts = [str(repo_root)] + [str(path) for path in src_root.iterdir() if path.is_dir()]
    return os.pathsep.join(parts)


def test_validate_profile_cli(repo_root: Path, tmp_path: Path) -> None:
    env = os.environ.copy()
    env["PYTHONPATH"] = _pythonpath(repo_root)
    shutil.copytree(repo_root / "configs", tmp_path / "configs")

    result = subprocess.run(
        [
            sys.executable,
            str(repo_root / "scripts" / "validate_configs" / "validate_profile.py"),
            "--type",
            "runtime",
            "--id",
            "default_runtime",
        ],
        cwd=tmp_path,
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0
    assert "VALID" in result.stdout
    assert "snapshot:" in result.stdout


def test_import_dataset_cli(repo_root: Path, tmp_path: Path, sample_wav: str) -> None:
    env = os.environ.copy()
    env["PYTHONPATH"] = _pythonpath(repo_root)
    source = tmp_path / "input_audio"
    source.mkdir(parents=True, exist_ok=True)
    shutil.copy2(sample_wav, source / "sample.wav")

    result = subprocess.run(
        [
            sys.executable,
            str(repo_root / "scripts" / "import_dataset" / "import_from_folder.py"),
            "--source",
            str(source),
            "--dataset-id",
            "cli_dataset",
        ],
        cwd=tmp_path,
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0
    assert "Imported dataset 'cli_dataset': 1 samples" in result.stdout
    registry = json.loads(
        (tmp_path / "datasets" / "registry" / "datasets.json").read_text(encoding="utf-8")
    )
    assert registry["datasets"][0]["dataset_id"] == "cli_dataset"


def test_import_dataset_cli_rejects_missing_source(repo_root: Path, tmp_path: Path) -> None:
    env = os.environ.copy()
    env["PYTHONPATH"] = _pythonpath(repo_root)

    result = subprocess.run(
        [
            sys.executable,
            str(repo_root / "scripts" / "import_dataset" / "import_from_folder.py"),
            "--source",
            str(tmp_path / "missing_audio"),
            "--dataset-id",
            "cli_dataset",
        ],
        cwd=tmp_path,
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode != 0
    assert "Source folder not found:" in result.stderr


def test_export_summary_cli(repo_root: Path, tmp_path: Path) -> None:
    env = os.environ.copy()
    env["PYTHONPATH"] = _pythonpath(repo_root)
    summary_json = tmp_path / "summary.json"
    summary_json.write_text(
        json.dumps({"run_id": "bench_cli", "wer": 0.0, "cer": 0.0}, ensure_ascii=True),
        encoding="utf-8",
    )
    output_md = tmp_path / "summary.md"

    result = subprocess.run(
        [
            sys.executable,
            str(repo_root / "scripts" / "export_reports" / "export_run_summary.py"),
            "--summary-json",
            str(summary_json),
            "--output-md",
            str(output_md),
        ],
        cwd=tmp_path,
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0
    assert output_md.exists()
    assert "# Benchmark bench_cli" in output_md.read_text(encoding="utf-8")


def test_export_summary_cli_rejects_missing_input(repo_root: Path, tmp_path: Path) -> None:
    env = os.environ.copy()
    env["PYTHONPATH"] = _pythonpath(repo_root)
    output_md = tmp_path / "summary.md"

    result = subprocess.run(
        [
            sys.executable,
            str(repo_root / "scripts" / "export_reports" / "export_run_summary.py"),
            "--summary-json",
            str(tmp_path / "missing-summary.json"),
            "--output-md",
            str(output_md),
        ],
        cwd=tmp_path,
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode != 0
    assert "Summary JSON not found:" in result.stderr


def test_generate_report_cli_bootstraps_repo_imports(repo_root: Path, tmp_path: Path) -> None:
    input_json = tmp_path / "benchmark_results.json"
    input_json.write_text(
        json.dumps(
            [
                {
                    "request_id": "req_cli",
                    "wav_path": "data/sample/vosk_test.wav",
                    "audio_id": "vosk_test",
                    "backend": "whisper",
                    "scenario": "clean_baseline",
                    "snr_db": None,
                    "language": "en-US",
                    "duration_sec": 1.0,
                    "text": "hello world",
                    "transcript_ref": "hello world",
                    "wer": 0.0,
                    "cer": 0.0,
                    "latency_ms": 12.0,
                    "preprocess_ms": 1.0,
                    "inference_ms": 10.0,
                    "postprocess_ms": 1.0,
                    "rtf": 0.2,
                    "cpu_percent": 0.0,
                    "ram_mb": 0.0,
                    "gpu_util_percent": 0.0,
                    "gpu_mem_mb": 0.0,
                    "success": True,
                    "error_code": "",
                    "error_message": "",
                    "cost_estimate": 0.0,
                    "audio_duration_sec": 1.0,
                    "transcript_hyp": "hello world",
                }
            ],
            ensure_ascii=True,
        ),
        encoding="utf-8",
    )
    output_md = tmp_path / "report.md"

    result = subprocess.run(
        [
            sys.executable,
            str(repo_root / "scripts" / "generate_report.py"),
            "--input",
            str(input_json),
            "--output",
            str(output_md),
        ],
        cwd=tmp_path,
        env={k: v for k, v in os.environ.items() if k != "PYTHONPATH"},
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0
    assert output_md.exists()
    assert "# ASR Benchmark Report" in output_md.read_text(encoding="utf-8")


def test_collect_metrics_cli_reads_canonical_artifacts(repo_root: Path, tmp_path: Path) -> None:
    run_id = "bench_schema_cli"
    summary_json = tmp_path / "latest_benchmark_summary.json"
    results_json = tmp_path / "canonical_results.json"
    summary_json.write_text(
        json.dumps(
            {
                "run_id": run_id,
                "benchmark_profile": "benchmark/fixture",
                "dataset_id": "fixture_dataset",
                "providers": ["providers/fake_a", "providers/fake_b"],
                "provider_summaries": [],
            },
            ensure_ascii=True,
        ),
        encoding="utf-8",
    )
    results_json.write_text(
        json.dumps(
            [
                {
                    "run_id": run_id,
                    "provider_profile": "providers/fake_a",
                    "provider_id": "fake",
                    "provider_preset": "small",
                    "sample_id": "clean_a",
                    "success": True,
                    "text": "hello world",
                    "reference_text": "hello world",
                    "metrics": {
                        "time_to_first_result_ms": 120.0,
                        "time_to_final_result_ms": 240.0,
                        "end_to_end_rtf": 0.30,
                        "audio_duration_sec": 1.0,
                        "cpu_percent_mean": 20.0,
                        "memory_mb_peak": 300.0,
                        "confidence": 0.9,
                    },
                    "noise_level": "clean",
                    "noise_mode": "none",
                    "execution_mode": "batch",
                    "normalized_result": {"language": "en-US", "confidence_available": True},
                },
                {
                    "run_id": run_id,
                    "provider_profile": "providers/fake_a",
                    "provider_id": "fake",
                    "provider_preset": "small",
                    "sample_id": "noisy_a",
                    "success": True,
                    "text": "hello noise",
                    "reference_text": "hello world",
                    "metrics": {
                        "time_to_first_result_ms": 140.0,
                        "time_to_final_result_ms": 260.0,
                        "end_to_end_rtf": 0.35,
                        "audio_duration_sec": 1.0,
                        "cpu_percent_mean": 22.0,
                        "memory_mb_peak": 320.0,
                        "confidence": 0.6,
                    },
                    "noise_level": "snr_10",
                    "noise_mode": "synthetic",
                    "noise_snr_db": 10,
                    "execution_mode": "batch",
                    "normalized_result": {"language": "en-US", "confidence_available": True},
                },
                {
                    "run_id": run_id,
                    "provider_profile": "providers/fake_b",
                    "provider_id": "fake",
                    "provider_preset": "large",
                    "sample_id": "clean_b",
                    "success": True,
                    "text": "hello brave world",
                    "reference_text": "hello world",
                    "metrics": {
                        "time_to_first_result_ms": 220.0,
                        "time_to_final_result_ms": 520.0,
                        "end_to_end_rtf": 0.55,
                        "audio_duration_sec": 1.0,
                        "cpu_percent_mean": 40.0,
                        "memory_mb_peak": 900.0,
                        "confidence": 0.7,
                    },
                    "noise_level": "clean",
                    "noise_mode": "none",
                    "execution_mode": "batch",
                    "normalized_result": {"language": "en-US", "confidence_available": True},
                },
            ],
            ensure_ascii=True,
        ),
        encoding="utf-8",
    )
    results_dir = tmp_path / "results"

    result = subprocess.run(
        [
            sys.executable,
            str(repo_root / "scripts" / "collect_metrics.py"),
            "--input",
            str(summary_json),
            "--results-json",
            str(results_json),
            "--results-dir",
            str(results_dir),
            "--scenario",
            "dialog",
        ],
        cwd=tmp_path,
        env={k: v for k, v in os.environ.items() if k != "PYTHONPATH"},
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)
    run_dir = Path(payload["run_dir"])
    assert (run_dir / "manifest.json").exists()
    assert (run_dir / "utterance_metrics.csv").exists()
    assert (run_dir / "summary.csv").exists()
    assert (run_dir / "summary.json").exists()
    assert (run_dir / "plots" / "pareto_wer_latency.png").exists()
    rows = list(csv.DictReader((run_dir / "summary.csv").open(encoding="utf-8")))
    assert {row["backend"] for row in rows} == {"providers/fake_a:small", "providers/fake_b:large"}
    assert rows[0]["scenario_score"]

    report_md = tmp_path / "schema_report.md"
    report_result = subprocess.run(
        [
            sys.executable,
            str(repo_root / "scripts" / "generate_report.py"),
            "--input",
            str(run_dir / "summary.json"),
            "--output",
            str(report_md),
        ],
        cwd=tmp_path,
        env={k: v for k, v in os.environ.items() if k != "PYTHONPATH"},
        capture_output=True,
        text=True,
        check=False,
    )
    assert report_result.returncode == 0, report_result.stderr
    assert "# ASR Thesis Benchmark Report" in report_md.read_text(encoding="utf-8")


def test_collect_metrics_cli_reads_legacy_results(repo_root: Path, tmp_path: Path) -> None:
    legacy_json = tmp_path / "benchmark_results.json"
    legacy_json.write_text(
        json.dumps(
            [
                {
                    "request_id": "req_legacy",
                    "wav_path": "data/sample/vosk_test.wav",
                    "audio_id": "sample_legacy",
                    "backend": "mock",
                    "scenario": "clean_baseline",
                    "snr_db": None,
                    "language": "en-US",
                    "duration_sec": 1.0,
                    "text": "hello world",
                    "transcript_ref": "hello world",
                    "transcript_hyp": "hello world",
                    "wer": 0.0,
                    "cer": 0.0,
                    "latency_ms": 100.0,
                    "preprocess_ms": 1.0,
                    "inference_ms": 98.0,
                    "postprocess_ms": 1.0,
                    "rtf": 0.1,
                    "cpu_percent": 10.0,
                    "ram_mb": 120.0,
                    "gpu_util_percent": 0.0,
                    "gpu_mem_mb": 0.0,
                    "success": True,
                    "error_code": "",
                    "error_message": "",
                    "cost_estimate": 0.0,
                    "audio_duration_sec": 1.0,
                }
            ],
            ensure_ascii=True,
        ),
        encoding="utf-8",
    )

    result = subprocess.run(
        [
            sys.executable,
            str(repo_root / "scripts" / "collect_metrics.py"),
            "--input",
            str(legacy_json),
            "--results-dir",
            str(tmp_path / "results"),
            "--run-id",
            "legacy_schema_cli",
            "--scenario",
            "embedded",
            "--no-plots",
        ],
        cwd=tmp_path,
        env={k: v for k, v in os.environ.items() if k != "PYTHONPATH"},
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    run_dir = tmp_path / "results" / "runs" / "legacy_schema_cli"
    utterances = list(csv.DictReader((run_dir / "utterance_metrics.csv").open(encoding="utf-8")))
    assert utterances[0]["source_schema"] == "legacy"
    assert (run_dir / "summary.json").exists()


def test_generate_report_cli_uses_corpus_wer_and_input_plot_directory(
    repo_root: Path, tmp_path: Path
) -> None:
    input_json = tmp_path / "benchmark_results.json"
    plots_dir = tmp_path / "plots"
    plots_dir.mkdir(parents=True, exist_ok=True)
    (plots_dir / "wer_cer_by_backend.png").write_text("fake", encoding="utf-8")
    input_json.write_text(
        json.dumps(
            [
                {
                    "request_id": "req_1",
                    "wav_path": "data/sample/vosk_test.wav",
                    "audio_id": "sample_a",
                    "backend": "whisper",
                    "scenario": "clean_baseline",
                    "snr_db": None,
                    "language": "en-US",
                    "duration_sec": 1.0,
                    "text": "beta",
                    "transcript_ref": "alpha",
                    "wer": 1.0,
                    "cer": 0.8,
                    "latency_ms": 10.0,
                    "preprocess_ms": 1.0,
                    "inference_ms": 8.0,
                    "postprocess_ms": 1.0,
                    "rtf": 0.5,
                    "cpu_percent": 0.0,
                    "ram_mb": 0.0,
                    "gpu_util_percent": 0.0,
                    "gpu_mem_mb": 0.0,
                    "success": True,
                    "error_code": "",
                    "error_message": "",
                    "cost_estimate": 0.1,
                    "audio_duration_sec": 1.0,
                    "transcript_hyp": "beta",
                },
                {
                    "request_id": "req_2",
                    "wav_path": "data/sample/vosk_test.wav",
                    "audio_id": "sample_b",
                    "backend": "whisper",
                    "scenario": "clean_baseline",
                    "snr_db": None,
                    "language": "en-US",
                    "duration_sec": 1.0,
                    "text": "one two three",
                    "transcript_ref": "one two three",
                    "wer": 0.0,
                    "cer": 0.0,
                    "latency_ms": 30.0,
                    "preprocess_ms": 1.0,
                    "inference_ms": 28.0,
                    "postprocess_ms": 1.0,
                    "rtf": 1.5,
                    "cpu_percent": 0.0,
                    "ram_mb": 0.0,
                    "gpu_util_percent": 0.0,
                    "gpu_mem_mb": 0.0,
                    "success": True,
                    "error_code": "",
                    "error_message": "",
                    "cost_estimate": 0.2,
                    "audio_duration_sec": 1.0,
                    "transcript_hyp": "one two three",
                },
            ],
            ensure_ascii=True,
        ),
        encoding="utf-8",
    )
    output_md = tmp_path / "report.md"

    result = subprocess.run(
        [
            sys.executable,
            str(repo_root / "scripts" / "generate_report.py"),
            "--input",
            str(input_json),
            "--output",
            str(output_md),
        ],
        cwd=tmp_path,
        env={k: v for k, v in os.environ.items() if k != "PYTHONPATH"},
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0
    report_text = output_md.read_text(encoding="utf-8")
    assert "| whisper | 0.250 | 0.250 | 20.0 | 1.000 | 0.000 | 0.3000 |" in report_text
    assert str(plots_dir / "wer_cer_by_backend.png") in report_text
    assert "Exact Match Rate" not in report_text


def test_generate_report_cli_rejects_missing_input(repo_root: Path, tmp_path: Path) -> None:
    output_md = tmp_path / "report.md"

    result = subprocess.run(
        [
            sys.executable,
            str(repo_root / "scripts" / "generate_report.py"),
            "--input",
            str(tmp_path / "missing-results.json"),
            "--output",
            str(output_md),
        ],
        cwd=tmp_path,
        env={k: v for k, v in os.environ.items() if k != "PYTHONPATH"},
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode != 0
    assert "Benchmark JSON not found:" in result.stderr


def test_generate_report_cli_accepts_canonical_summary_json(
    repo_root: Path, tmp_path: Path
) -> None:
    input_json = tmp_path / "summary.json"
    input_json.write_text(
        json.dumps(
            {
                "run_id": "bench_cli_summary",
                "benchmark_profile": "default_benchmark",
                "dataset_id": "sample_dataset",
                "providers": ["providers/fake_cli"],
                "scenario": "clean_baseline",
                "execution_mode": "batch",
                "aggregate_scope": "single_provider",
                "total_samples": 1,
                "successful_samples": 1,
                "failed_samples": 0,
                "provider_summaries": [
                    {
                        "provider_key": "providers/fake_cli",
                        "provider_profile": "providers/fake_cli",
                        "provider_id": "fake_cli",
                        "provider_preset": "",
                        "quality_metrics": {
                            "wer": 0.0,
                            "cer": 0.0,
                            "sample_accuracy": 1.0,
                        },
                        "latency_metrics": {
                            "total_latency_ms": 12.0,
                            "real_time_factor": 0.2,
                        },
                        "reliability_metrics": {
                            "success_rate": 1.0,
                        },
                        "cost_totals": {
                            "estimated_cost_usd": 0.0,
                        },
                        "metric_statistics": {
                            "estimated_cost_usd": {
                                "sum": 0.0,
                            }
                        },
                    }
                ],
                "noise_summary": {
                    "clean": {
                        "mean_metrics": {
                            "wer": 0.0,
                            "cer": 0.0,
                            "total_latency_ms": 12.0,
                            "real_time_factor": 0.2,
                        }
                    }
                },
            },
            ensure_ascii=True,
        ),
        encoding="utf-8",
    )
    output_md = tmp_path / "report.md"

    result = subprocess.run(
        [
            sys.executable,
            str(repo_root / "scripts" / "generate_report.py"),
            "--input",
            str(input_json),
            "--output",
            str(output_md),
        ],
        cwd=tmp_path,
        env={k: v for k, v in os.environ.items() if k != "PYTHONPATH"},
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0
    report_text = output_md.read_text(encoding="utf-8")
    assert "Run ID: bench_cli_summary" in report_text
    assert "Exact Match Rate" in report_text
    assert (
        "| providers/fake_cli | 0.000 | 0.000 | 1.000 | 12.0 | 0.200 | 1.000 | 0.0000 |"
        in report_text
    )


def test_run_benchmark_core_cli_exports_canonical_and_compatibility_artifacts(
    repo_root: Path, tmp_path: Path, sample_wav: str
) -> None:
    env = os.environ.copy()
    env["PYTHONPATH"] = _pythonpath(repo_root)

    configs = tmp_path / "configs"
    datasets_root = tmp_path / "datasets"
    artifacts = tmp_path / "artifacts"
    results = tmp_path / "results"
    registry = datasets_root / "registry" / "datasets.json"
    manifest = datasets_root / "manifests" / "cli_dataset.jsonl"
    imported_audio = datasets_root / "imported" / "cli_sample.wav"

    imported_audio.parent.mkdir(parents=True, exist_ok=True)
    manifest.parent.mkdir(parents=True, exist_ok=True)
    registry.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(sample_wav, imported_audio)
    manifest.write_text(
        json.dumps(
            {
                "sample_id": "cli_sample_001",
                "audio_path": str(imported_audio),
                "transcript": "hello world",
                "language": "en-US",
                "split": "test",
            },
            ensure_ascii=True,
        )
        + "\n",
        encoding="utf-8",
    )
    registry.write_text('{"datasets": []}\n', encoding="utf-8")

    (configs / "providers").mkdir(parents=True, exist_ok=True)
    (configs / "datasets").mkdir(parents=True, exist_ok=True)
    (configs / "benchmark").mkdir(parents=True, exist_ok=True)
    (configs / "metrics").mkdir(parents=True, exist_ok=True)

    (configs / "providers" / "fake_cli.yaml").write_text(
        "\n".join(
            [
                "profile_id: providers/fake_cli",
                "provider_id: fake",
                "adapter: tests.utils.fakes.FakeProviderAdapter",
                "settings: {}",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    (configs / "datasets" / "cli_dataset.yaml").write_text(
        "\n".join(
            [
                "dataset_id: cli_dataset",
                f"manifest_path: {manifest}",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    (configs / "metrics" / "quality.yaml").write_text(
        "metrics:\n  - wer\n  - cer\n  - sample_accuracy\n",
        encoding="utf-8",
    )
    (configs / "metrics" / "timing.yaml").write_text(
        "metrics:\n  - total_latency_ms\n  - real_time_factor\n  - success_rate\n",
        encoding="utf-8",
    )
    (configs / "benchmark" / "cli_benchmark.yaml").write_text(
        "\n".join(
            [
                "dataset_profile: datasets/cli_dataset",
                "providers:",
                "  - providers/fake_cli",
                "metric_profiles:",
                "  - metrics/quality",
                "  - metrics/timing",
                "execution_mode: batch",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    result = subprocess.run(
        [
            sys.executable,
            str(repo_root / "scripts" / "run_benchmark_core.py"),
            "--benchmark-profile",
            "cli_benchmark",
            "--configs-root",
            str(configs),
            "--artifact-root",
            str(artifacts),
            "--registry-path",
            str(registry),
            "--results-dir",
            str(results),
            "--run-id",
            "bench_cli_run",
        ],
        cwd=tmp_path,
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)
    assert payload["run_id"] == "bench_cli_run"
    assert (artifacts / "benchmark_runs" / "bench_cli_run" / "reports" / "summary.json").exists()
    assert (artifacts / "benchmark_runs" / "bench_cli_run" / "metrics" / "results.json").exists()
    assert (results / "latest_benchmark_summary.json").exists()
    assert (results / "latest_benchmark_run.json").exists()
    assert (results / "benchmark_results.json").exists()
    assert (results / "benchmark_results.csv").exists()
    assert (results / "plots" / "wer_cer_by_backend.png").exists()
    compat_payload = json.loads((results / "benchmark_results.json").read_text(encoding="utf-8"))
    assert compat_payload[0]["backend"] == "providers/fake_cli"


def test_generate_plots_cli_creates_output(repo_root: Path, tmp_path: Path) -> None:
    env = {k: v for k, v in os.environ.items() if k != "PYTHONPATH"}
    input_json = tmp_path / "benchmark_results.json"
    input_json.write_text(
        json.dumps(
            [
                {
                    "request_id": "req_cli",
                    "wav_path": "data/sample/vosk_test.wav",
                    "audio_id": "vosk_test",
                    "backend": "whisper",
                    "scenario": "clean_baseline",
                    "snr_db": None,
                    "language": "en-US",
                    "duration_sec": 1.0,
                    "text": "hello world",
                    "transcript_ref": "hello world",
                    "wer": 0.0,
                    "cer": 0.0,
                    "latency_ms": 12.0,
                    "preprocess_ms": 1.0,
                    "inference_ms": 10.0,
                    "postprocess_ms": 1.0,
                    "rtf": 0.2,
                    "cpu_percent": 0.0,
                    "ram_mb": 0.0,
                    "gpu_util_percent": 0.0,
                    "gpu_mem_mb": 0.0,
                    "success": True,
                    "error_code": "",
                    "error_message": "",
                    "cost_estimate": 0.0,
                    "audio_duration_sec": 1.0,
                    "transcript_hyp": "hello world",
                }
            ],
            ensure_ascii=True,
        ),
        encoding="utf-8",
    )
    output_dir = tmp_path / "plots"

    result = subprocess.run(
        [
            sys.executable,
            str(repo_root / "scripts" / "generate_plots.py"),
            "--input-json",
            str(input_json),
            "--output-dir",
            str(output_dir),
        ],
        cwd=tmp_path,
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0
    assert (output_dir / "wer_cer_by_backend.png").exists()


def test_generate_plots_cli_rejects_missing_input(repo_root: Path, tmp_path: Path) -> None:
    output_dir = tmp_path / "plots"

    result = subprocess.run(
        [
            sys.executable,
            str(repo_root / "scripts" / "generate_plots.py"),
            "--input-json",
            str(tmp_path / "missing-results.json"),
            "--output-dir",
            str(output_dir),
        ],
        cwd=tmp_path,
        env={k: v for k, v in os.environ.items() if k != "PYTHONPATH"},
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode != 0
    assert "Benchmark JSON not found:" in result.stderr
