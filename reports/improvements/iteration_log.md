# Iteration Log

Run family: `thesis_20260330_self_audit_final`

## Iteration 1

Tested:
- `reports/benchmarks/thesis_20260330_self_audit_final_iter01_light/`
- `reports/benchmarks/thesis_20260330_self_audit_final_iter01_balanced/`
- `reports/benchmarks/thesis_20260330_self_audit_final_iter01_accurate/`

Found:
- `balanced` was the best throughput-quality tradeoff on the built-in sample: `WER=0`, `1701.72 ms`, `RTF=0.2048`.
- `light` also achieved `WER=0`, but was slower than `balanced` in this run because preprocessing dominated.
- `accurate` was both slower and worse on the sample: `WER=0.3333`, `4382.00 ms`.

Fixed:
- unified runtime and benchmark timing breakdown propagation
- runtime trace export with validation for direct `RecognizeOnce`
- benchmark trace export plus CPU, memory, and GPU sampling

## Iteration 2

Tested:
- `reports/benchmarks/thesis_20260330_self_audit_final_iter02_noise_balanced/`
- synthetic white-noise levels `clean`, `light`, `medium`, `heavy`

Found:
- On the single built-in sample, all tested noise levels still normalized to `WER=0`.
- Latency dropped on noisy variants because the hypotheses were shorter and the provider returned faster.
- This demonstrates that the metric implementation works, but not that the model is noise-robust in general.

Fixed:
- noise generation endpoint now exports per-variant generation time and total generation time
- benchmark results now preserve `noise_level`, `noise_mode`, and `noise_snr_db` alongside WER/CER

## Iteration 3

Tested:
- `reports/benchmarks/thesis_20260330_self_audit_final_iter03_fr_balanced/`
- `reports/benchmarks/thesis_20260330_self_audit_final_iter03_sk_balanced/`
- `reports/benchmarks/thesis_20260330_self_audit_final_iter03_ja_balanced/`
- backend/API runtime probe in `reports/audit/runtime_api_probe.json`

Found:
- Multilingual quality is the main weakness of the current local Whisper profile set:
  - French mean `WER=0.2500`
  - Slovak mean `WER=0.7143`
  - Japanese mean `WER=1.0000`
- The live segmented runtime path returned `100001` for the demo file, while direct `RecognizeOnce` returned the full number sequence. This points to a segmentation issue rather than a transport issue.
- The direct runtime call initially dropped `audio_duration_sec`; the live verification exposed that bug.

Fixed:
- propagated `audio_duration_sec` through normalized results, ROS messages, and gateway payloads
- added isolated-domain audit execution with `ROS_DOMAIN_ID` to avoid contamination from other ROS graphs
- added a reproducible audit runner at `scripts/run_self_audit_cycle.py`

## Net effect

The repository now has:
- reproducible benchmark iterations with saved JSON, CSV, and Markdown reports
- validated direct runtime traces with latency breakdown and system metrics
- a clear audit trail for what remains missing: topic latency, message drops, action-path observability, and segmented runtime trace export
