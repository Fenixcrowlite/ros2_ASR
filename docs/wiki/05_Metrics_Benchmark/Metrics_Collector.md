# Metrics Collector

Файл: `ros2_ws/src/asr_metrics/asr_metrics/collector.py`.

## Что считает

- WER/CER,
- latency (pre/infer/post/total),
- RTF,
- CPU/RAM/GPU,
- error code/message,
- cost estimate.

## Выходной объект

`BenchmarkRecord`.

## Где используется

- [[02_ROS2/Node_ASR_Server]]
- [[05_Metrics_Benchmark/Benchmark_Runner]]
