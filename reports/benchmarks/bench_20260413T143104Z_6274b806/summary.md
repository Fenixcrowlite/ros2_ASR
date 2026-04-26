# Benchmark Summary: bench_20260413T143104Z_6274b806

- benchmark_profile: `cloud_comparison`
- dataset_id: `sample_dataset`
- providers: `providers/aws_cloud, providers/azure_cloud, providers/google_cloud, providers/vosk_local, providers/whisper_local`
- scenario: `clean_baseline`
- execution_mode: `batch`
- noise_modes: `none`
- noise_levels: `clean`
- aggregate_scope: `provider_only`
- total_samples: `5`
- successful_samples: `5`
- failed_samples: `0`
- aggregate_samples: `5`
- corrupted_samples: `0`

## Per-Provider Summary

### providers/aws_cloud (preset: `standard`)
- samples: `1`
- successful_samples: `1`
- failed_samples: `0`
- quality_metrics: `{"cer": 0.0, "confidence": 0.965, "sample_accuracy": 0.0, "wer": 1.0}`
- latency_metrics: `{"end_to_end_latency_ms": 13047.526213999958, "end_to_end_rtf": 1.5704773969667738, "inference_ms": 9227.165935000015, "per_utterance_latency_ms": 9227.637322000191, "postprocess_ms": 0.4461540000875175, "preprocess_ms": 0.02523300008760998, "provider_compute_latency_ms": 9227.637322000191, "provider_compute_rtf": 1.1106929853153817, "real_time_factor": 1.1106929853153817, "time_to_final_result_ms": 13047.526213999958, "time_to_first_result_ms": 13047.526213999958, "time_to_result_ms": 13047.526213999958, "total_latency_ms": 9227.637322000191}`
- reliability_metrics: `{"failure_rate": 0.0, "success_rate": 1.0}`
- cost_metrics: `{"estimated_cost_usd": 0.0033231999999999997}`
- cost_totals: `{"estimated_cost_usd": 0.0033231999999999997}`
- estimated_cost_total_usd: `0.0033231999999999997`

### providers/azure_cloud (preset: `standard`)
- samples: `1`
- successful_samples: `1`
- failed_samples: `0`
- quality_metrics: `{"cer": 0.6666666666666666, "confidence": 0.8921391, "sample_accuracy": 0.0, "wer": 0.6666666666666666}`
- latency_metrics: `{"end_to_end_latency_ms": 2905.3281929999457, "end_to_end_rtf": 0.34970247869522697, "inference_ms": 1713.034246999996, "per_utterance_latency_ms": 1847.3215469999786, "postprocess_ms": 0.10416800000712101, "preprocess_ms": 134.18313199997556, "provider_compute_latency_ms": 1847.3215469999786, "provider_compute_rtf": 0.2223545434520918, "real_time_factor": 0.2223545434520918, "time_to_final_result_ms": 2905.3281929999457, "time_to_first_result_ms": 2905.3281929999457, "time_to_result_ms": 2905.3281929999457, "total_latency_ms": 1847.3215469999786}`
- reliability_metrics: `{"failure_rate": 0.0, "success_rate": 1.0}`
- cost_metrics: `{"estimated_cost_usd": 0.0024923999999999997}`
- cost_totals: `{"estimated_cost_usd": 0.0024923999999999997}`
- estimated_cost_total_usd: `0.0024923999999999997`

### providers/google_cloud (preset: `balanced`)
- samples: `1`
- successful_samples: `1`
- failed_samples: `0`
- quality_metrics: `{"cer": 0.13333333333333333, "confidence": 0.25548477719227475, "sample_accuracy": 0.0, "wer": 0.3333333333333333}`
- latency_metrics: `{"end_to_end_latency_ms": 4349.080607000019, "end_to_end_rtf": 0.5234810552479561, "inference_ms": 2231.681987999991, "per_utterance_latency_ms": 4347.971927999993, "postprocess_ms": 0.0004309999894758221, "preprocess_ms": 2116.289509000012, "provider_compute_latency_ms": 4347.971927999993, "provider_compute_rtf": 0.5233476080885885, "real_time_factor": 0.5233476080885885, "time_to_final_result_ms": 4349.080607000019, "time_to_first_result_ms": 4349.080607000019, "time_to_result_ms": 4349.080607000019, "total_latency_ms": 4347.971927999993}`
- reliability_metrics: `{"failure_rate": 0.0, "success_rate": 1.0}`
- cost_metrics: `{"estimated_cost_usd": 0.0}`
- cost_totals: `{"estimated_cost_usd": 0.0}`
- estimated_cost_total_usd: `0.0`

