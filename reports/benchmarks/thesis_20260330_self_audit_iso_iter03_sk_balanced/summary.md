# Benchmark Summary: thesis_20260330_self_audit_iso_iter03_sk_balanced

- benchmark_profile: `benchmark/fleurs_sk_sk_test_subset_whisper`
- dataset_id: `fleurs_sk_sk_test_subset`
- providers: `providers/whisper_local`
- scenario: `clean_baseline`
- execution_mode: `batch`
- aggregate_scope: `single_provider`
- total_samples: `2`
- successful_samples: `2`
- failed_samples: `0`

## Per-Provider Summary

### providers/whisper_local (preset: `balanced`)
- samples: `2`
- successful_samples: `2`
- failed_samples: `0`
- quality_metrics: `{"cer": 0.20618556701030927, "confidence": 0.6505668741602589, "sample_accuracy": 0.0, "wer": 0.7142857142857143}`
- latency_metrics: `{"inference_ms": 700.8788059902145, "per_utterance_latency_ms": 871.9072834792314, "postprocess_ms": 0.09645598765928298, "preprocess_ms": 170.93202150135767, "real_time_factor": 0.20131864697214572, "total_latency_ms": 871.9072834792314}`
- reliability_metrics: `{"failure_rate": 0.0, "success_rate": 1.0}`
- cost_metrics: `{"estimated_cost_usd": 0.0}`
- cost_totals: `{"estimated_cost_usd": 0.0}`
- estimated_cost_total_usd: `0.0`

## Noise Summary
- clean: `{"cer": 0.20618556701030927, "confidence": 0.6505668741602589, "cpu_percent": 3.8, "estimated_cost_usd": 0.0, "failure_rate": 0.0, "gpu_memory_mb": 778.0, "gpu_util_percent": 35.5, "inference_ms": 700.8788059902145, "memory_mb": 442.783203125, "per_utterance_latency_ms": 871.9072834792314, "postprocess_ms": 0.09645598765928298, "preprocess_ms": 170.93202150135767, "real_time_factor": 0.20131864697214572, "sample_accuracy": 0.0, "success_rate": 1.0, "total_latency_ms": 871.9072834792314, "wer": 0.7142857142857143}`
