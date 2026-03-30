# Script: run_benchmarks.sh

Путь: `scripts/run_benchmarks.sh`.

## Назначение

- build,
- запуск canonical benchmark core через `scripts/run_benchmark_core.py`,
- генерация canonical run folder в `artifacts/benchmark_runs/<run_id>/...`,
- генерация compatibility `results/*.json`, `results/*.csv`, `results/plots/*.png`,
- публикация `results/latest_benchmark_summary.json`.

## Использование

```bash
bash scripts/run_benchmarks.sh
```

## Связанные

- [[05_Metrics_Benchmark/Benchmark_Runner]]
- [[05_Metrics_Benchmark/Results_Artifacts]]
