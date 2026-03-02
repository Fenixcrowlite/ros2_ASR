# Topic: /asr/text

Тип: `asr_interfaces/msg/AsrResult`.

Связанный plain-text канал: `/asr/text/plain` (тип `std_msgs/msg/String`),
его публикует отдельная нода [[02_ROS2/Node_ASR_Text_Output]].

## Содержимое

- `text`
- `confidence`
- `word_timestamps`
- `backend/model/region`
- timing breakdown
- `success/error_code/error_message`

## Команда просмотра

```bash
ros2 topic echo /asr/text --qos-durability transient_local --qos-reliability reliable
```

Для терминала/GUI обычно удобнее plain-text поток:

```bash
ros2 topic echo /asr/text/plain --qos-durability transient_local --qos-reliability reliable
```

## Связанные

- [[02_ROS2/Service_Recognize_Once]]
- [[02_ROS2/Action_Transcribe]]
- [[02_ROS2/Node_ASR_Text_Output]]
- [[00_Start/Glossary#Topic asr_text]]
- [[00_Start/Glossary#Topic asr_text_plain]]
