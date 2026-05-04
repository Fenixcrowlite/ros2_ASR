# Current Task Report

Status: completed

## Archive Evidence Finalization 2026-05-04

Finalization fixed the archive reproducibility trace from canonical benchmark artifacts to schema-first metrics, final CSV tables, and `final_report.md`.

Canonical artifact directories verified with required `metrics/results.json`, `metrics/results.csv`, `reports/summary.json`, `reports/summary.md`, and `manifest/run_manifest.json` files:

- `artifacts/benchmark_runs/thesis_fast_20260503T225907Z/`
- `artifacts/benchmark_runs/thesis_balanced_20260503T232650Z/`
- `artifacts/benchmark_runs/thesis_accurate_20260503T225907Z/`
- `artifacts/benchmark_runs/thesis_cloud_20260503T223116Z/`
- `artifacts/benchmark_runs/thesis_local_20260503T222647Z/`

Changes made in this finalization:

- Added `scripts/validate_thesis_evidence.py`, writing `reports/thesis_test/thesis_evidence_validation.md` and `.json`.
- Updated `results/thesis_final/final_report.md` generation to remove stale none-valued local/cloud run-id lines, list tiered primary run ids, and mark local/cloud matrix runs as supporting evidence.
- Updated AWS credential reporting so successful AWS smoke/benchmark evidence reports `bucket=available` with `bucket_mode=aws_list_buckets` instead of `bucket=missing`.
- Updated `scripts/secret_scan.sh` for ZIP-extracted archives: scans text evidence roots only, excludes audio/image/model binaries and generated derived audio, skips `secrets/`, prints scanned file count, and exits 0 when clean.

Final required command outcomes:

- `python3 scripts/validate_dataset_assets.py --registry datasets/registry/datasets.json --root .` -> PASS, `passed=true`, `dataset_count=1`
- `python3 scripts/validate_thesis_evidence.py --root .` -> PASS, `passed=true`, `checks=155`
- `python3 -m compileall -q scripts ros2_ws/src tests` -> PASS
- `bash scripts/secret_scan.sh` -> PASS, `Scanned files: 825`, no findings
- `python3 scripts/export_thesis_tables.py --input results/runs --output results/thesis_final` -> PASS, `run_count=12`
- rerun `python3 scripts/validate_thesis_evidence.py --root .` -> PASS, `passed=true`, `checks=155`

Final table provider coverage remains:

- Final metric tables include `aws_cloud`, `azure_cloud`, `google_cloud`, `huggingface_local`, `vosk_local`, and `whisper_local`.
- `provider_smoke_tests.csv` and `provider_comparison.csv` include `huggingface_api`; it remains skipped because no Hugging Face API token was available.
- `huggingface_local:accurate` remains reported as a failed preset attempt due CUDA out-of-memory and is excluded from metric ranking rows.

## Scope

Prepared the full bachelor-thesis ASR benchmark evidence package and reworked the final comparison so model presets are compared by fair capability tiers instead of mixing light, balanced and accurate variants in one ranking.

## Dataset Validation

- Active registry: `datasets/registry/datasets.json`
- Active dataset: `librispeech_test_clean_subset`
- Sample count: 10
- Validation command: `python3 scripts/validate_dataset_assets.py --registry datasets/registry/datasets.json --root .`
- Result: PASS, `dataset_count=1`

Catalog-only datasets:

- Stored in `datasets/registry/datasets_catalog.json`
- Status: `manifest_only_audio_missing`
- `used_in_final_benchmark: false`

Reports:

- `reports/datasets/dataset_asset_validation.md`
- `reports/datasets/dataset_asset_validation.json`

## Credential Discovery And Smoke Tests

Credential discovery now checks env vars, `.env` files, `secrets/local/runtime.env`, `secrets/refs/*.yaml`, provider configs, Google service-account project id, and AWS S3 bucket availability through AWS SDK discovery.

Smoke command:

- `.venv/bin/python scripts/run_provider_smoke_tests.py --output results/thesis_final/provider_smoke_tests.csv --timeout-sec 300`

Smoke outcome:

- `whisper_local`: success
- `vosk_local`: success
- `huggingface_local`: success
- `azure_cloud`: credentials detected, auth probe success, smoke recognition success
- `google_cloud`: credentials detected, auth probe success, smoke recognition success
- `aws_cloud`: credentials detected, auth probe success, smoke recognition success
- `huggingface_api`: skipped only provider, `missing_credentials: token`

Reports:

- `reports/thesis_test/credential_availability.md`
- `reports/thesis_test/credential_availability.json`
- `results/thesis_final/provider_smoke_tests.csv`

## Benchmark Runs

Local benchmark:

