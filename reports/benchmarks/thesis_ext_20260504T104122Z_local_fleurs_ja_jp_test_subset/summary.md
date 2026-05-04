# Benchmark Summary: thesis_ext_20260504T104122Z_local_fleurs_ja_jp_test_subset

- benchmark_profile: `benchmark/thesis_extended_local_matrix`
- dataset_id: `fleurs_ja_jp_test_subset`
- providers: `providers/whisper_local, providers/vosk_local, providers/huggingface_local`
- scenario: `clean`
- execution_mode: `batch`
- noise_modes: `none, white`
- noise_levels: `clean, custom_0db, custom_10db, custom_20db, custom_5db`
- aggregate_scope: `provider_only`
- total_samples: `150`
- successful_samples: `147`
- failed_samples: `3`
- aggregate_samples: `150`
- corrupted_samples: `0`

## Per-Provider Summary

### providers/huggingface_local (preset: `balanced`)
- samples: `50`
- successful_samples: `50`
- failed_samples: `0`
- quality_metrics: `{"cer": 0.1761194029850746, "confidence": 0.0, "sample_accuracy": 0.06, "wer": 0.9714285714285714}`
- latency_metrics: `{"end_to_end_latency_ms": 2455.7290783802455, "end_to_end_rtf": 0.15356396175872422, "inference_ms": 2454.6269096397737, "per_utterance_latency_ms": 2455.4714434007474, "postprocess_ms": 0.19307328053400852, "preprocess_ms": 0.6514604804397095, "provider_compute_latency_ms": 2455.4714434007474, "provider_compute_rtf": 0.15354585448933789, "real_time_factor": 0.15354585448933789, "time_to_final_result_ms": 2455.7290783802455, "time_to_first_result_ms": 2455.7290783802455, "time_to_result_ms": 2455.7290783802455, "total_latency_ms": 2455.4714434007474}`
- reliability_metrics: `{"failure_rate": 0.0, "success_rate": 1.0}`
- cost_metrics: `{"estimated_cost_usd": 0.0}`
- cost_totals: `{"estimated_cost_usd": 0.0}`
- estimated_cost_total_usd: `0.0`

### providers/vosk_local (preset: `en_small`)
- samples: `50`
- successful_samples: `47`
- failed_samples: `3`
- quality_metrics: `{"cer": 1.670978441127695, "confidence": 0.6430559077864678, "sample_accuracy": 0.0, "wer": 7.097142857142857}`
- latency_metrics: `{"end_to_end_latency_ms": 2646.719989840203, "end_to_end_rtf": 0.17224597759898178, "inference_ms": 2609.1546371202276, "per_utterance_latency_ms": 2618.2790317799663, "postprocess_ms": 0.11596437980188057, "preprocess_ms": 9.008430279936874, "provider_compute_latency_ms": 2618.2790317799663, "provider_compute_rtf": 0.17036857429668043, "real_time_factor": 0.17036857429668043, "time_to_final_result_ms": 2646.719989840203, "time_to_first_result_ms": 2646.719989840203, "time_to_result_ms": 2646.719989840203, "total_latency_ms": 2618.2790317799663}`
- reliability_metrics: `{"failure_rate": 0.06, "success_rate": 0.94}`
- cost_metrics: `{"estimated_cost_usd": 0.0}`
- cost_totals: `{"estimated_cost_usd": 0.0}`
- estimated_cost_total_usd: `0.0`

### providers/whisper_local (preset: `light`)
- samples: `50`
- successful_samples: `50`
- failed_samples: `0`
- quality_metrics: `{"cer": 0.6281923714759535, "confidence": 0.6874375875362726, "sample_accuracy": 0.04, "wer": 1.16}`
- latency_metrics: `{"end_to_end_latency_ms": 943.8551047797955, "end_to_end_rtf": 0.060456703486639826, "inference_ms": 852.7786046800611, "per_utterance_latency_ms": 943.4982773198863, "postprocess_ms": 0.0890962801349815, "preprocess_ms": 90.63057635969017, "provider_compute_latency_ms": 943.4982773198863, "provider_compute_rtf": 0.06043230896868143, "real_time_factor": 0.06043230896868143, "time_to_final_result_ms": 943.8551047797955, "time_to_first_result_ms": 943.8551047797955, "time_to_result_ms": 943.8551047797955, "total_latency_ms": 943.4982773198863}`
- reliability_metrics: `{"failure_rate": 0.0, "success_rate": 1.0}`
- cost_metrics: `{"estimated_cost_usd": 0.0}`
- cost_totals: `{"estimated_cost_usd": 0.0}`
- estimated_cost_total_usd: `0.0`

