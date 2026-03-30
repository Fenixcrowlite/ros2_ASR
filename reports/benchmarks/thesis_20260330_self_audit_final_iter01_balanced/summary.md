# Benchmark Summary: thesis_20260330_self_audit_final_iter01_balanced

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
- latency_metrics: `{"inference_ms": 787.7259140077513, "per_utterance_latency_ms": 1701.7247110197786, "postprocess_ms": 0.08333701407536864, "preprocess_ms": 913.915459997952, "real_time_factor": 0.20482964745062335, "total_latency_ms": 1701.7247110197786}`
- reliability_metrics: `{"failure_rate": 0.0, "success_rate": 1.0}`
- cost_metrics: `{"estimated_cost_usd": 0.0}`
- cost_totals: `{"estimated_cost_usd": 0.0}`
- estimated_cost_total_usd: `0.0`

## Noise Summary
- clean: `{"cer": 0.0, "confidence": 0.8086438129491665, "cpu_percent": 7.5, "estimated_cost_usd": 0.0, "failure_rate": 0.0, "gpu_memory_mb": 851.0, "gpu_util_percent": 13.0, "inference_ms": 787.7259140077513, "memory_mb": 370.65234375, "per_utterance_latency_ms": 1701.7247110197786, "postprocess_ms": 0.08333701407536864, "preprocess_ms": 913.915459997952, "real_time_factor": 0.20482964745062335, "sample_accuracy": 1.0, "success_rate": 1.0, "total_latency_ms": 1701.7247110197786, "wer": 0.0}`
