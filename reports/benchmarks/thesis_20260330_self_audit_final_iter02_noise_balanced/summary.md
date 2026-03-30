# Benchmark Summary: thesis_20260330_self_audit_final_iter02_noise_balanced

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
- latency_metrics: `{"inference_ms": 832.3381509981118, "per_utterance_latency_ms": 1043.7667179867276, "postprocess_ms": 0.5349337370716967, "preprocess_ms": 210.8936332515441, "real_time_factor": 0.125633933315687, "total_latency_ms": 1043.7667179867276}`
- reliability_metrics: `{"failure_rate": 0.0, "success_rate": 1.0}`
- cost_metrics: `{"estimated_cost_usd": 0.0}`
- cost_totals: `{"estimated_cost_usd": 0.0}`
- estimated_cost_total_usd: `0.0`

## Noise Summary
- clean: `{"cer": 0.0, "confidence": 0.8086438129491665, "cpu_percent": 2.5, "estimated_cost_usd": 0.0, "failure_rate": 0.0, "gpu_memory_mb": 829.0, "gpu_util_percent": 4.0, "inference_ms": 1041.094800020801, "memory_mb": 438.12109375, "per_utterance_latency_ms": 1886.3052420201711, "postprocess_ms": 1.6582209791522473, "preprocess_ms": 843.552221020218, "real_time_factor": 0.22704685147089204, "sample_accuracy": 1.0, "success_rate": 1.0, "total_latency_ms": 1886.3052420201711, "wer": 0.0}`
- heavy: `{"cer": 0.0, "confidence": 0.723194484554586, "cpu_percent": 3.9, "estimated_cost_usd": 0.0, "failure_rate": 0.0, "gpu_memory_mb": 832.0, "gpu_util_percent": 13.0, "inference_ms": 832.1164450026117, "memory_mb": 433.91796875, "per_utterance_latency_ms": 832.4352839845233, "postprocess_ms": 0.3110139805357903, "preprocess_ms": 0.007825001375749707, "real_time_factor": 0.1001968324487871, "sample_accuracy": 1.0, "success_rate": 1.0, "total_latency_ms": 832.4352839845233, "wer": 0.0}`
- light: `{"cer": 0.0, "confidence": 0.7381789052980186, "cpu_percent": 5.0, "estimated_cost_usd": 0.0, "failure_rate": 0.0, "gpu_memory_mb": 828.0, "gpu_util_percent": 1.0, "inference_ms": 677.275968977483, "memory_mb": 443.8203125, "per_utterance_latency_ms": 677.3681309714448, "postprocess_ms": 0.08535000961273909, "preprocess_ms": 0.006811984349042177, "real_time_factor": 0.08153203309718883, "sample_accuracy": 1.0, "success_rate": 1.0, "total_latency_ms": 677.3681309714448, "wer": 0.0}`
- medium: `{"cer": 0.0, "confidence": 0.7477221112415708, "cpu_percent": 7.7, "estimated_cost_usd": 0.0, "failure_rate": 0.0, "gpu_memory_mb": 829.0, "gpu_util_percent": 11.0, "inference_ms": 778.8653899915516, "memory_mb": 443.4140625, "per_utterance_latency_ms": 778.9582149707712, "postprocess_ms": 0.08514997898600996, "preprocess_ms": 0.007675000233575702, "real_time_factor": 0.09376001624588003, "sample_accuracy": 1.0, "success_rate": 1.0, "total_latency_ms": 778.9582149707712, "wer": 0.0}`
