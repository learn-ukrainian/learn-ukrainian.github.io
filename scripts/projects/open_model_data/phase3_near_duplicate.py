#!/usr/bin/env python3
"""Deterministic, machine-pinned Phase 3 near-duplicate firewall.

This module only compares supplied identifiers and text.  It makes no
linguistic judgement.  Callers must persist the returned policy fingerprint
with partitions, evaluation seals, rule identities, and activation reports.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import unicodedata
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass
from difflib import SequenceMatcher
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[3]
DEFAULT_POLICY_PATH = ROOT / "data/projects/open_model_data/evidence/correction_protection_near_duplicate_policy_v1.json"
POLICY_ID = "near_duplicate_policy_v1"
POLICY_SCHEMA_VERSION = "near_duplicate_policy_v1"
PINNED_POLICY_FINGERPRINT = "19518efb07dd8ef4173b32487da7427f3c1eb0b8f8dd5d21b046cfc4dc5d560e"
REQUIRED_GOVERNS = frozenset(
    {
        "train_development_to_heldout_firewall",
        "ua_eval_exclusion",
        "public_canary_neighbour_exclusion",
        "canonical_rule_identity_collapse",
        "heldout_activation_counts",
    }
)
REQUIRED_SCOPES = frozenset({"document", "unit", "span"})
REQUIRED_FIELDS = (
    "source_document_identity",
    "unit_identity",
    "span_fingerprint",
    "normalized_surface",
)
TOKEN_RE = re.compile(r"[^\W_]+", re.UNICODE)


class NearDuplicatePolicyError(ValueError):
    """A policy, comparison request, or pinned fingerprint is unsafe."""


@dataclass(frozen=True, slots=True)
class TextFingerprint:
    """Deterministic text features used by one span comparison."""

    normalized_surface: str
    exact_fingerprint: str
    tokens: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class MatchResult:
    """A deterministic duplicate classification with its frozen policy pin."""

    classification: str
    duplicate: bool
    scope: str
    method: str
    token_jaccard: float
    normalized_edit_similarity: float
    policy_fingerprint_sha256: str

    def as_dict(self) -> dict[str, Any]:
        return {
            "classification": self.classification,
            "duplicate": self.duplicate,
            "method": self.method,
            "normalized_edit_similarity": self.normalized_edit_similarity,
            "policy_fingerprint_sha256": self.policy_fingerprint_sha256,
            "scope": self.scope,
            "token_jaccard": self.token_jaccard,
        }


def canonical_json(value: Any) -> str:
    """Return the canonical JSON form used to pin a policy and identities."""
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"), sort_keys=True)


def sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def policy_fingerprint(policy: Mapping[str, Any]) -> str:
    """Hash policy content while excluding its self-referential digest field."""
    value = dict(policy)
    value.pop("policy_fingerprint_sha256", None)
    return sha256_text(canonical_json(value) + "\n")


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise NearDuplicatePolicyError(message)


def _verified_policy_pin(policy: Mapping[str, Any]) -> str:
    """Require both the artifact's self-hash and this implementation's pin."""
    actual = policy_fingerprint(policy)
    _require(policy.get("policy_fingerprint_sha256") == actual, "near-duplicate policy fingerprint drift")
    _require(actual == PINNED_POLICY_FINGERPRINT, "near-duplicate implementation policy pin drift")
    return actual


def load_policy(
    path: Path = DEFAULT_POLICY_PATH,
    *,
    expected_fingerprint: str | None = None,
) -> dict[str, Any]:
    """Load and validate the policy, refusing self-hash or caller-pin drift."""
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise NearDuplicatePolicyError(f"cannot read near-duplicate policy: {exc}") from exc
    _require(isinstance(value, dict), "near-duplicate policy must be a JSON object")
    _require(value.get("schema_version") == POLICY_SCHEMA_VERSION, "wrong near-duplicate policy schema")
    _require(value.get("policy_id") == POLICY_ID, "wrong near-duplicate policy id")
    _require(value.get("fail_closed") is True, "near-duplicate policy is not fail closed")
    _require(set(value.get("governs", ())) == REQUIRED_GOVERNS, "near-duplicate policy governs drift")
    _require(set(value.get("scopes", ())) == REQUIRED_SCOPES, "near-duplicate policy scope drift")
    _require(tuple(value.get("compared_fields", ())) == REQUIRED_FIELDS, "near-duplicate compared fields drift")
    _require(
        tuple(value.get("normalization_steps", ()))
        == ("unicode_normalization", "casefold", "whitespace_collapse", "punctuation_tokenization"),
        "near-duplicate normalization drift",
    )
    _require(
        tuple(value.get("similarity_features", ()))
        == ("exact_fingerprint", "token_jaccard", "normalized_edit_similarity"),
        "near-duplicate similarity features drift",
    )
    _require(
        value.get("numeric_thresholds") == {"exact_match": 1.0, "near_duplicate_minimum": 0.9},
        "near-duplicate thresholds drift",
    )
    actual = _verified_policy_pin(value)
    if expected_fingerprint is not None:
        _require(expected_fingerprint == actual, "near-duplicate expected fingerprint drift")
    return value


def pinned_policy_fingerprint(
    *, path: Path = DEFAULT_POLICY_PATH, expected_fingerprint: str | None = None
) -> str:
    """Return the verified policy fingerprint for sealing a downstream artifact."""
    return str(load_policy(path, expected_fingerprint=expected_fingerprint)["policy_fingerprint_sha256"])


def policy_for_governed_use(
    governed_use: str,
    *,
    path: Path = DEFAULT_POLICY_PATH,
    expected_fingerprint: str | None = None,
) -> dict[str, Any]:
    """Return the verified policy only for one of its frozen consumers."""
    policy = load_policy(path, expected_fingerprint=expected_fingerprint)
    _require(governed_use in REQUIRED_GOVERNS, f"near-duplicate use is not governed: {governed_use}")
    return policy


def normalize(value: str) -> str:
    """Apply the policy's Unicode, case, whitespace, and punctuation treatment."""
    _require(isinstance(value, str), "near-duplicate text must be a string")
    collapsed = " ".join(unicodedata.normalize("NFKC", value).casefold().split())
    return " ".join(TOKEN_RE.findall(collapsed))


