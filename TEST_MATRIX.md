# TEST_MATRIX

| Компонент | Что проверяется | Тип теста | Позитивный сценарий | Негативный сценарий | Edge-case | Статус |
|---|---|---|---|---|---|---|
| `web_gui/app/main.py` | Cloud auth fail-fast (google/azure/aws) | Unit | Валидные параметры проходят | Неполные/отсутствующие credentials -> `HTTP 400` | Явный `model_runs=mock` при cloud default backend не триггерит cloud auth | Covered |
| `web_gui/app/main.py` | Google credential file integrity | Unit | Валидный JSON object проходит | Битый JSON -> `HTTP 400` | Нечитаемый файл -> `HTTP 400` | Covered |
| `web_gui/app/main.py` | AWS STS preflight selection and cache | Unit | boto3-path выполняется; success-cache reuse в пределах TTL | boto3 недоступен -> CLI fallback | Нормализация SSO expired/invalid grant/token-missing сообщений | Covered |
| `web_gui/app/aws_auth_store.py` | SSO/access-key auth contract | Unit | Полный SSO профиль создает runtime env | Нет account/role в runtime SSO -> `ValueError` | `for_login=True` допускает partial SSO профиль | Covered |
| `web_gui/app/job_manager.py` | Stop/termination observability + restored visibility rule | Unit | Stop корректно завершает job; active restored job остается видимым | Wait timeout фиксируется в `job.error` | Неактивный restored job скрывается при `hide_inactive_restored=true` | Covered |
| `asr_backend_aws/backend.py` | Cleanup + error-code semantics | Unit | Успешный путь выполняет cleanup | Upload fail не вызывает delete_object | SSO token missing/expired -> отдельные коды | Covered |
| `asr_benchmark/dataset.py` | Dataset path reproducibility | Unit | Relative WAV из manifest dir резолвится | Missing WAV -> ошибка | CWD collision не перебивает manifest path | Covered |
| `asr_benchmark/runner.py` | Scenario normalization/validation | Unit | List/CSV scenarios нормализуются | Некорректный type/label -> `ValueError` | `clean,snr20,snr10` в YAML string | Covered |
| `asr_ros/shutdown.py` + ROS nodes | Graceful shutdown on stop/Ctrl+C | Unit + runtime | destroy+shutdown в корректном порядке | Double shutdown race не падает | Unexpected runtime error не скрывается | Covered |
| ROS integration (`tests/integration`) | `/asr/recognize_once` E2E | Integration (ROS) | Service call success path | Missing WAV returns error result | Runtime backend switch + status service | Covered |
| Packaging/quality gates | Lint/type/tests/release smoke | Static + runtime | `make lint`, `make test-*`, `release_check` pass | Regression breaks gate | colcon desktop notify now suppressed | Covered |
| Colcon orchestration (`scripts/with_colcon_lock.sh`, `Makefile`, run scripts) | Взаимное влияние параллельных сценариев build/test/demo/bench | Unit + runtime | lock-wrapper подключен во всех callsites | Без lock возможны race-конфликты build-dir | Одновременный старт test-таргетов не ломает последовательный pipeline | Covered |
| Web GUI frontend state (`web_gui/static/app.js`) | Persist/restore draft + archived jobs UX | Runtime smoke | После рестарта GUI поля формы восстанавливаются; активные jobs остаются в основной таблице | Битый draft JSON в localStorage игнорируется | Неактивные restored jobs уходят в раскрываемый dropdown и доступны для логов | Partially covered (runtime/manual) |
