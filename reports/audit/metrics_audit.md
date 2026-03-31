# Metrics Audit

Audit date: `2026-03-31`
Refresh after remediation: `2026-03-31`

Status vocabulary:

- `EXISTS_CORRECT`
- `EXISTS_BUT_SUSPICIOUS`
- `PARTIAL`
- `MISSING`
- `MISLEADING`

## Summary

The repository now has one coherent metrics story across canonical benchmark and canonical runtime paths:

- benchmark traces export WER, CER, latency breakdown, RTF, system samples, `model_load_ms`, and warm/cold markers
- runtime `RecognizeOnce`, segmented runtime, and provider-stream runtime export persisted JSON/CSV traces
- runtime transport telemetry now includes sequence-gap and one-way topic-delivery timing
- gateway provider status semantics no longer confuse “profile exists” with “runtime ready”

The remaining metric gaps are now low-severity and explicit:

- no DDS-native queue-depth/backpressure metric; current telemetry uses sequence-gap inference
- confidence remains provider-native and not cross-provider calibrated

## ASR Quality Metrics

| Metric | Status | Current code | Technical note |
|---|---|---|---|
| WER | `EXISTS_CORRECT` | [quality.py](/home/fenix/Desktop/ros2ws/ros2_ws/src/asr_metrics/asr_metrics/quality.py), [runtime validator](/home/fenix/Desktop/ros2ws/ros2_ws/src/asr_metrics/asr_observability/validators/runtime.py) | Corpus denominator logic is correct and validator no longer rejects valid `wer > 1.0`. |
| CER | `EXISTS_CORRECT` | same surfaces as WER | Character-level edit-rate logic is correct and validator now enforces only `>= 0`. |
| Confidence | `PARTIAL` | `NormalizedAsrResult`, runtime/benchmark traces | Confidence is exported correctly but remains provider-native, not normalized across providers. |
| Per-utterance result metadata | `EXISTS_CORRECT` | [asr_orchestrator_node.py](/home/fenix/Desktop/ros2ws/ros2_ws/src/asr_runtime_nodes/asr_runtime_nodes/asr_orchestrator_node.py), `AsrResult.msg`, benchmark result rows | Canonical runtime and benchmark rows now carry request/session/run IDs, provider IDs, latency fields, and trace artifact refs. |
| Hypothesis/reference pairing integrity | `EXISTS_CORRECT` | benchmark result rows and `quality_support` payloads | Benchmark rows keep `sample_id`, normalized reference/hypothesis texts, edit counts, and transcript pairing metadata. |

## Performance Metrics

| Metric | Status | Current code | Technical note |
|---|---|---|---|
| Total latency | `EXISTS_CORRECT` | provider latency metadata + runtime/benchmark traces | Exported consistently in runtime and benchmark traces. |
| Stage latency breakdown | `EXISTS_CORRECT` | provider latency fields + live runtime trace stages | Canonical traces now include runtime live-flow stages (`segment_transport`, `provider_stream_chunk`, `result_publish`) in addition to provider timings. |
| Inference latency | `EXISTS_CORRECT` | provider latency fields | Correctly exported and summarized. |
| Preprocessing latency | `EXISTS_BUT_SUSPICIOUS` | provider latency fields | Metric is correct as provider-side preprocessing, but distinct ROS-node preprocessing is exported separately via live runtime stage traces rather than the same scalar. |
| Postprocessing latency | `EXISTS_BUT_SUSPICIOUS` | provider latency fields | Same caveat as preprocessing latency. |
| Real-time factor (RTF) | `EXISTS_CORRECT` | [runtime.py](/home/fenix/Desktop/ros2ws/ros2_ws/src/asr_metrics/asr_observability/analyzers/runtime.py) | Defined as `processing_time / audio_duration`, exported in runtime and benchmark traces. |

## System Metrics

