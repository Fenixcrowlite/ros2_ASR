# Benchmark Summary: thesis_local_20260503T220622Z

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
- latency_metrics: `{"end_to_end_latency_ms": 1677.4636760800604, "end_to_end_rtf": 0.23687942344707946, "inference_ms": 1676.6043629799606, "per_utterance_latency_ms": 1677.2042041798522, "postprocess_ms": 0.11405329993067426, "preprocess_ms": 0.4857878999609966, "provider_compute_latency_ms": 1677.2042041798522, "provider_compute_rtf": 0.23683875109933183, "real_time_factor": 0.23683875109933183, "time_to_final_result_ms": 1677.4636760800604, "time_to_first_result_ms": 1677.4636760800604, "time_to_result_ms": 1677.4636760800604, "total_latency_ms": 1677.2042041798522}`
- reliability_metrics: `{"failure_rate": 0.0, "success_rate": 1.0}`
- cost_metrics: `{"estimated_cost_usd": 0.0}`
- cost_totals: `{"estimated_cost_usd": 0.0}`
- estimated_cost_total_usd: `0.0`

### providers/vosk_local (preset: `en_small`)
- samples: `50`
- successful_samples: `49`
- failed_samples: `1`
- quality_metrics: `{"cer": 0.18670212765957447, "confidence": 0.8987295188096863, "sample_accuracy": 0.08, "wer": 0.25258964143426293}`
- latency_metrics: `{"end_to_end_latency_ms": 1228.1347319600172, "end_to_end_rtf": 0.14891879500759242, "inference_ms": 1208.5676009000235, "per_utterance_latency_ms": 1213.8204251000752, "postprocess_ms": 0.08121265998852323, "preprocess_ms": 5.171611540063168, "provider_compute_latency_ms": 1213.8204251000752, "provider_compute_rtf": 0.14722146871939512, "real_time_factor": 0.14722146871939512, "time_to_final_result_ms": 1228.1347319600172, "time_to_first_result_ms": 1228.1347319600172, "time_to_result_ms": 1228.1347319600172, "total_latency_ms": 1213.8204251000752}`
- reliability_metrics: `{"failure_rate": 0.02, "success_rate": 0.98}`
- cost_metrics: `{"estimated_cost_usd": 0.0}`
- cost_totals: `{"estimated_cost_usd": 0.0}`
- estimated_cost_total_usd: `0.0`

### providers/whisper_local (preset: `light`)
- samples: `50`
- successful_samples: `50`
- failed_samples: `0`
- quality_metrics: `{"cer": 0.07180851063829788, "confidence": 0.849739053650733, "sample_accuracy": 0.22, "wer": 0.12270916334661354}`
- latency_metrics: `{"end_to_end_latency_ms": 582.5294616999417, "end_to_end_rtf": 0.08901182084172572, "inference_ms": 540.0442780799858, "per_utterance_latency_ms": 582.1918116400411, "postprocess_ms": 0.08494062007230241, "preprocess_ms": 42.062592939983006, "provider_compute_latency_ms": 582.1918116400411, "provider_compute_rtf": 0.08895962244919065, "real_time_factor": 0.08895962244919065, "time_to_final_result_ms": 582.5294616999417, "time_to_first_result_ms": 582.5294616999417, "time_to_result_ms": 582.5294616999417, "total_latency_ms": 582.1918116400411}`
- reliability_metrics: `{"failure_rate": 0.0, "success_rate": 1.0}`
- cost_metrics: `{"estimated_cost_usd": 0.0}`
- cost_totals: `{"estimated_cost_usd": 0.0}`
- estimated_cost_total_usd: `0.0`

