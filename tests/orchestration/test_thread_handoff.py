from __future__ import annotations

import json
import os
import sqlite3
import subprocess
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest

from scripts.orchestration import thread_handoff as th
from scripts.orchestration import thread_handoff_canary as canary


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
            "modified_files": [],
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


@pytest.fixture(autouse=True)
def clean_invoking_checkout(monkeypatch):
    """Unit CLI fixtures run outside Git; model the clean bound checkout."""
    monkeypatch.setattr(th, "gather_git_state", lambda root: sample_snapshot(root)["git"])


def prepared(*, agent: str = "orchestrator", thread_id: str = "old-thread") -> dict:
    state = th.prepare_state(
        {"schema_version": th.SCHEMA_VERSION},
        agent=agent,
        now=datetime(2026, 5, 30, 8, 0, tzinfo=UTC),
        active_thread_id=thread_id,
        active_automation_id="old-auto",
        context_percent=86.0,
        force_new_replacement=False,
    )
    state["replacement"]["source_checkout"] = {
        "full_head": sample_snapshot(Path("."))["git"]["full_head"],
        "clean": True,
    }
    return state


def resumed_with_proof(tmp_path: Path, state: dict, thread_id: str = "new-thread") -> tuple[dict, Path]:
    replacement = state["replacement"]
    resumed = th.resume_state(
        state,
        rollover_id=replacement["rollover_id"],
        replacement_thread_id=thread_id,
        now=datetime(2026, 5, 30, 8, 1, tzinfo=UTC),
    )
    proof_path = tmp_path / "canary-pass.json"
    canary.write_json_atomic(
        proof_path,
        canary.build_pass_proof(
            rollover_id=replacement["rollover_id"],
            replacement_thread_id=thread_id,
            challenge=replacement["canary_challenge"],
            now=datetime(2026, 5, 30, 8, 2, tzinfo=UTC),
        ),
    )
    return resumed, proof_path


def strict_artifacts(tmp_path: Path, state: dict) -> tuple[Path, Path]:
    """Create script-scored strict evidence at this lease's reserved paths."""
    replacement = state["replacement"]
    snapshot = tmp_path / replacement["semantic_snapshot_path"]
    probe = tmp_path / replacement["strict_probe_path"]
    answers = tmp_path / replacement["strict_answers_path"]
    verdict = tmp_path / replacement["strict_verdict_path"]
    source = "handoff:.agent/thread-rollovers/evidence.json"
    payload = {
        "generated_at": "2026-07-13T12:00:00Z",
        "lineage_id": state["lineage_id"],
        "rollover_id": replacement["rollover_id"],
        "seed": 7,
        "goals": [{"id": f"goal-{i}", "statement": f"goal {i}", "source_ref": f"{source}#goal-{i}"} for i in range(3)],
        "decision_records": [
            {
                "id": f"decision-{i}",
                "decision": f"decision {i}",
                "source_ref": f"decision:docs/decisions/evidence.md#decision-{i}",
            }
            for i in range(3)
        ],
        "constraint_records": [
            {"id": f"constraint-{i}", "prohibition": f"prohibition {i}", "source_ref": f"{source}#constraint-{i}"}
            for i in range(2)
        ],
        "next_actions": [
            {
                "id": f"action-{i}",
                "action": f"action {i}",
                "source_ref": f"queue:batch_state/orchestrator-runs/evidence.json#action-{i}",
            }
            for i in range(2)
        ],
    }
    th.write_json_atomic(snapshot, payload)
    assert th.context_canary.main(["mint", "--snapshot", str(snapshot), "--out", str(probe)]) == 0
    minted = json.loads(probe.read_text(encoding="utf-8"))
    th.write_json_atomic(answers, {anchor["id"]: anchor["a"] for anchor in minted["anchors"]})
    assert (
        th.context_canary.main(
            [
                "score",
                "--probe",
                str(probe),
                "--answers",
                str(answers),
                "--expected-lineage-id",
                state["lineage_id"],
                "--expected-rollover-id",
                replacement["rollover_id"],
                "--verdict",
                str(verdict),
            ]
        )
        == 0
    )
    return probe, verdict


def test_direct_script_help_from_repository_root():
    repo_root = Path(__file__).resolve().parents[2]
    env = os.environ.copy()
    env.pop("CODEX_THREAD_ID", None)
    env.pop("CODEX_SESSION_ID", None)

    completed = subprocess.run(
        [".venv/bin/python", "scripts/orchestration/thread_handoff.py", "--help"],
        cwd=repo_root,
        capture_output=True,
        text=True,
        env=env,
        check=False,
    )

    assert completed.returncode == 0, completed.stderr
    assert "Prepare and guard agent-specific thread handoffs." in completed.stdout
    for command in ("prepare", "confirm-started", "resume", "check", "audit"):
        assert command in completed.stdout


def test_prepare_state_requires_confirmation_before_cleanup(tmp_path: Path):
    now = datetime(2026, 5, 30, 8, 0, tzinfo=UTC)
    state = prepared()

    assert state["active"]["thread_id"] == "old-thread"
    assert state["active"]["automation_id"] == "old-auto"
    assert state["replacement"]["status"] == "pending_start"
    assert state["cleanup"]["old_automation_ready_to_delete"] is False

    resumed, proof_path = resumed_with_proof(tmp_path, state)
    strict_probe, strict_verdict = strict_artifacts(tmp_path, resumed)
    confirmed = th.confirm_started(
        resumed,
        new_thread_id="new-thread",
        new_automation_id=None,
        confirmed_by="tester",
        now=now + timedelta(minutes=2),
        canary_proof=proof_path,
        strict_probe=strict_probe,
        strict_verdict=strict_verdict,
        state_root=tmp_path,
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
            canary_proof=Path("missing-proof.json"),
            strict_probe=Path("missing-probe.json"),
            strict_verdict=Path("missing-verdict.json"),
            state_root=Path("."),
        )


def test_render_bootstrap_prompt_contains_guardrails(tmp_path: Path):
    now = datetime(2026, 5, 30, 8, 0, tzinfo=UTC)
    state = prepared()
    prompt = th.render_bootstrap_prompt(sample_snapshot(tmp_path), state, context_threshold=82.0)

    assert "You are the replacement Codex orchestrator thread." in prompt
    assert "Role handoff: docs/session-state/codex-orchestrator-handoff.md" in prompt
    assert "Thread handoff: .agent/thread-rollovers/" in prompt
    assert "Global router:" not in prompt
    assert "Do not write docs/session-state/current.md for thread rollover." in prompt
    assert "git status --short --branch" in prompt
    assert "issue_stream_audit.py --json" in prompt
    assert "git worktree list" in prompt
    assert "confirm-started --agent orchestrator --lineage-id" in prompt
    assert "Only after that command reports old_automation_ready_to_delete=true" in prompt
    assert "Keep the invoking checkout clean at prepared HEAD abc123def0456789 through resume and confirmation (clean fast-forward advances are tolerated)." in prompt
    assert "Context estimate: 86.0% (ROLL OVER NOW; threshold 82.0%)." in prompt
    assert "orchestrator_control.py inbox --recent 20 --include-results" in prompt


