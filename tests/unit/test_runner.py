from pathlib import Path

from asr_benchmark.runner import run_benchmark


def test_run_benchmark_mock(tmp_path: Path) -> None:
    out_json = tmp_path / "bench.json"
    out_csv = tmp_path / "bench.csv"
    records = run_benchmark(
        config_path="configs/default.yaml",
        dataset_path="data/transcripts/sample_manifest.csv",
        output_json=str(out_json),
        output_csv=str(out_csv),
        backends=["mock"],
    )
    assert records
    assert out_json.exists()
    assert out_csv.exists()
    assert (tmp_path / "plots" / "wer_by_backend.png").exists()
