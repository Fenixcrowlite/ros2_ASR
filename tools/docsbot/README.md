# docsbot

`docsbot` builds and maintains an Obsidian wiki for this ROS2 ASR repository.

## Features

- Auto-detects repository root and Obsidian vault.
- Builds a project index from ROS2 packages, interfaces, launch files, and Python AST.
- Computes incremental task plans from index diffs.
- Writes safe generated markdown pages into one vault subfolder (`Wiki-ASR`).
- Preserves user-authored pages (`generated: false`) by writing `*.autogen.md` siblings.
- Runs QA checks (links, mermaid syntax, entity hallucination checks).
- Supports one-shot generation, validation, snapshotting, watch mode, and git hook install.

## Install

```bash
cd tools/docsbot
python3 -m venv .venv
source .venv/bin/activate
pip install -U pip
pip install -e .[dev]
```

## Commands

```bash
docsbot detect
docsbot snapshot
docsbot generate
docsbot validate
docsbot watch
docsbot install-hooks
```

## LLM Provider

- Default mode is `DOCSBOT_LLM_PROVIDER=auto`.
  In `auto`, docsbot uses OpenAI only when `OPENAI_API_KEY` is present.
- Without an API key in `auto`, docsbot generates deterministic template-only pages and skips `LLM Draft` sections.
- `DOCSBOT_LLM_PROVIDER=openai` requires `OPENAI_API_KEY` and fails fast if the key is missing.
- `DOCSBOT_LLM_PROVIDER=mock` enables deterministic `MockProvider` explicitly for offline experiments.

The writer only receives a task plan and project index slices.

## Detection Defaults

- Obsidian vault search prioritizes desktop/home locations and currently prefers `~/Desktop/*` vaults with `.obsidian/`.
- Generated pages are written only inside one subfolder: `Wiki-ASR`.
- Cache/log/backup data is kept in `<repo>/.docsbot/`.

## Safety Rules

- Existing files with frontmatter `generated: false` are never overwritten.
- docsbot writes sibling `*.autogen.md` files instead.
- Existing generated files are backed up before overwrite (`.docsbot/backups/<timestamp>/...`).
- If pre-write QA fails, docsbot writes `90_Auto/_Errors.md` and aborts full overwrite.
