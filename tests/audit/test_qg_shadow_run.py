from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any

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


def test_shadow_driver_threads_writer_family_from_module_metadata(tmp_path: Path) -> None:
    module_dir = _module(tmp_path)
    (module_dir / "writer_meta.json").write_text('{"writer_family": "anthropic"}\n', encoding="utf-8")

    result = qg_shadow_run.run_shadow_module(
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

    artifact = json.loads(result.artifact_path.read_text(encoding="utf-8"))
    assert artifact["writer_family"] == "anthropic"
    assert artifact["writer_lineage"]["source"].endswith("writer_meta.json")
    assert artifact["writer_family"] != "fixture"


def test_shadow_driver_rejects_tau_other_than_attested_value(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(qg_shadow_run.layerb_shadow, "DEFAULT_TAU", 0.74)

    with pytest.raises(RuntimeError, match=r"pinned tau=0\.75"):
        qg_shadow_run.run_shadow_module(
            _target(_module(tmp_path)),
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


def test_artifact_survival_probe_passes_then_fails_on_loss_and_drift(tmp_path: Path) -> None:
    """#5195: evidence loss after a clean run must be loud, never a dangling DB row."""

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

    assert qg_shadow_run.verify_artifact_survival(result) == []

    result.artifact_path.write_text(result.artifact_path.read_text(encoding="utf-8") + "\n", encoding="utf-8")
    drifted = qg_shadow_run.verify_artifact_survival(result)
    assert len(drifted) == 1 and "drifted" in drifted[0]

    result.artifact_path.unlink()
    result.markdown_path.unlink()
    missing = qg_shadow_run.verify_artifact_survival(result)
    assert len(missing) == 2
    assert any("shadow artifact missing" in failure for failure in missing)
    assert any("evidence markdown missing" in failure for failure in missing)


def test_relative_operator_paths_anchor_to_primary_root() -> None:
    """#5171 class: relative --audit-dir/--shadow-db must never split evidence across cwds."""

    anchored = qg_shadow_run._anchor_to_repo_root(Path("audit/local-qg-shadow"))
    assert anchored.is_absolute()
    assert anchored.as_posix().endswith("audit/local-qg-shadow")
    # The anchor must be the PRIMARY checkout root (owns the real .git dir) —
    # not coupled to any branch-dependent file existing there.
    assert (anchored.parent.parent / ".git").is_dir()

    absolute = Path("/tmp/explicit-operator-target")
    assert qg_shadow_run._anchor_to_repo_root(absolute) == absolute


def test_main_exits_4_when_evidence_vanishes(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """The survival contract holds at the CLI boundary, not just in the helper."""

    module_dir = _module(tmp_path)

    real_run = qg_shadow_run.run_shadow_module

    def run_and_lose_evidence(*args: Any, **kwargs: Any) -> qg_shadow_run.ShadowRunResult:
        # Never let the CLI default reach the live reviewer in tests.
        kwargs["reviewer"] = _dispatch
        kwargs["live_reviewer"] = False
        kwargs["reviewer_model_id"] = "test-reviewer"
        kwargs["reviewer_family"] = "test-family"
        result = real_run(*args, **kwargs)
        result.artifact_path.unlink()
        return result

    monkeypatch.setattr(qg_shadow_run, "run_shadow_module", run_and_lose_evidence)

    rc = qg_shadow_run.main(
        [
            "--module-dir",
            str(module_dir),
            "--level",
            "folk",
            "--slug",
            "vesnianky-shadow",
            "--author-family",
            "openai",
            "--audit-dir",
            str(tmp_path / "audit"),
            "--shadow-db",
            str(tmp_path / "shadow.db"),
            "--max-cost-usd",
            "1.0",
            "--layerb-dry-run",
        ]
    )

    assert rc == 4


@pytest.mark.parametrize("family", ["fixture", "adversarial-fixture"])
def test_shadow_driver_rejects_fixture_family_on_real_module(tmp_path: Path, family: str) -> None:
    module_dir = _module(tmp_path)
    (module_dir / "writer_meta.json").write_text(f'{{"writer_family": "{family}"}}\n', encoding="utf-8")

    with pytest.raises(ValueError, match=f"writer lineage family '{family}' is classified as a fixture"):
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


def test_shadow_driver_no_writes_outside_audit_dir_and_db(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    import builtins
    import os
    import sqlite3

    module_dir = _module(tmp_path)
    audit_dir = tmp_path / "audit"
    shadow_db = tmp_path / "shadow.db"

    recorded_writes: set[Path] = set()
    recorded_mkdir: set[Path] = set()

    resolved_audit = audit_dir.resolve()
    resolved_shadow = shadow_db.resolve()
    resolved_module = module_dir.resolve()

    allowed_sqlite_paths = {
        resolved_shadow,
        resolved_shadow.with_name(resolved_shadow.name + "-wal"),
        resolved_shadow.with_name(resolved_shadow.name + "-shm"),
    }

    def is_in_audit_dir(path: Path) -> bool:
        try:
            resolved = path.resolve()
            return resolved == resolved_audit or resolved_audit in resolved.parents
        except Exception:
            return False

    def verify_path_for_write(path: Path) -> None:
        resolved = path.resolve()
        if is_in_audit_dir(resolved):
            recorded_writes.add(resolved)
            return
        if resolved in allowed_sqlite_paths:
            recorded_writes.add(resolved)
            return
        if resolved == resolved_module or resolved_module in resolved.parents:
            raise AssertionError(f"Write attempted inside module_dir: {resolved}")
        raise AssertionError(f"Write attempted outside allowed boundaries: {resolved}")

    original_path_open = Path.open

    def mocked_path_open(self: Path, *args: Any, **kwargs: Any) -> Any:
        mode = args[0] if args else kwargs.get("mode", "r")
        if any(c in mode for c in "wxa+"):
            verify_path_for_write(self)
        return original_path_open(self, *args, **kwargs)

    original_builtin_open = builtins.open

    def mocked_builtin_open(file: Any, *args: Any, **kwargs: Any) -> Any:
        mode = args[0] if args else kwargs.get("mode", "r")
        if any(c in mode for c in "wxa+"):
            if isinstance(file, (str, bytes)):
                verify_path_for_write(Path(os.fsdecode(file)))
            elif isinstance(file, Path):
                verify_path_for_write(file)
        return original_builtin_open(file, *args, **kwargs)

    original_path_replace = Path.replace

    def mocked_path_replace(self: Path, target: Any) -> Any:
        target_path = Path(target)
        verify_path_for_write(target_path)
        return original_path_replace(self, target)

    original_path_mkdir = Path.mkdir

    def mocked_path_mkdir(self: Path, *args: Any, **kwargs: Any) -> Any:
        resolved = self.resolve()
        if is_in_audit_dir(resolved) or resolved == resolved_shadow.parent or resolved in resolved_shadow.parents:
            recorded_mkdir.add(resolved)
        else:
            raise AssertionError(f"mkdir attempted outside allowed audit_dir or shadow_db parent: {resolved}")
        return original_path_mkdir(self, *args, **kwargs)

    original_sqlite_connect = sqlite3.connect

    def mocked_sqlite_connect(database: Any, *args: Any, **kwargs: Any) -> Any:
        if database != ":memory:":
            db_path = Path(database).resolve()
            if db_path != resolved_shadow:
                raise AssertionError(f"sqlite3 connected to unexpected database: {db_path}")
        return original_sqlite_connect(database, *args, **kwargs)

    monkeypatch.setattr(Path, "open", mocked_path_open)
    monkeypatch.setattr(builtins, "open", mocked_builtin_open)
    monkeypatch.setattr(Path, "replace", mocked_path_replace)
    monkeypatch.setattr(Path, "mkdir", mocked_path_mkdir)
    monkeypatch.setattr(sqlite3, "connect", mocked_sqlite_connect)

    qg_shadow_run.run_shadow_module(
        _target(module_dir),
        audit_dir=audit_dir,
        shadow_db=shadow_db,
        author_family="openai",
        reviewer=_dispatch,
        live_reviewer=False,
        reviewer_model_id="test-reviewer",
        reviewer_family="test-family",
        max_cost_usd=1.0,
        layerb_dry_run=True,
    )

    assert len(recorded_writes) > 0, "No write operations were intercepted!"
    for w_path in recorded_writes:
        assert is_in_audit_dir(w_path) or w_path in allowed_sqlite_paths


def test_shadow_driver_third_family_route_refusal_outputs_audit_record(tmp_path: Path) -> None:
    from datetime import UTC, datetime, timedelta

    from scripts.audit import layerb_qualify

    module_dir = _module(tmp_path)

    att_dir = tmp_path / "attested"
    att_dir.mkdir()

    labels = att_dir / "labels.json"
    labels.write_text(json.dumps({"cases": []}), encoding="utf-8")
    corpus_m = att_dir / "corpus.json"
    fixture_m = att_dir / "fixture.json"
    corpus_m.write_text(json.dumps({"corpus": "frozen"}), encoding="utf-8")
    fixture_m.write_text(json.dumps({"fixture": "frozen"}), encoding="utf-8")
    report_path = att_dir / "qualification-report.json"
    raw_path = att_dir / "raw-call-manifest.json"

    thresholds = {
        "adversarial_probes": {"status": "PASS"},
        "relation_agreement": {"status": "PASS"},
        "terminal_decision_agreement": {"status": "PASS"},
        "unsafe_accept_ucb": {"status": "PASS"},
        "accept_recall": {"status": "PASS"},
        "audit_rate": {"status": "PASS"},
        "cost_envelope": {"status": "PASS"},
        "layer_a_regression": {"status": "PASS"},
        "integrity": {"status": "PASS", "failures": {}},
        "semantic_stability": {
            "required": True,
            "seed": layerb_qualify.STABILITY_SEED,
            "case_ids": [],
            "status": "PASS",
            "disagreements": [],
        },
    }
    tier_evaluation = layerb_qualify._tier_evaluation(thresholds, "shadow")
    route_input = {
        "family": "claude",
        "resolved_model": "sonnet-5",
        "resolved_model_version": "2026-07-11",
        "bridge_executable": "echo",
        "bridge_config_sha256": "c" * 64,
        "provider_account_lane": "subscription:test",
        "tools_disabled": True,
        "tools_disabled_evidence": "test-evidence",
    }
    route_obj = layerb_qualify.EffectiveRoute.from_mapping(route_input)
    report = {
        "verdict": "PASS_SHADOW",
        "tier": "shadow",
        "effective_route": route_obj.to_dict(),
        "thresholds": thresholds,
        "tier_evaluation": tier_evaluation,
        "human_audit_of_new_accepts": {"complete": True},
        "row_eligibility_matrix": [{"case_id": "row", "reason": "ELIGIBLE", "eligible": True}],
        "raw_call_manifest": [{"case_id": "row", "raw": "recorded"}],
    }
    report_path.write_text(json.dumps(report, sort_keys=True), encoding="utf-8")
    raw_path.write_text(json.dumps(report["raw_call_manifest"], sort_keys=True), encoding="utf-8")

    att = layerb_qualify.create_attestation(
        report_path=report_path,
        raw_call_manifest_path=raw_path,
        labels_path=labels,
        corpus_manifests=[corpus_m],
        fixture_manifests=[fixture_m],
        expires_at=datetime.now(UTC) + timedelta(days=30),
        require_frozen_main_hash=False,
        tier="shadow",
    )
    att_path = att_dir / "qualification-attestation.json"
    att_path.write_text(json.dumps(att, sort_keys=True), encoding="utf-8")

    def _claude_dispatch(
        _target: qg_workflow.ReviewTarget,
        _prompt: str,
    ) -> llm_reviewer_dispatch.DispatchResult:
        res = _dispatch(_target, _prompt)
        return llm_reviewer_dispatch.DispatchResult(
            response_text=res.response_text,
            reviewer_model_id="test-reviewer",
            reviewer_family="claude",
            route_name="test-route",
            tool_call_count=res.tool_call_count,
            tools_used=res.tools_used,
            tool_events=res.tool_events,
        )

    result = qg_shadow_run.run_shadow_module(
        _target(module_dir),
        audit_dir=tmp_path / "audit",
        shadow_db=tmp_path / "shadow.db",
        author_family="claude",
        reviewer=_claude_dispatch,
        live_reviewer=False,
        reviewer_model_id="test-reviewer",
        reviewer_family="claude",
        max_cost_usd=1.0,
        layerb_dry_run=True,
        judge_command="echo",
        judge_family="claude",
        judge_model="sonnet-5",
        judge_model_version="2026-07-11",
        provider_account_lane="subscription:test",
        judge_attestation=att_path,
        labels=labels,
        corpus_manifests=[corpus_m],
        fixture_manifests=[fixture_m],
    )

    report = json.loads(result.layerb_report_path.read_text(encoding="utf-8"))
    assert report["records"]
    detail = report["records"][0]["candidate_details"][0]
    assert detail["relation"] == "AUDIT"
    assert detail["failure_class"] == "LINEAGE_OR_ROUTE"


def test_shadow_driver_partial_judge_args_raises_value_error(tmp_path: Path) -> None:
    module_dir = _module(tmp_path)
    with pytest.raises(ValueError, match="attested Layer-B shadow requires judge_family, judge_model"):
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
            judge_command="echo",  # ONLY setting judge_command, leaving siblings as None
        )
