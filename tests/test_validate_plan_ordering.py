from __future__ import annotations

from pathlib import Path

from scripts.validate import validate_plan_ordering


def _write_plan(path: Path, slug: str, *, intentional: bool = False) -> None:
    marker = "slug_intentional: true\n" if intentional else ""
    path.write_text(f"slug: {slug}\n{marker}", encoding="utf-8")


def test_unmarked_slug_filename_mismatch_errors(tmp_path: Path, monkeypatch) -> None:
    plan_dir = tmp_path / "plans" / "lit"
    plan_dir.mkdir(parents=True)
    _write_plan(plan_dir / "english-title.yaml", "ukrainian-title")
    monkeypatch.setattr(validate_plan_ordering, "PLANS_DIR", tmp_path / "plans")

    issues, fixes = validate_plan_ordering.validate_track("lit", ["english-title"])

    assert fixes == 0
    assert issues == [
        "[lit] english-title.yaml: slug='ukrainian-title', expected='english-title'; "
        "add slug_intentional: true if this mismatch is canonical"
    ]


def test_marked_slug_filename_mismatch_passes(tmp_path: Path, monkeypatch) -> None:
    plan_dir = tmp_path / "plans" / "lit"
    plan_dir.mkdir(parents=True)
    _write_plan(plan_dir / "english-title.yaml", "ukrainian-title", intentional=True)
    monkeypatch.setattr(validate_plan_ordering, "PLANS_DIR", tmp_path / "plans")

    issues, fixes = validate_plan_ordering.validate_track("lit", ["english-title"])

    assert fixes == 0
    assert issues == []


def test_legacy_slug_exception_is_exact(tmp_path: Path, monkeypatch) -> None:
    plan_dir = tmp_path / "plans" / "hist"
    plan_dir.mkdir(parents=True)
    _write_plan(plan_dir / "zunr.yaml", "different-zunr-slug")
    monkeypatch.setattr(validate_plan_ordering, "PLANS_DIR", tmp_path / "plans")

    issues, fixes = validate_plan_ordering.validate_track("hist", ["zunr"])

    assert fixes == 0
    assert issues == [
        "[hist] zunr.yaml: slug='different-zunr-slug', expected='zunr'; "
        "add slug_intentional: true if this mismatch is canonical"
    ]
