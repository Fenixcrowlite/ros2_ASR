# Service: /asr/set_backend

Тип: `asr_interfaces/srv/SetAsrBackend`.

## Request

- `backend`
- `model`
- `region`

## Response

- `success`
- `message`

## Пример

```bash
ros2 service call /asr/set_backend asr_interfaces/srv/SetAsrBackend "{backend: whisper, model: large-v3, region: local}"
```

## Связанные

- [[04_Backends/Backends_Index]]
- [[02_ROS2/Service_Get_Status]]
