# Benchmark Summary: thesis_20260330_self_audit_iter03_fr_balanced

- benchmark_profile: `benchmark/fleurs_fr_fr_test_subset_whisper`
- dataset_id: `fleurs_fr_fr_test_subset`
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
- quality_metrics: `{"cer": 0.11320754716981132, "confidence": 0.7509011223476927, "sample_accuracy": 0.0, "wer": 0.25}`
- latency_metrics: `{"inference_ms": 807.410222987528, "per_utterance_latency_ms": 1134.1410329914652, "postprocess_ms": 0.12887699995189905, "preprocess_ms": 326.6019330039853, "real_time_factor": 0.14305367585418477, "total_latency_ms": 1134.1410329914652}`
- reliability_metrics: `{"failure_rate": 0.0, "success_rate": 1.0}`
- cost_metrics: `{"estimated_cost_usd": 0.0}`
- cost_totals: `{"estimated_cost_usd": 0.0}`
- estimated_cost_total_usd: `0.0`

## Noise Summary
- clean: `{"cer": 0.11320754716981132, "confidence": 0.7509011223476927, "cpu_percent": 5.6, "estimated_cost_usd": 0.0, "failure_rate": 0.0, "gpu_memory_mb": 778.0, "gpu_util_percent": 33.0, "inference_ms": 807.410222987528, "memory_mb": 731.041015625, "per_utterance_latency_ms": 1134.1410329914652, "postprocess_ms": 0.12887699995189905, "preprocess_ms": 326.6019330039853, "real_time_factor": 0.14305367585418477, "sample_accuracy": 0.0, "success_rate": 1.0, "total_latency_ms": 1134.1410329914652, "wer": 0.25}`
