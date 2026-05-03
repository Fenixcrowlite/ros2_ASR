# Reproducibility Manifest

Created: 2026-05-03

## Repository

- Branch: `main`
- Commit SHA: `73403779554fdf1966f7b2feeaf024b81f535468`

## Environment

- OS: Ubuntu 24.04, Linux `6.17.0-22-generic`
- Python: `3.12.3`
- ROS distro: not exported in the shell during this run
- CPU: AMD Ryzen 7 7435HS, 16 logical CPUs
- RAM: 15 GiB
- GPU: NVIDIA GeForce RTX 4060 Laptop GPU, 8188 MiB, driver 590.48.01

## Provider Configs Used

- `configs/providers/whisper_local.yaml`
- `configs/providers/vosk_local.yaml`
- `configs/providers/huggingface_local.yaml`

Cloud provider configs were validated but not benchmarked because credential
availability was incomplete in this environment.

## Dataset Manifests Used

- `datasets/registry/datasets.json`
- `datasets/manifests/librispeech_test_clean_subset.jsonl`

The executed local thesis run used 2 clean LibriSpeech utterances expanded into
clean + SNR 20/10/5/0 white-noise variants.

## Commands Executed

```bash
python3 scripts/validate_dataset_assets.py --registry datasets/registry/datasets.json --root .
python3 scripts/validate_configs/validate_profile.py --type runtime --id default_runtime
python3 scripts/validate_configs/validate_profile.py --type benchmark --id thesis_local_matrix
python3 scripts/validate_configs/validate_profile.py --type benchmark --id thesis_cloud_matrix
python3 scripts/validate_configs/validate_profile.py --type benchmark --id thesis_full_matrix
.venv/bin/python scripts/run_thesis_benchmark_matrix.py --mode local
python3 scripts/export_thesis_tables.py --input results/runs --output results/thesis_final
python3 scripts/generate_report.py --input results/thesis_final/manifest.json --output results/thesis_final/final_report.md
python3 -m compileall -q scripts ros2_ws/src tests
.venv/bin/python -m pytest -q tests/unit tests/contract tests/component
.venv/bin/python -m pytest -q tests/integration/test_cli_flows.py
make validate-datasets
bash scripts/secret_scan.sh
```

## Artifact Paths

- Canonical run: `artifacts/benchmark_runs/thesis_local_20260503T181036Z/`
- Schema runs:
  - `results/runs/thesis_local_20260503T181036Z_embedded/`
  - `results/runs/thesis_local_20260503T181036Z_batch/`
  - `results/runs/thesis_local_20260503T181036Z_analytics/`
  - `results/runs/thesis_local_20260503T181036Z_dialog/`
- Final thesis outputs: `results/thesis_final/`
- Dataset validation report: `reports/datasets/dataset_asset_validation.md`
- Credential availability report: `reports/thesis_test/credential_availability.md`
