# Benchmark Summary: bench_20260427T141029Z_d6c1b1da

- benchmark_profile: `benchmark/default_benchmark`
- dataset_id: `sample_dataset`
- providers: `providers/whisper_local`
- scenario: `clean_baseline`
- execution_mode: `batch`
- noise_modes: `none`
- noise_levels: `clean`
- aggregate_scope: `single_provider`
- total_samples: `1`
- successful_samples: `1`
- failed_samples: `0`
- aggregate_samples: `1`
- corrupted_samples: `0`

## Per-Provider Summary

### providers/whisper_local (preset: `light`)
- samples: `1`
- successful_samples: `1`
- failed_samples: `0`
- quality_metrics: `{"cer": 0.0, "confidence": 0.6638665311297195, "sample_accuracy": 1.0, "wer": 0.0}`
- latency_metrics: `{"end_to_end_latency_ms": 2666.4197959999, "end_to_end_rtf": 0.3209460515165985, "inference_ms": 515.1705049993325, "per_utterance_latency_ms": 2666.0260779990494, "postprocess_ms": 0.09257300007448066, "preprocess_ms": 2150.7629999996425, "provider_compute_latency_ms": 2666.0260779990494, "provider_compute_rtf": 0.32089866129020816, "real_time_factor": 0.32089866129020816, "time_to_final_result_ms": 2666.4197959999, "time_to_first_result_ms": 2666.4197959999, "time_to_result_ms": 2666.4197959999, "total_latency_ms": 2666.0260779990494}`
- reliability_metrics: `{"failure_rate": 0.0, "success_rate": 1.0}`
- cost_metrics: `{"estimated_cost_usd": 0.0}`
- cost_totals: `{"estimated_cost_usd": 0.0}`
- estimated_cost_total_usd: `0.0`

## Noise Summary
- clean: `{"audio_duration_sec": 8.308, "cer": 0.0, "confidence": 0.6638665311297195, "cpu_percent": 16.425, "cpu_percent_mean": 16.425, "cpu_percent_peak": 70.6, "declared_audio_duration_sec": 8.308, "duration_mismatch_sec": 0.0, "end_to_end_latency_ms": 2666.4197959999, "end_to_end_rtf": 0.3209460515165985, "estimated_cost_usd": 0.0, "failure_rate": 0.0, "gpu_memory_mb": 692.4444444444445, "gpu_memory_mb_mean": 692.4444444444445, "gpu_memory_mb_peak": 705.0, "gpu_util_percent": 27.444444444444443, "gpu_util_percent_mean": 27.444444444444443, "gpu_util_percent_peak": 41.0, "inference_ms": 515.1705049993325, "measured_audio_duration_sec": 8.308, "memory_mb": 678.58447265625, "memory_mb_mean": 678.58447265625, "memory_mb_peak": 902.3046875, "per_utterance_latency_ms": 2666.0260779990494, "postprocess_ms": 0.09257300007448066, "preprocess_ms": 2150.7629999996425, "provider_compute_latency_ms": 2666.0260779990494, "provider_compute_rtf": 0.32089866129020816, "real_time_factor": 0.32089866129020816, "sample_accuracy": 1.0, "success_rate": 1.0, "time_to_final_result_ms": 2666.4197959999, "time_to_first_result_ms": 2666.4197959999, "time_to_result_ms": 2666.4197959999, "total_latency_ms": 2666.0260779990494, "wer": 0.0}`
