"""Hermetic tests for the private Phase 3 rule-author packet compiler."""

from __future__ import annotations

import copy
import json
import subprocess
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator

from scripts.projects.open_model_data import phase3_rule_author_packets as packets


def _write(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, ensure_ascii=False, separators=(",", ":"), sort_keys=True) + "\n", encoding="utf-8"
    )


def _jsonl(path: Path, rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "".join(json.dumps(row, ensure_ascii=False, separators=(",", ":"), sort_keys=True) + "\n" for row in rows),
        encoding="utf-8",
    )


def _role_contract() -> dict[str, object]:
    def seat(role: str, controller: str, must_not: list[str] | None = None) -> dict[str, object]:
        return {
            "seat_id": f"seat_{role}",
            "role_id": role,
            "assignment_state": "assigned_verified",
            "controller_identity_id": controller,
            "controller_identity_attested": True,
            "must_not": must_not or [],
        }

    def binding(role: str, controller: str, task: str) -> dict[str, object]:
        return {
            "role_id": role,
            "controller_identity_id": controller,
            "reserved_task_id": task,
            "status": "identity_attested_pre_artifact",
        }

    return {
        "seats": [
            seat("heldout_steward", "controller_phase3_heldout_steward_cursor_runtime_01"),
            seat("rule_author_extractor", "controller_author", ["read_heldout_text_locators_fingerprints_labels"]),
            seat("ukrainian_source_reviewer", "controller_reviewer"),
        ],
        "task_bindings": [
            binding(
                "heldout_steward",
                "controller_phase3_heldout_steward_cursor_runtime_01",
                "phase3-role-heldout-steward-cursor-v2",
            ),
            binding("rule_author_extractor", "controller_author", "author-task"),
            binding("ukrainian_source_reviewer", "controller_reviewer", "review-task"),
        ],
        "heldout_acl": {
            "pre_release_read_roles": ["heldout_steward", "heldout_label_reviewer"],
            "post_release_scorer_roles": ["scorer"],
            "forbidden_roles": ["rule_author_extractor", "ukrainian_source_reviewer"],
        },
    }


def _clearance(
    receipt_sha: str, evaluation_sha: str, coverage_sha: str, role_sha: str, units: list[dict[str, str]]
) -> dict[str, object]:
    value: dict[str, object] = {
        "schema_version": "phase3_author_clearance_receipt_v1",
        "text_free": True,
        "implementation_version": "phase3_heldout_partition_v1",
        "role_binding": {
            "role_id": "heldout_steward",
            "seat_id": "seat_heldout_steward",
            "controller_identity_id": "controller_phase3_heldout_steward_cursor_runtime_01",
            "attestation_task_id": "phase3-role-heldout-steward-cursor-v2",
            "artifact_task_id": "phase3-heldout-partition-seal-cursor-v1",
        },
        "input_bindings": {
            "combined_contract_sha256": packets.COMBINED_CONTRACT_SHA256,
            "role_contract_sha256": role_sha,
            "evaluation_contract_sha256": evaluation_sha,
            "coverage_contract_sha256": coverage_sha,
            "source_universe_receipt_sha256": receipt_sha,
            "near_duplicate_policy_fingerprint_sha256": packets.near_duplicate.PINNED_POLICY_FINGERPRINT,
            "ua_eval_exclusion_manifest_sha256": "2" * 64,
            "public_canary_exclusion_manifest_sha256": "3" * 64,
        },
        "cleared_units": units,
        "cleared_unit_count": len(units),
        "heldout_excluded": True,
        "ua_eval_exclusion_enforced": True,
        "public_canary_exclusion_enforced": True,
        "heldout_complement_encoded": False,
        "fingerprints_encoded": False,
        "locators_encoded": False,
    }
    value["receipt_sha256"] = packets.receipt_body_sha256(value)
    return value


