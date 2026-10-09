"""Tests for scripts/build/build_arc_landing.py (#8397 child 8)."""

from __future__ import annotations

import hashlib
import json
import re
import subprocess
import sys
import textwrap
from dataclasses import asdict
from pathlib import Path

import pytest
import yaml

from scripts.build import build_arc_landing as gen
from scripts.build import build_landing_pages
from scripts.curriculum.arc.loader import ArcPosition, load_arc
from tests.curriculum.evidence.conftest import synthetic_kaikki_side_db as synthetic_kaikki_side_db
from tests.curriculum.evidence.conftest import synthetic_sources as synthetic_sources
from tests.curriculum.evidence.conftest import synthetic_vesum as synthetic_vesum
from tests.curriculum.evidence.test_reference_sense import assert_runtime_absent, mutate_consumer, runtime_receipt_args
from tests.curriculum.evidence.test_reference_sense import authenticated_replay as authenticated_replay
from tests.curriculum.evidence.test_reference_sense import book_bound as book_bound
from tests.curriculum.evidence.test_reference_sense import bound as bound
from tests.curriculum.evidence.test_reference_sense import consumer_world as consumer_world
from tests.curriculum.evidence.test_reference_sense import reviewed_receipt_lifecycle as reviewed_receipt_lifecycle

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


def test_real_arc_generates_55_planned_positions_and_is_current() -> None:
    roots = gen.Roots(REPO_ROOT, LEVEL)
    arc = load_arc(LEVEL)
    files = gen.generated_files(roots, arc)

    assert len(arc) == 55
    assert len(files) == 55 + 3
    assert gen.stale_files(files) == [], "run python -m scripts.build.build_arc_landing a1 --write"
    records = json.loads(files[roots.data_json])["positions"]
    assert [r["position"] for r in records] == list(range(1, 56))
    # Positions climb the ladder as plans are reviewed and lessons built; every state is a ladder state.
    assert {r["state"] for r in records} <= {"planned", "plan_reviewed", "built", "reviewed"}
    assert all(r["previous_edition_href"] == f"/a1-v1/{r['slug']}/" for r in records)
    status = yaml.safe_load(roots.level_status.read_text(encoding="utf-8"))
    assert status["a1"]["planned"] == len(arc)


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


def test_reviewed_state_trusts_the_file_when_no_findings_database_exists(root: gen.Roots) -> None:
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
    with pytest.raises(ValueError, match="not valid YAML"):
        gen.generated_files(root, _arc("alpha"))


def test_plan_supplies_title_lessons_and_scope(root: gen.Roots) -> None:
    _plan(root, "alpha", 3, title="Звуки і привіт")
    _scope(root, "alpha")
    files = gen.generated_files(root, _arc("alpha", "beta"))
    alpha, beta = json.loads(files[root.data_json])["positions"]

    assert alpha["title_uk"] == "Звуки і привіт"
    assert alpha["lessons"] == 3
    assert alpha["lesson_numbers"] == [1, 2, 3]
    assert alpha["lesson_titles"] == ["Урок 1", "Урок 2", "Урок 3"]
    assert alpha["scope"] == {"letters": 13, "grammar_points": 2, "core_lemmas": 30}
    assert 'title: "Звуки і привіт · Alpha"' in files[root.docs / "alpha" / "index.mdx"]
    assert (beta["title_uk"], beta["lessons"], beta["scope"], beta["lesson_titles"]) == (None, None, None, [])
    assert beta["lesson_numbers"] == []
    assert 'title: "Beta"' in files[root.docs / "beta" / "index.mdx"]


def test_module_frontmatter_uses_bilingual_title_with_plan_and_english_fallback_without_plan(
    root: gen.Roots,
) -> None:
    _plan(root, "sounds-letters-and-hello", 1, title="Звуки і привіт")
    files = gen.generated_files(root, _arc("sounds-letters-and-hello", "reading-ukrainian"))

    planned = yaml.safe_load(files[root.docs / "sounds-letters-and-hello" / "index.mdx"].split("---\n")[1])
    unplanned = yaml.safe_load(files[root.docs / "reading-ukrainian" / "index.mdx"].split("---\n")[1])

    assert planned["title"] == "Звуки і привіт · Sounds letters and hello"
    assert unplanned["title"] == "Reading ukrainian"


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
        gen.generated_files(root, _arc("alpha"))


