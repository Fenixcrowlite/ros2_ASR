const state = {
  options: null,
  files: null,
  selectedJobId: null,
};

const $ = (id) => document.getElementById(id);

const DOCS = {
  guiReadme: { label: "Web GUI README", path: "web_gui/README.md" },
  runGuide: { label: "Run Guide", path: "docs/run_guide.md" },
  guiWiki: {
    label: "Wiki: Web GUI Control Center",
    path: "docs/wiki/07_Tooling/Web_GUI_Control_Center.md",
  },
  liveScript: {
    label: "Wiki: Live Sample Eval Script",
    path: "docs/wiki/07_Tooling/Scripts/Live_Sample_Eval_Script.md",
  },
  benchmarkWiki: {
    label: "Wiki: Benchmark Runner",
    path: "docs/wiki/05_Metrics_Benchmark/Benchmark_Runner.md",
  },
  bringupWiki: {
    label: "Wiki: Launch Bringup",
    path: "docs/wiki/02_ROS2/Launch_Bringup.md",
  },
  backendsWiki: {
    label: "Wiki: Backends Index",
    path: "docs/wiki/04_Backends/Backends_Index.md",
  },
  secretsWiki: {
    label: "Wiki: Secrets and ENV",
    path: "docs/wiki/04_Backends/Secrets_And_ENV.md",
  },
  defaultConfig: {
    label: "Wiki: Default Config",
    path: "docs/wiki/08_Data_Configs/Default_Config.md",
  },
  liveConfig: {
    label: "Wiki: Live Mic Whisper Config",
    path: "docs/wiki/08_Data_Configs/Live_Mic_Whisper_Config.md",
  },
};

const docs = (...keys) => keys.map((key) => DOCS[key]).filter(Boolean);
const docUrl = (path) => `/api/artifacts?path=${encodeURIComponent(path)}`;

