from __future__ import annotations

import json
import sqlite3
from pathlib import Path

import pytest

from scripts.audit import llm_qg_store, llm_reviewer_dispatch, qg_shadow_run, qg_workflow


def _module(tmp_path: Path) -> Path:
    module_dir = tmp_path / "folk" / "vesnianky-shadow"
    module_dir.mkdir(parents=True)
    (module_dir / "module.md").write_text(
        "# Веснянки\n\nВеснянки — це весняні обрядові пісні.\n",
        encoding="utf-8",
    )
    for name in ("activities.yaml", "vocabulary.yaml", "resources.yaml"):
        (module_dir / name).write_text("[]\n", encoding="utf-8")
    return module_dir


def _dispatch(
    _target: qg_workflow.ReviewTarget,
    _prompt: str,
) -> llm_reviewer_dispatch.DispatchResult:
    response = {
        "findings": [],
        "fact_checks": [
            {
                "claim": "Веснянки — це весняні обрядові пісні.",
                "verdict": "CONFIRMED",
                "grounding": {
                    "tool": "sources_query_wikipedia",
                    "query": "Веснянки",
                    "evidence_excerpt": "Веснянки — це весняні обрядові пісні.",
                    "tool_call_id": "call_1",
                },
            }
        ],
        "evidence_gaps": [],
    }
    return llm_reviewer_dispatch.DispatchResult(
        response_text=json.dumps(response, ensure_ascii=False),
        reviewer_model_id="test-reviewer",
        reviewer_family="test-family",
        route_name="test-route",
        tool_call_count=1,
        tools_used=("sources_query_wikipedia",),
        tool_events=(
            {
                "tool": "sources_query_wikipedia",
                "input": {"query": "Веснянки", "mode": "section"},
                "status": "completed",
                "tool_call_id": "call_1",
                "output": "Веснянки — це весняні обрядові пісні.",
            },
        ),
    )


def _target(module_dir: Path) -> qg_workflow.ReviewTarget:
    return qg_workflow.ReviewTarget(level="folk", slug="vesnianky-shadow", module_dir=module_dir)


def _count(db_path: Path, table: str) -> int:
    with sqlite3.connect(db_path) as conn:
        return int(conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0])


def test_shadow_driver_captures_lifecycle_and_advisory_verdicts(tmp_path: Path) -> None:
    module_dir = _module(tmp_path)

    result = qg_shadow_run.run_shadow_module(
        _target(module_dir),
        audit_dir=tmp_path / "audit",
        shadow_db=tmp_path / "shadow.db",
        author_family="openai",
        reviewer=_dispatch,
        live_reviewer=False,
        reviewer_model_id="test-reviewer",
        reviewer_family="test-family",
        max_cost_usd=1.0,
        layerb_dry_run=True,
    )

    artifact = json.loads(result.artifact_path.read_text(encoding="utf-8"))
    report = json.loads(result.layerb_report_path.read_text(encoding="utf-8"))
    evidence = result.markdown_path.read_text(encoding="utf-8")
    assert artifact["schema_version"] == "qg_bakeoff_run.v2"
    assert artifact["arm"] == "production_shadow"
    assert artifact["writer_family"] == "openai"
    assert artifact["dispatch"]["tool_events"][0]["output"] == "Веснянки — це весняні обрядові пісні."
    assert artifact["payload"]["fact_checks"][0]["grounding"]["tool_call_id"] == "call_1"
    assert artifact["retry_history"][0]["raw_response"]
    assert report["configuration"]["tau"] == 0.75
    assert report["records"]
    assert "## Verdict rows" in evidence
    assert _count(tmp_path / "shadow.db", "llm_qg_shadow_runs") == 1
    assert _count(tmp_path / "shadow.db", "llm_qg_shadow_findings") == len(report["records"])


def test_shadow_driver_never_writes_canonical_llm_qg_runs(tmp_path: Path) -> None:
    module_dir = _module(tmp_path)
    canonical_db = tmp_path / "llm_qg.db"
    llm_qg_store.record_llm_qg(
        level="folk",
        slug="existing-canonical",
        module_dir=module_dir,
        payload={"findings": [], "fact_checks": [], "evidence_gaps": []},
        gate_version="test.v1",
        path=canonical_db,
    )
    before = _count(canonical_db, "llm_qg_runs")

    qg_shadow_run.run_shadow_module(
        _target(module_dir),
        audit_dir=tmp_path / "audit",
        shadow_db=tmp_path / "shadow.db",
        author_family="openai",
        reviewer=_dispatch,
        live_reviewer=False,
        reviewer_model_id="test-reviewer",
        reviewer_family="test-family",
        max_cost_usd=1.0,
        layerb_dry_run=True,
    )

    assert _count(canonical_db, "llm_qg_runs") == before
    assert _count(tmp_path / "shadow.db", "llm_qg_shadow_runs") == 1


def test_shadow_driver_rejects_unresolvable_writer_lineage(tmp_path: Path) -> None:
    module_dir = _module(tmp_path)

    with pytest.raises(ValueError, match="writer lineage"):
        qg_shadow_run.run_shadow_module(
            _target(module_dir),
            audit_dir=tmp_path / "audit",
            shadow_db=tmp_path / "shadow.db",
            reviewer=_dispatch,
            live_reviewer=False,
            reviewer_model_id="test-reviewer",
            reviewer_family="test-family",
            max_cost_usd=1.0,
            layerb_dry_run=True,
        )
