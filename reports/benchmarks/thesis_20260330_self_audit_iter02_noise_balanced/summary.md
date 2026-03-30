# Benchmark Summary: thesis_20260330_self_audit_iter02_noise_balanced

- benchmark_profile: `benchmark/default_benchmark`
- dataset_id: `sample_dataset`
- providers: `providers/whisper_local`
- scenario: `noise_robustness`
- execution_mode: `batch`
- aggregate_scope: `single_provider`
- total_samples: `4`
- successful_samples: `4`
- failed_samples: `0`

## Per-Provider Summary

### providers/whisper_local (preset: `balanced`)
- samples: `4`
- successful_samples: `4`
- failed_samples: `0`
- quality_metrics: `{"cer": 0.0, "confidence": 0.7544348285108355, "sample_accuracy": 1.0, "wer": 0.0}`
- latency_metrics: `{"inference_ms": 760.286145748978, "per_utterance_latency_ms": 928.7234085059026, "postprocess_ms": 0.09849725029198453, "preprocess_ms": 168.33876550663263, "real_time_factor": 0.11178664040754727, "total_latency_ms": 928.7234085059026}`
- reliability_metrics: `{"failure_rate": 0.0, "success_rate": 1.0}`
- cost_metrics: `{"estimated_cost_usd": 0.0}`
- cost_totals: `{"estimated_cost_usd": 0.0}`
- estimated_cost_total_usd: `0.0`

## Noise Summary
- clean: `{"cer": 0.0, "confidence": 0.8086438129491665, "cpu_percent": 6.3, "estimated_cost_usd": 0.0, "failure_rate": 0.0, "gpu_memory_mb": 778.0, "gpu_util_percent": 33.0, "inference_ms": 782.1427099988796, "memory_mb": 699.59375, "per_utterance_latency_ms": 1455.584675015416, "postprocess_ms": 0.10992601164616644, "preprocess_ms": 673.3320390048902, "real_time_factor": 0.1752027774452836, "sample_accuracy": 1.0, "success_rate": 1.0, "total_latency_ms": 1455.584675015416, "wer": 0.0}`
- heavy: `{"cer": 0.0, "confidence": 0.723194484554586, "cpu_percent": 5.1, "estimated_cost_usd": 0.0, "failure_rate": 0.0, "gpu_memory_mb": 778.0, "gpu_util_percent": 35.0, "inference_ms": 723.3745499979705, "memory_mb": 703.390625, "per_utterance_latency_ms": 723.4859589952976, "postprocess_ms": 0.10376397403888404, "preprocess_ms": 0.007645023288205266, "real_time_factor": 0.08708304754396938, "sample_accuracy": 1.0, "success_rate": 1.0, "total_latency_ms": 723.4859589952976, "wer": 0.0}`
- light: `{"cer": 0.0, "confidence": 0.7381789052980186, "cpu_percent": 12.3, "estimated_cost_usd": 0.0, "failure_rate": 0.0, "gpu_memory_mb": 778.0, "gpu_util_percent": 34.0, "inference_ms": 799.4419960014056, "memory_mb": 701.63671875, "per_utterance_latency_ms": 799.5332670107018, "postprocess_ms": 0.08451900794170797, "preprocess_ms": 0.006752001354470849, "real_time_factor": 0.0962365511568009, "sample_accuracy": 1.0, "success_rate": 1.0, "total_latency_ms": 799.5332670107018, "wer": 0.0}`
- medium: `{"cer": 0.0, "confidence": 0.7477221112415708, "cpu_percent": 3.7, "estimated_cost_usd": 0.0, "failure_rate": 0.0, "gpu_memory_mb": 778.0, "gpu_util_percent": 35.0, "inference_ms": 736.1853269976564, "memory_mb": 702.49609375, "per_utterance_latency_ms": 736.2897330021951, "postprocess_ms": 0.09578000754117966, "preprocess_ms": 0.008625996997579932, "real_time_factor": 0.08862418548413518, "sample_accuracy": 1.0, "success_rate": 1.0, "total_latency_ms": 736.2897330021951, "wer": 0.0}`
