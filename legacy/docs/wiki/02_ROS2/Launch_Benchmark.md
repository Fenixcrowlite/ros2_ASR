# Launch: benchmark.launch.py

Есть в двух пакетах:

- `asr_ros/launch/benchmark.launch.py`
- `asr_benchmark/launch/benchmark.launch.py`

Обе версии поднимают `asr_benchmark_node`.

## Аргументы

- `config`
- `dataset`

## Использование

```bash
ros2 launch asr_ros benchmark.launch.py config:=configs/default.yaml dataset:=data/transcripts/sample_manifest.csv
```