## Noise Summary
- clean: `{"audio_duration_sec": 15.251999999999999, "cer": 0.8861249309010503, "confidence": 0.4974719619269577, "cpu_percent": 17.933796572226267, "cpu_percent_mean": 13.877688941458679, "cpu_percent_peak": 100.0, "declared_audio_duration_sec": 15.251999999999999, "duration_mismatch_sec": 0.0, "end_to_end_latency_ms": 2218.8584020999165, "end_to_end_rtf": 0.1349239659886333, "estimated_cost_usd": 0.0, "failure_rate": 0.0, "gpu_memory_mb": 2108.074729880256, "gpu_memory_mb_mean": 2272.5535258634013, "gpu_memory_mb_peak": 5166.0, "gpu_util_percent": 16.2581015037594, "gpu_util_percent_mean": 19.2137406689902, "gpu_util_percent_peak": 72.0, "inference_ms": 2041.790275233264, "measured_audio_duration_sec": 15.251999999999999, "memory_mb": 1476.1805207981733, "memory_mb_mean": 1548.6813350772309, "memory_mb_peak": 3496.28125, "per_utterance_latency_ms": 2208.433500866037, "postprocess_ms": 0.1061374663549941, "preprocess_ms": 166.53708816641787, "provider_compute_latency_ms": 2208.433500866037, "provider_compute_rtf": 0.13423045194237304, "real_time_factor": 0.13423045194237304, "sample_accuracy": 0.06666666666666667, "success_rate": 1.0, "time_to_final_result_ms": 2218.8584020999165, "time_to_first_result_ms": 2218.8584020999165, "time_to_result_ms": 2218.8584020999165, "total_latency_ms": 2208.433500866037, "wer": 4.104761904761904}`
- white:custom_0db: `{"audio_duration_sec": 15.251999999999999, "cer": 0.9093421779988944, "confidence": 0.42159098349371293, "cpu_percent": 18.68677513954753, "cpu_percent_mean": 16.0992668676368, "cpu_percent_peak": 100.0, "declared_audio_duration_sec": 15.251999999999999, "duration_mismatch_sec": 0.0, "end_to_end_latency_ms": 2148.1343086660977, "end_to_end_rtf": 0.13654465534398386, "estimated_cost_usd": 0.0, "failure_rate": 0.0, "gpu_memory_mb": 2195.6980506748155, "gpu_memory_mb_mean": 2285.7600648244693, "gpu_memory_mb_peak": 5171.0, "gpu_util_percent": 16.97825778796367, "gpu_util_percent_mean": 18.810570973198807, "gpu_util_percent_peak": 98.0, "inference_ms": 2140.3244164997886, "measured_audio_duration_sec": 15.251999999999999, "memory_mb": 1513.1268883288, "memory_mb_mean": 1562.8316624319436, "memory_mb_peak": 3431.98046875, "per_utterance_latency_ms": 2140.6086107999727, "postprocess_ms": 0.1276340670301579, "preprocess_ms": 0.15656023315386847, "provider_compute_latency_ms": 2140.6086107999727, "provider_compute_rtf": 0.1360402607195966, "real_time_factor": 0.1360402607195966, "sample_accuracy": 0.0, "success_rate": 1.0, "time_to_final_result_ms": 2148.1343086660977, "time_to_first_result_ms": 2148.1343086660977, "time_to_result_ms": 2148.1343086660977, "total_latency_ms": 2140.6086107999727, "wer": 2.123809523809524}`
- white:custom_10db: `{"audio_duration_sec": 15.251999999999999, "cer": 0.7423991155334438, "confidence": 0.42149203789714085, "cpu_percent": 19.778032928030576, "cpu_percent_mean": 15.01200613062837, "cpu_percent_peak": 100.0, "declared_audio_duration_sec": 15.251999999999999, "duration_mismatch_sec": 0.0, "end_to_end_latency_ms": 1868.9335908343007, "end_to_end_rtf": 0.12173745471982547, "estimated_cost_usd": 0.0, "failure_rate": 0.03333333333333333, "gpu_memory_mb": 2195.861716853408, "gpu_memory_mb_mean": 2552.227184152711, "gpu_memory_mb_peak": 5181.0, "gpu_util_percent": 16.473982259570494, "gpu_util_percent_mean": 19.66686979305575, "gpu_util_percent_peak": 85.0, "inference_ms": 1859.080010366597, "measured_audio_duration_sec": 15.251999999999999, "memory_mb": 1514.4280189268445, "memory_mb_mean": 1658.404315045641, "memory_mb_peak": 3514.97265625, "per_utterance_latency_ms": 1859.3652439323098, "postprocess_ms": 0.13448729951051064, "preprocess_ms": 0.15074626620238027, "provider_compute_latency_ms": 1859.3652439323098, "provider_compute_rtf": 0.12109489524347446, "real_time_factor": 0.12109489524347446, "sample_accuracy": 0.03333333333333333, "success_rate": 0.9666666666666667, "time_to_final_result_ms": 1868.9335908343007, "time_to_first_result_ms": 1868.9335908343007, "time_to_result_ms": 1868.9335908343007, "total_latency_ms": 1859.3652439323098, "wer": 3.0}`
- white:custom_20db: `{"audio_duration_sec": 15.251999999999999, "cer": 0.8253178551686015, "confidence": 0.4874068698979762, "cpu_percent": 18.498176652305983, "cpu_percent_mean": 14.148009822174204, "cpu_percent_peak": 91.9, "declared_audio_duration_sec": 15.251999999999999, "duration_mismatch_sec": 0.0, "end_to_end_latency_ms": 1885.7478563004406, "end_to_end_rtf": 0.12183942715262212, "estimated_cost_usd": 0.0, "failure_rate": 0.0, "gpu_memory_mb": 2193.2897623074095, "gpu_memory_mb_mean": 2503.3906699559843, "gpu_memory_mb_peak": 5175.0, "gpu_util_percent": 18.14678860355331, "gpu_util_percent_mean": 21.001959059439095, "gpu_util_percent_peak": 99.0, "inference_ms": 1874.151010466691, "measured_audio_duration_sec": 15.251999999999999, "memory_mb": 1512.9379232346728, "memory_mb_mean": 1644.9410116972922, "memory_mb_peak": 3513.98828125, "per_utterance_latency_ms": 1874.4351775664352, "postprocess_ms": 0.12582263346606246, "preprocess_ms": 0.15834446627801904, "provider_compute_latency_ms": 1874.4351775664352, "provider_compute_rtf": 0.12111226187426068, "real_time_factor": 0.12111226187426068, "sample_accuracy": 0.06666666666666667, "success_rate": 1.0, "time_to_final_result_ms": 1885.7478563004406, "time_to_first_result_ms": 1885.7478563004406, "time_to_result_ms": 1885.7478563004406, "total_latency_ms": 1874.4351775664352, "wer": 3.638095238095238}`
- white:custom_5db: `{"audio_duration_sec": 15.251999999999999, "cer": 0.7622996130458817, "confidence": 0.3895273056554462, "cpu_percent": 17.81459490754096, "cpu_percent_mean": 14.05626406532494, "cpu_percent_peak": 91.2, "declared_audio_duration_sec": 15.251999999999999, "duration_mismatch_sec": 0.0, "end_to_end_latency_ms": 1955.4994637663185, "end_to_end_rtf": 0.1287322348688449, "estimated_cost_usd": 0.0, "failure_rate": 0.06666666666666667, "gpu_memory_mb": 2196.2883469145236, "gpu_memory_mb_mean": 2469.1591506289533, "gpu_memory_mb_peak": 5204.0, "gpu_util_percent": 16.813833290892113, "gpu_util_percent_mean": 19.566418495658453, "gpu_util_percent_peak": 87.0, "inference_ms": 1945.5878731670964, "measured_audio_duration_sec": 15.251999999999999, "memory_mb": 1510.8021100042417, "memory_mb_mean": 1625.933658231342, "memory_mb_peak": 3431.9765625, "per_utterance_latency_ms": 1945.9053876695787, "postprocess_ms": 0.16947510108972588, "preprocess_ms": 0.14803940139245242, "provider_compute_latency_ms": 1945.9053876695787, "provider_compute_rtf": 0.12810002647812815, "real_time_factor": 0.12810002647812815, "sample_accuracy": 0.0, "success_rate": 0.9333333333333333, "time_to_final_result_ms": 1955.4994637663185, "time_to_first_result_ms": 1955.4994637663185, "time_to_result_ms": 1955.4994637663185, "total_latency_ms": 1945.9053876695787, "wer": 2.5142857142857142}`
