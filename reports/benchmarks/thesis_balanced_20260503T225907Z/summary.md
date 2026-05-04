# Benchmark Summary: thesis_balanced_20260503T225907Z

- benchmark_profile: `benchmark/thesis_tier_balanced`
- dataset_id: `librispeech_test_clean_subset`
- providers: `providers/whisper_local, providers/huggingface_local, providers/google_cloud, providers/azure_cloud, providers/aws_cloud`
- scenario: `noise_robustness`
- execution_mode: `batch`
- noise_modes: `none, white`
- noise_levels: `clean, custom_0db, custom_10db, custom_20db, custom_5db`
- aggregate_scope: `provider_only`
- total_samples: `250`
- successful_samples: `222`
- failed_samples: `28`
- aggregate_samples: `250`
- corrupted_samples: `0`

## Per-Provider Summary

### providers/aws_cloud (preset: `standard`)
- samples: `50`
- successful_samples: `36`
- failed_samples: `14`
- quality_metrics: `{"cer": 0.25336879432624115, "confidence": 0.7193649896785693, "sample_accuracy": 0.6, "wer": 0.24382470119521912}`
- latency_metrics: `{"end_to_end_latency_ms": 9896.9943479, "end_to_end_rtf": 1.506339604328291, "inference_ms": 6550.719600719949, "per_utterance_latency_ms": 6550.7791467598145, "postprocess_ms": 0.053960439890943235, "preprocess_ms": 0.005585599974438082, "provider_compute_latency_ms": 6550.7791467598145, "provider_compute_rtf": 0.9522681382189079, "real_time_factor": 0.9522681382189079, "time_to_final_result_ms": 9896.9943479, "time_to_first_result_ms": 9896.9943479, "time_to_result_ms": 9896.9943479, "total_latency_ms": 6550.7791467598145}`
- reliability_metrics: `{"failure_rate": 0.28, "success_rate": 0.72}`
- cost_metrics: `{"estimated_cost_usd": 0.003661}`
- cost_totals: `{"estimated_cost_usd": 0.18305}`
- estimated_cost_total_usd: `0.18305`

### providers/azure_cloud (preset: `standard`)
- samples: `50`
- successful_samples: `36`
- failed_samples: `14`
- quality_metrics: `{"cer": 0.16063829787234044, "confidence": 0.5818591954, "sample_accuracy": 0.48, "wer": 0.18964143426294822}`
- latency_metrics: `{"end_to_end_latency_ms": 3226.4521802599484, "end_to_end_rtf": 0.3462891840723369, "inference_ms": 2647.2381392199895, "per_utterance_latency_ms": 2647.3093183199126, "postprocess_ms": 0.06498823997389991, "preprocess_ms": 0.006190859949128935, "provider_compute_latency_ms": 2647.3093183199126, "provider_compute_rtf": 0.22938442313767504, "real_time_factor": 0.22938442313767504, "time_to_final_result_ms": 3226.4521802599484, "time_to_first_result_ms": 3226.4521802599484, "time_to_result_ms": 3226.4521802599484, "total_latency_ms": 2647.3093183199126}`
- reliability_metrics: `{"failure_rate": 0.28, "success_rate": 0.72}`
- cost_metrics: `{"estimated_cost_usd": 0.00274575}`
- cost_totals: `{"estimated_cost_usd": 0.13728749999999998}`
- estimated_cost_total_usd: `0.13728749999999998`

