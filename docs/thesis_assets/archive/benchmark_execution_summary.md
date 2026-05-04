# ASR Benchmark Execution Summary

Date: 2026-04-27

This execution used the existing canonical benchmark pipeline as the source of truth:

- `artifacts/benchmark_runs/<run_id>/manifest/run_manifest.json`
- `artifacts/benchmark_runs/<run_id>/metrics/results.json`
- `artifacts/benchmark_runs/<run_id>/metrics/results.csv`
- `artifacts/benchmark_runs/<run_id>/reports/summary.json`

Derived thesis-ready artifacts were generated under `results/runs/<run_id>/`.

RTF in this thesis means end-to-end real-time factor unless explicitly stated
otherwise. `provider_compute_rtf` is a secondary provider/model speed metric,
and `real_time_factor` is retained only as a deprecated compatibility alias.

## Test Gate

Passed before benchmark execution:

- `python3 -m pytest -q tests/integration/test_cli_flows.py tests/unit/test_metric_summary.py tests/unit/test_metrics.py` - 22 passed
- `python3 -m ruff check scripts/collect_metrics.py scripts/generate_report.py tests/integration/test_cli_flows.py` - passed
- `make test-unit` - passed

Because the test gate passed and benchmark runs completed without failed samples, the successful scenario runs below can be used as final local baseline runs. Interpret them as a minimal local subset because each run used one sample.

## Executed Runs

| Scenario | Run ID | Backend | Model | Samples | WER | CER | SER | Final p95 ms | RTF mean | Throughput audio-sec/sec | Scenario score | Admissible | Flags |
|---|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---|---|
| embedded | `bench_20260427T141016Z_2555b592` | `providers/whisper_local:light` | `light` | 1 | 0 | 0 | 0 | 5255.89161 | 0.632630189 | 1.580702308 | 69.80604681 | yes |  |
| batch | `bench_20260427T141029Z_d6c1b1da` | `providers/whisper_local:light` | `light` | 1 | 0 | 0 | 0 | 2666.419796 | 0.3209460515 | 3.115788449 | 83.32660648 | yes |  |
| analytics | `bench_20260427T141037Z_b687b3bf` | `providers/whisper_local:light` | `light` | 1 | 0 | 0 | 0 | 2715.28795 | 0.3268281115 | 3.059712323 | 84.24896062 | yes |  |
| dialog | `bench_20260427T141048Z_d1922b62` | `providers/whisper_local:light` | `light` | 1 | 0 | 0 | 0 | 2702.697965 | 0.3253127064 | 3.073965389 | 66.26281435 | no | `dialog_final_latency_p95_gt_1500_ms` |

## Derived Artifact Layout

For each run above, the following files were generated:

- `results/runs/<run_id>/manifest.json`
- `results/runs/<run_id>/utterance_metrics.csv`
- `results/runs/<run_id>/summary.csv`
- `results/runs/<run_id>/summary.json`
- `results/runs/<run_id>/report.md`
- `results/runs/<run_id>/plots/pareto_wer_latency.png`
- `results/runs/<run_id>/plots/pareto_wer_energy.png`
- `results/runs/<run_id>/plots/latency_boxplot.png`
- `results/runs/<run_id>/plots/robustness_wer_by_snr.png`
- `results/runs/<run_id>/plots/accent_disparity.png`
- `results/runs/<run_id>/plots/calibration_reliability.png`
- `results/runs/<run_id>/plots/scenario_score.png`

`results/benchmark_results.json` and `results/benchmark_results.csv` were preserved as compatibility exports and updated by the existing benchmark entry point.

## Missing Or Limited Metrics

- Energy was not measured or supplied with `--energy-j`; `energy_j_per_audio_min` is empty and the energy Pareto plot is a placeholder.
- Accent metadata was not present; `accent_gap_pp` is empty and the accent disparity plot is a placeholder.
- No OOV vocabulary file was supplied; `oov_rate` is empty.
- Only clean sample rows were present; `noise_deg_pp` is empty and the robustness plot is a placeholder.
- Confidence was available and ECE/Brier were derived, but the sample count is one, so calibration is not statistically meaningful.
- GPU memory fields were populated by the runtime metrics, but this run used the local Whisper CPU preset; treat GPU metrics as environment telemetry, not GPU inference evidence.
- Each run used one utterance from `datasets/sample_dataset`, so WER/CER/SER and confidence intervals are smoke-baseline values, not a statistically powered benchmark.
