# Script: generate_report.py

Путь: `scripts/generate_report.py`.

## Назначение

Генерирует `results/report.md` из benchmark JSON.
При ошибке во входном пути завершает работу с явным сообщением, а не Python traceback.

## Использование

```bash
python scripts/generate_report.py --input results/benchmark_results.json --output results/report.md
```

Соседние helper’ы:

- `python scripts/generate_plots.py --input-json results/benchmark_results.json --output-dir results/plots`
- `python scripts/export_reports/export_run_summary.py --summary-json /path/to/summary.json --output-md /path/to/summary.md`

## Связанные

- [[05_Metrics_Benchmark/Results_Artifacts]]
