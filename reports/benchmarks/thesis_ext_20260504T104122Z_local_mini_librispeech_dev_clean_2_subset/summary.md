# Benchmark Summary: thesis_ext_20260504T104122Z_local_mini_librispeech_dev_clean_2_subset

- benchmark_profile: `benchmark/thesis_extended_local_matrix`
- dataset_id: `mini_librispeech_dev_clean_2_subset`
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
- quality_metrics: `{"cer": 0.046052631578947366, "confidence": 0.0, "sample_accuracy": 0.48, "wer": 0.09069767441860466}`
- latency_metrics: `{"end_to_end_latency_ms": 1361.0833130800165, "end_to_end_rtf": 0.28334627431530734, "inference_ms": 1360.449839620269, "per_utterance_latency_ms": 1360.8286254009, "postprocess_ms": 0.11970674007898197, "preprocess_ms": 0.2590790405520238, "provider_compute_latency_ms": 1360.8286254009, "provider_compute_rtf": 0.2832890664826575, "real_time_factor": 0.2832890664826575, "time_to_final_result_ms": 1361.0833130800165, "time_to_first_result_ms": 1361.0833130800165, "time_to_result_ms": 1361.0833130800165, "total_latency_ms": 1360.8286254009}`
- reliability_metrics: `{"failure_rate": 0.0, "success_rate": 1.0}`
- cost_metrics: `{"estimated_cost_usd": 0.0}`
- cost_totals: `{"estimated_cost_usd": 0.0}`
- estimated_cost_total_usd: `0.0`

### providers/vosk_local (preset: `en_small`)
- samples: `50`
- successful_samples: `50`
- failed_samples: `0`
- quality_metrics: `{"cer": 0.23973684210526316, "confidence": 0.8551606253717775, "sample_accuracy": 0.14, "wer": 0.33372093023255817}`
- latency_metrics: `{"end_to_end_latency_ms": 1076.2270736797655, "end_to_end_rtf": 0.21607684152987494, "inference_ms": 1054.8555562195543, "per_utterance_latency_ms": 1063.423100420623, "postprocess_ms": 0.08613336060079746, "preprocess_ms": 8.481410840468016, "provider_compute_latency_ms": 1063.423100420623, "provider_compute_rtf": 0.21351830858317403, "real_time_factor": 0.21351830858317403, "time_to_final_result_ms": 1076.2270736797655, "time_to_first_result_ms": 1076.2270736797655, "time_to_result_ms": 1076.2270736797655, "total_latency_ms": 1063.423100420623}`
- reliability_metrics: `{"failure_rate": 0.0, "success_rate": 1.0}`
- cost_metrics: `{"estimated_cost_usd": 0.0}`
- cost_totals: `{"estimated_cost_usd": 0.0}`
- estimated_cost_total_usd: `0.0`

### providers/whisper_local (preset: `light`)
- samples: `50`
- successful_samples: `50`
- failed_samples: `0`
- quality_metrics: `{"cer": 0.15605263157894736, "confidence": 0.7879330943414635, "sample_accuracy": 0.18, "wer": 0.26627906976744187}`
- latency_metrics: `{"end_to_end_latency_ms": 561.2102697006776, "end_to_end_rtf": 0.11615606885361271, "inference_ms": 485.2131703795749, "per_utterance_latency_ms": 560.8920258798753, "postprocess_ms": 0.08896642015315592, "preprocess_ms": 75.58988908014726, "provider_compute_latency_ms": 560.8920258798753, "provider_compute_rtf": 0.11608681716399726, "real_time_factor": 0.11608681716399726, "time_to_final_result_ms": 561.2102697006776, "time_to_first_result_ms": 561.2102697006776, "time_to_result_ms": 561.2102697006776, "total_latency_ms": 560.8920258798753}`
- reliability_metrics: `{"failure_rate": 0.0, "success_rate": 1.0}`
- cost_metrics: `{"estimated_cost_usd": 0.0}`
- cost_totals: `{"estimated_cost_usd": 0.0}`
- estimated_cost_total_usd: `0.0`

