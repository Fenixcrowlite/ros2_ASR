# Benchmark Summary: thesis_ext_20260504T104122Z_local_voxpopuli_de_test_subset

- benchmark_profile: `benchmark/thesis_extended_local_matrix`
- dataset_id: `voxpopuli_de_test_subset`
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
- quality_metrics: `{"cer": 0.09391304347826086, "confidence": 0.0, "sample_accuracy": 0.04, "wer": 0.20297029702970298}`
- latency_metrics: `{"end_to_end_latency_ms": 1668.3385086405906, "end_to_end_rtf": 0.21677907994218276, "inference_ms": 1667.526020140358, "per_utterance_latency_ms": 1668.1109732603363, "postprocess_ms": 0.14081990055274218, "preprocess_ms": 0.4441332194255665, "provider_compute_latency_ms": 1668.1109732603363, "provider_compute_rtf": 0.21674637967376253, "real_time_factor": 0.21674637967376253, "time_to_final_result_ms": 1668.3385086405906, "time_to_first_result_ms": 1668.3385086405906, "time_to_result_ms": 1668.3385086405906, "total_latency_ms": 1668.1109732603363}`
- reliability_metrics: `{"failure_rate": 0.0, "success_rate": 1.0}`
- cost_metrics: `{"estimated_cost_usd": 0.0}`
- cost_totals: `{"estimated_cost_usd": 0.0}`
- estimated_cost_total_usd: `0.0`

### providers/vosk_local (preset: `en_small`)
- samples: `50`
- successful_samples: `50`
- failed_samples: `0`
- quality_metrics: `{"cer": 0.7321739130434782, "confidence": 0.7397793885819755, "sample_accuracy": 0.0, "wer": 1.205940594059406}`
- latency_metrics: `{"end_to_end_latency_ms": 2002.9513176999171, "end_to_end_rtf": 0.24195949226019975, "inference_ms": 1968.644250319776, "per_utterance_latency_ms": 1977.7464551599405, "postprocess_ms": 0.10330203993362375, "preprocess_ms": 8.998902800231008, "provider_compute_latency_ms": 1977.7464551599405, "provider_compute_rtf": 0.23887057435383882, "real_time_factor": 0.23887057435383882, "time_to_final_result_ms": 2002.9513176999171, "time_to_first_result_ms": 2002.9513176999171, "time_to_result_ms": 2002.9513176999171, "total_latency_ms": 1977.7464551599405}`
- reliability_metrics: `{"failure_rate": 0.0, "success_rate": 1.0}`
- cost_metrics: `{"estimated_cost_usd": 0.0}`
- cost_totals: `{"estimated_cost_usd": 0.0}`
- estimated_cost_total_usd: `0.0`

### providers/whisper_local (preset: `light`)
- samples: `50`
- successful_samples: `50`
- failed_samples: `0`
- quality_metrics: `{"cer": 0.1902608695652174, "confidence": 0.7125987072694792, "sample_accuracy": 0.0, "wer": 0.39900990099009903}`
- latency_metrics: `{"end_to_end_latency_ms": 680.5244361405494, "end_to_end_rtf": 0.08481099226944389, "inference_ms": 587.9565610003192, "per_utterance_latency_ms": 680.2288282605878, "postprocess_ms": 0.08543335992726497, "preprocess_ms": 92.1868339003413, "provider_compute_latency_ms": 680.2288282605878, "provider_compute_rtf": 0.08476784613402806, "real_time_factor": 0.08476784613402806, "time_to_final_result_ms": 680.5244361405494, "time_to_first_result_ms": 680.5244361405494, "time_to_result_ms": 680.5244361405494, "total_latency_ms": 680.2288282605878}`
- reliability_metrics: `{"failure_rate": 0.0, "success_rate": 1.0}`
- cost_metrics: `{"estimated_cost_usd": 0.0}`
- cost_totals: `{"estimated_cost_usd": 0.0}`
- estimated_cost_total_usd: `0.0`

