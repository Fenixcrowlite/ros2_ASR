# Launch: demo.launch.py

Файл: `ros2_ws/src/asr_ros/launch/demo.launch.py`.

## Что делает

Тонкий wrapper над [[02_ROS2/Launch_Bringup]] с аргументом `config`.

По цепочке также доступен plain-text канал `/asr/text/plain` через [[02_ROS2/Node_ASR_Text_Output]].

## Использование

```bash
ros2 launch asr_ros demo.launch.py config:=configs/default.yaml
```
