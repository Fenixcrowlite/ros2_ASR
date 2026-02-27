from __future__ import annotations

import logging
import os
import tempfile
import time
import uuid
from pathlib import Path
from typing import Any

import requests  # type: ignore[import-untyped]
from asr_core.audio import wav_duration_sec
from asr_core.backend import AsrBackend
from asr_core.config import as_bool, env_or
from asr_core.factory import register_backend
from asr_core.models import AsrRequest, AsrResponse, AsrTimings, BackendCapabilities, WordTimestamp

LOGGER = logging.getLogger(__name__)


@register_backend("aws")
class AwsAsrBackend(AsrBackend):
    name = "aws"

    @property
    def capabilities(self) -> BackendCapabilities:
        return BackendCapabilities(
            supports_recognize_once=True,
            supports_streaming=False,
            streaming_mode="simulated",
            supports_word_timestamps=True,
            supports_confidence=True,
            is_cloud=True,
        )

    def __init__(self, config: dict | None = None, client: object | None = None) -> None:
        super().__init__(config=config, client=client)
        self.region = env_or(self.config, "region", "AWS_REGION", "us-east-1")
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
        self.timeout_sec = int(self.config.get("timeout_sec", 180))
        self.cleanup_enabled = as_bool(
            env_or(self.config, "cleanup", "ASR_AWS_CLEANUP", "true"),
            default=True,
        )
        self._session: Any = client

    def has_credentials(self) -> bool:
        return bool(self.profile or (self.access_key_id and self.secret_access_key))

    def _clients(self) -> tuple[Any, Any]:
        import boto3

        session: Any = self._session
        if session is None:
            if self.profile:
                session = boto3.Session(profile_name=self.profile, region_name=self.region)
            else:
                kwargs: dict[str, str] = {"region_name": self.region}
                if self.access_key_id and self.secret_access_key:
                    kwargs["aws_access_key_id"] = self.access_key_id
                    kwargs["aws_secret_access_key"] = self.secret_access_key
                    if self.session_token:
                        kwargs["aws_session_token"] = self.session_token
                session = boto3.Session(**kwargs)
        s3 = session.client("s3", region_name=self.region)
        transcribe = session.client("transcribe", region_name=self.region)
        return s3, transcribe

    def _request_to_wav_path(self, request: AsrRequest) -> tuple[str, bool]:
        if request.wav_path:
            return request.wav_path, False
        if request.audio_bytes:
            fd, tmp_path = tempfile.mkstemp(suffix=".wav", prefix="aws_audio_")
            os.close(fd)
            with open(tmp_path, "wb") as f:
                f.write(request.audio_bytes)
            return tmp_path, True
        raise ValueError("Either wav_path or audio_bytes must be provided")

    def _cleanup_resources(
        self,
        *,
        s3_client: Any | None,
        transcribe_client: Any | None,
        object_key: str | None,
        job_name: str | None,
    ) -> None:
        if not self.cleanup_enabled:
            return

        if job_name and transcribe_client is not None:
            try:
                transcribe_client.delete_transcription_job(TranscriptionJobName=job_name)
            except Exception as cleanup_exc:  # pragma: no cover - defensive logging path
                LOGGER.warning(
                    "AWS cleanup: failed to delete transcription job '%s': %s",
                    job_name,
                    cleanup_exc,
                )

        if object_key and s3_client is not None:
            try:
                s3_client.delete_object(Bucket=self.s3_bucket, Key=object_key)
            except Exception as cleanup_exc:  # pragma: no cover - defensive logging path
                LOGGER.warning(
                    "AWS cleanup: failed to delete S3 object '%s': %s", object_key, cleanup_exc
                )

    def recognize_once(self, request: AsrRequest) -> AsrResponse:
        preprocess_start = time.perf_counter()
        if not self.region:
            return AsrResponse(
                success=False,
                error_code="config_missing",
                error_message="Missing AWS region. Set AWS_REGION or backends.aws.region.",
                backend_info={"provider": "aws", "model": "transcribe", "region": ""},
                language=request.language,
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
                language=request.language,
            )
        if not self.s3_bucket:
            return AsrResponse(
                success=False,
                error_code="config_missing",
                error_message="Missing S3 bucket. Set ASR_AWS_S3_BUCKET or backends.aws.s3_bucket.",
                backend_info={"provider": "aws", "model": "transcribe", "region": self.region},
                language=request.language,
            )

        tmp_file: str | None = None
        s3_client: Any | None = None
        transcribe_client: Any | None = None
        object_key: str | None = None
        job_name: str | None = None

        try:
            wav_path, cleanup_temp = self._request_to_wav_path(request)
            if cleanup_temp:
                tmp_file = wav_path
            preprocess_ms = (time.perf_counter() - preprocess_start) * 1000.0

            s3_client, transcribe_client = self._clients()
            object_key = f"asr-input/{uuid.uuid4()}.wav"
            s3_client.upload_file(wav_path, self.s3_bucket, object_key)
            media_uri = f"s3://{self.s3_bucket}/{object_key}"
            job_name = f"asr-job-{uuid.uuid4().hex[:20]}"
            language_code = request.language or "en-US"

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
            return AsrResponse(
                success=False,
                error_code="aws_runtime_error",
                error_message=str(exc),
                backend_info={"provider": "aws", "model": "transcribe", "region": self.region},
                language=request.language,
            )
        finally:
            self._cleanup_resources(
                s3_client=s3_client,
                transcribe_client=transcribe_client,
                object_key=object_key,
                job_name=job_name,
            )
            if tmp_file and Path(tmp_file).exists():
                Path(tmp_file).unlink(missing_ok=True)
