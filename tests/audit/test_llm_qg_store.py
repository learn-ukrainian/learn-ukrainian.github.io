from __future__ import annotations

import concurrent.futures
import hashlib
import json
import sqlite3
import subprocess
from pathlib import Path

import pytest

from scripts.audit.llm_qg_store import (
    current_evidence_for_module,
    current_payload_for_module,
    evidence_record_is_current_for_module,
    evidence_record_passes_for_module,
    latest_llm_qg,
    record_llm_qg,
)


def _module(tmp_path: Path) -> Path:
    module_dir = tmp_path / "b1" / "aspect-in-imperatives"
    module_dir.mkdir(parents=True)
    (module_dir / "module.md").write_text("## Тест\n\nЧекайте на номер.\n", encoding="utf-8")
    (module_dir / "activities.yaml").write_text("[]\n", encoding="utf-8")
    (module_dir / "vocabulary.yaml").write_text("[]\n", encoding="utf-8")
    return module_dir


def _payload(score: float = 7.5) -> dict:
    return {
        "aggregate": {
            "verdict": "REVISE",
            "terminal_verdict": "PASS",
            "min_score": score,
            "min_dim": "naturalness",
            "failing_dims": ["naturalness"],
            "warning_dims": ["naturalness"],
        },
        "dimensions": {
            "naturalness": {
                "score": score,
                "verdict": "REVISE",
                "evidence": '"Чекайте номер"',
                "findings": [
                    {
                        "category": "government",
                        "severity": "warning",
                        "quote": "Чекайте номер",
                        "replacement": "Чекайте на номер",
                    }
                ],
            }
        },
    }


def test_record_and_read_current_llm_qg(tmp_path: Path) -> None:
    module_dir = _module(tmp_path)
    db_path = tmp_path / "qg.db"

    stored = record_llm_qg(
        level="B1",
        slug="aspect-in-imperatives",
        module_dir=module_dir,
        payload=_payload(),
        gate_version="test.v1",
        reviewer_model="review-model",
        reviewer_family="reviewer-tools",
        source="test",
        path=db_path,
    )
    current = current_payload_for_module("b1", "aspect-in-imperatives", module_dir, path=db_path)

    assert stored.level == "b1"
    assert current is not None
    assert current["aggregate"]["min_dim"] == "naturalness"
    assert current["_store"]["gate_version"] == "test.v1"

    with sqlite3.connect(db_path) as conn:
        count = conn.execute("SELECT count(*) FROM llm_qg_findings").fetchone()[0]
    assert count == 1


def test_findings_index_uses_issue_id_when_category_is_absent(tmp_path: Path) -> None:
    module_dir = _module(tmp_path)
    db_path = tmp_path / "qg.db"
    payload = _payload()
    payload["dimensions"]["naturalness"]["findings"] = [
        {
            "issue_id": "UNNATURAL_ANTHROPOMORPHISM",
            "severity": "high",
            "quote": "Застереження каже",
        }
    ]

    record_llm_qg(
        level="b1",
        slug="aspect-in-imperatives",
        module_dir=module_dir,
        payload=payload,
        gate_version="test.v1",
        path=db_path,
    )

    with sqlite3.connect(db_path) as conn:
        category = conn.execute("SELECT category FROM llm_qg_findings").fetchone()[0]
    assert category == "UNNATURAL_ANTHROPOMORPHISM"


def test_current_llm_qg_is_hash_bound_to_module_content(tmp_path: Path) -> None:
    module_dir = _module(tmp_path)
    db_path = tmp_path / "qg.db"

    record_llm_qg(
        level="b1",
        slug="aspect-in-imperatives",
        module_dir=module_dir,
        payload=_payload(),
        gate_version="test.v1",
        path=db_path,
    )
    (module_dir / "module.md").write_text("## Тест\n\nЧекайте на свій номер.\n", encoding="utf-8")

    assert current_payload_for_module("b1", "aspect-in-imperatives", module_dir, path=db_path) is None
    assert latest_llm_qg("b1", "aspect-in-imperatives", path=db_path) is not None


def test_current_evidence_export_is_compact_and_hash_bound(tmp_path: Path) -> None:
    module_dir = _module(tmp_path)
    db_path = tmp_path / "qg.db"
    stored = record_llm_qg(
        level="b1",
        slug="aspect-in-imperatives",
        module_dir=module_dir,
        payload=_payload(score=9.5),
        gate_version="v7.llm_qg.1",
        prompt_hash="prompt-sha",
        reviewer_model="review-model",
        reviewer_family="reviewer-tools",
        source="test",
        path=db_path,
    )

    evidence = current_evidence_for_module(
        "b1",
        "aspect-in-imperatives",
        module_dir,
        profile="b1_plus",
        path=db_path,
    )

    assert evidence is not None
    assert evidence["schema_version"] == "llm_qg_evidence.v1"
    assert evidence["provenance"]["run_id"] == stored.run_id
    assert evidence["content_sha"] == stored.content_sha
    assert evidence["profile"] == "b1_plus"
    assert evidence["reviewer"] == {"family": "reviewer-tools", "model": "review-model"}
    assert evidence["dimensions"] == {
        "naturalness": {"score": 9.5, "verdict": "REVISE"}
    }
    assert evidence["findings_summary"] == {
        "total": 1,
        "by_category": {"government": 1},
        "by_severity": {"warning": 1},
    }
    assert "payload_json" not in evidence
    assert "findings" not in evidence
    assert evidence_record_is_current_for_module(evidence, module_dir)
    assert evidence_record_passes_for_module(evidence, module_dir)


