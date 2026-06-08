#!/usr/bin/env python3
"""Check that public setup guides stay aligned with provider profiles and safe examples."""

from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]
MARKDOWN_LINK_RE = re.compile(r"\[[^]]+\]\(([^)]+)\)")


def fail(message: str) -> None:
    print(f"FAIL: {message}", file=sys.stderr)
    raise SystemExit(1)


def require_file(path: Path) -> str:
    if not path.exists():
        fail(f"missing required file: {path.relative_to(ROOT)}")
    return path.read_text(encoding="utf-8")


def iter_public_markdown() -> list[Path]:
    files = [ROOT / "README.md", ROOT / "secrets/README.md"]
    files.extend(sorted((ROOT / "docs").rglob("*.md")))
    return [path for path in files if path.exists()]


def check_local_markdown_links() -> None:
    for source in iter_public_markdown():
        text = source.read_text(encoding="utf-8")
        for raw_link in MARKDOWN_LINK_RE.findall(text):
            link = raw_link.strip()
            if not link or link.startswith("#"):
                continue
            parsed = urlparse(link)
            if parsed.scheme or parsed.netloc:
                continue
            path_part = parsed.path
            if not path_part or not path_part.endswith(".md"):
                continue
            target = (source.parent / path_part).resolve()
            if not target.exists():
                fail(
                    "broken local Markdown link: "
                    f"{source.relative_to(ROOT)} -> {path_part}"
                )


def check_helper_syntax(paths: list[Path]) -> None:
    for path in paths:
        if not path.exists():
            fail(f"missing helper script: {path.relative_to(ROOT)}")
        if path.suffix == ".py":
            try:
                compile(path.read_text(encoding="utf-8"), str(path), "exec")
            except SyntaxError as exc:
                fail(
                    f"Python syntax check failed for {path.relative_to(ROOT)}: "
                    f"{exc.msg} at line {exc.lineno}"
                )
        elif path.suffix == ".sh":
            result = subprocess.run(
                ["bash", "-n", str(path)],
                check=False,
                capture_output=True,
                text=True,
            )
            if result.returncode != 0:
                fail(
                    f"shell syntax check failed for {path.relative_to(ROOT)}: "
                    f"{result.stderr.strip()}"
                )


