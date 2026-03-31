# Benchmark Summary: audit_20260331_canonical_ok

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
- latency_metrics: `{"inference_ms": 602.6282350067049, "per_utterance_latency_ms": 1322.456777037587, "postprocess_ms": 0.11509601608850062, "preprocess_ms": 719.7134460147936, "real_time_factor": 0.15917871654280055, "total_latency_ms": 1322.456777037587}`
- reliability_metrics: `{"failure_rate": 0.0, "success_rate": 1.0}`
- cost_metrics: `{"estimated_cost_usd": 0.0}`
- cost_totals: `{"estimated_cost_usd": 0.0}`
- estimated_cost_total_usd: `0.0`

## Noise Summary
- clean: `{"cer": 0.0, "confidence": 0.6638665311297195, "cpu_percent": 2.5, "estimated_cost_usd": 0.0, "failure_rate": 0.0, "gpu_memory_mb": 826.0, "gpu_util_percent": 20.0, "inference_ms": 602.6282350067049, "memory_mb": 242.88671875, "per_utterance_latency_ms": 1322.456777037587, "postprocess_ms": 0.11509601608850062, "preprocess_ms": 719.7134460147936, "real_time_factor": 0.15917871654280055, "sample_accuracy": 1.0, "success_rate": 1.0, "total_latency_ms": 1322.456777037587, "wer": 0.0}`
