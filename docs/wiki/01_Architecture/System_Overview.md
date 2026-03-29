# System Overview

Система состоит из модулей:

1. `asr_core` — единый API и модели.
2. `asr_backend_*` — backend implementations и low-level SDK wrappers.
3. `asr_runtime_nodes` + `asr_launch` — актуальный ROS2 runtime pipeline.
4. `asr_provider_base` + `asr_provider_*` — provider adapter layer.
5. `asr_gateway` + `web_ui` — browser/gateway control plane.
6. `asr_benchmark_core` + `asr_benchmark_nodes` + `asr_reporting` — benchmark/reporting path.
7. `asr_metrics` — качество, latency, ресурсы, стоимость.
8. `tools/archviz` — автоматическая архитектурная документация.

Legacy note:

- `asr_ros` и старые `/asr/set_backend`, `/asr/get_status`, `/asr/text/plain`
  остаются только как compatibility surface.
- Новые docs и новые расширения должны опираться на modular runtime stack.

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
