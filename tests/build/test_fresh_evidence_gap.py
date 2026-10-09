"""Regression replies from #9390's ddb6a619dbf64b2db2252cce341c9182d388cb16 build.

The fixtures are exact raw replies (attempt 1's canary copy and attempt 2's
root copy); they contain gap declarations and instructions, no source text.
"""

from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path
from types import SimpleNamespace

import pytest
import yaml

from scripts.build.fresh import cli, module
from scripts.build.fresh.draft_schema import validate_draft
from scripts.build.fresh.regeneration import INPUT_KEYS, load_ledger, record_failure, record_success, record_writer_call
from scripts.build.fresh.runner import run_lesson
from scripts.build.fresh.writer import parse_and_validate_reply
from scripts.curriculum.evidence import lock

FIXTURES = Path(__file__).parent / "fixtures/fresh"
TYPES = {"a1": "watch-and-repeat", "a2": "quiz", "a3": "watch-and-repeat", "a4": "quiz", "a5": "quiz"}


def _raw(attempt):
    fixture = json.loads((FIXTURES / f"evidence-gap-attempt-{attempt}.json").read_text(encoding="utf-8"))
    assert hashlib.sha256(fixture["raw_reply"].encode("utf-8")).hexdigest() == fixture["sha256"]
    return fixture["raw_reply"]


def _plan():
    return {
        "lessons": [
            {
                "n": 1,
                "kind": "teach",
                "steps": [
                    {"id": "s1", "evidence": ["T-002", "X-001", "V-001"]},
                    {"id": "s2", "evidence": ["T-002", "T-003", "T-020", "T-021"]},
                ],
                "activities": [{"id": aid, "type": typ} for aid, typ in TYPES.items()],
            }
        ]
    }


def _run(root, draft, plan=None, expected_inputs=None):
    return run_lesson(
        "a1",
        "sounds-letters-and-hello",
        1,
        draft=draft,
        plan=plan or _plan(),
        pack={},
        words={},
        state_dir=root,
        repo_root=Path(__file__).resolve().parents[2],
        plans_dir=root,
        evidence_dir=root,
        expected_inputs=expected_inputs,
    )


@pytest.mark.parametrize("attempt", [1, 2])
def test_real_gap_replies_validate_and_stop_at_gap_layer(tmp_path, attempt):
    draft = parse_and_validate_reply(_raw(attempt), "a1", plan_activity_types=TYPES)
    report = _run(tmp_path, draft)
    bad = next(row for row in report["checks"] if row["status"] == "failed")
    assert (bad["check"], bad["layer"]) == (2, "pack")
    assert json.loads(bad["reason"].removeprefix("evidence_gap: ")) == draft["gaps"]
    assert all(row["status"] == "not_checked" for row in report["checks"] if row["check"] > 2)


@pytest.mark.parametrize(
    "need", ["quote", "publication_right", "example", "error", "word_form", "video", "standard_line"]
)
def test_gap_need_routes_to_pack(tmp_path, need):
    draft = yaml.safe_load(_raw(1))
    for gap in draft["gaps"]:
        gap["need"] = need
    bad = next(row for row in _run(tmp_path, draft)["checks"] if row["status"] == "failed")
    assert (bad["check"], bad["layer"]) == (2, "pack")


@pytest.mark.parametrize("dialogue", [False, True])
def test_multi_step_quote_gaps_require_each_step_to_have_a_host(tmp_path, dialogue):
    plan = _plan()
    for step in plan["lessons"][0]["steps"]:
        step["evidence"] = ["X-001", "V-001"]
    if dialogue:
        plan["lessons"][0]["dialogue"] = {"step": "s1"}
    bad = next(row for row in _run(tmp_path, yaml.safe_load(_raw(2)), plan)["checks"] if row["status"] == "failed")
    assert (bad["check"], bad["layer"]) == (2, "plan")


@pytest.mark.parametrize("need", ["quote", "publication_right"])
@pytest.mark.parametrize("host", ["record", "dialogue"])
@pytest.mark.parametrize("host_step", ["s1", "s2"])
@pytest.mark.parametrize("gap_step", ["s1", "s2"])
def test_quote_host_must_belong_to_gap_step(tmp_path, need, host, host_step, gap_step):
    plan = _plan()
    lesson = plan["lessons"][0]
    for step in lesson["steps"]:
        step["evidence"] = ["X-001"]
        if host == "record" and step["id"] == host_step:
            step["evidence"].append("T-002")
    if host == "dialogue":
        lesson["dialogue"] = {"step": host_step}
    draft = yaml.safe_load(_raw(2))
    draft["gaps"] = [{"step": gap_step, "need": need, "detail": "Missing quote or publication right."}]
    for step in draft["steps"]:
        step["blocks"] = [] if step["id"] == gap_step else [{"kind": "tip", "text": "tip"}]
    bad = next(row for row in _run(tmp_path, draft, plan)["checks"] if row["status"] == "failed")
    assert (bad["check"], bad["layer"]) == (2, "pack" if host_step == gap_step else "plan")


