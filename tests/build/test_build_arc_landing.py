"""Tests for scripts/build/build_arc_landing.py (#8397 child 8)."""

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path

import pytest
import yaml

from scripts.build import build_arc_landing as gen
from scripts.build import build_landing_pages
from scripts.curriculum.arc.loader import ArcPosition, load_arc

pytestmark = pytest.mark.reads_content

REPO_ROOT = Path(__file__).resolve().parents[2]
LEVEL = "a1"


def _arc(*slugs: str) -> list[ArcPosition]:
    return [
        ArcPosition(
            position=index,
            slug=slug,
            est_lessons=2,
            job=f"Job of {slug}",
            inventory_text=None,
            phase="A1.1" if index <= 3 else "A1.2",
            skills_text="",
            skills=[],
            standard_line_refs=[],
        )
        for index, slug in enumerate(slugs, start=1)
    ]


def _write_yaml(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(data, allow_unicode=True), encoding="utf-8")


def _plan(root: gen.Roots, slug: str, lessons: int, title: str = "Назва модуля") -> None:
    _write_yaml(
        root.plans / f"{slug}.yaml",
        {
            "plan_schema": 2,
            "slug": slug,
            "title": title,
            "lessons": [{"n": n, "title": f"Урок {n}"} for n in range(1, lessons + 1)],
        },
    )


def _scope(root: gen.Roots, slug: str) -> None:
    _write_yaml(
        root.scope / f"{slug}.yaml",
        {"letters": {"count": 13, "list": []}, "grammar": {"count": 2, "ids": []}, "vocabulary": {"core_count": 30}},
    )


def _review(root: gen.Roots, slug: str, filename: str, verdict: str = "APPROVE") -> None:
    _write_yaml(root.state / slug / filename, {"verdict": verdict})


def _lesson_built(root: gen.Roots, slug: str, n: int, passed: bool = True) -> None:
    page = root.docs / slug / f"{n}.mdx"
    page.parent.mkdir(parents=True, exist_ok=True)
    page.write_text("---\ntitle: x\n---\n", encoding="utf-8")
    _write_yaml(root.state / slug / f"lesson-{n}.gates.yaml", {"passed": passed})


def _titles(root: gen.Roots, *slugs: str) -> None:
    _write_yaml(
        root.plans / gen.TITLES_EN_FILE,
        {"titles_schema": 1, "titles": {slug: f"Title of {slug}" for slug in slugs}},
    )


def _generated(root: gen.Roots, arc: list[ArcPosition]) -> dict[Path, str]:
    """``generated_files`` with an authored title for every arc slug unless the test wrote its own."""
    if not (root.plans / gen.TITLES_EN_FILE).exists():
        _titles(root, *(position.slug for position in arc))
    return gen.generated_files(root, arc)


def _states(root: gen.Roots, arc: list[ArcPosition]) -> dict[str, str]:
    data = json.loads(_generated(root, arc)[root.data_json])
    return {record["slug"]: record["state"] for record in data["positions"]}


LEVEL_STATUS = (
    '# header\n\na1:\n  planned: 99  # note kept\n  status: auto\n  description: "x"\n\n'
    "a2:\n  planned: 76\n  status: auto\n"
)


@pytest.fixture
def root(tmp_path: Path) -> gen.Roots:
    roots = gen.Roots(tmp_path, LEVEL)
    roots.level_status.parent.mkdir(parents=True)
    roots.level_status.write_text(LEVEL_STATUS, encoding="utf-8")
    return roots


def test_real_arc_generates_55_positions_and_is_current() -> None:
    roots = gen.Roots(REPO_ROOT, LEVEL)
    arc = load_arc(LEVEL)
    files = gen.generated_files(roots, arc)

    assert len(arc) == 55
    assert len(files) == 55 + 3 + 2
    assert gen.stale_files(files) == [], "run python -m scripts.build.build_arc_landing a1 --write"
    records = json.loads(files[roots.data_json])["positions"]
    assert [r["position"] for r in records] == list(range(1, 56))
    assert [r["title_en"] for r in records[:2]] == ["Introduction to Ukrainian", "Sounds, letters and hello"]
    assert records[4]["title_en"] == "Reading Ukrainian"
    # Positions climb the ladder as plans are reviewed and lessons built; every state is a ladder state.
    assert {r["state"] for r in records} <= {"planned", "plan_reviewed", "built", "reviewed"}
    assert all(r["previous_edition_href"] in (None, f"/a1-v1/{r['slug']}/") for r in records)
    recorded = json.loads(roots.data_json.read_text(encoding="utf-8"))["positions"]
    assert [(r["slug"], r["state"], r["scope"]) for r in records] == [
        (r["slug"], r["state"], r["scope"]) for r in recorded
    ]
    status = yaml.safe_load(roots.level_status.read_text(encoding="utf-8"))
    assert status["a1"]["planned"] == len(arc)


