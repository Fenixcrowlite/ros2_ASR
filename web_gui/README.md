# ROS2 ASR Web GUI

Полноценный web control center для проекта `ros2ws`.

## Что умеет

- Настройка runtime-конфига до деталей:
  - backend, language, sample rate, chunk size, input mode;
  - backend-specific параметры (Whisper/Vosk/Google/AWS/Azure);
  - cloud credentials/tokens/keys.
- Live pipeline:
  - запись с микрофона или выбор собственного WAV;
  - `manual/auto/config` режим языка;
  - множественные прогоны `backend[:model][@region]`;
  - интерфейсы `core`, `ros_service`, `ros_action`.
- Benchmark pipeline:
  - выбор dataset CSV;
  - список backend;
  - сценарии шума и выбранные метрики.
- Управление ROS2 bringup:
  - старт/стоп long-running launch;
  - включение/выключение отдельной text-node (`/asr/text/plain`).
- Data tools:
  - upload sample/dataset/config;
  - генерация noisy WAV по SNR уровням.
- Job orchestration:
  - фоновые задачи,
  - просмотр логов,
  - просмотр артефактов (CSV/JSON/MD/PNG/WAV),
  - остановка задач.

## Запуск

Из корня репозитория:

```bash
bash web_gui/run_web_gui.sh
```

По умолчанию: `http://localhost:8765`.

## Архитектура модуля

- `web_gui/app/main.py` — FastAPI API + статика.
- `web_gui/app/job_manager.py` — жизненный цикл subprocess job.
- `web_gui/app/config_builder.py` — генерация runtime YAML + инжекция секретов.
- `web_gui/app/command_builder.py` — команды для live/benchmark/bringup.
- `web_gui/static/` — frontend (HTML/CSS/JS).

## Замечания по безопасности

- Поля секретов UI передаются только в runtime config/env конкретного запуска.
- Не храните production-секреты в git.
- `web_gui/runtime_configs/`, `web_gui/uploads/`, `web_gui/noisy/`, `web_gui/logs/` рекомендуется держать в `.gitignore`.

## Smoke сценарии

1. Upload `data/sample/en_hello.wav`.
2. Noise overlay `30,20,10,0`.
3. Live run: `interfaces=core`, `model_runs=mock,whisper:tiny`, `language_mode=auto`.
4. Benchmark run: `dataset=data/transcripts/sample_manifest.csv`, `backends=mock,whisper`.
5. ROS bringup: `input_mode=mic`, затем стоп job.
