# Benchmark Summary: thesis_ext_20260504T115425Z_cloud_fleurs_ja_jp_test_subset

- benchmark_profile: `benchmark/thesis_extended_cloud_matrix`
- dataset_id: `fleurs_ja_jp_test_subset`
- providers: `providers/azure_cloud, providers/google_cloud, providers/aws_cloud`
- scenario: `clean`
- execution_mode: `batch`
- noise_modes: `none`
- noise_levels: `clean`
- aggregate_scope: `provider_only`
- total_samples: `30`
- successful_samples: `29`
- failed_samples: `1`
- aggregate_samples: `30`
- corrupted_samples: `0`

## Per-Provider Summary

### providers/aws_cloud (preset: `standard`)
- samples: `10`
- successful_samples: `10`
- failed_samples: `0`
- quality_metrics: `{"cer": 0.06135986733001658, "confidence": 0.9635807130676942, "sample_accuracy": 0.1, "wer": 0.9714285714285714}`
- latency_metrics: `{"end_to_end_latency_ms": 9815.36337760117, "end_to_end_rtf": 0.6842404881601128, "inference_ms": 8923.984865000239, "per_utterance_latency_ms": 8924.073744000634, "postprocess_ms": 0.08142180085997097, "preprocess_ms": 0.007457199535565451, "provider_compute_latency_ms": 8924.073744000634, "provider_compute_rtf": 0.6226968865048114, "real_time_factor": 0.6226968865048114, "time_to_final_result_ms": 9815.36337760117, "time_to_first_result_ms": 9815.36337760117, "time_to_result_ms": 9815.36337760117, "total_latency_ms": 8924.073744000634}`
- reliability_metrics: `{"failure_rate": 0.0, "success_rate": 1.0}`
- cost_metrics: `{"estimated_cost_usd": 0.0061008}`
- cost_totals: `{"estimated_cost_usd": 0.061008}`
- estimated_cost_total_usd: `0.061008`

### providers/azure_cloud (preset: `standard`)
- samples: `10`
- successful_samples: `9`
- failed_samples: `1`
- quality_metrics: `{"cer": 0.29519071310116085, "confidence": 0.813397899, "sample_accuracy": 0.1, "wer": 0.9714285714285714}`
- latency_metrics: `{"end_to_end_latency_ms": 3896.0192398008076, "end_to_end_rtf": 0.24578176947208208, "inference_ms": 3483.227632199123, "per_utterance_latency_ms": 3483.306827600609, "postprocess_ms": 0.07078360140440054, "preprocess_ms": 0.008411800081375986, "provider_compute_latency_ms": 3483.306827600609, "provider_compute_rtf": 0.2191444117615799, "real_time_factor": 0.2191444117615799, "time_to_final_result_ms": 3896.0192398008076, "time_to_first_result_ms": 3896.0192398008076, "time_to_result_ms": 3896.0192398008076, "total_latency_ms": 3483.306827600609}`
- reliability_metrics: `{"failure_rate": 0.1, "success_rate": 0.9}`
- cost_metrics: `{"estimated_cost_usd": 0.004575599999999999}`
- cost_totals: `{"estimated_cost_usd": 0.04575599999999999}`
- estimated_cost_total_usd: `0.04575599999999999`

### providers/google_cloud (preset: `balanced`)
- samples: `10`
- successful_samples: `10`
- failed_samples: `0`
- quality_metrics: `{"cer": 0.13930348258706468, "confidence": 0.9544339835643768, "sample_accuracy": 0.0, "wer": 1.3428571428571427}`
- latency_metrics: `{"end_to_end_latency_ms": 2876.3702303018363, "end_to_end_rtf": 0.19035834898306664, "inference_ms": 2803.941580200626, "per_utterance_latency_ms": 2875.2914365017205, "postprocess_ms": 0.00012830205378122628, "preprocess_ms": 71.34972799904062, "provider_compute_latency_ms": 2875.2914365017205, "provider_compute_rtf": 0.19028498197972174, "real_time_factor": 0.19028498197972174, "time_to_final_result_ms": 2876.3702303018363, "time_to_first_result_ms": 2876.3702303018363, "time_to_result_ms": 2876.3702303018363, "total_latency_ms": 2875.2914365017205}`
- reliability_metrics: `{"failure_rate": 0.0, "success_rate": 1.0}`
- cost_metrics: `{"estimated_cost_usd": 0.0}`
- cost_totals: `{"estimated_cost_usd": 0.0}`
- estimated_cost_total_usd: `0.0`

## Noise Summary
- clean: `{"audio_duration_sec": 15.251999999999999, "cer": 0.16528468767274737, "confidence": 0.9104708652106903, "cpu_percent": 2.63690040338036, "cpu_percent_mean": 2.583305656479969, "cpu_percent_peak": 50.0, "declared_audio_duration_sec": 15.251999999999999, "duration_mismatch_sec": 0.0, "end_to_end_latency_ms": 5529.250949234604, "end_to_end_rtf": 0.3734602022050872, "estimated_cost_usd": 0.0035588, "failure_rate": 0.03333333333333333, "gpu_memory_mb": 683.8877425232339, "gpu_memory_mb_mean": 683.0796935518567, "gpu_memory_mb_peak": 728.0, "gpu_util_percent": 0.7129320715741494, "gpu_util_percent_mean": 0.8555753540408985, "gpu_util_percent_peak": 43.0, "inference_ms": 5070.384692466662, "measured_audio_duration_sec": 15.251999999999999, "memory_mb": 153.04789187106874, "memory_mb_mean": 179.11215783345642, "memory_mb_peak": 286.07421875, "per_utterance_latency_ms": 5094.2240027009875, "postprocess_ms": 0.050777901439384245, "preprocess_ms": 23.788532332885854, "provider_compute_latency_ms": 5094.2240027009875, "provider_compute_rtf": 0.344042093415371, "real_time_factor": 0.344042093415371, "sample_accuracy": 0.06666666666666667, "success_rate": 0.9666666666666667, "time_to_final_result_ms": 5529.250949234604, "time_to_first_result_ms": 5529.250949234604, "time_to_result_ms": 5529.250949234604, "total_latency_ms": 5094.2240027009875, "wer": 1.0952380952380953}`
