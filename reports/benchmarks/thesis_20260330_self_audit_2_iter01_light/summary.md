# Benchmark Summary: thesis_20260330_self_audit_2_iter01_light

- benchmark_profile: `benchmark/default_benchmark`
- dataset_id: `sample_dataset`
- providers: `providers/whisper_local`
- scenario: `clean_baseline`
- execution_mode: `batch`
- aggregate_scope: `single_provider`
- total_samples: `1`
- successful_samples: `1`
- failed_samples: `0`

## Per-Provider Summary

### providers/whisper_local (preset: `light`)
- samples: `1`
- successful_samples: `1`
- failed_samples: `0`
- quality_metrics: `{"cer": 0.0, "confidence": 0.666260313307349, "sample_accuracy": 1.0, "wer": 0.0}`
- latency_metrics: `{"inference_ms": 469.5271929958835, "per_utterance_latency_ms": 1282.8750750049949, "postprocess_ms": 0.10316300904378295, "preprocess_ms": 813.2447190000676, "real_time_factor": 0.154414428864347, "total_latency_ms": 1282.8750750049949}`
- reliability_metrics: `{"failure_rate": 0.0, "success_rate": 1.0}`
- cost_metrics: `{"estimated_cost_usd": 0.0}`
- cost_totals: `{"estimated_cost_usd": 0.0}`
- estimated_cost_total_usd: `0.0`

## Noise Summary
- clean: `{"cer": 0.0, "confidence": 0.666260313307349, "cpu_percent": 8.5, "estimated_cost_usd": 0.0, "failure_rate": 0.0, "gpu_memory_mb": 776.0, "gpu_util_percent": 31.0, "inference_ms": 469.5271929958835, "memory_mb": 278.45703125, "per_utterance_latency_ms": 1282.8750750049949, "postprocess_ms": 0.10316300904378295, "preprocess_ms": 813.2447190000676, "real_time_factor": 0.154414428864347, "sample_accuracy": 1.0, "success_rate": 1.0, "total_latency_ms": 1282.8750750049949, "wer": 0.0}`
