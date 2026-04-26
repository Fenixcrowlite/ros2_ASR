# Static Extractor

Файл: `tools/archviz/static_extract.py`.

## Источники

- `package.xml` (имя пакета и deps)
- `setup.py` / `setup.cfg` (console_scripts)
- `launch/*.launch.py` (Node specs)
- `msg/srv/action`
- AST Python (`create_publisher/subscription/service/client/timer`)

## Evidence tags

- `static_package`
- `static_launch`
- `static_interfaces`
- `static_ast`

## Выход

`docs/arch/static_graph.json`
