#!/usr/bin/env python3
"""Frozen public Cycle-007 label semantics with source-grounded evidence verification."""

from __future__ import annotations

import json
import sys
from collections.abc import Mapping
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.projects.open_model_data import phase3_cycle007_evidence_contract as contract
from scripts.projects.open_model_data import phase3_cycle007_evidence_validator as validator

REJECTS = {
    "agree",
    "reject_fragment_or_too_short",
    "reject_exercise_or_task_prompt",
    "reject_error_or_contrast_example",
    "reject_table_list_formula_code",
    "reject_metalinguistic_or_grammar_talk",
    "reject_quoted_literary_or_anthology",
    "reject_archaic_historical_language",
    "reject_dialectal_regional_surzhyk",
    "reject_foreign_or_translation_artifact",
    "reject_learner_or_simplified_broken",
    "reject_parallel_norm_or_pre2026_only",
    "reject_mixed_or_uncertain",
    "reject_insufficient_locator_evidence",
}
GENRES = {"expository_narrative", "scientific_expository", "instructional_content_expository"}
TAX = contract.RESIDUAL_PHENOMENON_TAXONOMY
DEC = {"positive", "acceptable_control", "protected", "abstention", "disagreement"}
SUFFICIENT_REQUIRED_DECISIONS = validator.SUFFICIENT_REQUIRED_DECISIONS
UNCERTAINTY_DECISIONS = validator.UNCERTAINTY_DECISIONS


class Invalid(ValueError):
    """A Cycle 007 label violates schema, invariant, or evidence contract."""


