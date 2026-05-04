# Benchmark Summary: thesis_ext_20260504T104122Z_local_librispeech_test_clean_subset

- benchmark_profile: `benchmark/thesis_extended_local_matrix`
- dataset_id: `librispeech_test_clean_subset`
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
- successful_samples: `50`
- failed_samples: `0`
- quality_metrics: `{"cer": 0.019858156028368795, "confidence": 0.0, "sample_accuracy": 0.6, "wer": 0.034262948207171316}`
- latency_metrics: `{"end_to_end_latency_ms": 1771.1244644208637, "end_to_end_rtf": 0.2568012973130316, "inference_ms": 1770.4354370794317, "per_utterance_latency_ms": 1770.8782769803656, "postprocess_ms": 0.10885462092119269, "preprocess_ms": 0.3339852800127119, "provider_compute_latency_ms": 1770.8782769803656, "provider_compute_rtf": 0.2567631016683728, "real_time_factor": 0.2567631016683728, "time_to_final_result_ms": 1771.1244644208637, "time_to_first_result_ms": 1771.1244644208637, "time_to_result_ms": 1771.1244644208637, "total_latency_ms": 1770.8782769803656}`
- reliability_metrics: `{"failure_rate": 0.0, "success_rate": 1.0}`
- cost_metrics: `{"estimated_cost_usd": 0.0}`
- cost_totals: `{"estimated_cost_usd": 0.0}`
- estimated_cost_total_usd: `0.0`

### providers/vosk_local (preset: `en_small`)
- samples: `50`
- successful_samples: `49`
- failed_samples: `1`
- quality_metrics: `{"cer": 0.18670212765957447, "confidence": 0.8987295188096863, "sample_accuracy": 0.08, "wer": 0.25258964143426293}`
- latency_metrics: `{"end_to_end_latency_ms": 1206.6658297597314, "end_to_end_rtf": 0.14852825998390073, "inference_ms": 1182.443338020239, "per_utterance_latency_ms": 1192.1183180813387, "postprocess_ms": 0.09077534021344036, "preprocess_ms": 9.584204720886191, "provider_compute_latency_ms": 1192.1183180813387, "provider_compute_rtf": 0.14675040160747402, "real_time_factor": 0.14675040160747402, "time_to_final_result_ms": 1206.6658297597314, "time_to_first_result_ms": 1206.6658297597314, "time_to_result_ms": 1206.6658297597314, "total_latency_ms": 1192.1183180813387}`
- reliability_metrics: `{"failure_rate": 0.02, "success_rate": 0.98}`
- cost_metrics: `{"estimated_cost_usd": 0.0}`
- cost_totals: `{"estimated_cost_usd": 0.0}`
- estimated_cost_total_usd: `0.0`

### providers/whisper_local (preset: `light`)
- samples: `50`
- successful_samples: `50`
- failed_samples: `0`
- quality_metrics: `{"cer": 0.07180851063829788, "confidence": 0.849739053650733, "sample_accuracy": 0.22, "wer": 0.12270916334661354}`
- latency_metrics: `{"end_to_end_latency_ms": 652.7246938600729, "end_to_end_rtf": 0.10806440303744909, "inference_ms": 548.6577975600085, "per_utterance_latency_ms": 652.3885300208349, "postprocess_ms": 0.0897775408520829, "preprocess_ms": 103.64095491997432, "provider_compute_latency_ms": 652.3885300208349, "provider_compute_rtf": 0.10801029340013836, "real_time_factor": 0.10801029340013836, "time_to_final_result_ms": 652.7246938600729, "time_to_first_result_ms": 652.7246938600729, "time_to_result_ms": 652.7246938600729, "total_latency_ms": 652.3885300208349}`
- reliability_metrics: `{"failure_rate": 0.0, "success_rate": 1.0}`
- cost_metrics: `{"estimated_cost_usd": 0.0}`
- cost_totals: `{"estimated_cost_usd": 0.0}`
- estimated_cost_total_usd: `0.0`

