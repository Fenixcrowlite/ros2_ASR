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
