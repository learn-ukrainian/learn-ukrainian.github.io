"""Tests for verify_shippable — the Definition-of-Done predicate (#3138).

The pipeline functions are heavy; these tests monkeypatch them on the source
module (verify() imports them lazily at call time) to exercise the verdict logic
deterministically without data/, MCP, or Node.
"""

from __future__ import annotations

import pytest
import yaml

import scripts.build.linear_pipeline as lp
import scripts.build.verify_shippable as vs
from scripts.build import promote_quality_gate as pqg
from scripts.generate_mdx.core import generate_mdx

pytestmark = pytest.mark.reads_content


def _mk(tmp_path):
    md = tmp_path / "mod"
    md.mkdir()
    plan = tmp_path / "plan.yaml"
    plan.write_text("module: x\n", encoding="utf-8")
    return md, plan


def test_shippable_when_all_green(tmp_path, monkeypatch):
    md, plan = _mk(tmp_path)
    monkeypatch.setattr(lp, "run_python_qg", lambda m, p, **kw: {"gates": {"passed": True}})
    monkeypatch.setattr(lp, "assemble_mdx", lambda m, o, p: "MDXBODY")
    monkeypatch.setattr(lp, "run_mdx_render_gate", lambda t: {"passed": True, "message": "ok", "failures": []})
    monkeypatch.setattr(
        pqg,
        "verify",
        lambda *args, **kwargs: {
            "applicable": True,
            "passed": True,
            "reason": "ok",
            "failures": [],
        },
    )
    rep = vs.verify("folk", "x", module_dir=md, plan_path=plan)
    assert rep["shippable"] is True
    steps = {s["step"]: s["passed"] for s in rep["steps"]}
    assert steps["python_qg"] and steps["assemble_mdx"] and steps["mdx_render"]
    assert steps["promote_quality"]
    assert rep["corpus_hammer_required"] is True


def test_render_runs_even_when_python_qg_red(tmp_path, monkeypatch):
    """E's core guarantee: the render gate runs even when python_qg fails."""
    md, plan = _mk(tmp_path)
    monkeypatch.setattr(
        lp,
        "run_python_qg",
        lambda m, p, **kw: {"gates": {"passed": False, "vesum_verified": {"passed": False}}},
    )
    monkeypatch.setattr(lp, "assemble_mdx", lambda m, o, p: "MDXBODY")
    seen = {}

    def render(t):
        seen["ran"] = True
        return {"passed": True, "message": "ok", "failures": []}

    monkeypatch.setattr(lp, "run_mdx_render_gate", render)
    rep = vs.verify("folk", "x", module_dir=md, plan_path=plan)
    assert seen.get("ran") is True  # render evaluated despite python_qg red
    assert rep["shippable"] is False  # but a red gate still blocks ship
    steps = {s["step"]: s["passed"] for s in rep["steps"]}
    assert steps["python_qg"] is False and steps["mdx_render"] is True


def test_render_runs_when_python_qg_raises(tmp_path, monkeypatch):
    """A python_qg CRASH (not just a red gate) must still reach the render check."""
    md, plan = _mk(tmp_path)

    def boom(m, p, **kw):
        raise RuntimeError("vesum db missing")

    monkeypatch.setattr(lp, "run_python_qg", boom)
    monkeypatch.setattr(lp, "assemble_mdx", lambda m, o, p: "MDXBODY")
    seen = {}

    def render(t):
        seen["ran"] = True
        return {"passed": True, "message": "ok", "failures": []}

    monkeypatch.setattr(lp, "run_mdx_render_gate", render)
    rep = vs.verify("folk", "x", module_dir=md, plan_path=plan)
    assert seen.get("ran") is True  # render ran despite python_qg crash
    assert rep["shippable"] is False  # but the crash still blocks ship
    steps = {s["step"]: s["passed"] for s in rep["steps"]}
    assert steps["python_qg"] is False and steps["mdx_render"] is True


def test_render_failure_blocks_ship(tmp_path, monkeypatch):
    md, plan = _mk(tmp_path)
    monkeypatch.setattr(lp, "run_python_qg", lambda m, p, **kw: {"gates": {"passed": True}})
    monkeypatch.setattr(lp, "assemble_mdx", lambda m, o, p: "MDXBODY")
    monkeypatch.setattr(
        lp,
        "run_mdx_render_gate",
        lambda t: {"passed": False, "message": "boom", "failures": [{"snippet": "x", "error": "SyntaxError"}]},
    )
    rep = vs.verify("folk", "x", module_dir=md, plan_path=plan)
    assert rep["shippable"] is False


