# Benchmark Summary: bench_cost_run

- benchmark_profile: `bench`
- dataset_id: `bench_dataset`
- providers: `providers/fake_cost`
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

### providers/fake_cost (preset: `standard`)
- samples: `1`
- successful_samples: `1`
- failed_samples: `0`
- quality_metrics: `{"confidence": 0.92, "wer": 0.0}`
- latency_metrics: `{"end_to_end_latency_ms": 15.0, "end_to_end_rtf": 0.0018054886856042369, "inference_ms": 0.0, "per_utterance_latency_ms": 15.0, "postprocess_ms": 0.0, "preprocess_ms": 0.0, "provider_compute_latency_ms": 15.0, "provider_compute_rtf": 0.0018054886856042369, "real_time_factor": 0.0018054886856042369, "time_to_final_result_ms": 15.0, "time_to_first_result_ms": 15.0, "time_to_result_ms": 15.0, "total_latency_ms": 15.0}`
- cost_metrics: `{"estimated_cost_usd": 0.06923333333333333}`
- cost_totals: `{"estimated_cost_usd": 0.06923333333333333}`
- estimated_cost_total_usd: `0.06923333333333333`

## Noise Summary
- clean: `{"audio_duration_sec": 8.308, "confidence": 0.92, "declared_audio_duration_sec": 30.0, "duration_mismatch_sec": 21.692, "end_to_end_latency_ms": 15.0, "end_to_end_rtf": 0.0018054886856042369, "estimated_cost_usd": 0.06923333333333333, "inference_ms": 0.0, "measured_audio_duration_sec": 8.308, "per_utterance_latency_ms": 15.0, "postprocess_ms": 0.0, "preprocess_ms": 0.0, "provider_compute_latency_ms": 15.0, "provider_compute_rtf": 0.0018054886856042369, "real_time_factor": 0.0018054886856042369, "time_to_final_result_ms": 15.0, "time_to_first_result_ms": 15.0, "time_to_result_ms": 15.0, "total_latency_ms": 15.0, "wer": 0.0}`
