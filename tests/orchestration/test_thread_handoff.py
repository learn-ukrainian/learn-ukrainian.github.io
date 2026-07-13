from __future__ import annotations

import json
import sqlite3
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest

from scripts.orchestration import thread_handoff as th
from scripts.orchestration import thread_handoff_canary as canary


def sample_snapshot(tmp_path: Path) -> dict:
    return {
        "generated_at": "2026-05-30T08:00:00Z",
        "git": {
            "repo_root": str(tmp_path), "branch": "main", "head": "abc123def0",
            "full_head": "abc123def0456789", "ahead_behind": None,
            "last_commits": [], "modified_files": [],
        },
        "monitor": {"base_url": "http://127.0.0.1:8765", "orient": {}, "active_delegates": {"total": 0, "tasks": []}, "completed_delegates": {"total": 0, "tasks": []}, "worktrees": {"count": 0, "worktrees": []}},
        "github": {"open_prs": [], "open_issues": []},
    }


def prepared(*, agent: str = "orchestrator", thread_id: str = "old-thread") -> dict:
    return th.prepare_state(
        {"schema_version": th.SCHEMA_VERSION}, agent=agent,
        now=datetime(2026, 5, 30, 8, 0, tzinfo=UTC), active_thread_id=thread_id,
        active_automation_id="old-auto", context_percent=86.0, force_new_replacement=False,
    )


def test_v2_state_has_unique_rollover_and_lineage_runtime_paths():
    state = prepared()
    replacement = state["replacement"]

    assert state["schema_version"] == 2
    assert replacement["rollover_id"].startswith("rollover-")
    assert replacement["lineage_id"] == th.lineage_id_for("orchestrator", "old-thread")
    assert replacement["runtime_path"] == (
        ".agent/thread-rollovers/orchestrator/"
        f"{replacement['lineage_id']}/generation-0001/{replacement['rollover_id']}"
    )
    assert replacement["bootstrap_prompt_path"].startswith(replacement["runtime_path"])
    assert replacement["handoff_path"].startswith(replacement["runtime_path"])


def test_pending_prepare_refuses_unless_explicitly_forced():
    state = prepared()
    with pytest.raises(ValueError, match="pending rollover"):
        th.prepare_state(
            state, agent="orchestrator", now=datetime(2026, 5, 30, 8, 1, tzinfo=UTC),
            active_thread_id="old-thread", active_automation_id=None, context_percent=None,
            force_new_replacement=False,
        )

    forced = th.prepare_state(
        state, agent="orchestrator", now=datetime(2026, 5, 30, 8, 1, tzinfo=UTC),
        active_thread_id="old-thread", active_automation_id=None, context_percent=None,
        force_new_replacement=True,
    )
    assert forced["replacement"]["rollover_id"] != state["replacement"]["rollover_id"]


def test_resume_is_deterministic_and_refuses_a_different_thread():
    state = prepared()
    rollover_id = state["replacement"]["rollover_id"]
    resumed = th.resume_state(
        state, rollover_id=rollover_id, replacement_thread_id="new-thread",
        now=datetime(2026, 5, 30, 8, 1, tzinfo=UTC),
    )
    repeated = th.resume_state(
        resumed, rollover_id=rollover_id, replacement_thread_id="new-thread",
        now=datetime(2026, 5, 30, 8, 2, tzinfo=UTC),
    )

    assert repeated == resumed
    with pytest.raises(ValueError, match="different replacement thread"):
        th.resume_state(
            resumed, rollover_id=rollover_id, replacement_thread_id="other-thread",
            now=datetime(2026, 5, 30, 8, 2, tzinfo=UTC),
        )


