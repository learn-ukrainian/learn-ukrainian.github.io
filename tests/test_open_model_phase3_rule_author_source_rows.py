"""Hermetic checks for steward-only Phase 3 rule-author source rows."""

from __future__ import annotations

import json
import os
import sqlite3
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator

from scripts.projects.open_model_data import phase3_heldout_partition as heldout
from scripts.projects.open_model_data import phase3_rule_author_packets as packets
from scripts.projects.open_model_data import phase3_rule_author_source_rows as rows
from scripts.projects.open_model_data import phase3_source_universe as freeze

ROOT = Path(__file__).resolve().parents[1]


def _write(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(rows.canonical_json(value) + "\n", encoding="utf-8")


def _fixture(
    tmp_path: Path,
    *,
    include_test: bool = False,
    source_langs: tuple[str, str] = ("uk", "ru"),
) -> dict[str, Path]:
    root = tmp_path / "synthetic"
    data = root / "data/projects/open_model_data"
    role = ROOT / "data/projects/open_model_data/evidence/correction_protection_role_contract_v1.json"
    evaluation = ROOT / "data/projects/open_model_data/evidence/correction_protection_evaluation_contract_v1.json"
    coverage = ROOT / "data/projects/open_model_data/evidence/correction_protection_coverage_contract_v1.json"
    policy = ROOT / "data/projects/open_model_data/evidence/correction_protection_near_duplicate_policy_v1.json"
    for source, target in ((role, data / "role.json"), (evaluation, data / "evaluation.json"), (coverage, data / "coverage.json"), (policy, data / "policy.json")):
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(source.read_bytes())
    db = root / "data/sources.db"
    db.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(db)
    connection.execute("CREATE TABLE ua_gec_errors (id INTEGER PRIMARY KEY, error TEXT, correct TEXT, error_type TEXT, doc_id TEXT, annotator_id TEXT, partition TEXT, is_native INTEGER, source_lang TEXT)")
    records = [
        (1, "synthetic train error one", "synthetic correction one", "G/Case", "train-doc", "ann-one", "gec/train", 1, source_langs[0]),
        (2, "synthetic train error two", "synthetic correction two", "F/Calque", "train-doc-two", "ann-two", "gec/train", 0, source_langs[1]),
    ]
    if include_test:
        records.append((3, "synthetic heldout error", "synthetic heldout correction", "G/Case", "test-doc", "ann-three", "gec/test", 1, "uk"))
    connection.executemany("INSERT INTO ua_gec_errors VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)", records)
    connection.commit()
    connection.close()
    universe = data / "source-universe"
    units = []
    for ordinal, record in enumerate(records, 1):
        payload = dict(zip(("id", "error", "correct", "error_type", "doc_id", "annotator_id", "partition", "is_native", "source_lang"), record, strict=True))
        units.append({"family_id": "ua_gec", "unit_id": freeze._opaque_id("unit.ua_gec", {"table": "ua_gec_errors", "identity": {"id": record[0]}}), "unit_sha256": freeze._unit_hash(freeze._normal(payload)), "ordinal": ordinal, "locator": {"kind": "sqlite_row", "table": "ua_gec_errors", "primary_key_fields": ["id"], "primary_key_sha256": freeze._unit_hash({"id": record[0]})}})
    ledger = universe / "ua_gec.units.jsonl"
    ledger.parent.mkdir(parents=True, exist_ok=True)
    ledger.write_text("".join(rows.canonical_json(item) + "\n" for item in units), encoding="utf-8")
    freeze_receipt = {"schema_version": "phase3_source_universe_freeze_v1", "text_free": True, "merged_main_sha": "0" * 40, "families": [{"family_id": "ua_gec", "ledger_file": ledger.name, "ledger_sha256": rows.sha256_file(ledger)}]}
    _write(universe / "source-universe-freeze-receipt.json", freeze_receipt)
    steward = heldout.verify_role_binding(heldout.read_json(data / "role.json"))
    clearance = {"schema_version": "phase3_author_clearance_receipt_v1", "text_free": True, "implementation_version": "phase3_heldout_partition_v1", "role_binding": steward, "input_bindings": {"combined_contract_sha256": packets.COMBINED_CONTRACT_SHA256, "role_contract_sha256": rows.sha256_file(data / "role.json"), "evaluation_contract_sha256": rows.sha256_file(data / "evaluation.json"), "coverage_contract_sha256": rows.sha256_file(data / "coverage.json"), "source_universe_receipt_sha256": rows.sha256_file(universe / "source-universe-freeze-receipt.json"), "near_duplicate_policy_fingerprint_sha256": packets.near_duplicate.PINNED_POLICY_FINGERPRINT, "ua_eval_exclusion_manifest_sha256": "2" * 64, "public_canary_exclusion_manifest_sha256": "3" * 64}, "cleared_units": [{key: unit[key] for key in ("family_id", "unit_id", "unit_sha256")} for unit in units], "cleared_unit_count": len(units), "heldout_excluded": True, "ua_eval_exclusion_enforced": True, "public_canary_exclusion_enforced": True, "heldout_complement_encoded": False, "fingerprints_encoded": False, "locators_encoded": False}
    clearance["receipt_sha256"] = packets.receipt_body_sha256(clearance)
    clearance_path = root / "private/author_clearance_v1.json"
    _write(clearance_path, clearance)
    public = {"schema_version": "phase3_heldout_public_receipt_v1", "text_free": True, "input_bindings": {**clearance["input_bindings"], "sources_db_sha256": rows.sha256_file(db)}, "artifact_hashes": {"author_clearance_sha256": clearance["receipt_sha256"]}}
    public["receipt_sha256"] = heldout.receipt_body_sha256(public)
    public_path = root / "public/partition.json"
    _write(public_path, public)
    return {"db": db, "universe": universe, "clearance": clearance_path, "public": public_path, "evaluation": data / "evaluation.json", "coverage": data / "coverage.json", "role": data / "role.json", "policy": data / "policy.json", "private": root / "batch_state/source-rows", "receipt": root / "public/source-rows-receipt.json"}


def _build(paths: dict[str, Path]) -> dict[str, object]:
    return rows.build(clearance_path=paths["clearance"], source_universe_dir=paths["universe"], sources_db=paths["db"], public_partition_receipt_path=paths["public"], evaluation_path=paths["evaluation"], coverage_path=paths["coverage"], role_path=paths["role"], near_duplicate_policy_path=paths["policy"], private_dir=paths["private"], public_receipt_path=paths["receipt"])


def _rewrite_clearance_and_public(paths: dict[str, Path], clearance: dict[str, object]) -> None:
    clearance["cleared_unit_count"] = len(clearance["cleared_units"])
    clearance["receipt_sha256"] = packets.receipt_body_sha256(
        {key: value for key, value in clearance.items() if key != "receipt_sha256"}
    )
    _write(paths["clearance"], clearance)
    public = rows.read_json(paths["public"], "public")
    public["artifact_hashes"]["author_clearance_sha256"] = clearance["receipt_sha256"]
    public["receipt_sha256"] = heldout.receipt_body_sha256(
        {key: value for key, value in public.items() if key != "receipt_sha256"}
    )
    _write(paths["public"], public)


def test_rows_are_deterministic_private_complete_and_packet_compiler_compatible(tmp_path: Path) -> None:
    paths = _fixture(tmp_path)
    first = _build(paths)
    output = paths["private"] / rows.ROWS_FILENAME
    first_bytes = output.read_bytes()
    second = _build(paths)
    assert first == second
    assert output.read_bytes() == first_bytes
    assert (paths["private"].stat().st_mode & 0o777) == 0o700
    assert (output.stat().st_mode & 0o777) == 0o600
    materialized = [json.loads(line) for line in output.read_text(encoding="utf-8").splitlines()]
    assert {item["source_record"]["error_type"] for item in materialized} == {"G/Case", "F/Calque"}
    assert {item["source_record"]["annotator_id"] for item in materialized} == {"ann-one", "ann-two"}
    assert all(item["heldout"] is False and item["ua_eval"] is False and item["public_canary_neighbour"] is False for item in materialized)
    assert all(packets._item_from_row(item, "0" * 64, packets.near_duplicate.PINNED_POLICY_FINGERPRINT) for item in materialized)
    schema = rows.read_json(rows.SCHEMA_PATH, "adapter schema")
    Draft202012Validator.check_schema(schema)
    receipt = rows.read_json(paths["receipt"], "public receipt")
    assert receipt["text_free"] is True and "source_text" not in rows.canonical_json(receipt)
    assert receipt["rule_author_binding"]["role_id"] == "rule_author_extractor"
    assert receipt["rule_author_binding"]["controller_identity_id"] != receipt["role_binding"]["controller_identity_id"]
    assert receipt["input_bindings"]["ua_gec_ledger_sha256"] == rows.sha256_file(paths["universe"] / "ua_gec.units.jsonl")
    assert receipt["input_bindings"]["partition_public_receipt_body_sha256"] == rows.read_json(paths["public"])["receipt_sha256"]
    assert receipt["input_bindings"]["partition_public_receipt_file_sha256"] == rows.sha256_file(paths["public"])
    assert receipt["exclusions"]["all_rows_train"] is True
    assert receipt["exclusions"]["clearance_source_row_set_equal"] is True


def test_empty_source_lang_is_schema_valid_and_preserves_frozen_hash(tmp_path: Path) -> None:
    paths = _fixture(tmp_path, source_langs=("", "fr-CA"))
    _build(paths)
    materialized = [
        json.loads(line)
        for line in (paths["private"] / rows.ROWS_FILENAME).read_text(encoding="utf-8").splitlines()
    ]

    assert {item["source_record"]["source_lang"] for item in materialized} == {"", "fr-CA"}
    assert all(
        item["unit_sha256"] == freeze._unit_hash(freeze._normal(item["source_record"]))
        for item in materialized
    )
    schema = rows.read_json(rows.SCHEMA_PATH, "adapter schema")
    validator = Draft202012Validator(
        {"$schema": schema["$schema"], "$defs": schema["$defs"], "$ref": "#/$defs/sourceRow"}
    )
    for item in materialized:
        validator.validate(item)


def test_rejects_stale_db_test_injection_and_unexpected_or_symlink_private_inputs(tmp_path: Path) -> None:
    paths = _fixture(tmp_path)
    with sqlite3.connect(paths["db"]) as connection:
        connection.execute("UPDATE ua_gec_errors SET error = 'tampered' WHERE id = 1")
    with pytest.raises(rows.SourceRowsError, match="sources DB binding drift"):
        _build(paths)
    paths = _fixture(tmp_path / "test")
    clearance = rows.read_json(paths["clearance"], "clearance")
    clearance["cleared_units"] = [*clearance["cleared_units"], {"family_id": "ua_gec", "unit_id": "unit.ua_gec." + "0" * 64, "unit_sha256": "0" * 64}]
    _rewrite_clearance_and_public(paths, clearance)
    with pytest.raises(rows.SourceRowsError, match="missing frozen source unit"):
        _build(paths)
    paths = _fixture(tmp_path / "test-injection", include_test=True)
    with pytest.raises(rows.SourceRowsError, match="non-train row"):
        _build(paths)
    paths = _fixture(tmp_path / "unexpected")
    paths["private"].mkdir(parents=True, mode=0o700)
    os.chmod(paths["private"], 0o700)
    (paths["private"] / "unexpected.json").write_text("{}\n", encoding="utf-8")
    with pytest.raises(rows.SourceRowsError, match="unexpected file"):
        _build(paths)
    paths = _fixture(tmp_path / "symlink")
    paths["private"].parent.mkdir(parents=True)
    os.symlink(paths["private"].parent, paths["private"])
    with pytest.raises(rows.SourceRowsError, match="symlink"):
        _build(paths)


def test_clearance_omission_is_exact_not_a_complement(tmp_path: Path) -> None:
    paths = _fixture(tmp_path)
    clearance = rows.read_json(paths["clearance"], "clearance")
    clearance["cleared_units"] = clearance["cleared_units"][:1]
    _rewrite_clearance_and_public(paths, clearance)
    receipt = _build(paths)
    output = (paths["private"] / rows.ROWS_FILENAME).read_text(encoding="utf-8").splitlines()
    assert receipt["aggregates"]["source_row_count"] == 1
    assert len(output) == 1


@pytest.mark.parametrize("mutation, match", [
    (lambda clearance: clearance.__setitem__("cleared_units", [*clearance["cleared_units"], clearance["cleared_units"][0]]), "duplicate"),
    (lambda clearance: clearance.__setitem__("cleared_units", [{"family_id": "ua_gec"}]), "schema violation"),
    (lambda clearance: clearance["cleared_units"][0].__setitem__("unit_sha256", "0" * 64), "unit hash drift"),
])
def test_rejects_duplicate_missing_or_wrong_hash_clearance(tmp_path: Path, mutation, match: str) -> None:
    paths = _fixture(tmp_path)
    clearance = rows.read_json(paths["clearance"], "clearance")
    mutation(clearance)
    _rewrite_clearance_and_public(paths, clearance)
    with pytest.raises(rows.SourceRowsError, match=match):
        _build(paths)


def test_rejects_stale_contract_or_partition_receipt_binding_and_permission_drift(tmp_path: Path) -> None:
    paths = _fixture(tmp_path)
    paths["coverage"].write_text("{}\n", encoding="utf-8")
    with pytest.raises(rows.SourceRowsError, match="coverage-contract binding drift"):
        _build(paths)
    paths = _fixture(tmp_path / "receipt")
    public = rows.read_json(paths["public"], "public")
    public["input_bindings"]["sources_db_sha256"] = "0" * 64
    public["receipt_sha256"] = heldout.receipt_body_sha256({key: value for key, value in public.items() if key != "receipt_sha256"})
    _write(paths["public"], public)
    with pytest.raises(rows.SourceRowsError, match="sources DB binding drift"):
        _build(paths)
    paths = _fixture(tmp_path / "permissions")
    _build(paths)
    os.chmod(paths["private"] / rows.ROWS_FILENAME, 0o400)
    with pytest.raises(rows.SourceRowsError, match="permissions drift"):
        _build(paths)


def test_rejects_destructive_output_aliases_and_cli_symlink_path(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    paths = _fixture(tmp_path)
    public_alias = {**paths, "receipt": paths["clearance"]}
    with pytest.raises(rows.SourceRowsError, match="public receipt aliases an input"):
        _build(public_alias)
    private_alias = {**paths, "receipt": paths["private"] / "receipt.json"}
    with pytest.raises(rows.SourceRowsError, match="inside private"):
        _build(private_alias)
    private_in_freeze = {**paths, "private": paths["universe"] / "private-output"}
    with pytest.raises(rows.SourceRowsError, match="private source-row directory may not be inside an input directory"):
        _build(private_in_freeze)
    public_in_freeze = {**paths, "receipt": paths["universe"] / "public-receipt.json"}
    with pytest.raises(rows.SourceRowsError, match="public receipt may not be inside an input directory"):
        _build(public_in_freeze)
    paths["private"].mkdir(parents=True, mode=0o700)
    os.chmod(paths["private"], 0o700)
    aliased_clearance = paths["private"] / rows.ROWS_FILENAME
    aliased_clearance.write_bytes(paths["clearance"].read_bytes())
    os.chmod(aliased_clearance, 0o600)
    rows_alias = {**paths, "clearance": aliased_clearance}
    with pytest.raises(rows.SourceRowsError, match="private source rows alias an input"):
        _build(rows_alias)
    link = tmp_path / "clearance-link.json"
    os.symlink(paths["clearance"], link)
    with pytest.raises(SystemExit) as exc:
        rows.main([
            "--clearance", str(link), "--source-universe", str(paths["universe"]), "--sources-db", str(paths["db"]),
            "--partition-public-receipt", str(paths["public"]), "--evaluation", str(paths["evaluation"]),
            "--coverage", str(paths["coverage"]), "--role", str(paths["role"]), "--near-duplicate-policy", str(paths["policy"]),
            "--private-dir", str(paths["private"]), "--public-receipt", str(paths["receipt"]),
        ])
    assert exc.value.code == 2
    assert "symlink is forbidden" in capsys.readouterr().err
