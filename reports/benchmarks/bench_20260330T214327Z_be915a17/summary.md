# Benchmark Summary: bench_20260330T214327Z_be915a17

- benchmark_profile: `cloud_comparison`
- dataset_id: `fleurs_en_us_test_subset`
- providers: `providers/aws_cloud, providers/azure_cloud, providers/google_cloud`
- scenario: `noise_robustness`
- execution_mode: `streaming`
- aggregate_scope: `provider_only`
- total_samples: `18`
- successful_samples: `18`
- failed_samples: `0`

## Per-Provider Summary

### providers/aws_cloud (preset: `standard`)
- samples: `6`
- successful_samples: `6`
- failed_samples: `0`
- quality_metrics: `{"cer": 0.17922948073701842, "confidence": 0.9412858333333334, "sample_accuracy": 0.0, "wer": 0.20833333333333334}`
- latency_metrics: `{"inference_ms": 8510.468003999753, "per_utterance_latency_ms": 8830.925176497354, "postprocess_ms": 320.45717249760247, "preprocess_ms": 0.0, "real_time_factor": 0.9508182389375763, "total_latency_ms": 8830.925176497354}`
- reliability_metrics: `{"failure_rate": 0.0, "success_rate": 1.0}`
- cost_metrics: `{"estimated_cost_usd": 0.003704}`
- cost_totals: `{"estimated_cost_usd": 0.022224}`
- streaming_metrics: `{"finalization_latency_ms": 320.4571666666667, "first_partial_latency_ms": 1016.0188333333333, "partial_count": 13.333333333333334}`
- estimated_cost_total_usd: `0.022224`

### providers/azure_cloud (preset: `standard`)
- samples: `6`
- successful_samples: `6`
- failed_samples: `0`
- quality_metrics: `{"cer": 0.17252931323283083, "confidence": 0.6806720216666666, "sample_accuracy": 0.0, "wer": 0.19791666666666666}`
- latency_metrics: `{"inference_ms": 9241.921088338131, "per_utterance_latency_ms": 9406.490621501385, "postprocess_ms": 164.56953316325476, "preprocess_ms": 0.0, "real_time_factor": 1.0226012066767372, "total_latency_ms": 9406.490621501385}`
- reliability_metrics: `{"failure_rate": 0.0, "success_rate": 1.0}`
- cost_metrics: `{"estimated_cost_usd": 0.002778}`
- cost_totals: `{"estimated_cost_usd": 0.016668}`
- streaming_metrics: `{"finalization_latency_ms": 164.56933333333333, "first_partial_latency_ms": 2754.111, "partial_count": 8.666666666666666}`
- estimated_cost_total_usd: `0.016668`

### providers/google_cloud (preset: `accurate`)
- samples: `6`
- successful_samples: `6`
- failed_samples: `0`
- quality_metrics: `{"cer": 0.20100502512562815, "confidence": 0.8446741898854574, "sample_accuracy": 0.0, "wer": 0.2604166666666667}`
- latency_metrics: `{"inference_ms": 8936.347726174668, "per_utterance_latency_ms": 9036.480169170924, "postprocess_ms": 100.13244299625512, "preprocess_ms": 0.0, "real_time_factor": 0.9873963794090129, "total_latency_ms": 9036.480169170924}`
- reliability_metrics: `{"failure_rate": 0.0, "success_rate": 1.0}`
- cost_metrics: `{"estimated_cost_usd": 0.0}`
- cost_totals: `{"estimated_cost_usd": 0.0}`
- streaming_metrics: `{"finalization_latency_ms": 100.1325, "first_partial_latency_ms": 970.9955, "partial_count": 60.833333333333336}`
- estimated_cost_total_usd: `0.0`

## Noise Summary
- clean: `{"cer": 0.1390284757118928, "confidence": 0.8910623144009908, "cpu_percent": 16.05, "estimated_cost_usd": 0.0021606666666666666, "failure_rate": 0.0, "finalization_latency_ms": 180.5315, "first_partial_latency_ms": 1316.2371666666666, "gpu_memory_mb": 872.0, "gpu_util_percent": 4.166666666666667, "inference_ms": 8625.486711845346, "memory_mb": 152.33203125, "partial_count": 27.5, "per_utterance_latency_ms": 8806.018185336143, "postprocess_ms": 180.5314734907976, "preprocess_ms": 0.0, "real_time_factor": 0.9647387525764719, "sample_accuracy": 0.0, "success_rate": 1.0, "total_latency_ms": 8806.018185336143, "wer": 0.14583333333333334}`
- extreme: `{"cer": 0.2747068676716918, "confidence": 0.6828985513925425, "cpu_percent": 11.183333333333334, "estimated_cost_usd": 0.0021606666666666666, "failure_rate": 0.0, "finalization_latency_ms": 218.9345, "first_partial_latency_ms": 1792.2956666666666, "gpu_memory_mb": 854.8333333333334, "gpu_util_percent": 1.0, "inference_ms": 9033.805339005388, "memory_mb": 157.25716145833334, "partial_count": 28.666666666666668, "per_utterance_latency_ms": 9252.739880835483, "postprocess_ms": 218.93454183009453, "preprocess_ms": 0.0, "real_time_factor": 0.9984164514493871, "sample_accuracy": 0.0, "success_rate": 1.0, "total_latency_ms": 9252.739880835483, "wer": 0.375}`
- medium: `{"cer": 0.1390284757118928, "confidence": 0.8926711790919241, "cpu_percent": 10.25, "estimated_cost_usd": 0.0021606666666666666, "failure_rate": 0.0, "finalization_latency_ms": 185.693, "first_partial_latency_ms": 1632.5925, "gpu_memory_mb": 879.6666666666666, "gpu_util_percent": 14.166666666666666, "inference_ms": 9029.44476766182, "memory_mb": 156.09765625, "partial_count": 26.666666666666668, "per_utterance_latency_ms": 9215.13790099804, "postprocess_ms": 185.69313333622026, "preprocess_ms": 0.0, "real_time_factor": 0.9976606209974674, "sample_accuracy": 0.0, "success_rate": 1.0, "total_latency_ms": 9215.13790099804, "wer": 0.14583333333333334}`
