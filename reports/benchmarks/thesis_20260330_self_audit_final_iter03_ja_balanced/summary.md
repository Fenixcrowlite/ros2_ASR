# Benchmark Summary: thesis_20260330_self_audit_final_iter03_ja_balanced

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
- latency_metrics: `{"inference_ms": 1120.353160004015, "per_utterance_latency_ms": 1477.2429154982092, "postprocess_ms": 0.07944399840198457, "preprocess_ms": 356.8103114957921, "real_time_factor": 0.08456887381756042, "total_latency_ms": 1477.2429154982092}`
- reliability_metrics: `{"failure_rate": 0.0, "success_rate": 1.0}`
- cost_metrics: `{"estimated_cost_usd": 0.0}`
- cost_totals: `{"estimated_cost_usd": 0.0}`
- estimated_cost_total_usd: `0.0`

## Noise Summary
- clean: `{"cer": 0.08609271523178808, "confidence": 0.8506012982628055, "cpu_percent": 4.949999999999999, "estimated_cost_usd": 0.0, "failure_rate": 0.0, "gpu_memory_mb": 939.0, "gpu_util_percent": 13.0, "inference_ms": 1120.353160004015, "memory_mb": 418.953125, "per_utterance_latency_ms": 1477.2429154982092, "postprocess_ms": 0.07944399840198457, "preprocess_ms": 356.8103114957921, "real_time_factor": 0.08456887381756042, "sample_accuracy": 0.0, "success_rate": 1.0, "total_latency_ms": 1477.2429154982092, "wer": 1.0}`
