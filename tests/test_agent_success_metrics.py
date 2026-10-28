"""Hand-counted hot/archive cohorts and content-free public metrics (#10468)."""

from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest

from scripts.fleet.agent_success import main
from scripts.fleet_comms.agent_success_metrics import collect_agent_success

NOW = datetime(2026, 10, 28, 12, tzinfo=UTC)
FIXTURE = Path(__file__).parent / "fixtures/fleet/agent_success.json"


def _write(root: Path, record: dict, *, filename: str | None = None) -> Path:
    record = {"schema_version": 2, "mode": "workspace-write", "run_nonce": "run", "repo": "public", **record}
    root.mkdir(parents=True, exist_ok=True)
    path = root / (filename or record["task_id"] + ".json")
    text = record.pop("result", None)
    if text is not None:
        result = path.with_suffix(".result")
        result.write_text(text)
        record.update(result_file=str(result), result_sha256=hashlib.sha256(text.encode()).hexdigest())
    path.write_text(json.dumps(record))
    return path


@pytest.fixture
def ledger(tmp_path):
    fixture = json.loads(FIXTURE.read_text())
    for source, records in fixture.items():
        root = tmp_path / "archive" if source == "archive" else tmp_path
        for i, record in enumerate(records):
            _write(root, record, filename=f"{i:02}.json")
    return tmp_path


def test_hand_counted_model_agent_and_window_denominators(ledger):
    """Hot/archive copies must not inflate counts or lose separate nonces/statuses."""
    report = collect_agent_success(tasks_dir=ledger, until=NOW)
    assert report["complete"] is True
    assert report["tasks"] == 21
    assert report["coverage"]["duplicate_runs"] == 1
    assert report["coverage"]["outside_window"] == 1
    assert {k: v["tasks"] for k, v in report["by_agent"].items()} == {
        "codex": 9,
        "cursor": 2,
        "muse": 3,
        "claude": 3,
        "agy": 2,
        "other": 2,
    }
    assert {k: v["tasks"] for k, v in report["by_model"].items()} == {
        "gpt-6.1-terra": 5,
        "gpt-6.1-sol": 3,
        "muse-wonder-full-1.0": 3,
        "claude-opus-5-5": 2,
        "claude-sonnet-5-5": 1,
        "gemini-3.8-flash-high": 2,
        "retired-example-1": 1,
        "unknown": 1,
        "gpt-6-luna": 1,
        "grok-4.7": 2,
    }
    cursor = report["by_model"]["grok-4.7"]
    assert cursor["status"]["done"] == 1 and cursor["status"]["cancelled"] == 1
    assert cursor["terminal_success"] == {"numerator": 1, "denominator": 2, "percent": 50.0}
    assert cursor["model_sources"] == {"requested": 1, "resolved": 1}
    assert "grok-4.7-high" not in report["by_model"]
    terra = report["by_model"]["gpt-6.1-terra"]
    assert terra["status"] == {
        "done": 1,
        "no_deliverable": 2,
        "failed": 1,
        "timeout": 0,
        "rate_limited": 0,
        "cancelled": 0,
        "crashed": 0,
        "needs_finalize": 0,
        "running": 0,
        "spawning": 1,
        "unknown": 0,
    }
    assert terra["success"] == {"numerator": 1, "denominator": 5, "percent": 20.0}
    assert terra["terminal_success"] == {"numerator": 1, "denominator": 4, "percent": 25.0}
    assert terra["median_wall_seconds"] == {"value": 90.0, "observed": 4, "unknown": 0}
    assert terra["no_deliverable_reasons"]["outside_owned_paths"] == 1
    assert terra["failure_classes"]["stream"] == 1
    assert report["by_model"]["gpt-6.1-sol"]["no_deliverable_reasons"]["unknown"] == 1
    assert report["by_agent"]["agy"]["failure_classes"]["unknown"] == 1
    assert collect_agent_success(tasks_dir=ledger, until=NOW, since=NOW - timedelta(days=1))["tasks"] == 14
    assert collect_agent_success(tasks_dir=ledger, until=NOW, since=NOW - timedelta(days=14))["tasks"] == 22


