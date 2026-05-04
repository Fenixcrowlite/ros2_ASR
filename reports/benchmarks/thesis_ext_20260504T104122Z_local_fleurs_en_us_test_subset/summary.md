# Benchmark Summary: thesis_ext_20260504T104122Z_local_fleurs_en_us_test_subset

- benchmark_profile: `benchmark/thesis_extended_local_matrix`
- dataset_id: `fleurs_en_us_test_subset`
- providers: `providers/whisper_local, providers/vosk_local, providers/huggingface_local`
- scenario: `clean`
- execution_mode: `batch`
- noise_modes: `none, white`
- noise_levels: `clean, custom_0db, custom_10db, custom_20db, custom_5db`
- aggregate_scope: `provider_only`
- total_samples: `150`
- successful_samples: `138`
- failed_samples: `12`
- aggregate_samples: `150`
- corrupted_samples: `0`

## Per-Provider Summary

### providers/huggingface_local (preset: `balanced`)
- samples: `50`
- successful_samples: `50`
- failed_samples: `0`
- quality_metrics: `{"cer": 0.09680284191829484, "confidence": 0.0, "sample_accuracy": 0.24, "wer": 0.18851674641148325}`
- latency_metrics: `{"end_to_end_latency_ms": 1548.3486285197432, "end_to_end_rtf": 0.15577173997204435, "inference_ms": 1547.5080905602954, "per_utterance_latency_ms": 1548.1106104404898, "postprocess_ms": 0.19682904065120965, "preprocess_ms": 0.40569083954324014, "provider_compute_latency_ms": 1548.1106104404898, "provider_compute_rtf": 0.15574680012477327, "real_time_factor": 0.15574680012477327, "time_to_final_result_ms": 1548.3486285197432, "time_to_first_result_ms": 1548.3486285197432, "time_to_result_ms": 1548.3486285197432, "total_latency_ms": 1548.1106104404898}`
- reliability_metrics: `{"failure_rate": 0.0, "success_rate": 1.0}`
- cost_metrics: `{"estimated_cost_usd": 0.0}`
- cost_totals: `{"estimated_cost_usd": 0.0}`
- estimated_cost_total_usd: `0.0`

### providers/vosk_local (preset: `en_small`)
- samples: `50`
- successful_samples: `38`
- failed_samples: `12`
- quality_metrics: `{"cer": 0.4989342806394316, "confidence": 0.6363090664088145, "sample_accuracy": 0.02, "wer": 0.6258373205741626}`
- latency_metrics: `{"end_to_end_latency_ms": 1292.0180864195572, "end_to_end_rtf": 0.11903649417808479, "inference_ms": 1270.083443679905, "per_utterance_latency_ms": 1278.796813199442, "postprocess_ms": 0.11332069989293814, "preprocess_ms": 8.600048819644144, "provider_compute_latency_ms": 1278.796813199442, "provider_compute_rtf": 0.11784571369359093, "real_time_factor": 0.11784571369359093, "time_to_final_result_ms": 1292.0180864195572, "time_to_first_result_ms": 1292.0180864195572, "time_to_result_ms": 1292.0180864195572, "total_latency_ms": 1278.796813199442}`
- reliability_metrics: `{"failure_rate": 0.24, "success_rate": 0.76}`
- cost_metrics: `{"estimated_cost_usd": 0.0}`
- cost_totals: `{"estimated_cost_usd": 0.0}`
- estimated_cost_total_usd: `0.0`

### providers/whisper_local (preset: `light`)
- samples: `50`
- successful_samples: `50`
- failed_samples: `0`
- quality_metrics: `{"cer": 0.4676731793960924, "confidence": 0.7106648772577739, "sample_accuracy": 0.08, "wer": 0.676555023923445}`
- latency_metrics: `{"end_to_end_latency_ms": 705.0165824005671, "end_to_end_rtf": 0.0686372104173803, "inference_ms": 620.8744953203131, "per_utterance_latency_ms": 704.6326854206563, "postprocess_ms": 0.08804928060271777, "preprocess_ms": 83.67014081974048, "provider_compute_latency_ms": 704.6326854206563, "provider_compute_rtf": 0.06859361511101467, "real_time_factor": 0.06859361511101467, "time_to_final_result_ms": 705.0165824005671, "time_to_first_result_ms": 705.0165824005671, "time_to_result_ms": 705.0165824005671, "total_latency_ms": 704.6326854206563}`
- reliability_metrics: `{"failure_rate": 0.0, "success_rate": 1.0}`
- cost_metrics: `{"estimated_cost_usd": 0.0}`
- cost_totals: `{"estimated_cost_usd": 0.0}`
- estimated_cost_total_usd: `0.0`

