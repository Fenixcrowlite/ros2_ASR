# Node: asr_server_node

Файл: `ros2_ws/src/asr_ros/asr_ros/asr_server_node.py`.

## Роль

- Экспортирует сервисы и action.
- Подписывается на `/asr/audio_chunks`.
- Публикует структурированный результат в `/asr/text`.
- Публикует метрики в `/asr/metrics`.
- Plain-text канал `/asr/text/plain` формируется отдельной нодой [[02_ROS2/Node_ASR_Text_Output]].
- Создаёт backend через фабрику [[03_Core/Backend_Factory]].

## Ключевые параметры

- `config`
- `backend`
- `language`
- `model`
- `region`
- `sample_rate`
- `live_stream_enabled`
- `live_flush_timeout_sec`

## Экспортируемые интерфейсы

- [[02_ROS2/Service_Recognize_Once]]
- [[02_ROS2/Service_Set_Backend]]
- [[02_ROS2/Service_Get_Status]]
- [[02_ROS2/Action_Transcribe]]
- [[02_ROS2/Topic_Asr_Text]]
- [[02_ROS2/Topic_Asr_Metrics]]
- [[00_Start/Glossary#Backend]]
