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
- latency_metrics: `{"end_to_end_latency_ms": 8308.82820599993, "end_to_end_rtf": 1.0000996877708146, "inference_ms": 0.0, "per_utterance_latency_ms": 15.0, "postprocess_ms": 0.0, "preprocess_ms": 0.0, "provider_compute_latency_ms": 15.0, "provider_compute_rtf": 0.0018054886856042369, "real_time_factor": 0.0018054886856042369, "time_to_final_result_ms": 8308.82820599993, "time_to_first_result_ms": 5.0, "time_to_result_ms": 8308.82820599993, "total_latency_ms": 15.0}`
- cost_metrics: `{"estimated_cost_usd": 0.0}`
- cost_totals: `{"estimated_cost_usd": 0.0}`
- streaming_metrics: `{"finalization_latency_ms": 0.8552269999881901, "first_partial_latency_ms": 5.0, "partial_count": 34.0}`
- estimated_cost_total_usd: `0.0`

## Noise Summary
- clean: `{"audio_duration_sec": 8.308, "confidence": 0.92, "cpu_percent": 5.965060240963855, "cpu_percent_mean": 5.965060240963855, "cpu_percent_peak": 17.7, "duration_mismatch_sec": 0.0, "end_to_end_latency_ms": 8308.82820599993, "end_to_end_rtf": 1.0000996877708146, "estimated_cost_usd": 0.0, "finalization_latency_ms": 0.8552269999881901, "first_partial_latency_ms": 5.0, "gpu_memory_mb": 723.0, "gpu_memory_mb_mean": 723.0, "gpu_memory_mb_peak": 787.0, "gpu_util_percent": 8.821428571428571, "gpu_util_percent_mean": 8.821428571428571, "gpu_util_percent_peak": 23.0, "inference_ms": 0.0, "measured_audio_duration_sec": 8.308, "memory_mb": 109.8117469879518, "memory_mb_mean": 109.8117469879518, "memory_mb_peak": 109.81640625, "partial_count": 34.0, "per_utterance_latency_ms": 15.0, "postprocess_ms": 0.0, "preprocess_ms": 0.0, "provider_compute_latency_ms": 15.0, "provider_compute_rtf": 0.0018054886856042369, "real_time_factor": 0.0018054886856042369, "time_to_final_result_ms": 8308.82820599993, "time_to_first_result_ms": 5.0, "time_to_result_ms": 8308.82820599993, "total_latency_ms": 15.0, "wer": 0.3333333333333333}`
