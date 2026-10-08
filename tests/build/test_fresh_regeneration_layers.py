"""Non-writer stops and cross-run paid-call reuse regressions (#9525)."""

from __future__ import annotations

import hashlib
import json
import subprocess
from functools import partial
from types import SimpleNamespace

import pytest

from scripts.build.fresh import cli, module, regeneration, writer
from scripts.build.fresh.preflight import PreflightResult
from scripts.curriculum.evidence import lock
from tests.build.test_fresh_e3b2 import _fixture as module_fixture
from tests.build.test_fresh_runner import _fixture as lesson_fixture


@pytest.fixture
def context(tmp_path, monkeypatch):
    level, slug, plans, evidence, state, _ = module_fixture(tmp_path)
    draft, plan, pack, words = lesson_fixture()
    paths = {
        "plan": plans / f"{slug}.yaml",
        "pack": evidence / f"{slug}.yaml",
        "words": evidence / "_words.yaml",
        "state_dir": evidence / "_state",
    }
    hashes = {
        key: "a" * 64
        for key in ("plan_sha256", "pack_lock", "words_lock", "lesson_lock_entry_sha256", "learner_state_sha256")
    }
    monkeypatch.setattr(cli, "_load_lesson_data", lambda *a, **kw: (plan, plan["lessons"][0], pack, words, paths))
    monkeypatch.setattr(cli, "_compute_input_hashes", lambda *a: hashes.copy())
    monkeypatch.setattr(cli, "_load_cited_records", lambda *a: {})
    monkeypatch.setattr(module, "planned_state", lambda *a, **kw: object())
    monkeypatch.setattr(module, "render_lesson_prompt", lambda *a, **kw: "fixture prompt")
    monkeypatch.setattr(module, "check_rendered_prompt", lambda *a, **kw: SimpleNamespace(passed=True))
    monkeypatch.setattr(module, "lesson_immersion_payload", lambda *a, **kw: {})
    monkeypatch.setattr(
        module,
        "preflight_lesson",
        lambda *a, **kw: PreflightResult(passed=True, status="ok", gaps=[], homographs=[], homograph_count=0),
    )
    dispatches = []

    def delivered_writer(**kw):
        dispatches.append(kw["attempt"])
        lock.write(kw["output_dir"] / "lesson-1.draft.yaml", lock.yaml_bytes(draft))

    def build(runner, writer_dispatch=delivered_writer):
        return module.build_module(
            level,
            slug,
            repo_root=tmp_path,
            lesson_n=1,
            writer_seat="codex:gpt-6.1-sol",
            writer_dispatch=writer_dispatch,
            runner=runner,
        )

    return SimpleNamespace(
        build=build, state=state, paths=paths, slug=slug, draft=draft, dispatches=dispatches, root=tmp_path
    )


def _inputs(kw):
    return regeneration.writer_inputs(
        kw["expected_inputs"], kw["expected_inputs"]["style_card_sha256"], kw["expected_inputs"]["prompt_sha256"]
    )


def _success(*a, **kw):
    inputs = _inputs(kw)
    inputs["draft_sha256"] = hashlib.sha256((kw["state_dir"] / "lesson-1.draft.yaml").read_bytes()).hexdigest()
    regeneration.record_success(kw["state_dir"] / "lesson-1.regeneration.yaml", a[1], 1, inputs)
    return {"passed": True, "manifest_sha256": "b" * 64}


@pytest.mark.parametrize("layer", ["engine", "plan", "pack", "word_store", "driver"])
@pytest.mark.parametrize("runner_records", [False, True])
def test_fresh_non_writer_check_stops_without_regeneration(context, layer, runner_records):
    calls = []
    failure = {"check": 9, "status": "failed", "layer": layer, "reason": "span_location_unrendered"}

    def failing_runner(*a, **kw):
        calls.append(1)
        if runner_records:
            regeneration.record_failure(
                kw["state_dir"] / "lesson-1.regeneration.yaml", context.slug, 1, failure, _inputs(kw)
            )
        return {"passed": False, "checks": [failure]}

    report = context.build(failing_runner)
    lesson = report["lessons"][0]
    assert not report["complete"]
    assert lesson["terminal_layer"] == lesson["layer"] == layer
    assert lesson["regenerations"] == 0
    assert lesson["reason"] == failure["reason"]
    assert lesson["stopping_check"] == 9
    assert context.dispatches == [1] and calls == [1]
    ledger_path = context.state / "lesson-1.regeneration.yaml"
    ledger = regeneration.load_ledger(ledger_path, context.slug, 1)
    assert ledger["terminal_layer"] == layer
    assert ledger["regenerations"] == 0
    assert len(ledger["attempts"]) == 1
    assert lock.check(ledger_path)
    assert not (context.state / "lesson-1.writer-harness.yaml").exists()
    before = ledger_path.read_bytes()
    assert context.build(failing_runner) == report
    assert context.dispatches == [1] and calls == [1]
    assert ledger_path.read_bytes() == before


