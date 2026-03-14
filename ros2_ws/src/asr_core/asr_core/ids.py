"""Stable ID generation helpers."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone


def make_session_id(prefix: str = "session") -> str:
    return f"{prefix}_{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}_{uuid.uuid4().hex[:8]}"


def make_request_id(prefix: str = "req") -> str:
    return f"{prefix}_{uuid.uuid4().hex}"


def make_run_id(prefix: str = "run") -> str:
    return f"{prefix}_{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}_{uuid.uuid4().hex[:8]}"
