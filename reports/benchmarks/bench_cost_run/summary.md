# Benchmark Summary: bench_cost_run

- benchmark_profile: `bench`
- dataset_id: `bench_dataset`
- providers: `providers/fake_cost`
- scenario: `clean_baseline`
- execution_mode: `batch`
- aggregate_scope: `single_provider`
- total_samples: `1`
- successful_samples: `1`
- failed_samples: `0`
- aggregate_samples: `1`
- corrupted_samples: `0`

## Per-Provider Summary

### providers/fake_cost (preset: `standard`)
- samples: `1`
- successful_samples: `1`
- failed_samples: `0`
- quality_metrics: `{"confidence": 0.92, "wer": 0.0}`
- latency_metrics: `{"inference_ms": 0.0, "postprocess_ms": 0.0, "preprocess_ms": 0.0, "total_latency_ms": 15.0}`
- cost_metrics: `{"estimated_cost_usd": 0.25}`
- cost_totals: `{"estimated_cost_usd": 0.25}`
- estimated_cost_total_usd: `0.25`

## Noise Summary
- clean: `{"confidence": 0.92, "cpu_percent": 8.7, "estimated_cost_usd": 0.25, "gpu_memory_mb": 810.0, "gpu_util_percent": 2.0, "inference_ms": 0.0, "memory_mb": 175.671875, "model_load_ms": 0.012353, "postprocess_ms": 0.0, "preprocess_ms": 0.0, "provider_call_cold_start": 1.0, "provider_call_warm_start": 0.0, "provider_init_cold_start": 1.0, "provider_init_warm_start": 0.0, "provider_invocation_index": 1.0, "total_latency_ms": 15.0, "wer": 0.0}`
