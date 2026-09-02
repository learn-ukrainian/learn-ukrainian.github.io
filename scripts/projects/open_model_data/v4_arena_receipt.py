#!/usr/bin/env python3
"""Build hash-bound, text-free receipts for the private V4 proposal arena.

This is a transport and disagreement receipt only.  Model proposals and ballots
are quarantined observations: they can never assert gold, training, evaluation,
teaching, or coverage eligibility.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from collections import Counter
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

SCHEMA_VERSION = "v4-arena-receipt-v1"
PROPOSAL_SCHEMA_VERSION = "v4-arena-proposal-v1"
BEGIN_MARKER = "<<<V4_ARENA_PROPOSAL_JSON_BEGIN>>>"
END_MARKER = "<<<V4_ARENA_PROPOSAL_JSON_END>>>"
HASH_RE = re.compile(r"^[0-9a-f]{64}$")
QUARANTINE = "MODEL_AGREEMENT_QUARANTINED_NOT_GOLD"

# A retry is only ever granted for a *format* failure -- the wire shape was
# wrong, not the content.  A schema/content failure (wrong candidate, case
# drift, invalid label/tag, ...) is never retried: giving a provider a second
# attempt there would let it fabricate a differently-wrong-but-well-formed
# answer instead of recording the real disagreement.
FORMAT_ONLY_CODES = frozenset({"MALFORMED_PROVIDER_OUTPUT", "NONCANONICAL_PROVIDER_JSON"})


class ArenaReceiptError(ValueError):
    """The arena binding or its deterministic receipt is unsafe."""


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ArenaReceiptError(message)


def canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def sha256_value(value: Any) -> str:
    return hashlib.sha256((canonical_json(value) + "\n").encode("utf-8")).hexdigest()


def _hash(value: Any, label: str) -> str:
    require(isinstance(value, str) and HASH_RE.fullmatch(value) is not None, f"invalid {label} SHA-256")
    return value


def _unique_strings(value: Any, label: str) -> list[str]:
    require(isinstance(value, list) and value, f"{label} must be a non-empty list")
    require(all(isinstance(item, str) and item for item in value), f"{label} contains an invalid ID")
    require(len(value) == len(set(value)), f"{label} contains duplicate IDs")
    return list(value)


def format_proposal(proposal: Mapping[str, Any]) -> str:
    """Return the only accepted wire representation for a provider proposal."""
    return f"{BEGIN_MARKER}\n{canonical_json(dict(proposal))}\n{END_MARKER}"


def parse_proposal(raw: Any) -> dict[str, Any]:
    """Parse a proposal without accepting surrounding prose or multiple payloads."""
    require(isinstance(raw, str), "MALFORMED_PROVIDER_OUTPUT")
    prefix = f"{BEGIN_MARKER}\n"
    suffix = f"\n{END_MARKER}"
    require(raw.startswith(prefix) and raw.endswith(suffix), "MALFORMED_PROVIDER_OUTPUT")
    payload = raw[len(prefix) : -len(suffix)]
    require(payload and "\n" not in payload, "MALFORMED_PROVIDER_OUTPUT")
    try:
        proposal = json.loads(payload)
    except json.JSONDecodeError as exc:
        raise ArenaReceiptError("MALFORMED_PROVIDER_OUTPUT") from exc
    require(isinstance(proposal, dict), "MALFORMED_PROVIDER_OUTPUT")
    require(canonical_json(proposal) == payload, "NONCANONICAL_PROVIDER_JSON")
    return proposal


def _split_provider_entry(entry: Any) -> tuple[Any, Any]:
    """A provider output entry is either the raw single-shot payload (any
    type; ``parse_proposal`` fails it closed if it is not a wire-shaped
    string), or an object ``{"primary": ..., "retry": ...}`` opting into one
    format-only retry. Never raises -- an entry that looks like neither shape
    is passed through as a primary-only payload, so it still fails closed
    inside ``parse_proposal`` with the ordinary ``MALFORMED_PROVIDER_OUTPUT``
    residual rather than a different, surprising error here."""
    if isinstance(entry, Mapping) and set(entry) <= {"primary", "retry"} and "primary" in entry:
        return entry.get("primary"), entry.get("retry")
    return entry, None


def parse_proposal_with_one_format_retry(
    primary_raw: Any, retry_raw: Any = None
) -> tuple[dict[str, Any] | None, str | None, bool]:
    """Parse ``primary_raw``. If -- and only if -- that attempt fails with a
    *format-only* error code (``FORMAT_ONLY_CODES``) and ``retry_raw`` is
    supplied, make exactly one more attempt against ``retry_raw``. A
    non-format failure, or a format failure with no ``retry_raw``, is never
    retried, and a retry is never itself retried.

    Returns ``(proposal, error_code, retried)``: on success ``proposal`` is
    the parsed dict and ``error_code`` is ``None``; on failure ``proposal``
    is ``None`` and ``error_code`` is the final (post-retry, if attempted)
    failure code. ``retried`` reports whether a retry attempt was made,
    regardless of whether it succeeded.
    """
    try:
        return parse_proposal(primary_raw), None, False
    except ArenaReceiptError as exc:
        primary_code = str(exc)
        if primary_code not in FORMAT_ONLY_CODES or retry_raw is None:
            return None, primary_code, False
        try:
            return parse_proposal(retry_raw), None, True
        except ArenaReceiptError as retry_exc:
            return None, str(retry_exc), True


def _candidate_bindings(
    route_denominator: Sequence[str], candidate_map: Mapping[str, Any]
) -> tuple[list[str], dict[str, dict[str, str]]]:
    routes = _unique_strings(list(route_denominator), "route denominator")
    require(isinstance(candidate_map, Mapping) and candidate_map, "candidate map must be a non-empty object")
    bindings: dict[str, dict[str, str]] = {}
    for candidate_id, value in candidate_map.items():
        require(isinstance(candidate_id, str) and candidate_id, "candidate map has invalid candidate ID")
        require(isinstance(value, Mapping), f"candidate {candidate_id} binding must be an object")
        provider_id, route_id = value.get("provider_id"), value.get("route_id")
        require(isinstance(provider_id, str) and provider_id, f"candidate {candidate_id} provider ID missing")
        require(isinstance(route_id, str) and route_id in routes, f"candidate {candidate_id} route ID invalid")
        bindings[candidate_id] = {"provider_id": provider_id, "route_id": route_id}
    require(
        len({item["provider_id"] for item in bindings.values()}) == len(bindings),
        "candidate map has duplicate provider binding",
    )
    require(len({item["route_id"] for item in bindings.values()}) == len(bindings), "candidate map has duplicate route binding")
    require(set(item["route_id"] for item in bindings.values()) == set(routes), "candidate map / route denominator drift")
    return routes, bindings


def _proposal_cases(
    proposal: Mapping[str, Any], candidate_id: str, case_ids: list[str], allowed_labels: set[str], allowed_tags: set[str]
) -> list[dict[str, Any]]:
    require(proposal.get("schema_version") == PROPOSAL_SCHEMA_VERSION, "PROPOSAL_SCHEMA_DRIFT")
    require(proposal.get("candidate_id") == candidate_id, "INVENTED_CANDIDATE_OUTPUT")
    cases = proposal.get("cases")
    require(isinstance(cases, list), "PROPOSAL_CASES_MISSING")
    actual_ids = [item.get("case_id") if isinstance(item, Mapping) else None for item in cases]
    require(all(isinstance(item, str) for item in actual_ids), "PROPOSAL_CASE_ID_INVALID")
    if len(actual_ids) != len(set(actual_ids)):
        raise ArenaReceiptError("DUPLICATE_CASE_ID")
    if actual_ids != case_ids:
        raise ArenaReceiptError("PROPOSAL_CASE_IDS_OR_ORDER_DRIFT")
    normalized: list[dict[str, Any]] = []
    for item in cases:
        assert isinstance(item, Mapping)
        label, tags = item.get("label"), item.get("tags")
        require(isinstance(label, str) and label in allowed_labels, "PROPOSAL_LABEL_INVALID")
        require(isinstance(tags, list) and all(isinstance(tag, str) and tag in allowed_tags for tag in tags), "PROPOSAL_TAG_INVALID")
        require(len(tags) == len(set(tags)), "PROPOSAL_TAG_DUPLICATE")
        normalized.append({"case_id": item["case_id"], "label": label, "tags": sorted(tags)})
    return normalized


def _residual(code: str, **values: Any) -> dict[str, Any]:
    return {"code": code, **values}


def build_receipts(
    *,
    outcome_sha256: str,
    prompt_sha256: str,
    case_ids: Sequence[str],
    route_denominator: Sequence[str],
    candidate_map: Mapping[str, Any],
    provider_outputs: Mapping[str, Any],
    ballots: Sequence[Mapping[str, Any]],
    allowed_labels: Sequence[str],
    allowed_tags: Sequence[str],
) -> dict[str, dict[str, Any]]:
    """Build private and public receipts, preserving every failed route as a residual."""
    outcome_sha256, prompt_sha256 = _hash(outcome_sha256, "outcome"), _hash(prompt_sha256, "prompt")
    frozen_cases = _unique_strings(list(case_ids), "frozen case IDs")
    routes, candidates = _candidate_bindings(route_denominator, candidate_map)
    labels, tags = set(_unique_strings(list(allowed_labels), "allowed labels")), set(_unique_strings(list(allowed_tags), "allowed tags"))
    require(isinstance(provider_outputs, Mapping), "provider outputs must be an object")
    require(set(provider_outputs) <= set(candidates), "provider outputs include an unknown candidate")
    require(isinstance(ballots, Sequence) and not isinstance(ballots, (str, bytes)), "ballots must be a list")

    proposals: dict[str, list[dict[str, Any]]] = {}
    route_statuses: list[dict[str, Any]] = []
    residuals: list[dict[str, Any]] = []
    for candidate_id, binding in sorted(candidates.items(), key=lambda item: item[1]["route_id"]):
        primary_raw, retry_raw = _split_provider_entry(provider_outputs.get(candidate_id))
        primary_hash = sha256_value(primary_raw) if primary_raw is not None else None
        retry_hash = sha256_value(retry_raw) if retry_raw is not None else None
        proposal, parse_error, retried = parse_proposal_with_one_format_retry(primary_raw, retry_raw)
        try:
            require(parse_error is None, parse_error or "MALFORMED_PROVIDER_OUTPUT")
            assert proposal is not None
            require(proposal.get("provider_id") == binding["provider_id"], "PROVIDER_ID_DRIFT")
            proposals[candidate_id] = _proposal_cases(proposal, candidate_id, frozen_cases, labels, tags)
            route_statuses.append(
                {
                    "route_id": binding["route_id"],
                    "candidate_id": candidate_id,
                    "status": "valid",
                    "output_sha256": primary_hash,
                    "retry_output_sha256": retry_hash,
                    "retried": retried,
                }
            )
        except ArenaReceiptError as exc:
            code = str(exc)
            route_statuses.append(
                {
                    "route_id": binding["route_id"],
                    "candidate_id": candidate_id,
                    "status": "invalid",
                    "output_sha256": primary_hash,
                    "retry_output_sha256": retry_hash,
                    "retried": retried,
                    "residual_code": code,
                }
            )
            residuals.append(_residual(code, candidate_id=candidate_id, route_id=binding["route_id"]))

    valid_ballots: list[dict[str, str]] = []
    ballot_keys: set[tuple[str, str, str]] = set()
    for ordinal, ballot in enumerate(ballots):
        if not isinstance(ballot, Mapping):
            residuals.append(_residual("MALFORMED_BALLOT", ballot_index=ordinal))
            continue
        voter, target, case_id, label = ballot.get("voter_candidate_id"), ballot.get("candidate_id"), ballot.get("case_id"), ballot.get("label")
        if voter not in candidates or target not in candidates:
            residuals.append(_residual("UNKNOWN_CANDIDATE", ballot_index=ordinal))
            continue
        if voter == target:
            residuals.append(_residual("SELF_VOTE", ballot_index=ordinal, candidate_id=str(voter)))
            continue
        if case_id not in frozen_cases or label not in labels:
            residuals.append(_residual("INVALID_BALLOT", ballot_index=ordinal))
            continue
        key = (str(voter), str(target), str(case_id))
        if key in ballot_keys:
            residuals.append(_residual("DUPLICATE_CASE_BALLOT", ballot_index=ordinal, candidate_id=str(voter), case_id=str(case_id)))
            continue
        ballot_keys.add(key)
        valid_ballots.append({"voter_candidate_id": str(voter), "candidate_id": str(target), "case_id": str(case_id), "label": str(label)})

    # Leave-one-out index: every valid ballot is, by construction (self-vote is
    # rejected above), cast by a candidate *other than* the one it is about --
    # so grouping by (target, case) already gives the leave-one-out peer set
    # for that target on that case.  This is the only consensus this receipt
    # ever aggregates from ballots; a candidate's own self-reported proposal
    # label (see ``candidate_outputs`` below) never enters it.
    ballots_by_target_case: dict[tuple[str, str], list[dict[str, str]]] = {}
    for entry in valid_ballots:
        ballots_by_target_case.setdefault((entry["candidate_id"], entry["case_id"]), []).append(entry)

    # A valid provider must cover every non-self candidate and frozen case.  Invalid
    # provider routes remain residuals, rather than silently changing this expectation.
    for voter in sorted(proposals):
        for target in sorted(candidates):
            if voter == target:
                continue
            for case_id in frozen_cases:
                if (voter, target, case_id) not in ballot_keys:
                    residuals.append(_residual("MISSING_CASE_BALLOT", candidate_id=voter, target_candidate_id=target, case_id=case_id))

    per_case: list[dict[str, Any]] = []
    for index, case_id in enumerate(frozen_cases):
        outputs = [{"candidate_id": candidate_id, **proposals[candidate_id][index]} for candidate_id in sorted(proposals)]
        counts = Counter(item["label"] for item in outputs)
        status = "exact_agreement" if len(outputs) >= 2 and len(counts) == 1 else "disagreement"
        leave_one_out_ballots = []
        for target_candidate_id in sorted(candidates):
            peer_ballots = ballots_by_target_case.get((target_candidate_id, case_id), [])
            peer_counts = Counter(entry["label"] for entry in peer_ballots)
            ranked = peer_counts.most_common()
            consensus_label = ranked[0][0] if len(ranked) == 1 or (len(ranked) > 1 and ranked[0][1] > ranked[1][1]) else None
            leave_one_out_ballots.append({
                "candidate_id": target_candidate_id,
                "voter_count": len(peer_ballots),
                "label_counts": dict(sorted(peer_counts.items())),
                "consensus_label": consensus_label,
                "unanimous": len(peer_counts) == 1 and len(peer_ballots) > 0,
            })
        per_case.append({
            "case_id": case_id,
            "disposition": QUARANTINE,
            "agreement_status": status,
            "valid_candidate_count": len(outputs),
            "label_counts": dict(sorted(counts.items())),
            "candidate_outputs": outputs,
            "leave_one_out_ballots": leave_one_out_ballots,
        })

    binding = {
        "outcome_sha256": outcome_sha256,
        "prompt_sha256": prompt_sha256,
        "case_ids": frozen_cases,
        "route_denominator": routes,
        "candidate_map_sha256": sha256_value(candidate_map),
        "allowed_labels": sorted(labels),
        "allowed_tags": sorted(tags),
    }
    public = {
        "schema_version": SCHEMA_VERSION,
        "visibility": "public_safe_text_free",
        "binding": binding,
        "reproduction": {"proposal_schema_version": PROPOSAL_SCHEMA_VERSION, "begin_marker": BEGIN_MARKER, "end_marker": END_MARKER, "canonical_json": "utf8-sort-keys-compact-newline-sha256"},
        "route_statuses": route_statuses,
        "cases": per_case,
        "counts": {"declared_routes": len(routes), "valid_routes": len(proposals), "invalid_routes": len(routes) - len(proposals), "exact_agreement_cases": sum(case["agreement_status"] == "exact_agreement" for case in per_case), "disputed_cases": sum(case["agreement_status"] == "disagreement" for case in per_case)},
        "residuals": sorted(residuals, key=canonical_json),
        "eligibility": {"gold": False, "training": False, "evaluation": False, "teaching": False, "coverage": False},
    }
    public["receipt_sha256"] = sha256_value(public)
    private = {
        "schema_version": SCHEMA_VERSION,
        "visibility": "private_machine_text_free",
        "binding": binding,
        "route_statuses": route_statuses,
        "ballot_count": len(valid_ballots),
        "valid_ballots_sha256": sha256_value(valid_ballots),
        "public_receipt_sha256": public["receipt_sha256"],
        "eligibility": public["eligibility"],
    }
    private["receipt_sha256"] = sha256_value(private)
    return {"private": private, "public": public}


def verify_receipt(receipt: Mapping[str, Any]) -> dict[str, Any]:
    require(isinstance(receipt, Mapping), "receipt must be an object")
    value = dict(receipt)
    supplied = value.pop("receipt_sha256", None)
    require(isinstance(supplied, str) and supplied == sha256_value(value), "receipt hash drift")
    require(value.get("schema_version") == SCHEMA_VERSION, "receipt schema drift")
    visibility = value.get("visibility")
    expected_keys = {
        "public_safe_text_free": {
            "schema_version", "visibility", "binding", "reproduction", "route_statuses", "cases", "counts", "residuals", "eligibility"
        },
        "private_machine_text_free": {
            "schema_version", "visibility", "binding", "route_statuses", "ballot_count", "valid_ballots_sha256", "public_receipt_sha256", "eligibility"
        },
    }
    require(visibility in expected_keys and set(value) == expected_keys[visibility], "receipt schema drift")
    binding = value.get("binding")
    require(isinstance(binding, Mapping) and set(binding) == {"outcome_sha256", "prompt_sha256", "case_ids", "route_denominator", "candidate_map_sha256", "allowed_labels", "allowed_tags"}, "receipt binding schema drift")
    _hash(binding.get("outcome_sha256"), "outcome")
    _hash(binding.get("prompt_sha256"), "prompt")
    _hash(binding.get("candidate_map_sha256"), "candidate map")
    cases, routes = _unique_strings(binding.get("case_ids"), "receipt case IDs"), _unique_strings(binding.get("route_denominator"), "receipt route denominator")
    eligibility = value.get("eligibility")
    require(isinstance(eligibility, Mapping) and not any(eligibility.values()), "arena receipt eligibility drift")
    statuses = value.get("route_statuses")
    require(isinstance(statuses, list) and len(statuses) == len(routes), "receipt route status drift")
    require({item.get("route_id") for item in statuses if isinstance(item, Mapping)} == set(routes), "receipt route denominator drift")
    if visibility == "public_safe_text_free":
        counts, case_rows = value.get("counts"), value.get("cases")
        require(isinstance(counts, Mapping) and counts.get("declared_routes") == len(routes), "receipt count drift")
        require(isinstance(case_rows, list) and [item.get("case_id") if isinstance(item, Mapping) else None for item in case_rows] == cases, "receipt case order drift")
        require(all(isinstance(item, Mapping) and item.get("disposition") == QUARANTINE for item in case_rows), "arena quarantine drift")
    return dict(receipt)


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True, type=Path, help="JSON fixture containing build_receipts keyword arguments")
    parser.add_argument("--private-output", required=True, type=Path)
    parser.add_argument("--public-output", required=True, type=Path)
    args = parser.parse_args(argv)
    try:
        payload = json.loads(args.input.read_text(encoding="utf-8"))
        require(isinstance(payload, dict), "input fixture must be an object")
        receipts = build_receipts(**payload)
        args.private_output.write_text(canonical_json(receipts["private"]) + "\n", encoding="utf-8")
        args.public_output.write_text(canonical_json(receipts["public"]) + "\n", encoding="utf-8")
    except (ArenaReceiptError, OSError, TypeError, json.JSONDecodeError) as exc:
        print(f"V4 arena receipt: FAIL: {exc}", file=sys.stderr)
        return 1
    print(canonical_json({"private_receipt_sha256": receipts["private"]["receipt_sha256"], "public_receipt_sha256": receipts["public"]["receipt_sha256"]}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
