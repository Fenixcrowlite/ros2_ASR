# Merge Policy

Файл: `tools/archviz/merge_graph.py`.

## Анти-дыры правило

Merged graph всегда включает union static + runtime.

## State у сущностей

- `both`
- `expected_only`
- `observed_only`

## Evidence

Сохраняются источники фактов (static/runtime).

## Выход

`docs/arch/merged_graph.json`