def test_assemble_crash_blocks_ship(tmp_path, monkeypatch):
    md, plan = _mk(tmp_path)
    monkeypatch.setattr(lp, "run_python_qg", lambda m, p, **kw: {"gates": {"passed": True}})

    def boom(m, o, p):
        raise RuntimeError("assembler exploded")

    monkeypatch.setattr(lp, "assemble_mdx", boom)
    rep = vs.verify("folk", "x", module_dir=md, plan_path=plan)
    assert rep["shippable"] is False
    assert any(s["step"] == "assemble_mdx" and s["passed"] is False for s in rep["steps"])


def test_skipped_render_not_shippable(tmp_path, monkeypatch):
    """Node-absent (mdx_render=None) must NOT certify shippable — no render evidence."""
    md, plan = _mk(tmp_path)
    monkeypatch.setattr(lp, "run_python_qg", lambda m, p, **kw: {"gates": {"passed": True}})
    monkeypatch.setattr(lp, "assemble_mdx", lambda m, o, p: "MDXBODY")
    monkeypatch.setattr(
        lp,
        "run_mdx_render_gate",
        lambda t: {"passed": None, "skipped": True, "message": "node unavailable", "failures": []},
    )
    rep = vs.verify("folk", "x", module_dir=md, plan_path=plan)
    assert rep["shippable"] is False
    assert rep["render_fully_validated"] is False


def test_missing_inputs_not_shippable(tmp_path):
    rep = vs.verify("folk", "x", module_dir=tmp_path / "nope", plan_path=tmp_path / "nope.yaml")
    assert rep["shippable"] is False


def test_wikipedia_host_matching_normalizes_case_and_port(monkeypatch):
    """A missing wiki article must be caught regardless of host case/port, instead
    of falling through to a curl 200 on the missing-page stub (Codex hole #2)."""
    seen = []

    def fake_curl(url, *, status_only):
        seen.append(url)
        if "api.php" in url:
            # MediaWiki API reports a MISSING article
            return 200, '{"query": {"pages": {"-1": {"missing": ""}}}}'
        return 200, ""  # a missing-page /wiki/ GET would still be HTTP 200

    monkeypatch.setattr(vs, "_curl", fake_curl)
    for url in (
        "https://UK.WIKIPEDIA.ORG/wiki/Definitely_missing_title",
        "https://uk.wikipedia.org:443/wiki/Definitely_missing_title",
        # non-/wiki/ article form must ALSO route to the API (Codex hole #3)
        "https://uk.wikipedia.org/w/index.php?title=Definitely_missing_title",
    ):
        vs._url_live_cache.clear()
        assert vs._url_is_live(url) is False
    # the API path (not a bare curl GET) decided it — the hole would have skipped it
    assert any("api.php" in u for u in seen)


def test_wikipedia_url_without_title_fails_closed(monkeypatch):
    """A wikipedia-host URL with no extractable article title must fail closed,
    not fall through to a curl 200 (Codex hole #3)."""
    curled = []

    def fake_curl(url, *, status_only):
        curled.append(url)
        return 200, ""  # a bare wikipedia GET would be 200 -> the hole if reached

    monkeypatch.setattr(vs, "_curl", fake_curl)
    vs._url_live_cache.clear()
    # /w/index.php?oldid=... has no `title` -> not confirmable -> fail closed,
    # and must NOT be probed with a bare liveness GET.
    assert vs._url_is_live("https://uk.wikipedia.org/w/index.php?oldid=12345") is False
    assert curled == []  # never fell through to a generic curl on a wikipedia host


def test_fresh_path_resolution(tmp_path):
    """Test path resolution for --fresh vs default legacy paths."""
    mod_dir = vs._fresh_module_dir("a1", "my-module", repo_root=tmp_path)
    plan_path = vs._fresh_plan_path("a1", "my-module", repo_root=tmp_path)

    assert mod_dir == tmp_path / "site" / "src" / "content" / "docs" / "a1" / "my-module"
    assert plan_path == tmp_path / "curriculum" / "l2-uk-en" / "lesson-plans" / "a1" / "my-module.yaml"

    legacy_mod = vs._default_module_dir("a1", "my-module", repo_root=tmp_path)
    # Legacy module is in curriculum/l2-uk-en/a1/my-module
    assert legacy_mod == tmp_path / "curriculum" / "l2-uk-en" / "a1" / "my-module"


