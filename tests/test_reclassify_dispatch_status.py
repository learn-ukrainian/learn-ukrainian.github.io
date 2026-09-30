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
