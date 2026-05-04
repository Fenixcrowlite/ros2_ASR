# Benchmark Summary: thesis_ext_20260504T115425Z_cloud_librispeech_test_clean_subset

- benchmark_profile: `benchmark/thesis_extended_cloud_matrix`
- dataset_id: `librispeech_test_clean_subset`
- providers: `providers/azure_cloud, providers/google_cloud, providers/aws_cloud`
- scenario: `clean`
- execution_mode: `batch`
- noise_modes: `none`
- noise_levels: `clean`
- aggregate_scope: `provider_only`
- total_samples: `30`
- successful_samples: `30`
- failed_samples: `0`
- aggregate_samples: `30`
- corrupted_samples: `0`

## Per-Provider Summary

### providers/aws_cloud (preset: `standard`)
- samples: `10`
- successful_samples: `10`
- failed_samples: `0`
- quality_metrics: `{"cer": 0.0026595744680851063, "confidence": 0.9994772183457796, "sample_accuracy": 0.9, "wer": 0.00398406374501992}`
- latency_metrics: `{"end_to_end_latency_ms": 9822.416417299974, "end_to_end_rtf": 1.5328568152225965, "inference_ms": 8943.61527209985, "per_utterance_latency_ms": 8943.711088700366, "postprocess_ms": 0.0886235007783398, "preprocess_ms": 0.0071930997364688665, "provider_compute_latency_ms": 8943.711088700366, "provider_compute_rtf": 1.3907929864563497, "real_time_factor": 1.3907929864563497, "time_to_final_result_ms": 9822.416417299974, "time_to_first_result_ms": 9822.416417299974, "time_to_result_ms": 9822.416417299974, "total_latency_ms": 8943.711088700366}`
- reliability_metrics: `{"failure_rate": 0.0, "success_rate": 1.0}`
- cost_metrics: `{"estimated_cost_usd": 0.003661}`
- cost_totals: `{"estimated_cost_usd": 0.036610000000000004}`
- estimated_cost_total_usd: `0.036610000000000004`

### providers/azure_cloud (preset: `standard`)
- samples: `10`
- successful_samples: `10`
- failed_samples: `0`
- quality_metrics: `{"cer": 0.0026595744680851063, "confidence": 0.856182823, "sample_accuracy": 0.9, "wer": 0.00398406374501992}`
- latency_metrics: `{"end_to_end_latency_ms": 3305.4919971022173, "end_to_end_rtf": 0.35625044859177707, "inference_ms": 3060.9532235022925, "per_utterance_latency_ms": 3061.040198800765, "postprocess_ms": 0.07984189869603142, "preprocess_ms": 0.00713339977664873, "provider_compute_latency_ms": 3061.040198800765, "provider_compute_rtf": 0.31594756985019695, "real_time_factor": 0.31594756985019695, "time_to_final_result_ms": 3305.4919971022173, "time_to_first_result_ms": 3305.4919971022173, "time_to_result_ms": 3305.4919971022173, "total_latency_ms": 3061.040198800765}`
- reliability_metrics: `{"failure_rate": 0.0, "success_rate": 1.0}`
- cost_metrics: `{"estimated_cost_usd": 0.00274575}`
- cost_totals: `{"estimated_cost_usd": 0.027457499999999996}`
- estimated_cost_total_usd: `0.027457499999999996`

### providers/google_cloud (preset: `balanced`)
- samples: `10`
- successful_samples: `10`
- failed_samples: `0`
- quality_metrics: `{"cer": 0.014184397163120567, "confidence": 0.9707605898380279, "sample_accuracy": 0.6, "wer": 0.0199203187250996}`
- latency_metrics: `{"end_to_end_latency_ms": 1975.2822747999744, "end_to_end_rtf": 0.2430732512968379, "inference_ms": 1901.3275676996273, "per_utterance_latency_ms": 1974.282244299684, "postprocess_ms": 0.00018830105545930564, "preprocess_ms": 72.95448829900124, "provider_compute_latency_ms": 1974.282244299684, "provider_compute_rtf": 0.24293235298838345, "real_time_factor": 0.24293235298838345, "time_to_final_result_ms": 1975.2822747999744, "time_to_first_result_ms": 1975.2822747999744, "time_to_result_ms": 1975.2822747999744, "total_latency_ms": 1974.282244299684}`
- reliability_metrics: `{"failure_rate": 0.0, "success_rate": 1.0}`
- cost_metrics: `{"estimated_cost_usd": 0.0}`
- cost_totals: `{"estimated_cost_usd": 0.0}`
- estimated_cost_total_usd: `0.0`

## Noise Summary
- clean: `{"audio_duration_sec": 9.1525, "cer": 0.0065011820330969266, "confidence": 0.9421402103946025, "cpu_percent": 5.686729272937394, "cpu_percent_mean": 5.390100228259051, "cpu_percent_peak": 100.0, "declared_audio_duration_sec": 9.1525, "duration_mismatch_sec": 0.0, "end_to_end_latency_ms": 5034.396896400722, "end_to_end_rtf": 0.7107268383704038, "estimated_cost_usd": 0.002135583333333333, "failure_rate": 0.0, "gpu_memory_mb": 663.5648378146908, "gpu_memory_mb_mean": 660.2360514029907, "gpu_memory_mb_peak": 697.0, "gpu_util_percent": 4.5853965560583205, "gpu_util_percent_mean": 5.343636343631246, "gpu_util_percent_peak": 38.0, "inference_ms": 4635.2986877672565, "measured_audio_duration_sec": 9.1525, "memory_mb": 152.30334157712105, "memory_mb_mean": 184.811210175894, "memory_mb_peak": 285.52734375, "per_utterance_latency_ms": 4659.677843933605, "postprocess_ms": 0.05621790017661018, "preprocess_ms": 24.32293826617145, "provider_compute_latency_ms": 4659.677843933605, "provider_compute_rtf": 0.6498909697649766, "real_time_factor": 0.6498909697649766, "sample_accuracy": 0.8, "success_rate": 1.0, "time_to_final_result_ms": 5034.396896400722, "time_to_first_result_ms": 5034.396896400722, "time_to_result_ms": 5034.396896400722, "total_latency_ms": 4659.677843933605, "wer": 0.009296148738379814}`
