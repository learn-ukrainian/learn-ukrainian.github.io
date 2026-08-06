"""Synthetic tests for Phase 3 held-out partition, seal, and author clearance."""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator

from scripts.projects.open_model_data import phase3_heldout_partition as heldout
from scripts.projects.open_model_data import phase3_near_duplicate as near
from scripts.projects.open_model_data import phase3_source_universe as freeze_mod

ROOT = Path(__file__).resolve().parents[1]
SCHEMA = ROOT / "data/projects/open_model_data/contracts/phase3_heldout_partition_bundle_v1.schema.json"
POLICY = ROOT / "data/projects/open_model_data/evidence/correction_protection_near_duplicate_policy_v1.json"
ROLE = ROOT / "data/projects/open_model_data/evidence/correction_protection_role_contract_v1.json"


def _write(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if isinstance(value, str):
        path.write_text(value, encoding="utf-8")
    else:
        path.write_text(heldout.canonical_json(value) + "\n", encoding="utf-8")


def _unit_for_row(row_id: int, *, ordinal: int, payload: dict) -> dict:
    identity = {"id": row_id}
    normalized = freeze_mod._normal(payload)
    return {
        "family_id": "ua_gec",
        "unit_id": freeze_mod._opaque_id("unit.ua_gec", {"table": "ua_gec_errors", "identity": identity}),
        "unit_sha256": freeze_mod._unit_hash(normalized),
        "ordinal": ordinal,
        "locator": {
            "kind": "sqlite_row",
            "table": "ua_gec_errors",
            **freeze_mod._primary_key_locator(identity),
        },
        "duplicate_group_id": freeze_mod._opaque_id(
            "duplicate.ua_gec",
            {key: value for key, value in normalized.items() if key != "id"},
        ),
        "parse_status": "parsed",
        "rights": {
            "source_text_committed": False,
            "locator_only_allowed": True,
            "rights_limited_disposition": "evaluation_only",
        },
        "provenance": {
            "input_sha256": "a" * 64,
            "unit_grain": "ua_gec_error_row",
        },
    }


def _build_fixture_root(tmp_path: Path) -> Path:
    """Create a miniature repo root with synthetic UA-GEC, exclusions, and contracts."""
    root = tmp_path / "repo"
    # Shared long synthetic surfaces (ASCII only) so near-dup thresholds are meaningful.
    train_safe = (
        "alpha beta gamma delta epsilon zeta eta theta iota kappa lambda mu "
        "nu xi omicron pi rho sigma tau upsilon phi chi psi omega safe train"
    )
    test_text = (
        "alpha beta gamma delta epsilon zeta eta theta iota kappa lambda mu "
        "nu xi omicron pi rho sigma tau upsilon heldout test document"
    )
    near_train = (
        "alpha beta gamma delta epsilon zeta eta theta iota kappa lambda mu "
        "nu xi omicron pi rho sigma tau upsilon heldout test documentx"
    )
    canary_text = (
        "canary surface one two three four five six seven eight nine ten "
        "eleven twelve thirteen fourteen fifteen sixteen"
    )
    eval_text = (
        "evalset surface one two three four five six seven eight nine ten "
        "eleven twelve thirteen fourteen fifteen sixteen"
    )

    rows = [
        # Cross-layer same raw doc_id on test side (must collapse to one held-out document).
        (1, test_text, "corrected test one", "docA", "gec-only/test"),
        (2, test_text + " layer", "corrected test two", "docA", "gec-fluency/test"),
        # Distinct test document.
        (3, "other test text alpha beta gamma", "other corrected", "docB", "gec-fluency/test"),
        # Train author-safe.
        (4, train_safe, "safe correction one", "docC", "gec-only/train"),
        (5, train_safe + " two", "safe correction two", "docC", "gec-fluency/train"),
        # Train near-neighbour of held-out/eval surface — must be omitted from clearance.
        (6, near_train, "near correction", "docD", "gec-only/train"),
        # Train exact UA-eval row identity exclusion via id=7 linked from evalset.
        (7, eval_text, "eval correction", "docE", "gec-fluency/train"),
        # Train exact public-canary neighbour.
        (8, canary_text, "canary correction", "docF", "gec-only/train"),
    ]

    db_path = root / "data/sources.db"
    db_path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(db_path)
    connection.execute(
        """
        CREATE TABLE ua_gec_errors (
            id INTEGER PRIMARY KEY,
            error TEXT,
            correct TEXT,
            error_type TEXT,
            doc_id TEXT,
            annotator_id TEXT,
            partition TEXT,
            is_native INTEGER,
            source_lang TEXT
        )
        """
    )
    for row_id, error, correct, doc_id, partition in rows:
        connection.execute(
            "INSERT INTO ua_gec_errors VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (row_id, error, correct, "G/Case", doc_id, "ann", partition, 1, "uk"),
        )
    connection.commit()
    connection.close()

    units_path = root / "data/projects/open_model_data/evidence/source_universe_v1/ua_gec.units.jsonl"
    units_path.parent.mkdir(parents=True, exist_ok=True)
    with units_path.open("w", encoding="utf-8") as handle:
        for ordinal, (row_id, error, correct, doc_id, partition) in enumerate(rows, start=1):
            payload = {
                "id": row_id,
                "error": error,
                "correct": correct,
                "error_type": "G/Case",
                "doc_id": doc_id,
                "annotator_id": "ann",
                "partition": partition,
                "is_native": 1,
                "source_lang": "uk",
            }
            handle.write(heldout.canonical_json(_unit_for_row(row_id, ordinal=ordinal, payload=payload)) + "\n")

    freeze_receipt = {
        "schema_version": "phase3_source_universe_freeze_v1",
        "text_free": True,
        "merged_main_sha": "a" * 40,
        "coverage_contract_sha256": "b" * 64,
        "status": "frozen",
    }
    _write(units_path.parent / "source-universe-freeze-receipt.json", freeze_receipt)

    # Copy real role/eval/coverage/near-dup policy bindings into the fixture tree.
    for relative in (
        "data/projects/open_model_data/evidence/correction_protection_role_contract_v1.json",
        "data/projects/open_model_data/evidence/correction_protection_evaluation_contract_v1.json",
        "data/projects/open_model_data/evidence/correction_protection_coverage_contract_v1.json",
        "data/projects/open_model_data/evidence/correction_protection_near_duplicate_policy_v1.json",
        "data/projects/open_model_data/contracts/phase3_heldout_partition_bundle_v1.schema.json",
    ):
        source = ROOT / relative
        target = root / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(source.read_bytes())

    evalset = [
        {
            "id": "eval-synthetic-1",
            "text": eval_text,
            "target": "eval correction",
            "lang": "uk",
            "edits": [],
            "dialect": {"is_regionalism": False, "verdict": "ok", "evidence": []},
            "provenance": {
                "dataset": "synthetic",
                "license": "test",
                "source": "fixture",
                "ua_gec_error_id": 7,
                "taxonomy_version": "v0",
                "version": "v0.1.1",
            },
        }
    ]
    evalset_path = root / "data/projects/ua_eval_harness/evalset_v1.jsonl"
    evalset_path.parent.mkdir(parents=True, exist_ok=True)
    evalset_path.write_text(
        "".join(heldout.canonical_json(item) + "\n" for item in evalset),
        encoding="utf-8",
    )

    heldout_manifest = {
        "schema_version": "ua_gec_heldout_manifest.v1",
        "manifest_id": "synthetic",
        "task": "synthetic",
        "counts": {},
        "record_layouts": {
            "item": [
                "id",
                "doc_id",
                "sentence_index",
                "author_id",
                "is_native",
                "source_language",
                "annotator_ids",
                "is_sensitive",
                "source",
                "source_sha256",
                "observed_tags",
                "eligible_tags",
                "references",
            ],
            "exclusion": ["id", "doc_id", "sentence_index", "source_sha256", "observed_tags"],
            "edit": ["start", "end", "tag", "replacement"],
            "reference": ["annotator_index", "target", "target_sha256", "edits"],
        },
        "record_semantics": {},
        "predicate": {},
        "attribution": {},
        "integrity": {"algorithm": "synthetic", "inputs": [], "outputs": []},
        "items": [
            [
                "item-1",
                "docA",
                0,
                "auth",
                True,
                "uk",
                ["ann"],
                False,
                test_text,
                "c" * 64,
                ["G/Case"],
                ["G/Case"],
                [[0, "corrected test one", "d" * 64, []]],
            ]
        ],
        "exclusions": [["excl-1", "docB", 0, "e" * 64, []]],
    }
    _write(root / "data/projects/ua_eval_harness/heldout_manifest_v1.json", heldout_manifest)

    analysis = root / "data/projects/ua_eval_harness/analysis/v0.1.1/item_evidence.jsonl"
    analysis.parent.mkdir(parents=True, exist_ok=True)
    analysis.write_text(
        heldout.canonical_json({"item_id": "synthetic", "source_sha256": "f" * 64}) + "\n",
        encoding="utf-8",
    )
    v02 = root / "data/projects/ua_eval_harness/v0.2/review_packet_priority_v1.jsonl"
    v02.parent.mkdir(parents=True, exist_ok=True)
    v02.write_text(
        heldout.canonical_json(
            {
                "schema_version": "ua_eval_v02_review_packet.v1",
                "item_id": "synthetic-item",
                "packet_order": 1,
                "review_state": "pending",
                "decision": None,
                "blind_reviewer_view": {"note": "no-text"},
                "coordinator_priority_metadata": {},
                "data_handling": {},
                "frozen_receipts": {},
            }
        )
        + "\n",
        encoding="utf-8",
    )

    known_answers = {
        "schema_version": "correction_protection_known_answers_v1",
        "config_id": "synthetic",
        "consumer_decision": "measure",
        "defaults": {},
        "rights_scope": "project_authored_short_canaries",
        "categories": {
            "synthetic_phenomenon": {
                "phenomenon": "synthetic",
                "positive": [
                    {
                        "text": canary_text,
                        "surface": "canary",
                        "replacement": "canaryx",
                        "canary_ids": ["c1"],
                    }
                ],
                "acceptable_control": [],
                "protected": [],
                "evidence": [],
            }
        },
    }
    _write(
        root / "data/projects/open_model_data/detector/correction_protection_known_answers_v1.json",
        known_answers,
    )
    return root


def _build_fixture_artifacts(root: Path) -> tuple[Path, Path]:
    private = root / "batch_state/open-model-data/phase3-heldout"
    public = root / "data/projects/open_model_data/evidence/phase3_heldout_partition_v1"
    heldout.build_artifacts(
        root=root,
        source_universe=root / "data/projects/open_model_data/evidence/source_universe_v1",
        sources_db=root / "data/sources.db",
        private_dir=private,
        public_dir=public,
        role_contract_path=root / ROLE.relative_to(ROOT),
        eval_contract_path=root
        / "data/projects/open_model_data/evidence/correction_protection_evaluation_contract_v1.json",
        coverage_contract_path=root
        / "data/projects/open_model_data/evidence/correction_protection_coverage_contract_v1.json",
        near_dup_policy_path=root / POLICY.relative_to(ROOT),
        schema_path=root / SCHEMA.relative_to(ROOT),
        skip_source_freeze_git_binding=True,
    )
    return private, public


def _verify_fixture_artifacts(root: Path, private: Path, public: Path, *, require_private: bool = True) -> dict:
    return heldout.verify_artifacts(
        root=root,
        private_dir=private,
        public_dir=public,
        schema_path=root / SCHEMA.relative_to(ROOT),
        role_contract_path=root / ROLE.relative_to(ROOT),
        eval_contract_path=root
        / "data/projects/open_model_data/evidence/correction_protection_evaluation_contract_v1.json",
        coverage_contract_path=root
        / "data/projects/open_model_data/evidence/correction_protection_coverage_contract_v1.json",
        near_dup_policy_path=root / POLICY.relative_to(ROOT),
        sources_db=root / "data/sources.db",
        source_universe=root / "data/projects/open_model_data/evidence/source_universe_v1",
        require_private=require_private,
        skip_source_freeze_git_binding=True,
    )


def test_schema_is_draft_2020_12_and_has_stable_id() -> None:
    schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
    Draft202012Validator.check_schema(schema)
    assert schema["$id"].endswith("phase3_heldout_partition_bundle_v1.schema.json")
    for name in (
        "inputBindings",
        "heldoutSealReceipt",
        "authorClearanceReceipt",
        "publicReceipt",
        "partitionVerificationReceipt",
        "leakageVerificationReceipt",
        "bundle",
    ):
        assert name in schema["$defs"]


def test_document_identity_collapses_layers() -> None:
    left = heldout.document_identity_for_ua_gec("docA")
    right = heldout.document_identity_for_ua_gec("docA")
    assert left == right
    assert left != heldout.document_identity_for_ua_gec("docB")


def test_reconstruction_preserves_empty_source_lang_and_rejects_non_strings(tmp_path: Path) -> None:
    def reconstruct(source_lang: object, index: int) -> dict[str, object]:
        db_path = tmp_path / f"sources-{index}.db"
        with sqlite3.connect(db_path) as connection:
            connection.execute(
                "CREATE TABLE ua_gec_errors (id INTEGER PRIMARY KEY, error TEXT, correct TEXT, error_type TEXT, "
                "doc_id TEXT, annotator_id TEXT, partition TEXT, is_native INTEGER, source_lang TEXT)"
            )
            connection.execute(
                "INSERT INTO ua_gec_errors VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (1, "synthetic error", "synthetic correction", "G/Case", "doc", "annotator", "gec/train", 1, source_lang),
            )
        payload = {
            "id": 1,
            "error": "synthetic error",
            "correct": "synthetic correction",
            "error_type": "G/Case",
            "doc_id": "doc",
            "annotator_id": "annotator",
            "partition": "gec/train",
            "is_native": 1,
            "source_lang": source_lang if isinstance(source_lang, str) else "",
        }
        return heldout.reconstruct_ua_gec_rows(
            sources_db=db_path,
            freeze_units=[_unit_for_row(1, ordinal=1, payload=payload)],
        )[0]

    empty = reconstruct("", 1)
    assert empty["source_lang"] == ""
    assert empty["source_record"]["source_lang"] == ""
    assert empty["unit_sha256"] == freeze_mod._unit_hash(empty["source_record"])
    assert reconstruct("fr-CA", 2)["source_record"]["source_lang"] == "fr-CA"

    for index, invalid in enumerate((None, b"invalid"), start=3):
        with pytest.raises(heldout.PartitionError, match="source_lang malformed"):
            reconstruct(invalid, index)


def test_deterministic_partition_and_public_receipt_constraints(tmp_path: Path) -> None:
    root = _build_fixture_root(tmp_path)
    private = root / "batch_state/open-model-data/phase3-heldout"
    public = root / "data/projects/open_model_data/evidence/phase3_heldout_partition_v1"
    first = heldout.build_artifacts(
        root=root,
        source_universe=root / "data/projects/open_model_data/evidence/source_universe_v1",
        sources_db=root / "data/sources.db",
        private_dir=private,
        public_dir=public,
        role_contract_path=root / ROLE.relative_to(ROOT),
        eval_contract_path=root
        / "data/projects/open_model_data/evidence/correction_protection_evaluation_contract_v1.json",
        coverage_contract_path=root
        / "data/projects/open_model_data/evidence/correction_protection_coverage_contract_v1.json",
        near_dup_policy_path=root / POLICY.relative_to(ROOT),
        schema_path=root / SCHEMA.relative_to(ROOT),
        skip_source_freeze_git_binding=True,
    )
    public_bytes_before_reconstruction_metadata_rerun = (public / "public_receipt_v1.json").read_bytes()
    second = heldout.build_artifacts(
        root=root,
        source_universe=root / "data/projects/open_model_data/evidence/source_universe_v1",
        sources_db=root / "data/sources.db",
        private_dir=private,
        public_dir=public,
        role_contract_path=root / ROLE.relative_to(ROOT),
        eval_contract_path=root
        / "data/projects/open_model_data/evidence/correction_protection_evaluation_contract_v1.json",
        coverage_contract_path=root
        / "data/projects/open_model_data/evidence/correction_protection_coverage_contract_v1.json",
        near_dup_policy_path=root / POLICY.relative_to(ROOT),
        schema_path=root / SCHEMA.relative_to(ROOT),
        skip_source_freeze_git_binding=True,
    )
    assert first["public_receipt_sha256"] == second["public_receipt_sha256"]
    assert (public / "public_receipt_v1.json").read_bytes() == public_bytes_before_reconstruction_metadata_rerun
    assert first["heldout_seal_sha256"] == second["heldout_seal_sha256"]
    assert first["author_clearance_sha256"] == second["author_clearance_sha256"]

    seal = heldout.read_json(private / "heldout_seal_v1.json")
    author = heldout.read_json(private / "author_clearance_v1.json")
    public_receipt = heldout.read_json(public / "public_receipt_v1.json")

    heldout_ids = {item["unit_id"] for item in seal["sealed_units"]}
    author_ids = {item["unit_id"] for item in author["cleared_units"]}
    assert heldout_ids.isdisjoint(author_ids)
    assert all(item["split"] == "test" for item in seal["sealed_units"])
    # Cross-layer docA collapses: two test rows, one document identity.
    doc_ids = {item["source_document_identity"] for item in seal["sealed_units"]}
    assert seal["sealed_unit_count"] == 3
    assert len(doc_ids) == 2
    assert seal["text_free"] is False
    for item in seal["sealed_units"]:
        assert isinstance(item["error"], str)
        assert isinstance(item["correct"], str)
        assert item["locator"]["kind"] == "sqlite_row"
        assert item["locator"]["table"] == "ua_gec_errors"
        assert item["error_span_fingerprint_sha256"] == near.fingerprint(item["error"]).exact_fingerprint
        assert item["correct_span_fingerprint_sha256"] == near.fingerprint(item["correct"]).exact_fingerprint
        assert item["sources_db_sha256"] == heldout.sha256_file(root / "data/sources.db")
        assert item["near_duplicate_policy_fingerprint_sha256"] == near.PINNED_POLICY_FINGERPRINT
        assert item["unit_sha256"]
    assert author["text_free"] is True
    assert author["heldout_excluded"] is True
    assert author["ua_eval_exclusion_enforced"] is True
    assert author["public_canary_exclusion_enforced"] is True
    assert author["input_bindings"]["evaluation_contract_sha256"]
    assert author["input_bindings"]["coverage_contract_sha256"]
    assert "error" not in author["cleared_units"][0]
    assert "locator" not in author["cleared_units"][0]
    assert "source_document_identity" not in author["cleared_units"][0]

    # /test never cleared; row 7 (eval id) and canary/near neighbours omitted.
    assert first["aggregates"]["author_cleared_unit_total"] == 2
    assert author["cleared_unit_count"] == 2
    assert "source_document_identity" not in author["cleared_units"][0]

    heldout._assert_no_forbidden_public_fields(public_receipt)
    assert public_receipt["capability"]["state"] == "NOT_YET_LABELLED_OR_ACTIVATED"
    assert public_receipt["zero_overlap"]["test_excluded_from_author_clearance"] is True
    assert public_receipt["role_binding"]["controller_identity_id"] == heldout.CONTROLLER_IDENTITY
    assert public_receipt["role_binding"]["artifact_task_id"] == heldout.ARTIFACT_TASK_ID
    assert public_receipt["role_binding"]["attestation_task_id"] == heldout.ATTESTATION_TASK_ID
    body = public / "public_receipt_v1.json"
    assert "alpha beta" not in body.read_text(encoding="utf-8")

    verified = heldout.verify_artifacts(
        root=root,
        private_dir=private,
        public_dir=public,
        schema_path=root / SCHEMA.relative_to(ROOT),
        role_contract_path=root / ROLE.relative_to(ROOT),
        sources_db=root / "data/sources.db",
        source_universe=root / "data/projects/open_model_data/evidence/source_universe_v1",
        require_private=True,
        skip_source_freeze_git_binding=True,
    )
    assert verified["ok"] is True
    assert verified["private_verified"] is True


def test_private_seal_tamper_byte_locator_fingerprint_fail(tmp_path: Path) -> None:
    root = _build_fixture_root(tmp_path)
    private = root / "batch_state/open-model-data/phase3-heldout"
    public = root / "data/projects/open_model_data/evidence/phase3_heldout_partition_v1"
    heldout.build_artifacts(
        root=root,
        source_universe=root / "data/projects/open_model_data/evidence/source_universe_v1",
        sources_db=root / "data/sources.db",
        private_dir=private,
        public_dir=public,
        role_contract_path=root / ROLE.relative_to(ROOT),
        eval_contract_path=root
        / "data/projects/open_model_data/evidence/correction_protection_evaluation_contract_v1.json",
        coverage_contract_path=root
        / "data/projects/open_model_data/evidence/correction_protection_coverage_contract_v1.json",
        near_dup_policy_path=root / POLICY.relative_to(ROOT),
        schema_path=root / SCHEMA.relative_to(ROOT),
        skip_source_freeze_git_binding=True,
    )
    seal_path = private / "heldout_seal_v1.json"
    public_path = public / "public_receipt_v1.json"
    original_seal = heldout.read_json(seal_path)
    original_public = heldout.read_json(public_path)

    def _restore() -> None:
        heldout.write_private_json(seal_path, original_seal)
        heldout.write_public_json(public_path, original_public)

    def _rewrite(mutator) -> None:
        payload = heldout.read_json(seal_path)
        mutator(payload)
        rewritten = heldout.attach_receipt_hash(payload)
        heldout.write_private_json(seal_path, rewritten)
        public_receipt = heldout.read_json(public_path)
        public_receipt["artifact_hashes"]["heldout_seal_sha256"] = rewritten["receipt_sha256"]
        heldout.write_public_json(public_path, heldout.attach_receipt_hash(public_receipt))

    def _expect_fail(match: str) -> None:
        with pytest.raises(heldout.PartitionError, match=match):
            heldout.verify_artifacts(
                root=root,
                private_dir=private,
                public_dir=public,
                schema_path=root / SCHEMA.relative_to(ROOT),
                role_contract_path=root / ROLE.relative_to(ROOT),
                sources_db=root / "data/sources.db",
                source_universe=root / "data/projects/open_model_data/evidence/source_universe_v1",
                require_private=True,
                skip_source_freeze_git_binding=True,
            )

    _rewrite(
        lambda payload: payload["sealed_units"].__setitem__(
            0,
            {
                **payload["sealed_units"][0],
                "error": payload["sealed_units"][0]["error"] + "x",
            },
        )
    )
    _expect_fail(r"sealed error byte drift")
    _restore()

    _rewrite(
        lambda payload: payload["sealed_units"].__setitem__(
            0,
            {
                **payload["sealed_units"][0],
                "locator": {
                    **payload["sealed_units"][0]["locator"],
                    "primary_key_sha256": "0" * 64,
                },
            },
        )
    )
    _expect_fail(r"sealed locator drift")
    _restore()

    _rewrite(
        lambda payload: payload["sealed_units"].__setitem__(
            0,
            {
                **payload["sealed_units"][0],
                "error_span_fingerprint_sha256": "1" * 64,
            },
        )
    )
    _expect_fail(r"sealed error fingerprint drift")
    _restore()

    # Schema requires custody fields when text_free is false.
    incomplete = dict(original_seal)
    incomplete["sealed_units"] = [
        {
            key: value
            for key, value in original_seal["sealed_units"][0].items()
            if key
            not in {
                "error",
                "correct",
                "locator",
                "error_span_fingerprint_sha256",
                "correct_span_fingerprint_sha256",
                "sources_db_sha256",
                "near_duplicate_policy_fingerprint_sha256",
            }
        }
    ]
    incomplete = heldout.attach_receipt_hash(incomplete)
    with pytest.raises(heldout.PartitionError, match=r"schema validation failed"):
        heldout._schema_validate(
            incomplete,
            heldout.read_json(root / SCHEMA.relative_to(ROOT)),
            "heldoutSealReceipt",
        )


def test_public_receipt_rejects_arbitrary_ascii_after_rehash(tmp_path: Path) -> None:
    root = _build_fixture_root(tmp_path)
    private, public = _build_fixture_artifacts(root)
    public_path = public / "public_receipt_v1.json"
    receipt = heldout.read_json(public_path)
    receipt["capability"]["shortfalls"][0]["detail"] = "arbitrary ascii source prose"
    heldout.write_public_json(public_path, heldout.attach_receipt_hash(receipt))
    with pytest.raises(heldout.PartitionError, match="unapproved string"):
        _verify_fixture_artifacts(root, private, public, require_private=False)


def test_role_contract_duplicate_controller_and_steward_permission_drift_fail() -> None:
    role_contract = heldout.read_json(ROLE)
    duplicate = json.loads(json.dumps(role_contract))
    label_seat = next(seat for seat in duplicate["seats"] if seat["role_id"] == "heldout_label_reviewer")
    label_seat["controller_identity_id"] = heldout.CONTROLLER_IDENTITY
    with pytest.raises(heldout.PartitionError, match="reuse a controller identity"):
        heldout.verify_role_binding(duplicate)

    weakened = json.loads(json.dumps(role_contract))
    steward = next(seat for seat in weakened["seats"] if seat["role_id"] == heldout.ROLE_ID)
    steward["must_not"].remove("extract_rules")
    with pytest.raises(heldout.PartitionError, match="prohibited functions drift"):
        heldout.verify_role_binding(weakened)


def test_private_permissions_are_verified_for_directory_and_every_artifact(tmp_path: Path) -> None:
    root = _build_fixture_root(tmp_path)
    private, public = _build_fixture_artifacts(root)
    private.chmod(0o755)
    with pytest.raises(heldout.PartitionError, match="directory permissions too open"):
        _verify_fixture_artifacts(root, private, public)

    private.chmod(0o700)
    partition_path = private / "partition_verification_v1.json"
    partition_path.chmod(0o644)
    with pytest.raises(heldout.PartitionError, match="private artifact permissions too open: partition"):
        _verify_fixture_artifacts(root, private, public)


def test_partition_leakage_and_public_aggregate_evidence_cannot_be_retargeted(tmp_path: Path) -> None:
    root = _build_fixture_root(tmp_path)
    private, public = _build_fixture_artifacts(root)
    public_path = public / "public_receipt_v1.json"
    partition_path = private / "partition_verification_v1.json"
    leakage_path = private / "leakage_verification_v1.json"
    original_public = heldout.read_json(public_path)
    original_partition = heldout.read_json(partition_path)
    original_leakage = heldout.read_json(leakage_path)

    public_receipt = json.loads(json.dumps(original_public))
    public_receipt["aggregates"]["ua_gec_input_total"] += 1
    public_receipt["aggregates"]["author_omitted_unit_total"] += 1
    heldout.write_public_json(public_path, heldout.attach_receipt_hash(public_receipt))
    with pytest.raises(heldout.PartitionError, match="public aggregates differ from private evidence"):
        _verify_fixture_artifacts(root, private, public)

    heldout.write_public_json(public_path, original_public)
    partition = json.loads(json.dumps(original_partition))
    partition["ua_gec_input_total"] += 1
    partition["author_omitted_unit_total"] += 1
    partition["omit_reason_totals"]["retargeted"] = 1
    partition = heldout.attach_receipt_hash(partition)
    heldout.write_private_json(partition_path, partition)
    public_receipt = json.loads(json.dumps(original_public))
    public_receipt["artifact_hashes"]["partition_verification_sha256"] = partition["receipt_sha256"]
    public_receipt["aggregates"]["ua_gec_input_total"] += 1
    public_receipt["aggregates"]["author_omitted_unit_total"] += 1
    public_receipt["aggregates"]["omit_reason_code_count"] += 1
    heldout.write_public_json(public_path, heldout.attach_receipt_hash(public_receipt))
    with pytest.raises(
        heldout.PartitionError,
        match="partition omit reasons differ from live exclusion-safe partition",
    ):
        _verify_fixture_artifacts(root, private, public)

    heldout.write_private_json(partition_path, original_partition)
    heldout.write_public_json(public_path, original_public)
    leakage = json.loads(json.dumps(original_leakage))
    leakage["near_duplicate_policy_fingerprint_sha256"] = "0" * 64
    leakage = heldout.attach_receipt_hash(leakage)
    heldout.write_private_json(leakage_path, leakage)
    public_receipt = json.loads(json.dumps(original_public))
    public_receipt["artifact_hashes"]["leakage_verification_sha256"] = leakage["receipt_sha256"]
    heldout.write_public_json(public_path, heldout.attach_receipt_hash(public_receipt))
    with pytest.raises(heldout.PartitionError, match="leakage policy fingerprint drift"):
        _verify_fixture_artifacts(root, private, public)


def test_verify_recomputes_author_clearance_and_live_contract_bindings(tmp_path: Path) -> None:
    root = _build_fixture_root(tmp_path)
    private, public = _build_fixture_artifacts(root)
    author_path = private / "author_clearance_v1.json"
    partition_path = private / "partition_verification_v1.json"
    public_path = public / "public_receipt_v1.json"

    live_rows = heldout.reconstruct_ua_gec_rows(
        sources_db=root / "data/sources.db",
        freeze_units=heldout._load_freeze_ua_gec_units(
            root / "data/projects/open_model_data/evidence/source_universe_v1"
        ),
    )
    excluded = next(row for row in live_rows if row["row_id"] == 7)
    author = heldout.read_json(author_path)
    author["cleared_units"].append(
        {
            "unit_id": excluded["unit_id"],
            "unit_sha256": excluded["unit_sha256"],
            "family_id": heldout.UA_GEC_FAMILY,
        }
    )
    author["cleared_units"].sort(key=lambda item: item["unit_id"])
    author["cleared_unit_count"] += 1
    author = heldout.attach_receipt_hash({key: value for key, value in author.items() if key != "receipt_sha256"})
    heldout.write_private_json(author_path, author)

    partition = heldout.read_json(partition_path)
    partition["author_cleared_unit_total"] += 1
    partition["author_omitted_unit_total"] -= 1
    partition["omit_reason_totals"]["ua_eval_row_identity"] -= 1
    partition = heldout.attach_receipt_hash({key: value for key, value in partition.items() if key != "receipt_sha256"})
    heldout.write_private_json(partition_path, partition)

    public_receipt = heldout.read_json(public_path)
    public_receipt["artifact_hashes"]["author_clearance_sha256"] = author["receipt_sha256"]
    public_receipt["artifact_hashes"]["partition_verification_sha256"] = partition["receipt_sha256"]
    public_receipt["aggregates"]["author_cleared_unit_total"] += 1
    public_receipt["aggregates"]["author_omitted_unit_total"] -= 1
    public_receipt = heldout.attach_receipt_hash(
        {key: value for key, value in public_receipt.items() if key != "receipt_sha256"}
    )
    heldout.write_public_json(public_path, public_receipt)
    with pytest.raises(
        heldout.PartitionError,
        match="author clearance differs from live exclusion-safe partition",
    ):
        _verify_fixture_artifacts(root, private, public)

    _build_fixture_artifacts(root)
    eval_contract = root / "data/projects/open_model_data/evidence/correction_protection_evaluation_contract_v1.json"
    eval_contract.write_text(eval_contract.read_text(encoding="utf-8") + "\n", encoding="utf-8")
    with pytest.raises(heldout.PartitionError, match="evaluation-contract hash drift"):
        _verify_fixture_artifacts(root, private, public)


def test_malformed_comparison_fail_closed_and_source_drift(tmp_path: Path) -> None:
    policy = near.load_policy(POLICY)
    unit = {
        "row_id": 1,
        "source_document_identity": "doc.x",
        "error": None,
        "correct": "ok",
    }
    excluded, reason = heldout.unit_conflicts_with_exclusions(
        unit,
        exact_fingerprints=set(),
        exclusion_surfaces=[],
        exclusion_fps=[],
        token_index={},
        excluded_row_hashes=set(),
        excluded_doc_identities=set(),
        policy=policy,
    )
    assert excluded is True
    assert reason == "malformed_comparison"

    root = _build_fixture_root(tmp_path)
    # Drift: delete a freeze unit line so reconstruction fails closed.
    units = root / "data/projects/open_model_data/evidence/source_universe_v1/ua_gec.units.jsonl"
    lines = units.read_text(encoding="utf-8").splitlines()
    units.write_text("\n".join(lines[:-1]) + "\n", encoding="utf-8")
    with pytest.raises(heldout.PartitionError, match=r"row count drifts|missing"):
        heldout.build_artifacts(
            root=root,
            source_universe=root / "data/projects/open_model_data/evidence/source_universe_v1",
            sources_db=root / "data/sources.db",
            private_dir=root / "batch_state/open-model-data/phase3-heldout",
            public_dir=root / "data/projects/open_model_data/evidence/phase3_heldout_partition_v1",
            role_contract_path=root / ROLE.relative_to(ROOT),
            eval_contract_path=root
            / "data/projects/open_model_data/evidence/correction_protection_evaluation_contract_v1.json",
            coverage_contract_path=root
            / "data/projects/open_model_data/evidence/correction_protection_coverage_contract_v1.json",
            near_dup_policy_path=root / POLICY.relative_to(ROOT),
            schema_path=root / SCHEMA.relative_to(ROOT),
            skip_source_freeze_git_binding=True,
        )


def test_cli_build_verify_smoke(tmp_path: Path) -> None:
    root = _build_fixture_root(tmp_path)
    code = heldout.main(
        [
            "--root",
            str(root),
            "--source-universe",
            str(root / "data/projects/open_model_data/evidence/source_universe_v1"),
            "--sources-db",
            str(root / "data/sources.db"),
            "--private-dir",
            str(root / "batch_state/open-model-data/phase3-heldout"),
            "--public-dir",
            str(root / "data/projects/open_model_data/evidence/phase3_heldout_partition_v1"),
            "--schema",
            str(root / SCHEMA.relative_to(ROOT)),
            "build",
            "--skip-source-freeze-git-binding",
        ]
    )
    assert code == 0
    code = heldout.main(
        [
            "--root",
            str(root),
            "--source-universe",
            str(root / "data/projects/open_model_data/evidence/source_universe_v1"),
            "--sources-db",
            str(root / "data/sources.db"),
            "--private-dir",
            str(root / "batch_state/open-model-data/phase3-heldout"),
            "--public-dir",
            str(root / "data/projects/open_model_data/evidence/phase3_heldout_partition_v1"),
            "--schema",
            str(root / SCHEMA.relative_to(ROOT)),
            "verify",
            "--skip-source-freeze-git-binding",
        ]
    )
    assert code == 0
    code = heldout.main(
        [
            "--root",
            str(root),
            "--private-dir",
            str(root / "batch_state/open-model-data/phase3-heldout"),
            "--public-dir",
            str(root / "data/projects/open_model_data/evidence/phase3_heldout_partition_v1"),
            "--schema",
            str(root / SCHEMA.relative_to(ROOT)),
            "verify",
            "--public-only",
        ]
    )
    assert code == 0
