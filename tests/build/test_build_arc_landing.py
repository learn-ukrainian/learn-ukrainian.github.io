"""Tests for scripts/build/build_arc_landing.py (#8397 child 8)."""

from __future__ import annotations

import json
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


def _states(root: gen.Roots, arc: list[ArcPosition]) -> dict[str, str]:
    data = json.loads(gen.generated_files(root, arc)[root.data_json])
    return {record["slug"]: record["state"] for record in data["positions"]}


@pytest.fixture
def root(tmp_path: Path) -> gen.Roots:
    return gen.Roots(tmp_path, LEVEL)


def test_real_arc_generates_55_planned_positions_and_is_current() -> None:
    roots = gen.Roots(REPO_ROOT, LEVEL)
    arc = load_arc(LEVEL)
    files = gen.generated_files(roots, arc)

    assert len(arc) == 55
    assert len(files) == 55 + 2
    assert gen.stale_files(files) == [], "run python -m scripts.build.build_arc_landing a1 --write"
    records = json.loads(files[roots.data_json])["positions"]
    assert [r["position"] for r in records] == list(range(1, 56))
    assert {r["state"] for r in records} == {"planned"}
    assert all(r["previous_edition_href"] == f"/a1-v1/{r['slug']}/" for r in records)


def test_generation_is_byte_stable(root: gen.Roots) -> None:
    arc = _arc("alpha", "beta")
    _plan(root, "alpha", 2)
    assert gen.generated_files(root, arc) == gen.generated_files(root, arc)


def test_states_climb_one_predicate_at_a_time(root: gen.Roots) -> None:
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


def test_a_missing_file_never_yields_a_higher_state(root: gen.Roots) -> None:
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


def test_missing_state_directory_is_planned_not_an_error(root: gen.Roots) -> None:
    _plan(root, "alpha", 1)
    assert not root.state.exists()
    assert _states(root, _arc("alpha")) == {"alpha": "planned"}


def test_malformed_state_file_fails_loudly(root: gen.Roots) -> None:
    _plan(root, "alpha", 1)
    (root.state / "alpha").mkdir(parents=True)
    (root.state / "alpha" / "plan-review.yaml").write_text("verdict: [unclosed", encoding="utf-8")
    with pytest.raises(ValueError, match="not valid YAML"):
        gen.generated_files(root, _arc("alpha"))


def test_plan_supplies_title_lessons_and_scope(root: gen.Roots) -> None:
    _plan(root, "alpha", 3, title="Звуки і привіт")
    _scope(root, "alpha")
    files = gen.generated_files(root, _arc("alpha", "beta"))
    alpha, beta = json.loads(files[root.data_json])["positions"]

    assert alpha["title_uk"] == "Звуки і привіт"
    assert alpha["lessons"] == 3
    assert alpha["lesson_titles"] == ["Урок 1", "Урок 2", "Урок 3"]
    assert alpha["scope"] == {"letters": 13, "grammar_points": 2, "core_lemmas": 30}
    assert 'title: "Звуки і привіт"' in files[root.docs / "alpha" / "index.mdx"]
    assert (beta["title_uk"], beta["lessons"], beta["scope"], beta["lesson_titles"]) == (None, None, None, [])
    assert 'title: "Beta"' in files[root.docs / "beta" / "index.mdx"]


def test_frontmatter_carries_arc_keys_and_an_empty_body(root: gen.Roots) -> None:
    files = gen.generated_files(root, _arc("sounds-letters-and-hello"))
    landing = files[root.docs / "index.mdx"]
    module = files[root.docs / "sounds-letters-and-hello" / "index.mdx"]

    for text, kind in ((landing, "landing"), (module, "module")):
        _, frontmatter, body = text.split("---\n", 2)
        data = yaml.safe_load(frontmatter)
        assert data["arc_kind"] == kind and data["arc_level"] == LEVEL and data["title"]
        assert body == ""
    assert yaml.safe_load(module.split("---\n")[1])["arc_slug"] == "sounds-letters-and-hello"
    assert gen.humanise_slug("sounds-letters-and-hello") == "Sounds letters and hello"


def test_checkpoints_and_previous_edition(root: gen.Roots) -> None:
    (root.previous_docs).mkdir(parents=True)
    (root.previous_docs / "checkpoint-one.mdx").write_text("x", encoding="utf-8")
    records = json.loads(gen.generated_files(root, _arc("checkpoint-one", "plain"))[root.data_json])["positions"]

    assert [r["is_checkpoint"] for r in records] == [True, False]
    assert [r["previous_edition_href"] for r in records] == ["/a1-v1/checkpoint-one/", None]


def _run_main(monkeypatch: pytest.MonkeyPatch, root: gen.Roots, *flags: str) -> int:
    monkeypatch.setattr(gen, "REPO_ROOT", root.repo)
    monkeypatch.setattr(gen, "load_arc", lambda level: _arc("alpha", "beta"))
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


def test_a1_level_status_count_equals_the_arc() -> None:
    status = yaml.safe_load((REPO_ROOT / "docs/l2-uk-en/level-status.yaml").read_text(encoding="utf-8"))
    assert status["a1"]["planned"] == len(load_arc(LEVEL))


def test_legacy_landing_generators_skip_arc_levels(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    from scripts import generate_landing_pages

    assert gen.ARC_LANDING_LEVELS == build_landing_pages.ARC_LANDING_LEVELS == generate_landing_pages.ARC_LANDING_LEVELS

    monkeypatch.setattr(build_landing_pages, "DOCS_DIR", tmp_path)
    build_landing_pages.main()
    assert not (tmp_path / "a1" / "index.mdx").exists()
    assert (tmp_path / "a2" / "index.mdx").exists(), "other levels are still generated"
