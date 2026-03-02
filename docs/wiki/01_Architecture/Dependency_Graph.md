# Dependency Graph

## В направлении исполнения

`audio_capture_node` -> `/asr/audio_chunks` -> `asr_server_node` -> backend

`asr_server_node` -> `/asr/text` + `/asr/metrics`

`asr_text_output_node` читает `/asr/text` и публикует `/asr/text/plain`

## В направлении кода

- `asr_ros` зависит от `asr_core`, `asr_interfaces`, `asr_metrics`.
- Backend пакеты зависят от `asr_core`.
- `asr_benchmark` зависит от `asr_core` и `asr_metrics`.
- `tools/archviz` зависит только от stdlib (и опционально yaml из окружения).

## Смежные страницы

- [[03_Core/Core_Index]]
- [[02_ROS2/ROS2_Index]]
- [[05_Metrics_Benchmark/Metrics_Benchmark_Index]]
- [[02_ROS2/Node_ASR_Text_Output]]
- [[00_Start/Glossary#Topic asr_text_plain]]
