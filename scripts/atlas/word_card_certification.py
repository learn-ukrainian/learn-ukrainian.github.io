"""Word Card Certification Guard (#10513 / #8977).

Enforces strict refusal of uncertified, draft, missing, or mismatched cards
at every acceptance and dataset-export entry point.

Spec: docs/atlas/word-cards/schema.md, docs/atlas/word-cards/acceptance-export-path-census.json
Parent: #8977 (Word cards portfolio), #6321 (open-model-data)
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[2]
PATH_CENSUS_PATH = PROJECT_ROOT / "docs" / "atlas" / "word-cards" / "acceptance-export-path-census.json"


class UncertifiedCardRefusal(RuntimeError):
    """Raised when an uncertified, draft, or invalidated card is presented for acceptance or export."""


def is_valid_sha256(val: Any) -> bool:
    """Return True if val is a 64-character lowercase hexadecimal string."""
    if not isinstance(val, str) or isinstance(val, bool) or len(val) != 64:
        return False
    return all(c in "0123456789abcdef" for c in val.lower())


CANONICAL_RULES_VERSIONS: tuple[str, ...] = ("rules-v1-draft", "rules-v1")
CANONICAL_NORMALISER_VERSIONS: tuple[str, ...] = ("norm-v1",)


CANONICAL_SOURCE_SNAPSHOTS: dict[str, str] = {
    "vesum": "53923150073b4fc7bee419fe7b071acbe17b6a9aba76cfb2d0336c95f5188680",
    "ulif": "fe9f52cb261736443f511a85b52e8ee6fe05b51165c56384cfa969b411429b98",
    "puls": "98fc5be3e986f944fcf84cad34325ecbf770d22fc2dc54caa4b548f06e7f6b5a",
    "puls_cefr": "98fc5be3e986f944fcf84cad34325ecbf770d22fc2dc54caa4b548f06e7f6b5a",
    "frazeolohichnyi": "9889123be2ce073528ee038c66824ba35af118d2b702b4e8cb0723156015f108",
    "wiktionary": "ead3e1bc521293fde1cdbc3767d0131aca41e6b2e1701e93de17f919e3a89d69",
    "atlas0": "fcf802bda35dd4cd99e95317da0f4a1fa9315024befc83e73673c106278ebfca",
    "atlas_curated": "14d56cb53fdf14dd7e8b0155a2f1770f740cff93b3e10f8f0eb5bfb67be72f99",
}

CANONICAL_V_SNAPSHOTS: dict[str, str] = {
    "vesum": "53923150073b4fc7bee419fe7b071acbe17b6a9aba76cfb2d0336c95f5188680",
}

CANONICAL_I_SNAPSHOTS: dict[str, str] = {
    "identity_registry": "d19b02adb497e1807a4f0e27b1f37e79f955f1a542c0331b389858b7a946c253",
    "identity": "d19b02adb497e1807a4f0e27b1f37e79f955f1a542c0331b389858b7a946c253",
    "registry": "d19b02adb497e1807a4f0e27b1f37e79f955f1a542c0331b389858b7a946c253",
}

CANONICAL_O_OVERLAY_SNAPSHOTS: dict[str, str] = {
    "overlay": "6058ca798ad8327afd49d8c4cd29f4393e3c03e9c9dda93bc704ac358529d84a",
}

CANONICAL_O_SUPPRESSION_SNAPSHOTS: dict[str, str] = {
    "suppressions": "1b555453b7b942728992cc8a065e4279af184d5656f7a444e14ad4ced09b0d61",
    "suppression_selectors": "1b555453b7b942728992cc8a065e4279af184d5656f7a444e14ad4ced09b0d61",
}

PERMISSIONS_REGISTER_PATH = PROJECT_ROOT / "docs" / "sources" / "permissions-register.yaml"


def get_canonical_register_snapshot() -> str | None:
    """Return authoritative permissions register snapshot hash (AC-04), or None if unavailable."""
    if PERMISSIONS_REGISTER_PATH.is_file():
        try:
            return hashlib.sha256(PERMISSIONS_REGISTER_PATH.read_bytes()).hexdigest()
        except Exception:
            return None
    return None


CANONICAL_R_REGISTER_SNAPSHOTS: tuple[str, ...] = ("register", "permissions_register")
REVIEW_EVIDENCE_PATH = PROJECT_ROOT / "docs" / "atlas" / "word-cards" / "review-evidence-ledger.json"


def get_canonical_review_evidence() -> dict[str, Any]:
    """Return authoritative review evidence ledger mapping card_id to approved review metadata (AC-04)."""
    if REVIEW_EVIDENCE_PATH.is_file():
        try:
            with open(REVIEW_EVIDENCE_PATH, encoding="utf-8") as f:
                data = json.load(f)
            return dict(data.get("approved_reviews", {}))
        except Exception:
            return {}
    return {}


def compute_inputs_digest(inputs: dict[str, Any]) -> str:
    """Return canonical digest of build.inputs dictionary."""
    return "in_" + hashlib.sha256(
        json.dumps(inputs, sort_keys=True, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    ).hexdigest()[:24]


def get_canonical_source_snapshots() -> dict[str, str]:
    """Return canonical source snapshot digests from schema and ledger (AC-04)."""
    snapshots: dict[str, str] = dict(CANONICAL_SOURCE_SNAPSHOTS)
    ledger_path = PROJECT_ROOT / "docs" / "atlas" / "word-cards" / "source-completeness-ledger.json"
    if ledger_path.is_file():
        try:
            with open(ledger_path, encoding="utf-8") as f:
                data = json.load(f)
            for item in data.get("partitions", {}).get("verified-complete", []):
                src_id = item.get("source_id")
                sha = item.get("canonical_sha256")
                if src_id and sha and is_valid_sha256(sha):
                    snapshots[src_id] = sha
        except Exception:
            pass
    return snapshots


def load_path_census() -> dict[str, Any]:
    """Load the frozen acceptance and export path census (AC-01)."""
    if not PATH_CENSUS_PATH.exists():
        raise FileNotFoundError(f"Path census not found at {PATH_CENSUS_PATH}")
    with open(PATH_CENSUS_PATH, encoding="utf-8") as f:
        return json.load(f)


def verify_card_certification(
    card: dict[str, Any],
    *,
    required_approval: str | tuple[str, ...] | list[str] | set[str] = "dataset",
    expected_snapshots: dict[str, str] | None = None,
    expected_reviews: dict[str, Any] | None = None,
) -> tuple[bool, str]:
    """Verify that a word card meets strict exact-artifact certification requirements (AC-02, AC-04).

    Returns (is_certified, reason).

    Criteria:
    1. Card must be an active or valid lexeme/mwe/proper_name record.
    2. quality.identity_confidence must not be 'unresolved' or 'low'.
    3. quality.linguistic_review.status must be 'reviewed'.
    4. required_approval (e.g. 'dataset') must be in quality.linguistic_review.approved_for.
    5. build.card_version must match the canonical SHA-256 of public card fields.
    6. If expected_snapshots is given, build.inputs.S hashes must strictly match.
    7. Suppressed cards or assertions must not be exported as active facts.
    """
    if not isinstance(card, dict):
        return False, f"Card must be a dictionary, got {type(card).__name__}"

    card_id = card.get("card_id", "unknown")

    # 1. State check (F1: must be active)
    state = card.get("state")
    if state == "suppressed":
        return False, f"Card {card_id} is suppressed"
    if state != "active":
        return False, f"Card {card_id} state is '{state}', must be 'active'"

    # 2. Quality structure check (F6: type safety)
    quality = card.get("quality")
    if not isinstance(quality, dict):
        return False, f"Card {card_id} missing quality object"

    # 3. Identity confidence check
    confidence = quality.get("identity_confidence")
    if confidence in ("unresolved", "low", None):
        return False, f"Card {card_id} has uncertified identity confidence: {confidence}"

    # 4. Independent linguistic review check (F6: type safety)
    review = quality.get("linguistic_review")
    if not isinstance(review, dict):
        return False, f"Card {card_id} missing linguistic_review record"

    record = review.get("record")
    if not isinstance(record, str) or not record.strip():
        return False, f"Card {card_id} linguistic_review missing valid record"

    status = review.get("status")
    if status != "reviewed":
        return False, f"Card {card_id} linguistic_review status is '{status}', must be 'reviewed'"

    approved_for = review.get("approved_for")
    if not isinstance(approved_for, (list, tuple, set)):
        return False, f"Card {card_id} approved_for must be a collection, got: {type(approved_for).__name__}"

    if isinstance(required_approval, str):
        if required_approval not in approved_for:
            return (
                False,
                f"Card {card_id} review approval list {approved_for} does not contain required '{required_approval}'",
            )
    elif isinstance(required_approval, (tuple, list, set)) and not any(
        req in approved_for for req in required_approval
    ):
        return (
            False,
            f"Card {card_id} review approval list {approved_for} does not contain any required approval from {list(required_approval)}",
        )

    # 5. Build and snapshot verification (F3: rules and source freshness)
    build = card.get("build")
    if not isinstance(build, dict):
        return False, f"Card {card_id} missing build object"

    rules_version = build.get("rules_version")
    if not isinstance(rules_version, str) or rules_version not in CANONICAL_RULES_VERSIONS:
        return (
            False,
            f"Card {card_id} has invalid or non-canonical rules_version: {rules_version!r} (expected one of {CANONICAL_RULES_VERSIONS})",
        )

    inputs = build.get("inputs")
    if not isinstance(inputs, dict):
        return False, f"Card {card_id} missing inputs dictionary in build"

    # Validate all input categories (S, V, I, O, R) (F1 / R5)
    required_categories = ("S", "V", "I", "O", "R")
    for cat in required_categories:
        cat_inputs = inputs.get(cat)
        if not isinstance(cat_inputs, dict) or not cat_inputs:
            return False, f"Card {card_id} missing non-empty {cat!r} inputs in build.inputs"

    source_inputs = inputs["S"]
    for src_id, src_meta in source_inputs.items():
        if not isinstance(src_meta, dict):
            return False, f"Card {card_id} source snapshot {src_id} meta must be a dictionary"
        sha = src_meta.get("content_sha256")
        if not is_valid_sha256(sha):
            return (
                False,
                f"Card {card_id} source snapshot {src_id} has invalid content_sha256 (must be 64-char hex SHA-256): {sha!r}",
            )

    v_inputs = inputs["V"]
    for v_id, v_meta in v_inputs.items():
        if not isinstance(v_meta, dict):
            return False, f"Card {card_id} V input {v_id} meta must be a dictionary"
        sha = v_meta.get("content_sha256")
        if not is_valid_sha256(sha):
            return (
                False,
                f"Card {card_id} V input {v_id} has invalid content_sha256 (must be 64-char hex SHA-256): {sha!r}",
            )

    i_inputs = inputs["I"]
    for i_id, i_meta in i_inputs.items():
        if not isinstance(i_meta, dict):
            return False, f"Card {card_id} I input {i_id} meta must be a dictionary"
        sha = i_meta.get("content_sha256")
        if not is_valid_sha256(sha):
            return (
                False,
                f"Card {card_id} I input {i_id} has invalid content_sha256 (must be 64-char hex SHA-256): {sha!r}",
            )

    o_inputs = inputs["O"]
    for o_id, o_meta in o_inputs.items():
        if not isinstance(o_meta, dict):
            return False, f"Card {card_id} O input {o_id} meta must be a dictionary"
        sha = o_meta.get("content_sha256")
        if not is_valid_sha256(sha):
            return (
                False,
                f"Card {card_id} O input {o_id} has invalid content_sha256 (must be 64-char hex SHA-256): {sha!r}",
            )

    r_inputs = inputs["R"]
    for r_id, r_meta in r_inputs.items():
        if not isinstance(r_meta, dict):
            return False, f"Card {card_id} R input {r_id} meta must be a dictionary"
        sha = r_meta.get("content_sha256")
        version = r_meta.get("version")
        if sha is not None:
            if not is_valid_sha256(sha):
                return (
                    False,
                    f"Card {card_id} R input {r_id} has invalid content_sha256 (must be 64-char hex SHA-256): {sha!r}",
                )
        elif version is not None:
            if not isinstance(version, str) or isinstance(version, bool) or not version.strip():
                return (
                    False,
                    f"Card {card_id} R input {r_id} has invalid version string: {version!r}",
                )
        else:
            return (
                False,
                f"Card {card_id} R input {r_id} must have content_sha256 or version",
            )

    # F1: Recompute schema.md section 11 canonical public-card digest
    # Exclude build object since card_version is stored within build.
    body = {k: v for k, v in card.items() if k != "build"}
    expected_cv = "cv_" + hashlib.sha256(
        json.dumps(body, sort_keys=True, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    ).hexdigest()[:24]

    card_version = build.get("card_version")
    if card_version != expected_cv:
        return False, f"Card {card_id} card_version mismatch: got {card_version}, expected {expected_cv}"

    # 6. Snapshot correspondence and freshness verification (AC-04 / F2 / R5-F1 / R6-F1 / R7-F1)
    # Category S: Sources
    sources_to_check = get_canonical_source_snapshots()
    if expected_snapshots:
        sources_to_check.update(expected_snapshots)

    for src_id, src_meta in source_inputs.items():
        if src_id not in sources_to_check:
            return (
                False,
                f"Card {card_id} has unrecognized or uncertified source '{src_id}' with no authoritative snapshot binding",
            )
        expected_hash = sources_to_check[src_id]
        actual_hash = src_meta.get("content_sha256")
        if actual_hash != expected_hash:
            return (
                False,
                f"Card {card_id} snapshot mismatch for S.{src_id}: expected {expected_hash}, got {actual_hash}",
            )

    # Category V: VESUM
    v_expected = dict(CANONICAL_V_SNAPSHOTS)
    if expected_snapshots:
        for k, v in expected_snapshots.items():
            if k in CANONICAL_V_SNAPSHOTS:
                v_expected[k] = v

    if "vesum" not in v_inputs:
        return False, f"Card {card_id} missing required 'vesum' binding in build.inputs.V"

    for v_id, v_meta in v_inputs.items():
        if v_id not in v_expected:
            return (
                False,
                f"Card {card_id} has unrecognized or uncertified V input '{v_id}' with no authoritative snapshot binding",
            )
        expected_hash = v_expected[v_id]
        actual_hash = v_meta.get("content_sha256")
        if actual_hash != expected_hash:
            return (
                False,
                f"Card {card_id} snapshot mismatch for V.{v_id}: expected {expected_hash}, got {actual_hash}",
            )

    # Category I: Identity Registry
    i_expected = dict(CANONICAL_I_SNAPSHOTS)
    if expected_snapshots:
        for k, v in expected_snapshots.items():
            if k in CANONICAL_I_SNAPSHOTS:
                i_expected[k] = v

    for i_id, i_meta in i_inputs.items():
        if i_id not in i_expected:
            return (
                False,
                f"Card {card_id} has unrecognized or uncertified I input '{i_id}' with no authoritative snapshot binding",
            )
        expected_hash = i_expected[i_id]
        actual_hash = i_meta.get("content_sha256")
        if actual_hash != expected_hash:
            return (
                False,
                f"Card {card_id} snapshot mismatch for I.{i_id}: expected {expected_hash}, got {actual_hash}",
            )

    if not any(k in i_inputs for k in ("identity_registry", "identity", "registry")):
        return False, f"Card {card_id} missing required identity registry binding in build.inputs.I"

    # Category O: Overlays & Suppressions
    overlay_expected = dict(CANONICAL_O_OVERLAY_SNAPSHOTS)
    suppressions_expected = dict(CANONICAL_O_SUPPRESSION_SNAPSHOTS)
    if expected_snapshots:
        for k, v in expected_snapshots.items():
            if k in CANONICAL_O_OVERLAY_SNAPSHOTS:
                overlay_expected[k] = v
            if k in CANONICAL_O_SUPPRESSION_SNAPSHOTS:
                suppressions_expected[k] = v

    for o_id, o_meta in o_inputs.items():
        if o_id in overlay_expected:
            expected_hash = overlay_expected[o_id]
        elif o_id in suppressions_expected:
            expected_hash = suppressions_expected[o_id]
        else:
            return (
                False,
                f"Card {card_id} has unrecognized or uncertified O input '{o_id}' with no authoritative snapshot binding",
            )
        actual_hash = o_meta.get("content_sha256")
        if actual_hash != expected_hash:
            return (
                False,
                f"Card {card_id} snapshot mismatch for O.{o_id}: expected {expected_hash}, got {actual_hash}",
            )

    if "overlay" not in o_inputs:
        return False, f"Card {card_id} missing required 'overlay' binding in build.inputs.O"

    if not any(k in o_inputs for k in ("suppressions", "suppression_selectors")):
        return False, f"Card {card_id} missing required suppressions binding in build.inputs.O"

    # Category R: Rules, Normaliser, Register
    # Category R: Rules, Normaliser, Register
    register_expected: dict[str, str] = {}
    current_reg_sha = get_canonical_register_snapshot()
    if current_reg_sha:
        register_expected["register"] = current_reg_sha
        register_expected["permissions_register"] = current_reg_sha
    if expected_snapshots:
        for k, v in expected_snapshots.items():
            if k in CANONICAL_R_REGISTER_SNAPSHOTS:
                register_expected[k] = v

    if "rules" not in r_inputs:
        return False, f"Card {card_id} missing required 'rules' binding in build.inputs.R"

    if not any(k in r_inputs for k in ("normaliser", "normalizer")):
        return False, f"Card {card_id} missing required normaliser binding in build.inputs.R"

    if not any(k in r_inputs for k in ("register", "permissions_register")):
        return False, f"Card {card_id} missing required register binding in build.inputs.R"

    for r_id, r_meta in r_inputs.items():
        if r_id == "rules":
            ver = r_meta.get("version")
            if ver != rules_version:
                return (
                    False,
                    f"Card {card_id} R.rules version '{ver}' does not match build.rules_version '{rules_version}'",
                )
            if ver not in CANONICAL_RULES_VERSIONS:
                return (
                    False,
                    f"Card {card_id} R.rules version '{ver}' is not a canonical rules version ({CANONICAL_RULES_VERSIONS})",
                )
        elif r_id in ("normaliser", "normalizer"):
            ver = r_meta.get("version")
            if ver not in CANONICAL_NORMALISER_VERSIONS:
                return (
                    False,
                    f"Card {card_id} R.{r_id} version '{ver}' is not a canonical normaliser version ({CANONICAL_NORMALISER_VERSIONS})",
                )
        elif r_id in ("register", "permissions_register"):
            expected_hash = register_expected.get(r_id) or register_expected.get("register")
            if not expected_hash:
                return (
                    False,
                    f"Card {card_id} permissions register authority '{PERMISSIONS_REGISTER_PATH}' is missing or unreadable",
                )
            actual_hash = r_meta.get("content_sha256")
            if actual_hash != expected_hash:
                return (
                    False,
                    f"Card {card_id} snapshot mismatch for R.{r_id}: expected {expected_hash}, got {actual_hash}",
                )
        else:
            return (
                False,
                f"Card {card_id} has unrecognized or uncertified R input '{r_id}' with no authoritative binding",
            )

    # 7. Authoritative review evidence verification (R10/R11 Finding 1: exact artifact binding)
    review_evidence = get_canonical_review_evidence()
    if expected_reviews:
        review_evidence.update(expected_reviews)

    evidence_entry = review_evidence.get(card_id) or review_evidence.get(record)
    if not evidence_entry:
        return (
            False,
            f"Card {card_id} review record '{record}' has no authoritative review evidence binding it to this card",
        )

    if not isinstance(evidence_entry, dict):
        return (
            False,
            f"Card {card_id} authoritative review evidence must be a dictionary record, got {type(evidence_entry).__name__}",
        )

    approved_card_id = evidence_entry.get("card_id")
    if approved_card_id and approved_card_id != card_id:
        return (
            False,
            f"Card {card_id} does not match authoritative review evidence card_id '{approved_card_id}'",
        )
    approved_record = evidence_entry.get("record")
    if approved_record and approved_record != record:
        return (
            False,
            f"Card {card_id} review record '{record}' does not match authoritative review evidence record '{approved_record}'",
        )
    approved_rules = evidence_entry.get("rules_version")
    if not approved_rules:
        return (
            False,
            f"Card {card_id} authoritative review evidence missing approved rules_version",
        )
    if rules_version != approved_rules:
        return (
            False,
            f"Card {card_id} build rules_version '{rules_version}' does not match authoritative review evidence '{approved_rules}'",
        )
    approved_inputs = evidence_entry.get("inputs")
    approved_inputs_digest = evidence_entry.get("inputs_digest")
    if approved_inputs is not None:
        if inputs != approved_inputs:
            return (
                False,
                f"Card {card_id} build inputs do not match authoritative review evidence",
            )
    elif approved_inputs_digest is not None:
        computed_inputs_digest = compute_inputs_digest(inputs)
        if computed_inputs_digest != approved_inputs_digest:
            return (
                False,
                f"Card {card_id} build inputs digest '{computed_inputs_digest}' does not match authoritative review evidence '{approved_inputs_digest}'",
            )
    else:
        return (
            False,
            f"Card {card_id} authoritative review evidence missing approved inputs manifest",
        )
    approved_cv = evidence_entry.get("card_version")
    if not approved_cv:
        return (
            False,
            f"Card {card_id} authoritative review evidence missing approved card_version",
        )

    if card_version != approved_cv:
        return (
            False,
            f"Card {card_id} content was modified after review: card_version '{card_version}' does not match authoritative review evidence '{approved_cv}'",
        )

    return True, "Certified"


def refuse_uncertified_dataset_export(
    manifest_or_cards: dict[str, Any] | list[dict[str, Any]],
    *,
    allow_draft: bool = False,
    expected_snapshots: dict[str, str] | None = None,
    expected_reviews: dict[str, Any] | None = None,
) -> None:
    """Refuse open dataset export if candidate data lacks exact-artifact certification (AC-02).

    Raises UncertifiedCardRefusal on any uncertified, unreviewed, or legacy manifest input.
    """
    if allow_draft:
        return

    if expected_snapshots is None:
        expected_snapshots = get_canonical_source_snapshots()

    if expected_reviews is None:
        expected_reviews = get_canonical_review_evidence()

    # Check for legacy manifest structure and gather all candidate items (F2 parity)
    items_to_check: list[dict[str, Any]] = []

    if isinstance(manifest_or_cards, dict):
        has_entries = "entries" in manifest_or_cards
        has_cards = "cards" in manifest_or_cards

        # Legacy Atlas manifest structure check
        if has_entries and not manifest_or_cards.get("card_certification"):
            raise UncertifiedCardRefusal(
                "REFUSED: Legacy Atlas manifest entries lack exact-artifact certification. "
                "scripts/lexicon/export_open_dataset.py refuses to export uncertified cards (AC-02 / Issue #10513)."
            )

        if has_cards:
            cards_val = manifest_or_cards.get("cards")
            if not isinstance(cards_val, (list, tuple)):
                raise UncertifiedCardRefusal("REFUSED: 'cards' field must be a list in manifest.")
            items_to_check.extend(cards_val)

        if has_entries:
            entries_val = manifest_or_cards.get("entries")
            if not isinstance(entries_val, (list, tuple)):
                raise UncertifiedCardRefusal("REFUSED: 'entries' field must be a list in manifest.")
            items_to_check.extend(entries_val)
    elif isinstance(manifest_or_cards, (list, tuple)):
        items_to_check.extend(manifest_or_cards)
    else:
        raise UncertifiedCardRefusal(
            f"REFUSED: Invalid manifest or cards payload type: {type(manifest_or_cards).__name__}."
        )

    if not items_to_check:
        raise UncertifiedCardRefusal(
            "REFUSED: Empty card inventory provided for dataset export (no certified cards found)."
        )

    # Check every individual card
    for item in items_to_check:
        if not isinstance(item, dict) or "card_id" not in item:
            lemma = item.get("lemma", "unknown") if isinstance(item, dict) else "unknown"
            raise UncertifiedCardRefusal(
                f"REFUSED: Entry '{lemma}' is a legacy uncertified manifest entry, not a certified word card."
            )

        certified, reason = verify_card_certification(
            item,
            required_approval="dataset",
            expected_snapshots=expected_snapshots,
            expected_reviews=expected_reviews,
        )
        if not certified:
            raise UncertifiedCardRefusal(
                f"REFUSED: Card '{item.get('card_id')}' cannot be exported: {reason}. "
                "Dataset export requires 100% certified cards (Issue #10513)."
            )
