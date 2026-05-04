# Benchmark Summary: thesis_balanced_20260503T232650Z

- benchmark_profile: `benchmark/thesis_tier_balanced`
- dataset_id: `librispeech_test_clean_subset`
- providers: `providers/whisper_local, providers/huggingface_local, providers/google_cloud, providers/azure_cloud, providers/aws_cloud`
- scenario: `noise_robustness`
- execution_mode: `batch`
- noise_modes: `none, white`
- noise_levels: `clean, custom_0db, custom_10db, custom_20db, custom_5db`
- aggregate_scope: `provider_only`
- total_samples: `250`
- successful_samples: `250`
- failed_samples: `0`
- aggregate_samples: `250`
- corrupted_samples: `0`

## Per-Provider Summary

### providers/aws_cloud (preset: `standard`)
- samples: `50`
- successful_samples: `50`
- failed_samples: `0`
- quality_metrics: `{"cer": 0.003900709219858156, "confidence": 0.9991451588117618, "sample_accuracy": 0.88, "wer": 0.005577689243027889}`
- latency_metrics: `{"end_to_end_latency_ms": 10294.25465311997, "end_to_end_rtf": 1.6146547115135148, "inference_ms": 8913.577480279964, "per_utterance_latency_ms": 8913.663299819927, "postprocess_ms": 0.07824204007192748, "preprocess_ms": 0.007577499891340267, "provider_compute_latency_ms": 8913.663299819927, "provider_compute_rtf": 1.3977087388526728, "real_time_factor": 1.3977087388526728, "time_to_final_result_ms": 10294.25465311997, "time_to_first_result_ms": 10294.25465311997, "time_to_result_ms": 10294.25465311997, "total_latency_ms": 8913.663299819927}`
- reliability_metrics: `{"failure_rate": 0.0, "success_rate": 1.0}`
- cost_metrics: `{"estimated_cost_usd": 0.003661}`
- cost_totals: `{"estimated_cost_usd": 0.18305}`
- estimated_cost_total_usd: `0.18305`

### providers/azure_cloud (preset: `standard`)
- samples: `50`
- successful_samples: `50`
- failed_samples: `0`
- quality_metrics: `{"cer": 0.01524822695035461, "confidence": 0.8155070642, "sample_accuracy": 0.72, "wer": 0.02390438247011952}`
- latency_metrics: `{"end_to_end_latency_ms": 3268.648420099744, "end_to_end_rtf": 0.34304287548696283, "inference_ms": 3018.5849860599774, "per_utterance_latency_ms": 3018.6987855400366, "postprocess_ms": 0.10486242008482805, "preprocess_ms": 0.008937059974414296, "provider_compute_latency_ms": 3018.6987855400366, "provider_compute_rtf": 0.302708937788123, "real_time_factor": 0.302708937788123, "time_to_final_result_ms": 3268.648420099744, "time_to_first_result_ms": 3268.648420099744, "time_to_result_ms": 3268.648420099744, "total_latency_ms": 3018.6987855400366}`
- reliability_metrics: `{"failure_rate": 0.0, "success_rate": 1.0}`
- cost_metrics: `{"estimated_cost_usd": 0.00274575}`
- cost_totals: `{"estimated_cost_usd": 0.13728749999999998}`
- estimated_cost_total_usd: `0.13728749999999998`

