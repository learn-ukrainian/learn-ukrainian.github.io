"""Parallel tracks reuse base plans without taking ownership of their order."""


import pytest

from scripts.validate import validate_plan_ordering as validator

pytestmark = pytest.mark.reads_content


def test_parallel_level_validates_real_base_plan(monkeypatch, capsys):
    curriculum = validator.load_curriculum()
    parallel = curriculum["a1-v1"]
    assert parallel.base_level == "a1"
    assert len(parallel.modules) == 55
    assert parallel.modules[7] == "things-have-gender"
    plan = validator.PLANS_DIR / "a1" / "things-have-gender.yaml"
    before = plan.read_bytes()
    monkeypatch.setattr("sys.argv", ["validate_plan_ordering.py", "a1-v1", "--fix"])

    assert validator.main() == 0
    assert "All 55 modules verified — no issues found" in capsys.readouterr().out
    assert plan.read_bytes() == before


@pytest.mark.parametrize("base_level", ["a1", "b2"])
def test_parallel_level_requires_listed_base_plan(tmp_path, monkeypatch, base_level):
    (tmp_path / base_level).mkdir()
    monkeypatch.setattr(validator, "PLANS_DIR", tmp_path)

    issues, fixes = validator.validate_track(
        "preview", ["missing"], base_level=base_level
    )

    assert issues == ["[preview] MISSING: missing.yaml (seq 1) has no plan file"]
    assert fixes == 0


def test_parallel_level_reports_missing_base_directory(tmp_path, monkeypatch):
    monkeypatch.setattr(validator, "PLANS_DIR", tmp_path)
    issues, fixes = validator.validate_track("preview", ["missing"], base_level="b2")
    assert issues == [f"[preview] Plan directory not found: {tmp_path / 'b2'}"]
    assert fixes == 0


def test_parallel_level_checks_selected_metadata_only(tmp_path, monkeypatch):
    base_dir = tmp_path / "b2"
    base_dir.mkdir()
    (base_dir / "selected.yaml").write_text(
        "slug: wrong\nlevel: B2-V2\nmodule: b2-008\nsequence: 8\n",
        encoding="utf-8",
    )
    # Unselected base plans must not even be parsed as this track's plans.
    (base_dir / "unselected.yaml").write_text("[invalid yaml", encoding="utf-8")
    monkeypatch.setattr(validator, "PLANS_DIR", tmp_path)

    issues, fixes = validator.validate_track("b2-v2", ["selected"], base_level="b2")

    assert len(issues) == 2
    assert "slug='wrong'" in issues[0]
    assert "level='B2-V2'" in issues[1]
    assert fixes == 0


def test_ordinary_track_retains_order_orphan_and_missing_checks(tmp_path, monkeypatch):
    base_dir = tmp_path / "a1"
    base_dir.mkdir()
    (base_dir / "selected.yaml").write_text(
        "slug: selected\nlevel: A1\nmodule: a1-008\nsequence: 8\n",
        encoding="utf-8",
    )
    (base_dir / "unselected.yaml").write_text("slug: unselected\n", encoding="utf-8")
    monkeypatch.setattr(validator, "PLANS_DIR", tmp_path)

    issues, fixes = validator.validate_track("a1", ["selected", "missing"])

    assert len(issues) == 4
    for expected in ("sequence=8, expected=1", "module='a1-008'", "MISSING", "ORPHAN"):
        assert any(expected in issue for issue in issues)
    assert fixes == 0


@pytest.mark.parametrize("parallel", [False, True])
def test_level_variants_remain_independent_between_plans(tmp_path, monkeypatch, parallel):
    base_dir = tmp_path / "lit-essay"
    base_dir.mkdir()
    for slug, level in (("first", "LIT"), ("second", "LIT-ESSAY")):
        (base_dir / f"{slug}.yaml").write_text(f"slug: {slug}\nlevel: {level}\n", encoding="utf-8")
    monkeypatch.setattr(validator, "PLANS_DIR", tmp_path)

    issues, fixes = validator.validate_track(
        "preview" if parallel else "lit-essay", ["first", "second"],
        base_level="lit-essay" if parallel else None,
    )

    assert issues == []
    assert fixes == 0


def test_canonical_subset_still_checks_unpublished_plan_metadata(tmp_path, monkeypatch, capsys):
    plans = tmp_path / "a1"
    plans.mkdir()
    (plans / "first.yaml").write_text("slug: first\nlevel: A1\nsequence: 99\n")
    monkeypatch.setattr(validator, "PLANS_DIR", tmp_path)
    monkeypatch.setattr(validator, "load_curriculum", lambda: {
        "a1": validator.CurriculumLevel([], plan_modules=["first"]),
    })
    monkeypatch.setattr("sys.argv", ["validate_plan_ordering.py", "a1"])
    assert validator.main() == 1
    assert "sequence=99, expected=1" in capsys.readouterr().out
