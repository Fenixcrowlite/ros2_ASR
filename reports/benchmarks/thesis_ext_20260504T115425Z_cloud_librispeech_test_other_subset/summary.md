# Benchmark Summary: thesis_ext_20260504T115425Z_cloud_librispeech_test_other_subset

- benchmark_profile: `benchmark/thesis_extended_cloud_matrix`
- dataset_id: `librispeech_test_other_subset`
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
- quality_metrics: `{"cer": 0.013138686131386862, "confidence": 0.9965297060572278, "sample_accuracy": 0.5, "wer": 0.03550295857988166}`
- latency_metrics: `{"end_to_end_latency_ms": 9435.44482680154, "end_to_end_rtf": 2.473928829398595, "inference_ms": 8675.228365801013, "per_utterance_latency_ms": 8675.313538200862, "postprocess_ms": 0.07865109873819165, "preprocess_ms": 0.006521301111206412, "provider_compute_latency_ms": 8675.313538200862, "provider_compute_rtf": 2.276161805182834, "real_time_factor": 2.276161805182834, "time_to_final_result_ms": 9435.44482680154, "time_to_first_result_ms": 9435.44482680154, "time_to_result_ms": 9435.44482680154, "total_latency_ms": 8675.313538200862}`
- reliability_metrics: `{"failure_rate": 0.0, "success_rate": 1.0}`
- cost_metrics: `{"estimated_cost_usd": 0.0020246}`
- cost_totals: `{"estimated_cost_usd": 0.020246}`
- estimated_cost_total_usd: `0.020246`

### providers/azure_cloud (preset: `standard`)
- samples: `10`
- successful_samples: `10`
- failed_samples: `0`
- quality_metrics: `{"cer": 0.042335766423357665, "confidence": 0.824648226, "sample_accuracy": 0.4, "wer": 0.07692307692307693}`
- latency_metrics: `{"end_to_end_latency_ms": 1859.0029484003026, "end_to_end_rtf": 0.3999034609201542, "inference_ms": 1609.1127118997974, "per_utterance_latency_ms": 1609.1976837982656, "postprocess_ms": 0.07742889865767211, "preprocess_ms": 0.007542999810539186, "provider_compute_latency_ms": 1609.1976837982656, "provider_compute_rtf": 0.3329333563252714, "real_time_factor": 0.3329333563252714, "time_to_final_result_ms": 1859.0029484003026, "time_to_first_result_ms": 1859.0029484003026, "time_to_result_ms": 1859.0029484003026, "total_latency_ms": 1609.1976837982656}`
- reliability_metrics: `{"failure_rate": 0.0, "success_rate": 1.0}`
- cost_metrics: `{"estimated_cost_usd": 0.00151845}`
- cost_totals: `{"estimated_cost_usd": 0.015184499999999998}`
- estimated_cost_total_usd: `0.015184499999999998`

### providers/google_cloud (preset: `balanced`)
- samples: `10`
- successful_samples: `10`
- failed_samples: `0`
- quality_metrics: `{"cer": 0.049635036496350364, "confidence": 0.9303343564271926, "sample_accuracy": 0.3, "wer": 0.11242603550295859}`
- latency_metrics: `{"end_to_end_latency_ms": 1368.825226699846, "end_to_end_rtf": 0.31124133713558055, "inference_ms": 1290.9477453984437, "per_utterance_latency_ms": 1368.013990198233, "postprocess_ms": 0.00015229888958856463, "preprocess_ms": 77.06609250089969, "provider_compute_latency_ms": 1368.013990198233, "provider_compute_rtf": 0.31104750192484204, "real_time_factor": 0.31104750192484204, "time_to_final_result_ms": 1368.825226699846, "time_to_first_result_ms": 1368.825226699846, "time_to_result_ms": 1368.825226699846, "total_latency_ms": 1368.013990198233}`
- reliability_metrics: `{"failure_rate": 0.0, "success_rate": 1.0}`
- cost_metrics: `{"estimated_cost_usd": 0.0}`
- cost_totals: `{"estimated_cost_usd": 0.0}`
- estimated_cost_total_usd: `0.0`

## Noise Summary
- clean: `{"audio_duration_sec": 5.0615, "cer": 0.035036496350364967, "confidence": 0.9171707628281401, "cpu_percent": 5.241660363074399, "cpu_percent_mean": 5.880462954122882, "cpu_percent_peak": 50.0, "declared_audio_duration_sec": 5.0615, "duration_mismatch_sec": 0.0, "end_to_end_latency_ms": 4221.091000633896, "end_to_end_rtf": 1.0616912091514432, "estimated_cost_usd": 0.0011810166666666668, "failure_rate": 0.0, "gpu_memory_mb": 681.6983704388659, "gpu_memory_mb_mean": 707.2533845195653, "gpu_memory_mb_peak": 788.0, "gpu_util_percent": 8.854903993855606, "gpu_util_percent_mean": 7.332486701778148, "gpu_util_percent_peak": 75.0, "inference_ms": 3858.429607699751, "measured_audio_duration_sec": 5.0615, "memory_mb": 149.19689300053065, "memory_mb_mean": 193.2133778620831, "memory_mb_peak": 278.94921875, "per_utterance_latency_ms": 3884.1750707324536, "postprocess_ms": 0.052077432095150776, "preprocess_ms": 25.693385600607144, "provider_compute_latency_ms": 3884.1750707324536, "provider_compute_rtf": 0.9733808878109823, "real_time_factor": 0.9733808878109823, "sample_accuracy": 0.4, "success_rate": 1.0, "time_to_final_result_ms": 4221.091000633896, "time_to_first_result_ms": 4221.091000633896, "time_to_result_ms": 4221.091000633896, "total_latency_ms": 3884.1750707324536, "wer": 0.07495069033530571}`
