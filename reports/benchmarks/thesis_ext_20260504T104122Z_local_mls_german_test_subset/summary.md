# Benchmark Summary: thesis_ext_20260504T104122Z_local_mls_german_test_subset

- benchmark_profile: `benchmark/thesis_extended_local_matrix`
- dataset_id: `mls_german_test_subset`
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
- quality_metrics: `{"cer": 0.04628647214854111, "confidence": 0.0, "sample_accuracy": 0.14, "wer": 0.13131313131313133}`
- latency_metrics: `{"end_to_end_latency_ms": 1908.560077939619, "end_to_end_rtf": 0.11320547515610553, "inference_ms": 1907.4509563199535, "per_utterance_latency_ms": 1908.2998145585589, "postprocess_ms": 0.1261610999063123, "preprocess_ms": 0.7226971386990044, "provider_compute_latency_ms": 1908.2998145585589, "provider_compute_rtf": 0.11318955635003852, "real_time_factor": 0.11318955635003852, "time_to_final_result_ms": 1908.560077939619, "time_to_first_result_ms": 1908.560077939619, "time_to_result_ms": 1908.560077939619, "total_latency_ms": 1908.2998145585589}`
- reliability_metrics: `{"failure_rate": 0.0, "success_rate": 1.0}`
- cost_metrics: `{"estimated_cost_usd": 0.0}`
- cost_totals: `{"estimated_cost_usd": 0.0}`
- estimated_cost_total_usd: `0.0`

### providers/vosk_local (preset: `en_small`)
- samples: `50`
- successful_samples: `50`
- failed_samples: `0`
- quality_metrics: `{"cer": 0.7107427055702917, "confidence": 0.7268260620898366, "sample_accuracy": 0.0, "wer": 1.1535353535353536}`
- latency_metrics: `{"end_to_end_latency_ms": 2550.138354479859, "end_to_end_rtf": 0.1505475696514142, "inference_ms": 2512.8556665002543, "per_utterance_latency_ms": 2522.144223279465, "postprocess_ms": 0.10745729930931702, "preprocess_ms": 9.181099479901604, "provider_compute_latency_ms": 2522.144223279465, "provider_compute_rtf": 0.14889128299031187, "real_time_factor": 0.14889128299031187, "time_to_final_result_ms": 2550.138354479859, "time_to_first_result_ms": 2550.138354479859, "time_to_result_ms": 2550.138354479859, "total_latency_ms": 2522.144223279465}`
- reliability_metrics: `{"failure_rate": 0.0, "success_rate": 1.0}`
- cost_metrics: `{"estimated_cost_usd": 0.0}`
- cost_totals: `{"estimated_cost_usd": 0.0}`
- estimated_cost_total_usd: `0.0`

### providers/whisper_local (preset: `light`)
- samples: `50`
- successful_samples: `50`
- failed_samples: `0`
- quality_metrics: `{"cer": 0.1916445623342175, "confidence": 0.7342276159836723, "sample_accuracy": 0.0, "wer": 0.44377104377104376}`
- latency_metrics: `{"end_to_end_latency_ms": 752.7879942998698, "end_to_end_rtf": 0.04428232467310076, "inference_ms": 641.9151176990999, "per_utterance_latency_ms": 752.4162836177857, "postprocess_ms": 0.08376463971217163, "preprocess_ms": 110.41740127897356, "provider_compute_latency_ms": 752.4162836177857, "provider_compute_rtf": 0.04425983463007887, "real_time_factor": 0.04425983463007887, "time_to_final_result_ms": 752.7879942998698, "time_to_first_result_ms": 752.7879942998698, "time_to_result_ms": 752.7879942998698, "total_latency_ms": 752.4162836177857}`
- reliability_metrics: `{"failure_rate": 0.0, "success_rate": 1.0}`
- cost_metrics: `{"estimated_cost_usd": 0.0}`
- cost_totals: `{"estimated_cost_usd": 0.0}`
- estimated_cost_total_usd: `0.0`