def test_generation_is_byte_stable(root: gen.Roots) -> None:
    arc = _arc("alpha", "beta")
    _plan(root, "alpha", 2)
    assert _generated(root, arc) == _generated(root, arc)


def _stub_fresh_plan_status(monkeypatch, root):
    """Unit-test the upper ladder independently; real freshness is tested below."""
    from scripts.build.fresh import plan_manifest

    def status(level, slug, **kwargs):
        path = root.state / slug / "plan-review.yaml"
        review = yaml.safe_load(path.read_text()) if path.is_file() else {}
        return {"state": "reviewed_promoted" if review.get("verdict") == "APPROVE" else "unreviewed"}

    monkeypatch.setattr(plan_manifest, "plan_review_status", status)


def test_states_climb_one_predicate_at_a_time(root: gen.Roots, monkeypatch: pytest.MonkeyPatch) -> None:
    _stub_fresh_plan_status(monkeypatch, root)
    arc = _arc("no-plan", "plan-unreviewed", "plan-reviewed", "built", "reviewed")
    _plan(root, "plan-unreviewed", 1)
    _review(root, "plan-unreviewed", "plan-review.yaml", "REVISE")
    _plan(root, "plan-reviewed", 2)
    _review(root, "plan-reviewed", "plan-review.yaml")
    _lesson_built(root, "plan-reviewed", 1)  # lesson 2 missing
    _plan(root, "built", 2)
    _review(root, "built", "plan-review.yaml")
    _lesson_built(root, "built", 1)
    _lesson_built(root, "built", 2)
    _plan(root, "reviewed", 1)
    _review(root, "reviewed", "plan-review.yaml")
    _lesson_built(root, "reviewed", 1)
    _review(root, "reviewed", "module-verdict.yaml")

    assert _states(root, arc) == {
        "no-plan": "planned",
        "plan-unreviewed": "planned",
        "plan-reviewed": "plan_reviewed",
        "built": "built",
        "reviewed": "reviewed",
    }


def test_a_missing_file_never_yields_a_higher_state(root: gen.Roots, monkeypatch: pytest.MonkeyPatch) -> None:
    _stub_fresh_plan_status(monkeypatch, root)
    arc = _arc("a", "b", "c", "d")
    # a: verdict approved but the plan file is gone.
    _review(root, "a", "plan-review.yaml")
    # b: module verdict without gates -> stays plan_reviewed.
    _plan(root, "b", 1)
    _review(root, "b", "plan-review.yaml")
    _review(root, "b", "module-verdict.yaml")
    # c: page exists but the gates report failed.
    _plan(root, "c", 1)
    _review(root, "c", "plan-review.yaml")
    _lesson_built(root, "c", 1, passed=False)
    # d: module verdict and gates but the plan was never approved.
    _plan(root, "d", 1)
    _lesson_built(root, "d", 1)
    _review(root, "d", "module-verdict.yaml")

    assert _states(root, arc) == {"a": "planned", "b": "plan_reviewed", "c": "plan_reviewed", "d": "planned"}


def test_reviewed_state_trusts_the_file_when_no_findings_database_exists(root: gen.Roots, monkeypatch: pytest.MonkeyPatch) -> None:
    _stub_fresh_plan_status(monkeypatch, root)
    """CI never has a findings database (``batch_state/`` is gitignored): the committed file is trusted."""
    _plan(root, "reviewed", 1)
    _review(root, "reviewed", "plan-review.yaml")
    _lesson_built(root, "reviewed", 1)
    _review(root, "reviewed", "module-verdict.yaml")

    assert _states(root, _arc("reviewed")) == {"reviewed": "reviewed"}


