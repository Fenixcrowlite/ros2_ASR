# Benchmark Summary: thesis_ext_20260504T104122Z_local_fleurs_fr_fr_test_subset

- benchmark_profile: `benchmark/thesis_extended_local_matrix`
- dataset_id: `fleurs_fr_fr_test_subset`
- providers: `providers/whisper_local, providers/vosk_local, providers/huggingface_local`
- scenario: `clean`
- execution_mode: `batch`
- noise_modes: `none, white`
- noise_levels: `clean, custom_0db, custom_10db, custom_20db, custom_5db`
- aggregate_scope: `provider_only`
- total_samples: `150`
- successful_samples: `146`
- failed_samples: `4`
- aggregate_samples: `150`
- corrupted_samples: `0`

## Per-Provider Summary

### providers/huggingface_local (preset: `balanced`)
- samples: `50`
- successful_samples: `50`
- failed_samples: `0`
- quality_metrics: `{"cer": 0.24719283970707892, "confidence": 0.0, "sample_accuracy": 0.06, "wer": 0.4728813559322034}`
- latency_metrics: `{"end_to_end_latency_ms": 1804.365319460776, "end_to_end_rtf": 0.19747246388280937, "inference_ms": 1803.474928479991, "per_utterance_latency_ms": 1804.1167372204654, "postprocess_ms": 0.14633867976954207, "preprocess_ms": 0.49547006070497446, "provider_compute_latency_ms": 1804.1167372204654, "provider_compute_rtf": 0.19744369783259016, "real_time_factor": 0.19744369783259016, "time_to_final_result_ms": 1804.365319460776, "time_to_first_result_ms": 1804.365319460776, "time_to_result_ms": 1804.365319460776, "total_latency_ms": 1804.1167372204654}`
- reliability_metrics: `{"failure_rate": 0.0, "success_rate": 1.0}`
- cost_metrics: `{"estimated_cost_usd": 0.0}`
- cost_totals: `{"estimated_cost_usd": 0.0}`
- estimated_cost_total_usd: `0.0`

### providers/vosk_local (preset: `en_small`)
- samples: `50`
- successful_samples: `46`
- failed_samples: `4`
- quality_metrics: `{"cer": 0.7767290480065093, "confidence": 0.6479310333091167, "sample_accuracy": 0.0, "wer": 1.021186440677966}`
- latency_metrics: `{"end_to_end_latency_ms": 1962.1709330605518, "end_to_end_rtf": 0.21025770106064537, "inference_ms": 1929.4539558397082, "per_utterance_latency_ms": 1938.2467154590995, "postprocess_ms": 0.11864889980643056, "preprocess_ms": 8.67411071958486, "provider_compute_latency_ms": 1938.2467154590995, "provider_compute_rtf": 0.20764910256183022, "real_time_factor": 0.20764910256183022, "time_to_final_result_ms": 1962.1709330605518, "time_to_first_result_ms": 1962.1709330605518, "time_to_result_ms": 1962.1709330605518, "total_latency_ms": 1938.2467154590995}`
- reliability_metrics: `{"failure_rate": 0.08, "success_rate": 0.92}`
- cost_metrics: `{"estimated_cost_usd": 0.0}`
- cost_totals: `{"estimated_cost_usd": 0.0}`
- estimated_cost_total_usd: `0.0`

### providers/whisper_local (preset: `light`)
- samples: `50`
- successful_samples: `50`
- failed_samples: `0`
- quality_metrics: `{"cer": 0.8336859235150529, "confidence": 0.637110371176023, "sample_accuracy": 0.0, "wer": 1.4559322033898305}`
- latency_metrics: `{"end_to_end_latency_ms": 899.0686770802131, "end_to_end_rtf": 0.10032975075579188, "inference_ms": 814.3867095999303, "per_utterance_latency_ms": 898.716838380642, "postprocess_ms": 0.08282620052341372, "preprocess_ms": 84.24730258018826, "provider_compute_latency_ms": 898.716838380642, "provider_compute_rtf": 0.1002895656230128, "real_time_factor": 0.1002895656230128, "time_to_final_result_ms": 899.0686770802131, "time_to_first_result_ms": 899.0686770802131, "time_to_result_ms": 899.0686770802131, "total_latency_ms": 898.716838380642}`
- reliability_metrics: `{"failure_rate": 0.0, "success_rate": 1.0}`
- cost_metrics: `{"estimated_cost_usd": 0.0}`
- cost_totals: `{"estimated_cost_usd": 0.0}`
- estimated_cost_total_usd: `0.0`

