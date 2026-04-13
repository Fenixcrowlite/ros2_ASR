"""Local Hugging Face ASR provider using transformers pipelines."""

from __future__ import annotations

from time import perf_counter
from typing import Any

from asr_core.normalized import LatencyMetadata, NormalizedAsrResult
from asr_provider_base.capabilities import ProviderCapabilities
from asr_provider_base.models import ProviderAudio

from asr_provider_huggingface.common import (
    BaseHuggingFaceProvider,
    build_transcription_result,
    language_to_hf_token,
    local_timestamp_mode,
    provider_audio_to_waveform,
    resolve_token,
)


class HuggingFaceLocalProvider(BaseHuggingFaceProvider):
    """Local Hugging Face adapter backed by `transformers.pipeline`."""

    provider_id = "huggingface_local"
    display_name = "Hugging Face Local"
    implementation = "transformers.pipeline"
    source = "local"

    def __init__(self) -> None:
        super().__init__()
        self._token = ""
        self._pipeline: Any = None
        self._resolved_device = ""
        self._resolved_dtype: Any = None

    def initialize(self, config: dict[str, Any], credentials_ref: dict[str, str]) -> None:
        self._config = dict(config)
        self._token = resolve_token(credentials_ref)
        self._set_metadata(
            model_id=str(self._config.get("model_id", "") or ""),
            device=str(self._config.get("device", "auto") or "auto"),
        )
        self._status = self.get_status().__class__(
            provider_id=self.provider_id,
            state="initialized",
            message="initialized",
        )

    def validate_config(self) -> list[str]:
        errors: list[str] = []
        if not str(self._config.get("model_id", "") or "").strip():
            errors.append("Hugging Face local model_id is required.")
        try:
            import transformers  # noqa: F401
        except Exception as exc:
            errors.append(f"transformers is not available: {exc}")
        try:
            import torch  # noqa: F401
        except Exception as exc:
            errors.append(f"torch is not available: {exc}")
        return errors

    def discover_capabilities(self) -> ProviderCapabilities:
        return ProviderCapabilities(
            supports_streaming=False,
            streaming_mode="none",
            supports_batch=True,
            supports_word_timestamps=True,
            supports_partials=False,
            supports_confidence=False,
            supports_language_auto_detect=True,
            supports_cpu=True,
            supports_gpu=True,
            requires_network=False,
            cost_model_type="local",
        )

    def _resolve_device(self, torch_module: Any) -> str:
        requested = str(self._config.get("device", "auto") or "auto").strip().lower()
        if requested and requested != "auto":
            return requested
        if bool(getattr(torch_module.cuda, "is_available", lambda: False)()):
            return str(self._config.get("cuda_device", "cuda:0") or "cuda:0")
        mps_backend = getattr(getattr(torch_module, "backends", None), "mps", None)
        if mps_backend is not None and bool(getattr(mps_backend, "is_available", lambda: False)()):
            return "mps"
        return "cpu"

    def _resolve_dtype(self, torch_module: Any) -> Any:
        requested = str(self._config.get("torch_dtype", "auto") or "auto").strip().lower()
        if requested in {"", "auto"}:
            return "auto"
        mapping = {
            "float16": getattr(torch_module, "float16", "auto"),
            "fp16": getattr(torch_module, "float16", "auto"),
            "float32": getattr(torch_module, "float32", "auto"),
            "fp32": getattr(torch_module, "float32", "auto"),
            "bfloat16": getattr(torch_module, "bfloat16", "auto"),
            "bf16": getattr(torch_module, "bfloat16", "auto"),
        }
        return mapping.get(requested, "auto")

    def _is_whisper_model(self) -> bool:
        model_id = str(self._config.get("model_id", "") or "").lower()
        return "whisper" in model_id

    def _load_pipeline(self) -> Any:
        if self._pipeline is not None:
            return self._pipeline
        import torch  # type: ignore[import-not-found]
        from transformers import pipeline  # type: ignore[import-not-found]

        self._resolved_device = self._resolve_device(torch)
        self._resolved_dtype = self._resolve_dtype(torch)
        kwargs: dict[str, Any] = {
            "task": "automatic-speech-recognition",
            "model": str(self._config.get("model_id", "") or ""),
            "trust_remote_code": bool(self._config.get("trust_remote_code", False)),
        }
        if self._token:
            kwargs["token"] = self._token
        device_map = str(self._config.get("device_map", "") or "").strip()
        if device_map:
            kwargs["device_map"] = device_map
        else:
            kwargs["device"] = self._resolved_device
        if self._resolved_dtype is not None:
            kwargs["torch_dtype"] = self._resolved_dtype
        self._pipeline = pipeline(**kwargs)
        self._set_metadata(device=self._resolved_device)
        self._status = self.get_status().__class__(
            provider_id=self.provider_id,
            state="ready",
            message="pipeline loaded",
        )
        return self._pipeline

    def _call_kwargs(self, audio: ProviderAudio) -> dict[str, Any]:
        kwargs: dict[str, Any] = {}
        timestamp_mode = local_timestamp_mode(
            self._config,
            enable_word_timestamps=audio.enable_word_timestamps,
        )
        if timestamp_mode is not None:
            kwargs["return_timestamps"] = timestamp_mode
        chunk_length_s = float(self._config.get("chunk_length_s", 0.0) or 0.0)
        if chunk_length_s > 0.0:
            kwargs["chunk_length_s"] = chunk_length_s
        batch_size = int(self._config.get("batch_size", 0) or 0)
        if batch_size > 0:
            kwargs["batch_size"] = batch_size
        stride_length_s = self._config.get("stride_length_s")
        if stride_length_s is not None:
            kwargs["stride_length_s"] = stride_length_s
        if self._is_whisper_model():
            generate_kwargs = dict(self._config.get("generate_kwargs", {}) or {})
            task = str(self._config.get("task", "transcribe") or "transcribe").strip()
            if task:
                generate_kwargs.setdefault("task", task)
            if audio.language:
                generate_kwargs.setdefault("language", language_to_hf_token(audio.language))
            if generate_kwargs:
                kwargs["generate_kwargs"] = generate_kwargs
        return kwargs

    def recognize_once(
        self,
        audio: ProviderAudio,
        options: dict[str, Any] | None = None,
    ) -> NormalizedAsrResult:
        del options
        try:
            preprocess_started = perf_counter()
            waveform, sample_rate_hz, _duration_sec = provider_audio_to_waveform(audio)
            preprocess_ms = (perf_counter() - preprocess_started) * 1000.0

            inference_started = perf_counter()
            pipe = self._load_pipeline()
            call_kwargs = self._call_kwargs(audio)
            try:
                payload = pipe(
                    {"sampling_rate": sample_rate_hz, "raw": waveform},
                    **call_kwargs,
                )
                tags: list[str] = ["hf_local", "transformers"]
            except Exception:
                if "return_timestamps" not in call_kwargs or not bool(
                    self._config.get("allow_timestamp_fallback", True)
                ):
                    raise
                fallback_kwargs = dict(call_kwargs)
                fallback_kwargs.pop("return_timestamps", None)
                payload = pipe(
                    {"sampling_rate": sample_rate_hz, "raw": waveform},
                    **fallback_kwargs,
                )
                tags = ["hf_local", "transformers", "timestamp_fallback"]
            inference_ms = (perf_counter() - inference_started) * 1000.0

            postprocess_started = perf_counter()
            result = build_transcription_result(
                provider_id=self.provider_id,
                audio=audio,
                payload=payload if isinstance(payload, dict) else {"text": str(payload or "")},
                latency=LatencyMetadata(
                    total_ms=0.0,
                    preprocess_ms=preprocess_ms,
                    inference_ms=inference_ms,
                    postprocess_ms=0.0,
                ),
                language=audio.language,
                tags=tags,
            )
            result.latency.postprocess_ms = (perf_counter() - postprocess_started) * 1000.0
            result.latency.total_ms = (
                result.latency.preprocess_ms
                + result.latency.inference_ms
                + result.latency.postprocess_ms
            )
            self._record_result(result)
            return result
        except Exception as exc:
            error_message = str(exc)
            self._record_exception(
                error_code="hf_local_runtime_error",
                error_message=error_message,
            )
            return NormalizedAsrResult(
                request_id=audio.request_id,
                session_id=audio.session_id,
                provider_id=self.provider_id,
                text="",
                is_final=True,
                is_partial=False,
                language=audio.language,
                latency=LatencyMetadata(),
                degraded=True,
                error_code="hf_local_runtime_error",
                error_message=error_message,
                tags=["hf_local", "transformers"],
            )

    def teardown(self) -> None:
        self._pipeline = None
        try:
            import torch  # type: ignore[import-not-found]

            if bool(getattr(torch.cuda, "is_available", lambda: False)()):
                empty_cache = getattr(torch.cuda, "empty_cache", None)
                if callable(empty_cache):
                    empty_cache()
        except Exception:
            pass
        super().teardown()