def test_muse_reviews_tokens_and_missing_delivery_evidence(ledger):
    """Adapter usage is nested; a review's target PR and an approval never prove a merge."""
    report = collect_agent_success(tasks_dir=ledger, until=NOW)
    muse = report["by_model"]["muse-wonder-full-1.0"]
    assert muse["tokens"]["input_tokens"] == {"value": 170, "observed": 2, "unknown": 1}
    assert muse["tokens"]["output_tokens"]["value"] == 35
    assert muse["tokens"]["cache_read_tokens"]["value"] == 30
    assert muse["tokens"]["total_tokens"]["value"] == "unknown"
    assert "child-other-model" not in report["by_model"]
    reviews = muse["reviews"]
    assert reviews["verdicts"] == {"APPROVED": 2, "CHANGES_REQUESTED": 1, "BLOCKED": 0, "unknown": 0}
    assert reviews["rounds_to_approval"] == {"value": 2, "observed": 1, "unknown": 1}
    assert reviews["findings"] == {"value": 9, "observed": 2, "unknown": 1}
    assert reviews["finding_severities"] == {
        "P0": 1,
        "P1": 2,
        "P2": 3,
        "P3": 2,
        "critical": 0,
        "high": 0,
        "medium": 0,
        "low": 1,
        "unknown": 0,
    }
    assert reviews["confirmed_findings"] == {"value": 1, "observed": 2, "unknown": 7}
    assert reviews["confirmation_rate"] == {"numerator": 1, "denominator": 2, "percent": 50.0}
    assert muse["pr_opened"]["value"] == "unknown"
    assert muse["pr_merged"]["value"] == "unknown"
    assert muse["cost_usd"] == {"value": "unknown", "observed": 0, "unknown": 3}
    terra = report["by_model"]["gpt-6.1-terra"]
    assert terra["cost_usd"] == {"value": 0.1, "observed": 1, "unknown": 4}
    assert terra["pr_opened"] == {"value": 1, "observed": 1, "unknown": 4}
    assert terra["pr_merged"]["value"] == 1
    assert terra["merge_group_ci_failures"] == {"value": 1, "observed": 1, "unknown": 4}
    assert terra["tokens"]["input_tokens"]["value"] == 10
    assert terra["tokens"]["cache_read_tokens"]["value"] == 7
    _write(
        ledger,
        {
            "task_id": "second-author-run",
            "agent": "codex",
            "model": "gpt-6.1-terra",
            "status": "done",
            "started_at": "2026-10-28T01:00:00Z",
            "pr": 123,
            "pr_opened": True,
        },
    )
    assert collect_agent_success(tasks_dir=ledger, until=NOW)["by_model"]["gpt-6.1-terra"]["pr_opened"] == {
        "value": 1,
        "observed": 2,
        "unknown": 4,
    }


def test_cli_and_collector_never_emit_content_or_paths(ledger, capsys):
    """Private bodies, prompts, errors, reasons and invalid labels must not reach either format."""
    _write(
        ledger,
        {
            "task_id": "private",
            "agent": "/home/PRIVATE_SENTINEL",
            "model": "secret\nPRIVATE_SENTINEL",
            "status": "failed",
            "started_at": "2026-10-28T11:59:59Z",
            "prompt": "PRIVATE_SENTINEL",
            "body": "PRIVATE_SENTINEL",
        },
    )
    for flag in ([], ["--json"]):
        assert main(["--tasks-dir", str(ledger), "--until", NOW.isoformat(), *flag]) == 0
        output = capsys.readouterr().out
        assert "PRIVATE_SENTINEL" not in output
        assert "/home/" not in output
        assert str(ledger) not in output
        assert "outside_owned_paths" in output
        assert "unknown" in output


