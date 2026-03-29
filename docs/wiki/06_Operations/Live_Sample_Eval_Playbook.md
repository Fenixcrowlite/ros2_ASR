# Live Sample Eval Playbook

## Цель

Записать один live-семпл и сравнить результат по разным интерфейсам/бэкендам с метриками.

## Команда

```bash
bash scripts/run_live_sample_eval.sh
```

Интерактивный запуск:

- записывает live-семпл,
- затем предлагает выбрать `manual/auto/config` язык,
- затем позволяет задать прогоны по моделям (`backend[:model][@region]`).

Пример non-interactive:

```bash
bash scripts/run_live_sample_eval.sh \
  --interfaces core,ros_service,ros_action \
  --model-runs whisper:tiny,whisper:large-v3,mock \
  --language-mode auto \
  --ros-auto-launch \
  --reference-text "hello world"
```

## Подход

- один и тот же WAV для всех прогонов,
- сравнимые latency/RTF/ресурсы,
- единый output format (CSV/JSON/plots).

## Пререквизиты

- В `.venv` должны быть `sounddevice` + `soundfile` (для записи с микрофона).
- Для `language_mode=auto` обязателен рабочий `faster-whisper`; silent fallback к config-языку больше не используется.
- Для ROS интерфейсов (`ros_service`, `ros_action`) нужен собранный workspace.
- `ros_action --action-streaming` допустим только для streaming-capable backend’ов. Для Whisper и других batch-only backend’ов сценарий теперь отвергается до запуска.

## Когда использовать

- быстрый ручной A/B интерфейсов,
- демонстрация комиссии,
- smoke-проверка backend после изменений.

## Связанные

- [[07_Tooling/Scripts/Live_Sample_Eval_Script]]
- [[05_Metrics_Benchmark/Results_Artifacts]]
- [[00_Start/Glossary#Language Mode]]
- [[00_Start/Glossary#Model Run Spec]]
