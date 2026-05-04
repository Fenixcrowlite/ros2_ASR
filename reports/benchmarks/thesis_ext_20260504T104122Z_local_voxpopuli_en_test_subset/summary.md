# Benchmark Summary: thesis_ext_20260504T104122Z_local_voxpopuli_en_test_subset

- benchmark_profile: `benchmark/thesis_extended_local_matrix`
- dataset_id: `voxpopuli_en_test_subset`
- providers: `providers/whisper_local, providers/vosk_local, providers/huggingface_local`
- scenario: `clean`
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

### providers/huggingface_local (preset: `balanced`)
- samples: `50`
- successful_samples: `50`
- failed_samples: `0`
- quality_metrics: `{"cer": 0.045883293365307755, "confidence": 0.0, "sample_accuracy": 0.24, "wer": 0.12096774193548387}`
- latency_metrics: `{"end_to_end_latency_ms": 1704.925759920152, "end_to_end_rtf": 0.26682758873338064, "inference_ms": 1704.0516203203879, "per_utterance_latency_ms": 1704.6901734209678, "postprocess_ms": 0.12552368047181517, "preprocess_ms": 0.5130294201080687, "provider_compute_latency_ms": 1704.6901734209678, "provider_compute_rtf": 0.26678180201002827, "real_time_factor": 0.26678180201002827, "time_to_final_result_ms": 1704.925759920152, "time_to_first_result_ms": 1704.925759920152, "time_to_result_ms": 1704.925759920152, "total_latency_ms": 1704.6901734209678}`
- reliability_metrics: `{"failure_rate": 0.0, "success_rate": 1.0}`
- cost_metrics: `{"estimated_cost_usd": 0.0}`
- cost_totals: `{"estimated_cost_usd": 0.0}`
- estimated_cost_total_usd: `0.0`

### providers/vosk_local (preset: `en_small`)
- samples: `50`
- successful_samples: `50`
- failed_samples: `0`
- quality_metrics: `{"cer": 0.22334132693844924, "confidence": 0.8719296391819945, "sample_accuracy": 0.02, "wer": 0.3580645161290323}`
- latency_metrics: `{"end_to_end_latency_ms": 1662.9531996007427, "end_to_end_rtf": 0.19249699602573422, "inference_ms": 1633.1784486002289, "per_utterance_latency_ms": 1642.3197555393563, "postprocess_ms": 0.08620081993285567, "preprocess_ms": 9.055106119194534, "provider_compute_latency_ms": 1642.3197555393563, "provider_compute_rtf": 0.19025042318548266, "real_time_factor": 0.19025042318548266, "time_to_final_result_ms": 1662.9531996007427, "time_to_first_result_ms": 1662.9531996007427, "time_to_result_ms": 1662.9531996007427, "total_latency_ms": 1642.3197555393563}`
- reliability_metrics: `{"failure_rate": 0.0, "success_rate": 1.0}`
- cost_metrics: `{"estimated_cost_usd": 0.0}`
- cost_totals: `{"estimated_cost_usd": 0.0}`
- estimated_cost_total_usd: `0.0`

### providers/whisper_local (preset: `light`)
- samples: `50`
- successful_samples: `50`
- failed_samples: `0`
- quality_metrics: `{"cer": 0.17665867306155075, "confidence": 0.810968497819213, "sample_accuracy": 0.1, "wer": 0.3241935483870968}`
- latency_metrics: `{"end_to_end_latency_ms": 659.8528778996842, "end_to_end_rtf": 0.10683543055070588, "inference_ms": 569.653509260097, "per_utterance_latency_ms": 659.5215729996562, "postprocess_ms": 0.09147875942289829, "preprocess_ms": 89.77658498013625, "provider_compute_latency_ms": 659.5215729996562, "provider_compute_rtf": 0.10677539972113302, "real_time_factor": 0.10677539972113302, "time_to_final_result_ms": 659.8528778996842, "time_to_first_result_ms": 659.8528778996842, "time_to_result_ms": 659.8528778996842, "total_latency_ms": 659.5215729996562}`
- reliability_metrics: `{"failure_rate": 0.0, "success_rate": 1.0}`
- cost_metrics: `{"estimated_cost_usd": 0.0}`
- cost_totals: `{"estimated_cost_usd": 0.0}`
- estimated_cost_total_usd: `0.0`

