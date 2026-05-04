# ASR Benchmark Report

Run ID: bench_20260413T130728Z_83fc1eca
Benchmark Profile: benchmark/default_benchmark
Dataset ID: sample_dataset
Execution Mode: batch
Aggregate Scope: single_provider
Providers: providers/whisper_local
Total Samples: 1
Successful Samples: 1
Failed Samples: 0

## Provider Metrics

| Provider | WER | CER | Exact Match Rate | Mean Latency (ms) | Mean RTF | Success Rate | Estimated Total Cost (USD) |
|---|---:|---:|---:|---:|---:|---:|---:|
| providers/whisper_local (preset=light) | 0.000 | 0.000 | 1.000 | 8275.6 | 0.996 | 1.000 | 0.0000 |

## Noise Summary

- clean: wer=0.000, cer=0.000, latency_ms=8275.6, rtf=0.996

## Artifacts

- ![](results/plots/wer_cer_by_backend.png)
- ![](results/plots/latency_by_backend.png)
- ![](results/plots/rtf_by_backend.png)