const HELP_CONTENT = {
  section_runtime_setup: {
    title: "Runtime Setup",
    summary: "Блок базовых настроек запуска и профилей.",
    what: "Здесь выбирается базовый YAML и формируются runtime overrides, которые затем пишутся в отдельный runtime-config под каждый запуск.",
    how: "Сначала выберите Base config, затем заполните нужные поля и сохраните профиль. Секреты в профиль не сохраняются.",
    links: docs("guiReadme", "defaultConfig", "liveConfig"),
  },
  section_asr_global: {
    title: "ASR Global",
    summary: "Глобальные параметры ASR для runtime-config.",
    what: "Поля влияют на asr.backend, язык, sample_rate, chunk_ms и input_mode.",
    how: "Для стабильного старта оставьте sample_rate=16000 и chunk_ms=800, backend выберите под ваш сценарий.",
    links: docs("backendsWiki", "defaultConfig"),
  },
  section_interfaces_model_runs: {
    title: "Interfaces & Model Runs",
    summary: "Выбор интерфейсов и комбинаций backend/model/region.",
    what: "Live eval прогоняет выбранные интерфейсы по каждому target из поля model-runs.",
    how: "Формат model-runs: backend[:model][@region], например whisper:tiny,mock,google:latest_long@global.",
    links: docs("liveScript", "backendsWiki"),
  },
  section_backend_details: {
    title: "Backend Details",
    summary: "Тонкие параметры backend-ов.",
    what: "Поля пишутся в runtime-config в секцию backends.*.",
    how: "Если используете только mock или один backend, остальные поля можно оставить по умолчанию.",
    links: docs("backendsWiki", "defaultConfig"),
  },
  section_cloud_auth: {
    title: "Cloud Auth",
    summary: "Секреты облачных провайдеров.",
    what: "Секреты инжектятся в runtime-config и в env конкретного job.",
    how: "Заполняйте только те поля, которые нужны вашему backend. После запуска проверьте статус/логи job.",
    links: docs("secretsWiki", "backendsWiki"),
  },
  section_benchmark_controls: {
    title: "Benchmark Controls",
    summary: "Параметры benchmark запуска.",
    what: "Dataset/backends идут в benchmark команду, scenarios/chunk_sec пишутся в runtime-config.",
    how: "Укажите существующий CSV dataset и список backend-ов через запятую.",
    links: docs("benchmarkWiki", "runGuide"),
  },
  section_samples_noise_runs: {
    title: "Samples, Noise, Runs",
    summary: "Работа с файлами, шумами и запуском задач.",
    what: "Отсюда запускаются upload, noise generation, live eval, benchmark и ROS bringup.",
    how: "Следите за jobs/logs после каждого запуска: команды работают асинхронно в фоне.",
    links: docs("guiReadme", "runGuide"),
  },
  section_upload: {
    title: "Upload",
    summary: "Загрузка WAV/CSV/YAML и других вспомогательных файлов.",
    what: "Файлы сохраняются в web_gui/uploads и становятся доступны в выпадающих списках.",
    how: "Загрузите WAV для live/noise или CSV для benchmark.",
    links: docs("guiReadme"),
  },
  section_noise_overlay: {
    title: "Noise Overlay",
    summary: "Генерация noisy WAV по SNR.",
    what: "Из source WAV создаются копии с разными уровнями шума.",
    how: "Введите SNR через запятую, например 30,20,10,0.",
    links: docs("benchmarkWiki", "guiReadme"),
  },
  section_live_run: {
    title: "Live Run",
    summary: "Запуск scripts/live_sample_eval.py через GUI.",
    what: "Можно записать микрофон или использовать готовый WAV, прогнать через core/ros_service/ros_action.",
    how: "Если выбран ros_service/ros_action, включите ROS auto launch или запустите bringup вручную.",
    links: docs("liveScript", "runGuide"),
  },
  section_ros2_bringup: {
    title: "ROS2 Bringup",
    summary: "Запуск ros2 launch asr_ros bringup.launch.py.",
    what: "Поднимается runtime ASR pipeline: server, audio_capture и опционально text_output node.",
    how: "Для input_mode=file выберите WAV. Перед запуском нужен make build (install/setup.bash).",
    links: docs("bringupWiki", "runGuide"),
  },
  section_jobs: {
    title: "Jobs",
    summary: "Мониторинг фоновых процессов.",
    what: "Каждый запуск создаёт job с id, статусом, логом и артефактами.",
    how: "Клик по строке выбирает job, кнопка Stop останавливает running процесс.",
    links: docs("guiReadme"),
  },
  section_logs: {
    title: "Logs",
    summary: "Хвост лога выбранного job.",
    what: "Логи автоматически обновляются при автополлинге (каждые 3 секунды).",
    how: "Если запуск не удался, сначала смотрите последние строки здесь.",
    links: docs("runGuide"),
  },
  section_artifacts: {
    title: "Artifacts",
    summary: "Результаты запусков: CSV/JSON/MD/PNG/WAV.",
    what: "Ссылки открывают файл через API, PNG можно просмотреть в превью.",
    how: "Для benchmark смотрите report.md и plots; для live — summary.md и live_results.*.",
    links: docs("benchmarkWiki", "liveScript"),
  },
  run_preflight: {
    title: "Кнопка Preflight",
    summary: "Проверяет готовность окружения перед запуском задач.",
    what: "Проверяются зависимости Python, микрофон, ROS setup/build и исполняемые файлы.",
    how: "Нажмите перед первыми запусками после изменений окружения.",
    links: docs("runGuide", "guiReadme"),
  },
  refresh_all: {
    title: "Кнопка Refresh",
    summary: "Ручное обновление файлов, jobs, логов и артефактов.",
    what: "Эквивалентно принудительному refresh текущего состояния backend API.",
    how: "Используйте, если хотите сразу подтянуть изменения без ожидания автополлинга.",
    links: docs("guiReadme"),
  },
  profile_name: {
    title: "Поле Profile name",
    summary: "Имя профиля и суффикс runtime-конфига.",
    what: "Используется при Save/Load Profile и при имени runtime YAML.",
    how: "Пишите коротко и понятно: например lab_ru_whisper.",
    links: docs("guiReadme"),
  },
  base_config: {
    title: "Поле Base config",
    summary: "Базовый YAML для merge runtime-config.",
    what: "Выбранный файл загружается как основа, затем накладываются overrides.",
    how: "Для универсального старта берите configs/default.yaml; для live mic — live_mic_whisper.",
    links: docs("defaultConfig", "liveConfig"),
  },
  save_profile: {
    title: "Кнопка Save Profile",
    summary: "Сохраняет текущую форму в web_gui/profiles/*.yaml.",
    what: "Сохраняются runtime_overrides и payload, но не секреты.",
    how: "Задайте Profile name и нажмите кнопку.",
    links: docs("guiReadme"),
  },
  load_profile: {
    title: "Кнопка Load Profile",
    summary: "Загружает профиль по имени в форму.",
    what: "Применяются сохранённые поля runtime/payload.",
    how: "Сначала введите Profile name существующего профиля.",
    links: docs("guiReadme"),
  },
  asr_backend: {
    title: "Поле Backend",
    summary: "Backend по умолчанию в runtime-config.",
    what: "Доступно: mock, vosk, whisper, google, aws, azure.",
    how: "Выберите backend, если не переопределяете его в model-runs.",
    links: docs("backendsWiki"),
  },
  language_mode: {
    title: "Поле Language mode",
    summary: "Источник языка для live eval.",
    what: "manual — из поля Language; auto — автоопределение; config — из YAML.",
    how: "Если сомневаетесь, используйте config.",
    links: docs("liveScript", "runGuide"),
  },
  language: {
    title: "Поле Language",
    summary: "Язык распознавания, например ru-RU или en-US.",
    what: "В режиме manual используется явно, иначе как override/fallback.",
    how: "Используйте формат xx-YY.",
    links: docs("runGuide"),
  },
  input_mode: {
    title: "Поле Input mode",
    summary: "Источник аудио в runtime ASR pipeline.",
    what: "mic — микрофон, file — WAV, auto — выбор автоматически.",
    how: "Для воспроизводимых тестов часто удобнее file.",
    links: docs("bringupWiki"),
  },
  sample_rate: {
    title: "Поле Sample rate",
    summary: "Частота дискретизации аудио.",
    what: "Используется в live/bringup и runtime-config.",
    how: "Оставляйте 16000, если нет особой причины менять.",
    links: docs("runGuide"),
  },
  chunk_ms: {
    title: "Поле Chunk ms",
    summary: "Размер аудиочанка для audio capture.",
    what: "Влияет на частоту публикации чанков и latency/нагрузку.",
    how: "Типичное значение 800.",
    links: docs("bringupWiki"),
  },
  interfaces: {
    title: "Поле Interfaces",
    summary: "Какие интерфейсы прогонять в live eval.",
    what: "core, ros_service, ros_action.",
    how: "Для smoke-теста достаточно core; для end-to-end добавьте ros_service/ros_action.",
    links: docs("liveScript"),
  },
  model_runs: {
    title: "Поле Model runs",
    summary: "Список таргетов backend[:model][@region].",
    what: "Каждый таргет прогоняется по выбранным интерфейсам.",
    how: "Примеры: whisper:tiny,mock,google:latest_long@global.",
    links: docs("liveScript", "backendsWiki"),
  },
  whisper_model: {
    title: "Поле Whisper model",
    summary: "Размер модели faster-whisper.",
    what: "Пишется в backends.whisper.model_size.",
    how: "Для быстрого старта tiny/base; для качества large-v3.",
    links: docs("backendsWiki", "liveConfig"),
  },
  whisper_device: {
    title: "Поле Whisper device",
    summary: "Устройство инференса whisper.",
    what: "Обычно cpu или cuda.",
    how: "Если CUDA не настроена, используйте cpu.",
    links: docs("runGuide", "backendsWiki"),
  },
  whisper_compute: {
    title: "Поле Whisper compute",
    summary: "Тип вычислений whisper.",
    what: "Например int8 (CPU) или float16 (CUDA).",
    how: "Для CPU обычно int8.",
    links: docs("backendsWiki"),
  },
  vosk_model_path: {
    title: "Поле Vosk model path",
    summary: "Путь к директории модели Vosk.",
    what: "Без модели Vosk backend вернёт ошибку загрузки.",
    how: "Укажите абсолютный путь к скачанной модели.",
    links: docs("backendsWiki"),
  },
  google_model: {
    title: "Поле Google model",
    summary: "Имя модели Google Speech.",
    what: "Используется backend-ом google.",
    how: "Часто latest_long или latest_short.",
    links: docs("backendsWiki", "secretsWiki"),
  },
  aws_region: {
    title: "Поле AWS region",
    summary: "Регион AWS Transcribe/S3.",
    what: "Используется и как backend параметр, и как секрет env при запуске.",
    how: "Пример: us-east-1.",
    links: docs("backendsWiki", "secretsWiki"),
  },
  aws_bucket: {
    title: "Поле AWS bucket",
    summary: "S3 bucket для AWS Transcribe input.",
    what: "Обязателен для AWS backend recognize-once.",
    how: "Введите существующий bucket в вашем аккаунте.",
    links: docs("backendsWiki", "secretsWiki"),
  },
  azure_region: {
    title: "Поле Azure region",
    summary: "Регион Azure Speech.",
    what: "Используется как backend параметр и env-secret.",
    how: "Пример: westeurope.",
    links: docs("backendsWiki", "secretsWiki"),
  },
  azure_endpoint: {
    title: "Поле Azure endpoint",
    summary: "Опциональный endpoint id Azure Speech.",
    what: "Дополнительная точка конфигурации SDK.",
    how: "Оставьте пустым, если используете стандартный endpoint региона.",
    links: docs("backendsWiki"),
  },
  secret_google_cred: {
    title: "Поле Google credentials JSON path",
    summary: "Путь к файлу Google service account JSON.",
    what: "Прокидывается в runtime config и GOOGLE_APPLICATION_CREDENTIALS.",
    how: "Укажите абсолютный путь к локальному JSON.",
    links: docs("secretsWiki"),
  },
  secret_google_project: {
    title: "Поле Google project id",
    summary: "ID проекта Google Cloud.",
    what: "Прокидывается в runtime config и GOOGLE_CLOUD_PROJECT.",
    how: "Введите ваш project id.",
    links: docs("secretsWiki"),
  },
  secret_aws_id: {
    title: "Поле AWS access key id",
    summary: "AWS access key для backend AWS.",
    what: "Прокидывается в runtime config и AWS_ACCESS_KEY_ID.",
    how: "Заполняйте вместе с AWS secret access key.",
    links: docs("secretsWiki"),
  },
  secret_aws_secret: {
    title: "Поле AWS secret access key",
    summary: "Секретный ключ AWS.",
    what: "Прокидывается в runtime config и AWS_SECRET_ACCESS_KEY.",
    how: "Проверьте, что ключ имеет права на S3/Transcribe.",
    links: docs("secretsWiki"),
  },
  secret_aws_token: {
    title: "Поле AWS session token",
    summary: "Временный session token (если нужен).",
    what: "Прокидывается в runtime config и AWS_SESSION_TOKEN.",
    how: "Оставьте пустым для постоянных access/secret ключей.",
    links: docs("secretsWiki"),
  },
  secret_azure_key: {
    title: "Поле Azure speech key",
    summary: "Ключ Azure Speech resource.",
    what: "Прокидывается в runtime config и AZURE_SPEECH_KEY.",
    how: "Используйте вместе с корректным Azure region.",
    links: docs("secretsWiki"),
  },
  dataset: {
    title: "Поле Dataset CSV",
    summary: "Путь к CSV манифесту для benchmark.",
    what: "Файл должен существовать и иметь расширение .csv.",
    how: "Пример: data/transcripts/sample_manifest.csv.",
    links: docs("benchmarkWiki"),
  },
  bench_backends: {
    title: "Поле Backends list",
    summary: "Список backend-ов для benchmark.",
    what: "Передаётся как --backends в runner.",
    how: "Пример: mock,whisper,vosk.",
    links: docs("benchmarkWiki"),
  },
  bench_chunk_sec: {
    title: "Поле Chunk sec",
    summary: "Chunk size для streaming simulation benchmark.",
    what: "Пишется в benchmark.chunk_sec runtime-config.",
    how: "Обычно 0.8.",
    links: docs("benchmarkWiki"),
  },
  bench_scenarios: {
    title: "Поле Scenarios",
    summary: "Набор сценариев benchmark через запятую.",
    what: "Пишется в benchmark.scenarios.",
    how: "Пример: clean,snr20,snr10,snr0.",
    links: docs("benchmarkWiki"),
  },
  metric_select: {
    title: "Поле Metrics",
    summary: "Список интересующих метрик.",
    what: "Сохраняется в runtime/profile как selected_metrics.",
    how: "Используйте для удобства профиля, даже если часть метрик не фильтруется раннером напрямую.",
    links: docs("benchmarkWiki"),
  },
  upload_file: {
    title: "Поле Upload file",
    summary: "Выбор файла с диска.",
    what: "Поддерживаются wav/csv/yaml/json/txt.",
    how: "После выбора нажмите Upload.",
    links: docs("guiReadme"),
  },
  upload_btn: {
    title: "Кнопка Upload",
    summary: "Загружает файл в web_gui/uploads.",
    what: "После успешной загрузки файл появится в выпадающих списках source/use-wav/bringup-wav.",
    how: "Загрузите dataset CSV или WAV для тестов.",
    links: docs("guiReadme"),
  },
  noise_source: {
    title: "Поле Source WAV",
    summary: "Источник аудио для генерации шума.",
    what: "Список берётся из uploads + noisy.",
    how: "Сначала загрузите WAV через Upload, затем выберите его здесь.",
    links: docs("guiReadme"),
  },
  noise_levels: {
    title: "Поле SNR levels",
    summary: "Уровни SNR через запятую.",
    what: "Каждое число создаёт отдельный noisy WAV.",
    how: "Пример: 30,20,10,0.",
    links: docs("benchmarkWiki"),
  },
  apply_noise: {
    title: "Кнопка Generate Noisy Samples",
    summary: "Генерирует noisy WAV-файлы.",
    what: "Использует выбранный source WAV и список SNR.",
    how: "После генерации обновится список файлов.",
    links: docs("benchmarkWiki", "guiReadme"),
  },
  reference_text: {
    title: "Поле Reference text",
    summary: "Эталонная фраза для WER/CER в live eval.",
    what: "Если пусто, WER/CER выставляются в -1.",
    how: "Введите текст только если есть ground truth.",
    links: docs("liveScript"),
  },
  record_sec: {
    title: "Поле Record sec",
    summary: "Длительность записи с микрофона.",
    what: "Используется, если не выбран Use WAV.",
    how: "Обычно 3-8 секунд.",
    links: docs("liveScript"),
  },
  use_wav: {
    title: "Поле Use WAV",
    summary: "Использовать готовый WAV вместо записи.",
    what: "Если заполнено, запись микрофона пропускается.",
    how: "Выберите файл из uploads/noisy.",
    links: docs("liveScript"),
  },
  audio_device: {
    title: "Поле Audio device",
    summary: "Индекс/имя устройства sounddevice.",
    what: "Передаётся в live запись и bringup audio capture.",
    how: "Оставьте пустым для default input device.",
    links: docs("runGuide"),
  },
  action_chunk_sec: {
    title: "Поле Action chunk sec",
    summary: "Chunk size для ros_action streaming goals.",
    what: "Используется при action_streaming=true.",
    how: "Обычно 0.8.",
    links: docs("liveScript"),
  },
  request_timeout: {
    title: "Поле Timeout sec",
    summary: "Таймаут запросов к ROS service/action.",
    what: "Если время истекло, вызов завершится ошибкой в live eval.",
    how: "Для облачных backend-ов иногда полезно увеличить до 40-60.",
    links: docs("liveScript", "runGuide"),
  },
  ros_auto_launch: {
    title: "Флаг ROS auto launch in live eval",
    summary: "Автозапуск bringup внутри live-sample скрипта.",
    what: "Нужен для ros_service/ros_action, если pipeline не поднят заранее.",
    how: "Выключите, если вы уже запустили bringup вручную.",
    links: docs("liveScript", "bringupWiki"),
  },
  action_streaming: {
    title: "Флаг Action streaming mode",
    summary: "В ros_action отправлять goal.streaming=true.",
    what: "Меняет поведение action сценария в live eval.",
    how: "Включайте, когда хотите проверить streaming ветку action.",
    links: docs("liveScript"),
  },
  run_live: {
    title: "Кнопка Run Live Sample Eval",
    summary: "Запуск live evaluation job.",
    what: "Создаёт runtime config, строит команду live_sample_eval.py и запускает job.",
    how: "После старта выберите job в таблице и следите за логом.",
    links: docs("liveScript", "runGuide"),
  },
  bringup_input_mode: {
    title: "Поле Bringup input mode",
    summary: "Режим аудиоисточника для ros2 bringup.",
    what: "mic/file/auto.",
    how: "Для input_mode=file обязательно задайте Bringup WAV.",
    links: docs("bringupWiki"),
  },
  bringup_wav: {
    title: "Поле Bringup WAV",
    summary: "WAV-файл для bringup file mode.",
    what: "Передаётся как wav_path:=... в launch.",
    how: "Для file режима выберите существующий WAV.",
    links: docs("bringupWiki"),
  },
  bringup_mic_sec: {
    title: "Поле Mic capture sec",
    summary: "Длительность захвата чанка микрофона в режиме file/mic loops.",
    what: "Передаётся в launch как mic_capture_sec.",
    how: "Обычно 3-5 секунд.",
    links: docs("bringupWiki"),
  },
  bringup_continuous: {
    title: "Флаг Continuous",
    summary: "Непрерывный захват/публикация аудио.",
    what: "Передаётся как continuous:=true/false.",
    how: "Для one-shot отключайте.",
    links: docs("bringupWiki"),
  },
  bringup_live_enabled: {
    title: "Флаг Live stream enabled",
    summary: "Включает обработку live chunk-потока в asr_server.",
    what: "Передаётся как live_stream_enabled launch arg.",
    how: "Отключайте, если нужен только service/action путь.",
    links: docs("bringupWiki"),
  },
  bringup_text_enabled: {
    title: "Флаг Plain-text node enabled",
    summary: "Запуск asr_text_output_node.",
    what: "Даёт plain text topic /asr/text/plain.",
    how: "Если выключен, останется структурный /asr/text.",
    links: docs("bringupWiki", "runGuide"),
  },
  run_benchmark: {
    title: "Кнопка Run Benchmark",
    summary: "Запуск benchmark job + report generation.",
    what: "Команда запускает runner и затем generate_report.py.",
    how: "Проверьте dataset path и список backend-ов до запуска.",
    links: docs("benchmarkWiki", "runGuide"),
  },
  start_bringup: {
    title: "Кнопка Start ROS Bringup",
    summary: "Запускает ros2 launch pipeline как long-running job.",
    what: "Перед стартом валидируется build/install и input_mode.",
    how: "Если видите ошибку про make build, сначала соберите workspace.",
    links: docs("bringupWiki", "runGuide"),
  },
  jobs_table: {
    title: "Таблица Jobs",
    summary: "Список всех запущенных задач.",
    what: "Клик по строке выбирает job; у running строк доступен Stop.",
    how: "Сначала выбирайте job, затем смотрите Logs/Artifacts.",
    links: docs("guiReadme"),
  },
  log_viewer: {
    title: "Поле Logs",
    summary: "Хвост лога выбранной задачи.",
    what: "Показываются последние строки из job log файла.",
    how: "Ищите здесь traceback/ошибки конфигурации.",
    links: docs("runGuide"),
  },
  artifact_list: {
    title: "Список Artifacts",
    summary: "Файлы результатов выбранного job.",
    what: "Ссылки открывают файл, PNG можно просмотреть кнопкой Preview.",
    how: "Для сравнения прогонов открывайте summary.md и plots.",
    links: docs("benchmarkWiki", "liveScript"),
  },
};

