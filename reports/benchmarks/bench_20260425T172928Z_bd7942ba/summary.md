# Benchmark Summary: bench_20260425T172928Z_bd7942ba

- benchmark_profile: `cloud_comparison`
- dataset_id: `fleurs_en_us_test_subset`
- providers: `providers/aws_cloud, providers/azure_cloud, providers/google_cloud, providers/vosk_local, providers/whisper_local`
- scenario: `noise_robustness`
- execution_mode: `batch`
- noise_modes: `babble, none`
- noise_levels: `clean, heavy, light, medium`
- aggregate_scope: `provider_only`
- total_samples: `40`
- successful_samples: `31`
- failed_samples: `9`
- aggregate_samples: `40`
- corrupted_samples: `0`

## Per-Provider Summary

### providers/aws_cloud (preset: `standard`)
- samples: `8`
- successful_samples: `8`
- failed_samples: `0`
- quality_metrics: `{"cer": 0.12060301507537688, "confidence": 0.9921895833333333, "sample_accuracy": 0.0, "wer": 0.09375}`
- latency_metrics: `{"end_to_end_latency_ms": 10401.903260000154, "end_to_end_rtf": 1.2878255522021458, "inference_ms": 8732.944049750131, "per_utterance_latency_ms": 8733.234776874951, "postprocess_ms": 0.2829987500945208, "preprocess_ms": 0.00772837472595711, "provider_compute_latency_ms": 8733.234776874951, "provider_compute_rtf": 1.0865298822952116, "real_time_factor": 1.0865298822952116, "time_to_final_result_ms": 10401.903260000154, "time_to_first_result_ms": 10401.903260000154, "time_to_result_ms": 10401.903260000154, "total_latency_ms": 8733.234776874951}`
- reliability_metrics: `{"failure_rate": 0.0, "success_rate": 1.0}`
- cost_metrics: `{"estimated_cost_usd": 0.003704}`
- cost_totals: `{"estimated_cost_usd": 0.029632}`
- estimated_cost_total_usd: `0.029632`

### providers/azure_cloud (preset: `standard`)
- samples: `8`
- successful_samples: `0`
- failed_samples: `8`
- quality_metrics: `{"cer": 1.0, "confidence": 0.0, "sample_accuracy": 0.0, "wer": 1.0}`
- latency_metrics: `{"end_to_end_latency_ms": 157.61988300005214, "end_to_end_rtf": 0.01935142780909501, "inference_ms": 0.0, "per_utterance_latency_ms": 0.0, "postprocess_ms": 0.0, "preprocess_ms": 0.0, "provider_compute_latency_ms": 0.0, "provider_compute_rtf": 0.0, "real_time_factor": 0.0, "time_to_final_result_ms": 157.61988300005214, "time_to_first_result_ms": 157.61988300005214, "time_to_result_ms": 157.61988300005214, "total_latency_ms": 0.0}`
- reliability_metrics: `{"failure_rate": 1.0, "success_rate": 0.0}`
- cost_metrics: `{"estimated_cost_usd": 0.002778}`
- cost_totals: `{"estimated_cost_usd": 0.022224}`
- estimated_cost_total_usd: `0.022224`

### providers/google_cloud (preset: `accurate`)
- samples: `8`
- successful_samples: `8`
- failed_samples: `0`
- quality_metrics: `{"cer": 0.14321608040201006, "confidence": 0.8909328654408455, "sample_accuracy": 0.0, "wer": 0.15625}`
- latency_metrics: `{"end_to_end_latency_ms": 1867.7481248751064, "end_to_end_rtf": 0.21403491646244527, "inference_ms": 1862.8014618750512, "per_utterance_latency_ms": 1866.890052249687, "postprocess_ms": 0.0001464999286326929, "preprocess_ms": 4.088443874707082, "provider_compute_latency_ms": 1866.890052249687, "provider_compute_rtf": 0.21392786114197967, "real_time_factor": 0.21392786114197967, "time_to_final_result_ms": 1867.7481248751064, "time_to_first_result_ms": 1867.7481248751064, "time_to_result_ms": 1867.7481248751064, "total_latency_ms": 1866.890052249687}`
- reliability_metrics: `{"failure_rate": 0.0, "success_rate": 1.0}`
- cost_metrics: `{"estimated_cost_usd": 0.0}`
- cost_totals: `{"estimated_cost_usd": 0.0}`
- estimated_cost_total_usd: `0.0`

