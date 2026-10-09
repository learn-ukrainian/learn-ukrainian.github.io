"""Non-writer stops and cross-run paid-call reuse regressions (#9525)."""

from __future__ import annotations

import hashlib
import json
import subprocess
from functools import partial
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
    draft["lesson"]["module"] = f"{level}/{slug}"
    draft["inputs"].update({key: hashes[key] for key in ("plan_sha256", "pack_lock", "words_lock")})
    draft["inputs"]["style_card_sha256"] = hashlib.sha256((tmp_path / "docs/style-cards/a1.md").read_bytes()).hexdigest()
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
        lock.write(kw["output_dir"] / "lesson-1.writer.yaml", lock.yaml_bytes({
            "task_id": f"synthetic-writer-{len(dispatches)}", "attempt": kw["attempt"],
            "writer": kw["writer"], "model": kw["model"], "effort": "high",
            "prompt_sha256": kw["prompt_sha256"],
        }))

    def build(runner, writer_dispatch=delivered_writer):
        return module.build_module(
            level,
            slug,
            repo_root=tmp_path,
            lesson_n=1,
            writer_seat="codex:gpt-6.1-sol",
            writer_dispatch=writer_dispatch,
            runner=runner,
            runner_kwargs={"fixture_monkeypatch": monkeypatch},
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
    from tests.build.test_fresh_source_coverage import evaluated_writer_sources
    summary = evaluated_writer_sources(kw["fixture_monkeypatch"], *a[:3], **kw)
    inputs["draft_sha256"] = hashlib.sha256((kw["state_dir"] / "lesson-1.draft.yaml").read_bytes()).hexdigest()
    regeneration.record_success(kw["state_dir"] / "lesson-1.regeneration.yaml", a[1], 1, inputs)
    return {"passed": True, "manifest_sha256": "b" * 64,
            "checks": [{"check": 5, "status": "passed", "details": {"writer_sources": summary}}]}


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


def test_passed_runner_without_coverage_is_incomplete(context):
    report = context.build(lambda *a, **kw: {'passed': True, 'manifest_sha256': 'b' * 64})
    assert report['lessons'][0]['passed']
    assert not report['complete']
    assert report['lessons'][0]['writer_sources']['code'] == 'writer_sources_not_evaluated'
    assert report['lessons'][0]['writer_sources']['forms']['covered'] is None
    summary = report['lessons'][0]['writer_sources']
    assert summary['forms']['required'] > 0 and summary['evidence']['required'] > 0
    for group in ('forms', 'evidence'):
        for field in ('covered', 'missing', 'covered_sha256', 'missing_sha256'):
            assert summary[group][field] is None
    assert summary['noncredited_calls'] is None
    assert yaml.safe_load((context.state / 'module.build.yaml').read_text()) == report


def test_later_attempt_writer_stop_does_not_reuse_previous_coverage(context):
    from scripts.build.fresh.source_coverage import coverage_summary
    from scripts.build.fresh.writer import WriterCallError
    calls = []

    def write(**kw):
        calls.append(kw['attempt'])
        if len(calls) == 2:
            raise WriterCallError('current attempt stopped before check 5')
        lock.write(kw['output_dir'] / 'lesson-1.draft.yaml', lock.yaml_bytes(context.draft))

    def fail_after_coverage(*a, **kw):
        failure = {'check': 6, 'status': 'failed', 'layer': 'writer', 'reason': 'rewrite required'}
        regeneration.record_failure(kw['state_dir'] / 'lesson-1.regeneration.yaml', a[1], 1, failure, _inputs(kw))
        return {'passed': False, 'checks': [
            {'check': 5, 'status': 'passed', 'details': {'writer_sources': coverage_summary(
                {'previous-only'}, {}, {'form:previous-only'}, code=None)}}, failure]}

    report = context.build(fail_after_coverage, writer_dispatch=write)
    assert calls == [1, 2]
    row = report['lessons'][0]
    assert row['stopping_check'] == 1 and row['layer'] == 'writer'
    assert row['writer_sources']['code'] == 'writer_sources_not_evaluated'
    assert row['writer_sources']['forms']['covered'] is None
    assert row['writer_sources']['forms']['required_sha256'] != coverage_summary(
        {'previous-only'}, {}, set(), code=None)['forms']['required_sha256']
    assert not report['complete']
    assert yaml.safe_load((context.state / 'module.build.yaml').read_text()) == report


@pytest.mark.parametrize('draft_only', [False, True])
def test_unavailable_obligations_do_not_fabricate_zero(context, monkeypatch, draft_only):
    from scripts.build.fresh import source_coverage
    original = source_coverage.obligations

    def unavailable(draft, *a, **kw):
        if not draft_only or draft:
            raise ValueError('synthetic obligations unavailable')
        return original(draft, *a, **kw)

    monkeypatch.setattr(source_coverage, 'obligations', unavailable)
    report = context.build(lambda *a, **kw: {'passed': False, 'stopping_check': 5, 'layer': 'engine', 'reason': 'stop'})
    assert not report['complete']
    summary = report['lessons'][0]['writer_sources']
    if draft_only:
        assert summary['code'] == 'writer_sources_not_evaluated'
        assert summary['evidence']['required'] > 0
        assert summary['evidence']['covered'] is None
    else:
        assert summary is None
    assert yaml.safe_load((context.state / 'module.build.yaml').read_text()) == report


@pytest.mark.parametrize('mode', ['positive', 'coverage_exception', 'assembly_exception', 'missing', 'partial', 'later_writer_stop'])
def test_module_real_runner_writes_truthful_coverage(context, monkeypatch, mode):
    from scripts.build.fresh import assemble, runner, source_coverage
    from scripts.curriculum.learner_state.inventory_gate import GateReport
    from scripts.curriculum.resolver.inputs import Allowlist
    from tests.build.test_fresh_runner import _FixtureSources, _run_contract
    from tests.build.test_fresh_source_coverage import seal_writer, verification

    # Install the existing deterministic source/render dependencies, then run
    # the actual module -> run_lesson path with its own bound current receipt.
    setup = context.root / 'setup'
    setup.mkdir()
    draft, plan, pack, words = lesson_fixture()
    _run_contract(setup, monkeypatch, draft, plan, pack, words)
    real = source_coverage.check_coverage
    engine_calls = []
    monkeypatch.setattr(assemble.lesson_lock, 'compute_lesson_lock', lambda *a, **kw: {
        'lessons': [{'n': 1, 'entry_sha256': 'a' * 64}]})

    def coverage_error(*a, **kw):
        assert real(*a, **kw)['code'] is None, 'the receipt must be valid before the engine fails'
        raise ValueError('synthetic coverage engine failure')

    def assembly_error(*a, **kw):
        raise ValueError('synthetic assembly engine failure')

    def actual_runner(*a, **kw):
        kw.pop('fixture_monkeypatch')
        kw['draft']['lesson'] = {'module': f'{a[0]}/{a[1]}', 'n': a[2]}
        kw['draft']['inputs'].update({k: v for k, v in kw['expected_inputs'].items()
                                    if k in kw['draft']['inputs']})
        calls = [verification(['unrelated-form'])] if mode == 'partial' else None
        seal_writer(kw['state_dir'], monkeypatch, kw['draft'], kw['plan'], kw['pack'], kw['words'],
                    expected_inputs=kw['expected_inputs'], calls=calls,
                    prompt_bytes=(kw['state_dir'] / 'lesson-1.prompt.md').read_bytes())
        if mode == 'missing':
            (kw['state_dir'] / 'lesson-1.writer_tool_calls.json').unlink()
        with monkeypatch.context() as engine:
            if mode == 'coverage_exception':
                engine.setattr(source_coverage, 'check_coverage', coverage_error)
            elif mode == 'assembly_exception':
                engine.setattr(assemble, 'assemble_expanded_document', assembly_error)
            if mode == 'later_writer_stop':
                engine.setattr(runner, 'check_9_stress_and_render', lambda *a, **kw:
                    assemble.CheckResult(check=9, passed=False, layer='writer', reason='synthetic rewrite'))
            engine_calls.append(1)
            return runner.run_lesson(*a, **kw, sources=_FixtureSources(),
            allowlist=Allowlist.from_records(kw['words']['words'], words_lock='f' * 64),
            inventory_gate=lambda *a, **kw: GateReport('a1', context.slug, 1, ()),
            observed_writer=lambda *a, **kw: None,
            render_check=lambda *a, **kw: assemble.CheckResult(check=11, passed=True,
                artifacts={'verify_shippable': {'shippable': True}}))

    if mode == 'later_writer_stop':
        writer_calls = []

        def write(**kw):
            writer_calls.append(kw['attempt'])
            if len(writer_calls) > 1:
                raise writer.WriterCallError('current writer attempt stopped')
            lock.write(kw['output_dir'] / 'lesson-1.draft.yaml', lock.yaml_bytes(context.draft))

        report = context.build(actual_runner, writer_dispatch=write)
        assert writer_calls == [1, 2] and engine_calls == [1]
    else:
        report = context.build(actual_runner)
    row = report['lessons'][0]
    coverage = row['writer_sources']
    assert yaml.safe_load((context.state / 'module.build.yaml').read_text()) == report
    if mode == 'positive':
        assert report['complete'] and row['passed'], json.dumps(report)
        assert coverage['code'] is None and coverage['forms']['missing'] == 0
    elif mode == 'later_writer_stop':
        assert not report['complete'] and row['stopping_check'] == 1 and row['layer'] == 'writer'
        assert coverage['code'] == 'writer_sources_not_evaluated'
        assert coverage['forms']['required'] > 0 and coverage['forms']['covered'] is None
    else:
        assert not report['complete'] and not row['passed']
        assert row['stopping_check'] == 5, json.dumps(report)
        assert row['layer'] == ('writer' if mode == 'assembly_exception' else 'engine')
        if mode.endswith('exception'):
            assert 'raised' in row['reason']
            assert coverage['code'] == 'writer_sources_not_evaluated'
            assert coverage['forms']['required'] > 0
            assert coverage['forms']['covered'] is None
            assert coverage['forms']['missing'] is None
            assert coverage['noncredited_calls'] is None
        else:
            assert coverage['code'] == ('writer_sources_missing' if mode == 'missing'
                                         else 'writer_sources_forms_uncovered')
            assert coverage['forms']['missing'] > 0
            assert coverage['forms']['covered'] == 0