def test_reviewed_state_fails_on_a_stale_approve_when_a_findings_database_is_present(
    root: gen.Roots, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The reviewer's scenario (#8774 r5/r6): a saved APPROVE a later database write has superseded."""
    _stub_fresh_plan_status(monkeypatch, root)
    from scripts.review import findings_db, fixloop

    _plan(root, "reviewed", 1)
    _review(root, "reviewed", "plan-review.yaml")
    _lesson_built(root, "reviewed", 1)
    _review(root, "reviewed", "module-verdict.yaml")  # verdict: APPROVE, on file

    db_file = findings_db.db_path(root.level, repo_root=root.repo)
    db_file.parent.mkdir(parents=True, exist_ok=True)
    db_file.touch()  # a findings database is present: this module's APPROVE must be fresh
    monkeypatch.setattr(fixloop, "module_verdict_problems", lambda *a, **k: ["a fresh recomputation is HOLD"])

    with pytest.raises(ValueError, match=r"reviewed.*stale"):
        _states(root, _arc("reviewed"))


def test_missing_state_directory_is_planned_not_an_error(root: gen.Roots) -> None:
    _plan(root, "alpha", 1)
    assert not root.state.exists()
    assert _states(root, _arc("alpha")) == {"alpha": "planned"}


def test_malformed_state_file_fails_loudly(root: gen.Roots) -> None:
    _plan(root, "alpha", 1)
    (root.state / "alpha").mkdir(parents=True)
    (root.state / "alpha" / "plan-review.yaml").write_text("verdict: [unclosed", encoding="utf-8")
    assert _states(root, _arc("alpha")) == {"alpha": "planned"}


def test_plan_supplies_title_lessons_and_scope(root: gen.Roots) -> None:
    _plan(root, "alpha", 3, title="Звуки і привіт")
    _scope(root, "alpha")
    files = _generated(root, _arc("alpha", "beta"))
    alpha, beta = json.loads(files[root.data_json])["positions"]

    assert alpha["title_uk"] == "Звуки і привіт"
    assert alpha["lessons"] == 3
    assert alpha["lesson_numbers"] == [1, 2, 3]
    assert alpha["lesson_titles"] == ["Урок 1", "Урок 2", "Урок 3"]
    assert alpha["scope"] == {"letters": 13, "grammar_points": 2, "core_lemmas": 30}
    assert 'title: "Звуки і привіт · Title of alpha"' in files[root.docs / "alpha" / "index.mdx"]
    assert (beta["title_uk"], beta["lessons"], beta["scope"], beta["lesson_titles"]) == (None, None, None, [])
    assert beta["lesson_numbers"] == []
    assert 'title: "Title of beta"' in files[root.docs / "beta" / "index.mdx"]


def test_frontmatter_carries_arc_keys_and_an_empty_body(root: gen.Roots) -> None:
    files = _generated(root, _arc("sounds-letters-and-hello"))
    landing = files[root.docs / "index.mdx"]
    module = files[root.docs / "sounds-letters-and-hello" / "index.mdx"]

    for text, kind in ((landing, "landing"), (module, "module")):
        _, frontmatter, body = text.split("---\n", 2)
        data = yaml.safe_load(frontmatter)
        assert data["arc_kind"] == kind and data["arc_level"] == LEVEL and data["title"]
        assert body == ""
    assert yaml.safe_load(module.split("---\n")[1])["arc_slug"] == "sounds-letters-and-hello"
    assert gen.humanise_slug("sounds-letters-and-hello") == "Sounds letters and hello"


def test_english_titles_are_authored_never_derived_from_the_slug(root: gen.Roots) -> None:
    arc = _arc("reading-ukrainian", "sounds-letters-and-hello")
    with pytest.raises(ValueError, match="is missing"):
        gen.generated_files(root, arc)

    _write_yaml(
        root.plans / gen.TITLES_EN_FILE,
        {"titles": {"reading-ukrainian": "Reading Ukrainian", "sounds-letters-and-hello": "Sounds, letters and hello"}},
    )
    files = gen.generated_files(root, arc)
    records = json.loads(files[root.data_json])["positions"]
    assert [record["title_en"] for record in records] == ["Reading Ukrainian", "Sounds, letters and hello"]
    assert 'title: "Reading Ukrainian"' in files[root.docs / "reading-ukrainian" / "index.mdx"]


@pytest.mark.parametrize(
    ("titles", "message"),
    [
        ({"reading-ukrainian": "Reading Ukrainian"}, r"missing \['sounds-letters-and-hello'\]"),
        (
            {"reading-ukrainian": "A", "sounds-letters-and-hello": "B", "extra": "C"},
            r"not in the arc \['extra'\]",
        ),
        ({"reading-ukrainian": "A", "sounds-letters-and-hello": "  "}, "non-blank"),
        ({"reading-ukrainian": "A", "sounds-letters-and-hello": 7}, "non-blank"),
    ],
)
def test_english_titles_must_cover_the_arc_exactly(root: gen.Roots, titles: dict, message: str) -> None:
    _write_yaml(root.plans / gen.TITLES_EN_FILE, {"titles": titles})
    with pytest.raises(ValueError, match=message):
        gen.generated_files(root, _arc("reading-ukrainian", "sounds-letters-and-hello"))


def test_checkpoints_and_previous_edition(root: gen.Roots) -> None:
    (root.previous_docs).mkdir(parents=True)
    (root.previous_docs / "checkpoint-one.mdx").write_text("x", encoding="utf-8")
    records = json.loads(_generated(root, _arc("checkpoint-one", "plain"))[root.data_json])["positions"]

    assert [r["is_checkpoint"] for r in records] == [True, False]
    assert [r["previous_edition_href"] for r in records] == ["/a1-v1/checkpoint-one/", None]


def _run_main(monkeypatch: pytest.MonkeyPatch, root: gen.Roots, *flags: str) -> int:
    monkeypatch.setattr(gen, "REPO_ROOT", root.repo)
    monkeypatch.setattr(gen, "load_arc", lambda level: _arc("alpha", "beta"))
    _titles(root, "alpha", "beta")
    return gen.main([LEVEL, *flags])


def test_check_passes_after_write_and_fails_on_each_stale_output(
    root: gen.Roots, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    assert _run_main(monkeypatch, root, "--check") == 1, "missing files are stale"
    assert _run_main(monkeypatch, root, "--write") == 0
    assert _run_main(monkeypatch, root, "--check") == 0

    for stale in (root.data_json, root.docs / "index.mdx", root.docs / "beta" / "index.mdx"):
        original = stale.read_bytes()
        stale.write_bytes(original + b"\n")
        capsys.readouterr()
        assert _run_main(monkeypatch, root, "--check") == 1
        assert stale.name in capsys.readouterr().err
        stale.write_bytes(original)
    assert _run_main(monkeypatch, root, "--check") == 0


def test_check_fails_when_level_status_count_differs_and_write_fixes_only_that_value(
    root: gen.Roots, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    assert _run_main(monkeypatch, root, "--write") == 0
    assert root.level_status.read_text(encoding="utf-8") == LEVEL_STATUS.replace("planned: 99", "planned: 2")
    assert _run_main(monkeypatch, root, "--check") == 0

    root.level_status.write_text(LEVEL_STATUS, encoding="utf-8")
    capsys.readouterr()
    assert _run_main(monkeypatch, root, "--check") == 1
    assert "level-status.yaml" in capsys.readouterr().err


def test_level_status_without_the_level_block_fails_loudly() -> None:
    with pytest.raises(ValueError, match="no `a1:` block"):
        gen.render_level_status("a2:\n  planned: 1\n", "a1", 55)


def test_check_fails_on_an_index_page_for_a_slug_outside_the_arc(
    root: gen.Roots, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    assert _run_main(monkeypatch, root, "--write") == 0
    (root.docs / "alpha" / "1.mdx").write_text("---\ntitle: x\n---\n", encoding="utf-8")  # lesson: not ours
    (root.docs / "not-in-arc").mkdir()
    assert _run_main(monkeypatch, root, "--check") == 0, "a directory without index.mdx is not a page"

    (root.docs / "not-in-arc" / "1.mdx").write_text("x", encoding="utf-8")
    assert _run_main(monkeypatch, root, "--check") == 0, "lesson files are ignored"

    (root.docs / "not-in-arc" / "index.mdx").write_text("x", encoding="utf-8")
    capsys.readouterr()
    assert _run_main(monkeypatch, root, "--check") == 1
    assert "not-in-arc" in capsys.readouterr().err
    assert gen.orphan_pages(root, _arc("alpha", "beta")) == [root.docs / "not-in-arc" / "index.mdx"]


def _plan_with_lessons(root: gen.Roots, slug: str, numbers: list[int]) -> None:
    _write_yaml(
        root.plans / f"{slug}.yaml",
        {"plan_schema": 2, "slug": slug, "title": "T", "lessons": [{"n": n, "title": f"Урок {n}"} for n in numbers]},
    )


@pytest.mark.parametrize("numbers", [[], [2], [1, 3], [1, 1], [2, 1], [0, 1], [1, 2, 4]])
def test_plan_lesson_numbers_must_be_exactly_one_to_n(root: gen.Roots, numbers: list[int]) -> None:
    _plan_with_lessons(root, "alpha", numbers)
    _review(root, "alpha", "plan-review.yaml")
    for n in set(numbers):
        _lesson_built(root, "alpha", n)
    with pytest.raises(ValueError, match=rf"alpha.*1\.\.N.*{re.escape(str(numbers))}"):
        _generated(root, _arc("alpha"))


def test_legacy_landing_generators_skip_arc_levels(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    from scripts import generate_landing_pages

    assert gen.ARC_LANDING_LEVELS == build_landing_pages.ARC_LANDING_LEVELS == generate_landing_pages.ARC_LANDING_LEVELS

    monkeypatch.setattr(build_landing_pages, "DOCS_DIR", tmp_path)
    build_landing_pages.main()
    assert not (tmp_path / "a1" / "index.mdx").exists()
    assert (tmp_path / "a2" / "index.mdx").exists(), "other levels are still generated"


def _retire(root, slug, routes=()):
    path = root.plans / f"{slug}.yaml"
    _write_yaml(root.plans / "_retired.yaml", {
        "retirement_schema": 1,
        "plans": [{"slug": slug, "sha256": hashlib.sha256(path.read_bytes()).hexdigest(), "old_position": 1}],
        "routes": [{"slug": route, "old_position": 3} for route in routes],
    })


def test_retired_plan_has_no_scope_title_or_review_badge(root):
    _plan(root, "alpha", 2)
    _scope(root, "alpha")
    _review(root, "alpha", "plan-review.yaml")
    _lesson_built(root, "alpha", 1)
    _retire(root, "alpha")
    record = json.loads(_generated(root, _arc("alpha"))[root.data_json])["positions"][0]
    assert record["state"] == "planned"
    assert record["scope"] is record["title_uk"] is record["lessons"] is None
    assert record["lesson_titles"] == record["built_lessons"] == []


def test_replacement_does_not_inherit_a_bare_approve(root):
    _plan(root, "alpha", 2)
    _retire(root, "alpha")
    path = root.plans / "alpha.yaml"
    path.write_bytes(path.read_bytes() + b"\n")
    _review(root, "alpha", "plan-review.yaml")
    assert _states(root, _arc("alpha")) == {"alpha": "planned"}
    # Even a syntactically complete approval with a missing pinned manifest is stale.
    _write_yaml(root.state / "alpha/plan-review.yaml", {"verdict": "APPROVE", "manifest_sha256": "a" * 64, "attempt_id": "old"})
    assert _states(root, _arc("alpha")) == {"alpha": "planned"}


def test_recorded_retired_stubs_and_orphan_exclusions_are_exact(root):
    _plan(root, "alpha", 1)
    _retire(root, "alpha", routes=("old-route",))
    arc = _arc("alpha")
    files = _generated(root, arc)
    text = files[root.docs / "old-route/index.mdx"]
    _, frontmatter, body = text.split("---\n")
    data = yaml.safe_load(frontmatter)
    assert data["arc_kind"] == "retired" and "Retired" in data["title"]
    assert "sidebar" not in data and body == ""
    assert json.loads(files[root.data_json])["retired"] == [{"slug": "old-route", "old_position": 3}]
    gen.write_files(files)
    assert gen.orphan_pages(root, arc) == []
    orphan = root.docs / "unrecorded/index.mdx"
    orphan.parent.mkdir()
    orphan.write_text("unrecorded")
    assert gen.orphan_pages(root, arc) == [orphan]
    _titles(root, "alpha", "old-route")
    with pytest.raises(ValueError, match="intersect"):
        gen.generated_files(root, _arc("alpha", "old-route"))
    with pytest.raises(ValueError, match="intersect"):
        gen.orphan_pages(root, _arc("alpha", "old-route"))


def test_landing_only_handles_plan_retired_as_absent(root):
    _plan(root, "alpha", 1)
    (root.plans / "_retired.yaml").write_text("invalid: true")
    with pytest.raises(ValueError, match="retirement_record_invalid"):
        _generated(root, _arc("alpha"))
    # A malformed ordinary replacement cannot be silently treated as absent.
    _write_yaml(root.plans / "_retired.yaml", {"retirement_schema": 1, "plans": [], "routes": []})
    (root.plans / "alpha.yaml").write_text("plan_schema: 1\n")
    with pytest.raises(ValueError, match="v1_plan"):
        _generated(root, _arc("alpha"))
