# Benchmark Summary: bench_20260427T141016Z_2555b592

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
- latency_metrics: `{"end_to_end_latency_ms": 5255.891610000617, "end_to_end_rtf": 0.6326301889745567, "inference_ms": 669.412799001293, "per_utterance_latency_ms": 5255.533068002478, "postprocess_ms": 0.09478700121690053, "preprocess_ms": 4586.025481999968, "provider_compute_latency_ms": 5255.533068002478, "provider_compute_rtf": 0.6325870327398264, "real_time_factor": 0.6325870327398264, "time_to_final_result_ms": 5255.891610000617, "time_to_first_result_ms": 5255.891610000617, "time_to_result_ms": 5255.891610000617, "total_latency_ms": 5255.533068002478}`
- reliability_metrics: `{"failure_rate": 0.0, "success_rate": 1.0}`
- cost_metrics: `{"estimated_cost_usd": 0.0}`
- cost_totals: `{"estimated_cost_usd": 0.0}`
- estimated_cost_total_usd: `0.0`

## Noise Summary
- clean: `{"audio_duration_sec": 8.308, "cer": 0.0, "confidence": 0.6638665311297195, "cpu_percent": 17.51521739130435, "cpu_percent_mean": 17.51521739130435, "cpu_percent_peak": 76.4, "declared_audio_duration_sec": 8.308, "duration_mismatch_sec": 0.0, "end_to_end_latency_ms": 5255.891610000617, "end_to_end_rtf": 0.6326301889745567, "estimated_cost_usd": 0.0, "failure_rate": 0.0, "gpu_memory_mb": 684.0555555555555, "gpu_memory_mb_mean": 684.0555555555555, "gpu_memory_mb_peak": 732.0, "gpu_util_percent": 30.27777777777778, "gpu_util_percent_mean": 30.27777777777778, "gpu_util_percent_peak": 44.0, "inference_ms": 669.412799001293, "measured_audio_duration_sec": 8.308, "memory_mb": 635.0187669836956, "memory_mb_mean": 635.0187669836956, "memory_mb_peak": 918.7578125, "per_utterance_latency_ms": 5255.533068002478, "postprocess_ms": 0.09478700121690053, "preprocess_ms": 4586.025481999968, "provider_compute_latency_ms": 5255.533068002478, "provider_compute_rtf": 0.6325870327398264, "real_time_factor": 0.6325870327398264, "sample_accuracy": 1.0, "success_rate": 1.0, "time_to_final_result_ms": 5255.891610000617, "time_to_first_result_ms": 5255.891610000617, "time_to_result_ms": 5255.891610000617, "total_latency_ms": 5255.533068002478, "wer": 0.0}`
