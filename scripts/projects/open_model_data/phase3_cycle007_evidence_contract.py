#!/usr/bin/env python3
"""Frozen Cycle 007 evidence schema/contract primitives.

This module is the single source of truth for the Cycle 007 evidence-ID
recipe, the closed evidence-channel vocabulary, and the per-channel claim
boundary defined by ``batch_state/phase3-cycle007-source-grounded-amendment-v1.md``.
Both the evidence-sidecar compiler and the evidence validator import it so
the ID recipe and role boundaries can never drift between the two.

No network access, no private row content, and no provider output belongs in
this module. It only knows shapes and hashes.
"""

from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping, Sequence
from typing import Any

EVIDENCE_SCHEMA_VERSION = "phase3_cycle007_evidence_v1"

# Amendment step 1: the ten closed, explicit evidence channels. A channel not
# in this tuple can never be compiled or validated.
CHANNELS: tuple[str, ...] = (
    "pravopys_2026_normative",
    "pravopys_2019_comparison",
    "vesum_attestation",
    "antonenko_style",
    "ua_gec_calque",
    "heritage_attestation",
    "ukrainian_corpus_occurrence",
    "textbook_explanation",
    "russian_shadow_suspicion",
    "source_metadata",
)

# Amendment step 8: the closed retrieval-status vocabulary. Anything other
# than "attested" is a negative or unresolved result — never normalized into
# positive evidence.
STATUSES: tuple[str, ...] = (
    "attested",
    "not_found",
    "ambiguous",
    "incomplete",
    "parse_error",
    "unavailable",
)
NEGATIVE_STATUSES: frozenset[str] = frozenset(STATUSES) - {"attested"}

# Amendment step 8 ("support is a closed claim-boundary value") plus step 1
# ("attestation or occurrence cannot satisfy a normative-rule claim"). Every
# channel is bound to the exact subset of these values it may ever emit;
# "no_conclusion" is the universal negative/unresolved value.
SUPPORTS: tuple[str, ...] = (
    "normative_rule",
    "comparison_only",
    "attestation",
    "archaic_attestation",
    "occurrence",
    "style_guidance",
    "calque_flag",
    "explanation_context",
    "suspicion",
    "metadata_only",
    "no_conclusion",
)

CHANNEL_SUPPORTS: dict[str, frozenset[str]] = {
    "pravopys_2026_normative": frozenset({"normative_rule", "no_conclusion"}),
    "pravopys_2019_comparison": frozenset({"comparison_only", "no_conclusion"}),
    # check_modern_form fields are treated as vesum_attestation subclaims:
    # "archaic_attestation" carries has_only_archaic_form so archaic-only risk
    # review is mechanically selectable without ever condemning a VESUM miss.
    "vesum_attestation": frozenset({"attestation", "archaic_attestation", "no_conclusion"}),
    "antonenko_style": frozenset({"style_guidance", "no_conclusion"}),
    "ua_gec_calque": frozenset({"calque_flag", "no_conclusion"}),
    "heritage_attestation": frozenset({"attestation", "no_conclusion"}),
    "ukrainian_corpus_occurrence": frozenset({"occurrence", "no_conclusion"}),
    "textbook_explanation": frozenset({"explanation_context", "no_conclusion"}),
    # Russian-shadow is suspicion only — it can never carry attestation or
    # normative_rule support, so it can never independently accept or reject.
    "russian_shadow_suspicion": frozenset({"suspicion", "no_conclusion"}),
    "source_metadata": frozenset({"metadata_only"}),
}

# Supports values that count as "sufficient normative or attestation
# evidence" for an agree/positive/acceptable_control/protected decision.
# Deliberately excludes comparison_only, occurrence, style_guidance,
# calque_flag, explanation_context, suspicion, metadata_only, no_conclusion —
# none of those channels/values may independently accept or reject a row.
SUFFICIENT_SUPPORTS: frozenset[str] = frozenset({"normative_rule", "attestation"})

# archaic_attestation is deliberately NOT in SUFFICIENT_SUPPORTS: it flags an
# archaic-only VESUM result for mandatory risk review, it never counts as
# clean-modern support and it never condemns the row either.


class EvidenceContractError(ValueError):
    """A Cycle 007 evidence record violates the frozen schema/contract."""


def require(condition: bool, message: str) -> None:
    if not condition:
        raise EvidenceContractError(message)


def canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def sha256_text(value: str) -> str:
    return sha256_bytes(value.encode("utf-8"))


def sha256_value(value: Any) -> str:
    return sha256_text(canonical_json(value))


def sha256_file(path: Any) -> str:
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def row_identity(row: Mapping[str, Any]) -> dict[str, str]:
    unit_id = row.get("unit_id")
    unit_sha256 = row.get("unit_sha256")
    require(isinstance(unit_id, str) and bool(unit_id), "row identity missing unit_id")
    require(
        isinstance(unit_sha256, str) and len(unit_sha256) == 64,
        "row identity missing/malformed unit_sha256",
    )
    return {"unit_id": unit_id, "unit_sha256": unit_sha256}


def validate_channel_supports(channel: str, supports: str) -> None:
    require(channel in CHANNEL_SUPPORTS, f"unknown evidence channel: {channel!r}")
    require(
        supports in CHANNEL_SUPPORTS[channel],
        f"channel {channel!r} cannot emit supports={supports!r} (closed claim boundary)",
    )


