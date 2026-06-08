# Benchmarking

Benchmark execution is split between:

- `asr_benchmark_core`: provider execution, scenarios, metrics, and artifacts.
- `asr_benchmark_nodes`: ROS action/service interface for benchmark runs.
- `asr_metrics`: quality, timing, resource, and summary calculations.
- `asr_reporting`: report/export helpers.

## Run the Default Suite

```bash
make bench-suite
make report
```

The default benchmark profile is `configs/benchmark/default_benchmark.yaml`.
It uses the sample dataset profile and the local Whisper provider profile.

## Benchmark Profile

A benchmark profile defines:

- dataset profile
- providers to compare
- scenarios
- metric profiles
- execution mode
- batch and streaming settings
- noise settings

Example provider list:

```yaml
providers:
  - providers/whisper_local
  - providers/vosk_local
```

## Scenario and Normalization

The suite target accepts:

```bash
make bench-suite SCENARIO=embedded NORMALIZATION_PROFILE=normalized-v1
```

These values are passed into the benchmark export flow and become part of the
result context.

## Hugging Face Matrix

```bash
make bench-hf
```

This uses `configs/benchmark/huggingface_provider_matrix.yaml`.

## Outputs

Benchmark artifacts are written under ignored artifact and result directories.
Use:

```bash
make collect-metrics
make report
```

Reports are derived from run artifacts and should be regenerated rather than
edited manually.

## Release Check

The release helper runs tests, benchmark checks, artifact checks, and secret
scan steps:

```bash
bash scripts/release_check.sh
bash scripts/secret_scan.sh
```
