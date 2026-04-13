from __future__ import annotations

import json
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml  # type: ignore[import-untyped]
from asr_core.normalized import LatencyMetadata, NormalizedAsrResult, NormalizedWord
from asr_provider_base.adapter import AsrProviderAdapter
from asr_provider_base.capabilities import ProviderCapabilities
from asr_provider_base.models import ProviderAudio, ProviderStatus
from asr_storage import ArtifactStore


@dataclass(slots=True)
class GatewayResponse:
    success: bool
    message: str
    payload: dict[str, Any]


def make_normalized_result(
    *,
    provider_id: str = "fake",
    session_id: str = "session_demo",
    request_id: str = "req_demo",
    text: str = "hello world",
    degraded: bool = False,
    error_code: str = "",
    error_message: str = "",
    latency_ms: float = 15.0,
) -> NormalizedAsrResult:
    return NormalizedAsrResult(
        request_id=request_id,
        session_id=session_id,
        provider_id=provider_id,
        text=text,
        is_final=True,
        is_partial=False,
        utterance_start_sec=0.0,
        utterance_end_sec=0.8,
        words=[
            NormalizedWord(
                word="hello",
                start_sec=0.0,
                end_sec=0.4,
                confidence=0.91,
                confidence_available=True,
            ),
            NormalizedWord(
                word="world",
                start_sec=0.41,
                end_sec=0.8,
                confidence=0.93,
                confidence_available=True,
            ),
        ],
        confidence=0.92,
        confidence_available=True,
        timestamps_available=True,
        language="en-US",
        language_detected=False,
        latency=LatencyMetadata(total_ms=latency_ms, finalization_ms=3.0),
        raw_metadata_ref="artifact://fake/raw",
        degraded=degraded,
        error_code=error_code,
        error_message=error_message,
        tags=["fake"],
    )


class FakeProviderAdapter(AsrProviderAdapter):
    provider_id = "fake"

    def __init__(
        self,
        *,
        provider_id: str | None = None,
        supports_streaming: bool = True,
        streaming_mode: str = "native",
        supports_partials: bool | None = None,
        requires_network: bool = False,
    ) -> None:
        self.provider_id = provider_id or type(self).provider_id
        self._supports_streaming = supports_streaming
        self._streaming_mode = streaming_mode if supports_streaming else "none"
        self._supports_partials = (
            supports_streaming if supports_partials is None else bool(supports_partials)
        )
        self._requires_network = requires_network
        self._config: dict[str, Any] = {}
        self._credentials: dict[str, str] = {}
        self._stream_chunks: list[bytes] = []
        self._stream_session_id = "stream"
        self._stream_request_id = "stream"
        self._stream_started_at = 0.0
        self._status = ProviderStatus(provider_id=provider_id, state="created")

    def initialize(self, config: dict[str, Any], credentials_ref: dict[str, str]) -> None:
        self._config = dict(config)
        self._credentials = dict(credentials_ref)
        self._status = ProviderStatus(provider_id=self.provider_id, state="initialized")

    def validate_config(self) -> list[str]:
        if self._config.get("invalid"):
            return ["invalid config requested by test fixture"]
        if (
            self._requires_network
            and not self._credentials
            and not self._config.get("allow_anonymous")
        ):
            return ["network provider requires credentials"]
        return []

    def discover_capabilities(self) -> ProviderCapabilities:
        return ProviderCapabilities(
            supports_streaming=self._supports_streaming,
            streaming_mode=self._streaming_mode if self._supports_streaming else "none",
            supports_batch=True,
            supports_word_timestamps=True,
            supports_partials=self._supports_partials if self._supports_streaming else False,
            supports_confidence=True,
            supports_language_auto_detect=not self._requires_network,
            supports_cpu=True,
            supports_gpu=not self._requires_network,
            requires_network=self._requires_network,
            cost_model_type="cloud" if self._requires_network else "local",
        )

    def recognize_once(
        self,
        audio: ProviderAudio,
        options: dict[str, Any] | None = None,
    ) -> NormalizedAsrResult:
        del options
        text = str(audio.metadata.get("text_override", "hello world"))
        self._status = ProviderStatus(
            provider_id=self.provider_id, state="ready", message="recognize_once"
        )
        return make_normalized_result(
            provider_id=self.provider_id,
            session_id=audio.session_id,
            request_id=audio.request_id,
            text=text,
        )

    def start_stream(self, options: dict[str, Any] | None = None) -> None:
        opts = options or {}
        self._stream_chunks = []
        self._stream_session_id = str(opts.get("session_id", "stream") or "stream")
        self._stream_request_id = str(opts.get("request_id", "stream") or "stream")
        self._stream_started_at = time.perf_counter()
        self._status = ProviderStatus(provider_id=self.provider_id, state="streaming")

    def push_audio(self, chunk: bytes) -> NormalizedAsrResult | None:
        self._stream_chunks.append(chunk)
        if not self._supports_streaming or not self._supports_partials:
            return None
        return NormalizedAsrResult(
            request_id=self._stream_request_id,
            session_id=self._stream_session_id,
            provider_id=self.provider_id,
            text=f"partial {len(self._stream_chunks)}",
            is_final=False,
            is_partial=True,
            language="en-US",
            latency=LatencyMetadata(
                total_ms=(time.perf_counter() - self._stream_started_at) * 1000.0
                if self._stream_started_at
                else 0.0,
                first_partial_ms=5.0,
            ),
            confidence=0.0,
            confidence_available=False,
            timestamps_available=False,
        )

    def stop_stream(self) -> NormalizedAsrResult:
        self._status = ProviderStatus(provider_id=self.provider_id, state="ready")
        return make_normalized_result(
            provider_id=self.provider_id,
            session_id=self._stream_session_id,
            request_id=self._stream_request_id,
            text=f"stream {len(self._stream_chunks)} chunks",
        )

    def get_status(self) -> ProviderStatus:
        return self._status

    def teardown(self) -> None:
        self._status = ProviderStatus(provider_id=self.provider_id, state="stopped")


