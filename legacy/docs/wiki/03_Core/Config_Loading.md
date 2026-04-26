# Config Loading

Файл: `ros2_ws/src/asr_core/asr_core/config.py`.

## Механика

`load_runtime_config(default, commercial)` сливает:

1. default yaml,
2. optional commercial overlay,
3. `configs/commercial.yaml` если существует.

## ENV precedence

`env_or(...)`: ENV выше config.

## Связанные

- [[08_Data_Configs/Configs_Overview]]
- [[04_Backends/Secrets_And_ENV]]
