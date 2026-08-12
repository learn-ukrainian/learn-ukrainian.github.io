from __future__ import annotations

import copy
import json
import stat
from pathlib import Path

import pytest

from scripts.projects.open_model_data import phase3_v3_prefreeze_readiness as readiness

SHA_A = "a" * 64
SHA_B = "b" * 64


def _stub_external_receipts(monkeypatch: pytest.MonkeyPatch) -> None:
    ua_receipt = {
        "receipt_sha256": SHA_A,
        "complete_context": {
            "eligible_context_record_count": 6_698,
            "eligible_v2_unit_count": 8_934,
            "excluded_v2_unit_count_by_reason": {"target_sentence_not_exactly_aligned": 3},
        },
    }
    historical_receipt = {
        "receipt_sha256": SHA_B,
        "denominators": {
            "ud_explicit_orv_uk": {"documents": 82, "sentences": 1_311, "token_rows": 35_081},
            "plug2": {"uk_documents": 56_080},
            "plug2_candidate_uk_token_sum": 71_802_066,
        },
    }
    shapes = ["substitution", "insertion", "deletion", "reordering", "punctuation_only", "multi_edit"]
    battery = {"battery_sha256": SHA_A, "packets": [{"edit_shape": shape} for shape in shapes]}
    verification = {
        "verification_sha256": SHA_B,
        "documents_verified": 12,
        "retrievals_verified": 12,
    }
    monkeypatch.setattr(
        readiness,
        "_validate_ua_context_receipt",
        lambda _path, _database_sha256: (ua_receipt, SHA_A),
    )
    monkeypatch.setattr(
        readiness,
        "_validate_historical_receipt",
        lambda _path, _gate_sha256: (historical_receipt, SHA_B),
    )
    monkeypatch.setattr(readiness, "_validate_canary", lambda _path: (battery, verification))
    monkeypatch.setattr(readiness, "_validate_reboot_prompt", lambda _path: None)
    monkeypatch.setattr(
        readiness, "_validate_sources_database", lambda _path: readiness.university.EXPECTED_DATABASE["sha256"]
    )


def _build(monkeypatch: pytest.MonkeyPatch) -> dict:
    _stub_external_receipts(monkeypatch)
    return readiness.build_readiness(
        phase3_reboot_prompt_path=Path("unused-prompt"),
        sources_database_path=Path("unused-database"),
        ua_gec_root=Path("unused-ua-gec"),
        ua_gec_context_receipt_path=Path("unused-ua-receipt.json"),
        historical_full_receipt_path=Path("unused-historical-receipt.json"),
    )


def test_build_is_deterministic_text_free_and_fail_closed(monkeypatch: pytest.MonkeyPatch) -> None:
    first = _build(monkeypatch)
    second = readiness.build_readiness(
        phase3_reboot_prompt_path=Path("different-unused-prompt"),
        sources_database_path=Path("different-unused-database"),
        ua_gec_root=Path("different-unused-ua-gec"),
        ua_gec_context_receipt_path=Path("different-unused-ua-receipt.json"),
        historical_full_receipt_path=Path("different-unused-historical-receipt.json"),
    )

    assert first == second
    assert first["text_free"] is True
    assert first["provider_calls"] is False
    assert first["denominators"]["v2"] == {
        "source_units": 67_041,
        "evaluation_identities": 9_392,
        "ua_gec_units": 8_937,
    }
    assert first["denominators"]["ua_gec_complete_context"] == {
        "eligible_records": 6_698,
        "represented_v2_units": 8_934,
        "excluded_v2_units": 3,
    }
    assert first["bindings"]["ua_gec_representation_adapter_implementation_sha256"] == readiness.sha256_file(
        Path(readiness.ua_context.representation.__file__).resolve()
    )
    assert first["denominators"]["v3_evaluation"]["frozen_evidence_backed_labels"] == 0
    assert first["cycle002"]["disposition"] == "diagnostic_only"
    assert first["cycle002"]["semantic_gold"] is False
    assert first["additive_sources"]["university_and_historical_outside_v2_totals"] is True
    assert first["semantic_canary"]["packet_count"] == 6
    assert first["semantic_canary"]["operator_display_confirmed"] is True
    assert first["readiness"]["complete_evaluation_package_ready"] is False
    assert first["gates"] == {
        "new_train_development_extraction_authorized": False,
        "broad_provider_run_authorized": False,
        "source_authoring_authorized": False,
        "evaluation_partition_frozen": False,
        "source_coverage_ready": False,
        "source_freeze_ready": False,
        "phase3_complete": False,
        "phase4_blocked": True,
    }
    assert first["receipt_sha256"] == readiness.receipt_sha256(first)
    assert "source_text" not in readiness.canonical_json(first)


