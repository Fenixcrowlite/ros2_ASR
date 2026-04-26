# Backend Factory

Файл: `ros2_ws/src/asr_core/asr_core/factory.py`.

## Что делает

- регистрирует backend-классы (`@register_backend`),
- лениво импортирует backend по имени,
- создаёт экземпляр через `create_backend(name, config)`.

## Поддерживаемые имена

- `mock`
- `vosk`
- `whisper`
- `google`
- `aws`
- `azure`

## Где используется

- [[02_ROS2/Node_ASR_Server]]
- [[05_Metrics_Benchmark/Benchmark_Runner]]