## Noise Summary
- clean: `{"audio_duration_sec": 9.1525, "cer": 0.01950354609929078, "confidence": 0.6222468858925801, "cpu_percent": 17.635976301530466, "cpu_percent_mean": 12.452123073937601, "cpu_percent_peak": 100.0, "declared_audio_duration_sec": 9.1525, "duration_mismatch_sec": 0.0, "end_to_end_latency_ms": 1558.1587217665704, "end_to_end_rtf": 0.2777609701815031, "estimated_cost_usd": 0.0, "failure_rate": 0.0, "gpu_memory_mb": 1888.8624742506597, "gpu_memory_mb_mean": 2106.798283243643, "gpu_memory_mb_peak": 4754.0, "gpu_util_percent": 14.618868653747686, "gpu_util_percent_mean": 15.961942569123643, "gpu_util_percent_peak": 99.0, "inference_ms": 1364.8283985668968, "measured_audio_duration_sec": 9.1525, "memory_mb": 1335.8866558639593, "memory_mb_mean": 1414.9267982544511, "memory_mb_peak": 3195.41796875, "per_utterance_latency_ms": 1553.7097595673306, "postprocess_ms": 0.0932524009840563, "preprocess_ms": 188.78810859944983, "provider_compute_latency_ms": 1553.7097595673306, "provider_compute_rtf": 0.27720256458159814, "real_time_factor": 0.27720256458159814, "sample_accuracy": 0.4, "success_rate": 1.0, "time_to_final_result_ms": 1558.1587217665704, "time_to_first_result_ms": 1558.1587217665704, "time_to_result_ms": 1558.1587217665704, "total_latency_ms": 1553.7097595673306, "wer": 0.03718459495351926}`
- white:custom_0db: `{"audio_duration_sec": 9.1525, "cer": 0.30910165484633567, "confidence": 0.48108861261974156, "cpu_percent": 17.70072374887907, "cpu_percent_mean": 13.605394550699673, "cpu_percent_peak": 90.1, "declared_audio_duration_sec": 9.1525, "duration_mismatch_sec": 0.0, "end_to_end_latency_ms": 1177.1927745343419, "end_to_end_rtf": 0.14765949173817705, "estimated_cost_usd": 0.0, "failure_rate": 0.03333333333333333, "gpu_memory_mb": 1987.7766058941058, "gpu_memory_mb_mean": 2423.7582974370384, "gpu_memory_mb_peak": 4771.0, "gpu_util_percent": 13.595207015207015, "gpu_util_percent_mean": 18.187732998825688, "gpu_util_percent_peak": 88.0, "inference_ms": 1172.0841952660219, "measured_audio_duration_sec": 9.1525, "memory_mb": 1378.4479089501367, "memory_mb_mean": 1523.5544737961739, "memory_mb_peak": 3136.88671875, "per_utterance_latency_ms": 1172.304861900678, "postprocess_ms": 0.11275213449456108, "preprocess_ms": 0.10791450016161737, "provider_compute_latency_ms": 1172.304861900678, "provider_compute_rtf": 0.1470601331764742, "real_time_factor": 0.1470601331764742, "sample_accuracy": 0.1, "success_rate": 0.9666666666666667, "time_to_final_result_ms": 1177.1927745343419, "time_to_first_result_ms": 1177.1927745343419, "time_to_result_ms": 1177.1927745343419, "total_latency_ms": 1172.304861900678, "wer": 0.4037184594953519}`
- white:custom_10db: `{"audio_duration_sec": 9.1525, "cer": 0.03693853427895981, "confidence": 0.6108970524754765, "cpu_percent": 18.020078950203562, "cpu_percent_mean": 14.273744484562542, "cpu_percent_peak": 100.0, "declared_audio_duration_sec": 9.1525, "duration_mismatch_sec": 0.0, "end_to_end_latency_ms": 1078.3587318330926, "end_to_end_rtf": 0.14003165117102237, "estimated_cost_usd": 0.0, "failure_rate": 0.0, "gpu_memory_mb": 1982.6450671550672, "gpu_memory_mb_mean": 2620.398739260574, "gpu_memory_mb_peak": 4772.0, "gpu_util_percent": 14.396007326007327, "gpu_util_percent_mean": 21.165040022059358, "gpu_util_percent_peak": 87.0, "inference_ms": 1073.479382367077, "measured_audio_duration_sec": 9.1525, "memory_mb": 1375.8831874565305, "memory_mb_mean": 1579.6047487747958, "memory_mb_peak": 3204.09375, "per_utterance_latency_ms": 1073.6772918350955, "postprocess_ms": 0.09065080084837973, "preprocess_ms": 0.10725866717014772, "provider_compute_latency_ms": 1073.6772918350955, "provider_compute_rtf": 0.1394572143665919, "real_time_factor": 0.1394572143665919, "sample_accuracy": 0.3333333333333333, "success_rate": 1.0, "time_to_final_result_ms": 1078.3587318330926, "time_to_first_result_ms": 1078.3587318330926, "time_to_result_ms": 1078.3587318330926, "total_latency_ms": 1073.6772918350955, "wer": 0.06640106241699867}`
- white:custom_20db: `{"audio_duration_sec": 9.1525, "cer": 0.024822695035460994, "confidence": 0.6249539756645113, "cpu_percent": 17.785851388234516, "cpu_percent_mean": 14.057714816789906, "cpu_percent_peak": 98.1, "declared_audio_duration_sec": 9.1525, "duration_mismatch_sec": 0.0, "end_to_end_latency_ms": 1079.386568700041, "end_to_end_rtf": 0.14054612021061566, "estimated_cost_usd": 0.0, "failure_rate": 0.0, "gpu_memory_mb": 1981.7238461538461, "gpu_memory_mb_mean": 2638.567649029889, "gpu_memory_mb_peak": 4751.0, "gpu_util_percent": 13.130958485958486, "gpu_util_percent_mean": 20.159511890477727, "gpu_util_percent_peak": 98.0, "inference_ms": 1074.402026066188, "measured_audio_duration_sec": 9.1525, "memory_mb": 1378.2359036580613, "memory_mb_mean": 1586.655474454509, "memory_mb_peak": 3199.63671875, "per_utterance_latency_ms": 1074.638782733382, "postprocess_ms": 0.094133833287439, "preprocess_ms": 0.14262283390659528, "provider_compute_latency_ms": 1074.638782733382, "provider_compute_rtf": 0.13996089255725314, "real_time_factor": 0.13996089255725314, "sample_accuracy": 0.36666666666666664, "success_rate": 1.0, "time_to_final_result_ms": 1079.386568700041, "time_to_first_result_ms": 1079.386568700041, "time_to_result_ms": 1079.386568700041, "total_latency_ms": 1074.638782733382, "wer": 0.04648074369189907}`
- white:custom_5db: `{"audio_duration_sec": 9.1525, "cer": 0.07358156028368794, "confidence": 0.5749277607817226, "cpu_percent": 17.84550844827687, "cpu_percent_mean": 13.990586114208083, "cpu_percent_peak": 100.0, "declared_audio_duration_sec": 9.1525, "duration_mismatch_sec": 0.0, "end_to_end_latency_ms": 1157.7615165670675, "end_to_end_rtf": 0.14965836725598414, "estimated_cost_usd": 0.0, "failure_rate": 0.0, "gpu_memory_mb": 1986.8404965404966, "gpu_memory_mb_mean": 2487.637414633183, "gpu_memory_mb_peak": 4772.0, "gpu_util_percent": 13.660250305250306, "gpu_util_percent_mean": 19.371954742134847, "gpu_util_percent_peak": 85.0, "inference_ms": 1151.1002854999485, "measured_audio_duration_sec": 9.1525, "memory_mb": 1370.7581815688557, "memory_mb_mean": 1532.757306682277, "memory_mb_peak": 3143.31640625, "per_utterance_latency_ms": 1151.311179101079, "postprocess_ms": 0.09155666703009047, "preprocess_ms": 0.11933693410052608, "provider_compute_latency_ms": 1151.311179101079, "provider_compute_rtf": 0.14885885644472455, "real_time_factor": 0.14885885644472455, "sample_accuracy": 0.3, "success_rate": 1.0, "time_to_final_result_ms": 1157.7615165670675, "time_to_first_result_ms": 1157.7615165670675, "time_to_result_ms": 1157.7615165670675, "total_latency_ms": 1151.311179101079, "wer": 0.12881806108897742}`