def test_render_current_markdown_includes_required_handoff_sections(tmp_path: Path):
    now = datetime(2026, 5, 30, 8, 0, tzinfo=UTC)
    state = prepared()
    rendered = th.render_current_markdown(sample_snapshot(tmp_path), state, context_threshold=82.0)

    assert "## Thread Lease" in rendered
    assert "## Git State" in rendered
    assert "### Last 5 Commits" in rendered
    assert "### Modified Files" in rendered
    assert "## Open PRs" in rendered
    assert "## Delegated Tasks" in rendered
    assert "## First-Turn Checklist" in rendered
    assert "issue_stream_audit.py --json" in rendered
    assert "confirm-started --agent orchestrator --lineage-id" in rendered
    assert "orchestrator_control.py inbox --recent 20 --include-results" in rendered
    assert "Durable role handoff: `docs/session-state/codex-orchestrator-handoff.md`" in rendered
    assert "Source checkout HEAD: `abc123def0456789`" in rendered


def test_render_bootstrap_prompt_for_codex_uses_orchestrator_pointer(tmp_path: Path):
    now = datetime(2026, 5, 30, 8, 0, tzinfo=UTC)
    state = prepared(agent="codex")
    prompt = th.render_bootstrap_prompt(
        sample_snapshot(tmp_path),
        state,
        agent="codex",
        context_threshold=82.0,
    )

    assert "You are the replacement codex thread." in prompt
    assert "Role handoff: docs/session-state/current.orchestrator.md" in prompt
    assert "Thread handoff: .agent/thread-rollovers/" in prompt
    assert "issue_stream_audit.py --json" in prompt
    assert "git worktree list" in prompt


def test_render_current_markdown_for_codex_uses_orchestrator_pointer(tmp_path: Path):
    now = datetime(2026, 5, 30, 8, 0, tzinfo=UTC)
    state = prepared(agent="codex")
    rendered = th.render_current_markdown(
        sample_snapshot(tmp_path),
        state,
        agent="codex",
        context_threshold=82.0,
    )

    assert "## First-Turn Checklist" in rendered
    assert "Durable role handoff: `docs/session-state/current.orchestrator.md`" in rendered
    assert "confirm-started --agent codex --lineage-id" in rendered


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
    lineage_id = th.lineage_id_for("claude", "old-thread")
    rollover_id = "rollover-example"
    expected_runtime = Path(".agent/thread-rollovers/claude") / lineage_id / "generation-0001" / rollover_id
    assert th.default_state_path("claude", lineage_id) == (
        Path(".agent/thread-rollovers/claude") / lineage_id / "lease.json"
    )
    assert th.default_bootstrap_path("claude", lineage_id, 1, rollover_id) == expected_runtime / "bootstrap.md"
    assert th.default_thread_handoff_path("claude", lineage_id, 1, rollover_id) == expected_runtime / "handoff.md"
    assert th.default_handoff_path("orchestrator") == Path("docs/session-state/codex-orchestrator-handoff.md")
    assert th.default_handoff_path("codex") == Path("docs/session-state/current.orchestrator.md")
    assert th.default_handoff_path("claude") == Path("docs/session-state/current.claude.md")


def test_checkout_continuity_requires_clean_source_binding_and_same_clean_head():
    clean = sample_snapshot(Path("."))["git"]
    assert th.parse_status("M tracked.txt\n?? untracked.txt") == [
        {"status": "M", "path": "tracked.txt"},
        {"status": "??", "path": "untracked.txt"},
    ]
    binding = th.source_checkout_binding(clean)
    replacement = {"source_checkout": binding}

    assert th.checkout_continuity_error(replacement, clean) is None
    assert "missing its source checkout binding" in th.checkout_continuity_error({}, clean)

    wrong_head = {**clean, "full_head": "different-head"}
    assert "does not match prepared HEAD" in th.checkout_continuity_error(replacement, wrong_head)

    dirty = {**clean, "modified_files": [{"status": "M", "path": "tracked.txt"}]}
    assert "invoking checkout must be clean" in th.checkout_continuity_error(replacement, dirty)
    with pytest.raises(ValueError, match="source checkout must be clean before prepare"):
        th.source_checkout_binding(dirty)


def test_checkout_continuity_ff_descent_and_failure_modes():
    clean = sample_snapshot(Path("."))["git"]
    binding = th.source_checkout_binding(clean)
    replacement = {"source_checkout": binding}

    prepared_head = binding["full_head"]
    current_head = "current-head"
    git_state = {**clean, "full_head": current_head}

    def make_is_ancestor(ancestry_map):
        def is_ancestor(expected, current):
            return ancestry_map.get((expected, current))
        return is_ancestor

    # 1. Descent accepted: prepared is ancestor of current
    is_ancestor_ok = make_is_ancestor({(prepared_head, current_head): True})
    assert th.checkout_continuity_error(replacement, git_state, is_ancestor=is_ancestor_ok) is None

    # 2. Divergence rejected: neither is ancestor
    is_ancestor_diverged = make_is_ancestor({
        (prepared_head, current_head): False,
        (current_head, prepared_head): False,
    })
    err = th.checkout_continuity_error(replacement, git_state, is_ancestor=is_ancestor_diverged)
    assert f"invoking checkout HEAD {current_head} has diverged from prepared HEAD {prepared_head}" in err

    # 3. Rewind rejected: current is strict ancestor of prepared
    is_ancestor_rewind = make_is_ancestor({
        (prepared_head, current_head): False,
        (current_head, prepared_head): True,
    })
    err = th.checkout_continuity_error(replacement, git_state, is_ancestor=is_ancestor_rewind)
    assert f"invoking checkout HEAD {current_head} is a rewind (strict ancestor of prepared HEAD {prepared_head})" in err

    # 4. Dirty-at-descent rejected: prepared is ancestor, but tree is dirty
    dirty_state = {
        **clean,
        "full_head": current_head,
        "modified_files": [{"status": "M", "path": "tracked.txt"}]
    }
    err = th.checkout_continuity_error(replacement, dirty_state, is_ancestor=is_ancestor_ok)
    assert "invoking checkout must be clean" in err

    # 5. Ancestry undeterminable rejected: is_ancestor is None or returns None
    err = th.checkout_continuity_error(replacement, git_state, is_ancestor=None)
    assert "does not match prepared HEAD" in err
    assert "ancestry undeterminable" in err

    is_ancestor_none = make_is_ancestor({(prepared_head, current_head): None})
    err = th.checkout_continuity_error(replacement, git_state, is_ancestor=is_ancestor_none)
    assert "does not match prepared HEAD" in err
    assert "ancestry undeterminable" in err

    is_ancestor_partial_none = make_is_ancestor({
        (prepared_head, current_head): False,
        (current_head, prepared_head): None,
    })
    err = th.checkout_continuity_error(replacement, git_state, is_ancestor=is_ancestor_partial_none)
    assert "does not match prepared HEAD" in err
    assert "ancestry undeterminable" in err


