"""Writer reuse, bounded recovery and concurrent persistence regressions (#9525)."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest
import yaml

from scripts.build.fresh import regeneration, writer
from scripts.build.fresh.preflight import PreflightResult
from scripts.curriculum.evidence import lock

INPUTS = {key: "a" * 64 for key in regeneration.INPUT_KEYS}
SEAT = {"agent": "codex", "model": "gpt-6.1-sol", "effort": "high"}


def _record(store, task_id="stable", **updates):
    store.mkdir(exist_ok=True)
    result = store / f"{task_id}.result"
    result.write_text("readable but not validated")
    record = {**SEAT, "status": "done", "result_file": str(result), **updates}
    (store / f"{task_id}.json").write_text(json.dumps(record))
    return result


def _available(task_id="stable", **overrides):
    return writer._available_task_id(task_id, writer="codex", model="gpt-6.1-sol", effort="high", **overrides)


@pytest.mark.parametrize("archived", [False, True])
def test_fresh_legacy_same_seat_done_is_reusable(tmp_path, monkeypatch, archived):
    monkeypatch.setenv("LU_TASKS_DIR", str(tmp_path))
    store = tmp_path / "archive" if archived else tmp_path
    _record(store)
    assert _available() == ("stable", True)
    # Omitted model uses the current runtime registry default, not a historic pin.
    assert writer._available_task_id("stable", writer="codex", model=None, effort="high") == ("stable", True)


@pytest.mark.parametrize("status", ["done", "running", "spawning"])
@pytest.mark.parametrize("other", [{"agent": "agy"}, {"model": "another-model"}, {"resolved_model": "another-model"}])
def test_fresh_other_writer_never_reuses_legacy_record(tmp_path, monkeypatch, status, other):
    monkeypatch.setenv("LU_TASKS_DIR", str(tmp_path))
    _record(tmp_path, status=status, **other)
    before = (tmp_path / "stable.json").read_bytes()
    task_id, reuse = _available()
    assert task_id.startswith("stable-seat-") and not reuse
    assert _available() == (task_id, False)
    _record(tmp_path, task_id)
    assert _available() == (task_id, True)
    assert (tmp_path / "stable.json").read_bytes() == before


@pytest.mark.parametrize("updates", [{"agent": None}, {"model": "unknown"}, {"effort": None}, {"effort": "medium"}])
def test_fresh_unverified_identity_refuses_without_duplicate(tmp_path, monkeypatch, updates):
    monkeypatch.setenv("LU_TASKS_DIR", str(tmp_path))
    _record(tmp_path, **updates)
    with pytest.raises(writer.WriterHarnessError, match="unverified"):
        _available()
    assert len(list(tmp_path.glob("*.json"))) == 1


@pytest.mark.parametrize("kind", ["missing", "directory", "encoding", "permission", "no_path"])
@pytest.mark.parametrize("archived", [False, True])
def test_fresh_unreadable_done_advances_then_reuses_retry(tmp_path, monkeypatch, kind, archived):
    monkeypatch.setenv("LU_TASKS_DIR", str(tmp_path))
    store = tmp_path / "archive" if archived else tmp_path
    result = _record(store)
    if kind == "missing":
        result.unlink()
    elif kind == "directory":
        result.unlink()
        result.mkdir()
    elif kind == "encoding":
        result.write_bytes(b"\xff")
    elif kind == "permission":
        read_text = Path.read_text

        def deny(path, *args, **kwargs):
            if path == result:
                raise PermissionError("denied")
            return read_text(path, *args, **kwargs)

        monkeypatch.setattr(Path, "read_text", deny)
    else:
        _record(store, result_file=None)
    before = (store / "stable.json").read_bytes()
    assert _available() == ("stable-retry-1", False)
    _record(tmp_path, "stable-retry-1")
    assert _available() == ("stable-retry-1", True)
    assert (store / "stable.json").read_bytes() == before


def _dispatch_options(tmp_path):
    return dict(
        writer="codex",
        model="gpt-6.1-sol",
        effort="high",
        level="a1",
        slug="sample",
        lesson_n=1,
        prompt_file=tmp_path / "prompt.md",
        prompt_sha256=INPUTS["prompt_sha256"],
        inputs=INPUTS,
        output_dir=tmp_path,
        repo_root=tmp_path,
        preflight_result=PreflightResult(passed=True, status="ok", gaps=[], homographs=[], homograph_count=0),
    )


def test_fresh_direct_writer_stops_after_three_harness_failures(tmp_path, monkeypatch):
    monkeypatch.setenv("LU_TASKS_DIR", str(tmp_path / "tasks"))
    calls = []

    def fail(cmd, **kwargs):
        calls.append(cmd)
        raise OSError("cannot launch")

    monkeypatch.setattr(subprocess, "run", fail)
    for index in range(regeneration.MAX_HARNESS_FAILURES + 2):
        expected = "cannot launch" if index < 2 else regeneration.HARNESS_EXHAUSTED
        with pytest.raises(writer.WriterHarnessError, match=expected):
            writer.dispatch_writer(**_dispatch_options(tmp_path))
    assert len(calls) == 3
    path = tmp_path / "lesson-1.regeneration.yaml"
    evidence = regeneration.load_harness(path, "sample", 1)
    assert evidence["terminal_state"] == regeneration.HARNESS_EXHAUSTED
    assert len(evidence["failures"]) == 3
    assert not path.exists()
    assert lock.check(tmp_path / "lesson-1.writer-harness.yaml")


def test_fresh_content_failure_never_spends_harness_budget(tmp_path):
    def invalid(task_id, prompt, result):
        result.write_text("not a draft")

    for _ in range(4):
        with pytest.raises(writer.WriterCallError, match="not a YAML dictionary"):
            writer.dispatch_writer(**_dispatch_options(tmp_path), fake_seat=invalid)
    assert not (tmp_path / "lesson-1.writer-harness.yaml").exists()


def test_fresh_cap_survives_changed_inputs_and_does_not_change_ledger(tmp_path):
    path = tmp_path / "lesson-1.regeneration.yaml"
    regeneration.record_failure(path, "sample", 1, {"check": 1, "layer": "writer", "reason": "content"}, INPUTS)
    before = path.read_bytes()
    for index in range(3):
        current = {**INPUTS, "prompt_sha256": str(index) * 64}
        result = regeneration.record_harness_failure(path, "sample", 1, "transport", current)
    assert result["terminal_layer"] == "driver"
    evidence_path = tmp_path / "lesson-1.writer-harness.yaml"
    evidence_before = evidence_path.read_bytes()
    regeneration.record_harness_failure(path, "sample", 1, "fourth", INPUTS)
    assert evidence_path.read_bytes() == evidence_before
    assert path.read_bytes() == before
    assert regeneration.load_ledger(path, "sample", 1)["terminal_layer"] is None


@pytest.mark.parametrize("corruption", ["shape", "identity", "inputs", "timestamp", "timezone", "state", "digest"])
def test_fresh_sidecar_schema_identity_and_digest_fail_closed(tmp_path, corruption):
    path = tmp_path / "lesson-1.regeneration.yaml"
    regeneration.record_harness_failure(path, "sample", 1, "transport", INPUTS)
    evidence_path = tmp_path / "lesson-1.writer-harness.yaml"
    doc = yaml.safe_load(evidence_path.read_text())
    if corruption == "shape":
        doc["failures"] = {}
    elif corruption == "identity":
        doc["slug"] = "other"
    elif corruption == "inputs":
        doc["failures"][0]["inputs"]["prompt_sha256"] = "bad"
    elif corruption == "timestamp":
        doc["failures"][0]["at"] = "not a timestamp"
    elif corruption == "timezone":
        doc["failures"][0]["at"] = "2026-10-02T00:00:00"
    elif corruption == "state":
        doc["terminal_state"] = regeneration.HARNESS_EXHAUSTED
    if corruption == "digest":
        evidence_path.write_text("tampered")
    else:
        lock.write(evidence_path, lock.yaml_bytes(doc))
    before = evidence_path.read_bytes()
    with pytest.raises(ValueError):
        regeneration.record_harness_failure(path, "sample", 1, "next", INPUTS)
    assert evidence_path.read_bytes() == before


@pytest.mark.parametrize("count", [1, 3, 5])
def test_fresh_preschema_sidecar_retains_history_and_derives_cap(tmp_path, count):
    path = tmp_path / "lesson-1.regeneration.yaml"
    old = {
        "slug": "sample",
        "n": 1,
        "layer": "harness",
        "failures": [{"reason": "transport", "inputs": INPUTS, "at": "2026-10-02T00:00:00Z"} for _ in range(count)],
    }
    evidence_path = tmp_path / "lesson-1.writer-harness.yaml"
    lock.write(evidence_path, lock.yaml_bytes(old))
    evidence = regeneration.load_harness(path, "sample", 1)
    assert evidence["failures"] == old["failures"]
    assert evidence["terminal_state"] == (None if count < 3 else regeneration.HARNESS_EXHAUSTED)
    assert yaml.safe_load(evidence_path.read_text()) == old


@pytest.mark.parametrize("kind", ["harness", "regeneration"])
def test_fresh_concurrent_process_updates_preserve_both_rows(tmp_path, kind):
    path = tmp_path / "lesson-1.regeneration.yaml"
    script = """