### providers/vosk_local (preset: `en_small`)
- samples: `1`
- successful_samples: `1`
- failed_samples: `0`
- quality_metrics: `{"cer": 3.4, "confidence": 0.9069189333333333, "sample_accuracy": 0.0, "wer": 5.0}`
- latency_metrics: `{"end_to_end_latency_ms": 1916.9433170000048, "end_to_end_rtf": 0.230734631319211, "inference_ms": 1211.2422589999596, "per_utterance_latency_ms": 1908.94979899997, "postprocess_ms": 0.08016699996460375, "preprocess_ms": 697.6273730000457, "provider_compute_latency_ms": 1908.94979899997, "provider_compute_rtf": 0.22977248423206187, "real_time_factor": 0.22977248423206187, "time_to_final_result_ms": 1916.9433170000048, "time_to_first_result_ms": 1916.9433170000048, "time_to_result_ms": 1916.9433170000048, "total_latency_ms": 1908.94979899997}`
- reliability_metrics: `{"failure_rate": 0.0, "success_rate": 1.0}`
- cost_metrics: `{"estimated_cost_usd": 0.0}`
- cost_totals: `{"estimated_cost_usd": 0.0}`
- estimated_cost_total_usd: `0.0`

### providers/whisper_local (preset: `light`)
- samples: `1`
- successful_samples: `1`
- failed_samples: `0`
- quality_metrics: `{"cer": 0.0, "confidence": 0.6638665311297195, "sample_accuracy": 1.0, "wer": 0.0}`
- latency_metrics: `{"end_to_end_latency_ms": 3042.088665000051, "end_to_end_rtf": 0.366163777684166, "inference_ms": 504.3393849999802, "per_utterance_latency_ms": 3041.7995299999347, "postprocess_ms": 0.04954500002440909, "preprocess_ms": 2537.41059999993, "provider_compute_latency_ms": 3041.7995299999347, "provider_compute_rtf": 0.36612897568607783, "real_time_factor": 0.36612897568607783, "time_to_final_result_ms": 3042.088665000051, "time_to_first_result_ms": 3042.088665000051, "time_to_result_ms": 3042.088665000051, "total_latency_ms": 3041.7995299999347}`
- reliability_metrics: `{"failure_rate": 0.0, "success_rate": 1.0}`
- cost_metrics: `{"estimated_cost_usd": 0.0}`
- cost_totals: `{"estimated_cost_usd": 0.0}`
- estimated_cost_total_usd: `0.0`

## Noise Summary
- clean: `{"audio_duration_sec": 8.308, "cer": 0.84, "confidence": 0.7366818683310655, "cpu_percent": 7.9139226539298715, "cpu_percent_mean": 6.473061777499977, "cpu_percent_peak": 71.0, "declared_audio_duration_sec": 8.308, "duration_mismatch_sec": 0.0, "end_to_end_latency_ms": 5052.193399199996, "end_to_end_rtf": 0.6081118679826668, "estimated_cost_usd": 0.00116312, "failure_rate": 0.0, "gpu_memory_mb": 457.28064935064936, "gpu_memory_mb_mean": 461.17426287708207, "gpu_memory_mb_peak": 510.0, "gpu_util_percent": 10.708138528138528, "gpu_util_percent_mean": 10.533918798907825, "gpu_util_percent_peak": 61.0, "inference_ms": 2977.4927627999887, "measured_audio_duration_sec": 8.308, "memory_mb": 296.94954847437424, "memory_mb_mean": 220.597336597994, "memory_mb_peak": 1056.2734375, "per_utterance_latency_ms": 4074.7360252000135, "postprocess_ms": 0.13609300001462543, "preprocess_ms": 1097.1071694000102, "provider_compute_latency_ms": 4074.7360252000135, "provider_compute_rtf": 0.49045931935484033, "real_time_factor": 0.49045931935484033, "sample_accuracy": 0.2, "success_rate": 1.0, "time_to_final_result_ms": 5052.193399199996, "time_to_first_result_ms": 5052.193399199996, "time_to_result_ms": 5052.193399199996, "total_latency_ms": 4074.7360252000135, "wer": 1.4}`