def evidence_identity(
    *,
    channel: str,
    source_identity: str,
    source_version: str,
    locator: str,
    query_sha256: str,
    status: str,
    supports: str,
    retrieval_sha256: str,
    parser_id: str,
    parser_version: str,
    row: Mapping[str, Any],
    phenomenon_id: str | None,
) -> dict[str, Any]:
    """The exact canonical-JSON identity payload behind every evidence ID.

    Amendment step 8: "canonical JSON over exactly: evidence schema, channel,
    source identity and version, locator, query SHA-256, status, supports
    value, retrieval SHA-256, parser ID and version, row identity, and
    optional phenomenon ID." Binding row identity (and, when present,
    phenomenon ID) into the hash is what makes an evidence ID mechanically
    unreusable across rows or phenomena — a validator does not need a
    separate reuse table, it only needs to recompute this hash.
    """
    require(channel in CHANNELS, f"unknown evidence channel: {channel!r}")
    require(status in STATUSES, f"unknown evidence status: {status!r}")
    require(supports in SUPPORTS, f"unknown evidence supports value: {supports!r}")
    require(len(query_sha256) == 64, "query_sha256 must be a hex sha256")
    require(len(retrieval_sha256) == 64, "retrieval_sha256 must be a hex sha256")
    validate_channel_supports(channel, supports)
    return {
        "evidence_schema": EVIDENCE_SCHEMA_VERSION,
        "channel": channel,
        "source_identity": source_identity,
        "source_version": source_version,
        "locator": locator,
        "query_sha256": query_sha256,
        "status": status,
        "supports": supports,
        "retrieval_sha256": retrieval_sha256,
        "parser_id": parser_id,
        "parser_version": parser_version,
        "row_identity": row_identity(row),
        "phenomenon_id": phenomenon_id,
    }


def evidence_id(identity: Mapping[str, Any]) -> str:
    return "cycle007_evidence:" + sha256_value(identity)


def build_evidence_record(
    *,
    channel: str,
    source_identity: str,
    source_version: str,
    locator: str,
    query: str | None,
    query_sha256: str,
    status: str,
    supports: str,
    retrieval_sha256: str,
    parser_id: str,
    parser_version: str,
    row: Mapping[str, Any],
    phenomenon_id: str | None = None,
    negative_reason: str | None = None,
) -> dict[str, Any]:
    """Build one fully self-checking evidence record.

    ``query`` may hold private text (this is the private sidecar shape); the
    public receipt projection in the compiler strips it. ``negative_reason``
    is an optional free-text diagnostic for not_found/ambiguous/incomplete/
    parse_error/unavailable statuses; it is never treated as evidence.
    """
    identity = evidence_identity(
        channel=channel,
        source_identity=source_identity,
        source_version=source_version,
        locator=locator,
        query_sha256=query_sha256,
        status=status,
        supports=supports,
        retrieval_sha256=retrieval_sha256,
        parser_id=parser_id,
        parser_version=parser_version,
        row=row,
        phenomenon_id=phenomenon_id,
    )
    if status == "attested":
        require(negative_reason is None, "attested evidence cannot carry a negative_reason")
    else:
        require(supports == "no_conclusion", "non-attested evidence must carry supports=no_conclusion")
    record: dict[str, Any] = {
        "schema_version": EVIDENCE_SCHEMA_VERSION,
        "evidence_id": evidence_id(identity),
        "channel": channel,
        "source_identity": source_identity,
        "source_version": source_version,
        "locator": locator,
        "query": query,
        "query_sha256": query_sha256,
        "status": status,
        "supports": supports,
        "retrieval_sha256": retrieval_sha256,
        "parser_id": parser_id,
        "parser_version": parser_version,
        "row_identity": identity["row_identity"],
        "phenomenon_id": phenomenon_id,
        "negative_reason": negative_reason,
        "raw_payload_publication_allowed": False,
        "claim_boundary": {
            "authoritative": False,
            "human_gold": False,
            "model_vote_authoritative": False,
            "vesum_absence_only_authoritative": False,
        },
    }
    return record


def is_negative(record: Mapping[str, Any]) -> bool:
    return str(record["status"]) in NEGATIVE_STATUSES


def is_sufficient_positive(record: Mapping[str, Any]) -> bool:
    """True only for an attested record whose support is normative/attestation grade.

    Negative evidence IDs remain valid references (they can be cited to show
    a check ran) but this predicate is what "never count as sufficient
    positive support" means mechanically.
    """
    return str(record["status"]) == "attested" and str(record["supports"]) in SUFFICIENT_SUPPORTS


def is_archaic_only_risk(records: Sequence[Mapping[str, Any]]) -> bool:
    """True when VESUM only attests an archaic form for this row (mechanical risk flag)."""
    has_archaic = any(
        str(record["channel"]) == "vesum_attestation"
        and str(record["status"]) == "attested"
        and str(record["supports"]) == "archaic_attestation"
        for record in records
    )
    has_modern = any(
        str(record["channel"]) == "vesum_attestation"
        and str(record["status"]) == "attested"
        and str(record["supports"]) == "attestation"
        for record in records
    )
    return has_archaic and not has_modern


def public_evidence_projection(record: Mapping[str, Any]) -> dict[str, Any]:
    """The text-free public projection: counts, hashes, tool names, status/support facts only."""
    return {
        "schema_version": record["schema_version"],
        "evidence_id": record["evidence_id"],
        "channel": record["channel"],
        "source_identity": record["source_identity"],
        "source_version": record["source_version"],
        "query_sha256": record["query_sha256"],
        "status": record["status"],
        "supports": record["supports"],
        "retrieval_sha256": record["retrieval_sha256"],
        "parser_id": record["parser_id"],
        "parser_version": record["parser_version"],
        "phenomenon_id": record["phenomenon_id"],
        "raw_payload_publication_allowed": False,
    }
