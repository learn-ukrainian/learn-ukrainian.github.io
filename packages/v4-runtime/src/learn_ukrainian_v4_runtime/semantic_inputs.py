"""Immutable, permitted semantic inputs transported by the service parent."""

from __future__ import annotations

import json
import re

from learn_ukrainian_v4_runtime.operation_auth import HEX64, OperationRefused, canonical_bytes, digest
from learn_ukrainian_v4_runtime.resources import resource_root

CONSTRAINT_KEYS = frozenset({
    "task_kind", "cefr_level", "required_fields", "allowed_evidence_tools",
    "language", "stratum", "target",
})
TOOLS = frozenset({"verify_word", "verify_words", "verify_lemma", "verify_stress", "check_modern_form"})
# Phase 3 claim types, structuredMatcher and protected_context_roles. This
# bounded projection carries grammatical facts, never source expressions.
CLAIM_TYPES = {"prescriptive_rule", "human_correction_pair", "style_preference", "acceptable_variant",
               "historical_advice", "attestation_only", "unresolved"}
MECHANISMS = {"lemma_morphology", "government_valency", "syntax"}
PROTECTIONS = {"quotation", "code_switch", "transliteration", "metalinguistic_example", "name_title",
               "dialect_or_regional_form", "historical_text", "ambiguous_noisy"}
POS = {"ADJ", "ADP", "ADV", "AUX", "CCONJ", "DET", "INTJ", "NOUN", "NUM", "PART", "PRON", "PROPN",
       "PUNCT", "SCONJ", "SYM", "VERB", "X"}
FEATURES = {
    "Case": {"Nom", "Gen", "Dat", "Acc", "Ins", "Loc", "Voc"},
    "Number": {"Sing", "Plur"}, "Gender": {"Masc", "Fem", "Neut"},
    "Person": {"1", "2", "3"}, "Animacy": {"Anim", "Inan"},
    "Aspect": {"Imp", "Perf"}, "Tense": {"Past", "Pres", "Fut"},
    "VerbForm": {"Fin", "Inf", "Part", "Conv"}, "Mood": {"Ind", "Imp", "Cnd"},
}
RELATIONS = {"acl", "advcl", "advmod", "amod", "appos", "aux", "case", "cc", "ccomp", "clf", "compound",
             "conj", "cop", "csubj", "dep", "det", "discourse", "dislocated", "expl", "fixed", "flat",
             "goeswith", "iobj", "list", "mark", "nmod", "nsubj", "nummod", "obj", "obl", "orphan",
             "parataxis", "punct", "reparandum", "vocative", "xcomp"}
SCOPE_LABEL = re.compile(r"[a-z][a-z0-9_]{0,31}\Z")
REVIEW_RUBRIC_RELATIVE = "data/projects/open_model_data/trust/v4_review_rubric_v2.txt"
REVIEW_RUBRIC_SHA256 = "07fc5028f37961408e3a19369b2746154fbf2573f6cb740a17c8eec1b5b04f48"
A4_RELATIVE = "data/projects/open_model_data/admission/dataset_v4_a4_deterministic_extraction_receipt_v1.json"
A5_RELATIVE = "data/projects/open_model_data/admission/dataset_v4_a5_evidence_enrichment_receipt_v1.json"


def _keys(value, keys, reason):
    if not isinstance(value, dict) or set(value) != set(keys):
        raise OperationRefused(reason)


def _choice(value, choices, reason):
    if not isinstance(value, str) or value not in choices:
        raise OperationRefused(reason)


def _choices(value, choices, reason, *, minimum=1, maximum=16):
    if (not isinstance(value, list) or not minimum <= len(value) <= maximum
            or any(not isinstance(item, str) or item not in choices for item in value)
            or len(value) != len(set(value))):
        raise OperationRefused(reason)


