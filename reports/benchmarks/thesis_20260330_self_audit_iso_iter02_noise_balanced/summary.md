# Benchmark Summary: thesis_20260330_self_audit_iso_iter02_noise_balanced

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
- latency_metrics: `{"inference_ms": 732.8714357572608, "per_utterance_latency_ms": 907.2601049992954, "postprocess_ms": 0.10027574899140745, "preprocess_ms": 174.28839349304326, "real_time_factor": 0.10920319029842265, "total_latency_ms": 907.2601049992954}`
- reliability_metrics: `{"failure_rate": 0.0, "success_rate": 1.0}`
- cost_metrics: `{"estimated_cost_usd": 0.0}`
- cost_totals: `{"estimated_cost_usd": 0.0}`
- estimated_cost_total_usd: `0.0`

## Noise Summary
- clean: `{"cer": 0.0, "confidence": 0.8086438129491665, "cpu_percent": 7.6, "estimated_cost_usd": 0.0, "failure_rate": 0.0, "gpu_memory_mb": 778.0, "gpu_util_percent": 35.0, "inference_ms": 770.1474890054669, "memory_mb": 388.18359375, "per_utterance_latency_ms": 1467.3820349853486, "postprocess_ms": 0.10275299428030849, "preprocess_ms": 697.1317929856014, "real_time_factor": 0.1766227774416645, "sample_accuracy": 1.0, "success_rate": 1.0, "total_latency_ms": 1467.3820349853486, "wer": 0.0}`
- heavy: `{"cer": 0.0, "confidence": 0.723194484554586, "cpu_percent": 9.9, "estimated_cost_usd": 0.0, "failure_rate": 0.0, "gpu_memory_mb": 778.0, "gpu_util_percent": 34.0, "inference_ms": 718.45323900925, "memory_mb": 389.6796875, "per_utterance_latency_ms": 718.5424869821873, "postprocess_ms": 0.08174398681148887, "preprocess_ms": 0.0075039861258119345, "real_time_factor": 0.08648802202481792, "sample_accuracy": 1.0, "success_rate": 1.0, "total_latency_ms": 718.5424869821873, "wer": 0.0}`
- light: `{"cer": 0.0, "confidence": 0.7381789052980186, "cpu_percent": 3.8, "estimated_cost_usd": 0.0, "failure_rate": 0.0, "gpu_memory_mb": 778.0, "gpu_util_percent": 34.0, "inference_ms": 716.6243169922382, "memory_mb": 389.6328125, "per_utterance_latency_ms": 716.7594899947289, "postprocess_ms": 0.12802000856027007, "preprocess_ms": 0.007152993930503726, "real_time_factor": 0.08627340996566309, "sample_accuracy": 1.0, "success_rate": 1.0, "total_latency_ms": 716.7594899947289, "wer": 0.0}`
- medium: `{"cer": 0.0, "confidence": 0.7477221112415708, "cpu_percent": 7.4, "estimated_cost_usd": 0.0, "failure_rate": 0.0, "gpu_memory_mb": 778.0, "gpu_util_percent": 34.0, "inference_ms": 726.260698022088, "memory_mb": 389.67578125, "per_utterance_latency_ms": 726.356408034917, "postprocess_ms": 0.0885860063135624, "preprocess_ms": 0.007124006515368819, "real_time_factor": 0.08742855176154514, "sample_accuracy": 1.0, "success_rate": 1.0, "total_latency_ms": 726.356408034917, "wer": 0.0}`
