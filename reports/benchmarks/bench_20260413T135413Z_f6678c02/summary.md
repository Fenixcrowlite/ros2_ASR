# Benchmark Summary: bench_20260413T135413Z_f6678c02

- benchmark_profile: `cloud_comparison`
- dataset_id: `sample_dataset`
- providers: `providers/aws_cloud, providers/azure_cloud, providers/google_cloud, providers/vosk_local, providers/whisper_local`
- scenario: `clean_baseline`
- execution_mode: `batch`
- noise_modes: `none, pink`
- noise_levels: `clean, extreme, medium`
- aggregate_scope: `provider_only`
- total_samples: `15`
- successful_samples: `15`
- failed_samples: `0`
- aggregate_samples: `15`
- corrupted_samples: `0`

## Per-Provider Summary

### providers/aws_cloud (preset: `standard`)
- samples: `3`
- successful_samples: `3`
- failed_samples: `0`
- quality_metrics: `{"cer": 0.0, "confidence": 0.9833333333333333, "sample_accuracy": 0.6666666666666666, "wer": 0.3333333333333333}`
- latency_metrics: `{"end_to_end_latency_ms": 10468.853122341292, "end_to_end_rtf": 1.260093057575986, "inference_ms": 8733.514608989935, "per_utterance_latency_ms": 8733.818315668032, "postprocess_ms": 0.2938783533560733, "preprocess_ms": 0.009828324740131697, "provider_compute_latency_ms": 8733.818315668032, "provider_compute_rtf": 1.051254010070779, "real_time_factor": 1.051254010070779, "time_to_final_result_ms": 10468.853122341292, "time_to_first_result_ms": 10468.853122341292, "time_to_result_ms": 10468.853122341292, "total_latency_ms": 8733.818315668032}`
- reliability_metrics: `{"failure_rate": 0.0, "success_rate": 1.0}`
- cost_metrics: `{"estimated_cost_usd": 0.0033231999999999997}`
- cost_totals: `{"estimated_cost_usd": 0.009969599999999999}`
- estimated_cost_total_usd: `0.009969599999999999`

### providers/azure_cloud (preset: `standard`)
- samples: `3`
- successful_samples: `3`
- failed_samples: `0`
- quality_metrics: `{"cer": 0.6666666666666666, "confidence": 0.89992849, "sample_accuracy": 0.0, "wer": 0.6666666666666666}`
- latency_metrics: `{"end_to_end_latency_ms": 1137.4607049898866, "end_to_end_rtf": 0.13691149554524393, "inference_ms": 722.4674920241038, "per_utterance_latency_ms": 758.0502933512131, "postprocess_ms": 0.09334500646218657, "preprocess_ms": 35.48945632064715, "provider_compute_latency_ms": 758.0502933512131, "provider_compute_rtf": 0.09124341518430587, "real_time_factor": 0.09124341518430587, "time_to_final_result_ms": 1137.4607049898866, "time_to_first_result_ms": 1137.4607049898866, "time_to_result_ms": 1137.4607049898866, "total_latency_ms": 758.0502933512131}`
- reliability_metrics: `{"failure_rate": 0.0, "success_rate": 1.0}`
- cost_metrics: `{"estimated_cost_usd": 0.0024923999999999997}`
- cost_totals: `{"estimated_cost_usd": 0.007477199999999999}`
- estimated_cost_total_usd: `0.007477199999999999`

### providers/google_cloud (preset: `accurate`)
- samples: `3`
- successful_samples: `3`
- failed_samples: `0`
- quality_metrics: `{"cer": 0.08888888888888889, "confidence": 0.5090528097417619, "sample_accuracy": 0.0, "wer": 0.4444444444444444}`
- latency_metrics: `{"end_to_end_latency_ms": 1934.793759661261, "end_to_end_rtf": 0.232883216136406, "inference_ms": 1547.1908790059388, "per_utterance_latency_ms": 1934.038888992897, "postprocess_ms": 0.0002969948885341485, "preprocess_ms": 386.8477129920696, "provider_compute_latency_ms": 1934.038888992897, "provider_compute_rtf": 0.23279235543968427, "real_time_factor": 0.23279235543968427, "time_to_final_result_ms": 1934.793759661261, "time_to_first_result_ms": 1934.793759661261, "time_to_result_ms": 1934.793759661261, "total_latency_ms": 1934.038888992897}`
- reliability_metrics: `{"failure_rate": 0.0, "success_rate": 1.0}`
- cost_metrics: `{"estimated_cost_usd": 0.0}`
- cost_totals: `{"estimated_cost_usd": 0.0}`
- estimated_cost_total_usd: `0.0`

