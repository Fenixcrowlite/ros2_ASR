const state = {
  options: null,
  files: null,
  selectedJobId: null,
  profileAutocomplete: {
    open: false,
    items: [],
    activeIndex: -1,
  },
  helpLanguage: "ru",
  help: {
    key: "",
    anchor: null,
  },
};

const $ = (id) => document.getElementById(id);

const HELP_LANGUAGE_STORAGE_KEY = "web_gui_help_lang";

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

const HELP_CONTENT_RU = {
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
    how: "Начните вводить имя в Profile name, при желании выберите подсказку и нажмите Load Profile.",
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

const HELP_CONTENT_EN = {
  section_runtime_setup: {
    title: "Runtime Setup",
    summary: "Core run/profile settings.",
    what: "This section selects the base YAML and builds runtime overrides for each launch.",
    how: "Choose a base config, adjust fields, and save a profile if you want to reuse the setup.",
    links: docs("guiReadme", "defaultConfig", "liveConfig"),
  },
  section_asr_global: {
    title: "ASR Global",
    summary: "Global ASR runtime parameters.",
    what: "Controls default backend, language, sample rate, chunk size, and input mode.",
    how: "For a stable baseline keep sample rate at 16000 and chunk ms around 800.",
    links: docs("backendsWiki", "defaultConfig"),
  },
  section_interfaces_model_runs: {
    title: "Interfaces & Model Runs",
    summary: "Select interfaces and backend/model targets.",
    what: "Live eval runs selected interfaces against each target from model-runs.",
    how: "Use format backend[:model][@region], for example whisper:tiny,mock,google:latest_long@global.",
    links: docs("liveScript", "backendsWiki"),
  },
  section_backend_details: {
    title: "Backend Details",
    summary: "Backend-specific advanced options.",
    what: "Values are written into runtime config under backends.*.",
    how: "Only fill providers you actually use; leave the rest at defaults.",
    links: docs("backendsWiki", "defaultConfig"),
  },
  section_cloud_auth: {
    title: "Cloud Auth",
    summary: "Provider secrets and auth fields.",
    what: "Secrets are injected into runtime config and process environment for each job.",
    how: "Fill only the provider you need and verify credentials in job logs if something fails.",
    links: docs("secretsWiki", "backendsWiki"),
  },
  section_benchmark_controls: {
    title: "Benchmark Controls",
    summary: "Benchmark-specific inputs.",
    what: "Dataset and backend list go to benchmark command; scenarios/chunk settings go into runtime config.",
    how: "Use an existing CSV manifest and a comma-separated backend list.",
    links: docs("benchmarkWiki", "runGuide"),
  },
  section_samples_noise_runs: {
    title: "Samples, Noise, Runs",
    summary: "Assets and execution controls.",
    what: "This panel starts upload, noisy sample generation, live eval, benchmark, and ROS bringup jobs.",
    how: "After starting any job, monitor Jobs/Logs/Artifacts to verify progress and output.",
    links: docs("guiReadme", "runGuide"),
  },
  section_upload: {
    title: "Upload",
    summary: "Upload local assets for GUI runs.",
    what: "Uploaded files are saved into web_gui/uploads and become selectable in dropdowns.",
    how: "Upload WAV for live/noise flows, or CSV for benchmark dataset input.",
    links: docs("guiReadme"),
  },
  section_noise_overlay: {
    title: "Noise Overlay",
    summary: "Generate noisy WAV variants.",
    what: "Creates copies of a source WAV at requested SNR levels.",
    how: "Provide SNR list like 30,20,10,0 and run generation.",
    links: docs("benchmarkWiki", "guiReadme"),
  },
  section_live_run: {
    title: "Live Run",
    summary: "Run scripts/live_sample_eval.py from UI.",
    what: "Uses microphone or an existing WAV and executes core/ros_service/ros_action scenarios.",
    how: "If ROS interfaces are selected, enable ROS auto launch or run bringup manually first.",
    links: docs("liveScript", "runGuide"),
  },
  section_ros2_bringup: {
    title: "ROS2 Bringup",
    summary: "Launch ROS runtime pipeline.",
    what: "Starts asr_server_node, audio_capture_node, and optional text output node.",
    how: "For file mode you must provide WAV path; workspace must be built before launch.",
    links: docs("bringupWiki", "runGuide"),
  },
  section_jobs: {
    title: "Jobs",
    summary: "Background process tracking.",
    what: "Each run creates a job with id, status, logs, and discovered artifacts.",
    how: "Select a row to inspect details; stop a running job with Stop.",
    links: docs("guiReadme"),
  },
  section_logs: {
    title: "Logs",
    summary: "Tail view of selected job logs.",
    what: "Shows recent lines from the process log file.",
    how: "Use this first for troubleshooting command/config/runtime errors.",
    links: docs("runGuide"),
  },
  section_artifacts: {
    title: "Artifacts",
    summary: "Output files from completed jobs.",
    what: "Contains runtime config, json/csv/md, and plots; png supports inline preview.",
    how: "Open summary/report files first, then drill into raw json/csv.",
    links: docs("benchmarkWiki", "liveScript"),
  },
  run_preflight: {
    title: "Preflight Button",
    summary: "Environment readiness check.",
    what: "Checks Python dependencies, microphone stack, ROS setup/build, and expected binaries.",
    how: "Run this before first launch after environment changes.",
    links: docs("runGuide", "guiReadme"),
  },
  refresh_all: {
    title: "Refresh Button",
    summary: "Manual full UI refresh.",
    what: "Reloads files, jobs, selected-job logs, and artifacts.",
    how: "Use when you want immediate sync instead of waiting for polling.",
    links: docs("guiReadme"),
  },
  profile_name: {
    title: "Profile Name",
    summary: "Name used for save/load profile.",
    what: "Also used as suffix in generated runtime config filename.",
    how: "Use short stable names like lab_ru_whisper.",
    links: docs("guiReadme"),
  },
  base_config: {
    title: "Base Config",
    summary: "Base YAML file for merge.",
    what: "Runtime config is built from this file plus overrides from UI.",
    how: "Use default.yaml for generic runs, live_mic_whisper.yaml for microphone-focused runs.",
    links: docs("defaultConfig", "liveConfig"),
  },
  save_profile: {
    title: "Save Profile Button",
    summary: "Persist current UI setup.",
    what: "Stores runtime overrides and payload values into web_gui/profiles/*.yaml.",
    how: "Set profile name and click Save Profile.",
    links: docs("guiReadme"),
  },
  load_profile: {
    title: "Load Profile Button",
    summary: "Load saved UI setup.",
    what: "Applies stored runtime/payload values back into form fields.",
    how: "Type in Profile Name, optionally pick a suggestion, then click Load Profile.",
    links: docs("guiReadme"),
  },
  asr_backend: {
    title: "Backend",
    summary: "Default backend in runtime config.",
    what: "Allowed values: mock, vosk, whisper, google, aws, azure.",
    how: "Pick default backend here; model-runs can still override per target in live eval.",
    links: docs("backendsWiki"),
  },
  language_mode: {
    title: "Language Mode",
    summary: "Language source for live eval.",
    what: "manual uses Language field, auto uses detection, config uses YAML value.",
    how: "If unsure, use config mode first.",
    links: docs("liveScript", "runGuide"),
  },
  language: {
    title: "Language",
    summary: "Recognition language code.",
    what: "Typical values: en-US, ru-RU, de-DE.",
    how: "Use xx-YY format for best compatibility.",
    links: docs("runGuide"),
  },
  input_mode: {
    title: "Input Mode",
    summary: "Audio source mode.",
    what: "mic = microphone, file = WAV file, auto = fallback strategy.",
    how: "Use file for reproducible experiments.",
    links: docs("bringupWiki"),
  },
  sample_rate: {
    title: "Sample Rate",
    summary: "Audio sampling rate.",
    what: "Used by live recording, runtime pipeline, and bringup payload.",
    how: "16000 is the safest default for this project.",
    links: docs("runGuide"),
  },
  chunk_ms: {
    title: "Chunk ms",
    summary: "Audio chunk size in milliseconds.",
    what: "Affects chunk publish cadence and latency trade-offs.",
    how: "Start with 800 and tune only if needed.",
    links: docs("bringupWiki"),
  },
  interfaces: {
    title: "Interfaces",
    summary: "Live eval interface selection.",
    what: "Available: core, ros_service, ros_action.",
    how: "Use core for quick smoke tests; add ROS interfaces for end-to-end checks.",
    links: docs("liveScript"),
  },
  model_runs: {
    title: "Model Runs",
    summary: "Target list for live eval.",
    what: "Each token defines backend/model/region target.",
    how: "Format backend[:model][@region], for example whisper:tiny,mock.",
    links: docs("liveScript", "backendsWiki"),
  },
  whisper_model: {
    title: "Whisper Model",
    summary: "faster-whisper model size.",
    what: "Written to backends.whisper.model_size in runtime config.",
    how: "Use tiny/base for speed, large-v3 for quality.",
    links: docs("backendsWiki", "liveConfig"),
  },
  whisper_device: {
    title: "Whisper Device",
    summary: "Compute device for whisper backend.",
    what: "Typically cpu or cuda.",
    how: "Use cpu unless CUDA runtime is configured and verified.",
    links: docs("runGuide", "backendsWiki"),
  },
  whisper_compute: {
    title: "Whisper Compute",
    summary: "Compute type for whisper runtime.",
    what: "Examples: int8 (cpu), float16 (cuda).",
    how: "For CPU deployments, int8 is usually best.",
    links: docs("backendsWiki"),
  },
  vosk_model_path: {
    title: "Vosk Model Path",
    summary: "Path to Vosk model directory.",
    what: "Vosk backend requires a valid model directory.",
    how: "Set an absolute path to downloaded model files.",
    links: docs("backendsWiki"),
  },
  google_model: {
    title: "Google Model",
    summary: "Google Speech model name.",
    what: "Used by google backend recognize flow.",
    how: "Common values: latest_long, latest_short, chirp_2.",
    links: docs("backendsWiki", "secretsWiki"),
  },
  aws_region: {
    title: "AWS Region",
    summary: "Region for AWS backend services.",
    what: "Used by Transcribe and S3 operations.",
    how: "Typical value: us-east-1.",
    links: docs("backendsWiki", "secretsWiki"),
  },
  aws_bucket: {
    title: "AWS Bucket",
    summary: "S3 bucket for AWS transcription flow.",
    what: "Required for uploading input audio to AWS pipeline.",
    how: "Provide an existing bucket with proper IAM permissions.",
    links: docs("backendsWiki", "secretsWiki"),
  },
  azure_region: {
    title: "Azure Region",
    summary: "Azure Speech region setting.",
    what: "Used by azure backend and env-secrets mapping.",
    how: "Use your Speech resource region, e.g. westeurope.",
    links: docs("backendsWiki", "secretsWiki"),
  },
  azure_endpoint: {
    title: "Azure Endpoint",
    summary: "Optional endpoint id for Azure Speech.",
    what: "Advanced override for endpoint configuration.",
    how: "Leave empty unless your deployment requires custom endpoint id.",
    links: docs("backendsWiki"),
  },
  secret_google_cred: {
    title: "Google Credentials JSON Path",
    summary: "Path to Google service account JSON key.",
    what: "Mapped to runtime config and GOOGLE_APPLICATION_CREDENTIALS.",
    how: "Use absolute local path to credentials file.",
    links: docs("secretsWiki"),
  },
  secret_google_project: {
    title: "Google Project ID",
    summary: "Google Cloud project identifier.",
    what: "Mapped to runtime config and GOOGLE_CLOUD_PROJECT.",
    how: "Use the exact project id from GCP console.",
    links: docs("secretsWiki"),
  },
  secret_aws_id: {
    title: "AWS Access Key ID",
    summary: "AWS access key for programmatic auth.",
    what: "Mapped to runtime config and AWS_ACCESS_KEY_ID.",
    how: "Use with matching AWS secret access key.",
    links: docs("secretsWiki"),
  },
  secret_aws_secret: {
    title: "AWS Secret Access Key",
    summary: "Secret part of AWS key pair.",
    what: "Mapped to runtime config and AWS_SECRET_ACCESS_KEY.",
    how: "Verify IAM permissions for S3 and Transcribe APIs.",
    links: docs("secretsWiki"),
  },
  secret_aws_token: {
    title: "AWS Session Token",
    summary: "Temporary AWS session token.",
    what: "Mapped to runtime config and AWS_SESSION_TOKEN.",
    how: "Leave empty for long-lived key pairs without STS session.",
    links: docs("secretsWiki"),
  },
  secret_azure_key: {
    title: "Azure Speech Key",
    summary: "Azure Speech resource key.",
    what: "Mapped to runtime config and AZURE_SPEECH_KEY.",
    how: "Use together with correct Azure region.",
    links: docs("secretsWiki"),
  },
  dataset: {
    title: "Dataset CSV",
    summary: "Benchmark dataset manifest path.",
    what: "Must be existing CSV file.",
    how: "Default sample is data/transcripts/sample_manifest.csv.",
    links: docs("benchmarkWiki"),
  },
  bench_backends: {
    title: "Backends List",
    summary: "Backend list for benchmark run.",
    what: "Passed as --backends argument to benchmark runner.",
    how: "Comma-separated list, e.g. mock,whisper,vosk.",
    links: docs("benchmarkWiki"),
  },
  bench_chunk_sec: {
    title: "Chunk sec",
    summary: "Streaming simulation chunk size.",
    what: "Written into benchmark.chunk_sec runtime option.",
    how: "0.8 is a good default starting point.",
    links: docs("benchmarkWiki"),
  },
  bench_scenarios: {
    title: "Scenarios",
    summary: "Benchmark scenarios list.",
    what: "Written into benchmark.scenarios.",
    how: "Comma-separated values, e.g. clean,snr20,snr10,snr0.",
    links: docs("benchmarkWiki"),
  },
  metric_select: {
    title: "Metrics",
    summary: "Preferred metrics selection list.",
    what: "Saved in runtime/profile as selected_metrics.",
    how: "Use for profile organization even if runner does not hard-filter by this list.",
    links: docs("benchmarkWiki"),
  },
  upload_file: {
    title: "Upload File",
    summary: "Local file selector.",
    what: "Supports wav/csv/yaml/json/txt.",
    how: "Choose file then press Upload.",
    links: docs("guiReadme"),
  },
  upload_btn: {
    title: "Upload Button",
    summary: "Upload selected file to GUI storage.",
    what: "Stores file in web_gui/uploads.",
    how: "After upload it appears in source/use-wav/bringup-wav dropdowns.",
    links: docs("guiReadme"),
  },
  noise_source: {
    title: "Source WAV",
    summary: "Noise generation source file.",
    what: "Dropdown built from uploads and generated noisy files.",
    how: "Upload WAV first if list is empty.",
    links: docs("guiReadme"),
  },
  noise_levels: {
    title: "SNR Levels",
    summary: "Noise level list for generation.",
    what: "Each numeric level creates one noisy WAV.",
    how: "Use comma-separated values like 30,20,10,0.",
    links: docs("benchmarkWiki"),
  },
  apply_noise: {
    title: "Generate Noisy Samples Button",
    summary: "Create noisy WAV variants.",
    what: "Runs noise overlay service for selected source and SNR levels.",
    how: "Refresh is automatic; generated files show up in dropdowns.",
    links: docs("benchmarkWiki", "guiReadme"),
  },
  reference_text: {
    title: "Reference Text",
    summary: "Ground truth phrase for WER/CER.",
    what: "If empty, WER/CER are set to -1 for live records.",
    how: "Provide exact expected phrase only when you have reliable reference.",
    links: docs("liveScript"),
  },
  record_sec: {
    title: "Record sec",
    summary: "Microphone recording duration.",
    what: "Used only when Use WAV is empty.",
    how: "Typical range is 3 to 8 seconds.",
    links: docs("liveScript"),
  },
  use_wav: {
    title: "Use WAV",
    summary: "Use existing WAV instead of recording.",
    what: "Skips microphone capture and uses selected file directly.",
    how: "Select uploaded/noisy WAV for reproducible runs.",
    links: docs("liveScript"),
  },
  audio_device: {
    title: "Audio Device",
    summary: "sounddevice input target.",
    what: "Passed to live recorder and bringup audio capture node.",
    how: "Leave empty to use system default input device.",
    links: docs("runGuide"),
  },
  action_chunk_sec: {
    title: "Action chunk sec",
    summary: "Chunk parameter for ros_action streaming mode.",
    what: "Used when action_streaming flag is enabled.",
    how: "Start with 0.8 unless testing chunk sensitivity.",
    links: docs("liveScript"),
  },
  request_timeout: {
    title: "Timeout sec",
    summary: "ROS request timeout.",
    what: "Timeout for service/action calls in live eval.",
    how: "Increase for cloud backends if requests exceed default time.",
    links: docs("liveScript", "runGuide"),
  },
  ros_auto_launch: {
    title: "ROS auto launch",
    summary: "Auto-start ROS bringup for live eval.",
    what: "Useful when ros_service/ros_action are selected and pipeline is not running.",
    how: "Disable if you already run bringup manually.",
    links: docs("liveScript", "bringupWiki"),
  },
  action_streaming: {
    title: "Action streaming mode",
    summary: "Enable streaming=true for action calls.",
    what: "Switches ros_action path to streaming branch.",
    how: "Enable only when you need action streaming behavior in test.",
    links: docs("liveScript"),
  },
  run_live: {
    title: "Run Live Sample Eval Button",
    summary: "Start live evaluation background job.",
    what: "Builds runtime config and starts live_sample_eval.py command.",
    how: "Open job logs after start to monitor progress and errors.",
    links: docs("liveScript", "runGuide"),
  },
  bringup_input_mode: {
    title: "Bringup input mode",
    summary: "Audio mode passed to bringup launch.",
    what: "Allowed: mic, file, auto.",
    how: "If file mode is selected, provide Bringup WAV.",
    links: docs("bringupWiki"),
  },
  bringup_wav: {
    title: "Bringup WAV",
    summary: "WAV path for file mode bringup.",
    what: "Forwarded as wav_path launch argument.",
    how: "Pick existing valid WAV when input mode is file.",
    links: docs("bringupWiki"),
  },
  bringup_mic_sec: {
    title: "Mic capture sec",
    summary: "Capture duration parameter for bringup.",
    what: "Forwarded as mic_capture_sec launch argument.",
    how: "Use 3-5 seconds for practical live loops.",
    links: docs("bringupWiki"),
  },
  bringup_continuous: {
    title: "Continuous",
    summary: "Continuous capture toggle.",
    what: "Forwarded as continuous true/false.",
    how: "Disable for single-shot style processing.",
    links: docs("bringupWiki"),
  },
  bringup_live_enabled: {
    title: "Live stream enabled",
    summary: "Enable live chunk handling in ASR server.",
    what: "Forwarded as live_stream_enabled launch arg.",
    how: "Disable when you only need service/action testing.",
    links: docs("bringupWiki"),
  },
  bringup_text_enabled: {
    title: "Plain-text node enabled",
    summary: "Start asr_text_output_node.",
    what: "Provides plain text topic /asr/text/plain.",
    how: "Disable if you only need structured /asr/text output.",
    links: docs("bringupWiki", "runGuide"),
  },
  run_benchmark: {
    title: "Run Benchmark Button",
    summary: "Start benchmark and report generation.",
    what: "Runs benchmark runner and then scripts/generate_report.py.",
    how: "Validate dataset path and backend list before launch.",
    links: docs("benchmarkWiki", "runGuide"),
  },
  start_bringup: {
    title: "Start ROS Bringup Button",
    summary: "Start long-running ROS launch job.",
    what: "Validates mode/build and starts ros2 launch asr_ros bringup.launch.py.",
    how: "If you see build-related errors, run make build first.",
    links: docs("bringupWiki", "runGuide"),
  },
  jobs_table: {
    title: "Jobs Table",
    summary: "List of all started jobs.",
    what: "Click a row to load details; running rows expose Stop button.",
    how: "Use with Logs and Artifacts panels for diagnostics.",
    links: docs("guiReadme"),
  },
  log_viewer: {
    title: "Logs Viewer",
    summary: "Tail view for selected job log.",
    what: "Shows latest lines from process output log.",
    how: "Start here when a job fails or hangs unexpectedly.",
    links: docs("runGuide"),
  },
  artifact_list: {
    title: "Artifacts List",
    summary: "Output files of selected job.",
    what: "Links open files via API; PNG entries support inline preview.",
    how: "Review summary/report markdown first, then inspect detailed files.",
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

function normalizeHelpLanguage(value) {
  return value === "en" ? "en" : "ru";
}

function getHelpEntry(helpKey) {
  const primary = state.helpLanguage === "en" ? HELP_CONTENT_EN : HELP_CONTENT_RU;
  const fallback = state.helpLanguage === "en" ? HELP_CONTENT_RU : HELP_CONTENT_EN;
  return primary[helpKey] || fallback[helpKey] || null;
}

function updateHelpLanguageUI() {
  const langBtn = $("help-lang-toggle");
  if (langBtn) {
    langBtn.textContent = state.helpLanguage === "en" ? "Help: EN" : "Help: RU";
  }

  const closeBtn = $("help-close");
  if (closeBtn) {
    closeBtn.textContent = state.helpLanguage === "en" ? "Close" : "Закрыть";
  }

  const triggerTitle = state.helpLanguage === "en" ? "Show help" : "Показать справку";
  document.querySelectorAll(".help-trigger").forEach((el) => {
    el.title = triggerTitle;
  });
}

function setHelpLanguage(language, { persist = true, rerender = true } = {}) {
  state.helpLanguage = normalizeHelpLanguage(language);
  if (persist) {
    try {
      localStorage.setItem(HELP_LANGUAGE_STORAGE_KEY, state.helpLanguage);
    } catch (_err) {
      // Ignore storage errors.
    }
  }
  updateHelpLanguageUI();
  if (rerender && state.help.key) {
    openHelpAt(state.help.key, state.help.anchor);
  }
}

function toggleHelpLanguage() {
  setHelpLanguage(state.helpLanguage === "en" ? "ru" : "en");
}

function buildHelpTrigger(helpKey) {
  const button = document.createElement("button");
  button.type = "button";
  button.className = "help-trigger help-inline";
  button.textContent = "?";
  button.title = state.helpLanguage === "en" ? "Show help" : "Показать справку";
  button.dataset.helpKey = helpKey;
  button.onclick = (event) => {
    event.preventDefault();
    event.stopPropagation();
    openHelpAt(helpKey, button);
  };
  return button;
}

function attachHelpTrigger(target, helpKey) {
  if (!target || !helpKey) {
    return;
  }
  if (!getHelpEntry(helpKey)) {
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
  openHelpAt(helpKey, null);
}

function positionHelpCard(anchor) {
  const card = document.querySelector("#help-modal .help-card");
  if (!card) {
    return;
  }

  card.classList.remove("side");
  card.style.left = "";
  card.style.top = "";
  card.style.right = "";
  card.style.bottom = "";

  if (!anchor) {
    card.classList.add("side");
    return;
  }

  card.style.visibility = "hidden";
  card.style.left = "0px";
  card.style.top = "0px";
  const cardRect = card.getBoundingClientRect();
  card.style.visibility = "";

  const width = cardRect.width || 420;
  const height = cardRect.height || 360;
  const gap = 10;
  const margin = 12;
  const anchorRect = anchor.getBoundingClientRect();

  let left = anchorRect.right + gap;
  const topBase = anchorRect.top - 8;
  const fitsRight = left + width + margin <= window.innerWidth;
  const fitsLeft = anchorRect.left - gap - width >= margin;

  if (!fitsRight && fitsLeft) {
    left = anchorRect.left - width - gap;
  } else if (!fitsRight) {
    card.classList.add("side");
    return;
  }

  let top = topBase;
  const maxTop = window.innerHeight - height - margin;
  if (top > maxTop) {
    top = maxTop;
  }
  if (top < margin) {
    top = margin;
  }

  card.style.left = `${Math.round(left)}px`;
  card.style.top = `${Math.round(top)}px`;
}

function openHelpAt(helpKey, anchor) {
  const entry = getHelpEntry(helpKey);
  if (!entry) {
    return;
  }
  state.help.key = helpKey;
  state.help.anchor = anchor || null;
  const whatLabel = state.helpLanguage === "en" ? "What it is" : "Что это";
  const howLabel = state.helpLanguage === "en" ? "How to use" : "Как использовать";
  $("help-title").textContent = entry.title || (state.helpLanguage === "en" ? "Help" : "Справка");
  $("help-summary").textContent = entry.summary || "";
  $("help-what").textContent = entry.what ? `${whatLabel}: ${entry.what}` : "";
  $("help-how").textContent = entry.how ? `${howLabel}: ${entry.how}` : "";
  renderHelpLinks(entry.links || []);
  $("help-modal").classList.remove("hidden");
  positionHelpCard(state.help.anchor);
}

function closeHelp() {
  $("help-modal").classList.add("hidden");
  state.help.key = "";
  state.help.anchor = null;
}

function initializeHelpSystem() {
  let savedLang = "ru";
  try {
    savedLang = normalizeHelpLanguage(localStorage.getItem(HELP_LANGUAGE_STORAGE_KEY) || "ru");
  } catch (_err) {
    savedLang = "ru";
  }
  setHelpLanguage(savedLang, { persist: false, rerender: false });

  Object.entries(HELP_TARGETS).forEach(([id, helpKey]) => {
    const target = $(id);
    attachHelpTrigger(target, helpKey);
  });
  updateHelpLanguageUI();

  const langToggle = $("help-lang-toggle");
  if (langToggle) {
    langToggle.onclick = () => toggleHelpLanguage();
  }

  $("help-close").onclick = () => closeHelp();
  $("help-modal").onclick = (event) => {
    if (event.target === $("help-modal")) {
      closeHelp();
    }
  };

  document.addEventListener("mousedown", (event) => {
    const modal = $("help-modal");
    if (modal.classList.contains("hidden")) {
      return;
    }
    const card = modal.querySelector(".help-card");
    const target = event.target;
    if (!(target instanceof Element)) {
      return;
    }
    if (card && card.contains(target)) {
      return;
    }
    if (target.closest(".help-trigger")) {
      return;
    }
    closeHelp();
  });

  window.addEventListener("keydown", (event) => {
    if (event.key === "Escape") {
      closeHelp();
    }
  });

  window.addEventListener("resize", () => {
    const modal = $("help-modal");
    if (modal.classList.contains("hidden")) {
      return;
    }
    positionHelpCard(state.help.anchor);
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
  const normalized = Array.from(
    new Set(
      (values || [])
        .map((value) => String(value ?? "").trim())
        .filter(Boolean),
    ),
  );
  select.innerHTML = "";
  normalized.forEach((value) => {
    const option = document.createElement("option");
    option.value = value;
    option.textContent = value;
    select.appendChild(option);
  });
  if (selected && normalized.includes(selected)) {
    select.value = selected;
  }
}

function populateDatalist(listId, values) {
  const datalist = $(listId);
  if (!datalist) {
    return;
  }
  const normalized = Array.from(
    new Set(
      (values || [])
        .map((value) => String(value ?? "").trim())
        .filter(Boolean),
    ),
  );
  datalist.innerHTML = "";
  normalized.forEach((value) => {
    const option = document.createElement("option");
    option.value = value;
    datalist.appendChild(option);
  });
}

function splitCsvOrArray(raw) {
  if (Array.isArray(raw)) {
    return raw
      .map((item) => String(item ?? "").trim())
      .filter(Boolean);
  }
  return splitCsv(raw);
}

function csvFromAny(raw) {
  if (Array.isArray(raw)) {
    return raw
      .map((item) => String(item ?? "").trim())
      .filter(Boolean)
      .join(",");
  }
  return String(raw ?? "").trim();
}

function setCheckboxGroup(containerId, values, fallback = []) {
  const selectedValues = splitCsvOrArray(values);
  const selected = new Set(selectedValues.length ? selectedValues : splitCsvOrArray(fallback));
  const nodes = $(containerId).querySelectorAll("input[type='checkbox']");
  nodes.forEach((item) => {
    item.checked = selected.has(item.value);
  });
}

function setSelectValueIfPresent(selectId, value) {
  const select = $(selectId);
  const normalized = String(value ?? "").trim();
  if (!normalized) {
    return;
  }
  const options = Array.from(select.options).map((item) => item.value);
  if (options.includes(normalized)) {
    select.value = normalized;
  }
}

function setFieldValue(inputId, value) {
  if (value === undefined || value === null || value === "") {
    return;
  }
  $(inputId).value = String(value);
}

const AWS_AUTH_TEXT_KEY_ORDER = [
  "AWS_AUTH_TYPE",
  "AWS_PROFILE",
  "AWS_REGION",
  "AWS_SSO_START_URL",
  "AWS_SSO_REGION",
  "AWS_SSO_ACCOUNT_ID",
  "AWS_SSO_ROLE_NAME",
  "AWS_SSO_SESSION_NAME",
  "AWS_S3_BUCKET",
];

function parseEnvLikeText(raw) {
  const values = {};
  const lines = String(raw || "").split(/\r?\n/);
  for (const lineRaw of lines) {
    const line = lineRaw.trim();
    if (!line || line.startsWith("#")) {
      continue;
    }
    const eq = line.indexOf("=");
    if (eq <= 0) {
      continue;
    }
    const key = line.slice(0, eq).trim();
    let value = line.slice(eq + 1).trim();
    if (
      (value.startsWith("\"") && value.endsWith("\"")) ||
      (value.startsWith("'") && value.endsWith("'"))
    ) {
      value = value.slice(1, -1);
    }
    if (key) {
      values[key] = value;
    }
  }
  return values;
}

function renderEnvLikeText(values) {
  const rows = [];
  const used = new Set();
  for (const key of AWS_AUTH_TEXT_KEY_ORDER) {
    const value = String(values?.[key] || "").trim();
    if (!value) {
      continue;
    }
    rows.push(`${key}=${value}`);
    used.add(key);
  }
  const leftovers = Object.keys(values || {})
    .filter((key) => !used.has(key))
    .sort((left, right) => left.localeCompare(right));
  for (const key of leftovers) {
    const value = String(values[key] || "").trim();
    if (!value) {
      continue;
    }
    rows.push(`${key}=${value}`);
  }
  return rows.join("\n") + (rows.length ? "\n" : "");
}

function buildAwsAuthTextFromForm() {
  const values = parseEnvLikeText($("aws-auth-text").value);
  const ssoStartUrl = $("secret-aws-sso-start-url").value.trim();
  const ssoRegion = $("secret-aws-sso-region").value.trim();
  const region = $("aws-region").value.trim() || values.AWS_REGION || ssoRegion;
  const bucket = $("aws-bucket").value.trim();

  if (!ssoStartUrl) {
    throw new Error("Set AWS SSO start URL");
  }
  if (!ssoRegion) {
    throw new Error("Set AWS SSO region");
  }

  values.AWS_AUTH_TYPE = "sso";
  values.AWS_PROFILE = values.AWS_PROFILE || "ros2ws";
  if (region) {
    values.AWS_REGION = region;
  }
  values.AWS_SSO_START_URL = ssoStartUrl;
  values.AWS_SSO_REGION = ssoRegion;
  if (bucket) {
    values.AWS_S3_BUCKET = bucket;
  } else {
    delete values.AWS_S3_BUCKET;
  }
  delete values.AWS_ACCESS_KEY_ID;
  delete values.AWS_SECRET_ACCESS_KEY;
  delete values.AWS_SESSION_TOKEN;

  const rendered = renderEnvLikeText(values);
  $("aws-auth-text").value = rendered;
  return values;
}

function normalizeAwsAuthProfileNames(values) {
  const collator = new Intl.Collator(undefined, { sensitivity: "base", numeric: true });
  return Array.from(
    new Set(
      (values || [])
        .map((value) => String(value || "").trim())
        .filter(Boolean),
    ),
  ).sort((left, right) => collator.compare(left, right));
}

function selectedAwsAuthProfile() {
  const select = $("aws-auth-profile");
  if (!select) {
    return "";
  }
  return String(select.value || "").trim();
}

function safeAwsAuthName(raw) {
  return String(raw || "")
    .trim()
    .toLowerCase()
    .replace(/[^a-z0-9._-]+/g, "-")
    .replace(/^[._-]+|[._-]+$/g, "") || "aws-sso";
}

function defaultAwsAuthProfileName() {
  const ssoStartUrl = $("secret-aws-sso-start-url").value.trim();
  const ssoRegion = $("secret-aws-sso-region").value.trim();
  let host = "";
  if (ssoStartUrl) {
    try {
      host = new URL(ssoStartUrl).host;
    } catch (_error) {
      host = ssoStartUrl
        .replace(/^https?:\/\//i, "")
        .split("/")[0];
    }
  }
  const base = [host, ssoRegion].filter(Boolean).join("-");
  return safeAwsAuthName(base ? `sso-${base}` : "aws-sso");
}

function applyAwsAuthValues(values) {
  const region = String(values.AWS_REGION || "").trim();
  const bucket = String(values.AWS_S3_BUCKET || "").trim();
  const ssoStartUrl = String(values.AWS_SSO_START_URL || "").trim();
  const ssoRegion = String(values.AWS_SSO_REGION || "").trim();

  if (region) {
    $("aws-region").value = region;
  }
  if (bucket) {
    $("aws-bucket").value = bucket;
  }
  $("secret-aws-sso-start-url").value = ssoStartUrl;
  $("secret-aws-sso-region").value = ssoRegion;
}

function normalizeProfileNames(values) {
  const collator = new Intl.Collator(undefined, { sensitivity: "base", numeric: true });
  return Array.from(
    new Set(
      (values || [])
        .map((value) => String(value || "").trim())
        .filter(Boolean),
    ),
  ).sort((left, right) => collator.compare(left, right));
}

function setKnownProfiles(values) {
  const names = normalizeProfileNames(values);
  if (state.options) {
    state.options = { ...state.options, profiles: names };
  } else {
    state.options = { profiles: names };
  }
  return names;
}

function filterProfileSuggestions(rawQuery) {
  const names = normalizeProfileNames(state.options?.profiles || []);
  const query = String(rawQuery || "").trim().toLowerCase();
  if (!query) {
    return names;
  }

  const startsWith = [];
  const includes = [];
  names.forEach((name) => {
    const lower = name.toLowerCase();
    if (lower.startsWith(query)) {
      startsWith.push(name);
    } else if (lower.includes(query)) {
      includes.push(name);
    }
  });
  return [...startsWith, ...includes];
}

function hideProfileSuggestions() {
  const panel = $("profile-name-suggestions");
  if (!panel) {
    return;
  }
  panel.classList.add("hidden");
  panel.innerHTML = "";
  state.profileAutocomplete.open = false;
  state.profileAutocomplete.items = [];
  state.profileAutocomplete.activeIndex = -1;
}

function setActiveProfileSuggestion(index) {
  state.profileAutocomplete.activeIndex = index;
  const panel = $("profile-name-suggestions");
  if (!panel) {
    return;
  }
  const options = panel.querySelectorAll(".profile-suggestion-item");
  options.forEach((node, nodeIndex) => {
    node.classList.toggle("active", nodeIndex === index);
  });
}

function chooseProfileSuggestion(name) {
  const input = $("profile-name");
  input.value = name;
  hideProfileSuggestions();
  input.focus();
  input.setSelectionRange(name.length, name.length);
}

function renderProfileSuggestions(items) {
  const panel = $("profile-name-suggestions");
  if (!panel) {
    return;
  }

  panel.innerHTML = "";
  state.profileAutocomplete.items = items;
  state.profileAutocomplete.activeIndex = -1;

  if (!items.length) {
    hideProfileSuggestions();
    return;
  }

  items.forEach((name, index) => {
    const button = document.createElement("button");
    button.type = "button";
    button.className = "profile-suggestion-item";
    button.setAttribute("role", "option");
    button.textContent = name;
    button.onmousedown = (event) => {
      event.preventDefault();
      chooseProfileSuggestion(name);
    };
    button.onmouseenter = () => {
      setActiveProfileSuggestion(index);
    };
    panel.appendChild(button);
  });

  panel.classList.remove("hidden");
  state.profileAutocomplete.open = true;
}

function showProfileSuggestions() {
  const input = $("profile-name");
  const items = filterProfileSuggestions(input.value);
  renderProfileSuggestions(items);
}

function moveProfileSuggestion(step) {
  if (!state.profileAutocomplete.open) {
    showProfileSuggestions();
  }
  const { items, activeIndex } = state.profileAutocomplete;
  if (!items.length) {
    return;
  }
  const next = (activeIndex + step + items.length) % items.length;
  setActiveProfileSuggestion(next);
}

function selectActiveProfileSuggestion() {
  if (!state.profileAutocomplete.open) {
    return false;
  }
  const { items, activeIndex } = state.profileAutocomplete;
  if (!items.length) {
    return false;
  }
  const index = activeIndex >= 0 ? activeIndex : 0;
  chooseProfileSuggestion(items[index]);
  return true;
}

async function refreshSavedProfiles() {
  const options = await fetchJSON("/api/options");
  const names = setKnownProfiles(options.profiles || []);
  populateDatalist("aws-sso-start-url-options", options.aws_sso_start_urls || []);
  populateDatalist("aws-sso-region-options", options.aws_sso_regions || options.aws_regions || []);
  if (state.options) {
    state.options = { ...state.options, profiles: names };
  } else {
    state.options = { ...options, profiles: names };
  }
  if (document.activeElement === $("profile-name")) {
    showProfileSuggestions();
  }
}

function deriveModelRunsFromConfig(config) {
  const webCfg = config.web || {};
  if (webCfg.model_runs) {
    return String(webCfg.model_runs).trim();
  }

  const asr = config.asr || {};
  const backend = String(asr.backend || "").trim();
  if (!backend) {
    return "";
  }
  const backendCfg = (config.backends || {})[backend] || {};
  const model = String(backendCfg.model || backendCfg.model_size || asr.model || "").trim();
  const region = String(backendCfg.region || asr.region || "").trim();
  let token = backend;
  if (model) {
    token += `:${model}`;
  }
  if (region && region !== "local") {
    token += `@${region}`;
  }
  return token;
}

function populateStaticDatalists(options) {
  populateDatalist("language-options", options.languages || []);
  populateDatalist("sample-rate-options", options.sample_rates || [16000]);
  populateDatalist("chunk-ms-options", options.chunk_ms_values || [800]);
  populateDatalist("model-runs-options", options.model_run_presets || []);
  populateDatalist("whisper-model-options", options.backend_models?.whisper || []);
  populateDatalist("whisper-device-options", options.whisper_devices || ["cpu", "cuda"]);
  populateDatalist("whisper-compute-options", options.whisper_compute_types || ["int8"]);
  populateDatalist("vosk-model-path-options", options.vosk_model_paths || []);
  populateDatalist("google-model-options", options.backend_models?.google || []);
  populateDatalist("aws-region-options", options.aws_regions || ["us-east-1"]);
  populateDatalist("aws-sso-start-url-options", options.aws_sso_start_urls || []);
  populateDatalist("aws-sso-region-options", options.aws_sso_regions || options.aws_regions || []);
  populateDatalist("azure-region-options", options.azure_regions || ["eastus"]);
  populateDatalist("aws-bucket-options", options.aws_bucket_hints || []);
  populateDatalist("azure-endpoint-options", options.azure_endpoint_hints || []);
  populateDatalist("dataset-options", options.datasets || []);
  populateDatalist("bench-backends-options", options.benchmark_backend_presets || []);
  populateDatalist("bench-chunk-sec-options", options.benchmark_chunk_sec_values || [0.8]);
  populateDatalist("bench-scenarios-options", options.benchmark_scenario_presets || []);
  populateDatalist("noise-levels-options", options.noise_level_presets || ["30,20,10,0"]);
  populateDatalist("reference-text-options", options.reference_texts || []);
  populateDatalist("record-sec-options", options.record_sec_values || [5.0]);
  populateDatalist("audio-device-options", options.audio_device_hints || ["default", "0", "1"]);
  populateDatalist("action-chunk-sec-options", options.action_chunk_sec_values || [0.8]);
  populateDatalist("request-timeout-options", options.request_timeout_values || [25.0]);
  populateDatalist("bringup-mic-sec-options", options.mic_capture_sec_values || [4.0]);
}

function applyBaseConfigDefaults(configPath, { announce = false } = {}) {
  const catalog = state.options?.defaults_by_config || {};
  const cfg = catalog[configPath];
  if (!cfg || typeof cfg !== "object") {
    return;
  }

  const asr = cfg.asr || {};
  const benchmark = cfg.benchmark || {};
  const backends = cfg.backends || {};
  const webCfg = cfg.web || {};

  setFieldValue("asr-backend", asr.backend);
  setFieldValue("language", asr.language);
  setFieldValue("sample-rate", asr.sample_rate);
  setFieldValue("chunk-ms", asr.chunk_ms);
  setFieldValue("input-mode", asr.input_mode);

  if (benchmark.scenarios) {
    $("bench-scenarios").value = csvFromAny(benchmark.scenarios);
  }
  setFieldValue("bench-chunk-sec", benchmark.chunk_sec);
  setCheckboxGroup("metric-select", benchmark.selected_metrics, state.options?.metrics || []);

  const whisper = backends.whisper || {};
  setFieldValue("whisper-model", whisper.model_size || whisper.model);
  setFieldValue("whisper-device", whisper.device);
  setFieldValue("whisper-compute", whisper.compute_type);

  const vosk = backends.vosk || {};
  setFieldValue("vosk-model-path", vosk.model_path);

  const google = backends.google || {};
  setFieldValue("google-model", google.model);

  const aws = backends.aws || {};
  setFieldValue("aws-region", aws.region);
  setFieldValue("aws-bucket", aws.s3_bucket);
  setFieldValue("secret-aws-sso-region", aws.region);

  const azure = backends.azure || {};
  setFieldValue("azure-region", azure.region);
  setFieldValue("azure-endpoint", azure.endpoint);

  setFieldValue("language-mode", webCfg.language_mode);
  setFieldValue("reference-text", webCfg.reference_text);
  setFieldValue("record-sec", webCfg.record_sec);
  setFieldValue("action-chunk-sec", webCfg.action_chunk_sec);
  setFieldValue("request-timeout", webCfg.request_timeout_sec);
  setFieldValue("noise-levels", webCfg.noise_levels);

  if (webCfg.interfaces) {
    setCheckboxGroup("interfaces", webCfg.interfaces, ["core"]);
  } else {
    setCheckboxGroup("interfaces", ["core"], ["core"]);
  }

  const modelRuns = deriveModelRunsFromConfig(cfg);
  if (modelRuns) {
    $("model-runs").value = modelRuns;
  }

  if (webCfg.benchmark_backends || webCfg.backends) {
    $("bench-backends").value = csvFromAny(webCfg.benchmark_backends || webCfg.backends);
  } else if (asr.backend) {
    $("bench-backends").value = String(asr.backend);
  }
  setFieldValue("dataset", webCfg.dataset);

  if (webCfg.ros_auto_launch !== undefined) {
    $("ros-auto-launch").checked = Boolean(webCfg.ros_auto_launch);
  }
  if (webCfg.action_streaming !== undefined) {
    $("action-streaming").checked = Boolean(webCfg.action_streaming);
  }

  if (webCfg.bringup_input_mode) {
    $("bringup-input-mode").value = String(webCfg.bringup_input_mode);
  }
  setFieldValue("bringup-mic-sec", webCfg.bringup_mic_capture_sec);
  if (webCfg.bringup_continuous !== undefined) {
    $("bringup-continuous").checked = Boolean(webCfg.bringup_continuous);
  }
  if (webCfg.bringup_live_stream_enabled !== undefined) {
    $("bringup-live-enabled").checked = Boolean(webCfg.bringup_live_stream_enabled);
  }
  if (webCfg.bringup_text_output_enabled !== undefined) {
    $("bringup-text-enabled").checked = Boolean(webCfg.bringup_text_output_enabled);
  }

  const preferredWav = String(webCfg.use_wav || asr.wav_path || "").trim();
  setSelectValueIfPresent("use-wav", preferredWav);
  setSelectValueIfPresent("noise-source", preferredWav);
  setSelectValueIfPresent("bringup-wav", String(webCfg.bringup_wav || preferredWav));

  if (announce) {
    const label = webCfg.scenario_label ? `${webCfg.scenario_label} (${configPath})` : configPath;
    setStatus(`Applied config preset: ${label}`);
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
  const region = $("aws-region").value.trim();
  if (!region) {
    return {};
  }
  return { aws_region: region };
}

function commonRequestEnvelope(payload) {
  return {
    profile_name: $("profile-name").value.trim(),
    base_config: $("base-config").value,
    runtime_overrides: collectRuntimeOverrides(),
    aws_auth_profile: selectedAwsAuthProfile(),
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
  const sourceValues = Array.from(
    new Set([
      "",
      ...(state.options?.sample_wavs || []),
      ...(payload.uploads || []),
      ...(payload.noisy || []),
    ]),
  );
  const displayValues = sourceValues.map((item) => item || "(none)");
  const defaultCfg = (state.options?.defaults_by_config || {})[$("base-config").value] || {};
  const fallbackWav = String(defaultCfg?.web?.use_wav || defaultCfg?.asr?.wav_path || "").trim();

  const mapForSelect = (id) => {
    const select = $(id);
    const previous = select.value;
    select.innerHTML = "";
    sourceValues.forEach((value, idx) => {
      const option = document.createElement("option");
      option.value = value;
      option.textContent = displayValues[idx];
      select.appendChild(option);
    });
    if (sourceValues.includes(previous)) {
      select.value = previous;
      return;
    }
    if (fallbackWav && sourceValues.includes(fallbackWav)) {
      select.value = fallbackWav;
    }
  };

  mapForSelect("noise-source");
  mapForSelect("use-wav");
  mapForSelect("bringup-wav");

  const uploadedCsv = (payload.uploads || []).filter((item) =>
    String(item).toLowerCase().endsWith(".csv"),
  );
  const datasets = [...(state.options?.datasets || []), ...uploadedCsv];
  populateDatalist("dataset-options", datasets);
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
    aws_auth_profile: selectedAwsAuthProfile(),
    aws_sso_start_url: $("secret-aws-sso-start-url").value.trim(),
    aws_sso_region: $("secret-aws-sso-region").value.trim(),
    runtime_overrides: collectRuntimeOverrides(),
    payload: {
      interfaces: checkedValues("interfaces").join(","),
      model_runs: $("model-runs").value.trim(),
      language_mode: $("language-mode").value,
      language: $("language").value.trim(),
      reference_text: $("reference-text").value.trim(),
      record_sec: asNumber($("record-sec").value, 5),
      sample_rate: asNumber($("sample-rate").value, 16000),
      use_wav: selectedFileOrEmpty("use-wav"),
      device: $("audio-device").value.trim(),
      action_chunk_sec: asNumber($("action-chunk-sec").value, 0.8),
      request_timeout_sec: asNumber($("request-timeout").value, 25),
      ros_auto_launch: $("ros-auto-launch").checked,
      action_streaming: $("action-streaming").checked,
      dataset: $("dataset").value.trim(),
      backends: $("bench-backends").value.trim(),
      scenarios: $("bench-scenarios").value.trim(),
      bringup_input_mode: $("bringup-input-mode").value,
      bringup_wav: selectedFileOrEmpty("bringup-wav"),
      bringup_mic_sec: asNumber($("bringup-mic-sec").value, 4.0),
      bringup_continuous: $("bringup-continuous").checked,
      bringup_live_enabled: $("bringup-live-enabled").checked,
      bringup_text_enabled: $("bringup-text-enabled").checked,
      noise_levels: $("noise-levels").value.trim(),
    },
  };
}

function applyProfilePayload(payload) {
  $("profile-name").value = payload.profile_name || "";
  setFieldValue("secret-aws-sso-start-url", payload.aws_sso_start_url);
  setFieldValue("secret-aws-sso-region", payload.aws_sso_region);
  if (payload.aws_auth_profile) {
    setSelectValueIfPresent("aws-auth-profile", payload.aws_auth_profile);
    $("aws-auth-name").value = String(payload.aws_auth_profile);
  }
  if (payload.base_config) {
    $("base-config").value = payload.base_config;
    applyBaseConfigDefaults(payload.base_config);
  }

  const runtime = payload.runtime_overrides || {};
  const asr = runtime.asr || {};
  const benchmark = runtime.benchmark || {};
  const backends = runtime.backends || {};

  setFieldValue("asr-backend", asr.backend);
  setFieldValue("language", asr.language);
  setFieldValue("sample-rate", asr.sample_rate);
  setFieldValue("chunk-ms", asr.chunk_ms);
  setFieldValue("input-mode", asr.input_mode);

  setFieldValue("bench-chunk-sec", benchmark.chunk_sec);
  if (benchmark.scenarios) {
    $("bench-scenarios").value = csvFromAny(benchmark.scenarios);
  }
  if (benchmark.selected_metrics) {
    setCheckboxGroup("metric-select", benchmark.selected_metrics, state.options?.metrics || []);
  }

  const whisper = backends.whisper || {};
  setFieldValue("whisper-model", whisper.model_size || whisper.model);
  setFieldValue("whisper-device", whisper.device);
  setFieldValue("whisper-compute", whisper.compute_type);

  const vosk = backends.vosk || {};
  setFieldValue("vosk-model-path", vosk.model_path);

  const google = backends.google || {};
  setFieldValue("google-model", google.model);

  const aws = backends.aws || {};
  setFieldValue("aws-region", aws.region);
  setFieldValue("aws-bucket", aws.s3_bucket);
  setFieldValue("secret-aws-sso-region", aws.region);

  const azure = backends.azure || {};
  setFieldValue("azure-region", azure.region);
  setFieldValue("azure-endpoint", azure.endpoint);

  const run = payload.payload || {};
  setFieldValue("model-runs", run.model_runs);
  setFieldValue("language-mode", run.language_mode);
  setFieldValue("language", run.language);
  setFieldValue("reference-text", run.reference_text);
  setFieldValue("record-sec", run.record_sec);
  setFieldValue("action-chunk-sec", run.action_chunk_sec);
  setFieldValue("request-timeout", run.request_timeout_sec);
  setFieldValue("dataset", run.dataset);
  setFieldValue("bench-backends", run.backends);
  setFieldValue("bench-scenarios", run.scenarios);
  setFieldValue("audio-device", run.device);
  setFieldValue("noise-levels", run.noise_levels);

  if (run.interfaces) {
    setCheckboxGroup("interfaces", run.interfaces, ["core"]);
  }

  if (run.ros_auto_launch !== undefined) {
    $("ros-auto-launch").checked = Boolean(run.ros_auto_launch);
  }
  if (run.action_streaming !== undefined) {
    $("action-streaming").checked = Boolean(run.action_streaming);
  }
  if (run.use_wav) {
    setSelectValueIfPresent("use-wav", run.use_wav);
  }

  if (run.bringup_input_mode) {
    $("bringup-input-mode").value = String(run.bringup_input_mode);
  }
  setFieldValue("bringup-mic-sec", run.bringup_mic_sec);
  if (run.bringup_wav) {
    setSelectValueIfPresent("bringup-wav", run.bringup_wav);
  }
  if (run.bringup_continuous !== undefined) {
    $("bringup-continuous").checked = Boolean(run.bringup_continuous);
  }
  if (run.bringup_live_enabled !== undefined) {
    $("bringup-live-enabled").checked = Boolean(run.bringup_live_enabled);
  }
  if (run.bringup_text_enabled !== undefined) {
    $("bringup-text-enabled").checked = Boolean(run.bringup_text_enabled);
  }
}

async function saveProfile() {
  const name = $("profile-name").value.trim();
  if (!name) {
    throw new Error("Set profile name first");
  }
  const response = await postJSON("/api/profiles", {
    name,
    payload: exportCurrentProfilePayload(),
  });
  setKnownProfiles(response.profiles || []);
  if (document.activeElement === $("profile-name")) {
    showProfileSuggestions();
  }
  setStatus(`Profile saved: ${name}`);
}

async function loadProfile() {
  const name = $("profile-name").value.trim();
  if (!name) {
    throw new Error("Set profile name first");
  }
  const response = await fetchJSON(`/api/profiles/${encodeURIComponent(name)}`);
  applyProfilePayload(response.payload || {});
  if (!$("profile-name").value.trim()) {
    $("profile-name").value = response.name || name;
  }
  hideProfileSuggestions();
  setStatus(`Profile loaded: ${name}`);
}

async function refreshAwsAuthProfiles({ keepSelection = true } = {}) {
  const [payload, options] = await Promise.all([
    fetchJSON("/api/aws-auth-profiles"),
    fetchJSON("/api/options"),
  ]);
  const names = normalizeAwsAuthProfileNames(payload.profiles || []);
  const selectValues = ["", ...names];
  const previous = keepSelection ? selectedAwsAuthProfile() : "";
  populateSelect("aws-auth-profile", selectValues, previous);
  populateDatalist("aws-sso-start-url-options", options.aws_sso_start_urls || []);
  populateDatalist("aws-sso-region-options", options.aws_sso_regions || options.aws_regions || []);
}

async function loadAwsAuthProfile() {
  const selected = selectedAwsAuthProfile() || $("aws-auth-name").value.trim();
  if (!selected) {
    throw new Error("Select AWS auth profile first");
  }
  const payload = await fetchJSON(`/api/aws-auth-profiles/${encodeURIComponent(selected)}`);
  $("aws-auth-name").value = payload.name || selected;
  $("aws-auth-text").value = payload.content || "";
  setSelectValueIfPresent("aws-auth-profile", payload.name || selected);
  applyAwsAuthValues(payload.values || {});
  setStatus(`AWS auth profile loaded: ${payload.name || selected}`);
}

async function saveAwsAuthProfile() {
  buildAwsAuthTextFromForm();
  const computedName = defaultAwsAuthProfileName();
  const name =
    $("aws-auth-name").value.trim() || selectedAwsAuthProfile() || computedName;
  if (!name) {
    throw new Error("Set AWS auth profile name first");
  }
  const content = $("aws-auth-text").value.trim();
  if (!content) {
    throw new Error("AWS auth text is empty");
  }
  const payload = await postJSON("/api/aws-auth-profiles", { name, content });
  await refreshAwsAuthProfiles({ keepSelection: false });
  setSelectValueIfPresent("aws-auth-profile", name);
  $("aws-auth-name").value = name;
  $("aws-auth-text").value = payload.content || `${content}\n`;
  setStatus(`AWS auth profile saved: ${name}`);
}

async function runAwsSsoLogin() {
  let authProfile =
    selectedAwsAuthProfile() || $("aws-auth-name").value.trim() || defaultAwsAuthProfileName();
  if (!selectedAwsAuthProfile()) {
    if (!$("aws-auth-text").value.trim()) {
      buildAwsAuthTextFromForm();
    }
    if (!$("aws-auth-name").value.trim()) {
      $("aws-auth-name").value = authProfile;
    }
    await saveAwsAuthProfile();
    authProfile = selectedAwsAuthProfile() || authProfile;
  }
  if (!authProfile) {
    throw new Error("Select AWS auth profile first");
  }
  setStatus(`Starting AWS SSO login: ${authProfile}`);
  const response = await postJSON("/api/aws-sso-login", {
    auth_profile: authProfile,
    use_device_code: true,
    no_browser: true,
  });
  state.selectedJobId = response.job.job_id;
  await refreshJobs();
  await loadSelectedJob();
  setStatus(`AWS SSO login started: ${response.job.job_id}. Open Logs and follow URL/code.`);
}

async function bootstrap() {
  setStatus("Loading options...");
  const options = await fetchJSON("/api/options");
  state.options = options;

  const baseConfigs = options.base_configs || ["configs/default.yaml"];
  const defaultBase = baseConfigs.includes("configs/default.yaml")
    ? "configs/default.yaml"
    : baseConfigs[0];
  populateSelect("base-config", baseConfigs, defaultBase);

  populateSelect("asr-backend", options.backends || ["mock"], "mock");
  populateSelect("language-mode", options.language_modes || ["config", "manual", "auto"], "config");
  populateSelect("input-mode", options.input_modes || ["auto", "mic", "file"], "auto");
  populateSelect("bringup-input-mode", options.input_modes || ["auto", "mic", "file"], "mic");
  populateSelect("aws-auth-profile", ["", ...(options.aws_auth_profiles || [])], "");
  setKnownProfiles(options.profiles || []);
  populateStaticDatalists(options);

  renderCheckboxGroup($("interfaces"), options.interfaces || [], "iface", ["core"]);
  renderCheckboxGroup($("metric-select"), options.metrics || [], "metric", options.metrics || []);

  await refreshFiles();
  await refreshAwsAuthProfiles();
  applyBaseConfigDefaults($("base-config").value);
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
    await refreshSavedProfiles();
    await refreshAwsAuthProfiles();
    await refreshFiles();
    await refreshJobs();
    await loadSelectedJob();
    setStatus("Refreshed");
  };

  $("base-config").addEventListener("change", () => {
    applyBaseConfigDefaults($("base-config").value, { announce: true });
  });

  $("profile-name").addEventListener("focus", () => {
    showProfileSuggestions();
  });

  $("profile-name").addEventListener("input", () => {
    showProfileSuggestions();
  });

  $("profile-name").addEventListener("keydown", (event) => {
    if (event.key === "ArrowDown") {
      event.preventDefault();
      moveProfileSuggestion(1);
      return;
    }
    if (event.key === "ArrowUp") {
      event.preventDefault();
      moveProfileSuggestion(-1);
      return;
    }
    if (event.key === "Enter" && state.profileAutocomplete.open) {
      if (selectActiveProfileSuggestion()) {
        event.preventDefault();
      }
      return;
    }
    if (event.key === "Escape") {
      hideProfileSuggestions();
    }
  });

  document.addEventListener("mousedown", (event) => {
    const target = event.target;
    if (!(target instanceof Element)) {
      return;
    }
    const input = $("profile-name");
    const panel = $("profile-name-suggestions");
    if (target === input || panel.contains(target)) {
      return;
    }
    hideProfileSuggestions();
  });

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

  $("load-aws-auth").onclick = async () => {
    try {
      await loadAwsAuthProfile();
    } catch (error) {
      setStatus(`Load AWS auth failed: ${error.message}`);
    }
  };

  $("build-aws-auth").onclick = async () => {
    try {
      buildAwsAuthTextFromForm();
      if (!$("aws-auth-name").value.trim()) {
        $("aws-auth-name").value = defaultAwsAuthProfileName();
      }
      setStatus("AWS auth text built from GUI fields");
    } catch (error) {
      setStatus(`Build AWS auth failed: ${error.message}`);
    }
  };

  $("save-aws-auth").onclick = async () => {
    try {
      await saveAwsAuthProfile();
    } catch (error) {
      setStatus(`Save AWS auth failed: ${error.message}`);
    }
  };

  $("aws-sso-login").onclick = async () => {
    try {
      await runAwsSsoLogin();
    } catch (error) {
      setStatus(`AWS SSO login failed: ${error.message}`);
    }
  };

  $("aws-auth-profile").addEventListener("change", () => {
    const selected = selectedAwsAuthProfile();
    if (selected) {
      $("aws-auth-name").value = selected;
    }
  });
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
