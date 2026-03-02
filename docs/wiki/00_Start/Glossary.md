# Glossary

Единый словарь терминов проекта с короткими примерами.

## ASR

Что это: распознавание речи (Automatic Speech Recognition).
Где в вики: [[01_Architecture/System_Overview]], [[02_ROS2/ROS2_Index]].
Пример: `ros2 service call /asr/recognize_once ...`.

## Runtime Config

Что это: итоговый YAML конфиг, который реально потребляют runtime-процессы.
Где в вики: [[08_Data_Configs/Configs_Overview]], [[07_Tooling/Web_GUI_Control_Center]].
Пример: `web_gui/runtime_configs/20260302_230224_first-try.yaml`.

## Base Config

Что это: базовый YAML (обычно `configs/default.yaml` или `configs/live_mic_whisper.yaml`), поверх которого накладываются overrides.
Где в вики: [[08_Data_Configs/Default_Config]], [[08_Data_Configs/Live_Mic_Whisper_Config]].
Пример: запуск с `config:=configs/live_mic_whisper.yaml`.

## Runtime Overrides

Что это: частичные параметры, которыми перекрывают базовый конфиг на конкретный прогон.
Где в вики: [[07_Tooling/Web_GUI_Control_Center]], [[02_ROS2/Launch_Bringup]].
Пример: `sample_rate:=16000 chunk_ms:=800`.

## Backend

Что это: провайдер распознавания (`mock`, `vosk`, `whisper`, `google`, `aws`, `azure`).
Где в вики: [[04_Backends/Backends_Index]], [[04_Backends/Capabilities_Matrix]].
Пример: `ros2 service call /asr/set_backend ... "{backend: whisper, model: large-v3, region: local}"`.

## Model Run Spec

Что это: формат выбора прогона `backend[:model][@region]`.
Где в вики: [[06_Operations/Live_Sample_Eval_Playbook]], [[07_Tooling/Scripts/Live_Sample_Eval_Script]].
Пример: `whisper:tiny@local`, `google:latest_long@us-central1`, `mock`.

## Language Mode

Что это: способ выбора языка в live sample eval:
- `manual` (явно заданный код),
- `auto` (автоопределение),
- `config` (из YAML).
Где в вики: [[06_Operations/Live_Sample_Eval_Playbook]], [[07_Tooling/Web_GUI_Control_Center]].
Пример: `--language-mode auto`.

## Input Mode

Что это: источник аудио для `audio_capture_node`.
Где в вики: [[02_ROS2/Node_Audio_Capture]], [[02_ROS2/Launch_Bringup]].
Пример: `input_mode:=mic` или `input_mode:=file wav_path:=data/sample/en_hello.wav`.

## Sample Rate

Что это: частота дискретизации аудио (Гц).
Где в вики: [[02_ROS2/Launch_Bringup]], [[06_Operations/Live_Sample_Eval_Playbook]].
Пример: `--sample-rate 16000`.

## Chunk (ms/sec)

Что это: размер порции аудио в потоке.
Где в вики: [[02_ROS2/Node_Audio_Capture]], [[06_Operations/Live_Sample_Eval_Playbook]].
Пример: `chunk_ms:=800`, `--action-chunk-sec 0.8`.

## Interface core

Что это: прямой вызов backend через Python core без ROS transport.
Где в вики: [[07_Tooling/Scripts/Live_Sample_Eval_Script]], [[03_Core/Core_Index]].
Пример: `--interfaces core`.

## Interface ros_service

Что это: прогон через сервисы `/asr/set_backend` + `/asr/recognize_once`.
Где в вики: [[02_ROS2/Service_Set_Backend]], [[02_ROS2/Service_Recognize_Once]].
Пример: `--interfaces ros_service`.

## Interface ros_action

Что это: прогон через action `/asr/transcribe` (streaming/non-streaming).
Где в вики: [[02_ROS2/Action_Transcribe]], [[07_Tooling/Scripts/Live_Sample_Eval_Script]].
Пример: `--interfaces ros_action --action-streaming`.

## ROS Auto Launch

Что это: автозапуск ROS bringup из live sample eval.
Где в вики: [[06_Operations/Live_Sample_Eval_Playbook]], [[07_Tooling/Web_GUI_Control_Center]].
Пример: `--ros-auto-launch`.

## Action Streaming

Что это: режим action, где результат отдается как поток feedback + финал.
Где в вики: [[02_ROS2/Action_Transcribe]], [[07_Tooling/Scripts/Live_Sample_Eval_Script]].
Пример: `--action-streaming`.

## Request Timeout

Что это: ограничение ожидания ответа интерфейса.
Где в вики: [[07_Tooling/Scripts/Live_Sample_Eval_Script]], [[07_Tooling/Web_GUI_Control_Center]].
Пример: `--request-timeout-sec 25`.

## Bringup

Что это: основной ROS2 launch-контур для live работы.
Где в вики: [[02_ROS2/Launch_Bringup]], [[06_Operations/Live_Run_Playbook]].
Пример: `ros2 launch asr_ros bringup.launch.py config:=configs/live_mic_whisper.yaml input_mode:=mic`.

## Topic asr_audio_chunks

Что это: поток PCM-чанков от `audio_capture_node` к `asr_server_node`.
Где в вики: [[02_ROS2/Topic_Audio_Chunks]], [[02_ROS2/Runtime_Flow]].
Пример: размер/частота задаются `chunk_ms` + `sample_rate`.