def _source_record(
    row_id: int,
    *,
    error: str,
    correct: str,
    error_type: str,
    doc_id: str = "shared-doc",
    partition: str = "gec-only/train",
) -> dict[str, object]:
    return {
        "id": row_id,
        "error": error,
        "correct": correct,
        "error_type": error_type,
        "doc_id": doc_id,
        "annotator_id": "fixture-annotator",
        "partition": partition,
        "is_native": 1,
        "source_lang": "uk",
    }


def _source_row(record: dict[str, object]) -> dict[str, object]:
    normalized = packets.source_universe._normal(record)
    unit_id = packets.source_universe._opaque_id(
        "unit.ua_gec", {"table": "ua_gec_errors", "identity": {"id": normalized["id"]}}
    )
    return {
        "family_id": "ua_gec",
        "unit_id": unit_id,
        "unit_sha256": packets.source_universe._unit_hash(normalized),
        "source_locator": {"kind": "sqlite_row", "table": "ua_gec_errors", "id": normalized["id"]},
        "source_text": normalized["error"],
        "corrected_text": normalized["correct"],
        "source_record": normalized,
    }


def _fixture(
    tmp_path: Path,
    *,
    records: list[dict[str, object]] | None = None,
    rows: list[dict[str, object]] | None = None,
) -> dict[str, Path]:
    universe = tmp_path / "universe"
    records = records or [
        _source_record(1, error="synthetic source span one", correct="synthetic correction one", error_type="F"),
        _source_record(2, error="synthetic source span two", correct="synthetic correction two", error_type="Calque"),
    ]
    source_rows = rows or [_source_row(record) for record in records]
    units = [
        {
            "family_id": row["family_id"],
            "unit_id": row["unit_id"],
            "unit_sha256": row["unit_sha256"],
        }
        for row in source_rows
    ]
    by_family: dict[str, list[dict[str, object]]] = {"ua_gec": units}
    family_receipts = []
    for family, family_units in by_family.items():
        ledger = universe / f"{family}.units.jsonl"
        _jsonl(ledger, family_units)
        family_receipts.append(
            {"family_id": family, "ledger_file": ledger.name, "ledger_sha256": packets.sha256_file(ledger)}
        )
    receipt = {
        "schema_version": "phase3_source_universe_freeze_v1",
        "text_free": True,
        "merged_main_sha": "0" * 40,
        "families": family_receipts,
    }
    receipt_path = universe / packets.LEDGER_RECEIPT
    _write(receipt_path, receipt)
    evaluation = {
        "heldout_access": {"author_extractor_forbidden": True},
        "near_duplicate_policy": {"policy_fingerprint_sha256": packets.near_duplicate.PINNED_POLICY_FINGERPRINT},
    }
    evaluation_path = tmp_path / "evaluation.json"
    _write(evaluation_path, evaluation)
    coverage_path = tmp_path / "coverage.json"
    _write(coverage_path, {"schema_version": "synthetic_coverage_v1"})
    role_path = tmp_path / "role.json"
    _write(role_path, _role_contract())
    clearance_path = tmp_path / "clearance.json"
    clearance = _clearance(
        packets.sha256_file(receipt_path),
        packets.sha256_file(evaluation_path),
        packets.sha256_file(coverage_path),
        packets.sha256_file(role_path),
        units,
    )
    _write(clearance_path, clearance)
    source_path = tmp_path / "sources.jsonl"
    _jsonl(source_path, source_rows)
    return {
        "universe": universe,
        "evaluation": evaluation_path,
        "coverage": coverage_path,
        "role": role_path,
        "clearance": clearance_path,
        "sources": source_path,
        "output": tmp_path / "batch_state" / "packets.json",
    }


def _build(paths: dict[str, Path], output: Path | None = None) -> dict[str, object]:
    return packets.build(
        clearance_path=paths["clearance"],
        source_universe_dir=paths["universe"],
        sources_path=paths["sources"],
        evaluation_path=paths["evaluation"],
        coverage_path=paths["coverage"],
        role_path=paths["role"],
        output_path=output or paths["output"],
    )


