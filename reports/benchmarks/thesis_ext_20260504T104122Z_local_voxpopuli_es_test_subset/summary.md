# Benchmark Summary: thesis_ext_20260504T104122Z_local_voxpopuli_es_test_subset

- benchmark_profile: `benchmark/thesis_extended_local_matrix`
- dataset_id: `voxpopuli_es_test_subset`
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
- quality_metrics: `{"cer": 0.1016036655211913, "confidence": 0.0, "sample_accuracy": 0.12, "wer": 0.15542521994134897}`
- latency_metrics: `{"end_to_end_latency_ms": 2104.5345360793, "end_to_end_rtf": 0.17318148280634835, "inference_ms": 2103.4285403997637, "per_utterance_latency_ms": 2104.273538820271, "postprocess_ms": 0.24662720010383055, "preprocess_ms": 0.5983712204033509, "provider_compute_latency_ms": 2104.273538820271, "provider_compute_rtf": 0.17315566117118042, "real_time_factor": 0.17315566117118042, "time_to_final_result_ms": 2104.5345360793, "time_to_first_result_ms": 2104.5345360793, "time_to_result_ms": 2104.5345360793, "total_latency_ms": 2104.273538820271}`
- reliability_metrics: `{"failure_rate": 0.0, "success_rate": 1.0}`
- cost_metrics: `{"estimated_cost_usd": 0.0}`
- cost_totals: `{"estimated_cost_usd": 0.0}`
- estimated_cost_total_usd: `0.0`

### providers/vosk_local (preset: `en_small`)
- samples: `50`
- successful_samples: `50`
- failed_samples: `0`
- quality_metrics: `{"cer": 0.8040091638029783, "confidence": 0.7386093137823215, "sample_accuracy": 0.0, "wer": 1.3043988269794722}`
- latency_metrics: `{"end_to_end_latency_ms": 3249.936524680088, "end_to_end_rtf": 0.2673832213428284, "inference_ms": 3201.47286339954, "per_utterance_latency_ms": 3210.378762159089, "postprocess_ms": 0.09143753981334157, "preprocess_ms": 8.814461219735676, "provider_compute_latency_ms": 3210.378762159089, "provider_compute_rtf": 0.26398671043328176, "real_time_factor": 0.26398671043328176, "time_to_final_result_ms": 3249.936524680088, "time_to_first_result_ms": 3249.936524680088, "time_to_result_ms": 3249.936524680088, "total_latency_ms": 3210.378762159089}`
- reliability_metrics: `{"failure_rate": 0.0, "success_rate": 1.0}`
- cost_metrics: `{"estimated_cost_usd": 0.0}`
- cost_totals: `{"estimated_cost_usd": 0.0}`
- estimated_cost_total_usd: `0.0`

### providers/whisper_local (preset: `light`)
- samples: `50`
- successful_samples: `50`
- failed_samples: `0`
- quality_metrics: `{"cer": 0.30492554410080186, "confidence": 0.744753158725124, "sample_accuracy": 0.02, "wer": 0.5178885630498534}`
- latency_metrics: `{"end_to_end_latency_ms": 851.8195470997307, "end_to_end_rtf": 0.07476419997222132, "inference_ms": 762.4525237594207, "per_utterance_latency_ms": 851.4702856191434, "postprocess_ms": 0.08421629972872324, "preprocess_ms": 88.93354555999395, "provider_compute_latency_ms": 851.4702856191434, "provider_compute_rtf": 0.07473058225863287, "real_time_factor": 0.07473058225863287, "time_to_final_result_ms": 851.8195470997307, "time_to_first_result_ms": 851.8195470997307, "time_to_result_ms": 851.8195470997307, "total_latency_ms": 851.4702856191434}`
- reliability_metrics: `{"failure_rate": 0.0, "success_rate": 1.0}`
- cost_metrics: `{"estimated_cost_usd": 0.0}`
- cost_totals: `{"estimated_cost_usd": 0.0}`
- estimated_cost_total_usd: `0.0`