@pytest.mark.parametrize("layer_field", [{}, {"layer": None}])
def test_fresh_check_12_without_failed_gate_stops_as_engine(context, layer_field):
    report = context.build(
        lambda *a, **kw: {
            "passed": False,
            "checks": [],
            "stopping_check": 12,
            "reason": "manifest_error",
            **layer_field,
        }
    )
    lesson = report["lessons"][0]
    assert lesson["terminal_layer"] == lesson["layer"] == "engine"
    assert lesson["regenerations"] == 0
    assert lesson["stopping_check"] == 12
    assert context.dispatches == [1]
    ledger = regeneration.load_ledger(context.state / "lesson-1.regeneration.yaml", context.slug, 1)
    assert ledger["terminal_layer"] == "engine"
    assert ledger["attempts"][0]["failed_check"] == 12


def test_fresh_schema_invalid_reply_charges_content_ledger_only(context):
    calls = []

    def invalid(task_id, prompt, result):
        calls.append(task_id)
        result.write_text("a: 1")

    real_writer = partial(writer.dispatch_writer, fake_seat=invalid)
    for index in range(2):
        report = context.build(_success, real_writer)
        lesson = report["lessons"][0]
        assert not report["complete"]
        assert lesson["layer"] == "writer"
        assert regeneration.HARNESS_EXHAUSTED not in lesson["reason"]
        ledger = regeneration.load_ledger(context.state / "lesson-1.regeneration.yaml", context.slug, 1)
        assert len(ledger["attempts"]) == index + 1
        assert {row["failed_check"] for row in ledger["attempts"]} == {1}
        assert not (context.state / "lesson-1.writer-harness.yaml").exists()
    assert len(calls) == 2
    assert ledger["terminal_layer"] == "plan"
    resumed = context.build(_success, real_writer)
    assert resumed["lessons"][0]["terminal_layer"] == "plan"
    assert regeneration.HARNESS_EXHAUSTED not in resumed["lessons"][0]["reason"]
    assert len(calls) == 2


@pytest.mark.parametrize("status", ["rate_limited", "timeout"])
def test_fresh_module_capacity_failure_is_not_recharged(context, status):
    calls = []

    def unavailable(task_id, prompt, result):
        calls.append(task_id)
        result.with_suffix(".json").write_text(json.dumps({"status": status}))

    for _ in range(4):
        report = context.build(_success, partial(writer.dispatch_writer, fake_seat=unavailable))
        lesson = report["lessons"][0]
        assert not report["complete"] and status in lesson["reason"]
        assert lesson["layer"] == "engine" and lesson["terminal_layer"] is None
        assert lesson["regenerations"] == 0
        assert not (context.state / "lesson-1.writer-harness.yaml").exists()
    assert len(calls) == 4


def test_fresh_module_caller_failure_is_not_recharged(context):
    def mistyped(**kwargs):
        return writer.dispatch_writer(**{**kwargs, "writer": "codeex"})

    for _ in range(3):
        report = context.build(_success, mistyped)
        lesson = report["lessons"][0]
        assert "Invalid writer" in lesson["reason"]
        assert lesson["terminal_layer"] is None and lesson["regenerations"] == 0
        assert not (context.state / "lesson-1.writer-harness.yaml").exists()
    calls = []

    def corrected(task_id, prompt, result):
        calls.append(task_id)
        result.write_bytes(lock.yaml_bytes(context.draft))

    assert context.build(_success, partial(writer.dispatch_writer, fake_seat=corrected))["complete"]
    assert len(calls) == 1
    assert not (context.state / "lesson-1.writer-harness.yaml").exists()


@pytest.mark.parametrize("layer", ["engine", "plan", "pack", "word_store", "driver"])
def test_fresh_non_writer_failure_preserves_spent_budget(tmp_path, layer):
    path = tmp_path / "lesson-1.regeneration.yaml"
    inputs = {key: "a" * 64 for key in regeneration.INPUT_KEYS}
    regeneration.record_failure(path, "sample", 1, {"check": 3, "layer": "writer", "reason": "structure"}, inputs)
    delivered = regeneration.record_writer_call(path, "sample", 1, inputs)
    assert delivered["regenerations"] == 1
    failure = {"check": 9, "layer": layer, "reason": "upstream"}
    stopped = regeneration.record_failure(path, "sample", 1, failure, inputs)
    assert stopped["regenerations"] == 1
    assert stopped["terminal_layer"] == layer
    before = path.read_bytes()
    assert regeneration.record_writer_call(path, "sample", 1, inputs) == stopped
    assert regeneration.record_failure(path, "sample", 1, failure, inputs) == stopped
    assert path.read_bytes() == before and lock.check(path)
    # Changed input bytes remain the established way to start a new series.
    changed = {**inputs, "pack_lock": "b" * 64}
    reset = regeneration.record_writer_call(path, "sample", 1, changed)
    assert reset["terminal_layer"] is None
    assert reset["attempts"] == [] and reset["regenerations"] == 0
    assert lock.check(path)


