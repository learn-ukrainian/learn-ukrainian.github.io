from __future__ import annotations

import inspect
import json
import os
import sqlite3
import subprocess
from datetime import UTC, datetime, timedelta
from pathlib import Path
from types import SimpleNamespace

import pytest

from scripts.lib import session_record
from scripts.orchestration import claudex_supervisor as cs
from scripts.orchestration import task_identity
from scripts.orchestration import thread_handoff as th
from scripts.orchestration import thread_handoff_canary as canary
from scripts.orchestration.task_family import rollover, rollover_registry
from scripts.orchestration.task_family.storage import TaskFamilyStorage

_REPO_ROOT = Path(__file__).resolve().parents[2]


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
    for variable in (
        "LEARN_UKRAINIAN_CLAUDEX_RUN_ID",
        "LEARN_UKRAINIAN_CLAUDEX_LAUNCH_GENERATION",
        "LEARN_UKRAINIAN_SESSION_ID",
    ):
        monkeypatch.delenv(variable, raising=False)


def seed_supervised_claudex(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    *,
    session_id: str = "official-session-5265",
) -> cs.ClaudexSupervisor:
    (tmp_path / ".venv").symlink_to(_REPO_ROOT / ".venv", target_is_directory=True)
    supervisor_env = os.environ.copy()
    supervisor_env.update(
        {
            "LEARN_UKRAINIAN_PROFILE_ID": "sol_lead",
            "LEARN_UKRAINIAN_MAIN_MODEL_ID": "gpt-5.6-sol",
            "LEARN_UKRAINIAN_TRANSPORT": "claudex",
            "LEARN_UKRAINIAN_TRUSTED": "1",
            "CLAUDE_CODE_SUBAGENT_MODEL": "gpt-5.6-terra",
        }
    )
    supervisor = cs.ClaudexSupervisor(
        "/bin/true",
        [
            "--model",
            "gpt-5.6-sol",
            "--agent",
            "infra-orchestrator",
            "--epic",
            "harness",
        ],
        state_root=tmp_path,
        env=supervisor_env,
    )
    supervisor.child = SimpleNamespace(pid=4242)  # type: ignore[assignment]
    supervisor._write_runtime("running")
    cs.bind_session(
        state_root=tmp_path,
        run_id=supervisor.run_id,
        launch_generation=0,
        session_id=session_id,
        source="startup",
        model_id="gpt-5.6-sol",
        handoff_agent="claude-infra",
    )
    monkeypatch.setenv("LEARN_UKRAINIAN_CLAUDEX_RUN_ID", supervisor.run_id)
    monkeypatch.setenv("LEARN_UKRAINIAN_CLAUDEX_LAUNCH_GENERATION", "0")
    monkeypatch.setenv("LEARN_UKRAINIAN_SESSION_ID", session_id)
    return supervisor


def prepared(*, agent: str = "orchestrator", thread_id: str = "old-thread") -> dict:
    state = th.prepare_state(
        {"schema_version": th.SCHEMA_VERSION},
        agent=agent,
        now=datetime(2026, 5, 30, 8, 0, tzinfo=UTC),
        active_thread_id=thread_id,
        active_automation_id="old-auto",
        context_percent=86.0,
        force_new_replacement=False,
        harness="codex-app",
    )
    state["replacement"]["source_checkout"] = {
        "full_head": sample_snapshot(Path("."))["git"]["full_head"],
        "clean": True,
    }
    return state