### providers/vosk_local (preset: `en_small`)
- samples: `3`
- successful_samples: `3`
- failed_samples: `0`
- quality_metrics: `{"cer": 3.2666666666666666, "confidence": 0.9260930055555556, "sample_accuracy": 0.0, "wer": 4.666666666666667}`
- latency_metrics: `{"end_to_end_latency_ms": 1144.960148667451, "end_to_end_rtf": 0.13781417292578851, "inference_ms": 969.1787046613172, "per_utterance_latency_ms": 1132.8824096708558, "postprocess_ms": 0.10954233584925532, "preprocess_ms": 163.59416267368942, "provider_compute_latency_ms": 1132.8824096708558, "provider_compute_rtf": 0.13636042485205296, "real_time_factor": 0.13636042485205296, "time_to_final_result_ms": 1144.960148667451, "time_to_first_result_ms": 1144.960148667451, "time_to_result_ms": 1144.960148667451, "total_latency_ms": 1132.8824096708558}`
- reliability_metrics: `{"failure_rate": 0.0, "success_rate": 1.0}`
- cost_metrics: `{"estimated_cost_usd": 0.0}`
- cost_totals: `{"estimated_cost_usd": 0.0}`
- estimated_cost_total_usd: `0.0`

### providers/whisper_local (preset: `accurate`)
- samples: `3`
- successful_samples: `3`
- failed_samples: `0`
- quality_metrics: `{"cer": 2.3333333333333335, "confidence": 0.7692569270804466, "sample_accuracy": 0.0, "wer": 3.3333333333333335}`
- latency_metrics: `{"end_to_end_latency_ms": 4017.425383324735, "end_to_end_rtf": 0.4835610716568049, "inference_ms": 2294.645033970786, "per_utterance_latency_ms": 4017.0835506675453, "postprocess_ms": 0.3473450196906924, "preprocess_ms": 1722.091171677069, "provider_compute_latency_ms": 4017.0835506675453, "provider_compute_rtf": 0.48351992665714316, "real_time_factor": 0.48351992665714316, "time_to_final_result_ms": 4017.425383324735, "time_to_first_result_ms": 4017.425383324735, "time_to_result_ms": 4017.425383324735, "total_latency_ms": 4017.0835506675453}`
- reliability_metrics: `{"failure_rate": 0.0, "success_rate": 1.0}`
- cost_metrics: `{"estimated_cost_usd": 0.0}`
- cost_totals: `{"estimated_cost_usd": 0.0}`
- estimated_cost_total_usd: `0.0`

