# Benchmark Summary: bench_20260425T165230Z_b2639a70

- benchmark_profile: `default_benchmark`
- dataset_id: `sample_dataset`
- providers: `providers/aws_cloud, providers/azure_cloud, providers/google_cloud, providers/vosk_local`
- scenario: `noise_robustness`
- execution_mode: `streaming`
- noise_modes: `none`
- noise_levels: `clean`
- aggregate_scope: `provider_only`
- total_samples: `4`
- successful_samples: `3`
- failed_samples: `1`
- aggregate_samples: `4`
- corrupted_samples: `0`

## Per-Provider Summary

### providers/aws_cloud (preset: `standard`)
- samples: `1`
- successful_samples: `1`
- failed_samples: `0`
- quality_metrics: `{"cer": 0.0, "confidence": 0.4469, "sample_accuracy": 1.0, "wer": 0.0}`
- latency_metrics: `{"end_to_end_latency_ms": 8611.349726999833, "end_to_end_rtf": 1.0365129666586221, "inference_ms": 7323.465308999857, "per_utterance_latency_ms": 7626.545517000068, "postprocess_ms": 303.0802080002104, "preprocess_ms": 0.0, "provider_compute_latency_ms": 7626.545517000068, "provider_compute_rtf": 0.9179761094126225, "real_time_factor": 0.9179761094126225, "time_to_final_result_ms": 8611.349726999833, "time_to_first_result_ms": 2009.3402349998541, "time_to_result_ms": 8611.349726999833, "total_latency_ms": 7626.545517000068}`
- reliability_metrics: `{"failure_rate": 0.0, "success_rate": 1.0}`
- cost_metrics: `{"estimated_cost_usd": 0.0033231999999999997}`
- cost_totals: `{"estimated_cost_usd": 0.0033231999999999997}`
- streaming_metrics: `{"finalization_latency_ms": 303.34593699990364, "first_partial_latency_ms": 771.794, "partial_count": 8.0}`
- estimated_cost_total_usd: `0.0033231999999999997`

### providers/azure_cloud (preset: `standard`)
- samples: `1`
- successful_samples: `0`
- failed_samples: `1`
- quality_metrics: `{"cer": 1.0, "confidence": 0.0, "sample_accuracy": 0.0, "wer": 1.0}`
- latency_metrics: `{"end_to_end_latency_ms": 8308.445148999908, "end_to_end_rtf": 1.0000535807655162, "inference_ms": 8215.103471000475, "per_utterance_latency_ms": 8215.355404000093, "postprocess_ms": 0.25193299961756566, "preprocess_ms": 0.0, "provider_compute_latency_ms": 8215.355404000093, "provider_compute_rtf": 0.9888487486759862, "real_time_factor": 0.9888487486759862, "time_to_final_result_ms": 8308.445148999908, "time_to_first_result_ms": 8308.445148999908, "time_to_result_ms": 8308.445148999908, "total_latency_ms": 8215.355404000093}`
- reliability_metrics: `{"failure_rate": 1.0, "success_rate": 0.0}`
- cost_metrics: `{"estimated_cost_usd": 0.0024923999999999997}`
- cost_totals: `{"estimated_cost_usd": 0.0024923999999999997}`
- streaming_metrics: `{"finalization_latency_ms": 0.5073419997643214, "first_partial_latency_ms": 8308.445148999908, "partial_count": 0.0}`
- estimated_cost_total_usd: `0.0024923999999999997`

