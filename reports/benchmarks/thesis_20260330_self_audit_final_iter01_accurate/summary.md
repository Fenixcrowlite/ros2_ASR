# Benchmark Summary: thesis_20260330_self_audit_final_iter01_accurate

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

### providers/whisper_local (preset: `accurate`)
- samples: `1`
- successful_samples: `1`
- failed_samples: `0`
- quality_metrics: `{"cer": 0.06666666666666667, "confidence": 0.8086618960581042, "sample_accuracy": 0.0, "wer": 0.3333333333333333}`
- latency_metrics: `{"inference_ms": 2300.3903749922756, "per_utterance_latency_ms": 4382.002297992585, "postprocess_ms": 0.9722450049594045, "preprocess_ms": 2080.63967799535, "real_time_factor": 0.5274437046211585, "total_latency_ms": 4382.002297992585}`
- reliability_metrics: `{"failure_rate": 0.0, "success_rate": 1.0}`
- cost_metrics: `{"estimated_cost_usd": 0.0}`
- cost_totals: `{"estimated_cost_usd": 0.0}`
- estimated_cost_total_usd: `0.0`

## Noise Summary
- clean: `{"cer": 0.06666666666666667, "confidence": 0.8086618960581042, "cpu_percent": 6.0, "estimated_cost_usd": 0.0, "failure_rate": 0.0, "gpu_memory_mb": 827.0, "gpu_util_percent": 0.0, "inference_ms": 2300.3903749922756, "memory_mb": 748.8125, "per_utterance_latency_ms": 4382.002297992585, "postprocess_ms": 0.9722450049594045, "preprocess_ms": 2080.63967799535, "real_time_factor": 0.5274437046211585, "sample_accuracy": 0.0, "success_rate": 1.0, "total_latency_ms": 4382.002297992585, "wer": 0.3333333333333333}`
