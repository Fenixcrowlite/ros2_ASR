# Benchmark Summary: bench_multi_provider_run

- benchmark_profile: `bench`
- dataset_id: `bench_dataset`
- providers: `providers/provider_a, providers/provider_b`
- scenario: `clean_baseline`
- execution_mode: `batch`
- aggregate_scope: `provider_only`
- total_samples: `2`
- successful_samples: `2`
- failed_samples: `0`
- aggregate_samples: `2`
- corrupted_samples: `0`

## Per-Provider Summary

### providers/provider_a
- samples: `1`
- successful_samples: `1`
- failed_samples: `0`
- quality_metrics: `{"cer": 0.0, "confidence": 0.92, "sample_accuracy": 1.0, "wer": 0.0}`
- latency_metrics: `{"inference_ms": 0.0, "postprocess_ms": 0.0, "preprocess_ms": 0.0}`

### providers/provider_b
- samples: `1`
- successful_samples: `1`
- failed_samples: `0`
- quality_metrics: `{"cer": 0.0, "confidence": 0.92, "sample_accuracy": 1.0, "wer": 0.0}`
- latency_metrics: `{"inference_ms": 0.0, "postprocess_ms": 0.0, "preprocess_ms": 0.0}`

## Noise Summary
- clean: `{"cer": 0.0, "confidence": 0.92, "cpu_percent": 3.7, "gpu_memory_mb": 0.0, "gpu_util_percent": 0.0, "inference_ms": 0.0, "memory_mb": 153.6796875, "model_load_ms": 0.992246, "postprocess_ms": 0.0, "preprocess_ms": 0.0, "provider_call_cold_start": 1.0, "provider_call_warm_start": 0.0, "provider_init_cold_start": 1.0, "provider_init_warm_start": 0.0, "provider_invocation_index": 1.0, "sample_accuracy": 1.0, "wer": 0.0}`
