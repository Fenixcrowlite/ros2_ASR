from pathlib import Path

from docsbot.qa.link_checker import check_links


def test_link_checker_detects_missing_link(tmp_path: Path) -> None:
    docs = tmp_path / "Wiki-ASR"
    docs.mkdir()
    (docs / "00_Home.md").write_text(
        "See [[01_Project/Overview]] and [[Missing Page]]", encoding="utf-8"
    )
    (docs / "01_Project").mkdir()
    (docs / "01_Project" / "Overview.md").write_text("ok", encoding="utf-8")

    errors = check_links(docs)
    assert any("Missing Page" in error for error in errors)


def test_link_checker_accepts_existing_link(tmp_path: Path) -> None:
    docs = tmp_path / "Wiki-ASR"
    docs.mkdir()
    (docs / "A.md").write_text("[[B]]", encoding="utf-8")
    (docs / "B.md").write_text("ok", encoding="utf-8")

    errors = check_links(docs)
    assert errors == []
