# Benchmark Summary: bench_20260401T161116Z_2a496179

- benchmark_profile: `default_benchmark`
- dataset_id: `fleurs_en_us_test_subset`
- providers: `providers/aws_cloud, providers/azure_cloud, providers/google_cloud, providers/whisper_local`
- scenario: `noise_robustness`
- execution_mode: `batch`
- aggregate_scope: `provider_only`
- total_samples: `8`
- successful_samples: `8`
- failed_samples: `0`
- aggregate_samples: `8`
- corrupted_samples: `0`

## Per-Provider Summary

### providers/aws_cloud (preset: `standard`)
- samples: `2`
- successful_samples: `2`
- failed_samples: `0`
- quality_metrics: `{"cer": 0.12060301507537688, "confidence": 0.99295625, "sample_accuracy": 0.0, "wer": 0.09375}`
- latency_metrics: `{"inference_ms": 8844.141536497773, "per_utterance_latency_ms": 8844.433011505316, "postprocess_ms": 0.28409150399966165, "preprocess_ms": 0.007383503543678671, "real_time_factor": 1.106955029608989, "total_latency_ms": 8844.433011505316}`
- reliability_metrics: `{"failure_rate": 0.0, "success_rate": 1.0}`
- cost_metrics: `{"estimated_cost_usd": 0.003704}`
- cost_totals: `{"estimated_cost_usd": 0.007408}`
- estimated_cost_total_usd: `0.007408`

### providers/azure_cloud (preset: `standard`)
- samples: `2`
- successful_samples: `2`
- failed_samples: `0`
- quality_metrics: `{"cer": 0.1306532663316583, "confidence": 0.7734235, "sample_accuracy": 0.0, "wer": 0.125}`
- latency_metrics: `{"inference_ms": 2187.0693340024445, "per_utterance_latency_ms": 2229.258277504414, "postprocess_ms": 0.0988194988167379, "preprocess_ms": 42.090124003152596, "real_time_factor": 0.22783401322245728, "total_latency_ms": 2229.258277504414}`
- reliability_metrics: `{"failure_rate": 0.0, "success_rate": 1.0}`
- cost_metrics: `{"estimated_cost_usd": 0.002778}`
- cost_totals: `{"estimated_cost_usd": 0.005556}`
- estimated_cost_total_usd: `0.005556`

### providers/google_cloud (preset: `accurate`)
- samples: `2`
- successful_samples: `2`
- failed_samples: `0`
- quality_metrics: `{"cer": 0.1407035175879397, "confidence": 0.9141215682029724, "sample_accuracy": 0.0, "wer": 0.15625}`
- latency_metrics: `{"inference_ms": 1955.396187498991, "per_utterance_latency_ms": 2802.519722998113, "postprocess_ms": 0.00018550053937360644, "preprocess_ms": 847.1233499985829, "real_time_factor": 0.2869152375214054, "total_latency_ms": 2802.519722998113}`
- reliability_metrics: `{"failure_rate": 0.0, "success_rate": 1.0}`
- cost_metrics: `{"estimated_cost_usd": 0.0}`
- cost_totals: `{"estimated_cost_usd": 0.0}`
- estimated_cost_total_usd: `0.0`

### providers/whisper_local (preset: `accurate`)
- samples: `2`
- successful_samples: `2`
- failed_samples: `0`
- quality_metrics: `{"cer": 0.1306532663316583, "confidence": 0.9314740753585882, "sample_accuracy": 0.0, "wer": 0.125}`
- latency_metrics: `{"inference_ms": 2206.716893000703, "per_utterance_latency_ms": 2819.5278460043482, "postprocess_ms": 0.07911800275905989, "preprocess_ms": 612.7318350008863, "real_time_factor": 0.3204430474831035, "total_latency_ms": 2819.5278460043482}`
- reliability_metrics: `{"failure_rate": 0.0, "success_rate": 1.0}`
- cost_metrics: `{"estimated_cost_usd": 0.0}`
- cost_totals: `{"estimated_cost_usd": 0.0}`
- estimated_cost_total_usd: `0.0`

## Noise Summary
- clean: `{"cer": 0.1306532663316583, "confidence": 0.9029938483903901, "cpu_percent": 13.625, "estimated_cost_usd": 0.0016205, "failure_rate": 0.0, "gpu_memory_mb": 541.125, "gpu_util_percent": 4.625, "inference_ms": 3798.330987749978, "memory_mb": 279.2841796875, "model_load_ms": 22.799921, "per_utterance_latency_ms": 4173.934714503048, "postprocess_ms": 0.11555362652870826, "preprocess_ms": 375.48817312654137, "provider_call_cold_start": 0.5, "provider_call_warm_start": 0.5, "provider_init_cold_start": 1.0, "provider_init_warm_start": 0.0, "provider_invocation_index": 1.5, "real_time_factor": 0.4855368319589888, "sample_accuracy": 0.0, "success_rate": 1.0, "total_latency_ms": 4173.934714503048, "wer": 0.125}`
