# Thesis Scope

This project is a bachelor thesis prototype focused on analysis, integration
and experimental evaluation of automatic speech recognition systems for
ROS2-based robotic applications.

The goal is not to build a production ASR cloud platform, but to provide:

1. a ROS2-compatible ASR runtime,
2. interchangeable provider adapters,
3. a web/operator interface,
4. a reproducible benchmark pipeline,
5. experimental comparison of selected commercial and non-commercial ASR solutions.

## Target Environment

- Ubuntu 24.04
- ROS2 Jazzy
- COCOHRIP / robotic laboratory environment

## Evaluated ASR Families

- local open-source: Whisper, Vosk, Hugging Face local models
- cloud/commercial: Azure Speech, Google Speech-to-Text, Amazon Transcribe,
  Hugging Face Inference API

## Primary Evaluation Families

- recognition quality
- latency and real-time capability
- resource usage
- robustness
- cost and deployment feasibility

## In Scope

- ROS2-compatible ASR runtime and message/service integration
- provider adapters for selected local and cloud ASR systems
- operator-facing web GUI for configuration, execution and inspection
- reproducible benchmark profiles and stored run artifacts
- thesis tables for quality, performance, resource, robustness, cost and
  scenario suitability

## Out Of Scope

- production-grade multi-tenant ASR cloud service
- guaranteed statistical conclusions beyond the tested sample set
- training new ASR models from scratch
- committing or distributing provider credentials
- replacing provider-native billing, quota or reliability guarantees

## COCOHRIP / Robotic Lab Mapping

The prototype maps ASR providers into a ROS2 workflow where audio can be
captured, transcribed and evaluated as part of robotic operator interaction.
The benchmark layer is designed to compare whether a provider is suitable for
local embedded-style use, cloud-assisted transcription, batch analytics or
dialog-oriented operator interfaces in a COCOHRIP-like laboratory setting.