def _verify(paths: dict[str, Path], **kwargs: Path) -> dict[str, object]:
    return packets.verify(
        bundle_path=paths["output"],
        clearance_path=paths["clearance"],
        source_universe_dir=paths["universe"],
        sources_path=paths["sources"],
        evaluation_path=paths["evaluation"],
        coverage_path=paths["coverage"],
        role_path=paths["role"],
        **kwargs,
    )


def test_bundle_is_deterministic_private_and_cross_layer_doc_identity_collapses(tmp_path: Path) -> None:
    paths = _fixture(tmp_path)
    first = _build(paths)
    second_path = tmp_path / "batch_state" / "repeat.json"
    second = _build(paths, second_path)
    assert first == second
    assert paths["output"].read_bytes() == second_path.read_bytes()
    ua = [item for packet in first["packets"] for item in packet["items"] if item["family_id"] == "ua_gec"]
    assert len({item["source_document_identity"] for item in ua}) == 1
    assert _verify(paths)["ok"] is True


def test_document_identity_uses_hash_verified_normalized_record(tmp_path: Path) -> None:
    records = [
        _source_record(
            1,
            error="synthetic source span one",
            correct="synthetic correction one",
            error_type="F",
            doc_id="café",
        ),
        _source_record(
            2,
            error="synthetic source span two",
            correct="synthetic correction two",
            error_type="Calque",
            doc_id="café",
        ),
    ]
    source_rows = [_source_row(record) for record in records]
    source_rows[1]["source_record"]["doc_id"] = "cafe\u0301"
    paths = _fixture(tmp_path, records=records, rows=source_rows)

    bundle = _build(paths)
    identities = {
        item["source_document_identity"]
        for packet in bundle["packets"]
        for item in packet["items"]
    }
    assert len(identities) == 1


def test_source_lang_empty_maps_to_packet_sentinel_without_rewriting_nonempty_value(tmp_path: Path) -> None:
    empty = _source_record(
        1,
        error="synthetic source span one",
        correct="synthetic correction one",
        error_type="F",
    )
    empty["source_lang"] = ""
    nonempty = _source_record(
        2,
        error="synthetic source span two",
        correct="synthetic correction two",
        error_type="Calque",
    )
    nonempty["source_lang"] = "fr-CA"
    paths = _fixture(tmp_path, records=[empty, nonempty])

    bundle = _build(paths)
    metadata_by_text = {
        item["source_text"]: item["metadata"]["source_lang"]
        for packet in bundle["packets"]
        for item in packet["items"]
    }
    assert metadata_by_text == {
        "synthetic source span one": "unknown",
        "synthetic source span two": "fr-CA",
    }


def test_raw_unknown_source_lang_fails_closed_to_prevent_packet_sentinel_collision(tmp_path: Path) -> None:
    record = _source_record(
        1,
        error="synthetic source span one",
        correct="synthetic correction one",
        error_type="F",
    )
    record["source_lang"] = "unknown"
    paths = _fixture(tmp_path, records=[record])

    with pytest.raises(packets.PacketCompilerError, match="packet sentinel"):
        _build(paths)


def test_clearance_is_exact_not_a_complement_and_frozen_units_cannot_drift(tmp_path: Path) -> None:
    paths = _fixture(tmp_path)
    clearance = json.loads(paths["clearance"].read_text(encoding="utf-8"))
    clearance["cleared_units"] = clearance["cleared_units"][:-1]
    clearance["cleared_unit_count"] = len(clearance["cleared_units"])
    clearance["receipt_sha256"] = packets.receipt_body_sha256(clearance)
    _write(paths["clearance"], clearance)
    with pytest.raises(packets.PacketCompilerError, match="not explicitly cleared"):
        _build(paths)
    paths = _fixture(tmp_path / "tamper")
    rows = [json.loads(line) for line in paths["sources"].read_text(encoding="utf-8").splitlines()]
    rows[0]["unit_sha256"] = "d" * 64
    _jsonl(paths["sources"], rows)
    with pytest.raises(packets.PacketCompilerError, match="source record does not reproduce frozen unit hash"):
        _build(paths)