def pairs(items: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in items:
        if key in result:
            raise Invalid("duplicate JSON key")
        result[key] = value
    return result


def identities(rows: list[dict[str, Any]]) -> list[tuple[str, str]]:
    try:
        result = [(row["unit_id"], row["unit_sha256"]) for row in rows]
    except (KeyError, TypeError) as exc:
        raise Invalid("identity drift") from exc
    if len(result) != len(set(result)) or any(
        not isinstance(unit_id, str) or not isinstance(unit_sha256, str) or len(unit_sha256) != 64
        for unit_id, unit_sha256 in result
    ):
        raise Invalid("identity drift")
    return result


def _clean(label: dict[str, Any], row_evidence: Mapping[str, Any] | None = None) -> None:
    if (
        set(label)
        != {
            "unit_id",
            "unit_sha256",
            "decision_code",
            "clean_modern_standard_prose",
            "modern_genre_id",
            "evidence_ids",
        }
        or label.get("decision_code") not in REJECTS
        or type(label.get("clean_modern_standard_prose")) is not bool
        or not isinstance(label.get("evidence_ids"), list)
        or any(not isinstance(eid, str) for eid in label["evidence_ids"])
    ):
        raise Invalid("clean schema drift")
    agrees = label["decision_code"] == "agree"
    if (
        agrees != label["clean_modern_standard_prose"]
        or (agrees and label["modern_genre_id"] not in GENRES)
        or (not agrees and label["modern_genre_id"] is not None)
    ):
        raise Invalid("clean invariant")
    evidence_ids = label["evidence_ids"]
    if evidence_ids != sorted(set(evidence_ids)):
        raise Invalid("evidence id order/unique drift")
    if row_evidence is not None:
        try:
            validator.validate_label_evidence_refs(
                row_evidence,
                decision_code=label["decision_code"],
                evidence_ids=evidence_ids,
                phenomenon_id=None,
            )
        except validator.EvidenceValidationError as exc:
            raise Invalid(exc.code) from exc


def _residual(label: dict[str, Any], row: dict[str, Any], row_evidence: Mapping[str, Any] | None = None) -> None:
    if (
        set(label) != {"unit_id", "unit_sha256", "phenomena", "primary_phenomenon_id", "item_decision_rollup"}
        or not isinstance(label.get("phenomena"), list)
        or not label["phenomena"]
        or label.get("item_decision_rollup") not in DEC
    ):
        raise Invalid("residual schema drift")
    names: list[str] = []
    decisions: dict[str, str] = {}
    for phenomenon in label["phenomena"]:
        if (
            not isinstance(phenomenon, dict)
            or set(phenomenon) != {"phenomenon_id", "decision_code", "evidence_sufficiency", "evidence_ids"}
            or phenomenon.get("phenomenon_id") not in TAX
            or phenomenon.get("decision_code") not in DEC
            or phenomenon.get("evidence_sufficiency") not in {"sufficient", "insufficient"}
            or not isinstance(phenomenon.get("evidence_ids"), list)
            or any(not isinstance(eid, str) for eid in phenomenon["evidence_ids"])
        ):
            raise Invalid("residual phenomenon drift")
        evidence_ids = phenomenon["evidence_ids"]
        if evidence_ids != sorted(set(evidence_ids)):
            raise Invalid("evidence id order/unique drift")
        if (
            phenomenon["decision_code"] in {"positive", "acceptable_control", "protected"}
            and phenomenon["evidence_sufficiency"] != "sufficient"
        ):
            raise Invalid("scored decision insufficiency")
        if row.get("family_id") == "pravopys_2019_complete" and phenomenon["decision_code"] == "positive":
            raise Invalid("2019 positive forbidden")
        if row_evidence is not None:
            try:
                validator.validate_label_evidence_refs(
                    row_evidence,
                    decision_code=phenomenon["decision_code"],
                    evidence_ids=evidence_ids,
                    phenomenon_id=phenomenon["phenomenon_id"],
                )
            except validator.EvidenceValidationError as exc:
                raise Invalid(exc.code) from exc
        names.append(phenomenon["phenomenon_id"])
        decisions[phenomenon["phenomenon_id"]] = phenomenon["decision_code"]
    if len(names) != len(set(names)) or names != sorted(names, key=TAX.index):
        raise Invalid("taxonomy order/unique drift")
    viable = [name for name in names if decisions[name] not in {"abstention", "disagreement"}]
    primary = label["primary_phenomenon_id"]
    if viable and (primary not in viable or label["item_decision_rollup"] != decisions[primary]):
        raise Invalid("primary/rollup drift")
    if not viable and (
        primary is not None
        or label["item_decision_rollup"] != ("disagreement" if "disagreement" in decisions.values() else "abstention")
    ):
        raise Invalid("null rollup drift")


def validate(lane: str, packet: dict[str, Any], raw: bytes, sidecar: dict[str, Any] | None = None) -> dict[str, Any]:
    try:
        answer = json.loads(raw.decode("utf-8", "strict"), object_pairs_hook=pairs)
    except (UnicodeDecodeError, json.JSONDecodeError, Invalid) as exc:
        raise Invalid("response UTF-8/JSON invalid") from exc
    rows = packet.get("rows") if isinstance(packet, dict) else None
    if (
        lane not in {"clean_label", "residual_label"}
        or not isinstance(rows, list)
        or not isinstance(answer, dict)
        or set(answer) != {"labels"}
        or not isinstance(answer["labels"], list)
        or len(answer["labels"]) != len(rows)
    ):
        raise Invalid("response envelope drift")
    sidecar_rows: list[Mapping[str, Any]] | None = None
    if sidecar is not None:
        raw_sidecar_rows = sidecar.get("rows") if isinstance(sidecar, dict) else sidecar
        if not isinstance(raw_sidecar_rows, list) or len(raw_sidecar_rows) != len(rows):
            raise Invalid("sidecar row count drift")
        sidecar_rows = raw_sidecar_rows
    seen: list[tuple[str, str]] = []
    for index, (source, label) in enumerate(zip(rows, answer["labels"], strict=True)):
        if (
            not isinstance(source, dict)
            or not isinstance(label, dict)
            or (
                label.get("unit_id"),
                label.get("unit_sha256"),
            )
            != (source.get("unit_id"), source.get("unit_sha256"))
        ):
            raise Invalid("identity/order drift")
        row_ev = None
        if sidecar_rows is not None:
            row_ev = sidecar_rows[index]
            if (row_ev.get("unit_id"), row_ev.get("unit_sha256")) != (
                source.get("unit_id"),
                source.get("unit_sha256"),
            ):
                raise Invalid("cross_row_evidence")
        seen.append((label["unit_id"], label["unit_sha256"]))
        _clean(label, row_ev) if lane == "clean_label" else _residual(label, source, row_ev)
    if seen != identities(rows) or len(seen) != len(set(seen)):
        raise Invalid("identity uniqueness drift")
    return answer
