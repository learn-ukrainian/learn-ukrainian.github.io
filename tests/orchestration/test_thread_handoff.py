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
    assert "Role handoff: docs/session-state/codex-orchestrator-handoff.md" in prompt
    assert "Thread handoff: .agent/orchestrator-thread-handoff.md" in prompt
    assert "Global router:" not in prompt
    assert "Do not write docs/session-state/current.md for thread rollover." in prompt
    assert "git status --short --branch" in prompt
    assert "issue_stream_audit.py --json" in prompt
    assert "git worktree list" in prompt
    assert "confirm-started --agent orchestrator --new-thread-id <replacement-thread-id>" in prompt
    assert "Only after that command reports old_automation_ready_to_delete=true" in prompt
    assert "Context estimate: 90.0% (ROLL OVER NOW; threshold 82.0%)." in prompt
    assert "orchestrator_control.py inbox --recent 20 --include-results" in prompt


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
    assert "## First-Turn Checklist" in rendered
    assert "issue_stream_audit.py --json" in rendered
    assert "confirm-started --agent orchestrator --new-thread-id <replacement-thread-id>" in rendered
    assert "orchestrator_control.py inbox --recent 20 --include-results" in rendered
    assert "Durable role handoff: `docs/session-state/codex-orchestrator-handoff.md`" in rendered


def test_render_bootstrap_prompt_for_codex_uses_orchestrator_pointer(tmp_path: Path):
    now = datetime(2026, 5, 30, 8, 0, tzinfo=UTC)
    state = th.prepare_state(
        {},
        agent="codex",
        now=now,
        active_thread_id="old-thread",
        active_automation_id="old-auto",
        bootstrap_path=Path(".agent/bootstrap.md"),
        context_percent=90.0,
        force_new_replacement=False,
    )
    prompt = th.render_bootstrap_prompt(
        sample_snapshot(tmp_path),
        state,
        agent="codex",
        context_threshold=82.0,
    )

    assert "You are the replacement codex thread." in prompt
    assert "Role handoff: docs/session-state/current.orchestrator.md" in prompt
    assert "Thread handoff: .agent/codex-thread-handoff.md" in prompt
    assert "issue_stream_audit.py --json" in prompt
    assert "git worktree list" in prompt


def test_render_current_markdown_for_codex_uses_orchestrator_pointer(tmp_path: Path):
    now = datetime(2026, 5, 30, 8, 0, tzinfo=UTC)
    state = th.prepare_state(
        {},
        agent="codex",
        now=now,
        active_thread_id="old-thread",
        active_automation_id=None,
        bootstrap_path=Path(".agent/bootstrap.md"),
        context_percent=None,
        force_new_replacement=False,
    )
    rendered = th.render_current_markdown(
        sample_snapshot(tmp_path),
        state,
        agent="codex",
        context_threshold=82.0,
    )

    assert "## First-Turn Checklist" in rendered
    assert "Durable role handoff: `docs/session-state/current.orchestrator.md`" in rendered
    assert "confirm-started --agent codex --new-thread-id <replacement-thread-id>" in rendered


def test_render_router_markdown_contains_parseable_markers():
    rendered = th.render_router_markdown(
        generated_at="2026-05-30T08:00:00Z",
        default_agent="orchestrator",
        agents=["orchestrator", "codex", "claude", "gemini"],
    )

    assert "Latest-Brief: docs/session-state/codex-orchestrator-handoff.md" in rendered
    assert "Agent-Handoff:" in rendered
    assert "- orchestrator: docs/session-state/codex-orchestrator-handoff.md" in rendered
    assert "- codex: docs/session-state/current.orchestrator.md" in rendered
    assert len(rendered.encode("utf-8")) < 1200


def test_default_agent_paths_are_agent_specific():
    assert th.default_state_path("claude") == Path(".agent/claude-thread-lease.json")
    assert th.default_bootstrap_path("claude") == Path(".agent/claude-thread-bootstrap.md")
    assert th.default_thread_handoff_path("claude") == Path(".agent/claude-thread-handoff.md")
    assert th.default_handoff_path("orchestrator") == Path("docs/session-state/codex-orchestrator-handoff.md")
    assert th.default_handoff_path("codex") == Path("docs/session-state/current.orchestrator.md")
    assert th.default_handoff_path("claude") == Path("docs/session-state/current.claude.md")


def test_prepare_orchestrator_writes_only_local_thread_handoff_by_default(
    tmp_path: Path,
    capsys,
    monkeypatch,
):
    monkeypatch.setattr(th, "gather_snapshot", lambda repo_root, base_url: sample_snapshot(repo_root))

    rc = th.main([
        "--repo-root",
        str(tmp_path),
        "prepare",
        "--agent",
        "orchestrator",
        "--context-percent",
        "86",
    ])
    payload = json.loads(capsys.readouterr().out)

    assert rc == 0
    assert payload["agent"] == "orchestrator"
    assert payload["state_file"] == ".agent/orchestrator-thread-lease.json"
    assert payload["bootstrap_file"] == ".agent/orchestrator-thread-bootstrap.md"
    assert payload["handoff_file"] == ".agent/orchestrator-thread-handoff.md"
    assert payload["thread_handoff_file"] == ".agent/orchestrator-thread-handoff.md"
    assert payload["role_handoff_file"] == "docs/session-state/codex-orchestrator-handoff.md"
    assert payload["router_file"] is None
    assert not (tmp_path / "docs/session-state/current.md").exists()
    assert "## Thread Lease" in (
        tmp_path / ".agent/orchestrator-thread-handoff.md"
    ).read_text(encoding="utf-8")


