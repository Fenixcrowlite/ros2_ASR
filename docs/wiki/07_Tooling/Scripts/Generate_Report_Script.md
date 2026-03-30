# Script: generate_report.py

Путь: `scripts/generate_report.py`.

## Назначение

Генерирует `results/report.md` из benchmark JSON.
При ошибке во входном пути завершает работу с явным сообщением, а не Python traceback.
Для legacy flat export в aggregate table использует corpus-level `WER`/`CER`, а не среднее per-row значений.
Также умеет читать canonical `summary.json` из benchmark core.

## Использование

```bash
python scripts/generate_report.py --input results/latest_benchmark_summary.json --output results/report.md
```

Соседние helper’ы:

- `python scripts/generate_plots.py --input-json results/benchmark_results.json --output-dir results/plots`
- `python scripts/export_reports/export_run_summary.py --summary-json /path/to/summary.json --output-md /path/to/summary.md`

`generate_report.py` ищет plot images относительно директории входного JSON:

- `results/latest_benchmark_summary.json` -> `results/plots/*.png`
- `results/benchmark_results.json` -> `results/plots/*.png`
- `/tmp/run/results.json` -> `/tmp/run/plots/*.png`

## Связанные

- [[05_Metrics_Benchmark/Results_Artifacts]]