## Noise Summary
- clean: `{"audio_duration_sec": 5.2065, "cer": 0.014912280701754385, "confidence": 0.6343034384764784, "cpu_percent": 15.357917502667503, "cpu_percent_mean": 11.05953313307131, "cpu_percent_peak": 83.2, "declared_audio_duration_sec": 5.2065, "duration_mismatch_sec": 0.0, "end_to_end_latency_ms": 1185.698389867078, "end_to_end_rtf": 0.22946761238393837, "estimated_cost_usd": 0.0, "failure_rate": 0.0, "gpu_memory_mb": 1722.8327777777777, "gpu_memory_mb_mean": 1900.5562074585775, "gpu_memory_mb_peak": 4105.0, "gpu_util_percent": 11.726888888888888, "gpu_util_percent_mean": 13.539503853184726, "gpu_util_percent_peak": 73.0, "inference_ms": 1042.1964432993263, "measured_audio_duration_sec": 5.2065, "memory_mb": 1398.402134796627, "memory_mb_mean": 1489.2265766314445, "memory_mb_peak": 3347.3515625, "per_utterance_latency_ms": 1182.487439699374, "postprocess_ms": 0.08805606630630791, "preprocess_ms": 140.20294033374134, "provider_compute_latency_ms": 1182.487439699374, "provider_compute_rtf": 0.2288166052744472, "real_time_factor": 0.2288166052744472, "sample_accuracy": 0.5666666666666667, "success_rate": 1.0, "time_to_final_result_ms": 1185.698389867078, "time_to_first_result_ms": 1185.698389867078, "time_to_result_ms": 1185.698389867078, "total_latency_ms": 1182.487439699374, "wer": 0.046511627906976744}`
- white:custom_0db: `{"audio_duration_sec": 5.2065, "cer": 0.40789473684210525, "confidence": 0.42800469799192653, "cpu_percent": 17.30924034951976, "cpu_percent_mean": 13.253619097013818, "cpu_percent_peak": 100.0, "declared_audio_duration_sec": 5.2065, "duration_mismatch_sec": 0.0, "end_to_end_latency_ms": 1038.0603086676274, "end_to_end_rtf": 0.21529879631058227, "estimated_cost_usd": 0.0, "failure_rate": 0.0, "gpu_memory_mb": 1808.6052777777777, "gpu_memory_mb_mean": 2031.2386405696718, "gpu_memory_mb_peak": 4104.0, "gpu_util_percent": 12.569722222222222, "gpu_util_percent_mean": 14.76092673415268, "gpu_util_percent_peak": 72.0, "inference_ms": 1032.5497345666615, "measured_audio_duration_sec": 5.2065, "memory_mb": 1441.2312003504053, "memory_mb_mean": 1556.487357246544, "memory_mb_peak": 3362.203125, "per_utterance_latency_ms": 1032.7438218349319, "postprocess_ms": 0.10818480053179276, "preprocess_ms": 0.08590246773868178, "provider_compute_latency_ms": 1032.7438218349319, "provider_compute_rtf": 0.2142195935576685, "real_time_factor": 0.2142195935576685, "sample_accuracy": 0.06666666666666667, "success_rate": 1.0, "time_to_final_result_ms": 1038.0603086676274, "time_to_first_result_ms": 1038.0603086676274, "time_to_result_ms": 1038.0603086676274, "total_latency_ms": 1032.7438218349319, "wer": 0.5678294573643411}`
- white:custom_10db: `{"audio_duration_sec": 5.2065, "cer": 0.09912280701754386, "confidence": 0.5550112212118967, "cpu_percent": 17.41054256854257, "cpu_percent_mean": 13.982052137693946, "cpu_percent_peak": 100.0, "declared_audio_duration_sec": 5.2065, "duration_mismatch_sec": 0.0, "end_to_end_latency_ms": 922.194098100105, "end_to_end_rtf": 0.19245319360236077, "estimated_cost_usd": 0.0, "failure_rate": 0.0, "gpu_memory_mb": 1807.09, "gpu_memory_mb_mean": 2207.2297224754243, "gpu_memory_mb_peak": 4102.0, "gpu_util_percent": 11.876111111111111, "gpu_util_percent_mean": 15.163003194539955, "gpu_util_percent_peak": 71.0, "inference_ms": 917.193646266484, "measured_audio_duration_sec": 5.2065, "memory_mb": 1439.208160105953, "memory_mb_mean": 1624.4385336730434, "memory_mb_peak": 3274.56640625, "per_utterance_latency_ms": 917.3730998343672, "postprocess_ms": 0.09053496760316193, "preprocess_ms": 0.08891860027991545, "provider_compute_latency_ms": 917.3730998343672, "provider_compute_rtf": 0.1914677584951356, "real_time_factor": 0.1914677584951356, "sample_accuracy": 0.2, "success_rate": 1.0, "time_to_final_result_ms": 922.194098100105, "time_to_first_result_ms": 922.194098100105, "time_to_result_ms": 922.194098100105, "total_latency_ms": 917.3730998343672, "wer": 0.16279069767441862}`
- white:custom_20db: `{"audio_duration_sec": 5.2065, "cer": 0.035964912280701755, "confidence": 0.6111072484849261, "cpu_percent": 16.93902737077737, "cpu_percent_mean": 13.833056493161534, "cpu_percent_peak": 100.0, "declared_audio_duration_sec": 5.2065, "duration_mismatch_sec": 0.0, "end_to_end_latency_ms": 841.3768756994008, "end_to_end_rtf": 0.17717475545378447, "estimated_cost_usd": 0.0, "failure_rate": 0.0, "gpu_memory_mb": 1807.22, "gpu_memory_mb_mean": 2326.7244429094976, "gpu_memory_mb_peak": 4105.0, "gpu_util_percent": 13.716111111111111, "gpu_util_percent_mean": 17.729910439432686, "gpu_util_percent_peak": 76.0, "inference_ms": 838.0247487334904, "measured_audio_duration_sec": 5.2065, "memory_mb": 1439.9055614459326, "memory_mb_mean": 1677.9444661986072, "memory_mb_peak": 3354.7578125, "per_utterance_latency_ms": 838.2161092333263, "postprocess_ms": 0.10755756666185334, "preprocess_ms": 0.08380293317410785, "provider_compute_latency_ms": 838.2161092333263, "provider_compute_rtf": 0.1765378017061144, "real_time_factor": 0.1765378017061144, "sample_accuracy": 0.3333333333333333, "success_rate": 1.0, "time_to_final_result_ms": 841.3768756994008, "time_to_first_result_ms": 841.3768756994008, "time_to_result_ms": 841.3768756994008, "total_latency_ms": 838.2161092333263, "wer": 0.0872093023255814}`
- white:custom_5db: `{"audio_duration_sec": 5.2065, "cer": 0.17850877192982456, "confidence": 0.5100629266901738, "cpu_percent": 17.883097832722832, "cpu_percent_mean": 14.215014534371505, "cpu_percent_peak": 100.0, "declared_audio_duration_sec": 5.2065, "duration_mismatch_sec": 0.0, "end_to_end_latency_ms": 1010.2047550998881, "end_to_end_rtf": 0.21157095008065918, "estimated_cost_usd": 0.0, "failure_rate": 0.0, "gpu_memory_mb": 1808.5333333333333, "gpu_memory_mb_mean": 2061.6753630071694, "gpu_memory_mb_peak": 4103.0, "gpu_util_percent": 13.490555555555556, "gpu_util_percent_mean": 15.33361526977785, "gpu_util_percent_peak": 74.0, "inference_ms": 1004.2330374997013, "measured_audio_duration_sec": 5.2065, "memory_mb": 1434.661877312141, "memory_mb_mean": 1562.9793508543064, "memory_mb_peak": 3357.546875, "per_utterance_latency_ms": 1004.4191155669978, "postprocess_ms": 0.09701080028510962, "preprocess_ms": 0.08906726701146302, "provider_compute_latency_ms": 1004.4191155669978, "provider_compute_rtf": 0.21044856134968223, "real_time_factor": 0.21044856134968223, "sample_accuracy": 0.16666666666666666, "success_rate": 1.0, "time_to_final_result_ms": 1010.2047550998881, "time_to_first_result_ms": 1010.2047550998881, "time_to_result_ms": 1010.2047550998881, "total_latency_ms": 1004.4191155669978, "wer": 0.2868217054263566}`
