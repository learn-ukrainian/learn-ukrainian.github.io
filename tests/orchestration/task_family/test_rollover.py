"""Regression coverage for the native rollover Task Family Manager adapter."""

from __future__ import annotations

import json
import sqlite3
import subprocess
import time
from pathlib import Path
from uuid import uuid4

import pytest

from scripts.orchestration.task_family import codex_state, rollover
from scripts.orchestration.task_family.model import RelationType
from scripts.orchestration.task_family.storage import TaskFamilyStorage, advisory_lock


def _write_db(path: Path, rows: list[tuple[str, str, str, int, str | None, str]]) -> None:
    connection = sqlite3.connect(path)
    connection.execute(
        "CREATE TABLE threads (id TEXT PRIMARY KEY, title TEXT, cwd TEXT, "
        "archived INTEGER, archived_at TEXT, host TEXT)"
    )
    connection.executemany("INSERT INTO threads VALUES (?, ?, ?, ?, ?, ?)", rows)
    connection.commit()
    connection.close()


def _transition(tmp_path: Path) -> dict[str, object]:
    source_id, replacement_id, unrelated_id = (str(uuid4()) for _ in range(3))
    lineage_id = "lineage-1234567890abcdef12345678"
    title, title_source, _ = rollover.rollover_title(
        agent="codex",
        lineage_id=lineage_id,
        generation=1,
        epic_title="Curriculum lifecycle",
        goal="CI unblock",
        phase="P5",
        next_phase="P6",
    )
    prepared = rollover.prepare_transition(
        repo_root=tmp_path,
        agent="codex",
        lineage_id=lineage_id,
        rollover_id="rollover-abc123",
        generation=1,
        source_thread_id=source_id,
        intended_title=title,
        title_source=title_source,
        bootstrap_prompt_path=".agent/thread-rollovers/bootstrap.md",
    )
    db = tmp_path / "state_5.sqlite"
    _write_db(
        db,
        [
            (source_id, "Lifecycle source", str(tmp_path), 0, None, "local"),
            (replacement_id, "Resume codex rollover", str(tmp_path), 0, None, "local"),
            (unrelated_id, "Resume codex rollover", str(tmp_path), 0, None, "local"),
        ],
    )
    source = codex_state.read_thread_record(db, task_id=source_id)
    replacement = codex_state.read_thread_record(db, task_id=replacement_id)
    binding = rollover.bind_replacement(
        repo_root=tmp_path,
        family_id=str(prepared["family_id"]),
        operation_id=str(prepared["operation_id"]),
        source=source,
        replacement=replacement,
        db_path=db,
        evidence="native create_thread response threadId",
    )
    return {
        "source_id": source_id,
        "replacement_id": replacement_id,
        "unrelated_id": unrelated_id,
        "lineage_id": lineage_id,
        "title": title,
        "db": db,
        "prepared": prepared,
        "binding": binding,
    }


def _confirmed_state(data: dict[str, object]) -> dict[str, object]:
    source_id = str(data["source_id"])
    replacement_id = str(data["replacement_id"])
    return {
        "active": {"thread_id": source_id},
        "replacement": {
            "status": "started",
            "thread_id": replacement_id,
            "resumed_thread_id": replacement_id,
            "confirmed_at": "2026-07-15T10:00:00Z",
            "canary_proof": {"status": "PASS", "replacement_thread_id": replacement_id},
            "strict_verdict": {"verdict": "PASS", "correct": 10, "k": 10},
        },
        "cleanup": {"old_automation_ready_to_delete": True},
    }


def _title_reconciled(tmp_path: Path, data: dict[str, object]) -> None:
    prepared = data["prepared"]
    assert isinstance(prepared, dict)
    with sqlite3.connect(data["db"]) as connection:
        connection.execute(
            "UPDATE threads SET title = ? WHERE id = ?",
            (data["title"], data["replacement_id"]),
        )
        connection.commit()
    result = rollover.reconcile_action(
        repo_root=tmp_path,
        family_id=str(prepared["family_id"]),
        operation_id=str(prepared["operation_id"]),
        action="title",
        db_path=Path(data["db"]),
    )
    assert result["ok"] is True