def test_incomplete_ledger_and_window_boundaries_are_visible(tmp_path, capsys):
    """Malformed, undated and unknown-status records cannot silently improve the success rate."""
    base = {"agent": "agy", "model": "gemini-3.8-flash-high", "status": "done"}
    for task, start in (
        ("at-start", "2026-10-25T12:00:00Z"),
        ("at-end", NOW.isoformat()),
        ("future", "2026-10-29"),
        ("bad-date", "bad"),
    ):
        _write(tmp_path, {**base, "task_id": task, "started_at": start})
    _write(tmp_path, {**base, "task_id": "legacy", "schema_version": 1})
    _write(tmp_path, {**base, "task_id": "float-version", "schema_version": 2.0})
    _write(tmp_path, {**base, "task_id": "no-nonce", "run_nonce": None})
    _write(tmp_path, {**base, "task_id": "dry", "dry_run": True})
    _write(tmp_path, {**base, "task_id": "odd-status", "status": ["PRIVATE_SENTINEL"], "started_at": "2026-10-27"})
    (tmp_path / "bad.json").write_text("{PRIVATE_SENTINEL")
    report = collect_agent_success(tasks_dir=tmp_path, until=NOW)
    assert report["tasks"] == 2
    assert report["complete"] is False
    assert report["coverage"] == {
        "hot_records": 10,
        "archive_records": 0,
        "excluded_legacy": 2,
        "excluded_dry_run": 1,
        "invalid_records": 2,
        "undated_records": 1,
        "outside_window": 2,
        "duplicate_runs": 0,
        "unreadable_directories": 0,
        "model_catalog_unavailable": 0,
    }
    assert report["by_agent"]["agy"]["status"]["unknown"] == 1
    assert main(["--tasks-dir", str(tmp_path), "--until", NOW.isoformat(), "--json"]) == 1
    assert "PRIVATE_SENTINEL" not in capsys.readouterr().out
    assert collect_agent_success(tasks_dir=tmp_path / "missing", until=NOW)["available"] is False
    with pytest.raises(SystemExit) as error:
        main(["--until", "bad"])
    assert error.value.code == 2
    with pytest.raises(SystemExit) as error:
        main(["--since", "2026-10-29", "--until", "2026-10-28"])
    assert error.value.code == 2


def test_archived_review_cannot_borrow_newer_run_result_or_follow_symlink(tmp_path):
    """Result digest and sidecar locality prevent attribution of a different run's verdict."""
    base = {
        "task_id": "reused",
        "agent": "muse",
        "model": "muse-wonder-full-1.0",
        "status": "done",
        "mode": "read-only",
        "require_review_verdict": True,
        "started_at": "2026-10-27",
    }
    hot = _write(tmp_path, {**base, "result": "VERDICT: APPROVE"})
    record = json.loads(hot.read_text())
    _write(
        tmp_path / "archive",
        {**record, "run_nonce": "old", "result_sha256": hashlib.sha256(b"VERDICT: REQUEST_CHANGES").hexdigest()},
    )
    report = collect_agent_success(tasks_dir=tmp_path, until=NOW)
    assert report["by_agent"]["muse"]["reviews"]["verdicts"] == {
        "APPROVED": 1,
        "CHANGES_REQUESTED": 0,
        "BLOCKED": 0,
        "unknown": 1,
    }
    external = tmp_path.parent / (tmp_path.name + "-private.result")
    external.write_bytes(b"VERDICT: REQUEST_CHANGES")
    # A separate symlink cannot substitute for a final result, even with a matching digest.
    link = tmp_path / "link.result"
    link.symlink_to(external)
    _write(
        tmp_path,
        {
            **base,
            "task_id": "link",
            "result_file": str(link),
            "result_sha256": hashlib.sha256(external.read_bytes()).hexdigest(),
        },
    )
    assert (
        collect_agent_success(tasks_dir=tmp_path, until=NOW)["by_agent"]["muse"]["reviews"]["verdicts"]["unknown"] == 2
    )


def test_fresh_process_cli_resolves_primary_store_override(ledger):
    """A linked-worktree CLI must honor LU_TASKS_DIR instead of reading a relative checkout path."""
    proc = subprocess.run(
        [sys.executable, "-m", "scripts.fleet.agent_success", "--json", "--until", NOW.isoformat()],
        env={**os.environ, "LU_TASKS_DIR": str(ledger)},
        capture_output=True,
        text=True,
        check=False,
        timeout=60,
    )
    assert proc.returncode == 0, proc.stderr
    assert json.loads(proc.stdout)["tasks"] == 21


