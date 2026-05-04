# Benchmark Summary: thesis_ext_20260504T104122Z_local_fleurs_sk_sk_test_subset

- benchmark_profile: `benchmark/thesis_extended_local_matrix`
- dataset_id: `fleurs_sk_sk_test_subset`
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
- successful_samples: `49`
- failed_samples: `1`
- quality_metrics: `{"cer": 0.2136574074074074, "confidence": 0.0, "sample_accuracy": 0.0, "wer": 0.5602564102564103}`
- latency_metrics: `{"end_to_end_latency_ms": 1999.001527899527, "end_to_end_rtf": 0.2073037220924722, "inference_ms": 1855.863177819847, "per_utterance_latency_ms": 1856.4974389401323, "postprocess_ms": 0.14667714000097476, "preprocess_ms": 0.4875839802843984, "provider_compute_latency_ms": 1856.4974389401323, "provider_compute_rtf": 0.1917813365363938, "real_time_factor": 0.1917813365363938, "time_to_final_result_ms": 1999.001527899527, "time_to_first_result_ms": 1999.001527899527, "time_to_result_ms": 1999.001527899527, "total_latency_ms": 1856.4974389401323}`
- reliability_metrics: `{"failure_rate": 0.02, "success_rate": 0.98}`
- cost_metrics: `{"estimated_cost_usd": 0.0}`
- cost_totals: `{"estimated_cost_usd": 0.0}`
- estimated_cost_total_usd: `0.0`

### providers/vosk_local (preset: `en_small`)
- samples: `50`
- successful_samples: `48`
- failed_samples: `2`
- quality_metrics: `{"cer": 0.8314814814814815, "confidence": 0.6902542513962774, "sample_accuracy": 0.0, "wer": 1.2884615384615385}`
- latency_metrics: `{"end_to_end_latency_ms": 2022.3418911203044, "end_to_end_rtf": 0.20765112134516672, "inference_ms": 1988.4672487202624, "per_utterance_latency_ms": 1997.5882974409615, "postprocess_ms": 0.10927738068858162, "preprocess_ms": 9.011771340010455, "provider_compute_latency_ms": 1997.5882974409615, "provider_compute_rtf": 0.20509654151192105, "real_time_factor": 0.20509654151192105, "time_to_final_result_ms": 2022.3418911203044, "time_to_first_result_ms": 2022.3418911203044, "time_to_result_ms": 2022.3418911203044, "total_latency_ms": 1997.5882974409615}`
- reliability_metrics: `{"failure_rate": 0.04, "success_rate": 0.96}`
- cost_metrics: `{"estimated_cost_usd": 0.0}`
- cost_totals: `{"estimated_cost_usd": 0.0}`
- estimated_cost_total_usd: `0.0`

### providers/whisper_local (preset: `light`)
- samples: `50`
- successful_samples: `50`
- failed_samples: `0`
- quality_metrics: `{"cer": 0.8189814814814815, "confidence": 0.5529698734315686, "sample_accuracy": 0.0, "wer": 1.8012820512820513}`
- latency_metrics: `{"end_to_end_latency_ms": 864.7523634797835, "end_to_end_rtf": 0.09218120893675037, "inference_ms": 776.128047840175, "per_utterance_latency_ms": 864.40467035849, "postprocess_ms": 0.09085385914659128, "preprocess_ms": 88.18576865916839, "provider_compute_latency_ms": 864.40467035849, "provider_compute_rtf": 0.09214366272804696, "real_time_factor": 0.09214366272804696, "time_to_final_result_ms": 864.7523634797835, "time_to_first_result_ms": 864.7523634797835, "time_to_result_ms": 864.7523634797835, "total_latency_ms": 864.40467035849}`
- reliability_metrics: `{"failure_rate": 0.0, "success_rate": 1.0}`
- cost_metrics: `{"estimated_cost_usd": 0.0}`
- cost_totals: `{"estimated_cost_usd": 0.0}`
- estimated_cost_total_usd: `0.0`