def test_verify_readmits_sources_against_clearance_and_frozen_ledger(tmp_path: Path) -> None:
    paths = _fixture(tmp_path)
    _build(paths)
    rows = [json.loads(line) for line in paths["sources"].read_text(encoding="utf-8").splitlines()]
    rows[0]["source_record"]["error"] = "substituted after compilation"
    rows[0]["source_text"] = "substituted after compilation"
    _jsonl(paths["sources"], rows)
    with pytest.raises(packets.PacketCompilerError, match="source record does not reproduce frozen unit hash"):
        _verify(paths)

    paths = _fixture(tmp_path / "record-tamper")
    rows = [json.loads(line) for line in paths["sources"].read_text(encoding="utf-8").splitlines()]
    rows[0]["source_record"]["correct"] = "retargeted correction"
    rows[0]["corrected_text"] = "retargeted correction"
    _jsonl(paths["sources"], rows)
    with pytest.raises(packets.PacketCompilerError, match="source record does not reproduce frozen unit hash"):
        _build(paths)


def test_runtime_is_ua_gec_only_until_other_families_receive_steward_clearance() -> None:
    assert frozenset({"ua_gec"}) == packets.AUTHOR_FAMILIES
    with pytest.raises(packets.PacketCompilerError, match="non-author family"):
        packets._item_from_row(
            {
                "family_id": "calque_inventory",
                "unit_id": "unit.calque.fixture",
                "unit_sha256": "a" * 64,
                "source_text": "fixture",
                "source_locator": "fixture",
            },
            "b" * 64,
            packets.near_duplicate.PINNED_POLICY_FINGERPRINT,
        )


def test_steward_receipt_body_and_bindings_are_not_retargetable_or_legacy(tmp_path: Path) -> None:
    paths = _fixture(tmp_path)
    receipt = json.loads(paths["clearance"].read_text(encoding="utf-8"))
    receipt["input_bindings"]["evaluation_contract_sha256"] = "f" * 64
    receipt["receipt_sha256"] = packets.receipt_body_sha256(receipt)
    _write(paths["clearance"], receipt)
    with pytest.raises(packets.PacketCompilerError, match="evaluation-contract binding drift"):
        _build(paths)
    paths = _fixture(tmp_path / "legacy")
    _write(paths["clearance"], {"schema_version": "phase3_rule_author_clearance_v1", "authorized_units": []})
    with pytest.raises(packets.PacketCompilerError, match="schema violation"):
        _build(paths)


@pytest.mark.parametrize("field", ["heldout_access", "near_duplicate_policy"])
def test_malformed_nested_evaluation_contract_fails_closed(tmp_path: Path, field: str) -> None:
    paths = _fixture(tmp_path)
    evaluation = json.loads(paths["evaluation"].read_text(encoding="utf-8"))
    evaluation[field] = None
    _write(paths["evaluation"], evaluation)
    clearance = json.loads(paths["clearance"].read_text(encoding="utf-8"))
    clearance["input_bindings"]["evaluation_contract_sha256"] = packets.sha256_file(paths["evaluation"])
    clearance["receipt_sha256"] = packets.receipt_body_sha256(clearance)
    _write(paths["clearance"], clearance)

    with pytest.raises(packets.PacketCompilerError, match=f"evaluation contract {field} is malformed"):
        _build(paths)