### providers/google_cloud (preset: `balanced`)
- samples: `50`
- successful_samples: `50`
- failed_samples: `0`
- quality_metrics: `{"cer": 0.03173758865248227, "confidence": 0.9495263755321502, "sample_accuracy": 0.48, "wer": 0.054183266932270914}`
- latency_metrics: `{"end_to_end_latency_ms": 1740.8213091400467, "end_to_end_rtf": 0.20541830419615667, "inference_ms": 1737.92632616005, "per_utterance_latency_ms": 1739.8807322201174, "postprocess_ms": 0.0001247999352926854, "preprocess_ms": 1.9542812601321202, "provider_compute_latency_ms": 1739.8807322201174, "provider_compute_rtf": 0.2052953459148058, "real_time_factor": 0.2052953459148058, "time_to_final_result_ms": 1740.8213091400467, "time_to_first_result_ms": 1740.8213091400467, "time_to_result_ms": 1740.8213091400467, "total_latency_ms": 1739.8807322201174}`
- reliability_metrics: `{"failure_rate": 0.0, "success_rate": 1.0}`
- cost_metrics: `{"estimated_cost_usd": 0.0}`
- cost_totals: `{"estimated_cost_usd": 0.0}`
- estimated_cost_total_usd: `0.0`

### providers/huggingface_local (preset: `balanced`)
- samples: `50`
- successful_samples: `50`
- failed_samples: `0`
- quality_metrics: `{"cer": 0.019858156028368795, "confidence": 0.0, "sample_accuracy": 0.6, "wer": 0.034262948207171316}`
- latency_metrics: `{"end_to_end_latency_ms": 1712.8906682000343, "end_to_end_rtf": 0.23460260798106164, "inference_ms": 1712.2354382400226, "per_utterance_latency_ms": 1712.6432798198948, "postprocess_ms": 0.10688779992051423, "preprocess_ms": 0.3009537799516693, "provider_compute_latency_ms": 1712.6432798198948, "provider_compute_rtf": 0.2345646581154965, "real_time_factor": 0.2345646581154965, "time_to_final_result_ms": 1712.8906682000343, "time_to_first_result_ms": 1712.8906682000343, "time_to_result_ms": 1712.8906682000343, "total_latency_ms": 1712.6432798198948}`
- reliability_metrics: `{"failure_rate": 0.0, "success_rate": 1.0}`
- cost_metrics: `{"estimated_cost_usd": 0.0}`
- cost_totals: `{"estimated_cost_usd": 0.0}`
- estimated_cost_total_usd: `0.0`

### providers/whisper_local (preset: `balanced`)
- samples: `50`
- successful_samples: `50`
- failed_samples: `0`
- quality_metrics: `{"cer": 0.032624113475177303, "confidence": 0.888024330342506, "sample_accuracy": 0.42, "wer": 0.05816733067729084}`
- latency_metrics: `{"end_to_end_latency_ms": 1031.7164814199714, "end_to_end_rtf": 0.14760127914448717, "inference_ms": 1017.085030200069, "per_utterance_latency_ms": 1031.3641699401342, "postprocess_ms": 0.09171701995001058, "preprocess_ms": 14.187422720115137, "provider_compute_latency_ms": 1031.3641699401342, "provider_compute_rtf": 0.14754652823382536, "real_time_factor": 0.14754652823382536, "time_to_final_result_ms": 1031.7164814199714, "time_to_first_result_ms": 1031.7164814199714, "time_to_result_ms": 1031.7164814199714, "total_latency_ms": 1031.3641699401342}`
- reliability_metrics: `{"failure_rate": 0.0, "success_rate": 1.0}`
- cost_metrics: `{"estimated_cost_usd": 0.0}`
- cost_totals: `{"estimated_cost_usd": 0.0}`
- estimated_cost_total_usd: `0.0`

