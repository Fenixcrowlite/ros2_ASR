# Runtime Extractor

Файл: `tools/archviz/runtime_extract.py`.

## Как снимает граф

Для каждого launch из профиля:

1. `ros2 launch ...`
2. wait timeout
3. собирает:
   - `ros2 node list`
   - `ros2 node info`
   - `ros2 topic list -t` + `topic info -v`
   - `ros2 service list -t`
4. останавливает процесс (SIGINT/kill)

## Профили

- `tools/archviz/profiles.yaml`
- `full` генерируется автоматически из найденных launch файлов.

## Выход

- `docs/arch/runtime_graph.json`
- `docs/arch/runtime_errors.md`