const HELP_TARGETS = {
  "runtime-setup-title": "section_runtime_setup",
  "asr-global-title": "section_asr_global",
  "interfaces-model-runs-title": "section_interfaces_model_runs",
  "backend-details-title": "section_backend_details",
  "cloud-auth-title": "section_cloud_auth",
  "benchmark-controls-title": "section_benchmark_controls",
  "samples-noise-runs-title": "section_samples_noise_runs",
  "upload-title": "section_upload",
  "noise-overlay-title": "section_noise_overlay",
  "live-run-title": "section_live_run",
  "ros2-bringup-title": "section_ros2_bringup",
  "jobs-title": "section_jobs",
  "logs-title": "section_logs",
  "artifacts-title": "section_artifacts",
  "run-preflight": "run_preflight",
  "refresh-all": "refresh_all",
  "profile-name": "profile_name",
  "base-config": "base_config",
  "save-profile": "save_profile",
  "load-profile": "load_profile",
  "asr-backend": "asr_backend",
  "language-mode": "language_mode",
  language: "language",
  "input-mode": "input_mode",
  "sample-rate": "sample_rate",
  "chunk-ms": "chunk_ms",
  interfaces: "interfaces",
  "model-runs": "model_runs",
  "whisper-model": "whisper_model",
  "whisper-device": "whisper_device",
  "whisper-compute": "whisper_compute",
  "vosk-model-path": "vosk_model_path",
  "google-model": "google_model",
  "aws-region": "aws_region",
  "aws-bucket": "aws_bucket",
  "azure-region": "azure_region",
  "azure-endpoint": "azure_endpoint",
  "secret-google-cred": "secret_google_cred",
  "secret-google-project": "secret_google_project",
  "secret-aws-id": "secret_aws_id",
  "secret-aws-secret": "secret_aws_secret",
  "secret-aws-token": "secret_aws_token",
  "secret-azure-key": "secret_azure_key",
  dataset: "dataset",
  "bench-backends": "bench_backends",
  "bench-chunk-sec": "bench_chunk_sec",
  "bench-scenarios": "bench_scenarios",
  "metric-select": "metric_select",
  "upload-file": "upload_file",
  "upload-btn": "upload_btn",
  "noise-source": "noise_source",
  "noise-levels": "noise_levels",
  "apply-noise": "apply_noise",
  "reference-text": "reference_text",
  "record-sec": "record_sec",
  "use-wav": "use_wav",
  "audio-device": "audio_device",
  "action-chunk-sec": "action_chunk_sec",
  "request-timeout": "request_timeout",
  "ros-auto-launch": "ros_auto_launch",
  "action-streaming": "action_streaming",
  "run-live": "run_live",
  "bringup-input-mode": "bringup_input_mode",
  "bringup-wav": "bringup_wav",
  "bringup-mic-sec": "bringup_mic_sec",
  "bringup-continuous": "bringup_continuous",
  "bringup-live-enabled": "bringup_live_enabled",
  "bringup-text-enabled": "bringup_text_enabled",
  "run-benchmark": "run_benchmark",
  "start-bringup": "start_bringup",
  "jobs-table": "jobs_table",
  "log-viewer": "log_viewer",
  "artifact-list": "artifact_list",
};

