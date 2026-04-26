# Archviz CLI Commands

```bash
archviz static --ws ros2_ws --out docs/arch
archviz runtime --ws ros2_ws --out docs/arch --profile full --timeout-sec 20
archviz merge --static docs/arch/static_graph.json --runtime docs/arch/runtime_graph.json --out docs/arch/merged_graph.json
archviz render --in docs/arch/merged_graph.json --out docs/arch --format mermaid
archviz diff --a docs/arch/merged_graph_prev.json --b docs/arch/merged_graph.json --out docs/arch/CHANGELOG_ARCH.md
archviz all --ws ros2_ws --out docs/arch --profile full --timeout-sec 20
```

Важно:

- `archviz runtime` и `archviz all` теперь завершаются с non-zero exit code,
  если из того же workspace уже живет managed stack;
- это intentional guardrail против смешанного runtime graph.

## Эквиваленты в Makefile

- `make arch-static`
- `make arch-runtime`
- `make arch`
- `make arch-diff`
