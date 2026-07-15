from __future__ import annotations

import hashlib
import sqlite3
from pathlib import Path

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
