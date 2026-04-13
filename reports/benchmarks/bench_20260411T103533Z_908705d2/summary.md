# Benchmark Summary: bench_20260411T103533Z_908705d2

- benchmark_profile: `default_benchmark`
- dataset_id: `fleurs_en_us_test_subset`
- providers: `providers/aws_cloud, providers/azure_cloud, providers/google_cloud, providers/vosk_local, providers/whisper_local`
- scenario: `noise_robustness`
- execution_mode: `batch`
- aggregate_scope: `provider_only`
- total_samples: `50`
- successful_samples: `48`
- failed_samples: `2`
- aggregate_samples: `50`
- corrupted_samples: `0`

## Per-Provider Summary

### providers/aws_cloud (preset: `standard`)
- samples: `10`
- successful_samples: `10`
- failed_samples: `0`
- quality_metrics: `{"cer": 0.14170854271356784, "confidence": 0.9646560714285715, "sample_accuracy": 0.0, "wer": 0.125}`
- latency_metrics: `{"inference_ms": 8726.945466295001, "per_utterance_latency_ms": 8727.270234192838, "postprocess_ms": 0.31660539971198887, "preprocess_ms": 0.008162498124875128, "real_time_factor": 1.084505027447756, "total_latency_ms": 8727.270234192838}`
- reliability_metrics: `{"failure_rate": 0.0, "success_rate": 1.0}`
- cost_metrics: `{"estimated_cost_usd": 0.003704}`
- cost_totals: `{"estimated_cost_usd": 0.03704}`
- estimated_cost_total_usd: `0.03704`

### providers/azure_cloud (preset: `standard`)
- samples: `10`
- successful_samples: `10`
- failed_samples: `0`
- quality_metrics: `{"cer": 0.15577889447236182, "confidence": 0.72773634, "sample_accuracy": 0.0, "wer": 0.16875}`
- latency_metrics: `{"inference_ms": 2155.813864400261, "per_utterance_latency_ms": 2165.568948999862, "postprocess_ms": 0.10167219734285027, "preprocess_ms": 9.653412402258255, "real_time_factor": 0.22134150593769664, "total_latency_ms": 2165.568948999862}`
- reliability_metrics: `{"failure_rate": 0.0, "success_rate": 1.0}`
- cost_metrics: `{"estimated_cost_usd": 0.002778}`
- cost_totals: `{"estimated_cost_usd": 0.02778}`
- estimated_cost_total_usd: `0.02778`

### providers/google_cloud (preset: `accurate`)
- samples: `10`
- successful_samples: `10`
- failed_samples: `0`
- quality_metrics: `{"cer": 0.1798994974874372, "confidence": 0.8608106672763824, "sample_accuracy": 0.0, "wer": 0.21875}`
- latency_metrics: `{"inference_ms": 1738.1050274096197, "per_utterance_latency_ms": 1970.7091022050008, "postprocess_ms": 0.00015719560906291008, "preprocess_ms": 232.6039175997721, "real_time_factor": 0.21633842892089064, "total_latency_ms": 1970.7091022050008}`
- reliability_metrics: `{"failure_rate": 0.0, "success_rate": 1.0}`
- cost_metrics: `{"estimated_cost_usd": 0.0}`
- cost_totals: `{"estimated_cost_usd": 0.0}`
- estimated_cost_total_usd: `0.0`

### providers/vosk_local (preset: `en_small`)
- samples: `10`
- successful_samples: `8`
- failed_samples: `2`
- quality_metrics: `{"cer": 0.3608040201005025, "confidence": 0.7089891491628959, "sample_accuracy": 0.0, "wer": 0.5375}`
- latency_metrics: `{"inference_ms": 1171.6106414998649, "per_utterance_latency_ms": 1217.6882300991565, "postprocess_ms": 0.09658150083851069, "preprocess_ms": 45.98100709845312, "real_time_factor": 0.13481890953010645, "total_latency_ms": 1217.6882300991565}`
- reliability_metrics: `{"failure_rate": 0.2, "success_rate": 0.8}`
- cost_metrics: `{"estimated_cost_usd": 0.0}`
- cost_totals: `{"estimated_cost_usd": 0.0}`
- estimated_cost_total_usd: `0.0`

### providers/whisper_local (preset: `accurate`)
- samples: `10`
- successful_samples: `10`
- failed_samples: `0`
- quality_metrics: `{"cer": 0.16683417085427135, "confidence": 0.8759858536822741, "sample_accuracy": 0.0, "wer": 0.2}`
- latency_metrics: `{"inference_ms": 2207.1038964000763, "per_utterance_latency_ms": 3020.693126009428, "postprocess_ms": 0.1504510029917583, "preprocess_ms": 813.4387786063598, "real_time_factor": 0.3385076389816005, "total_latency_ms": 3020.693126009428}`
- reliability_metrics: `{"failure_rate": 0.0, "success_rate": 1.0}`
- cost_metrics: `{"estimated_cost_usd": 0.0}`
- cost_totals: `{"estimated_cost_usd": 0.0}`
- estimated_cost_total_usd: `0.0`