def test_confirm_requires_matching_script_proven_canary_pass(tmp_path: Path):
    state = prepared()
    replacement = state["replacement"]
    resumed = th.resume_state(
        state, rollover_id=replacement["rollover_id"], replacement_thread_id="new-thread",
        now=datetime(2026, 5, 30, 8, 1, tzinfo=UTC),
    )
    proof_path = tmp_path / "canary-pass.json"
    canary.write_json_atomic(proof_path, canary.build_pass_proof(
        rollover_id=replacement["rollover_id"], replacement_thread_id="new-thread",
        challenge=replacement["canary_challenge"], now=datetime(2026, 5, 30, 8, 2, tzinfo=UTC),
    ))

    confirmed = th.confirm_started(
        resumed, new_thread_id="new-thread", new_automation_id=None, confirmed_by="tester",
        now=datetime(2026, 5, 30, 8, 3, tzinfo=UTC), canary_proof=proof_path,
    )
    assert confirmed["replacement"]["status"] == "started"
    assert confirmed["cleanup"]["old_automation_ready_to_delete"] is True

    wrong_proof = tmp_path / "wrong.json"
    canary.write_json_atomic(wrong_proof, canary.build_pass_proof(
        rollover_id="other-rollover", replacement_thread_id="new-thread",
        challenge=replacement["canary_challenge"], now=datetime(2026, 5, 30, 8, 2, tzinfo=UTC),
    ))
    with pytest.raises(ValueError, match="script-proven canary PASS"):
        th.confirm_started(
            resumed, new_thread_id="new-thread", new_automation_id=None, confirmed_by="tester",
            now=datetime(2026, 5, 30, 8, 3, tzinfo=UTC), canary_proof=wrong_proof,
        )


def test_confirm_refuses_unresumed_or_identity_mismatch(tmp_path: Path):
    state = prepared()
    proof_path = tmp_path / "proof.json"
    replacement = state["replacement"]
    canary.write_json_atomic(proof_path, canary.build_pass_proof(
        rollover_id=replacement["rollover_id"], replacement_thread_id="new-thread",
        challenge=replacement["canary_challenge"], now=datetime(2026, 5, 30, 8, 2, tzinfo=UTC),
    ))
    with pytest.raises(ValueError, match="must be resumed"):
        th.confirm_started(
            state, new_thread_id="new-thread", new_automation_id=None, confirmed_by="tester",
            now=datetime(2026, 5, 30, 8, 3, tzinfo=UTC), canary_proof=proof_path,
        )


def test_v1_state_requires_explicit_migration_and_discards_unverified_replacement(tmp_path: Path, capsys, monkeypatch):
    state_path = tmp_path / ".agent/legacy.json"
    state_path.parent.mkdir(parents=True)
    state_path.write_text(json.dumps({"schema_version": 1, "active": {"thread_id": "old-thread"}, "replacement": {"status": "pending_start"}}), encoding="utf-8")
    monkeypatch.setattr(th, "gather_snapshot", lambda root, url: sample_snapshot(root))
    base = ["--repo-root", str(tmp_path), "prepare", "--state-file", ".agent/legacy.json", "--active-thread-id", "old-thread"]

    assert th.main(base) == 2
    assert "requires an explicit migration" in json.loads(capsys.readouterr().out)["error"]
    assert th.main([*base, "--migrate-v1"]) == 0
    payload = json.loads(capsys.readouterr().out)
    migrated = json.loads(state_path.read_text(encoding="utf-8"))
    assert payload["rollover_id"] == migrated["replacement"]["rollover_id"]
    assert migrated["schema_version"] == 2
    assert migrated["migrated_from_v1_at"]


def test_prepare_parallel_lineages_do_not_collide(tmp_path: Path, capsys, monkeypatch):
    monkeypatch.setattr(th, "gather_snapshot", lambda root, url: sample_snapshot(root))
    outputs = []
    for thread_id in ("old-a", "old-b"):
        assert th.main(["--repo-root", str(tmp_path), "prepare", "--agent", "codex", "--active-thread-id", thread_id]) == 0
        outputs.append(json.loads(capsys.readouterr().out))

    assert outputs[0]["lineage_id"] != outputs[1]["lineage_id"]
    assert outputs[0]["state_file"] != outputs[1]["state_file"]
    assert outputs[0]["runtime_path"] != outputs[1]["runtime_path"]
    assert (tmp_path / outputs[0]["bootstrap_file"]).is_file()
    assert (tmp_path / outputs[1]["bootstrap_file"]).is_file()


