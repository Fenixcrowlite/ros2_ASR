# Core Models

Файл: `ros2_ws/src/asr_core/asr_core/models.py`.

## Главные dataclass

- `AsrRequest`
- `AsrResponse`
- `AsrTimings`
- `WordTimestamp`
- `BackendCapabilities`

## Важное

`AsrResponse` — единый контракт для всех backend, поэтому ROS слой не зависит от провайдера.

## Связанные

- [[03_Core/Backend_Interface]]
- [[02_ROS2/Interfaces_Overview]]
