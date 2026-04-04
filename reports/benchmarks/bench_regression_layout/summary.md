# Benchmark Summary: bench_regression_layout

- benchmark_profile: `regression`
- dataset_id: `regression_dataset`
- providers: `providers/fake_regression`
- scenario: `clean_baseline`
- execution_mode: `batch`
- aggregate_scope: `single_provider`
- total_samples: `1`
- successful_samples: `1`
- failed_samples: `0`
- aggregate_samples: `1`
- corrupted_samples: `0`

## Per-Provider Summary

### providers/fake_regression
- samples: `1`
- successful_samples: `1`
- failed_samples: `0`
- quality_metrics: `{"cer": 0.0, "confidence": 0.92, "sample_accuracy": 1.0, "wer": 0.0}`
- latency_metrics: `{"inference_ms": 0.0, "postprocess_ms": 0.0, "preprocess_ms": 0.0}`

## Noise Summary
- clean: `{"cer": 0.0, "confidence": 0.92, "cpu_percent": 3.7, "gpu_memory_mb": 0.0, "gpu_util_percent": 0.0, "inference_ms": 0.0, "memory_mb": 167.3984375, "model_load_ms": 0.624188, "postprocess_ms": 0.0, "preprocess_ms": 0.0, "provider_call_cold_start": 1.0, "provider_call_warm_start": 0.0, "provider_init_cold_start": 1.0, "provider_init_warm_start": 0.0, "provider_invocation_index": 1.0, "sample_accuracy": 1.0, "wer": 0.0}`
