"""AWS Transcribe backend with native streaming and batch job support."""

from __future__ import annotations

import asyncio
import configparser
import json
import logging
import os
import queue
import socket
import threading
import time
import uuid
from collections.abc import Iterable
from contextlib import contextmanager
from datetime import UTC, datetime
from json import JSONDecodeError
from pathlib import Path
from typing import Any

import requests  # type: ignore[import-untyped]
from asr_core.audio import (
    audio_bytes_to_temp_wav,
    pcm_duration_sec,
    sample_width_from_encoding,
    wav_duration_sec,
)
from asr_core.backend import AsrBackend
from asr_core.config import as_bool, env_or
from asr_core.factory import register_backend
from asr_core.language import normalize_language_code
from asr_core.models import AsrRequest, AsrResponse, AsrTimings, BackendCapabilities, WordTimestamp
from asr_core.streaming import StreamAccumulator

LOGGER = logging.getLogger(__name__)


def _aws_streaming_host(region: str) -> str:
    normalized_region = str(region or "us-east-1").strip() or "us-east-1"
    return f"transcribestreaming.{normalized_region}.amazonaws.com"


def _ensure_streaming_endpoint_resolves(region: str) -> None:
    host = _aws_streaming_host(region)
    try:
        socket.getaddrinfo(host, 443, type=socket.SOCK_STREAM)
    except socket.gaierror as exc:
        raise RuntimeError(
            "AWS streaming endpoint "
            f"`{host}` could not be resolved. Configure `streaming_region` "
            "or `ASR_AWS_STREAMING_REGION` to a region that supports Amazon "
            "Transcribe Streaming."
        ) from exc


def _aws_streaming_session_id() -> str:
    return str(uuid.uuid4())