## Noise Summary
- clean: `{"audio_duration_sec": 10.40163125, "cer": 0.050359712230215826, "confidence": 0.6093613093059742, "cpu_percent": 17.223316219642072, "cpu_percent_mean": 13.366373783376012, "cpu_percent_peak": 89.9, "declared_audio_duration_sec": 10.4017, "duration_mismatch_sec": 8.124999999998827e-05, "end_to_end_latency_ms": 1478.7227506996715, "end_to_end_rtf": 0.21941776993260972, "estimated_cost_usd": 0.0, "failure_rate": 0.0, "gpu_memory_mb": 1954.6717442279942, "gpu_memory_mb_mean": 2174.1648552962583, "gpu_memory_mb_peak": 4940.0, "gpu_util_percent": 14.546630591630592, "gpu_util_percent_mean": 16.908340989101458, "gpu_util_percent_peak": 72.0, "inference_ms": 1307.8016622001694, "measured_audio_duration_sec": 10.40163125, "memory_mb": 1426.781562581028, "memory_mb_mean": 1513.374877453023, "memory_mb_peak": 3394.359375, "per_utterance_latency_ms": 1473.0057121009547, "postprocess_ms": 0.1196134010873114, "preprocess_ms": 165.084436499698, "provider_compute_latency_ms": 1473.0057121009547, "provider_compute_rtf": 0.2188244366101001, "real_time_factor": 0.2188244366101001, "sample_accuracy": 0.2, "success_rate": 1.0, "time_to_final_result_ms": 1478.7227506996715, "time_to_first_result_ms": 1478.7227506996715, "time_to_result_ms": 1478.7227506996715, "total_latency_ms": 1473.0057121009547, "wer": 0.13172043010752688}`
- white:custom_0db: `{"audio_duration_sec": 10.40163125, "cer": 0.4281907807087663, "confidence": 0.46550898198317636, "cpu_percent": 18.632610681775155, "cpu_percent_mean": 15.018911601529872, "cpu_percent_peak": 100.0, "declared_audio_duration_sec": 10.4017, "duration_mismatch_sec": 8.124999999998827e-05, "end_to_end_latency_ms": 1560.9072337999048, "end_to_end_rtf": 0.20705203196954344, "estimated_cost_usd": 0.0, "failure_rate": 0.0, "gpu_memory_mb": 2051.771697191697, "gpu_memory_mb_mean": 2118.233273215735, "gpu_memory_mb_peak": 4940.0, "gpu_util_percent": 14.332417582417582, "gpu_util_percent_mean": 16.03548846323418, "gpu_util_percent_peak": 89.0, "inference_ms": 1551.9737135677133, "measured_audio_duration_sec": 10.40163125, "memory_mb": 1476.0648389487765, "memory_mb_mean": 1516.9627061085798, "memory_mb_peak": 3425.203125, "per_utterance_latency_ms": 1552.2007590339247, "postprocess_ms": 0.1040347325518572, "preprocess_ms": 0.12301073365961201, "provider_compute_latency_ms": 1552.2007590339247, "provider_compute_rtf": 0.2060790559056749, "real_time_factor": 0.2060790559056749, "sample_accuracy": 0.0, "success_rate": 1.0, "time_to_final_result_ms": 1560.9072337999048, "time_to_first_result_ms": 1560.9072337999048, "time_to_result_ms": 1560.9072337999048, "total_latency_ms": 1552.2007590339247, "wer": 0.6586021505376344}`
- white:custom_10db: `{"audio_duration_sec": 10.40163125, "cer": 0.08100186517452705, "confidence": 0.5825059434204942, "cpu_percent": 17.692251954240575, "cpu_percent_mean": 14.177782848226753, "cpu_percent_peak": 100.0, "declared_audio_duration_sec": 10.4017, "duration_mismatch_sec": 8.124999999998827e-05, "end_to_end_latency_ms": 1206.0352329344216, "end_to_end_rtf": 0.17081052174509118, "estimated_cost_usd": 0.0, "failure_rate": 0.0, "gpu_memory_mb": 2040.7259583934583, "gpu_memory_mb_mean": 2434.813257113609, "gpu_memory_mb_peak": 4922.0, "gpu_util_percent": 14.197435064935064, "gpu_util_percent_mean": 19.172814674283885, "gpu_util_percent_peak": 87.0, "inference_ms": 1198.8106317003258, "measured_audio_duration_sec": 10.40163125, "memory_mb": 1470.2495381206923, "memory_mb_mean": 1635.425218194299, "memory_mb_peak": 3397.14453125, "per_utterance_latency_ms": 1199.0241093330649, "postprocess_ms": 0.09214400003353755, "preprocess_ms": 0.12133363270550035, "provider_compute_latency_ms": 1199.0241093330649, "provider_compute_rtf": 0.1700408388224298, "real_time_factor": 0.1700408388224298, "sample_accuracy": 0.13333333333333333, "success_rate": 1.0, "time_to_final_result_ms": 1206.0352329344216, "time_to_first_result_ms": 1206.0352329344216, "time_to_result_ms": 1206.0352329344216, "total_latency_ms": 1199.0241093330649, "wer": 0.17338709677419356}`
- white:custom_20db: `{"audio_duration_sec": 10.40163125, "cer": 0.05755395683453238, "confidence": 0.6069339851683384, "cpu_percent": 17.44597889528772, "cpu_percent_mean": 13.87512591562681, "cpu_percent_peak": 100.0, "declared_audio_duration_sec": 10.4017, "duration_mismatch_sec": 8.124999999998827e-05, "end_to_end_latency_ms": 1119.971230833956, "end_to_end_rtf": 0.16465549425609652, "estimated_cost_usd": 0.0, "failure_rate": 0.0, "gpu_memory_mb": 2041.2657936507937, "gpu_memory_mb_mean": 2583.6685323815486, "gpu_memory_mb_peak": 4938.0, "gpu_util_percent": 13.920873015873015, "gpu_util_percent_mean": 19.117781853070436, "gpu_util_percent_peak": 86.0, "inference_ms": 1114.335261599869, "measured_audio_duration_sec": 10.40163125, "memory_mb": 1473.2646329485963, "memory_mb_mean": 1688.6273866441584, "memory_mb_peak": 3396.12890625, "per_utterance_latency_ms": 1114.5445744000124, "postprocess_ms": 0.09516073332633823, "preprocess_ms": 0.11415206681704149, "provider_compute_latency_ms": 1114.5445744000124, "provider_compute_rtf": 0.16398960579797126, "real_time_factor": 0.16398960579797126, "sample_accuracy": 0.2, "success_rate": 1.0, "time_to_final_result_ms": 1119.971230833956, "time_to_first_result_ms": 1119.971230833956, "time_to_result_ms": 1119.971230833956, "total_latency_ms": 1114.5445744000124, "wer": 0.13978494623655913}`
- white:custom_5db: `{"audio_duration_sec": 10.40163125, "cer": 0.12603250732747134, "confidence": 0.5405200084573627, "cpu_percent": 17.909507830079036, "cpu_percent_mean": 14.377546811484061, "cpu_percent_peak": 100.0, "declared_audio_duration_sec": 10.4017, "duration_mismatch_sec": 8.124999999998827e-05, "end_to_end_latency_ms": 1347.2499474330107, "end_to_end_rtf": 0.18166420761302704, "estimated_cost_usd": 0.0, "failure_rate": 0.0, "gpu_memory_mb": 2044.5426343101344, "gpu_memory_mb_mean": 2296.6684630015566, "gpu_memory_mb_peak": 4915.0, "gpu_util_percent": 14.518049450549452, "gpu_util_percent_mean": 17.64620253074168, "gpu_util_percent_peak": 73.0, "inference_ms": 1338.5513612331124, "measured_audio_duration_sec": 10.40163125, "memory_mb": 1472.122479295107, "memory_mb_mean": 1584.7760348913355, "memory_mb_peak": 3394.359375, "per_utterance_latency_ms": 1338.7773483986773, "postprocess_ms": 0.09438589938023749, "preprocess_ms": 0.1316012661845889, "provider_compute_latency_ms": 1338.7773483986773, "provider_compute_rtf": 0.18074543772489723, "real_time_factor": 0.18074543772489723, "sample_accuracy": 0.06666666666666667, "success_rate": 1.0, "time_to_final_result_ms": 1347.2499474330107, "time_to_first_result_ms": 1347.2499474330107, "time_to_result_ms": 1347.2499474330107, "total_latency_ms": 1338.7773483986773, "wer": 0.23521505376344087}`