def test_rollover_titles_are_meaningful_bounded_and_have_unique_fallback() -> None:
    title, source, metadata = rollover.rollover_title(
        agent="codex",
        lineage_id="lineage-1234567890abcdef12345678",
        generation=1,
        epic_title="Curriculum lifecycle",
        goal="CI unblock",
        phase="P5",
        next_phase="P6",
    )
    assert title == "Curriculum lifecycle — P5 CI unblock → P6"
    assert source == "durable_metadata"
    assert metadata["phase"] == "P5"
    fallback, fallback_source, _ = rollover.rollover_title(
        agent="codex",
        lineage_id="lineage-1234567890abcdef12345678",
        generation=17,
        epic_title=None,
        goal=None,
        phase=None,
    )
    assert "lineage-1234567890abcdef12345678" in fallback
    assert "g0017" in fallback
    assert len(fallback) <= 60
    assert fallback_source == "lineage_generation_fallback"
    assert "resume codex rollover" not in fallback.casefold()
    orchestrator_fallback, _, _ = rollover.rollover_title(
        agent="orchestrator",
        lineage_id="lineage-fedcba0987654321fedcba09",
        generation=9999,
        epic_title=None,
        goal=None,
        phase=None,
    )
    assert "lineage-fedcba0987654321fedcba09" in orchestrator_fallback
    assert "g9999" in orchestrator_fallback
    assert len(orchestrator_fallback) <= 60
    with pytest.raises(ValueError, match="supplied together"):
        rollover.rollover_title(
            agent="codex",
            lineage_id="lineage-1234567890abcdef12345678",
            generation=1,
            epic_title="Infrastructure",
            goal=None,
            phase="P1",
        )


def test_transition_identity_is_stable_per_packet_without_splitting_the_family() -> None:
    first_family, first_operation = rollover.transition_identity(
        lineage_id="lineage-1234567890abcdef12345678",
        generation=1,
        rollover_id="rollover-first",
    )
    retry_family, retry_operation = rollover.transition_identity(
        lineage_id="lineage-1234567890abcdef12345678",
        generation=1,
        rollover_id="rollover-first",
    )
    second_family, second_operation = rollover.transition_identity(
        lineage_id="lineage-1234567890abcdef12345678",
        generation=1,
        rollover_id="rollover-second",
    )

    assert first_family == retry_family == second_family
    assert first_operation == retry_operation
    assert first_operation != second_operation


def test_advisory_lock_blocks_a_second_process_until_release(tmp_path: Path) -> None:
    lock_path = tmp_path / "lineage" / ".native-intent.lock"
    ready_path = tmp_path / "child-ready"
    acquired_path = tmp_path / "child-acquired"
    code = (
        "import sys\n"
        "from pathlib import Path\n"
        "from scripts.orchestration.task_family.storage import advisory_lock\n"
        "lock_path, ready_path, acquired_path = map(Path, sys.argv[1:])\n"
        "ready_path.write_text('ready', encoding='utf-8')\n"
        "with advisory_lock(lock_path):\n"
        "    acquired_path.write_text('acquired', encoding='utf-8')\n"
    )
    repo_root = Path(__file__).resolve().parents[3]
    with advisory_lock(lock_path):
        child = subprocess.Popen(
            [".venv/bin/python", "-c", code, str(lock_path), str(ready_path), str(acquired_path)],
            cwd=repo_root,
        )
        deadline = time.monotonic() + 5
        while not ready_path.exists() and time.monotonic() < deadline:
            time.sleep(0.01)
        assert ready_path.exists()
        assert acquired_path.exists() is False
        assert child.poll() is None
    stdout, stderr = child.communicate(timeout=5)
    assert child.returncode == 0, (stdout, stderr)
    assert acquired_path.read_text(encoding="utf-8") == "acquired"


