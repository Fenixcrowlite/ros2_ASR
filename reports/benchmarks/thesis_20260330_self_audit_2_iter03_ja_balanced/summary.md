# Benchmark Summary: thesis_20260330_self_audit_2_iter03_ja_balanced

- benchmark_profile: `benchmark/fleurs_ja_jp_test_subset_whisper`
- dataset_id: `fleurs_ja_jp_test_subset`
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
- quality_metrics: `{"cer": 0.08609271523178808, "confidence": 0.8506012982628055, "sample_accuracy": 0.0, "wer": 1.0}`
- latency_metrics: `{"inference_ms": 1188.1576154992217, "per_utterance_latency_ms": 1491.8287890031934, "postprocess_ms": 0.07737000123597682, "preprocess_ms": 303.5938035027357, "real_time_factor": 0.08627955378065054, "total_latency_ms": 1491.8287890031934}`
- reliability_metrics: `{"failure_rate": 0.0, "success_rate": 1.0}`
- cost_metrics: `{"estimated_cost_usd": 0.0}`
- cost_totals: `{"estimated_cost_usd": 0.0}`
- estimated_cost_total_usd: `0.0`

## Noise Summary
- clean: `{"cer": 0.08609271523178808, "confidence": 0.8506012982628055, "cpu_percent": 5.1, "estimated_cost_usd": 0.0, "failure_rate": 0.0, "gpu_memory_mb": 778.0, "gpu_util_percent": 31.0, "inference_ms": 1188.1576154992217, "memory_mb": 788.359375, "per_utterance_latency_ms": 1491.8287890031934, "postprocess_ms": 0.07737000123597682, "preprocess_ms": 303.5938035027357, "real_time_factor": 0.08627955378065054, "sample_accuracy": 0.0, "success_rate": 1.0, "total_latency_ms": 1491.8287890031934, "wer": 1.0}`