@pytest.mark.parametrize(
    ("path", "value"),
    [
        (("cycle002", "semantic_gold"), True),
        (("readiness", "complete_evaluation_package_ready"), True),
        (("gates", "source_authoring_authorized"), True),
        (("gates", "phase4_blocked"), False),
        (("denominators", "v3_evaluation", "frozen_evidence_backed_labels"), 9_392),
        (("semantic_canary", "operator_display_confirmed"), False),
    ],
)
def test_validator_rejects_completion_or_authority_overclaims(
    monkeypatch: pytest.MonkeyPatch,
    path: tuple[str, ...],
    value: object,
) -> None:
    receipt = copy.deepcopy(_build(monkeypatch))
    target = receipt
    for key in path[:-1]:
        target = target[key]
    target[path[-1]] = value
    receipt["receipt_sha256"] = readiness.receipt_sha256(receipt)

    with pytest.raises(readiness.PrefreezeReadinessError):
        readiness.validate_readiness(receipt)


def test_validator_rejects_body_hash_drift(monkeypatch: pytest.MonkeyPatch) -> None:
    receipt = _build(monkeypatch)
    receipt["receipt_sha256"] = SHA_A

    with pytest.raises(readiness.PrefreezeReadinessError, match="body hash drift"):
        readiness.validate_readiness(receipt)


