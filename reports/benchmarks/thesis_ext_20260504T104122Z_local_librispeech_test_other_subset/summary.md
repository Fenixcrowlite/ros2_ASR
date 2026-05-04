# Benchmark Summary: thesis_ext_20260504T104122Z_local_librispeech_test_other_subset

- benchmark_profile: `benchmark/thesis_extended_local_matrix`
- dataset_id: `librispeech_test_other_subset`
- providers: `providers/whisper_local, providers/vosk_local, providers/huggingface_local`
- scenario: `clean`
- execution_mode: `batch`
- noise_modes: `none, white`
- noise_levels: `clean, custom_0db, custom_10db, custom_20db, custom_5db`
- aggregate_scope: `provider_only`
- total_samples: `150`
- successful_samples: `150`
- failed_samples: `0`
- aggregate_samples: `150`
- corrupted_samples: `0`

## Per-Provider Summary

### providers/huggingface_local (preset: `balanced`)
- samples: `50`
- successful_samples: `50`
- failed_samples: `0`
- quality_metrics: `{"cer": 0.09576642335766423, "confidence": 0.0, "sample_accuracy": 0.22, "wer": 0.18461538461538463}`
- latency_metrics: `{"end_to_end_latency_ms": 1371.6253828196204, "end_to_end_rtf": 0.35703155402233966, "inference_ms": 1370.9085509605939, "per_utterance_latency_ms": 1371.3932537801156, "postprocess_ms": 0.12138085949118249, "preprocess_ms": 0.36332196003058925, "provider_compute_latency_ms": 1371.3932537801156, "provider_compute_rtf": 0.35697153124139686, "real_time_factor": 0.35697153124139686, "time_to_final_result_ms": 1371.6253828196204, "time_to_first_result_ms": 1371.6253828196204, "time_to_result_ms": 1371.6253828196204, "total_latency_ms": 1371.3932537801156}`
- reliability_metrics: `{"failure_rate": 0.0, "success_rate": 1.0}`
- cost_metrics: `{"estimated_cost_usd": 0.0}`
- cost_totals: `{"estimated_cost_usd": 0.0}`
- estimated_cost_total_usd: `0.0`

### providers/vosk_local (preset: `en_small`)
- samples: `50`
- successful_samples: `50`
- failed_samples: `0`
- quality_metrics: `{"cer": 0.3097810218978102, "confidence": 0.8440957870019824, "sample_accuracy": 0.04, "wer": 0.46982248520710057}`
- latency_metrics: `{"end_to_end_latency_ms": 1002.6295223401394, "end_to_end_rtf": 0.22060804304017279, "inference_ms": 981.2790084401786, "per_utterance_latency_ms": 990.549158060312, "postprocess_ms": 0.08357312020962127, "preprocess_ms": 9.18657649992383, "provider_compute_latency_ms": 990.549158060312, "provider_compute_rtf": 0.218014917488043, "real_time_factor": 0.218014917488043, "time_to_final_result_ms": 1002.6295223401394, "time_to_first_result_ms": 1002.6295223401394, "time_to_result_ms": 1002.6295223401394, "total_latency_ms": 990.549158060312}`
- reliability_metrics: `{"failure_rate": 0.0, "success_rate": 1.0}`
- cost_metrics: `{"estimated_cost_usd": 0.0}`
- cost_totals: `{"estimated_cost_usd": 0.0}`
- estimated_cost_total_usd: `0.0`

### providers/whisper_local (preset: `light`)
- samples: `50`
- successful_samples: `50`
- failed_samples: `0`
- quality_metrics: `{"cer": 0.2181021897810219, "confidence": 0.7486046574839438, "sample_accuracy": 0.14, "wer": 0.3656804733727811}`
- latency_metrics: `{"end_to_end_latency_ms": 603.156526539824, "end_to_end_rtf": 0.1744295523613813, "inference_ms": 494.59783931990387, "per_utterance_latency_ms": 602.8534409598797, "postprocess_ms": 0.08984846048406325, "preprocess_ms": 108.16575317949173, "provider_compute_latency_ms": 602.8534409598797, "provider_compute_rtf": 0.17435033989070553, "real_time_factor": 0.17435033989070553, "time_to_final_result_ms": 603.156526539824, "time_to_first_result_ms": 603.156526539824, "time_to_result_ms": 603.156526539824, "total_latency_ms": 602.8534409598797}`
- reliability_metrics: `{"failure_rate": 0.0, "success_rate": 1.0}`
- cost_metrics: `{"estimated_cost_usd": 0.0}`
- cost_totals: `{"estimated_cost_usd": 0.0}`
- estimated_cost_total_usd: `0.0`

