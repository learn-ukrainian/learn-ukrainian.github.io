"""Tests for verify_shippable — the Definition-of-Done predicate (#3138).

The pipeline functions are heavy; these tests monkeypatch them on the source
module (verify() imports them lazily at call time) to exercise the verdict logic
deterministically without data/, MCP, or Node.
"""

from __future__ import annotations

import scripts.build.linear_pipeline as lp
import scripts.build.verify_shippable as vs
from scripts.build import promote_quality_gate as pqg


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
    monkeypatch.setattr(
        lp, "run_mdx_render_gate", lambda t: {"passed": True, "message": "ok", "failures": []}
    )
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