- Run id: `thesis_local_20260503T222647Z`
- Providers: `whisper_local`, `vosk_local`, `huggingface_local`
- Canonical artifact: `artifacts/benchmark_runs/thesis_local_20260503T222647Z/`
- Rows: 150 total, 149 successful, 1 failed
- Schema exports:
  - `results/runs/thesis_local_20260503T222647Z_embedded/`
  - `results/runs/thesis_local_20260503T222647Z_batch/`
  - `results/runs/thesis_local_20260503T222647Z_analytics/`
  - `results/runs/thesis_local_20260503T222647Z_dialog/`

Cloud benchmark:

- Run id: `thesis_cloud_20260503T223116Z`
- Providers: `azure_cloud`, `google_cloud`, `aws_cloud`
- Canonical artifact: `artifacts/benchmark_runs/thesis_cloud_20260503T223116Z/`
- Rows: 150 total, 150 successful, 0 failed
- Schema exports:
  - `results/runs/thesis_cloud_20260503T223116Z_embedded/`
  - `results/runs/thesis_cloud_20260503T223116Z_batch/`
  - `results/runs/thesis_cloud_20260503T223116Z_analytics/`
  - `results/runs/thesis_cloud_20260503T223116Z_dialog/`

Tiered fair-comparison benchmark:

- Fast / low-resource tier: `thesis_fast_20260503T225907Z`
  - Providers/presets: `whisper_local:light`, `huggingface_local:light`, `google_cloud:light`, `vosk_local:en_small`
  - Canonical artifact: `artifacts/benchmark_runs/thesis_fast_20260503T225907Z/`
  - Rows: 200 total, 199 successful, 1 failed
- Balanced tier: `thesis_balanced_20260503T232650Z`
  - Providers/presets: `whisper_local:balanced`, `huggingface_local:balanced`, `google_cloud:balanced`, `azure_cloud:standard`, `aws_cloud:standard`
  - Canonical artifact: `artifacts/benchmark_runs/thesis_balanced_20260503T232650Z/`
  - Rows: 250 total, 250 successful, 0 failed
- Accurate / high-quality tier: `thesis_accurate_20260503T225907Z`
  - Valid metric providers/presets: `whisper_local:accurate`, `google_cloud:accurate`
  - Failed preset attempt: `huggingface_local:accurate`, 50/50 variants failed with sanitized `CUDA out of memory`; excluded from metric ranking tables and reported in `final_report.md`.
  - Canonical artifact: `artifacts/benchmark_runs/thesis_accurate_20260503T225907Z/`
  - Rows: 150 total, 100 successful, 50 failed

System-stability note:

- A duplicate tiered benchmark process was detected during rerun, causing heavy local HF inference load. After reboot, no benchmark processes remained.
- `scripts/run_tiered_thesis_benchmark.py` now uses a lock file at `.ai/thesis_tiered_benchmark.lock`, lowers process priority with `os.nice(8)`, and limits common BLAS/PyTorch/tokenizer thread environment defaults to reduce risk of freezing the workstation.
- No additional heavy HF accurate rerun was started after reboot; final export uses existing completed artifacts and treats the HF accurate failure as a failed HuggingFace preset attempt, which is allowed by the task constraints.

## Final Thesis Artifacts

Export command:

- `python3 scripts/export_thesis_tables.py --input results/runs --output results/thesis_final`

Generated files:

- `results/thesis_final/provider_comparison.csv`
- `results/thesis_final/provider_smoke_tests.csv`
- `results/thesis_final/quality_table.csv`
- `results/thesis_final/performance_table.csv`
- `results/thesis_final/resource_table.csv`
- `results/thesis_final/noise_robustness_table.csv`
- `results/thesis_final/cost_deployment_table.csv`
- `results/thesis_final/scenario_scores.csv`
- `results/thesis_final/final_report.md`
- `results/thesis_final/manifest.json`
- `results/thesis_final/plots/wer_by_provider.png`
- `results/thesis_final/plots/cer_by_provider.png`
- `results/thesis_final/plots/latency_p95_by_provider.png`
- `results/thesis_final/plots/rtf_by_provider.png`
- `results/thesis_final/plots/wer_vs_latency_pareto.png`
- `results/thesis_final/plots/noise_robustness_by_provider.png`
- `results/thesis_final/plots/cost_vs_quality.png`

Final table provider coverage:

- Local benchmarked: `whisper_local`, `vosk_local`, `huggingface_local`
- Cloud benchmarked: `azure_cloud`, `google_cloud`, `aws_cloud`
- Skipped: `huggingface_api` only, because no supported token was detected
- Tiered metric rows: 11 rows; `huggingface_local:accurate` is not included as a valid metric row because all variants failed.

## Commands Executed And Outcomes

