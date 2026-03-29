# Node: audio_capture_node

Файл: `ros2_ws/src/asr_ros/asr_ros/audio_capture_node.py`.

## Роль

- Захват микрофона или чтение WAV.
- Публикация PCM чанков в `/asr/audio_chunks`.

## Режимы

- `input_mode=mic`
- `input_mode=file`

## Параметры

- `wav_path`
- `sample_rate`
- `chunk_ms`
- `device`
- `continuous`
- `mic_capture_sec`

## Связанные страницы

- [[02_ROS2/Topic_Audio_Chunks]]
- [[06_Operations/Live_Run_Playbook]]
- [[00_Start/Glossary#Input Mode]]