def test_pristine_transition_supersession_is_durable_idempotent_and_blocks_old_create(tmp_path: Path) -> None:
    source_id = str(uuid4())
    common = {
        "repo_root": tmp_path,
        "agent": "codex",
        "lineage_id": "lineage-1234567890abcdef12345678",
        "generation": 1,
        "source_thread_id": source_id,
        "intended_title": "Infrastructure — P1 repair rollover",
        "title_source": "durable_metadata",
        "bootstrap_prompt_path": "bootstrap.md",
    }
    old = rollover.prepare_transition(**common, rollover_id="rollover-old")
    supersedes = {
        "family_id": str(old["family_id"]),
        "operation_id": str(old["operation_id"]),
        "rollover_id": "rollover-old",
    }
    successor = rollover.prepare_transition(**common, rollover_id="rollover-new", supersedes=supersedes)
    old_storage = TaskFamilyStorage(tmp_path, str(old["family_id"]), str(old["operation_id"]))
    old_plan = old_storage.rollover_plan_path.read_bytes()
    kwargs = {
        "repo_root": tmp_path,
        "family_id": str(old["family_id"]),
        "operation_id": str(old["operation_id"]),
        "lineage_id": common["lineage_id"],
        "generation": 1,
        "source_thread_id": source_id,
        "successor_rollover_id": "rollover-new",
        "successor_operation_id": str(successor["operation_id"]),
        "evidence": "No native create was authorized or invoked.",
        "expected_rollover_id": "rollover-old",
    }

    first = rollover.supersede_unexecuted_transition(**kwargs)
    retry = rollover.supersede_unexecuted_transition(**kwargs)
    activated = rollover.activate_superseding_transition(
        repo_root=tmp_path,
        family_id=str(successor["family_id"]),
        operation_id=str(successor["operation_id"]),
    )

    assert first["status"] == "superseded"
    assert retry["status"] == "already_superseded"
    assert activated["status"] == "awaiting_native_create"
    assert old_storage.rollover_plan_path.read_bytes() == old_plan
    assert old_storage.rollover_supersession_path.exists()
    assert old_storage.load_state()["details"]["status"] == "superseded_before_native_create"
    receipt = old_storage.load_receipt()
    assert receipt.actual == ()
    assert {item.action for item in receipt.skipped} == {item.action for item in receipt.planned}
    old_action = rollover.request_create_action(
        repo_root=tmp_path,
        family_id=str(old["family_id"]),
        operation_id=str(old["operation_id"]),
    )
    assert old_action["needs_native_action"] is False
    assert old_action["status"] == "superseded_before_native_create"
    with pytest.raises(ValueError, match="different exact successor"):
        rollover.assert_transition_supersedable(
            repo_root=tmp_path,
            family_id=str(old["family_id"]),
            operation_id=str(old["operation_id"]),
            lineage_id=common["lineage_id"],
            generation=1,
            source_thread_id=source_id,
            successor_rollover_id="rollover-other",
            successor_operation_id=str(uuid4()),
            expected_rollover_id="rollover-old",
        )


def test_superseding_transition_stays_blocked_until_exact_predecessor_is_superseded(tmp_path: Path) -> None:
    source_id = str(uuid4())
    common = {
        "repo_root": tmp_path,
        "agent": "codex",
        "lineage_id": "lineage-1234567890abcdef12345678",
        "generation": 1,
        "source_thread_id": source_id,
        "intended_title": "Infrastructure — P1 activation gate",
        "title_source": "durable_metadata",
        "bootstrap_prompt_path": "bootstrap.md",
    }
    old = rollover.prepare_transition(**common, rollover_id="rollover-old")
    supersedes = {
        "family_id": str(old["family_id"]),
        "operation_id": str(old["operation_id"]),
        "rollover_id": "rollover-old",
    }
    successor = rollover.prepare_transition(**common, rollover_id="rollover-new", supersedes=supersedes)

    blocked = rollover.request_create_action(
        repo_root=tmp_path,
        family_id=str(successor["family_id"]),
        operation_id=str(successor["operation_id"]),
    )
    assert blocked["status"] == "supersession_pending"
    assert blocked["needs_native_action"] is False
    with pytest.raises(ValueError, match="has not been durably superseded"):
        rollover.activate_superseding_transition(
            repo_root=tmp_path,
            family_id=str(successor["family_id"]),
            operation_id=str(successor["operation_id"]),
        )
    with pytest.raises(ValueError, match="supersedes must contain"):
        rollover.prepare_transition(
            **common,
            rollover_id="rollover-malformed",
            supersedes={"operation_id": str(old["operation_id"])},
        )


