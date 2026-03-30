# Benchmark Summary: bench_artifact_toggle

- benchmark_profile: `bench`
- dataset_id: `bench_dataset`
- providers: `providers/fake_artifact_toggle`
- scenario: `clean_baseline`
- execution_mode: `batch`
- aggregate_scope: `single_provider`
- total_samples: `1`
- successful_samples: `1`
- failed_samples: `0`

## Per-Provider Summary

### providers/fake_artifact_toggle
- samples: `1`
- successful_samples: `1`
- failed_samples: `0`
- quality_metrics: `{"confidence": 0.92, "wer": 0.0}`
- latency_metrics: `{"inference_ms": 0.0, "postprocess_ms": 0.0, "preprocess_ms": 0.0}`

## Noise Summary
- clean: `{"confidence": 0.92, "cpu_percent": 3.8, "gpu_memory_mb": 778.0, "gpu_util_percent": 33.0, "inference_ms": 0.0, "memory_mb": 65.92578125, "postprocess_ms": 0.0, "preprocess_ms": 0.0, "wer": 0.0}`
