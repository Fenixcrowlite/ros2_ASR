# Benchmark Summary: thesis_ext_20260504T115425Z_cloud_mini_librispeech_dev_clean_2_subset

- benchmark_profile: `benchmark/thesis_extended_cloud_matrix`
- dataset_id: `mini_librispeech_dev_clean_2_subset`
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
- quality_metrics: `{"cer": 0.0013157894736842105, "confidence": 0.9996475174825175, "sample_accuracy": 0.8, "wer": 0.01744186046511628}`
- latency_metrics: `{"end_to_end_latency_ms": 9470.933349400002, "end_to_end_rtf": 2.116308277163448, "inference_ms": 8700.763759999973, "per_utterance_latency_ms": 8700.849958199251, "postprocess_ms": 0.07969310026965104, "preprocess_ms": 0.006505099008791149, "provider_compute_latency_ms": 8700.849958199251, "provider_compute_rtf": 1.9497176838817152, "real_time_factor": 1.9497176838817152, "time_to_final_result_ms": 9470.933349400002, "time_to_first_result_ms": 9470.933349400002, "time_to_result_ms": 9470.933349400002, "total_latency_ms": 8700.849958199251}`
- reliability_metrics: `{"failure_rate": 0.0, "success_rate": 1.0}`
- cost_metrics: `{"estimated_cost_usd": 0.0020826}`
- cost_totals: `{"estimated_cost_usd": 0.020826}`
- estimated_cost_total_usd: `0.020826`

### providers/azure_cloud (preset: `standard`)
- samples: `10`
- successful_samples: `10`
- failed_samples: `0`
- quality_metrics: `{"cer": 0.003947368421052632, "confidence": 0.873724741, "sample_accuracy": 0.7, "wer": 0.023255813953488372}`
- latency_metrics: `{"end_to_end_latency_ms": 1635.0306225998793, "end_to_end_rtf": 0.336459534787714, "inference_ms": 1375.8990306982014, "per_utterance_latency_ms": 1375.9898355972837, "postprocess_ms": 0.08247339937952347, "preprocess_ms": 0.008331499702762812, "provider_compute_latency_ms": 1375.9898355972837, "provider_compute_rtf": 0.27790642662475984, "real_time_factor": 0.27790642662475984, "time_to_final_result_ms": 1635.0306225998793, "time_to_first_result_ms": 1635.0306225998793, "time_to_result_ms": 1635.0306225998793, "total_latency_ms": 1375.9898355972837}`
- reliability_metrics: `{"failure_rate": 0.0, "success_rate": 1.0}`
- cost_metrics: `{"estimated_cost_usd": 0.0015619499999999999}`
- cost_totals: `{"estimated_cost_usd": 0.015619499999999998}`
- estimated_cost_total_usd: `0.015619499999999998`

### providers/google_cloud (preset: `balanced`)
- samples: `10`
- successful_samples: `10`
- failed_samples: `0`
- quality_metrics: `{"cer": 0.006578947368421052, "confidence": 0.9715641260147094, "sample_accuracy": 0.6, "wer": 0.029069767441860465}`
- latency_metrics: `{"end_to_end_latency_ms": 1501.6487450993736, "end_to_end_rtf": 0.30222976468601176, "inference_ms": 1428.868552199856, "per_utterance_latency_ms": 1500.7514498014643, "postprocess_ms": 0.0001733009412419051, "preprocess_ms": 71.88272430066718, "provider_compute_latency_ms": 1500.7514498014643, "provider_compute_rtf": 0.3020405117425065, "real_time_factor": 0.3020405117425065, "time_to_final_result_ms": 1501.6487450993736, "time_to_first_result_ms": 1501.6487450993736, "time_to_result_ms": 1501.6487450993736, "total_latency_ms": 1500.7514498014643}`
- reliability_metrics: `{"failure_rate": 0.0, "success_rate": 1.0}`
- cost_metrics: `{"estimated_cost_usd": 0.0}`
- cost_totals: `{"estimated_cost_usd": 0.0}`
- estimated_cost_total_usd: `0.0`

## Noise Summary
- clean: `{"audio_duration_sec": 5.2065, "cer": 0.003947368421052632, "confidence": 0.9483121281657423, "cpu_percent": 5.890756594079368, "cpu_percent_mean": 6.174208461318452, "cpu_percent_peak": 66.7, "declared_audio_duration_sec": 5.2065, "duration_mismatch_sec": 0.0, "end_to_end_latency_ms": 4202.537572366418, "end_to_end_rtf": 0.9183325255457246, "estimated_cost_usd": 0.00121485, "failure_rate": 0.0, "gpu_memory_mb": 709.815145987525, "gpu_memory_mb_mean": 716.3236726142391, "gpu_memory_mb_peak": 757.0, "gpu_util_percent": 4.898489299678816, "gpu_util_percent_mean": 6.803979548176286, "gpu_util_percent_peak": 42.0, "inference_ms": 3835.1771142993434, "measured_audio_duration_sec": 5.2065, "memory_mb": 149.70069122132293, "memory_mb_mean": 194.74593237968824, "memory_mb_peak": 278.44921875, "per_utterance_latency_ms": 3859.197081199333, "postprocess_ms": 0.05411326686347214, "preprocess_ms": 23.965853633126244, "provider_compute_latency_ms": 3859.197081199333, "provider_compute_rtf": 0.8432215407496605, "real_time_factor": 0.8432215407496605, "sample_accuracy": 0.7, "success_rate": 1.0, "time_to_final_result_ms": 4202.537572366418, "time_to_first_result_ms": 4202.537572366418, "time_to_result_ms": 4202.537572366418, "total_latency_ms": 3859.197081199333, "wer": 0.023255813953488372}`