def _mk_fresh(tmp_path, *, ids=(1, 2), level="a1"):
    site_mod = tmp_path / "site" / "src" / "content" / "docs" / level / "greetings"
    site_mod.mkdir(parents=True)
    for n in ids:
        (site_mod / f"{n}.mdx").write_text(
            generate_mdx(
                md_content=f"# Lesson {n}\n", module_num=n, meta_data={"title": f"Lesson {n}"}, level=level, fresh=True
            ),
            encoding="utf-8",
        )
    plan_dir = tmp_path / "curriculum" / "l2-uk-en" / "lesson-plans" / level
    plan_dir.mkdir(parents=True)
    plan_file = plan_dir / "greetings.yaml"
    plan_file.write_text(
        yaml.safe_dump({"plan_schema": 2, "slug": "greetings", "lessons": [{"n": n} for n in ids]}), encoding="utf-8"
    )
    return site_mod, plan_file


@pytest.mark.parametrize("level,ids", [("a1", (1, 2)), ("a2", (1,)), ("a2", (9,)), ("b1", (1,))])
def test_verify_fresh_shippable_when_green(tmp_path, monkeypatch, level, ids):
    """Test verify with fresh=True validates mdx files in site/src/content/docs."""
    site_mod, plan_file = _mk_fresh(tmp_path, ids=ids, level=level)
    (site_mod / "index.mdx").write_text("# Landing\n", encoding="utf-8")
    rendered = []

    def render(text):
        rendered.append(text)
        return {"passed": True, "message": "ok", "failures": []}

    monkeypatch.setattr(lp, "run_mdx_render_gate", render)

    rep = vs.verify(
        level,
        "greetings",
        module_dir=site_mod,
        plan_path=plan_file,
        fresh=True,
    )
    assert rep["shippable"] is True
    steps = {s["step"]: s["passed"] for s in rep["steps"]}
    assert steps["mdx_render"] is True
    assert steps["fresh_lessons"] is True
    assert all(steps[f"fresh_tabs.{n}"] for n in ids)
    assert len(rendered) == len(ids) + 1


def test_verify_fresh_with_astro_build(tmp_path, monkeypatch):
    """Test verify with fresh=True and astro_build=True sets render_fully_validated."""
    site_mod, plan_file = _mk_fresh(tmp_path)

    monkeypatch.setattr(lp, "run_mdx_render_gate", lambda t: {"passed": True, "message": "ok", "failures": []})
    monkeypatch.setattr(vs, "PROJECT_ROOT", tmp_path)
    log_dir = tmp_path / "batch_state" / "verify_shippable"
    assert not log_dir.exists()

    def astro(log_path):
        log_path.write_text("fixture build green\n", encoding="utf-8")
        return True

    monkeypatch.setattr(vs, "_astro_build", astro)

    rep = vs.verify(
        "a1",
        "greetings",
        module_dir=site_mod,
        plan_path=plan_file,
        fresh=True,
        astro_build=True,
    )
    assert rep["shippable"] is True
    assert rep["render_fully_validated"] is True
    steps = {s["step"]: s["passed"] for s in rep["steps"]}
    assert steps["astro_build"] is True
    assert (log_dir / "a1-greetings.astro-build.log").read_text() == "fixture build green\n"


def test_verify_fresh_fails_when_mdx_render_red(tmp_path, monkeypatch):
    """Test verify with fresh=True reports not shippable when render gate fails."""
    site_mod, plan_file = _mk_fresh(tmp_path)

    monkeypatch.setattr(
        lp,
        "run_mdx_render_gate",
        lambda t: {"passed": False, "message": "fail", "failures": [{"snippet": "x", "error": "SyntaxError"}]},
    )

    rep = vs.verify(
        "a1",
        "greetings",
        module_dir=site_mod,
        plan_path=plan_file,
        fresh=True,
    )
    assert rep["shippable"] is False
    steps = {s["step"]: s["passed"] for s in rep["steps"]}
    assert steps["mdx_render"] is False