function buildHelpTrigger(helpKey) {
  const button = document.createElement("button");
  button.type = "button";
  button.className = "help-trigger help-inline";
  button.textContent = "?";
  button.title = "Показать справку";
  button.dataset.helpKey = helpKey;
  button.onclick = (event) => {
    event.preventDefault();
    event.stopPropagation();
    openHelp(helpKey);
  };
  return button;
}

function attachHelpTrigger(target, helpKey) {
  if (!target || !helpKey) {
    return;
  }
  if (!HELP_CONTENT[helpKey]) {
    return;
  }
  const parent = target.parentElement;
  const existing = parent
    ? parent.querySelector(`.help-trigger[data-help-key="${helpKey}"]`)
    : null;
  if (existing) {
    return;
  }

  const trigger = buildHelpTrigger(helpKey);
  if (target.matches("h2, h3")) {
    trigger.classList.remove("help-inline");
    target.appendChild(trigger);
    return;
  }

  if (target.tagName === "BUTTON") {
    target.insertAdjacentElement("afterend", trigger);
    return;
  }

  const label = target.closest("label");
  if (label) {
    label.appendChild(trigger);
    return;
  }
  target.insertAdjacentElement("afterend", trigger);
}

function renderHelpLinks(items) {
  const list = $("help-links");
  list.innerHTML = "";
  (items || []).forEach((item) => {
    if (!item || !item.path) {
      return;
    }
    const li = document.createElement("li");
    const a = document.createElement("a");
    a.href = docUrl(item.path);
    a.target = "_blank";
    a.rel = "noreferrer";
    a.textContent = item.label || item.path;
    li.appendChild(a);
    list.appendChild(li);
  });
}