def main() -> int:
    readme = require_file(ROOT / "README.md")
    docs_index = require_file(ROOT / "docs/README.md")
    setup = require_file(ROOT / "docs/setup.md")
    backends = require_file(ROOT / "docs/asr_backends.md")
    providers = require_file(ROOT / "docs/providers.md")
    provider_env = require_file(ROOT / "docs/provider_env.md")
    provider_cli = require_file(ROOT / "docs/provider_cli.md")
    release_checklist = require_file(ROOT / "docs/public_release_checklist.md")
    env_example = require_file(ROOT / "configs/runtime.env.example")
    workflow = require_file(ROOT / ".github/workflows/docs-check.yml")
    gnumake = require_file(ROOT / "GNUmakefile")
    public_tools = require_file(ROOT / "mk/public_tools.mk")

    helper_paths = [
        ROOT / "scripts/check_docs.py",
        ROOT / "scripts/provider_gateway_check.py",
        ROOT / "scripts/init_provider_env.sh",
        ROOT / "scripts/setup_env.sh",
        ROOT / "scripts/public_release_check.sh",
    ]
    check_helper_syntax(helper_paths)

    required_links = {
        "README.md": [
            "docs/setup.md",
            "docs/asr_backends.md",
            "docs/provider_env.md",
            "docs/provider_cli.md",
            "docs/providers.md",
            "docs/public_release_checklist.md",
        ],
        "docs/README.md": [
            "setup.md",
            "asr_backends.md",
            "provider_env.md",
            "provider_cli.md",
            "providers.md",
            "public_release_checklist.md",
            "runtime.md",
        ],
    }
    for name, links in required_links.items():
        text = readme if name == "README.md" else docs_index
        for link in links:
            if link not in text:
                fail(f"{name} does not reference {link}")

    profile_dir = ROOT / "configs/providers"
    profiles = sorted(path.stem for path in profile_dir.glob("*.yaml"))
    if not profiles:
        fail("no provider profiles found under configs/providers")

    missing_profiles = [name for name in profiles if f"providers/{name}" not in backends]
    if missing_profiles:
        fail("backend activation guide misses profiles: " + ", ".join(missing_profiles))

    required_sections = [
        "Local Whisper",
        "Vosk",
        "Hugging Face local",
        "Hugging Face API",
        "Azure Speech",
        "Google Cloud Speech-to-Text",
        "Amazon Transcribe",
    ]
    for section in required_sections:
        if section not in backends:
            fail(f"docs/asr_backends.md misses section: {section}")

    official_domains = [
        "github.com/SYSTRAN/faster-whisper",
        "alphacephei.com/vosk",
        "huggingface.co/docs",
        "learn.microsoft.com",
        "cloud.google.com",
        "docs.aws.amazon.com",
    ]
    for domain in official_domains:
        if domain not in backends and domain not in provider_env:
            fail(f"public provider guides miss official documentation link for: {domain}")

    expected_env_names = [
        "AZURE_SPEECH_KEY",
        "AZURE_SPEECH_REGION",
        "HF_TOKEN",
        "GOOGLE_APPLICATION_CREDENTIALS",
        "GOOGLE_CLOUD_PROJECT",
        "AWS_PROFILE",
        "AWS_REGION",
        "AWS_S3_BUCKET",
    ]
    for name in expected_env_names:
        if f"{name}=" not in env_example:
            fail(f"configs/runtime.env.example misses variable: {name}")
        if name not in provider_env:
            fail(f"docs/provider_env.md does not explain variable: {name}")

    for line in env_example.splitlines():
        if not line or line.startswith("#") or "=" not in line:
            continue
        _, value = line.split("=", 1)
        if value.strip():
            fail("configs/runtime.env.example must not contain populated values")

    forbidden_fragments = [
        "AZURE_SPEECH_KEY=...",
        "HF_TOKEN=hf_...",
        "AWS_TRANSCRIBE_BUCKET=my-transcribe-bucket",
        "git@github.com:Fenixcrowlite/ros2_ASR.git",
        "docs.cloud.google.com/docs/authentication/application-default-credentials",
    ]
    tracked_docs = "\n".join(path.read_text(encoding="utf-8") for path in iter_public_markdown())
    for fragment in forbidden_fragments:
        if fragment in tracked_docs:
            fail(f"public documentation contains stale example or link: {fragment}")

    if "include Makefile" not in gnumake or "include mk/public_tools.mk" not in gnumake:
        fail("GNUmakefile does not layer the public convenience targets over Makefile")

    expected_make_targets = [
        "public-help:",
        "init-provider-env:",
        "provider-validate:",
        "provider-test:",
        "public-release-check:",
    ]
    for target in expected_make_targets:
        if target not in public_tools:
            fail(f"mk/public_tools.mk misses target: {target}")

    if "make public-help" not in readme:
        fail("README.md does not expose make public-help")

    if "make docs-check" not in workflow:
        fail("documentation workflow does not run make docs-check")

    if "make public-release-check" not in workflow:
        fail("documentation workflow does not run make public-release-check")

    watched_paths = [
        "secrets/refs/**",
        "scripts/check_docs.py",
        "scripts/provider_gateway_check.py",
        "scripts/init_provider_env.sh",
        "scripts/setup_env.sh",
        "scripts/public_release_check.sh",
        "GNUmakefile",
        "mk/**",
    ]
    for path in watched_paths:
        if path not in workflow:
            fail(f"documentation workflow does not watch: {path}")

    if "make provider-validate" not in provider_cli or "make provider-test" not in provider_cli:
        fail("docs/provider_cli.md does not explain the Make provider-check commands")

    if "make init-provider-env" not in provider_env:
        fail("docs/provider_env.md does not explain make init-provider-env")

    if "git clone https://github.com/Fenixcrowlite/ros2_ASR.git" not in setup:
        fail("docs/setup.md must use the public HTTPS clone path")

    if "python3-colcon-common-extensions" not in setup:
        fail("docs/setup.md must install colcon extensions")

    if "make public-release-check" not in release_checklist:
        fail("public release checklist must include make public-release-check")

    check_local_markdown_links()

    print(f"PASS: documentation covers {len(profiles)} provider profiles and safe setup paths")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