def test_display_job_drops_line_references_and_backticks() -> None:
    assert gen.display_job("Name common professions (`:485`) and more") == "Name common professions and more"
    assert gen.display_job("Read the text (`:549-551`).") == "Read the text."
    assert gen.display_job("Use `є` and `немає` (`:12`)") == "Use є and немає"
    assert gen.display_job("Plain text, (not a ref)") == "Plain text, (not a ref)"
    # several citations in one group (A2-B2 arc jobs), en dash, semicolon, bare backticked reference
    assert gen.display_job("Eat out; complain (:1947-1952, :1709-1710)") == "Eat out; complain"
    assert gen.display_job("Read signs (`:361`; :523–525) at the border") == "Read signs at the border"
    assert gen.display_job("Fill a form `:361` here") == "Fill a form here"
    assert gen.display_job("Meet at 10:30 (see page 4)") == "Meet at 10:30 (see page 4)"


@pytest.mark.parametrize("level", ["a1", "a2", "b1", "b2"])
def test_every_arc_job_renders_without_a_source_line_reference(level: str) -> None:
    """The landing shows ``display_job(job)``; no level's job may leak a Standard line reference into it."""
    arc = yaml.safe_load(
        (REPO_ROOT / f"curriculum/l2-uk-en/lesson-plans/{level}/_arc.yaml").read_text(encoding="utf-8")
    )
    leaking = [
        (record["position"], shown)
        for record in arc["positions"]
        if re.search(r"(?<!\d):\d+(?:[-–]\d+)?", shown := gen.display_job(record["job"]))
    ]
    assert leaking == []


def test_real_arc_jobs_carry_no_line_references_or_backticks() -> None:
    roots = gen.Roots(REPO_ROOT, LEVEL)
    data = json.loads(gen.generated_files(roots, load_arc(LEVEL))[roots.data_json])
    assert not [r["slug"] for r in data["positions"] if "`" in r["job"] or "(:" in r["job"]]


