from __future__ import annotations

import json
import os
import stat
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator

from scripts.projects.open_model_data import phase3_evaluation_context_manifest as manifest
from scripts.projects.open_model_data import phase3_ua_gec_complete_context as ua_context

ROOT = Path(__file__).resolve().parents[1]
SCHEMA = ROOT / "data/projects/open_model_data/contracts/phase3_evaluation_context_manifest_receipt_v1.schema.json"


def _text(family: str, ordinal: int) -> str:
    return f"текст {family} {ordinal} для перевірки контексту."


def _source_row(family: str, ordinal: int, unit_id: str | None = None) -> dict[str, object]:
    text = _text(family, ordinal)
    unit_id = unit_id or f"unit.{family}.{ordinal}"
    frozen_locator = {"kind": "fixture", "family": family, "ordinal": ordinal}
    return {
        "family_id": family,
        "unit_id": unit_id,
        "unit_sha256": manifest.sha256_value([family, ordinal]),
        "frozen_locator": frozen_locator,
        "frozen_locator_sha256": manifest.sha256_value(frozen_locator),
        "document_or_edition_identity": f"doc.{family}.{ordinal}",
        "source_text": text,
        "source_record": {"text": text},
        "source_text_sha256": manifest.sha256_bytes(text.encode("utf-8")),
    }


def _partition_row(source_row: dict[str, object], *, lane: str) -> dict[str, object]:
    return {
        "family_id": source_row["family_id"],
        "unit_id": source_row["unit_id"],
        "unit_sha256": source_row["unit_sha256"],
        "reason": "evaluation_only",
        "candidate_lane": lane,
        "source_text_sha256": source_row["source_text_sha256"],
        "frozen_locator_sha256": source_row["frozen_locator_sha256"],
    }


def _ua_gec_representation(unit_id: str, source_text: str, corrected_text: str) -> dict[str, object]:
    return {
        "schema_version": "phase3_linguistic_representation_v3",
        "document": {
            "frozen_locator": {
                "repository": ua_context.UA_GEC_REPOSITORY,
                "commit": ua_context.UA_GEC_COMMIT,
                "v2_unit_ids": [unit_id],
                "v2_unit_count": 1,
            }
        },
        "source": {"complete_text": source_text},
        "corrected": {"complete_text": corrected_text},
        "evidence": {"correction_evidence": [], "corroborating_corpus_evidence": []},
        "provider_calls": False,
    }