def build_stub_provider_manager(configs_root: str):
    class StubProviderManager:
        def __init__(self, configs_root: str = configs_root) -> None:
            self.configs_root = configs_root

        def resolve_profile_payload(self, provider_profile: str) -> dict[str, Any]:
            profile_id = (
                provider_profile.split("/", 1)[1]
                if provider_profile.startswith("providers/")
                else provider_profile
            )
            profile_path = Path(self.configs_root) / "providers" / f"{profile_id}.yaml"
            return yaml.safe_load(profile_path.read_text(encoding="utf-8")) or {}

        def create_from_profile(
            self,
            provider_profile: str,
            *,
            preset_id: str = "",
            settings_overrides: dict[str, Any] | None = None,
        ) -> FakeProviderAdapter:
            payload = self.resolve_profile_payload(provider_profile)
            provider_id = str(payload.get("provider_id", "fake")).strip() or "fake"
            settings = (
                payload.get("settings", {}) if isinstance(payload.get("settings"), dict) else {}
            )
            if preset_id:
                ui = payload.get("ui", {}) if isinstance(payload.get("ui"), dict) else {}
                model_presets = (
                    ui.get("model_presets", {})
                    if isinstance(ui.get("model_presets", {}), dict)
                    else {}
                )
                preset = model_presets.get(preset_id, {}) if isinstance(model_presets, dict) else {}
                if isinstance(preset, dict) and isinstance(preset.get("settings"), dict):
                    settings.update(preset.get("settings", {}))
            if settings_overrides:
                settings.update(settings_overrides)
            credentials_ref = str(payload.get("credentials_ref", "")).strip()
            supports_streaming = provider_id in {"vosk", "google", "azure", "aws"}
            requires_network = provider_id in {"azure", "google", "aws", "huggingface_api"}
            provider = FakeProviderAdapter(
                provider_id=provider_id,
                supports_streaming=supports_streaming,
                streaming_mode="native" if supports_streaming else "none",
                supports_partials=supports_streaming,
                requires_network=requires_network,
            )
            credentials = {"ref": credentials_ref} if credentials_ref else {}
            provider.initialize(settings, credentials)
            errors = provider.validate_config()
            if errors:
                raise ValueError("; ".join(errors))
            return provider

    return StubProviderManager


