# Live Run Playbook

## Вариант A: автоскрипт (рекомендуется)

```bash
./scripts/open_live_test_terminals.sh
```

## Вариант B: вручную

1. Запусти [[02_ROS2/Launch_Bringup]].
2. В отдельном терминале читай plain-text:

```bash
ros2 topic echo /asr/text/plain --qos-durability transient_local --qos-reliability reliable
```

3. При необходимости смотри структурированный результат:

```bash
ros2 topic echo /asr/text --qos-durability transient_local --qos-reliability reliable
```

## Проверка статуса backend

```bash
ros2 service call /asr/get_status asr_interfaces/srv/GetAsrStatus "{}"
```

## Связанные

- [[02_ROS2/Topic_Asr_Text]]
- [[04_Backends/Runtime_Backend_Switch]]
- [[02_ROS2/Node_ASR_Text_Output]]
- [[00_Start/Glossary#QoS transient_local]]
