# Concept Alignment Refactor

## Canonical Entities

- runtime profile
- provider profile
- provider preset
- normalized ASR result
- benchmark run request
- benchmark run manifest
- benchmark result row
- benchmark summary
- artifact reference

## Canonical Flows

- `audio/request -> provider resolution -> normalized result`
- `dataset/profile/metrics -> provider matrix -> per-sample metrics -> corpus summary -> artifacts -> operator summary pointer`

## Demo / Compatibility Entities That Should Not Define The Platform

- `asr_ros`
- `asr_benchmark.runner`
- `configs/default.yaml`
- flat `results/benchmark_results.*` outputs

## Refactor Direction

Make the repository conceptually cleaner by treating compatibility flows as adapters around the platform, not as equal first-class architectures.
The current operator bridge already reflects that direction: `make bench` creates canonical benchmark artifacts first and only then emits compatibility exports.
