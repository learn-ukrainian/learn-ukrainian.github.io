from __future__ import annotations

from pathlib import Path

from scripts.audit import check_postmortems

VALID_ENTRY = """# Bug Autopsy: Cache Invalidation Failure

## Symptom
Users saw stale generated lessons after changing the source plan.

## Root cause
The cache key omitted the source plan hash.

## Prevention
The cache manifest now includes the source plan hash and a regression test.

## Links
- Issue: #1522
- Fix: abc1234
"""


def _write_tree(tmp_path: Path, entries: dict[str, str], index: str | None = None) -> None:
    autopsies = tmp_path / "docs" / "bug-autopsies"
    autopsies.mkdir(parents=True)
    for filename, content in entries.items():
        (autopsies / filename).write_text(content, "utf-8")
    (autopsies / "INDEX.md").write_text(
        index
        or """# Bug Autopsy Index

One-liner per bug.

<!-- INDEX-START -->
| Date | Issue | Category | Summary |
|------|-------|----------|---------|
<!-- INDEX-END -->
""",
        "utf-8",
    )


def test_validates_valid_entry(tmp_path: Path, capsys) -> None:
    _write_tree(tmp_path, {"cache-invalidation.md": VALID_ENTRY})

    exit_code = check_postmortems.main([], project_root=tmp_path)

    captured = capsys.readouterr()
    assert exit_code == 0
    assert "✅ 1 postmortems validated" in captured.out


def test_flags_missing_symptom(tmp_path: Path, capsys) -> None:
    _write_tree(
        tmp_path,
        {"cache-invalidation.md": VALID_ENTRY.replace("## Symptom\n", "")},
    )

    exit_code = check_postmortems.main(["--regenerate-index"], project_root=tmp_path)

    captured = capsys.readouterr()
    assert exit_code == 1
    assert (
        "❌ docs/bug-autopsies/cache-invalidation.md — missing required field: Symptom"
        in captured.out
    )


def test_flags_missing_prevention(tmp_path: Path, capsys) -> None:
    _write_tree(
        tmp_path,
        {"cache-invalidation.md": VALID_ENTRY.replace("## Prevention\n", "")},
    )

    exit_code = check_postmortems.main(["--regenerate-index"], project_root=tmp_path)

    captured = capsys.readouterr()
    assert exit_code == 1
    assert (
        "❌ docs/bug-autopsies/cache-invalidation.md — missing required field: Prevention"
        in captured.out
    )


def test_flags_missing_links(tmp_path: Path, capsys) -> None:
    _write_tree(
        tmp_path,
        {
            "cache-invalidation.md": VALID_ENTRY.replace(
                "## Links\n- Issue: #1522\n- Fix: abc1234\n",
                "",
            )
        },
    )

    exit_code = check_postmortems.main(["--regenerate-index"], project_root=tmp_path)

    captured = capsys.readouterr()
    assert exit_code == 1
    assert (
        "❌ docs/bug-autopsies/cache-invalidation.md — missing required field: Links"
        in captured.out
    )


def test_quiet_mode_silent_on_success(tmp_path: Path, capsys) -> None:
    _write_tree(tmp_path, {"cache-invalidation.md": VALID_ENTRY})

    exit_code = check_postmortems.main(["--quiet"], project_root=tmp_path)

    captured = capsys.readouterr()
    assert exit_code == 0
    assert captured.out == ""


def test_quiet_mode_reports_failures(tmp_path: Path, capsys) -> None:
    _write_tree(
        tmp_path,
        {"cache-invalidation.md": VALID_ENTRY.replace("## Symptom\n", "")},
    )

    exit_code = check_postmortems.main(["--quiet"], project_root=tmp_path)

    captured = capsys.readouterr()
    assert exit_code == 1
    assert "missing required field: Symptom" in captured.out


def test_index_regeneration_preserves_outer_content(tmp_path: Path) -> None:
    index = """# Bug Autopsy Index

Intro stays.

<!-- INDEX-START -->
stale content
<!-- INDEX-END -->

Trailing note stays.
"""
    _write_tree(tmp_path, {"cache-invalidation.md": VALID_ENTRY}, index=index)

    check_postmortems.main([], project_root=tmp_path)

    regenerated = (tmp_path / "docs" / "bug-autopsies" / "INDEX.md").read_text("utf-8")
    assert regenerated.startswith("# Bug Autopsy Index\n\nIntro stays.\n\n")
    assert regenerated.endswith("\n\nTrailing note stays.\n")
    assert "| cache-invalidation | Cache Invalidation Failure |" in regenerated


