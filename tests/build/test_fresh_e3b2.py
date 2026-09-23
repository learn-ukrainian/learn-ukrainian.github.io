"""Contract checks for check-12 manifests, immutable closure and draft freshness."""

from __future__ import annotations

import hashlib
import json
import os
import shutil
from pathlib import Path

import pytest
import yaml
from jsonschema import Draft202012Validator

from scripts.build.fresh import manifest
from scripts.build.fresh.closure import compute_closure
from scripts.build.fresh.module import draft_is_current
from scripts.build.fresh.regeneration import load_ledger, record_failure, record_success
from scripts.curriculum.evidence import lock

pytestmark = pytest.mark.reads_content


def _fixture(root: Path):
    level, slug = "a1", "fixture-module"
    plan_dir = root / "curriculum/l2-uk-en/lesson-plans/a1"
    evidence_dir = root / "curriculum/l2-uk-en/evidence/a1"
    state_dir = evidence_dir / "_state" / slug
    page_dir = root / "site/src/content/docs/a1" / slug
    cards = root / "docs/style-cards"
    for folder in (plan_dir, evidence_dir, state_dir, page_dir, cards):
        folder.mkdir(parents=True, exist_ok=True)
    (plan_dir / f"{slug}.yaml").write_text("lessons: []\n", encoding="utf-8")
    (plan_dir / "_decisions.yaml").write_text("decisions: []\n", encoding="utf-8")
    lock.write(evidence_dir / f"{slug}.yaml", b"records: []\n")
    lock.write(evidence_dir / "_words.yaml", b"words: []\n")
    (cards / "a1.md").write_text("A1 style\n", encoding="utf-8")
    (cards / "a1.sha256").write_text(hashlib.sha256((cards / "a1.md").read_bytes()).hexdigest() + "\n", encoding="ascii")
    (state_dir / "lessons.lock.yaml").write_bytes(lock.yaml_bytes({"lessons": [
        {"n": n, "entry_sha256": f"{n}" * 64} for n in (1, 2, 3)]}))
    for n in (1, 2, 3):
        (page_dir / f"{n}.mdx").write_text(f"# Lesson {n}\n", encoding="utf-8")
        (state_dir / f"lesson-{n}.gates.yaml").write_bytes(lock.yaml_bytes({"passed": True}))
    return level, slug, plan_dir, evidence_dir, state_dir, page_dir


def test_manifest_history_and_closure_preserve_stale_attempts(tmp_path, monkeypatch):
    level, slug, plan_dir, evidence_dir, state_dir, page_dir = _fixture(tmp_path)
    monkeypatch.setattr(manifest, "planned_state", lambda *a, **kw: type(
        "State", (), {"to_dict": lambda self: {"b": 2, "a": 1}})())
    assert manifest.learner_state_sha256(type("State", (), {"to_dict": lambda self: {"a": 1, "b": 2}})()) == (
        hashlib.sha256(b'{"a":1,"b":2}').hexdigest())
    old = {}
    for n in (1, 2, 3):
        _, old[n] = manifest.write_manifest(level, slug, n, lesson_kind="recap" if n == 3 else "lesson",
                                            state_dir=state_dir, repo_root=tmp_path, plans_dir=plan_dir,
                                            evidence_dir=evidence_dir, position=1, site_dir=page_dir)
        data = yaml.safe_load((state_dir / f"lesson-{n}.manifest.yaml").read_text(encoding="utf-8"))
        Draft202012Validator(json.loads(manifest.SCHEMA.read_text(encoding="utf-8"))).validate(data)
        assert data["recap"] is (n == 3)
        assert [row["n"] for row in data["upstream_lessons"]] == list(range(1, n))
    lessons = [{"n": n, "kind": "recap" if n == 3 else "teach"} for n in (1, 2, 3)]
    clean = compute_closure(level, slug, lessons, repo_root=tmp_path, state_dir=state_dir, site_dir=page_dir)
    assert clean["stale"] == []
    (page_dir / "1.mdx").write_text("# Lesson 1 changed\n", encoding="utf-8")
    for n in (1, 2, 3):
        manifest.write_manifest(level, slug, n, lesson_kind="recap" if n == 3 else "lesson",
                                state_dir=state_dir, repo_root=tmp_path, plans_dir=plan_dir,
                                evidence_dir=evidence_dir, position=1, site_dir=page_dir)
    changed = compute_closure(level, slug, lessons, repo_root=tmp_path, state_dir=state_dir, site_dir=page_dir)
    assert {(row["n"], row["manifest_sha256"]) for row in changed["stale"]} == {(2, old[2]), (3, old[3])}
    assert all(row["upstream"] == 1 for row in changed["stale"])


