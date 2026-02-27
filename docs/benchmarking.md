# Benchmarking Methodology

## Metrics

- WER, CER (against transcript).
- End-to-end latency (ms) and breakdown (preprocess/inference/postprocess).
- RTF = processing_time / audio_duration.
- CPU/RAM via `psutil`.
- GPU via `nvidia-smi` when available.
- Error rate (% failed requests).
- Cloud cost estimate from configurable `price_per_minute`.

## Scenarios

- Clean audio.
- Noise injection with SNR 20/10/0 dB.
- Varying phrase length.
- Languages: English + Slavic sample set.
- Streaming simulation with 0.5-1.0 sec chunks.

## Output Artifacts

- `results/benchmark_results.csv`
- `results/benchmark_results.json`
- `results/plots/*.png`

`make bench` uses `asr_benchmark.runner` as the single source of truth:
the runner writes raw results and generates plots once.

Raw result schema includes:
- `audio_id`, `duration_sec`, `backend`, `language`, `scenario`, `snr_db`
- `text`, `transcript_ref`, `wer`, `cer`
- `latency_ms`, `preprocess_ms`, `inference_ms`, `postprocess_ms`, `rtf`
- `cpu_percent`, `ram_mb`, `gpu_util_percent`, `gpu_mem_mb`
- `error_code`, `error_message`, `success`, `cost_estimate`
