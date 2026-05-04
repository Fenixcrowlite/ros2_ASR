# Benchmark Summary: thesis_ext_20260504T104122Z_local_mls_spanish_test_subset

- benchmark_profile: `benchmark/thesis_extended_local_matrix`
- dataset_id: `mls_spanish_test_subset`
- providers: `providers/whisper_local, providers/vosk_local, providers/huggingface_local`
- scenario: `clean`
- execution_mode: `batch`
- noise_modes: `none, white`
- noise_levels: `clean, custom_0db, custom_10db, custom_20db, custom_5db`
- aggregate_scope: `provider_only`
- total_samples: `150`
- successful_samples: `149`
- failed_samples: `1`
- aggregate_samples: `150`
- corrupted_samples: `0`

## Per-Provider Summary

### providers/huggingface_local (preset: `balanced`)
- samples: `50`
- successful_samples: `49`
- failed_samples: `1`
- quality_metrics: `{"cer": 0.049875, "confidence": 0.0, "sample_accuracy": 0.26, "wer": 0.09865951742627346}`
- latency_metrics: `{"end_to_end_latency_ms": 2155.3986172997975, "end_to_end_rtf": 0.15119265510691246, "inference_ms": 1999.4546099600848, "per_utterance_latency_ms": 2000.1899723791576, "postprocess_ms": 0.12166769956820644, "preprocess_ms": 0.613694719504565, "provider_compute_latency_ms": 2000.1899723791576, "provider_compute_rtf": 0.13905917470813112, "real_time_factor": 0.13905917470813112, "time_to_final_result_ms": 2155.3986172997975, "time_to_first_result_ms": 2155.3986172997975, "time_to_result_ms": 2155.3986172997975, "total_latency_ms": 2000.1899723791576}`
- reliability_metrics: `{"failure_rate": 0.02, "success_rate": 0.98}`
- cost_metrics: `{"estimated_cost_usd": 0.0}`
- cost_totals: `{"estimated_cost_usd": 0.0}`
- estimated_cost_total_usd: `0.0`

### providers/vosk_local (preset: `en_small`)
- samples: `50`
- successful_samples: `50`
- failed_samples: `0`
- quality_metrics: `{"cer": 0.83725, "confidence": 0.7360620568492078, "sample_accuracy": 0.0, "wer": 1.2509383378016086}`
- latency_metrics: `{"end_to_end_latency_ms": 2894.953406319546, "end_to_end_rtf": 0.20163197368685462, "inference_ms": 2849.9279500407283, "per_utterance_latency_ms": 2859.3933097619447, "postprocess_ms": 0.09310678025940433, "preprocess_ms": 9.372252940956969, "provider_compute_latency_ms": 2859.3933097619447, "provider_compute_rtf": 0.19915372738994772, "real_time_factor": 0.19915372738994772, "time_to_final_result_ms": 2894.953406319546, "time_to_first_result_ms": 2894.953406319546, "time_to_result_ms": 2894.953406319546, "total_latency_ms": 2859.3933097619447}`
- reliability_metrics: `{"failure_rate": 0.0, "success_rate": 1.0}`
- cost_metrics: `{"estimated_cost_usd": 0.0}`
- cost_totals: `{"estimated_cost_usd": 0.0}`
- estimated_cost_total_usd: `0.0`

### providers/whisper_local (preset: `light`)
- samples: `50`
- successful_samples: `50`
- failed_samples: `0`
- quality_metrics: `{"cer": 0.131625, "confidence": 0.7707420835391017, "sample_accuracy": 0.0, "wer": 0.2932975871313673}`
- latency_metrics: `{"end_to_end_latency_ms": 790.1347362797242, "end_to_end_rtf": 0.05499522982277749, "inference_ms": 676.6145723393129, "per_utterance_latency_ms": 789.767027439666, "postprocess_ms": 0.08600683970144019, "preprocess_ms": 113.06644826065167, "provider_compute_latency_ms": 789.767027439666, "provider_compute_rtf": 0.05496926352324111, "real_time_factor": 0.05496926352324111, "time_to_final_result_ms": 790.1347362797242, "time_to_first_result_ms": 790.1347362797242, "time_to_result_ms": 790.1347362797242, "total_latency_ms": 789.767027439666}`
- reliability_metrics: `{"failure_rate": 0.0, "success_rate": 1.0}`
- cost_metrics: `{"estimated_cost_usd": 0.0}`
- cost_totals: `{"estimated_cost_usd": 0.0}`
- estimated_cost_total_usd: `0.0`

