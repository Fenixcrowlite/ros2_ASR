# Benchmark Runner

Файл: `ros2_ws/src/asr_benchmark/asr_benchmark/runner.py`.

## Цикл исполнения

1. Загружает config и dataset.
2. Создаёт backend через [[03_Core/Backend_Factory]].
3. Прогоняет сценарии (`clean`, `snr*`, `streaming_sim`).
4. Сохраняет `JSON`, `CSV`, `plots`.

## Запуск

```bash
make bench
```

## Связанные

- [[05_Metrics_Benchmark/Dataset_And_Scenarios]]
- [[05_Metrics_Benchmark/Results_Artifacts]]
