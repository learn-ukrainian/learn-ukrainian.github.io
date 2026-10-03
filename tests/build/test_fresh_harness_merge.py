"""Shared writer/environment harness accounting after merging #9525 and #9544."""

from functools import partial

import pytest

from scripts.build.fresh import regeneration, writer
from scripts.curriculum.evidence import lock
from tests.build.test_fresh_regeneration_layers import _inputs, _success
from tests.build.test_fresh_regeneration_layers import context as context


def test_harness_check_and_dispatch_share_cap_without_touching_writer_ledger(tmp_path):
    path = tmp_path / "lesson-1.regeneration.yaml"
    inputs = {key: "a" * 64 for key in regeneration.INPUT_KEYS}
    regeneration.record_failure(path, "sample", 1, {"check": 3, "layer": "writer", "reason": "content"}, inputs)
    regeneration.record_writer_call(path, "sample", 1, inputs)
    before = path.read_bytes()
    regeneration.record_harness_failure(path, "sample", 1, "dispatch unavailable", inputs)
    for index in range(2):
        stopped = regeneration.record_failure(
            path, "sample", 1, {"check": 11, "layer": "harness", "reason": "environment unavailable"}, inputs
        )
        assert stopped["regenerations"] == 1
        assert stopped["terminal_layer"] == ("driver" if index == 1 else None)
    evidence = regeneration.load_harness(path, "sample", 1)
    assert evidence["layer"] == "harness"
    assert evidence["terminal_state"] == regeneration.HARNESS_EXHAUSTED
    assert len(evidence["failures"]) == 3
    assert path.read_bytes() == before and lock.check(path)


def test_harness_check_with_partial_inputs_keeps_schema_valid_and_caps(tmp_path):
    path = tmp_path / "lesson-1.regeneration.yaml"
    for _ in range(4):
        regeneration.record_failure(
            path, "sample", 1, {"check": 11, "layer": "harness", "reason": "environment unavailable"}, {}
        )
    evidence = regeneration.load_harness(path, "sample", 1)
    assert len(evidence["failures"]) == 3
    assert evidence["terminal_state"] == regeneration.HARNESS_EXHAUSTED
    assert evidence["failures"][0]["inputs"] == {key: "0" * 64 for key in regeneration.INPUT_KEYS}
    assert not path.exists()


@pytest.mark.parametrize("runner_records", [False, True])
@pytest.mark.parametrize("gate_row", [False, True])
def test_module_environment_failure_counts_once_and_stops_cached_checks(context, runner_records, gate_row):
    dispatches, checks = [], []

    def deliver(task_id, prompt, result):
        dispatches.append(task_id)
        result.write_bytes(lock.yaml_bytes(context.draft))

    def failed_check(*args, **kwargs):
        checks.append(1)
        failure = {"check": 11, "status": "failed", "layer": "harness", "reason": "environment unavailable"}
        if runner_records:
            regeneration.record_failure(
                context.state / "lesson-1.regeneration.yaml", context.slug, 1, failure, _inputs(kwargs)
            )
        report = {"passed": False, "passed_through": 11, "layer": "harness", "reason": failure["reason"]}
        if gate_row:
            report["checks"] = [failure]
        return report

    real_writer = partial(writer.dispatch_writer, fake_seat=deliver)
    assert context.build(_success, real_writer)["complete"]
    for index in range(5):
        report = context.build(failed_check, real_writer)
        lesson = report["lessons"][0]
        assert not report["complete"]
        assert lesson["layer"] == "harness"
        assert lesson["regenerations"] == 0
        assert lesson["terminal_layer"] == ("driver" if index >= 2 else None)
        assert lesson["reason"] == (regeneration.HARNESS_EXHAUSTED if index >= 2 else "environment unavailable")
        evidence = regeneration.load_harness(context.state / "lesson-1.regeneration.yaml", context.slug, 1)
        assert len(evidence["failures"]) == min(index + 1, 3)
    assert dispatches and len(dispatches) == 1
    assert checks == [1, 1, 1]
    ledger = regeneration.load_ledger(context.state / "lesson-1.regeneration.yaml", context.slug, 1)
    assert ledger["attempts"] == [] and ledger["regenerations"] == 0
    assert ledger["terminal_layer"] is None