def _write_jsonl(path: Path, rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    os.chmod(path.parent, manifest.PRIVATE_DIR_MODE)
    payload = b"".join(manifest.canonical_bytes(row) for row in rows)
    path.write_bytes(payload)
    os.chmod(path, manifest.PRIVATE_FILE_MODE)


def _write_json(path: Path, value: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    os.chmod(path.parent, manifest.PRIVATE_DIR_MODE)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    os.chmod(path, manifest.PRIVATE_FILE_MODE)


def _fixture_bundle(tmp_path: Path) -> dict[str, Path]:
    private = tmp_path / "private"
    private.mkdir(mode=manifest.PRIVATE_DIR_MODE)
    os.chmod(private, manifest.PRIVATE_DIR_MODE)

    ua_complete = _source_row("ua_gec", 0, "ua-gec:complete:1")
    ua_excluded = _source_row("ua_gec", 1, "ua-gec:excluded:1")
    school = _source_row("school_textbooks", 0)
    source_rows = [ua_complete, ua_excluded, school]
    source_jsonl = private / "source_units_v1.jsonl"
    _write_jsonl(source_jsonl, source_rows)

    partition_rows = [
        _partition_row(ua_complete, lane="clean_modern"),
        _partition_row(ua_excluded, lane="phenomenon_strata"),
        _partition_row(school, lane="phenomenon_strata"),
    ]
    partition = private / "partition_manifest_v1.jsonl"
    _write_jsonl(partition, partition_rows)

    materialization_receipt = {
        "schema_version": "phase3_source_unit_materialization_receipt_v1",
        "text_free": True,
        "implementation_version": "phase3_source_unit_materialization_v1",
        "no_leakage": True,
        "source_universe_receipt_sha256": "a" * 64,
        "private_jsonl_sha256": manifest.sha256_file(source_jsonl),
        "private_record_count": len(source_rows),
        "family_counts": {
            "antonenko_style_guide": 0,
            "ua_gec": 2,
            "school_textbooks": 1,
            "antonenko_textbook_representation": 0,
            "calque_inventory": 0,
            "pravopys_2019_complete": 0,
            "pravopys_2026_complete": 0,
            "other_normative_style_inventory": 0,
        },
    }
    materialization_receipt["receipt_sha256"] = manifest.receipt_sha256(materialization_receipt)
    materialization_path = private / "source-materialization-public.json"
    _write_json(materialization_path, materialization_receipt)

    evaluation_receipt = {
        "schema_version": "phase3_evaluation_partition_receipt_v1",
        "text_free": True,
        "implementation_version": "phase3_evaluation_freeze_v1",
        "artifact_hashes": {"partition_manifest_sha256": manifest.sha256_file(partition)},
        "aggregates": {
            "sealed_evaluation_total": len(partition_rows),
            "clean_modern_candidate_total": 1,
        },
    }
    evaluation_receipt["receipt_sha256"] = manifest.receipt_sha256(evaluation_receipt)
    evaluation_path = private / "evaluation-partition-public.json"
    _write_json(evaluation_path, evaluation_receipt)

    ua_context_rows = [
        _ua_gec_representation(
            "ua-gec:complete:1",
            str(ua_complete["source_text"]),
            "виправлений текст для повного контексту.",
        )
    ]
    ua_context_path = private / "ua_gec_complete_context_v1.jsonl"
    _write_jsonl(ua_context_path, ua_context_rows)

    exclusions = [{"unit_id": "ua-gec:excluded:1", "reason": "target_sentence_not_exactly_aligned"}]
    ua_exclusions_path = private / "ua_gec_complete_context_exclusions_v1.jsonl"
    _write_jsonl(ua_exclusions_path, exclusions)

    ua_receipt = {
        "schema_version": ua_context.SCHEMA_VERSION,
        "implementation_version": ua_context.IMPLEMENTATION_VERSION,
        "text_free": True,
        "provider_calls": False,
        "started_at": "2026-08-12T00:00:00Z",
        "completed_at": "2026-08-12T00:01:00Z",
        "bindings": {
            "phase3_reboot_prompt_v3_sha256": ua_context.PHASE3_REBOOT_V3_SHA256,
            "phase3_recovery_prompt_v2_sha256": ua_context.PHASE3_RECOVERY_V2_SHA256,
            "implementation_sha256": "b" * 64,
            "receipt_schema_sha256": "b" * 64,
            "representation_implementation_sha256": "b" * 64,
            "representation_schema_sha256": "b" * 64,
            "v2_source_universe_receipt_sha256": "b" * 64,
            "v2_ua_gec_ledger_sha256": "b" * 64,
            "sources_database_sha256": "b" * 64,
            "ua_gec_repository": ua_context.UA_GEC_REPOSITORY,
            "ua_gec_commit": ua_context.UA_GEC_COMMIT,
            "ua_gec_license": ua_context.UA_GEC_LICENSE,
        },
        "denominator": {"v2_ua_gec_unit_count": 2, "v2_tag_counts": {"G/Case": 2}, "all_v2_units_mapped": True},
        "complete_context": {
            "annotated_document_count": 1,
            "source_document_count_with_eligible_context": 1,
            "target_document_count_with_eligible_context": 1,
            "eligible_context_record_count": 1,
            "eligible_v2_unit_count": 1,
            "excluded_context_candidate_count_by_reason": {"target_sentence_not_exactly_aligned": 1},
            "excluded_v2_unit_count_by_reason": {"target_sentence_not_exactly_aligned": 1},
            "all_eligible_records_validate": True,
            "private_jsonl_sha256": manifest.sha256_file(ua_context_path),
            "private_jsonl_bytes": ua_context_path.stat().st_size,
            "private_exclusions_jsonl_sha256": manifest.sha256_file(ua_exclusions_path),
            "private_exclusions_jsonl_bytes": ua_exclusions_path.stat().st_size,
            "private_exclusions_jsonl_rows": 1,
        },
        "gates": {
            "complete_context_materialization_ready": True,
            "semantic_labels_present": False,
            "cycle002_labels_diagnostic_only": True,
            "source_authoring_blocked": True,
            "evaluation_partition_frozen": False,
            "source_coverage_ready": False,
            "phase3_complete": False,
            "phase4_blocked": True,
        },
    }
    ua_receipt["receipt_sha256"] = manifest.sha256_bytes(
        manifest.canonical_bytes({k: v for k, v in ua_receipt.items() if k != "receipt_sha256"})
    )
    ua_receipt_path = private / "phase3-ua-gec-complete-context-receipt-v1.json"
    _write_json(ua_receipt_path, ua_receipt)

    return {
        "source_jsonl": source_jsonl,
        "materialization_receipt": materialization_path,
        "partition": partition,
        "evaluation_freeze_receipt": evaluation_path,
        "ua_gec_context": ua_context_path,
        "ua_gec_exclusions": ua_exclusions_path,
        "ua_gec_receipt": ua_receipt_path,
        "private_output": private / manifest.PRIVATE_FILENAME,
        "public_receipt": tmp_path / "public-receipt.json",
    }


def _patch_fixture_pins(monkeypatch: pytest.MonkeyPatch, paths: dict[str, Path], row_count: int) -> None:
    monkeypatch.setattr(manifest, "ROW_COUNT", row_count)
    monkeypatch.setattr(manifest, "V2_EVALUATION_IDENTITIES", row_count)
    monkeypatch.setattr(manifest, "V2_SOURCE_UNITS", row_count)
    monkeypatch.setattr(
        manifest,
        "CONTEXT_ACCOUNTING",
        {
            "ua_gec_complete_context": 1,
            "ua_gec_typed_exclusion": 1,
            "frozen_source_unit_text": 1,
        },
    )
    monkeypatch.setattr(
        manifest,
        "SEALED_FAMILY_COUNTS",
        {
            "school_textbooks": 1,
            "ua_gec": 2,
            "pravopys_2026_complete": 0,
            "pravopys_2019_complete": 0,
            "antonenko_style_guide": 0,
            "calque_inventory": 0,
            "antonenko_textbook_representation": 0,
            "other_normative_style_inventory": 0,
        },
    )
    monkeypatch.setattr(manifest, "LANE_COUNTS", {"clean_modern": 1, "phenomenon_strata": 2})
    monkeypatch.setattr(manifest, "PINNED_SOURCE_UNIVERSE_RECEIPT_SHA256", "a" * 64)
    monkeypatch.setattr(manifest, "PINNED_SOURCE_UNITS_JSONL_SHA256", manifest.sha256_file(paths["source_jsonl"]))
    monkeypatch.setattr(
        manifest, "PINNED_MATERIALIZATION_RECEIPT_FILE_SHA256", manifest.sha256_file(paths["materialization_receipt"])
    )
    monkeypatch.setattr(
        manifest,
        "PINNED_MATERIALIZATION_RECEIPT_BODY_SHA256",
        manifest.receipt_sha256(json.loads(paths["materialization_receipt"].read_text(encoding="utf-8"))),
    )
    monkeypatch.setattr(manifest, "PINNED_PARTITION_SHA256", manifest.sha256_file(paths["partition"]))
    monkeypatch.setattr(
        manifest, "PINNED_EVALUATION_FREEZE_FILE_SHA256", manifest.sha256_file(paths["evaluation_freeze_receipt"])
    )
    monkeypatch.setattr(
        manifest,
        "PINNED_EVALUATION_FREEZE_BODY_SHA256",
        manifest.receipt_sha256(json.loads(paths["evaluation_freeze_receipt"].read_text(encoding="utf-8"))),
    )
    monkeypatch.setattr(manifest, "PINNED_UA_GEC_CONTEXT_SHA256", manifest.sha256_file(paths["ua_gec_context"]))
    monkeypatch.setattr(manifest, "PINNED_UA_GEC_EXCLUSIONS_SHA256", manifest.sha256_file(paths["ua_gec_exclusions"]))
    monkeypatch.setattr(
        manifest, "PINNED_UA_GEC_CONTEXT_RECEIPT_FILE_SHA256", manifest.sha256_file(paths["ua_gec_receipt"])
    )
    monkeypatch.setattr(
        manifest,
        "PINNED_UA_GEC_CONTEXT_RECEIPT_BODY_SHA256",
        manifest.receipt_sha256(json.loads(paths["ua_gec_receipt"].read_text(encoding="utf-8"))),
    )
    monkeypatch.setattr(
        manifest,
        "MATERIALIZATION_FAMILY_COUNTS",
        json.loads(paths["materialization_receipt"].read_text(encoding="utf-8"))["family_counts"],
    )
    monkeypatch.setattr(manifest, "validate_receipt", lambda receipt: dict(receipt))


def test_build_manifest_accounts_for_fixture_rows(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    paths = _fixture_bundle(tmp_path)
    _patch_fixture_pins(monkeypatch, paths, row_count=3)
    monkeypatch.setattr(ua_context, "validate_receipt", lambda value: dict(value))
    rows, accounting = manifest.build_manifest(
        source_jsonl=paths["source_jsonl"],
        materialization_receipt_path=paths["materialization_receipt"],
        partition_path=paths["partition"],
        evaluation_freeze_receipt_path=paths["evaluation_freeze_receipt"],
        ua_gec_context_path=paths["ua_gec_context"],
        ua_gec_exclusions_path=paths["ua_gec_exclusions"],
        ua_gec_receipt_path=paths["ua_gec_receipt"],
    )
    assert len(rows) == 3
    assert dict(accounting) == {"ua_gec_complete_context": 1, "ua_gec_typed_exclusion": 1, "frozen_source_unit_text": 1}
    complete = next(row for row in rows if row["context_kind"] == "ua_gec_complete_context")
    excluded = next(row for row in rows if row["context_kind"] == "ua_gec_typed_exclusion")
    fragment = next(row for row in rows if row["context_kind"] == "frozen_source_unit_text")
    assert complete["complete_sentence_context"] is True
    assert "representation" in complete
    assert excluded["complete_sentence_context"] is False
    assert excluded["exclusion_reason_code"] == "target_sentence_not_exactly_aligned"
    assert fragment["complete_sentence_context"] is False
    assert "qualified_human" not in fragment


def test_materialize_writes_restricted_private_output_and_text_free_receipt(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    paths = _fixture_bundle(tmp_path)
    _patch_fixture_pins(monkeypatch, paths, row_count=3)
    monkeypatch.setattr(ua_context, "validate_receipt", lambda value: dict(value))
    receipt = manifest.materialize(
        source_jsonl=paths["source_jsonl"],
        materialization_receipt_path=paths["materialization_receipt"],
        partition_path=paths["partition"],
        evaluation_freeze_receipt_path=paths["evaluation_freeze_receipt"],
        ua_gec_context_path=paths["ua_gec_context"],
        ua_gec_exclusions_path=paths["ua_gec_exclusions"],
        ua_gec_receipt_path=paths["ua_gec_receipt"],
        private_output=paths["private_output"],
        public_receipt_path=paths["public_receipt"],
        started_at="2026-08-13T21:00:00Z",
        completed_at="2026-08-13T21:00:01Z",
    )
    assert paths["private_output"].exists()
    assert stat.S_IMODE(paths["private_output"].stat().st_mode) == manifest.PRIVATE_FILE_MODE
    assert stat.S_IMODE(paths["private_output"].parent.stat().st_mode) == manifest.PRIVATE_DIR_MODE
    assert receipt["row_count"] == 3
    assert receipt["context_accounting"] == {
        "ua_gec_complete_context": 1,
        "ua_gec_typed_exclusion": 1,
        "frozen_source_unit_text": 1,
    }
    serialized = json.dumps(receipt, ensure_ascii=False)
    assert "source_text" not in serialized
    assert "unit_id" not in serialized
    assert receipt["frozen_evidence_backed_labels"] == 0
    assert receipt["gates"]["phase4_blocked"] is True


def test_public_schema_is_closed_and_text_free() -> None:
    schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
    Draft202012Validator.check_schema(schema)
    serialized = json.dumps(schema, ensure_ascii=False)
    assert "source_text" not in serialized
    assert "unit_id" not in serialized
    assert schema["additionalProperties"] is False


def test_hash_drift_fails_closed(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    paths = _fixture_bundle(tmp_path)
    _patch_fixture_pins(monkeypatch, paths, row_count=3)
    monkeypatch.setattr(ua_context, "validate_receipt", lambda value: dict(value))
    paths["partition"].write_bytes(paths["partition"].read_bytes() + b"\n")
    with pytest.raises(manifest.EvaluationContextManifestError, match="partition"):
        manifest.build_manifest(
            source_jsonl=paths["source_jsonl"],
            materialization_receipt_path=paths["materialization_receipt"],
            partition_path=paths["partition"],
            evaluation_freeze_receipt_path=paths["evaluation_freeze_receipt"],
            ua_gec_context_path=paths["ua_gec_context"],
            ua_gec_exclusions_path=paths["ua_gec_exclusions"],
            ua_gec_receipt_path=paths["ua_gec_receipt"],
        )


def test_changed_private_output_is_not_overwritten(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    paths = _fixture_bundle(tmp_path)
    _patch_fixture_pins(monkeypatch, paths, row_count=3)
    monkeypatch.setattr(ua_context, "validate_receipt", lambda value: dict(value))
    manifest.materialize(
        source_jsonl=paths["source_jsonl"],
        materialization_receipt_path=paths["materialization_receipt"],
        partition_path=paths["partition"],
        evaluation_freeze_receipt_path=paths["evaluation_freeze_receipt"],
        ua_gec_context_path=paths["ua_gec_context"],
        ua_gec_exclusions_path=paths["ua_gec_exclusions"],
        ua_gec_receipt_path=paths["ua_gec_receipt"],
        private_output=paths["private_output"],
        public_receipt_path=paths["public_receipt"],
        started_at="2026-08-13T21:00:00Z",
        completed_at="2026-08-13T21:00:01Z",
    )
    paths["private_output"].write_bytes(paths["private_output"].read_bytes() + b"x")
    with pytest.raises(manifest.EvaluationContextManifestError, match="changed private manifest"):
        manifest.materialize(
            source_jsonl=paths["source_jsonl"],
            materialization_receipt_path=paths["materialization_receipt"],
            partition_path=paths["partition"],
            evaluation_freeze_receipt_path=paths["evaluation_freeze_receipt"],
            ua_gec_context_path=paths["ua_gec_context"],
            ua_gec_exclusions_path=paths["ua_gec_exclusions"],
            ua_gec_receipt_path=paths["ua_gec_receipt"],
            private_output=paths["private_output"],
            public_receipt_path=paths["public_receipt"],
            started_at="2026-08-13T21:00:00Z",
            completed_at="2026-08-13T21:00:02Z",
        )


def test_live_database_path_is_rejected(tmp_path: Path) -> None:
    database = tmp_path / "sources.db"
    database.write_bytes(b"sqlite")
    exit_code = manifest.main(
        [
            "build",
            "--source-jsonl",
            str(tmp_path / "source.jsonl"),
            "--materialization-receipt",
            str(tmp_path / "materialization.json"),
            "--partition",
            str(tmp_path / "partition.jsonl"),
            "--evaluation-freeze-receipt",
            str(tmp_path / "freeze.json"),
            "--ua-gec-context",
            str(tmp_path / "context.jsonl"),
            "--ua-gec-exclusions",
            str(tmp_path / "exclusions.jsonl"),
            "--ua-gec-receipt",
            str(tmp_path / "ua-receipt.json"),
            "--private-output",
            str(tmp_path / "out.jsonl"),
            "--public-receipt",
            str(tmp_path / "public.json"),
            "--database",
            str(database),
        ]
    )
    assert exit_code == 2


@pytest.mark.production
def test_production_manifest_against_drive_custody() -> None:
    drive = (
        Path.home() / "Library/CloudStorage/GoogleDrive-krisztian.koos@gmail.com/My Drive/Projects/learn-ukrainian-data"
    )
    tarball = drive / "backups/phase3-6375/20260811T090325Z/phase3-private-and-durable-artifacts.tar.gz"
    closure = (
        drive / "backups/phase3-6375/20260811T090325Z/phase3-v3-prefreeze-20260812T024213Z/ua-gec-context-closure-v2"
    )
    backup_dir = drive / "backups/phase3-6375/20260813T220000Z/phase3-evaluation-context-manifest-v1"
    public_receipt = ROOT / "data/projects/open_model_data/evidence/phase3_evaluation_context_manifest_receipt_v1.json"
    if not tarball.exists() or not closure.exists():
        pytest.skip("Drive custody artifacts unavailable")
    if backup_dir.exists() and (backup_dir / manifest.PRIVATE_FILENAME).exists():
        receipt = json.loads(public_receipt.read_text(encoding="utf-8"))
        manifest.validate_receipt(receipt)
        assert receipt["context_accounting"] == manifest.CONTEXT_ACCOUNTING
        return
    receipt = manifest.production_run(
        custody_tarball=tarball,
        ua_gec_context_path=closure / "ua_gec_complete_context_v1.jsonl",
        ua_gec_exclusions_path=closure / "ua_gec_complete_context_exclusions_v1.jsonl",
        ua_gec_receipt_path=closure / "phase3-ua-gec-complete-context-receipt-v1.json",
        drive_backup_dir=backup_dir,
        public_receipt_path=public_receipt,
        started_at="2026-08-13T22:00:00Z",
        completed_at="2026-08-13T22:00:30Z",
    )
    manifest.validate_receipt(receipt)
    assert receipt["row_count"] == 9392
    assert receipt["context_accounting"] == manifest.CONTEXT_ACCOUNTING
