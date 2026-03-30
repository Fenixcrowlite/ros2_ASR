# Run Guide (ROS2 Jazzy + ASR)

Практический runbook для актуального modular runtime stack:
`asr_launch` + `asr_runtime_nodes` + `asr_gateway` + `web_ui`.

## 1. Требования

- Ubuntu 24.04
- ROS2 Jazzy в `/opt/ros/jazzy`
- Python 3.12
- `.venv` из `make setup`
- собранный workspace `ros2_ws/install`

Проверка:

```bash
ls /opt/ros/jazzy/setup.bash
python3 --version
test -f .venv/bin/activate
```

## 2. Первый запуск

Из корня репозитория:

```bash
make setup
make build
make test-unit
make test-ros
make test-colcon
```

Что это дает:

- `make setup` создает `.venv` и ставит Python dependencies.
- `make build` собирает ROS2 workspace.
- `make test-unit` прогоняет non-ROS проверки.
- `make test-ros` проверяет ROS integration surface.
- `make test-colcon` подтверждает, что все пакеты проходят `colcon test`.

## 3. Быстрый live-тест в 2 терминалах

Рекомендуемый способ:

```bash
./scripts/open_live_test_terminals.sh
```

Скрипт откроет 2 окна:

1. `ASR Runtime Launch`:
   - стартует `ros2 launch asr_launch runtime_streaming.launch.py`.
2. `ASR Final Results`:
   - подписывается на `/asr/runtime/results/final`,
   - ждет `/asr/runtime/start_session`,
   - запускает runtime session через сервис.

Позиционные аргументы скрипта:

```bash
./scripts/open_live_test_terminals.sh [runtime_profile] [input_mode] [provider_profile] [mic_capture_sec] [audio_file_path]
```

Пример file-mode:

```bash
./scripts/open_live_test_terminals.sh default_runtime file providers/whisper_local 0.0 data/sample/vosk_test.wav
```

## 4. Ручной запуск runtime

Терминал 1:

```bash
cd /home/fenix/Desktop/ros2ws
source .venv/bin/activate
source /opt/ros/jazzy/setup.bash
source ros2_ws/install/setup.bash
ros2 launch asr_launch runtime_streaming.launch.py \
  runtime_profile:=default_runtime \
  provider_profile:=providers/whisper_local \
  input_mode:=mic
```

Терминал 2: запуск session.

```bash
cd /home/fenix/Desktop/ros2ws
source .venv/bin/activate
source /opt/ros/jazzy/setup.bash
source ros2_ws/install/setup.bash
ros2 service call /asr/runtime/start_session asr_interfaces/srv/StartRuntimeSession \
  "{runtime_profile: default_runtime, provider_profile: providers/whisper_local, provider_preset: '', provider_settings_json: '{}', session_id: '', runtime_namespace: /asr/runtime, auto_start_audio: true, processing_mode: segmented, audio_source: mic, audio_file_path: data/sample/vosk_test.wav, language: en-US, mic_capture_sec: 6.0}"
```

Терминал 3: результаты и статус.

```bash
cd /home/fenix/Desktop/ros2ws
source /opt/ros/jazzy/setup.bash
source ros2_ws/install/setup.bash
ros2 topic echo /asr/runtime/results/final --qos-durability transient_local --qos-reliability reliable
```

Для `rqt` используйте подготовленный entrypoint:

```bash
cd /home/fenix/Desktop/ros2ws
bash scripts/run_rqt.sh
```

Опционально:

```bash
ros2 topic echo /asr/status/sessions
ros2 service call /asr/runtime/get_status asr_interfaces/srv/GetAsrStatus "{}"
```

Важно:

- launch сам по себе не начинает live-сессию;
- live flow стартует только после `/asr/runtime/start_session`;
- основной результат теперь в `/asr/runtime/results/final`, а не в legacy `/asr/text/plain`.
- orchestrator пишет каждый финальный результат в launch terminal, поэтому ручной запуск больше не выглядит "немым".
- `/asr/runtime/results/final` публикуется с `transient_local`, поэтому поздний `ros2 topic echo` должен использовать `--qos-durability transient_local`; `rqt_topic` автоматически выбирает durable subscription, когда publisher у топика один и он durable.
- если открыть `rqt` из несоответствующего shell, он не увидит `asr_interfaces/*`; не используйте устаревший корневой `install/setup.bash`, используйте `ros2_ws/install/setup.bash` или `scripts/run_rqt.sh`.

## 5. One-shot демо без live session

Поднять минимальный runtime:

```bash
make run
```

Или напрямую:

```bash
source .venv/bin/activate
source /opt/ros/jazzy/setup.bash
source ros2_ws/install/setup.bash
ros2 launch asr_launch runtime_minimal.launch.py \
  runtime_profile:=default_runtime \
  provider_profile:=providers/whisper_local
```

В другом терминале:

```bash
source .venv/bin/activate
source /opt/ros/jazzy/setup.bash
source ros2_ws/install/setup.bash
ros2 service call /asr/runtime/recognize_once asr_interfaces/srv/RecognizeOnce \
  "{wav_path: data/sample/vosk_test.wav, language: en-US, enable_word_timestamps: true, session_id: '', provider_profile: '', provider_preset: '', provider_settings_json: '{}'}"
```

`RecognizeOnce` можно вызывать с override `provider_profile`, `provider_preset`
и `provider_settings_json`, не меняя активную live session.

## 6. Актуальные runtime interfaces

Topics:

- `/asr/runtime/audio/raw`
- `/asr/runtime/audio/preprocessed`
- `/asr/runtime/vad/activity`
- `/asr/runtime/audio/segments`
- `/asr/runtime/results/partial`
- `/asr/runtime/results/final`
- `/asr/status/nodes`
- `/asr/status/sessions`

