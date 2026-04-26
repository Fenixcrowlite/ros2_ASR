# Google Backend

Файл: `ros2_ws/src/asr_backend_google/asr_backend_google/backend.py`.

## API

Google Cloud Speech-to-Text (`google-cloud-speech`).

## Конфиг/ENV

- model: `ASR_GOOGLE_MODEL`
- region: `ASR_GOOGLE_REGION`
- endpoint: `ASR_GOOGLE_ENDPOINT`
- credentials: `GOOGLE_APPLICATION_CREDENTIALS`

## Что возвращает

- transcript,
- confidence,
- word timestamps,
- latency breakdown.

## Практический тест

- [[06_Operations/Google_STT_Test_Playbook]]
