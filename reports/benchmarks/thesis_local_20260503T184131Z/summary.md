# Benchmark Summary: thesis_local_20260503T184131Z

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
- latency_metrics: `{"end_to_end_latency_ms": 1830.8780920999561, "end_to_end_rtf": 0.2580262189532981, "inference_ms": 1830.0770388998717, "per_utterance_latency_ms": 1830.64994922006, "postprocess_ms": 0.11337872012518346, "preprocess_ms": 0.45953160006320104, "provider_compute_latency_ms": 1830.64994922006, "provider_compute_rtf": 0.2579903549078168, "real_time_factor": 0.2579903549078168, "time_to_final_result_ms": 1830.8780920999561, "time_to_first_result_ms": 1830.8780920999561, "time_to_result_ms": 1830.8780920999561, "total_latency_ms": 1830.64994922006}`
- reliability_metrics: `{"failure_rate": 0.0, "success_rate": 1.0}`
- cost_metrics: `{"estimated_cost_usd": 0.0}`
- cost_totals: `{"estimated_cost_usd": 0.0}`
- estimated_cost_total_usd: `0.0`

### providers/vosk_local (preset: `en_small`)
- samples: `50`
- successful_samples: `49`
- failed_samples: `1`
- quality_metrics: `{"cer": 0.18670212765957447, "confidence": 0.8987295188096863, "sample_accuracy": 0.08, "wer": 0.25258964143426293}`
- latency_metrics: `{"end_to_end_latency_ms": 1197.30638938001, "end_to_end_rtf": 0.14718821255717301, "inference_ms": 1175.5370296000547, "per_utterance_latency_ms": 1183.8301773999592, "postprocess_ms": 0.08571069996833103, "preprocess_ms": 8.207437099936215, "provider_compute_latency_ms": 1183.8301773999592, "provider_compute_rtf": 0.145596315277491, "real_time_factor": 0.145596315277491, "time_to_final_result_ms": 1197.30638938001, "time_to_first_result_ms": 1197.30638938001, "time_to_result_ms": 1197.30638938001, "total_latency_ms": 1183.8301773999592}`
- reliability_metrics: `{"failure_rate": 0.02, "success_rate": 0.98}`
- cost_metrics: `{"estimated_cost_usd": 0.0}`
- cost_totals: `{"estimated_cost_usd": 0.0}`
- estimated_cost_total_usd: `0.0`

### providers/whisper_local (preset: `light`)
- samples: `50`
- successful_samples: `50`
- failed_samples: `0`
- quality_metrics: `{"cer": 0.07180851063829788, "confidence": 0.849739053650733, "sample_accuracy": 0.22, "wer": 0.12270916334661354}`
- latency_metrics: `{"end_to_end_latency_ms": 606.7517607799346, "end_to_end_rtf": 0.09473022586437503, "inference_ms": 546.3388934000795, "per_utterance_latency_ms": 606.4434481399803, "postprocess_ms": 0.08207929990021512, "preprocess_ms": 60.02247544000056, "provider_compute_latency_ms": 606.4434481399803, "provider_compute_rtf": 0.09468251796696057, "real_time_factor": 0.09468251796696057, "time_to_final_result_ms": 606.7517607799346, "time_to_first_result_ms": 606.7517607799346, "time_to_result_ms": 606.7517607799346, "total_latency_ms": 606.4434481399803}`
- reliability_metrics: `{"failure_rate": 0.0, "success_rate": 1.0}`
- cost_metrics: `{"estimated_cost_usd": 0.0}`
- cost_totals: `{"estimated_cost_usd": 0.0}`
- estimated_cost_total_usd: `0.0`