def test_style_card_sidecar_mismatch_fails_manifest(tmp_path, monkeypatch):
    level, slug, plan_dir, evidence_dir, state_dir, page_dir = _fixture(tmp_path)
    monkeypatch.setattr(manifest, "planned_state", lambda *a, **kw: type(
        "State", (), {"to_dict": lambda self: {}})())
    (tmp_path / "docs/style-cards/a1.sha256").write_text("0" * 64 + "\n", encoding="ascii")
    with pytest.raises(ValueError, match="style card sidecar mismatch"):
        manifest.write_manifest(level, slug, 1, lesson_kind="lesson", state_dir=state_dir,
                                repo_root=tmp_path, plans_dir=plan_dir, evidence_dir=evidence_dir,
                                position=1, site_dir=page_dir)
    assert not (state_dir / "lesson-1.manifest.yaml").exists()


def test_successful_manifest_clears_stale_check_12_error(tmp_path, monkeypatch):
    level, slug, plan_dir, evidence_dir, state_dir, page_dir = _fixture(tmp_path)
    monkeypatch.setattr(manifest, "planned_state", lambda *a, **kw: type(
        "State", (), {"to_dict": lambda self: {}})())
    manifest.write_manifest_error(state_dir, 1, "old failure", "docs/style-cards/a1.sha256",
                                  "2026-01-01T00:00:00Z")
    manifest.write_manifest(level, slug, 1, lesson_kind="lesson", state_dir=state_dir,
                            repo_root=tmp_path, plans_dir=plan_dir, evidence_dir=evidence_dir,
                            position=1, site_dir=page_dir)
    assert not (state_dir / "lesson-1.manifest-error.yaml").exists()


def test_manifest_hashes_all_imported_activity_data_sorted(tmp_path, monkeypatch):
    level, slug, plan_dir, evidence_dir, state_dir, page_dir = _fixture(tmp_path)
    monkeypatch.setattr(manifest, "planned_state", lambda *a, **kw: type(
        "State", (), {"to_dict": lambda self: {}})())
    data_dir = tmp_path / "site/src/data"
    data_dir.mkdir(parents=True)
    for name in ("activity-z.json", "activity-a.json"):
        (data_dir / name).write_text("{}\n", encoding="utf-8")
    (page_dir / "1.mdx").write_text(
        'import z from "@site/src/data/activity-z.json";\n'
        'import a from "@site/src/data/activity-a.json";\n', encoding="utf-8")
    doc, _ = manifest.write_manifest(level, slug, 1, lesson_kind="lesson", state_dir=state_dir,
                                     repo_root=tmp_path, plans_dir=plan_dir, evidence_dir=evidence_dir,
                                     position=1, site_dir=page_dir)
    assert [item["path"] for item in doc["inputs"]["activity_data"]] == [
        "site/src/data/activity-a.json", "site/src/data/activity-z.json"]
    (data_dir / "activity-a.json").unlink()
    with pytest.raises(FileNotFoundError, match=r"activity-a\.json"):
        manifest.write_manifest(level, slug, 1, lesson_kind="lesson", state_dir=state_dir,
                                repo_root=tmp_path, plans_dir=plan_dir, evidence_dir=evidence_dir,
                                position=1, site_dir=page_dir)


def test_build_cli_requires_exactly_one_target():
    from scripts.build.fresh.cli import _build_parser

    parser = _build_parser()
    with pytest.raises(SystemExit):
        parser.parse_args(["build", "a1", "fixture-module"])
    with pytest.raises(SystemExit):
        parser.parse_args(["build", "a1", "fixture-module", "--lesson", "1", "--module"])


