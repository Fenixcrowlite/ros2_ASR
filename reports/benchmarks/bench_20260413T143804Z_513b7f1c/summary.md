# Benchmark Summary: bench_20260413T143804Z_513b7f1c

- benchmark_profile: `default_benchmark`
- dataset_id: `fleurs_en_us_test_subset`
- providers: `providers/aws_cloud, providers/azure_cloud, providers/google_cloud, providers/vosk_local, providers/whisper_local`
- scenario: `clean_baseline`
- execution_mode: `batch`
- noise_modes: `none`
- noise_levels: `clean`
- aggregate_scope: `provider_only`
- total_samples: `10`
- successful_samples: `10`
- failed_samples: `0`
- aggregate_samples: `10`
- corrupted_samples: `0`

## Per-Provider Summary

### providers/aws_cloud (preset: `standard`)
- samples: `2`
- successful_samples: `2`
- failed_samples: `0`
- quality_metrics: `{"cer": 0.12060301507537688, "confidence": 0.99295625, "sample_accuracy": 0.0, "wer": 0.09375}`
- latency_metrics: `{"end_to_end_latency_ms": 12227.403885000002, "end_to_end_rtf": 1.516367212406623, "inference_ms": 9238.278197499938, "per_utterance_latency_ms": 9238.769031999938, "postprocess_ms": 0.4796129999817822, "preprocess_ms": 0.011221500017200015, "provider_compute_latency_ms": 9238.769031999938, "provider_compute_rtf": 1.1540124754326981, "real_time_factor": 1.1540124754326981, "time_to_final_result_ms": 12227.403885000002, "time_to_first_result_ms": 12227.403885000002, "time_to_result_ms": 12227.403885000002, "total_latency_ms": 9238.769031999938}`
- reliability_metrics: `{"failure_rate": 0.0, "success_rate": 1.0}`
- cost_metrics: `{"estimated_cost_usd": 0.003704}`
- cost_totals: `{"estimated_cost_usd": 0.007408}`
- estimated_cost_total_usd: `0.007408`

### providers/azure_cloud (preset: `standard`)
- samples: `2`
- successful_samples: `2`
- failed_samples: `0`
- quality_metrics: `{"cer": 0.1306532663316583, "confidence": 0.7734235, "sample_accuracy": 0.0, "wer": 0.125}`
- latency_metrics: `{"end_to_end_latency_ms": 3097.706262499969, "end_to_end_rtf": 0.322336635560898, "inference_ms": 2511.0235284999476, "per_utterance_latency_ms": 2511.167184999863, "postprocess_ms": 0.12553349995414465, "preprocess_ms": 0.01812299996117872, "provider_compute_latency_ms": 2511.167184999863, "provider_compute_rtf": 0.2709653747187768, "real_time_factor": 0.2709653747187768, "time_to_final_result_ms": 3097.706262499969, "time_to_first_result_ms": 3097.706262499969, "time_to_result_ms": 3097.706262499969, "total_latency_ms": 2511.167184999863}`
- reliability_metrics: `{"failure_rate": 0.0, "success_rate": 1.0}`
- cost_metrics: `{"estimated_cost_usd": 0.002778}`
- cost_totals: `{"estimated_cost_usd": 0.005556}`
- estimated_cost_total_usd: `0.005556`

### providers/google_cloud (preset: `accurate`)
- samples: `2`
- successful_samples: `2`
- failed_samples: `0`
- quality_metrics: `{"cer": 0.1407035175879397, "confidence": 0.9141215980052948, "sample_accuracy": 0.0, "wer": 0.15625}`
- latency_metrics: `{"end_to_end_latency_ms": 2030.0959560000251, "end_to_end_rtf": 0.23458319155284235, "inference_ms": 1996.2522544999501, "per_utterance_latency_ms": 2028.9211639999394, "postprocess_ms": 0.0001859999656517175, "preprocess_ms": 32.66872350002359, "provider_compute_latency_ms": 2028.9211639999394, "provider_compute_rtf": 0.2344457574019906, "real_time_factor": 0.2344457574019906, "time_to_final_result_ms": 2030.0959560000251, "time_to_first_result_ms": 2030.0959560000251, "time_to_result_ms": 2030.0959560000251, "total_latency_ms": 2028.9211639999394}`
- reliability_metrics: `{"failure_rate": 0.0, "success_rate": 1.0}`
- cost_metrics: `{"estimated_cost_usd": 0.0}`
- cost_totals: `{"estimated_cost_usd": 0.0}`
- estimated_cost_total_usd: `0.0`

