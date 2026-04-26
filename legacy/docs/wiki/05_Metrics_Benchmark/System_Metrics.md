# System Metrics

Файл: `ros2_ws/src/asr_metrics/asr_metrics/system.py`.

## Источники

- CPU/RAM: `psutil`
- GPU: `nvidia-smi` (если доступен)

## Поведение без GPU

Возвращает `0.0, 0.0` без падения.

## Связанные

- [[05_Metrics_Benchmark/Metrics_Collector]]
- [[06_Operations/Troubleshooting_Playbook]]
