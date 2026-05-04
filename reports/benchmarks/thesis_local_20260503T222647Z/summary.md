# Benchmark Summary: thesis_local_20260503T222647Z

- benchmark_profile: `benchmark/thesis_local_matrix`
- dataset_id: `librispeech_test_clean_subset`
- providers: `providers/whisper_local, providers/vosk_local, providers/huggingface_local`
- scenario: `noise_robustness`
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
- successful_samples: `50`
- failed_samples: `0`
- quality_metrics: `{"cer": 0.019858156028368795, "confidence": 0.0, "sample_accuracy": 0.6, "wer": 0.034262948207171316}`
- latency_metrics: `{"end_to_end_latency_ms": 1708.5467576599149, "end_to_end_rtf": 0.2347758672833595, "inference_ms": 1707.88272066, "per_utterance_latency_ms": 1708.3190175799791, "postprocess_ms": 0.1164738999614201, "preprocess_ms": 0.31982302001779317, "provider_compute_latency_ms": 1708.3190175799791, "provider_compute_rtf": 0.23474016831112005, "real_time_factor": 0.23474016831112005, "time_to_final_result_ms": 1708.5467576599149, "time_to_first_result_ms": 1708.5467576599149, "time_to_result_ms": 1708.5467576599149, "total_latency_ms": 1708.3190175799791}`
- reliability_metrics: `{"failure_rate": 0.0, "success_rate": 1.0}`
- cost_metrics: `{"estimated_cost_usd": 0.0}`
- cost_totals: `{"estimated_cost_usd": 0.0}`
- estimated_cost_total_usd: `0.0`

### providers/vosk_local (preset: `en_small`)
- samples: `50`
- successful_samples: `49`
- failed_samples: `1`
- quality_metrics: `{"cer": 0.18670212765957447, "confidence": 0.8987295188096863, "sample_accuracy": 0.08, "wer": 0.25258964143426293}`
- latency_metrics: `{"end_to_end_latency_ms": 1199.2993317399487, "end_to_end_rtf": 0.1457393001286505, "inference_ms": 1179.7669727000357, "per_utterance_latency_ms": 1185.1340728199466, "postprocess_ms": 0.08113835991025553, "preprocess_ms": 5.285961760000646, "provider_compute_latency_ms": 1185.1340728199466, "provider_compute_rtf": 0.1440435247731484, "real_time_factor": 0.1440435247731484, "time_to_final_result_ms": 1199.2993317399487, "time_to_first_result_ms": 1199.2993317399487, "time_to_result_ms": 1199.2993317399487, "total_latency_ms": 1185.1340728199466}`
- reliability_metrics: `{"failure_rate": 0.02, "success_rate": 0.98}`
- cost_metrics: `{"estimated_cost_usd": 0.0}`
- cost_totals: `{"estimated_cost_usd": 0.0}`
- estimated_cost_total_usd: `0.0`

### providers/whisper_local (preset: `light`)
- samples: `50`
- successful_samples: `50`
- failed_samples: `0`
- quality_metrics: `{"cer": 0.07180851063829788, "confidence": 0.849739053650733, "sample_accuracy": 0.22, "wer": 0.12270916334661354}`
- latency_metrics: `{"end_to_end_latency_ms": 598.5249285200189, "end_to_end_rtf": 0.09156301095546725, "inference_ms": 555.3597495599752, "per_utterance_latency_ms": 598.2318857999599, "postprocess_ms": 0.08339264002643176, "preprocess_ms": 42.78874359995825, "provider_compute_latency_ms": 598.2318857999599, "provider_compute_rtf": 0.09151804043427052, "real_time_factor": 0.09151804043427052, "time_to_final_result_ms": 598.5249285200189, "time_to_first_result_ms": 598.5249285200189, "time_to_result_ms": 598.5249285200189, "total_latency_ms": 598.2318857999599}`
- reliability_metrics: `{"failure_rate": 0.0, "success_rate": 1.0}`
- cost_metrics: `{"estimated_cost_usd": 0.0}`
- cost_totals: `{"estimated_cost_usd": 0.0}`
- estimated_cost_total_usd: `0.0`