### providers/vosk_local (preset: `en_small`)
- samples: `8`
- successful_samples: `7`
- failed_samples: `1`
- quality_metrics: `{"cer": 0.27386934673366836, "confidence": 0.7922408990765056, "sample_accuracy": 0.0, "wer": 0.453125}`
- latency_metrics: `{"end_to_end_latency_ms": 1002.7255150000656, "end_to_end_rtf": 0.11646555138321923, "inference_ms": 957.4252265001633, "per_utterance_latency_ms": 993.2393161257096, "postprocess_ms": 0.09317587546320283, "preprocess_ms": 35.72091375008313, "provider_compute_latency_ms": 993.2393161257096, "provider_compute_rtf": 0.11535051194077288, "real_time_factor": 0.11535051194077288, "time_to_final_result_ms": 1002.7255150000656, "time_to_first_result_ms": 1002.7255150000656, "time_to_result_ms": 1002.7255150000656, "total_latency_ms": 993.2393161257096}`
- reliability_metrics: `{"failure_rate": 0.125, "success_rate": 0.875}`
- cost_metrics: `{"estimated_cost_usd": 0.0}`
- cost_totals: `{"estimated_cost_usd": 0.0}`
- estimated_cost_total_usd: `0.0`

### providers/whisper_local (preset: `accurate`)
- samples: `8`
- successful_samples: `8`
- failed_samples: `0`
- quality_metrics: `{"cer": 0.1306532663316583, "confidence": 0.9123110347366471, "sample_accuracy": 0.0, "wer": 0.125}`
- latency_metrics: `{"end_to_end_latency_ms": 2488.038356874995, "end_to_end_rtf": 0.28458899123530607, "inference_ms": 1963.6090238750512, "per_utterance_latency_ms": 2487.7210762498407, "postprocess_ms": 0.07870874992477184, "preprocess_ms": 524.0333436248648, "provider_compute_latency_ms": 2487.7210762498407, "provider_compute_rtf": 0.28455085508284617, "real_time_factor": 0.28455085508284617, "time_to_final_result_ms": 2488.038356874995, "time_to_first_result_ms": 2488.038356874995, "time_to_result_ms": 2488.038356874995, "total_latency_ms": 2487.7210762498407}`
- reliability_metrics: `{"failure_rate": 0.0, "success_rate": 1.0}`
- cost_metrics: `{"estimated_cost_usd": 0.0}`
- cost_totals: `{"estimated_cost_usd": 0.0}`
- estimated_cost_total_usd: `0.0`

