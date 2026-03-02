# Vosk Backend

Файл: `ros2_ws/src/asr_backend_vosk/asr_backend_vosk/backend.py`.

## Назначение

Локальный offline backend с native chunk streaming.

## Конфиг

- `model_path` или `VOSK_MODEL_PATH`

## Ограничение

Ожидает mono 16-bit PCM WAV.

## Связанные

- [[04_Backends/Capabilities_Matrix]]
- [[08_Data_Configs/Live_Mic_Whisper_Config]]
