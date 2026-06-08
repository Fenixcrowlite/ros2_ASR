"""ROS topic/service namespace constants for ASR platform."""

from __future__ import annotations

RUNTIME_NS = "/asr/runtime"
PROVIDERS_NS = "/asr/providers"
STATUS_NS = "/asr/status"
BENCHMARK_NS = "/benchmark"
DATASETS_NS = "/datasets"
CONFIG_NS = "/config"
GATEWAY_NS = "/gateway"

TOPICS = {
    "raw_audio": f"{RUNTIME_NS}/audio/raw",
    "preprocessed_audio": f"{RUNTIME_NS}/audio/preprocessed",
    "vad_activity": f"{RUNTIME_NS}/vad/activity",
    "speech_segments": f"{RUNTIME_NS}/audio/segments",
    "partial_results": f"{RUNTIME_NS}/results/partial",
    "final_results": f"{RUNTIME_NS}/results/final",
    "node_status": f"{STATUS_NS}/nodes",
    "session_status": f"{STATUS_NS}/sessions",
    "benchmark_status": f"{BENCHMARK_NS}/status",
    "benchmark_events": f"{BENCHMARK_NS}/events",
}