def test_heldout_prohibition_is_checked_on_the_assigned_rule_author_seat(tmp_path: Path) -> None:
    paths = _fixture(tmp_path)
    role = json.loads(paths["role"].read_text(encoding="utf-8"))
    assigned = next(seat for seat in role["seats"] if seat["role_id"] == "rule_author_extractor")
    assigned["must_not"] = []
    role["seats"].insert(
        0,
        {
            **assigned,
            "seat_id": "seat_rule_author_extractor_revoked",
            "assignment_state": "revoked",
            "controller_identity_attested": False,
            "must_not": ["read_heldout_text_locators_fingerprints_labels"],
        },
    )
    _write(paths["role"], role)
    clearance = json.loads(paths["clearance"].read_text(encoding="utf-8"))
    clearance["input_bindings"]["role_contract_sha256"] = packets.sha256_file(paths["role"])
    clearance["receipt_sha256"] = packets.receipt_body_sha256(clearance)
    _write(paths["clearance"], clearance)

    with pytest.raises(packets.PacketCompilerError, match="heldout prohibition drift"):
        _build(paths)


@pytest.mark.parametrize(
    ("field", "match"),
    [
        ("bundle_policy", "bundle near-duplicate policy binding drift"),
        ("packet_policy", "packet near-duplicate policy binding drift"),
        ("packet_clearance", "packet clearance binding drift"),
        ("packet_query", "packet query-plan binding drift"),
    ],
)
def test_verify_rejects_tampered_bundle_and_packet_pins(tmp_path: Path, field: str, match: str) -> None:
    paths = _fixture(tmp_path)
    bundle = _build(paths)
    if field == "bundle_policy":
        bundle["near_duplicate_policy_fingerprint_sha256"] = "f" * 64
    elif field == "packet_policy":
        bundle["packets"][0]["near_duplicate_policy_fingerprint_sha256"] = "f" * 64
    elif field == "packet_clearance":
        bundle["packets"][0]["clearance_sha256"] = "f" * 64
    else:
        bundle["packets"][0]["query_plan_sha256"] = "f" * 64
    _write(paths["output"], bundle)

    with pytest.raises(packets.PacketCompilerError, match=match):
        _verify(paths)


def test_rejects_test_ua_eval_canary_and_malformed_rows(tmp_path: Path) -> None:
    for field, value, reason in (
        ("source_record.partition", "gec-only/test", "test unit"),
        ("ua_eval", True, "evaluation"),
        ("ua_eval", "false", "evaluation"),
        ("public_canary_neighbour", True, "evaluation"),
        ("public_canary_neighbour", 0, "evaluation"),
    ):
        paths = _fixture(tmp_path / field.replace(".", "-"))
        rows = [json.loads(line) for line in paths["sources"].read_text(encoding="utf-8").splitlines()]
        if field == "source_record.partition":
            rows[0]["source_record"]["partition"] = value
        else:
            rows[0][field] = value
        _jsonl(paths["sources"], rows)
        with pytest.raises(packets.PacketCompilerError, match=reason):
            _build(paths)
    paths = _fixture(tmp_path / "bad-span")
    rows = [json.loads(line) for line in paths["sources"].read_text(encoding="utf-8").splitlines()]
    rows[0]["span_end"] = 999
    _jsonl(paths["sources"], rows)
    with pytest.raises(packets.PacketCompilerError, match="invalid exact source span"):
        _build(paths)


def test_packet_caps_and_oversize_singleton_preserve_source(tmp_path: Path) -> None:
    oversize_text = "x" * (packets.MAX_UTF8_BYTES + 1)
    records = [
        _source_record(1, error=oversize_text, correct="synthetic correction one", error_type="F"),
        _source_record(2, error="synthetic source span two", correct="synthetic correction two", error_type="Calque"),
    ]
    paths = _fixture(tmp_path, records=records)
    bundle = _build(paths)
    oversize = next(packet for packet in bundle["packets"] if packet["oversize_singleton"])
    assert len(oversize["items"]) == 1
    assert oversize["items"][0]["source_text"] == oversize_text
    assert oversize["byte_count"] > packets.MAX_UTF8_BYTES
    assert all(len(packet["items"]) <= packets.MAX_ITEMS for packet in bundle["packets"])


