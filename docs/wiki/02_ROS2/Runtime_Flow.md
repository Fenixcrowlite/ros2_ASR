# Runtime Flow

## Step-by-step

1. [[02_ROS2/Node_Audio_Capture]] публикует `UInt8MultiArray` в `/asr/audio_chunks`.
2. [[02_ROS2/Node_ASR_Server]] буферизует чанки и вызывает backend.
3. Backend возвращает `AsrResponse`.
4. Сервер публикует:
   - [[02_ROS2/Topic_Asr_Text]] (структурированный результат)
   - [[02_ROS2/Topic_Asr_Metrics]] (метрики)
5. [[02_ROS2/Node_ASR_Text_Output]] читает `/asr/text` и публикует `/asr/text/plain`.
6. Управление backend делается через:
   - [[02_ROS2/Service_Set_Backend]]
   - [[02_ROS2/Service_Get_Status]]

## Связь с launch

- [[02_ROS2/Launch_Bringup]]
- [[02_ROS2/Launch_Demo]]
- [[00_Start/Glossary#Topic asr_text_plain]]
