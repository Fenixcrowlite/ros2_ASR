# ROS2 ASR Benchmarking and Integration Prototype

Bachelor thesis prototype for integrating and evaluating automatic speech
recognition systems in ROS2 robotic applications.

## Bachelor Thesis Scope

This repository supports a bachelor thesis focused on analysis, integration and
experimental evaluation of commercial and non-commercial ASR solutions for
ROS2-based robotic applications.

The project targets:

- Ubuntu 24.04
- ROS2 Jazzy
- COCOHRIP-like robotic laboratory usage
- local and cloud ASR provider comparison
- reproducible benchmark and evaluation artifacts

It is not presented as a generic production ASR cloud platform. The intended
outcome is a reproducible ROS2 ASR integration prototype with benchmark evidence
for selected ASR providers.

## Canonical Stack

- runtime: `asr_launch` + `asr_runtime_nodes`
- providers: `asr_provider_base` + `asr_provider_*`
- benchmark: `asr_benchmark_core` + `asr_benchmark_nodes`
- operator surface: `asr_gateway` + `web_ui`
- shared layers: `asr_core`, `asr_config`, `asr_datasets`, `asr_metrics`, `asr_storage`, `asr_reporting`, `asr_interfaces`

Archived compatibility packages, flat configs, and historical docs now live under `legacy/`.

## Main Commands

```bash
make setup
make build
make test-unit
make test-ros
make test-colcon
make bench
make report
make up
make up-runtime
```

For thesis release packaging, use:

```bash
make dist-thesis
```

## Thesis Evidence Package

The final thesis evidence package is located in:

- `results/thesis_final/final_report.md`
- `results/thesis_final/*.csv`
- `results/thesis_final/plots/*.png`
- `reports/datasets/dataset_asset_validation.md`
- `reports/thesis_test/thesis_evidence_validation.md`
- `reports/thesis_test/credential_availability.md`
- `artifacts/benchmark_runs/thesis_*`

To verify the packaged evidence without rerunning cloud benchmarks:

```bash
python3 scripts/validate_dataset_assets.py --registry datasets/registry/datasets.json --root .
python3 scripts/validate_thesis_evidence.py --root .
python3 -m compileall -q scripts ros2_ws/src tests
bash scripts/secret_scan.sh
```

## Final Benchmark Scope

The final benchmark uses one active validated dataset:

- `librispeech_test_clean_subset`
- 10 clean utterances
- derived SNR variants for robustness evaluation

The benchmark is thesis-scale and should not be interpreted as a large-scale ASR benchmark.

Metric groups and their interpretation are documented in `docs/metric_families.md`.

## Docs

- `docs/architecture.md`
- `docs/architecture/provider_model.md`
- `docs/run_guide.md`
- `docs/benchmarking.md`
- `docs/metric_families.md`
- `docs/interfaces.md`
- `docs/newbie_guide.md`