def fingerprint(value: str) -> TextFingerprint:
    """Produce the exact and token features for a normalized surface."""
    normalized = normalize(value)
    return TextFingerprint(
        normalized_surface=normalized,
        exact_fingerprint=sha256_text(normalized),
        tokens=tuple(normalized.split()),
    )


def _token_jaccard(first: Sequence[str], second: Sequence[str]) -> float:
    first_set, second_set = set(first), set(second)
    if not first_set and not second_set:
        return 1.0
    if not first_set or not second_set:
        return 0.0
    return len(first_set & second_set) / len(first_set | second_set)


def _edit_similarity(first: str, second: str) -> float:
    if not first and not second:
        return 1.0
    if not first or not second:
        return 0.0
    return SequenceMatcher(None, first, second, autojunk=False).ratio()


def classify_texts(
    left: str,
    right: str,
    *,
    scope: str = "span",
    policy: Mapping[str, Any] | None = None,
) -> MatchResult:
    """Classify text as exact, near, or nonmatch under the pinned policy.

    Near requires both token Jaccard and normalized edit similarity to meet the
    same frozen minimum.  This avoids a small shared token set or incidental
    character overlap becoming a duplicate decision on its own.
    """
    active = dict(policy) if policy is not None else load_policy()
    _require(scope in REQUIRED_SCOPES, f"unknown near-duplicate scope: {scope}")
    pin = _verified_policy_pin(active)
    if policy is not None:
        _require(active.get("policy_fingerprint_sha256") == pin, "near-duplicate policy fingerprint drift")
    first, second = fingerprint(left), fingerprint(right)
    threshold = float(active["numeric_thresholds"]["near_duplicate_minimum"])
    token_jaccard = _token_jaccard(first.tokens, second.tokens)
    edit_similarity = _edit_similarity(first.normalized_surface, second.normalized_surface)
    if first.exact_fingerprint == second.exact_fingerprint:
        label, method = "exact", "exact_fingerprint"
    elif token_jaccard >= threshold and edit_similarity >= threshold:
        label, method = "near", "token_jaccard_and_normalized_edit_similarity"
    else:
        label, method = "nonmatch", "below_near_duplicate_minimum"
    return MatchResult(label, label != "nonmatch", scope, method, token_jaccard, edit_similarity, pin)


