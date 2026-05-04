# Benchmark Summary: thesis_cloud_20260503T223116Z

- benchmark_profile: `benchmark/thesis_cloud_matrix`
- dataset_id: `librispeech_test_clean_subset`
- providers: `providers/azure_cloud, providers/google_cloud, providers/aws_cloud`
- scenario: `noise_robustness`
- execution_mode: `batch`
- noise_modes: `none, white`
- noise_levels: `clean, custom_0db, custom_10db, custom_20db, custom_5db`
- aggregate_scope: `provider_only`
- total_samples: `150`
- successful_samples: `150`
- failed_samples: `0`
- aggregate_samples: `150`
- corrupted_samples: `0`

## Per-Provider Summary

### providers/aws_cloud (preset: `standard`)
- samples: `50`
- successful_samples: `50`
- failed_samples: `0`
- quality_metrics: `{"cer": 0.003900709219858156, "confidence": 0.9991451588117618, "sample_accuracy": 0.88, "wer": 0.005577689243027889}`
- latency_metrics: `{"end_to_end_latency_ms": 10306.800630059843, "end_to_end_rtf": 1.6146490667202413, "inference_ms": 8875.726517379917, "per_utterance_latency_ms": 8875.816342779926, "postprocess_ms": 0.0820352800838009, "preprocess_ms": 0.007790119925630279, "provider_compute_latency_ms": 8875.816342779926, "provider_compute_rtf": 1.3935314981037088, "real_time_factor": 1.3935314981037088, "time_to_final_result_ms": 10306.800630059843, "time_to_first_result_ms": 10306.800630059843, "time_to_result_ms": 10306.800630059843, "total_latency_ms": 8875.816342779926}`
- reliability_metrics: `{"failure_rate": 0.0, "success_rate": 1.0}`
- cost_metrics: `{"estimated_cost_usd": 0.003661}`
- cost_totals: `{"estimated_cost_usd": 0.18305}`
- estimated_cost_total_usd: `0.18305`

### providers/azure_cloud (preset: `standard`)
- samples: `50`
- successful_samples: `50`
- failed_samples: `0`
- quality_metrics: `{"cer": 0.01524822695035461, "confidence": 0.8155070642, "sample_accuracy": 0.72, "wer": 0.02390438247011952}`
- latency_metrics: `{"end_to_end_latency_ms": 3250.5838503999985, "end_to_end_rtf": 0.34045854739207654, "inference_ms": 2996.3643732400487, "per_utterance_latency_ms": 2996.459967960018, "postprocess_ms": 0.08742117992369458, "preprocess_ms": 0.008173540045390837, "provider_compute_latency_ms": 2996.459967960018, "provider_compute_rtf": 0.29959217527660237, "real_time_factor": 0.29959217527660237, "time_to_final_result_ms": 3250.5838503999985, "time_to_first_result_ms": 3250.5838503999985, "time_to_result_ms": 3250.5838503999985, "total_latency_ms": 2996.459967960018}`
- reliability_metrics: `{"failure_rate": 0.0, "success_rate": 1.0}`
- cost_metrics: `{"estimated_cost_usd": 0.00274575}`
- cost_totals: `{"estimated_cost_usd": 0.13728749999999998}`
- estimated_cost_total_usd: `0.13728749999999998`

### providers/google_cloud (preset: `balanced`)
- samples: `50`
- successful_samples: `50`
- failed_samples: `0`
- quality_metrics: `{"cer": 0.03173758865248227, "confidence": 0.9495263719558715, "sample_accuracy": 0.48, "wer": 0.054183266932270914}`
- latency_metrics: `{"end_to_end_latency_ms": 1814.840009080017, "end_to_end_rtf": 0.21536805602333398, "inference_ms": 1799.495051779977, "per_utterance_latency_ms": 1813.8646067400077, "postprocess_ms": 0.00013350005247048102, "preprocess_ms": 14.369421459978184, "provider_compute_latency_ms": 1813.8646067400077, "provider_compute_rtf": 0.21523663210193522, "real_time_factor": 0.21523663210193522, "time_to_final_result_ms": 1814.840009080017, "time_to_first_result_ms": 1814.840009080017, "time_to_result_ms": 1814.840009080017, "total_latency_ms": 1813.8646067400077}`
- reliability_metrics: `{"failure_rate": 0.0, "success_rate": 1.0}`
- cost_metrics: `{"estimated_cost_usd": 0.0}`
- cost_totals: `{"estimated_cost_usd": 0.0}`
- estimated_cost_total_usd: `0.0`

