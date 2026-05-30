from __future__ import annotations

import json
import sqlite3
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest

from scripts.orchestration import thread_handoff as th


def sample_snapshot(tmp_path: Path) -> dict:
    return {
        "generated_at": "2026-05-30T08:00:00Z",
        "git": {
            "repo_root": str(tmp_path),
            "branch": "main",
            "head": "abc123def0",
            "full_head": "abc123def0456789",
            "ahead_behind": {"ahead": 1, "behind": 0, "upstream": "origin/main"},
            "last_commits": [
                {"sha": "abc123def0", "subject": "docs(session): handoff"},
                {"sha": "1111111111", "subject": "feat(api): monitor"},
            ],
            "modified_files": [
                {"status": "M", "path": "docs/session-state/current.md"},
            ],
        },
        "monitor": {
            "base_url": "http://127.0.0.1:8765",
            "orient": {"git": {"head": "abc123def0"}},
            "active_delegates": {"total": 0, "tasks": []},
            "completed_delegates": {
                "total": 1,
                "tasks": [{"task_id": "codex/example", "agent": "codex", "status": "done", "duration_s": 42}],
            },
            "worktrees": {"count": 2, "worktrees": []},
        },
        "github": {
            "open_prs": [
                {
                    "number": 12,
                    "title": "feat: example",
                    "headRefName": "codex/example",
                    "mergeStateStatus": "CLEAN",
                    "isDraft": False,
                }
            ],
            "open_issues": [
                {"number": 34, "title": "Need handoff", "updatedAt": "2026-05-30T07:00:00Z"},
            ],
        },
    }


def test_prepare_state_requires_confirmation_before_cleanup(tmp_path: Path):
    now = datetime(2026, 5, 30, 8, 0, tzinfo=UTC)
    state = th.prepare_state(
        {},
        now=now,
        active_thread_id="old-thread",
        active_automation_id="old-auto",
        bootstrap_path=Path(".agent/bootstrap.md"),
        context_percent=86.0,
        force_new_replacement=False,
    )

    assert state["active"]["thread_id"] == "old-thread"
    assert state["active"]["automation_id"] == "old-auto"
    assert state["replacement"]["status"] == "pending_start"
    assert state["cleanup"]["old_automation_ready_to_delete"] is False

    confirmed = th.confirm_started(
        state,
        new_thread_id="new-thread",
        new_automation_id=None,
        confirmed_by="tester",
        now=now + timedelta(minutes=2),
    )
    assert confirmed["replacement"]["status"] == "started"
    assert confirmed["replacement"]["thread_id"] == "new-thread"
    assert confirmed["cleanup"]["old_automation_ready_to_delete"] is True


def test_confirm_started_rejects_missing_pending_replacement():
    with pytest.raises(ValueError, match="run prepare first"):
        th.confirm_started(
            {},
            new_thread_id="new-thread",
            new_automation_id=None,
            confirmed_by="tester",
            now=datetime(2026, 5, 30, 8, 0, tzinfo=UTC),
        )


def test_render_bootstrap_prompt_contains_guardrails(tmp_path: Path):
    now = datetime(2026, 5, 30, 8, 0, tzinfo=UTC)
    state = th.prepare_state(
        {},
        now=now,
        active_thread_id="old-thread",
        active_automation_id="old-auto",
        bootstrap_path=Path(".agent/bootstrap.md"),
        context_percent=90.0,
        force_new_replacement=False,
    )
    prompt = th.render_bootstrap_prompt(sample_snapshot(tmp_path), state, context_threshold=82.0)

    assert "You are the replacement Codex orchestrator thread." in prompt
    assert "confirm-started --new-thread-id <replacement-thread-id>" in prompt
    assert "Only after that command reports old_automation_ready_to_delete=true" in prompt
    assert "Context estimate: 90.0% (ROLL OVER NOW; threshold 82.0%)." in prompt


