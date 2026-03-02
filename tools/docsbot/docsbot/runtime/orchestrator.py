from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from docsbot.config import DocsbotConfig, load_config, write_detection_snapshot
from docsbot.indexer.models import ProjectIndex
from docsbot.indexer.ros2_extractor import build_project_index
from docsbot.llm.mock_provider import MockProvider
from docsbot.llm.openai_provider import OpenAIProvider
from docsbot.llm.provider import LLMProvider
from docsbot.planner.models import TaskPlan
from docsbot.planner.slugger import (
    message_filename,
    parameter_filename,
    service_filename,
    topic_filename,
)
from docsbot.planner.task_planner import build_task_plan, tasks_to_json
from docsbot.qa.hallucination_checker import check_hallucinations
from docsbot.qa.link_checker import check_links
from docsbot.qa.mermaid_checker import check_mermaid
from docsbot.qa.report import QAReport, write_errors_page
from docsbot.runtime.filesystem import atomic_write
from docsbot.writer.md_writer import MarkdownWriter
from docsbot.writer.templates import (
    auto_index_page,
    changelog_page,
    dataflow_page,
    errors_page,
    generated_graph_page,
    glossary_page,
    home_page,
    layered_architecture_page,
    message_page,
    module_map_page,
    module_page,
    overview_page,
    parameter_page,
    ros_graph_page,
    service_page,
    topic_page,
)


