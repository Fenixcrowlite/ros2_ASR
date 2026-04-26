# Benchmark Summary: bench_20260426T141646Z_7a2e7f09

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
- latency_metrics: `{"end_to_end_latency_ms": 164.4560850036214, "end_to_end_rtf": 0.019852308004888596, "inference_ms": 0.0, "per_utterance_latency_ms": 0.0, "postprocess_ms": 0.0, "preprocess_ms": 0.0, "provider_compute_latency_ms": 0.0, "provider_compute_rtf": 0.0, "real_time_factor": 0.0, "time_to_final_result_ms": 164.4560850036214, "time_to_first_result_ms": 164.4560850036214, "time_to_result_ms": 164.4560850036214, "total_latency_ms": 0.0}`
- reliability_metrics: `{"failure_rate": 1.0, "success_rate": 0.0}`
- cost_metrics: `{"estimated_cost_usd": 0.002778}`
- cost_totals: `{"estimated_cost_usd": 0.011112}`
- estimated_cost_total_usd: `0.011112`

## Noise Summary
- clean: `{"audio_duration_sec": 9.26, "cer": 1.0, "confidence": 0.0, "cpu_percent": 4.175000000000001, "cpu_percent_mean": 4.241556138306097, "cpu_percent_peak": 7.5, "declared_audio_duration_sec": 9.26, "duration_mismatch_sec": 0.0, "end_to_end_latency_ms": 178.35269349598093, "end_to_end_rtf": 0.020950938868052302, "estimated_cost_usd": 0.002778, "failure_rate": 1.0, "gpu_memory_mb": 837.0, "gpu_memory_mb_mean": 839.8188482106112, "gpu_memory_mb_peak": 855.0, "gpu_util_percent": 0.0, "gpu_util_percent_mean": 0.0, "gpu_util_percent_peak": 0.0, "inference_ms": 0.0, "measured_audio_duration_sec": 9.26, "memory_mb": 98.5224609375, "memory_mb_mean": 97.82585429691115, "memory_mb_peak": 103.67578125, "per_utterance_latency_ms": 0.0, "postprocess_ms": 0.0, "preprocess_ms": 0.0, "provider_compute_latency_ms": 0.0, "provider_compute_rtf": 0.0, "real_time_factor": 0.0, "sample_accuracy": 0.0, "success_rate": 0.0, "time_to_final_result_ms": 178.35269349598093, "time_to_first_result_ms": 178.35269349598093, "time_to_result_ms": 178.35269349598093, "total_latency_ms": 0.0, "wer": 1.0}`
- white:custom_0db: `{"audio_duration_sec": 9.26, "cer": 1.0, "confidence": 0.0, "cpu_percent": 2.5250000000000004, "cpu_percent_mean": 2.525221900266266, "cpu_percent_peak": 5.7, "declared_audio_duration_sec": 9.26, "duration_mismatch_sec": 0.0, "end_to_end_latency_ms": 150.5594765112619, "end_to_end_rtf": 0.018753677141724885, "estimated_cost_usd": 0.002778, "failure_rate": 1.0, "gpu_memory_mb": 818.5, "gpu_memory_mb_mean": 818.4996586149749, "gpu_memory_mb_peak": 819.0, "gpu_util_percent": 10.0, "gpu_util_percent_mean": 9.993172299499504, "gpu_util_percent_peak": 20.0, "inference_ms": 0.0, "measured_audio_duration_sec": 9.26, "memory_mb": 103.146484375, "memory_mb_mean": 103.14537354013342, "memory_mb_peak": 104.78515625, "per_utterance_latency_ms": 0.0, "postprocess_ms": 0.0, "preprocess_ms": 0.0, "provider_compute_latency_ms": 0.0, "provider_compute_rtf": 0.0, "real_time_factor": 0.0, "sample_accuracy": 0.0, "success_rate": 0.0, "time_to_final_result_ms": 150.5594765112619, "time_to_first_result_ms": 150.5594765112619, "time_to_result_ms": 150.5594765112619, "total_latency_ms": 0.0, "wer": 1.0}`
