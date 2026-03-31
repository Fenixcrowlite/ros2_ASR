# Benchmark Summary: audit_20260331_risk_closure

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
- quality_metrics: `{"cer": 0.0, "confidence": 0.6638665311297195, "sample_accuracy": 1.0, "wer": 0.0}`
- latency_metrics: `{"inference_ms": 715.5420180060901, "per_utterance_latency_ms": 2098.0922669987194, "postprocess_ms": 0.11441600508987904, "preprocess_ms": 1382.4358329875395, "real_time_factor": 0.2525387899613288, "total_latency_ms": 2098.0922669987194}`
- reliability_metrics: `{"failure_rate": 0.0, "success_rate": 1.0}`
- cost_metrics: `{"estimated_cost_usd": 0.0}`
- cost_totals: `{"estimated_cost_usd": 0.0}`
- estimated_cost_total_usd: `0.0`

## Noise Summary
- clean: `{"cer": 0.0, "confidence": 0.6638665311297195, "cpu_percent": 21.2, "estimated_cost_usd": 0.0, "failure_rate": 0.0, "gpu_memory_mb": 854.0, "gpu_util_percent": 35.0, "inference_ms": 715.5420180060901, "memory_mb": 242.87890625, "model_load_ms": 0.891901, "per_utterance_latency_ms": 2098.0922669987194, "postprocess_ms": 0.11441600508987904, "preprocess_ms": 1382.4358329875395, "provider_call_cold_start": 1.0, "provider_call_warm_start": 0.0, "provider_init_cold_start": 1.0, "provider_init_warm_start": 0.0, "provider_invocation_index": 1.0, "real_time_factor": 0.2525387899613288, "sample_accuracy": 1.0, "success_rate": 1.0, "total_latency_ms": 2098.0922669987194, "wer": 0.0}`
