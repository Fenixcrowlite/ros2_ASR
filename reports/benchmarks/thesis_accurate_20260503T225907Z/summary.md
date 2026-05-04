# Benchmark Summary: thesis_accurate_20260503T225907Z

- benchmark_profile: `benchmark/thesis_tier_accurate`
- dataset_id: `librispeech_test_clean_subset`
- providers: `providers/whisper_local, providers/huggingface_local, providers/google_cloud`
- scenario: `noise_robustness`
- execution_mode: `batch`
- noise_modes: `none, white`
- noise_levels: `clean, custom_0db, custom_10db, custom_20db, custom_5db`
- aggregate_scope: `provider_only`
- total_samples: `150`
- successful_samples: `100`
- failed_samples: `50`
- aggregate_samples: `150`
- corrupted_samples: `0`

## Per-Provider Summary

### providers/google_cloud (preset: `accurate`)
- samples: `50`
- successful_samples: `50`
- failed_samples: `0`
- quality_metrics: `{"cer": 0.042375886524822694, "confidence": 0.9370753049850464, "sample_accuracy": 0.3, "wer": 0.07330677290836653}`
- latency_metrics: `{"end_to_end_latency_ms": 1626.7218500200033, "end_to_end_rtf": 0.1930650075827728, "inference_ms": 1623.323334319939, "per_utterance_latency_ms": 1625.6748130999404, "postprocess_ms": 0.0001410000550094992, "preprocess_ms": 2.351337779946334, "provider_compute_latency_ms": 1625.6748130999404, "provider_compute_rtf": 0.19291403263762175, "real_time_factor": 0.19291403263762175, "time_to_final_result_ms": 1626.7218500200033, "time_to_first_result_ms": 1626.7218500200033, "time_to_result_ms": 1626.7218500200033, "total_latency_ms": 1625.6748130999404}`
- reliability_metrics: `{"failure_rate": 0.0, "success_rate": 1.0}`
- cost_metrics: `{"estimated_cost_usd": 0.0}`
- cost_totals: `{"estimated_cost_usd": 0.0}`
- estimated_cost_total_usd: `0.0`

### providers/huggingface_local (preset: `accurate`)
- samples: `50`
- successful_samples: `0`
- failed_samples: `50`
- quality_metrics: `{"cer": 1.0, "confidence": 0.0, "sample_accuracy": 0.0, "wer": 1.0}`
- latency_metrics: `{"end_to_end_latency_ms": 4087.6067297000195, "end_to_end_rtf": 1.1242518419595129, "inference_ms": 0.0, "per_utterance_latency_ms": 0.0, "postprocess_ms": 0.0, "preprocess_ms": 0.0, "provider_compute_latency_ms": 0.0, "provider_compute_rtf": 0.0, "real_time_factor": 0.0, "time_to_final_result_ms": 4087.6067297000195, "time_to_first_result_ms": 4087.6067297000195, "time_to_result_ms": 4087.6067297000195, "total_latency_ms": 0.0}`
- reliability_metrics: `{"failure_rate": 1.0, "success_rate": 0.0}`
- cost_metrics: `{"estimated_cost_usd": 0.0}`
- cost_totals: `{"estimated_cost_usd": 0.0}`
- estimated_cost_total_usd: `0.0`

### providers/whisper_local (preset: `accurate`)
- samples: `50`
- successful_samples: `50`
- failed_samples: `0`
- quality_metrics: `{"cer": 0.015602836879432624, "confidence": 0.9333758427283579, "sample_accuracy": 0.58, "wer": 0.027091633466135457}`
- latency_metrics: `{"end_to_end_latency_ms": 2532.422673719884, "end_to_end_rtf": 0.37200049305105226, "inference_ms": 2496.2078727399785, "per_utterance_latency_ms": 2532.0973719600443, "postprocess_ms": 0.08974166001280537, "preprocess_ms": 35.79975756005297, "provider_compute_latency_ms": 2532.0973719600443, "provider_compute_rtf": 0.37194986873522096, "real_time_factor": 0.37194986873522096, "time_to_final_result_ms": 2532.422673719884, "time_to_first_result_ms": 2532.422673719884, "time_to_result_ms": 2532.422673719884, "total_latency_ms": 2532.0973719600443}`
- reliability_metrics: `{"failure_rate": 0.0, "success_rate": 1.0}`
- cost_metrics: `{"estimated_cost_usd": 0.0}`
- cost_totals: `{"estimated_cost_usd": 0.0}`
- estimated_cost_total_usd: `0.0`