### providers/vosk_local (preset: `en_small`)
- samples: `2`
- successful_samples: `2`
- failed_samples: `0`
- quality_metrics: `{"cer": 0.16080402010050251, "confidence": 0.8802833466386555, "sample_accuracy": 0.0, "wer": 0.28125}`
- latency_metrics: `{"end_to_end_latency_ms": 1585.846065499993, "end_to_end_rtf": 0.16745638738643948, "inference_ms": 1346.6076494999584, "per_utterance_latency_ms": 1575.418354999897, "postprocess_ms": 0.06587149999859321, "preprocess_ms": 228.74483399994006, "provider_compute_latency_ms": 1575.418354999897, "provider_compute_rtf": 0.16619744156870353, "real_time_factor": 0.16619744156870353, "time_to_final_result_ms": 1585.846065499993, "time_to_first_result_ms": 1585.846065499993, "time_to_result_ms": 1585.846065499993, "total_latency_ms": 1575.418354999897}`
- reliability_metrics: `{"failure_rate": 0.0, "success_rate": 1.0}`
- cost_metrics: `{"estimated_cost_usd": 0.0}`
- cost_totals: `{"estimated_cost_usd": 0.0}`
- estimated_cost_total_usd: `0.0`

### providers/whisper_local (preset: `accurate`)
- samples: `2`
- successful_samples: `2`
- failed_samples: `0`
- quality_metrics: `{"cer": 0.1306532663316583, "confidence": 0.9314740753585882, "sample_accuracy": 0.0, "wer": 0.125}`
- latency_metrics: `{"end_to_end_latency_ms": 2429.663140500054, "end_to_end_rtf": 0.2781921831428211, "inference_ms": 1921.0684169999581, "per_utterance_latency_ms": 2429.3747019999614, "postprocess_ms": 0.08920400000533846, "preprocess_ms": 508.21708099999796, "provider_compute_latency_ms": 2429.3747019999614, "provider_compute_rtf": 0.27815676949942414, "real_time_factor": 0.27815676949942414, "time_to_final_result_ms": 2429.663140500054, "time_to_first_result_ms": 2429.663140500054, "time_to_result_ms": 2429.663140500054, "total_latency_ms": 2429.3747019999614}`
- reliability_metrics: `{"failure_rate": 0.0, "success_rate": 1.0}`
- cost_metrics: `{"estimated_cost_usd": 0.0}`
- cost_totals: `{"estimated_cost_usd": 0.0}`
- estimated_cost_total_usd: `0.0`

## Noise Summary
- clean: `{"audio_duration_sec": 9.26, "cer": 0.13668341708542714, "confidence": 0.8984517540005077, "cpu_percent": 7.683674490838678, "cpu_percent_mean": 5.478939459462871, "cpu_percent_peak": 88.2, "declared_audio_duration_sec": 9.26, "duration_mismatch_sec": 0.0, "end_to_end_latency_ms": 4274.143061900008, "end_to_end_rtf": 0.5037871220099248, "estimated_cost_usd": 0.0012963999999999999, "failure_rate": 0.0, "gpu_memory_mb": 431.071968641115, "gpu_memory_mb_mean": 434.08357954325834, "gpu_memory_mb_peak": 449.0, "gpu_util_percent": 0.9561265969802555, "gpu_util_percent_mean": 2.5843627219026457, "gpu_util_percent_peak": 50.0, "inference_ms": 3402.6460093999503, "measured_audio_duration_sec": 9.26, "memory_mb": 1091.7161152004157, "memory_mb_mean": 1031.3287424886178, "memory_mb_peak": 1696.6171875, "per_utterance_latency_ms": 3556.7300875999194, "postprocess_ms": 0.15208159998110204, "preprocess_ms": 153.931996599988, "provider_compute_latency_ms": 3556.7300875999194, "provider_compute_rtf": 0.42075556372431866, "real_time_factor": 0.42075556372431866, "sample_accuracy": 0.0, "success_rate": 1.0, "time_to_final_result_ms": 4274.143061900008, "time_to_first_result_ms": 4274.143061900008, "time_to_result_ms": 4274.143061900008, "total_latency_ms": 3556.7300875999194, "wer": 0.15625}`
