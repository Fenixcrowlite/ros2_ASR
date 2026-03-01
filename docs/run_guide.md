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
2. `ASR Text Topic` — `ros2 topic echo /asr/text`.

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
ros2 topic echo /asr/text --qos-durability transient_local --qos-reliability reliable
```

Терминал 3 (метрики, опционально):

```bash
cd /home/fenix/Desktop/ros2ws
source /opt/ros/jazzy/setup.bash
source install/setup.bash
ros2 topic echo /asr/metrics
```

## 5. Где смотреть результат

- Основной текст: `/asr/text`
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

## 8. Архитектурные диаграммы

```bash
make arch
```

Артефакты будут в `docs/arch/`:

- `static_graph.json`
- `runtime_graph.json`
- `merged_graph.json`
- `mindmap.mmd`, `flow.mmd`, `seq_recognize_once.mmd`
- `CHANGELOG_ARCH.md`

## 9. Типовые проблемы

### 9.1 `libcublas.so.12 is not found`

Это CUDA runtime проблема. Для быстрого восстановления:

1. В `configs/live_mic_whisper.yaml` сменить `device: cuda` на `device: cpu`.
2. Перезапустить `bringup.launch.py`.

### 9.2 В `/asr/text` пусто

Проверь:

- в первом терминале есть логи `Live transcription published`;
- совпадает QoS (`--qos-durability transient_local --qos-reliability reliable`);
- микрофон доступен (иначе узел уйдёт в file fallback).

### 9.3 Распознавание "галлюцинирует" на тишине

Для Whisper уже включены анти-повторы в `configs/live_mic_whisper.yaml`:

- `condition_on_previous_text: false`
- `vad_filter: true`
- `no_speech_threshold: 0.7`

Если всё ещё шумно, увеличь `no_speech_threshold` (например до `0.8`).

## 10. Остановка

- Закрой терминалы с `ros2 launch` / `ros2 topic echo`.
- Либо нажми `Ctrl+C` в каждом активном ROS2 процессе.
