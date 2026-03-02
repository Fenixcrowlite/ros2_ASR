from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from rich.console import Console

from docsbot.config import detect as detect_config
from docsbot.runtime.orchestrator import DocsbotOrchestrator, install_git_hook
from docsbot.runtime.watcher import watch

console = Console()


def _common_parser(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--repo-root", type=Path, default=None, help="Repository root (auto-detected if omitted)"
    )
    parser.add_argument(
        "--vault-root",
        type=Path,
        default=None,
        help="Obsidian vault root (auto-detected if omitted)",
    )
    parser.add_argument("--subfolder", type=str, default=None, help="Wiki subfolder inside vault")


def cmd_detect(args: argparse.Namespace) -> int:
    result = detect_config(
        repo_root=args.repo_root, vault_root=args.vault_root, docs_subfolder=args.subfolder
    )
    payload = {
        "repo_root": str(result.repo_root),
        "vault_root": str(result.vault_root),
        "docs_root": str(result.docs_root),
        "docs_subfolder": result.docs_subfolder,
    }
    console.print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0


def _orchestrator(args: argparse.Namespace) -> DocsbotOrchestrator:
    return DocsbotOrchestrator.create(
        repo_root=args.repo_root, vault_root=args.vault_root, subfolder=args.subfolder
    )


def cmd_snapshot(args: argparse.Namespace) -> int:
    orchestrator = _orchestrator(args)
    result = orchestrator.snapshot()
    console.print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


def cmd_generate(args: argparse.Namespace) -> int:
    orchestrator = _orchestrator(args)
    result = orchestrator.generate()
    console.print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result.get("ok") else 2


def cmd_validate(args: argparse.Namespace) -> int:
    orchestrator = _orchestrator(args)
    report = orchestrator.validate()
    console.print(report.model_dump_json(indent=2))
    return 0 if report.passed else 2


def cmd_watch(args: argparse.Namespace) -> int:
    orchestrator = _orchestrator(args)
    console.print(f"Watching repository: {orchestrator.cfg.repo_root}")
    console.print(f"Wiki destination: {orchestrator.cfg.docs_root}")

    def on_change() -> None:
        result = orchestrator.generate()
        status = "ok" if result.get("ok") else "fail"
        console.print(f"[docsbot] regenerate: {status} ({result.get('written', 0)} files)")

    # Initial run to ensure docs are in sync.
    initial = orchestrator.generate()
    console.print(json.dumps(initial, ensure_ascii=False, indent=2))

    watch(orchestrator.cfg.repo_root, callback=on_change)
    return 0


def cmd_install_hooks(args: argparse.Namespace) -> int:
    orchestrator = _orchestrator(args)
    hook = install_git_hook(orchestrator.cfg)
    console.print(f"Installed pre-commit hook: {hook}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="docsbot", description="Self-updating Obsidian wiki generator"
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    detect_parser = subparsers.add_parser("detect", help="Detect repo and Obsidian vault")
    _common_parser(detect_parser)
    detect_parser.set_defaults(func=cmd_detect)

    snapshot_parser = subparsers.add_parser(
        "snapshot", help="Write current index and task plan snapshots"
    )
    _common_parser(snapshot_parser)
    snapshot_parser.set_defaults(func=cmd_snapshot)

    generate_parser = subparsers.add_parser("generate", help="Index -> plan -> write -> QA")
    _common_parser(generate_parser)
    generate_parser.set_defaults(func=cmd_generate)

    validate_parser = subparsers.add_parser("validate", help="Run QA checks on generated docs")
    _common_parser(validate_parser)
    validate_parser.set_defaults(func=cmd_validate)

    watch_parser = subparsers.add_parser(
        "watch", help="Watch repo changes and incrementally regenerate docs"
    )
    _common_parser(watch_parser)
    watch_parser.set_defaults(func=cmd_watch)

    hooks_parser = subparsers.add_parser(
        "install-hooks", help="Install git pre-commit docsbot hook"
    )
    _common_parser(hooks_parser)
    hooks_parser.set_defaults(func=cmd_install_hooks)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        return args.func(args)
    except KeyboardInterrupt:
        return 130
    except Exception as exc:
        console.print(f"docsbot error: {exc}", style="bold red")
        return 1


if __name__ == "__main__":
    sys.exit(main())