def test_resume_after_descent_state_roundtrips(tmp_path: Path, monkeypatch):
    # default_state_path is CWD-relative; without chdir this test would plant a
    # phantom orchestrator lease in the invoking checkout's real .agent/ tree,
    # which detect scans.
    monkeypatch.chdir(tmp_path)
    state = prepared()
    replacement = state["replacement"]
    replacement["source_checkout"]["head_advanced_to"] = "some-advanced-sha"

    assert th.source_checkout_binding_error(replacement) is None

    state_path = th.default_state_path("orchestrator", state["lineage_id"])
    th.write_json_atomic(state_path, state)

    loaded_state = th.load_state(state_path)
    res_replacement, err = th.validate_live_lease(loaded_state, agent="orchestrator", state_path=state_path)
    assert err is None
    assert res_replacement is not None
    assert res_replacement["source_checkout"]["head_advanced_to"] == "some-advanced-sha"


def test_live_lease_requires_binding_but_started_history_remains_compatible():
    state = prepared(agent="codex")
    state["replacement"].pop("source_checkout")
    state_path = th.default_state_path("codex", state["lineage_id"])

    replacement, error = th.validate_live_lease(state, agent="codex", state_path=state_path)
    assert replacement is None
    assert "missing its source checkout binding" in error

    state["replacement"]["status"] = "started"
    state["replacement"]["thread_id"] = "historical-thread"
    replacement, error = th.validate_live_lease(state, agent="codex", state_path=state_path)
    assert error is None
    assert replacement is not None
    assert replacement["status"] == "started"


def test_prepare_rejects_dirty_source_checkout_without_writing_packet(tmp_path: Path, capsys, monkeypatch):
    dirty_snapshot = sample_snapshot(tmp_path)
    dirty_snapshot["git"]["modified_files"] = [{"status": "??", "path": "untracked.txt"}]
    monkeypatch.setattr(th, "gather_snapshot", lambda root, url: dirty_snapshot)
    monkeypatch.setattr(th, "gather_git_state", lambda root: dirty_snapshot["git"])

    assert th.main(["--repo-root", str(tmp_path), "prepare", "--active-thread-id", "old-thread"]) == 2
    payload = json.loads(capsys.readouterr().out)
    assert "source checkout must be clean before prepare" in payload["error"]
    assert payload["old_automation_ready_to_delete"] is False
    assert not (tmp_path / ".agent/thread-rollovers").exists()


def test_resume_and_confirm_independently_recheck_checkout_continuity(tmp_path: Path, capsys, monkeypatch):
    clean = sample_snapshot(tmp_path)["git"]
    monkeypatch.setattr(th, "gather_snapshot", lambda root, url: sample_snapshot(root))
    assert th.main(["--repo-root", str(tmp_path), "prepare", "--active-thread-id", "old-thread"]) == 0
    packet = json.loads(capsys.readouterr().out)
    state_path = tmp_path / packet["state_file"]

    monkeypatch.setattr(th, "gather_git_state", lambda root: {**clean, "full_head": "wrong-head"})
    resume_command = [
        "--repo-root",
        str(tmp_path),
        "resume",
        "--lineage-id",
        packet["lineage_id"],
        "--rollover-id",
        packet["rollover_id"],
        "--replacement-thread-id",
        "new-thread",
    ]
    assert th.main(resume_command) == 2
    assert "does not match prepared HEAD" in json.loads(capsys.readouterr().out)["error"]
    assert json.loads(state_path.read_text(encoding="utf-8"))["replacement"]["status"] == "pending_start"

    monkeypatch.setattr(th, "gather_git_state", lambda root: clean)
    assert th.main(resume_command) == 0
    capsys.readouterr()
    resumed = json.loads(state_path.read_text(encoding="utf-8"))
    strict_probe, strict_verdict = strict_artifacts(tmp_path, resumed)
    capsys.readouterr()
    proof = tmp_path / resumed["replacement"]["canary_proof_path"]
    canary.write_json_atomic(
        proof,
        canary.build_pass_proof(
            rollover_id=packet["rollover_id"],
            replacement_thread_id="new-thread",
            challenge=resumed["replacement"]["canary_challenge"],
            now=datetime(2026, 5, 30, 8, 2, tzinfo=UTC),
        ),
    )

    monkeypatch.setattr(
        th,
        "gather_git_state",
        lambda root: {**clean, "modified_files": [{"status": "M", "path": "tracked.txt"}]},
    )
    assert (
        th.main(
            [
                "--repo-root",
                str(tmp_path),
                "confirm-started",
                "--lineage-id",
                packet["lineage_id"],
                "--rollover-id",
                packet["rollover_id"],
                "--new-thread-id",
                "new-thread",
                "--canary-proof",
                str(proof),
                "--strict-probe",
                str(strict_probe),
                "--strict-verdict",
                str(strict_verdict),
            ]
        )
        == 2
    )
    assert "invoking checkout must be clean" in json.loads(capsys.readouterr().out)["error"]
    final_state = json.loads(state_path.read_text(encoding="utf-8"))
    assert final_state["replacement"]["status"] == "resumed"
    assert final_state["cleanup"]["old_automation_ready_to_delete"] is False