## Noise Summary
- clean: `{"audio_duration_sec": 14.357, "cer": 0.32708333333333334, "confidence": 0.52845469245157, "cpu_percent": 14.087331617686592, "cpu_percent_mean": 9.52356549817826, "cpu_percent_peak": 90.0, "declared_audio_duration_sec": 14.357, "duration_mismatch_sec": 0.0, "end_to_end_latency_ms": 2170.9033118665197, "end_to_end_rtf": 0.15195653228069045, "estimated_cost_usd": 0.0, "failure_rate": 0.03333333333333333, "gpu_memory_mb": 2831.0716833890747, "gpu_memory_mb_mean": 3113.615970687196, "gpu_memory_mb_peak": 7652.0, "gpu_util_percent": 14.788729627860063, "gpu_util_percent_mean": 21.029450658242563, "gpu_util_percent_peak": 82.0, "inference_ms": 1697.7961628001747, "measured_audio_duration_sec": 14.357, "memory_mb": 1410.480091686007, "memory_mb_mean": 1505.8084594801937, "memory_mb_peak": 3388.30859375, "per_utterance_latency_ms": 1902.3927638668586, "postprocess_ms": 0.09408093295254123, "preprocess_ms": 204.5025201337315, "provider_compute_latency_ms": 1902.3927638668586, "provider_compute_rtf": 0.13104645993602007, "real_time_factor": 0.13104645993602007, "sample_accuracy": 0.13333333333333333, "success_rate": 0.9666666666666667, "time_to_final_result_ms": 2170.9033118665197, "time_to_first_result_ms": 2170.9033118665197, "time_to_result_ms": 2170.9033118665197, "total_latency_ms": 1902.3927638668586, "wer": 0.5424486148346738}`
- white:custom_0db: `{"audio_duration_sec": 14.357, "cer": 0.40375, "confidence": 0.4420104095350912, "cpu_percent": 14.905081769838352, "cpu_percent_mean": 10.580271453961263, "cpu_percent_peak": 91.8, "declared_audio_duration_sec": 14.357, "duration_mismatch_sec": 0.0, "end_to_end_latency_ms": 2051.748651999757, "end_to_end_rtf": 0.14316603818222134, "estimated_cost_usd": 0.0, "failure_rate": 0.0, "gpu_memory_mb": 2989.8974025974026, "gpu_memory_mb_mean": 2883.956659031387, "gpu_memory_mb_peak": 7652.0, "gpu_util_percent": 14.538756613756613, "gpu_util_percent_mean": 14.029568285631221, "gpu_util_percent_peak": 75.0, "inference_ms": 2039.7178614667307, "measured_audio_duration_sec": 14.357, "memory_mb": 1460.3904733974239, "memory_mb_mean": 1478.3640731111395, "memory_mb_peak": 3421.9609375, "per_utterance_latency_ms": 2039.972228400681, "postprocess_ms": 0.10843716663657688, "preprocess_ms": 0.14592976731364615, "provider_compute_latency_ms": 2039.972228400681, "provider_compute_rtf": 0.1423502547320052, "real_time_factor": 0.1423502547320052, "sample_accuracy": 0.0, "success_rate": 1.0, "time_to_final_result_ms": 2051.748651999757, "time_to_first_result_ms": 2051.748651999757, "time_to_result_ms": 2051.748651999757, "total_latency_ms": 2039.972228400681, "wer": 0.6157283288650581}`
- white:custom_10db: `{"audio_duration_sec": 14.357, "cer": 0.32166666666666666, "confidence": 0.5200635052772519, "cpu_percent": 15.537776887280156, "cpu_percent_mean": 11.077136111196241, "cpu_percent_peak": 100.0, "declared_audio_duration_sec": 14.357, "duration_mismatch_sec": 0.0, "end_to_end_latency_ms": 1861.9232065665226, "end_to_end_rtf": 0.12993467141312676, "estimated_cost_usd": 0.0, "failure_rate": 0.0, "gpu_memory_mb": 2984.8, "gpu_memory_mb_mean": 3057.6347601904718, "gpu_memory_mb_peak": 7652.0, "gpu_util_percent": 14.716349206349207, "gpu_util_percent_mean": 15.399170289301967, "gpu_util_percent_peak": 75.0, "inference_ms": 1848.2220161000441, "measured_audio_duration_sec": 14.357, "memory_mb": 1465.189799650885, "memory_mb_mean": 1519.8067051440369, "memory_mb_peak": 3441.4609375, "per_utterance_latency_ms": 1848.463670933658, "postprocess_ms": 0.10222066654629695, "preprocess_ms": 0.13943416706752032, "provider_compute_latency_ms": 1848.463670933658, "provider_compute_rtf": 0.12899597643617164, "real_time_factor": 0.12899597643617164, "sample_accuracy": 0.13333333333333333, "success_rate": 1.0, "time_to_final_result_ms": 1861.9232065665226, "time_to_first_result_ms": 1861.9232065665226, "time_to_result_ms": 1861.9232065665226, "total_latency_ms": 1848.463670933658, "wer": 0.5308310991957105}`
- white:custom_20db: `{"audio_duration_sec": 14.357, "cer": 0.31708333333333333, "confidence": 0.5268950870352695, "cpu_percent": 15.036860870473285, "cpu_percent_mean": 10.664916766635326, "cpu_percent_peak": 100.0, "declared_audio_duration_sec": 14.357, "duration_mismatch_sec": 0.0, "end_to_end_latency_ms": 1695.352628499677, "end_to_end_rtf": 0.11831908856124858, "estimated_cost_usd": 0.0, "failure_rate": 0.0, "gpu_memory_mb": 2984.8375, "gpu_memory_mb_mean": 3248.655049009803, "gpu_memory_mb_peak": 7652.0, "gpu_util_percent": 14.821626984126985, "gpu_util_percent_mean": 16.859673568551973, "gpu_util_percent_peak": 75.0, "inference_ms": 1683.6153270996874, "measured_audio_duration_sec": 14.357, "memory_mb": 1463.4780199576285, "memory_mb_mean": 1554.5008197022553, "memory_mb_peak": 3390.83984375, "per_utterance_latency_ms": 1683.8584833989444, "postprocess_ms": 0.09095326604438014, "preprocess_ms": 0.15220303321257234, "provider_compute_latency_ms": 1683.8584833989444, "provider_compute_rtf": 0.11751618156719508, "real_time_factor": 0.11751618156719508, "sample_accuracy": 0.13333333333333333, "success_rate": 1.0, "time_to_final_result_ms": 1695.352628499677, "time_to_first_result_ms": 1695.352628499677, "time_to_result_ms": 1695.352628499677, "total_latency_ms": 1683.8584833989444, "wer": 0.5254691689008043}`
- white:custom_5db: `{"audio_duration_sec": 14.357, "cer": 0.3283333333333333, "confidence": 0.4939165396813332, "cpu_percent": 15.849770331090133, "cpu_percent_mean": 10.868164311082197, "cpu_percent_peak": 100.0, "declared_audio_duration_sec": 14.357, "duration_mismatch_sec": 0.0, "end_to_end_latency_ms": 1954.216800899303, "end_to_end_rtf": 0.1363234339236205, "estimated_cost_usd": 0.0, "failure_rate": 0.0, "gpu_memory_mb": 2987.285714285714, "gpu_memory_mb_mean": 2963.2049673877405, "gpu_memory_mb_peak": 7652.0, "gpu_util_percent": 14.459325396825397, "gpu_util_percent_mean": 14.498860985490012, "gpu_util_percent_peak": 75.0, "inference_ms": 1940.6438531002398, "measured_audio_duration_sec": 14.357, "memory_mb": 1463.7380946840424, "memory_mb_mean": 1500.6700838826935, "memory_mb_peak": 3421.6796875, "per_utterance_latency_ms": 1940.8967027011386, "postprocess_ms": 0.10561016703528973, "preprocess_ms": 0.14723943386343308, "provider_compute_latency_ms": 1940.8967027011386, "provider_compute_rtf": 0.13539473669747457, "real_time_factor": 0.13539473669747457, "sample_accuracy": 0.03333333333333333, "success_rate": 1.0, "time_to_final_result_ms": 1954.216800899303, "time_to_first_result_ms": 1954.216800899303, "time_to_result_ms": 1954.216800899303, "total_latency_ms": 1940.8967027011386, "wer": 0.5236818588025023}`
