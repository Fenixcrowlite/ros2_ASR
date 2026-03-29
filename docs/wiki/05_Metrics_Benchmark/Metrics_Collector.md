# Metrics Collector

Файлы:

- legacy runner: `ros2_ws/src/asr_metrics/asr_metrics/collector.py`
- new summary engine: `ros2_ws/src/asr_metrics/asr_metrics/engine.py`
- aggregation helpers: `ros2_ws/src/asr_metrics/asr_metrics/summary.py`

## Что считает

- WER/CER,
- sample accuracy,
- latency (pre/infer/post/total),
- RTF,
- success/failure rate,
- CPU/RAM/GPU,
- error code/message,
- cost estimate.

## Выходной объект

- legacy flat artifact row: `BenchmarkRecord`
- core/gateway benchmark row: JSON row under `artifacts/benchmark_runs/<run_id>/metrics/results.json`

## Замечание по агрегации

- per-row quality метрики хранятся на уровне sample.
- summary/report/UI агрегируют `WER`/`CER` как corpus-level rate.
- streaming метрики не должны попадать в batch summary.

## Где используется

- [[02_ROS2/Node_ASR_Server]]
- [[05_Metrics_Benchmark/Benchmark_Runner]]