def test_prepare_orchestrator_writes_only_local_thread_handoff_by_default(
    tmp_path: Path,
    capsys,
    monkeypatch,
):
    monkeypatch.setattr(th, "gather_snapshot", lambda repo_root, base_url: sample_snapshot(repo_root))

    rc = th.main(
        [
            "--repo-root",
            str(tmp_path),
            "prepare",
            "--agent",
            "orchestrator",
            "--active-thread-id",
            "old-thread",
            "--context-percent",
            "86",
        ]
    )
    payload = json.loads(capsys.readouterr().out)

    assert rc == 0
    assert payload["agent"] == "orchestrator"
    assert payload["state_file"].startswith(".agent/thread-rollovers/orchestrator/")
    assert payload["bootstrap_file"].endswith("/bootstrap.md")
    assert payload["handoff_file"].endswith("/handoff.md")
    assert payload["thread_handoff_file"] == payload["handoff_file"]
    assert payload["role_handoff_file"] == "docs/session-state/codex-orchestrator-handoff.md"
    assert payload["router_file"] is None
    assert not (tmp_path / "docs/session-state/current.md").exists()
    assert "## Thread Lease" in (tmp_path / payload["handoff_file"]).read_text(encoding="utf-8")
    lease = json.loads((tmp_path / payload["state_file"]).read_text(encoding="utf-8"))
    assert lease["replacement"]["source_checkout"] == {"full_head": "abc123def0456789", "clean": True}


def test_prepare_rejects_write_current_without_explicit_router_unlock(
    tmp_path: Path,
    capsys,
    monkeypatch,
):
    monkeypatch.setattr(th, "gather_snapshot", lambda repo_root, base_url: sample_snapshot(repo_root))

    rc = th.main(
        [
            "--repo-root",
            str(tmp_path),
            "prepare",
            "--agent",
            "orchestrator",
            "--active-thread-id",
            "old-thread",
            "--write-current",
        ]
    )
    payload = json.loads(capsys.readouterr().out)

    assert rc == 2
    assert "--write-current is disabled by default" in payload["error"]
    assert payload["state_file"].startswith(".agent/thread-rollovers/orchestrator/")
    assert not (tmp_path / "docs/session-state/current.md").exists()
    assert not (tmp_path / payload["state_file"]).exists()


def test_prepare_writes_router_only_when_explicitly_unlocked(
    tmp_path: Path,
    capsys,
    monkeypatch,
):
    monkeypatch.setattr(th, "gather_snapshot", lambda repo_root, base_url: sample_snapshot(repo_root))

    rc = th.main(
        [
            "--repo-root",
            str(tmp_path),
            "prepare",
            "--agent",
            "orchestrator",
            "--active-thread-id",
            "old-thread",
            "--write-current",
            "--allow-git-router",
        ]
    )
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

    rc = th.main(
        [
            "--repo-root",
            str(tmp_path),
            "prepare",
            "--agent",
            "claude",
            "--active-thread-id",
            "old-thread",
        ]
    )
    payload = json.loads(capsys.readouterr().out)

    assert rc == 0
    assert payload["agent"] == "claude"
    assert payload["router_file"] is None
    assert router_path.read_text(encoding="utf-8") == "router stays\n"
    assert orchestrator_path.read_text(encoding="utf-8") == "orchestrator stays\n"
    assert claude_path.read_text(encoding="utf-8") == "claude role stays\n"
    assert (tmp_path / payload["handoff_file"]).is_file()
    assert (tmp_path / payload["state_file"]).is_file()
    assert (tmp_path / payload["bootstrap_file"]).is_file()


def test_confirm_started_is_scoped_to_selected_agent(tmp_path: Path, capsys):
    orchestrator_state = prepared(thread_id="old-orchestrator")
    claude_state = prepared(agent="claude", thread_id="old-claude")
    orchestrator_path = tmp_path / th.default_state_path("orchestrator", orchestrator_state["lineage_id"])
    claude_path = tmp_path / th.default_state_path("claude", claude_state["lineage_id"])
    th.write_json_atomic(orchestrator_path, orchestrator_state)
    resumed = th.resume_state(
        claude_state,
        rollover_id=claude_state["replacement"]["rollover_id"],
        replacement_thread_id="new-claude",
        now=datetime(2026, 5, 30, 8, 1, tzinfo=UTC),
    )
    strict_probe, strict_verdict = strict_artifacts(tmp_path, resumed)
    proof_path = tmp_path / resumed["replacement"]["canary_proof_path"]
    canary.write_json_atomic(
        proof_path,
        canary.build_pass_proof(
            rollover_id=resumed["replacement"]["rollover_id"],
            replacement_thread_id="new-claude",
            challenge=resumed["replacement"]["canary_challenge"],
            now=datetime(2026, 5, 30, 8, 2, tzinfo=UTC),
        ),
    )
    th.write_json_atomic(claude_path, resumed)
    capsys.readouterr()

    rc = th.main(
        [
            "--repo-root",
            str(tmp_path),
            "confirm-started",
            "--agent",
            "claude",
            "--lineage-id",
            resumed["lineage_id"],
            "--rollover-id",
            resumed["replacement"]["rollover_id"],
            "--new-thread-id",
            "new-claude",
            "--canary-proof",
            str(proof_path),
            "--strict-probe",
            str(strict_probe),
            "--strict-verdict",
            str(strict_verdict),
        ]
    )
    payload = json.loads(capsys.readouterr().out)

    assert rc == 0
    assert payload["agent"] == "claude"
    assert payload["state_file"] == claude_path.relative_to(tmp_path).as_posix()
    confirmed_claude = json.loads(claude_path.read_text(encoding="utf-8"))
    untouched_orchestrator = json.loads(orchestrator_path.read_text(encoding="utf-8"))
    assert confirmed_claude["replacement"]["thread_id"] == "new-claude"
    assert confirmed_claude["cleanup"]["old_automation_ready_to_delete"] is True
    assert untouched_orchestrator["cleanup"]["old_automation_ready_to_delete"] is False


def test_confirm_started_missing_agent_prepare_is_safe(tmp_path: Path, capsys):
    rc = th.main(
        [
            "--repo-root",
            str(tmp_path),
            "confirm-started",
            "--agent",
            "gemini",
            "--lineage-id",
            "lineage-missing",
            "--rollover-id",
            "rollover-missing",
            "--new-thread-id",
            "new-gemini",
            "--canary-proof",
            ".agent/missing-proof.json",
            "--strict-probe",
            ".agent/missing-probe.json",
            "--strict-verdict",
            ".agent/missing-verdict.json",
        ]
    )
    payload = json.loads(capsys.readouterr().out)

    assert rc == 2
    assert "run prepare first" in payload["error"]
    assert not (tmp_path / th.default_state_path("gemini", "lineage-missing")).exists()


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

    rc = th.main(
        [
            "--repo-root",
            str(tmp_path),
            "prepare",
            "--state-file",
            str(state_file),
            "--active-thread-id",
            "old-thread",
        ]
    )
    payload = json.loads(capsys.readouterr().out)

    assert rc == 2
    assert "unreadable state file" in payload["error"]
    assert state_path.read_text(encoding="utf-8") == "{not-json"
    assert not list((tmp_path / ".agent/thread-rollovers").glob("**/bootstrap.md"))


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
        conn.execute("create table threads (id text, title text, cwd text, archived integer, updated_at integer)")
        conn.execute("insert into threads values ('thread-1', 'Example', '/tmp/repo', 0, 100)")

    audit = th.inspect_codex_home(codex_home)

    assert audit["latest_state_db"] == str(db)
    assert audit["thread_count"] == 1
    assert audit["recent_threads"][0]["id"] == "thread-1"
    assert audit["automation_toml_files"] == []


