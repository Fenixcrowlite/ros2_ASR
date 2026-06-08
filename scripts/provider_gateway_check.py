#!/usr/bin/env python3
"""Validate or test one ASR provider through the running gateway API."""

from __future__ import annotations

import argparse
import json
import sys
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


def parse_settings(raw: str) -> dict[str, Any]:
    try:
        value = json.loads(raw or "{}")
    except json.JSONDecodeError as exc:
        raise argparse.ArgumentTypeError(f"invalid JSON settings: {exc}") from exc
    if not isinstance(value, dict):
        raise argparse.ArgumentTypeError("settings JSON must be an object")
    return value


def post_json(url: str, payload: dict[str, Any], *, timeout_sec: float) -> int:
    request = Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urlopen(request, timeout=timeout_sec) as response:
            raw = response.read().decode("utf-8", errors="replace")
    except HTTPError as exc:
        raw = exc.read().decode("utf-8", errors="replace")
        print(f"HTTP {exc.code} from {url}", file=sys.stderr)
        print(raw, file=sys.stderr)
        return 1
    except URLError as exc:
        print(f"Gateway request failed: {exc.reason}", file=sys.stderr)
        print("Start the stack first with: make up", file=sys.stderr)
        return 1

    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        print(raw)
        return 0

    print(json.dumps(data, indent=2, ensure_ascii=False, sort_keys=True))
    if not isinstance(data, dict):
        return 0

    if data.get("ok") is False or data.get("valid") is False or data.get("success") is False:
        return 1
    if str(data.get("status", "")).lower() in {"error", "failed", "invalid"}:
        return 1
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("validate", "test"))
    parser.add_argument("--base-url", default="http://127.0.0.1:8088")
    parser.add_argument("--profile", required=True)
    parser.add_argument("--preset", default="")
    parser.add_argument("--settings-json", default="{}", type=parse_settings)
    parser.add_argument("--wav-path", default="data/sample/vosk_test.wav")
    parser.add_argument("--language", default="en-US")
    parser.add_argument("--timeout-sec", default=60.0, type=float)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    payload: dict[str, Any] = {
        "provider_profile": args.profile,
        "provider_preset": args.preset,
        "provider_settings": args.settings_json,
    }
    endpoint = "/api/providers/validate"
    if args.command == "test":
        endpoint = "/api/providers/test"
        payload.update({"wav_path": args.wav_path, "language": args.language})

    return post_json(
        f"{args.base_url.rstrip('/')}{endpoint}",
        payload,
        timeout_sec=args.timeout_sec,
    )


if __name__ == "__main__":
    raise SystemExit(main())
