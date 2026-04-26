# Benchmark Summary: bench_20260426T141817Z_9527494c

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
- latency_metrics: `{"end_to_end_latency_ms": 175.90586074948078, "end_to_end_rtf": 0.02187276185112723, "inference_ms": 0.0, "per_utterance_latency_ms": 0.0, "postprocess_ms": 0.0, "preprocess_ms": 0.0, "provider_compute_latency_ms": 0.0, "provider_compute_rtf": 0.0, "real_time_factor": 0.0, "time_to_final_result_ms": 175.90586074948078, "time_to_first_result_ms": 175.90586074948078, "time_to_result_ms": 175.90586074948078, "total_latency_ms": 0.0}`
- reliability_metrics: `{"failure_rate": 1.0, "success_rate": 0.0}`
- cost_metrics: `{"estimated_cost_usd": 0.002778}`
- cost_totals: `{"estimated_cost_usd": 0.011112}`
- estimated_cost_total_usd: `0.011112`

## Noise Summary
- clean: `{"audio_duration_sec": 9.26, "cer": 1.0, "confidence": 0.0, "cpu_percent": 2.675, "cpu_percent_mean": 2.673839060312203, "cpu_percent_peak": 6.2, "declared_audio_duration_sec": 9.26, "duration_mismatch_sec": 0.0, "end_to_end_latency_ms": 201.28321799711557, "end_to_end_rtf": 0.02501734695557977, "estimated_cost_usd": 0.002778, "failure_rate": 1.0, "gpu_memory_mb": 782.0, "gpu_memory_mb_mean": 782.0, "gpu_memory_mb_peak": 782.0, "gpu_util_percent": 8.5, "gpu_util_percent_mean": 8.556388499121585, "gpu_util_percent_peak": 17.0, "inference_ms": 0.0, "measured_audio_duration_sec": 9.26, "memory_mb": 98.76888020833334, "memory_mb_mean": 98.73990422483098, "memory_mb_peak": 103.83203125, "per_utterance_latency_ms": 0.0, "postprocess_ms": 0.0, "preprocess_ms": 0.0, "provider_compute_latency_ms": 0.0, "provider_compute_rtf": 0.0, "real_time_factor": 0.0, "sample_accuracy": 0.0, "success_rate": 0.0, "time_to_final_result_ms": 201.28321799711557, "time_to_first_result_ms": 201.28321799711557, "time_to_result_ms": 201.28321799711557, "total_latency_ms": 0.0, "wer": 1.0}`
- white:custom_0db: `{"audio_duration_sec": 9.26, "cer": 1.0, "confidence": 0.0, "cpu_percent": 2.675, "cpu_percent_mean": 2.6756727487559453, "cpu_percent_peak": 5.7, "declared_audio_duration_sec": 9.26, "duration_mismatch_sec": 0.0, "end_to_end_latency_ms": 150.528503501846, "end_to_end_rtf": 0.018728176746674687, "estimated_cost_usd": 0.002778, "failure_rate": 1.0, "gpu_memory_mb": 782.0, "gpu_memory_mb_mean": 782.0, "gpu_memory_mb_peak": 782.0, "gpu_util_percent": 1.0, "gpu_util_percent_mean": 0.996155721394598, "gpu_util_percent_peak": 2.0, "inference_ms": 0.0, "measured_audio_duration_sec": 9.26, "memory_mb": 103.2763671875, "memory_mb_mean": 103.27022910593766, "memory_mb_peak": 104.89453125, "per_utterance_latency_ms": 0.0, "postprocess_ms": 0.0, "preprocess_ms": 0.0, "provider_compute_latency_ms": 0.0, "provider_compute_rtf": 0.0, "real_time_factor": 0.0, "sample_accuracy": 0.0, "success_rate": 0.0, "time_to_final_result_ms": 150.528503501846, "time_to_first_result_ms": 150.528503501846, "time_to_result_ms": 150.528503501846, "total_latency_ms": 0.0, "wer": 1.0}`
