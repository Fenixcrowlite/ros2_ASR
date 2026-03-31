# Benchmark Summary: bench_20260331T130252Z_e20dc37e

- benchmark_profile: `default_benchmark`
- dataset_id: `fleurs_en_us_test_subset`
- providers: `providers/aws_cloud, providers/azure_cloud, providers/google_cloud`
- scenario: `noise_robustness`
- execution_mode: `streaming`
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
- quality_metrics: `{"cer": 0.16482412060301507, "confidence": 0.9498823725490196, "sample_accuracy": 0.0, "wer": 0.19375}`
- latency_metrics: `{"inference_ms": 8574.593240395188, "per_utterance_latency_ms": 8909.9800401018, "postprocess_ms": 335.3867997066118, "preprocess_ms": 0.0, "real_time_factor": 0.9620540319856914, "total_latency_ms": 8909.9800401018}`
- reliability_metrics: `{"failure_rate": 0.0, "success_rate": 1.0}`
- cost_metrics: `{"estimated_cost_usd": 0.003704}`
- cost_totals: `{"estimated_cost_usd": 0.03704}`
- streaming_metrics: `{"finalization_latency_ms": 335.3869, "first_partial_latency_ms": 1037.1738, "partial_count": 13.4}`
- estimated_cost_total_usd: `0.03704`

### providers/azure_cloud (preset: `standard`)
- samples: `10`
- successful_samples: `10`
- failed_samples: `0`
- quality_metrics: `{"cer": 0.15577889447236182, "confidence": 0.724509182, "sample_accuracy": 0.0, "wer": 0.16875}`
- latency_metrics: `{"inference_ms": 9252.064199978486, "per_utterance_latency_ms": 9437.928490393097, "postprocess_ms": 185.86429041461088, "preprocess_ms": 0.0, "real_time_factor": 1.0254207079018398, "total_latency_ms": 9437.928490393097}`
- reliability_metrics: `{"failure_rate": 0.0, "success_rate": 1.0}`
- cost_metrics: `{"estimated_cost_usd": 0.002778}`
- cost_totals: `{"estimated_cost_usd": 0.02778}`
- streaming_metrics: `{"finalization_latency_ms": 185.8642, "first_partial_latency_ms": 2734.1043, "partial_count": 9.2}`
- estimated_cost_total_usd: `0.02778`

### providers/google_cloud (preset: `accurate`)
- samples: `10`
- successful_samples: `10`
- failed_samples: `0`
- quality_metrics: `{"cer": 0.1798994974874372, "confidence": 0.8608106553554535, "sample_accuracy": 0.0, "wer": 0.21875}`
- latency_metrics: `{"inference_ms": 9066.549522901187, "per_utterance_latency_ms": 9329.957114200806, "postprocess_ms": 263.4075912996195, "preprocess_ms": 0.0, "real_time_factor": 1.0260823957222949, "total_latency_ms": 9329.957114200806}`
- reliability_metrics: `{"failure_rate": 0.0, "success_rate": 1.0}`
- cost_metrics: `{"estimated_cost_usd": 0.0}`
- cost_totals: `{"estimated_cost_usd": 0.0}`
- streaming_metrics: `{"finalization_latency_ms": 263.4076, "first_partial_latency_ms": 1012.0387, "partial_count": 60.1}`
- estimated_cost_total_usd: `0.0`

