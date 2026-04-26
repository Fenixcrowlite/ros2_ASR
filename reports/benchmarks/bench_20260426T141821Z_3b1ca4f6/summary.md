# Benchmark Summary: bench_20260426T141821Z_3b1ca4f6

- benchmark_profile: `default_benchmark`
- dataset_id: `fleurs_en_us_test_subset`
- providers: `providers/azure_cloud`
- scenario: `clean_baseline`
- execution_mode: `batch`
- noise_modes: `none, white`
- noise_levels: `clean, custom_0db`
- aggregate_scope: `single_provider`
- total_samples: `4`
- successful_samples: `0`
- failed_samples: `4`
- aggregate_samples: `4`
- corrupted_samples: `0`

## Per-Provider Summary

### providers/azure_cloud (preset: `standard`)
- samples: `4`
- successful_samples: `0`
- failed_samples: `4`
- quality_metrics: `{"cer": 1.0, "confidence": 0.0, "sample_accuracy": 0.0, "wer": 1.0}`
- latency_metrics: `{"end_to_end_latency_ms": 150.35530625027604, "end_to_end_rtf": 0.018717132952998525, "inference_ms": 0.0, "per_utterance_latency_ms": 0.0, "postprocess_ms": 0.0, "preprocess_ms": 0.0, "provider_compute_latency_ms": 0.0, "provider_compute_rtf": 0.0, "real_time_factor": 0.0, "time_to_final_result_ms": 150.35530625027604, "time_to_first_result_ms": 150.35530625027604, "time_to_result_ms": 150.35530625027604, "total_latency_ms": 0.0}`
- reliability_metrics: `{"failure_rate": 1.0, "success_rate": 0.0}`
- cost_metrics: `{"estimated_cost_usd": 0.002778}`
- cost_totals: `{"estimated_cost_usd": 0.011112}`
- estimated_cost_total_usd: `0.011112`

## Noise Summary
- clean: `{"audio_duration_sec": 9.26, "cer": 1.0, "confidence": 0.0, "cpu_percent": 5.175, "cpu_percent_mean": 5.170033091997358, "cpu_percent_peak": 13.2, "declared_audio_duration_sec": 9.26, "duration_mismatch_sec": 0.0, "end_to_end_latency_ms": 150.2018559986027, "end_to_end_rtf": 0.018689986906722345, "estimated_cost_usd": 0.002778, "failure_rate": 1.0, "gpu_memory_mb": 800.0, "gpu_memory_mb_mean": 799.9790867031468, "gpu_memory_mb_peak": 806.0, "gpu_util_percent": 6.5, "gpu_util_percent_mean": 6.498257225262231, "gpu_util_percent_peak": 7.0, "inference_ms": 0.0, "measured_audio_duration_sec": 9.26, "memory_mb": 105.2236328125, "memory_mb_mean": 105.22339794637323, "memory_mb_peak": 105.30078125, "per_utterance_latency_ms": 0.0, "postprocess_ms": 0.0, "preprocess_ms": 0.0, "provider_compute_latency_ms": 0.0, "provider_compute_rtf": 0.0, "real_time_factor": 0.0, "sample_accuracy": 0.0, "success_rate": 0.0, "time_to_final_result_ms": 150.2018559986027, "time_to_first_result_ms": 150.2018559986027, "time_to_result_ms": 150.2018559986027, "total_latency_ms": 0.0, "wer": 1.0}`
- white:custom_0db: `{"audio_duration_sec": 9.26, "cer": 1.0, "confidence": 0.0, "cpu_percent": 3.3, "cpu_percent_mean": 3.2998300768362623, "cpu_percent_peak": 6.9, "declared_audio_duration_sec": 9.26, "duration_mismatch_sec": 0.0, "end_to_end_latency_ms": 150.5087565019494, "end_to_end_rtf": 0.018744278999274704, "estimated_cost_usd": 0.002778, "failure_rate": 1.0, "gpu_memory_mb": 799.5, "gpu_memory_mb_mean": 799.4903710207216, "gpu_memory_mb_peak": 808.0, "gpu_util_percent": 3.5, "gpu_util_percent_mean": 3.5039648738205473, "gpu_util_percent_peak": 7.0, "inference_ms": 0.0, "measured_audio_duration_sec": 9.26, "memory_mb": 106.3369140625, "memory_mb_mean": 106.3357049087372, "memory_mb_peak": 107.41796875, "per_utterance_latency_ms": 0.0, "postprocess_ms": 0.0, "preprocess_ms": 0.0, "provider_compute_latency_ms": 0.0, "provider_compute_rtf": 0.0, "real_time_factor": 0.0, "sample_accuracy": 0.0, "success_rate": 0.0, "time_to_final_result_ms": 150.5087565019494, "time_to_first_result_ms": 150.5087565019494, "time_to_result_ms": 150.5087565019494, "total_latency_ms": 0.0, "wer": 1.0}`