def validate_target(target: dict) -> None:
    _keys(target, {"claim_type", "mechanism", "scope", "matcher", "protections"}, "linguistic_target_required")
    _choice(target["claim_type"], CLAIM_TYPES, "linguistic_claim_type")
    # Unresolved/attestation-only status is never promoted to normative authority.
    if target["claim_type"] in {"unresolved", "attestation_only"}:
        raise OperationRefused("linguistic_authority_unresolved")
    _choice(target["mechanism"], MECHANISMS, "linguistic_mechanism")
    _keys(target["scope"], {"register", "period", "genre"}, "linguistic_scope")
    if any(not isinstance(v, str) or not SCOPE_LABEL.fullmatch(v) for v in target["scope"].values()):
        raise OperationRefused("linguistic_scope")
    _choices(target["protections"], PROTECTIONS, "linguistic_protections", minimum=0)
    matcher = target["matcher"]
    _keys(matcher, {"kind", "tokens", "dependency_constraints"}, "linguistic_matcher")
    if matcher["kind"] != target["mechanism"]:
        raise OperationRefused("linguistic_matcher_kind")
    tokens = matcher["tokens"]
    if not isinstance(tokens, list) or not 1 <= len(tokens) <= 4:
        raise OperationRefused("linguistic_tokens")
    for token in tokens:
        _keys(token, {"pos", "features"}, "linguistic_token")
        _choice(token["pos"], POS, "linguistic_pos")
        features = token["features"]
        if not isinstance(features, dict) or not 1 <= len(features) <= 4 or not set(features) <= FEATURES.keys():
            raise OperationRefused("linguistic_features")
        for key, value in features.items():
            _choice(value, FEATURES[key], "linguistic_feature_value")
    dependencies = matcher["dependency_constraints"]
    minimum_dependencies = 0 if target["mechanism"] == "lemma_morphology" else 1
    if not isinstance(dependencies, list) or not minimum_dependencies <= len(dependencies) <= 4:
        raise OperationRefused("linguistic_dependencies")
    for relation in dependencies:
        _keys(relation, {"head", "dependent", "relation"}, "linguistic_dependency")
        if (any(type(relation[k]) is not int or not 0 <= relation[k] < len(tokens) for k in ("head", "dependent"))
                or relation["head"] == relation["dependent"]):
            raise OperationRefused("linguistic_dependency_index")
        _choice(relation["relation"], RELATIONS, "linguistic_dependency_relation")


def validate_constraints(value: dict) -> None:
    _keys(value, CONSTRAINT_KEYS, "admitted_constraints_required")
    if value["language"] != "uk":
        raise OperationRefused("constraint_language")
    _choice(value["cefr_level"], {"A1", "A2", "B1", "B2", "C1", "C2"}, "constraint_level")
    _choice(value["task_kind"], {"original_row", "correction", "explanation", "exercise"}, "constraint_task")
    _choices(value["required_fields"], {"row_text", "explanation", "answer", "instruction"}, "constraint_fields")
    if "row_text" not in value["required_fields"]:
        raise OperationRefused("constraint_fields")
    _choices(value["allowed_evidence_tools"], TOOLS, "constraint_tools")
    _choice(value["stratum"], {"standard_correct", "correction", "literary", "dialect_regional",
                             "archaic_historical", "mixing", "quotation_interference", "abstention"}, "constraint_stratum")
    validate_target(value["target"])
    if value["stratum"] == "correction" and value["target"]["claim_type"] not in {"prescriptive_rule", "human_correction_pair"}:
        raise OperationRefused("correction_authority_required")
    if value["stratum"] == "correction" and not {"answer", "explanation", "instruction"} <= set(value["required_fields"]):
        raise OperationRefused("correction_target_separate")



def validate_authored_row(row: dict, constraints: dict) -> None:
    """Required output fields are a deterministic contract, not a model promise."""
    validate_constraints(constraints)
    required = constraints["required_fields"]
    if (not isinstance(row, dict) or not set(required) <= set(row)
            or any(not isinstance(row[key], str) or not row[key].strip() for key in required)):
        raise OperationRefused("author_required_fields")


def validate_owned_authored_row(conn, binding: dict, row: dict) -> None:
    """Resolve the immutable assignment contract before any author artifact is stored."""
    stored = conn.execute(
        "SELECT semantic_input_json FROM v4_execution_dispatch_bindings WHERE request_id=%s",
        (binding["request_id"],),
    ).fetchone()
    if stored is None or stored["semantic_input_json"] is None:
        raise OperationRefused("author_semantic_input_missing")
    snapshot = json.loads(stored["semantic_input_json"])
    if digest(prompt_from_snapshot(binding, snapshot).encode()) != binding["prompt_sha256"]:
        raise OperationRefused("semantic_input_digest")
    validate_authored_row(row, snapshot["constraints"])


