# Service: /asr/recognize_once

Тип: `asr_interfaces/srv/RecognizeOnce`.

## Request

- `wav_path`
- `language`
- `enable_word_timestamps`

## Response

- `result` (`AsrResult`)

## Пример

```bash
ros2 service call /asr/recognize_once asr_interfaces/srv/RecognizeOnce "{wav_path: data/sample/en_hello.wav, language: en-US, enable_word_timestamps: true}"
```

## Связанные

- [[02_ROS2/Node_ASR_Server]]
- [[03_Core/Core_Models]]
