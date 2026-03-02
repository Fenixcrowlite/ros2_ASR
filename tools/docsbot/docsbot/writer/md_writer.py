from __future__ import annotations

from pathlib import Path

from docsbot.runtime.backup import BackupManager
from docsbot.runtime.filesystem import atomic_write, is_user_owned, parse_frontmatter

from .models import WriteOutcome


class MarkdownWriter:
    def __init__(self, docs_root: Path, backups_root: Path) -> None:
        self.docs_root = docs_root
        self.backup_manager = BackupManager(backups_root)

    def write_pages(self, pages: dict[str, str]) -> WriteOutcome:
        outcome = WriteOutcome()
        for rel_path, content in sorted(pages.items()):
            target = (self.docs_root / rel_path).resolve()
            if (
                self.docs_root.resolve() not in target.parents
                and target != self.docs_root.resolve()
            ):
                outcome.errors.append(f"refusing to write outside docs root: {target}")
                continue

            if target.exists() and is_user_owned(target):
                autogen_target = target.with_name(f"{target.stem}.autogen{target.suffix}")
                if autogen_target.exists():
                    self.backup_manager.backup(autogen_target, self.docs_root)
                atomic_write(autogen_target, content)
                outcome.autogen.append(str(autogen_target))
                continue

            if target.exists():
                self.backup_manager.backup(target, self.docs_root)

            atomic_write(target, content)
            frontmatter = parse_frontmatter(content)
            if not frontmatter:
                outcome.errors.append(f"missing frontmatter in generated page: {rel_path}")
            outcome.written.append(str(target))

        return outcome