function openHelp(helpKey) {
  const entry = HELP_CONTENT[helpKey];
  if (!entry) {
    return;
  }
  $("help-title").textContent = entry.title || "Справка";
  $("help-summary").textContent = entry.summary || "";
  $("help-what").textContent = entry.what ? `Что это: ${entry.what}` : "";
  $("help-how").textContent = entry.how ? `Как использовать: ${entry.how}` : "";
  renderHelpLinks(entry.links || []);
  $("help-modal").classList.remove("hidden");
}

function closeHelp() {
  $("help-modal").classList.add("hidden");
}

function initializeHelpSystem() {
  Object.entries(HELP_TARGETS).forEach(([id, helpKey]) => {
    const target = $(id);
    attachHelpTrigger(target, helpKey);
  });

  $("help-close").onclick = () => closeHelp();
  $("help-modal").onclick = (event) => {
    if (event.target === $("help-modal")) {
      closeHelp();
    }
  };

  window.addEventListener("keydown", (event) => {
    if (event.key === "Escape") {
      closeHelp();
    }
  });
}

function splitCsv(raw) {
  return String(raw || "")
    .split(",")
    .map((item) => item.trim())
    .filter(Boolean);
}

function asNumber(value, fallback) {
  const parsed = Number(value);
  return Number.isFinite(parsed) ? parsed : fallback;
}

