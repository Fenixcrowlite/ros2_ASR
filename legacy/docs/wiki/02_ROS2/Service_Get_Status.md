# Service: /asr/get_status

Тип: `asr_interfaces/srv/GetAsrStatus`.

## Возвращает

- текущие `backend/model/region`
- `capabilities[]`
- `streaming_supported`
- `cloud_credentials_available`

## Пример

```bash
ros2 service call /asr/get_status asr_interfaces/srv/GetAsrStatus "{}"
```

## Связанные

- [[04_Backends/Capabilities_Matrix]]
- [[02_ROS2/Service_Set_Backend]]
