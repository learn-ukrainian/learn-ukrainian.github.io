from __future__ import annotations

from pathlib import Path

from scripts.audit import check_dossier_wordcount

# The fixture frontmatter block ("---\ntitle: fixture\n---") contributes 4
# whitespace-delimited tokens, which the total-word count includes. Subtract
# them from the body so the file's total word count equals `total_words`.
_FRONTMATTER_TOKENS = 4


def _write_dossier(root: Path, slug: str, total_words: int) -> Path:
    path = root / "docs" / "research" / "bio" / f"{slug}.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    body = " ".join(["слово"] * (total_words - _FRONTMATTER_TOKENS))
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


def test_total_count_includes_markup_and_urls(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    # Total-word count is wc -w semantics: markdown markup, HTML, and URLs all
    # count as words (unlike a prose-stripping count). 1196 body words + 4
    # frontmatter tokens = 1200 already; the extra markup tokens push it over.
    monkeypatch.setattr(check_dossier_wordcount, "PROJECT_ROOT", tmp_path)
    dossier = _write_dossier(tmp_path, "markup-fixture", 1200)
    dossier.write_text(
        dossier.read_text(encoding="utf-8")
        + "\n[link text](https://example.org/path) <kbd>x</kbd>\n",
        encoding="utf-8",
    )

    assert check_dossier_wordcount.main(["--paths", str(dossier)]) == 0

    output = capsys.readouterr().out
    # 1200 + tokens: "[link" "text](https://example.org/path)" "<kbd>x</kbd>" = 1203
    assert "1203   1200  PASS" in output


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


def test_non_dossier_research_subdirs_are_exempt(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    # docs/research/atlas/ and docs/research/lexicon/ hold tooling / research
    # notes, not curriculum dossiers — they must NOT trip the 1200-word floor
    # even though they live under docs/research/. (Regression: a 444-word Atlas
    # calque-triage note failed the gate before this exemption.)
    monkeypatch.setattr(check_dossier_wordcount, "PROJECT_ROOT", tmp_path)
    for subdir in ("atlas", "lexicon"):
        note = tmp_path / "docs" / "research" / subdir / "short-note.md"
        note.parent.mkdir(parents=True, exist_ok=True)
        note.write_text("слово слово слово\n", encoding="utf-8")
        assert not check_dossier_wordcount._is_research_dossier(note)

    # A real track dossier under the same root is still gated.
    dossier = _write_dossier(tmp_path, "real-dossier", 1200)
    assert check_dossier_wordcount._is_research_dossier(dossier)

    atlas_note = tmp_path / "docs" / "research" / "atlas" / "short-note.md"
    monkeypatch.setattr(
        check_dossier_wordcount, "changed_paths", lambda: [atlas_note, dossier]
    )
    assert check_dossier_wordcount.main(["--changed"]) == 0
    output = capsys.readouterr().out
    assert "atlas/short-note.md" not in output
    assert "docs/research/bio/real-dossier.md" in output


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
