"""Non-writer stops and cross-run paid-call reuse regressions (#9525)."""

from __future__ import annotations

import hashlib
import json
import subprocess
from functools import partial
from pathlib import Path
from types import SimpleNamespace

import pytest
import yaml

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
        build=build,
        state=state,
        paths=paths,
        slug=slug,
        draft=draft,
        dispatches=dispatches,
        root=tmp_path,
        plan=plan,
        pack=pack,
        words=words,
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


@pytest.mark.parametrize("change", [None, "draft", "inputs", "writer_seat", "effort"])
def test_requires_pause_and_resume_keeps_writer_draft(context, monkeypatch, change):
    from scripts.build.fresh import assemble, runner
    from scripts.curriculum.learner_state.inventory_gate import GateReport
    from scripts.curriculum.resolver.inputs import Allowlist
    from tests.build.test_fresh_runner import _complete_a1_choice_fixture, _confirm_fixture_form, _FixtureSources

    draft, plan, words = context.draft, context.plan, context.words
    form = {**words["words"][0]["forms"][0], "form": "слова", "stressed": "слова\u0301", "tags": "noun:inanim:n:v_rod"}
    words["words"][0]["forms"].append(form)
    plan["lessons"][0]["inventory"]["vocabulary"]["core"][0]["forms"].append(form["tags"])
    plan["lessons"][0]["steps"][0]["practice"] = ["a1"]
    plan["lessons"][0]["activities"] = [{"id": "a1", "type": "fill-in", "placement": "inline", "focus": "Forms"}]
    draft["steps"][0]["blocks"].append({"kind": "activity", "ref": "a1"})
    draft["activities"] = [
        {
            "id": "a1",
            "instruction": "Choose",
            "items": [
                {
                    "sentence": "____",
                    "answer": "слово",
                    "options": ["слово", "слова"],
                    "explanation": "Choose",
                    "mode": "form-choice",
                    "record": "W-1",
                    "answer_tags": words["words"][0]["forms"][0]["tags"],
                }
            ],
        }
    ]
    _complete_a1_choice_fixture(draft, plan, context.pack, words)
    allowlist = Allowlist.from_records(words["words"], words_lock="f" * 64)
    monkeypatch.setattr(
        assemble, "planned_state", lambda *a, **kw: SimpleNamespace(cumulative_core_count=10, waiver=None)
    )
    monkeypatch.setattr(assemble.lesson_lock, "check_lesson_lock", lambda *a, **kw: (True, ""))
    monkeypatch.setattr(
        assemble.lesson_lock, "compute_lesson_lock", lambda *a, **kw: {"lessons": [{"n": 1, "entry_sha256": "a" * 64}]}
    )
    monkeypatch.setattr(assemble, "compute_lesson_immersion_band", lambda **kw: SimpleNamespace(band_key="a1"))
    monkeypatch.setattr(runner, "write_manifest", lambda *a, **kw: ({"recap": False}, "b" * 64))

    def delivered(**kw):
        context.dispatches.append(kw["attempt"])
        draft["lesson"] = {"module": f"a1/{context.slug}", "n": 1}
        draft["inputs"].update(
            {
                **kw["inputs"],
                "style_card_sha256": kw["inputs"]["card_sha256"],
                "lesson_lock_entry_sha256": "a" * 64,
                "learner_state_sha256": "a" * 64,
            }
        )
        draft["inputs"].pop("card_sha256")
        draft["inputs"].pop("prompt_sha256")
        lock.write(context.state / "lesson-1.draft.yaml", lock.yaml_bytes(draft))
        (context.state / "lesson-1.writer.yaml").write_text("writer: codex\nmodel: gpt-6.1-sol\neffort: high\n")

    def actual(*a, **kw):
        return runner.run_lesson(
            *a,
            **kw,
            sources=_FixtureSources(),
            allowlist=allowlist,
            inventory_gate=lambda *a, **kw: GateReport("a1", context.slug, 1, ()),
            observed_writer=lambda *a, **kw: None,
            render_check=lambda *a, **kw: assemble.CheckResult(
                check=11, passed=True, artifacts={"verify_shippable": {"shippable": True}}
            ),
        )

    writer_dispatch = partial(delivered, effort="high")
    first = context.build(actual, writer_dispatch)
    assert not first["complete"]
    paused = first["lessons"][0]
    assert paused["reason"].startswith("awaiting_requires_confirmation:")
    assert "lesson-1.requires-questions.yaml" in paused["reason"]
    assert "lesson-1.requires-confirm.prompt.md" in paused["reason"]
    assert paused["terminal_layer"] is None and paused["regenerations"] == 0
    assert context.dispatches == [1]
    original = (context.state / "lesson-1.draft.yaml").read_bytes()
    assert context.build(actual, writer_dispatch) == first
    assert context.dispatches == [1]
    _confirm_fixture_form(context.state, draft["activities"][0]["items"][0])
    if change == "draft":
        draft["steps"][0]["blocks"][0]["text"] += " слово"
        lock.write(context.state / "lesson-1.draft.yaml", lock.yaml_bytes(draft))
    elif change == "inputs":
        hashes = cli._compute_input_hashes(None, None, None)
        monkeypatch.setattr(cli, "_compute_input_hashes", lambda *a: {**hashes, "plan_sha256": "c" * 64})
    elif change in {"writer_seat", "effort"}:
        path = context.state / "lesson-1.writer.yaml"
        meta = yaml.safe_load(path.read_text())
        meta["model" if change == "writer_seat" else "effort"] = "gpt-6-luna" if change == "writer_seat" else "xhigh"
        path.write_text(yaml.safe_dump(meta))
    resumed = context.build(actual, writer_dispatch)
    if change in {"draft", "inputs"}:
        assert not resumed["complete"]
        assert resumed["lessons"][0]["reason"] == "requires_receipt_stale"
        assert "awaiting_requires" not in regeneration.load_ledger(
            context.state / "lesson-1.regeneration.yaml", context.slug, 1
        )
    else:
        assert resumed["complete"], resumed
        assert context.dispatches == ([1, 1] if change else [1])
        assert (context.state / "lesson-1.draft.yaml").read_bytes() == original
        gates = yaml.safe_load((context.state / "lesson-1.gates.yaml").read_text())
        assert gates["checks"][6]["status"] == "passed"


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
                "schema_version": 2,
                "task_id": task_id,
                "run_nonce": "n1",
                "status": "done",
                "agent": "codex",
                "model": "gpt-6.1-sol",
                "effort": "high",
                "result_file": str(result),
                "prompt_sha256": hashlib.sha256(Path(cmd[cmd.index("--prompt-file") + 1]).read_bytes()).hexdigest(),
                "result_sha256": hashlib.sha256(result.read_bytes()).hexdigest(),
            }
            (tasks / f"{task_id}.json").write_text(json.dumps(record))
            return subprocess.CompletedProcess(cmd, 0, stdout=f"{task_id}\nn1\n", stderr="")
        assert cmd[2] == "wait"
        assert cmd[cmd.index("--run-nonce") + 1] == "n1"
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
