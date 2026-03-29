# Newbie Code Guide

Этот проект больше не является monolith `asr_ros`.
Актуальная архитектура разделена на runtime, benchmark, gateway и provider layers.

## 1. Главная картина

Система разбита на 4 основных контура:

1. Runtime:
   - `asr_runtime_nodes`
   - `asr_launch`
   - `asr_provider_base`
   - `asr_provider_*`
2. Benchmark:
   - `asr_benchmark_core`
   - `asr_benchmark_nodes`
   - `asr_metrics`
   - `asr_reporting`
3. Gateway/UI:
   - `asr_gateway`
   - `web_ui`
4. Shared contracts:
   - `asr_core`
   - `asr_interfaces`
   - `asr_config`
   - `asr_storage`

`asr_ros` и часть старых wiki pages остались как compatibility layer, а не как
основной runtime path.

## 2. Runtime flow

Актуальный live pipeline такой:

1. `audio_input_node`
   - читает микрофон или WAV;
   - публикует `AudioChunk` в `/asr/runtime/audio/raw`.
2. `audio_preprocess_node`
   - нормализует/ресемплит аудио;
   - публикует в `/asr/runtime/audio/preprocessed`.
3. `vad_segmenter_node`
   - режет поток на speech segments;
   - публикует activity и `AudioSegment`.
4. `asr_orchestrator_node`
   - загружает runtime/provider profile;
   - управляет session lifecycle;
   - вызывает provider adapters;
   - публикует `/asr/runtime/results/partial` и `/asr/runtime/results/final`.

Это важно:

- launch не означает автоматический старт live session;
- сначала поднимается runtime stack;
- потом вызывается `/asr/runtime/start_session`.
- финальный transcript публикуется в `/asr/runtime/results/final` и одновременно логируется в terminal orchestrator.

## 3. Основные runtime interfaces

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

Самый важный practical difference относительно старой схемы:

- больше нет primary `/asr/text/plain`;
- больше нет primary `/asr/set_backend`;
- больше нет primary `/asr/get_status`.

## 4. Provider layer

Provider adapters живут отдельно от runtime nodes.

Ключевые файлы:

- `asr_provider_base/adapter.py`: общий adapter contract.
- `asr_provider_base/manager.py`: загрузка provider profile + preset + secret ref.
- `configs/providers/*.yaml`: operator-facing provider profiles.
- `asr_provider_whisper`, `asr_provider_vosk`, `asr_provider_google`,
  `asr_provider_aws`, `asr_provider_azure`: конкретные adapters.

Идея:

- GUI/ROS/runtime работают с profile ids;
- `ProviderManager` превращает profile в готовый adapter;
- runtime не должен знать backend-specific детали.

## 5. Config layer

Конфиги теперь разложены по назначению:

- `configs/runtime/`
- `configs/providers/`
- `configs/benchmark/`
- `configs/datasets/`
- `configs/metrics/`
- `configs/deployment/`
- `configs/gui/`

Самый важный runtime profile сейчас:

- `configs/runtime/default_runtime.yaml`

Provider profiles:

- `configs/providers/whisper_local.yaml`
- `configs/providers/vosk_local.yaml`
- `configs/providers/google_cloud.yaml`
- `configs/providers/aws_cloud.yaml`
- `configs/providers/azure_cloud.yaml`

Cloud secrets не хранятся inline в profiles.
Для этого используется `credentials_ref` -> `secrets/refs/*.yaml`.

## 6. Gateway/UI flow

Browser не общается напрямую с Python backend packages.
Он идет через `asr_gateway`.

Путь запроса:

1. `web_ui/frontend/*`
2. HTTP API `/api/...`
3. `asr_gateway/api.py`
4. `GatewayRosClient`
5. ROS services/actions или filesystem artifacts

Примеры:

- `POST /api/runtime/start` -> `/asr/runtime/start_session`
- `POST /api/runtime/recognize_once` -> `/asr/runtime/recognize_once`
- `GET /api/runtime/live` -> snapshot runtime status/results
- `POST /api/providers/validate` -> provider profile preflight