@pytest.mark.parametrize("missing", [(2,), (2, 3)])
def test_verify_fresh_missing_planned_lessons(tmp_path, monkeypatch, missing):
    site_mod, plan_file = _mk_fresh(tmp_path, ids=(1, 2, 3))
    for n in missing:
        (site_mod / f"{n}.mdx").rename(site_mod / f"lesson-{n}.mdx")
    monkeypatch.setattr(lp, "run_mdx_render_gate", lambda t: {"passed": True})
    rep = vs.verify("a1", "greetings", module_dir=site_mod, plan_path=plan_file, fresh=True)
    assert rep["shippable"] is False
    step = next(s for s in rep["steps"] if s["step"] == "fresh_lessons")
    assert step["reason"] == "missing_planned_lessons"
    assert step["planned_count"] == 3
    assert step["missing_count"] == len(missing)
    assert step["missing_lesson_ids"] == list(missing)
    assert step["detail"] == f"missing {len(missing)} of 3 planned lessons: ids {list(missing)}"


@pytest.mark.parametrize("through_lesson", [None, 1])
def test_verify_fresh_landing_only(tmp_path, monkeypatch, through_lesson):
    site_mod, plan_file = _mk_fresh(tmp_path, ids=(1,))
    (site_mod / "1.mdx").rename(site_mod / "index.mdx")
    monkeypatch.setattr(lp, "run_mdx_render_gate", lambda t: {"passed": True})
    rep = vs.verify(
        "a1", "greetings", module_dir=site_mod, plan_path=plan_file, fresh=True, through_lesson=through_lesson
    )
    assert rep["shippable"] is False
    by_step = {s["step"]: s for s in rep["steps"]}
    assert by_step["fresh_lessons"]["reason"] == "missing_planned_lessons"
    assert by_step["fresh_lessons"]["missing_lesson_ids"] == [1]
    assert by_step["fresh_landing"]["reason"] == "landing_only"
    assert by_step["mdx_render"]["passed"] is True


@pytest.mark.parametrize(
    "uk,en", [("Урок", "Lesson"), ("Словник", "Vocabulary"), ("Вправи", "Activities"), ("Ресурси", "Resources")]
)
def test_verify_fresh_missing_lesson_tab(tmp_path, monkeypatch, uk, en):
    site_mod, plan_file = _mk_fresh(tmp_path)
    page = site_mod / "2.mdx"
    page.write_text(page.read_text().replace(f'label="{uk} — {en}"', 'label="Other"'), encoding="utf-8")
    monkeypatch.setattr(lp, "run_mdx_render_gate", lambda t: {"passed": True})
    rep = vs.verify("a1", "greetings", module_dir=site_mod, plan_path=plan_file, fresh=True)
    assert rep["shippable"] is False
    by_step = {s["step"]: s for s in rep["steps"]}
    assert by_step["fresh_tabs.1"]["passed"] is True
    assert by_step["fresh_tabs.2"]["reason"] == "missing_lesson_tabs"
    assert by_step["fresh_tabs.2"]["lesson_id"] == 2
    assert by_step["fresh_tabs.2"]["missing_tabs"] == [uk]


@pytest.mark.parametrize("wrapper", ["<!-- {} -->", "{{/* {} */}}", "```mdx\n{}\n```", "~~~mdx\n{}\n~~~"])
def test_verify_fresh_tab_examples_do_not_count(tmp_path, monkeypatch, wrapper):
    site_mod, plan_file = _mk_fresh(tmp_path, ids=(1,))
    page = site_mod / "1.mdx"
    tab_markup = page.read_text().split('<Tabs syncKey="module-tab">', 1)[1].split("</Tabs>", 1)[0]
    page.write_text(
        "# Урок Словник Вправи Ресурси\n" + wrapper.format('<Tabs syncKey="module-tab">' + tab_markup + "</Tabs>"),
        encoding="utf-8",
    )
    monkeypatch.setattr(lp, "run_mdx_render_gate", lambda t: {"passed": True})
    rep = vs.verify("a1", "greetings", module_dir=site_mod, plan_path=plan_file, fresh=True)
    assert rep["shippable"] is False
    step = next(s for s in rep["steps"] if s["step"] == "fresh_tabs.1")
    assert step["missing_tabs"] == ["Урок", "Словник", "Вправи", "Ресурси"]


