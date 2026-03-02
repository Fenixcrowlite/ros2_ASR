# Troubleshooting Playbook

## Симптом: `libcublas.so.12 not found`

Причина: не хватает CUDA runtime libs.

Решение:

1. В `configs/live_mic_whisper.yaml` поставить `device: cpu`.
2. Или корректно добавить NVIDIA libs в `LD_LIBRARY_PATH`.

## Симптом: пусто в `/asr/text/plain`

Проверь:

- жив ли `asr_server_node`,
- жив ли `asr_text_output_node`,
- что `text_output_enabled` не выключен,
- правильный QoS в `ros2 topic echo /asr/text/plain --qos-durability transient_local --qos-reliability reliable`,
- backend действительно распознаёт входной WAV,
- не идет fallback в неверный режим.

## Симптом: `ModuleNotFoundError: sounddevice` или `soundfile` в live sample eval

Причина: запуск не в окружении с зависимостями микрофона.

Решение:

1. Активировать `.venv` и установить зависимости:

```bash
source .venv/bin/activate
pip install -r requirements.txt
python -c "import sounddevice, soundfile; print('ok')"
```

2. Если нужен прогон без микрофона, использовать `--use-wav /path/to/file.wav`.
3. Для GUI запустить preflight и проверить секцию `microphone`.

## Симптом: `client_init_error` cloud backend

Проверь:

- установлен SDK пакет,
- ENV ключи заданы,
- Python path включает venv site-packages.

## Связанные

- [[04_Backends/Whisper_Backend]]
- [[04_Backends/Google_Backend]]
- [[04_Backends/Secrets_And_ENV]]
- [[02_ROS2/Node_ASR_Text_Output]]
- [[00_Start/Glossary#Preflight]]