## Noise Summary
- clean: `{"audio_duration_sec": 10.628, "cer": 0.07223208999407933, "confidence": 0.59785852570413, "cpu_percent": 16.256353143253108, "cpu_percent_mean": 12.894584875671711, "cpu_percent_peak": 92.5, "declared_audio_duration_sec": 10.628, "duration_mismatch_sec": 0.0, "end_to_end_latency_ms": 1358.8399495657843, "end_to_end_rtf": 0.13066409140093843, "estimated_cost_usd": 0.0, "failure_rate": 0.0, "gpu_memory_mb": 1754.673134920635, "gpu_memory_mb_mean": 1946.367925701837, "gpu_memory_mb_peak": 4401.0, "gpu_util_percent": 10.828968253968254, "gpu_util_percent_mean": 14.213216994865824, "gpu_util_percent_peak": 74.0, "inference_ms": 1200.1492929334443, "measured_audio_duration_sec": 10.628, "memory_mb": 1421.7241345169039, "memory_mb_mean": 1500.530339969136, "memory_mb_peak": 3406.15234375, "per_utterance_latency_ms": 1354.2999427331476, "postprocess_ms": 0.22384610031925453, "preprocess_ms": 153.92680369938412, "provider_compute_latency_ms": 1354.2999427331476, "provider_compute_rtf": 0.13020414005243958, "real_time_factor": 0.13020414005243958, "sample_accuracy": 0.2, "success_rate": 1.0, "time_to_final_result_ms": 1358.8399495657843, "time_to_first_result_ms": 1358.8399495657843, "time_to_result_ms": 1358.8399495657843, "total_latency_ms": 1354.2999427331476, "wer": 0.17384370015948963}`
- white:custom_0db: `{"audio_duration_sec": 10.628, "cer": 0.6933096506808762, "confidence": 0.3529315549445314, "cpu_percent": 17.167352503823075, "cpu_percent_mean": 15.41742538257382, "cpu_percent_peak": 91.3, "declared_audio_duration_sec": 10.628, "duration_mismatch_sec": 0.0, "end_to_end_latency_ms": 1262.9764325994377, "end_to_end_rtf": 0.11789798414047849, "estimated_cost_usd": 0.0, "failure_rate": 0.1, "gpu_memory_mb": 1844.7292857142857, "gpu_memory_mb_mean": 2063.9515021034945, "gpu_memory_mb_peak": 4395.0, "gpu_util_percent": 11.921459836459837, "gpu_util_percent_mean": 15.053507032899006, "gpu_util_percent_peak": 73.0, "inference_ms": 1258.1792428999809, "measured_audio_duration_sec": 10.628, "memory_mb": 1466.8552355899624, "memory_mb_mean": 1571.570458020223, "memory_mb_peak": 3408.98046875, "per_utterance_latency_ms": 1258.4506713668816, "postprocess_ms": 0.14060076670527147, "preprocess_ms": 0.13082770019536838, "provider_compute_latency_ms": 1258.4506713668816, "provider_compute_rtf": 0.1175511747798859, "real_time_factor": 0.1175511747798859, "sample_accuracy": 0.0, "success_rate": 0.9, "time_to_final_result_ms": 1262.9764325994377, "time_to_first_result_ms": 1262.9764325994377, "time_to_result_ms": 1262.9764325994377, "total_latency_ms": 1258.4506713668816, "wer": 1.0287081339712918}`
- white:custom_10db: `{"audio_duration_sec": 10.628, "cer": 0.23801065719360567, "confidence": 0.44056893150855236, "cpu_percent": 16.508516427744368, "cpu_percent_mean": 13.041824380240936, "cpu_percent_peak": 91.2, "declared_audio_duration_sec": 10.628, "duration_mismatch_sec": 0.0, "end_to_end_latency_ms": 1097.6819900007588, "end_to_end_rtf": 0.1081791373799136, "estimated_cost_usd": 0.0, "failure_rate": 0.1, "gpu_memory_mb": 1840.1066666666666, "gpu_memory_mb_mean": 2190.5976610487824, "gpu_memory_mb_peak": 4423.0, "gpu_util_percent": 11.159682539682539, "gpu_util_percent_mean": 14.404654792964081, "gpu_util_percent_peak": 76.0, "inference_ms": 1092.5748822332632, "measured_audio_duration_sec": 10.628, "memory_mb": 1465.263320908947, "memory_mb_mean": 1634.259203775647, "memory_mb_peak": 3405.875, "per_utterance_latency_ms": 1092.817782931282, "postprocess_ms": 0.1023904330698618, "preprocess_ms": 0.1405102649490194, "provider_compute_latency_ms": 1092.817782931282, "provider_compute_rtf": 0.1077316473042413, "real_time_factor": 0.1077316473042413, "sample_accuracy": 0.16666666666666666, "success_rate": 0.9, "time_to_final_result_ms": 1097.6819900007588, "time_to_first_result_ms": 1097.6819900007588, "time_to_result_ms": 1097.6819900007588, "total_latency_ms": 1092.817782931282, "wer": 0.34290271132376393}`
- white:custom_20db: `{"audio_duration_sec": 10.628, "cer": 0.09887507400828893, "confidence": 0.562751238534015, "cpu_percent": 17.225099715099716, "cpu_percent_mean": 13.86612271194802, "cpu_percent_peak": 97.5, "declared_audio_duration_sec": 10.628, "duration_mismatch_sec": 0.0, "end_to_end_latency_ms": 1053.6423717331975, "end_to_end_rtf": 0.10627255603928445, "estimated_cost_usd": 0.0, "failure_rate": 0.0, "gpu_memory_mb": 1837.3505555555555, "gpu_memory_mb_mean": 2234.054158779952, "gpu_memory_mb_peak": 4423.0, "gpu_util_percent": 10.793888888888889, "gpu_util_percent_mean": 14.565119030618042, "gpu_util_percent_peak": 76.0, "inference_ms": 1048.4609251342288, "measured_audio_duration_sec": 10.628, "memory_mb": 1465.4070378021502, "memory_mb_mean": 1653.2711206884812, "memory_mb_peak": 3408.7109375, "per_utterance_latency_ms": 1048.6741137356148, "postprocess_ms": 0.0879910677516212, "preprocess_ms": 0.12519753363449126, "provider_compute_latency_ms": 1048.6741137356148, "provider_compute_rtf": 0.10578382535792677, "real_time_factor": 0.10578382535792677, "sample_accuracy": 0.16666666666666666, "success_rate": 1.0, "time_to_final_result_ms": 1053.6423717331975, "time_to_first_result_ms": 1053.6423717331975, "time_to_result_ms": 1053.6423717331975, "total_latency_ms": 1048.6741137356148, "wer": 0.20414673046251994}`
- white:custom_5db: `{"audio_duration_sec": 10.628, "cer": 0.6699230313795145, "confidence": 0.2908463220864186, "cpu_percent": 17.529300451498017, "cpu_percent_mean": 15.242347636567375, "cpu_percent_peak": 100.0, "declared_audio_duration_sec": 10.628, "duration_mismatch_sec": 0.0, "end_to_end_latency_ms": 1135.8314183339342, "end_to_end_rtf": 0.10939530531856739, "estimated_cost_usd": 0.0, "failure_rate": 0.2, "gpu_memory_mb": 1843.3716666666667, "gpu_memory_mb_mean": 2185.39834732862, "gpu_memory_mb_peak": 4417.0, "gpu_util_percent": 10.883002645502645, "gpu_util_percent_mean": 14.035271992382905, "gpu_util_percent_peak": 74.0, "inference_ms": 1131.4123727332724, "measured_audio_duration_sec": 10.628, "memory_mb": 1467.7472027371477, "memory_mb_mean": 1627.0037784544245, "memory_mb_peak": 3408.96484375, "per_utterance_latency_ms": 1131.6576710007212, "postprocess_ms": 0.10883666739876692, "preprocess_ms": 0.13646160005009733, "provider_compute_latency_ms": 1131.6576710007212, "provider_compute_rtf": 0.10903942738780452, "real_time_factor": 0.10903942738780452, "sample_accuracy": 0.03333333333333333, "success_rate": 0.8, "time_to_final_result_ms": 1135.8314183339342, "time_to_first_result_ms": 1135.8314183339342, "time_to_result_ms": 1135.8314183339342, "total_latency_ms": 1131.6576710007212, "wer": 0.7352472089314195}`
