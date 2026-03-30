# Benchmark Summary: thesis_20260330_self_audit_final_iter03_sk_balanced

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
- latency_metrics: `{"inference_ms": 717.9445265064714, "per_utterance_latency_ms": 1212.4096534971613, "postprocess_ms": 0.09393600339535624, "preprocess_ms": 494.37119098729454, "real_time_factor": 0.2811906086768351, "total_latency_ms": 1212.4096534971613}`
- reliability_metrics: `{"failure_rate": 0.0, "success_rate": 1.0}`
- cost_metrics: `{"estimated_cost_usd": 0.0}`
- cost_totals: `{"estimated_cost_usd": 0.0}`
- estimated_cost_total_usd: `0.0`

## Noise Summary
- clean: `{"cer": 0.20618556701030927, "confidence": 0.6505668741602589, "cpu_percent": 3.7, "estimated_cost_usd": 0.0, "failure_rate": 0.0, "gpu_memory_mb": 902.5, "gpu_util_percent": 20.0, "inference_ms": 717.9445265064714, "memory_mb": 434.96875, "per_utterance_latency_ms": 1212.4096534971613, "postprocess_ms": 0.09393600339535624, "preprocess_ms": 494.37119098729454, "real_time_factor": 0.2811906086768351, "sample_accuracy": 0.0, "success_rate": 1.0, "total_latency_ms": 1212.4096534971613, "wer": 0.7142857142857143}`
