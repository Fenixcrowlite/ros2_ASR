# Benchmark Summary: thesis_ext_20260504T115425Z_cloud_fleurs_sk_sk_test_subset

- benchmark_profile: `benchmark/thesis_extended_cloud_matrix`
- dataset_id: `fleurs_sk_sk_test_subset`
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
- quality_metrics: `{"cer": 0.013888888888888888, "confidence": 0.9373888966968106, "sample_accuracy": 0.4, "wer": 0.08974358974358974}`
- latency_metrics: `{"end_to_end_latency_ms": 9598.675470700982, "end_to_end_rtf": 1.0453068304627398, "inference_ms": 8728.674167297868, "per_utterance_latency_ms": 8728.768852799112, "postprocess_ms": 0.0871795004059095, "preprocess_ms": 0.007506000838475302, "provider_compute_latency_ms": 8728.768852799112, "provider_compute_rtf": 0.9521003466498418, "real_time_factor": 0.9521003466498418, "time_to_final_result_ms": 9598.675470700982, "time_to_first_result_ms": 9598.675470700982, "time_to_result_ms": 9598.675470700982, "total_latency_ms": 8728.768852799112}`
- reliability_metrics: `{"failure_rate": 0.0, "success_rate": 1.0}`
- cost_metrics: `{"estimated_cost_usd": 0.0039624000000000005}`
- cost_totals: `{"estimated_cost_usd": 0.039624000000000006}`
- estimated_cost_total_usd: `0.039624000000000006`

### providers/azure_cloud (preset: `standard`)
- samples: `10`
- successful_samples: `10`
- failed_samples: `0`
- quality_metrics: `{"cer": 0.03125, "confidence": 0.926990865, "sample_accuracy": 0.6, "wer": 0.08333333333333333}`
- latency_metrics: `{"end_to_end_latency_ms": 2906.5502076016855, "end_to_end_rtf": 0.28833688870252144, "inference_ms": 2589.4247982992965, "per_utterance_latency_ms": 2589.511962899269, "postprocess_ms": 0.07867569947848096, "preprocess_ms": 0.008488900493830442, "provider_compute_latency_ms": 2589.511962899269, "provider_compute_rtf": 0.254609358251939, "real_time_factor": 0.254609358251939, "time_to_final_result_ms": 2906.5502076016855, "time_to_first_result_ms": 2906.5502076016855, "time_to_result_ms": 2906.5502076016855, "total_latency_ms": 2589.511962899269}`
- reliability_metrics: `{"failure_rate": 0.0, "success_rate": 1.0}`
- cost_metrics: `{"estimated_cost_usd": 0.0029717999999999997}`
- cost_totals: `{"estimated_cost_usd": 0.029717999999999998}`
- estimated_cost_total_usd: `0.029717999999999998`

### providers/google_cloud (preset: `balanced`)
- samples: `10`
- successful_samples: `10`
- failed_samples: `0`
- quality_metrics: `{"cer": 0.037037037037037035, "confidence": 0.8860481381416321, "sample_accuracy": 0.2, "wer": 0.1346153846153846}`
- latency_metrics: `{"end_to_end_latency_ms": 1911.9479549008247, "end_to_end_rtf": 0.19485613538873767, "inference_ms": 1829.8349881995819, "per_utterance_latency_ms": 1911.0279676002392, "postprocess_ms": 0.00020450097508728504, "preprocess_ms": 81.19277489968226, "provider_compute_latency_ms": 1911.0279676002392, "provider_compute_rtf": 0.19476067561778965, "real_time_factor": 0.19476067561778965, "time_to_final_result_ms": 1911.9479549008247, "time_to_first_result_ms": 1911.9479549008247, "time_to_result_ms": 1911.9479549008247, "total_latency_ms": 1911.0279676002392}`
- reliability_metrics: `{"failure_rate": 0.0, "success_rate": 1.0}`
- cost_metrics: `{"estimated_cost_usd": 0.0}`
- cost_totals: `{"estimated_cost_usd": 0.0}`
- estimated_cost_total_usd: `0.0`

## Noise Summary
- clean: `{"audio_duration_sec": 9.906, "cer": 0.027391975308641976, "confidence": 0.9168092999461476, "cpu_percent": 4.427784176581835, "cpu_percent_mean": 3.993273891038012, "cpu_percent_peak": 76.8, "declared_audio_duration_sec": 9.906, "duration_mismatch_sec": 0.0, "end_to_end_latency_ms": 4805.724544401164, "end_to_end_rtf": 0.5094999515179996, "estimated_cost_usd": 0.0023114, "failure_rate": 0.0, "gpu_memory_mb": 690.8702016964517, "gpu_memory_mb_mean": 688.8066775084686, "gpu_memory_mb_peak": 718.0, "gpu_util_percent": 5.776653259594436, "gpu_util_percent_mean": 3.7359964222665254, "gpu_util_percent_peak": 59.0, "inference_ms": 4382.644651265582, "measured_audio_duration_sec": 9.906, "memory_mb": 150.86414689631792, "memory_mb_mean": 184.90606486700233, "memory_mb_peak": 279.81640625, "per_utterance_latency_ms": 4409.769594432873, "postprocess_ms": 0.055353233619825915, "preprocess_ms": 27.069589933671523, "provider_compute_latency_ms": 4409.769594432873, "provider_compute_rtf": 0.46715679350652345, "real_time_factor": 0.46715679350652345, "sample_accuracy": 0.4, "success_rate": 1.0, "time_to_final_result_ms": 4805.724544401164, "time_to_first_result_ms": 4805.724544401164, "time_to_result_ms": 4805.724544401164, "total_latency_ms": 4409.769594432873, "wer": 0.10256410256410256}`
