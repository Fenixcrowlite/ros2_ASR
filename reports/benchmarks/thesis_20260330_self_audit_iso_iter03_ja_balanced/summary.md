# Benchmark Summary: thesis_20260330_self_audit_iso_iter03_ja_balanced

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
- latency_metrics: `{"inference_ms": 1177.9043129936326, "per_utterance_latency_ms": 1350.0232320075156, "postprocess_ms": 0.07667399768251926, "preprocess_ms": 172.04224501620047, "real_time_factor": 0.08030987597979733, "total_latency_ms": 1350.0232320075156}`
- reliability_metrics: `{"failure_rate": 0.0, "success_rate": 1.0}`
- cost_metrics: `{"estimated_cost_usd": 0.0}`
- cost_totals: `{"estimated_cost_usd": 0.0}`
- estimated_cost_total_usd: `0.0`

## Noise Summary
- clean: `{"cer": 0.08609271523178808, "confidence": 0.8506012982628055, "cpu_percent": 4.35, "estimated_cost_usd": 0.0, "failure_rate": 0.0, "gpu_memory_mb": 778.0, "gpu_util_percent": 33.5, "inference_ms": 1177.9043129936326, "memory_mb": 466.1640625, "per_utterance_latency_ms": 1350.0232320075156, "postprocess_ms": 0.07667399768251926, "preprocess_ms": 172.04224501620047, "real_time_factor": 0.08030987597979733, "sample_accuracy": 0.0, "success_rate": 1.0, "total_latency_ms": 1350.0232320075156, "wer": 1.0}`
