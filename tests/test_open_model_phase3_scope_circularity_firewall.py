"""Hostile contract tests for the #7427 held-out / Cycle007 firewall."""

from __future__ import annotations

import json
import os
from copy import deepcopy
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator

from scripts.projects.open_model_data import freeze_phase3_scope_circularity_firewall as firewall


def _record(*, namespace: str = "independent", origin: str = "independent", candidate: str = "a") -> dict[str, str]:
    return {"candidate_id": candidate, "origin": origin, "namespace": namespace, "membership_sha256": "a" * 64, "component_sha256": "b" * 64, "independent_origin": "true"}


def _private_config(root: Path, name: str = "config.json") -> Path:
    root.mkdir(parents=True, exist_ok=True)
    os.chmod(root, 0o700)
    path = root / name
    value = {
        "schema_version": "phase3_evaluation_steward_config_v1",
        "private_root": str(root),
        "content_pack_directory": str(root / "content-pack"),
        "steward_output_root": str(root / "steward-output"),
        "steward_role": "evaluation_steward",
    }
    value["config_sha256"] = firewall._config_hash(value)
    path.write_text(json.dumps(value), encoding="utf-8")
    os.chmod(path, 0o600)
    return path


def test_generated_contract_is_exact_and_schema_valid() -> None:
    contract = firewall.build_contract()
    assert firewall.validate_contract_integrity(contract)
    schema = json.loads((firewall.DATA / "contracts/phase3_scope_circularity_firewall_v1.schema.json").read_text())
    Draft202012Validator(schema).validate(contract)
    assert contract["denominator"]["coverage_blocked_cells"] == 14
    assert contract["cycle007"]["private_binding_state"] == "UNBOUND"


def test_schema_rejects_nested_extra_missing_and_frozen_drift() -> None:
    contract = firewall.build_contract()
    schema = json.loads((firewall.DATA / "contracts/phase3_scope_circularity_firewall_v1.schema.json").read_text())
    validator = Draft202012Validator(schema)
    extra = deepcopy(contract)
    extra["cycle007"]["unexpected"] = True
    missing = deepcopy(contract)
    del missing["private_runtime"]["rejects"]
    drift = deepcopy(contract)
    drift["denominator"]["source_units"] = 58
    assert list(validator.iter_errors(extra)) and list(validator.iter_errors(missing)) and list(validator.iter_errors(drift))


@pytest.mark.parametrize("namespace", firewall.DENY_NAMESPACES)
def test_every_cycle007_deny_namespace_is_terminal_and_never_derives(namespace: str) -> None:
    called = 0

    def derive(_: object) -> None:
        nonlocal called
        called += 1

    result = firewall.validate_lineage_batch([_record(namespace=namespace)], derive=derive)
    assert result == {"ok": False, "code": "leakage", "emitted": 0, "promoted": 0, "activated": 0}
    assert called == 0


def test_duplicate_and_cycle007_concept_cannot_call_derivation() -> None:
    called = 0

    def derive(_: object) -> None:
        nonlocal called
        called += 1

    duplicate = firewall.validate_lineage_batch([_record(), _record(candidate="a")], derive=derive)
    cycle = firewall.validate_lineage_batch([_record(origin="cycle007")], derive=derive)
    assert duplicate["code"] == "leakage"
    assert cycle["code"] == "leakage"
    assert called == 0


def test_clearance_is_positive_only_and_rehashed_outer_receipt_cannot_bypass() -> None:
    contract = firewall.build_contract()
    clearance = {"p1_sha256": firewall.PINS[firewall.P1], "p1_amendment_sha256": firewall.PINS[firewall.P1_AMENDMENT], "p2_sha256": firewall.PINS[firewall.P2], "near_duplicate_policy_sha256": firewall.PINS[firewall.NEAR_POLICY], "firewall_sha256": firewall.sha256_file(firewall.OUTPUT)}
    assert firewall.validate_builder_clearance(clearance, contract)
    assert not firewall.validate_builder_clearance({**clearance, "membership": "a" * 64}, contract)
    assert not firewall.validate_builder_clearance({**clearance, "near_duplicate_policy_sha256": "0" * 64}, contract)
    assert firewall.validate_lineage_batch([_record(namespace="prompts")])["emitted"] == 0


