# Azure Backend

Файл: `ros2_ws/src/asr_backend_azure/asr_backend_azure/backend.py`.

## API

Azure Cognitive Services Speech SDK.

## Конфиг/ENV

- `AZURE_SPEECH_KEY`
- `AZURE_SPEECH_REGION`
- optional endpoint id

## Возвращаемые данные

- text,
- confidence,
- word timestamps,
- normalized timing/error fields.