function setStatus(text) {
  const pill = $("status-pill");
  pill.textContent = text;
}

async function fetchJSON(url) {
  const response = await fetch(url);
  if (!response.ok) {
    const payload = await response.json().catch(() => ({}));
    throw new Error(payload.detail || `HTTP ${response.status}`);
  }
  return response.json();
}

async function postJSON(url, payload) {
  const response = await fetch(url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  if (!response.ok) {
    const data = await response.json().catch(() => ({}));
    throw new Error(data.detail || `HTTP ${response.status}`);
  }
  return response.json();
}

function renderCheckboxGroup(container, options, prefix, checkedValues) {
  container.innerHTML = "";
  for (const value of options) {
    const id = `${prefix}-${value}`;
    const label = document.createElement("label");
    label.innerHTML = `<input type="checkbox" id="${id}" value="${value}"> ${value}`;
    container.appendChild(label);
    if (checkedValues.includes(value)) {
      const input = label.querySelector("input");
      input.checked = true;
    }
  }
}

function checkedValues(containerId) {
  const container = $(containerId);
  return Array.from(container.querySelectorAll("input[type='checkbox']"))
    .filter((item) => item.checked)
    .map((item) => item.value);
}

function populateSelect(selectId, values, selected = "") {
  const select = $(selectId);
  select.innerHTML = "";
  values.forEach((value) => {
    const option = document.createElement("option");
    option.value = value;
    option.textContent = value;
    select.appendChild(option);
  });
  if (selected && values.includes(selected)) {
    select.value = selected;
  }
}

function collectRuntimeOverrides() {
  const language = $("language").value.trim();
  const runtime = {
    asr: {
      backend: $("asr-backend").value,
      sample_rate: asNumber($("sample-rate").value, 16000),
      chunk_ms: asNumber($("chunk-ms").value, 800),
      input_mode: $("input-mode").value,
    },
    benchmark: {
      scenarios: splitCsv($("bench-scenarios").value),
      chunk_sec: asNumber($("bench-chunk-sec").value, 0.8),
      selected_metrics: checkedValues("metric-select"),
    },
    backends: {
      whisper: {
        model_size: $("whisper-model").value.trim(),
        device: $("whisper-device").value.trim(),
        compute_type: $("whisper-compute").value.trim(),
      },
      vosk: {
        model_path: $("vosk-model-path").value.trim(),
      },
      google: {
        model: $("google-model").value.trim(),
      },
      aws: {
        region: $("aws-region").value.trim(),
        s3_bucket: $("aws-bucket").value.trim(),
      },
      azure: {
        region: $("azure-region").value.trim(),
        endpoint: $("azure-endpoint").value.trim(),
      },
    },
  };

  if (language) {
    runtime.asr.language = language;
  }
  return runtime;
}

function collectSecrets() {
  return {
    google_credentials_json: $("secret-google-cred").value.trim(),
    google_project_id: $("secret-google-project").value.trim(),
    aws_access_key_id: $("secret-aws-id").value.trim(),
    aws_secret_access_key: $("secret-aws-secret").value.trim(),
    aws_session_token: $("secret-aws-token").value.trim(),
    aws_region: $("aws-region").value.trim(),
    azure_speech_key: $("secret-azure-key").value.trim(),
    azure_region: $("azure-region").value.trim(),
  };
}

function commonRequestEnvelope(payload) {
  return {
    profile_name: $("profile-name").value.trim(),
    base_config: $("base-config").value,
    runtime_overrides: collectRuntimeOverrides(),
    secrets: collectSecrets(),
    payload,
  };
}

function selectedFileOrEmpty(selectId) {
  const select = $(selectId);
  return select && select.value ? select.value : "";
}

async function runLiveSample() {
  setStatus("Starting live sample job...");
  const payload = {
    interfaces: checkedValues("interfaces").join(",") || "core",
    model_runs: $("model-runs").value.trim(),
    language_mode: $("language-mode").value,
    language: $("language").value.trim(),
    reference_text: $("reference-text").value.trim(),
    record_sec: asNumber($("record-sec").value, 5),
    sample_rate: asNumber($("sample-rate").value, 16000),
    use_wav: selectedFileOrEmpty("use-wav"),
    device: $("audio-device").value.trim(),
    ros_auto_launch: $("ros-auto-launch").checked,
    action_streaming: $("action-streaming").checked,
    action_chunk_sec: asNumber($("action-chunk-sec").value, 0.8),
    request_timeout_sec: asNumber($("request-timeout").value, 25),
  };
  const response = await postJSON("/api/jobs/live-sample", commonRequestEnvelope(payload));
  state.selectedJobId = response.job.job_id;
  await refreshJobs();
  await loadSelectedJob();
  setStatus(`Live sample job started: ${response.job.job_id}`);
}

async function runBenchmark() {
  setStatus("Starting benchmark job...");
  const payload = {
    dataset: $("dataset").value.trim(),
    backends: $("bench-backends").value.trim(),
  };
  const response = await postJSON("/api/jobs/benchmark", commonRequestEnvelope(payload));
  state.selectedJobId = response.job.job_id;
  await refreshJobs();
  await loadSelectedJob();
  setStatus(`Benchmark job started: ${response.job.job_id}`);
}

async function startBringup() {
  setStatus("Starting ROS bringup...");
  const payload = {
    input_mode: $("bringup-input-mode").value,
    wav_path: selectedFileOrEmpty("bringup-wav"),
    mic_capture_sec: asNumber($("bringup-mic-sec").value, 4.0),
    continuous: $("bringup-continuous").checked,
    live_stream_enabled: $("bringup-live-enabled").checked,
    text_output_enabled: $("bringup-text-enabled").checked,
    sample_rate: asNumber($("sample-rate").value, 16000),
    chunk_ms: asNumber($("chunk-ms").value, 800),
    device: $("audio-device").value.trim(),
  };
  const response = await postJSON("/api/jobs/ros-bringup", commonRequestEnvelope(payload));
  state.selectedJobId = response.job.job_id;
  await refreshJobs();
  await loadSelectedJob();
  setStatus(`ROS bringup started: ${response.job.job_id}`);
}

async function stopJob(jobId) {
  await postJSON(`/api/jobs/${jobId}/stop`, {});
  await refreshJobs();
  if (state.selectedJobId === jobId) {
    await loadSelectedJob();
  }
  setStatus(`Job ${jobId} stopped`);
}

function renderArtifacts(artifacts) {
  const list = $("artifact-list");
  const preview = $("artifact-preview");
  list.innerHTML = "";
  preview.innerHTML = "";

  artifacts.forEach((item) => {
    const row = document.createElement("div");
    row.className = "artifact-item";

    const link = document.createElement("a");
    link.href = `/api/artifacts?path=${encodeURIComponent(item)}`;
    link.target = "_blank";
    link.rel = "noreferrer";
    link.textContent = item;
    row.appendChild(link);

    if (item.endsWith(".png")) {
      const btn = document.createElement("button");
      btn.className = "btn btn-secondary";
      btn.style.marginLeft = "0.5rem";
      btn.textContent = "Preview";
      btn.onclick = () => {
        preview.innerHTML = `<img src="/api/artifacts?path=${encodeURIComponent(item)}" alt="artifact">`;
      };
      row.appendChild(btn);
    }
    list.appendChild(row);
  });
}

async function loadSelectedJob() {
  if (!state.selectedJobId) {
    return;
  }
  const payload = await fetchJSON(`/api/jobs/${state.selectedJobId}`);
  const job = payload.job;
  const logs = await fetchJSON(`/api/jobs/${state.selectedJobId}/logs?lines=300`);
  $("log-viewer").value = logs.log || "";
  renderArtifacts(job.artifacts || []);
}

async function refreshJobs() {
  const payload = await fetchJSON("/api/jobs");
  const jobs = payload.jobs || [];
  const tbody = $("jobs-table").querySelector("tbody");
  tbody.innerHTML = "";

  jobs.forEach((job) => {
    const row = document.createElement("tr");
    row.innerHTML = `
      <td>${job.job_id}</td>
      <td>${job.kind}</td>
      <td>${job.status}</td>
      <td>${job.started_at}</td>
      <td></td>
    `;

    row.onclick = async () => {
      state.selectedJobId = job.job_id;
      await loadSelectedJob();
      setStatus(`Selected job ${job.job_id}`);
    };

    const actions = row.querySelector("td:last-child");
    if (job.status === "running") {
      const stopBtn = document.createElement("button");
      stopBtn.className = "btn btn-secondary";
      stopBtn.textContent = "Stop";
      stopBtn.onclick = async (event) => {
        event.stopPropagation();
        await stopJob(job.job_id);
      };
      actions.appendChild(stopBtn);
    } else {
      actions.textContent = "-";
    }
    tbody.appendChild(row);
  });
}

async function runPreflight() {
  const payload = await fetchJSON("/api/preflight");
  if (payload.ok) {
    setStatus("Preflight: all checks passed");
    return;
  }

  const failed = [];
  const checks = payload.checks || {};
  Object.entries(checks.modules || {}).forEach(([name, item]) => {
    if (!item.ok) {
      failed.push(`module:${name}`);
    }
  });
  if (checks.microphone && !checks.microphone.ok) {
    failed.push("microphone");
  }
  Object.entries(checks.ros || {}).forEach(([name, item]) => {
    if (!item.ok) {
      failed.push(`ros:${name}`);
    }
  });
  setStatus(`Preflight issues: ${failed.join(", ")}`);
}

async function refreshFiles() {
  const payload = await fetchJSON("/api/files");
  state.files = payload;
  const sourceValues = ["", ...(payload.uploads || []), ...(payload.noisy || [])];
  const displayValues = sourceValues.map((item) => item || "(none)");

  const mapForSelect = (id) => {
    const select = $(id);
    select.innerHTML = "";
    sourceValues.forEach((value, idx) => {
      const option = document.createElement("option");
      option.value = value;
      option.textContent = displayValues[idx];
      select.appendChild(option);
    });
  };

  mapForSelect("noise-source");
  mapForSelect("use-wav");
  mapForSelect("bringup-wav");
}

async function uploadFile(event) {
  event.preventDefault();
  const input = $("upload-file");
  if (!input.files || !input.files.length) {
    return;
  }
  const formData = new FormData();
  formData.append("file", input.files[0]);
  const response = await fetch("/api/upload", { method: "POST", body: formData });
  if (!response.ok) {
    const payload = await response.json().catch(() => ({}));
    throw new Error(payload.detail || `HTTP ${response.status}`);
  }
  await refreshFiles();
  setStatus(`Uploaded: ${input.files[0].name}`);
  input.value = "";
}

async function applyNoise() {
  const source = $("noise-source").value;
  if (!source) {
    throw new Error("Select source WAV first");
  }
  const levels = splitCsv($("noise-levels").value).map((item) => Number(item));
  const validLevels = levels.filter((item) => Number.isFinite(item));
  if (!validLevels.length) {
    throw new Error("Provide at least one valid SNR value");
  }
  await postJSON("/api/noise/apply", {
    source_wav: source,
    snr_levels: validLevels,
  });
  await refreshFiles();
  setStatus("Noisy samples generated");
}

function exportCurrentProfilePayload() {
  return {
    profile_name: $("profile-name").value.trim(),
    base_config: $("base-config").value,
    runtime_overrides: collectRuntimeOverrides(),
    payload: {
      interfaces: checkedValues("interfaces").join(","),
      model_runs: $("model-runs").value.trim(),
      language_mode: $("language-mode").value,
      language: $("language").value.trim(),
      reference_text: $("reference-text").value.trim(),
      record_sec: asNumber($("record-sec").value, 5),
      sample_rate: asNumber($("sample-rate").value, 16000),
      action_chunk_sec: asNumber($("action-chunk-sec").value, 0.8),
      request_timeout_sec: asNumber($("request-timeout").value, 25),
      ros_auto_launch: $("ros-auto-launch").checked,
      action_streaming: $("action-streaming").checked,
      dataset: $("dataset").value.trim(),
      backends: $("bench-backends").value.trim(),
      scenarios: $("bench-scenarios").value.trim(),
    },
  };
}

function applyProfilePayload(payload) {
  $("profile-name").value = payload.profile_name || "";
  if (payload.base_config) {
    $("base-config").value = payload.base_config;
  }

  const runtime = payload.runtime_overrides || {};
  const asr = runtime.asr || {};
  const benchmark = runtime.benchmark || {};
  const backends = runtime.backends || {};

  if (asr.backend) $("asr-backend").value = asr.backend;
  if (asr.language) $("language").value = asr.language;
  if (asr.sample_rate) $("sample-rate").value = asr.sample_rate;
  if (asr.chunk_ms) $("chunk-ms").value = asr.chunk_ms;
  if (asr.input_mode) $("input-mode").value = asr.input_mode;

  if (benchmark.chunk_sec) $("bench-chunk-sec").value = benchmark.chunk_sec;
  if (benchmark.scenarios) $("bench-scenarios").value = benchmark.scenarios.join(",");

  const whisper = backends.whisper || {};
  if (whisper.model_size) $("whisper-model").value = whisper.model_size;
  if (whisper.device) $("whisper-device").value = whisper.device;
  if (whisper.compute_type) $("whisper-compute").value = whisper.compute_type;

  const vosk = backends.vosk || {};
  if (vosk.model_path) $("vosk-model-path").value = vosk.model_path;

  const google = backends.google || {};
  if (google.model) $("google-model").value = google.model;

  const aws = backends.aws || {};
  if (aws.region) $("aws-region").value = aws.region;
  if (aws.s3_bucket) $("aws-bucket").value = aws.s3_bucket;

  const azure = backends.azure || {};
  if (azure.region) $("azure-region").value = azure.region;
  if (azure.endpoint) $("azure-endpoint").value = azure.endpoint;

  const run = payload.payload || {};
  if (run.model_runs) $("model-runs").value = run.model_runs;
  if (run.language_mode) $("language-mode").value = run.language_mode;
  if (run.reference_text) $("reference-text").value = run.reference_text;
  if (run.record_sec) $("record-sec").value = run.record_sec;
  if (run.action_chunk_sec) $("action-chunk-sec").value = run.action_chunk_sec;
  if (run.request_timeout_sec) $("request-timeout").value = run.request_timeout_sec;
  if (run.dataset) $("dataset").value = run.dataset;
  if (run.backends) $("bench-backends").value = run.backends;
  if (run.scenarios) $("bench-scenarios").value = run.scenarios;

  if (run.interfaces) {
    const selected = splitCsv(run.interfaces);
    const nodes = $("interfaces").querySelectorAll("input[type='checkbox']");
    nodes.forEach((item) => {
      item.checked = selected.includes(item.value);
    });
  }
}

async function saveProfile() {
  const name = $("profile-name").value.trim();
  if (!name) {
    throw new Error("Set profile name first");
  }
  await postJSON("/api/profiles", {
    name,
    payload: exportCurrentProfilePayload(),
  });
  setStatus(`Profile saved: ${name}`);
}

async function loadProfile() {
  const name = $("profile-name").value.trim();
  if (!name) {
    throw new Error("Set profile name first");
  }
  const response = await fetchJSON(`/api/profiles/${encodeURIComponent(name)}`);
  applyProfilePayload(response.payload || {});
  setStatus(`Profile loaded: ${name}`);
}

async function bootstrap() {
  setStatus("Loading options...");
  const options = await fetchJSON("/api/options");
  state.options = options;

  populateSelect("base-config", options.base_configs || ["configs/default.yaml"], "configs/default.yaml");
  populateSelect("asr-backend", options.backends || ["mock"], "mock");

  renderCheckboxGroup($("interfaces"), options.interfaces || [], "iface", ["core"]);
  renderCheckboxGroup($("metric-select"), options.metrics || [], "metric", [
    "wer",
    "cer",
    "latency_ms",
    "rtf",
  ]);

  await refreshFiles();
  await refreshJobs();
  setStatus("Ready");
}

function bindEvents() {
  $("run-preflight").onclick = async () => {
    try {
      await runPreflight();
    } catch (error) {
      setStatus(`Preflight failed: ${error.message}`);
    }
  };

  $("refresh-all").onclick = async () => {
    await refreshFiles();
    await refreshJobs();
    await loadSelectedJob();
    setStatus("Refreshed");
  };

  $("run-live").onclick = async () => {
    try {
      await runLiveSample();
    } catch (error) {
      setStatus(`Live run failed: ${error.message}`);
    }
  };

  $("run-benchmark").onclick = async () => {
    try {
      await runBenchmark();
    } catch (error) {
      setStatus(`Benchmark failed: ${error.message}`);
    }
  };

  $("start-bringup").onclick = async () => {
    try {
      await startBringup();
    } catch (error) {
      setStatus(`Bringup failed: ${error.message}`);
    }
  };

  $("upload-form").addEventListener("submit", async (event) => {
    try {
      await uploadFile(event);
    } catch (error) {
      setStatus(`Upload failed: ${error.message}`);
    }
  });

  $("apply-noise").onclick = async () => {
    try {
      await applyNoise();
    } catch (error) {
      setStatus(`Noise failed: ${error.message}`);
    }
  };

  $("save-profile").onclick = async () => {
    try {
      await saveProfile();
    } catch (error) {
      setStatus(`Save profile failed: ${error.message}`);
    }
  };

  $("load-profile").onclick = async () => {
    try {
      await loadProfile();
    } catch (error) {
      setStatus(`Load profile failed: ${error.message}`);
    }
  };
}

window.addEventListener("DOMContentLoaded", async () => {
  initializeHelpSystem();
  bindEvents();
  try {
    await bootstrap();
    await runPreflight();
  } catch (error) {
    setStatus(`Init failed: ${error.message}`);
  }

  setInterval(async () => {
    try {
      await refreshJobs();
      await loadSelectedJob();
    } catch (_error) {
      // Keep polling resilient.
    }
  }, 3000);
});