def test_v2_state_has_unique_rollover_and_lineage_runtime_paths():
    state = prepared()
    replacement = state["replacement"]

    assert state["schema_version"] == 2
    assert replacement["rollover_id"].startswith("rollover-")
    assert replacement["lineage_id"] == th.lineage_id_for("orchestrator", "old-thread")
    assert replacement["runtime_path"] == (
        f".agent/thread-rollovers/orchestrator/{replacement['lineage_id']}/generation-0001/{replacement['rollover_id']}"
    )
    assert replacement["bootstrap_prompt_path"].startswith(replacement["runtime_path"])
    assert replacement["handoff_path"].startswith(replacement["runtime_path"])


def test_pending_prepare_refuses_unless_explicitly_forced():
    state = prepared()
    with pytest.raises(ValueError, match="pending rollover"):
        th.prepare_state(
            state,
            agent="orchestrator",
            now=datetime(2026, 5, 30, 8, 1, tzinfo=UTC),
            active_thread_id="old-thread",
            active_automation_id=None,
            context_percent=None,
            force_new_replacement=False,
        )

    forced = th.prepare_state(
        state,
        agent="orchestrator",
        now=datetime(2026, 5, 30, 8, 1, tzinfo=UTC),
        active_thread_id="old-thread",
        active_automation_id=None,
        context_percent=None,
        force_new_replacement=True,
    )
    assert forced["replacement"]["rollover_id"] != state["replacement"]["rollover_id"]


def test_resume_is_deterministic_and_refuses_a_different_thread():
    state = prepared()
    rollover_id = state["replacement"]["rollover_id"]
    resumed = th.resume_state(
        state,
        rollover_id=rollover_id,
        replacement_thread_id="new-thread",
        now=datetime(2026, 5, 30, 8, 1, tzinfo=UTC),
    )
    repeated = th.resume_state(
        resumed,
        rollover_id=rollover_id,
        replacement_thread_id="new-thread",
        now=datetime(2026, 5, 30, 8, 2, tzinfo=UTC),
    )

    assert repeated == resumed
    with pytest.raises(ValueError, match="different replacement thread"):
        th.resume_state(
            resumed,
            rollover_id=rollover_id,
            replacement_thread_id="other-thread",
            now=datetime(2026, 5, 30, 8, 2, tzinfo=UTC),
        )


def test_confirm_requires_matching_script_proven_canary_pass(tmp_path: Path):
    state = prepared()
    resumed, proof_path = resumed_with_proof(tmp_path, state)
    strict_probe, strict_verdict = strict_artifacts(tmp_path, resumed)
    confirmed = th.confirm_started(
        resumed,
        new_thread_id="new-thread",
        new_automation_id=None,
        confirmed_by="tester",
        now=datetime(2026, 5, 30, 8, 3, tzinfo=UTC),
        canary_proof=proof_path,
        strict_probe=strict_probe,
        strict_verdict=strict_verdict,
        state_root=tmp_path,
    )
    assert confirmed["replacement"]["status"] == "started"
    assert confirmed["cleanup"]["old_automation_ready_to_delete"] is True

    wrong_proof = tmp_path / "wrong.json"
    canary.write_json_atomic(
        wrong_proof,
        canary.build_pass_proof(
            rollover_id="other-rollover",
            replacement_thread_id="new-thread",
            challenge=state["replacement"]["canary_challenge"],
            now=datetime(2026, 5, 30, 8, 2, tzinfo=UTC),
        ),
    )
    with pytest.raises(ValueError, match="script-proven canary PASS"):
        th.confirm_started(
            resumed,
            new_thread_id="new-thread",
            new_automation_id=None,
            confirmed_by="tester",
            now=datetime(2026, 5, 30, 8, 3, tzinfo=UTC),
            canary_proof=wrong_proof,
            strict_probe=strict_probe,
            strict_verdict=strict_verdict,
            state_root=tmp_path,
        )


def test_v1_state_requires_explicit_migration(tmp_path: Path, capsys, monkeypatch):
    state_path = tmp_path / ".agent/legacy.json"
    state_path.parent.mkdir(parents=True)
    state_path.write_text(
        json.dumps({"schema_version": 1, "active": {"thread_id": "old-thread"}}),
        encoding="utf-8",
    )
    monkeypatch.setattr(th, "gather_snapshot", lambda root, url: sample_snapshot(root))
    command = [
        "--repo-root",
        str(tmp_path),
        "prepare",
        "--state-file",
        ".agent/legacy.json",
        "--active-thread-id",
        "old-thread",
    ]

    assert th.main(command) == 2
    assert "requires an explicit migration" in json.loads(capsys.readouterr().out)["error"]
    assert th.main([*command, "--migrate-v1"]) == 0
    assert json.loads(state_path.read_text(encoding="utf-8"))["schema_version"] == 2


def test_cli_requires_exact_rollover_and_reserved_canary_proof(tmp_path: Path, capsys, monkeypatch):
    monkeypatch.setattr(th, "gather_snapshot", lambda root, url: sample_snapshot(root))
    assert th.main(["--repo-root", str(tmp_path), "prepare", "--active-thread-id", "old-thread"]) == 0
    prepared_payload = json.loads(capsys.readouterr().out)
    state_path = tmp_path / prepared_payload["state_file"]
    state = json.loads(state_path.read_text(encoding="utf-8"))

    assert (
        th.main(
            [
                "--repo-root",
                str(tmp_path),
                "resume",
                "--state-file",
                prepared_payload["state_file"],
                "--rollover-id",
                prepared_payload["rollover_id"],
                "--replacement-thread-id",
                "new-thread",
            ]
        )
        == 0
    )
    capsys.readouterr()
    proof_path = tmp_path / state["replacement"]["canary_proof_path"]
    assert (
        canary.main(
            [
                "--rollover-id",
                prepared_payload["rollover_id"],
                "--replacement-thread-id",
                "new-thread",
                "--challenge",
                state["replacement"]["canary_challenge"],
                "--proof-file",
                str(proof_path),
            ]
        )
        == 0
    )
    capsys.readouterr()
    strict_probe, strict_verdict = strict_artifacts(tmp_path, state)
    capsys.readouterr()

    assert (
        th.main(
            [
                "--repo-root",
                str(tmp_path),
                "confirm-started",
                "--lineage-id",
                prepared_payload["lineage_id"],
                "--rollover-id",
                prepared_payload["rollover_id"],
                "--new-thread-id",
                "new-thread",
                "--canary-proof",
                state["replacement"]["canary_proof_path"],
                "--strict-probe",
                str(strict_probe.relative_to(tmp_path)),
                "--strict-verdict",
                str(strict_verdict.relative_to(tmp_path)),
            ]
        )
        == 0
    )
    assert json.loads(capsys.readouterr().out)["old_automation_ready_to_delete"] is True