def test_verify_rejects_oversize_marker_on_multi_item_packet(tmp_path: Path) -> None:
    records = [
        _source_record(
            1,
            error="x" * 120_000,
            correct="synthetic correction one",
            error_type="F",
            doc_id="doc-one",
        ),
        _source_record(
            2,
            error="y" * 120_000,
            correct="synthetic correction two",
            error_type="Calque",
            doc_id="doc-two",
        ),
    ]
    paths = _fixture(tmp_path, records=records)
    bundle = _build(paths)
    assert len(bundle["packets"]) == 2
    packet = bundle["packets"][0]
    packet["items"] = [item for source_packet in bundle["packets"] for item in source_packet["items"]]
    packet["byte_count"] = packets._packet_byte_count(packet["items"])
    packet["oversize_singleton"] = True
    bundle["packets"] = [packet]
    _write(paths["output"], bundle)

    with pytest.raises(packets.PacketCompilerError, match="oversize-singleton marker drift"):
        _verify(paths)


def test_overall_review_decision_fails_closed_for_mixed_outcomes() -> None:
    assert packets._overall_review_decision([{"decision": "accepted"}]) == "accepted"
    assert packets._overall_review_decision([{"decision": "rejected"}]) == "rejected"
    assert packets._overall_review_decision([{"decision": "revise"}]) == "revise"
    assert packets._overall_review_decision([{"decision": "accepted"}, {"decision": "rejected"}]) == "revise"


def test_packet_item_and_per_document_caps_are_deterministic(tmp_path: Path) -> None:
    paths = _fixture(tmp_path)
    bundle = _build(paths)
    template = bundle["packets"][0]["items"][0]
    textbook_items = []
    for ordinal in range(5):
        item = copy.deepcopy(template)
        item["family_id"] = "school_textbooks"
        item["source_item_id"] = f"rule_author_source:{ordinal:064x}"
        textbook_items.append(item)
    packet_list = packets._pack(textbook_items, "0" * 64, packets.near_duplicate.PINNED_POLICY_FINGERPRINT, "1" * 64)
    assert [len(packet["items"]) for packet in packet_list] == [4, 1]
    literal_items = [copy.deepcopy(template) for _ in range(packets.MAX_ITEMS + 1)]
    for ordinal, item in enumerate(literal_items):
        item["family_id"] = "calque_inventory"
        item["source_document_identity"] = f"calque_inventory_document:{ordinal:064x}"
        item["source_item_id"] = f"rule_author_source:{ordinal:064x}"
    assert [
        len(packet["items"])
        for packet in packets._pack(literal_items, "0" * 64, packets.near_duplicate.PINNED_POLICY_FINGERPRINT, "1" * 64)
    ] == [24, 1]


