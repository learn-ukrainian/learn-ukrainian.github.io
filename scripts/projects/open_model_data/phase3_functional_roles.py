#!/usr/bin/env python3
"""Validate the Phase 3 v2.1 task-scoped functional-role ledger.

The ledger separates conflicting actions by concrete task identity. Provider,
model, harness, and natural-person identity are audit metadata, not the unit of
independence. This module makes no linguistic, label, score, or audit decision.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from collections.abc import Mapping
from pathlib import Path
from typing import Any

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parents[3]
DATA = ROOT / "data/projects/open_model_data"
SCHEMA_PATH = DATA / "contracts/correction_protection_functional_role_contract_v2_1.schema.json"
LEDGER_PATH = DATA / "evidence/correction_protection_functional_role_contract_v2_1.json"
BASE_SHA256 = "298591094d1281629ea444707909b679d1a5368f3ad8afddf39120bc0c34532b"
AMENDMENT_SHA256 = "ae36a961318b2a0a494837314929efd9849b4e6a6fa299b3d8dde17261777f5b"
COMBINED_SHA256 = "2f3ef840325d917b9f2763188627ad69d1b4e45b804860499a134586b112a907"

ROLE_TASKS = {
    "scope_circularity_critic": "phase3-v2-1-scope-circularity-review",
    "ukrainian_source_reviewer": "phase3-v2-1-ukrainian-source-review",
    "rule_author_extractor": "phase3-v2-1-rule-author-extraction",
    "heldout_steward": "phase3-v2-1-heldout-stewardship",
    "heldout_label_reviewer": "phase3-v2-1-heldout-label-review",
    "scorer": "phase3-v2-1-heldout-scoring",
    "outsider_reproducer": "phase3-v2-1-outsider-reproduction",
    "cross_family_code_infra_reviewer": "phase3-v2-1-code-infra-review",
    "disposition_auditor": "phase3-v2-1-disposition-audit",
    "textbook_nonhit_auditor": "phase3-v2-1-textbook-nonhit-audit",
}

ROLE_EXECUTION = {
    "scope_circularity_critic": {"exact_model": "composer-2.5", "model_family": "cursor", "harness": "cursor", "capability_class": "contract_scope_review"},
    "ukrainian_source_reviewer": {"exact_model": "grok-4.5", "model_family": "xai", "harness": "opencode", "capability_class": "ukrainian_decision"},
    "rule_author_extractor": {"exact_model": "gemini-3.6-flash-high", "model_family": "gemini", "harness": "agy", "capability_class": "ukrainian_rule_proposal"},
    "heldout_steward": {"exact_model": "phase3-heldout-partition-v1", "model_family": "deterministic", "harness": "local-python", "capability_class": "heldout_custody"},
    "heldout_label_reviewer": {"exact_model": "gpt-5.6-sol", "model_family": "openai", "harness": "codex", "capability_class": "ukrainian_decision"},
    "scorer": {"exact_model": "phase3-evaluation-scorer-v1", "model_family": "deterministic", "harness": "local-python", "capability_class": "evaluation_scoring"},
    "outsider_reproducer": {"exact_model": "glm-5", "model_family": "zhipu", "harness": "opencode", "capability_class": "independent_reproduction"},
    "cross_family_code_infra_reviewer": {"exact_model": "grok-4.5", "model_family": "xai", "harness": "opencode", "capability_class": "cross_family_code_review"},
    "disposition_auditor": {"exact_model": "claude-opus-4-6", "model_family": "anthropic", "harness": "claude-code", "capability_class": "ukrainian_decision"},
    "textbook_nonhit_auditor": {"exact_model": "grok-4.5", "model_family": "xai", "harness": "opencode", "capability_class": "ukrainian_decision"},
}

ROLE_PERMISSIONS = {
    "scope_circularity_critic": {
        "may_act": ["contract_scope_review", "denominator_review", "completion_claim_review"],
        "must_not": ["author_rules", "label_heldout", "score_heldout", "make_linguistic_dispositions"],
    },
    "ukrainian_source_reviewer": {
        "may_act": ["ukrainian_source_review", "source_conflict_review", "normative_scope_review"],
        "must_not": ["author_reviewed_rules", "seal_heldout", "score_heldout"],
    },
    "rule_author_extractor": {
        "may_act": ["propose_rules_from_allowed_train_development_packets"],
        "must_not": ["read_heldout_text_locators_fingerprints_labels", "label_heldout", "score_heldout", "review_own_output"],
    },
    "heldout_steward": {
        "may_act": ["partition_heldout", "seal_heldout", "custody_heldout_bytes_locators_fingerprints"],
        "must_not": ["author_rules", "label_linguistic_gold", "score_heldout"],
    },
    "heldout_label_reviewer": {
        "may_act": ["label_steward_sealed_heldout_items"],
        "must_not": ["author_rules", "alter_partition_after_seal", "score_heldout"],
    },
    "scorer": {
        "may_act": ["score_fixed_release_against_sealed_heldout"],
        "must_not": ["modify_rules_under_test", "label_heldout", "redefine_thresholds_after_results"],
    },
    "outsider_reproducer": {
        "may_act": ["fresh_worktree_byte_identical_reproduction"],
        "must_not": ["use_author_worktree", "read_private_heldout_plaintext", "use_canary_as_completion_proof"],
    },
    "cross_family_code_infra_reviewer": {
        "may_act": ["review_code_schemas_ci_rights_opsec"],
        "must_not": ["make_ukrainian_normative_dispositions", "substitute_for_ukrainian_source_review"],
    },
    "disposition_auditor": {
        "may_act": ["audit_conversion_dispositions", "audit_locator_sufficiency", "audit_wrong_code_support_calls"],
        "must_not": ["author_audited_ledgers", "author_rules_for_audited_families", "seal_heldout", "score_heldout"],
    },
    "textbook_nonhit_auditor": {
        "may_act": ["audit_frozen_textbook_nonhit_sample"],
        "must_not": ["author_scanner_under_audit", "author_rules_from_audited_sample", "seal_heldout", "score_heldout"],
    },
}

DIRECTED_EDGES = [
    {"edge_kind": "scope_inputs_to_scope_review", "producer_task_id": "phase3-v2-1-root-orchestration", "consumer_task_id": ROLE_TASKS["scope_circularity_critic"], "fixed_before_consumer": True},
    {"edge_kind": "author_output_to_source_review", "producer_task_id": ROLE_TASKS["rule_author_extractor"], "consumer_task_id": ROLE_TASKS["ukrainian_source_reviewer"], "fixed_before_consumer": True},
    {"edge_kind": "steward_seal_to_label_review", "producer_task_id": ROLE_TASKS["heldout_steward"], "consumer_task_id": ROLE_TASKS["heldout_label_reviewer"], "fixed_before_consumer": True},
    {"edge_kind": "fixed_release_to_scorer", "producer_task_id": "phase3-v2-1-fixed-release-freeze", "consumer_task_id": ROLE_TASKS["scorer"], "fixed_before_consumer": True},
    {"edge_kind": "disposition_ledger_to_disposition_audit", "producer_task_id": "phase3-v2-1-disposition-ledger-production", "consumer_task_id": ROLE_TASKS["disposition_auditor"], "fixed_before_consumer": True},
    {"edge_kind": "scanner_to_textbook_nonhit_audit", "producer_task_id": "phase3-v2-1-textbook-scanner-implementation", "consumer_task_id": ROLE_TASKS["textbook_nonhit_auditor"], "fixed_before_consumer": True},
    {"edge_kind": "implementation_to_cross_family_code_review", "producer_task_id": "phase3-v2-1-root-orchestration", "consumer_task_id": ROLE_TASKS["cross_family_code_infra_reviewer"], "fixed_before_consumer": True},
    {"edge_kind": "fixed_release_to_outsider_reproduction", "producer_task_id": "phase3-v2-1-fixed-release-freeze", "consumer_task_id": ROLE_TASKS["outsider_reproducer"], "fixed_before_consumer": True},
]

ROOT_FORBIDDEN_ACTIONS = [
    "make_ukrainian_linguistic_decision",
    "make_source_label_decision",
    "make_heldout_label_decision",
    "make_score_decision",
    "make_disposition_audit_decision",
    "make_textbook_nonhit_audit_decision",
]
ACTION_RECEIPT_FIELDS = [
    "receipt_id",
    "role_id",
    "task_id",
    "action_kind",
    "provider",
    "exact_model",
    "model_family",
    "harness",
    "input_manifest_sha256",
    "output_sha256",
    "evaluation_cycle_id",
    "base_contract_sha256",
    "amendment_sha256",
    "combined_contract_sha256",
    "functional_role_contract_sha256",
    "conflict_graph_sha256",
    "started_at",
    "completed_at",
    "status",
]


class FunctionalRoleError(ValueError):
    """The v2.1 functional-role ledger is missing, stale, or unsafe."""


def canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"), sort_keys=True)


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def require(condition: bool, message: str) -> None:
    if not condition:
        raise FunctionalRoleError(message)


def read_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise FunctionalRoleError(f"cannot read JSON artifact: {path}") from exc
    require(isinstance(value, dict), "functional-role artifact must be an object")
    return value


def conflict_graph_sha256(value: Mapping[str, Any]) -> str:
    return hashlib.sha256(canonical_json(value["task_conflict_graph"]).encode("utf-8")).hexdigest()


def verify_value(value: Mapping[str, Any]) -> dict[str, Any]:
    schema = read_json(SCHEMA_PATH)
    Draft202012Validator.check_schema(schema)
    errors = sorted(Draft202012Validator(schema).iter_errors(value), key=lambda error: list(error.path))
    require(not errors, f"functional-role schema violation: {errors[0].message if errors else ''}")
    require(
        value["contract_inputs"]
        == {
            "phase3_v2_base_sha256": BASE_SHA256,
            "functional_role_amendment_sha256": AMENDMENT_SHA256,
            "combined_contract_sha256": COMBINED_SHA256,
        },
        "functional-role contract input binding drift",
    )
    independence = value["independence_model"]
    require(
        independence
        == {
            "unit": "task_id",
            "provider_is_independence_identity": False,
            "natural_person_identity_required": False,
            "task_ids_unique": True,
            "provider_reuse_allowed_for_nonconflicting_tasks": True,
            "action_receipt_required": True,
        },
        "obsolete provider or natural-person independence model detected",
    )
    roles = value["functional_roles"]
    by_role = {item["role_id"]: item for item in roles}
    require(len(roles) == len(by_role) == len(ROLE_TASKS), "functional role set is not exactly ten unique roles")
    require({item["task_id"] for item in roles} == set(ROLE_TASKS.values()), "functional task IDs are not exact and unique")
    require(set(by_role) == set(ROLE_TASKS), "functional role set drift")
    for role_id, task_id in ROLE_TASKS.items():
        require(
            by_role[role_id]
            == {"role_id": role_id, "task_id": task_id, **ROLE_EXECUTION[role_id], **ROLE_PERMISSIONS[role_id]},
            f"functional role binding drift: {role_id}",
        )
    graph = value["task_conflict_graph"]
    require(
        graph["nodes"]
        == [
            "phase3-v2-1-root-orchestration",
            "phase3-v2-1-disposition-ledger-production",
            "phase3-v2-1-textbook-scanner-implementation",
            "phase3-v2-1-fixed-release-freeze",
            *ROLE_TASKS.values(),
        ],
        "task conflict graph node order or set drift",
    )
    require(graph["edges"] == DIRECTED_EDGES, "directed task conflict graph edge drift")
    require(
        all(edge["producer_task_id"] != edge["consumer_task_id"] for edge in graph["edges"]),
        "task conflict graph contains a self-review edge",
    )
    root = value["root"]
    require(
        root
        == {
            "task_id": "phase3-v2-1-root-orchestration",
            "functional_role_ids": [],
            "forbidden_action_kinds": ROOT_FORBIDDEN_ACTIONS,
            "may_authorize_phase4": False,
        },
        "root decision prohibition drift",
    )
    acl = value["heldout_acl"]
    require(
        acl["pre_release_read_task_ids"]
        == [ROLE_TASKS["heldout_steward"], ROLE_TASKS["heldout_label_reviewer"]]
        and acl["post_release_score_task_ids"] == [ROLE_TASKS["scorer"]]
        and acl["forbidden_task_ids"]
        == [ROLE_TASKS[role] for role in ROLE_TASKS if role not in {"heldout_steward", "heldout_label_reviewer", "scorer"}],
        "heldout ACL drift",
    )
    receipt = value["action_receipt_contract"]
    require(receipt["required_fields"] == ACTION_RECEIPT_FIELDS, "action receipt field set drift")
    require(
        receipt["provider_is_audit_metadata_not_identity"] is True
        and receipt["provider_reuse_allowed_without_conflict_edge"] is True,
        "action receipt independence semantics drift",
    )
    cycle = value["evaluation_cycle"]
    require(
        cycle
        == {
            "evaluation_cycle_id": "phase3-v2-1-evaluation-cycle-001",
            "release_freeze_binding_field": "fixed_release_sha256",
            "evaluation_freeze_binding_field": "heldout_evaluation_freeze_sha256",
            "activation_requires_both_freeze_bindings": True,
            "void_on": ["release_artifact_change", "evaluation_freeze_change", "denominator_change", "breadth_floor_change", "evaluation_threshold_change"],
            "voided_cycle_may_not_resume": True,
            "restart_requires_new_cycle_id_and_fresh_freezes": True,
            "action_receipts_must_match_evaluation_cycle_id": True,
        },
        "evaluation cycle freeze or restart semantics drift",
    )
    require(
        all(
            by_role[role]["capability_class"] == "ukrainian_decision"
            and by_role[role]["model_family"] in {"gemini", "openai", "anthropic", "xai"}
            for role in ("ukrainian_source_reviewer", "heldout_label_reviewer", "disposition_auditor", "textbook_nonhit_auditor")
        ),
        "Ukrainian-decision role lacks a sanctioned capability lane",
    )
    require(
        by_role["rule_author_extractor"]["capability_class"] == "ukrainian_rule_proposal"
        and by_role["rule_author_extractor"]["model_family"] in {"gemini", "openai", "anthropic", "xai"},
        "rule-author task lacks a sanctioned Ukrainian-capable lane",
    )
    require(
        by_role["cross_family_code_infra_reviewer"]["model_family"] != "openai"
        and by_role["cross_family_code_infra_reviewer"]["capability_class"] == "cross_family_code_review",
        "code/infra reviewer is not cross-family from the OpenAI implementation root",
    )
    require(
        value["role_graph_ready"] is True,
        "functional role graph readiness drift",
    )
    require(
        value["source_authoring"]
        == {"blocked": True, "reason": "v2_1_runtime_migration_and_exact_head_review_pending"},
        "source-authoring state drift",
    )
    require(
        value["phase4"] == {"blocked": True, "reason": "phase3_v2_rebuild_review_and_completion_not_established"},
        "Phase 4 block drift",
    )
    return dict(value)


def verify(path: Path = LEDGER_PATH) -> dict[str, Any]:
    value = verify_value(read_json(path))
    return {
        "ok": True,
        "schema_version": value["schema_version"],
        "base_contract_sha256": BASE_SHA256,
        "amendment_sha256": AMENDMENT_SHA256,
        "combined_contract_sha256": COMBINED_SHA256,
        "functional_role_contract_sha256": sha256_file(path),
        "conflict_graph_sha256": conflict_graph_sha256(value),
        "role_count": len(value["functional_roles"]),
        "role_graph_ready": True,
        "source_authoring_blocked": True,
        "phase4_blocked": True,
    }


def binding_for_role(value: Mapping[str, Any], role_id: str) -> dict[str, str]:
    verified = verify_value(value)
    matching = [item for item in verified["functional_roles"] if item["role_id"] == role_id]
    require(len(matching) == 1, f"functional-role ledger lacks exactly one {role_id} binding")
    return {"role_id": role_id, "task_id": str(matching[0]["task_id"])}


def tasks_conflict(value: Mapping[str, Any], left_task_id: str, right_task_id: str) -> bool:
    verified = verify_value(value)
    requested = frozenset((left_task_id, right_task_id))
    return any(
        frozenset((edge["producer_task_id"], edge["consumer_task_id"])) == requested
        for edge in verified["task_conflict_graph"]["edges"]
    )


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate the Phase 3 v2.1 functional-role ledger.")
    parser.add_argument("--ledger", type=Path, default=LEDGER_PATH)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        print(canonical_json(verify(args.ledger)))
    except FunctionalRoleError as exc:
        print(canonical_json({"ok": False, "error": str(exc)}))
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