def test_metrics_api_uses_context_ledger_even_when_comms_store_is_missing(tmp_path, monkeypatch):
    """An opt-in metrics field must use its fixture context, without scanning the live ledger."""
    from fastapi.testclient import TestClient

    from scripts.api.main import create_app
    from scripts.api.monitor_context import fixture_context

    monkeypatch.setenv("FLEET_COMMS_MESSAGE_PLANE", "authority")
    monkeypatch.setenv("FLEET_COMMS_ROOT", str(tmp_path / "batch_state/fleet-comms/v1"))
    _write(
        tmp_path / "batch_state/tasks",
        {
            "task_id": "api",
            "agent": "muse",
            "model": "muse-wonder-full-1.0",
            "status": "done",
            "started_at": (datetime.now(UTC) - timedelta(hours=1)).isoformat(),
            "body": "PRIVATE_SENTINEL",
        },
    )
    with TestClient(create_app(fixture_context(tmp_path))) as client:
        for route in ("/api/comms/v1/metrics", "/api/fleet/facade/metrics"):
            assert "agent_success" not in client.get(route).json()
            response = client.get(route, params={"include_agent_success": "true"})
            assert response.status_code == 200
            payload = response.json()["agent_success"]
            assert payload["tasks"] == 1
            assert payload["by_model"]["muse-wonder-full-1.0"]["status"]["done"] == 1
            assert "PRIVATE_SENTINEL" not in response.text


def test_review_scores_aggregate_by_reviewer_and_author_model(tmp_path):
    """C-3020: advisory scores group by reviewer and author model; missing or malformed stay absent."""
    reviews = [
        ("terra-1", "codex", "gpt-6.1-terra", "claude-opus-5-5", "VERDICT: APPROVE\nSCORE: 8/10 one nit.\nF1 [P3] a.py:1 nit."),
        ("terra-2", "codex", "gpt-6.1-terra", "gpt-6.1-sol", "VERDICT: APPROVE\nSCORE: 10/10 clean."),
        ("sol-1", "codex", "gpt-6.1-sol", "claude-opus-5-5", "VERDICT: REQUEST_CHANGES\nSCORE: 9/10\nF1 [P1] b.py:2 bug."),
        ("sol-2", "codex", "gpt-6.1-sol", "claude-opus-5-5", "VERDICT: REQUEST_CHANGES\nSCORE: 9.5/10\nF1 [P0] c.py:3"),
        ("muse-1", "muse", "muse-wonder-full-1.0", "gpt-6.1-terra", "VERDICT: APPROVE\nNo score line."),
    ]
    for task_id, agent, model, author, result in reviews:
        _write(tmp_path, {
            "task_id": task_id, "agent": agent, "model": model, "status": "done", "mode": "read-only",
            "started_at": "2026-10-28T01:00:00Z", "review_author_model": author, "result": result,
        })
    _write(tmp_path, {
        "task_id": "sol-failed", "agent": "codex", "model": "gpt-6.1-sol", "status": "failed", "mode": "read-only",
        "started_at": "2026-10-28T01:00:00Z", "review_author_model": "claude-opus-5-5",
    })
    scores = collect_agent_success(tasks_dir=tmp_path, until=NOW)["review_scores"]
    assert scores["by_reviewer_model"]["gpt-6.1-terra"] == {
        "rounds": 2, "scored": 2, "absent": 0, "mean": 9, "median": 9.0,
        # Free prose cannot establish zero findings, so the clean 10/10 has no band to compare.
        "rubric_agreement": {"numerator": 1, "denominator": 1, "percent": 100.0},
    }
    assert scores["by_reviewer_model"]["gpt-6.1-sol"] == {
        "rounds": 2, "scored": 1, "absent": 1, "mean": 9, "median": 9,
        "rubric_agreement": {"numerator": 0, "denominator": 1, "percent": 0.0},
    }
    assert scores["by_reviewer_model"]["muse-wonder-full-1.0"]["absent"] == 1
    assert scores["by_reviewer_model"]["muse-wonder-full-1.0"]["mean"] == "unknown"
    opus = scores["by_author_model"]["claude-opus-5-5"]
    assert (opus["rounds"], opus["scored"], opus["absent"], opus["mean"]) == (3, 2, 1, 8.5)
    assert scores["by_author_model"]["gpt-6.1-sol"]["median"] == 10
    assert scores["by_author_model"]["gpt-6.1-terra"]["scored"] == 0