def test_cli_requires_the_exact_rollover_and_canary_proof(tmp_path: Path, capsys, monkeypatch):
    monkeypatch.setattr(th, "gather_snapshot", lambda root, url: sample_snapshot(root))
    assert th.main([
        "--repo-root", str(tmp_path), "prepare", "--active-thread-id", "old-thread",
    ]) == 0
    prepared_payload = json.loads(capsys.readouterr().out)
    state_path = tmp_path / prepared_payload["state_file"]
    state = json.loads(state_path.read_text(encoding="utf-8"))

    assert th.main([
        "--repo-root", str(tmp_path), "resume", "--lineage-id", prepared_payload["lineage_id"],
        "--rollover-id", prepared_payload["rollover_id"], "--replacement-thread-id", "new-thread",
    ]) == 0
    capsys.readouterr()
    proof_path = tmp_path / state["replacement"]["canary_proof_path"]
    assert canary.main([
        "--rollover-id", prepared_payload["rollover_id"], "--replacement-thread-id", "new-thread",
        "--challenge", state["replacement"]["canary_challenge"], "--proof-file", str(proof_path),
    ]) == 0
    capsys.readouterr()

    assert th.main([
        "--repo-root", str(tmp_path), "confirm-started", "--lineage-id", prepared_payload["lineage_id"],
        "--rollover-id", prepared_payload["rollover_id"], "--new-thread-id", "new-thread",
        "--canary-proof", state["replacement"]["canary_proof_path"],
    ]) == 0
    confirmed_payload = json.loads(capsys.readouterr().out)
    assert confirmed_payload["old_automation_ready_to_delete"] is True


def test_prepare_retains_router_guard(tmp_path: Path, capsys, monkeypatch):
    monkeypatch.setattr(th, "gather_snapshot", lambda root, url: sample_snapshot(root))
    rc = th.main(["--repo-root", str(tmp_path), "prepare", "--active-thread-id", "old-thread", "--write-current"])
    payload = json.loads(capsys.readouterr().out)

    assert rc == 2
    assert "disabled by default" in payload["error"]
    assert not (tmp_path / "docs/session-state/current.md").exists()


def test_prepare_refuses_corrupted_state_without_overwrite(tmp_path: Path, capsys, monkeypatch):
    state_path = tmp_path / ".agent/corrupt.json"
    state_path.parent.mkdir(parents=True)
    state_path.write_text("{not-json", encoding="utf-8")
    monkeypatch.setattr(th, "gather_snapshot", lambda root, url: sample_snapshot(root))

    rc = th.main(["--repo-root", str(tmp_path), "prepare", "--state-file", ".agent/corrupt.json", "--active-thread-id", "old-thread"])
    assert rc == 2
    assert "unreadable state file" in json.loads(capsys.readouterr().out)["error"]
    assert state_path.read_text(encoding="utf-8") == "{not-json"


def test_bootstrap_explicitly_forbids_history_resume_and_contains_proof_protocol(tmp_path: Path):
    state = prepared()
    prompt = th.render_bootstrap_prompt(sample_snapshot(tmp_path), state, context_threshold=82.0)

    assert "do not fork, continue, or resume provider conversation history" in prompt
    assert "thread_handoff_canary.py" in prompt
    assert state["replacement"]["rollover_id"] in prompt
    assert state["replacement"]["canary_challenge"] in prompt


def test_check_state_flags_pending_stale_and_corrupt_state():
    state = prepared()
    facts, warnings = th.check_state(
        state, now=datetime(2026, 5, 31, 8, 0, tzinfo=UTC), stale_after=timedelta(hours=12),
        context_percent=90.0, context_threshold=82.0,
    )
    assert any(fact.startswith("rollover_id=rollover-") for fact in facts)
    assert any("pending_start" in warning for warning in warnings)
    assert any("context estimate" in warning for warning in warnings)


def test_atomic_writer_and_canary_validation_reject_tampering(tmp_path: Path):
    proof_path = tmp_path / "proof.json"
    payload = canary.build_pass_proof(
        rollover_id="rollover-1", replacement_thread_id="new-thread", challenge="challenge",
        now=datetime(2026, 5, 30, 8, 0, tzinfo=UTC),
    )
    canary.write_json_atomic(proof_path, payload)
    assert canary.load_and_validate_pass_proof(proof_path, rollover_id="rollover-1", replacement_thread_id="new-thread", challenge="challenge")[1] is None
    payload["status"] = "FAIL"
    canary.write_json_atomic(proof_path, payload)
    assert "did not report PASS" in canary.load_and_validate_pass_proof(proof_path, rollover_id="rollover-1", replacement_thread_id="new-thread", challenge="challenge")[1]


def test_inspect_codex_home_does_not_use_history_resume(tmp_path: Path):
    codex_home = tmp_path / ".codex"
    codex_home.mkdir()
    db = codex_home / "state_1.sqlite"
    with sqlite3.connect(db) as conn:
        conn.execute("create table threads (id text, title text, cwd text, archived integer, updated_at integer)")
        conn.execute("insert into threads values ('thread-1', 'Example', '/tmp/repo', 0, 100)")

    audit = th.inspect_codex_home(codex_home)
    assert audit["thread_count"] == 1
    assert audit["history_resume_used"] is False