## Noise Summary
- clean: `{"audio_duration_sec": 16.856, "cer": 0.2413793103448276, "confidence": 0.5428659759768093, "cpu_percent": 13.985143752654349, "cpu_percent_mean": 9.49871930494687, "cpu_percent_peak": 89.9, "declared_audio_duration_sec": 16.856, "duration_mismatch_sec": 0.0, "end_to_end_latency_ms": 1831.5466126664735, "end_to_end_rtf": 0.10555614301247733, "estimated_cost_usd": 0.0, "failure_rate": 0.0, "gpu_memory_mb": 2070.747543100175, "gpu_memory_mb_mean": 2176.2234548274437, "gpu_memory_mb_peak": 4735.0, "gpu_util_percent": 13.014949494949494, "gpu_util_percent_mean": 13.799306398712309, "gpu_util_percent_peak": 75.0, "inference_ms": 1624.0875071329356, "measured_audio_duration_sec": 16.856, "memory_mb": 1351.4807624373382, "memory_mb_mean": 1394.518408445557, "memory_mb_peak": 3194.7265625, "per_utterance_latency_ms": 1824.1066553317069, "postprocess_ms": 0.11315703304717317, "preprocess_ms": 199.90599116572412, "provider_compute_latency_ms": 1824.1066553317069, "provider_compute_rtf": 0.1051174675566083, "real_time_factor": 0.1051174675566083, "sample_accuracy": 0.06666666666666667, "success_rate": 1.0, "time_to_final_result_ms": 1831.5466126664735, "time_to_first_result_ms": 1831.5466126664735, "time_to_result_ms": 1831.5466126664735, "total_latency_ms": 1824.1066553317069, "wer": 0.4781144781144781}`
- white:custom_0db: `{"audio_duration_sec": 16.856, "cer": 0.5026525198938993, "confidence": 0.41834332119754125, "cpu_percent": 15.357995459117026, "cpu_percent_mean": 11.300588437814607, "cpu_percent_peak": 90.6, "declared_audio_duration_sec": 16.856, "duration_mismatch_sec": 0.0, "end_to_end_latency_ms": 2014.991236300072, "end_to_end_rtf": 0.11924976696988192, "estimated_cost_usd": 0.0, "failure_rate": 0.0, "gpu_memory_mb": 2161.39, "gpu_memory_mb_mean": 1989.4844451014817, "gpu_memory_mb_peak": 4735.0, "gpu_util_percent": 14.204107142857143, "gpu_util_percent_mean": 12.486019973335763, "gpu_util_percent_peak": 74.0, "inference_ms": 2005.8940836330294, "measured_audio_duration_sec": 16.856, "memory_mb": 1387.4663806371145, "memory_mb_mean": 1370.8336906350924, "memory_mb_peak": 3133.59375, "per_utterance_latency_ms": 2006.1740643977828, "postprocess_ms": 0.12818559916922823, "preprocess_ms": 0.15179516558418982, "provider_compute_latency_ms": 2006.1740643977828, "provider_compute_rtf": 0.11873234914523359, "real_time_factor": 0.11873234914523359, "sample_accuracy": 0.0, "success_rate": 1.0, "time_to_final_result_ms": 2014.991236300072, "time_to_first_result_ms": 2014.991236300072, "time_to_result_ms": 2014.991236300072, "total_latency_ms": 2006.1740643977828, "wer": 0.8159371492704826}`
- white:custom_10db: `{"audio_duration_sec": 16.856, "cer": 0.268788682581786, "confidence": 0.4974557528975709, "cpu_percent": 15.093438158309784, "cpu_percent_mean": 10.535911014217946, "cpu_percent_peak": 91.3, "declared_audio_duration_sec": 16.856, "duration_mismatch_sec": 0.0, "end_to_end_latency_ms": 1616.860078132595, "end_to_end_rtf": 0.09634261712086621, "estimated_cost_usd": 0.0, "failure_rate": 0.0, "gpu_memory_mb": 2160.3904761904764, "gpu_memory_mb_mean": 2264.0642710533284, "gpu_memory_mb_peak": 4736.0, "gpu_util_percent": 14.360952380952382, "gpu_util_percent_mean": 15.686704613547173, "gpu_util_percent_peak": 76.0, "inference_ms": 1605.955304366459, "measured_audio_duration_sec": 16.856, "memory_mb": 1387.764208092637, "memory_mb_mean": 1448.2564156426706, "memory_mb_peak": 3164.98046875, "per_utterance_latency_ms": 1606.2135767329892, "postprocess_ms": 0.09528186662161413, "preprocess_ms": 0.1629904999087254, "provider_compute_latency_ms": 1606.2135767329892, "provider_compute_rtf": 0.09570808857994338, "real_time_factor": 0.09570808857994338, "sample_accuracy": 0.06666666666666667, "success_rate": 1.0, "time_to_final_result_ms": 1616.860078132595, "time_to_first_result_ms": 1616.860078132595, "time_to_result_ms": 1616.860078132595, "total_latency_ms": 1606.2135767329892, "wer": 0.5218855218855218}`
- white:custom_20db: `{"audio_duration_sec": 16.856, "cer": 0.2486737400530504, "confidence": 0.5255111937662013, "cpu_percent": 14.916608764297852, "cpu_percent_mean": 10.73986970517453, "cpu_percent_peak": 90.0, "declared_audio_duration_sec": 16.856, "duration_mismatch_sec": 0.0, "end_to_end_latency_ms": 1472.4937234997924, "end_to_end_rtf": 0.0879625860409087, "estimated_cost_usd": 0.0, "failure_rate": 0.0, "gpu_memory_mb": 2159.247619047619, "gpu_memory_mb_mean": 2418.066913171214, "gpu_memory_mb_peak": 4735.0, "gpu_util_percent": 14.407936507936508, "gpu_util_percent_mean": 17.51438313287605, "gpu_util_percent_peak": 76.0, "inference_ms": 1462.965841400243, "measured_audio_duration_sec": 16.856, "memory_mb": 1385.0278218002913, "memory_mb_mean": 1488.7358487318756, "memory_mb_peak": 3181.6640625, "per_utterance_latency_ms": 1463.2090963653657, "postprocess_ms": 0.08724166618776508, "preprocess_ms": 0.15601329893494645, "provider_compute_latency_ms": 1463.2090963653657, "provider_compute_rtf": 0.08741232598164529, "real_time_factor": 0.08741232598164529, "sample_accuracy": 0.06666666666666667, "success_rate": 1.0, "time_to_final_result_ms": 1472.4937234997924, "time_to_first_result_ms": 1472.4937234997924, "time_to_result_ms": 1472.4937234997924, "total_latency_ms": 1463.2090963653657, "wer": 0.5050505050505051}`
- white:custom_5db: `{"audio_duration_sec": 16.856, "cer": 0.3196286472148541, "confidence": 0.4509132196177253, "cpu_percent": 14.904072517152017, "cpu_percent_mean": 10.31980026950108, "cpu_percent_peak": 90.0, "declared_audio_duration_sec": 16.856, "duration_mismatch_sec": 0.0, "end_to_end_latency_ms": 1749.9190605999804, "end_to_end_rtf": 0.10428116932356667, "estimated_cost_usd": 0.0, "failure_rate": 0.0, "gpu_memory_mb": 2161.304761904762, "gpu_memory_mb_mean": 2148.64622206052, "gpu_memory_mb_peak": 4736.0, "gpu_util_percent": 14.350793650793651, "gpu_util_percent_mean": 14.38627449293045, "gpu_util_percent_peak": 76.0, "inference_ms": 1738.1334976661794, "measured_audio_duration_sec": 16.856, "memory_mb": 1386.7694848169883, "memory_mb_mean": 1416.2976922506734, "memory_mb_peak": 3170.88671875, "per_utterance_latency_ms": 1738.3971429318383, "postprocess_ms": 0.10510556652055432, "preprocess_ms": 0.15853969913829738, "provider_compute_latency_ms": 1738.3971429318383, "provider_compute_rtf": 0.10359755868728489, "real_time_factor": 0.10359755868728489, "sample_accuracy": 0.03333333333333333, "success_rate": 1.0, "time_to_final_result_ms": 1749.9190605999804, "time_to_first_result_ms": 1749.9190605999804, "time_to_result_ms": 1749.9190605999804, "total_latency_ms": 1738.3971429318383, "wer": 0.5600448933782267}`
