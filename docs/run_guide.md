# Run Guide (ROS2 Jazzy + ASR)

Практическая инструкция: как поднять систему, где смотреть распознавание, как запускать быстрые проверки.

## 1. Требования

- Ubuntu 24.04
- ROS2 Jazzy установлен в `/opt/ros/jazzy`
- Python 3.12
- В репозитории есть `.venv` (или будет создан через `make setup`)

Проверка:

```bash
ls /opt/ros/jazzy/setup.bash
python3 --version
```

## 2. Первый запуск (один раз)

Из корня репозитория:

```bash
make setup
make build
make test-unit
```

Что делает:

- `make setup` создаёт `.venv`, ставит зависимости, добавляет launcher `archviz`.
- `make build` собирает ROS2 workspace (`colcon build`).
- `make test-unit` проверяет базовую логику без ROS runtime.

## 3. Быстрый live-тест в 2 терминалах (рекомендуется)

Самый удобный вариант:

```bash
./scripts/open_live_test_terminals.sh
```

Скрипт откроет 2 окна:

1. `ASR Recognition` — запуск `bringup.launch.py`.
2. `ASR Text Topic` — `ros2 topic echo /asr/text/plain`.

По умолчанию используется конфиг `configs/live_mic_whisper.yaml`.

## 4. Ручной запуск (если нужно без скрипта)

Терминал 1:

```bash
cd /home/fenix/Desktop/ros2ws
source .venv/bin/activate
export PYTHONPATH="$(python -c 'import site; print(site.getsitepackages()[0])'):${PYTHONPATH}"
source /opt/ros/jazzy/setup.bash
source install/setup.bash
ros2 launch asr_ros bringup.launch.py config:=configs/live_mic_whisper.yaml input_mode:=mic
```

Терминал 2 (распознанный текст):

```bash
cd /home/fenix/Desktop/ros2ws
source /opt/ros/jazzy/setup.bash
source install/setup.bash
ros2 topic echo /asr/text/plain --qos-durability transient_local --qos-reliability reliable
```

Терминал 3 (метрики, опционально):

```bash
cd /home/fenix/Desktop/ros2ws
source /opt/ros/jazzy/setup.bash
source install/setup.bash
ros2 topic echo /asr/metrics
```

## 5. Где смотреть результат

- Основной plain-text: `/asr/text/plain` (отдельная нода `asr_text_output_node`)
- Структурный результат: `/asr/text`
- Метрики: `/asr/metrics`
- One-shot сервис: `/asr/recognize_once`

Пример one-shot вызова:

```bash
ros2 service call /asr/recognize_once asr_interfaces/srv/RecognizeOnce "{wav_path: data/sample/en_hello.wav, language: en-US, enable_word_timestamps: true}"
```

## 6. Как поменять backend на лету

```bash
ros2 service call /asr/set_backend asr_interfaces/srv/SetAsrBackend "{backend: mock, model: '', region: ''}"
```

Проверить состояние:

```bash
ros2 service call /asr/get_status asr_interfaces/srv/GetAsrStatus "{}"
```

## 7. Тесты и бенчмарк

```bash
make test-unit
make test-ros
make test-colcon
make bench
make report
```

Примечания по benchmark reproducibility:

- `benchmark.scenarios` в YAML можно задавать как список или как строку через запятую (`clean,snr20,snr10`).
- Относительные `wav_path` в dataset-манифесте резолвятся сначала относительно директории самого манифеста, затем относительно текущего `cwd`.

## 8. Запись live-семпла и прогон по выбранным интерфейсам

Интерактивный режим (запись, затем выбор языка и моделей):

```bash
bash scripts/run_live_sample_eval.sh
```

Non-interactive режим:

```bash
bash scripts/run_live_sample_eval.sh \
  --interfaces core,ros_service,ros_action \
  --model-runs whisper:tiny,whisper:large-v3,mock \
  --language-mode auto \
  --ros-auto-launch \
  --reference-text "hello world"
```

Что делает:

1. Пишет микрофон в WAV.
2. Прогоняет один и тот же WAV через выбранные интерфейсы:
   - `core`
   - `ros_service`
   - `ros_action`
3. Для каждого прогона сохраняет метрики.

Артефакты:

- `results/live_sample/<timestamp>/live_results.csv`
- `results/live_sample/<timestamp>/live_results.json`
- `results/live_sample/<timestamp>/summary.md`
- `results/live_sample/<timestamp>/plots/*.png`

Полезные флаги:

- `--record-sec 5.0`
- `--model-runs whisper:tiny,whisper:large-v3,mock`
- `--language-mode manual|auto|config`
- `--language ru-RU`
- `--use-wav /path/to/file.wav`
- `--action-streaming`

## 9. Архитектурные диаграммы

