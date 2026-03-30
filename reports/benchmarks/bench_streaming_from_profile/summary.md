# Benchmark Summary: bench_streaming_from_profile

- benchmark_profile: `bench`
- dataset_id: `bench_dataset`
- providers: `providers/fake_stream`
- scenario: `clean_baseline`
- execution_mode: `streaming`
- aggregate_scope: `single_provider`
- total_samples: `1`
- successful_samples: `1`
- failed_samples: `0`

## Per-Provider Summary

### providers/fake_stream
- samples: `1`
- successful_samples: `1`
- failed_samples: `0`
- quality_metrics: `{"confidence": 0.92, "wer": 0.3333333333333333}`
- latency_metrics: `{"inference_ms": 0.0, "postprocess_ms": 0.0, "preprocess_ms": 0.0}`
- streaming_metrics: `{"first_partial_latency_ms": 5.0, "partial_count": 34.0}`

## Noise Summary
- clean: `{"confidence": 0.92, "cpu_percent": 4.9, "first_partial_latency_ms": 5.0, "gpu_memory_mb": 778.0, "gpu_util_percent": 33.0, "inference_ms": 0.0, "memory_mb": 65.8984375, "partial_count": 34.0, "postprocess_ms": 0.0, "preprocess_ms": 0.0, "wer": 0.3333333333333333}`