@pytest.mark.parametrize("unsafe_state", ["binding", "failed_ack", "success_ack", "authorization"])
def test_supersession_refuses_bound_partial_or_authorized_native_create(
    tmp_path: Path,
    unsafe_state: str,
) -> None:
    source_id = str(uuid4())
    transition = rollover.prepare_transition(
        repo_root=tmp_path,
        agent="codex",
        lineage_id="lineage-1234567890abcdef12345678",
        rollover_id=f"rollover-{unsafe_state}",
        generation=1,
        source_thread_id=source_id,
        intended_title="Infrastructure — P1 fail closed",
        title_source="durable_metadata",
        bootstrap_prompt_path="bootstrap.md",
    )
    storage = TaskFamilyStorage(tmp_path, str(transition["family_id"]), str(transition["operation_id"]))
    operation = {
        "repo_root": tmp_path,
        "family_id": str(transition["family_id"]),
        "operation_id": str(transition["operation_id"]),
    }
    if unsafe_state == "binding":
        storage.write_immutable_json(storage.rollover_binding_path, {"binding": "exists"})
    elif unsafe_state == "authorization":
        assert rollover.request_create_action(**operation)["needs_native_action"] is True
    else:
        rollover.record_native_result(
            **operation,
            action="create",
            succeeded=unsafe_state == "success_ack",
            evidence="native create response",
            error="partial failure" if unsafe_state == "failed_ack" else "",
        )

    with pytest.raises(ValueError, match=r"cannot be superseded|untouched native-create intent"):
        rollover.assert_transition_supersedable(
            **operation,
            lineage_id="lineage-1234567890abcdef12345678",
            generation=1,
            source_thread_id=source_id,
            successor_rollover_id="rollover-successor",
            successor_operation_id=str(uuid4()),
            expected_rollover_id=f"rollover-{unsafe_state}",
        )


def test_prepare_and_bind_persist_exact_ids_typed_relations_and_receipt(tmp_path: Path) -> None:
    data = _transition(tmp_path)
    prepared = data["prepared"]
    assert isinstance(prepared, dict)
    storage = TaskFamilyStorage(tmp_path, str(prepared["family_id"]), str(prepared["operation_id"]))
    manifest = storage.load_manifest()
    assert manifest.seed_task_id == data["source_id"]
    assert {node.task_id for node in manifest.nodes} == {data["source_id"], data["replacement_id"]}
    assert {relation.relation_type for relation in manifest.relations} == {
        RelationType.REPLACEMENT_OF,
        RelationType.ROLLOVER_GENERATION_OF,
    }
    assert {relation.source_id for relation in manifest.relations} == {data["replacement_id"]}
    assert {relation.target_id for relation in manifest.relations} == {data["source_id"]}
    receipt = storage.load_receipt()
    assert any(
        item.action == "create_replacement" and item.resource_id == data["replacement_id"] for item in receipt.actual
    )
    assert storage.rollover_binding_path.exists()
    assert "Resume codex rollover" not in storage.read_json(storage.rollover_plan_path)["intended_title"]
    retry = rollover.request_create_action(
        repo_root=tmp_path,
        family_id=str(prepared["family_id"]),
        operation_id=str(prepared["operation_id"]),
    )
    assert retry["status"] == "already_bound"
    assert retry["needs_native_action"] is False
    assert any(item.action == "create_retry_readback" for item in storage.load_receipt().skipped)


def test_create_partial_failure_retries_but_success_ack_blocks_duplicate(tmp_path: Path) -> None:
    source_id = str(uuid4())
    transition = rollover.prepare_transition(
        repo_root=tmp_path,
        agent="codex",
        lineage_id="lineage-1234567890abcdef12345678",
        rollover_id="rollover-create-retry",
        generation=1,
        source_thread_id=source_id,
        intended_title="Infrastructure — P1 native lifecycle",
        title_source="durable_metadata",
        bootstrap_prompt_path="bootstrap.md",
    )
    kwargs = {
        "repo_root": tmp_path,
        "family_id": str(transition["family_id"]),
        "operation_id": str(transition["operation_id"]),
    }
    first = rollover.request_create_action(**kwargs)
    assert first["needs_native_action"] is True
    rollover.record_native_result(
        **kwargs,
        action="create",
        succeeded=False,
        evidence="create_thread error response",
        error="temporary native failure",
    )
    assert rollover.request_create_action(**kwargs)["needs_native_action"] is True
    rollover.record_native_result(
        **kwargs,
        action="create",
        succeeded=True,
        evidence="create_thread returned 00000000-0000-0000-0000-000000000002",
    )
    blocked = rollover.request_create_action(**kwargs)
    assert blocked["ok"] is False
    assert blocked["status"] == "awaiting_create_binding"
    assert blocked["needs_native_action"] is False
    storage = TaskFamilyStorage(tmp_path, str(transition["family_id"]), str(transition["operation_id"]))
    assert any(item.action == "create_binding_missing_after_ack" for item in storage.load_receipt().failures)


