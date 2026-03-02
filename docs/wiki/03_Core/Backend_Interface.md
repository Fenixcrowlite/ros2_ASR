# Backend Interface

Файл: `ros2_ws/src/asr_core/asr_core/backend.py`.

## Контракт

Каждый backend обязан реализовать:

- `recognize_once(request)`

И может реализовать:

- `streaming_recognize(chunks, language, sample_rate)`

Если streaming не реализован нативно, базовый класс делает fallback:

- буферизация PCM чанков,
- упаковка в WAV bytes,
- вызов `recognize_once`.

## Capability flags

См. `BackendCapabilities` в [[03_Core/Core_Models]].