## 7. Benchmark flow

Benchmark pipeline отдельный от low-latency runtime.

Основная цепочка:

1. dataset profile
2. benchmark profile
3. provider list
4. orchestrator run
5. metric aggregation
6. report export

Ключевые модули:

- `asr_benchmark_core/orchestrator.py`
- `asr_benchmark_nodes/benchmark_manager_node.py`
- `asr_metrics/`
- `asr_reporting/`

Артефакты пишутся в:

- `results/`
- `artifacts/benchmark_runs/<run_id>/`

Для внешнего corpus smoke path теперь есть готовая автоматизация:

- `bash scripts/download_dataset_optional.sh`
- `python scripts/run_external_dataset_suite.py --mode core`
- `python scripts/run_external_dataset_suite.py --mode both --api-base-url http://127.0.0.1:8088`

Она поднимает набор tiny subset-профилей из больших внешних корпусов и нужна
для проверки не только quality metrics, но и стабильности manifest/config/API
слоев на реальных данных.

Важно для reproducibility:

- relative `audio_path` в dataset manifest теперь трактуются от директории manifest-файла;
- uploaded manifest bundle теперь отвергается, если manifest ссылается на аудио,
  которого нет в самом bundle, или если basename-ы файлов конфликтуют после
  нормализации.

## 8. Entry points, которые реально важны

Для обычного использования:

- `bash scripts/run_rqt.sh`: безопасный способ открыть `rqt_topic` с правильным ROS/workspace overlay.
- Не используйте на автомате корневой `install/setup.bash`, если рядом есть актуальный `ros2_ws/install/setup.bash`: старый overlay может ломать импорт `asr_interfaces/*` и диагностику в `rqt`.
- Для ручного `ros2 topic echo` по финальным результатам используйте `--qos-durability transient_local --qos-reliability reliable`, иначе поздний подписчик после короткого file-run может не увидеть уже опубликованный финал.

- `make run`
- `./scripts/open_live_test_terminals.sh`
- `make web-gui`
- `make bench`
- `make report`
- `make arch-static`

Для полного runtime-aware archviz:

- `make arch`
- этот target теперь специально отказывается запускаться, если из того же
  workspace уже живет managed stack (`full_stack_dev`, runtime, benchmark),
  чтобы не строить смешанный runtime graph.

Для ROS launch:

- `asr_launch/runtime_minimal.launch.py`
- `asr_launch/runtime_streaming.launch.py`
- `asr_launch/gateway_with_runtime.launch.py`
- `asr_launch/full_stack_dev.launch.py`

## 9. Что считать legacy

Следующее больше не является primary architecture path:

- `asr_ros`
- `/asr/set_backend`
- `/asr/get_status`
- `/asr/text/plain`
- старые `bringup.launch.py` / `demo.launch.py` из compatibility package

Это все еще может существовать для migration/testing, но не должно быть
исходной точкой для новых запусков, docs или расширений.

## 10. Что смотреть первым при отладке

Если runtime ведет себя странно, первым делом смотри:

1. `configs/runtime/default_runtime.yaml`
2. `configs/providers/<profile>.yaml`
3. `asr_runtime_nodes/asr_orchestrator_node.py`
4. `asr_gateway/ros_client.py`
5. `docs/architecture/runtime_architecture.md`
6. `docs/interfaces/ros2_comm_map.md`

Если benchmark ведет себя странно:

1. `asr_benchmark_core/orchestrator.py`
2. `asr_metrics/engine.py`
3. `asr_reporting/*`
4. `tests/component/test_benchmark_orchestrator.py`

## 11. Operational rules of thumb

- Если нужен live pipeline, думай в терминах `launch -> start_session -> results topics`.
- Если нужен один transcript целого WAV, используй `recognize_once`.
- Если нужен browser/operator workflow, стартуй `make web-gui`.
- Если нужен reproducible experiment, используй benchmark profiles и `make bench`.
- Если сталкиваешься с cloud providers, отдельно проверяй profile validity и secret readiness.