def test_app_absence_and_db_absence_are_durable_and_fail_closed(tmp_path: Path) -> None:
    source_id = str(uuid4())
    transition = rollover.prepare_transition(
        repo_root=tmp_path,
        agent="codex",
        lineage_id="lineage-1234567890abcdef12345678",
        rollover_id="rollover-app-absent",
        generation=1,
        source_thread_id=source_id,
        intended_title="Infrastructure — P1 native lifecycle",
        title_source="durable_metadata",
        bootstrap_prompt_path="bootstrap.md",
    )
    blocked = rollover.record_blocker(
        repo_root=tmp_path,
        family_id=str(transition["family_id"]),
        operation_id=str(transition["operation_id"]),
        action="create",
        error="create_thread tool unavailable",
        evidence="app capability discovery",
    )
    assert blocked["ok"] is False
    storage = TaskFamilyStorage(tmp_path, str(transition["family_id"]), str(transition["operation_id"]))
    assert storage.load_state()["state"] == "blocked"
    assert storage.load_receipt().failures[-1].action == "create_preflight_blocked"
    assert not storage.manifest_path.exists()


def test_title_partial_failure_retry_and_readback_do_not_create_twice(tmp_path: Path) -> None:
    data = _transition(tmp_path)
    prepared = data["prepared"]
    assert isinstance(prepared, dict)
    kwargs = {
        "repo_root": tmp_path,
        "family_id": str(prepared["family_id"]),
        "operation_id": str(prepared["operation_id"]),
    }
    action = rollover.request_action(**kwargs, action="title", db_path=Path(data["db"]))
    assert action["needs_native_action"] is True
    assert action["arguments"] == {"threadId": data["replacement_id"], "title": data["title"]}
    failed = rollover.record_native_result(
        **kwargs,
        action="title",
        succeeded=False,
        evidence="set_thread_title response",
        error="temporary native failure",
    )
    assert failed["ok"] is False
    assert rollover.request_action(**kwargs, action="title", db_path=Path(data["db"]))["needs_native_action"] is True
    with sqlite3.connect(data["db"]) as connection:
        connection.execute("UPDATE threads SET title = ? WHERE id = ?", (data["title"], data["replacement_id"]))
        connection.commit()
    rollover.record_native_result(
        **kwargs,
        action="title",
        succeeded=True,
        evidence="set_thread_title success",
    )
    reconciled = rollover.reconcile_action(**kwargs, action="title", db_path=Path(data["db"]))
    assert reconciled["ok"] is True
    retry = rollover.request_action(**kwargs, action="title", db_path=Path(data["db"]))
    assert retry["needs_native_action"] is False
    storage = TaskFamilyStorage(tmp_path, str(prepared["family_id"]), str(prepared["operation_id"]))
    assert len([item for item in storage.load_receipt().actual if item.action == "create_replacement"]) == 1
    assert any(item.action == "title_retry_readback" for item in storage.load_receipt().skipped)


def test_unconfirmed_predecessor_is_preserved(tmp_path: Path) -> None:
    data = _transition(tmp_path)
    _title_reconciled(tmp_path, data)
    prepared = data["prepared"]
    assert isinstance(prepared, dict)
    state = _confirmed_state(data)
    state["replacement"]["status"] = "resumed"
    state["cleanup"]["old_automation_ready_to_delete"] = False
    result = rollover.request_action(
        repo_root=tmp_path,
        family_id=str(prepared["family_id"]),
        operation_id=str(prepared["operation_id"]),
        action="archive",
        db_path=Path(data["db"]),
        state=state,
        source_status="idle",
        pin_state="unpinned",
        evidence="native read_thread response",
    )
    assert result["ok"] is False
    assert any("not confirmed" in blocker or "locked" in blocker for blocker in result["blockers"])
    assert codex_state.read_thread_record(Path(data["db"]), task_id=str(data["source_id"])).archived is False
    storage = TaskFamilyStorage(tmp_path, str(prepared["family_id"]), str(prepared["operation_id"]))
    assert "native read_thread response" in storage.load_receipt().failures[-1].reason


@pytest.mark.parametrize(
    ("source_status", "pin_state", "expected"),
    [
        ("active", "unpinned", "not authoritatively idle"),
        ("idle", "pinned", "not authoritatively unpinned"),
        ("idle", "unknown", "not authoritatively unpinned"),
        ("unknown", "unknown", "not authoritatively idle"),
    ],
)
def test_running_pinned_and_unknown_predecessors_are_preserved(
    tmp_path: Path,
    source_status: str,
    pin_state: rollover.PinState,
    expected: str,
) -> None:
    data = _transition(tmp_path)
    _title_reconciled(tmp_path, data)
    prepared = data["prepared"]
    assert isinstance(prepared, dict)
    result = rollover.authorize_archive(
        repo_root=tmp_path,
        family_id=str(prepared["family_id"]),
        operation_id=str(prepared["operation_id"]),
        state=_confirmed_state(data),
        source_status=source_status,
        pin_state=pin_state,
        evidence="native read_thread response",
    )
    assert result["ok"] is False
    assert any(expected in blocker for blocker in result["blockers"])
    assert codex_state.read_thread_record(Path(data["db"]), task_id=str(data["source_id"])).archived is False