class AwsStreamingSession:
    """Native Amazon Transcribe Streaming session."""

    def __init__(
        self,
        *,
        region: str,
        credential_resolver: Any,
        language: str,
        sample_rate: int,
        channels: int = 1,
        sample_width_bytes: int = 2,
        language_model_name: str = "",
        enable_partial_results_stabilization: bool = True,
        partial_results_stability: str = "medium",
    ) -> None:
        self._region = str(region or "us-east-1")
        self._language = normalize_language_code(language, fallback="en-US")
        self._sample_rate = int(sample_rate or 16000)
        self._channels = int(channels or 1)
        self._sample_width_bytes = int(sample_width_bytes or 2)
        self._credential_resolver = credential_resolver
        self._language_model_name = str(language_model_name or "").strip()
        self._enable_partial_results_stabilization = bool(enable_partial_results_stabilization)
        self._partial_results_stability = str(partial_results_stability or "medium")
        self._audio_queue: queue.Queue[bytes | None] = queue.Queue()
        self._done = threading.Event()
        self._accumulator = StreamAccumulator(
            provider="aws",
            language=self._language,
            model=self._language_model_name or "transcribe_streaming",
            region=self._region,
        )
        self._thread = threading.Thread(target=self._run, name="aws-stream-session", daemon=True)
        self._thread.start()

    @staticmethod
    def _classify_error(exc: Exception) -> tuple[str, str]:
        message = str(exc).strip() or exc.__class__.__name__
        lowered = message.lower()
        if "sessionid" in lowered and "failed to satisfy constraint" in lowered:
            return "aws_stream_session_id_invalid", message
        if "streaming endpoint" in lowered and "could not be resolved" in lowered:
            return "aws_stream_endpoint_unreachable", message
        if "aws_io_dns_invalid_name" in lowered or "dns resolution" in lowered:
            return "aws_stream_endpoint_unreachable", message
        if "error loading sso token" in lowered or (
            "token for" in lowered and "does not exist" in lowered
        ):
            return "aws_sso_token_missing", message
        if "token has expired" in lowered or "expired and refresh failed" in lowered:
            return "aws_sso_token_expired", message
        if "unable to locate credentials" in lowered or "partial credentials found" in lowered:
            return "credential_missing", message
        if "invalidclienttokenid" in lowered or "unrecognizedclientexception" in lowered:
            return "credential_invalid", message
        if "access denied" in lowered:
            return "aws_access_denied", message
        return "aws_stream_runtime_error", message

    def _build_words(self, items: list[Any]) -> tuple[list[WordTimestamp], float]:
        words: list[WordTimestamp] = []
        confidences: list[float] = []
        for item in items or []:
            if getattr(item, "item_type", "") != "pronunciation":
                continue
            confidence = float(getattr(item, "confidence", 0.0) or 0.0)
            confidences.append(confidence)
            words.append(
                WordTimestamp(
                    word=str(getattr(item, "content", "") or ""),
                    start_sec=float(getattr(item, "start_time", 0.0) or 0.0),
                    end_sec=float(getattr(item, "end_time", 0.0) or 0.0),
                    confidence=confidence,
                )
            )
        avg_conf = sum(confidences) / len(confidences) if confidences else 0.0
        return words, avg_conf

    async def _write_chunks(self, input_stream) -> None:
        loop = asyncio.get_running_loop()
        while True:
            chunk = await loop.run_in_executor(None, self._audio_queue.get)
            if chunk is None:
                await input_stream.end_stream()
                break
            await input_stream.send_audio_event(audio_chunk=bytes(chunk))

    async def _consume_events(self, output_stream) -> None:
        from amazon_transcribe.model import TranscriptEvent

        async for event in output_stream:
            if not isinstance(event, TranscriptEvent):
                continue
            transcript = getattr(event, "transcript", None)
            for result in getattr(transcript, "results", []) or []:
                if not getattr(result, "alternatives", None):
                    continue
                alt = result.alternatives[0]
                text = str(getattr(alt, "transcript", "") or "").strip()
                if not text:
                    continue
                if bool(getattr(result, "is_partial", False)):
                    self._accumulator.mark_partial(
                        text,
                        language=str(getattr(result, "language_code", "") or self._language),
                        backend_info={
                            "model": self._accumulator.model,
                            "region": self._region,
                        },
                        raw_response=event,
                    )
                else:
                    words, avg_conf = self._build_words(list(getattr(alt, "items", []) or []))
                    self._accumulator.add_final(
                        text,
                        words=words,
                        confidence=avg_conf,
                        language=str(getattr(result, "language_code", "") or self._language),
                        backend_info={
                            "model": self._accumulator.model,
                            "region": self._region,
                        },
                        raw_response=event,
                    )

    async def _run_async(self) -> None:
        from amazon_transcribe.client import TranscribeStreamingClient

        _ensure_streaming_endpoint_resolves(self._region)
        client = TranscribeStreamingClient(
            region=self._region,
            credential_resolver=self._credential_resolver,
        )
        stream = await client.start_stream_transcription(
            language_code=self._language,
            media_sample_rate_hz=self._sample_rate,
            media_encoding="pcm",
            session_id=_aws_streaming_session_id(),
            enable_partial_results_stabilization=self._enable_partial_results_stabilization,
            partial_results_stability=self._partial_results_stability,
            language_model_name=self._language_model_name or None,
            number_of_channels=self._channels if self._channels > 1 else None,
            enable_channel_identification=True if self._channels > 1 else None,
        )
        writer = asyncio.create_task(self._write_chunks(stream.input_stream))
        reader = asyncio.create_task(self._consume_events(stream.output_stream))
        await writer
        await reader

    def _run(self) -> None:
        try:
            asyncio.run(self._run_async())
        except Exception as exc:
            error_code, error_message = self._classify_error(exc)
            self._accumulator.set_error(error_code, error_message, raw_response=exc)
        finally:
            self._done.set()

    def push_audio(self, chunk: bytes) -> None:
        self._accumulator.audio_duration_sec += pcm_duration_sec(
            chunk,
            sample_rate=self._sample_rate,
            channels=self._channels,
            sample_width=self._sample_width_bytes,
        )
        self._audio_queue.put(bytes(chunk))

    def drain_partials(self) -> list[AsrResponse]:
        return self._accumulator.drain_partials()

    def stop(self) -> AsrResponse:
        self._accumulator.note_stop_requested()
        self._audio_queue.put(None)
        self._done.wait(timeout=30.0)
        self._thread.join(timeout=1.0)
        return self._accumulator.build_final_response()


