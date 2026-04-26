# Google STT Test Playbook

## Подготовка ENV

```bash
export GOOGLE_APPLICATION_CREDENTIALS="/home/fenix/Desktop/creditionals/your-key.json"
```

## Unit cloud test

```bash
pytest -q tests/unit/test_cloud_backends.py -m cloud -k google
```

## ROS e2e test

1. Поднять demo launch.
2. Вызвать `set_backend` -> `google`.
3. Вызвать `recognize_once`.

Примеры:

```bash
ros2 service call /asr/set_backend asr_interfaces/srv/SetAsrBackend "{backend: google, model: latest_long, region: global}"
ros2 service call /asr/recognize_once asr_interfaces/srv/RecognizeOnce "{wav_path: /tmp/google_test_digit.wav, language: en-US, enable_word_timestamps: true}"
```

## Типичный симптом

`client_init_error` при запуске ноды системным Python без venv site-packages.

См. [[06_Operations/Troubleshooting_Playbook]].
