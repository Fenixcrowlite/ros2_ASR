# Benchmark Summary: audit_20260331_canonical

- benchmark_profile: `benchmark/default_benchmark`
- dataset_id: `sample_dataset`
- providers: `providers/whisper_local`
- scenario: `clean_baseline`
- execution_mode: `batch`
- aggregate_scope: `single_provider`
- total_samples: `1`
- successful_samples: `0`
- failed_samples: `1`

## Per-Provider Summary

### providers/whisper_local (preset: `light`)
- samples: `1`
- successful_samples: `0`
- failed_samples: `1`
- quality_metrics: `{"cer": 1.0, "confidence": 0.0, "sample_accuracy": 0.0, "wer": 1.0}`
- latency_metrics: `{"inference_ms": 0.0, "per_utterance_latency_ms": 0.0, "postprocess_ms": 0.0, "preprocess_ms": 0.0, "real_time_factor": 0.0, "total_latency_ms": 0.0}`
- reliability_metrics: `{"failure_rate": 1.0, "success_rate": 0.0}`
- cost_metrics: `{"estimated_cost_usd": 0.0}`
- cost_totals: `{"estimated_cost_usd": 0.0}`
- estimated_cost_total_usd: `0.0`

## Noise Summary
- clean: `{"cer": 1.0, "confidence": 0.0, "cpu_percent": 3.7, "estimated_cost_usd": 0.0, "failure_rate": 1.0, "gpu_memory_mb": 816.0, "gpu_util_percent": 11.0, "inference_ms": 0.0, "memory_mb": 185.57421875, "per_utterance_latency_ms": 0.0, "postprocess_ms": 0.0, "preprocess_ms": 0.0, "real_time_factor": 0.0, "sample_accuracy": 0.0, "success_rate": 0.0, "total_latency_ms": 0.0, "wer": 1.0}`