def test_default_runtime_root_is_shared_by_real_linked_worktree(tmp_path: Path, capsys, monkeypatch):
    primary = tmp_path / "primary"
    linked = tmp_path / "linked"
    primary.mkdir()
    git_env = {key: value for key, value in os.environ.items() if not key.startswith("GIT_")}
    for command in (
        ["git", "init"],
        ["git", "config", "user.email", "test@example.invalid"],
        ["git", "config", "user.name", "Test"],
    ):
        subprocess.run(command, cwd=primary, check=True, capture_output=True, text=True, env=git_env)
    (primary / "README.md").write_text("fixture\n", encoding="utf-8")
    subprocess.run(["git", "add", "README.md"], cwd=primary, check=True, capture_output=True, text=True, env=git_env)
    subprocess.run(
        ["git", "commit", "-m", "fixture"], cwd=primary, check=True, capture_output=True, text=True, env=git_env
    )
    subprocess.run(
        ["git", "worktree", "add", "-b", "linked", str(linked)],
        cwd=primary,
        check=True,
        capture_output=True,
        text=True,
        env=git_env,
    )

    assert th.canonical_state_root(primary) == primary.resolve()
    assert th.canonical_state_root(linked) == primary.resolve()
    monkeypatch.setattr(th, "gather_snapshot", lambda root, url: sample_snapshot(root))
    monkeypatch.setattr(th, "repo_root_from_file", lambda: linked)
    assert th.main(["prepare", "--active-thread-id", "same-thread"]) == 0
    linked_payload = json.loads(capsys.readouterr().out)
    monkeypatch.setattr(th, "repo_root_from_file", lambda: primary)
    assert th.main(["prepare", "--active-thread-id", "same-thread"]) == 2
    primary_payload = json.loads(capsys.readouterr().out)

    expected_lineage = th.lineage_id_for("orchestrator", "same-thread")
    linked_state_path = th.resolve_state_path(
        repo_root=linked,
        state_root=th.canonical_state_root(linked),
        supplied_state_file=None,
        default_path=th.default_state_path("orchestrator", expected_lineage),
    )
    primary_state_path = th.resolve_state_path(
        repo_root=primary,
        state_root=th.canonical_state_root(primary),
        supplied_state_file=None,
        default_path=th.default_state_path("orchestrator", expected_lineage),
    )
    assert linked_state_path == primary_state_path
    assert linked_payload["state_file"] == primary_payload["state_file"]
    assert (primary / linked_payload["state_file"]).is_file()
    assert (primary / linked_payload["bootstrap_file"]).is_file()
    assert not (linked / ".agent").exists()


def test_canonical_discovery_failure_refuses_fallback_and_explicit_root_is_isolated(monkeypatch, tmp_path: Path):
    monkeypatch.setattr(
        th,
        "run_command",
        lambda *args, **kwargs: th.CommandResult(128, "", "not a repository"),
    )
    with pytest.raises(ValueError, match="cannot discover canonical Git common directory"):
        th.canonical_state_root(tmp_path)

    assert th.resolve_roots(tmp_path) == (tmp_path.resolve(), tmp_path.resolve())


def test_parallel_lineages_do_not_collide_in_an_explicit_fixture(tmp_path: Path, capsys, monkeypatch):
    monkeypatch.setattr(th, "gather_snapshot", lambda root, url: sample_snapshot(root))
    payloads = []
    for thread_id in ("old-a", "old-b"):
        assert (
            th.main(
                [
                    "--repo-root",
                    str(tmp_path),
                    "prepare",
                    "--agent",
                    "codex",
                    "--active-thread-id",
                    thread_id,
                ]
            )
            == 0
        )
        payloads.append(json.loads(capsys.readouterr().out))

    assert payloads[0]["lineage_id"] != payloads[1]["lineage_id"]
    assert payloads[0]["state_file"] != payloads[1]["state_file"]
    assert payloads[0]["runtime_path"] != payloads[1]["runtime_path"]


def test_bootstrap_uses_resume_canary_confirm_without_history_resume(tmp_path: Path):
    state = prepared()
    state_root = tmp_path / "canonical"
    prompt = th.render_bootstrap_prompt(
        sample_snapshot(tmp_path),
        state,
        state_root=state_root,
        context_threshold=82.0,
    )

    assert "do not fork, continue, or resume provider conversation history" in prompt
    assert "thread_handoff.py resume" in prompt
    assert "thread_handoff_canary.py" in prompt
    assert "thread_handoff.py confirm-started" in prompt
    assert str(state_root / state["replacement"]["canary_proof_path"]) in prompt


def test_canary_proof_rejects_tampering_after_atomic_write(tmp_path: Path):
    proof_path = tmp_path / "proof.json"
    payload = canary.build_pass_proof(
        rollover_id="rollover-1",
        replacement_thread_id="new-thread",
        challenge="challenge",
        now=datetime(2026, 5, 30, 8, 0, tzinfo=UTC),
    )
    canary.write_json_atomic(proof_path, payload)
    assert (
        canary.load_and_validate_pass_proof(
            proof_path,
            rollover_id="rollover-1",
            replacement_thread_id="new-thread",
            challenge="challenge",
        )[1]
        is None
    )

    payload["status"] = "FAIL"
    canary.write_json_atomic(proof_path, payload)
    assert (
        "did not report PASS"
        in canary.load_and_validate_pass_proof(
            proof_path,
            rollover_id="rollover-1",
            replacement_thread_id="new-thread",
            challenge="challenge",
        )[1]
    )


