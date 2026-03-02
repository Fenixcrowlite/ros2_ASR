# Node: asr_text_output_node

Файл: `ros2_ws/src/asr_ros/asr_ros/asr_text_output_node.py`.

## Роль

- Подписывается на структурированный топик `/asr/text`.
- Публикует plain-text в `/asr/text/plain`.
- Нужна как отдельная нода для удобного потребления текста в CLI/GUI.

## Параметры

- `input_topic` (default: `/asr/text`)
- `output_topic` (default: `/asr/text/plain`)
- `final_only` (default: `true`)
- `publish_errors_as_text` (default: `true`)

## Запуск

По умолчанию стартует из [[02_ROS2/Launch_Bringup]] если `text_output_enabled=true`.

## Проверка

```bash
ros2 node list | grep asr_text_output_node
```

```bash
ros2 topic echo /asr/text/plain --qos-durability transient_local --qos-reliability reliable
```

## Связанные

- [[02_ROS2/Topic_Asr_Text]]
- [[02_ROS2/Launch_Bringup]]
- [[00_Start/Glossary#Node asr_text_output_node]]
