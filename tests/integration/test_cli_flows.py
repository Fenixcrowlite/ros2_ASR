from __future__ import annotations

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
    registry = json.loads((tmp_path / "datasets" / "registry" / "datasets.json").read_text(encoding="utf-8"))
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
