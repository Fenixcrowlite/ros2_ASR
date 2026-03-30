# Missing Metrics

Status after the `thesis_20260330_self_audit_final` pass.

## Corrected in this pass

- `RecognizeOnce` HTTP payloads now carry `audio_duration_sec`, `preprocess_ms`, `inference_ms`, `postprocess_ms`, and `raw_metadata_ref`.
- Benchmark runs now export per-sample traces, system usage samples, and thesis-facing `reports/benchmarks/<run_id>/` copies.
- Noise generation now records per-variant and total generation latency.

## Remaining missing or partial metrics

| Metric | Status | Current state |
|---|---|---|
| ROS topic latency | Missing | No first-class metric exists for one-way or round-trip latency across `raw_audio`, `preprocessed_audio`, `speech_segments`, and `final_results`. Current runtime session evidence is wall-clock only. |
| ROS message drops | Missing | No sequence counter or drop detector is attached to runtime topic messages, so drops cannot be measured or exported. |
| Action latency (`/asr/transcribe`) | Missing | Legacy action mode exists in `asr_ros`, but the new observability path targets benchmark execution and runtime services, not the action server. |
| Segmented runtime trace artifact | Partial | Direct `RecognizeOnce` writes a validated trace artifact. Live segmented runtime sessions still publish empty `raw_metadata_ref`, so per-segment trace files are not exported yet. |
| Runtime session system metrics | Partial | CPU, memory, and GPU metrics are present in benchmark traces and direct `RecognizeOnce` traces. The live segmented runtime path does not yet persist per-segment system usage samples. |
| GUI time-to-result as persistent metric | Partial | The audit runner measures wall time to first result (`4032.65 ms` in the final probe), but the runtime session path does not export this as a named artifact field. |
| WER vs noise statistical coverage | Partial | Metric computation exists and was correct for the sample dataset, but the live thesis run only covered one sample under synthetic white noise. Broader dataset coverage is still needed. |

## Validation coverage

Implemented validators currently enforce:
- latency values must be non-negative
- WER and CER must be in `[0, 1]`
- timestamps and stage boundaries must be ordered
- missing required metrics mark the trace as corrupted

Validator gaps:
- no validator currently checks topic sequence continuity, because no message sequence counter exists
- no validator currently checks action feedback/result timing, because that path is not instrumented
