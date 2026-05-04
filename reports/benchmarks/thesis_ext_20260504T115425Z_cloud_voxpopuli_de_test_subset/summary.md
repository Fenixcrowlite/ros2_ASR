# Benchmark Summary: thesis_ext_20260504T115425Z_cloud_voxpopuli_de_test_subset

- benchmark_profile: `benchmark/thesis_extended_cloud_matrix`
- dataset_id: `voxpopuli_de_test_subset`
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
- quality_metrics: `{"cer": 0.04782608695652174, "confidence": 0.9281094650629691, "sample_accuracy": 0.2, "wer": 0.08415841584158416}`
- latency_metrics: `{"end_to_end_latency_ms": 10019.448648198886, "end_to_end_rtf": 1.4210426325532595, "inference_ms": 9143.720949099225, "per_utterance_latency_ms": 9143.809744798637, "postprocess_ms": 0.08012040052562952, "preprocess_ms": 0.008675298886373639, "provider_compute_latency_ms": 9143.809744798637, "provider_compute_rtf": 1.2979997669028822, "real_time_factor": 1.2979997669028822, "time_to_final_result_ms": 10019.448648198886, "time_to_first_result_ms": 10019.448648198886, "time_to_result_ms": 10019.448648198886, "total_latency_ms": 9143.809744798637}`
- reliability_metrics: `{"failure_rate": 0.0, "success_rate": 1.0}`
- cost_metrics: `{"estimated_cost_usd": 0.00351811}`
- cost_totals: `{"estimated_cost_usd": 0.0351811}`
- estimated_cost_total_usd: `0.0351811`

### providers/azure_cloud (preset: `standard`)
- samples: `10`
- successful_samples: `10`
- failed_samples: `0`
- quality_metrics: `{"cer": 0.20695652173913043, "confidence": 0.883457188, "sample_accuracy": 0.1, "wer": 0.27722772277227725}`
- latency_metrics: `{"end_to_end_latency_ms": 2478.212994799105, "end_to_end_rtf": 0.31791690210421064, "inference_ms": 2235.381218699331, "per_utterance_latency_ms": 2235.470104900014, "postprocess_ms": 0.08039210079004988, "preprocess_ms": 0.008494099893141538, "provider_compute_latency_ms": 2235.470104900014, "provider_compute_rtf": 0.2806122531542963, "real_time_factor": 0.2806122531542963, "time_to_final_result_ms": 2478.212994799105, "time_to_first_result_ms": 2478.212994799105, "time_to_result_ms": 2478.212994799105, "total_latency_ms": 2235.470104900014}`
- reliability_metrics: `{"failure_rate": 0.0, "success_rate": 1.0}`
- cost_metrics: `{"estimated_cost_usd": 0.0026385824999999997}`
- cost_totals: `{"estimated_cost_usd": 0.026385824999999998}`
- estimated_cost_total_usd: `0.026385824999999998`

### providers/google_cloud (preset: `balanced`)
- samples: `10`
- successful_samples: `10`
- failed_samples: `0`
- quality_metrics: `{"cer": 0.06869565217391305, "confidence": 0.923268449306488, "sample_accuracy": 0.1, "wer": 0.1485148514851485}`
- latency_metrics: `{"end_to_end_latency_ms": 2534.7896544015384, "end_to_end_rtf": 0.30631849444611436, "inference_ms": 2444.1874139985885, "per_utterance_latency_ms": 2533.9138067982276, "postprocess_ms": 0.0001333006366621703, "preprocess_ms": 89.72625949900248, "provider_compute_latency_ms": 2533.9138067982276, "provider_compute_rtf": 0.3061972974948363, "real_time_factor": 0.3061972974948363, "time_to_final_result_ms": 2534.7896544015384, "time_to_first_result_ms": 2534.7896544015384, "time_to_result_ms": 2534.7896544015384, "total_latency_ms": 2533.9138067982276}`
- reliability_metrics: `{"failure_rate": 0.0, "success_rate": 1.0}`
- cost_metrics: `{"estimated_cost_usd": 0.0}`
- cost_totals: `{"estimated_cost_usd": 0.0}`
- estimated_cost_total_usd: `0.0`

## Noise Summary
- clean: `{"audio_duration_sec": 8.795275, "cer": 0.10782608695652174, "confidence": 0.911611700789819, "cpu_percent": 3.3183027705534895, "cpu_percent_mean": 3.727833997649358, "cpu_percent_peak": 50.0, "declared_audio_duration_sec": 8.7953, "duration_mismatch_sec": 0.00016249999999979893, "end_to_end_latency_ms": 5010.817099133176, "end_to_end_rtf": 0.6817593430345282, "estimated_cost_usd": 0.0020522308333333333, "failure_rate": 0.0, "gpu_memory_mb": 688.8504704677131, "gpu_memory_mb_mean": 704.4567789344438, "gpu_memory_mb_peak": 826.0, "gpu_util_percent": 5.132830845624963, "gpu_util_percent_mean": 6.121616956770422, "gpu_util_percent_peak": 60.0, "inference_ms": 4607.763193932381, "measured_audio_duration_sec": 8.795275, "memory_mb": 151.3266925728305, "memory_mb_mean": 186.53108140761844, "memory_mb_peak": 280.7421875, "per_utterance_latency_ms": 4637.731218832293, "postprocess_ms": 0.05354860065078052, "preprocess_ms": 29.914476299260667, "provider_compute_latency_ms": 4637.731218832293, "provider_compute_rtf": 0.6282697725173383, "real_time_factor": 0.6282697725173383, "sample_accuracy": 0.13333333333333333, "success_rate": 1.0, "time_to_final_result_ms": 5010.817099133176, "time_to_first_result_ms": 5010.817099133176, "time_to_result_ms": 5010.817099133176, "total_latency_ms": 4637.731218832293, "wer": 0.16996699669966997}`