| Metric | Status | Current code | Technical note |
|---|---|---|---|
| CPU usage | `PARTIAL` | [system.py](/home/fenix/Desktop/ros2ws/ros2_ws/src/asr_metrics/asr_metrics/system.py) | Point-in-time sample, not peak or stage-specific profile. |
| Memory usage | `PARTIAL` | same file | Point-in-time RSS sample, not peak. |
| GPU usage | `PARTIAL` | same file | Best-effort sample when `nvidia-smi` is available. |
| Model load time | `EXISTS_CORRECT` | [manager.py](/home/fenix/Desktop/ros2ws/ros2_ws/src/asr_provider_base/asr_provider_base/manager.py), runtime/benchmark trace exporters | Exported as `model_load_ms`. |
| Warm vs cold start behavior | `EXISTS_CORRECT` | same path + benchmark/runtime traces | Exported as init and call cold/warm markers plus invocation index. |

## ROS-Specific Metrics

| Metric | Status | Current code | Technical note |
|---|---|---|---|
| Service latency | `EXISTS_CORRECT` | gateway `service_call_ms`, runtime trace `ros_service_latency_ms` | Correct for recognize-once and gateway service calls. |
| Action latency | `EXISTS_CORRECT` | [ros_client.py](/home/fenix/Desktop/ros2ws/ros2_ws/src/asr_gateway/asr_gateway/ros_client.py) | Gateway action helper now exports `action_goal_wait_ms`, `action_result_wait_ms`, `action_latency_ms`, and `ros_action_latency_ms` for benchmark/dataset action flows. |
| Topic publication latency | `EXISTS_CORRECT` | [transport.py](/home/fenix/Desktop/ros2ws/ros2_ws/src/asr_runtime_nodes/asr_runtime_nodes/transport.py) + runtime node status/trace metrics | One-way delivery latency is now computed from publisher stamp to subscriber receipt and exported in live runtime traces. |
| Queue backpressure / message drops | `PARTIAL` | transport metadata + sequence-gap counters in runtime nodes/traces | Gap detection is now present, but DDS queue-depth remains inferred rather than directly measured. |

## Benchmark Metrics

| Metric | Status | Current code | Technical note |
|---|---|---|---|
| Model x language x noise condition matrix | `EXISTS_CORRECT` | [benchmark_matrix.json](/home/fenix/Desktop/ros2ws/reports/benchmarks/benchmark_matrix.json) | Canonical benchmark matrix artifact now exists in `reports/benchmarks/`. |
| Failure rate | `EXISTS_CORRECT` | benchmark summary aggregation | Exported and summarized correctly. |
| Corrupted run detection | `EXISTS_CORRECT` | [summary.py](/home/fenix/Desktop/ros2ws/ros2_ws/src/asr_metrics/asr_metrics/summary.py), [orchestrator.py](/home/fenix/Desktop/ros2ws/ros2_ws/src/asr_benchmark_core/asr_benchmark_core/orchestrator.py) | Corrupted rows are flagged, counted, and excluded from aggregate summary metrics while total run counts remain preserved. |
| Reproducibility via resolved config snapshot | `EXISTS_CORRECT` | run manifest `config_snapshots` | Present and tied to benchmark run artifacts. |

## UX Metrics

| Metric | Status | Current code | Technical note |
|---|---|---|---|
| Time-to-first-result | `EXISTS_CORRECT` | provider-stream runtime trace metrics | Exported for live provider-stream runtime as `time_to_first_result_ms`. |
| Time-to-final-result | `EXISTS_CORRECT` | runtime and benchmark traces | Exported as `time_to_final_result_ms` / `time_to_result_ms` depending on path. |
| GUI-visible status consistency | `PARTIAL` | gateway provider/runtime status surfaces | Provider readiness semantics are now honest, but GUI state still depends on observer snapshots plus API composition rather than a single typed status contract. |

## Validation Layer Audit

Current validators now enforce:

- non-negative latency metrics
- ordered timestamps
- non-negative WER/CER
- trace corruption flagging when required latency metrics are missing

Still recommended:

1. add DDS- or executor-native queue-depth instrumentation if deeper ROS transport attribution becomes necessary
2. add peak/over-time CPU and GPU profiling if thesis reporting requires more than point-in-time samples
3. normalize confidence semantics across providers if cross-provider ranking needs statistical comparability
