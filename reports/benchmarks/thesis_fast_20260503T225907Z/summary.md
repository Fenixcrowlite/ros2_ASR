# Benchmark Summary: thesis_fast_20260503T225907Z

- benchmark_profile: `benchmark/thesis_tier_fast`
- dataset_id: `librispeech_test_clean_subset`
- providers: `providers/whisper_local, providers/huggingface_local, providers/google_cloud, providers/vosk_local`
- scenario: `noise_robustness`
- execution_mode: `batch`
- noise_modes: `none, white`
- noise_levels: `clean, custom_0db, custom_10db, custom_20db, custom_5db`
- aggregate_scope: `provider_only`
- total_samples: `200`
- successful_samples: `199`
- failed_samples: `1`
- aggregate_samples: `200`
- corrupted_samples: `0`

## Per-Provider Summary

### providers/google_cloud (preset: `light`)
- samples: `50`
- successful_samples: `50`
- failed_samples: `0`
- quality_metrics: `{"cer": 0.08173758865248226, "confidence": 0.9185949981212616, "sample_accuracy": 0.22, "wer": 0.11952191235059761}`
- latency_metrics: `{"end_to_end_latency_ms": 1981.8622515399875, "end_to_end_rtf": 0.2466073437161985, "inference_ms": 1962.2306098399895, "per_utterance_latency_ms": 1980.7674922000115, "postprocess_ms": 0.00024885999664547853, "preprocess_ms": 18.536633500025346, "provider_compute_latency_ms": 1980.7674922000115, "provider_compute_rtf": 0.24645673807761448, "real_time_factor": 0.24645673807761448, "time_to_final_result_ms": 1981.8622515399875, "time_to_first_result_ms": 1981.8622515399875, "time_to_result_ms": 1981.8622515399875, "total_latency_ms": 1980.7674922000115}`
- reliability_metrics: `{"failure_rate": 0.0, "success_rate": 1.0}`
- cost_metrics: `{"estimated_cost_usd": 0.0}`
- cost_totals: `{"estimated_cost_usd": 0.0}`
- estimated_cost_total_usd: `0.0`

### providers/huggingface_local (preset: `light`)
- samples: `50`
- successful_samples: `50`
- failed_samples: `0`
- quality_metrics: `{"cer": 0.10070921985815603, "confidence": 0.0, "sample_accuracy": 0.26, "wer": 0.1450199203187251}`
- latency_metrics: `{"end_to_end_latency_ms": 539.162241740014, "end_to_end_rtf": 0.07624736666109524, "inference_ms": 538.5147320200849, "per_utterance_latency_ms": 538.9266750799834, "postprocess_ms": 0.10681227988243336, "preprocess_ms": 0.305130780016043, "provider_compute_latency_ms": 538.9266750799834, "provider_compute_rtf": 0.07620993603343924, "real_time_factor": 0.07620993603343924, "time_to_final_result_ms": 539.162241740014, "time_to_first_result_ms": 539.162241740014, "time_to_result_ms": 539.162241740014, "total_latency_ms": 538.9266750799834}`
- reliability_metrics: `{"failure_rate": 0.0, "success_rate": 1.0}`
- cost_metrics: `{"estimated_cost_usd": 0.0}`
- cost_totals: `{"estimated_cost_usd": 0.0}`
- estimated_cost_total_usd: `0.0`

### providers/vosk_local (preset: `en_small`)
- samples: `50`
- successful_samples: `49`
- failed_samples: `1`
- quality_metrics: `{"cer": 0.18670212765957447, "confidence": 0.8990661191454645, "sample_accuracy": 0.08, "wer": 0.25258964143426293}`
- latency_metrics: `{"end_to_end_latency_ms": 1258.7089517200548, "end_to_end_rtf": 0.1533455158092782, "inference_ms": 1234.6642952799994, "per_utterance_latency_ms": 1243.329158079905, "postprocess_ms": 0.08181683992006583, "preprocess_ms": 8.583045959985611, "provider_compute_latency_ms": 1243.329158079905, "provider_compute_rtf": 0.15148624982262654, "real_time_factor": 0.15148624982262654, "time_to_final_result_ms": 1258.7089517200548, "time_to_first_result_ms": 1258.7089517200548, "time_to_result_ms": 1258.7089517200548, "total_latency_ms": 1243.329158079905}`
- reliability_metrics: `{"failure_rate": 0.02, "success_rate": 0.98}`
- cost_metrics: `{"estimated_cost_usd": 0.0}`
- cost_totals: `{"estimated_cost_usd": 0.0}`
- estimated_cost_total_usd: `0.0`