def test_non_pass_canary_status_preserves_predecessor(tmp_path: Path) -> None:
    data = _transition(tmp_path)
    _title_reconciled(tmp_path, data)
    prepared = data["prepared"]
    assert isinstance(prepared, dict)
    state = _confirmed_state(data)
    state["replacement"]["canary_proof"]["status"] = "FAIL"
    result = rollover.authorize_archive(
        repo_root=tmp_path,
        family_id=str(prepared["family_id"]),
        operation_id=str(prepared["operation_id"]),
        state=state,
        source_status="idle",
        pin_state="unpinned",
        evidence="native read_thread response",
    )
    assert result["ok"] is False
    assert "script canary proof is not PASS" in result["blockers"]
    assert codex_state.read_thread_record(Path(data["db"]), task_id=str(data["source_id"])).archived is False


def test_exact_confirmed_predecessor_archive_failure_retry_preserves_unrelated(tmp_path: Path) -> None:
    data = _transition(tmp_path)
    _title_reconciled(tmp_path, data)
    prepared = data["prepared"]
    assert isinstance(prepared, dict)
    kwargs = {
        "repo_root": tmp_path,
        "family_id": str(prepared["family_id"]),
        "operation_id": str(prepared["operation_id"]),
    }
    action = rollover.request_action(
        **kwargs,
        action="archive",
        db_path=Path(data["db"]),
        state=_confirmed_state(data),
        source_status="idle",
        pin_state="unpinned",
        evidence="fresh native read_thread retry: idle, pinned=false",
    )
    assert action["needs_native_action"] is True
    assert action["arguments"] == {"threadId": data["source_id"], "archived": True}
    rollover.record_native_result(
        **kwargs,
        action="archive",
        succeeded=False,
        evidence="set_thread_archived response",
        error="temporary native failure",
    )
    retry = rollover.request_action(
        **kwargs,
        action="archive",
        db_path=Path(data["db"]),
        state=_confirmed_state(data),
        source_status="idle",
        pin_state="unpinned",
        evidence="native read_thread: idle, pinned=false",
    )
    assert retry["needs_native_action"] is True
    rollover.record_native_result(
        **kwargs,
        action="archive",
        succeeded=True,
        evidence="set_thread_archived success",
    )
    with sqlite3.connect(data["db"]) as connection:
        connection.execute(
            "UPDATE threads SET archived = 1, archived_at = ? WHERE id = ?",
            ("2026-07-15T10:05:00Z", data["source_id"]),
        )
        connection.commit()
    reconciled = rollover.reconcile_action(**kwargs, action="archive", db_path=Path(data["db"]))
    assert reconciled["ok"] is True
    assert reconciled["task_id"] == data["source_id"]
    assert codex_state.read_thread_record(Path(data["db"]), task_id=str(data["replacement_id"])).archived is False
    assert codex_state.read_thread_record(Path(data["db"]), task_id=str(data["unrelated_id"])).archived is False
    storage = TaskFamilyStorage(tmp_path, str(prepared["family_id"]), str(prepared["operation_id"]))
    assert len([item for item in storage.load_receipt().actual if item.action == "archive_reconciled"]) == 1


def test_persisted_transition_plan_drift_fails_closed(tmp_path: Path) -> None:
    data = _transition(tmp_path)
    prepared = data["prepared"]
    assert isinstance(prepared, dict)
    storage = TaskFamilyStorage(tmp_path, str(prepared["family_id"]), str(prepared["operation_id"]))
    plan = storage.read_json(storage.rollover_plan_path)
    plan["source_thread_id"] = str(uuid4())
    storage.rollover_plan_path.write_text(json.dumps(plan), encoding="utf-8")
    with pytest.raises(ValueError, match="digest mismatch"):
        rollover.request_action(
            repo_root=tmp_path,
            family_id=str(prepared["family_id"]),
            operation_id=str(prepared["operation_id"]),
            action="title",
            db_path=Path(data["db"]),
        )