def _field(record: Mapping[str, Any], name: str) -> str:
    value = record.get(name)
    _require(isinstance(value, str) and bool(value), f"missing required comparison field: {name}")
    return value


def classify_records(
    left: Mapping[str, Any],
    right: Mapping[str, Any],
    *,
    scope: str,
    policy: Mapping[str, Any] | None = None,
) -> MatchResult:
    """Compare document, unit, or span records at the requested frozen scope."""
    active = dict(policy) if policy is not None else load_policy()
    pin = _verified_policy_pin(active)
    _require(scope in REQUIRED_SCOPES, f"unknown near-duplicate scope: {scope}")
    if scope == "document":
        duplicate = _field(left, "source_document_identity") == _field(right, "source_document_identity")
        return MatchResult(
            "exact" if duplicate else "nonmatch", duplicate, scope, "source_document_identity",
            1.0 if duplicate else 0.0, 1.0 if duplicate else 0.0, pin,
        )
    if scope == "unit":
        same_document = _field(left, "source_document_identity") == _field(right, "source_document_identity")
        duplicate = same_document and _field(left, "unit_identity") == _field(right, "unit_identity")
        return MatchResult(
            "exact" if duplicate else "nonmatch", duplicate, scope, "source_document_identity_and_unit_identity",
            1.0 if duplicate else 0.0, 1.0 if duplicate else 0.0, pin,
        )
    left_span_fingerprint = _field(left, "span_fingerprint")
    right_span_fingerprint = _field(right, "span_fingerprint")
    if left_span_fingerprint == right_span_fingerprint:
        return MatchResult(
            "exact", True, scope, "span_fingerprint", 1.0, 1.0, pin
        )
    return classify_texts(
        _field(left, "normalized_surface"), _field(right, "normalized_surface"), scope=scope, policy=active
    )


def duplicate_or_fail_closed(
    left: Mapping[str, Any] | str,
    right: Mapping[str, Any] | str,
    *,
    scope: str = "span",
    policy: Mapping[str, Any] | None = None,
) -> bool:
    """Return true for duplicates and for malformed/disputed comparisons."""
    try:
        if isinstance(left, str) and isinstance(right, str):
            return classify_texts(left, right, scope=scope, policy=policy).duplicate
        _require(isinstance(left, Mapping) and isinstance(right, Mapping), "comparison values must share a type")
        return classify_records(left, right, scope=scope, policy=policy).duplicate
    except (NearDuplicatePolicyError, KeyError, TypeError, ValueError):
        return True


def canonical_rule_identity(rule: Mapping[str, Any], *, policy: Mapping[str, Any] | None = None) -> str:
    """Return a stable identity for rule collapse without source or free context."""
    active = dict(policy) if policy is not None else load_policy()
    pin = _verified_policy_pin(active)
    original, replacement = _rule_surface_pair(rule)
    payload = {
        "policy_fingerprint_sha256": pin,
        "original_surface": original,
        "replacement": replacement,
    }
    return f"near_duplicate_rule:{sha256_text(canonical_json(payload))}"


def _rule_surface_pair(rule: Mapping[str, Any]) -> tuple[str, str]:
    """Return the normalized incorrect-to-correct pair used for rule collapse."""
    original = rule.get("original_surface", rule.get("surface", rule.get("incorrect")))
    replacement = rule.get("replacement", rule.get("correct"))
    _require(isinstance(original, str) and isinstance(replacement, str), "rule needs original/surface and replacement text")
    return normalize(original), normalize(replacement)


def _pair_text(pair: tuple[str, str]) -> str:
    """Encode pair sides explicitly so token boundaries cannot blur the arrow."""
    return f"incorrect {pair[0]} replacement {pair[1]}"


