# Benchmark Summary: bench_20260425T221457Z_1499e577

- benchmark_profile: `default_benchmark`
- dataset_id: `fleurs_en_us_test_subset`
- providers: `providers/aws_cloud, providers/azure_cloud, providers/google_cloud, providers/vosk_local, providers/whisper_local`
- scenario: `noise_robustness`
- execution_mode: `batch`
- noise_modes: `none, white`
- noise_levels: `clean, extreme, heavy, light, medium`
- aggregate_scope: `provider_only`
- total_samples: `50`
- successful_samples: `38`
- failed_samples: `12`
- aggregate_samples: `50`
- corrupted_samples: `0`

## Per-Provider Summary

### providers/aws_cloud (preset: `standard`)
- samples: `10`
- successful_samples: `10`
- failed_samples: `0`
- quality_metrics: `{"cer": 0.16482412060301507, "confidence": 0.96976, "sample_accuracy": 0.0, "wer": 0.14375}`
- latency_metrics: `{"end_to_end_latency_ms": 10413.98420009973, "end_to_end_rtf": 1.2914902490312137, "inference_ms": 8739.206264699897, "per_utterance_latency_ms": 8739.487578599801, "postprocess_ms": 0.2713712998229312, "preprocess_ms": 0.00994260008155834, "provider_compute_latency_ms": 8739.487578599801, "provider_compute_rtf": 1.0882393355620377, "real_time_factor": 1.0882393355620377, "time_to_final_result_ms": 10413.98420009973, "time_to_first_result_ms": 10413.98420009973, "time_to_result_ms": 10413.98420009973, "total_latency_ms": 8739.487578599801}`
- reliability_metrics: `{"failure_rate": 0.0, "success_rate": 1.0}`
- cost_metrics: `{"estimated_cost_usd": 0.003704}`
- cost_totals: `{"estimated_cost_usd": 0.03704}`
- estimated_cost_total_usd: `0.03704`

### providers/azure_cloud (preset: `standard`)
- samples: `10`
- successful_samples: `0`
- failed_samples: `10`
- quality_metrics: `{"cer": 1.0, "confidence": 0.0, "sample_accuracy": 0.0, "wer": 1.0}`
- latency_metrics: `{"end_to_end_latency_ms": 165.9266889997525, "end_to_end_rtf": 0.01995887686019103, "inference_ms": 0.0, "per_utterance_latency_ms": 0.0, "postprocess_ms": 0.0, "preprocess_ms": 0.0, "provider_compute_latency_ms": 0.0, "provider_compute_rtf": 0.0, "real_time_factor": 0.0, "time_to_final_result_ms": 165.9266889997525, "time_to_first_result_ms": 165.9266889997525, "time_to_result_ms": 165.9266889997525, "total_latency_ms": 0.0}`
- reliability_metrics: `{"failure_rate": 1.0, "success_rate": 0.0}`
- cost_metrics: `{"estimated_cost_usd": 0.002778}`
- cost_totals: `{"estimated_cost_usd": 0.02778}`
- estimated_cost_total_usd: `0.02778`

### providers/google_cloud (preset: `accurate`)
- samples: `10`
- successful_samples: `10`
- failed_samples: `0`
- quality_metrics: `{"cer": 0.24723618090452262, "confidence": 0.7587153866887093, "sample_accuracy": 0.0, "wer": 0.3}`
- latency_metrics: `{"end_to_end_latency_ms": 1932.0657973996276, "end_to_end_rtf": 0.20688987258842015, "inference_ms": 1805.8540952999465, "per_utterance_latency_ms": 1931.282430200372, "postprocess_ms": 0.0001481999788666144, "preprocess_ms": 125.42818670044653, "provider_compute_latency_ms": 1931.282430200372, "provider_compute_rtf": 0.20679266280730374, "real_time_factor": 0.20679266280730374, "time_to_final_result_ms": 1932.0657973996276, "time_to_first_result_ms": 1932.0657973996276, "time_to_result_ms": 1932.0657973996276, "total_latency_ms": 1931.282430200372}`
- reliability_metrics: `{"failure_rate": 0.0, "success_rate": 1.0}`
- cost_metrics: `{"estimated_cost_usd": 0.0}`
- cost_totals: `{"estimated_cost_usd": 0.0}`
- estimated_cost_total_usd: `0.0`

### providers/vosk_local (preset: `en_small`)
- samples: `10`
- successful_samples: `8`
- failed_samples: `2`
- quality_metrics: `{"cer": 0.4623115577889447, "confidence": 0.6267103112789661, "sample_accuracy": 0.0, "wer": 0.6375}`
- latency_metrics: `{"end_to_end_latency_ms": 1136.6647087001184, "end_to_end_rtf": 0.12326468445031459, "inference_ms": 1077.6267167995684, "per_utterance_latency_ms": 1126.3835238998581, "postprocess_ms": 0.10524410026846454, "preprocess_ms": 48.65156300002127, "provider_compute_latency_ms": 1126.3835238998581, "provider_compute_rtf": 0.12215921670083284, "real_time_factor": 0.12215921670083284, "time_to_final_result_ms": 1136.6647087001184, "time_to_first_result_ms": 1136.6647087001184, "time_to_result_ms": 1136.6647087001184, "total_latency_ms": 1126.3835238998581}`
- reliability_metrics: `{"failure_rate": 0.2, "success_rate": 0.8}`
- cost_metrics: `{"estimated_cost_usd": 0.0}`
- cost_totals: `{"estimated_cost_usd": 0.0}`
- estimated_cost_total_usd: `0.0`