@pytest.mark.parametrize(
    "defect",
    ["empty_gaps", "unknown_need", "missing_hash", "bad_hash", "unknown_step", "nonempty_gap_step", "duplicate_step"],
)
def test_gap_shape_and_identity_inputs_remain_binding(defect):
    draft = yaml.safe_load(_raw(2))
    if defect == "empty_gaps":
        draft["gaps"] = []
    elif defect == "unknown_need":
        draft["gaps"][0]["need"] = "plan"
    elif defect == "missing_hash":
        del draft["inputs"]["pack_lock"]
    elif defect == "bad_hash":
        draft["inputs"]["pack_lock"] = "invalid"
    elif defect == "unknown_step":
        draft["gaps"][0]["step"] = "s3"
    elif defect == "nonempty_gap_step":
        draft["steps"][0]["blocks"] = [{"kind": "tip", "text": "tip"}]
    else:
        draft["steps"].append(copy.deepcopy(draft["steps"][0]))
    assert validate_draft(draft, "a1", activity_types=TYPES)


@pytest.mark.parametrize("defect", ["lesson", "hash", "plan_step"])
def test_gap_identity_is_checked_before_check_2(tmp_path, defect):
    draft = yaml.safe_load(_raw(2))
    inputs = dict(draft["inputs"])
    if defect == "lesson":
        draft["lesson"]["n"] = 2
    elif defect == "hash":
        inputs["pack_lock"] = "a" * 64
    else:
        draft["gaps"][0]["step"] = "s3"
        draft["steps"][0]["id"] = "s3"
    bad = next(row for row in _run(tmp_path, draft, expected_inputs=inputs)["checks"] if row["status"] == "failed")
    assert (bad["check"], bad["layer"]) == (1, "writer")


def test_ok_reply_still_requires_full_lesson_payload():
    draft = yaml.safe_load(_raw(2))
    draft["status"] = "ok"
    draft["gaps"] = []
    assert validate_draft(draft, "a1", activity_types=TYPES)


@pytest.fixture
def module_build(tmp_path, monkeypatch):
    plan = _plan()
    pack, words = {}, {}
    slug = "sounds-letters-and-hello"
    ev = tmp_path / "curriculum/l2-uk-en/evidence/a1"
    plans = tmp_path / "curriculum/l2-uk-en/lesson-plans/a1"
    cards = tmp_path / "docs/style-cards"
    for directory in (ev, plans, cards):
        directory.mkdir(parents=True)
    (cards / "a1.md").write_text("A1 card", encoding="utf-8")
    paths = {
        "state_dir": ev / "_state",
        "pack": ev / "pack.yaml",
        "words": ev / "_words.yaml",
        "plan": plans / "module.yaml",
    }
    hashes = yaml.safe_load(_raw(1))["inputs"]
    hashes["style_card_sha256"] = hashlib.sha256((cards / "a1.md").read_bytes()).hexdigest()
    monkeypatch.setattr(cli, "_load_lesson_data", lambda *a, **kw: (plan, plan["lessons"][0], pack, words, paths))
    monkeypatch.setattr(cli, "_compute_input_hashes", lambda *a: dict(hashes))
    monkeypatch.setattr(cli, "_load_cited_records", lambda *a: {})
    monkeypatch.setattr(module, "planned_state", lambda *a, **kw: object())
    monkeypatch.setattr(module, "grammar_points", lambda *a: [])
    monkeypatch.setattr(module, "lesson_immersion_payload", lambda *a: {})
    monkeypatch.setattr(module, "render_lesson_prompt", lambda *a, **kw: "fixture prompt")
    monkeypatch.setattr(module, "check_rendered_prompt", lambda *a, **kw: SimpleNamespace(passed=True, errors=[]))
    monkeypatch.setattr(module, "preflight_lesson", lambda *a, **kw: SimpleNamespace(passed=True))
    state = ev / "_state" / slug
    calls = []

    def build(
        *,
        invalid_second=False,
        runner=run_lesson,
        writer_seat="codex:gpt-6.1-sol",
        successful=False,
        prompt="fixture prompt",
    ):
        nonlocal plan, pack, words
        if successful:
            from tests.build.test_fresh_runner import _fixture

            # Accounting success needs a complete lesson; gap replies remain
            # the unchanged failure fixtures above.
            complete_draft, plan, pack, words = _fixture()
        monkeypatch.setattr(module, "render_lesson_prompt", lambda *a, **kw: prompt)

        def writer(**kw):
            calls.append(kw["attempt"])
            # The task ID is keyed by the ledger's full input snapshot (#8425).
            assert set(kw["inputs"]) == set(INPUT_KEYS)
            assert kw["inputs"]["prompt_sha256"] == kw["prompt_sha256"]
            if not successful:
                assert len(calls) <= 2, "a repeated evidence gap must stop before a third writer call"
            if successful:
                draft = copy.deepcopy(complete_draft)
                draft["lesson"]["module"] = f"a1/{slug}"
            else:
                raw = _raw(len(calls))
                if invalid_second and len(calls) == 2:
                    raw = raw.replace("status: evidence_gap", "status: unknown")
                draft = parse_and_validate_reply(raw, "a1", plan_activity_types=kw["plan_activity_types"])
            # Only the synthetic tree's input identity differs from the real reply.
            draft["inputs"] = dict(hashes)
            lock.write(state / "lesson-1.draft.yaml", lock.yaml_bytes(draft))
            if successful:
                lock.write(state / "lesson-1.writer.yaml", lock.yaml_bytes({
                    "task_id": f"synthetic-gap-success-{len(calls)}", "attempt": kw["attempt"],
                    "writer": kw["writer"], "model": kw["model"], "effort": "high",
                    "prompt_sha256": kw["prompt_sha256"],
                }))

        return module.build_module(
            "a1", slug, repo_root=tmp_path, lesson_n=1, writer_seat=writer_seat, writer_dispatch=writer, runner=runner
        )

    return build, state, calls


