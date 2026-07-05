from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Any

from scripts.audit import llm_qg_store, qg_corpus_report, qg_schema, qg_workflow
from scripts.audit.content_surface_gates import policy_for_level
from scripts.audit.curriculum_qg_harness import CHECKER_VERSION


def _module(tmp_path: Path, *, level: str = "b1", slug: str = "sample", body: str | None = None) -> Path:
    module_dir = tmp_path / level / slug
    module_dir.mkdir(parents=True)
    (module_dir / "module.md").write_text(
        body or "# Модуль\n\nУчні читають український текст і виконують завдання.\n",
        encoding="utf-8",
    )
    (module_dir / "activities.yaml").write_text("[]\n", encoding="utf-8")
    (module_dir / "vocabulary.yaml").write_text("[]\n", encoding="utf-8")
    (module_dir / "resources.yaml").write_text("[]\n", encoding="utf-8")
    return module_dir


def _target(module_dir: Path, *, level: str = "b1", slug: str | None = None) -> qg_corpus_report.ReportTarget:
    return qg_corpus_report.ReportTarget(level=level, slug=slug or module_dir.name, module_dir=module_dir)


def _finding(
    *,
    issue_id: str = "TEST_CALQUE",
    issue_class: str = "calque",
    dimension: str = "contact_calque",
    severity: str = "warning",
    confidence: str = "llm_judgment",
    disposition: str = "defect",
    excerpt: str = "тестовий фрагмент",
    metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    return qg_schema.build_finding(
        issue_id=issue_id,
        issue_class=issue_class,
        dimension=dimension,
        severity=severity,
        file="module.md",
        line=1,
        span={"start": 0, "end": len(excerpt)},
        excerpt=excerpt,
        message="Test finding.",
        contact_source_lang="ru",
        confidence=confidence,
        disposition=disposition,
        detector={"adapter": "test", "rule_id": issue_id},
        attribution={"corpus": "test", "evidence": "unit test"},
        metadata=metadata,
    )


def _payload(*findings: dict[str, Any]) -> dict[str, Any]:
    return qg_workflow._payload_from_findings(list(findings))


def _record(
    db_path: Path,
    module_dir: Path,
    *,
    gate_version: str = "gate.v1",
    reviewer_model: str = "model-a",
    payload: dict[str, Any] | None = None,
) -> llm_qg_store.StoredQG:
    target = _target(module_dir)
    return llm_qg_store.record_llm_qg(
        level=target.level,
        slug=target.slug,
        module_dir=module_dir,
        payload=payload or _payload(),
        gate_version=gate_version,
        prompt_hash=qg_corpus_report._prompt_hash_for_target(target),
        checker_version=CHECKER_VERSION,
        level_policy_family=policy_for_level(target.level).family,
        reviewer_model=reviewer_model,
        reviewer_family="test-family",
        source="test",
        path=db_path,
    )


def _set_created_at(db_path: Path, run_id: str, created_at: str) -> None:
    with sqlite3.connect(db_path) as conn:
        conn.execute("UPDATE llm_qg_runs SET created_at = ? WHERE run_id = ?", (created_at, run_id))
        conn.commit()


def test_report_uses_latest_composite_row_and_cache_statuses(tmp_path: Path) -> None:
    db_path = tmp_path / "qg.db"
    hit = _module(tmp_path, slug="hit")
    stale = _module(tmp_path, slug="stale")
    miss = _module(tmp_path, slug="miss")

    old = _record(db_path, hit, payload=_payload(_finding(excerpt="старий дефект")))
    new = _record(db_path, hit, payload=_payload())
    stale_record = _record(db_path, stale, payload=_payload())
    _set_created_at(db_path, old.run_id, "2026-01-01T00:00:00Z")
    _set_created_at(db_path, new.run_id, "2026-01-02T00:00:00Z")
    _set_created_at(db_path, stale_record.run_id, "2026-01-03T00:00:00Z")
    (stale / "module.md").write_text("# Модуль\n\nОновлений текст.\n", encoding="utf-8")

    report = qg_corpus_report.build_report(
        db_path=db_path,
        targets=[_target(hit), _target(stale), _target(miss)],
        gate_version="gate.v1",
        checker_version=CHECKER_VERSION,
        reviewer_model_id="model-a",
    )

    assert report["selection"]["raw_db_rows"] == 3
    assert report["selection"]["latest_composite_records"] == 2
    assert report["cache"]["hit"] == 1
    assert report["cache"]["stale"] == 1
    assert report["cache"]["miss"] == 1
    assert report["defect_rates"]["overall"]["records_with_defects"] == 0


def test_contested_gold_delta_and_per_model_calque_f1(tmp_path: Path) -> None:
    db_path = tmp_path / "qg.db"
    module_dir = _module(tmp_path)
    calque_tp = _finding(
        issue_id="CALQUE_TP",
        metadata={"qg_eval": {"axis": "calque", "gold_label": True, "predicted": True, "matched": True}},
    )
    contested_fp = _finding(
        issue_id="CALQUE_FP_CONTESTED",
        metadata={
            "qg_eval": {"axis": "calque", "gold_label": False, "predicted": True, "matched": False, "contested": True},
            "ua_gec_gold": {"contested_flag": True, "gold_tag": "F/Calque"},
        },
    )
    grammar_tp = _finding(
        issue_id="GRAMMAR_TP",
        issue_class="grammar",
        dimension="contact_grammar",
        metadata={"qg_eval": {"axis": "grammar", "gold_label": True, "predicted": True, "matched": True}},
    )
    grammar_fn = _finding(
        issue_id="GRAMMAR_FN",
        issue_class="grammar",
        dimension="contact_grammar",
        disposition="suppressed_fp",
        metadata={"qg_eval": {"axis": "grammar", "gold_label": True, "predicted": False, "matched": False}},
    )
    _record(db_path, module_dir, payload=_payload(calque_tp, contested_fp, grammar_tp, grammar_fn))

    report = qg_corpus_report.build_report(db_path=db_path)

    calque = report["gold_metrics"]["calque"]
    assert calque["with_contested"]["precision"] == 0.5
    assert calque["without_contested"]["precision"] == 1.0
    assert calque["contested_delta"]["precision"] == -0.5
    assert report["gold_metrics"]["grammar"]["with_contested"]["recall"] == 0.5
    assert report["gold_metrics"]["per_model_calque_f1"]["model-a"]["without_contested"]["f1"] == 1.0


def test_workflow_records_count_failures_spend_and_warn_conversion(tmp_path: Path) -> None:
    module_dir = _module(tmp_path, slug="warn")
    deterministic_warn = _finding(confidence="deterministic", excerpt="спільний фрагмент")
    reviewer_confirm = _finding(confidence="llm_judgment", excerpt="спільний фрагмент")
    pass_record = _workflow_record(
        module_dir,
        slug="warn",
        findings=[deterministic_warn, reviewer_confirm],
        tier2_status="ran",
        terminal_verdict="PASS",
        workflow_verdict="WARN",
        completion_status="COMPLETE",
        estimated_cost=0.2,
        observed_cost=0.4,
    )
    provider_record = _workflow_record(
        _module(tmp_path, slug="provider"),
        slug="provider",
        tier2_status="provider_error",
        terminal_verdict="FAIL",
        workflow_verdict="PROVIDER_FAILURE",
        completion_status="INCOMPLETE",
        estimated_cost=0.1,
        observed_cost=0.1,
    )
    parse_record = _workflow_record(
        _module(tmp_path, slug="parse"),
        slug="parse",
        tier2_status="parse_failure",
        terminal_verdict="FAIL",
        workflow_verdict="PARSE_FAILURE",
        completion_status="INCOMPLETE",
    )

    report = qg_corpus_report.build_report(
        workflow_payloads=[[pass_record, provider_record, parse_record]],
        db_path=tmp_path / "empty.db",
    )

    assert report["warn_to_reviewer_confirmed"]["warn_findings"] == 1
    assert report["warn_to_reviewer_confirmed"]["reviewer_confirmed"] == 1
    assert report["completion"]["provider_error"] == 1
    assert report["completion"]["parse_failure"] == 1
    assert report["completion"]["incomplete"] == 2
    assert report["spend"]["accepted_evidence"] == 1
    assert report["spend"]["observed_cost_usd"] == 0.5
    assert report["spend"]["spend_per_accepted_evidence_usd"] == 0.5


def test_backfill_inserts_missing_or_stale_but_skips_current(tmp_path: Path) -> None:
    db_path = tmp_path / "qg.db"
    first = _module(tmp_path, slug="first")
    second = _module(tmp_path, slug="second")
    first_record = _workflow_record(first, slug="first", terminal_verdict="PASS")
    second_record = _workflow_record(second, slug="second", terminal_verdict="PASS")

    first_result = qg_corpus_report.backfill_from_workflow_records([first_record], db_path=db_path, dry_run=False)
    second_result = qg_corpus_report.backfill_from_workflow_records([first_record], db_path=db_path, dry_run=False)
    _record(db_path, second, gate_version="old.gate", payload=_payload())
    stale_result = qg_corpus_report.backfill_from_workflow_records([second_record], db_path=db_path, dry_run=False)

    with sqlite3.connect(db_path) as conn:
        rows = conn.execute("SELECT count(*) FROM llm_qg_runs").fetchone()[0]

    assert first_result["counts"] == {"inserted": 1}
    assert second_result["counts"] == {"current": 1}
    assert stale_result["counts"] == {"inserted": 1}
    assert rows == 3


def _workflow_record(
    module_dir: Path,
    *,
    slug: str,
    findings: list[dict[str, Any]] | None = None,
    tier2_status: str = "ran",
    terminal_verdict: str = "PASS",
    workflow_verdict: str = "PASS",
    completion_status: str = "COMPLETE",
    estimated_cost: float | None = None,
    observed_cost: float | None = None,
) -> dict[str, Any]:
    target = _target(module_dir, slug=slug)
    payload = _payload(*(findings or []))
    tier2: dict[str, Any] = {
        "tier": 2,
        "status": tier2_status,
        "reviewer_model_id": "model-a",
        "reviewer_family": "test-family",
    }
    if estimated_cost is not None:
        tier2["estimate"] = {"estimated_cost_usd": estimated_cost}
    if observed_cost is not None:
        tier2["dispatch"] = {"observed_cost_usd": observed_cost}
    return {
        "schema_version": qg_schema.SCHEMA_VERSION,
        "module_id": f"b1/{slug}",
        "content_sha": llm_qg_store.content_sha_for_module(module_dir),
        "level_policy": {"family": policy_for_level("b1").family},
        "aggregate": {
            **payload["aggregate"],
            "completion_status": completion_status,
            "workflow_verdict": workflow_verdict,
        },
        "dimensions": payload["dimensions"],
        "findings": payload["findings"],
        "terminal_verdict": terminal_verdict,
        "workflow_verdict": workflow_verdict,
        "completion_status": completion_status,
        "provenance": {"module_dir": str(module_dir), "run_id": f"workflow-{slug}"},
        "qg_workflow": {
            "gate_version": "gate.v1",
            "prompt_hash": qg_corpus_report._prompt_hash_for_target(target),
            "checker_version": CHECKER_VERSION,
            "reviewer_model_id": "model-a",
            "reviewer_family": "test-family",
            "tiers": [tier2],
        },
    }
