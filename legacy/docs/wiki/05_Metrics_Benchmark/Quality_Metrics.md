# Quality Metrics

Файл: `ros2_ws/src/asr_metrics/asr_metrics/quality.py`.

## Метрики

- `wer`: word error rate.
- `cer`: character error rate без пробелов после нормализации.
- `sample_accuracy`: доля сэмплов, где нормализованные reference и hypothesis совпали полностью.

## Нормализация

Перед сравнением применяется:

- `lower()`,
- схлопывание whitespace,
- удаление пунктуации и symbol noise с обеих сторон.

Это сделано, чтобы базовые benchmark-метрики отражали именно качество распознавания, а не различия форматирования вроде `Hello.` vs `hello`.

## Агрегация

- В raw rows `wer` и `cer` остаются per-sample.
- В `summary.json`, gateway results view и Markdown report `wer`/`cer` агрегируются как corpus-level rate.
- `sample_accuracy` считается только по exact normalized match и больше не выводится из `cer == 0`.

## Связанные

- [[05_Metrics_Benchmark/Metrics_Collector]]
- [[05_Metrics_Benchmark/Results_Artifacts]]
- [[02_ROS2/Topic_Asr_Metrics]]
- [[00_Start/Glossary#WER]]
- [[00_Start/Glossary#CER]]
