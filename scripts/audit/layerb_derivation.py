#!/usr/bin/env python3
"""Pure source derivation for offline Layer B comparison records.

The comparison record is reconstructed while each raw bakeoff artifact and
``fact_checks`` entry is in hand.  That is the only point at which the stable
grounding identity is unambiguous; downstream label tools must never recover it
by matching a duplicate-prone rendered row.

This module deliberately has no reviewer-dispatch or bakeoff-runtime imports.
It shares only the stateless Layer A primitives and so is safe to import from
the offline label-handoff tools.
"""

from __future__ import annotations

import json
import re
import unicodedata
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from scripts.audit import anchor_primitives, grounding_gate_v2
from scripts.audit.layerb_keys import _stable_grounding_key
from scripts.audit.layerb_label_common import LabelJoinError

DEFAULT_TAU = 0.75
_CLAIM_PUNCT_RE = re.compile(r"[^\w\s]", re.UNICODE)
_LEADING_CLAIM_FILLER_RE = re.compile(r"^(?:або|чи)\s+", re.IGNORECASE)
_RECOVER_ABSTAIN_MIN_SIMILARITY = 1.0
_ARMS = frozenset({"bare", "tooled", "both"})


@dataclass(frozen=True)
class FixtureClaim:
    """The fixture fields required for deterministic truth lookup."""

    claim_id: str
    claim: str
    is_true: bool


def _read_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise LabelJoinError(f"cannot read source JSON {path}: {exc}") from exc


def _normalize_claim_loose(text: str) -> str:
    """Mirror the baked comparison's punctuation-insensitive claim matching."""
    normalized = unicodedata.normalize("NFC", text).lower()
    normalized = normalized.replace("’", "'").replace("`", "'")
    normalized = re.sub(r"\s+", " ", normalized).strip(" \t\r\n.。")
    normalized = _LEADING_CLAIM_FILLER_RE.sub("", normalized)
    return " ".join(_CLAIM_PUNCT_RE.sub(" ", normalized).split())


def _judgment_verdict(row: Mapping[str, Any]) -> str:
    if row.get("admissibility_downgraded") is True and isinstance(row.get("original_verdict"), str):
        return str(row["original_verdict"]).strip().upper()
    return str(row.get("verdict") or "").strip().upper()


def _load_fixture_claims(fixtures_dir: Path | None) -> dict[str, tuple[FixtureClaim, ...]]:
    if fixtures_dir is None:
        return {}
    if not fixtures_dir.is_dir():
        raise LabelJoinError(f"fixtures directory does not exist: {fixtures_dir}")
    fixtures: dict[str, tuple[FixtureClaim, ...]] = {}
    for path in sorted(fixtures_dir.glob("*.json")):
        document = _read_json(path)
        if not isinstance(document, Mapping):
            raise LabelJoinError(f"fixture is not an object: {path}")
        slug = document.get("slug")
        raw_claims = document.get("claims")
        if not isinstance(slug, str) or not slug or not isinstance(raw_claims, list):
            raise LabelJoinError(f"fixture lacks slug or claims: {path}")
        claims: list[FixtureClaim] = []
        for item in raw_claims:
            if not isinstance(item, Mapping):
                raise LabelJoinError(f"fixture claim is not an object: {path}")
            claim_id = item.get("claim_id")
            claim = item.get("claim")
            is_true = item.get("is_true")
            if not isinstance(claim_id, str) or not isinstance(claim, str) or not isinstance(is_true, bool):
                raise LabelJoinError(f"fixture claim lacks identity or truth value: {path}")
            claims.append(FixtureClaim(claim_id, claim, is_true))
        fixtures[slug] = tuple(claims)
    if not fixtures:
        raise LabelJoinError(f"no bakeoff fixtures found in {fixtures_dir}")
    return fixtures


def _match_rows_to_fixture_claims(
    rows: list[dict[str, Any]], claims: Sequence[FixtureClaim]
) -> dict[str, dict[str, Any]]:
    """Reuse the frozen comparison's precedence and polarity guard exactly."""
    matched: dict[str, dict[str, Any]] = {}
    norm_rows = [(_normalize_claim_loose(str(row.get("claim") or "")), row) for row in rows]
    for claim in claims:
        wanted = _normalize_claim_loose(claim.claim)
        if not wanted:
            continue
        hit = next((index for index, (row_claim, _row) in enumerate(norm_rows) if row_claim == wanted), None)
        if hit is None:
            candidates = [
                index
                for index, (row_claim, row) in enumerate(norm_rows)
                if row_claim
                and wanted in row_claim
                and (not claim.is_true or _judgment_verdict(row) == "CONFIRMED")
            ]
            if candidates:
                hit = min(candidates, key=lambda index: len(norm_rows[index][0]))
        if hit is None:
            candidates = [
                index
                for index, (row_claim, _row) in enumerate(norm_rows)
                if row_claim and row_claim in wanted and len(row_claim) >= max(20, int(0.6 * len(wanted)))
            ]
            if candidates:
                hit = max(candidates, key=lambda index: len(norm_rows[index][0]))
        if hit is not None:
            matched[claim.claim_id] = norm_rows[hit][1]
    return matched


def _artifact_is_bakeoff_cell(artifact: Mapping[str, Any]) -> bool:
    schema = artifact.get("schema_version")
    return isinstance(schema, str) and schema.startswith("qg_bakeoff_run.")


def _artifact_arm(path: Path, artifact: Mapping[str, Any]) -> str:
    arm = artifact.get("arm")
    if isinstance(arm, str) and arm in _ARMS:
        return arm
    return "bare" if "__bare" in path.stem else "tooled"


