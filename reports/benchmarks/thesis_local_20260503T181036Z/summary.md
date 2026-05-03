# Benchmark Summary: thesis_local_20260503T181036Z

- benchmark_profile: `benchmark/thesis_local_matrix`
- dataset_id: `librispeech_test_clean_subset`
- providers: `providers/whisper_local, providers/vosk_local, providers/huggingface_local`
- scenario: `noise_robustness`
- execution_mode: `batch`
- noise_modes: `none, white`
- noise_levels: `clean, custom_0db, custom_10db, custom_20db, custom_5db`
- aggregate_scope: `provider_only`
- total_samples: `30`
- successful_samples: `30`
- failed_samples: `0`
- aggregate_samples: `30`
- corrupted_samples: `0`

## Per-Provider Summary

### providers/huggingface_local (preset: `balanced`)
- samples: `10`
- successful_samples: `10`
- failed_samples: `0`
- quality_metrics: `{"cer": 0.033480176211453744, "confidence": 0.0, "sample_accuracy": 0.4, "wer": 0.0392156862745098}`
- latency_metrics: `{"end_to_end_latency_ms": 7895.766326200101, "end_to_end_rtf": 2.0388758055906244, "inference_ms": 7894.884674899731, "per_utterance_latency_ms": 7895.52471299985, "postprocess_ms": 0.34244350008520996, "preprocess_ms": 0.29759460003333515, "provider_compute_latency_ms": 7895.52471299985, "provider_compute_rtf": 2.0388326836422586, "real_time_factor": 2.0388326836422586, "time_to_final_result_ms": 7895.766326200101, "time_to_first_result_ms": 7895.766326200101, "time_to_result_ms": 7895.766326200101, "total_latency_ms": 7895.52471299985}`
- reliability_metrics: `{"failure_rate": 0.0, "success_rate": 1.0}`
- cost_metrics: `{"estimated_cost_usd": 0.0}`
- cost_totals: `{"estimated_cost_usd": 0.0}`
- estimated_cost_total_usd: `0.0`

### providers/vosk_local (preset: `en_small`)
- samples: `10`
- successful_samples: `10`
- failed_samples: `0`
- quality_metrics: `{"cer": 0.23524229074889869, "confidence": 0.8898051624295278, "sample_accuracy": 0.0, "wer": 0.2784313725490196}`
- latency_metrics: `{"end_to_end_latency_ms": 1295.7025016999978, "end_to_end_rtf": 0.17721771970109262, "inference_ms": 1233.4266716999991, "per_utterance_latency_ms": 1282.222389600247, "postprocess_ms": 0.09639470008551143, "preprocess_ms": 48.699323200162326, "provider_compute_latency_ms": 1282.222389600247, "provider_compute_rtf": 0.17537630615842587, "real_time_factor": 0.17537630615842587, "time_to_final_result_ms": 1295.7025016999978, "time_to_first_result_ms": 1295.7025016999978, "time_to_result_ms": 1295.7025016999978, "total_latency_ms": 1282.222389600247}`
- reliability_metrics: `{"failure_rate": 0.0, "success_rate": 1.0}`
- cost_metrics: `{"estimated_cost_usd": 0.0}`
- cost_totals: `{"estimated_cost_usd": 0.0}`
- estimated_cost_total_usd: `0.0`

### providers/whisper_local (preset: `light`)
- samples: `10`
- successful_samples: `10`
- failed_samples: `0`
- quality_metrics: `{"cer": 0.1066079295154185, "confidence": 0.837277419218951, "sample_accuracy": 0.0, "wer": 0.14901960784313725}`
- latency_metrics: `{"end_to_end_latency_ms": 1175.8696256002622, "end_to_end_rtf": 0.26682235081263955, "inference_ms": 567.533513699891, "per_utterance_latency_ms": 1175.5495270996107, "postprocess_ms": 0.09208729989040876, "preprocess_ms": 607.9239260998293, "provider_compute_latency_ms": 1175.5495270996107, "provider_compute_rtf": 0.2667671547987035, "real_time_factor": 0.2667671547987035, "time_to_final_result_ms": 1175.8696256002622, "time_to_first_result_ms": 1175.8696256002622, "time_to_result_ms": 1175.8696256002622, "total_latency_ms": 1175.5495270996107}`
- reliability_metrics: `{"failure_rate": 0.0, "success_rate": 1.0}`
- cost_metrics: `{"estimated_cost_usd": 0.0}`
- cost_totals: `{"estimated_cost_usd": 0.0}`
- estimated_cost_total_usd: `0.0`

