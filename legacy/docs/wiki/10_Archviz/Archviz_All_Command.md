# Archviz All Command

## Рекомендуемый путь

```bash
make build
make arch
```

`make arch` теперь fail-fast, если из этого же workspace уже запущен другой
managed stack. Сначала остановите `make web-gui`, `full_stack_dev.launch.py`
или другой живой runtime/gateway/benchmark stack, иначе runtime graph будет
смешанным и недостоверным.

## Ручной путь

```bash
source .venv/bin/activate
archviz all --ws ros2_ws --out docs/arch --profile full --timeout-sec 20
```

## Проверка

Ожидаемые файлы:

- `docs/arch/static_graph.json`
- `docs/arch/runtime_graph.json`
- `docs/arch/merged_graph.json`
- `docs/arch/mindmap.mmd`
- `docs/arch/flow.mmd`
- `docs/arch/seq_recognize_once.mmd`
- `docs/arch/CHANGELOG_ARCH.md`
