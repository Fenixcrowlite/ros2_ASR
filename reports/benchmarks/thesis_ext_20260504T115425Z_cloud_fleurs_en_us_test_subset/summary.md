# Benchmark Summary: thesis_ext_20260504T115425Z_cloud_fleurs_en_us_test_subset

- benchmark_profile: `benchmark/thesis_extended_cloud_matrix`
- dataset_id: `fleurs_en_us_test_subset`
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
- quality_metrics: `{"cer": 0.03818827708703375, "confidence": 0.982802689440777, "sample_accuracy": 0.4, "wer": 0.09090909090909091}`
- latency_metrics: `{"end_to_end_latency_ms": 9531.786706500861, "end_to_end_rtf": 0.9950664355985548, "inference_ms": 8701.652037700842, "per_utterance_latency_ms": 8701.735371701943, "postprocess_ms": 0.07646430021850392, "preprocess_ms": 0.006869700882816687, "provider_compute_latency_ms": 8701.735371701943, "provider_compute_rtf": 0.9094300023208209, "real_time_factor": 0.9094300023208209, "time_to_final_result_ms": 9531.786706500861, "time_to_first_result_ms": 9531.786706500861, "time_to_result_ms": 9531.786706500861, "total_latency_ms": 8701.735371701943}`
- reliability_metrics: `{"failure_rate": 0.0, "success_rate": 1.0}`
- cost_metrics: `{"estimated_cost_usd": 0.0042512}`
- cost_totals: `{"estimated_cost_usd": 0.042512}`
- estimated_cost_total_usd: `0.042512`

### providers/azure_cloud (preset: `standard`)
- samples: `10`
- successful_samples: `10`
- failed_samples: `0`
- quality_metrics: `{"cer": 0.0674955595026643, "confidence": 0.772071164, "sample_accuracy": 0.3, "wer": 0.11483253588516747}`
- latency_metrics: `{"end_to_end_latency_ms": 2910.861783699511, "end_to_end_rtf": 0.2664961545372823, "inference_ms": 2703.0181995010935, "per_utterance_latency_ms": 2703.1191919006233, "postprocess_ms": 0.09272569950553589, "preprocess_ms": 0.008266700024250895, "provider_compute_latency_ms": 2703.1191919006233, "provider_compute_rtf": 0.24431365354296672, "real_time_factor": 0.24431365354296672, "time_to_final_result_ms": 2910.861783699511, "time_to_first_result_ms": 2910.861783699511, "time_to_result_ms": 2910.861783699511, "total_latency_ms": 2703.1191919006233}`
- reliability_metrics: `{"failure_rate": 0.0, "success_rate": 1.0}`
- cost_metrics: `{"estimated_cost_usd": 0.0031883999999999997}`
- cost_totals: `{"estimated_cost_usd": 0.031883999999999996}`
- estimated_cost_total_usd: `0.031883999999999996`

### providers/google_cloud (preset: `balanced`)
- samples: `10`
- successful_samples: `10`
- failed_samples: `0`
- quality_metrics: `{"cer": 0.0586145648312611, "confidence": 0.8974618136882782, "sample_accuracy": 0.2, "wer": 0.1339712918660287}`
- latency_metrics: `{"end_to_end_latency_ms": 4251.789104101772, "end_to_end_rtf": 0.4396565493988507, "inference_ms": 4171.424501300498, "per_utterance_latency_ms": 4250.872467400768, "postprocess_ms": 0.0001204010914079845, "preprocess_ms": 79.44784569917829, "provider_compute_latency_ms": 4250.872467400768, "provider_compute_rtf": 0.43956510025877793, "real_time_factor": 0.43956510025877793, "time_to_final_result_ms": 4251.789104101772, "time_to_first_result_ms": 4251.789104101772, "time_to_result_ms": 4251.789104101772, "total_latency_ms": 4250.872467400768}`
- reliability_metrics: `{"failure_rate": 0.0, "success_rate": 1.0}`
- cost_metrics: `{"estimated_cost_usd": 0.0}`
- cost_totals: `{"estimated_cost_usd": 0.0}`
- estimated_cost_total_usd: `0.0`

## Noise Summary
- clean: `{"audio_duration_sec": 10.628, "cer": 0.05476613380698638, "confidence": 0.8841118890430184, "cpu_percent": 7.324966145198257, "cpu_percent_mean": 7.204459938909013, "cpu_percent_peak": 100.0, "declared_audio_duration_sec": 10.628, "duration_mismatch_sec": 0.0, "end_to_end_latency_ms": 5564.812531434048, "end_to_end_rtf": 0.5670730465115625, "estimated_cost_usd": 0.0024798666666666666, "failure_rate": 0.0, "gpu_memory_mb": 728.7564877061936, "gpu_memory_mb_mean": 730.7672800653442, "gpu_memory_mb_peak": 870.0, "gpu_util_percent": 8.252858006644772, "gpu_util_percent_mean": 7.049932852491089, "gpu_util_percent_peak": 58.0, "inference_ms": 5192.031579500811, "measured_audio_duration_sec": 10.628, "memory_mb": 151.1783317841066, "memory_mb_mean": 179.38763332523666, "memory_mb_peak": 281.11328125, "per_utterance_latency_ms": 5218.575677001111, "postprocess_ms": 0.05643680027181593, "preprocess_ms": 26.487660700028453, "provider_compute_latency_ms": 5218.575677001111, "provider_compute_rtf": 0.5311029187075219, "real_time_factor": 0.5311029187075219, "sample_accuracy": 0.3, "success_rate": 1.0, "time_to_final_result_ms": 5564.812531434048, "time_to_first_result_ms": 5564.812531434048, "time_to_result_ms": 5564.812531434048, "total_latency_ms": 5218.575677001111, "wer": 0.11323763955342903}`