def test_prepare_rejects_write_current_without_explicit_router_unlock(
    tmp_path: Path,
    capsys,
    monkeypatch,
):
    monkeypatch.setattr(th, "gather_snapshot", lambda repo_root, base_url: sample_snapshot(repo_root))

    rc = th.main([
        "--repo-root",
        str(tmp_path),
        "prepare",
        "--agent",
        "orchestrator",
        "--write-current",
    ])
    payload = json.loads(capsys.readouterr().out)

    assert rc == 2
    assert "--write-current is disabled by default" in payload["error"]
    assert payload["thread_handoff_file"] == ".agent/orchestrator-thread-handoff.md"
    assert not (tmp_path / "docs/session-state/current.md").exists()
    assert not (tmp_path / ".agent/orchestrator-thread-handoff.md").exists()


def test_prepare_writes_router_only_when_explicitly_unlocked(
    tmp_path: Path,
    capsys,
    monkeypatch,
):
    monkeypatch.setattr(th, "gather_snapshot", lambda repo_root, base_url: sample_snapshot(repo_root))

    rc = th.main([
        "--repo-root",
        str(tmp_path),
        "prepare",
        "--agent",
        "orchestrator",
        "--write-current",
        "--allow-git-router",
    ])
    payload = json.loads(capsys.readouterr().out)

    assert rc == 0
    assert payload["router_file"] == "docs/session-state/current.md"
    assert "Latest-Brief: docs/session-state/codex-orchestrator-handoff.md" in (
        tmp_path / "docs/session-state/current.md"
    ).read_text(encoding="utf-8")


def test_prepare_non_orchestrator_does_not_clobber_router_or_orchestrator_handoff(
    tmp_path: Path,
    capsys,
    monkeypatch,
):
    session_dir = tmp_path / "docs/session-state"
    session_dir.mkdir(parents=True)
    router_path = session_dir / "current.md"
    orchestrator_path = session_dir / "codex-orchestrator-handoff.md"
    claude_path = session_dir / "current.claude.md"
    router_path.write_text("router stays\n", encoding="utf-8")
    orchestrator_path.write_text("orchestrator stays\n", encoding="utf-8")
    claude_path.write_text("claude role stays\n", encoding="utf-8")
    monkeypatch.setattr(th, "gather_snapshot", lambda repo_root, base_url: sample_snapshot(repo_root))

    rc = th.main([
        "--repo-root",
        str(tmp_path),
        "prepare",
        "--agent",
        "claude",
    ])
    payload = json.loads(capsys.readouterr().out)

    assert rc == 0
    assert payload["agent"] == "claude"
    assert payload["router_file"] is None
    assert router_path.read_text(encoding="utf-8") == "router stays\n"
    assert orchestrator_path.read_text(encoding="utf-8") == "orchestrator stays\n"
    assert claude_path.read_text(encoding="utf-8") == "claude role stays\n"
    assert (tmp_path / ".agent/claude-thread-handoff.md").is_file()
    assert (tmp_path / ".agent/claude-thread-lease.json").is_file()
    assert (tmp_path / ".agent/claude-thread-bootstrap.md").is_file()


def test_confirm_started_is_scoped_to_selected_agent(tmp_path: Path, capsys):
    now = datetime(2026, 5, 30, 8, 0, tzinfo=UTC)
    agent_dir = tmp_path / ".agent"
    agent_dir.mkdir()
    th.write_json_atomic(
        agent_dir / "orchestrator-thread-lease.json",
        th.prepare_state(
            {},
            agent="orchestrator",
            now=now,
            active_thread_id="old-orchestrator",
            active_automation_id=None,
            bootstrap_path=Path(".agent/orchestrator-thread-bootstrap.md"),
            context_percent=None,
            force_new_replacement=False,
        ),
    )
    th.write_json_atomic(
        agent_dir / "claude-thread-lease.json",
        th.prepare_state(
            {},
            agent="claude",
            now=now,
            active_thread_id="old-claude",
            active_automation_id=None,
            bootstrap_path=Path(".agent/claude-thread-bootstrap.md"),
            context_percent=None,
            force_new_replacement=False,
        ),
    )

    rc = th.main([
        "--repo-root",
        str(tmp_path),
        "confirm-started",
        "--agent",
        "claude",
        "--new-thread-id",
        "new-claude",
    ])
    payload = json.loads(capsys.readouterr().out)

    assert rc == 0
    assert payload["agent"] == "claude"
    assert payload["state_file"] == ".agent/claude-thread-lease.json"
    claude_state = json.loads((agent_dir / "claude-thread-lease.json").read_text(encoding="utf-8"))
    orchestrator_state = json.loads((agent_dir / "orchestrator-thread-lease.json").read_text(encoding="utf-8"))
    assert claude_state["replacement"]["thread_id"] == "new-claude"
    assert claude_state["cleanup"]["old_automation_ready_to_delete"] is True
    assert orchestrator_state["cleanup"]["old_automation_ready_to_delete"] is False


def test_confirm_started_missing_agent_prepare_is_safe(tmp_path: Path, capsys):
    rc = th.main([
        "--repo-root",
        str(tmp_path),
        "confirm-started",
        "--agent",
        "gemini",
        "--new-thread-id",
        "new-gemini",
    ])
    payload = json.loads(capsys.readouterr().out)

    assert rc == 2
    assert "run prepare first" in payload["error"]
    assert not (tmp_path / ".agent/gemini-thread-lease.json").exists()


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
