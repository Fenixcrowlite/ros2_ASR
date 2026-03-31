# Benchmark Summary: bench_20260331T123337Z_4926faad

- benchmark_profile: `default_benchmark`
- dataset_id: `fleurs_en_us_test_subset`
- providers: `providers/aws_cloud, providers/azure_cloud, providers/google_cloud`
- scenario: `noise_robustness`
- execution_mode: `streaming`
- aggregate_scope: `provider_only`
- total_samples: `18`
- successful_samples: `18`
- failed_samples: `0`
- aggregate_samples: `18`
- corrupted_samples: `0`

## Per-Provider Summary

### providers/aws_cloud (preset: `standard`)
- samples: `6`
- successful_samples: `6`
- failed_samples: `0`
- quality_metrics: `{"cer": 0.17922948073701842, "confidence": 0.9412858333333334, "sample_accuracy": 0.0, "wer": 0.20833333333333334}`
- latency_metrics: `{"inference_ms": 8560.903816328695, "per_utterance_latency_ms": 8907.674661992738, "postprocess_ms": 346.7708456640442, "preprocess_ms": 0.0, "real_time_factor": 0.9578742225568816, "total_latency_ms": 8907.674661992738}`
- reliability_metrics: `{"failure_rate": 0.0, "success_rate": 1.0}`
- cost_metrics: `{"estimated_cost_usd": 0.003704}`
- cost_totals: `{"estimated_cost_usd": 0.022224}`
- streaming_metrics: `{"finalization_latency_ms": 346.7708333333333, "first_partial_latency_ms": 1074.5203333333334, "partial_count": 13.333333333333334}`
- estimated_cost_total_usd: `0.022224`

### providers/azure_cloud (preset: `standard`)
- samples: `6`
- successful_samples: `6`
- failed_samples: `0`
- quality_metrics: `{"cer": 0.17252931323283083, "confidence": 0.6806720216666666, "sample_accuracy": 0.0, "wer": 0.19791666666666666}`
- latency_metrics: `{"inference_ms": 9241.65433983823, "per_utterance_latency_ms": 9546.3544796609, "postprocess_ms": 304.7001398226712, "preprocess_ms": 0.0, "real_time_factor": 1.0338959054311212, "total_latency_ms": 9546.3544796609}`
- reliability_metrics: `{"failure_rate": 0.0, "success_rate": 1.0}`
- cost_metrics: `{"estimated_cost_usd": 0.002778}`
- cost_totals: `{"estimated_cost_usd": 0.016668}`
- streaming_metrics: `{"finalization_latency_ms": 304.7, "first_partial_latency_ms": 2760.775, "partial_count": 8.833333333333334}`
- estimated_cost_total_usd: `0.016668`

### providers/google_cloud (preset: `accurate`)
- samples: `6`
- successful_samples: `6`
- failed_samples: `0`
- quality_metrics: `{"cer": 0.20100502512562815, "confidence": 0.8446742097536722, "sample_accuracy": 0.0, "wer": 0.2604166666666667}`
- latency_metrics: `{"inference_ms": 8890.791069803527, "per_utterance_latency_ms": 8983.524790984424, "postprocess_ms": 92.73372118089658, "preprocess_ms": 0.0, "real_time_factor": 0.9821008923333001, "total_latency_ms": 8983.524790984424}`
- reliability_metrics: `{"failure_rate": 0.0, "success_rate": 1.0}`
- cost_metrics: `{"estimated_cost_usd": 0.0}`
- cost_totals: `{"estimated_cost_usd": 0.0}`
- streaming_metrics: `{"finalization_latency_ms": 92.73366666666666, "first_partial_latency_ms": 960.5876666666667, "partial_count": 60.833333333333336}`
- estimated_cost_total_usd: `0.0`

## Noise Summary
- clean: `{"cer": 0.1390284757118928, "confidence": 0.8910623243350982, "cpu_percent": 17.366666666666667, "estimated_cost_usd": 0.0021606666666666666, "failure_rate": 0.0, "finalization_latency_ms": 199.52266666666668, "first_partial_latency_ms": 1358.879, "gpu_memory_mb": 897.8333333333334, "gpu_util_percent": 22.0, "inference_ms": 8606.78820030686, "memory_mb": 152.41080729166666, "model_load_ms": 27.75449466666667, "partial_count": 27.5, "per_utterance_latency_ms": 8806.31094465692, "postprocess_ms": 199.5227443500577, "preprocess_ms": 0.0, "provider_call_cold_start": 0.5, "provider_call_warm_start": 0.5, "provider_init_cold_start": 1.0, "provider_init_warm_start": 0.0, "provider_invocation_index": 2.5, "real_time_factor": 0.9661651568808558, "sample_accuracy": 0.0, "success_rate": 1.0, "total_latency_ms": 8806.31094465692, "wer": 0.14583333333333334}`
- extreme: `{"cer": 0.2747068676716918, "confidence": 0.6828985613266499, "cpu_percent": 17.4, "estimated_cost_usd": 0.0021606666666666666, "failure_rate": 0.0, "finalization_latency_ms": 208.993, "first_partial_latency_ms": 1798.891, "gpu_memory_mb": 917.5, "gpu_util_percent": 24.833333333333332, "inference_ms": 9035.902112829112, "memory_mb": 157.68489583333334, "model_load_ms": 27.75449466666667, "partial_count": 28.666666666666668, "per_utterance_latency_ms": 9244.89503565322, "postprocess_ms": 208.99292282410897, "preprocess_ms": 0.0, "provider_call_cold_start": 0.0, "provider_call_warm_start": 1.0, "provider_init_cold_start": 1.0, "provider_init_warm_start": 0.0, "provider_invocation_index": 4.5, "real_time_factor": 0.9946538305267013, "sample_accuracy": 0.0, "success_rate": 1.0, "total_latency_ms": 9244.89503565322, "wer": 0.375}`
- medium: `{"cer": 0.1390284757118928, "confidence": 0.8926711790919241, "cpu_percent": 32.483333333333334, "estimated_cost_usd": 0.0021606666666666666, "failure_rate": 0.0, "finalization_latency_ms": 335.6888333333333, "first_partial_latency_ms": 1638.113, "gpu_memory_mb": 905.0, "gpu_util_percent": 23.666666666666668, "inference_ms": 9050.658912834479, "memory_mb": 156.0859375, "model_load_ms": 27.75449466666667, "partial_count": 26.833333333333332, "per_utterance_latency_ms": 9386.347952327924, "postprocess_ms": 335.6890394934453, "preprocess_ms": 0.0, "provider_call_cold_start": 0.0, "provider_call_warm_start": 1.0, "provider_init_cold_start": 1.0, "provider_init_warm_start": 0.0, "provider_invocation_index": 3.5, "real_time_factor": 1.013052032913746, "sample_accuracy": 0.0, "success_rate": 1.0, "total_latency_ms": 9386.347952327924, "wer": 0.14583333333333334}`
