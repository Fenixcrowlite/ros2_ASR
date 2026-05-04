# Benchmark Summary: thesis_ext_20260504T115425Z_cloud_voxpopuli_en_test_subset

- benchmark_profile: `benchmark/thesis_extended_cloud_matrix`
- dataset_id: `voxpopuli_en_test_subset`
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
- quality_metrics: `{"cer": 0.023181454836131096, "confidence": 0.9874348101440522, "sample_accuracy": 0.7, "wer": 0.036290322580645164}`
- latency_metrics: `{"end_to_end_latency_ms": 9726.448436799546, "end_to_end_rtf": 1.912593902675641, "inference_ms": 8903.30005880096, "per_utterance_latency_ms": 8903.384007603745, "postprocess_ms": 0.07722400114289485, "preprocess_ms": 0.006724801642121747, "provider_compute_latency_ms": 8903.384007603745, "provider_compute_rtf": 1.7583908263979782, "real_time_factor": 1.7583908263979782, "time_to_final_result_ms": 9726.448436799546, "time_to_first_result_ms": 9726.448436799546, "time_to_result_ms": 9726.448436799546, "total_latency_ms": 8903.384007603745}`
- reliability_metrics: `{"failure_rate": 0.0, "success_rate": 1.0}`
- cost_metrics: `{"estimated_cost_usd": 0.0041606525}`
- cost_totals: `{"estimated_cost_usd": 0.041606525}`
- estimated_cost_total_usd: `0.041606525`

### providers/azure_cloud (preset: `standard`)
- samples: `10`
- successful_samples: `10`
- failed_samples: `0`
- quality_metrics: `{"cer": 0.03117505995203837, "confidence": 0.824871232, "sample_accuracy": 0.4, "wer": 0.07258064516129033}`
- latency_metrics: `{"end_to_end_latency_ms": 3926.3775608000287, "end_to_end_rtf": 0.4124367306683414, "inference_ms": 3674.4684213001165, "per_utterance_latency_ms": 3674.5630209014053, "postprocess_ms": 0.08612770034233108, "preprocess_ms": 0.008471900946460664, "provider_compute_latency_ms": 3674.5630209014053, "provider_compute_rtf": 0.3625041293927381, "real_time_factor": 0.3625041293927381, "time_to_final_result_ms": 3926.3775608000287, "time_to_first_result_ms": 3926.3775608000287, "time_to_result_ms": 3926.3775608000287, "total_latency_ms": 3674.5630209014053}`
- reliability_metrics: `{"failure_rate": 0.0, "success_rate": 1.0}`
- cost_metrics: `{"estimated_cost_usd": 0.003120489375}`
- cost_totals: `{"estimated_cost_usd": 0.031204893749999997}`
- estimated_cost_total_usd: `0.031204893749999997`

### providers/google_cloud (preset: `balanced`)
- samples: `10`
- successful_samples: `10`
- failed_samples: `0`
- quality_metrics: `{"cer": 0.03916866506794564, "confidence": 0.9738637208938599, "sample_accuracy": 0.4, "wer": 0.0967741935483871}`
- latency_metrics: `{"end_to_end_latency_ms": 2457.940673101257, "end_to_end_rtf": 0.25205084336796746, "inference_ms": 2371.0758144989086, "per_utterance_latency_ms": 2456.886460899841, "postprocess_ms": 0.0001443004293832928, "preprocess_ms": 85.81050210050307, "provider_compute_latency_ms": 2456.886460899841, "provider_compute_rtf": 0.25187531740592806, "real_time_factor": 0.25187531740592806, "time_to_final_result_ms": 2457.940673101257, "time_to_first_result_ms": 2457.940673101257, "time_to_result_ms": 2457.940673101257, "total_latency_ms": 2456.886460899841}`
- reliability_metrics: `{"failure_rate": 0.0, "success_rate": 1.0}`
- cost_metrics: `{"estimated_cost_usd": 0.0}`
- cost_totals: `{"estimated_cost_usd": 0.0}`
- estimated_cost_total_usd: `0.0`

## Noise Summary
- clean: `{"audio_duration_sec": 10.40163125, "cer": 0.03117505995203837, "confidence": 0.9287232543459707, "cpu_percent": 2.8614256126468374, "cpu_percent_mean": 2.7213707796952566, "cpu_percent_peak": 100.0, "declared_audio_duration_sec": 10.4017, "duration_mismatch_sec": 8.124999999998827e-05, "end_to_end_latency_ms": 5370.255556900277, "end_to_end_rtf": 0.8590271589039834, "estimated_cost_usd": 0.0024270472916666664, "failure_rate": 0.0, "gpu_memory_mb": 673.7503587049923, "gpu_memory_mb_mean": 673.6487335885217, "gpu_memory_mb_peak": 698.0, "gpu_util_percent": 0.5983069957144501, "gpu_util_percent_mean": 0.972116220974238, "gpu_util_percent_peak": 66.0, "inference_ms": 4982.948098199995, "measured_audio_duration_sec": 10.40163125, "memory_mb": 151.62637784258092, "memory_mb_mean": 178.81373426741797, "memory_mb_peak": 281.87890625, "per_utterance_latency_ms": 5011.611163134997, "postprocess_ms": 0.05449866730486974, "preprocess_ms": 28.608566267697217, "provider_compute_latency_ms": 5011.611163134997, "provider_compute_rtf": 0.7909234243988814, "real_time_factor": 0.7909234243988814, "sample_accuracy": 0.5, "success_rate": 1.0, "time_to_final_result_ms": 5370.255556900277, "time_to_first_result_ms": 5370.255556900277, "time_to_result_ms": 5370.255556900277, "total_latency_ms": 5011.611163134997, "wer": 0.06854838709677419}`
