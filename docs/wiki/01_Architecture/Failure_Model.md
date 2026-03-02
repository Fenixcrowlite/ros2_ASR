# Failure Model

## Типы отказов

1. Конфигурационные: отсутствуют region/keys/model paths.
2. Runtime backend: SDK/model init errors.
3. Инфраструктурные: нет ROS2 env, нет микрофона, нет GPU runtime.
4. Cloud-ограничения: auth/quota/network/timeout.

## Обработка

- Backend возвращает `success=false`, `error_code`, `error_message`.
- `asr_server_node` публикует результат даже при ошибке в унифицированной форме.
- Cloud тесты в pytest помечены `cloud` и skip без ENV.

## Где проверять

- [[02_ROS2/Topic_Asr_Text]]
- [[02_ROS2/Topic_Asr_Metrics]]
- [[09_Quality_CI/Test_Strategy]]
- [[06_Operations/Troubleshooting_Playbook]]