```bash
make arch
```

Артефакты будут в `docs/arch/`:

- `static_graph.json`
- `runtime_graph.json`
- `merged_graph.json`
- `mindmap.mmd`, `flow.mmd`, `seq_recognize_once.mmd`
- `CHANGELOG_ARCH.md`

## 10. Типовые проблемы

### 10.1 `libcublas.so.12 is not found`

Это CUDA runtime проблема. Для быстрого восстановления:

1. В `configs/live_mic_whisper.yaml` сменить `device: cuda` на `device: cpu`.
2. Перезапустить `bringup.launch.py`.

### 10.2 В `/asr/text/plain` пусто

Проверь:

- в первом терминале есть логи `Live transcription published`;
- совпадает QoS (`--qos-durability transient_local --qos-reliability reliable`);
- в `ros2 node list` есть `asr_text_output_node`;
- микрофон доступен (иначе узел уйдёт в file fallback).

### 10.3 Распознавание "галлюцинирует" на тишине

Для Whisper уже включены анти-повторы в `configs/live_mic_whisper.yaml`:

- `condition_on_previous_text: false`
- `vad_filter: true`
- `no_speech_threshold: 0.7`

Если всё ещё шумно, увеличь `no_speech_threshold` (например до `0.8`).

## 11. Остановка

- Закрой терминалы с `ros2 launch` / `ros2 topic echo`.
- Либо нажми `Ctrl+C` в каждом активном ROS2 процессе.

## 12. Web GUI (новый gateway-first control center)

Запуск:

```bash
make web-gui
```

`make web-gui` запускает новый GUI-стек:
- runtime pipeline,
- benchmark manager,
- `asr_gateway` backend с новым `web_ui` фронтендом.

Для запуска в LAN:

```bash
make web-gui-lan
```

Адрес:

```text
http://localhost:8088
```

Возможности нового GUI:

- настройка языков/моделей/backend параметров,
- управление profiles/providers/datasets/benchmark runs,
- просмотр results/logs/diagnostics,
- работа с credentials refs (без показа секретов).

Legacy GUI остался как совместимый fallback:

```bash
make web-gui-legacy
make web-gui-legacy-lan
```

### 12.1 Cloud auth fail-fast (legacy `web_gui`, важно)

Для legacy GUI (`make web-gui-legacy`) перед стартом job выполняется cloud auth fail-fast и запуск останавливается с `HTTP 400`, если:

- `google`: не задан/не найден `secrets/google/service-account.json` или `GOOGLE_APPLICATION_CREDENTIALS`.
- `azure`: не заданы `AZURE_SPEECH_KEY` и/или `AZURE_SPEECH_REGION`.
- `aws`: не задан `AWS_PROFILE` и нет пары `AWS_ACCESS_KEY_ID` + `AWS_SECRET_ACCESS_KEY`.
- `aws`: не задан `ASR_AWS_S3_BUCKET`.

Для `aws` дополнительно выполняется preflight:

```bash
# boto3 STS preflight (fallback to AWS CLI `aws sts get-caller-identity`
# when boto3 is unavailable in runtime environment)
```

Это позволяет поймать просроченный/отсутствующий SSO token до длинного запуска ROS.

Для повторных AWS запусков в рамках одной GUI-сессии успешный STS preflight
кешируется на короткое время (по умолчанию 120 секунд, `WEB_GUI_AWS_STS_PREFLIGHT_TTL_SEC`).
Типовые SSO ошибки (`pending authorization expired`, `InvalidGrantException`, `token expired`)
возвращаются с явными подсказками в `HTTP 400` detail.
Отключение (только для диагностики):

```bash
export WEB_GUI_SKIP_AWS_STS_PREFLIGHT=1
```

### 12.2 AWS SSO login из legacy GUI

В legacy GUI `AWS SSO Login` запускается в browser-first режиме (без принудительного `--no-browser`), что снижает риск истечения pending authorization при device-code flow.
Для runtime SSO профиля обязательно указывать:

- `AWS_SSO_ACCOUNT_ID`
- `AWS_SSO_ROLE_NAME`

## 13. Colcon notifications и пробуждение экрана

В проекте по умолчанию отключено desktop-notify расширение colcon:

```bash
COLCON_EXTENSION_BLOCKLIST=colcon_core.event_handler.desktop_notification
```

Это снижает вероятность самопроизвольного пробуждения экрана во время фоновых `build/test` запусков.
Если уведомления нужны явно, переопределите переменную окружения перед запуском.

Дополнительно `colcon`-вызовы в `Makefile` и runtime-скриптах теперь выполняются через lock-wrapper
`scripts/with_colcon_lock.sh`, чтобы параллельные сценарии (`build/test/bench/demo`) не портили
друг другу `build/install/log` состояние workspace.