## Noise Summary
- clean: `{"audio_duration_sec": 9.1525, "cer": 0.34131205673758863, "confidence": 0.6392748392070785, "cpu_percent": 15.87761513933335, "cpu_percent_mean": 10.151911235230516, "cpu_percent_peak": 100.0, "declared_audio_duration_sec": 9.1525, "duration_mismatch_sec": 0.0, "end_to_end_latency_ms": 7801.911304866372, "end_to_end_rtf": 2.0057057126166464, "estimated_cost_usd": 0.0, "failure_rate": 0.3333333333333333, "gpu_memory_mb": 2891.6152493218283, "gpu_memory_mb_mean": 978.3814823133534, "gpu_memory_mb_peak": 7742.0, "gpu_util_percent": 35.79187383766331, "gpu_util_percent_mean": 10.464850189174173, "gpu_util_percent_peak": 100.0, "inference_ms": 1363.8686534998972, "measured_audio_duration_sec": 9.1525, "memory_mb": 2498.5720944949985, "memory_mb_mean": 3038.1310184225176, "memory_mb_peak": 4749.3515625, "per_utterance_latency_ms": 1427.0595987001798, "postprocess_ms": 0.029789400165706564, "preprocess_ms": 63.16115580011683, "provider_compute_latency_ms": 1427.0595987001798, "provider_compute_rtf": 0.20116857800066512, "real_time_factor": 0.20116857800066512, "sample_accuracy": 0.36666666666666664, "success_rate": 0.6666666666666666, "time_to_final_result_ms": 7801.911304866372, "time_to_first_result_ms": 7801.911304866372, "time_to_result_ms": 7801.911304866372, "total_latency_ms": 1427.0595987001798, "wer": 0.3466135458167331}`
- white:custom_0db: `{"audio_duration_sec": 9.1525, "cer": 0.37884160756501184, "confidence": 0.584379357285275, "cpu_percent": 17.225376401387855, "cpu_percent_mean": 23.288762478466218, "cpu_percent_peak": 100.0, "declared_audio_duration_sec": 9.1525, "duration_mismatch_sec": 0.0, "end_to_end_latency_ms": 1526.1555177003781, "end_to_end_rtf": 0.20817712113102807, "estimated_cost_usd": 0.0, "failure_rate": 0.3333333333333333, "gpu_memory_mb": 3116.5823148148147, "gpu_memory_mb_mean": 1314.1404635266608, "gpu_memory_mb_peak": 7742.0, "gpu_util_percent": 25.04153133903134, "gpu_util_percent_mean": 12.452134037670552, "gpu_util_percent_peak": 100.0, "inference_ms": 1415.8331001000988, "measured_audio_duration_sec": 9.1525, "memory_mb": 2478.9654456419294, "memory_mb_mean": 2552.6151292732475, "memory_mb_peak": 2852.31640625, "per_utterance_latency_ms": 1415.9723503998976, "postprocess_ms": 0.028849066560117837, "preprocess_ms": 0.11040123323861432, "provider_compute_latency_ms": 1415.9723503998976, "provider_compute_rtf": 0.19075284472947138, "real_time_factor": 0.19075284472947138, "sample_accuracy": 0.13333333333333333, "success_rate": 0.6666666666666666, "time_to_final_result_ms": 1526.1555177003781, "time_to_first_result_ms": 1526.1555177003781, "time_to_result_ms": 1526.1555177003781, "total_latency_ms": 1415.9723503998976, "wer": 0.4103585657370518}`
- white:custom_10db: `{"audio_duration_sec": 9.1525, "cer": 0.34515366430260047, "confidence": 0.6308276742477075, "cpu_percent": 15.958037741594543, "cpu_percent_mean": 21.674958298157236, "cpu_percent_peak": 100.0, "declared_audio_duration_sec": 9.1525, "duration_mismatch_sec": 0.0, "end_to_end_latency_ms": 1473.7534143331384, "end_to_end_rtf": 0.19980344059288682, "estimated_cost_usd": 0.0, "failure_rate": 0.3333333333333333, "gpu_memory_mb": 3119.9881493506496, "gpu_memory_mb_mean": 1335.574769693082, "gpu_memory_mb_peak": 7742.0, "gpu_util_percent": 24.959356661856663, "gpu_util_percent_mean": 11.94927884645382, "gpu_util_percent_peak": 100.0, "inference_ms": 1363.8193408665757, "measured_audio_duration_sec": 9.1525, "memory_mb": 2477.2350446326222, "memory_mb_mean": 2551.5821699618364, "memory_mb_peak": 2852.31640625, "per_utterance_latency_ms": 1363.9595962332653, "postprocess_ms": 0.029075099822269596, "preprocess_ms": 0.11118026686744997, "provider_compute_latency_ms": 1363.9595962332653, "provider_compute_rtf": 0.18247981633786103, "real_time_factor": 0.18247981633786103, "sample_accuracy": 0.3333333333333333, "success_rate": 0.6666666666666666, "time_to_final_result_ms": 1473.7534143331384, "time_to_first_result_ms": 1473.7534143331384, "time_to_result_ms": 1473.7534143331384, "total_latency_ms": 1363.9595962332653, "wer": 0.35723771580345287}`
- white:custom_20db: `{"audio_duration_sec": 9.1525, "cer": 0.341903073286052, "confidence": 0.6365233560717104, "cpu_percent": 16.443516802725366, "cpu_percent_mean": 21.862608629083383, "cpu_percent_peak": 91.9, "declared_audio_duration_sec": 9.1525, "duration_mismatch_sec": 0.0, "end_to_end_latency_ms": 1464.3265640332174, "end_to_end_rtf": 0.19892922831078322, "estimated_cost_usd": 0.0, "failure_rate": 0.3333333333333333, "gpu_memory_mb": 3119.2714466089465, "gpu_memory_mb_mean": 1340.0058103209954, "gpu_memory_mb_peak": 7742.0, "gpu_util_percent": 24.419506974506973, "gpu_util_percent_mean": 12.189859477148742, "gpu_util_percent_peak": 100.0, "inference_ms": 1353.9720708332122, "measured_audio_duration_sec": 9.1525, "memory_mb": 2476.529554808932, "memory_mb_mean": 2551.7627530461036, "memory_mb_peak": 2852.31640625, "per_utterance_latency_ms": 1354.113641799995, "postprocess_ms": 0.03089353352455267, "preprocess_ms": 0.11067743325838819, "provider_compute_latency_ms": 1354.113641799995, "provider_compute_rtf": 0.1814757112656014, "real_time_factor": 0.1814757112656014, "sample_accuracy": 0.4, "success_rate": 0.6666666666666666, "time_to_final_result_ms": 1464.3265640332174, "time_to_first_result_ms": 1464.3265640332174, "time_to_result_ms": 1464.3265640332174, "total_latency_ms": 1354.113641799995, "wer": 0.3452855245683931}`
- white:custom_5db: `{"audio_duration_sec": 9.1525, "cer": 0.35608747044917255, "confidence": 0.6264133527105691, "cpu_percent": 16.063229095341843, "cpu_percent_mean": 21.578042885307852, "cpu_percent_peak": 91.9, "declared_audio_duration_sec": 9.1525, "duration_mismatch_sec": 0.0, "end_to_end_latency_ms": 1478.4386214667393, "end_to_end_rtf": 0.20291340167088553, "estimated_cost_usd": 0.0, "failure_rate": 0.3333333333333333, "gpu_memory_mb": 3117.9342472342473, "gpu_memory_mb_mean": 1331.3954105872426, "gpu_memory_mb_peak": 7742.0, "gpu_util_percent": 25.59821669071669, "gpu_util_percent_mean": 12.19814761541485, "gpu_util_percent_peak": 100.0, "inference_ms": 1368.3921798000786, "measured_audio_duration_sec": 9.1525, "memory_mb": 2477.103778099843, "memory_mb_mean": 2551.3613694521396, "memory_mb_peak": 2852.31640625, "per_utterance_latency_ms": 1368.51512129997, "postprocess_ms": 0.031197333373711444, "preprocess_ms": 0.09174416651755261, "provider_compute_latency_ms": 1368.51512129997, "provider_compute_rtf": 0.1855628852878055, "real_time_factor": 0.1855628852878055, "sample_accuracy": 0.23333333333333334, "success_rate": 0.6666666666666666, "time_to_final_result_ms": 1478.4386214667393, "time_to_first_result_ms": 1478.4386214667393, "time_to_result_ms": 1478.4386214667393, "total_latency_ms": 1368.51512129997, "wer": 0.3745019920318725}`