## Noise Summary
- clean: `{"audio_duration_sec": 9.1525, "cer": 0.01950354609929078, "confidence": 0.6222468858925801, "cpu_percent": 17.457254914043073, "cpu_percent_mean": 13.796078016346959, "cpu_percent_peak": 90.7, "declared_audio_duration_sec": 9.1525, "duration_mismatch_sec": 0.0, "end_to_end_latency_ms": 1307.0168914666585, "end_to_end_rtf": 0.20553558752273893, "estimated_cost_usd": 0.0, "failure_rate": 0.0, "gpu_memory_mb": 1813.9186375125848, "gpu_memory_mb_mean": 2223.311607887898, "gpu_memory_mb_peak": 4654.0, "gpu_util_percent": 28.585961592014225, "gpu_util_percent_mean": 30.44276332847727, "gpu_util_percent_peak": 79.0, "inference_ms": 1222.3988686333541, "measured_audio_duration_sec": 9.1525, "memory_mb": 1424.101924124585, "memory_mb_mean": 1591.1770656700116, "memory_mb_peak": 3396.0390625, "per_utterance_latency_ms": 1302.6869720666884, "postprocess_ms": 0.08814259996749267, "preprocess_ms": 80.19996083336689, "provider_compute_latency_ms": 1302.6869720666884, "provider_compute_rtf": 0.20500866332250048, "real_time_factor": 0.20500866332250048, "sample_accuracy": 0.4, "success_rate": 1.0, "time_to_final_result_ms": 1307.0168914666585, "time_to_first_result_ms": 1307.0168914666585, "time_to_result_ms": 1307.0168914666585, "total_latency_ms": 1302.6869720666884, "wer": 0.03718459495351926}`
- white:custom_0db: `{"audio_duration_sec": 9.1525, "cer": 0.30910165484633567, "confidence": 0.48108861261974156, "cpu_percent": 20.0581260322211, "cpu_percent_mean": 16.05358274590083, "cpu_percent_peak": 100.0, "declared_audio_duration_sec": 9.1525, "duration_mismatch_sec": 0.0, "end_to_end_latency_ms": 1195.0245388000137, "end_to_end_rtf": 0.1483149585146042, "estimated_cost_usd": 0.0, "failure_rate": 0.03333333333333333, "gpu_memory_mb": 1895.7372222222223, "gpu_memory_mb_mean": 2378.56197734335, "gpu_memory_mb_peak": 4654.0, "gpu_util_percent": 27.526342546342548, "gpu_util_percent_mean": 30.051763803587882, "gpu_util_percent_peak": 75.0, "inference_ms": 1189.961699133255, "measured_audio_duration_sec": 9.1525, "memory_mb": 1471.910716951234, "memory_mb_mean": 1659.1086989336989, "memory_mb_peak": 3398.95703125, "per_utterance_latency_ms": 1190.1699430998935, "postprocess_ms": 0.10980680002224592, "preprocess_ms": 0.09843716661634971, "provider_compute_latency_ms": 1190.1699430998935, "provider_compute_rtf": 0.14773839268667294, "real_time_factor": 0.14773839268667294, "sample_accuracy": 0.1, "success_rate": 0.9666666666666667, "time_to_final_result_ms": 1195.0245388000137, "time_to_first_result_ms": 1195.0245388000137, "time_to_result_ms": 1195.0245388000137, "total_latency_ms": 1190.1699430998935, "wer": 0.4037184594953519}`
- white:custom_10db: `{"audio_duration_sec": 9.1525, "cer": 0.03693853427895981, "confidence": 0.6108970524754765, "cpu_percent": 19.7211407120428, "cpu_percent_mean": 15.457656062897218, "cpu_percent_peak": 100.0, "declared_audio_duration_sec": 9.1525, "duration_mismatch_sec": 0.0, "end_to_end_latency_ms": 1092.3419227665363, "end_to_end_rtf": 0.14241757630455093, "estimated_cost_usd": 0.0, "failure_rate": 0.0, "gpu_memory_mb": 1893.6011416361416, "gpu_memory_mb_mean": 2537.867329489743, "gpu_memory_mb_peak": 4644.0, "gpu_util_percent": 28.570970695970697, "gpu_util_percent_mean": 31.479674681735165, "gpu_util_percent_peak": 76.0, "inference_ms": 1087.53883436666, "measured_audio_duration_sec": 9.1525, "memory_mb": 1474.540863223957, "memory_mb_mean": 1719.5611022819082, "memory_mb_peak": 3401.70703125, "per_utterance_latency_ms": 1087.7530935998645, "postprocess_ms": 0.08779996660450706, "preprocess_ms": 0.1264592665999468, "provider_compute_latency_ms": 1087.7530935998645, "provider_compute_rtf": 0.14185235090460113, "real_time_factor": 0.14185235090460113, "sample_accuracy": 0.3333333333333333, "success_rate": 1.0, "time_to_final_result_ms": 1092.3419227665363, "time_to_first_result_ms": 1092.3419227665363, "time_to_result_ms": 1092.3419227665363, "total_latency_ms": 1087.7530935998645, "wer": 0.06640106241699867}`
- white:custom_20db: `{"audio_duration_sec": 9.1525, "cer": 0.024822695035460994, "confidence": 0.6249539756645113, "cpu_percent": 19.280409180387895, "cpu_percent_mean": 15.42454277634987, "cpu_percent_peak": 100.0, "declared_audio_duration_sec": 9.1525, "duration_mismatch_sec": 0.0, "end_to_end_latency_ms": 1082.7364509332863, "end_to_end_rtf": 0.14086198836681527, "estimated_cost_usd": 0.0, "failure_rate": 0.0, "gpu_memory_mb": 1898.3190415140416, "gpu_memory_mb_mean": 2553.2578824755174, "gpu_memory_mb_peak": 4654.0, "gpu_util_percent": 29.35949938949939, "gpu_util_percent_mean": 32.59440703932255, "gpu_util_percent_peak": 77.0, "inference_ms": 1077.8458954999526, "measured_audio_duration_sec": 9.1525, "memory_mb": 1468.8339161693514, "memory_mb_mean": 1714.357227661599, "memory_mb_peak": 3382.95703125, "per_utterance_latency_ms": 1078.0432181333708, "postprocess_ms": 0.08711116667351841, "preprocess_ms": 0.11021146674465854, "provider_compute_latency_ms": 1078.0432181333708, "provider_compute_rtf": 0.14028737928352786, "real_time_factor": 0.14028737928352786, "sample_accuracy": 0.36666666666666664, "success_rate": 1.0, "time_to_final_result_ms": 1082.7364509332863, "time_to_first_result_ms": 1082.7364509332863, "time_to_result_ms": 1082.7364509332863, "total_latency_ms": 1078.0432181333708, "wer": 0.04648074369189907}`
- white:custom_5db: `{"audio_duration_sec": 9.1525, "cer": 0.07358156028368794, "confidence": 0.5749277607817226, "cpu_percent": 19.054444108629017, "cpu_percent_mean": 14.747017663242689, "cpu_percent_peak": 100.0, "declared_audio_duration_sec": 9.1525, "duration_mismatch_sec": 0.0, "end_to_end_latency_ms": 1166.8318925666426, "end_to_end_rtf": 0.14966685323708606, "estimated_cost_usd": 0.0, "failure_rate": 0.0, "gpu_memory_mb": 1893.563319088319, "gpu_memory_mb_mean": 2395.314599657362, "gpu_memory_mb_peak": 4645.0, "gpu_util_percent": 27.63962555962556, "gpu_util_percent_mean": 31.08159146457219, "gpu_util_percent_peak": 95.0, "inference_ms": 1160.6037739001295, "measured_audio_duration_sec": 9.1525, "memory_mb": 1470.3577554749218, "memory_mb_mean": 1664.9105417506821, "memory_mb_peak": 3398.95703125, "per_utterance_latency_ms": 1160.821733433325, "postprocess_ms": 0.09548096656241493, "preprocess_ms": 0.12247856663331429, "provider_compute_latency_ms": 1160.821733433325, "provider_compute_rtf": 0.14894943633359592, "real_time_factor": 0.14894943633359592, "sample_accuracy": 0.3, "success_rate": 1.0, "time_to_final_result_ms": 1166.8318925666426, "time_to_first_result_ms": 1166.8318925666426, "time_to_result_ms": 1166.8318925666426, "total_latency_ms": 1160.821733433325, "wer": 0.12881806108897742}`