## Noise Summary
- babble:heavy: `{"audio_duration_sec": 9.26, "cer": 0.3849246231155779, "confidence": 0.6309674644123746, "cpu_percent": 7.80569498282034, "cpu_percent_mean": 5.4843162035794215, "cpu_percent_peak": 88.8, "declared_audio_duration_sec": 9.26, "duration_mismatch_sec": 0.0, "end_to_end_latency_ms": 2951.8747307000012, "end_to_end_rtf": 0.3589415162300895, "estimated_cost_usd": 0.0012963999999999999, "failure_rate": 0.3, "gpu_memory_mb": 655.2857142857143, "gpu_memory_mb_mean": 614.2070071296605, "gpu_memory_mb_peak": 672.0, "gpu_util_percent": 0.02, "gpu_util_percent_mean": 0.06983208143494923, "gpu_util_percent_peak": 5.0, "inference_ms": 2610.3931753000325, "measured_audio_duration_sec": 9.26, "memory_mb": 595.1761808133448, "memory_mb_mean": 485.54881022813316, "memory_mb_peak": 1502.11328125, "per_utterance_latency_ms": 2610.556994199851, "postprocess_ms": 0.09224079994964995, "preprocess_ms": 0.07157809986892971, "provider_compute_latency_ms": 2610.556994199851, "provider_compute_rtf": 0.31704682701448256, "real_time_factor": 0.31704682701448256, "sample_accuracy": 0.0, "success_rate": 0.7, "time_to_final_result_ms": 2951.8747307000012, "time_to_first_result_ms": 2951.8747307000012, "time_to_result_ms": 2951.8747307000012, "total_latency_ms": 2610.556994199851, "wer": 0.41875}`
- babble:light: `{"audio_duration_sec": 9.26, "cer": 0.3165829145728643, "confidence": 0.7470552504788109, "cpu_percent": 7.842633468640127, "cpu_percent_mean": 5.522069914270485, "cpu_percent_peak": 88.8, "declared_audio_duration_sec": 9.26, "duration_mismatch_sec": 0.0, "end_to_end_latency_ms": 3050.1030887002344, "end_to_end_rtf": 0.3734300781863263, "estimated_cost_usd": 0.0012963999999999999, "failure_rate": 0.2, "gpu_memory_mb": 657.2236928104575, "gpu_memory_mb_mean": 620.9497128305544, "gpu_memory_mb_peak": 675.0, "gpu_util_percent": 0.23431372549019608, "gpu_util_percent_mean": 0.8155767198210069, "gpu_util_percent_peak": 62.0, "inference_ms": 2689.4598583000516, "measured_audio_duration_sec": 9.26, "memory_mb": 589.1903139812823, "memory_mb_mean": 469.18027584224205, "memory_mb_peak": 1499.70703125, "per_utterance_latency_ms": 2689.60183829995, "postprocess_ms": 0.08999660003610188, "preprocess_ms": 0.05198339986236533, "provider_compute_latency_ms": 2689.60183829995, "provider_compute_rtf": 0.3297722012112283, "real_time_factor": 0.3297722012112283, "sample_accuracy": 0.0, "success_rate": 0.8, "time_to_final_result_ms": 3050.1030887002344, "time_to_first_result_ms": 3050.1030887002344, "time_to_result_ms": 3050.1030887002344, "total_latency_ms": 2689.60183829995, "wer": 0.35}`
- babble:medium: `{"audio_duration_sec": 9.26, "cer": 0.31959798994974875, "confidence": 0.7442259779520991, "cpu_percent": 8.212749130367063, "cpu_percent_mean": 5.382577644421482, "cpu_percent_peak": 88.7, "declared_audio_duration_sec": 9.26, "duration_mismatch_sec": 0.0, "end_to_end_latency_ms": 3068.6669055001403, "end_to_end_rtf": 0.3794961984436263, "estimated_cost_usd": 0.0012963999999999999, "failure_rate": 0.2, "gpu_memory_mb": 655.3114285714286, "gpu_memory_mb_mean": 616.3649624893476, "gpu_memory_mb_peak": 673.0, "gpu_util_percent": 0.011428571428571429, "gpu_util_percent_mean": 0.03841396572848004, "gpu_util_percent_peak": 3.0, "inference_ms": 2718.4408077001535, "measured_audio_duration_sec": 9.26, "memory_mb": 591.1006559431543, "memory_mb_mean": 473.96687156887185, "memory_mb_peak": 1501.078125, "per_utterance_latency_ms": 2718.5858484001074, "postprocess_ms": 0.09589460014467477, "preprocess_ms": 0.049146099809149746, "provider_compute_latency_ms": 2718.5858484001074, "provider_compute_rtf": 0.3361662736808064, "real_time_factor": 0.3361662736808064, "sample_accuracy": 0.0, "success_rate": 0.8, "time_to_final_result_ms": 3068.6669055001403, "time_to_first_result_ms": 3068.6669055001403, "time_to_result_ms": 3068.6669055001403, "total_latency_ms": 2718.5858484001074, "wer": 0.35}`
- clean: `{"audio_duration_sec": 9.26, "cer": 0.3135678391959799, "confidence": 0.7478908132265807, "cpu_percent": 7.2711637246248895, "cpu_percent_mean": 6.572780305539347, "cpu_percent_peak": 88.8, "declared_audio_duration_sec": 9.26, "duration_mismatch_sec": 0.0, "end_to_end_latency_ms": 3663.7833868999223, "end_to_end_rtf": 0.42594535841372705, "estimated_cost_usd": 0.0012963999999999999, "failure_rate": 0.2, "gpu_memory_mb": 646.6592792792793, "gpu_memory_mb_mean": 598.0609247362781, "gpu_memory_mb_peak": 675.0, "gpu_util_percent": 0.47096525096525094, "gpu_util_percent_mean": 1.3904409619771132, "gpu_util_percent_peak": 20.0, "inference_ms": 2795.12996830008, "measured_audio_duration_sec": 9.26, "memory_mb": 552.6240218336786, "memory_mb_mean": 521.196408539782, "memory_mb_peak": 1602.75390625, "per_utterance_latency_ms": 3246.1234963002426, "postprocess_ms": 0.08589190019847592, "preprocess_ms": 450.9076360999643, "provider_compute_latency_ms": 3246.1234963002426, "provider_compute_rtf": 0.377301986462131, "real_time_factor": 0.377301986462131, "sample_accuracy": 0.0, "success_rate": 0.8, "time_to_final_result_ms": 3663.7833868999223, "time_to_first_result_ms": 3663.7833868999223, "time_to_result_ms": 3663.7833868999223, "total_latency_ms": 3246.1234963002426, "wer": 0.34375}`