@pytest.mark.parametrize(
    "plan",
    [
        "[invalid",
        "[]",
        "module: old",
        "plan_schema: 2\nlessons: []",
        "plan_schema: 2\nlessons: [{n: 1}, {n: 1}]",
        "plan_schema: 2\nlessons: [{n: true}]",
        "plan_schema: 2\nlessons: [{n: ../index}]",
        "plan_schema: 2\nlessons: [{n: 0}]",
        "plan_schema: 2\nlessons: [null]",
    ],
)
@pytest.mark.parametrize("through_lesson", [None, 1])
def test_verify_fresh_invalid_plan_fails_closed(tmp_path, monkeypatch, plan, through_lesson):
    site_mod, plan_file = _mk_fresh(tmp_path)
    plan_file.write_text(plan, encoding="utf-8")
    monkeypatch.setattr(lp, "run_mdx_render_gate", lambda t: {"passed": True})
    rep = vs.verify(
        "a1", "greetings", module_dir=site_mod, plan_path=plan_file, fresh=True, through_lesson=through_lesson
    )
    assert rep["shippable"] is False
    assert rep["steps"][0]["reason"] == "invalid_lesson_plan"


def test_verify_fresh_skipped_lesson_render_blocks_even_green_astro(tmp_path, monkeypatch):
    site_mod, plan_file = _mk_fresh(tmp_path)
    monkeypatch.setattr(vs, "PROJECT_ROOT", tmp_path)
    monkeypatch.setattr(vs, "_astro_build", lambda p: True)
    monkeypatch.setattr(lp, "run_mdx_render_gate", lambda t: {"passed": None})
    rep = vs.verify("a1", "greetings", module_dir=site_mod, plan_path=plan_file, fresh=True, astro_build=True)
    assert rep["render_fully_validated"] is True
    assert rep["shippable"] is False


@pytest.mark.parametrize("args,through_lesson", [([], None), (["--fresh", "--through-lesson", "1"], 1)])
def test_verify_shippable_no_flag_default_paths(monkeypatch, args, through_lesson):
    """Pin default path arguments and forwarding of the optional fresh scope."""
    seen = {}

    def fake_verify(
        level, slug, *, module_dir=None, plan_path=None, astro_build=False, fresh=False, through_lesson=None
    ):
        seen["level"] = level
        seen["slug"] = slug
        seen["module_dir"] = module_dir
        seen["plan_path"] = plan_path
        seen["astro_build"] = astro_build
        seen["fresh"] = fresh
        seen["through_lesson"] = through_lesson
        return {"level": level, "slug": slug, "shippable": True, "steps": []}

    monkeypatch.setattr(vs, "verify", fake_verify)
    ret = vs.main(["a1", "greetings", *args])
    assert ret == 0
    assert seen["level"] == "a1"
    assert seen["slug"] == "greetings"
    assert seen["fresh"] is bool(args)
    assert seen["through_lesson"] == through_lesson
    assert seen["module_dir"] is None
    assert seen["plan_path"] is None


def test_verify_shippable_fresh_and_lesson_is_ap_error():
    """--fresh cannot be combined with --lesson (ap.error -> exit code 2)."""
    import pytest

    with pytest.raises(SystemExit) as exc_info:
        vs.main(["a1", "greetings", "--fresh", "--lesson"])
    assert exc_info.value.code == 2


@pytest.mark.parametrize("ids,through_lesson", [((1, 2), 1), ((1, 3, 5), 3)])
def test_verify_fresh_scoped_pass_with_later_lessons_missing(tmp_path, monkeypatch, ids, through_lesson):
    site_mod, plan_file = _mk_fresh(tmp_path, ids=ids)
    for n in ids:
        if n > through_lesson:
            (site_mod / f"{n}.mdx").unlink()
    # Recaps participate in the same numeric scope as teaching lessons.
    plan = yaml.safe_load(plan_file.read_text())
    plan["lessons"][-1]["kind"] = "recap"
    plan_file.write_text(yaml.safe_dump(plan))
    monkeypatch.setattr(lp, "run_mdx_render_gate", lambda t: {"passed": True})
    rep = vs.verify(
        "a1", "greetings", module_dir=site_mod, plan_path=plan_file, fresh=True, through_lesson=through_lesson
    )
    assert rep["shippable"] is True
    lessons = rep["steps"][0]
    assert lessons["planned_count"] == len(ids)
    assert lessons["required_lesson_ids"] == [n for n in ids if n <= through_lesson]
    assert vs.verify("a1", "greetings", module_dir=site_mod, plan_path=plan_file, fresh=True)["shippable"] is False