def test_confirmation_refuses_unresumed_and_identity_mismatched_rollovers(tmp_path: Path):
    state = prepared()
    replacement = state["replacement"]
    proof_path = tmp_path / "proof.json"
    canary.write_json_atomic(
        proof_path,
        canary.build_pass_proof(
            rollover_id=replacement["rollover_id"],
            replacement_thread_id="new-thread",
            challenge=replacement["canary_challenge"],
            now=datetime(2026, 5, 30, 8, 1, tzinfo=UTC),
        ),
    )
    with pytest.raises(ValueError, match="must be resumed"):
        th.confirm_started(
            state,
            new_thread_id="new-thread",
            new_automation_id=None,
            confirmed_by="tester",
            now=datetime(2026, 5, 30, 8, 2, tzinfo=UTC),
            canary_proof=proof_path,
            strict_probe=tmp_path / "strict-probe.json",
            strict_verdict=tmp_path / "strict-verdict.json",
            state_root=tmp_path,
        )
    resumed = th.resume_state(
        state,
        rollover_id=replacement["rollover_id"],
        replacement_thread_id="bound-thread",
        now=datetime(2026, 5, 30, 8, 1, tzinfo=UTC),
    )
    strict_probe, strict_verdict = strict_artifacts(tmp_path, resumed)
    with pytest.raises(ValueError, match="does not match the thread"):
        th.confirm_started(
            resumed,
            new_thread_id="new-thread",
            new_automation_id=None,
            confirmed_by="tester",
            now=datetime(2026, 5, 30, 8, 2, tzinfo=UTC),
            canary_proof=proof_path,
            strict_probe=strict_probe,
            strict_verdict=strict_verdict,
            state_root=tmp_path,
        )


def test_detect_is_structured_fail_closed_and_reports_reserved_packet_paths(tmp_path: Path, capsys, monkeypatch):
    monkeypatch.setattr(th, "gather_snapshot", lambda root, url: sample_snapshot(root))
    assert th.main(["--repo-root", str(tmp_path), "detect", "--agent", "codex"]) == 0
    assert json.loads(capsys.readouterr().out) == {"agent": "codex", "status": "none"}

    assert th.main(["--repo-root", str(tmp_path), "prepare", "--agent", "codex", "--active-thread-id", "old"]) == 0
    prepared_payload = json.loads(capsys.readouterr().out)
    assert th.main(["--repo-root", str(tmp_path), "detect", "--agent", "codex"]) == 0
    detected = json.loads(capsys.readouterr().out)
    assert detected["lineage_id"] == prepared_payload["lineage_id"]
    assert detected["rollover_id"] == prepared_payload["rollover_id"]
    for key in (
        "state_file",
        "runtime_path",
        "handoff_path",
        "bootstrap_prompt_path",
        "canary_challenge",
        "canary_proof_path",
        "semantic_snapshot_path",
        "strict_probe_path",
        "strict_questions_path",
        "strict_answers_path",
        "strict_verdict_path",
    ):
        assert detected[key]

    state_path = tmp_path / detected["state_file"]
    state = json.loads(state_path.read_text(encoding="utf-8"))
    state["replacement"]["strict_probe_path"] = "forged.json"
    th.write_json_atomic(state_path, state)
    assert th.main(["--repo-root", str(tmp_path), "detect", "--agent", "codex"]) == 2
    assert "reserved packet path" in json.loads(capsys.readouterr().out)["error"]


def test_detect_ignores_completed_started_rollovers_for_status_none(tmp_path: Path, capsys, monkeypatch):
    monkeypatch.setattr(th, "gather_snapshot", lambda root, url: sample_snapshot(root))
    assert (
        th.main(["--repo-root", str(tmp_path), "prepare", "--agent", "codex", "--active-thread-id", "old-thread"]) == 0
    )
    capsys.readouterr()

    state_file = next((tmp_path / ".agent/thread-rollovers/codex").glob("*/lease.json"))
    state = json.loads(state_file.read_text(encoding="utf-8"))
    state["replacement"]["status"] = "started"
    for key in (
        "runtime_path",
        "handoff_path",
        "bootstrap_prompt_path",
        "canary_challenge",
        "canary_proof_path",
        "semantic_snapshot_path",
        "strict_probe_path",
        "strict_questions_path",
        "strict_answers_path",
        "strict_verdict_path",
    ):
        state["replacement"].pop(key, None)
    th.write_json_atomic(state_file, state)

    assert th.main(["--repo-root", str(tmp_path), "detect", "--agent", "codex"]) == 0
    assert json.loads(capsys.readouterr().out) == {"agent": "codex", "status": "none"}


@pytest.mark.parametrize("mutation", ["schema", "agent", "lineage", "rollover", "ambiguous"])
def test_detect_rejects_bad_or_ambiguous_engine_leases(tmp_path: Path, capsys, monkeypatch, mutation: str):
    monkeypatch.setattr(th, "gather_snapshot", lambda root, url: sample_snapshot(root))
    for thread_id in ("old-a", "old-b") if mutation == "ambiguous" else ("old-a",):
        assert (
            th.main(["--repo-root", str(tmp_path), "prepare", "--agent", "codex", "--active-thread-id", thread_id]) == 0
        )
        capsys.readouterr()
    if mutation != "ambiguous":
        state_path = next((tmp_path / ".agent/thread-rollovers/codex").glob("*/lease.json"))
        state = json.loads(state_path.read_text(encoding="utf-8"))
        if mutation == "schema":
            state["schema_version"] = 9
        elif mutation == "agent":
            state["agent"] = "claude"
        elif mutation == "lineage":
            state["replacement"]["lineage_id"] = "lineage-other"
        else:
            state["replacement"]["rollover_id"] = "rollover-!!!"
        th.write_json_atomic(state_path, state)
    assert th.main(["--repo-root", str(tmp_path), "detect", "--agent", "codex"]) == 2