## Noise Summary
- clean: `{"audio_duration_sec": 9.456, "cer": 0.2823433685923515, "confidence": 0.49309480234450664, "cpu_percent": 16.014676128136042, "cpu_percent_mean": 11.417524839577629, "cpu_percent_peak": 91.9, "declared_audio_duration_sec": 9.456, "duration_mismatch_sec": 0.0, "end_to_end_latency_ms": 1684.1042248663143, "end_to_end_rtf": 0.18341410029437777, "estimated_cost_usd": 0.0, "failure_rate": 0.0, "gpu_memory_mb": 1962.0194871794872, "gpu_memory_mb_mean": 2038.307255331038, "gpu_memory_mb_peak": 5443.0, "gpu_util_percent": 16.229199365449364, "gpu_util_percent_mean": 15.584997035386031, "gpu_util_percent_peak": 74.0, "inference_ms": 1519.8095908000444, "measured_audio_duration_sec": 9.456, "memory_mb": 1439.1004180791172, "memory_mb_mean": 1485.9124381536049, "memory_mb_peak": 3430.65625, "per_utterance_latency_ms": 1675.158685666732, "postprocess_ms": 0.11957049961589898, "preprocess_ms": 155.22952436707178, "provider_compute_latency_ms": 1675.158685666732, "provider_compute_rtf": 0.18243109417452152, "real_time_factor": 0.18243109417452152, "sample_accuracy": 0.06666666666666667, "success_rate": 1.0, "time_to_final_result_ms": 1684.1042248663143, "time_to_first_result_ms": 1684.1042248663143, "time_to_result_ms": 1684.1042248663143, "total_latency_ms": 1675.158685666732, "wer": 0.4745762711864407}`
- white:custom_0db: `{"audio_duration_sec": 9.456, "cer": 1.1545972335231895, "confidence": 0.4008937768830384, "cpu_percent": 18.088761427066565, "cpu_percent_mean": 16.73823118190889, "cpu_percent_peak": 100.0, "declared_audio_duration_sec": 9.456, "duration_mismatch_sec": 0.0, "end_to_end_latency_ms": 1589.5757475673843, "end_to_end_rtf": 0.17074951375946218, "estimated_cost_usd": 0.0, "failure_rate": 0.06666666666666667, "gpu_memory_mb": 2075.7449159663865, "gpu_memory_mb_mean": 2178.5761996616284, "gpu_memory_mb_peak": 5426.0, "gpu_util_percent": 14.006136009959539, "gpu_util_percent_mean": 15.034550111563206, "gpu_util_percent_peak": 74.0, "inference_ms": 1584.538709766154, "measured_audio_duration_sec": 9.456, "memory_mb": 1478.9188547330502, "memory_mb_mean": 1511.9278293138116, "memory_mb_peak": 3431.0234375, "per_utterance_latency_ms": 1584.7997807325253, "postprocess_ms": 0.13515593309421092, "preprocess_ms": 0.12591503327712417, "provider_compute_latency_ms": 1584.7997807325253, "provider_compute_rtf": 0.17024558055723463, "real_time_factor": 0.17024558055723463, "sample_accuracy": 0.0, "success_rate": 0.9333333333333333, "time_to_final_result_ms": 1589.5757475673843, "time_to_first_result_ms": 1589.5757475673843, "time_to_result_ms": 1589.5757475673843, "total_latency_ms": 1584.7997807325253, "wer": 1.7019774011299436}`
- white:custom_10db: `{"audio_duration_sec": 9.456, "cer": 0.6257119609438568, "confidence": 0.40191510038412626, "cpu_percent": 17.110933070899403, "cpu_percent_mean": 13.781667919465574, "cpu_percent_peak": 100.0, "declared_audio_duration_sec": 9.456, "duration_mismatch_sec": 0.0, "end_to_end_latency_ms": 1564.2216049336032, "end_to_end_rtf": 0.17292012847938298, "estimated_cost_usd": 0.0, "failure_rate": 0.03333333333333333, "gpu_memory_mb": 2070.3503174603175, "gpu_memory_mb_mean": 2215.141357356121, "gpu_memory_mb_peak": 5412.0, "gpu_util_percent": 14.114193121693122, "gpu_util_percent_mean": 14.812760236083955, "gpu_util_percent_peak": 72.0, "inference_ms": 1554.477861066698, "measured_audio_duration_sec": 9.456, "memory_mb": 1474.1057046789197, "memory_mb_mean": 1541.8989930171856, "memory_mb_peak": 3430.65234375, "per_utterance_latency_ms": 1554.6987465990242, "postprocess_ms": 0.10580799983775553, "preprocess_ms": 0.11507753248830947, "provider_compute_latency_ms": 1554.6987465990242, "provider_compute_rtf": 0.17186838363403814, "real_time_factor": 0.17186838363403814, "sample_accuracy": 0.0, "success_rate": 0.9666666666666667, "time_to_final_result_ms": 1564.2216049336032, "time_to_first_result_ms": 1564.2216049336032, "time_to_result_ms": 1564.2216049336032, "total_latency_ms": 1554.6987465990242, "wer": 1.1144067796610169}`
- white:custom_20db: `{"audio_duration_sec": 9.456, "cer": 0.3718470301057771, "confidence": 0.45402629000437417, "cpu_percent": 17.232103532636895, "cpu_percent_mean": 13.36633514472782, "cpu_percent_peak": 100.0, "declared_audio_duration_sec": 9.456, "duration_mismatch_sec": 0.0, "end_to_end_latency_ms": 1435.1799802013072, "end_to_end_rtf": 0.1566721643115151, "estimated_cost_usd": 0.0, "failure_rate": 0.0, "gpu_memory_mb": 2065.7615079365078, "gpu_memory_mb_mean": 2310.261821087086, "gpu_memory_mb_peak": 5444.0, "gpu_util_percent": 13.82315527065527, "gpu_util_percent_mean": 15.421394865292594, "gpu_util_percent_peak": 74.0, "inference_ms": 1425.4290689665747, "measured_audio_duration_sec": 9.456, "memory_mb": 1479.2802543590883, "memory_mb_mean": 1586.7509596849354, "memory_mb_peak": 3431.0234375, "per_utterance_latency_ms": 1425.656719601587, "postprocess_ms": 0.10918530097114854, "preprocess_ms": 0.11846533404119934, "provider_compute_latency_ms": 1425.656719601587, "provider_compute_rtf": 0.15563100597321405, "real_time_factor": 0.15563100597321405, "sample_accuracy": 0.03333333333333333, "success_rate": 1.0, "time_to_final_result_ms": 1435.1799802013072, "time_to_first_result_ms": 1435.1799802013072, "time_to_result_ms": 1435.1799802013072, "total_latency_ms": 1425.656719601587, "wer": 0.597457627118644}`
- white:custom_5db: `{"audio_duration_sec": 9.456, "cer": 0.661513425549227, "confidence": 0.39180570452585395, "cpu_percent": 17.49143290818312, "cpu_percent_mean": 13.988603489895262, "cpu_percent_peak": 100.0, "declared_audio_duration_sec": 9.456, "duration_mismatch_sec": 0.0, "end_to_end_latency_ms": 1502.9266584339591, "end_to_end_rtf": 0.163010619320673, "estimated_cost_usd": 0.0, "failure_rate": 0.03333333333333333, "gpu_memory_mb": 2074.1076875901877, "gpu_memory_mb_mean": 2254.4454172924516, "gpu_memory_mb_peak": 5396.0, "gpu_util_percent": 12.650440115440116, "gpu_util_percent_mean": 14.303621788890164, "gpu_util_percent_peak": 73.0, "inference_ms": 1494.6040925999114, "measured_audio_duration_sec": 9.456, "memory_mb": 1482.5733612017398, "memory_mb_mean": 1562.7437716754946, "memory_mb_peak": 3431.0234375, "per_utterance_latency_ms": 1494.8198858338098, "postprocess_ms": 0.10996989997996327, "preprocess_ms": 0.10582333391842742, "provider_compute_latency_ms": 1494.8198858338098, "provider_compute_rtf": 0.16212787902338033, "real_time_factor": 0.16212787902338033, "sample_accuracy": 0.0, "success_rate": 0.9666666666666667, "time_to_final_result_ms": 1502.9266584339591, "time_to_first_result_ms": 1502.9266584339591, "time_to_result_ms": 1502.9266584339591, "total_latency_ms": 1494.8198858338098, "wer": 1.0282485875706215}`