## Noise Summary
- clean: `{"audio_duration_sec": 8.308, "cer": 0.8533333333333334, "confidence": 0.8108807105694436, "cpu_percent": 26.394348484848486, "cpu_percent_mean": 27.164733618034514, "cpu_percent_peak": 100.0, "declared_audio_duration_sec": 8.308, "duration_mismatch_sec": 0.0, "end_to_end_latency_ms": 4926.58401960507, "end_to_end_rtf": 0.5929927804050398, "estimated_cost_usd": 0.00116312, "failure_rate": 0.0, "gpu_memory_mb": 1000.5980708180708, "gpu_memory_mb_mean": 1001.9836991611751, "gpu_memory_mb_peak": 1033.0, "gpu_util_percent": 0.6816816816816818, "gpu_util_percent_mean": 1.4737282182854547, "gpu_util_percent_peak": 20.0, "inference_ms": 2910.680079413578, "measured_audio_duration_sec": 8.308, "memory_mb": 359.48932673085017, "memory_mb_mean": 420.8508071709116, "memory_mb_peak": 1576.59765625, "per_utterance_latency_ms": 4295.427902415395, "postprocess_ms": 0.11816560290753841, "preprocess_ms": 1384.6296573989093, "provider_compute_latency_ms": 4295.427902415395, "provider_compute_rtf": 0.5170230985093157, "real_time_factor": 0.5170230985093157, "sample_accuracy": 0.0, "success_rate": 1.0, "time_to_final_result_ms": 4926.58401960507, "time_to_first_result_ms": 4926.58401960507, "time_to_result_ms": 4926.58401960507, "total_latency_ms": 4295.427902415395, "wer": 1.5333333333333334}`
- pink:extreme: `{"audio_duration_sec": 8.308, "cer": 1.4266666666666667, "confidence": 0.8177278569371064, "cpu_percent": 27.473176470588236, "cpu_percent_mean": 26.401474306530325, "cpu_percent_peak": 89.5, "declared_audio_duration_sec": 8.308, "duration_mismatch_sec": 0.0, "end_to_end_latency_ms": 3149.8115143855102, "end_to_end_rtf": 0.3791299367339324, "estimated_cost_usd": 0.00116312, "failure_rate": 0.0, "gpu_memory_mb": 1017.9911764705882, "gpu_memory_mb_mean": 1008.7911891907825, "gpu_memory_mb_peak": 1033.0, "gpu_util_percent": 6.84921568627451, "gpu_util_percent_mean": 3.4207776482938597, "gpu_util_percent_peak": 56.0, "inference_ms": 2820.973080198746, "measured_audio_duration_sec": 8.308, "memory_mb": 468.79204142594534, "memory_mb_mean": 364.6511676038056, "memory_mb_peak": 1642.76171875, "per_utterance_latency_ms": 2821.290682198014, "postprocess_ms": 0.20034200279042125, "preprocess_ms": 0.1172599964775145, "provider_compute_latency_ms": 2821.290682198014, "provider_compute_rtf": 0.3395872270339449, "real_time_factor": 0.3395872270339449, "sample_accuracy": 0.2, "success_rate": 1.0, "time_to_final_result_ms": 3149.8115143855102, "time_to_first_result_ms": 3149.8115143855102, "time_to_result_ms": 3149.8115143855102, "total_latency_ms": 2821.290682198014, "wer": 1.9333333333333333}`
- pink:medium: `{"audio_duration_sec": 8.308, "cer": 1.5333333333333334, "confidence": 0.8239901719201085, "cpu_percent": 28.081693071491614, "cpu_percent_mean": 25.755924974909522, "cpu_percent_peak": 89.4, "declared_audio_duration_sec": 8.308, "duration_mismatch_sec": 0.0, "end_to_end_latency_ms": 3145.7003374001943, "end_to_end_rtf": 0.3786350911651654, "estimated_cost_usd": 0.00116312, "failure_rate": 0.0, "gpu_memory_mb": 999.1280952380953, "gpu_memory_mb_mean": 1002.842234140201, "gpu_memory_mb_peak": 1033.0, "gpu_util_percent": 1.5676190476190477, "gpu_util_percent_mean": 1.9897494127959765, "gpu_util_percent_peak": 34.0, "inference_ms": 2828.5448715789244, "measured_audio_duration_sec": 8.308, "memory_mb": 464.9822879833683, "memory_mb_mean": 339.68878571466524, "memory_mb_peak": 1642.7421875, "per_utterance_latency_ms": 2828.805490396917, "postprocess_ms": 0.1881370204500854, "preprocess_ms": 0.07248179754242301, "provider_compute_latency_ms": 2828.805490396917, "provider_compute_rtf": 0.34049175377911856, "real_time_factor": 0.34049175377911856, "sample_accuracy": 0.2, "success_rate": 1.0, "time_to_final_result_ms": 3145.7003374001943, "time_to_first_result_ms": 3145.7003374001943, "time_to_result_ms": 3145.7003374001943, "total_latency_ms": 2828.805490396917, "wer": 2.2}`