def rubric_bytes() -> bytes:
    raw = (resource_root() / REVIEW_RUBRIC_RELATIVE).read_bytes()
    if digest(raw) != REVIEW_RUBRIC_SHA256:
        raise OperationRefused("rubric_digest")
    return raw


def _canonical_artifact(conn, sha256):
    if not isinstance(sha256, str) or not HEX64.fullmatch(sha256):
        raise OperationRefused("preparation_artifact_digest")
    row = conn.execute(
        "SELECT payload FROM fleet_comms_artifact_blobs WHERE sha256=%s AND octet_length(payload) BETWEEN 1 AND 16384", (sha256,),
    ).fetchone()
    if row is None:
        raise OperationRefused("source_qualified_target_required")
    raw = bytes(row["payload"])
    if not 0 < len(raw) <= 16384 or digest(raw) != sha256:
        raise OperationRefused("preparation_artifact_digest")
    try:
        value = json.loads(raw)
        if canonical_bytes(value) != raw:
            raise OperationRefused("preparation_artifact_noncanonical")
    except (ValueError, UnicodeError) as exc:
        raise OperationRefused("preparation_artifact_noncanonical") from exc
    return value


def _validate_evidence(evidence, constraints):
    _keys(evidence, {"target_sha256", "a4_receipt_sha256", "a5_receipt_sha256", "source_role",
                     "claim_type", "support_decision", "locator_decision", "evidence_locator_sha256s"}, "target_evidence_required")
    target = constraints["target"]
    if evidence["target_sha256"] != digest(canonical_bytes(target)) or evidence["claim_type"] != target["claim_type"]:
        raise OperationRefused("target_evidence_binding")
    # These decisions come from the trusted preparer's canonical source-qualified
    # artifact, not a caller's observation or a Sources word-success flag.
    if evidence["support_decision"] != "source_supported" or evidence["locator_decision"] != "exact_sufficient":
        raise OperationRefused("linguistic_authority_unresolved")
    _choice(evidence["source_role"], {"explicit_rule", "correct_example", "corrected_example", "historical_or_literary_excerpt",
                                     "quotation", "metalinguistic_mention"}, "target_source_role")
    if target["claim_type"] == "prescriptive_rule" and evidence["source_role"] != "explicit_rule":
        raise OperationRefused("normative_source_role_required")
    if target["claim_type"] == "human_correction_pair" and evidence["source_role"] != "corrected_example":
        raise OperationRefused("correction_source_role_required")
    locators = evidence["evidence_locator_sha256s"]
    if (not isinstance(locators, list) or not 1 <= len(locators) <= 4
            or any(not isinstance(v, str) or not HEX64.fullmatch(v) for v in locators)
            or len(locators) != len(set(locators))):
        raise OperationRefused("target_evidence_locators")
    for key, relative in (("a4_receipt_sha256", A4_RELATIVE), ("a5_receipt_sha256", A5_RELATIVE)):
        if evidence[key] != digest((resource_root() / relative).read_bytes()):
            raise OperationRefused("target_upstream_binding")


def _resolve_preparation(conn, binding, snapshot):
    expected = {"preparation_sha256"}
    if binding["role"] == "reviewer":
        expected |= {"authored_row", "rubric_sha256"}
    _keys(snapshot, expected, "canonical_preparation_reference_required")
    prepared = _canonical_artifact(conn, snapshot["preparation_sha256"])
    _keys(prepared, {"schema", "slot_id", "packet_sha256", "constraints", "evidence"}, "preparation_artifact_shape")
    if prepared["schema"] != "v4-admitted-linguistic-context.v1":
        raise OperationRefused("preparation_artifact_schema")
    from learn_ukrainian_v4_runtime.v4_execution_origin import load_frozen_slot

    slot = load_frozen_slot(prepared["slot_id"])
    validate_constraints(prepared["constraints"])
    if (slot["stratum"] != prepared["constraints"]["stratum"]
            or prepared["packet_sha256"] != binding["packet_sha256"]
            or (binding["role"] == "author" and prepared["slot_id"] != binding["slot_id"])):
        raise OperationRefused("target_assignment_binding")
    _validate_evidence(prepared["evidence"], prepared["constraints"])
    return {**snapshot, "constraints": prepared["constraints"], "evidence": prepared["evidence"]}


