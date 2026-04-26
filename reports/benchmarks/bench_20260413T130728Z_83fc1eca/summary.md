# Benchmark Summary: bench_20260413T130728Z_83fc1eca

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
- latency_metrics: `{"end_to_end_latency_ms": 8275.992633018177, "end_to_end_rtf": 0.9961474040705558, "inference_ms": 872.2279969952069, "per_utterance_latency_ms": 8275.608088995796, "postprocess_ms": 0.10525801917538047, "preprocess_ms": 7403.274833981413, "provider_compute_latency_ms": 8275.608088995796, "provider_compute_rtf": 0.996101118078454, "real_time_factor": 0.996101118078454, "time_to_final_result_ms": 8275.992633018177, "time_to_first_result_ms": 8275.992633018177, "time_to_result_ms": 8275.992633018177, "total_latency_ms": 8275.608088995796}`
- reliability_metrics: `{"failure_rate": 0.0, "success_rate": 1.0}`
- cost_metrics: `{"estimated_cost_usd": 0.0}`
- cost_totals: `{"estimated_cost_usd": 0.0}`
- estimated_cost_total_usd: `0.0`

## Noise Summary
- clean: `{"audio_duration_sec": 8.308, "cer": 0.0, "confidence": 0.6638665311297195, "cpu_percent": 24.54385964912281, "cpu_percent_mean": 24.54385964912281, "cpu_percent_peak": 75.0, "declared_audio_duration_sec": 8.308, "duration_mismatch_sec": 0.0, "end_to_end_latency_ms": 8275.992633018177, "end_to_end_rtf": 0.9961474040705558, "estimated_cost_usd": 0.0, "failure_rate": 0.0, "gpu_memory_mb": 928.8260869565217, "gpu_memory_mb_mean": 928.8260869565217, "gpu_memory_mb_peak": 933.0, "gpu_util_percent": 28.26086956521739, "gpu_util_percent_mean": 28.26086956521739, "gpu_util_percent_peak": 44.0, "inference_ms": 872.2279969952069, "measured_audio_duration_sec": 8.308, "memory_mb": 570.8850740131579, "memory_mb_mean": 570.8850740131579, "memory_mb_peak": 814.55078125, "per_utterance_latency_ms": 8275.608088995796, "postprocess_ms": 0.10525801917538047, "preprocess_ms": 7403.274833981413, "provider_compute_latency_ms": 8275.608088995796, "provider_compute_rtf": 0.996101118078454, "real_time_factor": 0.996101118078454, "sample_accuracy": 1.0, "success_rate": 1.0, "time_to_final_result_ms": 8275.992633018177, "time_to_first_result_ms": 8275.992633018177, "time_to_result_ms": 8275.992633018177, "total_latency_ms": 8275.608088995796, "wer": 0.0}`
