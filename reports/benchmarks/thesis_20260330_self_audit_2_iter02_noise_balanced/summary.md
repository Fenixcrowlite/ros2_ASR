# Benchmark Summary: thesis_20260330_self_audit_2_iter02_noise_balanced

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
- latency_metrics: `{"inference_ms": 748.5222144896397, "per_utterance_latency_ms": 913.7502877420047, "postprocess_ms": 0.09688399586593732, "preprocess_ms": 165.13118925649906, "real_time_factor": 0.10998438706572036, "total_latency_ms": 913.7502877420047}`
- reliability_metrics: `{"failure_rate": 0.0, "success_rate": 1.0}`
- cost_metrics: `{"estimated_cost_usd": 0.0}`
- cost_totals: `{"estimated_cost_usd": 0.0}`
- estimated_cost_total_usd: `0.0`

## Noise Summary
- clean: `{"cer": 0.0, "confidence": 0.8086438129491665, "cpu_percent": 6.2, "estimated_cost_usd": 0.0, "failure_rate": 0.0, "gpu_memory_mb": 776.0, "gpu_util_percent": 30.0, "inference_ms": 783.6135879915673, "memory_mb": 715.984375, "per_utterance_latency_ms": 1444.2216199822724, "postprocess_ms": 0.1053469895850867, "preprocess_ms": 660.50268500112, "real_time_factor": 0.17383505295886764, "sample_accuracy": 1.0, "success_rate": 1.0, "total_latency_ms": 1444.2216199822724, "wer": 0.0}`
- heavy: `{"cer": 0.0, "confidence": 0.723194484554586, "cpu_percent": 3.8, "estimated_cost_usd": 0.0, "failure_rate": 0.0, "gpu_memory_mb": 776.0, "gpu_util_percent": 30.0, "inference_ms": 748.9105089916848, "memory_mb": 721.91015625, "per_utterance_latency_ms": 749.039129994344, "postprocess_ms": 0.12100700405426323, "preprocess_ms": 0.007613998604938388, "real_time_factor": 0.09015877828530862, "sample_accuracy": 1.0, "success_rate": 1.0, "total_latency_ms": 749.039129994344, "wer": 0.0}`
- light: `{"cer": 0.0, "confidence": 0.7381789052980186, "cpu_percent": 7.4, "estimated_cost_usd": 0.0, "failure_rate": 0.0, "gpu_memory_mb": 776.0, "gpu_util_percent": 31.0, "inference_ms": 721.7740039923228, "memory_mb": 719.234375, "per_utterance_latency_ms": 721.8590639822651, "postprocess_ms": 0.07809698581695557, "preprocess_ms": 0.006963004125282168, "real_time_factor": 0.08688722484138964, "sample_accuracy": 1.0, "success_rate": 1.0, "total_latency_ms": 721.8590639822651, "wer": 0.0}`
- medium: `{"cer": 0.0, "confidence": 0.7477221112415708, "cpu_percent": 5.1, "estimated_cost_usd": 0.0, "failure_rate": 0.0, "gpu_memory_mb": 776.0, "gpu_util_percent": 30.0, "inference_ms": 739.790756982984, "memory_mb": 720.08984375, "per_utterance_latency_ms": 739.8813370091375, "postprocess_ms": 0.08308500400744379, "preprocess_ms": 0.0074950221460312605, "real_time_factor": 0.08905649217731554, "sample_accuracy": 1.0, "success_rate": 1.0, "total_latency_ms": 739.8813370091375, "wer": 0.0}`