## Noise Summary
- clean: `{"audio_duration_sec": 8.865, "cer": 0.032305433186490456, "confidence": 0.5897164325340237, "cpu_percent": 12.77953125, "cpu_percent_mean": 7.658642903102906, "cpu_percent_peak": 90.6, "declared_audio_duration_sec": 8.865, "duration_mismatch_sec": 0.0, "end_to_end_latency_ms": 12749.926269000298, "end_to_end_rtf": 3.490912605178785, "estimated_cost_usd": 0.0, "failure_rate": 0.0, "gpu_memory_mb": 1219.5920696443952, "gpu_memory_mb_mean": 794.6000960101239, "gpu_memory_mb_peak": 4287.0, "gpu_util_percent": 12.617601821090194, "gpu_util_percent_mean": 9.752994717446567, "gpu_util_percent_peak": 69.0, "inference_ms": 11651.571198666565, "measured_audio_duration_sec": 8.865, "memory_mb": 1282.4840066092354, "memory_mb_mean": 1452.5196958045751, "memory_mb_peak": 3824.38671875, "per_utterance_latency_ms": 12746.091709333086, "postprocess_ms": 0.08720499984823012, "preprocess_ms": 1094.433305666674, "provider_compute_latency_ms": 12746.091709333086, "provider_compute_rtf": 3.4903441768493133, "real_time_factor": 3.4903441768493133, "sample_accuracy": 0.16666666666666666, "success_rate": 1.0, "time_to_final_result_ms": 12749.926269000298, "time_to_first_result_ms": 12749.926269000298, "time_to_result_ms": 12749.926269000298, "total_latency_ms": 12746.091709333086, "wer": 0.0392156862745098}`
- white:custom_0db: `{"audio_duration_sec": 8.865, "cer": 0.40381791483113066, "confidence": 0.5249651288065782, "cpu_percent": 17.861035562665997, "cpu_percent_mean": 13.600589905171942, "cpu_percent_peak": 88.1, "declared_audio_duration_sec": 8.865, "duration_mismatch_sec": 0.0, "end_to_end_latency_ms": 1210.448096833564, "end_to_end_rtf": 0.1712031054150253, "estimated_cost_usd": 0.0, "failure_rate": 0.0, "gpu_memory_mb": 1766.4404761904761, "gpu_memory_mb_mean": 2078.971691009376, "gpu_memory_mb_peak": 4285.0, "gpu_util_percent": 18.789682539682538, "gpu_util_percent_mean": 20.45146105715087, "gpu_util_percent_peak": 69.0, "inference_ms": 1206.6915231668343, "measured_audio_duration_sec": 8.865, "memory_mb": 1591.471037991359, "memory_mb_mean": 1770.7762871535986, "memory_mb_peak": 3824.40625, "per_utterance_latency_ms": 1207.0494405002137, "postprocess_ms": 0.24315233349625487, "preprocess_ms": 0.1147649998832397, "provider_compute_latency_ms": 1207.0494405002137, "provider_compute_rtf": 0.17062347502859546, "real_time_factor": 0.17062347502859546, "sample_accuracy": 0.0, "success_rate": 1.0, "time_to_final_result_ms": 1210.448096833564, "time_to_first_result_ms": 1210.448096833564, "time_to_result_ms": 1210.448096833564, "total_latency_ms": 1207.0494405002137, "wer": 0.49019607843137253}`
- white:custom_10db: `{"audio_duration_sec": 8.865, "cer": 0.05873715124816446, "confidence": 0.600216494311435, "cpu_percent": 17.884281045751635, "cpu_percent_mean": 14.530376210135966, "cpu_percent_peak": 89.4, "declared_audio_duration_sec": 8.865, "duration_mismatch_sec": 0.0, "end_to_end_latency_ms": 1082.2123673334925, "end_to_end_rtf": 0.15552923760007611, "estimated_cost_usd": 0.0, "failure_rate": 0.0, "gpu_memory_mb": 1761.7916666666667, "gpu_memory_mb_mean": 2301.3704651421963, "gpu_memory_mb_peak": 4265.0, "gpu_util_percent": 16.827380952380953, "gpu_util_percent_mean": 21.91156299046165, "gpu_util_percent_peak": 68.0, "inference_ms": 1077.2599941663732, "measured_audio_duration_sec": 8.865, "memory_mb": 1576.4157490991188, "memory_mb_mean": 1875.2794124818363, "memory_mb_peak": 3824.23828125, "per_utterance_latency_ms": 1077.5255463328601, "postprocess_ms": 0.15429549997255285, "preprocess_ms": 0.11125666651423671, "provider_compute_latency_ms": 1077.5255463328601, "provider_compute_rtf": 0.1548926789590888, "real_time_factor": 0.1548926789590888, "sample_accuracy": 0.16666666666666666, "success_rate": 1.0, "time_to_final_result_ms": 1082.2123673334925, "time_to_first_result_ms": 1082.2123673334925, "time_to_result_ms": 1082.2123673334925, "total_latency_ms": 1077.5255463328601, "wer": 0.0718954248366013}`
- white:custom_20db: `{"audio_duration_sec": 8.865, "cer": 0.039647577092511016, "confidence": 0.5987941208911642, "cpu_percent": 19.169513888888886, "cpu_percent_mean": 16.61664282427699, "cpu_percent_peak": 100.0, "declared_audio_duration_sec": 8.865, "duration_mismatch_sec": 0.0, "end_to_end_latency_ms": 1049.0075831667127, "end_to_end_rtf": 0.15076502006410347, "estimated_cost_usd": 0.0, "failure_rate": 0.0, "gpu_memory_mb": 1760.388888888889, "gpu_memory_mb_mean": 2336.5116369744487, "gpu_memory_mb_peak": 4279.0, "gpu_util_percent": 16.974206349206348, "gpu_util_percent_mean": 23.58335467225423, "gpu_util_percent_peak": 69.0, "inference_ms": 1043.9811999998103, "measured_audio_duration_sec": 8.865, "memory_mb": 1572.8020186166914, "memory_mb_mean": 1896.771443729482, "memory_mb_peak": 3818.81640625, "per_utterance_latency_ms": 1044.3554978331424, "postprocess_ms": 0.258417666676299, "preprocess_ms": 0.11588016665579441, "provider_compute_latency_ms": 1044.3554978331424, "provider_compute_rtf": 0.1501671962430795, "real_time_factor": 0.1501671962430795, "sample_accuracy": 0.16666666666666666, "success_rate": 1.0, "time_to_final_result_ms": 1049.0075831667127, "time_to_first_result_ms": 1049.0075831667127, "time_to_result_ms": 1049.0075831667127, "total_latency_ms": 1044.3554978331424, "wer": 0.0457516339869281}`
- white:custom_5db: `{"audio_duration_sec": 8.865, "cer": 0.09104258443465492, "confidence": 0.5647787928709304, "cpu_percent": 18.344612794612793, "cpu_percent_mean": 14.29714999853256, "cpu_percent_peak": 90.6, "declared_audio_duration_sec": 8.865, "duration_mismatch_sec": 0.0, "end_to_end_latency_ms": 1187.303106166534, "end_to_end_rtf": 0.16978315858260443, "estimated_cost_usd": 0.0, "failure_rate": 0.0, "gpu_memory_mb": 1762.515873015873, "gpu_memory_mb_mean": 2138.7820989283127, "gpu_memory_mb_peak": 4285.0, "gpu_util_percent": 21.376984126984127, "gpu_util_percent_mean": 23.053409308084692, "gpu_util_percent_peak": 69.0, "inference_ms": 1180.2375178331204, "measured_audio_duration_sec": 8.865, "memory_mb": 1587.0015484081891, "memory_mb_mean": 1795.0391320170372, "memory_mb_peak": 3827.3125, "per_utterance_latency_ms": 1180.4721888335432, "postprocess_ms": 0.14180533344188007, "preprocess_ms": 0.09286566698089398, "provider_compute_latency_ms": 1180.4721888335432, "provider_compute_rtf": 0.16893271391890297, "real_time_factor": 0.16893271391890297, "sample_accuracy": 0.16666666666666666, "success_rate": 1.0, "time_to_final_result_ms": 1187.303106166534, "time_to_first_result_ms": 1187.303106166534, "time_to_result_ms": 1187.303106166534, "total_latency_ms": 1180.4721888335432, "wer": 0.13071895424836602}`