def test_role_separation_and_response_review_schema_closure(tmp_path: Path) -> None:
    paths = _fixture(tmp_path)
    clearance = json.loads(paths["clearance"].read_text(encoding="utf-8"))
    clearance["role_binding"]["controller_identity_id"] = "controller_author"
    clearance["receipt_sha256"] = packets.receipt_body_sha256(clearance)
    _write(paths["clearance"], clearance)
    with pytest.raises(
        packets.PacketCompilerError, match=r"schema violation|role contract does not bind|must be distinct"
    ):
        _build(paths)
    paths = _fixture(tmp_path / "response")
    bundle = _build(paths)
    packet = bundle["packets"][0]
    item = packet["items"][0]
    response = {
        "schema_version": "phase3_rule_author_response_v1",
        "authority_state": "non_authoritative_model_proposal",
        "author": {
            "role_id": "rule_author_extractor",
            "controller_identity_id": "controller_author",
            "provider": "fixture",
            "model_family": "fixture",
            "harness": "fixture",
            "exact_model": "fixture",
            "task_id": "author-task",
        },
        "packet_sha256": packets.sha256_bytes(packets.canonical_json(packet).encode("utf-8")),
        "prompt_sha256": "1" * 64,
        "raw_response_sha256": "2" * 64,
        "parse_state": "parsed",
        "limitations": [],
        "abstentions": [],
        "proposals": [
            {
                "proposal_id": "fixture-proposal",
                "source_item_id": item["source_item_id"],
                "source_span": item["source_span"],
                "primary_source_role": "explicit_rule",
                "secondary_source_roles": [],
                "claim_type": "unresolved",
                "phenomenon": "fixture",
                "mechanism": "syntax",
                "matcher": {
                    "kind": "syntax",
                    "tokens": [{"pos": "NOUN", "features": {"Case": "Nom"}}],
                    "dependency_constraints": [{"head": 0, "dependent": 0, "relation": "root"}],
                    "abstention": ["insufficient_evidence"],
                },
                "incorrect_pattern": "fixture",
                "replacements": [],
                "scope": "fixture",
                "exceptions": [],
                "controls": [],
                "protections": [],
                "abstentions": ["insufficient_evidence"],
                "evidence_refs": [],
                "consumer_views": [],
                "dissent_or_alternatives": [],
            }
        ],
    }
    response_path = tmp_path / "batch_state" / "response.json"
    _write(response_path, response)
    canonical_rule = copy.deepcopy(response["proposals"][0])
    proposal_decision = {
        "proposal_id": canonical_rule["proposal_id"],
        "decision": "revise",
        "source_role_decision": {
            "primary": canonical_rule["primary_source_role"],
            "secondary": canonical_rule["secondary_source_roles"],
        },
        "claim_type_decision": canonical_rule["claim_type"],
        "phenomenon_decision": canonical_rule["phenomenon"],
        "mechanism_decision": canonical_rule["mechanism"],
        "support_decision": "unresolved",
        "locator_decision": "exact_sufficient",
        "canonical_reviewed_rule": canonical_rule,
        "canonical_reviewed_rule_sha256": packets.sha256_bytes(packets.canonical_json(canonical_rule).encode("utf-8")),
        "reasons": ["fixture"],
    }
    review = {
        "schema_version": "phase3_ukrainian_rule_review_decision_v1",
        "reviewer": {
            "role_id": "ukrainian_source_reviewer",
            "controller_identity_id": "controller_reviewer",
            "task_id": "review-task",
        },
        "reviewed_payload_sha256": packets.sha256_file(response_path),
        "canonical_reviewed_payload_sha256": packets.sha256_bytes(
            packets.canonical_json([proposal_decision]).encode("utf-8")
        ),
        "decision": "revise",
        "proposal_decisions": [proposal_decision],
        "reasons": ["fixture"],
    }
    review_path = tmp_path / "batch_state" / "review.json"
    _write(review_path, review)
    assert (
        _verify(
            paths,
            response_path=response_path,
            review_path=review_path,
        )["review_verified"]
        is True
    )
    broken = copy.deepcopy(response)
    broken["proposals"][0]["matcher"] = {"kind": "syntax", "pattern": "not-executable", "abstention": ["x"]}
    with pytest.raises(packets.PacketCompilerError, match="schema violation"):
        packets.validate(broken, "ruleAuthorResponse", "response")

    unbound = copy.deepcopy(response)
    unbound["proposals"][0]["source_item_id"] = "rule_author_source:" + "f" * 64
    unbound_path = tmp_path / "batch_state" / "unbound-response.json"
    _write(unbound_path, unbound)
    with pytest.raises(packets.PacketCompilerError, match="does not bind a source item"):
        _verify(paths, response_path=unbound_path)

    duplicate = copy.deepcopy(response)
    duplicate["proposals"].append(copy.deepcopy(duplicate["proposals"][0]))
    duplicate_path = tmp_path / "batch_state" / "duplicate-response.json"
    _write(duplicate_path, duplicate)
    with pytest.raises(packets.PacketCompilerError, match="duplicate proposal IDs"):
        _verify(paths, response_path=duplicate_path)

    missing = copy.deepcopy(review)
    missing["proposal_decisions"] = []
    missing["canonical_reviewed_payload_sha256"] = packets.sha256_bytes(b"[]")
    missing_path = tmp_path / "batch_state" / "missing-review.json"
    _write(missing_path, missing)
    with pytest.raises(packets.PacketCompilerError, match="decide every proposal exactly once"):
        _verify(
            paths,
            response_path=response_path,
            review_path=missing_path,
        )

    retargeted = copy.deepcopy(review)
    retargeted_rule = retargeted["proposal_decisions"][0]["canonical_reviewed_rule"]
    retargeted_rule["source_item_id"] = "rule_author_source:" + "f" * 64
    retargeted["proposal_decisions"][0]["canonical_reviewed_rule_sha256"] = packets.sha256_bytes(
        packets.canonical_json(retargeted_rule).encode("utf-8")
    )
    retargeted["canonical_reviewed_payload_sha256"] = packets.sha256_bytes(
        packets.canonical_json(retargeted["proposal_decisions"]).encode("utf-8")
    )
    retargeted_path = tmp_path / "batch_state" / "retargeted-review.json"
    _write(retargeted_path, retargeted)
    with pytest.raises(packets.PacketCompilerError, match="retargets"):
        _verify(
            paths,
            response_path=response_path,
            review_path=retargeted_path,
        )