### providers/google_cloud (preset: `balanced`)
- samples: `50`
- successful_samples: `50`
- failed_samples: `0`
- quality_metrics: `{"cer": 0.03173758865248227, "confidence": 0.9495263803005218, "sample_accuracy": 0.48, "wer": 0.054183266932270914}`
- latency_metrics: `{"end_to_end_latency_ms": 1745.9634368800107, "end_to_end_rtf": 0.2095655669105895, "inference_ms": 1726.0359365600016, "per_utterance_latency_ms": 1744.9849139601429, "postprocess_ms": 0.0001290400541620329, "preprocess_ms": 18.94884836008714, "provider_compute_latency_ms": 1744.9849139601429, "provider_compute_rtf": 0.2094393154147997, "real_time_factor": 0.2094393154147997, "time_to_final_result_ms": 1745.9634368800107, "time_to_first_result_ms": 1745.9634368800107, "time_to_result_ms": 1745.9634368800107, "total_latency_ms": 1744.9849139601429}`
- reliability_metrics: `{"failure_rate": 0.0, "success_rate": 1.0}`
- cost_metrics: `{"estimated_cost_usd": 0.0}`
- cost_totals: `{"estimated_cost_usd": 0.0}`
- estimated_cost_total_usd: `0.0`

### providers/huggingface_local (preset: `balanced`)
- samples: `50`
- successful_samples: `50`
- failed_samples: `0`
- quality_metrics: `{"cer": 0.019858156028368795, "confidence": 0.0, "sample_accuracy": 0.6, "wer": 0.034262948207171316}`
- latency_metrics: `{"end_to_end_latency_ms": 1753.4565197800475, "end_to_end_rtf": 0.2495673995838609, "inference_ms": 1752.7972659200896, "per_utterance_latency_ms": 1753.2157299197934, "postprocess_ms": 0.12398735991155263, "preprocess_ms": 0.2944766397922649, "provider_compute_latency_ms": 1753.2157299197934, "provider_compute_rtf": 0.2495293940281236, "real_time_factor": 0.2495293940281236, "time_to_final_result_ms": 1753.4565197800475, "time_to_first_result_ms": 1753.4565197800475, "time_to_result_ms": 1753.4565197800475, "total_latency_ms": 1753.2157299197934}`
- reliability_metrics: `{"failure_rate": 0.0, "success_rate": 1.0}`
- cost_metrics: `{"estimated_cost_usd": 0.0}`
- cost_totals: `{"estimated_cost_usd": 0.0}`
- estimated_cost_total_usd: `0.0`

### providers/whisper_local (preset: `balanced`)
- samples: `50`
- successful_samples: `50`
- failed_samples: `0`
- quality_metrics: `{"cer": 0.032624113475177303, "confidence": 0.888024330342506, "sample_accuracy": 0.42, "wer": 0.05816733067729084}`
- latency_metrics: `{"end_to_end_latency_ms": 980.8427799800847, "end_to_end_rtf": 0.14919695179028863, "inference_ms": 909.8686695199285, "per_utterance_latency_ms": 980.5282260799868, "postprocess_ms": 0.08738127999095013, "preprocess_ms": 70.57217528006731, "provider_compute_latency_ms": 980.5282260799868, "provider_compute_rtf": 0.14914938114497175, "real_time_factor": 0.14914938114497175, "time_to_final_result_ms": 980.8427799800847, "time_to_first_result_ms": 980.8427799800847, "time_to_result_ms": 980.8427799800847, "total_latency_ms": 980.5282260799868}`
- reliability_metrics: `{"failure_rate": 0.0, "success_rate": 1.0}`
- cost_metrics: `{"estimated_cost_usd": 0.0}`
- cost_totals: `{"estimated_cost_usd": 0.0}`
- estimated_cost_total_usd: `0.0`