import json, sys
from pathlib import Path
from scripts.build.fresh import regeneration
from scripts.build.fresh.regeneration import record_harness_failure, record_failure
import time
path, inputs, kind, check = Path(sys.argv[1]), json.loads(sys.argv[2]), sys.argv[3], int(sys.argv[4])
loader_name = '_load_harness' if kind == 'harness' else '_load_ledger'
loader = getattr(regeneration, loader_name)
def slow_load(*args, **kwargs):
    doc = loader(*args, **kwargs)
    time.sleep(0.2)  # Force overlapping read-modify-write windows without the mutex.
    return doc
setattr(regeneration, loader_name, slow_load)
if kind == 'harness':
    record_harness_failure(path, 'sample', 1, f'transport-{check}', inputs)
else:
    record_failure(path, 'sample', 1, {'check': check, 'layer': 'writer', 'reason': f'content-{check}'}, inputs)
"""
    processes = [
        subprocess.Popen(
            [sys.executable, "-c", script, str(path), json.dumps(INPUTS), kind, str(check)],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        for check in (1, 2)
    ]
    for process in processes:
        _, stderr = process.communicate(timeout=30)
        assert process.returncode == 0, stderr
    if kind == "harness":
        doc = regeneration.load_harness(path, "sample", 1)
        assert {row["reason"] for row in doc["failures"]} == {"transport-1", "transport-2"}
        evidence = path.with_name("lesson-1.writer-harness.yaml")
    else:
        doc = regeneration.load_ledger(path, "sample", 1)
        assert {row["failed_check"] for row in doc["attempts"]} == {1, 2}
        evidence = path
    assert lock.check(evidence)


@pytest.mark.parametrize("effort", [None, "high", "medium"])
def test_fresh_completed_draft_cache_binds_writer_and_effort(tmp_path, effort):
    from scripts.build.fresh.module import draft_matches_writer

    draft = tmp_path / "lesson-1.draft.yaml"
    meta = tmp_path / "lesson-1.writer.yaml"
    assert not draft_matches_writer(draft, "codex:gpt-6.1-sol", effort)
    meta.write_text(yaml.safe_dump({"writer": "codex", "model": "gpt-6.1-sol", "effort": "high"}))
    assert draft_matches_writer(draft, "codex:gpt-6.1-sol", effort) == (effort != "medium")
    assert not draft_matches_writer(draft, "agy:gpt-6.1-sol", effort)
    assert not draft_matches_writer(draft, "codex:another-model", effort)
    meta.write_text("[]")
    assert not draft_matches_writer(draft, "codex:gpt-6.1-sol", effort)
    meta.write_text("[")
    assert not draft_matches_writer(draft, "codex:gpt-6.1-sol", effort)
