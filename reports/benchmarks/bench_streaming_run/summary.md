# Benchmark Summary: bench_streaming_run

- benchmark_profile: `bench`
- dataset_id: `bench_dataset`
- providers: `providers/fake_stream`
- scenario: `clean_baseline`
- execution_mode: `streaming`
- noise_modes: `none`
- noise_levels: `clean`
- aggregate_scope: `single_provider`
- total_samples: `1`
- successful_samples: `1`
- failed_samples: `0`
- aggregate_samples: `1`
- corrupted_samples: `0`

## Per-Provider Summary

### providers/fake_stream
- samples: `1`
- successful_samples: `1`
- failed_samples: `0`
- quality_metrics: `{"confidence": 0.92, "wer": 0.3333333333333333}`
- latency_metrics: `{"end_to_end_latency_ms": 8308.171002998279, "end_to_end_rtf": 1.0000205829319064, "inference_ms": 0.0, "per_utterance_latency_ms": 15.0, "postprocess_ms": 0.0, "preprocess_ms": 0.0, "provider_compute_latency_ms": 15.0, "provider_compute_rtf": 0.0018054886856042369, "real_time_factor": 0.0018054886856042369, "time_to_final_result_ms": 8308.171002998279, "time_to_first_result_ms": 5.0, "time_to_result_ms": 8308.171002998279, "total_latency_ms": 15.0}`
- cost_metrics: `{"estimated_cost_usd": 0.0}`
- cost_totals: `{"estimated_cost_usd": 0.0}`
- streaming_metrics: `{"finalization_latency_ms": 0.29817999893566594, "first_partial_latency_ms": 5.0, "partial_count": 34.0}`
- estimated_cost_total_usd: `0.0`

## Noise Summary
- clean: `{"audio_duration_sec": 8.308, "confidence": 0.92, "cpu_percent": 12.981927710843374, "cpu_percent_mean": 12.981927710843374, "cpu_percent_peak": 100.0, "duration_mismatch_sec": 0.0, "end_to_end_latency_ms": 8308.171002998279, "end_to_end_rtf": 1.0000205829319064, "estimated_cost_usd": 0.0, "finalization_latency_ms": 0.29817999893566594, "first_partial_latency_ms": 5.0, "gpu_memory_mb": 803.8928571428571, "gpu_memory_mb_mean": 803.8928571428571, "gpu_memory_mb_peak": 818.0, "gpu_util_percent": 9.785714285714286, "gpu_util_percent_mean": 9.785714285714286, "gpu_util_percent_peak": 19.0, "inference_ms": 0.0, "measured_audio_duration_sec": 8.308, "memory_mb": 126.05845256024097, "memory_mb_mean": 126.05845256024097, "memory_mb_peak": 126.05859375, "partial_count": 34.0, "per_utterance_latency_ms": 15.0, "postprocess_ms": 0.0, "preprocess_ms": 0.0, "provider_compute_latency_ms": 15.0, "provider_compute_rtf": 0.0018054886856042369, "real_time_factor": 0.0018054886856042369, "time_to_final_result_ms": 8308.171002998279, "time_to_first_result_ms": 5.0, "time_to_result_ms": 8308.171002998279, "total_latency_ms": 15.0, "wer": 0.3333333333333333}`