def test_schema_is_draft_2020_12_and_no_packet_output_may_escape_batch_state(tmp_path: Path) -> None:
    schema = json.loads(packets.SCHEMA_PATH.read_text(encoding="utf-8"))
    Draft202012Validator.check_schema(schema)
    assert schema["additionalProperties"] is False
    assert "clearance" not in schema["$defs"]
    canonical = json.loads(packets.CLEARANCE_SCHEMA_PATH.read_text(encoding="utf-8"))
    Draft202012Validator.check_schema(canonical)
    assert "authorClearanceReceipt" in canonical["$defs"]
    assert all(
        "$id" in schema["$defs"][name] for name in ("packet", "sourceItem", "ruleAuthorResponse", "reviewDecision")
    )
    paths = _fixture(tmp_path)
    with pytest.raises(packets.PacketCompilerError, match="batch_state"):
        _build(paths, tmp_path / "tracked-packets.json")


def test_cli_synthetic_build_and_verify_smoke(tmp_path: Path) -> None:
    paths = _fixture(tmp_path)
    project_root = packets.ROOT if (packets.ROOT / ".venv" / "bin" / "python").is_file() else packets.ROOT.parents[3]
    executable = project_root / ".venv" / "bin" / "python"
    build = subprocess.run(
        [
            str(executable),
            "-m",
            "scripts.projects.open_model_data.phase3_rule_author_packets",
            "build",
            "--clearance",
            str(paths["clearance"]),
            "--source-universe-dir",
            str(paths["universe"]),
            "--sources",
            str(paths["sources"]),
            "--evaluation-contract",
            str(paths["evaluation"]),
            "--coverage-contract",
            str(paths["coverage"]),
            "--role-contract",
            str(paths["role"]),
            "--output",
            str(paths["output"]),
        ],
        cwd=packets.ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    assert build.returncode == 0, build.stdout
    verify = subprocess.run(
        [
            str(executable),
            "-m",
            "scripts.projects.open_model_data.phase3_rule_author_packets",
            "verify",
            "--bundle",
            str(paths["output"]),
            "--clearance",
            str(paths["clearance"]),
            "--source-universe-dir",
            str(paths["universe"]),
            "--sources",
            str(paths["sources"]),
            "--evaluation-contract",
            str(paths["evaluation"]),
            "--coverage-contract",
            str(paths["coverage"]),
            "--role-contract",
            str(paths["role"]),
        ],
        cwd=packets.ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    assert verify.returncode == 0, verify.stdout
    assert json.loads(verify.stdout)["ok"] is True
