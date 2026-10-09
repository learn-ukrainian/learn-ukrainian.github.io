"""The rate-limit reclassifier walks archived records too (#8625)."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

from scripts.maintenance import reclassify_dispatch_status as rds
from scripts.orchestration import dead_worker_state


def test_reclassify_walks_hot_then_archived_records(tmp_path, monkeypatch):
    tasks = tmp_path / "tasks"
    (tasks / "archive").mkdir(parents=True)
    (tasks / "hot.json").write_text("{}", encoding="utf-8")
    (tasks / "archive" / "old.json").write_text("{}", encoding="utf-8")
    seen: list[str] = []

    def probe(path, **_kwargs):
        seen.append(str(path.relative_to(tasks)))
        return ("skipped", path.stem, "probe")

    monkeypatch.setattr(rds, "_reclassify_task", probe)
    monkeypatch.setattr(rds, "_load_usage_by_task_id", lambda _usage_dir, **_kwargs: {})

    outcome = rds.reclassify_rate_limited_tasks(tasks_dir=tasks, usage_dir=tmp_path / "usage", dry_run=True)

    assert seen == ["hot.json", "archive/old.json"]
    assert outcome["skipped"] == [("hot", "probe"), ("old", "probe")]
    assert outcome["unreadable"] == {"files": 0, "lines": 0, "records": 0}


@pytest.mark.parametrize("tasks_exist", [False, True])
def test_reclassify_outcomes_surface_unreadable_usage(tmp_path, tasks_exist):
    tasks = tmp_path / "tasks"
    if tasks_exist:
        tasks.mkdir()
    usage = tmp_path / "usage"
    usage.mkdir()
    (usage / "usage_codex-delegate_2026-08-22.jsonl").write_bytes(b'{}\n\xff\nnot-json\n[]\n{}\n')
    (usage / "usage_codex-delegate_2026-08-21.jsonl").mkdir()

    outcomes = rds.reclassify_rate_limited_tasks(tasks_dir=tasks, usage_dir=usage, dry_run=True)

    assert outcomes == {"changed": [], "skipped": [], "unreadable": {"files": 1, "lines": 3, "records": 0}}


@pytest.mark.parametrize("corrupt", [False, True])
@pytest.mark.parametrize("summary", ["empty", "dry_run", "changed"])
def test_main_prints_nonzero_unreadable_usage_in_each_summary(tmp_path, monkeypatch, capsys, corrupt, summary):
    tasks = tmp_path / "tasks"
    tasks.mkdir()
    if summary != "empty":
        (tasks / "task.json").write_text("{}", encoding="utf-8")
    monkeypatch.setattr(rds, "_reclassify_task", lambda *_args, **_kwargs: ("changed", "task", "probe"))
    usage = tmp_path / "usage"
    usage.mkdir()
    (usage / "usage_codex-delegate_2026-08-22.jsonl").write_bytes(b'{}\n\xff\n{}\n' if corrupt else b'{}\n')
    argv = ["reclassify_dispatch_status.py", "--tasks-dir", str(tasks), "--usage-dir", str(usage)]
    if summary == "dry_run":
        argv.append("--dry-run")
    monkeypatch.setattr(sys, "argv", argv)

    assert rds.main() == 0

    output = capsys.readouterr().out
    if corrupt:
        assert "Unreadable usage records: {'files': 0, 'lines': 1, 'records': 0}" in output
    else:
        assert "Unreadable usage records" not in output
    assert {
        "empty": "No task states changed.",
        "dry_run": "Dry run only. Proposed changes: 1",
        "changed": "Changed: 1",
    }[summary] in output


# #9275: a rate-limit false positive becomes ``done`` only for a delivery-only
# record whose delivery gate passes on the saved evidence; a gated record settles
# ``failed`` with ``recovery_requires_rerun`` (operator decision 2026-09-30).


class _OkAdapter:
    def parse_response(self, **_kwargs):
        return type("_Parse", (), {"ok": True, "rate_limited": False})()


RERUN = ("failed", "recovery_requires_rerun")


@pytest.mark.parametrize(
    ("response", "fields", "expected"),
    [
        ("VERDICT: APPROVE\n", {"mode": "read-only", "require_review_verdict": True}, RERUN),
        ("still waiting\n", {"mode": "read-only", "require_review_verdict": True}, RERUN),
        ("pushed\n", {"mode": "danger", "commits_ahead": 1}, ("done", None)),
        ("looked around\n", {"mode": "danger", "commits_ahead": 0}, ("rate_limited", None)),
        ("pushed\n", {"mode": "danger", "commits_ahead": 1, "advisory_envelope": {}}, RERUN),
        ("pushed\n", {"mode": "danger", "commits_ahead": 1, "advisory_exemption": {}}, RERUN),
        ("pushed\n", {"mode": "danger", "commits_ahead": 1, "leftovers_scan": "unknown"}, RERUN),
        (
            "pushed\n",
            {
                "mode": "danger",
                "commits_ahead": 1,
                "advisory_envelope": {},
                "failure_reason": "advisory_ceiling_exceeded",
            },
            ("failed", "advisory_ceiling_exceeded"),
        ),
        (
            "VERDICT: APPROVE\n",
            {"mode": "read-only", "failure_reason": "kimi_content_refused"},
            ("rate_limited", "kimi_content_refused"),
        ),
    ],
    ids=[
        "verdict-passes",
        "verdict-missing",
        "delivered",
        "no-delivery",
        "advisory-ceiling",
        "advisory-exemption",
        "leftovers-unknown",
        "gated-recorded-failure",
        "recorded-failure",
    ],
)
def test_reclassify_promotes_to_done_only_a_delivery_only_record_that_passes(
    tmp_path, monkeypatch, response, fields, expected
):
    monkeypatch.setattr(rds, "_load_adapter", lambda _agent: _OkAdapter())
    path = tmp_path / "task.json"
    (tmp_path / "task.result").write_text(response, encoding="utf-8")
    state = {
        "task_id": "task",
        "agent": "codex",
        "status": "rate_limited",
        "returncode": 0,
        "result_file": str(tmp_path / "task.result"),
        "response_chars": len(response),
        **fields,
    }
    path.write_text(json.dumps(state), encoding="utf-8")

    first = rds._reclassify_task(path, usage_by_task_id={}, dry_run=False)
    second = rds._reclassify_task(path, usage_by_task_id={}, dry_run=False)

    record = json.loads(path.read_text())
    assert (record["status"], record.get("failure_reason")) == expected
    if expected[0] == "rate_limited":
        assert first == second and first[0] == "skipped" and "completion gate refuses done" in first[2]
    else:
        # A repeated run leaves the settled record alone.
        assert (first[0], second) == ("changed", None)
        assert f"rate_limited -> {expected[0]}" in first[2]


@pytest.mark.parametrize("gated", [False, True])
def test_interrupted_reclassifier_replace_preserves_prior_record(tmp_path, monkeypatch, gated):
    monkeypatch.setattr(rds, "_load_adapter", lambda _agent: _OkAdapter())
    path = tmp_path / "task.json"
    state = {
        "task_id": "task",
        "agent": "codex",
        "status": "rate_limited",
        "returncode": 0,
        "mode": "danger",
        "commits_ahead": 1,
        "require_review_verdict": gated,
    }
    prior = (json.dumps(state, indent=4) + "\n").encode()
    path.write_bytes(prior)
    replacements = []

    def interrupt(source, target):
        assert Path(target) == path
        pending = json.loads(Path(source).read_text(encoding="utf-8"))
        assert pending["status"] == ("failed" if gated else "done")
        replacements.append(target)
        raise OSError("simulated interruption before replace")

    monkeypatch.setattr(dead_worker_state.os, "replace", interrupt)
    with pytest.raises(OSError, match="simulated interruption before replace"):
        rds._reclassify_task(path, usage_by_task_id={}, dry_run=False)
    assert replacements == [path]
    assert path.read_bytes() == prior
    assert path.with_suffix(".json.bak").read_bytes() == prior


def test_reclassifier_maps_mutation_field_name_and_uses_public_sink(tmp_path, monkeypatch):
    monkeypatch.setattr(rds, "_load_adapter", lambda _agent: _OkAdapter())
    path = tmp_path / "task.json"
    raw_reason = "synthetic diagnostic at private-worker.example.invalid"
    state = {
        "task_id": "task",
        "agent": "codex",
        "status": "rate_limited",
        "returncode": 0,
        "mode": "read-only",
        "require_review_verdict": True,
        "read_only_mutation_paths": ["example.txt"],
        "last_error": raw_reason,
    }
    path.write_text(json.dumps(state), encoding="utf-8")

    assert rds._reclassify_task(path, usage_by_task_id={}, dry_run=False)[0] == "changed"
    record = json.loads(path.read_text(encoding="utf-8"))
    assert record["status"] == "failed"
    assert record["failure_reason"] == "read_only_checkout_mutation"
    assert record["last_error"] == "unclassified_error"
    entries = [json.loads(line) for line in path.with_suffix(".diag").read_text(encoding="utf-8").splitlines()]
    assert any(entry["field"] == "last_error" and entry["diagnostic"] == raw_reason for entry in entries)
