# Launch: bringup.launch.py

Файл: `ros2_ws/src/asr_ros/launch/bringup.launch.py`.

## Запускает

- `asr_server_node`
- `audio_capture_node`
- `asr_text_output_node` (условно, если `text_output_enabled=true`)

## Launch-аргументы

- `config` (default: `configs/default.yaml`)
- `input_mode` (default: `auto`)
- `wav_path` (default: `data/sample/en_hello.wav`)
- `sample_rate` (default: `16000`)
- `chunk_ms` (default: `800`)
- `device` (default: `""`)
- `continuous` (default: `true`)
- `mic_capture_sec` (default: `4.0`)
- `live_stream_enabled` (default: `true`)
- `live_flush_timeout_sec` (default: `1.0`)
- `text_output_enabled` (default: `true`)

## Использование

```bash
ros2 launch asr_ros bringup.launch.py config:=configs/live_mic_whisper.yaml input_mode:=mic
```

```bash
ros2 launch asr_ros bringup.launch.py config:=configs/live_mic_whisper.yaml input_mode:=mic text_output_enabled:=true
```

## Связанные страницы

- [[02_ROS2/Launch_Demo]]
- [[06_Operations/Live_Run_Playbook]]
- [[02_ROS2/Node_ASR_Text_Output]]
- [[00_Start/Glossary#Bringup]]
