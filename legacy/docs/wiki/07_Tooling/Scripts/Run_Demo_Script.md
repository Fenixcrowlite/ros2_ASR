# Script: run_demo.sh

Путь: `scripts/run_demo.sh`.

## Назначение

- source ROS2,
- build workspace,
- source install,
- запустить `ros2 launch asr_launch runtime_minimal.launch.py`.
- перед build/launch fail-fast проверить, не запущен ли уже другой managed ASR stack из этого же workspace.

## Использование

```bash
bash scripts/run_demo.sh
```

Если уже поднят `run_web_ui.sh` или другой managed stack из этого repo, скрипт теперь
останавливается сразу с явной ошибкой и списком конфликтующих PID, не тратя время на
лишний `colcon build`.

## Связанные

- [[02_ROS2/Launch_Demo]]
- [[06_Operations/Live_Run_Playbook]]