def test_evidence_record_detects_stale_module_content(tmp_path: Path) -> None:
    module_dir = _module(tmp_path)
    db_path = tmp_path / "qg.db"
    record_llm_qg(
        level="b1",
        slug="aspect-in-imperatives",
        module_dir=module_dir,
        payload=_payload(),
        gate_version="test.v1",
        path=db_path,
    )
    evidence = current_evidence_for_module(
        "b1",
        "aspect-in-imperatives",
        module_dir,
        path=db_path,
    )
    assert evidence is not None

    (module_dir / "module.md").write_text("## Тест\n\nНовий текст.\n", encoding="utf-8")

    assert not evidence_record_is_current_for_module(evidence, module_dir)


_LEGACY_SCHEMA = """
CREATE TABLE llm_qg_runs (
    run_id TEXT PRIMARY KEY, created_at TEXT NOT NULL, level TEXT NOT NULL,
    slug TEXT NOT NULL, content_sha TEXT NOT NULL, gate_version TEXT NOT NULL,
    prompt_hash TEXT, checker_version TEXT, level_policy_family TEXT,
    reviewer_model TEXT, reviewer_family TEXT, source TEXT NOT NULL,
    verdict TEXT, terminal_verdict TEXT, min_score REAL, min_dim TEXT,
    payload_json TEXT NOT NULL
);
CREATE TABLE llm_qg_findings (
    id INTEGER PRIMARY KEY AUTOINCREMENT, run_id TEXT NOT NULL, category TEXT,
    severity TEXT, file TEXT, quote TEXT, replacement TEXT, payload_json TEXT NOT NULL
);
"""


