"""Minimal HTTP client for Hugging Face Inference API ASR calls."""

from __future__ import annotations

import base64
from dataclasses import dataclass
from typing import Any

import requests  # type: ignore[import-untyped]


@dataclass(slots=True)
class HuggingFaceInferenceError(RuntimeError):
    code: str
    message: str
    status_code: int = 0

    def __str__(self) -> str:  # pragma: no cover - dataclass repr is not user facing
        return self.message


class HuggingFaceInferenceHttpClient:
    """Small requests-based client for automatic speech recognition."""

    def __init__(
        self,
        *,
        token: str,
        timeout_sec: float = 60.0,
        session: requests.Session | None = None,
        base_url: str = "https://api-inference.huggingface.co/models/{model}",
    ) -> None:
        self.token = str(token or "").strip()
        self.timeout_sec = max(float(timeout_sec or 0.0), 1.0)
        self._session = session or requests.Session()
        self.base_url = str(base_url or "").strip() or "https://api-inference.huggingface.co/models/{model}"

    def _resolve_url(self, *, model_id: str, endpoint_url: str = "") -> str:
        explicit = str(endpoint_url or "").strip()
        if explicit:
            return explicit.format(model=model_id)
        if str(model_id or "").startswith(("http://", "https://")):
            return str(model_id)
        return self.base_url.format(model=model_id)

    @staticmethod
    def _error_code(status_code: int, message: str) -> str:
        lowered = str(message or "").lower()
        if status_code in {401, 403}:
            return "hf_auth_error"
        if status_code == 404:
            return "hf_model_not_found"
        if status_code in {408, 504}:
            return "timeout"
        if status_code == 503:
            return "model_unavailable"
        if "timed out" in lowered:
            return "timeout"
        return "hf_api_http_error"

    def automatic_speech_recognition(
        self,
        *,
        audio_bytes: bytes,
        model_id: str,
        endpoint_url: str = "",
        return_timestamps: bool = False,
        generation_parameters: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        if not self.token:
            raise HuggingFaceInferenceError(
                code="credential_missing",
                message="HF token is missing. Provide HF_TOKEN.",
            )

        url = self._resolve_url(model_id=model_id, endpoint_url=endpoint_url)
        headers = {
            "Authorization": f"Bearer {self.token}",
            "Accept": "application/json",
        }
        request_kwargs: dict[str, Any] = {
            "timeout": self.timeout_sec,
        }
        generation = dict(generation_parameters or {})
        if return_timestamps or generation:
            headers["Content-Type"] = "application/json"
            parameters: dict[str, Any] = {}
            if return_timestamps:
                parameters["return_timestamps"] = True
            if generation:
                parameters["generation_parameters"] = generation
            request_kwargs["json"] = {
                "inputs": base64.b64encode(audio_bytes).decode("ascii"),
                "parameters": parameters,
            }
        else:
            request_kwargs["data"] = audio_bytes

        try:
            response = self._session.post(url, headers=headers, **request_kwargs)
        except requests.Timeout as exc:
            raise HuggingFaceInferenceError(
                code="timeout",
                message=f"Hugging Face request timed out: {exc}",
            ) from exc
        except requests.RequestException as exc:
            raise HuggingFaceInferenceError(
                code="hf_api_transport_error",
                message=f"Hugging Face request failed: {exc}",
            ) from exc

        try:
            payload = response.json()
        except ValueError:
            payload = {"error": response.text.strip()}

        if response.status_code >= 400:
            error_message = str(payload.get("error", "") or response.text or "HTTP error").strip()
            raise HuggingFaceInferenceError(
                code=self._error_code(response.status_code, error_message),
                message=error_message,
                status_code=int(response.status_code),
            )

        if not isinstance(payload, dict):
            raise HuggingFaceInferenceError(
                code="hf_api_invalid_response",
                message="Hugging Face returned a non-object ASR response.",
                status_code=int(response.status_code),
            )
        if payload.get("error"):
            error_message = str(payload.get("error", "") or "").strip()
            raise HuggingFaceInferenceError(
                code=self._error_code(int(response.status_code), error_message),
                message=error_message,
                status_code=int(response.status_code),
            )
        return payload
