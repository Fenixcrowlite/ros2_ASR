# Makefile Targets

Основные цели:

- `make setup`
- `make build`
- `make test-unit`
- `make test-ros`
- `make test-colcon`
- `make test`
- `make run`
- `make bench`
- `make report`
- `make arch-static`
- `make arch-runtime`
- `make arch`
- `make arch-diff`
- `make clean`
- `make dist`

Примечание по archviz:

- `make arch-static` всегда безопасен как purely static extractor;
- `make arch-runtime` и `make arch` теперь fail-fast, если уже запущен другой
  managed stack из того же workspace.

См. исходник: `Makefile`.