def test_render_current_markdown_includes_required_handoff_sections(tmp_path: Path):
    now = datetime(2026, 5, 30, 8, 0, tzinfo=UTC)
    state = th.prepare_state(
        {},
        now=now,
        active_thread_id="old-thread",
        active_automation_id=None,
        bootstrap_path=Path(".agent/bootstrap.md"),
        context_percent=None,
        force_new_replacement=False,
    )
    rendered = th.render_current_markdown(sample_snapshot(tmp_path), state, context_threshold=82.0)

    assert "## Thread Lease" in rendered
    assert "## Git State" in rendered
    assert "### Last 5 Commits" in rendered
    assert "### Modified Files" in rendered
    assert "## Open PRs" in rendered
    assert "## Delegated Tasks" in rendered
    assert "## Next Commands" in rendered
    assert "docs/session-state/current.md" in rendered


def test_check_state_flags_pending_and_stale_replacement():
    prepared_at = datetime(2026, 5, 30, 8, 0, tzinfo=UTC)
    state = {
        "active": {"generation": "orchestrator-1", "last_seen_at": th.isoformat_z(prepared_at)},
        "replacement": {"status": "pending_start", "prepared_at": th.isoformat_z(prepared_at)},
        "cleanup": {"old_automation_ready_to_delete": False},
    }

    facts, warnings = th.check_state(
        state,
        now=prepared_at + timedelta(hours=13),
        stale_after=timedelta(hours=12),
        context_percent=83.0,
        context_threshold=82.0,
    )

    assert "active_generation=orchestrator-1" in facts
    assert any("pending_start" in warning for warning in warnings)
    assert any("context estimate 83.0%" in warning for warning in warnings)
    assert any("replacement has been pending" in warning for warning in warnings)


def test_check_state_flags_corrupted_state_file():
    facts, warnings = th.check_state(
        {"schema_version": th.SCHEMA_VERSION, "state_error": "unreadable state file: bad json"},
        now=datetime(2026, 5, 30, 8, 0, tzinfo=UTC),
        stale_after=timedelta(hours=12),
        context_percent=None,
        context_threshold=82.0,
    )

    assert "replacement_status=none" in facts
    assert warnings == ["unreadable state file: bad json"]


def test_prepare_refuses_to_overwrite_corrupted_state_file(tmp_path: Path, capsys, monkeypatch):
    state_file = Path(".agent/orchestrator-thread-lease.json")
    state_path = tmp_path / state_file
    state_path.parent.mkdir(parents=True)
    state_path.write_text("{not-json", encoding="utf-8")
    monkeypatch.setattr(th, "gather_snapshot", lambda repo_root, base_url: sample_snapshot(repo_root))

    rc = th.main([
        "--repo-root",
        str(tmp_path),
        "prepare",
        "--state-file",
        str(state_file),
        "--bootstrap-file",
        ".agent/bootstrap.md",
    ])
    payload = json.loads(capsys.readouterr().out)

    assert rc == 2
    assert "unreadable state file" in payload["error"]
    assert state_path.read_text(encoding="utf-8") == "{not-json"
    assert not (tmp_path / ".agent/bootstrap.md").exists()


def test_parse_ahead_behind_reports_malformed_output():
    parsed = th.parse_ahead_behind("not-a-count", "origin/main")

    assert parsed == {
        "upstream": "origin/main",
        "parse_error": "unexpected rev-list output: 'not-a-count'",
    }


def test_inspect_codex_home_reports_thread_metadata(tmp_path: Path):
    codex_home = tmp_path / ".codex"
    codex_home.mkdir()
    db = codex_home / "state_1.sqlite"
    with sqlite3.connect(db) as conn:
        conn.execute(
            "create table threads (id text, title text, cwd text, archived integer, updated_at integer)"
        )
        conn.execute(
            "insert into threads values ('thread-1', 'Example', '/tmp/repo', 0, 100)"
        )

    audit = th.inspect_codex_home(codex_home)

    assert audit["latest_state_db"] == str(db)
    assert audit["thread_count"] == 1
    assert audit["recent_threads"][0]["id"] == "thread-1"
    assert audit["automation_toml_files"] == []