def test_same_count_pack_or_row_commitment_mutation_fails() -> None:
    manifest = {"schema_version": firewall.storage.PACK_SCHEMA_VERSION, "pack_kind": "content_compact", "receipt_sha256": firewall.EXPECTED_PACK_MANIFEST_RECEIPT_SHA256, "object_set_sha256": firewall.EXPECTED_OBJECT_SET_SHA256, "ordered_row_identity_commitment_sha256": firewall.EXPECTED_ORDERED_ROW_IDENTITY_SHA256, "packet_count": 204, "row_count": 10159, "object_count": 419}
    inventory = {"packet_count": 204, "row_count": 10159, "object_count": 419, "sidecar_count": 408, "object_set_sha256": firewall.EXPECTED_OBJECT_SET_SHA256, "ordered_row_identity_commitment_sha256": firewall.EXPECTED_ORDERED_ROW_IDENTITY_SHA256}
    assert not firewall.validate_pack_commitments(manifest, inventory)
    assert not firewall.validate_pack_commitments({**manifest, "object_set_sha256": "0" * 64}, inventory)
    assert not firewall.validate_pack_commitments(manifest, {**inventory, "ordered_row_identity_commitment_sha256": "0" * 64})


def test_private_runtime_rejects_caller_hashes_and_unsafe_config_paths(tmp_path: Path) -> None:
    root = tmp_path / "private"
    config = _private_config(root)
    assert firewall.run_steward_production(str(config))["ok"] is False
    forged = json.loads(config.read_text())
    forged["membership_sha256"] = "a" * 64
    forged["component_graph_sha256"] = "b" * 64
    config.write_text(json.dumps(forged), encoding="utf-8")
    os.chmod(config, 0o600)
    assert firewall.run_steward_production(str(config))["code"] == "private_path_unsafe"
    config = _private_config(root)
    os.chmod(config, 0o644)
    assert firewall.run_steward_production(str(config))["code"] == "private_path_unsafe"
    os.chmod(config, 0o600)
    hard = root / "hard.json"
    os.link(config, hard)
    assert firewall.run_steward_production(str(hard))["code"] == "private_path_unsafe"
    hard.unlink()
    link = root / "link.json"
    link.symlink_to(config)
    assert firewall.run_steward_production(str(link))["code"] == "private_path_unsafe"


