#!/usr/bin/env python3
"""Validate the text-free Phase 3 recovery contract freeze before extraction."""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator
from jsonschema.exceptions import ValidationError

ROOT = Path(__file__).resolve().parents[3]
CONTRACTS = ROOT / "data/projects/open_model_data/contracts"
EVIDENCE = ROOT / "data/projects/open_model_data/evidence"
SCHEMA_NAMES = (
    "correction_protection_coverage_contract_v1.schema.json",
    "correction_protection_evaluation_contract_v1.schema.json",
    "correction_protection_role_contract_v1.schema.json",
)
ARTIFACT_NAMES = (
    "correction_protection_coverage_contract_v1.json",
    "correction_protection_evaluation_contract_v1.json",
    "correction_protection_role_contract_v1.json",
)
BINDING_INPUT_NAMES = (
    "phase3-recovery-prompt-v1.md",
    "phase3-recovery-scope-amendment-v3.md",
)
PROMPT_HASH = "6a563a7526c4ec7a89732f3de5651b0ab2e176ec089abf80f9eb733337db7662"
AMENDMENT_HASH = "da0f814f2f12e4974073de1a7b547fc3f27c07f6d903c95fde8f704d4e664132"
COMBINED_HASH = "bf387adaeb180d11ade272819d77e1eb3d3fdecc43982fff9c775039c9e0bed7"
PRAVOPYS_2026_HASH = "E593956BFBA6737D991A76FA86970DB9C10A5CD7FD8895BAE67F2B9A950C3A92"
PRAVOPYS_2019_HASH = "9adcb3e7e6b68db62719a4e8b0c34d7b1f4abde2986c694ab77662f2791ad24c"
PRAVOPYS_2026_DECISION_LOCATOR = "https://mova.gov.ua/rozyasnennya/rishennia-2026/berezen-2026/rishennia-47-vid-1-bereznia"
PRAVOPYS_2026_DOWNLOAD_LOCATOR = "https://mova.gov.ua/storage/app/sites/19/2026/rishennja-komisiji/01-03/sdm-ukrayinskii-pravopis-vidannia.pdf"
PRAVOPYS_2019_DOWNLOAD_LOCATOR = "https://mon.gov.ua/storage/app/media/zagalna%20serednya/05062019-onovl-pravo.pdf"
NEAR_DUPLICATE_IMPLEMENTATION_VERSION = "phase3_near_duplicate.py-v1"
NEAR_DUPLICATE_IMPLEMENTATION_MODULE = "scripts/projects/open_model_data/phase3_near_duplicate.py"
NEAR_DUPLICATE_POLICY_ARTIFACT = "data/projects/open_model_data/evidence/correction_protection_near_duplicate_policy_v1.json"
NEAR_DUPLICATE_POLICY_FINGERPRINT = "19518efb07dd8ef4173b32487da7427f3c1eb0b8f8dd5d21b046cfc4dc5d560e"
DISPOSITIONS = {
    "converted",
    "not_rule_bearing",
    "duplicate_representation",
    "evaluation_only",
    "rights_limited_locator_only",
    "superseded_or_historical",
    "blocked_with_reason",
}
FAMILY_TOTALS = {
    "antonenko_style_guide": 342,
    "antonenko_textbook_representation": 169,
    "calque_inventory": 58,
    "ua_gec": 8937,
    "school_textbooks": 54979,
    "lexical_vesum": 6691276,
    "lexical_sum11": 127069,
    "lexical_r2u": 13,
    "lexical_ulif": 8,
    "lexical_balla_en_uk": 78704,
    "lexical_dmklinger_uk_en": 30111,
    "lexical_esum_cognate_forms": 134836,
    "lexical_esum_etymology": 36177,
    "lexical_frazeolohichnyi": 24683,
    "lexical_grinchenko": 67275,
    "lexical_puls_cefr": 5939,
    "lexical_ukrajinet": 122441,
    "lexical_wiktionary": 50278,
}
LEXICAL_FAMILY_IDS = {family_id for family_id in FAMILY_TOTALS if family_id.startswith("lexical_")}
PENDING_FAMILY_IDS = {"pravopys_2019_complete", "pravopys_2026_complete", "other_normative_style_inventory"}
EVALUATION_PHENOMENA = {
    "direct_address_vocative",
    "impersonal_no_to_expressed_agent",
    "prepositional_government_valency",
    "pravopys_parallel_norms",
    "participial_versus_lexicalized_chyi",
    "numeral_agreement",
    "semantic_false_friends_interlanguage_homonyms",
    "lexical_interference",
    "phrase_collocation",
    "orthography",
    "punctuation",
    "syntactic_calque",
}
MATCHER_MECHANISMS = {
    "literal",
    "lemma_morphology",
    "phrase_collocation",
    "government_valency",
    "syntax",
    "semantic_contextual",
    "orthography",
    "punctuation",
}
EVALUATION_FAMILIES = {
    "antonenko_style_guide",
    "calque_inventory",
    "ua_gec",
    "school_textbooks",
    "pravopys_2019_complete",
    "pravopys_2026_complete",
    "other_normative_style_inventory",
}
ROLE_IDS = {
    "scope_circularity_critic",
    "ukrainian_source_reviewer",
    "rule_author_extractor",
    "heldout_steward",
    "heldout_label_reviewer",
    "scorer",
    "outsider_reproducer",
    "cross_family_code_infra_reviewer",
    "disposition_auditor",
    "textbook_nonhit_auditor",
}


