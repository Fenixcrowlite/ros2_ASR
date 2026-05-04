# Benchmark Summary: thesis_ext_20260504T115425Z_cloud_voxpopuli_es_test_subset

- benchmark_profile: `benchmark/thesis_extended_cloud_matrix`
- dataset_id: `voxpopuli_es_test_subset`
- providers: `providers/azure_cloud, providers/google_cloud, providers/aws_cloud`
- scenario: `clean`
- execution_mode: `batch`
- noise_modes: `none`
- noise_levels: `clean`
- aggregate_scope: `provider_only`
- total_samples: `30`
- successful_samples: `30`
- failed_samples: `0`
- aggregate_samples: `30`
- corrupted_samples: `0`

## Per-Provider Summary

### providers/aws_cloud (preset: `standard`)
- samples: `10`
- successful_samples: `10`
- failed_samples: `0`
- quality_metrics: `{"cer": 0.05211912943871707, "confidence": 0.9563668211334178, "sample_accuracy": 0.2, "wer": 0.07331378299120235}`
- latency_metrics: `{"end_to_end_latency_ms": 11074.681688800047, "end_to_end_rtf": 1.0353448012468103, "inference_ms": 10225.923195698851, "per_utterance_latency_ms": 10226.017203399533, "postprocess_ms": 0.0869234005222097, "preprocess_ms": 0.0070843001594766974, "provider_compute_latency_ms": 10226.017203399533, "provider_compute_rtf": 0.9543897321004089, "real_time_factor": 0.9543897321004089, "time_to_final_result_ms": 11074.681688800047, "time_to_first_result_ms": 11074.681688800047, "time_to_result_ms": 11074.681688800047, "total_latency_ms": 10226.017203399533}`
- reliability_metrics: `{"failure_rate": 0.0, "success_rate": 1.0}`
- cost_metrics: `{"estimated_cost_usd": 0.0050163875}`
- cost_totals: `{"estimated_cost_usd": 0.050163875000000004}`
- estimated_cost_total_usd: `0.050163875000000004`

### providers/azure_cloud (preset: `standard`)
- samples: `10`
- successful_samples: `10`
- failed_samples: `0`
- quality_metrics: `{"cer": 0.13459335624284077, "confidence": 0.869848104, "sample_accuracy": 0.2, "wer": 0.16129032258064516}`
- latency_metrics: `{"end_to_end_latency_ms": 4452.792032599973, "end_to_end_rtf": 0.3347102443387874, "inference_ms": 4221.098575599171, "per_utterance_latency_ms": 4221.191200499015, "postprocess_ms": 0.08568310076952912, "preprocess_ms": 0.006941799074411392, "provider_compute_latency_ms": 4221.191200499015, "provider_compute_rtf": 0.3108222592710861, "real_time_factor": 0.3108222592710861, "time_to_final_result_ms": 4452.792032599973, "time_to_first_result_ms": 4452.792032599973, "time_to_result_ms": 4452.792032599973, "total_latency_ms": 4221.191200499015}`
- reliability_metrics: `{"failure_rate": 0.0, "success_rate": 1.0}`
- cost_metrics: `{"estimated_cost_usd": 0.003762290625}`
- cost_totals: `{"estimated_cost_usd": 0.03762290625}`
- estimated_cost_total_usd: `0.03762290625`

### providers/google_cloud (preset: `balanced`)
- samples: `10`
- successful_samples: `10`
- failed_samples: `0`
- quality_metrics: `{"cer": 0.09221076746849943, "confidence": 0.9569252669811249, "sample_accuracy": 0.1, "wer": 0.1348973607038123}`
- latency_metrics: `{"end_to_end_latency_ms": 2958.115008599998, "end_to_end_rtf": 0.23639545844167625, "inference_ms": 2870.19578780164, "per_utterance_latency_ms": 2956.9546696991893, "postprocess_ms": 0.00016039848560467362, "preprocess_ms": 86.75872149906354, "provider_compute_latency_ms": 2956.9546696991893, "provider_compute_rtf": 0.23628976146769762, "real_time_factor": 0.23628976146769762, "time_to_final_result_ms": 2958.115008599998, "time_to_first_result_ms": 2958.115008599998, "time_to_result_ms": 2958.115008599998, "total_latency_ms": 2956.9546696991893}`
- reliability_metrics: `{"failure_rate": 0.0, "success_rate": 1.0}`
- cost_metrics: `{"estimated_cost_usd": 0.0}`
- cost_totals: `{"estimated_cost_usd": 0.0}`
- estimated_cost_total_usd: `0.0`

## Noise Summary
- clean: `{"audio_duration_sec": 12.540968750000001, "cer": 0.09297441771668576, "confidence": 0.9277133973715141, "cpu_percent": 4.709693591308301, "cpu_percent_mean": 5.022621612263659, "cpu_percent_peak": 100.0, "declared_audio_duration_sec": 12.541, "duration_mismatch_sec": 6.875000000006182e-05, "end_to_end_latency_ms": 6161.862910000006, "end_to_end_rtf": 0.5354835013424246, "estimated_cost_usd": 0.0029262260416666667, "failure_rate": 0.0, "gpu_memory_mb": 695.3867678438475, "gpu_memory_mb_mean": 695.0533191138375, "gpu_memory_mb_peak": 754.0, "gpu_util_percent": 7.08588167373973, "gpu_util_percent_mean": 7.239635817647568, "gpu_util_percent_peak": 58.0, "inference_ms": 5772.405853033221, "measured_audio_duration_sec": 12.540968750000001, "memory_mb": 153.35019806533836, "memory_mb_mean": 180.38101974263932, "memory_mb_peak": 286.58203125, "per_utterance_latency_ms": 5801.387691199246, "postprocess_ms": 0.05758896659244783, "preprocess_ms": 28.924249199432477, "provider_compute_latency_ms": 5801.387691199246, "provider_compute_rtf": 0.5005005842797309, "real_time_factor": 0.5005005842797309, "sample_accuracy": 0.16666666666666666, "success_rate": 1.0, "time_to_final_result_ms": 6161.862910000006, "time_to_first_result_ms": 6161.862910000006, "time_to_result_ms": 6161.862910000006, "total_latency_ms": 5801.387691199246, "wer": 0.12316715542521994}`