def test_legacy_landing_generators_skip_arc_levels(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    from scripts import generate_landing_pages

    assert gen.ARC_LANDING_LEVELS == build_landing_pages.ARC_LANDING_LEVELS == generate_landing_pages.ARC_LANDING_LEVELS

    monkeypatch.setattr(build_landing_pages, "DOCS_DIR", tmp_path)
    build_landing_pages.main()
    assert not (tmp_path / "a1" / "index.mdx").exists()
    assert (tmp_path / "a2" / "index.mdx").exists(), "other levels are still generated"


def test_built_state_label_is_the_accurate_ukrainian_phrase() -> None:
    chrome = (REPO_ROOT / "site/src/lib/i18n/chrome.ts").read_text(encoding="utf-8")
    assert "'arc.state.built': 'уроки підготовлено'," in chrome


@pytest.fixture
def landing_world(consumer_world, request):
    """Real complete private checker; synthetic plan/lesson reviews are engine inputs only.

    Reuse the existing Git/HMAC/reselection fixture. Add a titled plan and a
    current synthetic lesson manifest/projection, never replace the checker,
    freshness, fingerprint or module-verdict computation with an all-green stub.
    The inherited fixture substitutes pedagogical validation only.
    """
    from scripts.build.fresh import closure, plan_promote
    from scripts.build.fresh import plan_manifest as pm
    from scripts.curriculum.evidence import lock, pack, words
    from scripts.curriculum.evidence import sense_bindings as bindings
    from scripts.review import findings_db, fixloop, record

    w = consumer_world
    w.roots = gen.Roots(w.repo, LEVEL)
    w.arc = _arc("synthetic")
    private = getattr(request, "param", "private") == "private"
    plan_path = w.plans / "synthetic.yaml"
    plan = yaml.safe_load(plan_path.read_bytes())
    plan["title"] = "Synthetic module"
    plan["lessons"][0]["title"] = "Synthetic lesson"
    _write_yaml(plan_path, plan)
    _scope(w.roots, "synthetic")
    w.roots.level_status.parent.mkdir(parents=True, exist_ok=True)
    w.roots.level_status.write_text(LEVEL_STATUS)
    if not private:

        def commit_public():
            bindings.git(w.repo, "add", ".")
            bindings.git(w.repo, "commit", "-qm", "Synthetic public landing artifacts")

        w.commit_reissue = commit_public
        bindings.write(w.evidence / bindings.BINDINGS, LEVEL, {})
        word_request = w.inputs.receipt.parent / "word-request.yaml"
        requested = yaml.safe_load(word_request.read_bytes())
        requested["words"][0]["want"] = "W-001"
        _write_yaml(word_request, requested)
        words.build_words(
            LEVEL,
            word_request,
            evidence_dir=w.evidence,
            sources_instance=w.api,
            mcp_commit="a" * 40,
        )
        pack.build_pack(
            LEVEL,
            "synthetic",
            w.inputs.receipt.parent / "pack-request.yaml",
            evidence_dir=w.evidence,
            sources_instance=w.api,
            offline=True,
        )
    report_path = w.directory / pm.VALIDATE_REPORT_NAME
    report = json.loads(report_path.read_bytes())
    report["inputs"] = {path: hashlib.sha256((w.repo / path).read_bytes()).hexdigest() for path in report["inputs"]}
    report_path.write_bytes(pm.json_bytes(report))
    w.commit_reissue()
    runtime = w.runtime if private else {"sources_instance": w.api}
    w.manifest, w.digest = pm.write_plan_manifest(LEVEL, "synthetic", repo_root=w.repo, **runtime)
    w.commit_reissue()
    # The existing return builder closes over the old manifest; update its
    # synthetic return and terminal hash to the newly generated manifest.
    w.review, w.record_kwargs = w.make_return()
    review = yaml.safe_load(w.review.read_bytes())
    review["attempt"]["manifest_sha256"] = w.digest
    data = yaml.safe_dump(review).encode()
    w.review.write_bytes(data)
    task_path = w.record_kwargs["tasks_dir"] / "accepted.json"
    task = json.loads(task_path.read_bytes())
    task["review_attempt"]["manifest_sha256"] = w.digest
    Path(task["result_file"]).write_bytes(data)
    task["result_sha256"] = hashlib.sha256(data).hexdigest()
    task_path.write_text(json.dumps(task))
    assert record.record_return(w.review, **w.record_kwargs, **runtime).accepted
    w.commit_reissue()
    assert not plan_promote.promote_plan(LEVEL, "synthetic", repo_root=w.repo, **runtime)["already_promoted"]
    w.commit_reissue()
    _lesson_built(w.roots, "synthetic", 1)
    page = w.roots.docs / "synthetic/1.mdx"
    lesson = {
        "kind": "lesson",
        "level": LEVEL,
        "slug": "synthetic",
        "lesson": 1,
        "inputs": {
            "lesson": {
                "path": page.relative_to(w.repo).as_posix(),
                "sha256": hashlib.sha256(page.read_bytes()).hexdigest(),
            }
        },
    }
    content = lock.yaml_bytes(lesson)
    digest = hashlib.sha256(content).hexdigest()
    history = w.directory / f"manifests/lesson-1/{digest}.yaml"
    history.parent.mkdir(parents=True)
    history.write_bytes(content)
    (w.directory / "lesson-1.manifest.yaml").write_bytes(content)
    (w.directory / "lesson-1.manifest.sha256").write_text(digest + "\n")
    conn = findings_db.connect(w.db)
    try:
        # A synthetic accepted review row and its exact projection are inputs
        # to the real complete checker, not a language/reviewer approval claim.
        row = dict(findings_db.latest_accepted(conn, LEVEL, "synthetic", "plan", None))
        row.update(
            kind="lesson", lesson_n=1, review_id="synthetic-lesson", attempt_id="lesson-1", manifest_sha256=digest
        )
        findings_db.insert_attempt(conn, row)
        _write_yaml(
            w.directory / "lesson-1.verdict.yaml",
            fixloop.projection_document(findings_db.latest_accepted(conn, LEVEL, "synthetic", "lesson", 1)),
        )
        closure.compute_closure(
            LEVEL, "synthetic", [{"n": 1}], repo_root=w.repo, state_dir=w.directory, site_dir=page.parent
        )
        w.commit_reissue()
        w.params = findings_db.load_parameters()
        w.verdict, w.verdict_path = fixloop.compute_and_write_module_verdict(
            conn, LEVEL, "synthetic", root=w.repo, params=w.params, **runtime
        )
        assert w.verdict["verdict"] == "APPROVE", w.verdict["holds"]
        assert w.verdict["holds"] == []
        w.commit_reissue()
        assert fixloop.module_verdict_problems(conn, LEVEL, "synthetic", root=w.repo, params=w.params, **runtime) == []
    finally:
        conn.close()
    w.runtime = runtime
    w.private = private
    return w


def _landing_routes(w, runtime):
    plan = gen._load_module_plan(w.roots, "synthetic")
    return (
        lambda: gen._module_verdict_reviewed(w.roots, "synthetic", **runtime),
        lambda: gen.position_state(w.roots, "synthetic", plan, [1], **runtime),
        lambda: gen.build_record(w.roots, w.arc[0], **runtime),
        lambda: gen.generated_files(w.roots, w.arc, **runtime),
    )


def _landing_snapshot(w):
    """Tracked projections and outputs plus findings rows; no runtime input serialization."""
    from scripts.review import findings_db

    files = {
        p.relative_to(w.repo).as_posix(): p.read_bytes()
        for folder in (w.directory, w.roots.docs, w.repo / "site/src/data")
        for p in folder.rglob("*")
        if p.is_file()
    }
    conn = findings_db.connect(w.db)
    try:
        rows = {
            table: [dict(r) for r in conn.execute(f"SELECT * FROM {table}")]
            for table in ("attempts", "findings", "settle_items")
        }
    finally:
        conn.close()
    return files, rows


@pytest.mark.parametrize("landing_world", ["private", "public"], indirect=True)
def test_complete_checker_landing_positive_and_cli_privacy(landing_world, monkeypatch, capsys):
    from scripts.curriculum.evidence import sense_cli
    from scripts.review import fixloop

    w = landing_world
    original = fixloop.module_verdict_problems
    seen = []

    def capture(*args, **kwargs):
        seen.append((kwargs["receipt_inputs"], kwargs["sources_instance"]))
        return original(*args, **kwargs)

    monkeypatch.setattr(fixloop, "module_verdict_problems", capture)
    reviewed, state, record, files = [call() for call in _landing_routes(w, w.runtime)]
    assert reviewed is True and state == "reviewed" and record["state"] == "reviewed"
    assert json.loads(files[w.roots.data_json])["positions"][0]["state"] == "reviewed"
    expected = w.inputs if w.private else None
    assert seen == [(expected, w.api)] * 4
    assert_runtime_absent(w.inputs, record, list(files.values()), w.verdict, w.manifest)
    gen.write_files(files)  # Synthetic repository only.
    monkeypatch.setattr(gen, "REPO_ROOT", w.repo)
    monkeypatch.setattr(gen, "load_arc", lambda level: w.arc)
    # Commit synthetic outputs before exact-head receipt authentication.
    w.commit_reissue()
    before = _landing_snapshot(w)
    flags = runtime_receipt_args(w.inputs) if w.private else []
    assert gen.main([LEVEL, "--check", *flags]) == 0
    output = capsys.readouterr()
    assert "generated files are current" in output.out
    assert_runtime_absent(w.inputs, output.out, output.err)
    assert seen[-1][0] == expected and seen[-1][1] is None
    assert _landing_snapshot(w) == before
    if not w.private:
        monkeypatch.setattr(
            sense_cli, "verify_local_receipt", lambda *a, **kw: pytest.fail("public proof needs no receipt")
        )
        assert gen._module_verdict_reviewed(w.roots, "synthetic", sources_instance=w.api)


@pytest.mark.parametrize(
    "change",
    [
        "missing_runtime",
        "head",
        "tampered_receipt",
        "wrong_identity",
        "bindings_drift",
        "cached_success",
        "private_input",
        "partial_runtime",
        "unsafe_source_error",
    ],
)
def test_complete_checker_landing_refusals_do_not_write(landing_world, change, monkeypatch, capsys):
    from dataclasses import replace

    w = landing_world
    if change == "partial_runtime":
        inputs = replace(w.inputs, receipt=None)
    elif change == "unsafe_source_error":
        inputs = w.inputs

        def unavailable(*args, **kwargs):
            raise ValueError(f"synthetic private body {w.inputs.private_input} {w.inputs.key_file}")

        monkeypatch.setattr(w.api, "gloss_rows", unavailable)
    else:
        inputs = mutate_consumer(w, change)
    runtime = {"receipt_inputs": inputs, "sources_instance": w.api}
    before = _landing_snapshot(w)
    for call in _landing_routes(w, runtime):
        with pytest.raises(ValueError, match="APPROVE but is stale") as caught:
            call()
        assert_runtime_absent(w.inputs, str(caught.value))
        assert "synthetic private body" not in str(caught.value)
        assert _landing_snapshot(w) == before
    monkeypatch.setattr(gen, "REPO_ROOT", w.repo)
    monkeypatch.setattr(gen, "load_arc", lambda level: w.arc)
    flags = runtime_receipt_args(inputs) if inputs is not None else []
    # Both CLI modes compute admission before writing any generated output.
    for mode in ("--check", "--write"):
        with pytest.raises(ValueError, match="APPROVE but is stale") as caught:
            gen.main([LEVEL, mode, *flags])
        output = capsys.readouterr()
        assert_runtime_absent(w.inputs, str(caught.value), output.out, output.err)
        assert "synthetic private body" not in str(caught.value) + output.out + output.err
        assert _landing_snapshot(w) == before


def test_authentic_landing_inputs_preserve_other_holds(landing_world):
    from scripts.review import findings_db, fixloop

    w = landing_world
    conn = findings_db.connect(w.db)
    try:
        conn.execute("UPDATE attempts SET verdict='REVISE' WHERE kind='lesson'")
        fresh = fixloop.compute_module_verdict(conn, LEVEL, "synthetic", root=w.repo, params=w.params, **w.runtime)
        assert fresh["verdict"] != "APPROVE"
        assert "verdict_projection_stale" in {hold["code"] for hold in fresh["holds"]}
        assert "plan_not_promoted" not in {hold["code"] for hold in fresh["holds"]}
    finally:
        conn.close()
    before = _landing_snapshot(w)
    with pytest.raises(ValueError, match="APPROVE but is stale"):
        gen.generated_files(w.roots, w.arc, **w.runtime)
    assert _landing_snapshot(w) == before


@pytest.mark.parametrize("verdict", [None, "HOLD", "REVISE", "APPROVE"])
def test_no_database_projection_does_not_verify_runtime(root, verdict, monkeypatch):
    from scripts.curriculum.evidence import sense_cli
    from scripts.review import fixloop

    _plan(root, "synthetic", 1)
    _review(root, "synthetic", "plan-review.yaml")
    _lesson_built(root, "synthetic", 1)
    if verdict is not None:
        _review(root, "synthetic", "module-verdict.yaml", verdict)
    monkeypatch.setattr(fixloop, "module_verdict_problems", lambda *a, **kw: pytest.fail("no database recomputation"))
    monkeypatch.setattr(
        sense_cli, "verify_local_receipt", lambda *a, **kw: pytest.fail("no fresh private certification")
    )
    inputs = sense_cli.LocalReceiptInputs(root.repo / "unavailable-private", key_id="unavailable")
    state = gen.build_record(root, _arc("synthetic")[0], receipt_inputs=inputs, sources_instance=object())["state"]
    assert state == ("reviewed" if verdict == "APPROVE" else "built")
    assert gen.generated_files(root, _arc("synthetic"), receipt_inputs=inputs, sources_instance=object()) == (
        gen.generated_files(root, _arc("synthetic"))
    )


def test_cli_help_and_partial_receipt_forwarding(root, monkeypatch, capsys):
    from scripts.curriculum.evidence import sense_cli

    with pytest.raises(SystemExit) as caught:
        gen.main(["--help"])
    assert caught.value.code == 0
    help_text = capsys.readouterr().out
    for option in ("--private-input", "--key-file", "--key-id", "--receipt", "--receipt-base"):
        assert option in help_text
    assert "Outputs:" in help_text and "Exit codes:" in help_text and "Related:" in help_text
    original = gen.generated_files
    seen = []

    def capture(*args, **kwargs):
        seen.append(kwargs["receipt_inputs"])
        return original(*args, **kwargs)

    monkeypatch.setattr(gen, "generated_files", capture)
    assert _run_main(monkeypatch, root, "--check", "--key-id", "partial") == 1
    assert seen[-1] == sense_cli.LocalReceiptInputs(key_id="partial")
    assert _run_main(monkeypatch, root, "--check", "--receipt-base", "explicit-base") == 1
    assert seen[-1] == sense_cli.LocalReceiptInputs(base="explicit-base")


def test_import_keeps_minimal_ci_dependencies():
    result = subprocess.run(
        [
            sys.executable,
            "-c",
            "import sys; from scripts.build import build_arc_landing; "
            "assert 'scripts.curriculum.evidence.sense_cli' not in sys.modules; "
            "assert 'scripts.review.fixloop' not in sys.modules",
        ],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert result.returncode == 0, result.stderr


@pytest.mark.parametrize("mode", ["--help", "--check", "--write"])
def test_cli_keeps_minimal_dependencies(root, mode):
    """Exercise actual CLI startup in a fresh process with heavy imports refused."""
    arc = _arc("synthetic")
    _plan(root, "synthetic", 1)
    _review(root, "synthetic", "plan-review.yaml")
    _lesson_built(root, "synthetic", 1)
    _review(root, "synthetic", "module-verdict.yaml")
    files = gen.generated_files(root, arc)
    assert json.loads(files[root.data_json])["positions"][0]["state"] == "reviewed"
    if mode == "--check":
        gen.write_files(files)
    script = textwrap.dedent("""\
        import importlib.abc
        import json
        import sys
        from pathlib import Path

        blocked = (
            'requests',
            'scripts.curriculum.evidence.sense_cli',
            'scripts.curriculum.evidence.sources',
            'scripts.review.fixloop',
        )
        class MinimalDependencies(importlib.abc.MetaPathFinder):
            def find_spec(self, fullname, path=None, target=None):
                if any(fullname == name or fullname.startswith(name + '.') for name in blocked):
                    raise ModuleNotFoundError('Heavy dependency unavailable: ' + fullname)

        sys.meta_path.insert(0, MinimalDependencies())
        from scripts.build import build_arc_landing as gen
        mode, repo, positions = sys.argv[1:]
        gen.REPO_ROOT = Path(repo)
        gen.load_arc = lambda level: [gen.ArcPosition(**p) for p in json.loads(positions)]
        try:
            result = gen.main(['--help'] if mode == '--help' else ['a1', mode])
        except SystemExit as error:
            assert mode == '--help' and error.code == 0
            result = error.code
        assert result == 0
        assert not any(name in sys.modules for name in blocked)
        if mode != '--help':
            assert gen.main(['a1', '--check']) == 0
        """)
    result = subprocess.run(
        [sys.executable, "-c", script, mode, str(root.repo), json.dumps([asdict(p) for p in arc])],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    if mode == "--help":
        assert "--private-input" in result.stdout and "Outputs:" in result.stdout
        assert not root.data_json.exists()
    else:
        assert not gen.stale_files(files)


@pytest.mark.parametrize(
    "flags",
    [
        [],
        ["--private-input", "synthetic-input"],
        ["--key-file", "synthetic-key"],
        ["--key-id", "synthetic-id"],
        ["--receipt", "synthetic-receipt"],
        ["--receipt-base", "explicit-base"],
        ["--receipt-base", "origin/main"],
        ["--key-id", ""],
        [
            "--private-input", "synthetic-input", "--key-file", "synthetic-key",
            "--key-id", "synthetic-id", "--receipt", "synthetic-receipt", "--receipt-base", "explicit-base",
        ],
    ],
)
def test_cli_receipt_parsing_matches_existing_contract(root, monkeypatch, flags):
    import argparse

    from scripts.curriculum.evidence import sense_cli

    parser = argparse.ArgumentParser()
    sense_cli.add_receipt_arguments(parser)
    expected = sense_cli.receipt_inputs(parser.parse_args(flags))
    original = gen.generated_files
    seen = []

    def capture(*args, **kwargs):
        seen.append(kwargs["receipt_inputs"])
        return original(*args, **kwargs)

    monkeypatch.setattr(gen, "generated_files", capture)
    assert _run_main(monkeypatch, root, "--check", *flags) == 1
    assert seen == [expected]
