# Benchmark Summary: bench_component_run

- benchmark_profile: `bench`
- dataset_id: `bench_dataset`
- providers: `providers/fake_bench`
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

### providers/fake_bench
- samples: `1`
- successful_samples: `1`
- failed_samples: `0`
- quality_metrics: `{"cer": 0.0, "confidence": 0.92, "sample_accuracy": 1.0, "wer": 0.0}`
- latency_metrics: `{"end_to_end_latency_ms": 15.0, "end_to_end_rtf": 0.0018054886856042369, "inference_ms": 0.0, "per_utterance_latency_ms": 15.0, "postprocess_ms": 0.0, "preprocess_ms": 0.0, "provider_compute_latency_ms": 15.0, "provider_compute_rtf": 0.0018054886856042369, "real_time_factor": 0.0018054886856042369, "time_to_final_result_ms": 15.0, "time_to_first_result_ms": 15.0, "time_to_result_ms": 15.0, "total_latency_ms": 15.0}`
- reliability_metrics: `{"success_rate": 1.0}`
- cost_metrics: `{"estimated_cost_usd": 0.0}`
- cost_totals: `{"estimated_cost_usd": 0.0}`
- estimated_cost_total_usd: `0.0`

## Noise Summary
- clean: `{"audio_duration_sec": 8.308, "cer": 0.0, "confidence": 0.92, "duration_mismatch_sec": 0.0, "end_to_end_latency_ms": 15.0, "end_to_end_rtf": 0.0018054886856042369, "estimated_cost_usd": 0.0, "inference_ms": 0.0, "measured_audio_duration_sec": 8.308, "per_utterance_latency_ms": 15.0, "postprocess_ms": 0.0, "preprocess_ms": 0.0, "provider_compute_latency_ms": 15.0, "provider_compute_rtf": 0.0018054886856042369, "real_time_factor": 0.0018054886856042369, "sample_accuracy": 1.0, "success_rate": 1.0, "time_to_final_result_ms": 15.0, "time_to_first_result_ms": 15.0, "time_to_result_ms": 15.0, "total_latency_ms": 15.0, "wer": 0.0}`