class DocsbotOrchestrator:
    def __init__(self, cfg: DocsbotConfig) -> None:
        self.cfg = cfg

    @classmethod
    def create(
        cls,
        repo_root: Path | None = None,
        vault_root: Path | None = None,
        subfolder: str | None = None,
    ) -> DocsbotOrchestrator:
        return cls(
            load_config(repo_root=repo_root, vault_root=vault_root, docs_subfolder=subfolder)
        )

    @property
    def workspace_root(self) -> Path:
        ros_ws = self.cfg.repo_root / "ros2_ws"
        if ros_ws.exists():
            return ros_ws
        src = self.cfg.repo_root / "src"
        if src.exists():
            return self.cfg.repo_root
        return self.cfg.repo_root

    def _provider(self) -> LLMProvider:
        if self.cfg.openai_api_key:
            return OpenAIProvider(api_key=self.cfg.openai_api_key, model=self.cfg.docsbot_model)
        return MockProvider()

    def _load_previous_index(self) -> ProjectIndex | None:
        index_path = self.cfg.cache_dir / "index.json"
        if not index_path.exists():
            return None
        try:
            return ProjectIndex.model_validate_json(index_path.read_text(encoding="utf-8"))
        except Exception:
            return None

    def _index_and_plan(self) -> tuple[ProjectIndex, TaskPlan]:
        current = build_project_index(
            repo_root=self.cfg.repo_root, workspace_root=self.workspace_root
        )
        previous = self._load_previous_index()
        plan = build_task_plan(
            current=current, previous=previous, docs_subfolder=self.cfg.docs_subfolder
        )
        current.to_json_path(self.cfg.cache_dir / "index.json")
        tasks_to_json(plan, self.cfg.cache_dir / "tasks.json")
        return current, plan

    def snapshot(self) -> dict[str, str]:
        write_detection_snapshot(self.cfg)
        index, plan = self._index_and_plan()
        auto_dir = self.cfg.docs_root / "90_Auto"
        auto_dir.mkdir(parents=True, exist_ok=True)
        (auto_dir / "index.latest.json").write_text(
            index.model_dump_json(indent=2), encoding="utf-8"
        )
        (auto_dir / "tasks.latest.json").write_text(
            plan.model_dump_json(indent=2), encoding="utf-8"
        )
        return {
            "index": str(self.cfg.cache_dir / "index.json"),
            "tasks": str(self.cfg.cache_dir / "tasks.json"),
            "snapshot_index": str(auto_dir / "index.latest.json"),
            "snapshot_tasks": str(auto_dir / "tasks.latest.json"),
        }

    def _entity_payload(
        self, task_id: str, entity_type: str, index: ProjectIndex
    ) -> dict[str, Any]:
        if entity_type == "topic":
            matches = []
            for node in index.nodes:
                for endpoint in [*node.publishers, *node.subscribers]:
                    if endpoint.name == task_id:
                        matches.append(
                            {
                                "node": node.node_id,
                                "direction": endpoint.direction,
                                "type": endpoint.type_name,
                            }
                        )
            return {"topic": task_id, "connections": matches}

        if entity_type == "service":
            matches = []
            for node in index.nodes:
                for endpoint in [*node.services, *node.clients]:
                    if endpoint.name == task_id:
                        matches.append(
                            {
                                "node": node.node_id,
                                "direction": endpoint.direction,
                                "type": endpoint.type_name,
                            }
                        )
            return {"service": task_id, "connections": matches}

        if entity_type == "message":
            for interface in index.interfaces:
                key = f"{interface.package}/{interface.name}"
                if task_id == key:
                    return interface.model_dump()
            return {"message": task_id}

        if entity_type == "module":
            for package in index.packages:
                if package.name == task_id:
                    return package.model_dump()
            return {"module": task_id}

        if entity_type == "parameter":
            owners = []
            for node in index.nodes:
                for param in node.parameters:
                    if param.name == task_id:
                        owners.append({"node": node.node_id, "default": param.default})
            return {"parameter": task_id, "owners": owners}

        return {"entity": task_id, "type": entity_type}

    def _ai_draft(
        self, provider: LLMProvider, task, index: ProjectIndex, existing: str | None
    ) -> str:
        payload = self._entity_payload(task.entity_id, task.entity_type, index)
        try:
            return provider.generate_markdown(
                task=task, index=index, entity_payload=payload, existing_content=existing
            )
        except Exception as exc:
            fallback = MockProvider()
            draft = fallback.generate_markdown(
                task=task, index=index, entity_payload=payload, existing_content=existing
            )
            return draft + f"\n\n> provider_error: {exc}\n"

    def _compose_pages(
        self, index: ProjectIndex, plan: TaskPlan, provider: LLMProvider
    ) -> dict[str, str]:
        pages: dict[str, str] = {}

        pages["00_Home.md"] = home_page(index)
        pages["01_Project/Overview.md"] = overview_page(index)
        pages["01_Project/Glossary.md"] = glossary_page(index)
        pages["02_Architecture/Layered Architecture.md"] = layered_architecture_page(index)
        pages["02_Architecture/Dataflow.md"] = dataflow_page(index)
        pages["02_Architecture/ROS Graph.md"] = ros_graph_page(index)
        pages["02_Architecture/Module Map.md"] = module_map_page(index)

        for interface in index.interfaces:
            if interface.kind != "msg":
                continue
            rel = f"03_API/Messages/{message_filename(f'{interface.package}-{interface.name}')}"
            fields = [(field.name, field.type_name, field.section) for field in interface.fields]
            pages[rel] = message_page(index, interface.package, interface.name, fields)

        topics = sorted(
            {
                endpoint.name
                for node in index.nodes
                for endpoint in [*node.publishers, *node.subscribers]
            }
        )
        for topic in topics:
            rel = f"03_API/Topics/{topic_filename(topic)}"
            pages[rel] = topic_page(index, topic)

        services = sorted(
            {endpoint.name for node in index.nodes for endpoint in [*node.services, *node.clients]}
        )
        for service in services:
            rel = f"03_API/Services/{service_filename(service)}"
            pages[rel] = service_page(index, service)

        params = sorted({param.name for node in index.nodes for param in node.parameters})
        for param in params:
            rel = f"03_API/Parameters/{parameter_filename(param)}"
            pages[rel] = parameter_page(index, param)

        for package in index.packages:
            rel = f"04_Modules/{package.name}/{package.name}.md"
            pages[rel] = module_page(index, package.name)

        # Run provider for task entities and append draft sections only for changed content pages.
        for task in plan.tasks:
            if task.entity_type not in {"topic", "service", "message", "module", "parameter"}:
                continue
            rel = task.target_path.replace(f"{self.cfg.docs_subfolder}/", "")
            existing = pages.get(rel, "")
            draft = self._ai_draft(provider=provider, task=task, index=index, existing=existing)
            pages[rel] = existing.rstrip() + "\n\n## LLM Draft\n\n" + draft.strip() + "\n"

        page_list = sorted(pages.keys())
        pages["90_Auto/_Generated Graph.md"] = generated_graph_page(index, page_paths=page_list)
        pages["90_Auto/_Index.md"] = auto_index_page(index, page_paths=page_list, autogen_paths=[])
        pages["90_Auto/_Changelog.md"] = changelog_page(index, plan)
        pages["90_Auto/_Errors.md"] = errors_page(index, [])
        return pages

    def _qa_paths(self, root: Path, index: ProjectIndex) -> QAReport:
        link_errors = check_links(root)
        mermaid_errors = check_mermaid(root)
        hallucination_errors = check_hallucinations(root, index)
        errors = [*link_errors, *mermaid_errors, *hallucination_errors]
        return QAReport(passed=not errors, errors=errors)

    def validate(self) -> QAReport:
        index = build_project_index(
            repo_root=self.cfg.repo_root, workspace_root=self.workspace_root
        )
        report = self._qa_paths(self.cfg.docs_root, index)
        report_path = self.cfg.logs_dir / "qa_latest.json"
        report_path.write_text(report.model_dump_json(indent=2), encoding="utf-8")
        if report.errors:
            write_errors_page(self.cfg.docs_root / "90_Auto" / "_Errors.md", report.errors)
        return report

    def generate(self) -> dict[str, Any]:
        index, plan = self._index_and_plan()
        provider = self._provider()
        pages = self._compose_pages(index=index, plan=plan, provider=provider)

        # QA in staging folder before touching existing vault docs.
        stage_root = self.cfg.cache_dir / "staging" / datetime.now(UTC).strftime("%Y%m%d_%H%M%S")
        for rel, content in pages.items():
            target = stage_root / rel
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(content, encoding="utf-8")

        stage_report = self._qa_paths(stage_root, index)
        if not stage_report.passed:
            write_errors_page(self.cfg.docs_root / "90_Auto" / "_Errors.md", stage_report.errors)
            return {
                "ok": False,
                "provider": provider.name(),
                "errors": stage_report.errors,
                "stage_root": str(stage_root),
            }

        writer = MarkdownWriter(docs_root=self.cfg.docs_root, backups_root=self.cfg.backups_dir)
        outcome = writer.write_pages(pages)

        # Rebuild auto index with autogen file links now that we know them.
        relative_autogen = [
            str(Path(path).resolve().relative_to(self.cfg.docs_root.resolve()))
            for path in outcome.autogen
            if self.cfg.docs_root.resolve() in Path(path).resolve().parents
        ]
        index_page = auto_index_page(
            index, page_paths=sorted(pages.keys()), autogen_paths=sorted(relative_autogen)
        )
        generated_page = generated_graph_page(
            index,
            page_paths=sorted(set(list(pages.keys()) + relative_autogen)),
        )
        atomic_write(self.cfg.docs_root / "90_Auto" / "_Index.md", index_page)
        atomic_write(self.cfg.docs_root / "90_Auto" / "_Generated Graph.md", generated_page)

        if outcome.errors:
            write_errors_page(self.cfg.docs_root / "90_Auto" / "_Errors.md", outcome.errors)
        else:
            atomic_write(self.cfg.docs_root / "90_Auto" / "_Errors.md", errors_page(index, []))

        # Save snapshot in vault auto folder.
        auto_dir = self.cfg.docs_root / "90_Auto"
        auto_dir.mkdir(parents=True, exist_ok=True)
        (auto_dir / "index.latest.json").write_text(
            index.model_dump_json(indent=2), encoding="utf-8"
        )
        (auto_dir / "tasks.latest.json").write_text(
            plan.model_dump_json(indent=2), encoding="utf-8"
        )

        return {
            "ok": len(outcome.errors) == 0,
            "provider": provider.name(),
            "written": len(outcome.written),
            "autogen": len(outcome.autogen),
            "errors": outcome.errors,
            "docs_root": str(self.cfg.docs_root),
        }


def install_git_hook(cfg: DocsbotConfig) -> Path:
    hook_path = cfg.repo_root / ".git" / "hooks" / "pre-commit"
    hook_path.parent.mkdir(parents=True, exist_ok=True)
    script = "\n".join(
        [
            "#!/usr/bin/env bash",
            "set -euo pipefail",
            'REPO_ROOT="$(git rev-parse --show-toplevel)"',
            'cd "$REPO_ROOT"',
            (
                "if [ -x tools/docsbot/.venv/bin/docsbot ]; then "
                'DOCSBOT="tools/docsbot/.venv/bin/docsbot"; '
                'else DOCSBOT="docsbot"; fi'
            ),
            '$DOCSBOT generate --repo-root "$REPO_ROOT"',
            '$DOCSBOT validate --repo-root "$REPO_ROOT"',
        ]
    )
    hook_path.write_text(script + "\n", encoding="utf-8")
    hook_path.chmod(0o755)
    return hook_path


def dump_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