- `python3 -m compileall -q scripts ros2_ws/src tests` -> PASS
- `python3 scripts/validate_dataset_assets.py --registry datasets/registry/datasets.json --root .` -> PASS
- `.venv/bin/python scripts/run_provider_smoke_tests.py --output results/thesis_final/provider_smoke_tests.csv --timeout-sec 300` -> PASS
- `.venv/bin/python scripts/run_thesis_benchmark_matrix.py --mode full` -> interrupted after local canonical artifact; local schema collection continued manually from `thesis_local_20260503T222647Z`
- `.venv/bin/python scripts/collect_metrics.py --input artifacts/benchmark_runs/thesis_local_20260503T222647Z --results-dir results --run-id thesis_local_20260503T222647Z_embedded --scenario embedded --normalization-profile normalized-v1` -> PASS
- `.venv/bin/python scripts/collect_metrics.py --input artifacts/benchmark_runs/thesis_local_20260503T222647Z --results-dir results --run-id thesis_local_20260503T222647Z_batch --scenario batch --normalization-profile normalized-v1` -> PASS
- `.venv/bin/python scripts/collect_metrics.py --input artifacts/benchmark_runs/thesis_local_20260503T222647Z --results-dir results --run-id thesis_local_20260503T222647Z_analytics --scenario analytics --normalization-profile normalized-v1` -> PASS
- `.venv/bin/python scripts/collect_metrics.py --input artifacts/benchmark_runs/thesis_local_20260503T222647Z --results-dir results --run-id thesis_local_20260503T222647Z_dialog --scenario dialog --normalization-profile normalized-v1` -> PASS
- `.venv/bin/python scripts/run_thesis_benchmark_matrix.py --mode cloud` -> PASS, cloud run `thesis_cloud_20260503T223116Z`
- `python3 scripts/export_thesis_tables.py --input results/runs --output results/thesis_final` -> PASS
- `python3 -m pytest -q tests/unit tests/contract tests/component` -> PASS
- `bash scripts/secret_scan.sh` -> PASS
- `.venv/bin/python scripts/run_tiered_thesis_benchmark.py --tiers fast,balanced,accurate` -> completed with tier artifacts; `huggingface_local:accurate` failed due GPU OOM.
- `.venv/bin/python scripts/run_tiered_thesis_benchmark.py --tiers balanced,accurate` -> interrupted by system reboot after duplicate process/resource saturation; retained completed `thesis_balanced_20260503T232650Z` artifact.
- `python3 -m compileall -q scripts/export_thesis_tables.py scripts/run_tiered_thesis_benchmark.py` -> PASS
- `python3 scripts/export_thesis_tables.py --input results/runs --output results/thesis_final` -> PASS after tiered export fix.
- `python3 - <<'PY' ... write_credential_reports(smoke_rows=...) ... PY` -> PASS, credential report updated from existing smoke CSV without new cloud calls.
- `python3 -m compileall -q scripts ros2_ws/src tests` -> PASS after final edits.
- `python3 -m pytest -q tests/unit tests/contract tests/component` -> PASS after final edits.
- `bash scripts/secret_scan.sh` -> PASS after final edits; now scans generated evidence paths as well as tracked files and works outside git through `find`.

## Implementation Fixes

- `scripts/credential_discovery.py`: added Google project id discovery from service-account JSON and AWS bucket discovery through AWS SDK without printing secret values.
- `ros2_ws/src/asr_provider_aws/asr_provider_aws/backend.py`: fixed AWS Transcribe result retrieval when an output S3 bucket/key is configured by reading the transcript JSON from S3 instead of treating the URI as public HTTP JSON.
- `scripts/export_thesis_tables.py`: final export selects latest local and latest cloud thesis runs together and reports provider credential/smoke/benchmark/failure status separately.
- `scripts/export_thesis_tables.py`: added `comparison_tier`-aware export, selects latest `fast`, `balanced`, and `accurate` thesis runs, excludes fully failed presets from metric ranking tables, and reports them under `Failed Preset Attempts`.
- `scripts/run_tiered_thesis_benchmark.py`: added resource guards and a nonblocking lock to avoid duplicate heavy runs.
- `scripts/credential_discovery.py`: smoke-success providers are now marked `config_complete=true` in credential availability reports.
- `scripts/secret_scan.sh`: works outside git via `find` and scans generated `reports/`, `results/`, `artifacts/`, `.ai/`, `scripts/`, `configs/`, and `datasets/` paths while excluding `secrets/`.
- `configs/benchmark/thesis_tier_fast.yaml`, `configs/benchmark/thesis_tier_balanced.yaml`, `configs/benchmark/thesis_tier_accurate.yaml`: added fair preset-tier benchmark profiles.
- `ros2_ws/src/asr_benchmark_core/asr_benchmark_core/orchestrator.py`: benchmark profile `provider_overrides` are now merged into provider execution resolution so tier profiles can select provider presets.

## Limitations

- `huggingface_api` remains skipped because no supported API token source was detected.
- Benchmark scale is thesis prototype scale: 10 clean LibriSpeech utterances with clean and SNR variants.
- Fast tier has one failed Vosk noisy utterance row; it remains represented in aggregate metrics and report limitations.
- `huggingface_local:accurate` is reported as a failed HuggingFace preset attempt due GPU memory pressure and is excluded from fair metric tables to avoid pretending an infrastructure failure is an ASR-quality result.