def prompt_from_snapshot(binding: dict, snapshot: dict) -> str:
    if (not isinstance(snapshot, dict) or not isinstance(snapshot.get("preparation_sha256"), str)
            or not HEX64.fullmatch(snapshot["preparation_sha256"])):
        raise OperationRefused("semantic_preparation_digest")
    if binding["role"] == "author":
        if set(snapshot) != {"constraints", "evidence", "preparation_sha256"}:
            raise OperationRefused("author_snapshot")
        validate_constraints(snapshot["constraints"])
        _validate_evidence(snapshot["evidence"], snapshot["constraints"])
        payload = {
            "role": "author",
            "slot_id": binding["slot_id"],
            "packet_sha256": binding["packet_sha256"],
            "constraints": snapshot["constraints"],
            "target_evidence": snapshot["evidence"],
            "preparation_sha256": snapshot["preparation_sha256"],
        }
        instructions = (
            "Author one original row in proper Ukrainian (language uk), satisfying the actual atomic target facts, "
            "evidence and scope in every admitted constraint and the fixed linguistic contract below. "
            "Fluency alone is insufficient. If authority or context is unsupported or unknown, abstain: "
            "do not emit V4-AUTHOR-ROW; the existing missing-row refusal terminates execution. "
            "Otherwise emit V4-AUTHOR-ROW: followed by its JSON object.\n" + rubric_bytes().decode()
        )
    elif binding["role"] == "reviewer":
        if set(snapshot) != {"authored_row", "constraints", "rubric_sha256", "evidence", "preparation_sha256"}:
            raise OperationRefused("reviewer_snapshot")
        validate_constraints(snapshot["constraints"])
        _validate_evidence(snapshot["evidence"], snapshot["constraints"])
        row = snapshot["authored_row"]
        if not isinstance(row, dict) or not isinstance(row.get("row_text"), str) or not row["row_text"]:
            raise OperationRefused("authored_row_required")
        if not set(row) <= {"row_text", "explanation", "answer", "instruction"}:
            raise OperationRefused("authored_row_keys")
        if any(not isinstance(value, str) for value in row.values()):
            raise OperationRefused("authored_row_values")
        validate_authored_row(row, snapshot["constraints"])
        rubric = rubric_bytes()
        if snapshot["rubric_sha256"] != digest(rubric) or binding["rubric_sha256"] != digest(rubric):
            raise OperationRefused("rubric_digest")
        payload = {
            "role": "reviewer",
            "authored_row": row,
            "constraints": snapshot["constraints"],
            "target_evidence": snapshot["evidence"],
            "preparation_sha256": snapshot["preparation_sha256"],
            "rubric": rubric.decode(),
            "authorship_receipt_sha256": binding["authorship_receipt_sha256"],
        }
        instructions = (
            "Independently evaluate the actual authored row against the bound target facts, evidence, context, "
            "scope and fixed rubric, including originality. A Sources word/morphology pass is not syntax or "
            "whole-sentence semantic proof. Unknown authority requires FAIL, never a guessed norm. "
            "Emit exactly V4-REVIEW-VERDICT: PASS or V4-REVIEW-VERDICT: FAIL."
        )
    else:
        raise OperationRefused("operation_role")
    return (
        f"V4_PROMPT_PROFILE={binding['prompt_profile']}\n{instructions}\nV4-SEMANTIC-INPUT: "
        + json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        + "\n"
    )