## Noise Summary
- clean: `{"audio_duration_sec": 5.0615, "cer": 0.06277372262773723, "confidence": 0.5861424803390659, "cpu_percent": 16.050533004820238, "cpu_percent_mean": 12.0211886577962, "cpu_percent_peak": 100.0, "declared_audio_duration_sec": 5.0615, "duration_mismatch_sec": 0.0, "end_to_end_latency_ms": 1212.8464058002767, "end_to_end_rtf": 0.3774775187290596, "estimated_cost_usd": 0.0, "failure_rate": 0.0, "gpu_memory_mb": 1743.4293121693122, "gpu_memory_mb_mean": 1936.769215327342, "gpu_memory_mb_peak": 5021.0, "gpu_util_percent": 11.217526455026455, "gpu_util_percent_mean": 14.645006297520801, "gpu_util_percent_peak": 74.0, "inference_ms": 1013.9439871335829, "measured_audio_duration_sec": 5.0615, "memory_mb": 1381.5815303736692, "memory_mb_mean": 1445.9170737888985, "memory_mb_peak": 3298.0078125, "per_utterance_latency_ms": 1209.9520604332308, "postprocess_ms": 0.11067136680746141, "preprocess_ms": 195.89740193284038, "provider_compute_latency_ms": 1209.9520604332308, "provider_compute_rtf": 0.37683679724853086, "real_time_factor": 0.37683679724853086, "sample_accuracy": 0.3, "success_rate": 1.0, "time_to_final_result_ms": 1212.8464058002767, "time_to_first_result_ms": 1212.8464058002767, "time_to_result_ms": 1212.8464058002767, "total_latency_ms": 1209.9520604332308, "wer": 0.1301775147928994}`
- white:custom_0db: `{"audio_duration_sec": 5.0615, "cer": 0.4583941605839416, "confidence": 0.4345613227837787, "cpu_percent": 16.751680624930625, "cpu_percent_mean": 13.33202496902694, "cpu_percent_peak": 89.3, "declared_audio_duration_sec": 5.0615, "duration_mismatch_sec": 0.0, "end_to_end_latency_ms": 1028.3544947000337, "end_to_end_rtf": 0.23544621824899808, "estimated_cost_usd": 0.0, "failure_rate": 0.0, "gpu_memory_mb": 1843.6144444444444, "gpu_memory_mb_mean": 2148.884260744918, "gpu_memory_mb_peak": 5021.0, "gpu_util_percent": 11.121666666666666, "gpu_util_percent_mean": 15.13484884066175, "gpu_util_percent_peak": 75.0, "inference_ms": 1022.8283090002757, "measured_audio_duration_sec": 5.0615, "memory_mb": 1436.4541896605276, "memory_mb_mean": 1570.8246951642827, "memory_mb_peak": 3297.98828125, "per_utterance_latency_ms": 1023.0032007340924, "postprocess_ms": 0.09882520098472014, "preprocess_ms": 0.07606653283194949, "provider_compute_latency_ms": 1023.0032007340924, "provider_compute_rtf": 0.23428308038412393, "real_time_factor": 0.23428308038412393, "sample_accuracy": 0.0, "success_rate": 1.0, "time_to_final_result_ms": 1028.3544947000337, "time_to_first_result_ms": 1028.3544947000337, "time_to_result_ms": 1028.3544947000337, "total_latency_ms": 1023.0032007340924, "wer": 0.6489151873767258}`
- white:custom_10db: `{"audio_duration_sec": 5.0615, "cer": 0.16155717761557178, "confidence": 0.5406962504652241, "cpu_percent": 16.125540172790174, "cpu_percent_mean": 12.761103653232864, "cpu_percent_peak": 88.8, "declared_audio_duration_sec": 5.0615, "duration_mismatch_sec": 0.0, "end_to_end_latency_ms": 903.2009712662935, "end_to_end_rtf": 0.21241756468378273, "estimated_cost_usd": 0.0, "failure_rate": 0.0, "gpu_memory_mb": 1834.845873015873, "gpu_memory_mb_mean": 2295.891856039968, "gpu_memory_mb_peak": 5021.0, "gpu_util_percent": 10.98857142857143, "gpu_util_percent_mean": 15.604089484843534, "gpu_util_percent_peak": 75.0, "inference_ms": 898.922229000406, "measured_audio_duration_sec": 5.0615, "memory_mb": 1430.4841625713696, "memory_mb_mean": 1633.5514304598878, "memory_mb_peak": 3320.2578125, "per_utterance_latency_ms": 899.0815212998617, "postprocess_ms": 0.09049429985073705, "preprocess_ms": 0.06879799960491557, "provider_compute_latency_ms": 899.0815212998617, "provider_compute_rtf": 0.21151096008166878, "real_time_factor": 0.21151096008166878, "sample_accuracy": 0.13333333333333333, "success_rate": 1.0, "time_to_final_result_ms": 903.2009712662935, "time_to_first_result_ms": 903.2009712662935, "time_to_result_ms": 903.2009712662935, "total_latency_ms": 899.0815212998617, "wer": 0.2938856015779093}`
- white:custom_20db: `{"audio_duration_sec": 5.0615, "cer": 0.09440389294403893, "confidence": 0.5760947123927609, "cpu_percent": 17.028016509634156, "cpu_percent_mean": 13.749892941303663, "cpu_percent_peak": 88.7, "declared_audio_duration_sec": 5.0615, "duration_mismatch_sec": 0.0, "end_to_end_latency_ms": 851.1596836329167, "end_to_end_rtf": 0.20274444155647478, "estimated_cost_usd": 0.0, "failure_rate": 0.0, "gpu_memory_mb": 1835.411111111111, "gpu_memory_mb_mean": 2402.8154984189086, "gpu_memory_mb_peak": 5021.0, "gpu_util_percent": 12.710476190476191, "gpu_util_percent_mean": 18.321430199380348, "gpu_util_percent_peak": 75.0, "inference_ms": 847.6037555000706, "measured_audio_duration_sec": 5.0615, "memory_mb": 1427.5538058151765, "memory_mb_mean": 1673.7429324954537, "memory_mb_peak": 3298.0078125, "per_utterance_latency_ms": 847.7867396344664, "postprocess_ms": 0.10187590014538728, "preprocess_ms": 0.08110823425037476, "provider_compute_latency_ms": 847.7867396344664, "provider_compute_rtf": 0.2020246997226622, "real_time_factor": 0.2020246997226622, "sample_accuracy": 0.2, "success_rate": 1.0, "time_to_final_result_ms": 851.1596836329167, "time_to_first_result_ms": 851.1596836329167, "time_to_result_ms": 851.1596836329167, "total_latency_ms": 847.7867396344664, "wer": 0.1913214990138067}`
- white:custom_5db: `{"audio_duration_sec": 5.0615, "cer": 0.262287104622871, "confidence": 0.5170059748290473, "cpu_percent": 16.287262506012507, "cpu_percent_mean": 12.913964449064899, "cpu_percent_peak": 89.4, "declared_audio_duration_sec": 5.0615, "duration_mismatch_sec": 0.0, "end_to_end_latency_ms": 966.7908307664524, "end_to_end_rtf": 0.2253628391548411, "estimated_cost_usd": 0.0, "failure_rate": 0.0, "gpu_memory_mb": 1836.9477777777777, "gpu_memory_mb_mean": 2196.9683155197695, "gpu_memory_mb_peak": 5021.0, "gpu_util_percent": 11.783650793650793, "gpu_util_percent_mean": 16.02164341447021, "gpu_util_percent_peak": 74.0, "inference_ms": 961.3440505667919, "measured_audio_duration_sec": 5.0615, "memory_mb": 1432.468344536323, "memory_mb_mean": 1593.6843247219613, "memory_mb_peak": 3323.3515625, "per_utterance_latency_ms": 961.5028992321944, "postprocess_ms": 0.0894706325198058, "preprocess_ms": 0.06937803288262027, "provider_compute_latency_ms": 961.5028992321944, "provider_compute_rtf": 0.22423911026325652, "real_time_factor": 0.22423911026325652, "sample_accuracy": 0.03333333333333333, "success_rate": 1.0, "time_to_final_result_ms": 966.7908307664524, "time_to_first_result_ms": 966.7908307664524, "time_to_result_ms": 966.7908307664524, "total_latency_ms": 961.5028992321944, "wer": 0.4358974358974359}`