## Noise Summary
- clean: `{"audio_duration_sec": 9.1525, "cer": 0.006914893617021276, "confidence": 0.7518706336090033, "cpu_percent": 13.96202681759119, "cpu_percent_mean": 10.950288277698364, "cpu_percent_peak": 100.0, "declared_audio_duration_sec": 9.1525, "duration_mismatch_sec": 0.0, "end_to_end_latency_ms": 3786.2249623601383, "end_to_end_rtf": 0.5714124654545731, "estimated_cost_usd": 0.00128135, "failure_rate": 0.0, "gpu_memory_mb": 1980.2667228245612, "gpu_memory_mb_mean": 1630.737339115488, "gpu_memory_mb_peak": 4798.0, "gpu_util_percent": 18.1929937546114, "gpu_util_percent_mean": 16.614470786230267, "gpu_util_percent_peak": 98.0, "inference_ms": 3363.533386840063, "measured_audio_duration_sec": 9.1525, "memory_mb": 1957.9864218630269, "memory_mb_mean": 2094.598741707899, "memory_mb_peak": 3347.15625, "per_utterance_latency_ms": 3452.9290452801433, "postprocess_ms": 0.07683260009798687, "preprocess_ms": 89.31882583998231, "provider_compute_latency_ms": 3452.9290452801433, "provider_compute_rtf": 0.5185213697173131, "real_time_factor": 0.5185213697173131, "sample_accuracy": 0.76, "success_rate": 1.0, "time_to_final_result_ms": 3786.2249623601383, "time_to_first_result_ms": 3786.2249623601383, "time_to_result_ms": 3786.2249623601383, "total_latency_ms": 3452.9290452801433, "wer": 0.010358565737051793}`
- white:custom_0db: `{"audio_duration_sec": 9.1525, "cer": 0.05531914893617021, "confidence": 0.6859912495534093, "cpu_percent": 14.210549431040779, "cpu_percent_mean": 9.865625399907143, "cpu_percent_peak": 90.0, "declared_audio_duration_sec": 9.1525, "duration_mismatch_sec": 0.0, "end_to_end_latency_ms": 3562.6398520598377, "end_to_end_rtf": 0.49928163322266594, "estimated_cost_usd": 0.00128135, "failure_rate": 0.0, "gpu_memory_mb": 1989.4663750236691, "gpu_memory_mb_mean": 1501.0983831064814, "gpu_memory_mb_peak": 4836.0, "gpu_util_percent": 17.12081417848757, "gpu_util_percent_mean": 14.864825740776917, "gpu_util_percent_peak": 96.0, "inference_ms": 3240.703112880037, "measured_audio_duration_sec": 9.1525, "memory_mb": 1990.5910683289737, "memory_mb_mean": 2174.697552712782, "memory_mb_peak": 3347.15625, "per_utterance_latency_ms": 3240.9213300998817, "postprocess_ms": 0.08381209994695382, "preprocess_ms": 0.13440511989756487, "provider_compute_latency_ms": 3240.9213300998817, "provider_compute_rtf": 0.44964426031875704, "real_time_factor": 0.44964426031875704, "sample_accuracy": 0.38, "success_rate": 1.0, "time_to_final_result_ms": 3562.6398520598377, "time_to_first_result_ms": 3562.6398520598377, "time_to_result_ms": 3562.6398520598377, "total_latency_ms": 3240.9213300998817, "wer": 0.09561752988047809}`
- white:custom_10db: `{"audio_duration_sec": 9.1525, "cer": 0.01400709219858156, "confidence": 0.7417468484058892, "cpu_percent": 13.948148781014346, "cpu_percent_mean": 10.444174854532251, "cpu_percent_peak": 89.9, "declared_audio_duration_sec": 9.1525, "duration_mismatch_sec": 0.0, "end_to_end_latency_ms": 3562.0610839000437, "end_to_end_rtf": 0.49812832108420746, "estimated_cost_usd": 0.00128135, "failure_rate": 0.0, "gpu_memory_mb": 1971.0827787704086, "gpu_memory_mb_mean": 1477.4834259082584, "gpu_memory_mb_peak": 4821.0, "gpu_util_percent": 17.322076314885496, "gpu_util_percent_mean": 15.487594529374482, "gpu_util_percent_peak": 98.0, "inference_ms": 3245.490154459876, "measured_audio_duration_sec": 9.1525, "memory_mb": 1989.2445362275082, "memory_mb_mean": 2167.146704958005, "memory_mb_peak": 3347.15625, "per_utterance_latency_ms": 3245.6880938599716, "postprocess_ms": 0.0735132402041927, "preprocess_ms": 0.1244261598912999, "provider_compute_latency_ms": 3245.6880938599716, "provider_compute_rtf": 0.4479943929049854, "real_time_factor": 0.4479943929049854, "sample_accuracy": 0.64, "success_rate": 1.0, "time_to_final_result_ms": 3562.0610839000437, "time_to_first_result_ms": 3562.0610839000437, "time_to_result_ms": 3562.0610839000437, "total_latency_ms": 3245.6880938599716, "wer": 0.024701195219123506}`
- white:custom_20db: `{"audio_duration_sec": 9.1525, "cer": 0.008333333333333333, "confidence": 0.7460571515303005, "cpu_percent": 14.39974237594336, "cpu_percent_mean": 10.622432461554258, "cpu_percent_peak": 100.0, "declared_audio_duration_sec": 9.1525, "duration_mismatch_sec": 0.0, "end_to_end_latency_ms": 3626.9797195399588, "end_to_end_rtf": 0.5031982985842216, "estimated_cost_usd": 0.00128135, "failure_rate": 0.0, "gpu_memory_mb": 1971.5845230080376, "gpu_memory_mb_mean": 1455.1346392019025, "gpu_memory_mb_peak": 4800.0, "gpu_util_percent": 16.823839691354397, "gpu_util_percent_mean": 14.845340487315811, "gpu_util_percent_peak": 99.0, "inference_ms": 3280.4515239799002, "measured_audio_duration_sec": 9.1525, "memory_mb": 1988.1588447531215, "memory_mb_mean": 2171.128164442266, "memory_mb_peak": 3347.15625, "per_utterance_latency_ms": 3280.6544295598724, "postprocess_ms": 0.07841909995477181, "preprocess_ms": 0.12448648001736728, "provider_compute_latency_ms": 3280.6544295598724, "provider_compute_rtf": 0.447851761712221, "real_time_factor": 0.447851761712221, "sample_accuracy": 0.74, "success_rate": 1.0, "time_to_final_result_ms": 3626.9797195399588, "time_to_first_result_ms": 3626.9797195399588, "time_to_result_ms": 3626.9797195399588, "total_latency_ms": 3280.6544295598724, "wer": 0.014342629482071713}`
- white:custom_5db: `{"audio_duration_sec": 9.1525, "cer": 0.01879432624113475, "confidence": 0.7265370505561873, "cpu_percent": 14.271458799169277, "cpu_percent_mean": 10.631669378932491, "cpu_percent_peak": 100.0, "declared_audio_duration_sec": 9.1525, "duration_mismatch_sec": 0.0, "end_to_end_latency_ms": 3505.260191999878, "end_to_end_rtf": 0.49400678693954836, "estimated_cost_usd": 0.00128135, "failure_rate": 0.0, "gpu_memory_mb": 1968.7627016219076, "gpu_memory_mb_mean": 1470.649217266342, "gpu_memory_mb_peak": 4842.0, "gpu_util_percent": 17.7811093579623, "gpu_util_percent_mean": 15.521847003831942, "gpu_util_percent_peak": 98.0, "inference_ms": 3190.6861601800847, "measured_audio_duration_sec": 9.1525, "memory_mb": 1990.9684640283951, "memory_mb_mean": 2172.8700719764697, "memory_mb_peak": 3347.15625, "per_utterance_latency_ms": 3190.898056520018, "postprocess_ms": 0.08202509990951512, "preprocess_ms": 0.12987124002393102, "provider_compute_latency_ms": 3190.898056520018, "provider_compute_rtf": 0.44452398257541437, "real_time_factor": 0.44452398257541437, "sample_accuracy": 0.58, "success_rate": 1.0, "time_to_final_result_ms": 3505.260191999878, "time_to_first_result_ms": 3505.260191999878, "time_to_result_ms": 3505.260191999878, "total_latency_ms": 3190.898056520018, "wer": 0.031075697211155377}`
