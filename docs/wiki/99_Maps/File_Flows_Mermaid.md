# File Flows (Mermaid)

Диаграммы ниже показывают, какие именно файлы в `ros2_ws/src` участвуют
в основных runtime-сценариях.

## 1) Live Bringup: mic/file -> /asr/text/plain + /asr/metrics

```mermaid
flowchart LR
  L["asr_ros/launch/bringup.launch.py"]
  A["asr_ros/asr_ros/audio_capture_node.py"]
  S["asr_ros/asr_ros/asr_server_node.py"]
  T["asr_ros/asr_ros/asr_text_output_node.py"]
  C["asr_ros/asr_ros/converters.py"]
  F["asr_core/asr_core/factory.py"]
  B["asr_backend_*/asr_backend_*/backend.py"]
  M["asr_metrics/asr_metrics/collector.py"]
  SYS["asr_metrics/asr_metrics/system.py"]
  Q["asr_metrics/asr_metrics/quality.py"]
  TOP1["/asr/audio_chunks"]
  TOP2["/asr/text (AsrResult)"]
  TOP3["/asr/text/plain (String)"]
  TOP4["/asr/metrics (AsrMetrics)"]

  L --> A
  L --> S
  L --> T
  A --> TOP1 --> S
  S --> F --> B
  S --> C
  S --> M
  M --> SYS
  M --> Q
  S --> TOP2 --> T --> TOP3
  S --> TOP4
```

## 2) Service Path: /asr/recognize_once + /asr/set_backend

```mermaid
flowchart LR
  SRV1["asr_interfaces/srv/RecognizeOnce.srv"]
  SRV2["asr_interfaces/srv/SetAsrBackend.srv"]
  S["asr_ros/asr_ros/asr_server_node.py"]
  MOD["asr_core/asr_core/models.py"]
  F["asr_core/asr_core/factory.py"]
  B["asr_backend_*/asr_backend_*/backend.py"]
  CONV["asr_ros/asr_ros/converters.py"]
  RES["asr_interfaces/msg/AsrResult.msg"]
  MET["asr_interfaces/msg/AsrMetrics.msg"]

  SRV2 --> S
  S --> F --> B

  SRV1 --> S
  S --> MOD
  S --> B
  S --> CONV --> RES
  S --> CONV --> MET
```

## 3) Action Path: /asr/transcribe (streaming/non-streaming)

```mermaid
flowchart LR
  ACT["asr_interfaces/action/Transcribe.action"]
  S["asr_ros/asr_ros/asr_server_node.py"]
  AU["asr_core/asr_core/audio.py (wav_pcm_chunks)"]
  B["asr_backend_*/asr_backend_*/backend.py"]
  CONV["asr_ros/asr_ros/converters.py"]
  RES["AsrResult.msg"]
  MET["AsrMetrics.msg"]

  ACT --> S
  S --> AU
  S --> B
  S --> CONV --> RES
  S --> CONV --> MET
```

## 4) Benchmark Pipeline: dataset/scenarios -> CSV/JSON/plots

```mermaid
flowchart LR
  R["asr_benchmark/asr_benchmark/runner.py"]
  D["asr_benchmark/asr_benchmark/dataset.py"]
  N["asr_benchmark/asr_benchmark/noise.py"]
  CFG["asr_core/asr_core/config.py"]
  F["asr_core/asr_core/factory.py"]
  B["asr_backend_*/asr_backend_*/backend.py"]
  MC["asr_metrics/asr_metrics/collector.py"]
  IO["asr_metrics/asr_metrics/io.py"]
  P["asr_metrics/asr_metrics/plotting.py"]
  OUT1["benchmark_results.csv"]
  OUT2["benchmark_results.json"]
  OUT3["plots/*.png"]

  R --> CFG
  R --> D
  R --> N
  R --> F --> B
  R --> MC
  R --> IO --> OUT1
  R --> IO --> OUT2
  R --> P --> OUT3
```

## 5) Interfaces Build Flow (type generation)

```mermaid
flowchart LR
  CMAKE["asr_interfaces/CMakeLists.txt"]
  MSG1["msg/AsrResult.msg"]
  MSG2["msg/AsrMetrics.msg"]
  MSG3["msg/WordTimestamp.msg"]
  SRV1["srv/RecognizeOnce.srv"]
  SRV2["srv/SetAsrBackend.srv"]
  SRV3["srv/GetAsrStatus.srv"]
  ACT["action/Transcribe.action"]
  GEN["rosidl generated Python/C++ interfaces"]
  ROS["asr_ros nodes + benchmark + clients"]

  CMAKE --> MSG1 --> GEN
  CMAKE --> MSG2 --> GEN
  CMAKE --> MSG3 --> GEN
  CMAKE --> SRV1 --> GEN
  CMAKE --> SRV2 --> GEN
  CMAKE --> SRV3 --> GEN
  CMAKE --> ACT --> GEN
  GEN --> ROS
```

## Связанные

- [[99_Maps/Project_Map]]
- [[99_Maps/Runtime_Map]]
- [[99_Maps/Code_Map]]
- [[02_ROS2/Runtime_Flow]]
