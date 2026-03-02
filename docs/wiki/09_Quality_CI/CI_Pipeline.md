# CI Pipeline

Файл: `.github/workflows/ci.yml`.

## Шаги

1. checkout
2. Python 3.12
3. `pip install -r requirements.txt`
4. `ruff check .`
5. `pytest -m "not cloud and not ros" -q`

## Почему так

CI остаётся быстрым и предсказуемым:

- без cloud затрат,
- без ROS runtime в CI контуре.