## Noise Summary
- clean: `{"audio_duration_sec": 9.1525, "cer": 0.0065011820330969266, "confidence": 0.9421402064209595, "cpu_percent": 6.273203034524728, "cpu_percent_mean": 6.800001206445639, "cpu_percent_peak": 100.0, "declared_audio_duration_sec": 9.1525, "duration_mismatch_sec": 0.0, "end_to_end_latency_ms": 5173.141483999916, "end_to_end_rtf": 0.7370892453520494, "estimated_cost_usd": 0.002135583333333333, "failure_rate": 0.0, "gpu_memory_mb": 600.1327154733037, "gpu_memory_mb_mean": 594.8040549635559, "gpu_memory_mb_peak": 684.0, "gpu_util_percent": 10.175257366507367, "gpu_util_percent_mean": 11.583966645486646, "gpu_util_percent_peak": 86.0, "inference_ms": 4569.103819699892, "measured_audio_duration_sec": 9.1525, "memory_mb": 180.47047857078422, "memory_mb_mean": 221.18132044821226, "memory_mb_peak": 300.33984375, "per_utterance_latency_ms": 4592.6894225332335, "postprocess_ms": 0.05496010001782755, "preprocess_ms": 23.530642733324687, "provider_compute_latency_ms": 4592.6894225332335, "provider_compute_rtf": 0.6490619093315726, "real_time_factor": 0.6490619093315726, "sample_accuracy": 0.8, "success_rate": 1.0, "time_to_final_result_ms": 5173.141483999916, "time_to_first_result_ms": 5173.141483999916, "time_to_result_ms": 5173.141483999916, "total_latency_ms": 4592.6894225332335, "wer": 0.009296148738379814}`
- white:custom_0db: `{"audio_duration_sec": 9.1525, "cer": 0.04491725768321513, "confidence": 0.8782327972885315, "cpu_percent": 6.041904366662583, "cpu_percent_mean": 6.3638408168615666, "cpu_percent_peak": 100.0, "declared_audio_duration_sec": 9.1525, "duration_mismatch_sec": 0.0, "end_to_end_latency_ms": 5113.670484833347, "end_to_end_rtf": 0.719077468678756, "estimated_cost_usd": 0.002135583333333333, "failure_rate": 0.0, "gpu_memory_mb": 596.4240716881158, "gpu_memory_mb_mean": 594.90779269016, "gpu_memory_mb_peak": 688.0, "gpu_util_percent": 8.87196558071558, "gpu_util_percent_mean": 10.235973598288346, "gpu_util_percent_peak": 100.0, "inference_ms": 4578.450876733344, "measured_audio_duration_sec": 9.1525, "memory_mb": 185.33361989878495, "memory_mb_mean": 227.01995441298936, "memory_mb_peak": 301.16796875, "per_utterance_latency_ms": 4578.618157099936, "postprocess_ms": 0.052192999889181614, "preprocess_ms": 0.11508736670293729, "provider_compute_latency_ms": 4578.618157099936, "provider_compute_rtf": 0.6355874384837654, "real_time_factor": 0.6355874384837654, "sample_accuracy": 0.5, "success_rate": 1.0, "time_to_final_result_ms": 5113.670484833347, "time_to_first_result_ms": 5113.670484833347, "time_to_result_ms": 5113.670484833347, "total_latency_ms": 4578.618157099936, "wer": 0.07569721115537849}`
- white:custom_10db: `{"audio_duration_sec": 9.1525, "cer": 0.01152482269503546, "confidence": 0.9318474539820705, "cpu_percent": 5.831282865365568, "cpu_percent_mean": 6.536350921120999, "cpu_percent_peak": 50.0, "declared_audio_duration_sec": 9.1525, "duration_mismatch_sec": 0.0, "end_to_end_latency_ms": 5122.558199899989, "end_to_end_rtf": 0.7189550590314884, "estimated_cost_usd": 0.002135583333333333, "failure_rate": 0.0, "gpu_memory_mb": 598.4540898943105, "gpu_memory_mb_mean": 589.9258789161729, "gpu_memory_mb_peak": 679.0, "gpu_util_percent": 8.595924960116136, "gpu_util_percent_mean": 9.007766221694304, "gpu_util_percent_peak": 62.0, "inference_ms": 4563.7404552332855, "measured_audio_duration_sec": 9.1525, "memory_mb": 183.43803617578143, "memory_mb_mean": 225.61037945588572, "memory_mb_peak": 301.14453125, "per_utterance_latency_ms": 4563.911392699993, "postprocess_ms": 0.05491860007775055, "preprocess_ms": 0.11601886662901961, "provider_compute_latency_ms": 4563.911392699993, "provider_compute_rtf": 0.6319071345174838, "real_time_factor": 0.6319071345174838, "sample_accuracy": 0.7, "success_rate": 1.0, "time_to_final_result_ms": 5122.558199899989, "time_to_first_result_ms": 5122.558199899989, "time_to_result_ms": 5122.558199899989, "total_latency_ms": 4563.911392699993, "wer": 0.01859229747675963}`
- white:custom_20db: `{"audio_duration_sec": 9.1525, "cer": 0.0070921985815602835, "confidence": 0.9365645916449731, "cpu_percent": 6.0321260144791795, "cpu_percent_mean": 6.58594900520745, "cpu_percent_peak": 50.0, "declared_audio_duration_sec": 9.1525, "duration_mismatch_sec": 0.0, "end_to_end_latency_ms": 5053.700645766578, "end_to_end_rtf": 0.7215041826329759, "estimated_cost_usd": 0.002135583333333333, "failure_rate": 0.0, "gpu_memory_mb": 599.8966287361876, "gpu_memory_mb_mean": 594.8172389625034, "gpu_memory_mb_peak": 735.0, "gpu_util_percent": 8.103646873279226, "gpu_util_percent_mean": 9.962025180732978, "gpu_util_percent_peak": 88.0, "inference_ms": 4463.0625689667495, "measured_audio_duration_sec": 9.1525, "memory_mb": 182.92049205246354, "memory_mb_mean": 225.1726735249727, "memory_mb_peak": 301.1171875, "per_utterance_latency_ms": 4463.225823066689, "postprocess_ms": 0.060183266759850085, "preprocess_ms": 0.1030708331806333, "provider_compute_latency_ms": 4463.225823066689, "provider_compute_rtf": 0.6280243635658342, "real_time_factor": 0.6280243635658342, "sample_accuracy": 0.8, "success_rate": 1.0, "time_to_final_result_ms": 5053.700645766578, "time_to_first_result_ms": 5053.700645766578, "time_to_result_ms": 5053.700645766578, "total_latency_ms": 4463.225823066689, "wer": 0.01195219123505976}`
- white:custom_5db: `{"audio_duration_sec": 9.1525, "cer": 0.014775413711583925, "confidence": 0.918179275609521, "cpu_percent": 6.482556787193655, "cpu_percent_mean": 6.532883905430645, "cpu_percent_peak": 53.1, "declared_audio_duration_sec": 9.1525, "duration_mismatch_sec": 0.0, "end_to_end_latency_ms": 5157.303334733267, "end_to_end_rtf": 0.7208334945308168, "estimated_cost_usd": 0.002135583333333333, "failure_rate": 0.0, "gpu_memory_mb": 594.5822093708141, "gpu_memory_mb_mean": 591.3507593482716, "gpu_memory_mb_peak": 657.0, "gpu_util_percent": 10.388146065104458, "gpu_util_percent_mean": 9.988283473275436, "gpu_util_percent_peak": 88.0, "inference_ms": 4611.618850033301, "measured_audio_duration_sec": 9.1525, "memory_mb": 184.27522466147755, "memory_mb_mean": 226.8150457915114, "memory_mb_peak": 301.15234375, "per_utterance_latency_ms": 4611.790067066734, "postprocess_ms": 0.060394966688666805, "preprocess_ms": 0.11082206674473127, "provider_compute_latency_ms": 4611.790067066734, "provider_compute_rtf": 0.636019663238421, "real_time_factor": 0.636019663238421, "sample_accuracy": 0.6666666666666666, "success_rate": 1.0, "time_to_final_result_ms": 5157.303334733267, "time_to_first_result_ms": 5157.303334733267, "time_to_result_ms": 5157.303334733267, "total_latency_ms": 4611.790067066734, "wer": 0.02390438247011952}`