def test_lifecycle_requires_strict_ten_of_ten_before_cleanup(tmp_path: Path, capsys, monkeypatch):
    monkeypatch.setattr(th, "gather_snapshot", lambda root, url: sample_snapshot(root))
    assert (
        th.main(["--repo-root", str(tmp_path), "prepare", "--agent", "codex", "--active-thread-id", "old-thread"]) == 0
    )
    packet = json.loads(capsys.readouterr().out)
    assert (
        th.main(
            [
                "--repo-root",
                str(tmp_path),
                "detect",
                "--agent",
                "codex",
                "--format",
                "session-start",
                "--current-thread-id",
                "new-thread",
            ]
        )
        == 0
    )
    startup = capsys.readouterr().out
    assert "PENDING THREAD ROLLOVER DETECTED" in startup and "context_canary.py questions" in startup
    assert (
        th.main(
            [
                "--repo-root",
                str(tmp_path),
                "resume",
                "--agent",
                "codex",
                "--lineage-id",
                packet["lineage_id"],
                "--rollover-id",
                packet["rollover_id"],
                "--replacement-thread-id",
                "new-thread",
            ]
        )
        == 0
    )
    capsys.readouterr()
    state_path = tmp_path / packet["state_file"]
    resumed = json.loads(state_path.read_text(encoding="utf-8"))
    strict_probe, strict_verdict = strict_artifacts(tmp_path, resumed)
    questions = tmp_path / resumed["replacement"]["strict_questions_path"]
    assert th.context_canary.main(["questions", "--probe", str(strict_probe), "--out", str(questions)]) == 0
    assert all("a" not in item for item in json.loads(questions.read_text(encoding="utf-8"))["questions"])
    proof = tmp_path / resumed["replacement"]["canary_proof_path"]
    assert (
        canary.main(
            [
                "--rollover-id",
                packet["rollover_id"],
                "--replacement-thread-id",
                "new-thread",
                "--challenge",
                resumed["replacement"]["canary_challenge"],
                "--proof-file",
                str(proof),
            ]
        )
        == 0
    )
    capsys.readouterr()
    assert (
        th.main(
            [
                "--repo-root",
                str(tmp_path),
                "confirm-started",
                "--agent",
                "codex",
                "--lineage-id",
                packet["lineage_id"],
                "--rollover-id",
                packet["rollover_id"],
                "--new-thread-id",
                "new-thread",
                "--canary-proof",
                str(proof),
                "--strict-probe",
                str(strict_probe),
                "--strict-verdict",
                str(strict_verdict),
            ]
        )
        == 0
    )
    assert json.loads(capsys.readouterr().out)["old_automation_ready_to_delete"] is True


def test_confirmation_rejects_nine_of_ten_and_wrong_reserved_paths(tmp_path: Path, capsys, monkeypatch):
    monkeypatch.setattr(th, "gather_snapshot", lambda root, url: sample_snapshot(root))
    assert (
        th.main(["--repo-root", str(tmp_path), "prepare", "--agent", "codex", "--active-thread-id", "old-thread"]) == 0
    )
    packet = json.loads(capsys.readouterr().out)
    assert (
        th.main(
            [
                "--repo-root",
                str(tmp_path),
                "resume",
                "--agent",
                "codex",
                "--lineage-id",
                packet["lineage_id"],
                "--rollover-id",
                packet["rollover_id"],
                "--replacement-thread-id",
                "new-thread",
            ]
        )
        == 0
    )
    capsys.readouterr()
    state_path = tmp_path / packet["state_file"]
    resumed = json.loads(state_path.read_text(encoding="utf-8"))
    strict_probe, strict_verdict = strict_artifacts(tmp_path, resumed)
    verdict = json.loads(strict_verdict.read_text(encoding="utf-8"))
    verdict["correct"] = 9
    verdict["score"] = 0.9
    verdict["verdict"] = "FAIL-HANDOFF"
    verdict["per_anchor"][-1]["match"] = False
    th.write_json_atomic(strict_verdict, verdict)
    proof = tmp_path / resumed["replacement"]["canary_proof_path"]
    assert (
        canary.main(
            [
                "--rollover-id",
                packet["rollover_id"],
                "--replacement-thread-id",
                "new-thread",
                "--challenge",
                resumed["replacement"]["canary_challenge"],
                "--proof-file",
                str(proof),
            ]
        )
        == 0
    )
    capsys.readouterr()
    command = [
        "--repo-root",
        str(tmp_path),
        "confirm-started",
        "--agent",
        "codex",
        "--lineage-id",
        packet["lineage_id"],
        "--rollover-id",
        packet["rollover_id"],
        "--new-thread-id",
        "new-thread",
        "--canary-proof",
        str(proof),
        "--strict-probe",
        str(strict_probe),
        "--strict-verdict",
        str(strict_verdict),
    ]
    assert th.main(command) == 2
    assert json.loads(state_path.read_text(encoding="utf-8"))["cleanup"]["old_automation_ready_to_delete"] is False
    assert th.main([*command[:-2], "--strict-probe", "wrong.json", "--strict-verdict", str(strict_verdict)]) == 2
    assert json.loads(state_path.read_text(encoding="utf-8"))["cleanup"]["old_automation_ready_to_delete"] is False


@pytest.mark.parametrize("forgery", ["minimal", "top_level", "category", "source_ref"])
def test_confirmation_revalidates_probe_before_handwritten_pass_can_unlock_cleanup(tmp_path: Path, forgery: str):
    """The Fable bypass cannot turn a resumed lease into a started lease."""
    state = prepared()
    resumed, proof_path = resumed_with_proof(tmp_path, state)
    strict_probe, strict_verdict = strict_artifacts(tmp_path, resumed)

    if forgery == "minimal":
        probe = {
            "schema": "production-handoff-v2",
            "strict_production": True,
            "lineage_id": resumed["lineage_id"],
            "rollover_id": resumed["replacement"]["rollover_id"],
            "anchors": [{"id": f"forged-{index}"} for index in range(10)],
        }
    else:
        probe = json.loads(strict_probe.read_text(encoding="utf-8"))
        if forgery == "top_level":
            probe.pop("source")
        elif forgery == "category":
            probe["anchors"][0]["category"] = "decision/rationale"
        else:
            probe["anchors"][0]["source_ref"] = "git:HEAD"
    th.write_json_atomic(strict_probe, probe)

    forged_verdict = {
        "version": "2",
        "schema": "production-handoff-v2",
        "lineage_id": resumed["lineage_id"],
        "rollover_id": resumed["replacement"]["rollover_id"],
        "probe_sha256": th._canonical_json_sha256(probe),
        "seed": probe.get("seed", 0),
        "k": 10,
        "correct": 10,
        "score": 1.0,
        "verdict": "PASS",
        "model": "handwritten",
        "per_anchor": [{"id": anchor["id"], "match": True} for anchor in probe["anchors"]],
    }
    th.write_json_atomic(strict_verdict, forged_verdict)
    before_confirmation = json.loads(json.dumps(resumed))

    with pytest.raises(ValueError, match="strict probe failed production validation"):
        th.confirm_started(
            resumed,
            new_thread_id="new-thread",
            new_automation_id=None,
            confirmed_by="tester",
            now=datetime(2026, 5, 30, 8, 3, tzinfo=UTC),
            canary_proof=proof_path,
            strict_probe=strict_probe,
            strict_verdict=strict_verdict,
            state_root=tmp_path,
        )

    assert resumed == before_confirmation
    assert resumed["replacement"]["status"] == "resumed"
    assert resumed["cleanup"]["old_automation_ready_to_delete"] is False
