# Benchmark Summary: thesis_ext_20260504T115425Z_cloud_mls_spanish_test_subset

- benchmark_profile: `benchmark/thesis_extended_cloud_matrix`
- dataset_id: `mls_spanish_test_subset`
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
- quality_metrics: `{"cer": 0.01875, "confidence": 0.9511555663779155, "sample_accuracy": 0.6, "wer": 0.032171581769437}`
- latency_metrics: `{"end_to_end_latency_ms": 11089.294998098921, "end_to_end_rtf": 0.7781566292716908, "inference_ms": 10176.41843570018, "per_utterance_latency_ms": 10176.507899699209, "postprocess_ms": 0.08267219964182004, "preprocess_ms": 0.0067917993874289095, "provider_compute_latency_ms": 10176.507899699209, "provider_compute_rtf": 0.7135124009537968, "real_time_factor": 0.7135124009537968, "time_to_final_result_ms": 11089.294998098921, "time_to_first_result_ms": 11089.294998098921, "time_to_result_ms": 11089.294998098921, "total_latency_ms": 10176.507899699209}`
- reliability_metrics: `{"failure_rate": 0.0, "success_rate": 1.0}`
- cost_metrics: `{"estimated_cost_usd": 0.0057428}`
- cost_totals: `{"estimated_cost_usd": 0.057428}`
- estimated_cost_total_usd: `0.057428`

### providers/azure_cloud (preset: `standard`)
- samples: `10`
- successful_samples: `10`
- failed_samples: `0`
- quality_metrics: `{"cer": 0.166875, "confidence": 0.889033957, "sample_accuracy": 0.3, "wer": 0.1581769436997319}`
- latency_metrics: `{"end_to_end_latency_ms": 4517.577155098843, "end_to_end_rtf": 0.3136867310141596, "inference_ms": 4301.772130098107, "per_utterance_latency_ms": 4301.875060297607, "postprocess_ms": 0.09352759952889755, "preprocess_ms": 0.009402599971508607, "provider_compute_latency_ms": 4301.875060297607, "provider_compute_rtf": 0.2983887451781434, "real_time_factor": 0.2983887451781434, "time_to_final_result_ms": 4517.577155098843, "time_to_first_result_ms": 4517.577155098843, "time_to_result_ms": 4517.577155098843, "total_latency_ms": 4301.875060297607}`
- reliability_metrics: `{"failure_rate": 0.0, "success_rate": 1.0}`
- cost_metrics: `{"estimated_cost_usd": 0.0043070999999999995}`
- cost_totals: `{"estimated_cost_usd": 0.043071}`
- estimated_cost_total_usd: `0.043071`

### providers/google_cloud (preset: `balanced`)
- samples: `10`
- successful_samples: `10`
- failed_samples: `0`
- quality_metrics: `{"cer": 0.01875, "confidence": 0.972483092546463, "sample_accuracy": 0.3, "wer": 0.04289544235924933}`
- latency_metrics: `{"end_to_end_latency_ms": 3108.9471896004397, "end_to_end_rtf": 0.21623941292716092, "inference_ms": 3029.665727101383, "per_utterance_latency_ms": 3107.641571401473, "postprocess_ms": 0.00013630051398649812, "preprocess_ms": 77.97570799957612, "provider_compute_latency_ms": 3107.641571401473, "provider_compute_rtf": 0.21614922449344648, "real_time_factor": 0.21614922449344648, "time_to_final_result_ms": 3108.9471896004397, "time_to_first_result_ms": 3108.9471896004397, "time_to_result_ms": 3108.9471896004397, "total_latency_ms": 3107.641571401473}`
- reliability_metrics: `{"failure_rate": 0.0, "success_rate": 1.0}`
- cost_metrics: `{"estimated_cost_usd": 0.0}`
- cost_totals: `{"estimated_cost_usd": 0.0}`
- estimated_cost_total_usd: `0.0`

## Noise Summary
- clean: `{"audio_duration_sec": 14.357, "cer": 0.068125, "confidence": 0.9375575386414595, "cpu_percent": 5.073588649550502, "cpu_percent_mean": 5.09282300280471, "cpu_percent_peak": 57.0, "declared_audio_duration_sec": 14.357, "duration_mismatch_sec": 0.0, "end_to_end_latency_ms": 6238.606447599402, "end_to_end_rtf": 0.43602759107100375, "estimated_cost_usd": 0.0033499666666666665, "failure_rate": 0.0, "gpu_memory_mb": 732.5501130842019, "gpu_memory_mb_mean": 734.5303129039405, "gpu_memory_mb_peak": 878.0, "gpu_util_percent": 8.316781032089535, "gpu_util_percent_mean": 8.492838462370468, "gpu_util_percent_peak": 58.0, "inference_ms": 5835.952097633223, "measured_audio_duration_sec": 14.357, "memory_mb": 151.5936803522819, "memory_mb_mean": 177.75929192144966, "memory_mb_peak": 284.19140625, "per_utterance_latency_ms": 5862.008177132763, "postprocess_ms": 0.058778699894901365, "preprocess_ms": 25.997300799645018, "provider_compute_latency_ms": 5862.008177132763, "provider_compute_rtf": 0.40935012354179556, "real_time_factor": 0.40935012354179556, "sample_accuracy": 0.4, "success_rate": 1.0, "time_to_final_result_ms": 6238.606447599402, "time_to_first_result_ms": 6238.606447599402, "time_to_result_ms": 6238.606447599402, "total_latency_ms": 5862.008177132763, "wer": 0.0777479892761394}`