def test_rollover_state_commits_identity_receipt_before_lease(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    state = prepared()
    state_path = tmp_path / ".agent/thread-rollovers/orchestrator/lease.json"
    writes: list[tuple[Path, dict]] = []
    monkeypatch.setattr(th, "write_json_atomic", lambda path, payload: writes.append((path, payload)))

    th.write_rollover_state(state_path, tmp_path, state)

    assert writes[0][0] == tmp_path / state["replacement"]["identity_receipt_path"]
    assert writes[0][1]["schema_version"] == "rollover-identity-receipt.v1"
    assert writes[1] == (state_path, state)


def test_rollover_state_missing_receipt_path_writes_nothing(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    state = prepared()
    state["replacement"].pop("identity_receipt_path")
    writes: list[tuple[Path, dict]] = []
    monkeypatch.setattr(th, "write_json_atomic", lambda path, payload: writes.append((path, payload)))

    with pytest.raises(ValueError, match="receipt path is missing"):
        th.write_rollover_state(tmp_path / "lease.json", tmp_path, state)

    assert writes == []


def test_rollover_state_refreshes_canonical_registry_projection(tmp_path: Path) -> None:
    state = prepared(agent="codex", thread_id="source-registry-sync")
    lineage_id = state["lineage_id"]
    rollover_id = state["replacement"]["rollover_id"]
    state_path = tmp_path / th.default_state_path("codex", lineage_id)

    th.write_rollover_state(state_path, tmp_path, state)

    record = rollover_registry.load_record(
        tmp_path,
        agent="codex",
        lineage_id=lineage_id,
        rollover_id=rollover_id,
    )
    assert record["task_identity"] == state["replacement"]["identity"]
    assert record["title_transition"] == state["replacement"]["title_transition"]
    assert record["lease_path"] == state_path.relative_to(tmp_path).as_posix()


@pytest.mark.parametrize(
    ("command_name", "locked_name"),
    [
        ("cmd_register_created", "_cmd_register_created_locked"),
        ("cmd_native_action", "_cmd_native_action_locked"),
        ("cmd_record_native_result", "_cmd_record_native_result_locked"),
        ("cmd_reconcile_native", "_cmd_reconcile_native_locked"),
    ],
)
def test_every_native_mutation_runs_inside_the_lineage_lock(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    command_name: str,
    locked_name: str,
) -> None:
    events: list[str] = []

    class RecordingLock:
        def __enter__(self) -> None:
            events.append("lock-entered")

        def __exit__(self, *_args: object) -> None:
            events.append("lock-exited")

    monkeypatch.setattr(th, "_rollover_mutation_lock_path", lambda _args: tmp_path / "lineage.lock")
    monkeypatch.setattr(th, "task_family_advisory_lock", lambda _path: RecordingLock())
    monkeypatch.setattr(th, locked_name, lambda _args: events.append("mutation") or 0)

    returncode = getattr(th, command_name)(SimpleNamespace())

    assert returncode == 0
    assert events == ["lock-entered", "mutation", "lock-exited"]


def bind_native_replacement(state: dict, thread_id: str) -> None:
    replacement = state["replacement"]
    replacement["native_lifecycle"]["replacement_thread_id"] = thread_id
    replacement["native_lifecycle"]["status"] = "title_reconciled"
    identity, transition = task_identity.bind_replacement(
        replacement["identity"],
        replacement["title_transition"],
        replacement_task_id=thread_id,
        evidence="test exact binding",
        now="2026-05-30T08:00:30Z",
    )
    identity, transition = task_identity.record_title_acknowledgement(
        identity,
        transition,
        replacement_task_id=thread_id,
        succeeded=True,
        evidence="test native title acknowledgement",
        error="",
        now="2026-05-30T08:00:40Z",
    )
    identity, transition = task_identity.record_title_readback(
        identity,
        transition,
        replacement_task_id=thread_id,
        observed_title=identity["visible_title"],
        succeeded=True,
        evidence="test exact title readback",
        error="",
        now="2026-05-30T08:00:50Z",
    )
    replacement["identity"] = identity
    replacement["title_transition"] = transition


def bind_native_lease(state_path: Path, thread_id: str) -> None:
    state = json.loads(state_path.read_text(encoding="utf-8"))
    bind_native_replacement(state, thread_id)
    th.write_json_atomic(state_path, state)


def resumed_with_proof(tmp_path: Path, state: dict, thread_id: str = "new-thread") -> tuple[dict, Path]:
    replacement = state["replacement"]
    bind_native_replacement(state, thread_id)
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


def filled_snapshot_from_template(template: dict) -> dict:
    """Model the two semantic fields the replacement is allowed to author."""
    snapshot = json.loads(json.dumps(template))
    for index, record in enumerate(snapshot["goals"], start=1):
        record["statement"] = f"goal {index}"
    for index, record in enumerate(snapshot["decision_records"], start=1):
        record["decision"] = f"decision {index}"
    for index, record in enumerate(snapshot["constraint_records"], start=1):
        record["prohibition"] = f"prohibition {index}"
    for index, record in enumerate(snapshot["next_actions"], start=1):
        record["action"] = f"action {index}"
    return snapshot


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
        timeout=30,
    )

    assert completed.returncode == 0, completed.stderr
    assert "Prepare and guard agent-specific thread handoffs." in completed.stdout
    for command in (
        "prepare",
        "repair-native-intent",
        "register-created",
        "bind-replacement",
        "native-action",
        "record-native-result",
        "reconcile-native",
        "confirm-started",
        "resume",
        "bootstrap-replacement",
        "confirm-replacement",
        "check",
        "audit",
    ):
        assert command in completed.stdout


def test_prepare_state_records_meaningful_title_and_native_identity():
    state = th.prepare_state(
        {"schema_version": th.SCHEMA_VERSION},
        agent="codex",
        now=datetime(2026, 5, 30, 8, 0, tzinfo=UTC),
        active_thread_id="source-thread",
        active_automation_id=None,
        context_percent=86.0,
        force_new_replacement=False,
        epic_title="Curriculum lifecycle",
        goal="CI unblock",
        phase="P5",
        next_phase="P6",
    )

    replacement = state["replacement"]
    assert replacement["display"]["title"] == "thread-rollover — CI unblock"
    assert replacement["display"]["title_source"] == "legacy-prepare-goal"
    assert replacement["identity"]["semantic_title"] == "CI unblock"
    assert replacement["native_lifecycle"] == {
        "family_id": replacement["native_lifecycle"]["family_id"],
        "operation_id": replacement["native_lifecycle"]["operation_id"],
        "source_thread_id": "source-thread",
        "replacement_thread_id": None,
        "status": "awaiting_native_create",
    }
    assert "Resume codex rollover" not in replacement["display"]["title"]


def test_prepare_state_uses_deterministic_non_generic_fallback():
    state = prepared(agent="codex", thread_id="source-thread")

    title = state["replacement"]["display"]["title"]
    assert title == "thread-rollover — Recover predecessor task context"
    assert state["lineage_id"] not in title
    assert "generation" not in title.casefold()
    assert title.casefold() != "resume codex rollover"


def test_prepare_state_rejects_partial_title_metadata():
    with pytest.raises(ValueError, match="must be supplied together"):
        th.prepare_state(
            {"schema_version": th.SCHEMA_VERSION},
            agent="codex",
            now=datetime(2026, 5, 30, 8, 0, tzinfo=UTC),
            active_thread_id="source-thread",
            active_automation_id=None,
            context_percent=None,
            force_new_replacement=False,
            epic_title="Curriculum lifecycle",
        )


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


def test_confirm_started_requires_exact_predecessor_identity(tmp_path: Path):
    state = prepared()
    resumed, proof_path = resumed_with_proof(tmp_path, state)
    strict_probe, strict_verdict = strict_artifacts(tmp_path, resumed)
    resumed.pop("active")

    with pytest.raises(ValueError, match="no exact predecessor"):
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


def test_handoff_policy_uses_recorded_actual_window_and_profile_tier(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("LEARN_UKRAINIAN_SESSION_ID", "recorded-sol-session")
    monkeypatch.setattr(
        session_record,
        "read_record",
        lambda session_id: {
            "session_id": session_id,
            "effective_profile_id": "sol_lead",
            "actual_context_window_tokens": 360_000,
            "actual_context_window_provenance": (
                "statusline.context_window.context_window_size"
            ),
            "rollover_warning_percentages": [75.0, 85.0, 92.0],
        },
    )

    assert th.resolve_handoff_policy(th.DEFAULT_CONTEXT_THRESHOLD) == (
        85.0,
        360_000,
        "sol_lead",
        "statusline.context_window.context_window_size",
    )


def test_handoff_policy_unknown_route_has_no_fabricated_window(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("LEARN_UKRAINIAN_SESSION_ID", raising=False)
    monkeypatch.setenv("LEARN_UKRAINIAN_REQUESTED_PROFILE_ID", "unknown-route")
    monkeypatch.setenv("LEARN_UKRAINIAN_MAIN_MODEL_ID", "unknown-model")

    assert th.resolve_handoff_policy(th.DEFAULT_CONTEXT_THRESHOLD) == (
        85.0,
        0,
        "fallback",
        "unavailable",
    )


def test_render_bootstrap_prompt_contains_guardrails(tmp_path: Path):
    now = datetime(2026, 5, 30, 8, 0, tzinfo=UTC)
    state = prepared()
    prompt = th.render_bootstrap_prompt(sample_snapshot(tmp_path), state, context_threshold=82.0)

    assert "You are the replacement Codex orchestrator thread." in prompt
    assert f"Task title: {state['replacement']['display']['title']}" in prompt
    assert "Role handoff: docs/session-state/codex-orchestrator-handoff.md" in prompt
    assert "Thread handoff: .agent/thread-rollovers/" in prompt
    assert "Global router:" not in prompt
    assert "Do not write docs/session-state/current.md for thread rollover." in prompt
    assert "git status --short --branch" in prompt
    assert "issue_stream_audit.py --json" in prompt
    assert "git worktree list" in prompt
    assert "detect --format session-start" in prompt
    assert "bootstrap-replacement" in prompt
    assert "confirm-replacement" in prompt
    assert "Only after that command reports old_automation_ready_to_delete=true" in prompt
    assert "If either fact is absent, use `unknown`" in prompt
    assert "Only an actionable response authorizes `set_thread_archived`" in prompt
    assert "must create and register this exact replacement" in prompt
    assert "exact readback before resume" in prompt
    assert (
        "Keep the invoking checkout clean at prepared HEAD abc123def0456789 through resume and confirmation (clean fast-forward advances are tolerated)."
        in prompt
    )
    assert "Context estimate: 86.0% (ROLL OVER NOW; threshold 82.0%)." in prompt
    assert "orchestrator_control.py inbox --recent 20 --include-results" in prompt


def test_render_current_markdown_includes_required_handoff_sections(tmp_path: Path):
    now = datetime(2026, 5, 30, 8, 0, tzinfo=UTC)
    state = prepared()
    rendered = th.render_current_markdown(sample_snapshot(tmp_path), state, context_threshold=82.0)

    assert "## Thread Lease" in rendered
    assert "## Task Identity" in rendered
    assert "## First-Turn Checklist" in rendered
    assert "issue_stream_audit.py --json" in rendered
    assert "## Rollover Command Capsule" in rendered
    assert "detect --format session-start" in rendered
    assert "context_canary.py mint" not in rendered
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
    assert "detect --format session-start" in rendered
    assert "confirm-replacement" in rendered


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


def _v2_lease(
    *,
    owner_thread_id: str = "old-owner",
    generation: int = 1,
    heartbeat_at: str = "2026-07-23T10:00:00Z",
    acquired_at: str = "2026-07-23T09:00:00Z",
    owner_pid: int = 4242,
    owner_pid_started_at: float = 1000.0,
    owner_machine_id: str = "machine-a",
    agent: str = "claude-infra",
) -> dict:
    return {
        "schema_version": 2,
        "agent": agent,
        "generation": generation,
        "owner_thread_id": owner_thread_id,
        "acquired_at": acquired_at,
        "heartbeat_at": heartbeat_at,
        "owner_pid": owner_pid,
        "owner_pid_started_at": owner_pid_started_at,
        "owner_machine_id": owner_machine_id,
    }


def _write_lease(tmp_path: Path, agent: str, lease: dict) -> Path:
    path = tmp_path / f".agent/{agent}-thread-lease.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(lease), encoding="utf-8")
    return path


def _fake_snapshot(**overrides) -> th.ProcessSnapshot:
    defaults = {"pid": 4242, "ppid": 1, "candidate_basenames": frozenset(), "started_at": 1000.0}
    defaults.update(overrides)
    return th.ProcessSnapshot(**defaults)


# --- claim_thread_lease: liveness-based takeover (test matrix items 1-13) ---


def test_dead_owner_fresh_clock_takes_over(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    """Matrix 1: today's user-facing bug — a dead owner must never lock out a restart."""
    now = datetime(2026, 7, 23, 10, 0, tzinfo=UTC)
    lease = _v2_lease(heartbeat_at="2026-07-23T09:59:00Z")  # 1 minute old: fresh under the old clock design
    lease_path = _write_lease(tmp_path, "claude-infra", lease)
    monkeypatch.setattr(th, "_default_machine_id", lambda: "machine-a")
    monkeypatch.setattr(th, "_process_is_alive", lambda pid: False)

    result = th.claim_thread_lease(
        state_root=tmp_path, agent="claude-infra", current_thread_id="new-owner", now=now, starting_pid=1
    )

    assert result["status"] == "acquired"
    assert result["generation"] == 2
    assert result["replaced_owner_thread_id"] == "old-owner"
    assert "not found" in result["takeover_reason"]
    on_disk = json.loads(lease_path.read_text(encoding="utf-8"))
    assert on_disk["owner_thread_id"] == "new-owner"
    assert on_disk["generation"] == 2


def test_live_owner_fresh_clock_conflicts(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    """Matrix 2: unchanged behavior — a genuinely live owner is never stolen from."""
    now = datetime(2026, 7, 23, 10, 0, tzinfo=UTC)
    lease = _v2_lease(heartbeat_at="2026-07-23T09:59:00Z")
    lease_path = _write_lease(tmp_path, "claude-infra", lease)
    monkeypatch.setattr(th, "_default_machine_id", lambda: "machine-a")
    monkeypatch.setattr(th, "_process_is_alive", lambda pid: True)
    monkeypatch.setattr(th, "_default_process_snapshot", lambda pid: _fake_snapshot(pid=pid))

    result = th.claim_thread_lease(
        state_root=tmp_path, agent="claude-infra", current_thread_id="new-owner", now=now, starting_pid=1
    )

    assert result["status"] == "conflict"
    assert result["liveness"] == "live_owner"
    assert result["owner_thread_id"] == "old-owner"
    assert json.loads(lease_path.read_text(encoding="utf-8"))["owner_thread_id"] == "old-owner"


def test_live_owner_beyond_old_clock_window_still_conflicts_not_stolen(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    """Matrix 3: today's opposite bug — a live owner working >12h must not be stolen from."""
    now = datetime(2026, 7, 23, 10, 0, tzinfo=UTC)
    lease = _v2_lease(heartbeat_at="2026-07-22T08:00:00Z")  # 26h old: reclaimable under the old clock-only design
    lease_path = _write_lease(tmp_path, "claude-infra", lease)
    monkeypatch.setattr(th, "_default_machine_id", lambda: "machine-a")
    monkeypatch.setattr(th, "_process_is_alive", lambda pid: True)
    monkeypatch.setattr(th, "_default_process_snapshot", lambda pid: _fake_snapshot(pid=pid))

    result = th.claim_thread_lease(
        state_root=tmp_path, agent="claude-infra", current_thread_id="new-owner", now=now, starting_pid=1
    )

    assert result["status"] == "conflict"
    assert result["liveness"] == "live_owner"
    assert json.loads(lease_path.read_text(encoding="utf-8"))["owner_thread_id"] == "old-owner"


def test_pid_reused_by_unrelated_process_takes_over(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    """Matrix 4: start-time mismatch means the pid was recycled — takeover regardless of clock age."""
    now = datetime(2026, 7, 23, 10, 0, tzinfo=UTC)
    lease = _v2_lease(heartbeat_at="2026-07-23T09:59:00Z", owner_pid_started_at=1000.0)
    lease_path = _write_lease(tmp_path, "claude-infra", lease)
    monkeypatch.setattr(th, "_default_machine_id", lambda: "machine-a")
    monkeypatch.setattr(th, "_process_is_alive", lambda pid: True)
    monkeypatch.setattr(th, "_default_process_snapshot", lambda pid: _fake_snapshot(pid=pid, started_at=5000.0))

    result = th.claim_thread_lease(
        state_root=tmp_path, agent="claude-infra", current_thread_id="new-owner", now=now, starting_pid=1
    )

    assert result["status"] == "acquired"
    assert "reused" in result["takeover_reason"]
    assert json.loads(lease_path.read_text(encoding="utf-8"))["owner_thread_id"] == "new-owner"


def test_start_time_within_the_same_whole_second_still_matches(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    """Fix 6: sub-second jitter between psutil and the ps-fallback probe must not look like reuse."""
    now = datetime(2026, 7, 23, 10, 0, tzinfo=UTC)
    lease = _v2_lease(heartbeat_at="2026-07-23T09:59:00Z", owner_pid_started_at=1000.9)
    lease_path = _write_lease(tmp_path, "claude-infra", lease)
    monkeypatch.setattr(th, "_default_machine_id", lambda: "machine-a")
    monkeypatch.setattr(th, "_process_is_alive", lambda pid: True)
    monkeypatch.setattr(th, "_default_process_snapshot", lambda pid: _fake_snapshot(pid=pid, started_at=1000.0))

    result = th.claim_thread_lease(
        state_root=tmp_path, agent="claude-infra", current_thread_id="new-owner", now=now, starting_pid=1
    )

    assert result["status"] == "conflict"
    assert result["liveness"] == "live_owner"
    assert json.loads(lease_path.read_text(encoding="utf-8"))["owner_thread_id"] == "old-owner"


def test_start_time_one_whole_second_apart_is_treated_as_pid_reuse(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    """Fix 6: exact whole-second comparison, not a 2s tolerance — a gap this small used to be
    (wrongly) absorbed by the old tolerance and would have missed a genuine pid reuse."""
    now = datetime(2026, 7, 23, 10, 0, tzinfo=UTC)
    lease = _v2_lease(heartbeat_at="2026-07-23T09:59:00Z", owner_pid_started_at=1000.0)
    lease_path = _write_lease(tmp_path, "claude-infra", lease)
    monkeypatch.setattr(th, "_default_machine_id", lambda: "machine-a")
    monkeypatch.setattr(th, "_process_is_alive", lambda pid: True)
    monkeypatch.setattr(th, "_default_process_snapshot", lambda pid: _fake_snapshot(pid=pid, started_at=1001.0))

    result = th.claim_thread_lease(
        state_root=tmp_path, agent="claude-infra", current_thread_id="new-owner", now=now, starting_pid=1
    )

    assert result["status"] == "acquired"
    assert "reused" in result["takeover_reason"]
    assert json.loads(lease_path.read_text(encoding="utf-8"))["owner_thread_id"] == "new-owner"


def test_legacy_v1_lease_with_fresh_heartbeat_conflicts_as_liveness_unknown(tmp_path: Path):
    """Matrix 5/6: an uncheckable owner (legacy v1 lease) is never taken over — a DIFFERENT
    thread id claiming it always conflicts and points at the operator force-release command."""
    now = datetime(2026, 7, 23, 10, 0, tzinfo=UTC)
    v1_lease = {
        "schema_version": 1,
        "agent": "claude-infra",
        "generation": 1,
        "owner_thread_id": "old-owner-v1",
        "acquired_at": "2026-07-23T09:55:00Z",
        "heartbeat_at": "2026-07-23T09:55:00Z",  # 5 minutes old
    }
    lease_path = _write_lease(tmp_path, "claude-infra", v1_lease)

    result = th.claim_thread_lease(
        state_root=tmp_path, agent="claude-infra", current_thread_id="new-owner", now=now, starting_pid=1
    )

    assert result["status"] == "conflict"
    assert result["liveness"] == "liveness_unknown"
    assert result["owner_thread_id"] == "old-owner-v1"
    assert json.loads(lease_path.read_text(encoding="utf-8"))["owner_thread_id"] == "old-owner-v1"


def test_uncheckable_lease_never_taken_over_regardless_of_clock_age(tmp_path: Path):
    """Fix 5 (design change, supersedes the 900s emergency TTL): this used to be the exact
    stuck-lease shape that healed via a clock-based takeover once the heartbeat aged past the
    TTL (formerly ``test_legacy_v1_lease_with_stale_heartbeat_is_healed_by_takeover``, deleted
    — it asserted status == "acquired" here, which is now the vulnerability, not the fix).
    Silently stealing from a possibly-live owner whose liveness just cannot be checked would
    corrupt the mutual exclusion this lease exists to provide, so a DIFFERENT thread id must
    conflict no matter how old the heartbeat is — there is no longer a clock that grants
    ownership to anyone. The legacy lease still heals, but only via the same-owner refresh
    upgrade path (see test_same_owner_refresh_upgrades_v1_lease_to_v2) or an explicit
    --force release, never via a timer."""
    now = datetime(2026, 7, 23, 10, 0, tzinfo=UTC)
    v1_lease = {
        "schema_version": 1,
        "agent": "claude-infra",
        "generation": 3,
        "owner_thread_id": "old-owner-v1",
        "acquired_at": "2026-07-22T01:00:00Z",
        "heartbeat_at": "2026-07-23T01:00:00Z",  # 9 hours old: reclaimable under the old TTL design
    }
    lease_path = _write_lease(tmp_path, "claude-infra", v1_lease)

    result = th.claim_thread_lease(
        state_root=tmp_path, agent="claude-infra", current_thread_id="new-owner", now=now, starting_pid=1
    )

    assert result["status"] == "conflict"
    assert result["liveness"] == "liveness_unknown"
    on_disk = json.loads(lease_path.read_text(encoding="utf-8"))
    assert on_disk["owner_thread_id"] == "old-owner-v1"  # untouched — no takeover happened
    assert on_disk["schema_version"] == 1  # not healed by this path either


def test_claim_thread_lease_has_no_emergency_ttl_parameter(tmp_path: Path):
    """Fix 5: the emergency TTL and its parameter are deleted outright, not merely unused —
    guards against a future reintroduction of clock-based takeover."""
    assert "emergency_ttl" not in inspect.signature(th.claim_thread_lease).parameters
    assert not hasattr(th, "DEFAULT_THREAD_LEASE_EMERGENCY_TTL_SECONDS")


def test_different_machine_id_is_uncheckable(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    """Matrix 7: a lease recorded on another machine can never be liveness-checked here."""
    now = datetime(2026, 7, 23, 10, 0, tzinfo=UTC)
    lease = _v2_lease(heartbeat_at="2026-07-23T09:55:00Z", owner_machine_id="machine-remote")
    _write_lease(tmp_path, "claude-infra", lease)
    monkeypatch.setattr(th, "_default_machine_id", lambda: "machine-local")

    result = th.claim_thread_lease(
        state_root=tmp_path, agent="claude-infra", current_thread_id="new-owner", now=now, starting_pid=1
    )

    assert result["status"] == "conflict"
    assert result["liveness"] == "liveness_unknown"


def test_liveness_probe_raising_never_escapes(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    """Matrix 8: a probe failure of any kind is an uncheckable verdict, never an exception."""
    now = datetime(2026, 7, 23, 10, 0, tzinfo=UTC)
    lease = _v2_lease(heartbeat_at="2026-07-23T09:55:00Z")
    _write_lease(tmp_path, "claude-infra", lease)
    monkeypatch.setattr(th, "_default_machine_id", lambda: "machine-a")

    def _boom(pid: int) -> bool:
        raise OSError("simulated probe failure")

    monkeypatch.setattr(th, "_process_is_alive", _boom)

    result = th.claim_thread_lease(
        state_root=tmp_path, agent="claude-infra", current_thread_id="new-owner", now=now, starting_pid=1
    )

    assert result["status"] == "conflict"
    assert result["liveness"] == "liveness_unknown"
    assert "probe raised" in result["reason"]


def test_eperm_from_os_kill_is_treated_as_alive_and_conflicts(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    """Matrix 9: EPERM means the process exists (owned by another user), not that it's dead."""

    def _raise_eperm(pid: int, sig: int) -> None:
        raise PermissionError("no permission")

    monkeypatch.setattr(th.os, "kill", _raise_eperm)
    assert th._process_is_alive(4242) is True  # unit-level: the EPERM branch itself

    now = datetime(2026, 7, 23, 10, 0, tzinfo=UTC)
    lease = _v2_lease(heartbeat_at="2026-07-23T09:55:00Z", owner_pid=4242, owner_pid_started_at=1000.0)
    _write_lease(tmp_path, "claude-infra", lease)
    monkeypatch.setattr(th, "_default_machine_id", lambda: "machine-a")
    monkeypatch.setattr(th, "_default_process_snapshot", lambda pid: _fake_snapshot(pid=pid))

    result = th.claim_thread_lease(
        state_root=tmp_path, agent="claude-infra", current_thread_id="new-owner", now=now, starting_pid=1
    )

    assert result["status"] == "conflict"
    assert result["liveness"] == "live_owner"


def test_process_is_alive_treats_zombie_as_dead(monkeypatch: pytest.MonkeyPatch):
    """Fix 4 (unit-level): kill(pid, 0) succeeds for a zombie — without a status check it
    would look identical to a live owner and conflict forever."""
    monkeypatch.setattr(th.os, "kill", lambda pid, sig: None)  # zombie: kill(0) still succeeds
    monkeypatch.setattr(th, "_process_is_zombie", lambda pid: True)

    assert th._process_is_alive(4242) is False


def test_zombie_owner_is_reclaimed_not_treated_as_live(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    """Fix 4: a zombie owner must be reclaimable immediately, exactly like a confirmed-dead one —
    otherwise it recreates the original lockout (a dead-looking owner blocking every restart)."""
    now = datetime(2026, 7, 23, 10, 0, tzinfo=UTC)
    lease = _v2_lease(heartbeat_at="2026-07-23T09:59:00Z")  # fresh under the old clock-only design
    lease_path = _write_lease(tmp_path, "claude-infra", lease)
    monkeypatch.setattr(th, "_default_machine_id", lambda: "machine-a")
    monkeypatch.setattr(th.os, "kill", lambda pid, sig: None)
    monkeypatch.setattr(th, "_process_is_zombie", lambda pid: True)

    result = th.claim_thread_lease(
        state_root=tmp_path, agent="claude-infra", current_thread_id="new-owner", now=now, starting_pid=1
    )

    assert result["status"] == "acquired"
    assert result["generation"] == 2
    assert json.loads(lease_path.read_text(encoding="utf-8"))["owner_thread_id"] == "new-owner"


def test_malformed_v2_liveness_fields_are_uncheckable_not_raised(tmp_path: Path):
    """Matrix 10: a malformed individual field degrades to uncheckable, never raises."""
    now = datetime(2026, 7, 23, 10, 0, tzinfo=UTC)
    lease = _v2_lease(heartbeat_at="2026-07-23T09:55:00Z")
    lease["owner_pid"] = "not-an-int"
    _write_lease(tmp_path, "claude-infra", lease)

    result = th.claim_thread_lease(
        state_root=tmp_path, agent="claude-infra", current_thread_id="new-owner", now=now, starting_pid=1
    )

    assert result["status"] == "conflict"
    assert result["liveness"] == "liveness_unknown"


def test_unknown_future_schema_version_is_uncheckable_not_raised(tmp_path: Path):
    """Matrix 11: SessionStart must never be blocked by a schema version this code predates."""
    now = datetime(2026, 7, 23, 10, 0, tzinfo=UTC)
    lease = _v2_lease(heartbeat_at="2026-07-23T09:55:00Z")
    lease["schema_version"] = 3
    _write_lease(tmp_path, "claude-infra", lease)

    result = th.claim_thread_lease(
        state_root=tmp_path, agent="claude-infra", current_thread_id="new-owner", now=now, starting_pid=1
    )

    assert result["status"] == "conflict"
    assert result["liveness"] == "liveness_unknown"


def test_corrupt_json_lease_heals_via_fresh_acquire(tmp_path: Path):
    """Matrix 12: unreadable/corrupt state is recoverable, never a reason to raise and block."""
    now = datetime(2026, 7, 23, 10, 0, tzinfo=UTC)
    lease_path = tmp_path / ".agent/claude-infra-thread-lease.json"
    lease_path.parent.mkdir(parents=True)
    lease_path.write_text("{not-valid-json", encoding="utf-8")

    result = th.claim_thread_lease(
        state_root=tmp_path, agent="claude-infra", current_thread_id="new-owner", now=now, starting_pid=1
    )

    assert result["status"] == "acquired"
    assert result["generation"] == 1
    assert "recovered_from_corrupt_lease" in result
    on_disk = json.loads(lease_path.read_text(encoding="utf-8"))
    assert on_disk["owner_thread_id"] == "new-owner"
    assert on_disk["schema_version"] == 2


def test_same_owner_resume_of_uncheckable_v2_lease_reacquires_with_new_generation(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    """A v2 lease with no usable identity must NOT keep its generation on an explicit resume.

    Cross-family review finding F002 (gpt-5.6-sol, PR #5758). The v1->v2 upgrade concession is
    safe only because a v1 lease predates the generation export, so its predecessor cannot hold
    a generation to release with. A v2 lease whose liveness fields are absent is different: its
    predecessor ran under this schema and may already have exported generation 2, so preserving
    it would let that dead predecessor's delayed SessionEnd pass release fencing and delete THIS
    process's live lease.
    """
    now = datetime(2026, 7, 25, 10, 0, tzinfo=UTC)
    uncheckable_v2 = {
        "schema_version": th.THREAD_LEASE_SCHEMA_VERSION,
        "agent": "claude-infra",
        "generation": 2,
        "owner_thread_id": "same-owner",
        "acquired_at": "2026-07-25T09:00:00Z",
        "heartbeat_at": "2026-07-25T09:00:00Z",
        # v2, but carries no owner_pid/owner_pid_started_at/owner_machine_id — nothing to probe.
    }
    lease_path = _write_lease(tmp_path, "claude-infra", uncheckable_v2)
    monkeypatch.setattr(
        th,
        "_derive_owner_liveness_fields",
        lambda starting_pid: {"owner_pid": 777, "owner_pid_started_at": 99.0, "owner_machine_id": "machine-a"},
    )

    result = th.claim_thread_lease(
        state_root=tmp_path, agent="claude-infra", current_thread_id="same-owner", now=now, starting_pid=1
    )

    # The generation MUST advance: absence of proof is not proof of continuity.
    assert result["generation"] == 3, "an uncheckable v2 lease must reacquire, not refresh in place"
    on_disk = json.loads(lease_path.read_text(encoding="utf-8"))
    assert on_disk["generation"] == 3
    assert on_disk["owner_pid"] == 777
    assert on_disk["owner_machine_id"] == "machine-a"


def test_same_owner_refresh_upgrades_v1_lease_to_v2(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    """Matrix 13 / rule E: a same-owner refresh must not leave a v1 lease stuck on the fallback path."""
    now = datetime(2026, 7, 23, 10, 0, tzinfo=UTC)
    v1_lease = {
        "schema_version": 1,
        "agent": "claude-infra",
        "generation": 2,
        "owner_thread_id": "same-owner",
        "acquired_at": "2026-07-23T09:00:00Z",
        "heartbeat_at": "2026-07-23T09:00:00Z",
    }
    lease_path = _write_lease(tmp_path, "claude-infra", v1_lease)
    monkeypatch.setattr(
        th,
        "_derive_owner_liveness_fields",
        lambda starting_pid: {"owner_pid": 555, "owner_pid_started_at": 42.0, "owner_machine_id": "machine-a"},
    )

    result = th.claim_thread_lease(
        state_root=tmp_path, agent="claude-infra", current_thread_id="same-owner", now=now, starting_pid=1
    )

    assert result["status"] == "refreshed"
    assert result["generation"] == 2
    on_disk = json.loads(lease_path.read_text(encoding="utf-8"))
    assert on_disk["schema_version"] == 2
    assert on_disk["owner_pid"] == 555
    assert on_disk["owner_machine_id"] == "machine-a"
    assert on_disk["acquired_at"] == "2026-07-23T09:00:00Z"  # preserved across the v1->v2 upgrade
    assert on_disk["heartbeat_at"] == "2026-07-23T10:00:00Z"  # refreshed


def test_same_thread_id_with_matching_process_identity_preserves_generation(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    """Fix 2 (regression guard): a genuine resume by the SAME process must stay on the fast,
    generation-preserving refresh path — only an identity CHANGE should force a reacquire."""
    now = datetime(2026, 7, 23, 10, 0, tzinfo=UTC)
    lease = _v2_lease(owner_thread_id="resumed-thread", generation=3, owner_pid=111, owner_pid_started_at=1000.0)
    _write_lease(tmp_path, "claude-infra", lease)
    monkeypatch.setattr(th, "_default_machine_id", lambda: "machine-a")
    monkeypatch.setattr(
        th,
        "_derive_owner_liveness_fields",
        lambda starting_pid: {"owner_pid": 111, "owner_pid_started_at": 1000.0, "owner_machine_id": "machine-a"},
    )

    result = th.claim_thread_lease(
        state_root=tmp_path, agent="claude-infra", current_thread_id="resumed-thread", now=now, starting_pid=111
    )

    assert result["status"] == "refreshed"
    assert result["generation"] == 3


def test_same_thread_id_with_changed_process_identity_increments_generation(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    """Fix 2: resuming the same thread id under a NEW harness process (different pid/start
    time) must NOT silently preserve generation. If it did, the dead predecessor process —
    which cached the OLD generation from its own SessionStart — could still release-fence
    its way past a late SessionEnd and delete the SUCCESSOR's live lease. (The release-side
    consequence of this exact scenario, with pid-sensitive identity mocking, is
    test_resume_aba_late_release_from_dead_predecessor_is_fenced_by_identity_and_generation
    below — this test's blanket-identity mock, which ignores the calling starting_pid, cannot
    faithfully simulate release's own identity check.)"""
    now = datetime(2026, 7, 23, 10, 0, tzinfo=UTC)
    lease = _v2_lease(owner_thread_id="resumed-thread", generation=1, owner_pid=111, owner_pid_started_at=1000.0)
    lease_path = _write_lease(tmp_path, "claude-infra", lease)
    monkeypatch.setattr(th, "_default_machine_id", lambda: "machine-a")
    # The predecessor process (pid 111) is gone; a NEW process (pid 222) resumes the thread id.
    monkeypatch.setattr(
        th,
        "_derive_owner_liveness_fields",
        lambda starting_pid: {"owner_pid": 222, "owner_pid_started_at": 5000.0, "owner_machine_id": "machine-a"},
    )

    result = th.claim_thread_lease(
        state_root=tmp_path, agent="claude-infra", current_thread_id="resumed-thread", now=now, starting_pid=222
    )

    assert result["status"] == "acquired"
    assert result["generation"] == 2
    on_disk = json.loads(lease_path.read_text(encoding="utf-8"))
    assert on_disk["generation"] == 2
    assert on_disk["owner_pid"] == 222


def test_resume_aba_late_release_from_dead_predecessor_is_fenced_by_identity_and_generation(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    """Resume-ABA: claim(T, proc A) -> identity-changed reacquire(T, proc B) at gen+1 -> a late
    release from a process presenting A's identity, carrying A's stale generation, must no-op —
    release is now itself identity-gated (item 2), doubly fencing this exact scenario. The
    successor's lease must survive both fences."""
    now = datetime(2026, 7, 23, 10, 0, tzinfo=UTC)
    lease = _v2_lease(owner_thread_id="resumed-thread", generation=1, owner_pid=111, owner_pid_started_at=1000.0)
    lease_path = _write_lease(tmp_path, "claude-infra", lease)
    monkeypatch.setattr(th, "_default_machine_id", lambda: "machine-a")
    identities = {111: (111, 1000.0), 222: (222, 5000.0)}
    monkeypatch.setattr(
        th,
        "_derive_owner_liveness_fields",
        lambda starting_pid: {
            "owner_pid": identities[starting_pid][0],
            "owner_pid_started_at": identities[starting_pid][1],
            "owner_machine_id": "machine-a",
        },
    )

    result = th.claim_thread_lease(
        state_root=tmp_path, agent="claude-infra", current_thread_id="resumed-thread", now=now, starting_pid=222
    )
    assert result["status"] == "acquired"
    assert result["generation"] == 2
    on_disk = json.loads(lease_path.read_text(encoding="utf-8"))
    assert on_disk["generation"] == 2
    assert on_disk["owner_pid"] == 222

    # Process A's late SessionEnd: presents A's own real identity (pid 111) and carries A's
    # stale generation 1 — identity mismatches the current (B's) record, so this falls through
    # to the generation fence, which also fails (1 != 2).
    late_release = th.release_thread_lease(
        state_root=tmp_path,
        agent="claude-infra",
        current_thread_id="resumed-thread",
        now=now,
        generation=1,
        starting_pid=111,
    )
    assert late_release["status"] == "noop"
    assert json.loads(lease_path.read_text(encoding="utf-8"))["generation"] == 2

    # Process B's own release, presenting its own real identity, succeeds WITHOUT even
    # supplying a generation — identity proof alone is a sufficient, stronger fence (item 2).
    own_release = th.release_thread_lease(
        state_root=tmp_path, agent="claude-infra", current_thread_id="resumed-thread", now=now, starting_pid=222
    )
    assert own_release["status"] == "released"
    tombstone = json.loads(lease_path.read_text(encoding="utf-8"))
    assert tombstone["state"] == "released"
    assert tombstone["generation"] == 2
    assert tombstone["released_by_thread_id"] == "resumed-thread"


def test_same_thread_id_with_unresolvable_new_identity_reacquires_defensively(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    """Fix 2: when the recorded identity is checkable but a fresh probe cannot confirm it still
    matches (e.g. the harness-ancestor walk fails this time), continuity must NOT be assumed —
    assuming it would recreate the exact vulnerability finding 2 describes."""
    now = datetime(2026, 7, 23, 10, 0, tzinfo=UTC)
    lease = _v2_lease(owner_thread_id="resumed-thread", generation=1, owner_pid=111, owner_pid_started_at=1000.0)
    lease_path = _write_lease(tmp_path, "claude-infra", lease)
    monkeypatch.setattr(th, "_default_machine_id", lambda: "machine-a")
    monkeypatch.setattr(th, "_derive_owner_liveness_fields", lambda starting_pid: {})

    result = th.claim_thread_lease(
        state_root=tmp_path, agent="claude-infra", current_thread_id="resumed-thread", now=now, starting_pid=999
    )

    assert result["status"] == "acquired"
    assert result["generation"] == 2
    assert json.loads(lease_path.read_text(encoding="utf-8"))["generation"] == 2


# --- release_thread_lease: fencing (test matrix items 14-16) ---


def test_release_without_proof_or_generation_is_a_noop(tmp_path: Path):
    """Item 2: generation is no longer unconditionally mandatory — identity proof
    (require_proof=True) is the stronger fence and makes it optional. But when identity
    canNOT be reconfirmed (as here: no machine-id/process mocking, so the lease is
    uncheckable in this test process) AND no generation is supplied either, this must fail
    closed as an explicit no-op — never a silent release, and (unlike the old design) never
    a raised exception that would crash a caller that forgot to special-case it."""
    now = datetime(2026, 7, 23, 10, 0, tzinfo=UTC)
    lease = _v2_lease(owner_thread_id="real-owner", generation=1)
    lease_path = _write_lease(tmp_path, "claude-infra", lease)

    result = th.release_thread_lease(state_root=tmp_path, agent="claude-infra", current_thread_id="real-owner", now=now)

    assert result["status"] == "noop"
    assert "generation" in result["reason"]
    on_disk = json.loads(lease_path.read_text(encoding="utf-8"))
    assert on_disk["owner_thread_id"] == "real-owner"
    assert on_disk.get("state") != "released"


def test_release_with_proven_identity_and_no_generation_succeeds(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    """Item 2: when this process's identity IS reconfirmed against the lease, generation is
    genuinely optional — proof alone is a sufficient, stronger fence. Mutation check: without
    the identity-proof branch (i.e. reverting to the old owner+generation-only fence), this
    call would incorrectly raise/refuse since no generation is supplied."""
    now = datetime(2026, 7, 23, 10, 0, tzinfo=UTC)
    lease = _v2_lease(owner_thread_id="real-owner", generation=4, owner_pid=111, owner_pid_started_at=1000.0)
    lease_path = _write_lease(tmp_path, "claude-infra", lease)
    monkeypatch.setattr(th, "_default_machine_id", lambda: "machine-a")
    monkeypatch.setattr(
        th,
        "_derive_owner_liveness_fields",
        lambda starting_pid: {"owner_pid": 111, "owner_pid_started_at": 1000.0, "owner_machine_id": "machine-a"},
    )

    result = th.release_thread_lease(
        state_root=tmp_path, agent="claude-infra", current_thread_id="real-owner", now=now, starting_pid=111
    )

    assert result["status"] == "released"
    tombstone = json.loads(lease_path.read_text(encoding="utf-8"))
    assert tombstone["state"] == "released"
    assert tombstone["generation"] == 4
    assert tombstone["released_by_thread_id"] == "real-owner"
    assert tombstone["owner_pid"] == 111  # prior identity fields preserved as evidence


def test_release_by_non_owner_is_noop(tmp_path: Path):
    """Matrix 14: release never touches a lease it does not own."""
    now = datetime(2026, 7, 23, 10, 0, tzinfo=UTC)
    lease = _v2_lease(owner_thread_id="real-owner", generation=1)
    lease_path = _write_lease(tmp_path, "claude-infra", lease)

    result = th.release_thread_lease(
        state_root=tmp_path, agent="claude-infra", current_thread_id="impostor", now=now, generation=1
    )

    assert result["status"] == "noop"
    assert json.loads(lease_path.read_text(encoding="utf-8"))["owner_thread_id"] == "real-owner"


def test_release_after_takeover_is_fenced_by_owner_and_generation(tmp_path: Path):
    """Matrix 15: a stale former owner's late SessionEnd must not clobber the new owner's lease."""
    now = datetime(2026, 7, 23, 10, 0, tzinfo=UTC)
    # On-disk state after a real takeover: "new-owner" now holds generation 2.
    current_lease = _v2_lease(owner_thread_id="new-owner", generation=2)
    lease_path = _write_lease(tmp_path, "claude-infra", current_lease)

    # The old owner's late SessionEnd, still believing it holds generation 1.
    result = th.release_thread_lease(
        state_root=tmp_path, agent="claude-infra", current_thread_id="old-owner", now=now, generation=1
    )

    assert result["status"] == "noop"
    on_disk = json.loads(lease_path.read_text(encoding="utf-8"))
    assert on_disk["owner_thread_id"] == "new-owner"
    assert on_disk["generation"] == 2

    # Generation fencing also holds even when the owner_thread_id happens to match.
    result_same_owner_wrong_generation = th.release_thread_lease(
        state_root=tmp_path, agent="claude-infra", current_thread_id="new-owner", now=now, generation=1
    )
    assert result_same_owner_wrong_generation["status"] == "noop"
    assert json.loads(lease_path.read_text(encoding="utf-8"))["generation"] == 2


def test_release_thread_lease_takes_the_advisory_lock(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    """Matrix 16: an unlocked release could lose updates or clobber a newer generation."""
    events: list[str] = []

    class RecordingLock:
        def __enter__(self) -> None:
            events.append("lock-entered")

        def __exit__(self, *_args: object) -> None:
            events.append("lock-exited")

    monkeypatch.setattr(th, "task_family_advisory_lock", lambda _path: RecordingLock())

    now = datetime(2026, 7, 23, 10, 0, tzinfo=UTC)
    result = th.release_thread_lease(
        state_root=tmp_path, agent="claude-infra", current_thread_id="whoever", now=now, generation=1
    )

    assert result["status"] == "noop"  # no lease file exists — the lock must still be taken
    assert events == ["lock-entered", "lock-exited"]


def test_force_release_bare_is_refused(tmp_path: Path):
    """Item 6: a bare --force (no CAS expectations) is refused, never an unscoped delete —
    it must instead echo back the exact pre-filled CAS command using the CURRENT on-disk
    owner/generation. Mutation check: without the unscoped-refusal branch, this would fall
    straight through to an unconditional release exactly like the old bare --force design."""
    now = datetime(2026, 7, 23, 10, 0, tzinfo=UTC)
    lease = _v2_lease(owner_thread_id="somebody-else", generation=5)
    lease_path = _write_lease(tmp_path, "claude-infra", lease)

    result = th.release_thread_lease(state_root=tmp_path, agent="claude-infra", current_thread_id="", now=now, force=True)

    assert result["status"] == "refused"
    assert result["error_code"] == "THREAD_LEASE_FORCE_UNSCOPED"
    assert "--expect-owner-thread-id somebody-else" in result["resolution"]
    assert "--expect-generation 5" in result["resolution"]
    on_disk = json.loads(lease_path.read_text(encoding="utf-8"))
    assert on_disk["owner_thread_id"] == "somebody-else"  # untouched


def test_force_release_with_wrong_expectations_is_refused(tmp_path: Path):
    """Item 6: CAS expectations that don't match the current lease are refused, showing the
    real current state — a stale copy-pasted force command must never silently no-op-succeed
    against a lease it no longer describes."""
    now = datetime(2026, 7, 23, 10, 0, tzinfo=UTC)
    lease = _v2_lease(owner_thread_id="somebody-else", generation=5)
    lease_path = _write_lease(tmp_path, "claude-infra", lease)

    result = th.release_thread_lease(
        state_root=tmp_path,
        agent="claude-infra",
        current_thread_id="",
        now=now,
        force=True,
        expect_owner_thread_id="somebody-else",
        expect_generation=4,  # stale
    )

    assert result["status"] == "refused"
    assert result["error_code"] == "THREAD_LEASE_FORCE_MISMATCH"
    assert result["current_generation"] == 5
    assert json.loads(lease_path.read_text(encoding="utf-8"))["owner_thread_id"] == "somebody-else"


def test_force_release_with_live_owner_requires_acknowledgement(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    """Item 6: correct CAS expectations still refuse a verifiably-alive owner unless the
    operator explicitly acknowledges it — a force release must never be a silent way to
    steal from a session that is provably still running."""
    now = datetime(2026, 7, 23, 10, 0, tzinfo=UTC)
    lease = _v2_lease(owner_thread_id="somebody-else", generation=5, owner_pid=4242, owner_pid_started_at=1000.0)
    lease_path = _write_lease(tmp_path, "claude-infra", lease)
    monkeypatch.setattr(th, "_default_machine_id", lambda: "machine-a")
    monkeypatch.setattr(th, "_process_is_alive", lambda pid: True)
    monkeypatch.setattr(th, "_default_process_snapshot", lambda pid: _fake_snapshot(pid=pid))

    refused = th.release_thread_lease(
        state_root=tmp_path,
        agent="claude-infra",
        current_thread_id="",
        now=now,
        force=True,
        expect_owner_thread_id="somebody-else",
        expect_generation=5,
    )
    assert refused["status"] == "refused"
    assert refused["error_code"] == "THREAD_LEASE_FORCE_LIVE_OWNER"
    assert json.loads(lease_path.read_text(encoding="utf-8"))["owner_thread_id"] == "somebody-else"

    acknowledged = th.release_thread_lease(
        state_root=tmp_path,
        agent="claude-infra",
        current_thread_id="",
        now=now,
        force=True,
        expect_owner_thread_id="somebody-else",
        expect_generation=5,
        acknowledge_live_owner=True,
    )
    assert acknowledged["status"] == "released"
    assert acknowledged["forced"] is True
    tombstone = json.loads(lease_path.read_text(encoding="utf-8"))
    assert tombstone["state"] == "released"
    assert tombstone["generation"] == 5


def test_force_release_with_correct_cas_succeeds(tmp_path: Path):
    """Item 6: the exact CAS-scoped command (correct owner + generation, owner not
    verifiably alive) succeeds and writes a tombstone rather than deleting the file."""
    now = datetime(2026, 7, 23, 10, 0, tzinfo=UTC)
    lease = _v2_lease(owner_thread_id="somebody-else", generation=5)
    lease_path = _write_lease(tmp_path, "claude-infra", lease)

    result = th.release_thread_lease(
        state_root=tmp_path,
        agent="claude-infra",
        current_thread_id="",
        now=now,
        force=True,
        expect_owner_thread_id="somebody-else",
        expect_generation=5,
    )

    assert result["status"] == "released"
    assert result["forced"] is True
    tombstone = json.loads(lease_path.read_text(encoding="utf-8"))
    assert tombstone["state"] == "released"
    assert tombstone["generation"] == 5
    assert tombstone["released_forced"] is True


# --- released tombstone: monotonic generation, no unlink (item 3) ---


def test_tombstone_monotonic_generation_across_claim_release_claim(tmp_path: Path):
    """Item 3: claim -> release -> claim strictly increases generation and NEVER resets to 1
    while a tombstone exists — the tombstone is durable evidence of the last generation, not
    an absent-file fresh start. Mutation check: reverting the tombstone-reclaim branch to
    treat a released record as absent would incorrectly restart at generation 1."""
    now = datetime(2026, 7, 23, 10, 0, tzinfo=UTC)

    first_claim = th.claim_thread_lease(
        state_root=tmp_path, agent="claude-infra", current_thread_id="first-owner", now=now, starting_pid=1
    )
    assert first_claim["status"] == "acquired"
    assert first_claim["generation"] == 1

    release = th.release_thread_lease(
        state_root=tmp_path,
        agent="claude-infra",
        current_thread_id="first-owner",
        now=now,
        generation=1,
        starting_pid=1,
    )
    assert release["status"] == "released"
    lease_path = tmp_path / ".agent/claude-infra-thread-lease.json"
    tombstone = json.loads(lease_path.read_text(encoding="utf-8"))
    assert tombstone["state"] == "released"
    assert tombstone["generation"] == 1

    second_claim = th.claim_thread_lease(
        state_root=tmp_path, agent="claude-infra", current_thread_id="second-owner", now=now, starting_pid=1
    )
    assert second_claim["status"] == "acquired"
    assert second_claim["generation"] == 2  # monotonic, never reset to 1
    on_disk = json.loads(lease_path.read_text(encoding="utf-8"))
    assert on_disk["generation"] == 2
    assert on_disk["owner_thread_id"] == "second-owner"
    assert on_disk.get("state") != "released"


def test_stale_release_against_a_tombstone_is_noop(tmp_path: Path):
    """Item 3: a second (e.g. duplicate/late) release call against an already-released
    tombstone must no-op — there is nothing left to release, and it must never re-derive or
    rewrite the tombstone."""
    now = datetime(2026, 7, 23, 10, 0, tzinfo=UTC)
    lease = _v2_lease(owner_thread_id="real-owner", generation=3)
    lease_path = _write_lease(tmp_path, "claude-infra", lease)

    first_release = th.release_thread_lease(
        state_root=tmp_path, agent="claude-infra", current_thread_id="real-owner", now=now, generation=3
    )
    assert first_release["status"] == "released"
    tombstone_before = lease_path.read_text(encoding="utf-8")

    stale_release = th.release_thread_lease(
        state_root=tmp_path, agent="claude-infra", current_thread_id="real-owner", now=now, generation=3
    )

    assert stale_release["status"] == "noop"
    assert "already released" in stale_release["reason"]
    assert lease_path.read_text(encoding="utf-8") == tombstone_before  # byte-identical, never rewritten


# --- harness-ancestor walk (test matrix items 17-18) ---


def test_ancestor_walk_skips_transient_subshell_and_finds_harness():
    """Matrix 17: a fake process table, no shelling out — the launcher subshell must be skipped."""
    table = {
        100: _fake_snapshot(pid=100, ppid=200, candidate_basenames=frozenset({"python3.12"}), started_at=10.0),
        200: _fake_snapshot(pid=200, ppid=300, candidate_basenames=frozenset({"bash"}), started_at=9.0),
        300: _fake_snapshot(pid=300, ppid=1, candidate_basenames=frozenset({"claude"}), started_at=1.0),
    }

    ancestor = th._find_harness_ancestor(100, process_snapshot=lambda pid: table.get(pid))

    assert ancestor is not None
    assert ancestor.pid == 300
    assert ancestor.started_at == 1.0


def test_ancestor_walk_with_no_harness_ancestor_records_no_liveness_fields(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    """Matrix 18: no known-harness ancestor means the uncheckable path, never a guessed pid."""
    table = {
        100: _fake_snapshot(pid=100, ppid=200, candidate_basenames=frozenset({"python3.12"}), started_at=10.0),
        200: _fake_snapshot(pid=200, ppid=1, candidate_basenames=frozenset({"launchd"}), started_at=1.0),
    }

    ancestor = th._find_harness_ancestor(100, process_snapshot=lambda pid: table.get(pid))
    assert ancestor is None

    fields = th._derive_owner_liveness_fields(100, process_snapshot=lambda pid: table.get(pid))
    assert fields == {}

    now = datetime(2026, 7, 23, 10, 0, tzinfo=UTC)
    monkeypatch.setattr(th, "_default_process_snapshot", lambda pid: table.get(pid))
    result = th.claim_thread_lease(
        state_root=tmp_path, agent="claude-infra", current_thread_id="fresh-owner", now=now, starting_pid=100
    )

    assert result["status"] == "acquired"
    assert result["liveness_fields_recorded"] is False
    on_disk = json.loads((tmp_path / ".agent/claude-infra-thread-lease.json").read_text(encoding="utf-8"))
    assert "owner_pid" not in on_disk


def test_claim_thread_lease_command_reports_a_clear_double_launch_conflict(tmp_path: Path, capsys):
    """CLI-level: deterministic across environments via --starting-pid 1 (never a known harness)."""
    command = [
        "--repo-root",
        str(tmp_path),
        "claim-thread-lease",
        "--agent",
        "claude-infra",
        "--starting-pid",
        "1",
        "--current-thread-id",
    ]

    assert th.main([*command, "first-session"]) == 0
    capsys.readouterr()
    assert th.main([*command, "second-session"]) == 2

    payload = json.loads(capsys.readouterr().out)
    assert payload["error_code"] == "THREAD_LEASE_LIVENESS_UNKNOWN"
    assert payload["owner_thread_id"] == "first-session"
    assert "stop to avoid double-driving" in payload["error"]
    assert "release-thread-lease" in payload["resolution"]


def test_claim_thread_lease_command_reports_structured_lock_timeout(
    tmp_path: Path, capsys, monkeypatch: pytest.MonkeyPatch
):
    def raise_timeout(_: Path) -> None:
        raise TimeoutError("timed out waiting for local state lock")

    monkeypatch.setattr(th, "task_family_advisory_lock", raise_timeout)

    assert th.main(
        [
            "--repo-root",
            str(tmp_path),
            "claim-thread-lease",
            "--agent",
            "claude-infra",
            "--current-thread-id",
            "session-under-lock",
        ]
    ) == 124
    payload = json.loads(capsys.readouterr().out)
    assert payload == {
        "error_code": "LOCK_TIMEOUT",
        "error": "timed out waiting for local state lock",
    }


def test_release_thread_lease_command_end_to_end(tmp_path: Path, capsys):
    """CLI-level: claim then release through the same subcommands a real hook would call.
    Release now writes a tombstone (item 3) rather than deleting the lease file."""
    repo_args = ["--repo-root", str(tmp_path)]

    assert th.main([*repo_args, "claim-thread-lease", "--agent", "claude-infra", "--starting-pid", "1",
                     "--current-thread-id", "cli-session"]) == 0
    claim_payload = json.loads(capsys.readouterr().out)

    assert th.main([*repo_args, "release-thread-lease", "--agent", "claude-infra",
                     "--current-thread-id", "cli-session",
                     "--generation", str(claim_payload["generation"])]) == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["status"] == "released"
    tombstone = json.loads((tmp_path / ".agent/claude-infra-thread-lease.json").read_text(encoding="utf-8"))
    assert tombstone["state"] == "released"
    assert tombstone["generation"] == claim_payload["generation"]


def test_release_thread_lease_command_without_generation_or_proof_is_a_noop(tmp_path: Path, capsys):
    """Item 2: --generation is no longer unconditionally required — but with neither a
    generation NOR a reconfirmable process identity (as here: --starting-pid 1 is never a
    known harness, matching the double-launch-conflict test's convention), the release must
    fail closed as an explicit no-op (exit 0, status noop) rather than releasing or raising."""
    repo_args = ["--repo-root", str(tmp_path)]

    assert th.main([*repo_args, "claim-thread-lease", "--agent", "claude-infra", "--starting-pid", "1",
                     "--current-thread-id", "cli-session"]) == 0
    capsys.readouterr()

    assert th.main([*repo_args, "release-thread-lease", "--agent", "claude-infra",
                     "--current-thread-id", "cli-session"]) == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["status"] == "noop"
    assert "generation" in payload["reason"]
    # Untouched: the lease must survive an attempted release with no generation or proof.
    on_disk = json.loads((tmp_path / ".agent/claude-infra-thread-lease.json").read_text(encoding="utf-8"))
    assert on_disk["owner_thread_id"] == "cli-session"
    assert on_disk.get("state") != "released"


def test_refresh_thread_lease_heartbeat_command_is_noop_for_a_different_owner(tmp_path: Path, capsys):
    """Rule G: the Stop-hook heartbeat refresh must never take over — only ever refresh its own lease."""
    repo_args = ["--repo-root", str(tmp_path)]
    assert th.main([*repo_args, "claim-thread-lease", "--agent", "claude-infra", "--starting-pid", "1",
                     "--current-thread-id", "owner-session"]) == 0
    capsys.readouterr()

    assert th.main([*repo_args, "refresh-thread-lease-heartbeat", "--agent", "claude-infra",
                     "--current-thread-id", "someone-else", "--starting-pid", "1",
                     "--generation", "1"]) == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["status"] == "noop"
    assert json.loads((tmp_path / ".agent/claude-infra-thread-lease.json").read_text())["owner_thread_id"] == (
        "owner-session"
    )


def test_refresh_thread_lease_heartbeat_is_noop_for_a_stale_generation(tmp_path: Path):
    """Fix 2: a takeover that resumes the SAME thread id under a NEW process bumps generation
    but keeps the old thread id — a late heartbeat call still in flight from the dead
    predecessor process, carrying the OLD generation it cached, must not rewrite the
    successor's recorded process identity just because the thread id still matches."""
    now = datetime(2026, 7, 23, 10, 0, tzinfo=UTC)
    lease = _v2_lease(owner_thread_id="resumed-thread", generation=2, owner_pid=222, owner_pid_started_at=5000.0)
    lease_path = _write_lease(tmp_path, "claude-infra", lease)
    original = lease_path.read_text(encoding="utf-8")

    result = th.refresh_thread_lease_heartbeat(
        state_root=tmp_path,
        agent="claude-infra",
        current_thread_id="resumed-thread",
        generation=1,  # the dead predecessor's stale, cached generation
        now=now,
        starting_pid=111,  # the dead predecessor's own pid
    )

    assert result["status"] == "noop"
    assert "generation" in result["reason"]
    assert lease_path.read_text(encoding="utf-8") == original  # never rewritten


def test_refresh_thread_lease_heartbeat_is_noop_when_process_identity_unconfirmed(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    """Fix 2: even with a matching thread id AND generation, the heartbeat refresh must
    reconfirm the calling process's identity — unlike claim_thread_lease's explicit
    same-owner resume, it never assumes unproven continuity for an uncheckable lease."""
    now = datetime(2026, 7, 23, 10, 0, tzinfo=UTC)
    lease = _v2_lease(owner_thread_id="owner-session", generation=1, owner_pid=111, owner_pid_started_at=1000.0)
    lease_path = _write_lease(tmp_path, "claude-infra", lease)
    original = lease_path.read_text(encoding="utf-8")
    monkeypatch.setattr(th, "_default_machine_id", lambda: "machine-a")
    # A fresh probe from the calling process resolves to a DIFFERENT identity.
    monkeypatch.setattr(
        th,
        "_derive_owner_liveness_fields",
        lambda starting_pid: {"owner_pid": 222, "owner_pid_started_at": 5000.0, "owner_machine_id": "machine-a"},
    )

    result = th.refresh_thread_lease_heartbeat(
        state_root=tmp_path,
        agent="claude-infra",
        current_thread_id="owner-session",
        generation=1,
        now=now,
        starting_pid=222,
    )

    assert result["status"] == "noop"
    assert "identity" in result["reason"]
    assert lease_path.read_text(encoding="utf-8") == original  # never rewritten


def test_refresh_thread_lease_heartbeat_is_noop_for_an_uncheckable_lease(tmp_path: Path):
    """Fix 2: an uncheckable lease (e.g. legacy v1) must never be blindly refreshed here —
    unproven continuity is not assumed on the implicit, frequent heartbeat path, only on
    claim_thread_lease's explicit same-owner resume."""
    now = datetime(2026, 7, 23, 10, 0, tzinfo=UTC)
    v1_lease = {
        "schema_version": 1,
        "agent": "claude-infra",
        "generation": 1,
        "owner_thread_id": "owner-session",
        "acquired_at": "2026-07-23T09:00:00Z",
        "heartbeat_at": "2026-07-23T09:58:30Z",  # 90s old, past any throttle
    }
    lease_path = _write_lease(tmp_path, "claude-infra", v1_lease)
    original = lease_path.read_text(encoding="utf-8")

    result = th.refresh_thread_lease_heartbeat(
        state_root=tmp_path,
        agent="claude-infra",
        current_thread_id="owner-session",
        generation=1,
        now=now,
        starting_pid=1,
        min_refresh_interval=timedelta(seconds=60),
    )

    assert result["status"] == "noop"
    assert "identity" in result["reason"]
    assert lease_path.read_text(encoding="utf-8") == original  # never rewritten


def test_throttled_heartbeat_refresh_is_a_cheap_noop_within_the_interval(tmp_path: Path):
    """The PostToolUse hook fires on every tool call — it must not rewrite the lease
    file every time, only once the existing heartbeat is already older than the throttle.
    Throttle is checked before process identity, so this stays a cheap read even when
    identity would be unconfirmed."""
    now = datetime(2026, 7, 23, 10, 0, tzinfo=UTC)
    lease = _v2_lease(owner_thread_id="owner-session", heartbeat_at="2026-07-23T09:59:30Z")  # 30s old
    lease_path = _write_lease(tmp_path, "claude-infra", lease)
    original_mtime = lease_path.stat().st_mtime_ns

    result = th.refresh_thread_lease_heartbeat(
        state_root=tmp_path,
        agent="claude-infra",
        current_thread_id="owner-session",
        generation=1,
        now=now,
        starting_pid=1,
        min_refresh_interval=timedelta(seconds=60),
    )

    assert result["status"] == "throttled"
    assert lease_path.stat().st_mtime_ns == original_mtime  # never rewritten
    assert json.loads(lease_path.read_text(encoding="utf-8"))["heartbeat_at"] == "2026-07-23T09:59:30Z"


def test_throttled_heartbeat_refresh_writes_once_the_interval_has_elapsed(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    """Past the throttle window, the refresh must still actually happen when generation and
    process identity both confirm this session still owns the lease."""
    now = datetime(2026, 7, 23, 10, 0, tzinfo=UTC)
    lease = _v2_lease(owner_thread_id="owner-session", heartbeat_at="2026-07-23T09:58:30Z")  # 90s old
    lease_path = _write_lease(tmp_path, "claude-infra", lease)
    monkeypatch.setattr(th, "_default_machine_id", lambda: "machine-a")
    monkeypatch.setattr(
        th,
        "_derive_owner_liveness_fields",
        lambda starting_pid: {"owner_pid": 4242, "owner_pid_started_at": 1000.0, "owner_machine_id": "machine-a"},
    )

    result = th.refresh_thread_lease_heartbeat(
        state_root=tmp_path,
        agent="claude-infra",
        current_thread_id="owner-session",
        generation=1,
        now=now,
        starting_pid=1,
        min_refresh_interval=timedelta(seconds=60),
    )

    assert result["status"] == "refreshed"
    assert json.loads(lease_path.read_text(encoding="utf-8"))["heartbeat_at"] == "2026-07-23T10:00:00Z"


def test_refresh_thread_lease_heartbeat_command_throttles_via_min_refresh_interval_seconds(
    tmp_path: Path, capsys
):
    """CLI-level: --min-refresh-interval-seconds is the flag the PostToolUse hook actually passes."""
    repo_args = ["--repo-root", str(tmp_path)]
    assert th.main([*repo_args, "claim-thread-lease", "--agent", "claude-infra", "--starting-pid", "1",
                     "--current-thread-id", "owner-session"]) == 0
    capsys.readouterr()

    assert th.main([*repo_args, "refresh-thread-lease-heartbeat", "--agent", "claude-infra",
                     "--current-thread-id", "owner-session", "--starting-pid", "1",
                     "--generation", "1",
                     "--min-refresh-interval-seconds", "3600"]) == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["status"] == "throttled"  # fresh claim heartbeat is well within the 3600s window


# --- refresh_thread_lease_heartbeat without --generation (item 1) ---


def test_refresh_thread_lease_heartbeat_without_generation_and_proven_identity_succeeds(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    """Item 1: --generation is now optional — a confirmed process identity (require_proof=True)
    is the sole, strictly-stronger fence. Mutation check: reverting refresh to require
    generation unconditionally would make this call raise a TypeError/no-op instead of
    refreshing, since no generation is supplied here at all."""
    now = datetime(2026, 7, 23, 10, 0, tzinfo=UTC)
    lease = _v2_lease(
        owner_thread_id="owner-session",
        generation=7,
        heartbeat_at="2026-07-23T09:00:00Z",
        owner_pid=111,
        owner_pid_started_at=1000.0,
    )
    lease_path = _write_lease(tmp_path, "claude-infra", lease)
    monkeypatch.setattr(th, "_default_machine_id", lambda: "machine-a")
    monkeypatch.setattr(
        th,
        "_derive_owner_liveness_fields",
        lambda starting_pid: {"owner_pid": 111, "owner_pid_started_at": 1000.0, "owner_machine_id": "machine-a"},
    )

    result = th.refresh_thread_lease_heartbeat(
        state_root=tmp_path, agent="claude-infra", current_thread_id="owner-session", now=now, starting_pid=111
    )

    assert result["status"] == "refreshed"
    on_disk = json.loads(lease_path.read_text(encoding="utf-8"))
    assert on_disk["heartbeat_at"] == "2026-07-23T10:00:00Z"
    assert on_disk["generation"] == 7  # untouched


def test_refresh_thread_lease_heartbeat_without_generation_and_unproven_identity_is_noop(tmp_path: Path):
    """Item 1: with no generation supplied AND no way to reconfirm identity (no mocking here,
    so the lease is uncheckable in this test process), the refresh must fail closed as a
    no-op — never blindly rewrite heartbeat_at just because the thread id happens to match."""
    now = datetime(2026, 7, 23, 10, 0, tzinfo=UTC)
    lease = _v2_lease(owner_thread_id="owner-session", generation=1)
    lease_path = _write_lease(tmp_path, "claude-infra", lease)
    original = lease_path.read_text(encoding="utf-8")

    result = th.refresh_thread_lease_heartbeat(
        state_root=tmp_path, agent="claude-infra", current_thread_id="owner-session", now=now
    )

    assert result["status"] == "noop"
    assert "identity" in result["reason"]
    assert lease_path.read_text(encoding="utf-8") == original


def test_refresh_thread_lease_heartbeat_command_without_generation_flag(tmp_path: Path, capsys):
    """CLI-level: --generation is optional on refresh-thread-lease-heartbeat (item 1) — the
    updated hook scripts no longer pass it at all."""
    repo_args = ["--repo-root", str(tmp_path)]
    assert th.main([*repo_args, "claim-thread-lease", "--agent", "claude-infra", "--starting-pid", "1",
                     "--current-thread-id", "owner-session"]) == 0
    capsys.readouterr()

    assert th.main([*repo_args, "refresh-thread-lease-heartbeat", "--agent", "claude-infra",
                     "--current-thread-id", "owner-session"]) == 0
    payload = json.loads(capsys.readouterr().out)
    # --starting-pid 1 is never a known harness ancestor (matches the double-launch-conflict
    # test's convention), so identity cannot be reconfirmed here either — this is the
    # documented fail-closed no-op, exercised purely through the CLI surface with no
    # --generation flag passed at all, exactly like the updated hook scripts.
    assert payload["status"] == "noop"


# --- claim conflict diagnosis (item 5) ---


def test_claim_conflict_diagnosis_reports_pid_heartbeat_age_and_cas_resolution_command(tmp_path: Path, capsys):
    """Diagnosis golden test: the conflict JSON must give an operator everything needed to
    decide without opening the lease file by hand, including the exact CAS-scoped (never
    bare) force-release command."""
    lease = {
        "schema_version": 2,
        "agent": "claude-infra",
        "generation": 3,
        "owner_thread_id": "stuck-owner",
        "acquired_at": "2020-01-01T00:00:00Z",
        "heartbeat_at": "2020-01-01T00:00:00Z",  # far enough in the past to be unambiguous forever
        "owner_pid": 55555,
        "owner_pid_started_at": 1000.0,
        "owner_machine_id": "some-other-machine",  # cross-machine: liveness is never checkable
    }
    _write_lease(tmp_path, "claude-infra", lease)

    assert (
        th.main(
            [
                "--repo-root",
                str(tmp_path),
                "claim-thread-lease",
                "--agent",
                "claude-infra",
                "--starting-pid",
                "1",
                "--current-thread-id",
                "new-session",
            ]
        )
        == 2
    )
    payload = json.loads(capsys.readouterr().out)

    assert payload["error_code"] == "THREAD_LEASE_LIVENESS_UNKNOWN"
    assert payload["owner_thread_id"] == "stuck-owner"
    assert payload["owner_pid"] == 55555
    assert payload["owner_pid_started_at"] == 1000.0
    assert payload["owner_alive"] is None  # never checkable, never guessed
    assert payload["heartbeat_age_seconds"] > 45 * 60
    assert payload["heartbeat_age_humanized"]
    assert payload["idle_suspected"] is True
    resolution = payload["resolution"]
    assert "--force" in resolution
    assert "--expect-owner-thread-id stuck-owner" in resolution
    assert "--expect-generation 3" in resolution
    assert "--acknowledge-live-owner" not in resolution  # liveness is unknown, not confirmed alive


def test_claim_conflict_diagnosis_flags_a_confirmed_live_owner_and_requires_acknowledgement(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys
):
    """Item 5/6: a genuinely live owner reports owner_alive=True and its resolution command
    includes --acknowledge-live-owner up front — an operator should never have to discover
    that flag by trial and error against a live process."""
    lease = {
        "schema_version": 2,
        "agent": "claude-infra",
        "generation": 2,
        "owner_thread_id": "live-owner",
        "acquired_at": "2020-01-01T00:00:00Z",
        "heartbeat_at": "2020-01-01T00:00:00Z",
        "owner_pid": 4242,
        "owner_pid_started_at": 1000.0,
        "owner_machine_id": "machine-a",
    }
    _write_lease(tmp_path, "claude-infra", lease)
    monkeypatch.setattr(th, "_default_machine_id", lambda: "machine-a")
    monkeypatch.setattr(th, "_process_is_alive", lambda pid: True)
    monkeypatch.setattr(th, "_default_process_snapshot", lambda pid: _fake_snapshot(pid=pid))

    assert (
        th.main(
            [
                "--repo-root",
                str(tmp_path),
                "claim-thread-lease",
                "--agent",
                "claude-infra",
                "--starting-pid",
                "1",
                "--current-thread-id",
                "new-session",
            ]
        )
        == 2
    )
    payload = json.loads(capsys.readouterr().out)

    assert payload["error_code"] == "THREAD_LEASE_CONFLICT"
    assert payload["owner_alive"] is True
    assert payload["idle_suspected"] is True
    assert "--acknowledge-live-owner" in payload["resolution"]


# --- cooperative release at prepare/rollover seal (item 4) ---


def test_prepare_releases_the_slot_lease_on_successful_seal_for_claude_agent(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys
):
    """Item 4: once the rollover packet is sealed, prepare's own terminal mutating action for
    a claude/claude-* agent slot is to cooperatively release its thread-lease through the
    same identity-gated release path a SessionEnd hook would use — the predecessor does not
    have to wait for (or rely on) a hook firing correctly to unblock its own successor."""
    monkeypatch.setattr(th, "gather_snapshot", lambda root, url: sample_snapshot(root))
    monkeypatch.setattr(th, "_default_machine_id", lambda: "machine-a")
    monkeypatch.setattr(
        th,
        "_derive_owner_liveness_fields",
        lambda starting_pid: {"owner_pid": 999, "owner_pid_started_at": 1000.0, "owner_machine_id": "machine-a"},
    )
    lease = _v2_lease(
        owner_thread_id="old-thread",
        generation=1,
        agent="claude",
        owner_pid=999,
        owner_pid_started_at=1000.0,
        owner_machine_id="machine-a",
    )
    lease_path = _write_lease(tmp_path, "claude", lease)

    assert (
        th.main(["--repo-root", str(tmp_path), "prepare", "--agent", "claude", "--active-thread-id", "old-thread"])
        == 0
    )
    capsys.readouterr()

    tombstone = json.loads(lease_path.read_text(encoding="utf-8"))
    assert tombstone["state"] == "released"
    assert tombstone["generation"] == 1
    assert tombstone["released_by_thread_id"] == "old-thread"


def test_prepare_release_failure_at_seal_warns_but_does_not_fail_prepare(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys
):
    """Item 4: a failure releasing the slot lease at seal time must never fail prepare itself
    — it only warns loudly (to stderr) so an operator can notice and investigate."""
    monkeypatch.setattr(th, "gather_snapshot", lambda root, url: sample_snapshot(root))

    def _boom(**_kwargs):
        raise OSError("simulated release failure")

    monkeypatch.setattr(th, "release_thread_lease", _boom)

    rc = th.main(["--repo-root", str(tmp_path), "prepare", "--agent", "claude", "--active-thread-id", "old-thread"])

    assert rc == 0
    captured = capsys.readouterr()
    assert "WARNING" in captured.err
    assert "simulated release failure" in captured.err


def test_prepare_does_not_release_a_non_claude_agent_slot(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys):
    """Item 4 is scoped to claude/claude-* agent slots only — Codex's own lifecycle fix is a
    separate, parallel effort (Phase B), so prepare must never touch a codex lease."""
    monkeypatch.setattr(th, "gather_snapshot", lambda root, url: sample_snapshot(root))
    lease = _v2_lease(owner_thread_id="old-thread", generation=1, agent="codex")
    lease_path = _write_lease(tmp_path, "codex", lease)
    original = lease_path.read_text(encoding="utf-8")

    assert (
        th.main(["--repo-root", str(tmp_path), "prepare", "--agent", "codex", "--active-thread-id", "old-thread"])
        == 0
    )
    capsys.readouterr()

    assert lease_path.read_text(encoding="utf-8") == original  # untouched


def test_resume_aba_late_release_no_ops(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    """resume-ABA: claim(T,procA) -> resume claim(T,procB,gen2) -> late release from A (carried gen1) -> MUST no-op."""
    now = datetime(2026, 7, 23, 10, 0, tzinfo=UTC)
    monkeypatch.setattr(th, "_default_machine_id", lambda: "machine-a")
    monkeypatch.setattr(
        th,
        "_derive_owner_liveness_fields",
        lambda pid: (
            {"owner_pid": 111, "owner_pid_started_at": 1000.0, "owner_machine_id": "machine-a"}
            if pid == 111
            else {"owner_pid": 222, "owner_pid_started_at": 2000.0, "owner_machine_id": "machine-a"}
        ),
    )
    claim1 = th.claim_thread_lease(
        state_root=tmp_path, agent="claude-infra", current_thread_id="thread-T", now=now, starting_pid=111
    )
    assert claim1["status"] == "acquired"
    assert claim1["generation"] == 1

    claim2 = th.claim_thread_lease(
        state_root=tmp_path, agent="claude-infra", current_thread_id="thread-T", now=now, starting_pid=222
    )
    assert claim2["status"] == "acquired"
    assert claim2["generation"] == 2

    release_res = th.release_thread_lease(
        state_root=tmp_path,
        agent="claude-infra",
        current_thread_id="thread-T",
        generation=1,
        now=now,
        starting_pid=111,
    )
    assert release_res["status"] == "noop"
    lease_data = json.loads((tmp_path / ".agent/claude-infra-thread-lease.json").read_text(encoding="utf-8"))
    assert lease_data["generation"] == 2
    assert lease_data["owner_thread_id"] == "thread-T"
    assert lease_data.get("state", "held") == "held"


def test_tombstone_monotonic_generation(tmp_path: Path):
    """claim -> release -> claim => gen strictly increases; late stale release no-ops."""
    now = datetime(2026, 7, 23, 10, 0, tzinfo=UTC)
    c1 = th.claim_thread_lease(
        state_root=tmp_path, agent="claude-infra", current_thread_id="thread-1", now=now, starting_pid=111
    )
    assert c1["generation"] == 1

    r1 = th.release_thread_lease(
        state_root=tmp_path,
        agent="claude-infra",
        current_thread_id="thread-1",
        generation=1,
        now=now,
        starting_pid=111,
    )
    assert r1["status"] == "released"
    tombstone = json.loads((tmp_path / ".agent/claude-infra-thread-lease.json").read_text(encoding="utf-8"))
    assert tombstone["state"] == "released"
    assert tombstone["generation"] == 1

    c2 = th.claim_thread_lease(
        state_root=tmp_path, agent="claude-infra", current_thread_id="thread-2", now=now, starting_pid=222
    )
    assert c2["generation"] == 2
    assert c2["status"] == "acquired"

    r2 = th.release_thread_lease(
        state_root=tmp_path,
        agent="claude-infra",
        current_thread_id="thread-1",
        generation=1,
        now=now,
        starting_pid=111,
    )
    assert r2["status"] == "noop"


def test_absent_state_migration_compatibility(tmp_path: Path):
    """Schema migration: absent state field is treated as state: held."""
    lease_path = tmp_path / ".agent/claude-infra-thread-lease.json"
    lease_path.parent.mkdir(parents=True, exist_ok=True)
    lease = {
        "schema_version": 2,
        "agent": "claude-infra",
        "generation": 1,
        "owner_thread_id": "old-owner",
        "acquired_at": "2026-07-23T09:00:00Z",
        "heartbeat_at": "2026-07-23T09:00:00Z",
    }
    lease_path.write_text(json.dumps(lease), encoding="utf-8")
    now = datetime(2026, 7, 23, 10, 0, tzinfo=UTC)
    res = th.release_thread_lease(
        state_root=tmp_path, agent="claude-infra", current_thread_id="old-owner", generation=1, now=now, starting_pid=1
    )
    assert res["status"] == "released"
    on_disk = json.loads(lease_path.read_text(encoding="utf-8"))
    assert on_disk["state"] == "released"




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
    is_ancestor_diverged = make_is_ancestor(
        {
            (prepared_head, current_head): False,
            (current_head, prepared_head): False,
        }
    )
    err = th.checkout_continuity_error(replacement, git_state, is_ancestor=is_ancestor_diverged)
    assert f"invoking checkout HEAD {current_head} has diverged from prepared HEAD {prepared_head}" in err

    # 3. Rewind rejected: current is strict ancestor of prepared
    is_ancestor_rewind = make_is_ancestor(
        {
            (prepared_head, current_head): False,
            (current_head, prepared_head): True,
        }
    )
    err = th.checkout_continuity_error(replacement, git_state, is_ancestor=is_ancestor_rewind)
    assert (
        f"invoking checkout HEAD {current_head} is a rewind (strict ancestor of prepared HEAD {prepared_head})" in err
    )

    # 4. Dirty-at-descent rejected: prepared is ancestor, but tree is dirty
    dirty_state = {**clean, "full_head": current_head, "modified_files": [{"status": "M", "path": "tracked.txt"}]}
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

    is_ancestor_partial_none = make_is_ancestor(
        {
            (prepared_head, current_head): False,
            (current_head, prepared_head): None,
        }
    )
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


def test_live_lease_keeps_legacy_v2_pending_packet_compatible():
    state = prepared(agent="codex")
    state["replacement"].pop("display")
    state["replacement"].pop("native_lifecycle")
    state["replacement"].pop("identity")
    state["replacement"].pop("title_transition")
    state["replacement"].pop("identity_receipt_path")
    state_path = th.default_state_path("codex", state["lineage_id"])

    replacement, error = th.validate_live_lease(state, agent="codex", state_path=state_path)

    assert error is None
    assert replacement is not None
    assert replacement["status"] == "pending_start"
    assert replacement["identity"]["migration"]["legacy_fallback"] is True
    assert replacement["identity"]["visible_title"] == "thread-rollover — Recover predecessor task context"


def _legacy_lease_with_unconditional_native_plan(*, agent: str) -> dict:
    """Model a pre-identity-envelope lease: no identity, native_lifecycle always present."""
    state = prepared(agent=agent)
    state["replacement"].pop("display")
    state["replacement"].pop("identity")
    state["replacement"].pop("title_transition")
    state["replacement"].pop("identity_receipt_path")
    assert state["replacement"]["native_lifecycle"]["status"] == "awaiting_native_create"
    return state


@pytest.mark.parametrize("agent", ["claude-infra", "codex"])
def test_legacy_migration_retires_unsatisfiable_native_plan_and_unbricks_resume(agent: str):
    state = _legacy_lease_with_unconditional_native_plan(agent=agent)
    original_native = dict(state["replacement"]["native_lifecycle"])

    normalized, changed = th.normalize_identity_state(state, agent=agent, now=datetime(2026, 7, 16, 12, 0, tzinfo=UTC))

    assert changed is True
    replacement = normalized["replacement"]
    assert replacement["title_transition"]["native_title_supported"] is False
    assert "native_lifecycle" not in replacement
    retired = replacement["native_lifecycle_retired"]
    assert retired["status"] == "retired_non_native_harness"
    assert retired["family_id"] == original_native["family_id"]
    assert retired["operation_id"] == original_native["operation_id"]
    assert retired["replacement_thread_id"] is None
    assert retired["retired_at"] == "2026-07-16T12:00:00Z"
    assert "unsatisfiable" in retired["reason"]

    identity, transition = task_identity.bind_replacement(
        replacement["identity"],
        replacement["title_transition"],
        replacement_task_id="new-thread-1",
        evidence="harness binding receipt for regression test",
        now="2026-07-16T12:00:01Z",
    )
    replacement["identity"] = identity
    replacement["title_transition"] = transition

    resumed = th.resume_state(
        normalized,
        rollover_id=replacement["rollover_id"],
        replacement_thread_id="new-thread-1",
        now=datetime(2026, 7, 16, 12, 0, 2, tzinfo=UTC),
    )
    assert resumed["replacement"]["status"] == "resumed"
    assert resumed["replacement"]["resumed_thread_id"] == "new-thread-1"


def test_already_migrated_fallback_lease_still_retires_orphan_native_plan():
    """A lease migrated+bound by pre-fix code keeps its orphan block; normalize must retire it."""
    state = _legacy_lease_with_unconditional_native_plan(agent="claude-infra")
    first, _ = th.normalize_identity_state(state, agent="claude-infra", now=datetime(2026, 7, 16, 12, 0, tzinfo=UTC))
    replacement = first["replacement"]
    # Simulate the pre-fix migration outcome: identity bound via fallback, orphan block intact.
    identity, transition = task_identity.bind_replacement(
        replacement["identity"],
        replacement["title_transition"],
        replacement_task_id="new-thread-2",
        evidence="harness binding receipt recorded before the fix",
        now="2026-07-16T12:00:01Z",
    )
    replacement["identity"] = identity
    replacement["title_transition"] = transition
    replacement["native_lifecycle"] = dict(replacement["native_lifecycle_retired"])
    replacement["native_lifecycle"]["status"] = "awaiting_native_create"
    del replacement["native_lifecycle_retired"]

    normalized, changed = th.normalize_identity_state(
        first, agent="claude-infra", now=datetime(2026, 7, 16, 12, 0, 3, tzinfo=UTC)
    )

    assert changed is True
    assert "native_lifecycle" not in normalized["replacement"]
    assert normalized["replacement"]["native_lifecycle_retired"]["status"] == "retired_non_native_harness"
    resumed = th.resume_state(
        normalized,
        rollover_id=normalized["replacement"]["rollover_id"],
        replacement_thread_id="new-thread-2",
        now=datetime(2026, 7, 16, 12, 0, 4, tzinfo=UTC),
    )
    assert resumed["replacement"]["status"] == "resumed"


def test_native_capable_packet_is_never_retired_and_resume_stays_gated():
    state = prepared(agent="codex")  # current prepare: codex-app harness, native-capable

    normalized, changed = th.normalize_identity_state(state, agent="codex", now=datetime(2026, 7, 16, 12, 0, tzinfo=UTC))

    assert changed is False
    replacement = normalized["replacement"]
    assert replacement["title_transition"]["native_title_supported"] is True
    assert replacement["native_lifecycle"]["status"] == "awaiting_native_create"
    assert "native_lifecycle_retired" not in replacement
    with pytest.raises(ValueError, match="must be registered before resume"):
        th.resume_state(
            normalized,
            rollover_id=replacement["rollover_id"],
            replacement_thread_id="new-thread-3",
            now=datetime(2026, 7, 16, 12, 0, 1, tzinfo=UTC),
        )


def test_touched_legacy_native_plan_is_never_retired():
    state = _legacy_lease_with_unconditional_native_plan(agent="claude-infra")
    state["replacement"]["native_lifecycle"]["status"] = "supersession_pending"

    normalized, _ = th.normalize_identity_state(state, agent="claude-infra", now=datetime(2026, 7, 16, 12, 0, tzinfo=UTC))

    assert normalized["replacement"]["native_lifecycle"]["status"] == "supersession_pending"
    assert "native_lifecycle_retired" not in normalized["replacement"]


def test_repair_refuses_retired_native_plan_with_clear_error_and_persists_retirement(
    tmp_path: Path, capsys
) -> None:
    state = _legacy_lease_with_unconditional_native_plan(agent="claude-infra")
    lineage_id = state["lineage_id"]
    rollover_id = state["replacement"]["rollover_id"]
    state_path = th.default_state_path("claude-infra", lineage_id)
    th.write_json_atomic(tmp_path / state_path, state)

    command = [
        "--repo-root",
        str(tmp_path),
        "repair-native-intent",
        "--agent",
        "claude-infra",
        "--lineage-id",
        lineage_id,
        "--rollover-id",
        rollover_id,
        "--evidence",
        "Legacy non-native packet; probing the repair path.",
    ]
    assert th.main(command) == 2
    payload = json.loads(capsys.readouterr().out)
    assert "retired as unsatisfiable" in payload["error"]

    persisted = json.loads((tmp_path / state_path).read_text(encoding="utf-8"))
    assert "native_lifecycle" not in persisted["replacement"]
    assert persisted["replacement"]["native_lifecycle_retired"]["status"] == "retired_non_native_harness"
    identity_receipt = tmp_path / persisted["replacement"]["identity_receipt_path"]
    assert identity_receipt.exists()


def test_prepare_rejects_dirty_source_checkout_without_writing_packet(tmp_path: Path, capsys, monkeypatch):
    dirty_snapshot = sample_snapshot(tmp_path)
    dirty_snapshot["git"]["modified_files"] = [{"status": "??", "path": "untracked.txt"}]
    monkeypatch.setattr(th, "gather_snapshot", lambda root, url: dirty_snapshot)
    monkeypatch.setattr(th, "gather_git_state", lambda root: dirty_snapshot["git"])

    assert th.main(["--repo-root", str(tmp_path), "prepare", "--active-thread-id", "old-thread"]) == 2
    payload = json.loads(capsys.readouterr().out)
    assert "source checkout must be clean before prepare" in payload["error"]
    assert payload["old_automation_ready_to_delete"] is False
    rollover_root = tmp_path / ".agent/thread-rollovers"
    assert [path for path in rollover_root.rglob("*") if path.is_file() and path.name != ".native-intent.lock"] == []


def test_supervised_claudex_prepare_emits_one_typed_request(
    tmp_path: Path,
    capsys,
    monkeypatch,
) -> None:
    supervisor = seed_supervised_claudex(tmp_path, monkeypatch)
    monkeypatch.setattr(th, "gather_snapshot", lambda root, url: sample_snapshot(root))

    assert (
        th.main(
            [
                "--repo-root",
                str(tmp_path),
                "prepare",
                "--agent",
                "claude-infra",
            ]
        )
        == 0
    )
    payload = json.loads(capsys.readouterr().out)
    request_path = cs._request_path(tmp_path, supervisor.run_id)
    request = json.loads(request_path.read_text(encoding="utf-8"))

    assert payload["lineage_id"] == th.lineage_id_for(
        "claude-infra", "official-session-5265"
    )
    assert payload["claudex_rollover_request"] == {
        "request_id": request["request_id"],
        "rollover_id": payload["rollover_id"],
        "run_id": supervisor.run_id,
    }
    assert request["source_session_id"] == "official-session-5265"
    assert request["launch_generation"] == 0
    assert request["profile_id"] == "sol_lead"
    assert request["lead_model_id"] == "gpt-5.6-sol"
    assert request["subagent_model_id"] == "gpt-5.6-terra"
    assert request["handoff_agent"] == "claude-infra"
    assert len(list(supervisor.run_dir.glob("request.json"))) == 1


def test_supervised_claudex_request_failure_preserves_prepared_lease(
    tmp_path: Path,
    capsys,
    monkeypatch,
) -> None:
    supervisor = seed_supervised_claudex(tmp_path, monkeypatch)
    monkeypatch.setattr(th, "gather_snapshot", lambda root, url: sample_snapshot(root))
    monkeypatch.setenv("LEARN_UKRAINIAN_CLAUDEX_LAUNCH_GENERATION", "1")

    assert (
        th.main(
            [
                "--repo-root",
                str(tmp_path),
                "prepare",
                "--agent",
                "claude-infra",
            ]
        )
        == 2
    )
    payload = json.loads(capsys.readouterr().out)
    lease_path = tmp_path / payload["state_file"]
    lease = json.loads(lease_path.read_text(encoding="utf-8"))

    assert "request launch generation is stale" in payload["error"]
    assert payload["old_automation_ready_to_delete"] is False
    assert lease["replacement"]["status"] == "pending_start"
    assert lease["replacement"]["rollover_id"] == payload["rollover_id"]
    assert not cs._request_path(tmp_path, supervisor.run_id).exists()


def test_prepare_seal_release_skipped_when_claudex_rollover_request_fails(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys,
) -> None:
    """P1 regression (bridge msg #5285): the cooperative seal-time thread-lease release must
    be the LAST fallible-free step in prepare. If request_claudex_rollover fails, prepare
    returns an error — the predecessor's own slot lease must still be HELD so no successor can
    claim it and double-drive. Mutation check: moving the release call back before the
    request_claudex_rollover call makes this test fail (the lease flips to "released" even
    though prepare returned rc=2)."""
    seed_supervised_claudex(tmp_path, monkeypatch)
    monkeypatch.setattr(th, "gather_snapshot", lambda root, url: sample_snapshot(root))
    monkeypatch.setattr(th, "_default_machine_id", lambda: "machine-a")
    monkeypatch.setattr(
        th,
        "_derive_owner_liveness_fields",
        lambda starting_pid: {"owner_pid": 999, "owner_pid_started_at": 1000.0, "owner_machine_id": "machine-a"},
    )
    lease = _v2_lease(
        owner_thread_id="official-session-5265",
        generation=1,
        agent="claude-infra",
        owner_pid=999,
        owner_pid_started_at=1000.0,
        owner_machine_id="machine-a",
    )
    lease_path = _write_lease(tmp_path, "claude-infra", lease)
    original_lease_text = lease_path.read_text(encoding="utf-8")
    monkeypatch.setenv("LEARN_UKRAINIAN_CLAUDEX_LAUNCH_GENERATION", "1")  # stale -> request fails

    rc = th.main(
        [
            "--repo-root",
            str(tmp_path),
            "prepare",
            "--agent",
            "claude-infra",
        ]
    )
    payload = json.loads(capsys.readouterr().out)

    assert rc == 2
    assert "request launch generation is stale" in payload["error"]
    assert lease_path.read_text(encoding="utf-8") == original_lease_text  # still held, not tombstoned


def test_prepare_without_native_adapter_records_carrier_binding_action(
    tmp_path: Path,
    capsys,
    monkeypatch,
) -> None:
    monkeypatch.setattr(th, "gather_snapshot", lambda root, url: sample_snapshot(root))

    assert (
        th.main(
            [
                "--repo-root",
                str(tmp_path),
                "prepare",
                "--agent",
                "claude",
                "--active-thread-id",
                "native-session",
            ]
        )
        == 0
    )
    payload = json.loads(capsys.readouterr().out)

    assert "claudex_rollover_request" not in payload
    assert payload["next_native_action"]["tool"] == "bind-replacement"
    assert payload["title_transition"]["native_title_supported"] is False
    assert not (tmp_path / ".agent/claudex-supervisors").exists()


def test_unsupported_native_title_adapter_binds_exact_task_without_claiming_rename(
    tmp_path: Path,
    capsys,
    monkeypatch,
) -> None:
    monkeypatch.setattr(th, "gather_snapshot", lambda root, url: sample_snapshot(root))
    assert (
        th.main(
            [
                "--repo-root",
                str(tmp_path),
                "prepare",
                "--agent",
                "claude",
                "--active-thread-id",
                "claude-old",
                "--issue-number",
                "5295",
                "--stream-epic",
                "4707",
                "--semantic-title",
                "Repair fleet rollover task identity",
                "--terminal-goal",
                "merge",
            ]
        )
        == 0
    )
    prepared_payload = json.loads(capsys.readouterr().out)
    bind_command = [
        "--repo-root",
        str(tmp_path),
        "bind-replacement",
        "--agent",
        "claude",
        "--lineage-id",
        prepared_payload["lineage_id"],
        "--rollover-id",
        prepared_payload["rollover_id"],
        "--replacement-task-id",
        "claude-new",
        "--evidence",
        "dispatch runtime exact task receipt",
    ]
    assert th.main(bind_command) == 0
    bound = json.loads(capsys.readouterr().out)

    assert bound["native_title_mutation_supported"] is False
    assert bound["fallback_receipt"]["attempted"] is False
    assert bound["visible_title"] == "#5295 — Repair fleet rollover task identity"
    assert th.main(bind_command) == 0
    capsys.readouterr()
    assert (
        th.main(
            [
                "--repo-root",
                str(tmp_path),
                "resume",
                "--agent",
                "claude",
                "--lineage-id",
                prepared_payload["lineage_id"],
                "--rollover-id",
                prepared_payload["rollover_id"],
                "--replacement-thread-id",
                "claude-new",
            ]
        )
        == 0
    )
    resumed = json.loads(capsys.readouterr().out)
    assert resumed["identity"]["lifecycle_state"] == "resumed"
    assert resumed["title_transition"]["fallback_receipt"]["attempted"] is False


def test_prepare_dry_run_never_prints_canary_bearing_prompt(
    tmp_path: Path,
    capsys,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    challenge = "a" * 64
    monkeypatch.setattr(th, "gather_snapshot", lambda root, url: sample_snapshot(root))
    monkeypatch.setattr(th, "new_canary_challenge", lambda: challenge)

    assert (
        th.main(
            [
                "--repo-root",
                str(tmp_path),
                "prepare",
                "--active-thread-id",
                "old-thread",
                "--dry-run",
            ]
        )
        == 0
    )
    raw = capsys.readouterr().out
    payload = json.loads(raw)

    assert challenge not in raw
    assert "bootstrap_prompt" not in payload
    assert payload["bootstrap_prompt_bytes"] > 0
    assert len(payload["bootstrap_prompt_sha256"]) == 64
    assert not (tmp_path / payload["bootstrap_file"]).exists()


def test_register_created_context_failure_reports_cleanly(tmp_path: Path, capsys):
    rc = th.main(
        [
            "--repo-root",
            str(tmp_path),
            "register-created",
            "--lineage-id",
            "lineage-1234567890abcdef12345678",
            "--rollover-id",
            "rollover-missing",
            "--replacement-thread-id",
            "00000000-0000-0000-0000-000000000002",
            "--evidence",
            "native create result",
        ]
    )

    assert rc == 2
    payload = json.loads(capsys.readouterr().out)
    assert payload["action"] == "register-created"
    assert "isolated rollover" in payload["error"]
    assert "NameError" not in payload["error"]


def test_native_create_action_is_retry_gate_without_db(tmp_path: Path, capsys, monkeypatch):
    monkeypatch.setattr(th, "gather_snapshot", lambda root, url: sample_snapshot(root))
    assert th.main(["--repo-root", str(tmp_path), "prepare", "--active-thread-id", "old-thread"]) == 0
    prepared_payload = json.loads(capsys.readouterr().out)

    assert (
        th.main(
            [
                "--repo-root",
                str(tmp_path),
                "native-action",
                "--lineage-id",
                prepared_payload["lineage_id"],
                "--rollover-id",
                prepared_payload["rollover_id"],
                "--action",
                "create",
            ]
        )
        == 0
    )
    action = json.loads(capsys.readouterr().out)
    assert action["tool"] == "create_thread"
    assert action["needs_native_action"] is True
    assert action["bootstrap_prompt_path"] == prepared_payload["bootstrap_file"]


def test_forced_prepare_supersedes_only_pristine_exact_predecessor_intent(
    tmp_path: Path,
    capsys,
    monkeypatch,
) -> None:
    monkeypatch.setattr(th, "gather_snapshot", lambda root, url: sample_snapshot(root))
    command = ["--repo-root", str(tmp_path), "prepare", "--agent", "codex", "--active-thread-id", "old-thread"]
    assert th.main(command) == 0
    first = json.loads(capsys.readouterr().out)

    assert th.main([*command, "--force-new-replacement"]) == 0
    second = json.loads(capsys.readouterr().out)

    assert second["rollover_id"] != first["rollover_id"]
    assert second["native_lifecycle"]["operation_id"] != first["native_lifecycle"]["operation_id"]
    old_storage = TaskFamilyStorage(
        tmp_path,
        first["native_lifecycle"]["family_id"],
        first["native_lifecycle"]["operation_id"],
    )
    assert old_storage.load_state()["details"]["status"] == "superseded_before_native_create"
    assert old_storage.rollover_supersession_path.exists()
    assert old_storage.load_receipt().actual == ()
    lease = json.loads((tmp_path / second["state_file"]).read_text(encoding="utf-8"))
    assert lease["replacement"]["rollover_id"] == second["rollover_id"]
    assert lease["replacement"]["native_lifecycle"]["status"] == "awaiting_native_create"
    assert "Resume codex rollover" not in second["intended_title"]


def test_legacy_receipt_collision_repairs_current_packet_and_never_creates_from_mismatch(
    tmp_path: Path,
    capsys,
    monkeypatch,
) -> None:
    state = prepared(agent="codex", thread_id="old-thread")
    replacement = state["replacement"]
    current_rollover_id = replacement["rollover_id"]
    current_bootstrap = replacement["bootstrap_prompt_path"]
    lineage_id = state["lineage_id"]
    legacy_family_id, legacy_operation_id = rollover.legacy_transition_identity(
        lineage_id=lineage_id,
        generation=1,
    )
    original_identity = rollover.transition_identity
    monkeypatch.setattr(
        rollover,
        "transition_identity",
        lambda **kwargs: (legacy_family_id, legacy_operation_id),
    )
    rollover.prepare_transition(
        repo_root=tmp_path,
        agent="codex",
        lineage_id=lineage_id,
        rollover_id="rollover-superseded-packet",
        generation=1,
        source_thread_id="old-thread",
        intended_title=replacement["display"]["title"],
        title_source=replacement["display"]["title_source"],
        bootstrap_prompt_path="stale-bootstrap.md",
    )
    monkeypatch.setattr(rollover, "transition_identity", original_identity)
    replacement["native_lifecycle"] = {
        "family_id": legacy_family_id,
        "operation_id": legacy_operation_id,
        "source_thread_id": "old-thread",
        "replacement_thread_id": None,
        "status": "needs_native_action",
        "error": "immutable operation document mismatch: rollover-plan.json",
    }
    state_path = th.default_state_path("codex", lineage_id)
    th.write_json_atomic(tmp_path / state_path, state)

    native_command = [
        "--repo-root",
        str(tmp_path),
        "native-action",
        "--agent",
        "codex",
        "--lineage-id",
        lineage_id,
        "--rollover-id",
        current_rollover_id,
        "--action",
        "create",
    ]
    assert th.main(native_command) == 2
    assert "does not match its durable lineage" in json.loads(capsys.readouterr().out)["error"]
    legacy_storage = TaskFamilyStorage(tmp_path, legacy_family_id, legacy_operation_id)
    assert [event.kind for event in legacy_storage.load_events()] == ["rollover_native_intent_prepared"]

    repair_command = [
        "--repo-root",
        str(tmp_path),
        "repair-native-intent",
        "--agent",
        "codex",
        "--lineage-id",
        lineage_id,
        "--rollover-id",
        current_rollover_id,
        "--evidence",
        "App stopped before create_thread; receipt and binding are pristine.",
    ]
    assert th.main(repair_command) == 0
    repaired = json.loads(capsys.readouterr().out)
    assert repaired["status"] == "native_intent_repaired"
    repaired_state = json.loads((tmp_path / state_path).read_text(encoding="utf-8"))
    repaired_native = repaired_state["replacement"]["native_lifecycle"]
    expected_family, expected_operation = original_identity(
        lineage_id=lineage_id,
        generation=1,
        rollover_id=current_rollover_id,
    )
    assert repaired_native["family_id"] == expected_family
    assert repaired_native["operation_id"] == expected_operation
    assert repaired_native["status"] == "awaiting_native_create"
    assert repaired_state["replacement"]["bootstrap_prompt_path"] == current_bootstrap
    identity_receipt = tmp_path / repaired_state["replacement"]["identity_receipt_path"]
    assert identity_receipt.exists()
    assert json.loads(identity_receipt.read_text(encoding="utf-8"))["identity"] == (
        repaired_state["replacement"]["identity"]
    )
    assert legacy_storage.load_state()["details"]["status"] == "superseded_before_native_create"
    current_storage = TaskFamilyStorage(tmp_path, expected_family, expected_operation)
    assert current_storage.read_json(current_storage.rollover_plan_path)["rollover_id"] == current_rollover_id
    validated, error = th.validate_live_lease(repaired_state, agent="codex", state_path=tmp_path / state_path)
    assert error is None
    assert validated is not None

    assert th.main(repair_command) == 0
    retry = json.loads(capsys.readouterr().out)
    assert retry["status"] == "native_intent_repaired"
    assert th.main(native_command) == 0
    action = json.loads(capsys.readouterr().out)
    assert action["needs_native_action"] is True
    assert action["bootstrap_prompt_path"] == current_bootstrap


def test_prepare_plan_failure_does_not_publish_a_live_lease(tmp_path: Path, capsys, monkeypatch) -> None:
    monkeypatch.setattr(th, "gather_snapshot", lambda root, url: sample_snapshot(root))
    monkeypatch.setattr(
        th.task_family_rollover,
        "prepare_transition",
        lambda **kwargs: (_ for _ in ()).throw(ValueError("simulated persistence failure")),
    )

    assert th.main(["--repo-root", str(tmp_path), "prepare", "--active-thread-id", "old-thread"]) == 2
    payload = json.loads(capsys.readouterr().out)
    assert "simulated persistence failure" in payload["error"]
    assert not (
        tmp_path / th.default_state_path("orchestrator", th.lineage_id_for("orchestrator", "old-thread"))
    ).exists()


def test_prepare_repair_and_create_authorization_share_one_lineage_lock(tmp_path: Path) -> None:
    lineage_id = "lineage-1234567890abcdef12345678"
    parser = th.build_parser()
    prepare_args = parser.parse_args(
        [
            "--repo-root",
            str(tmp_path),
            "prepare",
            "--agent",
            "codex",
            "--lineage-id",
            lineage_id,
            "--active-thread-id",
            "old-thread",
        ]
    )
    repair_args = parser.parse_args(
        [
            "--repo-root",
            str(tmp_path),
            "repair-native-intent",
            "--agent",
            "codex",
            "--lineage-id",
            lineage_id,
            "--rollover-id",
            "rollover-current",
            "--evidence",
            "no native call",
        ]
    )
    create_args = parser.parse_args(
        [
            "--repo-root",
            str(tmp_path),
            "native-action",
            "--agent",
            "codex",
            "--lineage-id",
            lineage_id,
            "--rollover-id",
            "rollover-current",
            "--action",
            "create",
        ]
    )
    resume_args = parser.parse_args(
        [
            "--repo-root",
            str(tmp_path),
            "resume",
            "--agent",
            "codex",
            "--lineage-id",
            lineage_id,
            "--rollover-id",
            "rollover-current",
            "--replacement-thread-id",
            "replacement-thread",
        ]
    )
    confirm_args = parser.parse_args(
        [
            "--repo-root",
            str(tmp_path),
            "confirm-started",
            "--agent",
            "codex",
            "--lineage-id",
            lineage_id,
            "--rollover-id",
            "rollover-current",
            "--new-thread-id",
            "replacement-thread",
            "--canary-proof",
            "canary.json",
            "--strict-probe",
            "probe.json",
            "--strict-verdict",
            "verdict.json",
        ]
    )

    expected = tmp_path / th.default_state_path("codex", lineage_id).parent / ".native-intent.lock"
    assert th._rollover_mutation_lock_path(prepare_args) == expected
    assert th._rollover_mutation_lock_path(repair_args) == expected
    assert th._rollover_mutation_lock_path(create_args) == expected
    assert th._rollover_mutation_lock_path(resume_args) == expected
    assert th._rollover_mutation_lock_path(confirm_args) == expected


def test_resume_and_confirm_independently_recheck_checkout_continuity(tmp_path: Path, capsys, monkeypatch):
    clean = sample_snapshot(tmp_path)["git"]
    monkeypatch.setattr(th, "gather_snapshot", lambda root, url: sample_snapshot(root))
    assert th.main(["--repo-root", str(tmp_path), "prepare", "--active-thread-id", "old-thread"]) == 0
    packet = json.loads(capsys.readouterr().out)
    state_path = tmp_path / packet["state_file"]
    bind_native_lease(state_path, "new-thread")

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
    bind_native_replacement(claude_state, "new-claude")
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
    assert (
        forced["replacement"]["native_lifecycle"]["operation_id"]
        != state["replacement"]["native_lifecycle"]["operation_id"]
    )


def test_resume_is_deterministic_and_refuses_a_different_thread():
    state = prepared()
    rollover_id = state["replacement"]["rollover_id"]
    with pytest.raises(ValueError, match="must be registered"):
        th.resume_state(
            state,
            rollover_id=rollover_id,
            replacement_thread_id="new-thread",
            now=datetime(2026, 5, 30, 8, 1, tzinfo=UTC),
        )
    bind_native_replacement(state, "new-thread")
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
    with pytest.raises(ValueError, match="does not match"):
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
    bind_native_lease(state_path, "new-thread")

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
        subprocess.run(command, cwd=primary, check=True, capture_output=True, text=True, env=git_env, timeout=30)
    (primary / "README.md").write_text("fixture\n", encoding="utf-8")
    subprocess.run(["git", "add", "README.md"], cwd=primary, check=True, capture_output=True, text=True, env=git_env, timeout=30)
    subprocess.run(
        ["git", "commit", "-m", "fixture"], cwd=primary, check=True, capture_output=True, text=True, env=git_env,
        timeout=30,
    )
    subprocess.run(
        ["git", "worktree", "add", "-b", "linked", str(linked)],
        cwd=primary,
        check=True,
        capture_output=True,
        text=True,
        env=git_env,
        timeout=30,
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


def test_bootstrap_references_compact_capsule_without_history_resume(tmp_path: Path):
    state = prepared()
    state_root = tmp_path / "canonical"
    prompt = th.render_bootstrap_prompt(
        sample_snapshot(tmp_path),
        state,
        state_root=state_root,
        context_threshold=82.0,
    )

    assert "do not fork, continue, or resume provider conversation history" in prompt
    assert "detect --format session-start" in prompt
    assert "bootstrap-replacement" in prompt
    assert "confirm-replacement" in prompt
    assert "context_canary.py mint" not in prompt
    assert "thread_handoff_canary.py" not in prompt


def test_bootstrap_replacement_writes_rejected_template_and_is_idempotent(
    tmp_path: Path, capsys, monkeypatch: pytest.MonkeyPatch
):
    monkeypatch.setattr(th, "gather_snapshot", lambda root, url: sample_snapshot(root))
    assert th.main(["--repo-root", str(tmp_path), "prepare", "--agent", "codex", "--harness", "headless", "--active-thread-id", "old"]) == 0
    packet = json.loads(capsys.readouterr().out)
    command = [
        "--repo-root",
        str(tmp_path),
        "bootstrap-replacement",
        "--agent",
        "codex",
        "--lineage-id",
        packet["lineage_id"],
        "--rollover-id",
        packet["rollover_id"],
        "--replacement-thread-id",
        "new-thread",
        "--evidence",
        "test exact binding",
    ]
    assert th.main(command) == 0
    capsys.readouterr()
    state_path = tmp_path / packet["state_file"]
    state = json.loads(state_path.read_text(encoding="utf-8"))
    template_path = (tmp_path / state["replacement"]["semantic_snapshot_path"]).with_name(
        "semantic-snapshot.template.json"
    )
    template = json.loads(template_path.read_text(encoding="utf-8"))
    assert [len(template[key]) for key in ("goals", "decision_records", "constraint_records", "next_actions")] == [3, 3, 2, 2]
    assert all(not record["statement"] for record in template["goals"])
    assert all(not record["decision"] for record in template["decision_records"])
    assert all(not record["prohibition"] for record in template["constraint_records"])
    assert all(not record["action"] for record in template["next_actions"])
    assert all(
        th.context_canary._parse_and_validate_source_ref(record["source_ref"], category)
        for category, records in (
            ("goal", template["goals"]),
            ("decision/rationale", template["decision_records"]),
            ("negative-constraint/prohibition", template["constraint_records"]),
            ("next-action", template["next_actions"]),
        )
        for record in records
    )
    assert th.context_canary.main(["mint", "--snapshot", str(template_path), "--out", str(tmp_path / "probe.json")]) == 1

    state_bytes = state_path.read_bytes()
    template_bytes = template_path.read_bytes()
    assert th.main(command) == 0
    capsys.readouterr()
    assert state_path.read_bytes() == state_bytes
    assert template_path.read_bytes() == template_bytes


def test_confirm_replacement_composes_strict_flow_and_reruns_idempotently(
    tmp_path: Path, capsys, monkeypatch: pytest.MonkeyPatch
):
    monkeypatch.setattr(th, "gather_snapshot", lambda root, url: sample_snapshot(root))
    assert th.main(["--repo-root", str(tmp_path), "prepare", "--agent", "codex", "--harness", "headless", "--active-thread-id", "old"]) == 0
    packet = json.loads(capsys.readouterr().out)
    bootstrap = [
        "--repo-root",
        str(tmp_path),
        "bootstrap-replacement",
        "--agent",
        "codex",
        "--lineage-id",
        packet["lineage_id"],
        "--rollover-id",
        packet["rollover_id"],
        "--replacement-thread-id",
        "new-thread",
        "--evidence",
        "test exact binding",
    ]
    assert th.main(bootstrap) == 0
    capsys.readouterr()
    state_path = tmp_path / packet["state_file"]
    state = json.loads(state_path.read_text(encoding="utf-8"))
    replacement = state["replacement"]
    template_path = (tmp_path / replacement["semantic_snapshot_path"]).with_name("semantic-snapshot.template.json")
    th.write_json_atomic(
        tmp_path / replacement["semantic_snapshot_path"],
        filled_snapshot_from_template(json.loads(template_path.read_text(encoding="utf-8"))),
    )
    probe_path = tmp_path / replacement["strict_probe_path"]
    answers_path = tmp_path / replacement["strict_answers_path"]
    verdict_path = tmp_path / replacement["strict_verdict_path"]
    confirm = [
        "--repo-root",
        str(tmp_path),
        "confirm-replacement",
        "--agent",
        "codex",
        "--lineage-id",
        packet["lineage_id"],
        "--rollover-id",
        packet["rollover_id"],
    ]
    assert th.context_canary.main(["mint", "--snapshot", str(tmp_path / replacement["semantic_snapshot_path"]), "--out", str(probe_path)]) == 0
    probe = json.loads(probe_path.read_text(encoding="utf-8"))
    th.write_json_atomic(answers_path, {anchor["id"]: anchor["a"] for anchor in probe["anchors"]})
    probe_path.unlink()
    assert th.main(confirm) == 0
    capsys.readouterr()
    confirmed = json.loads(state_path.read_text(encoding="utf-8"))
    assert confirmed["replacement"]["status"] == "started"
    assert confirmed["cleanup"]["old_automation_ready_to_delete"] is True
    state_bytes = state_path.read_bytes()
    verdict_bytes = verdict_path.read_bytes()
    assert th.main(confirm) == 0
    assert json.loads(capsys.readouterr().out)["status"] == "already_confirmed"
    assert state_path.read_bytes() == state_bytes
    assert verdict_path.read_bytes() == verdict_bytes


def test_confirm_replacement_failed_or_skipped_score_leaves_confirmation_locked(
    tmp_path: Path, capsys, monkeypatch: pytest.MonkeyPatch
):
    monkeypatch.setattr(th, "gather_snapshot", lambda root, url: sample_snapshot(root))
    assert th.main(["--repo-root", str(tmp_path), "prepare", "--agent", "codex", "--harness", "headless", "--active-thread-id", "old"]) == 0
    packet = json.loads(capsys.readouterr().out)
    bootstrap = [
        "--repo-root",
        str(tmp_path),
        "bootstrap-replacement",
        "--agent",
        "codex",
        "--lineage-id",
        packet["lineage_id"],
        "--rollover-id",
        packet["rollover_id"],
        "--replacement-thread-id",
        "new-thread",
        "--evidence",
        "test exact binding",
    ]
    assert th.main(bootstrap) == 0
    capsys.readouterr()
    state_path = tmp_path / packet["state_file"]
    state = json.loads(state_path.read_text(encoding="utf-8"))
    replacement = state["replacement"]
    template_path = (tmp_path / replacement["semantic_snapshot_path"]).with_name("semantic-snapshot.template.json")
    th.write_json_atomic(
        tmp_path / replacement["semantic_snapshot_path"],
        filled_snapshot_from_template(json.loads(template_path.read_text(encoding="utf-8"))),
    )
    th.write_json_atomic(tmp_path / replacement["strict_answers_path"], {})
    confirm = [
        "--repo-root",
        str(tmp_path),
        "confirm-replacement",
        "--agent",
        "codex",
        "--lineage-id",
        packet["lineage_id"],
        "--rollover-id",
        packet["rollover_id"],
    ]
    assert th.main(confirm) == 2
    failed_output = capsys.readouterr().out
    assert '"schema": "production-handoff-v2-questions"' in failed_output
    locked = json.loads(state_path.read_text(encoding="utf-8"))
    assert locked["replacement"]["status"] == "resumed"
    assert locked["cleanup"]["old_automation_ready_to_delete"] is False

    original_score = th.context_canary.cmd_score
    monkeypatch.setattr(th.context_canary, "cmd_score", lambda args: 0)
    assert th.main(confirm) == 2
    capsys.readouterr()
    locked_after_skip = json.loads(state_path.read_text(encoding="utf-8"))
    assert locked_after_skip["replacement"]["status"] == "resumed"
    assert locked_after_skip["cleanup"]["old_automation_ready_to_delete"] is False
    monkeypatch.setattr(th.context_canary, "cmd_score", original_score)


def test_confirm_replacement_canary_failure_prints_questions_and_keeps_lock(
    tmp_path: Path, capsys, monkeypatch: pytest.MonkeyPatch
):
    monkeypatch.setattr(th, "gather_snapshot", lambda root, url: sample_snapshot(root))
    assert (
        th.main(
            [
                "--repo-root",
                str(tmp_path),
                "prepare",
                "--agent",
                "codex",
                "--harness",
                "headless",
                "--active-thread-id",
                "old",
            ]
        )
        == 0
    )
    packet = json.loads(capsys.readouterr().out)
    bootstrap = [
        "--repo-root",
        str(tmp_path),
        "bootstrap-replacement",
        "--agent",
        "codex",
        "--lineage-id",
        packet["lineage_id"],
        "--rollover-id",
        packet["rollover_id"],
        "--replacement-thread-id",
        "new-thread",
        "--evidence",
        "test exact binding",
    ]
    assert th.main(bootstrap) == 0
    capsys.readouterr()
    state_path = tmp_path / packet["state_file"]
    state = json.loads(state_path.read_text(encoding="utf-8"))
    replacement = state["replacement"]
    template_path = (tmp_path / replacement["semantic_snapshot_path"]).with_name("semantic-snapshot.template.json")
    snapshot_path = tmp_path / replacement["semantic_snapshot_path"]
    probe_path = tmp_path / replacement["strict_probe_path"]
    th.write_json_atomic(snapshot_path, filled_snapshot_from_template(json.loads(template_path.read_text(encoding="utf-8"))))
    assert th.context_canary.main(["mint", "--snapshot", str(snapshot_path), "--out", str(probe_path)]) == 0
    probe = json.loads(probe_path.read_text(encoding="utf-8"))
    th.write_json_atomic(
        tmp_path / replacement["strict_answers_path"],
        {anchor["id"]: anchor["a"] for anchor in probe["anchors"]},
    )
    probe_path.unlink()
    monkeypatch.setattr(th.thread_handoff_canary, "main", lambda argv: 2)
    assert (
        th.main(
            [
                "--repo-root",
                str(tmp_path),
                "confirm-replacement",
                "--agent",
                "codex",
                "--lineage-id",
                packet["lineage_id"],
                "--rollover-id",
                packet["rollover_id"],
            ]
        )
        == 2
    )
    assert '"schema": "production-handoff-v2-questions"' in capsys.readouterr().out
    locked = json.loads(state_path.read_text(encoding="utf-8"))
    assert locked["replacement"]["status"] == "resumed"
    assert locked["cleanup"]["old_automation_ready_to_delete"] is False


def test_bootstrap_replacement_wrong_id_fails_closed_without_overwriting_template(
    tmp_path: Path, capsys, monkeypatch: pytest.MonkeyPatch
):
    monkeypatch.setattr(th, "gather_snapshot", lambda root, url: sample_snapshot(root))
    assert th.main(["--repo-root", str(tmp_path), "prepare", "--agent", "codex", "--harness", "headless", "--active-thread-id", "old"]) == 0
    packet = json.loads(capsys.readouterr().out)
    command = [
        "--repo-root",
        str(tmp_path),
        "bootstrap-replacement",
        "--agent",
        "codex",
        "--lineage-id",
        packet["lineage_id"],
        "--rollover-id",
        packet["rollover_id"],
        "--replacement-thread-id",
        "new-thread",
        "--evidence",
        "test exact binding",
    ]
    assert th.main(command) == 0
    capsys.readouterr()
    state_path = tmp_path / packet["state_file"]
    state = json.loads(state_path.read_text(encoding="utf-8"))
    template_path = (tmp_path / state["replacement"]["semantic_snapshot_path"]).with_name(
        "semantic-snapshot.template.json"
    )
    state_bytes = state_path.read_bytes()
    template_bytes = template_path.read_bytes()
    assert th.main([*command[:-3], "other-thread", "--evidence", "test exact binding"]) == 2
    assert "replacement task ID does not match the exact persisted binding" in capsys.readouterr().out
    assert state_path.read_bytes() == state_bytes
    assert template_path.read_bytes() == template_bytes


def test_compact_rendering_has_one_capsule_and_no_volatile_tables(tmp_path: Path):
    state = prepared(agent="codex")
    handoff = th.render_current_markdown(sample_snapshot(tmp_path), state, agent="codex", context_threshold=82.0)
    bootstrap = th.render_bootstrap_prompt(sample_snapshot(tmp_path), state, agent="codex", context_threshold=82.0)
    candidate = {
        "lineage_id": state["lineage_id"],
        "rollover_id": state["replacement"]["rollover_id"],
        "status": "pending_start",
    }
    startup = th.render_session_start_context(candidate, agent="codex", current_thread_id="new-thread")
    assert len(handoff.encode("utf-8")) <= 4096
    for volatile_heading in ("Open PRs", "Open Issues", "Delegated Tasks", "Last 5 Commits", "## Worktrees"):
        assert volatile_heading not in handoff
    assert "detect --format session-start" in handoff
    assert "detect --format session-start" in bootstrap
    assert "context_canary.py mint" not in handoff + bootstrap
    assert startup.count("```bash") == 1
    assert "bootstrap-replacement" in startup and "confirm-replacement" in startup
    assert "context_canary.py" not in startup
    assert len(startup.encode("utf-8")) <= 550


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
    bind_native_replacement(state, "bound-thread")
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
    assert detected["identity"] == prepared_payload["identity"]
    assert detected["title_transition"] == prepared_payload["title_transition"]
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

    snapshot = th.rollover_identity_snapshot(tmp_path, agent="codex")
    assert snapshot["candidate_count"] == 1
    assert snapshot["candidates"][0]["visible_title"] == prepared_payload["identity"]["visible_title"]
    assert snapshot["candidates"][0]["safe_recommended_resolution"]

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
    payload = json.loads(capsys.readouterr().out)
    if mutation == "ambiguous":
        assert payload["error_code"] == "MULTIPLE_LIVE_PENDING_ROLLOVERS"
        assert payload["status"] == "ambiguous"
        assert payload["candidate_count"] == 2
        assert "filesystem order" in payload["resolution_policy"]
        for candidate in payload["candidates"]:
            assert set(candidate) >= {
                "semantic_title",
                "visible_title",
                "issue",
                "lineage_id",
                "generation",
                "rollover_id",
                "predecessor_task_id",
                "replacement_task_id",
                "created_at",
                "updated_at",
                "confirmation_state",
                "title_confirmation_state",
                "safe_recommended_resolution",
            }


def test_detect_task_family_filter_selects_one_of_many(tmp_path: Path, capsys, monkeypatch) -> None:
    """#5398: --task-family must disambiguate multi-packet detect to one lane."""
    monkeypatch.setattr(th, "gather_snapshot", lambda root, url: sample_snapshot(root))
    for thread_id, family, title in (
        ("old-a", "hramatka", "Ship hramatka lessons"),
        ("old-b", "thread-rollover", "Repair infra PR"),
    ):
        assert (
            th.main(
                [
                    "--repo-root",
                    str(tmp_path),
                    "prepare",
                    "--agent",
                    "claude",
                    "--active-thread-id",
                    thread_id,
                    "--task-family",
                    family,
                    "--semantic-title",
                    title,
                    "--terminal-goal",
                    "merge",
                    "--role",
                    f"{family} driver",
                ]
            )
            == 0
        )
        capsys.readouterr()

    # Without filter: ambiguous exit 2.
    assert th.main(["--repo-root", str(tmp_path), "detect", "--agent", "claude"]) == 2
    multi = json.loads(capsys.readouterr().out)
    assert multi["error_code"] == "MULTIPLE_LIVE_PENDING_ROLLOVERS"
    assert multi["candidate_count"] == 2

    # With filter: single hramatka packet selected.
    assert (
        th.main(
            [
                "--repo-root",
                str(tmp_path),
                "detect",
                "--agent",
                "claude",
                "--task-family",
                "hramatka",
            ]
        )
        == 0
    )
    selected = json.loads(capsys.readouterr().out)
    assert selected["status"] == "pending_start"
    assert selected["task_family_filter"] == "hramatka"
    identity = selected.get("identity") or {}
    assert identity.get("task_family") == "hramatka" or "hramatka" in str(selected).lower()

    # Epic slot claude-hramatka scans bare claude namespace with filter (#5398 slot trap).
    assert (
        th.main(
            [
                "--repo-root",
                str(tmp_path),
                "detect",
                "--agent",
                "claude-hramatka",
                "--task-family",
                "hramatka",
            ]
        )
        == 0
    )
    epic_slot = json.loads(capsys.readouterr().out)
    assert epic_slot["status"] == "pending_start"
    assert epic_slot.get("packet_agent") == "claude"


def test_epic_harness_session_start_surfaces_claude_infra_pending_packet(tmp_path: Path, capsys, monkeypatch) -> None:
    """#5201: --epic harness must resolve to claude-infra and surface its packet.

    Regression: handoff_identity_for_epic used to invent ``claude-harness``, so
    SessionStart reported COLD START while a validated pending_start packet sat
    under ``claude-infra``. Identity guardrail stays intact — a packet bound to
    another thread is still a stop condition (covered elsewhere).
    """
    import subprocess

    monkeypatch.setattr(th, "gather_snapshot", lambda root, url: sample_snapshot(root))

    # Launcher mapping: --epic harness → claude-infra (not phantom claude-harness).
    identity_sh = Path(__file__).resolve().parents[2] / "scripts" / "lib" / "handoff_identity.sh"
    mapped = subprocess.check_output(
        ["bash", "-c", f'source "{identity_sh}" && handoff_identity_for_epic harness'],
        text=True,
        timeout=30,
    ).strip()
    assert mapped == "claude-infra", f"--epic harness must map to claude-infra, got {mapped!r}"
    assert mapped != "claude-harness"

    # Real lane packet lives under claude-infra (prepare as the lane does).
    assert (
        th.main(
            [
                "--repo-root",
                str(tmp_path),
                "prepare",
                "--agent",
                "claude-infra",
                "--active-thread-id",
                "old-infra-thread",
            ]
        )
        == 0
    )
    prepared_payload = json.loads(capsys.readouterr().out)
    assert prepared_payload["agent"] == "claude-infra"

    # Phantom slot: silent miss (the pre-fix failure mode).
    assert th.main(["--repo-root", str(tmp_path), "detect", "--agent", "claude-harness"]) == 0
    assert json.loads(capsys.readouterr().out) == {"agent": "claude-harness", "status": "none"}

    # Resolved slot (post-fix): SessionStart must surface the pending packet.
    assert (
        th.main(
            [
                "--repo-root",
                str(tmp_path),
                "detect",
                "--agent",
                mapped,
                "--format",
                "session-start",
                "--current-thread-id",
                "new-infra-thread",
            ]
        )
        == 0
    )
    startup = capsys.readouterr().out
    assert "PENDING THREAD ROLLOVER DETECTED" in startup
    assert "COLD START: NO LIVE THREAD ROLLOVER" not in startup
    assert "-a claude-infra" in startup
    assert prepared_payload["lineage_id"] in startup
    assert prepared_payload["rollover_id"] in startup


def test_lifecycle_requires_strict_ten_of_ten_before_cleanup(tmp_path: Path, capsys, monkeypatch):
    monkeypatch.setattr(th, "gather_snapshot", lambda root, url: sample_snapshot(root))
    assert (
        th.main(
            [
                "--repo-root",
                str(tmp_path),
                "prepare",
                "--agent",
                "codex",
                "--active-thread-id",
                "old-thread",
                "--stream-epic",
                "4707",
                "--issue-number",
                "5295",
                "--semantic-title",
                "Repair fleet rollover task identity",
                "--terminal-goal",
                "merge",
            ]
        )
        == 0
    )
    packet = json.loads(capsys.readouterr().out)
    assert packet["identity"]["visible_title"] == "#5295 — Repair fleet rollover task identity"
    bind_native_lease(tmp_path / packet["state_file"], "new-thread")
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
    assert "PENDING THREAD ROLLOVER DETECTED" in startup
    assert "bootstrap-replacement" in startup and "confirm-replacement" in startup
    assert "context_canary.py questions" not in startup
    assert (
        th.main(
            [
                "--repo-root",
                str(tmp_path),
                "bootstrap-replacement",
                "--agent",
                "codex",
                "--lineage-id",
                packet["lineage_id"],
                "--rollover-id",
                packet["rollover_id"],
                "--replacement-thread-id",
                "new-thread",
                "--evidence",
                "native title already registered and reconciled",
            ]
        )
        == 0
    )
    capsys.readouterr()
    resume_command = [
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
    assert th.main(resume_command) == 0
    resumed_payload = json.loads(capsys.readouterr().out)
    assert resumed_payload["identity"]["visible_title"] == packet["identity"]["visible_title"]
    state_path = tmp_path / packet["state_file"]
    resumed_bytes = state_path.read_bytes()
    assert th.main(resume_command) == 0
    capsys.readouterr()
    assert state_path.read_bytes() == resumed_bytes
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
    confirm_command = [
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
    assert th.main(confirm_command) == 0
    confirmed_payload = json.loads(capsys.readouterr().out)
    assert confirmed_payload["old_automation_ready_to_delete"] is True
    assert confirmed_payload["identity"]["lifecycle_state"] == "confirmed"
    confirmed_bytes = state_path.read_bytes()
    assert th.main(confirm_command) == 0
    capsys.readouterr()
    assert state_path.read_bytes() == confirmed_bytes


def test_confirmation_rejects_nine_of_ten_and_wrong_reserved_paths(tmp_path: Path, capsys, monkeypatch):
    monkeypatch.setattr(th, "gather_snapshot", lambda root, url: sample_snapshot(root))
    assert (
        th.main(["--repo-root", str(tmp_path), "prepare", "--agent", "codex", "--active-thread-id", "old-thread"]) == 0
    )
    packet = json.loads(capsys.readouterr().out)
    bind_native_lease(tmp_path / packet["state_file"], "new-thread")
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


def test_detect_excludes_registry_terminal_rollover_packets(tmp_path: Path, capsys, monkeypatch):
    """#5851: detect excludes registry-terminal rollover packets (e.g. SUPERSEDED)."""
    monkeypatch.setattr(th, "gather_snapshot", lambda root, url: sample_snapshot(root))

    # 1. Prepare packet 1
    assert th.main(["--repo-root", str(tmp_path), "prepare", "--agent", "codex", "--active-thread-id", "t1"]) == 0
    p1 = json.loads(capsys.readouterr().out)
    lineage1, rollover1 = p1["lineage_id"], p1["rollover_id"]

    # Mark packet 1 as SUPERSEDED in registry
    reg_path1 = tmp_path / ".agent" / "thread-rollover-registry" / "v1" / "codex" / lineage1 / rollover1 / "record.json"
    rec1 = json.loads(reg_path1.read_text(encoding="utf-8"))
    rec1["state"] = "SUPERSEDED"
    rec1["terminal_reason"] = "superseded by new packet"
    th.write_json_atomic(reg_path1, rec1)

    # Detect with single superseded packet -> status: none, excluded_terminal populated
    assert th.main(["--repo-root", str(tmp_path), "detect", "--agent", "codex"]) == 0
    detected_single = json.loads(capsys.readouterr().out)
    assert detected_single["status"] == "none"
    assert detected_single["excluded_terminal"] == [
        {"agent": "codex", "lineage_id": lineage1, "rollover_id": rollover1, "state": "SUPERSEDED"}
    ]

    # Test session-start output for single superseded packet
    assert th.main(["--repo-root", str(tmp_path), "detect", "--agent", "codex", "--format", "session-start"]) == 0
    start_output = capsys.readouterr().out
    assert "COLD START: NO LIVE THREAD ROLLOVER" in start_output
    assert f"Excluded terminal rollover: codex/{lineage1}/{rollover1} (SUPERSEDED)" in start_output

    # 2. Prepare packet 2 (live)
    assert th.main(["--repo-root", str(tmp_path), "prepare", "--agent", "codex", "--active-thread-id", "t2"]) == 0
    p2 = json.loads(capsys.readouterr().out)
    lineage2, rollover2 = p2["lineage_id"], p2["rollover_id"]

    # Detect with 1 superseded packet + 1 live packet -> resolves packet 2 directly instead of ambiguous error
    assert th.main(["--repo-root", str(tmp_path), "detect", "--agent", "codex"]) == 0
    detected_multi = json.loads(capsys.readouterr().out)
    assert detected_multi["status"] == "pending_start"
    assert detected_multi["lineage_id"] == lineage2
    assert detected_multi["rollover_id"] == rollover2
    assert detected_multi["excluded_terminal"] == [
        {"agent": "codex", "lineage_id": lineage1, "rollover_id": rollover1, "state": "SUPERSEDED"}
    ]

    # Sibling sweep: check rollover_identity_snapshot
    snapshot = th.rollover_identity_snapshot(tmp_path, agent="codex")
    assert snapshot["candidate_count"] == 1
    assert snapshot["candidates"][0]["lineage_id"] == lineage2
    assert snapshot["excluded_terminal"] == [
        {"agent": "codex", "lineage_id": lineage1, "rollover_id": rollover1, "state": "SUPERSEDED"}
    ]


def test_detect_registry_non_terminal_record_is_detected(tmp_path: Path, capsys, monkeypatch):
    """Negative control: non-terminal registry record is still detected as live."""
    monkeypatch.setattr(th, "gather_snapshot", lambda root, url: sample_snapshot(root))

    assert th.main(["--repo-root", str(tmp_path), "prepare", "--agent", "codex", "--active-thread-id", "t1"]) == 0
    p1 = json.loads(capsys.readouterr().out)

    assert th.main(["--repo-root", str(tmp_path), "detect", "--agent", "codex"]) == 0
    detected = json.loads(capsys.readouterr().out)
    assert detected["status"] == "pending_start"
    assert detected["lineage_id"] == p1["lineage_id"]
    assert "excluded_terminal" not in detected


def test_detect_corrupt_registry_record_fails_open(tmp_path: Path, capsys, monkeypatch):
    """Corrupt registry record must not crash detect, fails open, and surfaces error."""
    monkeypatch.setattr(th, "gather_snapshot", lambda root, url: sample_snapshot(root))

    assert th.main(["--repo-root", str(tmp_path), "prepare", "--agent", "codex", "--active-thread-id", "t1"]) == 0
    p1 = json.loads(capsys.readouterr().out)
    lineage1, rollover1 = p1["lineage_id"], p1["rollover_id"]

    # Corrupt registry record
    reg_path1 = tmp_path / ".agent" / "thread-rollover-registry" / "v1" / "codex" / lineage1 / rollover1 / "record.json"
    reg_path1.write_text("{invalid json", encoding="utf-8")

    assert th.main(["--repo-root", str(tmp_path), "detect", "--agent", "codex"]) == 0
    detected = json.loads(capsys.readouterr().out)
    assert detected["status"] == "pending_start"
    assert detected["lineage_id"] == lineage1
    assert "registry_errors" in detected
    assert len(detected["registry_errors"]) == 1
    assert "corrupt or unreadable" in detected["registry_errors"][0]