@dataclass(slots=True)
class FakeGatewayRosClient:
    project_root: Path
    runtime_started: bool = False
    runtime_profile: str = "default_runtime"
    provider_profile: str = "providers/whisper_local"
    session_id: str = ""
    audio_source: str = "file"
    fail_recognize: bool = False
    fail_validate: bool = False
    _benchmark_status: dict[str, dict[str, Any]] = field(default_factory=dict)
    _runtime_results: list[dict[str, Any]] = field(default_factory=list)
    _runtime_partials: list[dict[str, Any]] = field(default_factory=list)
    provider_preset: str = ""
    provider_settings: dict[str, Any] = field(default_factory=dict)
    processing_mode: str = "segmented"

    def __post_init__(self) -> None:
        return None

    def _runtime_capabilities(self) -> tuple[bool, str]:
        provider_key = str(self.provider_profile or "").split("/")[-1]
        if provider_key.startswith(("azure", "google", "aws", "vosk")):
            return True, "native"
        return False, "none"

    def start_runtime(
        self,
        runtime_profile: str,
        provider_profile: str,
        session_id: str,
        *,
        processing_mode: str = "",
        provider_preset: str = "",
        provider_settings: dict[str, Any] | None = None,
        audio_source: str = "",
        audio_file_path: str = "",
        language: str = "",
        mic_capture_sec: float = 0.0,
    ) -> GatewayResponse:
        if self.runtime_started:
            return GatewayResponse(False, "runtime session already active", {})
        self.runtime_started = True
        self.runtime_profile = runtime_profile
        self.provider_profile = provider_profile
        self.provider_preset = provider_preset
        self.provider_settings = dict(provider_settings or {})
        self.processing_mode = processing_mode or "segmented"
        self.session_id = session_id or "session_demo"
        self.audio_source = audio_source or "file"
        return GatewayResponse(
            True,
            "runtime started",
            {
                "session_id": self.session_id,
                "resolved": "configs/resolved/runtime__default_runtime.json",
                "provider_preset": provider_preset,
                "provider_settings": dict(provider_settings or {}),
                "processing_mode": self.processing_mode,
                "audio_file_path": audio_file_path,
                "language": language,
                "mic_capture_sec": mic_capture_sec,
            },
        )

    def stop_runtime(self, session_id: str) -> GatewayResponse:
        if not self.runtime_started:
            return GatewayResponse(False, "runtime session is not active", {})
        if session_id and session_id != self.session_id:
            return GatewayResponse(False, f"unknown session: {session_id}", {})
        self.runtime_started = False
        return GatewayResponse(True, "runtime stopped", {})

    def reconfigure_runtime(
        self,
        session_id: str,
        runtime_profile: str,
        provider_profile: str,
        *,
        processing_mode: str = "",
        provider_preset: str = "",
        provider_settings: dict[str, Any] | None = None,
        audio_source: str = "",
        audio_file_path: str = "",
        language: str = "",
        mic_capture_sec: float = 0.0,
    ) -> GatewayResponse:
        if self.runtime_started and session_id and session_id != self.session_id:
            return GatewayResponse(False, f"unknown session: {session_id}", {})
        self.runtime_profile = runtime_profile
        self.provider_profile = provider_profile
        self.provider_preset = provider_preset or self.provider_preset
        self.provider_settings = dict(provider_settings or self.provider_settings)
        self.processing_mode = processing_mode or self.processing_mode
        if audio_source:
            self.audio_source = audio_source
        return GatewayResponse(
            True,
            "runtime reconfigured",
            {
                "resolved": "configs/resolved/runtime__default_runtime.json",
                "provider_preset": self.provider_preset,
                "provider_settings": self.provider_settings,
                "processing_mode": self.processing_mode,
                "audio_file_path": audio_file_path,
                "language": language,
                "mic_capture_sec": mic_capture_sec,
            },
        )

    def recognize_once(
        self,
        wav_path: str,
        language: str,
        session_id: str,
        provider_profile: str,
        *,
        provider_preset: str = "",
        provider_settings: dict[str, Any] | None = None,
    ) -> GatewayResponse:
        if self.fail_recognize:
            return GatewayResponse(False, "recognize failed", {})
        active_session = session_id or self.session_id or "session_demo"
        payload = {
            "request_id": "req_demo",
            "text": f"recognized from {Path(wav_path).name} ({language})",
            "provider_id": provider_profile.split("/")[-1].replace("_local", ""),
            "success": True,
            "error_code": "",
            "error_message": "",
            "resolved_profile": provider_profile,
            "session_id": active_session,
            "language": language,
            "latency_ms": 12.5,
            "degraded": False,
            "raw_metadata_ref": "artifact://fake/raw",
            "provider_preset": provider_preset,
            "provider_settings": dict(provider_settings or {}),
        }
        self.record_runtime_result(payload)
        return GatewayResponse(
            True,
            "ok",
            payload,
        )

    def get_runtime_status(self) -> GatewayResponse:
        state = "active" if self.runtime_started else "idle"
        streaming_supported, streaming_mode = self._runtime_capabilities()
        return GatewayResponse(
            True,
            "ok",
            {
                "backend": self.provider_profile.split("/")[-1],
                "model": self.provider_preset or "default",
                "region": "",
                "capabilities": ["batch", "timestamps"],
                "streaming_supported": streaming_supported,
                "streaming_mode": streaming_mode,
                "cloud_credentials_available": False,
                "provider_runtime_ready": True,
                "status_message": "runtime active" if self.runtime_started else "runtime idle",
                "session_id": self.session_id if self.runtime_started else "",
                "session_state": state,
                "processing_mode": self.processing_mode,
                "audio_source": self.audio_source,
                "runtime_profile": self.runtime_profile,
            },
        )

    def runtime_snapshot(self) -> dict[str, Any]:
        active_session = {
            "session_id": self.session_id,
            "state": "active" if self.runtime_started else "idle",
            "provider_id": self.provider_profile.split("/")[-1],
            "profile_id": self.runtime_profile,
            "processing_mode": self.processing_mode,
            "status_message": "runtime active" if self.runtime_started else "runtime idle",
            "updated_at": "2026-03-13T00:00:00+00:00",
        }
        return {
            "observer_error": "",
            "recent_results": list(self._runtime_results),
            "recent_partials": list(self._runtime_partials),
            "node_statuses": [
                {
                    "node_name": "audio_input_node",
                    "health": "ok",
                    "ready": True,
                    "status_message": f"running source={self.audio_source}",
                    "time": "2026-03-13T00:00:00+00:00",
                    "last_error_code": "",
                    "last_error_message": "",
                }
            ],
            "session_statuses": [active_session] if self.session_id else [],
            "active_session": active_session if self.session_id else {},
        }

    def record_runtime_result(self, payload: dict[str, Any]) -> None:
        request_id = str(payload.get("request_id", "") or "")
        self._runtime_results = [
            item for item in self._runtime_results if item.get("request_id") != request_id
        ]
        self._runtime_results.insert(
            0,
            {
                "time": "2026-03-13T00:00:00+00:00",
                "type": "final",
                **payload,
            },
        )

    def list_backends(self) -> GatewayResponse:
        return GatewayResponse(True, "ok", {"provider_ids": ["whisper", "azure", "aws"]})

    def validate_config(self, profile_type: str, profile_id: str) -> GatewayResponse:
        if self.fail_validate:
            return GatewayResponse(False, "validation failed", {})
        return GatewayResponse(
            True,
            "valid",
            {
                "resolved_config_ref": f"configs/resolved/{profile_type}__{profile_id}.json",
            },
        )

    def register_dataset(
        self, manifest_path: str, dataset_id: str, dataset_profile: str
    ) -> GatewayResponse:
        del dataset_profile
        registry_path = self.project_root / "datasets" / "registry" / "datasets.json"
        payload = json.loads(registry_path.read_text(encoding="utf-8"))
        payload.setdefault("datasets", [])
        payload["datasets"] = [
            row for row in payload["datasets"] if row.get("dataset_id") != dataset_id
        ]
        payload["datasets"].append(
            {
                "dataset_id": dataset_id,
                "manifest_ref": manifest_path,
                "sample_count": 1,
                "metadata": {"registered_by": "fake_gateway"},
            }
        )
        registry_path.write_text(json.dumps(payload, ensure_ascii=True, indent=2), encoding="utf-8")
        return GatewayResponse(True, "dataset registered", {"dataset_id": dataset_id})

    def import_dataset(
        self, *, source_path: str, dataset_id: str, dataset_profile: str
    ) -> GatewayResponse:
        del dataset_profile
        manifest_path = self.project_root / "datasets" / "manifests" / f"{dataset_id}.jsonl"
        audio_path = Path(source_path)
        sample = {
            "sample_id": f"{dataset_id}_00000",
            "audio_path": str(audio_path),
            "transcript": "",
            "language": "en-US",
            "split": "test",
            "tags": ["imported"],
            "metadata": {"source_path": str(audio_path)},
        }
        manifest_path.write_text(json.dumps(sample) + "\n", encoding="utf-8")
        self.register_dataset(str(manifest_path), dataset_id, "")
        return GatewayResponse(
            True, "dataset imported", {"dataset_id": dataset_id, "manifest_ref": str(manifest_path)}
        )

    def run_benchmark(
        self,
        benchmark_profile: str,
        dataset_profile: str,
        providers: list[str],
        *,
        scenario: str = "",
        provider_overrides: dict[str, dict[str, Any]] | None = None,
        benchmark_settings: dict[str, Any] | None = None,
        run_id: str = "",
    ) -> GatewayResponse:
        run_id = run_id or "bench_demo"
        self._benchmark_status[run_id] = {
            "run_id": run_id,
            "state": "running",
            "progress": 0.25,
            "total_samples": 1,
            "processed_samples": 0,
            "failed_samples": 0,
            "status_message": "running",
            "error_message": "",
            "scenario": scenario or "clean_baseline",
        }
        time.sleep(0.05)
        store = ArtifactStore(root=str(self.project_root / "artifacts"))
        run_dir = store.make_benchmark_run(run_id)
        provider_overrides = provider_overrides or {}
        benchmark_settings = benchmark_settings or {}
        execution_mode = str(benchmark_settings.get("execution_mode", "batch") or "batch")
        run_manifest = {
            "run_id": run_id,
            "benchmark_profile": benchmark_profile,
            "dataset_profile": dataset_profile,
            "scenario": scenario or "clean_baseline",
            "providers": providers,
            "provider_overrides": provider_overrides,
            "benchmark_settings": benchmark_settings,
            "execution_mode": execution_mode,
            "sample_count": 1,
            "created_at": "2026-03-12T00:00:00+00:00",
        }
        mean_metrics = {
            "wer": 0.0,
            "cer": 0.0,
            "sample_accuracy": 1.0,
            "total_latency_ms": 15.0,
            "per_utterance_latency_ms": 15.0,
            "real_time_factor": 0.25,
            "estimated_cost_usd": 0.0,
            "success_rate": 1.0,
            "failure_rate": 0.0,
        }
        streaming_metrics = (
            {
                "first_partial_latency_ms": 25.0,
                "finalization_latency_ms": 6.0,
                "partial_count": 3.0,
            }
            if execution_mode == "streaming"
            else {}
        )
        mean_metrics.update(streaming_metrics)
        provider_summaries = [
            {
                "provider_key": provider,
                "provider_profile": provider,
                "provider_id": provider.split("/")[-1].replace("_local", "").replace("_cloud", ""),
                "provider_preset": str(
                    (provider_overrides.get(provider) or {}).get("preset_id", "") or ""
                ),
                "provider_label": "",
                "total_samples": 1,
                "successful_samples": 1,
                "failed_samples": 0,
                "mean_metrics": mean_metrics,
                "quality_metrics": {"wer": 0.0, "cer": 0.0, "sample_accuracy": 1.0},
                "latency_metrics": {
                    "total_latency_ms": 15.0,
                    "per_utterance_latency_ms": 15.0,
                    "real_time_factor": 0.25,
                },
                "reliability_metrics": {
                    "success_rate": 1.0,
                    "failure_rate": 0.0,
                },
                "cost_metrics": {"estimated_cost_usd": 0.0},
                "cost_totals": {"estimated_cost_usd": 0.0},
                "streaming_metrics": streaming_metrics,
                "resource_metrics": {},
                "metric_statistics": {
                    "estimated_cost_usd": {
                        "aggregator": "mean",
                        "count": 1,
                        "sum": 0.0,
                        "mean": 0.0,
                        "min": 0.0,
                        "max": 0.0,
                        "p50": 0.0,
                        "p95": 0.0,
                    }
                },
            }
            for provider in providers
        ]
        summary = {
            "run_id": run_id,
            "benchmark_profile": benchmark_profile,
            "dataset_id": dataset_profile.split("/")[-1],
            "providers": providers,
            "scenario": scenario or "clean_baseline",
            "execution_mode": execution_mode,
            "total_samples": 1,
            "successful_samples": 1,
            "failed_samples": 0,
            "mean_metrics": mean_metrics,
            "quality_metrics": {"wer": 0.0, "cer": 0.0, "sample_accuracy": 1.0},
            "latency_metrics": {
                "total_latency_ms": 15.0,
                "per_utterance_latency_ms": 15.0,
                "real_time_factor": 0.25,
            },
            "reliability_metrics": {
                "success_rate": 1.0,
                "failure_rate": 0.0,
            },
            "cost_metrics": {"estimated_cost_usd": 0.0},
            "cost_totals": {"estimated_cost_usd": 0.0},
            "streaming_metrics": streaming_metrics,
            "resource_metrics": {},
            "provider_summaries": provider_summaries,
            "noise_summary": {
                "clean": {
                    "samples": 1,
                    "mean_metrics": {"wer": 0.0, "cer": 0.0, "total_latency_ms": 15.0},
                }
            },
            "providers_summary": {},
        }
        summary["providers_summary"] = {
            str(provider_summary["provider_key"]): provider_summary
            for provider_summary in provider_summaries
        }
        rows = [
            {
                "run_id": run_id,
                "provider_profile": providers[0] if providers else "providers/whisper_local",
                "provider_id": (
                    providers[0].split("/")[-1].replace("_local", "").replace("_cloud", "")
                    if providers
                    else "whisper"
                ),
                "execution_mode": execution_mode,
                "streaming_mode": "native" if execution_mode == "streaming" else "none",
                "sample_id": "sample_000",
                "success": True,
                "text": "hello world",
                "error_code": "",
                "error_message": "",
                "scenario": scenario or "clean_baseline",
                "noise_level": "clean",
                "provider_preset": str(
                    (provider_overrides.get(providers[0]) or {}).get("preset_id", "") or "default"
                )
                if providers
                else "default",
                "metrics": summary["mean_metrics"],
            }
        ]
        store.save_manifest(run_dir, run_manifest)
        store.save_json(run_dir / "metrics" / "results.json", rows)
        store.save_text(run_dir / "metrics" / "results.csv", "run_id,provider_id\n")
        store.save_json(run_dir / "reports" / "summary.json", summary)
        store.save_report(run_dir, "summary.md", "# Summary\n")
        self._benchmark_status[run_id] = {
            "run_id": run_id,
            "state": "completed",
            "progress": 1.0,
            "total_samples": 1,
            "processed_samples": 1,
            "failed_samples": 0,
            "status_message": "completed",
            "error_message": "",
        }
        return GatewayResponse(
            True,
            "benchmark completed",
            {
                "run_id": run_id,
                "success": True,
                "message": "benchmark completed",
                "summary": {
                    "total_samples": 1,
                    "successful_samples": 1,
                    "failed_samples": 0,
                    "mean_wer": 0.0,
                    "mean_cer": 0.0,
                    "mean_latency_ms": 15.0,
                    "summary_artifact_ref": str(run_dir / "reports" / "summary.json"),
                },
            },
        )

    def get_benchmark_status(self, run_id: str) -> GatewayResponse:
        status = self._benchmark_status.get(run_id)
        if not status:
            return GatewayResponse(False, "benchmark not found", {})
        return GatewayResponse(True, "ok", status)