## Noise Summary
- clean: `{"audio_duration_sec": 9.1525, "cer": 0.01950354609929078, "confidence": 0.6222468858925801, "cpu_percent": 17.094486545116965, "cpu_percent_mean": 13.52329664812252, "cpu_percent_peak": 100.0, "declared_audio_duration_sec": 9.1525, "duration_mismatch_sec": 0.0, "end_to_end_latency_ms": 1362.7500612666154, "end_to_end_rtf": 0.22144919316719844, "estimated_cost_usd": 0.0, "failure_rate": 0.0, "gpu_memory_mb": 1714.6020512820512, "gpu_memory_mb_mean": 2038.8294496874178, "gpu_memory_mb_peak": 4637.0, "gpu_util_percent": 14.897054131054132, "gpu_util_percent_mean": 18.81209861292629, "gpu_util_percent_peak": 86.0, "inference_ms": 1279.194437033281, "measured_audio_duration_sec": 9.1525, "memory_mb": 1413.7594482803552, "memory_mb_mean": 1563.0257760749726, "memory_mb_peak": 3372.12890625, "per_utterance_latency_ms": 1358.3773421333415, "postprocess_ms": 0.10049053338055576, "preprocess_ms": 79.0824145666799, "provider_compute_latency_ms": 1358.3773421333415, "provider_compute_rtf": 0.22091418400778517, "real_time_factor": 0.22091418400778517, "sample_accuracy": 0.4, "success_rate": 1.0, "time_to_final_result_ms": 1362.7500612666154, "time_to_first_result_ms": 1362.7500612666154, "time_to_result_ms": 1362.7500612666154, "total_latency_ms": 1358.3773421333415, "wer": 0.03718459495351926}`
- white:custom_0db: `{"audio_duration_sec": 9.1525, "cer": 0.30910165484633567, "confidence": 0.48108861261974156, "cpu_percent": 18.888960068311462, "cpu_percent_mean": 14.161611269332651, "cpu_percent_peak": 100.0, "declared_audio_duration_sec": 9.1525, "duration_mismatch_sec": 0.0, "end_to_end_latency_ms": 1171.0944259333398, "end_to_end_rtf": 0.14603737646158446, "estimated_cost_usd": 0.0, "failure_rate": 0.03333333333333333, "gpu_memory_mb": 1807.6674603174604, "gpu_memory_mb_mean": 2211.0932006691514, "gpu_memory_mb_peak": 4637.0, "gpu_util_percent": 14.567103174603174, "gpu_util_percent_mean": 18.7493849013871, "gpu_util_percent_peak": 75.0, "inference_ms": 1165.7866823999939, "measured_audio_duration_sec": 9.1525, "memory_mb": 1467.1689825785509, "memory_mb_mean": 1623.2707414445106, "memory_mb_peak": 3358.30859375, "per_utterance_latency_ms": 1165.9912153999965, "postprocess_ms": 0.10002666670819356, "preprocess_ms": 0.10450633329431487, "provider_compute_latency_ms": 1165.9912153999965, "provider_compute_rtf": 0.14544936671980566, "real_time_factor": 0.14544936671980566, "sample_accuracy": 0.1, "success_rate": 0.9666666666666667, "time_to_final_result_ms": 1171.0944259333398, "time_to_first_result_ms": 1171.0944259333398, "time_to_result_ms": 1171.0944259333398, "total_latency_ms": 1165.9912153999965, "wer": 0.4037184594953519}`
- white:custom_10db: `{"audio_duration_sec": 9.1525, "cer": 0.03693853427895981, "confidence": 0.6108970524754765, "cpu_percent": 17.16484857837799, "cpu_percent_mean": 13.605508933138514, "cpu_percent_peak": 100.0, "declared_audio_duration_sec": 9.1525, "duration_mismatch_sec": 0.0, "end_to_end_latency_ms": 1066.3275061666052, "end_to_end_rtf": 0.1384414721871095, "estimated_cost_usd": 0.0, "failure_rate": 0.0, "gpu_memory_mb": 1808.5693528693528, "gpu_memory_mb_mean": 2418.326793719653, "gpu_memory_mb_peak": 4642.0, "gpu_util_percent": 15.017735042735042, "gpu_util_percent_mean": 21.280552489371818, "gpu_util_percent_peak": 84.0, "inference_ms": 1061.2994423334687, "measured_audio_duration_sec": 9.1525, "memory_mb": 1463.6968699946824, "memory_mb_mean": 1689.1752524313279, "memory_mb_peak": 3375.48046875, "per_utterance_latency_ms": 1061.5017178667586, "postprocess_ms": 0.08860263318031987, "preprocess_ms": 0.11367290010942573, "provider_compute_latency_ms": 1061.5017178667586, "provider_compute_rtf": 0.13786106784717958, "real_time_factor": 0.13786106784717958, "sample_accuracy": 0.3333333333333333, "success_rate": 1.0, "time_to_final_result_ms": 1066.3275061666052, "time_to_first_result_ms": 1066.3275061666052, "time_to_result_ms": 1066.3275061666052, "total_latency_ms": 1061.5017178667586, "wer": 0.06640106241699867}`
- white:custom_20db: `{"audio_duration_sec": 9.1525, "cer": 0.024822695035460994, "confidence": 0.6249539756645113, "cpu_percent": 17.005168146424726, "cpu_percent_mean": 13.560291303440332, "cpu_percent_peak": 90.7, "declared_audio_duration_sec": 9.1525, "duration_mismatch_sec": 0.0, "end_to_end_latency_ms": 1057.3339835334689, "end_to_end_rtf": 0.1369905210382333, "estimated_cost_usd": 0.0, "failure_rate": 0.0, "gpu_memory_mb": 1805.691111111111, "gpu_memory_mb_mean": 2436.3899037133697, "gpu_memory_mb_peak": 4637.0, "gpu_util_percent": 15.05470695970696, "gpu_util_percent_mean": 21.467764351689908, "gpu_util_percent_peak": 80.0, "inference_ms": 1052.6536185332286, "measured_audio_duration_sec": 9.1525, "memory_mb": 1459.0792878990014, "memory_mb_mean": 1695.6202182481197, "memory_mb_peak": 3371.72265625, "per_utterance_latency_ms": 1052.853752266583, "postprocess_ms": 0.08811396673991112, "preprocess_ms": 0.11201976661444253, "provider_compute_latency_ms": 1052.853752266583, "provider_compute_rtf": 0.13643586765000784, "real_time_factor": 0.13643586765000784, "sample_accuracy": 0.36666666666666664, "success_rate": 1.0, "time_to_final_result_ms": 1057.3339835334689, "time_to_first_result_ms": 1057.3339835334689, "time_to_result_ms": 1057.3339835334689, "total_latency_ms": 1052.853752266583, "wer": 0.04648074369189907}`
- white:custom_5db: `{"audio_duration_sec": 9.1525, "cer": 0.07358156028368794, "confidence": 0.5749277607817226, "cpu_percent": 17.50850998962338, "cpu_percent_mean": 13.635405297765136, "cpu_percent_peak": 90.1, "declared_audio_duration_sec": 9.1525, "duration_mismatch_sec": 0.0, "end_to_end_latency_ms": 1156.04047266667, "end_to_end_rtf": 0.14843150263987026, "estimated_cost_usd": 0.0, "failure_rate": 0.0, "gpu_memory_mb": 1808.1518315018316, "gpu_memory_mb_mean": 2281.360744178967, "gpu_memory_mb_peak": 4642.0, "gpu_util_percent": 14.615193325193324, "gpu_util_percent_mean": 19.836867995140153, "gpu_util_percent_peak": 75.0, "inference_ms": 1149.7595562999777, "measured_audio_duration_sec": 9.1525, "memory_mb": 1461.844905858801, "memory_mb_mean": 1641.3267482142194, "memory_mb_peak": 3374.35546875, "per_utterance_latency_ms": 1149.9700405332685, "postprocess_ms": 0.0897771666435195, "preprocess_ms": 0.12070706664720394, "provider_compute_latency_ms": 1149.9700405332685, "provider_compute_rtf": 0.14770591755508442, "real_time_factor": 0.14770591755508442, "sample_accuracy": 0.3, "success_rate": 1.0, "time_to_final_result_ms": 1156.04047266667, "time_to_first_result_ms": 1156.04047266667, "time_to_result_ms": 1156.04047266667, "total_latency_ms": 1149.9700405332685, "wer": 0.12881806108897742}`
