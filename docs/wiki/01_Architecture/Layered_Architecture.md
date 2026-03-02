# Layered Architecture

## Layer 1: Interfaces

- ROS msg/srv/action: [[02_ROS2/Interfaces_Overview]]
- Core dataclasses: [[03_Core/Core_Models]]

## Layer 2: ASR Core

- Backend contract: [[03_Core/Backend_Interface]]
- Factory + registry: [[03_Core/Backend_Factory]]

## Layer 3: Backend Implementations

- Local: [[04_Backends/Mock_Backend]], [[04_Backends/Vosk_Backend]], [[04_Backends/Whisper_Backend]]
- Cloud: [[04_Backends/Google_Backend]], [[04_Backends/AWS_Backend]], [[04_Backends/Azure_Backend]]

## Layer 4: ROS Runtime

- [[02_ROS2/Node_ASR_Server]]
- [[02_ROS2/Node_Audio_Capture]]
- [[02_ROS2/Launch_Bringup]]

## Layer 5: Evaluation & Docs

- [[05_Metrics_Benchmark/Benchmark_Runner]]
- [[10_Archviz/Archviz_All_Command]]