@pytest.mark.parametrize("defect", ["missing", "tab", "render"])
def test_verify_fresh_scoped_earlier_lesson_defect_blocks(tmp_path, monkeypatch, defect):
    site_mod, plan_file = _mk_fresh(tmp_path, ids=(1, 3, 5))
    (site_mod / "5.mdx").unlink()
    page = site_mod / "1.mdx"
    if defect == "missing":
        page.unlink()
    elif defect == "tab":
        page.write_text(page.read_text().replace('label="Ресурси — Resources"', 'label="Other"'))
    monkeypatch.setattr(lp, "run_mdx_render_gate", lambda t: {"passed": defect != "render"})
    rep = vs.verify("a1", "greetings", module_dir=site_mod, plan_path=plan_file, fresh=True, through_lesson=3)
    assert rep["shippable"] is False
    by_step = {s["step"]: s for s in rep["steps"]}
    if defect == "missing":
        assert by_step["fresh_lessons"]["missing_lesson_ids"] == [1]
    elif defect == "tab":
        assert by_step["fresh_tabs.1"]["missing_tabs"] == ["Ресурси"]
    else:
        assert by_step["mdx_render"]["passed"] is False


@pytest.mark.parametrize("through_lesson", [0, 2, 6, True])
def test_verify_fresh_scoped_out_of_plan_number(tmp_path, monkeypatch, through_lesson):
    site_mod, plan_file = _mk_fresh(tmp_path, ids=(1, 3, 5))
    monkeypatch.setattr(lp, "run_mdx_render_gate", lambda t: pytest.fail("invalid scope must stop before rendering"))
    rep = vs.verify(
        "a1", "greetings", module_dir=site_mod, plan_path=plan_file, fresh=True, through_lesson=through_lesson
    )
    assert rep["shippable"] is False
    assert rep["steps"][0]["reason"] == "invalid_lesson_scope"
    assert rep["steps"][0]["planned_lesson_ids"] == [1, 3, 5]


def test_verify_fresh_scoped_ignores_later_page_defects_but_renders_landing(tmp_path, monkeypatch):
    site_mod, plan_file = _mk_fresh(tmp_path)
    (site_mod / "2.mdx").write_text("broken later page")
    (site_mod / "index.mdx").write_text("landing")
    seen = []

    def render(text):
        seen.append(text)
        return {"passed": text != "broken later page"}

    monkeypatch.setattr(lp, "run_mdx_render_gate", render)
    rep = vs.verify("a1", "greetings", module_dir=site_mod, plan_path=plan_file, fresh=True, through_lesson=1)
    assert rep["shippable"] is True
    assert len(seen) == 2 and "landing" in seen and "broken later page" not in seen


def test_verify_scoped_requires_fresh(tmp_path):
    rep = vs.verify("a1", "greetings", through_lesson=1)
    assert rep["shippable"] is False
    assert rep["steps"][0]["reason"] == "invalid_lesson_scope"
    with pytest.raises(SystemExit) as exc:
        vs.main(["a1", "greetings", "--through-lesson", "1"])
    assert exc.value.code == 2


def test_verify_fresh_scoped_requires_recap_endpoint(tmp_path, monkeypatch):
    site_mod, plan_file = _mk_fresh(tmp_path, ids=(1, 3))
    plan = yaml.safe_load(plan_file.read_text())
    plan["lessons"][-1]["kind"] = "recap"
    plan_file.write_text(yaml.safe_dump(plan))
    (site_mod / "3.mdx").unlink()
    monkeypatch.setattr(lp, "run_mdx_render_gate", lambda t: {"passed": True})
    rep = vs.verify("a1", "greetings", module_dir=site_mod, plan_path=plan_file, fresh=True, through_lesson=3)
    assert rep["shippable"] is False
    assert rep["steps"][0]["missing_lesson_ids"] == [3]
    assert rep["steps"][0]["required_lesson_ids"] == [1, 3]


def test_verify_fresh_scoped_cli_out_of_plan_is_typed_failure(tmp_path, capsys):
    site_mod, plan_file = _mk_fresh(tmp_path, ids=(1, 3))
    result = vs.main(
        [
            "a1",
            "greetings",
            "--fresh",
            "--through-lesson",
            "2",
            "--module-dir",
            str(site_mod),
            "--plan",
            str(plan_file),
            "--json",
        ]
    )
    assert result == 1
    import json

    report = json.loads(capsys.readouterr().out)
    assert report["steps"][0]["reason"] == "invalid_lesson_scope"
