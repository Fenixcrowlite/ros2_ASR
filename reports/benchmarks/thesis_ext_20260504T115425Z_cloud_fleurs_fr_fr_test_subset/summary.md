# Benchmark Summary: thesis_ext_20260504T115425Z_cloud_fleurs_fr_fr_test_subset

- benchmark_profile: `benchmark/thesis_extended_cloud_matrix`
- dataset_id: `fleurs_fr_fr_test_subset`
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
- quality_metrics: `{"cer": 0.014646053702196907, "confidence": 0.9419337848604178, "sample_accuracy": 0.6, "wer": 0.0423728813559322}`
- latency_metrics: `{"end_to_end_latency_ms": 9804.060802499589, "end_to_end_rtf": 1.1158128114291057, "inference_ms": 8915.971291400638, "per_utterance_latency_ms": 8916.059859400411, "postprocess_ms": 0.08114010051940568, "preprocess_ms": 0.007427899254253134, "provider_compute_latency_ms": 8916.059859400411, "provider_compute_rtf": 1.0137161398099204, "real_time_factor": 1.0137161398099204, "time_to_final_result_ms": 9804.060802499589, "time_to_first_result_ms": 9804.060802499589, "time_to_result_ms": 9804.060802499589, "total_latency_ms": 8916.059859400411}`
- reliability_metrics: `{"failure_rate": 0.0, "success_rate": 1.0}`
- cost_metrics: `{"estimated_cost_usd": 0.0037824}`
- cost_totals: `{"estimated_cost_usd": 0.037824}`
- estimated_cost_total_usd: `0.037824`

### providers/azure_cloud (preset: `standard`)
- samples: `10`
- successful_samples: `10`
- failed_samples: `0`
- quality_metrics: `{"cer": 0.01627339300244101, "confidence": 0.892544809, "sample_accuracy": 0.4, "wer": 0.05508474576271186}`
- latency_metrics: `{"end_to_end_latency_ms": 2779.0695990006498, "end_to_end_rtf": 0.2805478901394675, "inference_ms": 2560.3386395006964, "per_utterance_latency_ms": 2560.4314892996626, "postprocess_ms": 0.08403959946008399, "preprocess_ms": 0.008810199506115168, "provider_compute_latency_ms": 2560.4314892996626, "provider_compute_rtf": 0.2547439998908437, "real_time_factor": 0.2547439998908437, "time_to_final_result_ms": 2779.0695990006498, "time_to_first_result_ms": 2779.0695990006498, "time_to_result_ms": 2779.0695990006498, "total_latency_ms": 2560.4314892996626}`
- reliability_metrics: `{"failure_rate": 0.0, "success_rate": 1.0}`
- cost_metrics: `{"estimated_cost_usd": 0.0028368}`
- cost_totals: `{"estimated_cost_usd": 0.028367999999999997}`
- estimated_cost_total_usd: `0.028367999999999997`

### providers/google_cloud (preset: `balanced`)
- samples: `10`
- successful_samples: `10`
- failed_samples: `0`
- quality_metrics: `{"cer": 0.02115541090317331, "confidence": 0.7424776792526245, "sample_accuracy": 0.4, "wer": 0.0847457627118644}`
- latency_metrics: `{"end_to_end_latency_ms": 2870.072730499669, "end_to_end_rtf": 0.3120025492223859, "inference_ms": 2799.500312098098, "per_utterance_latency_ms": 2869.2607931989187, "postprocess_ms": 0.00010320072760805488, "preprocess_ms": 69.76037790009286, "provider_compute_latency_ms": 2869.2607931989187, "provider_compute_rtf": 0.311910217448233, "real_time_factor": 0.311910217448233, "time_to_final_result_ms": 2870.072730499669, "time_to_first_result_ms": 2870.072730499669, "time_to_result_ms": 2870.072730499669, "total_latency_ms": 2869.2607931989187}`
- reliability_metrics: `{"failure_rate": 0.0, "success_rate": 1.0}`
- cost_metrics: `{"estimated_cost_usd": 0.0}`
- cost_totals: `{"estimated_cost_usd": 0.0}`
- estimated_cost_total_usd: `0.0`

## Noise Summary
- clean: `{"audio_duration_sec": 9.456, "cer": 0.01735828586927041, "confidence": 0.8589854243710141, "cpu_percent": 7.066144950036509, "cpu_percent_mean": 6.692981490026193, "cpu_percent_peak": 100.0, "declared_audio_duration_sec": 9.456, "duration_mismatch_sec": 0.0, "end_to_end_latency_ms": 5151.067710666636, "end_to_end_rtf": 0.5694544169303197, "estimated_cost_usd": 0.0022064, "failure_rate": 0.0, "gpu_memory_mb": 724.808469388244, "gpu_memory_mb_mean": 716.350710123505, "gpu_memory_mb_peak": 773.0, "gpu_util_percent": 8.941422097080304, "gpu_util_percent_mean": 8.48106499430062, "gpu_util_percent_peak": 85.0, "inference_ms": 4758.603414333144, "measured_audio_duration_sec": 9.456, "memory_mb": 151.4219957220604, "memory_mb_mean": 184.11336306540846, "memory_mb_peak": 280.83984375, "per_utterance_latency_ms": 4781.917380632997, "postprocess_ms": 0.055094300235699244, "preprocess_ms": 23.258871999617742, "provider_compute_latency_ms": 4781.917380632997, "provider_compute_rtf": 0.5267901190496657, "real_time_factor": 0.5267901190496657, "sample_accuracy": 0.4666666666666667, "success_rate": 1.0, "time_to_final_result_ms": 5151.067710666636, "time_to_first_result_ms": 5151.067710666636, "time_to_result_ms": 5151.067710666636, "total_latency_ms": 4781.917380632997, "wer": 0.06073446327683616}`
