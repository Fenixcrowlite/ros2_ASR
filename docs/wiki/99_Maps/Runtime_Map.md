# Runtime Map

## Главный поток

1. [[02_ROS2/Node_Audio_Capture]] -> публикует `/asr/audio_chunks`
2. [[02_ROS2/Node_ASR_Server]] -> читает чанки, вызывает backend
3. [[04_Backends/Backends_Index]] -> распознавание
4. [[02_ROS2/Topic_Asr_Text]] -> структурированный результат
5. [[02_ROS2/Node_ASR_Text_Output]] -> plain-text `/asr/text/plain`
6. [[02_ROS2/Topic_Asr_Metrics]] -> телеметрия

## Управление

- [[02_ROS2/Service_Recognize_Once]]
- [[02_ROS2/Service_Set_Backend]]
- [[02_ROS2/Service_Get_Status]]
- [[02_ROS2/Action_Transcribe]]

## Где смотреть фактическую топологию

- [[10_Archviz/Static_Extractor]]
- [[10_Archviz/Runtime_Extractor]]
- [[10_Archviz/Merge_Policy]]
- [[00_Start/Glossary#Topic asr_text_plain]]
- [[99_Maps/File_Flows_Mermaid]]
