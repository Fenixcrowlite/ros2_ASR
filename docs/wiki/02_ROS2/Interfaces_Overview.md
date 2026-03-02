# Interfaces Overview

Источник интерфейсов: `ros2_ws/src/asr_interfaces`.

## Message types

- `AsrResult.msg` -> [[02_ROS2/Topic_Asr_Text]]
- `AsrMetrics.msg` -> [[02_ROS2/Topic_Asr_Metrics]]
- `WordTimestamp.msg` -> вложен в `AsrResult`

## Services

- `RecognizeOnce.srv` -> [[02_ROS2/Service_Recognize_Once]]
- `SetAsrBackend.srv` -> [[02_ROS2/Service_Set_Backend]]
- `GetAsrStatus.srv` -> [[02_ROS2/Service_Get_Status]]

## Action

- `Transcribe.action` -> [[02_ROS2/Action_Transcribe]]

## Интерфейсы запуска live sample eval

- `core` -> прямой backend call (без ROS transport)
- `ros_service` -> `SetAsrBackend + RecognizeOnce`
- `ros_action` -> `SetAsrBackend + Transcribe`

## Внешняя документация

- [[../../interfaces]]
- [[00_Start/Glossary#Interface core]]