### providers/google_cloud (preset: `balanced`)
- samples: `1`
- successful_samples: `1`
- failed_samples: `0`
- quality_metrics: `{"cer": 0.13333333333333333, "confidence": 0.25548477719227475, "sample_accuracy": 0.0, "wer": 0.3333333333333333}`
- latency_metrics: `{"end_to_end_latency_ms": 8422.315379000338, "end_to_end_rtf": 1.0137596748917115, "inference_ms": 7030.028907999622, "per_utterance_latency_ms": 7144.0459549999105, "postprocess_ms": 114.01704700028858, "preprocess_ms": 0.0, "provider_compute_latency_ms": 7144.0459549999105, "provider_compute_rtf": 0.8598996094126036, "real_time_factor": 0.8598996094126036, "time_to_final_result_ms": 8422.315379000338, "time_to_first_result_ms": 2000.311363000037, "time_to_result_ms": 8422.315379000338, "total_latency_ms": 7144.0459549999105}`
- reliability_metrics: `{"failure_rate": 0.0, "success_rate": 1.0}`
- cost_metrics: `{"estimated_cost_usd": 0.0}`
- cost_totals: `{"estimated_cost_usd": 0.0}`
- streaming_metrics: `{"finalization_latency_ms": 144.930191000185, "first_partial_latency_ms": 282.182, "partial_count": 10.0}`
- estimated_cost_total_usd: `0.0`

### providers/vosk_local (preset: `en_small`)
- samples: `1`
- successful_samples: `1`
- failed_samples: `0`
- quality_metrics: `{"cer": 3.4, "confidence": 0.906944, "sample_accuracy": 0.0, "wer": 5.0}`
- latency_metrics: `{"end_to_end_latency_ms": 8349.956591000137, "end_to_end_rtf": 1.005050143355818, "inference_ms": 7782.047435000095, "per_utterance_latency_ms": 7813.234413999908, "postprocess_ms": 31.18697899981271, "preprocess_ms": 0.0, "provider_compute_latency_ms": 7813.234413999908, "provider_compute_rtf": 0.9404470888300323, "real_time_factor": 0.9404470888300323, "time_to_final_result_ms": 8349.956591000137, "time_to_first_result_ms": 1054.6152010001606, "time_to_result_ms": 8349.956591000137, "total_latency_ms": 7813.234413999908}`
- reliability_metrics: `{"failure_rate": 0.0, "success_rate": 1.0}`
- cost_metrics: `{"estimated_cost_usd": 0.0}`
- cost_totals: `{"estimated_cost_usd": 0.0}`
- streaming_metrics: `{"finalization_latency_ms": 42.00115999992704, "first_partial_latency_ms": 528.5666509998919, "partial_count": 11.0}`
- estimated_cost_total_usd: `0.0`

## Noise Summary
- clean: `{"audio_duration_sec": 8.308, "cer": 1.1333333333333333, "confidence": 0.40233219429806866, "cpu_percent": 5.752779815764916, "cpu_percent_mean": 5.774294941276024, "cpu_percent_peak": 43.7, "declared_audio_duration_sec": 8.308, "duration_mismatch_sec": 0.0, "end_to_end_latency_ms": 8423.016711500055, "end_to_end_rtf": 1.013844091417917, "estimated_cost_usd": 0.0014538999999999997, "failure_rate": 0.25, "finalization_latency_ms": 122.696157499945, "first_partial_latency_ms": 2472.74694999995, "gpu_memory_mb": 517.2657019704434, "gpu_memory_mb_mean": 517.1481349894041, "gpu_memory_mb_peak": 565.0, "gpu_util_percent": 6.137007389162562, "gpu_util_percent_mean": 6.132785347646664, "gpu_util_percent_peak": 26.0, "inference_ms": 7587.661280750012, "measured_audio_duration_sec": 8.308, "memory_mb": 175.9303880758861, "memory_mb_mean": 175.46692299044247, "memory_mb_peak": 320.54296875, "partial_count": 7.25, "per_utterance_latency_ms": 7699.795322499995, "postprocess_ms": 112.13404174998232, "preprocess_ms": 0.0, "provider_compute_latency_ms": 7699.795322499995, "provider_compute_rtf": 0.9267928890828111, "real_time_factor": 0.9267928890828111, "sample_accuracy": 0.25, "success_rate": 0.75, "time_to_final_result_ms": 8423.016711500055, "time_to_first_result_ms": 3343.17798699999, "time_to_result_ms": 8423.016711500055, "total_latency_ms": 7699.795322499995, "wer": 1.5833333333333333}`