def test_real_gap_stops_without_regeneration_and_counts_agree(module_build):
    build, state, calls = module_build
    report = build()
    assert calls == [1]
    ledger = load_ledger(state / "lesson-1.regeneration.yaml", "sounds-letters-and-hello", 1)
    stored = yaml.safe_load((state / "module.build.yaml").read_text(encoding="utf-8"))
    assert report == stored
    assert len(ledger["attempts"]) == 1
    assert ledger["regenerations"] == stored["lessons"][0]["regenerations"] == 0
    assert ledger["terminal_layer"] == stored["lessons"][0]["terminal_layer"] == "pack"
    assert (stored["lessons"][0]["stopping_check"], stored["lessons"][0]["layer"]) == (2, "pack")
    assert json.loads(stored["lessons"][0]["reason"].removeprefix("evidence_gap: ")) == yaml.safe_load(_raw(1))["gaps"]
    rerun = build()
    assert calls == [1]  # A terminal rerun never dispatches again.
    assert rerun == report


def _writer_failure(*args, **kw):
    """A delivered writer defect permits the second reply in accounting tests."""
    failure = {"check": 6, "status": "failed", "layer": "writer", "reason": "fixture writer failure"}
    expected = kw["expected_inputs"]
    inputs = {key: expected["style_card_sha256" if key == "card_sha256" else key] for key in INPUT_KEYS}
    record_failure(kw["state_dir"] / "lesson-1.regeneration.yaml", args[1], args[2], failure, inputs)
    return {"passed": False, "checks": [failure]}


def test_rejected_second_reply_still_counts_writer_call(module_build):
    build, state, calls = module_build
    report = build(invalid_second=True, runner=_writer_failure)
    ledger = load_ledger(state / "lesson-1.regeneration.yaml", "sounds-letters-and-hello", 1)
    assert calls == [1, 2]
    assert ledger["regenerations"] == report["lessons"][0]["regenerations"] == 1
    assert len(ledger["attempts"]) == 2
    assert report["lessons"][0]["stopping_check"] == 1


def test_resume_without_writer_preserves_count_in_both_state_files(module_build):
    build, state, calls = module_build
    build(invalid_second=True, runner=_writer_failure)
    report = build(writer_seat=None)
    ledger = load_ledger(state / "lesson-1.regeneration.yaml", "sounds-letters-and-hello", 1)
    stored = yaml.safe_load((state / "module.build.yaml").read_text(encoding="utf-8"))
    assert calls == [1, 2]
    assert report == stored
    assert ledger["regenerations"] == stored["lessons"][0]["regenerations"] == 1


def test_regeneration_limit_counts_calls_without_double_counting(tmp_path):
    path = tmp_path / "lesson-1.regeneration.yaml"
    for attempt in (1, 2, 3):
        before = record_writer_call(path, "sample", 1)
        assert before["regenerations"] == attempt - 1
        after = record_failure(path, "sample", 1, {"check": attempt, "layer": "writer", "reason": "failure"}, {})
        assert after["regenerations"] == attempt - 1
    assert after["terminal_layer"] == "driver"
    assert record_writer_call(path, "sample", 1) == after


