# Web GUI Control Center

Пути:

- `web_gui/README.md`
- `web_gui/app/main.py`
- запуск: `web_gui/run_web_gui.sh`

## Назначение

Единый web-интерфейс для:

- настройки runtime (языки, модели, backend параметры, cloud secrets),
- live sample eval (микрофон или свой WAV),
- benchmark run (dataset/scenarios/metrics),
- ROS2 bringup start/stop,
- просмотра jobs/logs/artifacts.

## Запуск

```bash
make web-gui
```

или

```bash
bash web_gui/run_web_gui.sh
```

URL по умолчанию: `http://localhost:8765`.

## Минимальный сценарий работы

1. Нажать `Preflight` и убедиться, что `sounddevice/soundfile/ROS` отмечены как `ok`.
2. Выбрать `Base config` и заполнить runtime поля.
3. Для live запуска выбрать `interfaces`, `model runs`, `language mode` и (опционально) `use WAV`.
4. Нажать `Run Live Sample Eval` или `Run Benchmark` / `Start ROS Bringup`.
5. Смотреть статус в таблице Jobs, затем открыть Logs и Artifacts.

## Что происходит с runtime setup

1. Frontend отправляет payload в API `/api/jobs/*`.
2. `config_builder.build_runtime_config(...)`:
   - грузит base config,
   - применяет runtime overrides,
   - инжектит secrets,
   - пишет итоговый YAML в `web_gui/runtime_configs/<timestamp>_<profile>.yaml`.
3. `command_builder` собирает команду запуска:
   - live: `python3 scripts/live_sample_eval.py --config <runtime.yaml> ...`
   - benchmark: `python3 -m asr_benchmark.runner --config <runtime.yaml> ...`
   - bringup: `ros2 launch asr_ros bringup.launch.py config:=<runtime.yaml> ...`
4. `job_manager` стартует subprocess, передает env secrets, пишет лог в `web_gui/logs/*.log`.
5. Конечный потребитель runtime-конфига:
   - `asr_server_node` (через launch `config:=...`),
   - `live_sample_eval.py` (прямой `--config`),
   - `asr_benchmark.runner` (прямой `--config`).

## Артефакты

- runtime configs: `web_gui/runtime_configs/*.yaml`
- логи jobs: `web_gui/logs/*.log`
- live artifacts: `results/web_gui/live_sample/<timestamp>/...`
- benchmark artifacts: `results/web_gui/benchmark/<timestamp>/...`

## Важные термины

- [[00_Start/Glossary#Runtime Config]]
- [[00_Start/Glossary#Language Mode]]
- [[00_Start/Glossary#Model Run Spec]]
- [[00_Start/Glossary#Preflight]]
- [[00_Start/Glossary#Job]]
