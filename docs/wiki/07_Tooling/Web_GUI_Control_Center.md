# Web GUI Control Center

Note:
- The only active browser control plane is `web_ui` served by `asr_gateway`.
- The historical `web_gui/` implementation has been removed from the repository.

Пути:

- `web_ui/README.md`
- `ros2_ws/src/asr_gateway/asr_gateway/api.py`
- запуск: `scripts/run_web_ui.sh`

## Назначение

Единый gateway-first web-интерфейс для:

- управления runtime session,
- работы с providers/profiles/datasets,
- запуска benchmark runs,
- просмотра results/logs/diagnostics,
- credentials workflows (`AWS SSO`, `Google JSON`, `Azure env`),
- runtime sample upload и генерации noisy WAV.

## Запуск

```bash
make web-gui
```

Для LAN:

```bash
make web-gui-lan
```

URL по умолчанию: `http://localhost:8088`.

## Минимальный сценарий работы

1. Открыть `http://localhost:8088`.
2. Перейти в `Logs & Diagnostics` и выполнить `Run Preflight`.
3. В `Runtime` выбрать runtime/provider profile и при необходимости загрузить WAV.
4. Для live pipeline нажать `Start Live Runtime`, а для одной транскрипции целого WAV нажать `Transcribe Whole File`.
5. Для сравнений перейти в `Benchmark`, собрать run и следить за статусом на этой же странице.

## Что происходит в новом UI

1. Frontend обращается к `asr_gateway` (`/api/runtime/*`, `/api/benchmark/*`, `/api/results/*`, `/api/secrets/*`).
2. Gateway валидирует profiles / secret refs и проксирует вызовы в ROS/service-action слой.
3. Runtime и benchmark артефакты читаются из `artifacts/`.
4. `Runtime` страница ведёт каталог project WAV samples в `data/sample/`, включая `uploads/` и `generated_noise/`.

## Артефакты

- runtime sessions: `artifacts/runtime_sessions/<session_id>/...`
- benchmark runs: `artifacts/benchmark_runs/<run_id>/...`
- exports: `artifacts/exports/...`
- uploaded samples: `data/sample/uploads/...`
- generated noisy samples: `data/sample/generated_noise/...`

## Важные термины

- [[00_Start/Glossary#Runtime Config]]
- [[00_Start/Glossary#Language Mode]]
- [[00_Start/Glossary#Preflight]]
