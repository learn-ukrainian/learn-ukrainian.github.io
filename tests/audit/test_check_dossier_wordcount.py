from __future__ import annotations

from pathlib import Path

from scripts.audit import check_dossier_wordcount


def _write_dossier(root: Path, slug: str, word_count: int) -> Path:
    path = root / "docs" / "research" / "bio" / f"{slug}.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    body = " ".join(["слово"] * word_count)
    path.write_text(
        f"""---
title: fixture
---

{body}
""",
        encoding="utf-8",
    )
    return path


def test_wordcount_passes_at_template_floor(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    monkeypatch.setattr(check_dossier_wordcount, "PROJECT_ROOT", tmp_path)
    dossier = _write_dossier(tmp_path, "passing-fixture", 1200)

    assert check_dossier_wordcount.main(["--paths", str(dossier)]) == 0

    output = capsys.readouterr().out
    assert "docs/research/bio/passing-fixture.md" in output
    assert "1200   1200  PASS" in output
    assert "All checked dossiers meet the 1200-word floor." in output


def test_paths_can_be_relative_to_current_directory(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    monkeypatch.setattr(check_dossier_wordcount, "PROJECT_ROOT", tmp_path)
    dossier = _write_dossier(tmp_path, "cwd-relative-fixture", 1200)
    monkeypatch.chdir(dossier.parent)

    assert check_dossier_wordcount.main(["--paths", dossier.name]) == 0

    output = capsys.readouterr().out
    assert "docs/research/bio/cwd-relative-fixture.md" in output
    assert "1200   1200  PASS" in output


def test_wordcount_strips_html_tags_but_keeps_visible_text(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    monkeypatch.setattr(check_dossier_wordcount, "PROJECT_ROOT", tmp_path)
    dossier = _write_dossier(tmp_path, "html-fixture", 1199)
    dossier.write_text(
        dossier.read_text(encoding="utf-8") + "\n<div><kbd>слово</kbd></div>\n",
        encoding="utf-8",
    )

    assert check_dossier_wordcount.main(["--paths", str(dossier)]) == 0

    output = capsys.readouterr().out
    assert "docs/research/bio/html-fixture.md" in output
    assert "1200   1200  PASS" in output


def test_changed_mode_uses_changed_research_dossiers_only(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    monkeypatch.setattr(check_dossier_wordcount, "PROJECT_ROOT", tmp_path)
    dossier = _write_dossier(tmp_path, "changed-fixture", 1200)
    ignored = tmp_path / "docs" / "notes.md"
    ignored.parent.mkdir(parents=True, exist_ok=True)
    ignored.write_text("слово\n", encoding="utf-8")
    monkeypatch.setattr(
        check_dossier_wordcount,
        "changed_paths",
        lambda: [dossier, ignored],
    )

    assert check_dossier_wordcount.main(["--changed"]) == 0

    output = capsys.readouterr().out
    assert "docs/research/bio/changed-fixture.md" in output
    assert "docs/notes.md" not in output


def test_wordcount_fails_below_template_floor(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    monkeypatch.setattr(check_dossier_wordcount, "PROJECT_ROOT", tmp_path)
    dossier = _write_dossier(tmp_path, "failing-fixture", 1199)

    assert check_dossier_wordcount.main(["--paths", str(dossier)]) == 1

    output = capsys.readouterr().out
    assert "docs/research/bio/failing-fixture.md" in output
    assert "1199   1200  FAIL" in output
    assert "1 dossier(s) below the 1200-word floor." in output