@register_backend("aws")
class AwsAsrBackend(AsrBackend):
    """Amazon Transcribe backend."""

    name = "aws"

    @property
    def capabilities(self) -> BackendCapabilities:
        return BackendCapabilities(
            supports_recognize_once=True,
            supports_streaming=True,
            streaming_mode="native",
            supports_word_timestamps=True,
            supports_confidence=True,
            is_cloud=True,
        )

    def __init__(self, config: dict | None = None, client: object | None = None) -> None:
        super().__init__(config=config, client=client)
        self.region = env_or(self.config, "region", "AWS_REGION", "us-east-1")
        self.streaming_region = (
            str(
                env_or(
                    self.config,
                    "streaming_region",
                    "ASR_AWS_STREAMING_REGION",
                    self.region or "us-east-1",
                )
                or self.region
                or "us-east-1"
            ).strip()
            or "us-east-1"
        )
        self.s3_bucket = env_or(self.config, "s3_bucket", "ASR_AWS_S3_BUCKET", "")
        self.media_format = env_or(self.config, "media_format", "ASR_AWS_MEDIA_FORMAT", "wav")
        self.profile = env_or(self.config, "profile", "AWS_PROFILE", "")
        self.access_key_id = env_or(self.config, "access_key_id", "AWS_ACCESS_KEY_ID", "")
        self.secret_access_key = env_or(
            self.config,
            "secret_access_key",
            "AWS_SECRET_ACCESS_KEY",
            "",
        )
        self.session_token = env_or(self.config, "session_token", "AWS_SESSION_TOKEN", "")
        self.config_file = env_or(self.config, "config_file", "AWS_CONFIG_FILE", "")
        self.shared_credentials_file = env_or(
            self.config,
            "shared_credentials_file",
            "AWS_SHARED_CREDENTIALS_FILE",
            "",
        )
        self.timeout_sec = int(self.config.get("timeout_sec", 180))
        self.cleanup_enabled = as_bool(
            env_or(self.config, "cleanup", "ASR_AWS_CLEANUP", "true"),
            default=True,
        )
        self.streaming_language_model_name = env_or(
            self.config,
            "language_model_name",
            "ASR_AWS_LANGUAGE_MODEL_NAME",
            "",
        )
        self.streaming_partial_results_stabilization = as_bool(
            env_or(
                self.config,
                "enable_partial_results_stabilization",
                "ASR_AWS_ENABLE_PARTIAL_RESULTS_STABILIZATION",
                "true",
            ),
            default=True,
        )
        self.streaming_partial_results_stability = env_or(
            self.config,
            "partial_results_stability",
            "ASR_AWS_PARTIAL_RESULTS_STABILITY",
            "medium",
        )
        self._session: Any = client

    def has_credentials(self) -> bool:
        return bool(self.profile or (self.access_key_id and self.secret_access_key))

    @contextmanager
    def _aws_env_overrides(self):
        updates = {
            "AWS_CONFIG_FILE": self.config_file,
            "AWS_SHARED_CREDENTIALS_FILE": self.shared_credentials_file,
        }
        previous = {key: os.environ.get(key) for key in updates}
        try:
            for key, value in updates.items():
                if value:
                    os.environ[key] = value
            yield
        finally:
            for key, value in previous.items():
                if value is None:
                    os.environ.pop(key, None)
                else:
                    os.environ[key] = value

    @staticmethod
    def _parse_iso_datetime(value: str) -> datetime | None:
        text = str(value or "").strip()
        if not text:
            return None
        try:
            return datetime.fromisoformat(text.replace("Z", "+00:00"))
        except ValueError:
            return None

    @staticmethod
    def _latest_cli_cache_expiry(*, account_id: str = "") -> datetime | None:
        cache_dir = Path.home() / ".aws" / "cli" / "cache"
        if not cache_dir.exists():
            return None

        matches: list[datetime] = []
        for cache_path in cache_dir.glob("*.json"):
            try:
                payload = json.loads(cache_path.read_text(encoding="utf-8"))
            except (OSError, JSONDecodeError):
                continue
            credentials = payload.get("Credentials", {})
            if not isinstance(credentials, dict):
                continue
            if account_id:
                cached_account = str(credentials.get("AccountId", "") or "").strip()
                if cached_account and cached_account != account_id:
                    continue
            expiry = AwsAsrBackend._parse_iso_datetime(str(credentials.get("Expiration", "")))
            if expiry is not None:
                matches.append(expiry)
        return max(matches) if matches else None

    @staticmethod
    def _latest_sso_cache_expiry(
        *,
        start_url: str = "",
        sso_region: str = "",
    ) -> datetime | None:
        cache_dir = Path.home() / ".aws" / "sso" / "cache"
        if not cache_dir.exists():
            return None

        matches: list[datetime] = []
        for cache_path in cache_dir.glob("*.json"):
            try:
                payload = json.loads(cache_path.read_text(encoding="utf-8"))
            except (OSError, JSONDecodeError):
                continue
            if not str(payload.get("accessToken", "")).strip():
                continue
            payload_start_url = str(payload.get("startUrl", "")).strip()
            payload_region = str(payload.get("region", "")).strip()
            if start_url and payload_start_url and payload_start_url != start_url:
                continue
            if sso_region and payload_region and payload_region != sso_region:
                continue

            parsed_expiry = AwsAsrBackend._parse_iso_datetime(
                str(payload.get("expiresAt", "")).strip()
            )
            if parsed_expiry is not None:
                matches.append(parsed_expiry)
        return max(matches) if matches else None

    @staticmethod
    def _load_cli_cache_credentials(*, account_id: str = "") -> dict[str, str] | None:
        cache_dir = Path.home() / ".aws" / "cli" / "cache"
        if not cache_dir.exists():
            return None

        now = datetime.now(UTC)
        best: tuple[datetime, dict[str, str]] | None = None
        for cache_path in cache_dir.glob("*.json"):
            try:
                payload = json.loads(cache_path.read_text(encoding="utf-8"))
            except (OSError, JSONDecodeError):
                continue

            credentials = payload.get("Credentials", {})
            if not isinstance(credentials, dict):
                continue

            if account_id:
                cached_account = str(credentials.get("AccountId", "") or "").strip()
                if cached_account and cached_account != account_id:
                    continue

            expiry = AwsAsrBackend._parse_iso_datetime(str(credentials.get("Expiration", "")))
            if expiry is None or expiry <= now:
                continue

            access_key_id = str(credentials.get("AccessKeyId", "") or "").strip()
            secret_access_key = str(credentials.get("SecretAccessKey", "") or "").strip()
            session_token = str(credentials.get("SessionToken", "") or "").strip()
            if not (access_key_id and secret_access_key and session_token):
                continue

            candidate = (
                expiry,
                {
                    "aws_access_key_id": access_key_id,
                    "aws_secret_access_key": secret_access_key,
                    "aws_session_token": session_token,
                },
            )
            if best is None or candidate[0] > best[0]:
                best = candidate

        return best[1] if best is not None else None

    def _profile_sso_account_id(self) -> str:
        if not self.profile:
            return ""
        config_path = (
            Path(self.config_file).expanduser()
            if self.config_file
            else Path.home() / ".aws" / "config"
        )
        if not config_path.exists():
            return ""
        parser = configparser.RawConfigParser()
        parser.read(config_path, encoding="utf-8")
        section = self.profile if self.profile == "default" else f"profile {self.profile}"
        if not parser.has_section(section):
            return ""
        return parser.get(section, "sso_account_id", fallback="").strip()

    def auth_status(self) -> dict[str, Any]:
        now = datetime.now(UTC)
        status: dict[str, Any] = {
            "profile": self.profile,
            "region": self.region,
            "uses_sso": False,
            "runtime_ready": False,
            "login_supported": False,
            "login_recommended": False,
            "login_command": "",
            "config_file": str(
                Path(self.config_file).expanduser()
                if self.config_file
                else Path.home() / ".aws" / "config"
            ),
            "shared_credentials_file": str(
                Path(self.shared_credentials_file).expanduser()
                if self.shared_credentials_file
                else Path.home() / ".aws" / "credentials"
            ),
            "static_keys_present": bool(self.access_key_id and self.secret_access_key),
            "sso_session_name": "",
            "sso_start_url": "",
            "sso_region": "",
            "sso_session_expires_at": "",
            "sso_session_valid": False,
            "role_credentials_expires_at": "",
            "role_credentials_valid": False,
            "account_id": "",
            "status": "unknown",
            "message": "",
        }

        if self.config_file and not Path(self.config_file).expanduser().exists():
            status["status"] = "config_missing"
            status["message"] = f"AWS config file does not exist: {self.config_file}"
            return status
        if (
            self.shared_credentials_file
            and not Path(self.shared_credentials_file).expanduser().exists()
        ):
            status["status"] = "shared_credentials_missing"
            status["message"] = (
                f"AWS shared credentials file does not exist: {self.shared_credentials_file}"
            )
            return status

        if not self.profile:
            if status["static_keys_present"]:
                status["status"] = "static_credentials"
                status["message"] = "Using native AWS access keys from environment/config."
                status["runtime_ready"] = True
                return status
            status["status"] = "anonymous_or_default_chain"
            status["message"] = (
                "No explicit AWS profile configured. SDK default credential chain will be used."
            )
            return status

        config_path = Path(status["config_file"])
        if not config_path.exists():
            status["status"] = "config_missing"
            status["message"] = (
                f"AWS config file not found for profile `{self.profile}`: {config_path}"
            )
            return status

        parser = configparser.RawConfigParser()
        parser.read(config_path, encoding="utf-8")
        section = self.profile if self.profile == "default" else f"profile {self.profile}"
        if not parser.has_section(section):
            status["status"] = "profile_missing"
            status["message"] = f"AWS profile `{self.profile}` is not defined in {config_path}"
            return status

        sso_session = parser.get(section, "sso_session", fallback="").strip()
        start_url = parser.get(section, "sso_start_url", fallback="").strip()
        sso_region = parser.get(section, "sso_region", fallback="").strip()
        account_id = parser.get(section, "sso_account_id", fallback="").strip()
        if sso_session:
            sso_section = f"sso-session {sso_session}"
            if parser.has_section(sso_section):
                start_url = (
                    start_url or parser.get(sso_section, "sso_start_url", fallback="").strip()
                )
                sso_region = (
                    sso_region or parser.get(sso_section, "sso_region", fallback="").strip()
                )

        status["uses_sso"] = bool(sso_session or start_url)
        status["login_supported"] = bool(status["uses_sso"] and self.profile)
        status["sso_session_name"] = sso_session
        status["sso_start_url"] = start_url
        status["sso_region"] = sso_region
        status["account_id"] = account_id
        if status["login_supported"]:
            status["login_command"] = f"aws sso login --profile {self.profile}"

        cli_cache_expiry = self._latest_cli_cache_expiry(account_id=account_id)
        if cli_cache_expiry is not None:
            status["role_credentials_expires_at"] = (
                cli_cache_expiry.astimezone(UTC).isoformat().replace("+00:00", "Z")
            )
            status["role_credentials_valid"] = cli_cache_expiry > now

        if not status["uses_sso"]:
            if status["role_credentials_valid"]:
                status["status"] = "role_credentials_valid"
                status["message"] = "AWS profile resolves to valid role credentials."
                status["runtime_ready"] = True
            else:
                status["status"] = "profile_configured"
                status["message"] = "AWS profile is configured and does not use SSO."
            return status

        sso_expiry = self._latest_sso_cache_expiry(start_url=start_url, sso_region=sso_region)
        if sso_expiry is not None:
            status["sso_session_expires_at"] = (
                sso_expiry.astimezone(UTC).isoformat().replace("+00:00", "Z")
            )
            status["sso_session_valid"] = sso_expiry > now

        if status["role_credentials_valid"]:
            status["runtime_ready"] = True
            if status["sso_session_valid"]:
                status["status"] = "role_credentials_valid"
                status["message"] = "AWS role credentials and SSO sign-in session are both valid."
            else:
                status["status"] = "role_credentials_valid_sso_expired"
                status["login_recommended"] = True
                status["message"] = (
                    "AWS role credentials are still valid, but the IAM Identity "
                    "Center sign-in session is expired. "
                    "Runtime and benchmark requests may continue to work until "
                    "role credentials expire."
                )
            return status

        if status["sso_session_valid"]:
            status["status"] = "sso_session_valid_no_role_credentials"
            status["runtime_ready"] = True
            status["message"] = (
                "IAM Identity Center sign-in session is valid. "
                "Active role credentials are not cached yet, "
                "but the AWS SDK can mint them on the first real request."
            )
            return status

        if status["sso_session_expires_at"]:
            status["status"] = "sso_session_expired"
            status["login_recommended"] = True
            status["message"] = (
                f"AWS SSO sign-in session expired at {status['sso_session_expires_at']}. "
                f"Run `aws sso login --profile {self.profile}`."
            )
            return status

        status["status"] = "sso_login_required"
        status["login_recommended"] = True
        status["message"] = f"AWS SSO login required for profile `{self.profile}`."
        return status

    def auth_validation_errors(self) -> list[str]:
        errors: list[str] = []
        if self.config_file and not Path(self.config_file).expanduser().exists():
            errors.append(f"AWS config file does not exist: {self.config_file}")
        if (
            self.shared_credentials_file
            and not Path(self.shared_credentials_file).expanduser().exists()
        ):
            errors.append(
                f"AWS shared credentials file does not exist: {self.shared_credentials_file}"
            )

        if errors:
            return errors
        status = self.auth_status()
        state = str(status.get("status", "") or "")
        if state in {
            "static_credentials",
            "profile_configured",
            "role_credentials_valid",
            "role_credentials_valid_sso_expired",
            "sso_session_valid_no_role_credentials",
        }:
            return []
        message = str(status.get("message", "") or "").strip()
        return [message] if message else []

    def _build_boto3_session(self):
        session: Any = self._session
        if session is not None:
            return session
        import boto3

        with self._aws_env_overrides():
            if self.profile:
                cached_credentials = self._load_cli_cache_credentials(
                    account_id=self._profile_sso_account_id()
                )
                if cached_credentials:
                    return boto3.Session(region_name=self.region, **cached_credentials)
                return boto3.Session(profile_name=self.profile, region_name=self.region)
            kwargs: dict[str, str] = {"region_name": self.region}
            if self.access_key_id and self.secret_access_key:
                kwargs["aws_access_key_id"] = self.access_key_id
                kwargs["aws_secret_access_key"] = self.secret_access_key
                if self.session_token:
                    kwargs["aws_session_token"] = self.session_token
            return boto3.Session(**kwargs)

    def _clients(self) -> tuple[Any, Any]:
        session = self._build_boto3_session()
        s3 = session.client("s3", region_name=self.region)
        transcribe = session.client("transcribe", region_name=self.region)
        return s3, transcribe

    def _streaming_credential_resolver(self):
        from amazon_transcribe.auth import StaticCredentialResolver

        session = self._build_boto3_session()
        credentials = session.get_credentials()
        if credentials is None:
            raise RuntimeError("Unable to locate AWS credentials for streaming session.")
        frozen = credentials.get_frozen_credentials()
        return StaticCredentialResolver(
            access_key_id=frozen.access_key,
            secret_access_key=frozen.secret_key,
            session_token=frozen.token,
        )

    def _request_to_wav_path(self, request: AsrRequest) -> tuple[str, bool]:
        if request.wav_path:
            return request.wav_path, False
        if request.audio_bytes:
            return (
                audio_bytes_to_temp_wav(
                    request.audio_bytes,
                    sample_rate=int(request.sample_rate or 16000),
                    channels=int(request.metadata.get("channels", 1) or 1),
                    sample_width=int(
                        request.metadata.get(
                            "sample_width_bytes",
                            sample_width_from_encoding(request.metadata.get("encoding"), default=2),
                        )
                        or 2
                    ),
                    prefix="aws_audio_",
                ),
                True,
            )
        raise ValueError("Either wav_path or audio_bytes must be provided")

    def _cleanup_resources(
        self,
        *,
        s3_client: Any | None,
        transcribe_client: Any | None,
        object_key: str | None,
        job_name: str | None,
        object_uploaded: bool,
    ) -> None:
        if not self.cleanup_enabled:
            return

        if job_name and transcribe_client is not None:
            try:
                transcribe_client.delete_transcription_job(TranscriptionJobName=job_name)
            except Exception as cleanup_exc:  # pragma: no cover
                LOGGER.warning(
                    "AWS cleanup: failed to delete transcription job '%s': %s",
                    job_name,
                    cleanup_exc,
                )

        if object_uploaded and object_key and s3_client is not None:
            try:
                s3_client.delete_object(Bucket=self.s3_bucket, Key=object_key)
            except Exception as cleanup_exc:  # pragma: no cover
                LOGGER.warning(
                    "AWS cleanup: failed to delete S3 object '%s': %s",
                    object_key,
                    cleanup_exc,
                )

    @staticmethod
    def _classify_runtime_error(exc: Exception) -> tuple[str, str]:
        message = str(exc).strip() or exc.__class__.__name__
        lowered = message.lower()
        if "error loading sso token" in lowered or (
            "token for" in lowered and "does not exist" in lowered
        ):
            return "aws_sso_token_missing", message
        if "token has expired" in lowered or "expired and refresh failed" in lowered:
            return "aws_sso_token_expired", message
        if "unable to locate credentials" in lowered or "partial credentials found" in lowered:
            return "credential_missing", message
        if "invalidclienttokenid" in lowered or "unrecognizedclientexception" in lowered:
            return "credential_invalid", message
        if "access denied" in lowered:
            return "aws_access_denied", message
        return "aws_runtime_error", message

    def create_stream_session(
        self,
        *,
        language: str,
        sample_rate: int,
        channels: int = 1,
        sample_width_bytes: int = 2,
    ) -> AwsStreamingSession:
        if not self.region:
            raise RuntimeError("Missing AWS region. Set AWS_REGION or backends.aws.region.")
        if not self.has_credentials():
            raise RuntimeError(
                "Missing AWS credentials. Set AWS_PROFILE or both "
                "AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY."
            )
        validation_errors = self.auth_validation_errors()
        if validation_errors:
            raise RuntimeError("; ".join(validation_errors))
        resolver = self._streaming_credential_resolver()
        return AwsStreamingSession(
            region=self.streaming_region,
            credential_resolver=resolver,
            language=language,
            sample_rate=sample_rate,
            channels=channels,
            sample_width_bytes=sample_width_bytes,
            language_model_name=self.streaming_language_model_name,
            enable_partial_results_stabilization=self.streaming_partial_results_stabilization,
            partial_results_stability=self.streaming_partial_results_stability,
        )

    def recognize_once(self, request: AsrRequest) -> AsrResponse:
        preprocess_start = time.perf_counter()
        language = normalize_language_code(request.language, fallback="en-US")
        if not self.region:
            return AsrResponse(
                success=False,
                error_code="config_missing",
                error_message="Missing AWS region. Set AWS_REGION or backends.aws.region.",
                backend_info={"provider": "aws", "model": "transcribe", "region": ""},
                language=language,
            )
        if not self.has_credentials():
            return AsrResponse(
                success=False,
                error_code="credential_missing",
                error_message=(
                    "Missing AWS credentials. Set AWS_PROFILE or both AWS_ACCESS_KEY_ID and "
                    "AWS_SECRET_ACCESS_KEY."
                ),
                backend_info={"provider": "aws", "model": "transcribe", "region": self.region},
                language=language,
            )
        if not self.s3_bucket:
            return AsrResponse(
                success=False,
                error_code="config_missing",
                error_message="Missing S3 bucket. Set ASR_AWS_S3_BUCKET or backends.aws.s3_bucket.",
                backend_info={"provider": "aws", "model": "transcribe", "region": self.region},
                language=language,
            )

        tmp_file: str | None = None
        s3_client: Any | None = None
        transcribe_client: Any | None = None
        object_key: str | None = None
        job_name: str | None = None
        object_uploaded = False

        try:
            wav_path, cleanup_temp = self._request_to_wav_path(request)
            if cleanup_temp:
                tmp_file = wav_path
            preprocess_ms = (time.perf_counter() - preprocess_start) * 1000.0

            s3_client, transcribe_client = self._clients()
            object_key = f"asr-input/{uuid.uuid4()}.wav"
            s3_client.upload_file(wav_path, self.s3_bucket, object_key)
            object_uploaded = True
            media_uri = f"s3://{self.s3_bucket}/{object_key}"
            job_name = f"asr-job-{uuid.uuid4().hex[:20]}"
            language_code = language or "en-US"

            inf_start = time.perf_counter()
            transcribe_client.start_transcription_job(
                TranscriptionJobName=job_name,
                LanguageCode=language_code,
                MediaFormat=self.media_format,
                Media={"MediaFileUri": media_uri},
            )

            status = "QUEUED"
            transcript_uri = ""
            poll_start = time.perf_counter()
            while status in {"QUEUED", "IN_PROGRESS"}:
                if time.perf_counter() - poll_start > self.timeout_sec:
                    return AsrResponse(
                        success=False,
                        error_code="timeout",
                        error_message="AWS transcription timeout",
                        backend_info={
                            "provider": "aws",
                            "model": "transcribe",
                            "region": self.region,
                        },
                        language=language_code,
                    )
                time.sleep(2.0)
                job = transcribe_client.get_transcription_job(TranscriptionJobName=job_name)
                job_data = job.get("TranscriptionJob", {})
                status = job_data.get("TranscriptionJobStatus", "FAILED")
                transcript_uri = (job_data.get("Transcript", {}) or {}).get("TranscriptFileUri", "")
                if status == "FAILED":
                    reason = job_data.get("FailureReason", "AWS transcription failed")
                    return AsrResponse(
                        success=False,
                        error_code="aws_job_failed",
                        error_message=reason,
                        backend_info={
                            "provider": "aws",
                            "model": "transcribe",
                            "region": self.region,
                        },
                        language=language_code,
                    )
            inference_ms = (time.perf_counter() - inf_start) * 1000.0

            if not transcript_uri:
                return AsrResponse(
                    success=False,
                    error_code="aws_transcript_missing",
                    error_message="No transcript URI returned",
                    backend_info={"provider": "aws", "model": "transcribe", "region": self.region},
                    language=language_code,
                )

            payload = requests.get(transcript_uri, timeout=20).json()
            results = payload.get("results", {})
            text = ""
            transcripts = results.get("transcripts", [])
            if transcripts:
                text = transcripts[0].get("transcript", "")

            words: list[WordTimestamp] = []
            conf_values: list[float] = []
            for item in results.get("items", []):
                if item.get("type") != "pronunciation":
                    continue
                alts = item.get("alternatives", [])
                if not alts:
                    continue
                alt = alts[0]
                conf = float(alt.get("confidence", 0.0))
                conf_values.append(conf)
                words.append(
                    WordTimestamp(
                        word=alt.get("content", ""),
                        start_sec=float(item.get("start_time", 0.0)),
                        end_sec=float(item.get("end_time", 0.0)),
                        confidence=conf,
                    )
                )
            avg_conf = sum(conf_values) / len(conf_values) if conf_values else 0.0

            post_start = time.perf_counter()
            duration = wav_duration_sec(wav_path)
            post_ms = (time.perf_counter() - post_start) * 1000.0
            return AsrResponse(
                text=text,
                partials=[],
                confidence=avg_conf,
                word_timestamps=words if request.enable_word_timestamps else [],
                language=language_code,
                backend_info={"provider": "aws", "model": "transcribe", "region": self.region},
                timings=AsrTimings(
                    preprocess_ms=preprocess_ms,
                    inference_ms=inference_ms,
                    postprocess_ms=post_ms,
                ),
                audio_duration_sec=duration,
                success=True,
            )
        except Exception as exc:
            error_code, error_message = self._classify_runtime_error(exc)
            return AsrResponse(
                success=False,
                error_code=error_code,
                error_message=error_message,
                backend_info={"provider": "aws", "model": "transcribe", "region": self.region},
                language=language,
            )
        finally:
            self._cleanup_resources(
                s3_client=s3_client,
                transcribe_client=transcribe_client,
                object_key=object_key,
                job_name=job_name,
                object_uploaded=object_uploaded,
            )
            if tmp_file and Path(tmp_file).exists():
                Path(tmp_file).unlink(missing_ok=True)

    def streaming_recognize(
        self,
        chunks: Iterable[bytes],
        *,
        language: str,
        sample_rate: int,
    ) -> AsrResponse:
        session = self.create_stream_session(language=language, sample_rate=sample_rate)
        for chunk in chunks:
            session.push_audio(bytes(chunk))
        return session.stop()
