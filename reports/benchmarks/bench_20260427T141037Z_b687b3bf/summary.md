# Benchmark Summary: bench_20260427T141037Z_b687b3bf

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
- latency_metrics: `{"end_to_end_latency_ms": 2715.2879500008567, "end_to_end_rtf": 0.326828111458938, "inference_ms": 515.1961619994836, "per_utterance_latency_ms": 2714.9230539998825, "postprocess_ms": 0.10449500041431747, "preprocess_ms": 2199.6223969999846, "provider_compute_latency_ms": 2714.9230539998825, "provider_compute_rtf": 0.32678419041885926, "real_time_factor": 0.32678419041885926, "time_to_final_result_ms": 2715.2879500008567, "time_to_first_result_ms": 2715.2879500008567, "time_to_result_ms": 2715.2879500008567, "total_latency_ms": 2714.9230539998825}`
- reliability_metrics: `{"failure_rate": 0.0, "success_rate": 1.0}`
- cost_metrics: `{"estimated_cost_usd": 0.0}`
- cost_totals: `{"estimated_cost_usd": 0.0}`
- estimated_cost_total_usd: `0.0`

## Noise Summary
- clean: `{"audio_duration_sec": 8.308, "cer": 0.0, "confidence": 0.6638665311297195, "cpu_percent": 16.516, "cpu_percent_mean": 16.516, "cpu_percent_peak": 71.2, "declared_audio_duration_sec": 8.308, "duration_mismatch_sec": 0.0, "end_to_end_latency_ms": 2715.2879500008567, "end_to_end_rtf": 0.326828111458938, "estimated_cost_usd": 0.0, "failure_rate": 0.0, "gpu_memory_mb": 680.8888888888889, "gpu_memory_mb_mean": 680.8888888888889, "gpu_memory_mb_peak": 684.0, "gpu_util_percent": 27.555555555555557, "gpu_util_percent_mean": 27.555555555555557, "gpu_util_percent_peak": 47.0, "inference_ms": 515.1961619994836, "measured_audio_duration_sec": 8.308, "memory_mb": 672.85390625, "memory_mb_mean": 672.85390625, "memory_mb_peak": 881.375, "per_utterance_latency_ms": 2714.9230539998825, "postprocess_ms": 0.10449500041431747, "preprocess_ms": 2199.6223969999846, "provider_compute_latency_ms": 2714.9230539998825, "provider_compute_rtf": 0.32678419041885926, "real_time_factor": 0.32678419041885926, "sample_accuracy": 1.0, "success_rate": 1.0, "time_to_final_result_ms": 2715.2879500008567, "time_to_first_result_ms": 2715.2879500008567, "time_to_result_ms": 2715.2879500008567, "total_latency_ms": 2714.9230539998825, "wer": 0.0}`