def _tool_events(dispatch: Any) -> tuple[dict[str, Any], ...]:
    if not isinstance(dispatch, Mapping):
        return ()
    raw_events = dispatch.get("tool_events")
    if not isinstance(raw_events, Sequence) or isinstance(raw_events, (str, bytes)):
        return ()
    return tuple(dict(event) for event in raw_events if isinstance(event, Mapping))


def _grounding_matches_events(grounding: Mapping[str, Any], events: Sequence[Mapping[str, Any]]) -> bool:
    query = str(grounding.get("query") or "").strip()
    excerpt = str(grounding.get("evidence_excerpt") or "").strip()
    if not query or not excerpt:
        return False
    tool = anchor_primitives.canonical_tool_name(grounding.get("tool"))
    for event in events:
        if tool and anchor_primitives.canonical_tool_name(event.get("tool")) != tool:
            continue
        if not anchor_primitives.event_input_matches_query(event, query):
            continue
        output = anchor_primitives.event_output_text(event)
        if output is not None and anchor_primitives.output_contains_excerpt(output, excerpt):
            return True
    return False


def _abstain_recovered(result: grounding_gate_v2.AnchorResult) -> bool:
    return result.abstained and result.similarity >= _RECOVER_ABSTAIN_MIN_SIMILARITY


def derive_keyed_records(
    artifacts_dir: Path,
    *,
    fixtures_dir: Path | None,
    tau: float = DEFAULT_TAU,
) -> list[dict[str, Any]]:
    """Regenerate records and keys while walking ``(artifact, fact_check)``.

    The emitted non-key fields are intentionally identical to the historical
    ``grounding_shadow_compare`` records at the same tau.  The two identity
    fields are appended at source and are therefore not the result of a join.
    A comparison-only caller may pass ``fixtures_dir=None`` to retain the
    legacy no-gold fallback; source-keyed label derivation passes a real
    fixture directory and proves every field against its frozen baseline.
    """
    if not artifacts_dir.is_dir():
        raise LabelJoinError(f"artifacts directory does not exist: {artifacts_dir}")
    fixtures = _load_fixture_claims(fixtures_dir)
    records: list[dict[str, Any]] = []
    for path in sorted(artifacts_dir.glob("*.json")):
        artifact = _read_json(path)
        if not isinstance(artifact, Mapping):
            continue
        if not _artifact_is_bakeoff_cell(artifact):
            continue
        payload = artifact.get("payload")
        fact_checks = payload.get("fact_checks") if isinstance(payload, Mapping) else []
        if not isinstance(fact_checks, list):
            fact_checks = []
        fixture_data = artifact.get("fixture")
        slug = fixture_data.get("slug") if isinstance(fixture_data, Mapping) else None
        fixture = fixtures.get(slug) if isinstance(slug, str) else None
        if not all(isinstance(fact_check, Mapping) for fact_check in fact_checks):
            raise LabelJoinError(f"bakeoff fact_checks contains a non-object: {path}")
        fact_rows = [dict(fact_check) for fact_check in fact_checks]
        matched = _match_rows_to_fixture_claims(fact_rows, fixture) if fixture is not None else {}
        truth_by_fact_index: dict[int, bool] = {}
        for claim_id, row in matched.items():
            truth = next(claim.is_true for claim in fixture if claim.claim_id == claim_id)
            index = next(index for index, source_row in enumerate(fact_rows) if source_row is row)
            truth_by_fact_index[index] = truth
        events = _tool_events(artifact.get("dispatch"))
        seat = artifact.get("seat") or artifact.get("model") or "unknown"
        seat_arm = f"{seat}/{_artifact_arm(path, artifact)}"
        for fact_check_index, fact_check in enumerate(fact_checks):
            if not isinstance(fact_check, Mapping):
                continue
            grounding = fact_check.get("grounding")
            if not isinstance(grounding, Mapping):
                continue
            v1_admissible = _grounding_matches_events(grounding, events)
            result = grounding_gate_v2.anchor_evidence_to_events(grounding, events, tau=tau)
            tool_query_matched = False
            if result.source_index is not None:
                tool_query_matched = grounding_gate_v2._tool_query_match(grounding, events[result.source_index])
            best_span_preview = ""
            if result.span is not None and result.source_index is not None:
                output = anchor_primitives.event_output_text(events[result.source_index])
                if output is not None:
                    normalized_output = anchor_primitives.normalize_for_match(output)
                    best_span_preview = normalized_output[result.span[0] : result.span[1]][:160]
            record = {
                "fixture": slug or "unknown",
                "seat_arm": seat_arm,
                "claim": str(fact_check.get("claim") or ""),
                "excerpt": str(grounding.get("evidence_excerpt") or ""),
                "v1_admissible": v1_admissible,
                "v2_anchored": result.anchored,
                "v2_abstained": result.abstained,
                "similarity": result.similarity,
                "abstain_recovered": _abstain_recovered(result),
                "v2_effective": result.anchored or _abstain_recovered(result),
                "tool_query_matched": tool_query_matched,
                "best_span_preview": best_span_preview,
                "gold_is_true": truth_by_fact_index.get(fact_check_index),
                "grounding_key": _stable_grounding_key(path, fact_check_index, fact_check),
                "fact_check_index": fact_check_index,
            }
            records.append(record)
    keys = [str(record["grounding_key"]) for record in records]
    if len(keys) != len(set(keys)):
        raise LabelJoinError("source derivation emitted duplicate grounding keys")
    return records