def _pairs_are_duplicates(
    left: tuple[str, str], right: tuple[str, str], *, policy: Mapping[str, Any]
) -> bool:
    """Compare the whole normalized surface-pair key under the frozen policy."""
    return classify_texts(_pair_text(left), _pair_text(right), policy=policy).duplicate


def collapse_canonical_rules(
    rules: Iterable[Mapping[str, Any]], *, policy: Mapping[str, Any] | None = None
) -> dict[str, list[dict[str, Any]]]:
    """Collapse exact and near surface pairs into deterministic components.

    Pairwise near-duplicate matches are converted to connected components before
    counts are made.  The lexicographically first normalized pair is the
    component representative, so input ordering never changes the identity.
    """
    active = dict(policy) if policy is not None else load_policy()
    _verified_policy_pin(active)
    ordered = sorted(
        (dict(rule) for rule in rules),
        key=lambda rule: (canonical_json(_rule_surface_pair(rule)), canonical_json(rule)),
    )
    parents = list(range(len(ordered)))

    def find(index: int) -> int:
        while parents[index] != index:
            parents[index] = parents[parents[index]]
            index = parents[index]
        return index

    def union(first: int, second: int) -> None:
        left_root, right_root = find(first), find(second)
        if left_root != right_root:
            parents[max(left_root, right_root)] = min(left_root, right_root)

    pairs = [_rule_surface_pair(rule) for rule in ordered]
    for first in range(len(ordered)):
        for second in range(first + 1, len(ordered)):
            if _pairs_are_duplicates(pairs[first], pairs[second], policy=active):
                union(first, second)

    components: dict[int, list[int]] = {}
    for index in range(len(ordered)):
        components.setdefault(find(index), []).append(index)
    collapsed: dict[str, list[dict[str, Any]]] = {}
    for members in components.values():
        representative = min(members, key=lambda index: (canonical_json(pairs[index]), canonical_json(ordered[index])))
        identity = canonical_rule_identity(ordered[representative], policy=active)
        collapsed[identity] = [ordered[index] for index in members]
    return {identity: collapsed[identity] for identity in sorted(collapsed)}


def nonduplicate_activation_count(
    activations: Iterable[Mapping[str, Any]], *, policy: Mapping[str, Any] | None = None
) -> int:
    """Count held-out activations once per canonical rule, failing closed on rows."""
    active = dict(policy) if policy is not None else load_policy()
    rules: list[Mapping[str, Any]] = []
    for row in activations:
        _require(row.get("duplicate") is False, "activation duplicate state must be explicitly false")
        rule = row.get("rule")
        _require(isinstance(rule, Mapping), "activation requires rule mapping")
        rules.append(rule)
    return len(collapse_canonical_rules(rules, policy=active))


def _json_output(value: Any) -> None:
    print(canonical_json(value))


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--policy", type=Path, default=DEFAULT_POLICY_PATH)
    parser.add_argument("--expected-fingerprint")
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("verify")
    normalize_parser = commands.add_parser("normalize")
    normalize_parser.add_argument("text")
    fingerprint_parser = commands.add_parser("fingerprint")
    fingerprint_parser.add_argument("text")
    classify_parser = commands.add_parser("classify")
    classify_parser.add_argument("left")
    classify_parser.add_argument("right")
    classify_parser.add_argument("--scope", choices=sorted(REQUIRED_SCOPES), default="span")
    args = parser.parse_args(argv)
    try:
        policy = load_policy(args.policy, expected_fingerprint=args.expected_fingerprint)
        if args.command == "verify":
            _json_output({"policy_fingerprint_sha256": policy["policy_fingerprint_sha256"], "verified": True})
        elif args.command == "normalize":
            _json_output({"normalized_surface": normalize(args.text)})
        elif args.command == "fingerprint":
            item = fingerprint(args.text)
            _json_output({"exact_fingerprint": item.exact_fingerprint, "normalized_surface": item.normalized_surface, "tokens": list(item.tokens)})
        else:
            _json_output(classify_texts(args.left, args.right, scope=args.scope, policy=policy).as_dict())
    except NearDuplicatePolicyError as exc:
        parser.error(str(exc))
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