def test_legacy_db_without_tool_columns_migrates_on_read(tmp_path: Path) -> None:
    module_dir = _module(tmp_path)
    db_path = tmp_path / "legacy.db"

    # Build a store with the pre-#2156 schema (no route_name / tool_call_count /
    # tools_used_json columns) and a legacy row inserted directly.
    with sqlite3.connect(db_path) as conn:
        conn.executescript(_LEGACY_SCHEMA)
        conn.execute(
            """INSERT INTO llm_qg_runs
               (run_id, created_at, level, slug, content_sha, gate_version, source, payload_json)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            ("legacy-1", "2020-01-01T00:00:00Z", "b1", "aspect-in-imperatives", "oldsha", "gate.v0", "legacy", "{}"),
        )

    # READ through the new code path: must not raise, columns backfilled, and the
    # new tool fields default cleanly for a legacy row.
    record = latest_llm_qg("b1", "aspect-in-imperatives", path=db_path)
    assert record is not None
    assert record.tool_call_count == 0
    assert record.tools_used == ()
    assert record.tool_events is None
    assert record.route_name is None
    assert record.raw_response is None
    assert record.dispatch_metadata is None
    assert record.retry_history is None
    assert record.gate_outcomes is None

    cols = {row[1] for row in sqlite3.connect(db_path).execute("PRAGMA table_info(llm_qg_runs)")}
    assert {
        "route_name",
        "tool_call_count",
        "tools_used_json",
        "tool_events_json",
        "raw_response",
        "raw_response_sha256",
        "dispatch_json",
        "retry_history_json",
        "gate_outcomes_json",
        "attempt_id",
    } <= cols

    # WRITE through the new code path on the migrated DB: also must not raise.
    event = {
        "tool": "sources_query_wikipedia",
        "input": {"query": "Веснянки", "mode": "section"},
        "status": "completed",
        "tool_call_id": "call_1",
        "output": "Веснянки — це весняні обрядові пісні.",
    }
    stored = record_llm_qg(
        level="b1",
        slug="aspect-in-imperatives",
        module_dir=module_dir,
        payload=_payload(),
        gate_version="qg_workflow.v2",
        route_name="opencode_frontier",
        tool_call_count=5,
        tools_used=["sources_query_wikipedia"],
        tool_events=[event],
        path=db_path,
    )
    assert stored.tool_call_count == 5
    assert stored.tools_used == ("sources_query_wikipedia",)
    assert stored.tool_events == (event,)
    reread = latest_llm_qg("b1", "aspect-in-imperatives", content_sha=stored.content_sha, path=db_path)
    assert reread is not None
    assert reread.tool_call_count == 5
    assert reread.tools_used == ("sources_query_wikipedia",)
    assert reread.tool_events == (event,)


def test_tool_telemetry_round_trips_through_store(tmp_path: Path) -> None:
    module_dir = _module(tmp_path)
    db_path = tmp_path / "qg.db"
    event = {
        "tool": "sources_search_heritage",
        "input": {"query": "Веснянки"},
        "status": "completed",
        "tool_call_id": "call_1",
        "output": {"rows": ["heritage result"]},
        "ignored_extra": "not persisted",
    }
    record_llm_qg(
        level="b1",
        slug="aspect-in-imperatives",
        module_dir=module_dir,
        payload=_payload(),
        gate_version="qg_workflow.v2",
        route_name="opencode_frontier",
        tool_call_count=7,
        tools_used=("sources_search_heritage", "sources_query_wikipedia"),
        tool_events=(event,),
        raw_response='{"findings": []}',
        raw_response_sha256=hashlib.sha256(b'{"findings": []}').hexdigest(),
        dispatch_metadata={
            "route_name": "opencode_frontier",
            "tool_call_count": 7,
            "tools_used": ["sources_search_heritage", "sources_query_wikipedia"],
            "tool_events": [event],
        },
        retry_history=[{"attempt": 1, "raw_response": '{"findings": []}', "dispatch": {"route_name": "opencode_frontier"}}],
        gate_outcomes={"status": "ran"},
        attempt_id=1,
        path=db_path,
    )
    record = latest_llm_qg("b1", "aspect-in-imperatives", path=db_path)
    assert record is not None
    assert record.tool_call_count == 7
    assert record.tools_used == ("sources_search_heritage", "sources_query_wikipedia")
    assert record.route_name == "opencode_frontier"
    assert record.tool_events == (
        {
            "tool": "sources_search_heritage",
            "input": {"query": "Веснянки"},
            "status": "completed",
            "tool_call_id": "call_1",
            "output": {"rows": ["heritage result"]},
        },
    )
    assert record.raw_response == '{"findings": []}'
    assert record.raw_response_sha256 == hashlib.sha256(b'{"findings": []}').hexdigest()
    assert record.dispatch_metadata is not None
    assert record.retry_history == (
        {"attempt": 1, "raw_response": '{"findings": []}', "dispatch": {"route_name": "opencode_frontier"}},
    )
    assert record.gate_outcomes == {"status": "ran"}
    assert record.attempt_id == 1


def test_composite_cache_key_includes_route_name(tmp_path: Path) -> None:
    module_dir = _module(tmp_path)
    db_path = tmp_path / "qg.db"
    stored = record_llm_qg(
        level="b1",
        slug="aspect-in-imperatives",
        module_dir=module_dir,
        payload=_payload(),
        gate_version="qg_workflow.v2",
        reviewer_model="shared-model",
        route_name="opencode_frontier",
        path=db_path,
    )

    # Same model, DIFFERENT route -> cache miss (transport change invalidates).
    assert (
        latest_llm_qg(
            "b1",
            "aspect-in-imperatives",
            content_sha=stored.content_sha,
            reviewer_model="shared-model",
            route_name="agy_frontier",
            path=db_path,
        )
        is None
    )
    # Matching route -> hit.
    assert (
        latest_llm_qg(
            "b1",
            "aspect-in-imperatives",
            content_sha=stored.content_sha,
            reviewer_model="shared-model",
            route_name="opencode_frontier",
            path=db_path,
        )
        is not None
    )


def test_evidence_record_rejects_unknown_schema_gate_and_terminal_verdict(tmp_path: Path) -> None:
    module_dir = _module(tmp_path)
    db_path = tmp_path / "qg.db"
    record_llm_qg(
        level="b1",
        slug="aspect-in-imperatives",
        module_dir=module_dir,
        payload=_payload(score=9.5),
        gate_version="v7.llm_qg.1",
        path=db_path,
    )
    evidence = current_evidence_for_module(
        "b1",
        "aspect-in-imperatives",
        module_dir,
        path=db_path,
    )
    assert evidence is not None
    assert evidence_record_passes_for_module(evidence, module_dir)

    stale_schema = {**evidence, "schema_version": "llm_qg_evidence.v0"}
    assert not evidence_record_passes_for_module(stale_schema, module_dir)

    unsupported_gate = {**evidence, "gate_version": "v7.llm_qg.0"}
    assert not evidence_record_passes_for_module(unsupported_gate, module_dir)

    failing_terminal = {**evidence, "terminal_verdict": "FAIL"}
    assert not evidence_record_passes_for_module(failing_terminal, module_dir)


def _concurrent_worker(args: tuple[Path, Path, int]) -> None:
    module_dir, db_path, i = args
    record_llm_qg(
        level="b1",
        slug="aspect-in-imperatives",
        module_dir=module_dir,
        payload=_payload(),
        gate_version="test.v1",
        run_id=f"run-{i}",
        path=db_path,
    )


def test_concurrent_writers_shared_store(tmp_path: Path) -> None:
    import concurrent.futures
    module_dir = _module(tmp_path)
    db_path = tmp_path / "shared_qg.db"
    num_procs = 16

    tasks = [(module_dir, db_path, i) for i in range(num_procs)]

    with concurrent.futures.ProcessPoolExecutor(max_workers=num_procs) as executor:
        futures = [executor.submit(_concurrent_worker, task) for task in tasks]
        for future in concurrent.futures.as_completed(futures):
            future.result()

    with sqlite3.connect(db_path) as conn:
        assert conn.execute("SELECT count(*) FROM llm_qg_runs").fetchone()[0] == num_procs

def test_db_uses_wal_mode_and_busy_timeout(tmp_path: Path) -> None:
    from scripts.audit.llm_qg_store import init_db

    db_path = tmp_path / "wal_test.db"
    init_db(db_path)

    with sqlite3.connect(db_path) as conn:
        journal_mode = conn.execute("PRAGMA journal_mode").fetchone()[0]
        assert str(journal_mode).lower() == "wal"




def test_repository_root_failure_degrades_gracefully(monkeypatch) -> None:
    from scripts.audit import llm_qg_store

    monkeypatch.delenv(llm_qg_store.DB_ENV_VAR, raising=False)

    def mock_repo_root(*args: object, **kwargs: object) -> Path:
        raise RuntimeError("git execution failed: mock failure")

    monkeypatch.setattr(llm_qg_store, "_repository_root", mock_repo_root)

    # Should degrade to returning None instead of propagating RuntimeError
    assert llm_qg_store.latest_llm_qg("b1", "aspect-in-imperatives", path=None) is None


def _git_cmd(cwd: Path, *args: str) -> None:
    subprocess.run(
        ["git", "-C", str(cwd), *args],
        check=True,
        capture_output=True,
        text=True,
        timeout=30,
    )


def test_circuit_state_path_shared_in_linked_worktree(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from scripts.audit import llm_qg_store

    primary = tmp_path / "primary"
    primary.mkdir()
    _git_cmd(primary, "init")
    _git_cmd(primary, "config", "user.email", "test@example.invalid")
    _git_cmd(primary, "config", "user.name", "QG test")
    (primary / "README.md").write_text("fixture\n", encoding="utf-8")
    _git_cmd(primary, "add", "README.md")
    _git_cmd(primary, "commit", "-m", "fixture")
    linked = tmp_path / "linked"
    _git_cmd(primary, "worktree", "add", "--detach", str(linked), "HEAD")

    monkeypatch.delenv(llm_qg_store.CIRCUIT_ENV_VAR, raising=False)
    monkeypatch.setattr(llm_qg_store, "LIVE_REPO_ROOT", primary)
    primary_circuit = llm_qg_store.circuit_state_path()
    assert primary_circuit == primary / "data" / "telemetry" / "llm_qg_live_circuit.json"

    # From linked worktree, circuit_state_path() must resolve to primary's shared path
    monkeypatch.setattr(llm_qg_store, "LIVE_REPO_ROOT", linked)
    linked_circuit = llm_qg_store.circuit_state_path()
    assert linked_circuit == primary_circuit

    # Trip circuit in linked worktree
    for _ in range(llm_qg_store.CIRCUIT_WINDOW_SIZE):
        llm_qg_store.record_live_tier2_outcome(
            level="b1",
            slug="target",
            gate_version="test.v1",
            reviewer_model="model",
            reviewer_family="family",
            route_name="route",
            status="provider_error",
            reason="simulated failure",
        )

    # Primary checkout and linked worktree both see open circuit
    monkeypatch.setattr(llm_qg_store, "LIVE_REPO_ROOT", primary)
    assert llm_qg_store.live_tier2_circuit_status()["open"] is True

    # Explicit env var override works
    custom_circuit = tmp_path / "custom_circuit.json"
    monkeypatch.setenv(llm_qg_store.CIRCUIT_ENV_VAR, str(custom_circuit))
    assert llm_qg_store.circuit_state_path() == custom_circuit


def test_discover_worktree_dbs(tmp_path: Path) -> None:
    from scripts.audit import llm_qg_store

    primary = tmp_path / "primary"
    primary.mkdir()
    _git_cmd(primary, "init")
    _git_cmd(primary, "config", "user.email", "test@example.invalid")
    _git_cmd(primary, "config", "user.name", "QG test")
    (primary / "README.md").write_text("fixture\n", encoding="utf-8")
    _git_cmd(primary, "add", "README.md")
    _git_cmd(primary, "commit", "-m", "fixture")

    wt1 = tmp_path / "wt1"
    wt2 = tmp_path / "wt2"
    _git_cmd(primary, "worktree", "add", "--detach", str(wt1), "HEAD")
    _git_cmd(primary, "worktree", "add", "--detach", str(wt2), "HEAD")

    # Primary db
    primary_db = primary / "data" / "telemetry" / "llm_qg.db"
    llm_qg_store.init_db(primary_db)

    # wt1 db
    wt1_db = wt1 / "data" / "telemetry" / "llm_qg.db"
    llm_qg_store.init_db(wt1_db)

    # wt2 db
    wt2_db = wt2 / "data" / "telemetry" / "llm_qg.db"
    llm_qg_store.init_db(wt2_db)

    # Detached / extra worktree in .worktrees/
    extra_wt = primary / ".worktrees" / "sub" / "wt3"
    extra_db = extra_wt / "data" / "telemetry" / "llm_qg.db"
    llm_qg_store.init_db(extra_db)

    discovered = llm_qg_store.discover_worktree_dbs(repo_root=primary)
    discovered_resolved = {p.resolve() for p in discovered}
    assert primary_db.resolve() not in discovered_resolved
    assert wt1_db.resolve() in discovered_resolved
    assert wt2_db.resolve() in discovered_resolved
    assert extra_db.resolve() in discovered_resolved


def test_migrate_worktree_dbs_handles_no_worktrees(tmp_path: Path) -> None:
    from scripts.audit import llm_qg_store

    primary_db = tmp_path / "primary.db"
    stats = llm_qg_store.migrate_worktree_dbs(primary_path=primary_db, worktree_dbs=[])
    assert stats == {
        "discovered_dbs": 0,
        "scanned_rows": 0,
        "migrated_rows": 0,
        "skipped_rows": 0,
        "skipped_sources": [],
    }


def test_migrate_worktree_dbs_conflicting_rows_latest_wins(tmp_path: Path) -> None:
    from scripts.audit import llm_qg_store

    primary_db = tmp_path / "primary.db"
    wt1_db = tmp_path / "wt1.db"
    wt2_db = tmp_path / "wt2.db"
    module_dir = _module(tmp_path)

    # Key 1 (b1, target1, sha_current):
    # wt1: 2026-07-01 (score 7.0)
    # wt2: 2026-07-02 (score 8.5) -> should win over primary and wt1
    # primary: 2026-06-30 (score 6.0)
    llm_qg_store.record_llm_qg(
        level="b1",
        slug="target1",
        module_dir=module_dir,
        payload=_payload(score=6.0),
        gate_version="test.v1",
        run_id="run-p1",
        path=primary_db,
    )
    with sqlite3.connect(primary_db) as conn:
        conn.execute("UPDATE llm_qg_runs SET created_at = '2026-06-30T10:00:00Z' WHERE run_id = 'run-p1'")

    llm_qg_store.record_llm_qg(
        level="b1",
        slug="target1",
        module_dir=module_dir,
        payload=_payload(score=7.0),
        gate_version="test.v1",
        run_id="run-wt1-1",
        path=wt1_db,
    )
    with sqlite3.connect(wt1_db) as conn:
        conn.execute("UPDATE llm_qg_runs SET created_at = '2026-07-01T10:00:00Z' WHERE run_id = 'run-wt1-1'")

    llm_qg_store.record_llm_qg(
        level="b1",
        slug="target1",
        module_dir=module_dir,
        payload=_payload(score=8.5),
        gate_version="test.v1",
        run_id="run-wt2-1",
        path=wt2_db,
    )
    with sqlite3.connect(wt2_db) as conn:
        conn.execute("UPDATE llm_qg_runs SET created_at = '2026-07-02T10:00:00Z' WHERE run_id = 'run-wt2-1'")

    # Key 2 (b1, target2, sha_current):
    # wt1: 2026-07-01 (score 8.0)
    # primary: 2026-07-03 (score 9.0) -> primary is already newer, wt1 skipped
    llm_qg_store.record_llm_qg(
        level="b1",
        slug="target2",
        module_dir=module_dir,
        payload=_payload(score=9.0),
        gate_version="test.v1",
        run_id="run-p2",
        path=primary_db,
    )
    with sqlite3.connect(primary_db) as conn:
        conn.execute("UPDATE llm_qg_runs SET created_at = '2026-07-03T10:00:00Z' WHERE run_id = 'run-p2'")

    llm_qg_store.record_llm_qg(
        level="b1",
        slug="target2",
        module_dir=module_dir,
        payload=_payload(score=8.0),
        gate_version="test.v1",
        run_id="run-wt1-2",
        path=wt1_db,
    )
    with sqlite3.connect(wt1_db) as conn:
        conn.execute("UPDATE llm_qg_runs SET created_at = '2026-07-01T10:00:00Z' WHERE run_id = 'run-wt1-2'")

    # Key 3 (b1, target3, sha_current):
    # wt2: 2026-07-02 (score 9.5)
    # primary: none -> wt2 inserted
    llm_qg_store.record_llm_qg(
        level="b1",
        slug="target3",
        module_dir=module_dir,
        payload=_payload(score=9.5),
        gate_version="test.v1",
        run_id="run-wt2-3",
        path=wt2_db,
    )
    with sqlite3.connect(wt2_db) as conn:
        conn.execute("UPDATE llm_qg_runs SET created_at = '2026-07-02T10:00:00Z' WHERE run_id = 'run-wt2-3'")

    stats = llm_qg_store.migrate_worktree_dbs(primary_path=primary_db, worktree_dbs=[wt1_db, wt2_db])
    assert stats["discovered_dbs"] == 2
    assert stats["scanned_rows"] == 4
    assert stats["migrated_rows"] == 4
    assert stats["skipped_rows"] == 0

    rec1 = llm_qg_store.latest_llm_qg("b1", "target1", path=primary_db)
    assert rec1 is not None
    assert rec1.run_id == "run-wt2-1"
    assert rec1.payload["aggregate"]["min_score"] == 8.5

    rec2 = llm_qg_store.latest_llm_qg("b1", "target2", path=primary_db)
    assert rec2 is not None
    assert rec2.run_id == "run-p2"
    assert rec2.payload["aggregate"]["min_score"] == 9.0

    rec3 = llm_qg_store.latest_llm_qg("b1", "target3", path=primary_db)
    assert rec3 is not None
    assert rec3.run_id == "run-wt2-3"
    assert rec3.payload["aggregate"]["min_score"] == 9.5


def test_migrate_worktree_dbs_is_idempotent(tmp_path: Path) -> None:
    from scripts.audit import llm_qg_store

    primary_db = tmp_path / "primary.db"
    wt_db = tmp_path / "wt.db"
    module_dir = _module(tmp_path)

    llm_qg_store.record_llm_qg(
        level="b1",
        slug="module-a",
        module_dir=module_dir,
        payload=_payload(score=9.0),
        gate_version="test.v1",
        run_id="run-a",
        path=wt_db,
    )
    llm_qg_store.record_llm_qg(
        level="b1",
        slug="module-b",
        module_dir=module_dir,
        payload=_payload(score=8.0),
        gate_version="test.v1",
        run_id="run-b",
        path=wt_db,
    )

    # First run: migrates both rows
    stats1 = llm_qg_store.migrate_worktree_dbs(primary_path=primary_db, worktree_dbs=[wt_db])
    assert stats1["scanned_rows"] == 2
    assert stats1["migrated_rows"] == 2
    assert stats1["skipped_rows"] == 0

    with sqlite3.connect(primary_db) as conn:
        rows_run1 = conn.execute("SELECT * FROM llm_qg_runs ORDER BY run_id").fetchall()

    # Second run: changes nothing, 0 migrated rows
    stats2 = llm_qg_store.migrate_worktree_dbs(primary_path=primary_db, worktree_dbs=[wt_db])
    assert stats2["scanned_rows"] == 2
    assert stats2["migrated_rows"] == 0
    assert stats2["skipped_rows"] == 2

    with sqlite3.connect(primary_db) as conn:
        rows_run2 = conn.execute("SELECT * FROM llm_qg_runs ORDER BY run_id").fetchall()

    assert rows_run1 == rows_run2


def test_migrate_worktree_dbs_cli(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    from scripts.audit import llm_qg_store

    primary_db = tmp_path / "primary.db"
    wt_db = tmp_path / "wt.db"
    module_dir = _module(tmp_path)

    llm_qg_store.record_llm_qg(
        level="b1",
        slug="module-cli",
        module_dir=module_dir,
        payload=_payload(score=9.2),
        gate_version="test.v1",
        run_id="run-cli",
        path=wt_db,
    )

    rc = llm_qg_store.main([
        "--migrate-worktrees",
        "--db",
        str(primary_db),
        "--worktree-db",
        str(wt_db),
    ])
    assert rc == 0
    captured = capsys.readouterr().out
    assert "Worktree DB migration complete" in captured
    assert "migrated=1" in captured


def test_circuit_state_path_raises_on_repo_root_failure(monkeypatch: pytest.MonkeyPatch) -> None:
    from scripts.audit import llm_qg_store

    monkeypatch.delenv(llm_qg_store.CIRCUIT_ENV_VAR, raising=False)

    def mock_repo_root(*args: object, **kwargs: object) -> Path:
        raise RuntimeError("git execution failed: mock failure")

    monkeypatch.setattr(llm_qg_store, "_repository_root", mock_repo_root)

    with pytest.raises(RuntimeError, match="mock failure"):
        llm_qg_store.circuit_state_path()


def test_concurrent_writers_circuit_state(tmp_path: Path) -> None:
    from scripts.audit import llm_qg_store

    circuit_file = tmp_path / "concurrent_circuit.json"

    def write_outcome(worker_id: int) -> None:
        for i in range(5):
            llm_qg_store.record_live_tier2_outcome(
                level="b1",
                slug=f"worker-{worker_id}-item-{i}",
                gate_version="test.v1",
                reviewer_model="test-model",
                reviewer_family="test-family",
                route_name="route-test",
                status="provider_error" if (worker_id + i) % 2 == 0 else "completed",
                reason=f"worker {worker_id} pass {i}",
                path=circuit_file,
            )

    with concurrent.futures.ThreadPoolExecutor(max_workers=8) as executor:
        futures = [executor.submit(write_outcome, wid) for wid in range(8)]
        for f in concurrent.futures.as_completed(futures):
            f.result()

    status = llm_qg_store.live_tier2_circuit_status(path=circuit_file)
    assert status["attempted"] == min(8 * 5, llm_qg_store.CIRCUIT_WINDOW_SIZE)
    assert circuit_file.is_file()
    data = json.loads(circuit_file.read_text(encoding="utf-8"))
    assert data["schema_version"] == llm_qg_store.CIRCUIT_SCHEMA_VERSION
    assert len(data["live_outcomes"]) == min(40, llm_qg_store.CIRCUIT_WINDOW_SIZE)


def test_migrate_worktree_dbs_preserves_distinct_prompt_hashes_and_resumes(tmp_path: Path) -> None:
    from scripts.audit import llm_qg_store
    from scripts.build import v7_build

    primary_db = tmp_path / "primary.db"
    wt_db = tmp_path / "wt.db"
    module_dir = _module(tmp_path)

    # Older PASS run under prompt_hash "hash-pass"
    pass_payload = {
        "gate_version": v7_build.LLM_QG_GATE_VERSION,
        "aggregate": {"verdict": "PASS", "terminal_verdict": "PASS", "min_score": 9.0},
        "dimensions": {},
    }
    llm_qg_store.record_llm_qg(
        level="b1",
        slug="module-target",
        module_dir=module_dir,
        payload=pass_payload,
        gate_version=v7_build.LLM_QG_GATE_VERSION,
        prompt_hash="hash-pass",
        run_id="run-pass-1",
        path=wt_db,
    )
    with sqlite3.connect(wt_db) as conn:
        conn.execute("UPDATE llm_qg_runs SET created_at = '2026-07-01T10:00:00Z' WHERE run_id = 'run-pass-1'")

    # Newer REVISE run under prompt_hash "hash-revise"
    revise_payload = {
        "gate_version": v7_build.LLM_QG_GATE_VERSION,
        "aggregate": {"verdict": "REVISE", "terminal_verdict": "REVISE", "min_score": 5.0},
        "dimensions": {},
    }
    llm_qg_store.record_llm_qg(
        level="b1",
        slug="module-target",
        module_dir=module_dir,
        payload=revise_payload,
        gate_version=v7_build.LLM_QG_GATE_VERSION,
        prompt_hash="hash-revise",
        run_id="run-revise-2",
        path=wt_db,
    )
    with sqlite3.connect(wt_db) as conn:
        conn.execute("UPDATE llm_qg_runs SET created_at = '2026-07-02T10:00:00Z' WHERE run_id = 'run-revise-2'")

    # Migrate wt_db to primary_db
    stats = llm_qg_store.migrate_worktree_dbs(primary_path=primary_db, worktree_dbs=[wt_db])
    assert stats["scanned_rows"] == 2
    assert stats["migrated_rows"] == 2

    # Both rows must be present in primary store
    with sqlite3.connect(primary_db) as conn:
        runs = conn.execute("SELECT run_id, prompt_hash, verdict FROM llm_qg_runs ORDER BY created_at ASC").fetchall()
    assert runs == [("run-pass-1", "hash-pass", "PASS"), ("run-revise-2", "hash-revise", "REVISE")]

    # Lookup by prompt_hash="hash-pass" finds the older PASS run
    found_pass = llm_qg_store.current_payload_for_module(
        "b1",
        "module-target",
        module_dir,
        gate_version=v7_build.LLM_QG_GATE_VERSION,
        prompt_hash="hash-pass",
        path=primary_db,
    )
    assert found_pass is not None
    assert found_pass["_store"]["run_id"] == "run-pass-1"
    assert found_pass["aggregate"]["verdict"] == "PASS"

    # And v7_build resume authority accepts this matching PASS payload
    assert v7_build._llm_qg_payload_passes(found_pass) is True


def test_migrate_worktree_dbs_migrates_findings_table(tmp_path: Path) -> None:
    from scripts.audit import llm_qg_store

    primary_db = tmp_path / "primary.db"
    wt_db = tmp_path / "wt.db"
    module_dir = _module(tmp_path)

    payload_with_findings = {
        "gate_version": "test.v1",
        "aggregate": {"verdict": "PASS", "terminal_verdict": "PASS", "min_score": 8.5},
        "findings": [
            {
                "category": "tone_issue",
                "severity": "minor",
                "file": "module.md",
                "quote": "bad text",
                "replacement": "good text",
                "detail": "tone adjustment",
            },
            {
                "issue_id": "pedagogical_gap",
                "severity": "major",
                "file": "activities.yaml",
                "quote": "missing explanation",
                "replacement": "clarify grammar",
                "detail": "activity fix",
            },
        ],
    }
    llm_qg_store.record_llm_qg(
        level="b1",
        slug="module-findings",
        module_dir=module_dir,
        payload=payload_with_findings,
        gate_version="test.v1",
        run_id="run-with-findings",
        path=wt_db,
    )

    stats = llm_qg_store.migrate_worktree_dbs(primary_path=primary_db, worktree_dbs=[wt_db])
    assert stats["migrated_rows"] == 1

    with sqlite3.connect(primary_db) as conn:
        conn.row_factory = sqlite3.Row
        findings = conn.execute(
            "SELECT * FROM llm_qg_findings WHERE run_id = 'run-with-findings' ORDER BY id ASC"
        ).fetchall()

    assert len(findings) == 2
    assert findings[0]["category"] == "tone_issue"
    assert findings[0]["severity"] == "minor"
    assert findings[0]["file"] == "module.md"
    assert findings[0]["quote"] == "bad text"
    assert findings[0]["replacement"] == "good text"
    assert json.loads(findings[0]["payload_json"])["detail"] == "tone adjustment"

    assert findings[1]["category"] == "pedagogical_gap"
    assert findings[1]["severity"] == "major"
    assert findings[1]["file"] == "activities.yaml"
    assert findings[1]["quote"] == "missing explanation"


def test_migrate_worktree_dbs_on_conflict_updates_existing_run_id(tmp_path: Path) -> None:
    from scripts.audit import llm_qg_store

    primary_db = tmp_path / "primary.db"
    wt_db = tmp_path / "wt.db"
    module_dir = _module(tmp_path)

    # In primary DB: run-dup with older created_at and score 5.0
    llm_qg_store.record_llm_qg(
        level="b1",
        slug="module-conflict",
        module_dir=module_dir,
        payload=_payload(score=5.0),
        gate_version="test.v1",
        run_id="run-dup",
        path=primary_db,
    )
    with sqlite3.connect(primary_db) as conn:
        conn.execute("UPDATE llm_qg_runs SET created_at = '2026-07-01T10:00:00Z' WHERE run_id = 'run-dup'")

    # In wt_db: same run_id "run-dup" with newer created_at and updated score 9.5
    llm_qg_store.record_llm_qg(
        level="b1",
        slug="module-conflict",
        module_dir=module_dir,
        payload=_payload(score=9.5),
        gate_version="test.v1",
        run_id="run-dup",
        path=wt_db,
    )
    with sqlite3.connect(wt_db) as conn:
        conn.execute("UPDATE llm_qg_runs SET created_at = '2026-07-02T10:00:00Z' WHERE run_id = 'run-dup'")

    stats = llm_qg_store.migrate_worktree_dbs(primary_path=primary_db, worktree_dbs=[wt_db])
    assert stats["scanned_rows"] == 1
    assert stats["migrated_rows"] == 1
    assert stats["skipped_rows"] == 0

    rec = llm_qg_store.latest_llm_qg("b1", "module-conflict", path=primary_db)
    assert rec is not None
    assert rec.run_id == "run-dup"
    assert rec.created_at == "2026-07-02T10:00:00Z"
    assert rec.payload["aggregate"]["min_score"] == 9.5


def test_migrate_worktree_dbs_reports_skipped_sources(tmp_path: Path) -> None:
    from scripts.audit import llm_qg_store

    primary_db = tmp_path / "primary.db"
    wt_valid_db = tmp_path / "valid.db"
    corrupted_db = tmp_path / "corrupted.db"
    corrupted_db.write_bytes(b"not a valid sqlite file")
    module_dir = _module(tmp_path)

    llm_qg_store.record_llm_qg(
        level="b1",
        slug="module-valid",
        module_dir=module_dir,
        payload=_payload(score=8.8),
        gate_version="test.v1",
        run_id="run-valid",
        path=wt_valid_db,
    )

    stats = llm_qg_store.migrate_worktree_dbs(
        primary_path=primary_db,
        worktree_dbs=[wt_valid_db, corrupted_db],
    )
    assert stats["discovered_dbs"] == 2
    assert stats["migrated_rows"] == 1
    assert str(corrupted_db.resolve()) in stats["skipped_sources"]


def test_migrate_worktree_dbs_does_not_alter_source_dbs(tmp_path: Path) -> None:
    from scripts.audit import llm_qg_store

    primary_db = tmp_path / "primary.db"
    legacy_src_db = tmp_path / "legacy_src.db"

    # Create bare legacy table without newer composite columns
    with sqlite3.connect(legacy_src_db) as conn:
        conn.execute(
            """
            CREATE TABLE llm_qg_runs (
                run_id TEXT PRIMARY KEY,
                created_at TEXT NOT NULL,
                level TEXT NOT NULL,
                slug TEXT NOT NULL,
                content_sha TEXT NOT NULL,
                gate_version TEXT NOT NULL,
                prompt_hash TEXT,
                source TEXT NOT NULL,
                verdict TEXT,
                terminal_verdict TEXT,
                min_score REAL,
                min_dim TEXT,
                payload_json TEXT NOT NULL
            )
            """
        )
        conn.execute(
            """
            INSERT INTO llm_qg_runs VALUES (
                'run-legacy-1', '2026-07-01T10:00:00Z', 'b1', 'legacy-slug',
                'sha123', 'test.v1', 'hash123', 'pipeline', 'PASS', 'PASS', 9.0, 'tone', '{}'
            )
            """
        )
        conn.commit()
        cols_before = [row[1] for row in conn.execute("PRAGMA table_info(llm_qg_runs)").fetchall()]

    stats = llm_qg_store.migrate_worktree_dbs(primary_path=primary_db, worktree_dbs=[legacy_src_db])
    assert stats["migrated_rows"] == 1

    # Verify source database schema was NOT altered
    with sqlite3.connect(legacy_src_db) as conn:
        cols_after = [row[1] for row in conn.execute("PRAGMA table_info(llm_qg_runs)").fetchall()]
    assert cols_before == cols_after

    # Verify primary database has the row with NULL for the composite columns
    with sqlite3.connect(primary_db) as conn:
        conn.row_factory = sqlite3.Row
        migrated = conn.execute("SELECT * FROM llm_qg_runs WHERE run_id = 'run-legacy-1'").fetchone()
    assert migrated is not None
    assert migrated["run_id"] == "run-legacy-1"
    assert migrated["route_name"] is None
    assert migrated["tools_used_json"] is None


def test_parse_iso_timestamp_normalization() -> None:
    from scripts.audit.llm_qg_store import _parse_iso_timestamp

    t1 = _parse_iso_timestamp("2026-08-15T12:00:00Z")
    t2 = _parse_iso_timestamp("2026-08-15T12:00:00+00:00")
    t3 = _parse_iso_timestamp("2026-08-15T12:00:00.000000Z")
    t4 = _parse_iso_timestamp("2026-08-15T12:00:00.123456Z")
    assert t1 == t2 == t3
    assert t4 > t1
    assert _parse_iso_timestamp(None) == 0.0
    assert _parse_iso_timestamp("invalid") == 0.0

