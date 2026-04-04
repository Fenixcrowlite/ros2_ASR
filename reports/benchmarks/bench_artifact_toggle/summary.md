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
- aggregate_samples: `1`
- corrupted_samples: `0`

## Per-Provider Summary

### providers/fake_artifact_toggle
- samples: `1`
- successful_samples: `1`
- failed_samples: `0`
- quality_metrics: `{"confidence": 0.92, "wer": 0.0}`
- latency_metrics: `{"inference_ms": 0.0, "postprocess_ms": 0.0, "preprocess_ms": 0.0}`

## Noise Summary
- clean: `{"confidence": 0.92, "cpu_percent": 9.8, "gpu_memory_mb": 0.0, "gpu_util_percent": 0.0, "inference_ms": 0.0, "memory_mb": 167.3984375, "model_load_ms": 0.228748, "postprocess_ms": 0.0, "preprocess_ms": 0.0, "provider_call_cold_start": 1.0, "provider_call_warm_start": 0.0, "provider_init_cold_start": 1.0, "provider_init_warm_start": 0.0, "provider_invocation_index": 1.0, "wer": 0.0}`