## Noise Summary
- clean: `{"audio_duration_sec": 9.1525, "cer": 0.08439716312056737, "confidence": 0.6565362913023653, "cpu_percent": 13.627764424594073, "cpu_percent_mean": 10.12009080623272, "cpu_percent_peak": 100.0, "declared_audio_duration_sec": 9.1525, "duration_mismatch_sec": 0.0, "end_to_end_latency_ms": 3619.555535380023, "end_to_end_rtf": 0.5115962591007762, "estimated_cost_usd": 0.00128135, "failure_rate": 0.1, "gpu_memory_mb": 1494.9544208692923, "gpu_memory_mb_mean": 1186.8558011786936, "gpu_memory_mb_peak": 4687.0, "gpu_util_percent": 14.929465215492135, "gpu_util_percent_mean": 13.106581809004531, "gpu_util_percent_peak": 92.0, "inference_ms": 2833.0447445799837, "measured_audio_duration_sec": 9.1525, "memory_mb": 2221.181495166963, "memory_mb_mean": 2225.8047850584126, "memory_mb_peak": 3437.8984375, "per_utterance_latency_ms": 2849.019542720034, "postprocess_ms": 0.06472621991633787, "preprocess_ms": 15.910071920134214, "provider_compute_latency_ms": 2849.019542720034, "provider_compute_rtf": 0.3799015376675367, "real_time_factor": 0.3799015376675367, "sample_accuracy": 0.66, "success_rate": 0.9, "time_to_final_result_ms": 3619.555535380023, "time_to_first_result_ms": 3619.555535380023, "time_to_result_ms": 3619.555535380023, "total_latency_ms": 2849.019542720034, "wer": 0.08764940239043825}`
- white:custom_0db: `{"audio_duration_sec": 9.1525, "cer": 0.125, "confidence": 0.5987523800278278, "cpu_percent": 13.359942217355893, "cpu_percent_mean": 9.562452852137923, "cpu_percent_peak": 100.0, "declared_audio_duration_sec": 9.1525, "duration_mismatch_sec": 0.0, "end_to_end_latency_ms": 3475.729616080007, "end_to_end_rtf": 0.4781702200105213, "estimated_cost_usd": 0.00128135, "failure_rate": 0.1, "gpu_memory_mb": 1543.5056821936234, "gpu_memory_mb_mean": 1187.6731317089623, "gpu_memory_mb_peak": 4687.0, "gpu_util_percent": 15.765283003352856, "gpu_util_percent_mean": 13.058351973921202, "gpu_util_percent_peak": 72.0, "inference_ms": 2824.7774266600572, "measured_audio_duration_sec": 9.1525, "memory_mb": 2229.6183238335575, "memory_mb_mean": 2230.637068535255, "memory_mb_peak": 3387.47265625, "per_utterance_latency_ms": 2824.980638180059, "postprocess_ms": 0.0638217999767221, "preprocess_ms": 0.1393897200250649, "provider_compute_latency_ms": 2824.980638180059, "provider_compute_rtf": 0.374052891823834, "real_time_factor": 0.374052891823834, "sample_accuracy": 0.3, "success_rate": 0.9, "time_to_final_result_ms": 3475.729616080007, "time_to_first_result_ms": 3475.729616080007, "time_to_result_ms": 3475.729616080007, "total_latency_ms": 2824.980638180059, "wer": 0.1697211155378486}`
- white:custom_10db: `{"audio_duration_sec": 9.1525, "cer": 0.09663120567375887, "confidence": 0.6315104319300754, "cpu_percent": 13.491129037086512, "cpu_percent_mean": 9.20191976385849, "cpu_percent_peak": 100.0, "declared_audio_duration_sec": 9.1525, "duration_mismatch_sec": 0.0, "end_to_end_latency_ms": 3554.664554139981, "end_to_end_rtf": 0.4912590479890499, "estimated_cost_usd": 0.00128135, "failure_rate": 0.12, "gpu_memory_mb": 1545.547250378003, "gpu_memory_mb_mean": 1182.1372707320693, "gpu_memory_mb_peak": 4714.0, "gpu_util_percent": 15.027078330999995, "gpu_util_percent_mean": 11.465446132433026, "gpu_util_percent_peak": 91.0, "inference_ms": 2746.601312820112, "measured_audio_duration_sec": 9.1525, "memory_mb": 2228.3351256472274, "memory_mb_mean": 2230.969388776434, "memory_mb_peak": 3406.65625, "per_utterance_latency_ms": 2746.7920946000595, "postprocess_ms": 0.06618685994908446, "preprocess_ms": 0.12459491999834427, "provider_compute_latency_ms": 2746.7920946000595, "provider_compute_rtf": 0.34662453963798734, "real_time_factor": 0.34662453963798734, "sample_accuracy": 0.52, "success_rate": 0.88, "time_to_final_result_ms": 3554.664554139981, "time_to_first_result_ms": 3554.664554139981, "time_to_result_ms": 3554.664554139981, "total_latency_ms": 2746.7920946000595, "wer": 0.10916334661354582}`
- white:custom_20db: `{"audio_duration_sec": 9.1525, "cer": 0.09095744680851064, "confidence": 0.6350961626465796, "cpu_percent": 13.421767434112372, "cpu_percent_mean": 9.794615981332226, "cpu_percent_peak": 100.0, "declared_audio_duration_sec": 9.1525, "duration_mismatch_sec": 0.0, "end_to_end_latency_ms": 3540.662685119987, "end_to_end_rtf": 0.5050974583146144, "estimated_cost_usd": 0.00128135, "failure_rate": 0.12, "gpu_memory_mb": 1549.2818632364367, "gpu_memory_mb_mean": 1191.473671592809, "gpu_memory_mb_peak": 4714.0, "gpu_util_percent": 15.284690722676016, "gpu_util_percent_mean": 12.854020190363618, "gpu_util_percent_peak": 100.0, "inference_ms": 2602.701735979954, "measured_audio_duration_sec": 9.1525, "memory_mb": 2226.8366271128493, "memory_mb_mean": 2225.7551365213567, "memory_mb_peak": 3463.046875, "per_utterance_latency_ms": 2602.8981899797873, "postprocess_ms": 0.06056273987269378, "preprocess_ms": 0.135891259960772, "provider_compute_latency_ms": 2602.8981899797873, "provider_compute_rtf": 0.3323606354120532, "real_time_factor": 0.3323606354120532, "sample_accuracy": 0.62, "success_rate": 0.88, "time_to_final_result_ms": 3540.662685119987, "time_to_first_result_ms": 3540.662685119987, "time_to_result_ms": 3540.662685119987, "total_latency_ms": 2602.8981899797873, "wer": 0.09880478087649402}`
- white:custom_5db: `{"audio_duration_sec": 9.1525, "cer": 0.10124113475177304, "confidence": 0.6168796250463775, "cpu_percent": 13.153638340448687, "cpu_percent_mean": 9.412854199206095, "cpu_percent_peak": 91.9, "declared_audio_duration_sec": 9.1525, "duration_mismatch_sec": 0.0, "end_to_end_latency_ms": 3418.262596200002, "end_to_end_rtf": 0.4541279943073718, "estimated_cost_usd": 0.00128135, "failure_rate": 0.12, "gpu_memory_mb": 1546.3514132820364, "gpu_memory_mb_mean": 1198.1529946099706, "gpu_memory_mb_peak": 4704.0, "gpu_util_percent": 14.736077421970034, "gpu_util_percent_mean": 12.532329852235828, "gpu_util_percent_peak": 83.0, "inference_ms": 2658.0793144999734, "measured_audio_duration_sec": 9.1525, "memory_mb": 2229.460695130832, "memory_mb_mean": 2234.1597362015223, "memory_mb_peak": 3402.8203125, "per_utterance_latency_ms": 2658.2861815799333, "postprocess_ms": 0.062380679955822416, "preprocess_ms": 0.14448640000409796, "provider_compute_latency_ms": 2658.2861815799333, "provider_compute_rtf": 0.33611948907929945, "real_time_factor": 0.33611948907929945, "sample_accuracy": 0.48, "success_rate": 0.88, "time_to_final_result_ms": 3418.262596200002, "time_to_first_result_ms": 3418.262596200002, "time_to_result_ms": 3418.262596200002, "total_latency_ms": 2658.2861815799333, "wer": 0.1147410358565737}`