## Noise Summary
- clean: `{"cer": 0.1390284757118928, "confidence": 0.8910623144009908, "cpu_percent": 8.733333333333333, "estimated_cost_usd": 0.0021606666666666666, "failure_rate": 0.0, "finalization_latency_ms": 180.35333333333332, "first_partial_latency_ms": 1323.2433333333333, "gpu_memory_mb": 870.1666666666666, "gpu_util_percent": 0.6666666666666666, "inference_ms": 8635.061901334362, "memory_mb": 162.41536458333334, "model_load_ms": 29.412683333333334, "partial_count": 27.5, "per_utterance_latency_ms": 8815.41541533079, "postprocess_ms": 180.35351399642727, "preprocess_ms": 0.0, "provider_call_cold_start": 0.5, "provider_call_warm_start": 0.5, "provider_init_cold_start": 1.0, "provider_init_warm_start": 0.0, "provider_invocation_index": 3.5, "real_time_factor": 0.9672433965649138, "sample_accuracy": 0.0, "success_rate": 1.0, "total_latency_ms": 8815.41541533079, "wer": 0.14583333333333334}`
- extreme: `{"cer": 0.2747068676716918, "confidence": 0.6828985513925425, "cpu_percent": 13.633333333333333, "estimated_cost_usd": 0.0021606666666666666, "failure_rate": 0.0, "finalization_latency_ms": 258.836, "first_partial_latency_ms": 1816.3876666666665, "gpu_memory_mb": 886.5, "gpu_util_percent": 14.5, "inference_ms": 9048.318721344307, "memory_mb": 170.23307291666666, "model_load_ms": 29.412683333333334, "partial_count": 29.0, "per_utterance_latency_ms": 9307.15446601001, "postprocess_ms": 258.8357446657028, "preprocess_ms": 0.0, "provider_call_cold_start": 0.0, "provider_call_warm_start": 1.0, "provider_init_cold_start": 1.0, "provider_init_warm_start": 0.0, "provider_invocation_index": 7.5, "real_time_factor": 1.0017179917909529, "sample_accuracy": 0.0, "success_rate": 1.0, "total_latency_ms": 9307.15446601001, "wer": 0.375}`
- heavy: `{"cer": 0.1423785594639866, "confidence": 0.8667413817652015, "cpu_percent": 19.7, "estimated_cost_usd": 0.0021606666666666666, "failure_rate": 0.0, "finalization_latency_ms": 196.80983333333333, "first_partial_latency_ms": 1566.195, "gpu_memory_mb": 868.5, "gpu_util_percent": 15.5, "inference_ms": 9054.04684697472, "memory_mb": 168.61002604166666, "model_load_ms": 29.412683333333334, "partial_count": 28.333333333333332, "per_utterance_latency_ms": 9250.85675548568, "postprocess_ms": 196.8099085109619, "preprocess_ms": 0.0, "provider_call_cold_start": 0.0, "provider_call_warm_start": 1.0, "provider_init_cold_start": 1.0, "provider_init_warm_start": 0.0, "provider_invocation_index": 6.5, "real_time_factor": 1.003460893957273, "sample_accuracy": 0.0, "success_rate": 1.0, "total_latency_ms": 9250.85675548568, "wer": 0.15625}`
- light: `{"cer": 0.1390284757118928, "confidence": 0.8919635799226888, "cpu_percent": 8.316666666666666, "estimated_cost_usd": 0.0021606666666666666, "failure_rate": 0.0, "finalization_latency_ms": 195.90433333333334, "first_partial_latency_ms": 1618.5223333333333, "gpu_memory_mb": 861.8333333333334, "gpu_util_percent": 1.0, "inference_ms": 9036.385134987844, "memory_mb": 166.17578125, "model_load_ms": 29.412683333333334, "partial_count": 26.333333333333332, "per_utterance_latency_ms": 9232.289365492761, "postprocess_ms": 195.9042305049176, "preprocess_ms": 0.0, "provider_call_cold_start": 0.0, "provider_call_warm_start": 1.0, "provider_init_cold_start": 1.0, "provider_init_warm_start": 0.0, "provider_invocation_index": 4.5, "real_time_factor": 1.0002804632402889, "sample_accuracy": 0.0, "success_rate": 1.0, "total_latency_ms": 9232.289365492761, "wer": 0.14583333333333334}`
- medium: `{"cer": 0.1390284757118928, "confidence": 0.8926711890260315, "cpu_percent": 7.75, "estimated_cost_usd": 0.0021606666666666666, "failure_rate": 0.0, "finalization_latency_ms": 475.861, "first_partial_latency_ms": 1647.8463333333334, "gpu_memory_mb": 866.0, "gpu_util_percent": 12.666666666666666, "inference_ms": 9048.19900081687, "memory_mb": 166.85677083333334, "model_load_ms": 29.412683333333334, "partial_count": 26.666666666666668, "per_utterance_latency_ms": 9524.060072173597, "postprocess_ms": 475.86107135672745, "preprocess_ms": 0.0, "provider_call_cold_start": 0.0, "provider_call_warm_start": 1.0, "provider_init_cold_start": 1.0, "provider_init_warm_start": 0.0, "provider_invocation_index": 5.5, "real_time_factor": 1.0498924804629486, "sample_accuracy": 0.0, "success_rate": 1.0, "total_latency_ms": 9524.060072173597, "wer": 0.14583333333333334}`
