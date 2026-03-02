# Test Strategy

## Unit tests

Маркер: `not ros`.

Покрытие:

- core,
- backends,
- metrics,
- benchmark,
- archviz.

## ROS integration tests

Маркер: `ros`.

## Cloud tests

Маркер: `cloud`, запускаются только с credentials.

## Команды

- `make test-unit`
- `make test-ros`
- `make test-colcon`
