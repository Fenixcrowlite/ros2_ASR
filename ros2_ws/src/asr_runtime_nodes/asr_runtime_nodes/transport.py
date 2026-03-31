"""Transport metadata helpers encoded into ROS Header.frame_id."""

from __future__ import annotations

import json
from typing import Any

_TRANSPORT_PREFIX = "asr_transport:"


def encode_transport_metadata(metadata: dict[str, Any]) -> str:
    payload = {
        str(key): value
        for key, value in metadata.items()
        if value is not None and value != ""
    }
    return _TRANSPORT_PREFIX + json.dumps(
        payload,
        ensure_ascii=True,
        sort_keys=True,
        separators=(",", ":"),
    )


def decode_transport_metadata(frame_id: object) -> dict[str, Any]:
    text = str(frame_id or "").strip()
    if not text.startswith(_TRANSPORT_PREFIX):
        return {}
    try:
        payload = json.loads(text[len(_TRANSPORT_PREFIX) :])
    except Exception:
        return {}
    return dict(payload) if isinstance(payload, dict) else {}


def stamp_to_ns(stamp: object) -> int:
    sec = int(getattr(stamp, "sec", 0) or 0)
    nanosec = int(getattr(stamp, "nanosec", 0) or 0)
    return max((sec * 1_000_000_000) + nanosec, 0)


def delivery_latency_ms(*, now_ns: int, stamp: object) -> float:
    published_ns = stamp_to_ns(stamp)
    if published_ns <= 0 or now_ns <= 0:
        return 0.0
    return max((now_ns - published_ns) / 1_000_000.0, 0.0)


def sequence_gap(previous: int | None, current: int | None) -> int:
    if previous is None or previous < 0 or current is None or current < 0:
        return 0
    if current <= previous + 1:
        return 0
    return current - previous - 1