def test_validator_preserves_historical_v1_receipts_without_adapter_binding(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    receipt = _build(monkeypatch)
    del receipt["bindings"]["ua_gec_representation_adapter_implementation_sha256"]
    receipt["receipt_sha256"] = readiness.receipt_sha256(receipt)

    assert readiness.validate_readiness(receipt) == receipt


def test_optional_saint_sophia_receipt_binds_without_opening_other_gates(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _stub_external_receipts(monkeypatch)
    saint_receipt = {"receipt_sha256": SHA_A}
    captured: dict[str, str] = {}

    def validate_saint(path: Path, *, university_database_sha256: str, current_database_sha256: str) -> tuple[dict, str]:
        captured.update({"path": str(path), "pre": university_database_sha256, "post": current_database_sha256})
        return saint_receipt, SHA_B

    monkeypatch.setattr(readiness, "_validate_saint_sophia_reconciliation_receipt", validate_saint)
    receipt = readiness.build_readiness(
        phase3_reboot_prompt_path=Path("unused"), sources_database_path=Path("unused"),
        ua_gec_root=Path("unused"), ua_gec_context_receipt_path=Path("unused"),
        historical_full_receipt_path=Path("unused"),
        saint_sophia_reconciliation_receipt_path=Path("saint-sophia.json"),
    )
    assert captured == {
        "path": "saint-sophia.json", "pre": readiness.university.EXPECTED_DATABASE["sha256"],
        "post": readiness.university.EXPECTED_DATABASE["sha256"],
    }
    assert receipt["readiness"]["saint_sophia_db_reconciliation_ready"] is True
    assert receipt["gates"]["phase4_blocked"] is True
    assert receipt["gates"]["source_authoring_authorized"] is False
    assert receipt["bindings"]["saint_sophia_reconciliation_receipt_sha256"] == SHA_A


def test_optional_saint_sophia_receipt_allows_distinct_pre_and_post_database_hashes(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _stub_external_receipts(monkeypatch)
    pre_sha, post_sha = "c" * 64, "d" * 64
    monkeypatch.setattr(readiness, "_validate_sources_database", lambda _path: post_sha)
    university_freeze, university_file_sha256 = readiness._validate_university_freeze()
    university_freeze = copy.deepcopy(university_freeze)
    university_freeze["database"]["sha256"] = pre_sha
    monkeypatch.setattr(readiness, "_validate_university_freeze", lambda: (university_freeze, university_file_sha256))
    captured: dict[str, str] = {}

    def validate_saint(_path: Path, *, university_database_sha256: str, current_database_sha256: str) -> tuple[dict, str]:
        captured.update({"pre": university_database_sha256, "post": current_database_sha256})
        return {"receipt_sha256": SHA_A}, SHA_B

    monkeypatch.setattr(readiness, "_validate_saint_sophia_reconciliation_receipt", validate_saint)
    receipt = readiness.build_readiness(
        phase3_reboot_prompt_path=Path("unused"), sources_database_path=Path("unused"),
        ua_gec_root=Path("unused"), ua_gec_context_receipt_path=Path("unused"),
        historical_full_receipt_path=Path("unused"), saint_sophia_reconciliation_receipt_path=Path("sophia.json"),
    )
    assert captured == {"pre": pre_sha, "post": post_sha}
    assert receipt["bindings"]["sources_database_sha256"] == post_sha


def test_validator_rejects_saint_sophia_readiness_without_matching_bindings(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    receipt = _build(monkeypatch)
    receipt["readiness"]["saint_sophia_db_reconciliation_ready"] = True
    receipt["receipt_sha256"] = readiness.receipt_sha256(receipt)
    with pytest.raises(readiness.PrefreezeReadinessError, match="Saint Sophia readiness"):
        readiness.validate_readiness(receipt)


def test_saint_sophia_receipt_requires_current_implementation_and_database_bindings(
    tmp_path: Path,
) -> None:
    sophia = readiness.sophia_reconciliation
    database_sha = readiness.university.EXPECTED_DATABASE["sha256"]
    body = {
        "schema_version": "phase3_saint_sophia_db_reconciliation_v1", "text_free": True,
        "provider_calls": False, "mode": "candidate_atomic_replace",
        "bindings": {
            "implementation_sha256": readiness.sha256_file(Path(sophia.__file__).resolve()),
            "schema_sha256": readiness.sha256_file(sophia.SCHEMA_PATH),
            "denominator_sha256": readiness.sha256_file(sophia.DENOMINATOR_PATH),
            "expected_pre_database_sha256": database_sha,
            "saint_sophia_jsonl_sha256": sophia.EXPECTED_JSONL_SHA256,
            "saint_sophia_coverage_sha256": sophia.EXPECTED_COVERAGE_SHA256,
            "coverage_receipt_sha256": sophia.EXPECTED_COVERAGE_SHA256,
        },
        "database": {
            "pre_sha256": database_sha, "post_sha256": database_sha, "historical_rows_before": 0,
            "historical_rows_after": 4157, "historical_fts_rows_after": 4157,
            "foreign_key_failures_before": 0, "foreign_key_failures_after": 0,
            "foreign_key_failure_sha256_before": SHA_B, "foreign_key_failure_sha256_after": SHA_B,
        },
        "invariants": {
            "saint_sophia_id_set_sha256": sophia.EXPECTED_ID_SET_SHA256,
            "non_historical_table_fingerprint_before": SHA_A,
            "non_historical_table_fingerprint_after": SHA_A, "integrity_check": "ok",
        },
        "safeguards": {"exact_expected_rows": True, "exact_fts_parity": True,
                       "foreign_key_failures_unchanged": True, "non_historical_invariants_unchanged": True,
                       "output_private_0600": True},
        "phase_boundaries": {"historical_modern_correction_eligible": False, "phase4_blocked": True},
    }
    receipt = {**body, "receipt_sha256": sophia.receipt_sha256(body)}
    path = tmp_path / "saint-sophia-receipt.json"
    path.write_text(json.dumps(receipt), encoding="utf-8")
    path.chmod(0o600)
    assert readiness._validate_saint_sophia_reconciliation_receipt(
        path, university_database_sha256=database_sha, current_database_sha256=database_sha
    )[0] == receipt
    receipt["bindings"]["implementation_sha256"] = SHA_A
    receipt["receipt_sha256"] = sophia.receipt_sha256(receipt)
    path.write_text(json.dumps(receipt), encoding="utf-8")
    with pytest.raises(readiness.PrefreezeReadinessError, match="implementation drift"):
        readiness._validate_saint_sophia_reconciliation_receipt(
            path, university_database_sha256=database_sha, current_database_sha256=database_sha
        )


def test_saint_sophia_receipt_rejects_nonprivate_mode(tmp_path: Path) -> None:
    sophia = readiness.sophia_reconciliation
    database_sha = readiness.university.EXPECTED_DATABASE["sha256"]
    body = {
        "schema_version": "phase3_saint_sophia_db_reconciliation_v1", "text_free": True,
        "provider_calls": False, "mode": "candidate_atomic_replace",
        "bindings": {"implementation_sha256": readiness.sha256_file(Path(sophia.__file__).resolve()),
                     "schema_sha256": readiness.sha256_file(sophia.SCHEMA_PATH),
                     "denominator_sha256": readiness.sha256_file(sophia.DENOMINATOR_PATH),
                     "expected_pre_database_sha256": database_sha,
                     "saint_sophia_jsonl_sha256": sophia.EXPECTED_JSONL_SHA256,
                     "saint_sophia_coverage_sha256": sophia.EXPECTED_COVERAGE_SHA256,
                     "coverage_receipt_sha256": sophia.EXPECTED_COVERAGE_SHA256},
        "database": {"pre_sha256": database_sha, "post_sha256": database_sha, "historical_rows_before": 0,
                     "historical_rows_after": 4157, "historical_fts_rows_after": 4157,
                     "foreign_key_failures_before": 0, "foreign_key_failures_after": 0,
                     "foreign_key_failure_sha256_before": SHA_B, "foreign_key_failure_sha256_after": SHA_B},
        "invariants": {"saint_sophia_id_set_sha256": sophia.EXPECTED_ID_SET_SHA256,
                       "non_historical_table_fingerprint_before": SHA_A,
                       "non_historical_table_fingerprint_after": SHA_A, "integrity_check": "ok"},
        "safeguards": {"exact_expected_rows": True, "exact_fts_parity": True,
                       "foreign_key_failures_unchanged": True, "non_historical_invariants_unchanged": True,
                       "output_private_0600": True},
        "phase_boundaries": {"historical_modern_correction_eligible": False, "phase4_blocked": True},
    }
    receipt = {**body, "receipt_sha256": sophia.receipt_sha256(body)}
    path = tmp_path / "public-mode.json"
    path.write_text(json.dumps(receipt), encoding="utf-8")
    path.chmod(0o644)
    with pytest.raises(readiness.PrefreezeReadinessError, match="mode 0600"):
        readiness._validate_saint_sophia_reconciliation_receipt(
            path, university_database_sha256=database_sha, current_database_sha256=database_sha
        )


def test_build_rejects_incomplete_canary(monkeypatch: pytest.MonkeyPatch) -> None:
    _stub_external_receipts(monkeypatch)
    monkeypatch.setattr(
        readiness,
        "_validate_canary",
        lambda _path: (
            {"battery_sha256": SHA_A, "packets": [{"edit_shape": "substitution"}]},
            {"verification_sha256": SHA_B, "documents_verified": 12, "retrievals_verified": 12},
        ),
    )

    with pytest.raises(readiness.PrefreezeReadinessError, match="schema violation"):
        readiness.build_readiness(
            phase3_reboot_prompt_path=Path("unused"),
            sources_database_path=Path("unused"),
            ua_gec_root=Path("unused"),
            ua_gec_context_receipt_path=Path("unused"),
            historical_full_receipt_path=Path("unused"),
        )


def test_main_writes_private_canonical_receipt(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    receipt = _build(monkeypatch)
    output = tmp_path / "receipt.json"
    monkeypatch.setattr(readiness, "build_readiness", lambda **_kwargs: receipt)

    assert (
        readiness.main(
            [
                "--phase3-reboot-prompt",
                "unused",
                "--sources-database",
                "unused",
                "--ua-gec-root",
                "unused",
                "--ua-gec-context-receipt",
                "unused",
                "--historical-full-receipt",
                "unused",
                "--output",
                str(output),
            ]
        )
        == 0
    )
    status = json.loads(capsys.readouterr().out)
    assert status == {"ok": True, "output": str(output), "receipt_sha256": receipt["receipt_sha256"]}
    assert output.read_bytes() == readiness.canonical_bytes(receipt)
    assert stat.S_IMODE(output.stat().st_mode) == 0o600
