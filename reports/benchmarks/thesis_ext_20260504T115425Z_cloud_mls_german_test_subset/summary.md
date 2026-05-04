# Benchmark Summary: thesis_ext_20260504T115425Z_cloud_mls_german_test_subset

- benchmark_profile: `benchmark/thesis_extended_cloud_matrix`
- dataset_id: `mls_german_test_subset`
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
- quality_metrics: `{"cer": 0.009283819628647215, "confidence": 0.9366121471850116, "sample_accuracy": 0.5, "wer": 0.03367003367003367}`
- latency_metrics: `{"end_to_end_latency_ms": 9763.152175900177, "end_to_end_rtf": 0.5954576107292718, "inference_ms": 8912.549425300676, "per_utterance_latency_ms": 8912.635250700987, "postprocess_ms": 0.07902340003056452, "preprocess_ms": 0.006802000280003995, "provider_compute_latency_ms": 8912.635250700987, "provider_compute_rtf": 0.5436113096851354, "real_time_factor": 0.5436113096851354, "time_to_final_result_ms": 9763.152175900177, "time_to_first_result_ms": 9763.152175900177, "time_to_result_ms": 9763.152175900177, "total_latency_ms": 8912.635250700987}`
- reliability_metrics: `{"failure_rate": 0.0, "success_rate": 1.0}`
- cost_metrics: `{"estimated_cost_usd": 0.0067424}`
- cost_totals: `{"estimated_cost_usd": 0.067424}`
- estimated_cost_total_usd: `0.067424`

### providers/azure_cloud (preset: `standard`)
- samples: `10`
- successful_samples: `10`
- failed_samples: `0`
- quality_metrics: `{"cer": 0.5311671087533156, "confidence": 0.858583565, "sample_accuracy": 0.0, "wer": 0.5589225589225589}`
- latency_metrics: `{"end_to_end_latency_ms": 2522.572513299383, "end_to_end_rtf": 0.1495338929703925, "inference_ms": 2231.4231041011226, "per_utterance_latency_ms": 2231.521210099163, "postprocess_ms": 0.09020619909279048, "preprocess_ms": 0.007899798947619274, "provider_compute_latency_ms": 2231.521210099163, "provider_compute_rtf": 0.13280673376670055, "real_time_factor": 0.13280673376670055, "time_to_final_result_ms": 2522.572513299383, "time_to_first_result_ms": 2522.572513299383, "time_to_result_ms": 2522.572513299383, "total_latency_ms": 2231.521210099163}`
- reliability_metrics: `{"failure_rate": 0.0, "success_rate": 1.0}`
- cost_metrics: `{"estimated_cost_usd": 0.005056799999999999}`
- cost_totals: `{"estimated_cost_usd": 0.050567999999999995}`
- estimated_cost_total_usd: `0.050567999999999995`

### providers/google_cloud (preset: `balanced`)
- samples: `10`
- successful_samples: `10`
- failed_samples: `0`
- quality_metrics: `{"cer": 0.020557029177718834, "confidence": 0.9484062016010284, "sample_accuracy": 0.3, "wer": 0.07744107744107744}`
- latency_metrics: `{"end_to_end_latency_ms": 3979.023227500147, "end_to_end_rtf": 0.2371128091015781, "inference_ms": 3896.2212543985515, "per_utterance_latency_ms": 3977.9839710972738, "postprocess_ms": 0.00015339901437982917, "preprocess_ms": 81.76256329970784, "provider_compute_latency_ms": 3977.9839710972738, "provider_compute_rtf": 0.2370511818731779, "real_time_factor": 0.2370511818731779, "time_to_final_result_ms": 3979.023227500147, "time_to_first_result_ms": 3979.023227500147, "time_to_result_ms": 3979.023227500147, "total_latency_ms": 3977.9839710972738}`
- reliability_metrics: `{"failure_rate": 0.0, "success_rate": 1.0}`
- cost_metrics: `{"estimated_cost_usd": 0.0}`
- cost_totals: `{"estimated_cost_usd": 0.0}`
- estimated_cost_total_usd: `0.0`

## Noise Summary
- clean: `{"audio_duration_sec": 16.856, "cer": 0.1870026525198939, "confidence": 0.9145339712620134, "cpu_percent": 6.089253727823768, "cpu_percent_mean": 5.7129724391376735, "cpu_percent_peak": 100.0, "declared_audio_duration_sec": 16.856, "duration_mismatch_sec": 0.0, "end_to_end_latency_ms": 5421.582638899902, "end_to_end_rtf": 0.3273681042670808, "estimated_cost_usd": 0.003933066666666667, "failure_rate": 0.0, "gpu_memory_mb": 698.478236000111, "gpu_memory_mb_mean": 699.1380370568265, "gpu_memory_mb_peak": 788.0, "gpu_util_percent": 8.605581085581086, "gpu_util_percent_mean": 9.78889135919274, "gpu_util_percent_peak": 71.0, "inference_ms": 5013.39792793345, "measured_audio_duration_sec": 16.856, "memory_mb": 152.18399436004069, "memory_mb_mean": 183.39018711632468, "memory_mb_peak": 281.6953125, "per_utterance_latency_ms": 5040.713477299141, "postprocess_ms": 0.056460999379244946, "preprocess_ms": 27.25908836631182, "provider_compute_latency_ms": 5040.713477299141, "provider_compute_rtf": 0.3044897417750046, "real_time_factor": 0.3044897417750046, "sample_accuracy": 0.26666666666666666, "success_rate": 1.0, "time_to_final_result_ms": 5421.582638899902, "time_to_first_result_ms": 5421.582638899902, "time_to_result_ms": 5421.582638899902, "total_latency_ms": 5040.713477299141, "wer": 0.22334455667789002}`