def freeze_semantic_input(conn, *, request_id: str, snapshot: dict) -> None:
    """Trusted preparation of an already assigned binding, never an API route.

    The existing private preparation adapter must first qualify source evidence
    and store its expression-free admitted context in the owned artifact store.
    This function accepts only its digest (plus reviewer row/rubric references),
    resolves and validates canonical bytes, then locks the exact semantic input.
    It never qualifies a source occurrence, writes a target, or accepts a public
    caller's constraints/verified flag. A4/A5 structural receipts alone cannot
    supply this artifact. HTTP authorization remains opaque and unchanged.
    """
    with conn.transaction():
        request = conn.execute("SELECT state FROM requests WHERE request_id=%s FOR UPDATE", (request_id,)).fetchone()
        row = conn.execute(
            "SELECT * FROM v4_execution_dispatch_bindings WHERE request_id=%s FOR UPDATE", (request_id,)
        ).fetchone()
        if request is None or request["state"] != "queued" or row is None or row["semantic_input_json"] is not None:
            raise OperationRefused("assignment_not_freezable")
        binding = json.loads(row["record_json"])
        if digest(canonical_bytes(binding)) != row["record_sha256"]:
            raise OperationRefused("binding_digest")
        snapshot = _resolve_preparation(conn, binding, snapshot)
        prompt = prompt_from_snapshot(binding, snapshot)
        if binding["role"] == "reviewer":
            authorship = conn.execute(
                "SELECT record_json,task_id,run_id FROM v4_authorship_receipts WHERE receipt_id=%s",
                (binding["authorship_receipt_id"],),
            ).fetchone()
            if authorship is None:
                raise OperationRefused("authorship_unresolved")
            receipt = json.loads(authorship["record_json"])
            if digest(canonical_bytes(receipt)) != binding["authorship_receipt_sha256"]:
                raise OperationRefused("authorship_receipt_digest")
            if digest(snapshot["authored_row"]["row_text"].encode()) != receipt["row_content_sha256"]:
                raise OperationRefused("authored_row_digest")
            # Resolve the complete authored object and constraints from the
            # parent's captured bytes, not from a preparer's row-text assertion.
            origin = conn.execute(
                """SELECT o.record_json AS observation,o.record_sha256 AS observation_sha256,b.record_json AS binding,
                b.semantic_input_json AS snapshot,b.record_sha256 AS binding_sha256,a.payload AS capture
                FROM v4_execution_observations o
                JOIN v4_execution_attempts t ON t.attempt_id=(o.record_json::jsonb->>'attempt_id')
                JOIN v4_execution_dispatch_bindings b ON b.request_id=t.request_id
                JOIN fleet_comms_artifact_blobs a ON a.sha256=(o.record_json::jsonb->>'raw_capture_sha256')
                WHERE o.task_id=%s AND o.run_id=%s AND o.role='author'""",
                (authorship["task_id"], authorship["run_id"]),
            ).fetchone()
            if origin is None:
                raise OperationRefused("authored_capture_unresolved")
            from learn_ukrainian_v4_runtime.child_runtime import CapturedChild, parse_child

            observation = json.loads(origin["observation"])
            author_binding = json.loads(origin["binding"])
            author_snapshot = json.loads(origin["snapshot"])
            if (digest(canonical_bytes(observation)) != origin["observation_sha256"]
                    or digest(canonical_bytes(author_binding)) != origin["binding_sha256"]
                    or digest(prompt_from_snapshot(author_binding, author_snapshot).encode()) != author_binding["prompt_sha256"]
                    or observation["prompt_sha256"] != author_binding["prompt_sha256"]
                    or author_binding["packet_sha256"] != binding["packet_sha256"]):
                raise OperationRefused("reviewer_semantic_origin_mismatch")
            raw = bytes(origin["capture"])
            if digest(raw) != observation["raw_capture_sha256"]:
                raise OperationRefused("authored_capture_digest")
            captured = CapturedChild(
                request_id=author_binding["request_id"],
                attempt_id=observation["attempt_id"],
                argv_sha256=observation["argv_digest"],
                prompt_sha256=observation["prompt_sha256"],
                stdout=raw,
                stderr=b"",
                returncode=observation["process_returncode"],
                harness=observation["harness"],
            )
            if (
                parse_child(captured, author_binding)["row"] != snapshot["authored_row"]
                or any(author_snapshot[key] != snapshot[key] for key in ("constraints", "evidence", "preparation_sha256"))
            ):
                raise OperationRefused("reviewer_semantic_origin_mismatch")
        binding["prompt_sha256"] = digest(prompt.encode())
        body = canonical_bytes(binding)
        conn.execute(
            "UPDATE v4_execution_dispatch_bindings SET record_json=%s,record_sha256=%s,semantic_input_json=%s WHERE request_id=%s",
            (body.decode(), digest(body), canonical_bytes(snapshot).decode(), request_id),
        )
