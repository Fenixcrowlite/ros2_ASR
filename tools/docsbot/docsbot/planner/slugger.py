from __future__ import annotations

import hashlib
import re


def slugify(value: str) -> str:
    text = value.strip().lower()
    text = text.replace("/", "-")
    text = re.sub(r"[^a-z0-9._-]+", "-", text)
    text = re.sub(r"-+", "-", text).strip("-")
    return text or "item"


def stable_id(prefix: str, value: str) -> str:
    digest = hashlib.sha256(f"{prefix}:{value}".encode()).hexdigest()[:12]
    return f"{prefix}-{digest}"


def topic_filename(topic_name: str) -> str:
    name = topic_name.strip("/")
    return f"{slugify(name)}.md"


def service_filename(service_name: str) -> str:
    name = service_name.strip("/")
    return f"{slugify(name)}.md"


def message_filename(msg_name: str) -> str:
    return f"{slugify(msg_name)}.md"


def parameter_filename(param_name: str) -> str:
    return f"{slugify(param_name)}.md"
