# Benchmark Summary

Generated at: `2026-03-31T12:24:00+00:00`

## Canonical run used for the remediation close-out

- run_id: `audit_20260331_risk_closure_final`
- benchmark_profile: `benchmark/default_benchmark`
- dataset_profile: `datasets/sample_dataset`
- provider_profile: `providers/whisper_local`
- provider_preset: `light`
- scenario: `clean_baseline`
- execution_mode: `batch`
- total_samples: `1`
- successful_samples: `1`
- failed_samples: `0`

## Key results

- `WER = 0.0`
- `CER = 0.0`
- `sample_accuracy = 1.0`
- `total_latency_ms = 1974.159280071035`
- `preprocess_ms = 1322.2330459975637`
- `inference_ms = 651.823531021364`
- `postprocess_ms = 0.10270305210724473`
- `real_time_factor = 0.23762148291659063`
- `confidence = 0.6638665311297195`
- `cpu_percent = 27.2`
- `memory_mb = 240.87890625`
- `gpu_util_percent = 26.0`
- `gpu_memory_mb = 821.0`
- `model_load_ms = 3.129232`
- `provider_init_cold_start = true`
- `provider_call_cold_start = true`
- `provider_invocation_index = 1`
- `trace_corrupted = false`
- `aggregate_samples = 1`
- `corrupted_samples = 0`

## Important interpretation

This run is the first canonical benchmark artifact in this audit sequence that includes:

- split dependency / CI / security hardening already applied
- provider init/load timing exported into benchmark metrics
- cold/warm markers exported into result rows and trace index
- updated observability exporter schema with the new metrics columns

## Artifact references

- run manifest: [run_manifest.json](/home/fenix/Desktop/ros2ws/artifacts/benchmark_runs/audit_20260331_risk_closure_final/manifest/run_manifest.json)
- canonical summary JSON: [summary.json](/home/fenix/Desktop/ros2ws/artifacts/benchmark_runs/audit_20260331_risk_closure_final/reports/summary.json)
- canonical summary Markdown: [summary.md](/home/fenix/Desktop/ros2ws/artifacts/benchmark_runs/audit_20260331_risk_closure_final/reports/summary.md)
- canonical results JSON: [results.json](/home/fenix/Desktop/ros2ws/artifacts/benchmark_runs/audit_20260331_risk_closure_final/metrics/results.json)
- canonical results CSV: [results.csv](/home/fenix/Desktop/ros2ws/artifacts/benchmark_runs/audit_20260331_risk_closure_final/metrics/results.csv)
- per-sample trace JSON: [trace_50a7334b138648c9909cd094b3ae3c19.json](/home/fenix/Desktop/ros2ws/artifacts/benchmark_runs/audit_20260331_risk_closure_final/metrics/traces/trace_50a7334b138648c9909cd094b3ae3c19.json)
- trace index export: [audit_20260331_risk_closure_final_trace_index.csv](/home/fenix/Desktop/ros2ws/reports/benchmarks/metrics_exports/audit_20260331_risk_closure_final_trace_index.csv)
- compatibility copy: [audit_20260331_risk_closure_final](/home/fenix/Desktop/ros2ws/reports/benchmarks/audit_20260331_risk_closure_final)