def test_fresh_real_runner_check_9_is_terminal_on_first_failure(tmp_path, monkeypatch):
    from scripts.build.fresh import assemble, runner
    from tests.build.test_fresh_runner import _run_contract

    draft, plan, pack, words = lesson_fixture()
    monkeypatch.setattr(
        runner,
        "check_9_stress_and_render",
        lambda *a, **kw: assemble.CheckResult(check=9, passed=False, reason="span_location_unrendered", layer="engine"),
    )
    report, state, _ = _run_contract(tmp_path, monkeypatch, draft, plan, pack, words)
    failure = next(row for row in report["checks"] if row["status"] == "failed")
    assert failure["check"] == 9 and failure["layer"] == "engine"
    path = state / "lesson-1.regeneration.yaml"
    ledger = regeneration.load_ledger(path, "sample-slug", 1)
    assert ledger["terminal_layer"] == "engine" and ledger["regenerations"] == 0
    assert len(ledger["attempts"]) == 1 and lock.check(path)


def test_fresh_writer_check_still_regenerates(context):
    calls = []

    def runner(*a, **kw):
        calls.append(1)
        if len(calls) == 1:
            failure = {"check": 3, "status": "failed", "layer": "writer", "reason": "step_ids_or_order"}
            regeneration.record_failure(
                kw["state_dir"] / "lesson-1.regeneration.yaml", context.slug, 1, failure, _inputs(kw)
            )
            return {"passed": False, "checks": [failure]}
        return _success(*a, **kw)

    report = context.build(runner)
    assert report["complete"]
    assert report["lessons"][0]["regenerations"] == 1
    assert report["lessons"][0]["terminal_layer"] is None
    assert context.dispatches == [1, 2] and calls == [1, 1]
    assert lock.check(context.state / "lesson-1.regeneration.yaml")
    assert not (context.state / "lesson-1.writer-harness.yaml").exists()


@pytest.mark.parametrize("failure_layer", [None, "writer", "engine"])
def test_fresh_state_rerun_reuses_done_attempts_without_paid_dispatch(context, monkeypatch, failure_layer):
    tasks = context.root / "batch_state/tasks"
    tasks.mkdir(parents=True)
    monkeypatch.setenv("LU_TASKS_DIR", str(tasks))
    paid = []
    waits = []

    def harness(cmd, **kwargs):
        if cmd[2] == "dispatch":
            task_id = cmd[cmd.index("--task-id") + 1]
            paid.append(task_id)
            result = tasks / f"{task_id}.result"
            result.write_bytes(lock.yaml_bytes(context.draft))
            record = {
                "status": "done",
                "agent": "codex",
                "model": "gpt-6.1-sol",
                "effort": "high",
                "result_file": str(result),
            }
            (tasks / f"{task_id}.json").write_text(json.dumps(record))
            return subprocess.CompletedProcess(cmd, 0, stdout="", stderr="")
        assert cmd[2] == "wait"
        waits.append(cmd[3])
        return subprocess.CompletedProcess(cmd, 0, stdout=(tasks / f"{cmd[3]}.json").read_text(), stderr="")

    monkeypatch.setattr(writer, "_run_harness", harness)
    real_writer = partial(writer.dispatch_writer, effort="high")

    def runner(*a, **kw):
        ledger_path = kw["state_dir"] / "lesson-1.regeneration.yaml"
        if failure_layer == "engine" or (
            failure_layer == "writer" and not regeneration.load_ledger(ledger_path, context.slug, 1)["attempts"]
        ):
            failure = {"check": 6, "status": "failed", "layer": failure_layer, "reason": "fixture failure"}
            regeneration.record_failure(ledger_path, context.slug, 1, failure, _inputs(kw))
            return {"passed": False, "checks": [failure]}
        return _success(*a, **kw)

    first = context.build(runner, real_writer)
    assert first["complete"] == (failure_layer != "engine")
    count = 2 if failure_layer == "writer" else 1
    assert len(paid) == len(waits) == count
    records_before = {path: path.read_bytes() for path in tasks.iterdir()}
    # Change only the ephemeral output directory: no ledger, draft or sidecar is copied.
    context.paths["state_dir"] = context.paths["state_dir"].with_name("_fresh_state")
    fresh_state = context.paths["state_dir"] / context.slug
    assert not fresh_state.exists()
    second = context.build(runner, real_writer)
    assert second == first
    assert len(paid) == count
    assert waits == paid + paid
    assert {path: path.read_bytes() for path in tasks.iterdir()} == records_before
    ledger_path = fresh_state / "lesson-1.regeneration.yaml"
    assert lock.check(ledger_path)
    ledger = regeneration.load_ledger(ledger_path, context.slug, 1)
    assert ledger["regenerations"] == int(failure_layer == "writer")
    assert ledger["terminal_layer"] == ("engine" if failure_layer == "engine" else None)
    assert not (fresh_state / "lesson-1.writer-harness.yaml").exists()