def test_index_regeneration_idempotent(tmp_path: Path) -> None:
    _write_tree(tmp_path, {"cache-invalidation.md": VALID_ENTRY})

    check_postmortems.main([], project_root=tmp_path)
    first = (tmp_path / "docs" / "bug-autopsies" / "INDEX.md").read_text("utf-8")
    check_postmortems.main([], project_root=tmp_path)
    second = (tmp_path / "docs" / "bug-autopsies" / "INDEX.md").read_text("utf-8")

    assert second == first


def test_index_regeneration_preserves_sort_order(tmp_path: Path) -> None:
    _write_tree(
        tmp_path,
        {
            "zulu-cache.md": VALID_ENTRY.replace(
                "Cache Invalidation Failure",
                "Zulu Cache Failure",
            ),
            "alpha-cache.md": VALID_ENTRY.replace(
                "Cache Invalidation Failure",
                "Alpha Cache Failure",
            ),
        },
    )

    check_postmortems.main([], project_root=tmp_path)

    regenerated = (tmp_path / "docs" / "bug-autopsies" / "INDEX.md").read_text("utf-8")
    assert regenerated.index("| alpha-cache |") < regenerated.index("| zulu-cache |")


# --- #3045: non-lossy regen (slug-mismatch dups + multi-incident + --check) ---


_INDEX_HEADER = (
    "# Bug Autopsy Index\n\n<!-- INDEX-START -->\n"
    "| Date | Issue | Category | Summary |\n"
    "|------|-------|----------|---------|\n"
)


def test_no_duplicate_row_for_slug_mismatched_curated_row(tmp_path: Path) -> None:
    # A curated row whose Category ("ocr-pivot") differs from the filename slug
    # ("esum-ocr-pivot") but links the file in its Summary must NOT get a
    # duplicate generated row appended. The file's issue also differs from the
    # row's, so only the `<slug>.md` summary link can match it.
    index = (
        _INDEX_HEADER
        + "| 2026-05-21 | #2001 | ocr-pivot | ESUM re-OCR pivot. Detail in `esum-ocr-pivot.md`. |\n"
        + "<!-- INDEX-END -->\n"
    )
    file_entry = VALID_ENTRY.replace("Issue: #1522", "Issue: #9999")
    _write_tree(tmp_path, {"esum-ocr-pivot.md": file_entry}, index=index)

    check_postmortems.main([], project_root=tmp_path)

    regenerated = (tmp_path / "docs" / "bug-autopsies" / "INDEX.md").read_text("utf-8")
    assert "| ocr-pivot |" in regenerated  # curated row preserved
    assert "| esum-ocr-pivot |" not in regenerated  # no slug-keyed duplicate
    assert regenerated.count("esum-ocr-pivot.md") == 1


def test_multi_incident_rows_preserved(tmp_path: Path) -> None:
    # A file with multiple curated rows (multi-incident autopsy) keeps all rows;
    # regen must not collapse to one or append a duplicate.
    index = (
        _INDEX_HEADER
        + "| 2026-05-10 | — | secret-leakage | Incident A. Detail in `secret-leakage.md`. |\n"
        + "| 2026-05-19 | — | secret-leakage | Incident B. Detail in `secret-leakage.md`. |\n"
        + "<!-- INDEX-END -->\n"
    )
    _write_tree(tmp_path, {"secret-leakage.md": VALID_ENTRY}, index=index)

    check_postmortems.main([], project_root=tmp_path)

    regenerated = (tmp_path / "docs" / "bug-autopsies" / "INDEX.md").read_text("utf-8")
    assert regenerated.count("| secret-leakage |") == 2  # both incidents kept
    assert "Incident A" in regenerated
    assert "Incident B" in regenerated


def test_check_mode_flags_stale_index_without_writing(tmp_path: Path, capsys) -> None:
    _write_tree(tmp_path, {"cache-invalidation.md": VALID_ENTRY})
    index_path = tmp_path / "docs" / "bug-autopsies" / "INDEX.md"
    before = index_path.read_text("utf-8")

    exit_code = check_postmortems.main(["--check"], project_root=tmp_path)

    captured = capsys.readouterr()
    assert exit_code == 1
    assert "INDEX.md is stale" in captured.out
    assert index_path.read_text("utf-8") == before  # dry-run: not written


def test_check_mode_passes_when_index_current(tmp_path: Path, capsys) -> None:
    _write_tree(tmp_path, {"cache-invalidation.md": VALID_ENTRY})
    check_postmortems.main([], project_root=tmp_path)  # make it current
    index_path = tmp_path / "docs" / "bug-autopsies" / "INDEX.md"
    current = index_path.read_text("utf-8")

    exit_code = check_postmortems.main(["--check"], project_root=tmp_path)

    captured = capsys.readouterr()
    assert exit_code == 0
    assert "INDEX.md is stale" not in captured.out
    assert index_path.read_text("utf-8") == current  # unchanged
