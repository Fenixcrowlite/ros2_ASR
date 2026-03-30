# Benchmark Summary: thesis_20260330_self_audit_final_iter01_light

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
- latency_metrics: `{"inference_ms": 619.3613930081483, "per_utterance_latency_ms": 3055.1247730036266, "postprocess_ms": 0.5050879844930023, "preprocess_ms": 2435.2582920109853, "real_time_factor": 0.36773288071781735, "total_latency_ms": 3055.1247730036266}`
- reliability_metrics: `{"failure_rate": 0.0, "success_rate": 1.0}`
- cost_metrics: `{"estimated_cost_usd": 0.0}`
- cost_totals: `{"estimated_cost_usd": 0.0}`
- estimated_cost_total_usd: `0.0`

## Noise Summary
- clean: `{"cer": 0.0, "confidence": 0.666260313307349, "cpu_percent": 6.3, "estimated_cost_usd": 0.0, "failure_rate": 0.0, "gpu_memory_mb": 815.0, "gpu_util_percent": 17.0, "inference_ms": 619.3613930081483, "memory_mb": 269.3828125, "per_utterance_latency_ms": 3055.1247730036266, "postprocess_ms": 0.5050879844930023, "preprocess_ms": 2435.2582920109853, "real_time_factor": 0.36773288071781735, "sample_accuracy": 1.0, "success_rate": 1.0, "total_latency_ms": 3055.1247730036266, "wer": 0.0}`