def test_success_snapshot_controls_draft_reuse(tmp_path):
    draft = tmp_path / "lesson-1.draft.yaml"
    draft.write_text("lesson: one\n", encoding="utf-8")
    keys = ("plan_sha256", "pack_lock", "words_lock", "card_sha256", "prompt_sha256")
    inputs = {key: "a" * 64 for key in keys}
    path = tmp_path / "lesson-1.regeneration.yaml"
    record_success(path, "fixture-module", 1, {**inputs, "draft_sha256": hashlib.sha256(draft.read_bytes()).hexdigest()},
                   at="2026-01-01T00:00:00Z")
    ledger = load_ledger(path, "fixture-module", 1)
    assert draft_is_current(ledger, draft, inputs)
    assert not draft_is_current(ledger, draft, {**inputs, "prompt_sha256": "b" * 64})
    record_failure(path, "fixture-module", 1, {"check": 11, "reason": "render_failed", "layer": "engine"}, inputs,
                   at="2026-01-02T00:00:00Z")
    ledger = load_ledger(path, "fixture-module", 1)
    assert ledger["attempts"][0]["failed_check"] == 11
    assert not draft_is_current(ledger, draft, inputs)


def test_module_build_three_lessons_and_rebuild_closure(tmp_path, monkeypatch, capsys):
    """Exercise the real checks 1-12 with injected model, resolver, and render edges."""
    import copy

    from scripts.build.fresh import assemble, cli, module, runner
    from scripts.build.fresh.preflight import PreflightResult
    from scripts.curriculum.learner_state.inventory_gate import GateReport
    from scripts.curriculum.resolver.inputs import Allowlist
    from tests.build.test_fresh_assemble import validate_fixture_plan
    from tests.build.test_fresh_runner import _fixture as lesson_fixture
    from tests.build.test_fresh_runner import _FixtureSources

    level, slug, plan_dir, evidence_dir, state_dir, page_dir = _fixture(tmp_path)
    base_draft, base_plan, pack, words = lesson_fixture()
    lessons = []
    for n in (1, 2, 3):
        entry = copy.deepcopy(base_plan["lessons"][0])
        entry.update(n=n, slug=f"lesson-{n}", title=f"Lesson {n}", kind="recap" if n == 3 else "teach")
        lessons.append(entry)
    plan = {**base_plan, "module": slug, "slug": slug, "lessons": lessons}
    validate_fixture_plan(plan)
    (plan_dir / f"{slug}.yaml").write_bytes(lock.yaml_bytes(plan))
    paths = {"plan": plan_dir / f"{slug}.yaml", "pack": evidence_dir / f"{slug}.yaml",
             "words": evidence_dir / "_words.yaml", "lock": state_dir / "lessons.lock.yaml",
             "state_dir": evidence_dir / "_state"}

    class State:
        cumulative_core_count = 10
        waiver = None

        def to_dict(self):
            return {"lesson": 1}

    def load_data(_level, _slug, n, **_kw):
        return plan, lessons[n - 1], pack, words, paths

    def hashes(_paths, n, _state):
        return {"plan_sha256": hashlib.sha256(paths["plan"].read_bytes()).hexdigest(),
                "pack_lock": "0" * 64, "words_lock": "0" * 64,
                "lesson_lock_entry_sha256": "0" * 64, "learner_state_sha256": "0" * 64}

    monkeypatch.setattr(cli, "_load_lesson_data", load_data)
    monkeypatch.setattr(cli, "_compute_input_hashes", hashes)
    monkeypatch.setattr(cli, "_load_cited_records", lambda *a: {})
    monkeypatch.setattr(module, "planned_state", lambda *a, **kw: State())
    monkeypatch.setattr(manifest, "planned_state", lambda *a, **kw: State())
    monkeypatch.setattr(assemble, "planned_state", lambda *a, **kw: State())
    monkeypatch.setattr(assemble.lesson_lock, "check_lesson_lock", lambda *a, **kw: (True, ""))
    monkeypatch.setattr(assemble.lesson_lock, "compute_lesson_lock", lambda *a, **kw: {
        "lessons": [{"n": n, "entry_sha256": "0" * 64} for n in (1, 2, 3)]})
    monkeypatch.setattr(assemble, "compute_lesson_immersion_band", lambda **kw: type(
        "Band", (), {"band_key": "a1"})())
    monkeypatch.setattr(module, "preflight_lesson", lambda *a, **kw: PreflightResult(
        passed=True, status="ok", gaps=[], homographs=[], homograph_count=0))
    monkeypatch.setattr(module, "render_lesson_prompt", lambda _entry, **kw: "lesson prompt " + kw["plan_sha256"])
    monkeypatch.setattr(module, "render_recap_prompt", lambda _entry, *, built_lessons, **kw:
                        "recap prompt " + " ".join(item["sha256"] for item in built_lessons) + kw["plan_sha256"])
    monkeypatch.setattr(module, "check_rendered_prompt", lambda prompt, *a, **kw: type(
        "Result", (), {"passed": True, "errors": []})())
    monkeypatch.setattr(module, "compute_immersion_payload", lambda *a, **kw: {})
    allowlist = Allowlist.from_records(words["words"], words_lock="f" * 64)
    calls = []
    version = [1]

    def writer_call(**kw):
        n = kw["lesson_n"]
        calls.append(n)
        draft = copy.deepcopy(base_draft)
        draft["lesson"] = {"module": f"a1/{slug}", "n": n}
        draft["inputs"].update(hashes(paths, n, None))
        draft["inputs"]["style_card_sha256"] = hashlib.sha256((tmp_path / "docs/style-cards/a1.md").read_bytes()).hexdigest()
        if n == 1 and version[0] == 2:
            draft["steps"][0]["blocks"][0]["text"] += " слово"
        lock.atomic_write(state_dir / f"lesson-{n}.draft.yaml", lock.yaml_bytes(draft))

    def question_call(batch, seat):
        return {"answers": [{"id": q["id"], "record": q["candidates"][0]["record"]}
                            for q in batch["questions"]]}

    def run_actual(*args, **kwargs):
        return runner.run_lesson(*args, **kwargs, sources=_FixtureSources(), allowlist=allowlist,
                                 question_dispatch=question_call,
                                 inventory_gate=lambda *a, **kw: GateReport("a1", slug, args[2], ()),
                                 observed_writer=lambda *a, **kw: None,
                                 render_check=lambda *a, **kw: assemble.CheckResult(
                                     check=11, passed=True, artifacts={"verify_shippable": {"shippable": True}}))

    evidence_path = os.environ.get("E3B2_EVIDENCE_DIR")
    saved = Path(evidence_path) if evidence_path else None
    if saved:
        saved.mkdir(parents=True, exist_ok=True)
    no_seat = module.build_module(level, slug, repo_root=tmp_path, runner=run_actual)
    assert not no_seat["complete"] and no_seat["lessons"][0]["stopping_check"] == 0
    assert no_seat["lessons"][0]["reason"] == "writer_seat_required"
    if saved:
        shutil.copy2(state_dir / "module.build.yaml", saved / "writer-seat-required.build.yaml")
    no_recap = module.build_module(level, slug, repo_root=tmp_path, lesson_n=3,
                                   writer_seat="codex:gpt-6-sol", runner=run_actual)
    assert not no_recap["complete"] and no_recap["lessons"][0]["reason"] == "recap_inputs_not_built"
    if saved:
        shutil.copy2(state_dir / "module.build.yaml", saved / "recap-inputs-not-built.build.yaml")
    build_with_injections = module.build_module
    with monkeypatch.context() as patch:
        patch.setattr(module, "build_module", lambda *a, **kw: build_with_injections(
            *a, writer_dispatch=writer_call, runner=run_actual, **kw))
        assert cli.main(["build", level, slug, "--module", "--writer-seat", "codex:gpt-6-sol",
                         "--question-seat", "codex:gpt-6-sol", "--repo-root", str(tmp_path)]) == 0
    first = json.loads(capsys.readouterr().out)
    assert first["complete"] and calls == [1, 2, 3], first
    assert cli.main(["closure", level, slug, "--repo-root", str(tmp_path)]) == 0
    assert json.loads(capsys.readouterr().out)["stale"] == []
    assert all(row["passed_through"] == 12 and row["manifest_sha256"] for row in first["lessons"])
    for n in (1, 2, 3):
        gates = yaml.safe_load((state_dir / f"lesson-{n}.gates.yaml").read_text(encoding="utf-8"))
        assert [row["check"] for row in gates["checks"]] == list(range(1, 12))
        assert gates["passed"] is True
    recap = yaml.safe_load((state_dir / "lesson-3.manifest.yaml").read_text(encoding="utf-8"))
    assert recap["recap"] is True and [item["n"] for item in recap["upstream_lessons"]] == [1, 2]
    assert yaml.safe_load((state_dir / "module.closure.yaml").read_text(encoding="utf-8"))["stale"] == []
    stable_before = {name: (state_dir / name).read_bytes() for name in (
        "module.build.yaml", "module.closure.yaml", "lesson-1.manifest.yaml", "lesson-2.manifest.yaml",
        "lesson-3.manifest.yaml", "lesson-1.regeneration.yaml", "lesson-2.regeneration.yaml",
        "lesson-3.regeneration.yaml")}
    if evidence_path:
        shutil.copy2(paths["plan"], saved / "fixture-module.yaml")
        for n in (1, 2, 3):
            shutil.copy2(page_dir / f"{n}.mdx", saved / f"initial-{n}.mdx")
            shutil.copy2(state_dir / f"lesson-{n}.gates.yaml", saved / f"lesson-{n}.gates.yaml")
            shutil.copy2(state_dir / f"lesson-{n}.manifest.yaml", saved / f"initial-{n}.manifest.yaml")
        shutil.copy2(state_dir / "module.build.yaml", saved / "initial-module.build.yaml")
        shutil.copy2(state_dir / "module.closure.yaml", saved / "initial-module.closure.yaml")
    before = {n: hashlib.sha256((page_dir / f"{n}.mdx").read_bytes()).hexdigest() for n in (1, 2, 3)}
    second = module.build_module(level, slug, repo_root=tmp_path, writer_seat="codex:gpt-6-sol",
                                 question_seat="codex:gpt-6-sol", writer_dispatch=writer_call, runner=run_actual)
    assert second["complete"] and calls == [1, 2, 3]
    assert stable_before == {name: (state_dir / name).read_bytes() for name in stable_before}
    assert before == {n: hashlib.sha256((page_dir / f"{n}.mdx").read_bytes()).hexdigest() for n in (1, 2, 3)}
    version[0] = 2
    paths["plan"].write_bytes(paths["plan"].read_bytes() + b"# revised\n")
    third = module.build_module(level, slug, repo_root=tmp_path, writer_seat="codex:gpt-6-sol",
                                question_seat="codex:gpt-6-sol", writer_dispatch=writer_call, runner=run_actual)
    assert third["complete"] and calls == [1, 2, 3, 1, 2, 3], third
    assert hashlib.sha256((page_dir / "1.mdx").read_bytes()).hexdigest() != before[1]
    closure = yaml.safe_load((state_dir / "module.closure.yaml").read_text(encoding="utf-8"))
    assert {(row["n"], row["upstream"]) for row in closure["stale"]} >= {(2, 1), (3, 1)}
    if evidence_path:
        shutil.copy2(state_dir / "module.build.yaml", saved / "rebuilt-module.build.yaml")
        shutil.copy2(state_dir / "module.closure.yaml", saved / "rebuilt-module.closure.yaml")
    (tmp_path / "docs/style-cards/a1.sha256").write_text("0" * 64 + "\n", encoding="ascii")
    mismatch = module.build_module(level, slug, repo_root=tmp_path, lesson_n=1,
                                   writer_seat="codex:gpt-6-sol", question_seat="codex:gpt-6-sol",
                                   writer_dispatch=writer_call, runner=run_actual)
    assert not mismatch["complete"] and mismatch["lessons"][0]["stopping_check"] == 12
    assert mismatch["lessons"][0]["terminal_layer"] == "driver"
    error = yaml.safe_load((state_dir / "lesson-1.manifest-error.yaml").read_text(encoding="utf-8"))
    assert error["check"] == 12 and "sidecar mismatch" in error["reason"]
    assert error["path"] == "docs/style-cards/a1.sha256"
    assert not (state_dir / "lesson-1.manifest.yaml").exists()
    if evidence_path:
        shutil.copy2(state_dir / "lesson-1.manifest-error.yaml", saved / "lesson-1.manifest-error.yaml")
        shutil.copy2(state_dir / "module.build.yaml", saved / "mismatch-module.build.yaml")
    terminal = module.build_module(level, slug, repo_root=tmp_path, lesson_n=1,
                                   writer_seat="codex:gpt-6-sol", runner=run_actual)
    assert terminal["lessons"][0]["terminal_layer"] == "driver"
    if evidence_path:
        shutil.copy2(state_dir / "module.build.yaml", saved / "terminal-module.build.yaml")
