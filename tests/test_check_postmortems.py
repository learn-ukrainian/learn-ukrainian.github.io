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