## Noise Summary
- clean: `{"cer": 0.1306532663316583, "confidence": 0.8989214147907435, "cpu_percent": 14.98, "estimated_cost_usd": 0.0012963999999999999, "failure_rate": 0.0, "gpu_memory_mb": 727.1, "gpu_util_percent": 1.3, "inference_ms": 3208.54442580021, "memory_mb": 442.078125, "model_load_ms": 33.1443918, "per_utterance_latency_ms": 4310.146070696646, "postprocess_ms": 0.17714609566610307, "preprocess_ms": 1101.4244988007704, "provider_call_cold_start": 0.5, "provider_call_warm_start": 0.5, "provider_init_cold_start": 1.0, "provider_init_warm_start": 0.0, "provider_invocation_index": 3.5, "real_time_factor": 0.46805711833287156, "sample_accuracy": 0.0, "success_rate": 1.0, "total_latency_ms": 4310.146070696646, "wer": 0.15625}`
- extreme: `{"cer": 0.3768844221105528, "confidence": 0.6267098230365733, "cpu_percent": 10.48, "estimated_cost_usd": 0.0012963999999999999, "failure_rate": 0.1, "gpu_memory_mb": 710.4, "gpu_util_percent": 2.2, "inference_ms": 3248.877772598644, "memory_mb": 449.307421875, "model_load_ms": 33.1443918, "per_utterance_latency_ms": 3249.114172201371, "postprocess_ms": 0.15932370151858777, "preprocess_ms": 0.07707590120844543, "provider_call_cold_start": 0.0, "provider_call_warm_start": 1.0, "provider_init_cold_start": 1.0, "provider_init_warm_start": 0.0, "provider_invocation_index": 7.5, "real_time_factor": 0.3852161500226429, "sample_accuracy": 0.0, "success_rate": 0.9, "total_latency_ms": 3249.114172201371, "wer": 0.50625}`
- heavy: `{"cer": 0.21306532663316582, "confidence": 0.7972074724766312, "cpu_percent": 14.35, "estimated_cost_usd": 0.0012963999999999999, "failure_rate": 0.1, "gpu_memory_mb": 709.7, "gpu_util_percent": 3.1, "inference_ms": 3140.1420553942444, "memory_mb": 447.10390625, "model_load_ms": 33.1443918, "per_utterance_latency_ms": 3140.3090134903323, "postprocess_ms": 0.10258699767291546, "preprocess_ms": 0.06437109841499478, "provider_call_cold_start": 0.0, "provider_call_warm_start": 1.0, "provider_init_cold_start": 1.0, "provider_init_warm_start": 0.0, "provider_invocation_index": 6.5, "real_time_factor": 0.37353602132345803, "sample_accuracy": 0.0, "success_rate": 0.9, "total_latency_ms": 3140.3090134903323, "wer": 0.2375}`
- light: `{"cer": 0.14271356783919598, "confidence": 0.9058069847020918, "cpu_percent": 11.38, "estimated_cost_usd": 0.0012963999999999999, "failure_rate": 0.0, "gpu_memory_mb": 722.3, "gpu_util_percent": 8.4, "inference_ms": 3207.0370383007685, "memory_mb": 444.059765625, "model_load_ms": 33.1443918, "per_utterance_latency_ms": 3207.2140900971135, "postprocess_ms": 0.11521849373821169, "preprocess_ms": 0.06183330260682851, "provider_call_cold_start": 0.0, "provider_call_warm_start": 1.0, "provider_init_cold_start": 1.0, "provider_init_warm_start": 0.0, "provider_invocation_index": 4.5, "real_time_factor": 0.38496086994647627, "sample_accuracy": 0.0, "success_rate": 1.0, "total_latency_ms": 3207.2140900971135, "wer": 0.175}`
- medium: `{"cer": 0.14170854271356784, "confidence": 0.9095323865440842, "cpu_percent": 12.79, "estimated_cost_usd": 0.0012963999999999999, "failure_rate": 0.0, "gpu_memory_mb": 716.3, "gpu_util_percent": 6.8, "inference_ms": 3194.9776039109565, "memory_mb": 445.316796875, "model_load_ms": 33.1443918, "per_utterance_latency_ms": 3195.1462950208224, "postprocess_ms": 0.11119200789835304, "preprocess_ms": 0.057499101967550814, "provider_call_cold_start": 0.0, "provider_call_warm_start": 1.0, "provider_init_cold_start": 1.0, "provider_init_warm_start": 0.0, "provider_invocation_index": 5.5, "real_time_factor": 0.3837413511926012, "sample_accuracy": 0.0, "success_rate": 1.0, "total_latency_ms": 3195.1462950208224, "wer": 0.175}`
