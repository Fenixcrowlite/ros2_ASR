from __future__ import annotations

from pathlib import Path

from .models import InterfaceDefinition, InterfaceField


def _parse_fields(lines: list[str]) -> list[InterfaceField]:
    fields: list[InterfaceField] = []
    section = "main"
    for raw_line in lines:
        line = raw_line.split("#", 1)[0].strip()
        if not line:
            continue
        if line == "---":
            if section == "main":
                section = "response"
            elif section == "response":
                section = "feedback"
            continue
        parts = line.split()
        if len(parts) < 2:
            continue
        type_name = parts[0]
        name = parts[1]
        fields.append(InterfaceField(name=name, type_name=type_name, section=section))
    return fields


def extract_interfaces(package_name: str, package_path: Path) -> list[InterfaceDefinition]:
    interfaces: list[InterfaceDefinition] = []
    for kind in ("msg", "srv", "action"):
        folder = package_path / kind
        if not folder.exists():
            continue
        for file_path in sorted(folder.glob(f"*.{kind}")):
            lines = file_path.read_text(encoding="utf-8").splitlines()
            interfaces.append(
                InterfaceDefinition(
                    kind=kind,
                    package=package_name,
                    name=file_path.stem,
                    file=str(file_path),
                    fields=_parse_fields(lines),
                )
            )
    return interfaces
