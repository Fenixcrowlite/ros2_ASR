# Benchmark Summary: bench_20260427T141048Z_d1922b62

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
- latency_metrics: `{"end_to_end_latency_ms": 2702.6979649999703, "end_to_end_rtf": 0.3253127064275361, "inference_ms": 512.2012390002055, "per_utterance_latency_ms": 2702.3913089997222, "postprocess_ms": 0.08279500070784707, "preprocess_ms": 2190.107274998809, "provider_compute_latency_ms": 2702.3913089997222, "provider_compute_rtf": 0.32527579549828145, "real_time_factor": 0.32527579549828145, "time_to_final_result_ms": 2702.6979649999703, "time_to_first_result_ms": 2702.6979649999703, "time_to_result_ms": 2702.6979649999703, "total_latency_ms": 2702.3913089997222}`
- reliability_metrics: `{"failure_rate": 0.0, "success_rate": 1.0}`
- cost_metrics: `{"estimated_cost_usd": 0.0}`
- cost_totals: `{"estimated_cost_usd": 0.0}`
- estimated_cost_total_usd: `0.0`

## Noise Summary
- clean: `{"audio_duration_sec": 8.308, "cer": 0.0, "confidence": 0.6638665311297195, "cpu_percent": 16.952, "cpu_percent_mean": 16.952, "cpu_percent_peak": 71.2, "declared_audio_duration_sec": 8.308, "duration_mismatch_sec": 0.0, "end_to_end_latency_ms": 2702.6979649999703, "end_to_end_rtf": 0.3253127064275361, "estimated_cost_usd": 0.0, "failure_rate": 0.0, "gpu_memory_mb": 693.4444444444445, "gpu_memory_mb_mean": 693.4444444444445, "gpu_memory_mb_peak": 694.0, "gpu_util_percent": 33.55555555555556, "gpu_util_percent_mean": 33.55555555555556, "gpu_util_percent_peak": 43.0, "inference_ms": 512.2012390002055, "measured_audio_duration_sec": 8.308, "memory_mb": 670.406875, "memory_mb_mean": 670.406875, "memory_mb_peak": 894.56640625, "per_utterance_latency_ms": 2702.3913089997222, "postprocess_ms": 0.08279500070784707, "preprocess_ms": 2190.107274998809, "provider_compute_latency_ms": 2702.3913089997222, "provider_compute_rtf": 0.32527579549828145, "real_time_factor": 0.32527579549828145, "sample_accuracy": 1.0, "success_rate": 1.0, "time_to_final_result_ms": 2702.6979649999703, "time_to_first_result_ms": 2702.6979649999703, "time_to_result_ms": 2702.6979649999703, "total_latency_ms": 2702.3913089997222, "wer": 0.0}`
