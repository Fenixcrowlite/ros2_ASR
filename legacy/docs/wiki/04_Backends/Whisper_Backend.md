# Whisper Backend

Файл: `ros2_ws/src/asr_backend_whisper/asr_backend_whisper/backend.py`.

## Назначение

Высокое качество локального ASR (faster-whisper).

## Основные параметры

- `model_size`
- `device`
- `compute_type`
- `temperature`
- `no_speech_threshold`
- `condition_on_previous_text`
- `vad_filter`

## GPU mode

Если выбран `device=cuda`, backend теперь работает строго в CUDA-режиме.
Если CUDA runtime библиотек нет, он возвращает явную ошибку с подсказкой
исправить окружение или задать `device=cpu` явно. Автоматического CPU fallback
больше нет.

## Связанные

- [[06_Operations/Troubleshooting_Playbook]]
- [[08_Data_Configs/Live_Mic_Whisper_Config]]