## Noise Summary
- clean: `{"audio_duration_sec": 9.906, "cer": 0.3541666666666667, "confidence": 0.44411233299577463, "cpu_percent": 17.041483234077415, "cpu_percent_mean": 12.265404988038336, "cpu_percent_peak": 100.0, "declared_audio_duration_sec": 9.906, "duration_mismatch_sec": 0.0, "end_to_end_latency_ms": 1733.8827109335398, "end_to_end_rtf": 0.17528250421844865, "estimated_cost_usd": 0.0, "failure_rate": 0.0, "gpu_memory_mb": 2095.6480952380953, "gpu_memory_mb_mean": 2200.089275259872, "gpu_memory_mb_peak": 5246.0, "gpu_util_percent": 15.547538904450668, "gpu_util_percent_mean": 16.556028473432495, "gpu_util_percent_peak": 73.0, "inference_ms": 1563.263676500598, "measured_audio_duration_sec": 9.906, "memory_mb": 1393.256800618956, "memory_mb_mean": 1452.4193636228208, "memory_mb_peak": 3385.14453125, "per_utterance_latency_ms": 1725.7731132337842, "postprocess_ms": 0.1676907338454233, "preprocess_ms": 162.341745999341, "provider_compute_latency_ms": 1725.7731132337842, "provider_compute_rtf": 0.1744704079778608, "real_time_factor": 0.1744704079778608, "sample_accuracy": 0.0, "success_rate": 1.0, "time_to_final_result_ms": 1733.8827109335398, "time_to_first_result_ms": 1733.8827109335398, "time_to_result_ms": 1733.8827109335398, "total_latency_ms": 1725.7731132337842, "wer": 0.8803418803418803}`
- white:custom_0db: `{"audio_duration_sec": 9.906, "cer": 0.9799382716049383, "confidence": 0.4089861875243337, "cpu_percent": 18.473434479107663, "cpu_percent_mean": 15.853802815322743, "cpu_percent_peak": 100.0, "declared_audio_duration_sec": 9.906, "duration_mismatch_sec": 0.0, "end_to_end_latency_ms": 1773.986694100313, "end_to_end_rtf": 0.18855423381762193, "estimated_cost_usd": 0.0, "failure_rate": 0.06666666666666667, "gpu_memory_mb": 2225.290634920635, "gpu_memory_mb_mean": 2806.1953203927224, "gpu_memory_mb_peak": 7041.0, "gpu_util_percent": 16.780965608465607, "gpu_util_percent_mean": 23.62546469015789, "gpu_util_percent_peak": 75.0, "inference_ms": 1530.8064455001538, "measured_audio_duration_sec": 9.906, "memory_mb": 1418.1897241266465, "memory_mb_mean": 1558.0597765881334, "memory_mb_peak": 3321.140625, "per_utterance_latency_ms": 1531.031343932894, "postprocess_ms": 0.10772426661181574, "preprocess_ms": 0.11717416612858263, "provider_compute_latency_ms": 1531.031343932894, "provider_compute_rtf": 0.16211191665082114, "real_time_factor": 0.16211191665082114, "sample_accuracy": 0.0, "success_rate": 0.9333333333333333, "time_to_final_result_ms": 1773.986694100313, "time_to_first_result_ms": 1773.986694100313, "time_to_result_ms": 1773.986694100313, "total_latency_ms": 1531.031343932894, "wer": 1.6324786324786325}`
- white:custom_10db: `{"audio_duration_sec": 9.906, "cer": 0.6087962962962963, "confidence": 0.4028227589884315, "cpu_percent": 18.409694442160248, "cpu_percent_mean": 14.513552201400538, "cpu_percent_peak": 100.0, "declared_audio_duration_sec": 9.906, "duration_mismatch_sec": 0.0, "end_to_end_latency_ms": 1549.6651819996866, "end_to_end_rtf": 0.161210449630071, "estimated_cost_usd": 0.0, "failure_rate": 0.0, "gpu_memory_mb": 2195.879356661857, "gpu_memory_mb_mean": 2358.2830798762675, "gpu_memory_mb_peak": 5254.0, "gpu_util_percent": 17.353261183261182, "gpu_util_percent_mean": 18.738854876864583, "gpu_util_percent_peak": 72.0, "inference_ms": 1539.8300451323546, "measured_audio_duration_sec": 9.906, "memory_mb": 1428.2671120502182, "memory_mb_mean": 1503.252056063041, "memory_mb_peak": 3427.05859375, "per_utterance_latency_ms": 1540.0470962663046, "postprocess_ms": 0.09516616652642067, "preprocess_ms": 0.12188496742358741, "provider_compute_latency_ms": 1540.0470962663046, "provider_compute_rtf": 0.16020616780717642, "real_time_factor": 0.16020616780717642, "sample_accuracy": 0.0, "success_rate": 1.0, "time_to_final_result_ms": 1549.6651819996866, "time_to_first_result_ms": 1549.6651819996866, "time_to_result_ms": 1549.6651819996866, "total_latency_ms": 1540.0470962663046, "wer": 1.3525641025641026}`
- white:custom_20db: `{"audio_duration_sec": 9.906, "cer": 0.36496913580246915, "confidence": 0.4298709107336673, "cpu_percent": 17.697765053218355, "cpu_percent_mean": 13.473043685607921, "cpu_percent_peak": 100.0, "declared_audio_duration_sec": 9.906, "duration_mismatch_sec": 0.0, "end_to_end_latency_ms": 1454.9907958995998, "end_to_end_rtf": 0.15057646586742449, "estimated_cost_usd": 0.0, "failure_rate": 0.0, "gpu_memory_mb": 2190.3554545454544, "gpu_memory_mb_mean": 2447.0233183647442, "gpu_memory_mb_peak": 5244.0, "gpu_util_percent": 16.981771284271286, "gpu_util_percent_mean": 19.118052407655828, "gpu_util_percent_peak": 73.0, "inference_ms": 1445.3607237677109, "measured_audio_duration_sec": 9.906, "memory_mb": 1431.7012803450623, "memory_mb_mean": 1536.903804393715, "memory_mb_peak": 3369.6796875, "per_utterance_latency_ms": 1445.5750555328752, "postprocess_ms": 0.10496739899584402, "preprocess_ms": 0.10936436616854432, "provider_compute_latency_ms": 1445.5750555328752, "provider_compute_rtf": 0.1496062134963845, "real_time_factor": 0.1496062134963845, "sample_accuracy": 0.0, "success_rate": 1.0, "time_to_final_result_ms": 1454.9907958995998, "time_to_first_result_ms": 1454.9907958995998, "time_to_result_ms": 1454.9907958995998, "total_latency_ms": 1445.5750555328752, "wer": 0.8611111111111112}`
- white:custom_5db: `{"audio_duration_sec": 9.906, "cer": 0.7989969135802469, "confidence": 0.38624801780420276, "cpu_percent": 17.687783810683303, "cpu_percent_mean": 14.237816740129615, "cpu_percent_peak": 100.0, "declared_audio_duration_sec": 9.906, "duration_mismatch_sec": 0.0, "end_to_end_latency_ms": 1630.9675878995524, "end_to_end_rtf": 0.1696031004237494, "estimated_cost_usd": 0.0, "failure_rate": 0.03333333333333333, "gpu_memory_mb": 2195.6539713064712, "gpu_memory_mb_mean": 2303.3004527009525, "gpu_memory_mb_peak": 5254.0, "gpu_util_percent": 17.241622914122914, "gpu_util_percent_mean": 17.924029355621627, "gpu_util_percent_peak": 74.0, "inference_ms": 1621.5032330663234, "measured_audio_duration_sec": 9.906, "memory_mb": 1428.7521293478417, "memory_mb_mean": 1482.8079255513826, "memory_mb_peak": 3407.4296875, "per_utterance_latency_ms": 1621.7240689334478, "postprocess_ms": 0.1024654004140757, "preprocess_ms": 0.11837046671037872, "provider_compute_latency_ms": 1621.7240689334478, "provider_compute_rtf": 0.16864119536169342, "real_time_factor": 0.16864119536169342, "sample_accuracy": 0.0, "success_rate": 0.9666666666666667, "time_to_final_result_ms": 1630.9675878995524, "time_to_first_result_ms": 1630.9675878995524, "time_to_result_ms": 1630.9675878995524, "total_latency_ms": 1621.7240689334478, "wer": 1.356837606837607}`