def test_production_fixture_uses_only_content_compact_pack_and_writes_private_graph(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    root = tmp_path / "private"
    pack = root / "content-pack"
    output = root / "steward-output"
    for path in (root, pack, output):
        path.mkdir(parents=True, exist_ok=True)
        os.chmod(path, 0o700)
    objects = [{"role_relative_path": f"object-{index}", "role_relative_paths": [f"object-{index}", f"alias-{index}"] if index < 205 else [f"object-{index}"], "selection_class": "materialization_manifest", "selection_classes": ["materialization_manifest"]} for index in range(419)]
    manifest = firewall.storage._receipt({"schema_version": firewall.storage.PACK_SCHEMA_VERSION, "pack_kind": "content_compact", "packet_count": 204, "row_count": 10159, "object_count": 419, "object_set_sha256": firewall.EXPECTED_OBJECT_SET_SHA256, "ordered_row_identity_commitment_sha256": firewall.EXPECTED_ORDERED_ROW_IDENTITY_SHA256, "inventory_receipt_sha256": "a" * 64, "content_bodies_stored": True, "objects": objects})
    (pack / "pack-manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
    os.chmod(pack / "pack-manifest.json", 0o600)
    config = {"schema_version": "phase3_evaluation_steward_config_v1", "private_root": str(root), "content_pack_directory": str(pack), "steward_output_root": str(output), "steward_role": "evaluation_steward"}
    config["config_sha256"] = firewall._config_hash(config)
    config_path = root / "config.json"
    config_path.write_text(json.dumps(config), encoding="utf-8")
    os.chmod(config_path, 0o600)
    monkeypatch.setattr(firewall, "validate_pack_commitments", lambda *_: True)
    monkeypatch.setattr(firewall.storage, "prove_content_pack_stream", lambda *_: ({}, {}))
    monkeypatch.setattr(firewall, "_build_private_deny_corpus", lambda *_: {"corpus_sha256": "b" * 64})
    result = firewall.run_steward_production(str(config_path))
    assert result["ok"] is True
    assert (output / "cycle007-deny-component-manifest-v1.json").stat().st_mode & 0o777 == 0o600
    assert json.loads((output / "cycle007-firewall-run-state-v1.json").read_text())["state"] == "COMPLETE"
    assert firewall.evaluate_steward_candidates([], str(config_path))["code"] == "uncertain_lineage"


def test_unbound_and_graph_incomplete_batches_fail_with_zero_outputs() -> None:
    assert firewall.validate_private_runtime_binding(None)["code"] == "private_binding_unbound"
    result = firewall.validate_lineage_batch([{"candidate_id": "missing"}])
    assert result == {"ok": False, "code": "graph_incompleteness", "emitted": 0, "promoted": 0, "activated": 0}


def test_candidate_evaluator_rejects_caller_collision_and_cycle_derivative() -> None:
    row = {"row": "a" * 64, "source_example": "b" * 64, "document_or_edition": "c" * 64, "exact": "d" * 64, "token_hashes": "e" * 64, "component": "f" * 64, "packet": "0" * 64}
    corpus = {"schema_version": "phase3_cycle007_private_deny_corpus_v1", "pack_manifest_receipt_sha256": firewall.EXPECTED_PACK_MANIFEST_RECEIPT_SHA256, "near_duplicate_policy_sha256": firewall.near.pinned_policy_fingerprint(), "rows": [row]}
    corpus["corpus_sha256"] = firewall.sha256_bytes(firewall.canonical_json(corpus))
    assert firewall.evaluate_candidate_batch([{"evaluation_cycle_id": "phase3-v2-1-evaluation-cycle-007"}], corpus)["code"] == "uncertain_lineage"
    assert firewall.evaluate_candidate_batch([{"unit_id": "x"}], corpus)["code"] == "uncertain_lineage"


def _private_candidate_corpus(candidate: dict[str, object]) -> dict[str, object]:
    arrays = {name: [] for name in firewall.PRIVATE_DENY_ARRAYS}
    commitments = {name: {"count": 0, "sha256": firewall.sha256_bytes(firewall.canonical_json([]))} for name in firewall.ALL_DENY_ARRAYS}
    corpus: dict[str, object] = {
        "schema_version": "phase3_cycle007_private_deny_corpus_v1",
        "pack_manifest_receipt_sha256": firewall.EXPECTED_PACK_MANIFEST_RECEIPT_SHA256,
        "near_duplicate_policy_sha256": firewall.near.pinned_policy_fingerprint(),
        "deny_arrays": arrays, "namespace_commitments": commitments, "rows": [],
        "candidate_clearance_allowlist": [], "candidate_clearance_commitment_sha256": firewall.sha256_bytes(firewall.canonical_json([])),
    }
    corpus["corpus_sha256"] = firewall.sha256_bytes(firewall.canonical_json(corpus))
    return corpus


def test_candidate_requires_private_clearance_and_every_lineage_namespace_is_denied() -> None:
    document = firewall.materialization._identity("pravopys_2026_complete", {}, {"locator": {}})
    lineage = {name: None for name in firewall.CANDIDATE_LINEAGE_KEYS}
    candidate: dict[str, object] = {"evaluation_cycle_id": "other", "family_id": "pravopys_2026_complete", "unit_id": "candidate", "unit_sha256": "a" * 64, "source_text": "novel independent text", "source_record": {}, "source_locator": {}, "document_or_edition_identity": document, "lineage": lineage}
    corpus = _private_candidate_corpus(candidate)
    assert firewall.evaluate_candidate_batch([candidate], corpus)["code"] == "uncertain_lineage"
    for lineage_key, namespace in {
        "packet": "packet", "sidecar": "sidecar", "annotation": "annotation", "label_or_prompt": "prompt_or_request",
        "paraphrase_parent": "paraphrase_parent", "synthetic_parent": "synthetic_parent", "derivative_parent": "derivative",
        "provenance_receipt": "labeling_receipt", "raw_or_log": "raw_or_log", "provider_result_terminal": "provider_result_terminal",
    }.items():
        value = "b" * 64
        changed = deepcopy(candidate)
        changed["lineage"] = {**lineage, lineage_key: value}
        collision = _private_candidate_corpus(changed)
        if namespace == "packet":
            row = {"row": "a" * 64, "source_example": "b" * 64, "document_or_edition": "c" * 64, "packet": value, "exact": "d" * 64, "component": "e" * 64, "normalized_surface": "separate"}
            collision["rows"] = [row]
            for name, identity in {"row": row["row"], "source_example": row["source_example"], "document_work_edition": row["document_or_edition"], "packet": row["packet"], "exact": row["exact"], "component": row["component"]}.items():
                collision["namespace_commitments"][name] = {"count": 1, "sha256": firewall.sha256_bytes(firewall.canonical_json([identity]))}  # type: ignore[index]
        else:
            collision["deny_arrays"][namespace] = [value]  # type: ignore[index]
            collision["namespace_commitments"][namespace] = {"count": 1, "sha256": firewall.sha256_bytes(firewall.canonical_json([value]))}  # type: ignore[index]
        collision["corpus_sha256"] = firewall.sha256_bytes(firewall.canonical_json({key: value for key, value in collision.items() if key != "corpus_sha256"}))
        assert firewall.evaluate_candidate_batch([changed], collision)["code"] == "leakage"


def test_row_derived_deny_sets_are_reconstructed_without_private_array_copies() -> None:
    candidate = {"evaluation_cycle_id": "other"}
    corpus = _private_candidate_corpus(candidate)
    row = {"row": "a" * 64, "source_example": "b" * 64, "document_or_edition": "c" * 64, "packet": "d" * 64, "exact": "e" * 64, "component": "f" * 64}
    corpus["rows"] = [row]
    for name, value in {"row": row["row"], "source_example": row["source_example"], "document_work_edition": row["document_or_edition"], "packet": row["packet"], "exact": row["exact"], "component": row["component"]}.items():
        corpus["namespace_commitments"][name] = {"count": 1, "sha256": firewall.sha256_bytes(firewall.canonical_json([value]))}  # type: ignore[index]
    corpus["corpus_sha256"] = firewall.sha256_bytes(firewall.canonical_json({key: value for key, value in corpus.items() if key != "corpus_sha256"}))
    denied = firewall._validate_private_deny_corpus(corpus)
    assert denied["row"] == {"a" * 64} and denied["packet"] == {"d" * 64}
    assert "row" not in corpus["deny_arrays"]  # type: ignore[operator]


def test_concept_authority_gate_requires_pinned_human_registry_and_rejects_renamed_derivative() -> None:
    allowed = {"kind": "authority_citation", "origin_kind": "independent", "concept_or_citation_id": "external_authority", "authority_sha256": "a" * 64}
    assert firewall.admit_concept_or_authority(allowed) == {"ok": False, "code": "unregistered_authority", "emitted": 0, "promoted": 0, "activated": 0}
    rejected = {"kind": "abstract_concept", "origin_kind": "independent", "concept_or_citation_id": "rehash", "authority_sha256": "a" * 64, "membership": "b" * 64}
    assert firewall.admit_concept_or_authority(rejected)["code"] == "leakage"


def test_compact_row_identity_uses_source_locator_for_every_family() -> None:
    row = {"family_id": "pravopys_2026_complete", "unit_id": "unit", "unit_sha256": "a" * 64, "source_locator": {}, "source_text": "x", "source_text_sha256": firewall.sha256_bytes(b"x"), "source_record": {}, "materialization_projection": "clean_label"}
    assert firewall._canonical_packed_document_identity(row).startswith("document_or_edition.pravopys_2026_complete")
    unknown = {**row, "family_id": "unmapped_family"}
    with pytest.raises(firewall.FirewallError):
        firewall._canonical_packed_document_identity(unknown)


def _labeling_receipt(schema: str, index: int) -> dict[str, object]:
    common = {
        "evaluation_cycle_id": "phase3-v2-1-evaluation-cycle-007",
        "lane": "clean_label",
        "packet_index": index + 1,
        "chunk_index": 1,
        "attempt": 1,
        "request_plan_sha256": f"{index + 1:064x}",
        "request_byte_budget": 524288,
        "request_byte_count": 7,
        "text_free": True,
    }
    if schema == "phase3_cycle007_gemini_attempt_v2":
        terminal = index < 2
        if not terminal:
            return common | {
                "schema_version": schema, "state": "started", "exact_model": "Gemini 3.6 Flash (High)",
                "model_family": "google", "harness": "agy",
            }
        return common | {
            "schema_version": schema, "state": "terminal", "exact_model": "Gemini 3.6 Flash (High)",
            "model_family": "google", "harness": "agy", "failure_code": "provider_status_timeout",
            "failure_stage": "provider_return", "provider_call_started": True,
            "executable_binding_result": "verified", "provider_return_code": "nonzero",
            "raw_byte_count": 11, "raw_sha256": f"{index + 10:064x}",
            "log_byte_count": 7, "log_sha256": f"{index + 20:064x}",
            "init_count": 1, "result_count": 1,
            "first_event_kind": "init", "last_event_kind": "result", "model_binding_result": "verified",
            "result_status": "non_success", "structured_output_type": "missing",
            "elapsed_milliseconds": 1,
        }
    if schema == "phase3_cycle007_gemini_pre_call_v1":
        return {
            "schema_version": schema, **common, "planner_version": "v1", "row_count": 1,
            "estimated_input_tokens_ceiling": 1, "ordered_identity_sha256": f"{index + 30:064x}",
            "receipt_sha256": f"{index + 40:064x}",
        }
    if schema == "phase3_cycle007_gemini_request_plan_v1":
        return {
            "schema_version": schema, "evaluation_cycle_id": common["evaluation_cycle_id"], "lane": "clean_label",
            "packet_index": 7, "planner_version": "v1", "request_byte_budget": 524288, "row_count": 1,
            "packet_identity_set_sha256": "a" * 64, "label_prompt_sha256": "b" * 64,
            "chunks": [{"chunk_index": 1, "row_start": 1, "row_end": 1, "row_count": 1,
                        "request_byte_count": 7, "estimated_input_tokens_ceiling": 1,
                        "ordered_identity_sha256": "c" * 64}], "text_free": True, "plan_sha256": "d" * 64,
        }
    assert schema == "phase3_cycle007_gemini_provider_stop_v3"
    return {
        "schema_version": schema, "evaluation_cycle_id": common["evaluation_cycle_id"], "lane": "clean_label",
        "terminal_packet_index": 7, "failure_code": "provider_status_timeout", "new_provider_calls_allowed": False,
        "exact_model": "Gemini 3.6 Flash (High)", "model_family": "google", "harness": "agy", "text_free": True,
        "failure_stage": "provider_return", "provider_call_started": True, "executable_binding_result": "verified",
        "provider_return_code": "nonzero", "raw_byte_count": 1, "raw_sha256": "e" * 64,
        "log_byte_count": 1, "log_sha256": "f" * 64, "init_count": 1, "result_count": 1,
        "first_event_kind": "init", "last_event_kind": "result", "model_binding_result": "verified",
        "result_status": "non_success", "structured_output_type": "missing", "chunk_index": 1, "attempt": 1,
        "terminal_marker_sha256": "1" * 64, "request_plan_sha256": "2" * 64, "request_byte_budget": 524288,
        "request_byte_count": 7, "elapsed_milliseconds": 0,
    }


def test_exact_labeling_receipt_census_is_populated_deny_lineage(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    schemas = (
        ["phase3_cycle007_gemini_attempt_v2"] * 4
        + ["phase3_cycle007_gemini_pre_call_v1"] * 2
        + ["phase3_cycle007_gemini_request_plan_v1"]
        + ["phase3_cycle007_gemini_provider_stop_v3"]
    )
    receipt_bytes: dict[str, bytes] = {}
    objects: list[dict[str, object]] = []
    for index, schema in enumerate(schemas):
        payload = _labeling_receipt(schema, index)
        path = f"objects/{index}.json"
        receipt_bytes[path] = json.dumps(payload).encode()
        objects.append({"object_relative_path": path, "storage": "raw", "sha256": f"{index + 45:064x}", "selection_classes": ["labeling_expansion"]})

    monkeypatch.setattr(firewall.storage, "_iter_stored_raw_chunks", lambda path, *_: iter([receipt_bytes[path.relative_to(tmp_path).as_posix()]]))
    identities, census = firewall._labeling_expansion_identities(tmp_path, {"objects": objects})
    assert set(identities) == {"labeling_receipt", "prompt_or_request", "raw_or_log", "provider_result_terminal", "derivative"}
    assert all(len(values) == 8 for values in identities.values())
    assert identities["labeling_receipt"] == sorted(f"{index + 45:064x}" for index in range(8))
    assert census == {
        "schema_counts": firewall.LABELING_RECEIPT_SCHEMA_COUNTS,
        "historical_provider_attempts": 3,
        "historical_result_receipts": 3,
        "historical_raw_log_receipts": 3,
        "bodies_available": False,
    }
    drift = json.loads(receipt_bytes["objects/0.json"])
    drift["result_count"] = 0
    receipt_bytes["objects/0.json"] = json.dumps(drift).encode()
    with pytest.raises(firewall.FirewallError, match="graph_incompleteness"):
        firewall._labeling_expansion_identities(tmp_path, {"objects": objects})


def test_labeling_receipt_census_rejects_drift_or_body_payload(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    schemas = ["phase3_cycle007_gemini_attempt_v2"] * 4 + ["phase3_cycle007_gemini_pre_call_v1"] * 2 + ["phase3_cycle007_gemini_request_plan_v1", "phase3_cycle007_gemini_provider_stop_v3"]
    objects = [{"object_relative_path": f"objects/{index}.json", "storage": "raw", "sha256": f"{index:064x}", "selection_classes": ["labeling_expansion"]} for index in range(8)]
    payloads = {f"objects/{index}.json": json.dumps(_labeling_receipt(schema, index) | ({"raw_payload": "body"} if index == 0 else {})).encode() for index, schema in enumerate(schemas)}
    monkeypatch.setattr(firewall.storage, "_iter_stored_raw_chunks", lambda path, *_: iter([payloads[path.relative_to(tmp_path).as_posix()]]))
    with pytest.raises(firewall.FirewallError, match="graph_incompleteness"):
        firewall._labeling_expansion_identities(tmp_path, {"objects": objects})
    drift_schemas = [*schemas]
    drift_schemas[-1] = "phase3_cycle007_gemini_attempt_v2"
    payloads = {f"objects/{index}.json": json.dumps(_labeling_receipt(schema, index)).encode() for index, schema in enumerate(drift_schemas)}
    with pytest.raises(firewall.FirewallError, match="graph_incompleteness"):
        firewall._labeling_expansion_identities(tmp_path, {"objects": objects})
