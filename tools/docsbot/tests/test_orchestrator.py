from __future__ import annotations

from pathlib import Path

from docsbot.config import DocsbotConfig
from docsbot.indexer.models import ProjectIndex, RepoMeta
from docsbot.planner.models import TaskPlan
from docsbot.qa.report import QAReport
from docsbot.runtime.orchestrator import DocsbotOrchestrator


def _make_cfg(tmp_path: Path, *, llm_provider: str, openai_api_key: str | None = None) -> DocsbotConfig:
    vault_root = tmp_path / "vault"
    docs_root = vault_root / "Wiki-ASR"
    cache_dir = tmp_path / ".docsbot" / "cache"
    logs_dir = tmp_path / ".docsbot" / "logs"
    backups_dir = tmp_path / ".docsbot" / "backups"
    docs_root.mkdir(parents=True, exist_ok=True)
    cache_dir.mkdir(parents=True, exist_ok=True)
    logs_dir.mkdir(parents=True, exist_ok=True)
    backups_dir.mkdir(parents=True, exist_ok=True)
    return DocsbotConfig(
        repo_root=tmp_path,
        vault_root=vault_root,
        docs_subfolder="Wiki-ASR",
        docs_root=docs_root,
        cache_dir=cache_dir,
        logs_dir=logs_dir,
        backups_dir=backups_dir,
        openai_api_key=openai_api_key,
        docsbot_model="gpt-4.1-mini",
        llm_provider=llm_provider,
    )


def _minimal_index(tmp_path: Path) -> ProjectIndex:
    return ProjectIndex(
        repo=RepoMeta(
            repo_name="ros2ws",
            repo_root=str(tmp_path),
            workspace_root=str(tmp_path / "ros2_ws"),
            commit="deadbeef",
        )
    )


def test_generate_without_openai_key_uses_template_only_mode(tmp_path: Path, monkeypatch) -> None:
    orchestrator = DocsbotOrchestrator(_make_cfg(tmp_path, llm_provider="auto", openai_api_key=None))
    monkeypatch.setattr(
        orchestrator,
        "_index_and_plan",
        lambda: (_minimal_index(tmp_path), TaskPlan(tasks=[])),
    )
    monkeypatch.setattr(
        orchestrator,
        "_qa_paths",
        lambda _root, _index: QAReport(passed=True, errors=[], warnings=[]),
    )

    result = orchestrator.generate()

    assert result["ok"] is True
    assert result["provider"] == "none"
    assert result["warnings"] == [
        "OPENAI_API_KEY is not set; docsbot generated template-only pages without LLM drafts."
    ]
    overview = (orchestrator.cfg.docs_root / "01_Project" / "Overview.md").read_text(encoding="utf-8")
    assert "LLM Draft" not in overview


def test_forced_openai_mode_requires_api_key(tmp_path: Path) -> None:
    orchestrator = DocsbotOrchestrator(_make_cfg(tmp_path, llm_provider="openai", openai_api_key=None))

    try:
        orchestrator._provider()
    except RuntimeError as exc:
        assert "requires OPENAI_API_KEY" in str(exc)
    else:
        raise AssertionError("expected RuntimeError when OpenAI mode is forced without a key")


def test_mock_provider_is_only_used_when_explicitly_requested(
    tmp_path: Path, monkeypatch
) -> None:
    orchestrator = DocsbotOrchestrator(_make_cfg(tmp_path, llm_provider="mock", openai_api_key=None))
    monkeypatch.setattr(
        orchestrator,
        "_index_and_plan",
        lambda: (_minimal_index(tmp_path), TaskPlan(tasks=[])),
    )
    monkeypatch.setattr(
        orchestrator,
        "_qa_paths",
        lambda _root, _index: QAReport(passed=True, errors=[], warnings=[]),
    )

    result = orchestrator.generate()

    assert result["ok"] is True
    assert result["provider"] == "mock"
    assert result["warnings"] == []