## Noise Summary
- clean: `{"audio_duration_sec": 12.540968750000001, "cer": 0.3270332187857961, "confidence": 0.5287640252340087, "cpu_percent": 16.50118691330456, "cpu_percent_mean": 11.815743334895986, "cpu_percent_peak": 91.8, "declared_audio_duration_sec": 12.541, "duration_mismatch_sec": 6.875000000006182e-05, "end_to_end_latency_ms": 2197.4642900323183, "end_to_end_rtf": 0.1748790969562263, "estimated_cost_usd": 0.0, "failure_rate": 0.0, "gpu_memory_mb": 2143.991281271129, "gpu_memory_mb_mean": 2195.477473673346, "gpu_memory_mb_peak": 5709.0, "gpu_util_percent": 16.801187041866555, "gpu_util_percent_mean": 18.411836947333512, "gpu_util_percent_peak": 80.0, "inference_ms": 2021.8015816659317, "measured_audio_duration_sec": 12.540968750000001, "memory_mb": 1455.1002041145346, "memory_mb_mean": 1498.083707952273, "memory_mb_peak": 4354.390625, "per_utterance_latency_ms": 2185.3544261330776, "postprocess_ms": 0.20847536652581766, "preprocess_ms": 163.34436910062018, "provider_compute_latency_ms": 2185.3544261330776, "provider_compute_rtf": 0.17383320118125134, "real_time_factor": 0.17383320118125134, "sample_accuracy": 0.1, "success_rate": 1.0, "time_to_final_result_ms": 2197.4642900323183, "time_to_first_result_ms": 2197.4642900323183, "time_to_result_ms": 2197.4642900323183, "total_latency_ms": 2185.3544261330776, "wer": 0.5962854349951124}`
- white:custom_0db: `{"audio_duration_sec": 12.540968750000001, "cer": 0.6361206567392135, "confidence": 0.4452865560417896, "cpu_percent": 18.567855264517885, "cpu_percent_mean": 13.838578306914368, "cpu_percent_peak": 99.4, "declared_audio_duration_sec": 12.541, "duration_mismatch_sec": 6.875000000006182e-05, "end_to_end_latency_ms": 2234.651690032721, "end_to_end_rtf": 0.18918002524834962, "estimated_cost_usd": 0.0, "failure_rate": 0.0, "gpu_memory_mb": 2255.8986594202897, "gpu_memory_mb_mean": 2084.347427810064, "gpu_memory_mb_peak": 5709.0, "gpu_util_percent": 17.525829020013802, "gpu_util_percent_mean": 15.095500827088774, "gpu_util_percent_peak": 76.0, "inference_ms": 2223.916311732561, "measured_audio_duration_sec": 12.540968750000001, "memory_mb": 1472.8907086066765, "memory_mb_mean": 1438.5721283762377, "memory_mb_peak": 3474.09375, "per_utterance_latency_ms": 2224.1864193330307, "postprocess_ms": 0.12818680042983033, "preprocess_ms": 0.14192080003946708, "provider_compute_latency_ms": 2224.1864193330307, "provider_compute_rtf": 0.1882494620317044, "real_time_factor": 0.1882494620317044, "sample_accuracy": 0.0, "success_rate": 1.0, "time_to_final_result_ms": 2234.651690032721, "time_to_first_result_ms": 2234.651690032721, "time_to_result_ms": 2234.651690032721, "total_latency_ms": 2224.1864193330307, "wer": 0.8914956011730205}`
- white:custom_10db: `{"audio_duration_sec": 12.540968750000001, "cer": 0.3531882397861779, "confidence": 0.4956509701775728, "cpu_percent": 18.172188925800047, "cpu_percent_mean": 13.039815433727346, "cpu_percent_peak": 100.0, "declared_audio_duration_sec": 12.541, "duration_mismatch_sec": 6.875000000006182e-05, "end_to_end_latency_ms": 1998.7815581664715, "end_to_end_rtf": 0.16806421383745523, "estimated_cost_usd": 0.0, "failure_rate": 0.0, "gpu_memory_mb": 2236.3314992877495, "gpu_memory_mb_mean": 2232.309242053849, "gpu_memory_mb_peak": 5709.0, "gpu_util_percent": 17.232961436711438, "gpu_util_percent_mean": 17.63842753214064, "gpu_util_percent_peak": 76.0, "inference_ms": 1982.718244233062, "measured_audio_duration_sec": 12.540968750000001, "memory_mb": 1472.2538992943346, "memory_mb_mean": 1494.750053151118, "memory_mb_peak": 3474.09375, "per_utterance_latency_ms": 1982.977733732696, "postprocess_ms": 0.12318906665313989, "preprocess_ms": 0.1363004329808367, "provider_compute_latency_ms": 1982.977733732696, "provider_compute_rtf": 0.1667160156018237, "real_time_factor": 0.1667160156018237, "sample_accuracy": 0.06666666666666667, "success_rate": 1.0, "time_to_final_result_ms": 1998.7815581664715, "time_to_first_result_ms": 1998.7815581664715, "time_to_result_ms": 1998.7815581664715, "total_latency_ms": 1982.977733732696, "wer": 0.6158357771260997}`
- white:custom_20db: `{"audio_duration_sec": 12.540968750000001, "cer": 0.3381061473844979, "confidence": 0.5278084288409963, "cpu_percent": 18.362122830890897, "cpu_percent_mean": 13.2743980450442, "cpu_percent_peak": 100.0, "declared_audio_duration_sec": 12.541, "duration_mismatch_sec": 6.875000000006182e-05, "end_to_end_latency_ms": 1817.1541447341344, "end_to_end_rtf": 0.1532634690705037, "estimated_cost_usd": 0.0, "failure_rate": 0.0, "gpu_memory_mb": 2234.2410826210826, "gpu_memory_mb_mean": 2368.5562000683813, "gpu_memory_mb_peak": 5709.0, "gpu_util_percent": 17.258570411070412, "gpu_util_percent_mean": 18.509912320938685, "gpu_util_percent_peak": 89.0, "inference_ms": 1803.6397481662182, "measured_audio_duration_sec": 12.540968750000001, "memory_mb": 1471.3621071117198, "memory_mb_mean": 1529.2536689314113, "memory_mb_peak": 3474.09375, "per_utterance_latency_ms": 1803.889436732182, "postprocess_ms": 0.10626563283343178, "preprocess_ms": 0.14342293313044743, "provider_compute_latency_ms": 1803.889436732182, "provider_compute_rtf": 0.15215101519931834, "real_time_factor": 0.15215101519931834, "sample_accuracy": 0.03333333333333333, "success_rate": 1.0, "time_to_final_result_ms": 1817.1541447341344, "time_to_first_result_ms": 1817.1541447341344, "time_to_result_ms": 1817.1541447341344, "total_latency_ms": 1803.889436732182, "wer": 0.6050830889540567}`
- white:custom_5db: `{"audio_duration_sec": 12.540968750000001, "cer": 0.3631156930126002, "confidence": 0.47476080721804176, "cpu_percent": 17.46847097220788, "cpu_percent_mean": 12.895878831690162, "cpu_percent_peak": 91.8, "declared_audio_duration_sec": 12.541, "duration_mismatch_sec": 6.875000000006182e-05, "end_to_end_latency_ms": 2095.765996799552, "end_to_end_rtf": 0.1734947017564619, "estimated_cost_usd": 0.0, "failure_rate": 0.0, "gpu_memory_mb": 2250.346504777429, "gpu_memory_mb_mean": 2166.2376085381647, "gpu_memory_mb_peak": 5709.0, "gpu_util_percent": 18.889283303250693, "gpu_util_percent_mean": 19.130403550934666, "gpu_util_percent_peak": 84.0, "inference_ms": 2080.1806601334342, "measured_audio_duration_sec": 12.540968750000001, "memory_mb": 1476.2792908065699, "memory_mb_mean": 1473.4882635231772, "memory_mb_peak": 3474.09375, "per_utterance_latency_ms": 2080.462961733186, "postprocess_ms": 0.13768486630093926, "preprocess_ms": 0.14461673345067538, "provider_compute_latency_ms": 2080.462961733186, "provider_compute_rtf": 0.17217189575772734, "real_time_factor": 0.17217189575772734, "sample_accuracy": 0.03333333333333333, "success_rate": 1.0, "time_to_final_result_ms": 2095.765996799552, "time_to_first_result_ms": 2095.765996799552, "time_to_result_ms": 2095.765996799552, "total_latency_ms": 2080.462961733186, "wer": 0.5874877810361682}`