### providers/whisper_local (preset: `light`)
- samples: `50`
- successful_samples: `50`
- failed_samples: `0`
- quality_metrics: `{"cer": 0.07180851063829788, "confidence": 0.849739053650733, "sample_accuracy": 0.22, "wer": 0.12270916334661354}`
- latency_metrics: `{"end_to_end_latency_ms": 602.7124299000025, "end_to_end_rtf": 0.09233860790310153, "inference_ms": 557.8992199798995, "per_utterance_latency_ms": 602.3845204599274, "postprocess_ms": 0.08235822004280635, "preprocess_ms": 44.40294225998514, "provider_compute_latency_ms": 602.3845204599274, "provider_compute_rtf": 0.09228945107010553, "real_time_factor": 0.09228945107010553, "time_to_final_result_ms": 602.7124299000025, "time_to_first_result_ms": 602.7124299000025, "time_to_result_ms": 602.7124299000025, "total_latency_ms": 602.3845204599274}`
- reliability_metrics: `{"failure_rate": 0.0, "success_rate": 1.0}`
- cost_metrics: `{"estimated_cost_usd": 0.0}`
- cost_totals: `{"estimated_cost_usd": 0.0}`
- estimated_cost_total_usd: `0.0`

## Noise Summary
- clean: `{"audio_duration_sec": 9.1525, "cer": 0.022384751773049646, "confidence": 0.7066650325831808, "cpu_percent": 14.096217716542716, "cpu_percent_mean": 11.2130173799144, "cpu_percent_peak": 94.4, "declared_audio_duration_sec": 9.1525, "duration_mismatch_sec": 0.0, "end_to_end_latency_ms": 1173.337548849986, "end_to_end_rtf": 0.17197519842412975, "estimated_cost_usd": 0.0, "failure_rate": 0.0, "gpu_memory_mb": 914.8745089285715, "gpu_memory_mb_mean": 829.0463255156772, "gpu_memory_mb_peak": 1606.0, "gpu_util_percent": 13.470297619047619, "gpu_util_percent_mean": 11.213005573654575, "gpu_util_percent_peak": 66.0, "inference_ms": 1080.2451087750114, "measured_audio_duration_sec": 9.1525, "memory_mb": 1674.0934884720857, "memory_mb_mean": 1688.4777299274533, "memory_mb_peak": 2316.7421875, "per_utterance_latency_ms": 1169.4042929999569, "postprocess_ms": 0.06381944999702682, "preprocess_ms": 89.0953647749484, "provider_compute_latency_ms": 1169.4042929999569, "provider_compute_rtf": 0.1714896735546214, "real_time_factor": 0.1714896735546214, "sample_accuracy": 0.275, "success_rate": 1.0, "time_to_final_result_ms": 1173.337548849986, "time_to_first_result_ms": 1173.337548849986, "time_to_result_ms": 1173.337548849986, "total_latency_ms": 1169.4042929999569, "wer": 0.046812749003984064}`
- white:custom_0db: `{"audio_duration_sec": 9.1525, "cer": 0.32734929078014185, "confidence": 0.5648042697105875, "cpu_percent": 15.766941639101166, "cpu_percent_mean": 12.064959559122906, "cpu_percent_peak": 89.9, "declared_audio_duration_sec": 9.1525, "duration_mismatch_sec": 0.0, "end_to_end_latency_ms": 1131.203688200003, "end_to_end_rtf": 0.1324338193006916, "estimated_cost_usd": 0.0, "failure_rate": 0.025, "gpu_memory_mb": 929.2427777777777, "gpu_memory_mb_mean": 833.355477945314, "gpu_memory_mb_peak": 1606.0, "gpu_util_percent": 10.663090277777778, "gpu_util_percent_mean": 10.87078308790042, "gpu_util_percent_peak": 42.0, "inference_ms": 1126.5264855249598, "measured_audio_duration_sec": 9.1525, "memory_mb": 1705.6527697813526, "memory_mb_mean": 1844.9557754051928, "memory_mb_peak": 2131.03125, "per_utterance_latency_ms": 1126.7825012499543, "postprocess_ms": 0.07605682499161048, "preprocess_ms": 0.17995890000293002, "provider_compute_latency_ms": 1126.7825012499543, "provider_compute_rtf": 0.13191743946015916, "real_time_factor": 0.13191743946015916, "sample_accuracy": 0.025, "success_rate": 0.975, "time_to_final_result_ms": 1131.203688200003, "time_to_first_result_ms": 1131.203688200003, "time_to_result_ms": 1131.203688200003, "total_latency_ms": 1126.7825012499543, "wer": 0.4342629482071713}`
- white:custom_10db: `{"audio_duration_sec": 9.1525, "cer": 0.06006205673758865, "confidence": 0.6923283276231613, "cpu_percent": 15.04584146311508, "cpu_percent_mean": 10.468705024944601, "cpu_percent_peak": 91.3, "declared_audio_duration_sec": 9.1525, "duration_mismatch_sec": 0.0, "end_to_end_latency_ms": 1179.308475525022, "end_to_end_rtf": 0.16223210759364948, "estimated_cost_usd": 0.0, "failure_rate": 0.0, "gpu_memory_mb": 930.7162851037851, "gpu_memory_mb_mean": 840.4372488158883, "gpu_memory_mb_peak": 1607.0, "gpu_util_percent": 12.6952297008547, "gpu_util_percent_mean": 10.93249134509799, "gpu_util_percent_peak": 75.0, "inference_ms": 1175.3109992999953, "measured_audio_duration_sec": 9.1525, "memory_mb": 1704.3563711231564, "memory_mb_mean": 1830.1702609473364, "memory_mb_peak": 2241.53125, "per_utterance_latency_ms": 1175.5160177749758, "postprocess_ms": 0.06417634992885723, "preprocess_ms": 0.1408421250516767, "provider_compute_latency_ms": 1175.5160177749758, "provider_compute_rtf": 0.16175927235794646, "real_time_factor": 0.16175927235794646, "sample_accuracy": 0.25, "success_rate": 1.0, "time_to_final_result_ms": 1179.308475525022, "time_to_first_result_ms": 1179.308475525022, "time_to_result_ms": 1179.308475525022, "total_latency_ms": 1175.5160177749758, "wer": 0.08964143426294821}`
- white:custom_20db: `{"audio_duration_sec": 9.1525, "cer": 0.049867021276595744, "confidence": 0.7075441514213223, "cpu_percent": 15.171513086900386, "cpu_percent_mean": 12.041013013663818, "cpu_percent_peak": 95.0, "declared_audio_duration_sec": 9.1525, "duration_mismatch_sec": 0.0, "end_to_end_latency_ms": 939.8060853999823, "end_to_end_rtf": 0.11627754788150897, "estimated_cost_usd": 0.0, "failure_rate": 0.0, "gpu_memory_mb": 931.3159821428571, "gpu_memory_mb_mean": 848.8822415534789, "gpu_memory_mb_peak": 1607.0, "gpu_util_percent": 12.519010989010988, "gpu_util_percent_mean": 11.969339353011614, "gpu_util_percent_peak": 80.0, "inference_ms": 935.5395687749933, "measured_audio_duration_sec": 9.1525, "memory_mb": 1704.5039484647768, "memory_mb_mean": 1803.9100058204713, "memory_mb_peak": 2131.01953125, "per_utterance_latency_ms": 935.7985046749718, "postprocess_ms": 0.06620422502692236, "preprocess_ms": 0.19273167495157395, "provider_compute_latency_ms": 935.7985046749718, "provider_compute_rtf": 0.11574312866975218, "real_time_factor": 0.11574312866975218, "sample_accuracy": 0.25, "success_rate": 1.0, "time_to_final_result_ms": 939.8060853999823, "time_to_first_result_ms": 939.8060853999823, "time_to_result_ms": 939.8060853999823, "total_latency_ms": 935.7985046749718, "wer": 0.07370517928286853}`
- white:custom_5db: `{"audio_duration_sec": 9.1525, "cer": 0.09153368794326242, "confidence": 0.6629084323085719, "cpu_percent": 15.80817946415095, "cpu_percent_mean": 12.323275820735475, "cpu_percent_peak": 100.0, "declared_audio_duration_sec": 9.1525, "duration_mismatch_sec": 0.0, "end_to_end_latency_ms": 1054.4015456500802, "end_to_end_rtf": 0.12775486941211203, "estimated_cost_usd": 0.0, "failure_rate": 0.0, "gpu_memory_mb": 929.6788095238095, "gpu_memory_mb_mean": 839.5173608434927, "gpu_memory_mb_peak": 1607.0, "gpu_util_percent": 12.065456349206348, "gpu_util_percent_mean": 11.568688203808412, "gpu_util_percent_peak": 45.0, "inference_ms": 1049.0139090250068, "measured_audio_duration_sec": 9.1525, "memory_mb": 1704.339699498093, "memory_mb_mean": 1835.35346459714, "memory_mb_peak": 2097.49609375, "per_utterance_latency_ms": 1049.2584905749254, "postprocess_ms": 0.06878839985802188, "preprocess_ms": 0.17579315006059915, "provider_compute_latency_ms": 1049.2584905749254, "provider_compute_rtf": 0.12714345471225305, "real_time_factor": 0.12714345471225305, "sample_accuracy": 0.175, "success_rate": 1.0, "time_to_final_result_ms": 1054.4015456500802, "time_to_first_result_ms": 1054.4015456500802, "time_to_result_ms": 1054.4015456500802, "total_latency_ms": 1049.2584905749254, "wer": 0.1553784860557769}`
