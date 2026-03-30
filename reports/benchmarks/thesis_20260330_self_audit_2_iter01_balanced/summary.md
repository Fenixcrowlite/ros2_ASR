# Benchmark Summary: thesis_20260330_self_audit_2_iter01_balanced

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

### providers/whisper_local (preset: `balanced`)
- samples: `1`
- successful_samples: `1`
- failed_samples: `0`
- quality_metrics: `{"cer": 0.0, "confidence": 0.8086438129491665, "sample_accuracy": 1.0, "wer": 0.0}`
- latency_metrics: `{"inference_ms": 777.9535659938119, "per_utterance_latency_ms": 1518.92625799519, "postprocess_ms": 0.09274401236325502, "preprocess_ms": 740.8799479890149, "real_time_factor": 0.18282694487183318, "total_latency_ms": 1518.92625799519}`
- reliability_metrics: `{"failure_rate": 0.0, "success_rate": 1.0}`
- cost_metrics: `{"estimated_cost_usd": 0.0}`
- cost_totals: `{"estimated_cost_usd": 0.0}`
- estimated_cost_total_usd: `0.0`

## Noise Summary
- clean: `{"cer": 0.0, "confidence": 0.8086438129491665, "cpu_percent": 5.0, "estimated_cost_usd": 0.0, "failure_rate": 0.0, "gpu_memory_mb": 776.0, "gpu_util_percent": 30.0, "inference_ms": 777.9535659938119, "memory_mb": 383.14453125, "per_utterance_latency_ms": 1518.92625799519, "postprocess_ms": 0.09274401236325502, "preprocess_ms": 740.8799479890149, "real_time_factor": 0.18282694487183318, "sample_accuracy": 1.0, "success_rate": 1.0, "total_latency_ms": 1518.92625799519, "wer": 0.0}`
