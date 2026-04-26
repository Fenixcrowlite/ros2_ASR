# live_mic_whisper.yaml

Путь: `configs/live_mic_whisper.yaml`.

## Назначение

Live профиль для микрофона с backend whisper.

## Важные поля

- `asr.backend: whisper`
- `asr.language: ru-RU`
- `backends.whisper.model_size: large-v3`
- `backends.whisper.device: cuda`
- anti-hallucination flags (`condition_on_previous_text`, `vad_filter`, `no_speech_threshold`)

## Связанные

- [[04_Backends/Whisper_Backend]]
- [[06_Operations/Live_Run_Playbook]]
