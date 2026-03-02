# Runtime Backend Switch

## Механизм

Смена backend делается через сервис [[02_ROS2/Service_Set_Backend]].

## Пример

```bash
ros2 service call /asr/set_backend asr_interfaces/srv/SetAsrBackend "{backend: google, model: latest_long, region: global}"
```

## Проверка

```bash
ros2 service call /asr/get_status asr_interfaces/srv/GetAsrStatus "{}"
```

## Примечание

Смена происходит в `asr_server_node` без перезапуска launch.
