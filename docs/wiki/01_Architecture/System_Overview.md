# System Overview

Система состоит из модулей:

1. `asr_core` — единый API и модели.
2. `asr_backend_*` — конкретные реализации STT.
3. `asr_ros` — ROS2-ноды и интерфейсы исполнения.
4. `asr_metrics` — качество, latency, ресурсы, стоимость.
5. `asr_benchmark` — сценарии и отчётные артефакты.
6. `tools/archviz` — автоматическая архитектурная документация.

## Цели архитектуры

- смена backend без правки кода,
- единая нормализация ответа,
- воспроизводимые метрики,
- наблюдаемость через ROS topics/services,
- безопасная работа с cloud credentials.

## Дальше

- [[01_Architecture/Layered_Architecture]]
- [[03_Core/Core_Index]]
- [[04_Backends/Backends_Index]]
