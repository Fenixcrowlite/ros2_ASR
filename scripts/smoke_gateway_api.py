#!/usr/bin/env python3
"""Smoke-test the ASR gateway HTTP API after `make up`.

The script intentionally uses only the Python standard library so it works
before development tooling is activated. It checks the endpoints used by the
browser UI and verifies that missing optional provider setup fails cleanly.
"""

from __future__ import annotations

import argparse
import json
import sys
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from typing import Any


@dataclass
class Check:
    ok: bool
    method: str
    path: str
    detail: str


class GatewaySmoke:
    def __init__(self, base_url: str, *, timeout_sec: float = 180.0) -> None:
        self.base_url = base_url.rstrip("/")
        self.timeout_sec = float(timeout_sec)
        self.results: list[Check] = []

    def request(
        self,
        method: str,
        path: str,
        payload: dict[str, Any] | None = None,
        *,
        expected: tuple[int, ...] = (200,),
    ) -> tuple[int | None, Any]:
        data = None
        headers: dict[str, str] = {}
        if payload is not None:
            data = json.dumps(payload).encode("utf-8")
            headers["Content-Type"] = "application/json"

        req = urllib.request.Request(
            self.base_url + path,
            data=data,
            headers=headers,
            method=method,
        )
        body = b""
        content_type = ""
        try:
            with urllib.request.urlopen(req, timeout=self.timeout_sec) as response:
                status = int(response.status)
                body = response.read()
                content_type = response.headers.get("content-type", "")
        except urllib.error.HTTPError as exc:
            status = int(exc.code)
            body = exc.read()
            content_type = exc.headers.get("content-type", "")
        except Exception as exc:  # pragma: no cover - this is a CLI diagnostic path
            self.results.append(Check(False, method, path, f"exception: {exc}"))
            return None, None

        ok = status in expected
        parsed: Any = body
        if "application/json" in content_type:
            try:
                parsed = json.loads(body.decode("utf-8"))
            except Exception as exc:
                ok = False
                parsed = {
                    "parse_error": str(exc),
                    "raw": body[:200].decode("utf-8", "replace"),
                }
        self.results.append(Check(ok, method, path, f"status={status} expected={expected}"))
        return status, parsed

    def expect(self, condition: bool, label: str, detail: str = "") -> None:
        self.results.append(Check(bool(condition), "ASSERT", label, detail))

    def run(self, *, runtime_control: bool = True, recognition: bool = True) -> int:
        self._read_endpoints()
        self._profiles_and_config()
        self._providers()
        self._secrets()
        self._datasets_and_preview()
        if runtime_control:
            self._runtime_control(recognition=recognition)
        self._expected_failures()
        return self._report()

    def _read_endpoints(self) -> None:
        for path in [
            "/",
            "/ui/",
            "/ui/index.html",
            "/api/health",
            "/api/system/status",
            "/api/dashboard",
            "/api/runtime/status",
            "/api/runtime/live",
            "/api/runtime/backends",
            "/api/runtime/samples",
            "/api/noise/catalog",
            "/api/providers/catalog",
            "/api/providers/profiles",
            "/api/profiles",
            "/api/profiles/runtime",
            "/api/profiles/providers?detailed=true",
            "/api/profiles/benchmark",
            "/api/profiles/datasets",
            "/api/profiles/metrics",
            "/api/secrets/refs",
            "/api/secrets/azure_env",
            "/api/secrets/google_service_account",
            "/api/secrets/huggingface_token",
            "/api/datasets",
            "/api/datasets/sample_dataset",
            "/api/benchmark/history?limit=5",
            "/api/results/overview",
            "/api/diagnostics/health",
            "/api/diagnostics/preflight",
            "/api/diagnostics/issues",
            "/api/logs?component=all&severity=all&limit=10",
            "/api/artifacts",
            "/openapi.json",
        ]:
            self.request("GET", path)

    def _profiles_and_config(self) -> None:
        for path in [
            "/api/profiles/runtime/default_runtime",
            "/api/profiles/providers/whisper_local",
            "/api/profiles/providers/aws_cloud",
            "/api/profiles/datasets/sample_dataset",
            "/api/profiles/benchmark/default_benchmark",
        ]:
            _status, payload = self.request("GET", path)
            self.expect(
                isinstance(payload, dict) and "payload" in payload,
                f"profile payload {path}",
                str(payload)[:240],
            )

        for payload in [
            {"profile_type": "runtime", "profile_id": "default_runtime"},
            {"profile_type": "providers", "profile_id": "providers/whisper_local"},
            {"profile_type": "benchmark", "profile_id": "default_benchmark"},
        ]:
            self.request("POST", "/api/config/validate", payload)

    def _providers(self) -> None:
        required_provider_expectations = {
            "providers/whisper_local": True,
            "providers/huggingface_local": True,
        }
        optional_provider_profiles = [
            "providers/vosk_local",
            "providers/aws_cloud",
            "providers/azure_cloud",
            "providers/google_cloud",
            "providers/huggingface_api",
        ]
        for profile, expected_valid in required_provider_expectations.items():
            _status, payload = self.request(
                "POST",
                "/api/providers/validate",
                {"provider_profile": profile},
            )
            self.expect(
                isinstance(payload, dict) and payload.get("valid") is expected_valid,
                f"provider validate {profile}",
                json.dumps(payload)[:360] if isinstance(payload, dict) else str(payload),
            )
        for profile in optional_provider_profiles:
            _status, payload = self.request(
                "POST",
                "/api/providers/validate",
                {"provider_profile": profile},
            )
            self.expect(
                isinstance(payload, dict) and isinstance(payload.get("valid"), bool),
                f"optional provider validate shape {profile}",
                json.dumps(payload)[:360] if isinstance(payload, dict) else str(payload),
            )
            if isinstance(payload, dict) and payload.get("valid") is False:
                self.expect(
                    bool(str(payload.get("message", "") or "").strip()),
                    f"optional provider has diagnostic {profile}",
                    json.dumps(payload)[:360],
                )
            self.expect(
                "secrets/refs/secrets" not in (
                    json.dumps(payload) if isinstance(payload, dict) else str(payload)
                ),
                f"provider diagnostic path {profile}",
                json.dumps(payload)[:360] if isinstance(payload, dict) else str(payload),
            )

    def _secrets(self) -> None:
        for ref_name in [
            "local_none",
            "azure_speech_key",
            "google_service_account",
            "aws_profile",
            "huggingface_api_token",
            "huggingface_local_token",
        ]:
            _status, payload = self.request(
                "POST",
                "/api/secrets/validate",
                {"ref_name": ref_name},
            )
            self.expect(
                isinstance(payload, dict) and payload.get("name") == ref_name,
                f"secret validate {ref_name}",
                str(payload)[:240],
            )
            self.expect(
                "secrets/refs/secrets" not in (
                    json.dumps(payload) if isinstance(payload, dict) else str(payload)
                ),
                f"secret diagnostic path {ref_name}",
                str(payload)[:240],
            )

    def _datasets_and_preview(self) -> None:
        self.request(
            "POST",
            "/api/datasets/validate_manifest",
            {
                "manifest_path": "datasets/manifests/sample_dataset.jsonl",
                "check_audio_files": True,
            },
        )
        path = (
            "/api/benchmark/preview_audio?"
            + urllib.parse.urlencode(
                {
                    "dataset_profile": "sample_dataset",
                    "sample_id": "sample_vosk_numbers",
                    "start_sec": "0",
                    "duration_sec": "0.2",
                    "noise_level": "clean",
                }
            )
        )
        _status, body = self.request("GET", path)
        self.expect(
            isinstance(body, (bytes, bytearray)) and body[:4] == b"RIFF",
            "benchmark preview audio is wav",
            str(body[:16]) if isinstance(body, (bytes, bytearray)) else str(type(body)),
        )

    def _runtime_control(self, *, recognition: bool) -> None:
        session_id = "gateway_smoke"
        start_payload = {
            "runtime_profile": "default_runtime",
            "provider_profile": "providers/whisper_local",
            "processing_mode": "segmented",
            "provider_preset": "light",
            "session_id": session_id,
            "audio_source": "file",
            "audio_file_path": "data/sample/vosk_test.wav",
            "language": "en-US",
        }
        self.request(
            "POST",
            "/api/runtime/reconfigure",
            {
                **start_payload,
                "session_id": session_id,
            },
        )
        self.request("POST", "/api/runtime/start", start_payload)
        self.request("GET", "/api/runtime/live")
        if recognition:
            _status, payload = self.request(
                "POST",
                "/api/runtime/recognize_once",
                {
                    "provider_profile": "providers/whisper_local",
                    "provider_preset": "light",
                    "wav_path": "data/sample/vosk_test.wav",
                    "language": "en-US",
                    "session_id": session_id,
                },
            )
            self.expect(
                isinstance(payload, dict)
                and payload.get("success") is True
                and bool(str(payload.get("text", "") or "").strip()),
                "runtime recognize_once sample succeeds",
                json.dumps(payload)[:480] if isinstance(payload, dict) else str(payload),
            )
        self.request("POST", "/api/runtime/stop", {"session_id": session_id})

    def _expected_failures(self) -> None:
        self.request("GET", "/api/datasets/not_a_dataset", expected=(404,))
        self.request(
            "POST",
            "/api/providers/test",
            {
                "provider_profile": "providers/vosk_local",
                "wav_path": "data/sample/vosk_test.wav",
            },
            expected=(400,),
        )
        self.request(
            "POST",
            "/api/secrets/aws_sso_login",
            {"ref_name": "aws_profile", "profile": "missing_sso_profile"},
            expected=(400,),
        )

    def _report(self) -> int:
        failed = [item for item in self.results if not item.ok]
        for item in self.results:
            prefix = "PASS" if item.ok else "FAIL"
            print(f"{prefix} {item.method} {item.path} {item.detail}")
        print(f"SUMMARY total={len(self.results)} failed={len(failed)}")
        return 1 if failed else 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-url", default="http://127.0.0.1:8088")
    parser.add_argument(
        "--timeout-sec",
        type=float,
        default=180.0,
        help="HTTP timeout per request. First local Whisper run may download a small model.",
    )
    parser.add_argument(
        "--skip-runtime-control",
        action="store_true",
        help="Skip runtime start/reconfigure/stop checks.",
    )
    parser.add_argument(
        "--skip-recognition",
        action="store_true",
        help="Skip the real sample recognition check inside runtime control.",
    )
    args = parser.parse_args()
    return GatewaySmoke(args.base_url, timeout_sec=args.timeout_sec).run(
        runtime_control=not args.skip_runtime_control,
        recognition=not args.skip_recognition,
    )


if __name__ == "__main__":
    sys.exit(main())
