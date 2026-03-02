# Script: live_sample_eval.py

Пути:

- `scripts/live_sample_eval.py`
- wrapper: `scripts/run_live_sample_eval.sh`

## Назначение

1. Записать live-семпл с микрофона.
2. После записи (в interactive режиме) выбрать:
   - режим языка `manual/auto/config`;
   - набор прогонов `backend[:model][@region]`.
3. Прогнать этот же WAV по выбранным интерфейсам:
   - `core`
   - `ros_service`
   - `ros_action`
4. Собрать метрики и артефакты (CSV/JSON/plots + summary).

## Зависимости

- Для записи с микрофона: `sounddevice` и `soundfile`.
- Для `language-mode=auto`: `faster-whisper`.
- Для ROS интерфейсов: собранный `install/setup.bash`.

## Пример

```bash
bash scripts/run_live_sample_eval.sh
```

```bash
bash scripts/run_live_sample_eval.sh \
  --interfaces core,ros_service,ros_action \
  --model-runs whisper:tiny,whisper:large-v3,mock \
  --language-mode auto \
  --ros-auto-launch \
  --reference-text "hello world"
```

## Выход

`results/live_sample/<timestamp>/`:

- `live_sample.wav`
- `live_results.csv`
- `live_results.json`
- `summary.md`
- `plots/*.png`

## Связанные

- [[06_Operations/Live_Run_Playbook]]
- [[05_Metrics_Benchmark/Metrics_Collector]]
- [[02_ROS2/Service_Recognize_Once]]
- [[02_ROS2/Action_Transcribe]]
- [[00_Start/Glossary#Language Mode]]