### providers/whisper_local (preset: `accurate`)
- samples: `10`
- successful_samples: `10`
- failed_samples: `0`
- quality_metrics: `{"cer": 0.21708542713567838, "confidence": 0.8378531790490642, "sample_accuracy": 0.0, "wer": 0.30625}`
- latency_metrics: `{"end_to_end_latency_ms": 2480.1447914000164, "end_to_end_rtf": 0.2894254816089561, "inference_ms": 2065.9707848000835, "per_utterance_latency_ms": 2479.839476900088, "postprocess_ms": 0.08539999944332521, "preprocess_ms": 413.7832921005611, "provider_compute_latency_ms": 2479.839476900088, "provider_compute_rtf": 0.28938928392980756, "real_time_factor": 0.28938928392980756, "time_to_final_result_ms": 2480.1447914000164, "time_to_first_result_ms": 2480.1447914000164, "time_to_result_ms": 2480.1447914000164, "total_latency_ms": 2479.839476900088}`
- reliability_metrics: `{"failure_rate": 0.0, "success_rate": 1.0}`
- cost_metrics: `{"estimated_cost_usd": 0.0}`
- cost_totals: `{"estimated_cost_usd": 0.0}`
- estimated_cost_total_usd: `0.0`

## Noise Summary
- clean: `{"audio_duration_sec": 9.26, "cer": 0.3185929648241206, "confidence": 0.749234780881723, "cpu_percent": 9.372774591802004, "cpu_percent_mean": 7.532792477957631, "cpu_percent_peak": 100.0, "declared_audio_duration_sec": 9.26, "duration_mismatch_sec": 0.0, "end_to_end_latency_ms": 3737.3229033000825, "end_to_end_rtf": 0.43034714127596885, "estimated_cost_usd": 0.0012963999999999999, "failure_rate": 0.2, "gpu_memory_mb": 585.296746031746, "gpu_memory_mb_mean": 560.0708926711558, "gpu_memory_mb_peak": 733.0, "gpu_util_percent": 5.561428571428571, "gpu_util_percent_mean": 5.213558203405151, "gpu_util_percent_peak": 80.0, "inference_ms": 2734.173505500439, "measured_audio_duration_sec": 9.26, "memory_mb": 429.1642237548061, "memory_mb_mean": 394.4318590862619, "memory_mb_peak": 1399.14453125, "per_utterance_latency_ms": 3321.853387601004, "postprocess_ms": 0.08450220011582132, "preprocess_ms": 587.5953799004492, "provider_compute_latency_ms": 3321.853387601004, "provider_compute_rtf": 0.3815235227712577, "real_time_factor": 0.3815235227712577, "sample_accuracy": 0.0, "success_rate": 0.8, "time_to_final_result_ms": 3737.3229033000825, "time_to_first_result_ms": 3737.3229033000825, "time_to_result_ms": 3737.3229033000825, "total_latency_ms": 3321.853387601004, "wer": 0.35625}`
- white:extreme: `{"audio_duration_sec": 9.26, "cer": 0.6934673366834171, "confidence": 0.38285727292657307, "cpu_percent": 9.708290248673697, "cpu_percent_mean": 8.215010253676413, "cpu_percent_peak": 90.0, "declared_audio_duration_sec": 9.26, "duration_mismatch_sec": 0.0, "end_to_end_latency_ms": 3191.977302899977, "end_to_end_rtf": 0.3798103219744923, "estimated_cost_usd": 0.0012963999999999999, "failure_rate": 0.3, "gpu_memory_mb": 586.4311134453782, "gpu_memory_mb_mean": 583.975118551976, "gpu_memory_mb_peak": 696.0, "gpu_util_percent": 5.896050420168067, "gpu_util_percent_mean": 7.643836974866001, "gpu_util_percent_peak": 63.0, "inference_ms": 2853.5691999000846, "measured_audio_duration_sec": 9.26, "memory_mb": 485.1961019981695, "memory_mb_mean": 374.5708918656967, "memory_mb_peak": 1597.37109375, "per_utterance_latency_ms": 2853.735083700303, "postprocess_ms": 0.09229989955201745, "preprocess_ms": 0.07358390066656284, "provider_compute_latency_ms": 2853.735083700303, "provider_compute_rtf": 0.3386385195629007, "real_time_factor": 0.3386385195629007, "sample_accuracy": 0.0, "success_rate": 0.7, "time_to_final_result_ms": 3191.977302899977, "time_to_first_result_ms": 3191.977302899977, "time_to_result_ms": 3191.977302899977, "total_latency_ms": 2853.735083700303, "wer": 0.84375}`
- white:heavy: `{"audio_duration_sec": 9.26, "cer": 0.38994974874371857, "confidence": 0.6178082717218972, "cpu_percent": 9.916179898532839, "cpu_percent_mean": 7.380083030082513, "cpu_percent_peak": 88.7, "declared_audio_duration_sec": 9.26, "duration_mismatch_sec": 0.0, "end_to_end_latency_ms": 3019.456545799767, "end_to_end_rtf": 0.36567955261190366, "estimated_cost_usd": 0.0012963999999999999, "failure_rate": 0.3, "gpu_memory_mb": 594.5661134453782, "gpu_memory_mb_mean": 575.1400973788121, "gpu_memory_mb_peak": 658.0, "gpu_util_percent": 10.47607843137255, "gpu_util_percent_mean": 9.57658938526439, "gpu_util_percent_peak": 59.0, "inference_ms": 2672.103157599122, "measured_audio_duration_sec": 9.26, "memory_mb": 477.89738923453996, "memory_mb_mean": 353.29191484790283, "memory_mb_peak": 1472.21875, "per_utterance_latency_ms": 2672.262648499236, "postprocess_ms": 0.0956150997808436, "preprocess_ms": 0.06387580033333506, "provider_compute_latency_ms": 2672.262648499236, "provider_compute_rtf": 0.3231385207924373, "real_time_factor": 0.3231385207924373, "sample_accuracy": 0.0, "success_rate": 0.7, "time_to_final_result_ms": 3019.456545799767, "time_to_first_result_ms": 3019.456545799767, "time_to_result_ms": 3019.456545799767, "total_latency_ms": 2672.262648499236, "wer": 0.425}`
- white:light: `{"audio_duration_sec": 9.26, "cer": 0.32261306532663314, "confidence": 0.7466939850243055, "cpu_percent": 11.02000618646007, "cpu_percent_mean": 7.793975304579815, "cpu_percent_peak": 88.7, "declared_audio_duration_sec": 9.26, "duration_mismatch_sec": 0.0, "end_to_end_latency_ms": 3115.2795307993074, "end_to_end_rtf": 0.38119678149737524, "estimated_cost_usd": 0.0012963999999999999, "failure_rate": 0.2, "gpu_memory_mb": 586.0664682539682, "gpu_memory_mb_mean": 562.6466389646886, "gpu_memory_mb_peak": 676.0, "gpu_util_percent": 9.918253968253968, "gpu_util_percent_mean": 8.445547955220867, "gpu_util_percent_peak": 56.0, "inference_ms": 2714.0744491003716, "measured_audio_duration_sec": 9.26, "memory_mb": 471.8040028494098, "memory_mb_mean": 342.5212873588737, "memory_mb_peak": 1596.359375, "per_utterance_latency_ms": 2714.25016830035, "postprocess_ms": 0.09266540000680834, "preprocess_ms": 0.08305379997182172, "provider_compute_latency_ms": 2714.25016830035, "provider_compute_rtf": 0.33207735684154227, "real_time_factor": 0.33207735684154227, "sample_accuracy": 0.0, "success_rate": 0.8, "time_to_final_result_ms": 3115.2795307993074, "time_to_first_result_ms": 3115.2795307993074, "time_to_result_ms": 3115.2795307993074, "total_latency_ms": 2714.25016830035, "wer": 0.3625}`
- white:medium: `{"audio_duration_sec": 9.26, "cer": 0.36683417085427134, "confidence": 0.6964445664622407, "cpu_percent": 11.881482184482184, "cpu_percent_mean": 7.429253494971252, "cpu_percent_peak": 89.4, "declared_audio_duration_sec": 9.26, "duration_mismatch_sec": 0.0, "end_to_end_latency_ms": 3064.7499038001115, "end_to_end_rtf": 0.3739953671793556, "estimated_cost_usd": 0.0012963999999999999, "failure_rate": 0.2, "gpu_memory_mb": 593.0568253968254, "gpu_memory_mb_mean": 575.2347880593258, "gpu_memory_mb_peak": 699.0, "gpu_util_percent": 11.463968253968254, "gpu_util_percent_mean": 7.32789163182915, "gpu_util_percent_peak": 77.0, "inference_ms": 2714.7375494994776, "measured_audio_duration_sec": 9.26, "memory_mb": 472.5945093357164, "memory_mb_mean": 346.19142796093894, "memory_mb_peak": 1519.67578125, "per_utterance_latency_ms": 2714.8917214992252, "postprocess_ms": 0.09708100005809683, "preprocess_ms": 0.05709099968953524, "provider_compute_latency_ms": 2714.8917214992252, "provider_compute_rtf": 0.33120257903184386, "real_time_factor": 0.33120257903184386, "sample_accuracy": 0.0, "success_rate": 0.8, "time_to_final_result_ms": 3064.7499038001115, "time_to_first_result_ms": 3064.7499038001115, "time_to_result_ms": 3064.7499038001115, "total_latency_ms": 2714.8917214992252, "wer": 0.4}`