## Noise Summary
- clean: `{"audio_duration_sec": 8.795275, "cer": 0.28347826086956524, "confidence": 0.5235776073934147, "cpu_percent": 18.50950111660985, "cpu_percent_mean": 13.63209982616689, "cpu_percent_peak": 98.1, "declared_audio_duration_sec": 8.7953, "duration_mismatch_sec": 0.00016249999999979893, "end_to_end_latency_ms": 1628.5944555677513, "end_to_end_rtf": 0.18982151582326617, "estimated_cost_usd": 0.0, "failure_rate": 0.0, "gpu_memory_mb": 1939.4369436663553, "gpu_memory_mb_mean": 1981.420161376279, "gpu_memory_mb_peak": 4843.0, "gpu_util_percent": 16.843923124805478, "gpu_util_percent_mean": 18.5921608309857, "gpu_util_percent_peak": 70.0, "inference_ms": 1451.8320199012426, "measured_audio_duration_sec": 8.795275, "memory_mb": 1426.8071535224944, "memory_mb_mean": 1456.7348850140054, "memory_mb_peak": 3418.84375, "per_utterance_latency_ms": 1620.884578434925, "postprocess_ms": 0.10553676717487785, "preprocess_ms": 168.94702176650753, "provider_compute_latency_ms": 1620.884578434925, "provider_compute_rtf": 0.18886716329347025, "real_time_factor": 0.18886716329347025, "sample_accuracy": 0.03333333333333333, "success_rate": 1.0, "time_to_final_result_ms": 1628.5944555677513, "time_to_first_result_ms": 1628.5944555677513, "time_to_result_ms": 1628.5944555677513, "total_latency_ms": 1620.884578434925, "wer": 0.566006600660066}`
- white:custom_0db: `{"audio_duration_sec": 8.795275, "cer": 0.4446376811594203, "confidence": 0.40812242697432094, "cpu_percent": 19.29455270293561, "cpu_percent_mean": 15.261526762300367, "cpu_percent_peak": 100.0, "declared_audio_duration_sec": 8.7953, "duration_mismatch_sec": 0.00016249999999979893, "end_to_end_latency_ms": 1510.198931366661, "end_to_end_rtf": 0.1865703132134441, "estimated_cost_usd": 0.0, "failure_rate": 0.0, "gpu_memory_mb": 2038.3558201058202, "gpu_memory_mb_mean": 2042.4979839314283, "gpu_memory_mb_peak": 4857.0, "gpu_util_percent": 16.305462962962963, "gpu_util_percent_mean": 16.168918982208677, "gpu_util_percent_peak": 71.0, "inference_ms": 1502.1282626330503, "measured_audio_duration_sec": 8.795275, "memory_mb": 1474.61460673115, "memory_mb_mean": 1503.4460250972782, "memory_mb_peak": 3416.64453125, "per_utterance_latency_ms": 1502.3516206000447, "postprocess_ms": 0.11575959967255282, "preprocess_ms": 0.10759836732177064, "provider_compute_latency_ms": 1502.3516206000447, "provider_compute_rtf": 0.18562725834763955, "real_time_factor": 0.18562725834763955, "sample_accuracy": 0.0, "success_rate": 1.0, "time_to_final_result_ms": 1510.198931366661, "time_to_first_result_ms": 1510.198931366661, "time_to_result_ms": 1510.198931366661, "total_latency_ms": 1502.3516206000447, "wer": 0.6468646864686468}`
- white:custom_10db: `{"audio_duration_sec": 8.795275, "cer": 0.32405797101449274, "confidence": 0.49471490754945574, "cpu_percent": 19.64067852055352, "cpu_percent_mean": 15.384964535260451, "cpu_percent_peak": 100.0, "declared_audio_duration_sec": 8.7953, "duration_mismatch_sec": 0.00016249999999979893, "end_to_end_latency_ms": 1368.8857340001657, "end_to_end_rtf": 0.1759712146764322, "estimated_cost_usd": 0.0, "failure_rate": 0.0, "gpu_memory_mb": 2033.9143915343916, "gpu_memory_mb_mean": 2187.908152036679, "gpu_memory_mb_peak": 4831.0, "gpu_util_percent": 17.727989417989416, "gpu_util_percent_mean": 19.097306446712622, "gpu_util_percent_peak": 100.0, "inference_ms": 1359.3088737002593, "measured_audio_duration_sec": 8.795275, "memory_mb": 1470.1677909814432, "memory_mb_mean": 1554.283991374844, "memory_mb_peak": 3418.84375, "per_utterance_latency_ms": 1359.5342781334086, "postprocess_ms": 0.11361553357952896, "preprocess_ms": 0.11178889956984979, "provider_compute_latency_ms": 1359.5342781334086, "provider_compute_rtf": 0.17481525153178262, "real_time_factor": 0.17481525153178262, "sample_accuracy": 0.0, "success_rate": 1.0, "time_to_final_result_ms": 1368.8857340001657, "time_to_first_result_ms": 1368.8857340001657, "time_to_result_ms": 1368.8857340001657, "total_latency_ms": 1359.5342781334086, "wer": 0.6056105610561056}`
- white:custom_20db: `{"audio_duration_sec": 8.795275, "cer": 0.2927536231884058, "confidence": 0.5212003444858827, "cpu_percent": 18.733027361797742, "cpu_percent_mean": 14.752946651457533, "cpu_percent_peak": 93.0, "declared_audio_duration_sec": 8.7953, "duration_mismatch_sec": 0.00016249999999979893, "end_to_end_latency_ms": 1279.44074176703, "end_to_end_rtf": 0.1658867164158704, "estimated_cost_usd": 0.0, "failure_rate": 0.0, "gpu_memory_mb": 2032.3141005291004, "gpu_memory_mb_mean": 2283.814559813857, "gpu_memory_mb_peak": 4831.0, "gpu_util_percent": 15.96547619047619, "gpu_util_percent_mean": 17.724024659575406, "gpu_util_percent_peak": 71.0, "inference_ms": 1270.9159738333256, "measured_audio_duration_sec": 8.795275, "memory_mb": 1469.7566778027426, "memory_mb_mean": 1589.89483115132, "memory_mb_peak": 3418.84375, "per_utterance_latency_ms": 1271.1206490009015, "postprocess_ms": 0.09845050080912188, "preprocess_ms": 0.10622466676674473, "provider_compute_latency_ms": 1271.1206490009015, "provider_compute_rtf": 0.1648406118578517, "real_time_factor": 0.1648406118578517, "sample_accuracy": 0.03333333333333333, "success_rate": 1.0, "time_to_final_result_ms": 1279.44074176703, "time_to_first_result_ms": 1279.44074176703, "time_to_result_ms": 1279.44074176703, "total_latency_ms": 1271.1206490009015, "wer": 0.5858085808580858}`
- white:custom_5db: `{"audio_duration_sec": 8.795275, "cer": 0.34898550724637684, "confidence": 0.4730148733493501, "cpu_percent": 19.67330661388853, "cpu_percent_mean": 15.111504545973222, "cpu_percent_peak": 100.0, "declared_audio_duration_sec": 8.7953, "duration_mismatch_sec": 0.00016249999999979893, "end_to_end_latency_ms": 1465.9039081001538, "end_to_end_rtf": 0.18766618065736437, "estimated_cost_usd": 0.0, "failure_rate": 0.0, "gpu_memory_mb": 2036.3949603174603, "gpu_memory_mb_mean": 2091.798020632838, "gpu_memory_mb_peak": 4815.0, "gpu_util_percent": 16.93564935064935, "gpu_util_percent_mean": 17.190185915213178, "gpu_util_percent_peak": 70.0, "inference_ms": 1456.026255699544, "measured_audio_duration_sec": 8.795275, "memory_mb": 1474.1713455160989, "memory_mb_mean": 1522.1688710390251, "memory_mb_peak": 3413.25390625, "per_utterance_latency_ms": 1456.2526349654945, "postprocess_ms": 0.11589643278663668, "preprocess_ms": 0.11048283316389036, "provider_compute_latency_ms": 1456.2526349654945, "provider_compute_rtf": 0.1864910485719716, "real_time_factor": 0.1864910485719716, "sample_accuracy": 0.0, "success_rate": 1.0, "time_to_final_result_ms": 1465.9039081001538, "time_to_first_result_ms": 1465.9039081001538, "time_to_result_ms": 1465.9039081001538, "total_latency_ms": 1456.2526349654945, "wer": 0.6089108910891089}`
