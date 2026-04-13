"""Stable ID generation helpers."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime


def make_session_id(prefix: str = "session") -> str:
    """Build a human-readable runtime session identifier."""
    return f"{prefix}_{datetime.now(UTC).strftime('%Y%m%dT%H%M%SZ')}_{uuid.uuid4().hex[:8]}"


def make_request_id(prefix: str = "req") -> str:
    """Build a unique per-request identifier."""
    return f"{prefix}_{uuid.uuid4().hex}"


def make_run_id(prefix: str = "run") -> str:
    """Build a benchmark/report run identifier with a sortable timestamp."""
    return f"{prefix}_{datetime.now(UTC).strftime('%Y%m%dT%H%M%SZ')}_{uuid.uuid4().hex[:8]}"