Services:

- `/asr/runtime/start_session`
- `/asr/runtime/stop_session`
- `/asr/runtime/reconfigure`
- `/asr/runtime/recognize_once`
- `/asr/runtime/list_backends`
- `/asr/runtime/get_status`
- `/config/list_profiles`
- `/config/validate`

## 7. Provider profiles

Текущие provider profiles в `configs/providers/`:

- `providers/whisper_local`
- `providers/vosk_local`
- `providers/google_cloud`
- `providers/aws_cloud`
- `providers/azure_cloud`

Cloud profiles требуют корректных secret refs в `secrets/refs/`.

## 8. Benchmark и отчеты

```bash
make bench
make report
```

Внешний cross-corpus smoke suite:

```bash
bash scripts/download_dataset_optional.sh
python scripts/run_external_dataset_suite.py --mode core
python scripts/run_external_dataset_suite.py --mode both --api-base-url http://127.0.0.1:8088
```

Артефакты:

- `results/latest_benchmark_summary.json`
- `results/latest_benchmark_run.json`
- `results/benchmark_results.csv`
- `results/benchmark_results.json`
- `results/report.md`
- `results/plots/*.png`
- `artifacts/benchmark_runs/<run_id>/...`
- `results/external_dataset_suite_*.md`
- `results/external_dataset_suite_*.json`

Что считать каноническим:

- `artifacts/benchmark_runs/<run_id>/reports/summary.json` это основной summary для gateway/core benchmark path;
- `results/latest_benchmark_summary.json` это основной локальный summary pointer для `make bench`;
- `results/benchmark_results.json` это compatibility flat export, построенный из canonical run artifacts;
- `results/report.md` строится из `results/latest_benchmark_summary.json`, а не из flat export как источника истины.
- для multi-provider benchmark главным разрезом анализа являются `provider_summaries` внутри `summary.json`.

Семантика summary:

- для multi-provider run top-level metric groups пустые и не используются;
- внутри `provider_summaries` `wer` и `cer` агрегируются как corpus-level rate;
- `sample_accuracy` это exact normalized match rate;
- `streaming_metrics` существуют только для streaming run;
- `cost_metrics.estimated_cost_usd` это mean per sample, а total cost берется из `metric_statistics.estimated_cost_usd.sum`.

CLI utilities теперь умеют bootstrapping repo imports без внешнего `PYTHONPATH`,
поэтому их можно запускать и из временного `cwd`.

Dataset manifests могут хранить относительные `audio_path`.
Теперь они интерпретируются относительно самого manifest-файла, а не текущего
`cwd`. При upload/import manifest bundle также будет отвергнут, если:

- имена файлов сталкиваются после нормализации basename;
- manifest ссылается на аудио, которого нет в загруженном наборе.

`bash scripts/download_dataset_optional.sh` теперь больше не placeholder:
он пересобирает локальные subset-профили из LibriSpeech, Mini LibriSpeech,
FLEURS, VoxPopuli и Multilingual LibriSpeech.

## 9. Web GUI

Локальный запуск:

```bash
make web-gui
```

LAN bind:

```bash
make web-gui-lan
```

Остановка:

```bash
make web-gui-stop
```

Что важно:

- default bind теперь `127.0.0.1`, а не `0.0.0.0`;
- `--mode lan` это осознанный opt-in;
- GUI опирается на `asr_gateway` и runtime services `/asr/runtime/*`.

## 10. Archviz

Быстрый безопасный путь:

```bash
make arch-static
```

Полный runtime-aware path:

```bash
make arch
```

Важно:

- `make arch` и `make arch-runtime` теперь fail-fast, если другой managed stack
  из этого же workspace уже запущен;
- это сделано специально, чтобы не смешивать runtime graph с чужими live nodes,
  topics и services;
- если у вас уже поднят `make web-gui` / `full_stack_dev.launch.py`, сначала
  остановите его, потом запускайте archviz.

## 11. Типовые проблемы

### 11.1 Runtime поднялся, но ничего не распознает

Проверь:

- был ли реально вызван `/asr/runtime/start_session`;
- `audio_source` совпадает с ожидаемым (`mic|file`);
- выбран существующий `audio_file_path` для file-mode;
- `ros2 service call /asr/runtime/get_status ...` возвращает `session_state=ready|running`.

### 11.2 Нет сообщений в `/asr/runtime/results/final`

Проверь:

- что session уже стартовала;
- что `provider_profile` валиден;
- что для позднего CLI-подписчика указан `--qos-durability transient_local`;
- что нет ошибок в `/asr/status/nodes` и логах orchestrator/audio_input.

### 11.3 Cloud provider profile валиден по YAML, но runtime не готов

Разделяй два уровня:

- profile validation: профиль синтаксически и структурно корректен;
- runtime readiness: секреты/credentials реально доступны и backend может стартовать.

Перед live/benchmark прогонами для cloud providers сначала проверь страницу
`Secrets` в GUI или secret refs в `secrets/refs/`.

### 11.4 `libcublas.so.12` или другие CUDA runtime ошибки

Для быстрого обхода:

- переключи provider profile на CPU-friendly режим;
- либо используй `providers/vosk_local`;
- либо настрой корректный CUDA runtime в `.venv`.

## 12. Legacy compatibility

В репозитории все еще есть `asr_ros` и связанные legacy docs/scripts для
совместимости и migration reference. Для актуального runtime stack не используй
их как основной runbook, если задача не состоит именно в проверке обратной
совместимости.