## Topic asr_text

Что это: структурированный результат распознавания (`AsrResult`).
Где в вики: [[02_ROS2/Topic_Asr_Text]], [[02_ROS2/Node_ASR_Server]].
Пример: содержит `text`, `confidence`, `timings`, `error_code`.

## Topic asr_text_plain

Что это: plain-text канал для удобного чтения в терминале/UI (`std_msgs/String`).
Где в вики: [[02_ROS2/Topic_Asr_Text]], [[02_ROS2/Node_ASR_Text_Output]].
Пример: `ros2 topic echo /asr/text/plain --qos-durability transient_local --qos-reliability reliable`.

## Node asr_text_output_node

Что это: отдельная нода, которая репаблишит `/asr/text` в `/asr/text/plain`.
Где в вики: [[02_ROS2/Node_ASR_Text_Output]], [[02_ROS2/Launch_Bringup]].
Пример: включается аргументом `text_output_enabled:=true`.

## Launch Arg text_output_enabled

Что это: флаг запуска/отключения `asr_text_output_node` в `bringup.launch.py`.
Где в вики: [[02_ROS2/Launch_Bringup]], [[06_Operations/Troubleshooting_Playbook]].
Пример: `ros2 launch ... text_output_enabled:=false`.

## Topic asr_metrics

Что это: метрики прогона (`AsrMetrics`).
Где в вики: [[02_ROS2/Topic_Asr_Metrics]], [[05_Metrics_Benchmark/Metrics_Collector]].
Пример: `ros2 topic echo /asr/metrics`.

## QoS transient_local

Что это: политика DDS, при которой поздний подписчик получает последний опубликованный message.
Где в вики: [[02_ROS2/Topic_Asr_Text]], [[06_Operations/Troubleshooting_Playbook]].
Пример: `--qos-durability transient_local --qos-reliability reliable`.

## Dataset CSV Manifest

Что это: CSV файл для benchmark runner (пути WAV, референс-тексты, параметры сценариев).
Где в вики: [[05_Metrics_Benchmark/Dataset_And_Scenarios]], [[07_Tooling/Web_GUI_Control_Center]].
Пример: `data/transcripts/sample_manifest.csv`.

## Scenario

Что это: условия прогона (например `clean`, `snr20`, `snr10`, `snr0`).
Где в вики: [[05_Metrics_Benchmark/Dataset_And_Scenarios]], [[07_Tooling/Web_GUI_Control_Center]].
Пример: `--scenarios clean,snr20,snr10,snr0`.

## SNR

Что это: Signal-to-Noise Ratio для шумовых сценариев.
Где в вики: [[05_Metrics_Benchmark/Dataset_And_Scenarios]], [[07_Tooling/Web_GUI_Control_Center]].
Пример: генерация noisy WAV с уровнями `30,20,10,0`.

## Artifact

Что это: выходные файлы запусков (CSV/JSON/MD/PNG/WAV/log).
Где в вики: [[05_Metrics_Benchmark/Results_Artifacts]], [[07_Tooling/Web_GUI_Control_Center]].
Пример: `results/live_sample/<timestamp>/summary.md`.

## Preflight

Что это: набор проверок готовности окружения (модули, микрофон, ROS setup).
Где в вики: [[07_Tooling/Web_GUI_Control_Center]], [[06_Operations/Troubleshooting_Playbook]].
Пример: кнопка `Preflight` в GUI перед запуском jobs.

## Job

Что это: фоновая задача GUI (live sample, benchmark, ros bringup) с логом и статусом.
Где в вики: [[07_Tooling/Web_GUI_Control_Center]].
Пример: `kind=live_sample`, `status=running|succeeded|failed|stopped`.

## WER

Что это: Word Error Rate, доля ошибок по словам.
Где в вики: [[05_Metrics_Benchmark/Quality_Metrics]], [[02_ROS2/Topic_Asr_Metrics]].
Пример: `WER=0.05` означает ~5% ошибок по словам.

## CER

Что это: Character Error Rate, доля ошибок по символам.
Где в вики: [[05_Metrics_Benchmark/Quality_Metrics]], [[02_ROS2/Topic_Asr_Metrics]].
Пример: `CER=0.02`.

## Latency

Что это: задержка получения результата распознавания (обычно мс).
Где в вики: [[02_ROS2/Topic_Asr_Metrics]], [[05_Metrics_Benchmark/System_Metrics]].
Пример: `latency_ms=780`.

## RTF

Что это: Real-Time Factor (время распознавания / длина аудио).
Где в вики: [[02_ROS2/Topic_Asr_Metrics]], [[05_Metrics_Benchmark/System_Metrics]].
Пример: `RTF=0.4` быстрее реального времени.

## Success Rate

Что это: доля успешных прогонов без ошибок backend/runtime.
Где в вики: [[05_Metrics_Benchmark/Metrics_Collector]], [[07_Tooling/Web_GUI_Control_Center]].
Пример: `success_rate=0.98`.

## Cost Estimate

Что это: оценка стоимости распознавания (актуально для cloud backends).
Где в вики: [[02_ROS2/Topic_Asr_Metrics]], [[05_Metrics_Benchmark/System_Metrics]].
Пример: `cost_estimate=0.0025` за запрос.