class ContractError(ValueError):
    """A frozen contract is malformed or has been weakened."""


def canonical_json(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"), sort_keys=True)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ContractError(message)


def read_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ContractError(f"cannot read JSON {path}: {exc}") from exc
    require(isinstance(value, dict), f"expected JSON object: {path}")
    return value


def locate_shared_batch_state(repo_root: Path) -> Path | None:
    direct = repo_root / "batch_state"
    if direct.is_dir() and any((direct / name).is_file() for name in BINDING_INPUT_NAMES):
        return direct
    try:
        common_dir = subprocess.run(
            ["git", "-C", str(repo_root), "rev-parse", "--path-format=absolute", "--git-common-dir"],
            check=True,
            capture_output=True,
            text=True,
        ).stdout.strip()
    except (OSError, subprocess.CalledProcessError):
        return None
    candidate = Path(common_dir).parent / "batch_state"
    if candidate.is_dir() and any((candidate / name).is_file() for name in BINDING_INPUT_NAMES):
        return candidate
    return None


def _schema_validate(schema_path: Path, artifact_path: Path) -> dict[str, Any]:
    schema = read_json(schema_path)
    artifact = read_json(artifact_path)
    try:
        Draft202012Validator.check_schema(schema)
        Draft202012Validator(schema).validate(artifact)
    except ValidationError as exc:
        location = ".".join(str(part) for part in exc.path) or "<root>"
        raise ContractError(f"{artifact_path.name} schema violation at {location}: {exc.message}") from exc
    return artifact


def _validate_hashes(repo_root: Path, artifacts: list[dict[str, Any]]) -> bool:
    expected_files = {
        BINDING_INPUT_NAMES[0]: PROMPT_HASH,
        BINDING_INPUT_NAMES[1]: AMENDMENT_HASH,
    }
    for artifact in artifacts:
        inputs = artifact["contract_inputs"]
        require(inputs == {
            "original_prompt_sha256": PROMPT_HASH,
            "scope_amendment_sha256": AMENDMENT_HASH,
            "combined_contract_sha256": COMBINED_HASH,
        }, "contract input hashes are not the approved freeze")
    batch_state = locate_shared_batch_state(repo_root)
    if batch_state is None:
        return False
    for name, expected in expected_files.items():
        path = batch_state / name
        require(path.is_file(), f"missing binding input: {name}")
        require(sha256_file(path) == expected, f"binding input hash mismatch: {name}")
    combined_bytes = (
        (batch_state / "phase3-recovery-prompt-v1.md").read_bytes()
        + b"\n---\n"
        + (batch_state / "phase3-recovery-scope-amendment-v3.md").read_bytes()
    )
    require(hashlib.sha256(combined_bytes).hexdigest() == COMBINED_HASH, "combined binding input hash mismatch")
    return True


def _validate_coverage(coverage: dict[str, Any]) -> None:
    require(coverage["text_free"] is True, "coverage contract must remain text-free")
    require(set(coverage["disposition_taxonomy"]) == DISPOSITIONS, "coverage disposition taxonomy changed")
    require(coverage["source_audit_population_contract"] == {
        "family_audit_stratification_field_population": "nonconverted",
        "nonconverted_stratification": ["disposition_code", "document_or_edition_identity"],
        "converted_stratification": ["source_role", "claim_type", "document_or_edition_identity"],
        "seed_committed_by_responsible_auditing_seat_before_results": True,
    }, "source audit population contract changed")
    require(coverage["audit_seed_independence_contract"] == {
        "applies_to": ["source_nonconverted", "source_converted", "textbook_nonhit", "pravopys_delta"],
        "seed_committed_by_responsible_auditing_seat_before_results": True,
        "author_roles_forbidden_from_seed_proposal_filter_search_or_reroll": True,
        "seed_search_or_reroll_invalidates_receipt": True,
        "author_seat_seed_invalidates_receipt": True,
        "lexical_used_subset_is_complete_census_without_sampling_or_seed": True,
    }, "audit seed independence contract changed")
    require(coverage["audit_result_acceptance_contract"] == {
        "source_nonconverted_zero_nonagree_required": True,
        "source_converted_zero_miss_required": True,
        "textbook_nonhit_zero_miss_required": True,
        "pravopys_delta_zero_nonagree_required": True,
        "lexical_used_subset_zero_nonagree_required": True,
        "any_nonagree_requires_repair_new_freeze_and_fresh_sample_or_census": True,
    }, "audit result acceptance contract changed")
    require(coverage["ledger_audit_identity_contract"] == {
        "receipt_fields": ["frozen_input_identity_total", "family_unit_total", "ledger_input_total", "disposition_row_sum", "ledger_universe_sha256", "audit_universe_sha256"],
        "required_equalities": [
            "frozen_input_identity_total==family_unit_total",
            "family_unit_total==ledger_input_total",
            "ledger_input_total==disposition_row_sum",
            "ledger_universe_sha256==audit_universe_sha256",
        ],
        "mismatch_blocks": ["SOURCE_COVERAGE_READY", "PHASE3_COMPLETE"],
    }, "ledger/audit identity contract changed")
    families = {item["family_id"]: item for item in coverage["mandatory_families"]}
    require(len(families) == len(coverage["mandatory_families"]), "duplicate coverage family")
    require(set(families) == set(FAMILY_TOTALS) | PENDING_FAMILY_IDS, "mandatory coverage family set changed")
    for family_id, total in FAMILY_TOTALS.items():
        require(families[family_id]["input_identity"]["observed_input_total"] == total, f"denominator shrunk: {family_id}")
    require("pravopys_2019_complete" in families, "2019 acquisition/ledger missing")
    require("other_normative_style_inventory" in families, "other normative/style inventory missing")
    for family in families.values():
        identity = family["input_identity"]
        require(identity["freeze_state"] in {"observed_not_frozen", "pending_acquisition"}, "pre-extraction universe falsely frozen")
        require(identity["universe_sha256"] is None, "non-frozen universe has a present or fabricated hash")
        require(family["mandatory"] is True, "optional mandatory family")
        require(family["rights"]["source_text_committed"] is False, "source text must remain locator-only")
        if family["family_id"] not in LEXICAL_FAMILY_IDS:
            audit = family["audit"]
            require(family["coverage_mode"] in {"source_conversion", "duplicate_representation"}, "non-lexical coverage mode weakened")
            require(audit["nonconverted_formula"] == "min(nonconverted_total,max(100,ceil(0.02*family_unit_total)))", "non-converted sample formula weakened")
            require(audit["converted_formula"] == "min(converted_total,max(100,ceil(0.02*family_unit_total)))", "converted sample formula weakened")
            require(audit["nonconverted_stratification"] == ["disposition_code", "document_or_edition_identity"], "non-converted stratification changed")
            require(audit["converted_stratification"] == ["source_role", "claim_type", "document_or_edition_identity"], "converted stratification changed")
            require(audit["sampling_without_replacement"] is True, "source audit permits replacement")
            require(audit["repair_invalidates_both_samples"] is True, "source repair does not invalidate both samples")
            require(audit["passing_sample_reuse_forbidden"] is True, "source audit permits sample reuse")
            require(set(audit["nonconverted_decision_codes"]) == {
                "agree", "disagree_should_be_converted", "disagree_wrong_code", "insufficient_locator_evidence",
            }, "non-converted audit decision codes changed")
            require(set(audit["converted_miss_codes"]) == {
                "disagree_stub_conversion", "disagree_misclassified_role_or_claim",
                "disagree_unsupported_evidence", "disagree_non_actionable_rule",
            }, "converted audit miss codes changed")
    require(families["pravopys_2019_complete"]["input_identity"]["freeze_state"] == "pending_acquisition", "2019 acquisition state changed")
    require(families["pravopys_2019_complete"]["input_identity"]["observed_input_total"] == "unknown_pending_acquisition", "2019 navigation capture misrepresented as complete")
    require(families["pravopys_2026_complete"]["input_identity"]["freeze_state"] == "pending_acquisition", "2026 acquisition state changed")
    require(families["pravopys_2026_complete"]["input_identity"]["observed_input_total"] == "unknown_pending_acquisition", "2026 paragraph extent misused as ledger total")
    require(families["other_normative_style_inventory"]["input_identity"]["freeze_state"] == "pending_acquisition", "other normative/style inventory falsely closed")
    require(families["antonenko_textbook_representation"]["coverage_mode"] == "duplicate_representation", "Antonenko representation role changed")
    require("7250_sections_168_tracked_files" in families["school_textbooks"]["input_identity"]["unit_grain"], "textbook grain weakened")
    school = families["school_textbooks"]
    require(school["audit"]["auditor_role_id"] == "disposition_auditor", "textbook source disposition audit changed")
    scanner = school.get("scanner_nonhit_audit")
    require(isinstance(scanner, dict), "textbook scanner/non-hit audit missing")
    require(scanner["auditor_role_id"] == "textbook_nonhit_auditor", "textbook scanner auditor changed")
    require(scanner["seed_owner_role_id"] == "textbook_nonhit_auditor", "textbook scanner seed owner changed")
    require(scanner["sample_formula"] == "min(1000,nonhit_total)", "textbook non-hit formula weakened")
    require(scanner["stratification"] == ["tracked_file", "source_identity"], "textbook non-hit stratification changed")
    require(scanner["rubric_frozen_before_sampling"] is True and scanner["zero_misses_required"] is True, "textbook scanner audit weakened")
    for lexical_id in LEXICAL_FAMILY_IDS:
        family = families[lexical_id]
        audit = family["audit"]
        require(family["coverage_mode"] == "lexical_structural_and_used_subset", "lexical coverage mode weakened")
        require(audit["mode"] == "lexical_structural_and_used_subset", "lexical audit mode weakened")
        require(audit["structural_index_audit_required"] is True and audit["machine_derived_used_subset_census_required"] is True, "lexical census weakened")
        require(audit["used_subset_extracted_from_all_release_artifacts"] is True, "lexical used subset became author-declared")
        require(audit["zero_nonagree_required"] is True and audit["repair_requires_new_freeze_and_census"] is True, "lexical census fail-closed rule weakened")
        require(set(audit["structural_fields_required"]) == {"count", "identifier", "hash", "parse_status", "duplicate_group", "retrieval_version_provenance"}, "lexical structural fields changed")
        require(set(audit["decision_codes"]) == {"agree", "disagree_invalid_attestation", "disagree_unsupported_semantic_range", "disagree_mismapped_morphology", "insufficient_locator_evidence"}, "lexical decision codes changed")
    require("28_sections_26_raw_responses" in families["lexical_ulif"]["input_identity"]["unit_grain"], "stale ULIF section/raw-response counts")
    authority = coverage["pravopys_2026_authority"]
    require(authority["official_pdf_sha256"] == PRAVOPYS_2026_HASH, "wrong 2026 Pravopys hash")
    require(authority["official_decision_locator"] == PRAVOPYS_2026_DECISION_LOCATOR, "wrong 2026 decision locator")
    require(authority["official_download_locator"] == PRAVOPYS_2026_DOWNLOAD_LOCATOR, "wrong 2026 download locator")
    require(authority["digest_hex_case"] == "uppercase_as_published", "2026 published digest casing provenance changed")
    require(authority["page_count"] == 426 and authority["stated_paragraph_extent"] == 168, "2026 Pravopys provenance changed")
    require(authority["official_bytes_acquired_and_verified"] is True, "verified 2026 acquisition lost")
    require(authority["acquisition_retrieved_at"] == "2026-08-05T22:05:39Z", "2026 retrieval time changed")
    require(authority["rights_provenance_classification"] == "rights_limited_locator_only", "2026 rights provenance changed")
    alignment = coverage["edition_alignment"]
    require(alignment["current_authority_family"] == "pravopys_2026_complete", "2026 authority changed")
    require(alignment["historical_family"] == "pravopys_2019_complete", "2019 retention changed")
    require(alignment["pravopys_2019_official_pdf_sha256"] == PRAVOPYS_2019_HASH, "wrong official 2019 Pravopys hash")
    require(alignment["pravopys_2019_official_download_locator"] == PRAVOPYS_2019_DOWNLOAD_LOCATOR, "wrong 2019 download locator")
    require(alignment["pravopys_2019_official_provenance_verified"] is True, "verified 2019 provenance lost")
    require(alignment["pravopys_2019_rights_provenance_classification"] == "rights_limited_locator_only", "2019 rights provenance changed")
    required_delta = {"unchanged", "editorial_technical_only", "illustration_removed_or_changed", "stress_or_formulation_clarified", "new_structural_wrapper_or_alphabet_material", "added_rule_bearing_unit", "removed_rule_bearing_unit", "normative_conflict"}
    require(set(alignment["delta_dispositions"]) == required_delta, "Pravopys delta taxonomy changed")
    delta = alignment["delta_coverage_required"]
    require(all(delta.values()), "edition delta coverage weakened")
    delta_audit = alignment["delta_audit"]
    require(delta_audit["sample_formula"] == "min(delta_total,max(100,ceil(0.02*delta_total)))", "delta sample formula weakened")
    require(delta_audit["sampling_without_replacement"] is True and delta_audit["passing_sample_reuse_forbidden"] is True, "delta sample rules weakened")
    require(delta_audit["stratification"] == ["delta_disposition", "edition_section_identity"], "delta stratification changed")
    require(delta_audit["zero_nonagree_required"] is True and delta_audit["repair_requires_new_freeze_and_sample"] is True, "delta zero-miss repair rule weakened")
    require(set(delta_audit["decision_codes"]) == {
        "agree", "disagree_wrong_delta_disposition", "disagree_missed_normative_conflict", "insufficient_locator_evidence",
    }, "delta audit decision codes changed")
    blocker_ids = {blocker["blocker_id"] for blocker in coverage["status_blockers"]}
    require("all_mandatory_unit_universes_must_be_genuinely_frozen_hash_bound_before_source_extraction" in blocker_ids, "universe-freeze extraction blocker missing")


def _validate_evaluation(evaluation: dict[str, Any], repo_root: Path) -> None:
    require(evaluation["text_free"] is True, "evaluation contract must remain text-free")
    require(set(evaluation["matcher_mechanisms"]) == MATCHER_MECHANISMS, "matcher mechanism classes changed")
    require(set(evaluation["phenomena"]) == EVALUATION_PHENOMENA, "evaluation phenomenon classes changed")
    require(set(evaluation["source_families"]) == EVALUATION_FAMILIES, "evaluation source families changed")
    matrix = evaluation["release_category_matrix"]
    require(matrix["matrix_encoding"] == "complete_cartesian_predeclaration_v1", "category matrix encoding changed")
    require(set(matrix["source_families"]) == EVALUATION_FAMILIES, "incomplete category-matrix source families")
    require(set(matrix["phenomena"]) == EVALUATION_PHENOMENA, "incomplete category-matrix phenomena")
    require(matrix["predeclared_state"] == "automatic_candidate", "automatic candidate matrix weakened before evaluation")
    require(matrix["automatic_nomination_is_not_normative_approval"] is True, "automatic candidate became normative approval")
    require(matrix["ukrainian_artifact_review_required_before_extraction"] is True, "automatic nomination bypasses Ukrainian artifact review")
    policy = evaluation["near_duplicate_policy"]
    require(policy["policy_id"] == "near_duplicate_policy_v1" and policy["fail_closed"] is True, "near-duplicate policy weakened")
    require(policy["implementation_version"] == NEAR_DUPLICATE_IMPLEMENTATION_VERSION, "near-duplicate implementation version drift")
    require(policy["implementation_module"] == NEAR_DUPLICATE_IMPLEMENTATION_MODULE, "near-duplicate implementation module drift")
    require(policy["implementation_artifact"] == NEAR_DUPLICATE_POLICY_ARTIFACT, "near-duplicate policy artifact drift")
    require(policy["policy_fingerprint_sha256"] == NEAR_DUPLICATE_POLICY_FINGERPRINT, "near-duplicate policy fingerprint drift")
    require((repo_root / policy["implementation_module"]).is_file(), "near-duplicate implementation missing")
    policy_artifact = read_json(repo_root / policy["implementation_artifact"])
    require(policy_artifact["policy_fingerprint_sha256"] == NEAR_DUPLICATE_POLICY_FINGERPRINT, "near-duplicate policy artifact fingerprint drift")
    artifact_fingerprint_input = dict(policy_artifact)
    artifact_fingerprint_input.pop("policy_fingerprint_sha256", None)
    require(
        hashlib.sha256((canonical_json(artifact_fingerprint_input) + "\n").encode("utf-8")).hexdigest()
        == NEAR_DUPLICATE_POLICY_FINGERPRINT,
        "near-duplicate policy artifact content drift",
    )
    require(policy_artifact["implementation"] == {
        "algorithm_identity": "phase3-normalized-token-edit-firewall-v1",
        "implementation_version": NEAR_DUPLICATE_IMPLEMENTATION_VERSION,
        "module": NEAR_DUPLICATE_IMPLEMENTATION_MODULE,
    }, "near-duplicate policy artifact implementation drift")
    require(policy["normalization_steps"] == ["unicode_normalization", "casefold", "whitespace_collapse", "punctuation_tokenization"], "near-duplicate normalization changed")
    require(policy["compared_fields"] == ["source_document_identity", "unit_identity", "span_fingerprint", "normalized_surface"], "near-duplicate compared fields changed")
    require(policy["similarity_features"] == ["exact_fingerprint", "token_jaccard", "normalized_edit_similarity"], "near-duplicate similarity features changed")
    require(policy["numeric_thresholds"] == {"near_duplicate_minimum": 0.9, "exact_match": 1.0}, "near-duplicate thresholds changed")
    require(policy["implementation_and_fixture_manifest_required_before_partition"] is True, "near-duplicate manifest prerequisite missing")
    require(policy["independent_code_review_required"] is True and policy["scope_critic_challenge_required"] is True, "near-duplicate independent review prerequisite missing")
    require(set(policy["required_fixture_classes"]) == {"exact_matches_minimum", "near_matches_minimum", "non_matches_minimum"}, "near-duplicate fixture specification changed")
    require(set(policy["scopes"]) == {"document", "unit", "span"}, "near-duplicate scope weakened")
    required_governs = {"train_development_to_heldout_firewall", "ua_eval_exclusion", "public_canary_neighbour_exclusion", "canonical_rule_identity_collapse", "heldout_activation_counts"}
    require(set(policy["governs"]) == required_governs, "near-duplicate firewall scope changed")
    access = evaluation["heldout_access"]
    require(access["partition_before_extraction"] is True and access["exact_and_near_overlap_allowed"] is False, "held-out firewall weakened")
    require(set(access["pre_release_read_acl"]) == {"heldout_steward", "heldout_label_reviewer"}, "pre-release ACL changed")
    require(access["post_release_scorer_acl"] == ["scorer"], "scorer ACL changed")
    gate = evaluation["per_phenomenon_gate"]
    exact_gate = {"positive_per_phenomenon": 30, "acceptable_control_per_phenomenon": 30, "protected_per_phenomenon": 30, "distinct_documents_per_stratum": 3, "precision_minimum": 0.98, "recall_minimum": 0.8, "protected_destructive_changes_maximum": 0, "control_false_corrections_maximum": 0}
    require({key: gate[key] for key in exact_gate} == exact_gate, "per-phenomenon threshold weakened")
    require(gate["pooling_forbidden"] is True, "per-phenomenon pooling permitted")
    floors = evaluation["breadth_floors"]
    require({key: floors[key] for key in ("total_canonical_rule_identities_minimum", "total_phenomena_minimum", "total_mechanisms_minimum", "total_source_families_minimum")} == {"total_canonical_rule_identities_minimum": 100, "total_phenomena_minimum": 6, "total_mechanisms_minimum": 4, "total_source_families_minimum": 4}, "total breadth floors weakened")
    require({key: floors[key] for key in ("automatic_canonical_rule_identities_minimum", "automatic_phenomena_minimum", "automatic_mechanisms_minimum", "automatic_source_families_minimum")} == {"automatic_canonical_rule_identities_minimum": 25, "automatic_phenomena_minimum": 4, "automatic_mechanisms_minimum": 3, "automatic_source_families_minimum": 3}, "automatic breadth floors weakened")
    require(floors["automatic_categories_minimum"] == 4 and floors["automatic_rule_activations_minimum"] == 2, "automatic breadth/activation floor weakened")
    require(floors["surface_pair_key_definition"] == "frozen_literal_or_normalized_incorrect_to_correct_surface_pair_only", "surface-pair key rule weakened")
    require(all(floors[key] == 0.1 for key in ("canary_neighbour_share_maximum", "canary_rule_identity_share_maximum", "canary_heldout_positive_share_maximum")), "canary cap weakened")
    require(evaluation["residual_map_required"] is True, "residual-map requirement missing")
    require(set(evaluation["status_blockers"]) == {
        "near_duplicate_implementation_and_fixture_manifest_with_independent_code_review_and_scope_critic_challenge_required_before_partition",
        "ukrainian_domain_artifact_review_required_before_source_extraction",
        "scope_circularity_artifact_review_required_before_source_extraction",
    }, "pre-extraction artifact-review blockers changed")
    require(set(evaluation["excluded_denominators"]) == {"phase2_metadata_rows", "public_authored_canaries", "public_canary_near_duplicates"}, "Phase 2 or canary denominator admitted")
    require(evaluation["invalidation"]["near_duplicate_policy_change_invalidates"] is True and evaluation["invalidation"]["rescore_from_scratch"] is True, "invalidation weakened")


def _validate_roles(roles: dict[str, Any]) -> None:
    require(roles["identity_exclusivity_contract"] == {
        "scope": "entire_phase3_recovery_program",
        "registry": "durable_program_identity_registry",
        "one_natural_person_or_continuing_agent_identity_per_decision_role_maximum": True,
        "same_controller_reuses_identity_across_sessions_task_ids_harnesses_models_and_providers": True,
        "controller_identity_attestation_required_before_role_action": True,
        "assigned_controller_identity_ids_unique_across_decision_seats": True,
        "root_controller_identity_forbidden_from_decision_seats": True,
        "unassigned_reserved_seats_may_not_act_or_issue_receipts": True,
        "task_binding_must_match_seat_controller_identity": True,
    }, "durable controller identity exclusivity contract changed")
    require(roles["root"] == {
        "controller_identity_id": "controller_phase3_root_01",
        "decision_role_ids": [],
        "may_hold_decision_role": False,
    }, "root assigned a decision role or root identity changed")
    seats = roles["seats"]
    seat_ids = [seat["seat_id"] for seat in seats]
    role_ids = [seat["role_id"] for seat in seats]
    require(len(set(seat_ids)) == len(seat_ids) == 10, "decision seat reused")
    require(len(set(role_ids)) == len(role_ids) == 10 and set(role_ids) == ROLE_IDS, "decision roles changed or reused")
    require(set(seat_ids) == {f"seat_{role_id}" for role_id in ROLE_IDS}, "durable seat IDs changed")
    assigned_controller_ids = [seat["controller_identity_id"] for seat in seats if seat["assignment_state"] == "assigned_verified"]
    require(len(set(assigned_controller_ids)) == len(assigned_controller_ids), "one durable controller identity assigned to multiple decision roles")
    require(roles["root"]["controller_identity_id"] not in assigned_controller_ids, "root controller identity assigned a decision role")
    required_ukrainian = {"ukrainian_source_reviewer", "rule_author_extractor", "heldout_label_reviewer", "disposition_auditor", "textbook_nonhit_auditor"}
    for seat in seats:
        require(seat["ukrainian_capable_required"] is (seat["role_id"] in required_ukrainian), "Ukrainian capability requirement changed")
    acl = roles["heldout_acl"]
    require(set(acl["pre_release_read_roles"]) == {"heldout_steward", "heldout_label_reviewer"}, "role held-out ACL changed")
    require(acl["post_release_scorer_roles"] == ["scorer"], "post-release scorer role changed")
    expected_forbidden = ROLE_IDS - {"heldout_steward", "heldout_label_reviewer", "scorer"}
    require(set(acl["forbidden_roles"]) == expected_forbidden, "forbidden held-out role set changed")
    bindings = roles["task_bindings"]
    require(len(bindings) == 10 and {binding["role_id"] for binding in bindings} == ROLE_IDS, "reserved task bindings incomplete")
    require(len({binding["reserved_task_id"] for binding in bindings}) == 10, "reserved task binding reused")
    by_role = {binding["role_id"]: binding for binding in bindings}
    seat_by_role = {seat["role_id"]: seat for seat in seats}
    for role_id in ROLE_IDS:
        require(by_role[role_id]["controller_identity_id"] == seat_by_role[role_id]["controller_identity_id"], "task binding controller identity differs from decision seat")
    attested = {
        "scope_circularity_critic": ("review-phase3-recovery-contract-scope-v9", "controller_phase3_scope_critic_01", "combined_contract_text_approved_pre_artifact"),
        "ukrainian_source_reviewer": ("review-phase3-recovery-contract-domain-v8", "controller_phase3_ukrainian_reviewer_01", "combined_contract_text_approved_pre_artifact"),
        "rule_author_extractor": ("phase3-role-rule-author-agy-v3", "controller_phase3_rule_author_agy_runtime_01", "identity_attested_pre_artifact"),
        "heldout_steward": ("phase3-role-heldout-steward-cursor-v2", "controller_phase3_heldout_steward_cursor_runtime_01", "identity_attested_pre_artifact"),
        "heldout_label_reviewer": ("phase3-role-label-reviewer-codex-v2", "controller_phase3_heldout_label_reviewer_codex_runtime_01", "identity_attested_pre_artifact"),
        "scorer": ("phase3-role-scorer-kimi-v1", "controller_phase3_scorer_kimi_01", "identity_attested_pre_artifact"),
        "outsider_reproducer": ("phase3-role-outsider-reproducer-glm-v1", "controller_phase3_outsider_reproducer_glm_01", "identity_attested_pre_artifact"),
        "cross_family_code_infra_reviewer": ("phase3-role-cross-family-code-infra-reviewer-grok-v1", "controller_phase3_cross_family_reviewer_grok_01", "identity_attested_pre_artifact"),
        "disposition_auditor": ("phase3-role-disposition-auditor-claude-v1", "controller_phase3_disposition_auditor_claude_01", "identity_attested_pre_artifact"),
        "textbook_nonhit_auditor": ("phase3-role-textbook-nonhit-auditor-agy-v1", "controller_phase3_textbook_nonhit_auditor_agy_01", "identity_attested_pre_artifact"),
    }
    for role_id, (task_id, controller_identity_id, status) in attested.items():
        binding = by_role[role_id]
        require(binding["status"] == status and binding["reserved_task_id"] == task_id, "attested decision role binding changed")
        seat = seat_by_role[role_id]
        require(seat["assignment_state"] == "assigned_verified" and seat["controller_identity_attested"] is True, "attested decision seat identity is not assigned and attested")
        require(binding["controller_identity_id"] == controller_identity_id, "attested decision seat controller identity changed")
        require(binding["artifact_approval_claimed"] is False, "artifact review falsely self-sealed")
        require(binding["program_completion_claimed"] is False, "attested role falsely claims program completion")
    for role_id in ROLE_IDS - set(attested):
        binding = by_role[role_id]
        seat = seat_by_role[role_id]
        require(seat["assignment_state"] == "reserved_unassigned" and seat["controller_identity_id"] is None and seat["controller_identity_attested"] is False, "unlaunched decision seat claims a controller identity")
        require(binding["status"] == "reserved_not_launched" and binding["artifact_approval_claimed"] is False and binding["program_completion_claimed"] is False, "reserved role status changed")


def validate_contracts(repo_root: Path = ROOT) -> dict[str, Any]:
    repo_root = repo_root.resolve()
    schema_paths = [repo_root / "data/projects/open_model_data/contracts" / name for name in SCHEMA_NAMES]
    artifact_paths = [repo_root / "data/projects/open_model_data/evidence" / name for name in ARTIFACT_NAMES]
    artifacts = [_schema_validate(schema_path, artifact_path) for schema_path, artifact_path in zip(schema_paths, artifact_paths, strict=True)]
    local_binding_inputs_verified = _validate_hashes(repo_root, artifacts)
    _validate_coverage(artifacts[0])
    _validate_evaluation(artifacts[1], repo_root)
    _validate_roles(artifacts[2])
    return {
        "artifacts": ARTIFACT_NAMES,
        "local_binding_inputs_verified": local_binding_inputs_verified,
        "ok": True,
        "schema_version": "phase3_recovery_contract_validator_v1",
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=ROOT)
    arguments = parser.parse_args(argv)
    try:
        print(canonical_json(validate_contracts(arguments.repo_root)))
    except ContractError as exc:
        print(canonical_json({"error": str(exc), "ok": False, "schema_version": "phase3_recovery_contract_validator_v1"}))
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
