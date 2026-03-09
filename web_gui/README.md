# ROS2 ASR Web GUI

Полноценный web control center для проекта `ros2ws`.

## Что умеет

- Настройка runtime-конфига до деталей:
  - backend, language, sample rate, chunk size, input mode;
  - backend-specific параметры (Whisper/Vosk/Google/AWS/Azure);
  - cloud credentials/tokens/keys.
  - переносимые AWS auth-файлы (`web_gui/auth_profiles/*.txt`) c выбором из dropdown.
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
  - AWS SSO login как отдельный job прямо из GUI (device-code flow).

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
- `web_gui/app/aws_auth_store.py` — хранение/парсинг AWS auth-текстов и подготовка runtime AWS config.
- `web_gui/app/command_builder.py` — команды для live/benchmark/bringup.
- `web_gui/static/` — frontend (HTML/CSS/JS).

## Замечания по безопасности

- Поля секретов UI передаются только в runtime config/env конкретного запуска.
- Не храните production-секреты в git.
- `web_gui/runtime_configs/`, `web_gui/uploads/`, `web_gui/noisy/`, `web_gui/logs/`, `web_gui/auth_profiles/`, `web_gui/runtime_aws/` рекомендуется держать в `.gitignore`.

## AWS auth-файл (переносимый)

В блоке `Cloud Auth` можно:

1. Выбрать/сохранить AWS auth-файл (`.txt`) в `web_gui/auth_profiles/`.
2. Заполнить только 2 поля в GUI: `AWS SSO start URL` и `AWS SSO region`.
3. Собрать текст файла из этих полей кнопкой `Build AWS Auth File`.
4. Выбирать ранее введённые URL/region из выпадающих подсказок (берутся из сохранённых auth/profile конфигов).
5. Сохранить в `AWS auth profile file` (значения останутся как константы на будущее).
6. Запустить `AWS SSO Login` из GUI и пройти авторизацию по URL+code из логов job.

Пример содержимого файла:

```text
AWS_AUTH_TYPE=sso
AWS_PROFILE=ros2ws
AWS_REGION=eu-north-1
AWS_S3_BUCKET=ros2ws-asr-787345513049-eu-north-1
AWS_SSO_START_URL=https://d-xxxxxxxxxx.awsapps.com/start
AWS_SSO_REGION=eu-north-1
AWS_SSO_ACCOUNT_ID=123456789012
AWS_SSO_ROLE_NAME=AdministratorAccess
```

## Smoke сценарии

1. Upload `data/sample/en_hello.wav`.
2. Noise overlay `30,20,10,0`.
3. Live run: `interfaces=core`, `model_runs=mock,whisper:tiny`, `language_mode=auto`.
4. Benchmark run: `dataset=data/transcripts/sample_manifest.csv`, `backends=mock,whisper`.
5. ROS bringup: `input_mode=mic`, затем стоп job.

## Готовые web-сценарии в `configs/`

- `configs/web_latest_local_matrix.yaml` — быстрый локальный matrix по `mock/whisper` с полным списком метрик.
- `configs/web_latest_local_quality.yaml` — quality-набор для сравнения `whisper:small/medium/large-v3`.
- `configs/web_latest_cloud_matrix.yaml` — вариации последних cloud-моделей (`google latest_* + chirp_2`, `aws`, `azure`) + локальный baseline.
- `configs/web_ros_wrapper_e2e.yaml` — end-to-end сценарий для `core + ros_service + ros_action`.

В GUI эти конфиги появляются в `Base config`; при выборе автоматически применяются значения из YAML (`asr/backends/benchmark/web`).