@pytest.mark.parametrize("with_snapshot", [False, True])
def test_rewrite_after_success_never_burns_regeneration_budget(tmp_path, with_snapshot):
    path = tmp_path / "lesson-1.regeneration.yaml"
    inputs = {key: "a" * 64 for key in INPUT_KEYS}
    for _ in range(4):
        before = record_writer_call(path, "sample", 1)
        assert (before["regenerations"], before["terminal_layer"]) == (0, None)
        after = record_success(path, "sample", 1, {**inputs, "draft_sha256": "b" * 64} if with_snapshot else None)
        assert (after["regenerations"], after["terminal_layer"]) == (0, None)


def test_retry_after_failure_counts_once_even_when_successful(tmp_path):
    path = tmp_path / "lesson-1.regeneration.yaml"
    inputs = {key: "a" * 64 for key in INPUT_KEYS}
    record_writer_call(path, "sample", 1, inputs)
    record_failure(path, "sample", 1, {"check": 1, "layer": "writer", "reason": "failure"}, inputs)
    assert record_writer_call(path, "sample", 1, inputs)["regenerations"] == 1
    after = record_success(path, "sample", 1, {**inputs, "draft_sha256": "b" * 64})
    assert (after["regenerations"], after["terminal_layer"]) == (1, None)
    assert record_writer_call(path, "sample", 1, inputs)["regenerations"] == 0
    failed = record_failure(path, "sample", 1, {"check": 1, "layer": "writer", "reason": "new failure"}, inputs)
    assert (failed["regenerations"], failed["terminal_layer"], len(failed["attempts"])) == (0, None, 1)


@pytest.mark.parametrize("changed_key", INPUT_KEYS)
@pytest.mark.parametrize("terminal", [False, True])
@pytest.mark.parametrize("record_call", [False, True])
def test_changed_inputs_start_fresh_failure_series(tmp_path, changed_key, terminal, record_call):
    path = tmp_path / "lesson-1.regeneration.yaml"
    inputs = {key: "a" * 64 for key in INPUT_KEYS}
    failure = {"check": 2, "layer": "writer", "reason": "writer failure"}
    record_failure(path, "sample", 1, failure, inputs)
    if terminal:
        assert record_failure(path, "sample", 1, failure, inputs)["terminal_layer"] == "plan"
    changed = {**inputs, changed_key: "b" * 64}
    if record_call:
        before = record_writer_call(path, "sample", 1, changed)
        assert (before["regenerations"], before["terminal_layer"]) == (0, None)
    after = record_failure(path, "sample", 1, failure, changed)
    assert (after["regenerations"], after["terminal_layer"], len(after["attempts"])) == (0, None, 1)
    assert record_failure(path, "sample", 1, failure, changed)["regenerations"] == 1


def test_module_rewrite_after_success_starts_each_call_at_one(module_build, monkeypatch):
    build, state, calls = module_build

    def successful_runner(*args, **kw):
        from tests.build.test_fresh_source_coverage import evaluated_writer_sources
        summary = evaluated_writer_sources(monkeypatch, *args[:3], **kw)
        expected = kw["expected_inputs"]
        inputs = {key: expected["style_card_sha256" if key == "card_sha256" else key] for key in INPUT_KEYS}
        inputs["draft_sha256"] = hashlib.sha256((state / "lesson-1.draft.yaml").read_bytes()).hexdigest()
        record_success(state / "lesson-1.regeneration.yaml", "sounds-letters-and-hello", 1, inputs)
        return {"passed": True, "manifest_sha256": "a" * 64,
                "checks": [{"check": 5, "status": "passed", "details": {"writer_sources": summary}}]}

    for number in range(4):
        report = build(successful=True, runner=successful_runner, prompt=f"fixture prompt {number}")
        assert report["complete"]
        assert report["lessons"][0]["regenerations"] == 0
        assert report["lessons"][0]["terminal_layer"] is None
        assert yaml.safe_load((state / "module.build.yaml").read_text(encoding="utf-8")) == report
    assert calls == [1, 1, 1, 1]


def test_runner_changed_inputs_restart_terminal_gap_series(tmp_path):
    draft = yaml.safe_load(_raw(2))
    inputs = dict(draft["inputs"])
    _run(tmp_path, draft, expected_inputs=inputs)
    _run(tmp_path, draft, expected_inputs=inputs)
    path = tmp_path / "lesson-1.regeneration.yaml"
    assert load_ledger(path, "sounds-letters-and-hello", 1)["terminal_layer"] == "pack"
    inputs["plan_sha256"] = "b" * 64
    draft["inputs"] = dict(inputs)
    bad = next(row for row in _run(tmp_path, draft, expected_inputs=inputs)["checks"] if row["status"] == "failed")
    assert (bad["check"], bad["layer"]) == (2, "pack")
    ledger = load_ledger(path, "sounds-letters-and-hello", 1)
    assert (ledger["regenerations"], ledger["terminal_layer"], len(ledger["attempts"])) == (0, "pack", 1)