## Noise Summary
- clean: `{"audio_duration_sec": 9.1525, "cer": 0.01950354609929078, "confidence": 0.6222468858925801, "cpu_percent": 17.21675910309734, "cpu_percent_mean": 13.68396487055557, "cpu_percent_peak": 91.3, "declared_audio_duration_sec": 9.1525, "duration_mismatch_sec": 0.0, "end_to_end_latency_ms": 1454.3981722333228, "end_to_end_rtf": 0.24481473202756124, "estimated_cost_usd": 0.0, "failure_rate": 0.0, "gpu_memory_mb": 1730.3990231990233, "gpu_memory_mb_mean": 2085.0398728742034, "gpu_memory_mb_peak": 4548.0, "gpu_util_percent": 17.36545177045177, "gpu_util_percent_mean": 20.569217935234672, "gpu_util_percent_peak": 75.0, "inference_ms": 1336.3787584667382, "measured_audio_duration_sec": 9.1525, "memory_mb": 1421.4328415715122, "memory_mb_mean": 1581.0191265761737, "memory_mb_peak": 3369.35546875, "per_utterance_latency_ms": 1450.4761461002392, "postprocess_ms": 0.08711496678491433, "preprocess_ms": 114.01027266671615, "provider_compute_latency_ms": 1450.4761461002392, "provider_compute_rtf": 0.2443139861895409, "real_time_factor": 0.2443139861895409, "sample_accuracy": 0.4, "success_rate": 1.0, "time_to_final_result_ms": 1454.3981722333228, "time_to_first_result_ms": 1454.3981722333228, "time_to_result_ms": 1454.3981722333228, "total_latency_ms": 1450.4761461002392, "wer": 0.03718459495351926}`
- white:custom_0db: `{"audio_duration_sec": 9.1525, "cer": 0.30910165484633567, "confidence": 0.48108861261974156, "cpu_percent": 17.968243597239535, "cpu_percent_mean": 14.237191105308716, "cpu_percent_peak": 90.5, "declared_audio_duration_sec": 9.1525, "duration_mismatch_sec": 0.0, "end_to_end_latency_ms": 1191.6091434666366, "end_to_end_rtf": 0.1490674187625457, "estimated_cost_usd": 0.0, "failure_rate": 0.03333333333333333, "gpu_memory_mb": 1822.074347041847, "gpu_memory_mb_mean": 2327.585943859342, "gpu_memory_mb_peak": 4545.0, "gpu_util_percent": 15.998354145854146, "gpu_util_percent_mean": 20.598903666404066, "gpu_util_percent_peak": 72.0, "inference_ms": 1186.9708828998835, "measured_audio_duration_sec": 9.1525, "memory_mb": 1471.9465015882345, "memory_mb_mean": 1671.041512782208, "memory_mb_peak": 3395.1328125, "per_utterance_latency_ms": 1187.1840015331752, "postprocess_ms": 0.10154509991480154, "preprocess_ms": 0.11157353337694076, "provider_compute_latency_ms": 1187.1840015331752, "provider_compute_rtf": 0.1485572218307216, "real_time_factor": 0.1485572218307216, "sample_accuracy": 0.1, "success_rate": 0.9666666666666667, "time_to_final_result_ms": 1191.6091434666366, "time_to_first_result_ms": 1191.6091434666366, "time_to_result_ms": 1191.6091434666366, "total_latency_ms": 1187.1840015331752, "wer": 0.4037184594953519}`
- white:custom_10db: `{"audio_duration_sec": 9.1525, "cer": 0.03693853427895981, "confidence": 0.6108970524754765, "cpu_percent": 18.896910435370728, "cpu_percent_mean": 15.705923277055781, "cpu_percent_peak": 100.0, "declared_audio_duration_sec": 9.1525, "duration_mismatch_sec": 0.0, "end_to_end_latency_ms": 1114.8094110999107, "end_to_end_rtf": 0.14338030942884603, "estimated_cost_usd": 0.0, "failure_rate": 0.0, "gpu_memory_mb": 1823.453253968254, "gpu_memory_mb_mean": 2514.0261076902148, "gpu_memory_mb_peak": 4558.0, "gpu_util_percent": 16.58335978835979, "gpu_util_percent_mean": 22.57016945813823, "gpu_util_percent_peak": 71.0, "inference_ms": 1110.0284726666662, "measured_audio_duration_sec": 9.1525, "memory_mb": 1463.3385697084757, "memory_mb_mean": 1728.3366470814497, "memory_mb_peak": 3405.2890625, "per_utterance_latency_ms": 1110.25310716653, "postprocess_ms": 0.09850633332462166, "preprocess_ms": 0.1261281665392744, "provider_compute_latency_ms": 1110.25310716653, "provider_compute_rtf": 0.14282522024589914, "real_time_factor": 0.14282522024589914, "sample_accuracy": 0.3333333333333333, "success_rate": 1.0, "time_to_final_result_ms": 1114.8094110999107, "time_to_first_result_ms": 1114.8094110999107, "time_to_result_ms": 1114.8094110999107, "total_latency_ms": 1110.25310716653, "wer": 0.06640106241699867}`
- white:custom_20db: `{"audio_duration_sec": 9.1525, "cer": 0.024822695035460994, "confidence": 0.6249539756645113, "cpu_percent": 19.37333533133533, "cpu_percent_mean": 16.862576248824837, "cpu_percent_peak": 100.0, "declared_audio_duration_sec": 9.1525, "duration_mismatch_sec": 0.0, "end_to_end_latency_ms": 1113.1573882000037, "end_to_end_rtf": 0.14436558300488378, "estimated_cost_usd": 0.0, "failure_rate": 0.0, "gpu_memory_mb": 1821.9492857142857, "gpu_memory_mb_mean": 2535.3214579974137, "gpu_memory_mb_peak": 4559.0, "gpu_util_percent": 17.157896825396826, "gpu_util_percent_mean": 22.452610158370902, "gpu_util_percent_peak": 71.0, "inference_ms": 1108.2643917000798, "measured_audio_duration_sec": 9.1525, "memory_mb": 1467.7267524904928, "memory_mb_mean": 1739.6304017129298, "memory_mb_peak": 3387.78515625, "per_utterance_latency_ms": 1108.4707411668205, "postprocess_ms": 0.08952913334117814, "preprocess_ms": 0.11682033339942184, "provider_compute_latency_ms": 1108.4707411668205, "provider_compute_rtf": 0.1438238953124291, "real_time_factor": 0.1438238953124291, "sample_accuracy": 0.36666666666666664, "success_rate": 1.0, "time_to_final_result_ms": 1113.1573882000037, "time_to_first_result_ms": 1113.1573882000037, "time_to_result_ms": 1113.1573882000037, "total_latency_ms": 1108.4707411668205, "wer": 0.04648074369189907}`
- white:custom_5db: `{"audio_duration_sec": 9.1525, "cer": 0.07358156028368794, "confidence": 0.5749277607817226, "cpu_percent": 17.43603269225328, "cpu_percent_mean": 14.052988185699688, "cpu_percent_peak": 100.0, "declared_audio_duration_sec": 9.1525, "duration_mismatch_sec": 0.0, "end_to_end_latency_ms": 1184.2529554332941, "end_to_end_rtf": 0.15161305240090675, "estimated_cost_usd": 0.0, "failure_rate": 0.0, "gpu_memory_mb": 1823.7527513227512, "gpu_memory_mb_mean": 2363.226125751104, "gpu_memory_mb_peak": 4556.0, "gpu_util_percent": 15.16973544973545, "gpu_util_percent_mean": 20.64690275292388, "gpu_util_percent_peak": 72.0, "inference_ms": 1178.2790974333086, "measured_audio_duration_sec": 9.1525, "memory_mb": 1468.8694160290408, "memory_mb_mean": 1678.6270521925117, "memory_mb_peak": 3414.1328125, "per_utterance_latency_ms": 1178.4886286332342, "postprocess_ms": 0.091918999957367, "preprocess_ms": 0.11761219996818302, "provider_compute_latency_ms": 1178.4886286332342, "provider_compute_rtf": 0.15092832334185655, "real_time_factor": 0.15092832334185655, "sample_accuracy": 0.3, "success_rate": 1.0, "time_to_final_result_ms": 1184.2529554332941, "time_to_first_result_ms": 1184.2529554332941, "time_to_result_ms": 1184.2529554332941, "total_latency_ms": 1178.4886286332342, "wer": 0.12881806108897742}`
