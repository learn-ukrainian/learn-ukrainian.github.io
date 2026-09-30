"""The rate-limit reclassifier walks archived records too (#8625)."""

from __future__ import annotations

import json

import pytest

from scripts.maintenance import reclassify_dispatch_status as rds


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
    monkeypatch.setattr(rds, "_load_usage_by_task_id", lambda _usage_dir: {})

    outcome = rds.reclassify_rate_limited_tasks(tasks_dir=tasks, usage_dir=tmp_path / "usage", dry_run=True)

    assert seen == ["hot.json", "archive/old.json"]
    assert outcome["skipped"] == [("hot", "probe"), ("old", "probe")]


# #9275: a rate-limit false positive becomes ``done`` only when every completion
# gate the record calls for passes on the saved evidence.


class _OkAdapter:
    def parse_response(self, **_kwargs):
        return type("_Parse", (), {"ok": True, "rate_limited": False})()


@pytest.mark.parametrize(
    ("response", "fields", "expected"),
    [
        ("VERDICT: APPROVE\n", {"mode": "read-only", "require_review_verdict": True}, "done"),
        ("still waiting\n", {"mode": "read-only", "require_review_verdict": True}, "rate_limited"),
        ("pushed\n", {"mode": "danger", "commits_ahead": 1}, "done"),
        ("looked around\n", {"mode": "danger", "commits_ahead": 0}, "rate_limited"),
        ("pushed\n", {"mode": "danger", "commits_ahead": 1, "advisory_envelope": {}}, "rate_limited"),
        ("VERDICT: APPROVE\n", {"mode": "read-only", "failure_reason": "kimi_content_refused"}, "rate_limited"),
    ],
    ids=["verdict-passes", "verdict-missing", "delivered", "no-delivery", "advisory-unmeasurable", "recorded-failure"],
)
def test_reclassify_promotes_to_done_only_when_every_completion_gate_passes(
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

    outcome = rds._reclassify_task(path, usage_by_task_id={}, dry_run=False)

    assert json.loads(path.read_text())["status"] == expected
    assert outcome[0] == ("changed" if expected == "done" else "skipped")
    if expected != "done":
        assert "completion gate refuses done" in outcome[2]
