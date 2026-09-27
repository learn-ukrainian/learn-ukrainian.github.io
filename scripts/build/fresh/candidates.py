"""Store-backed, single-form options for A1 form-choice items."""

from __future__ import annotations

from typing import Any

from scripts.curriculum.evidence.tags import to_oracle
from scripts.curriculum.resolver.narrow import learner_usable
from scripts.curriculum.resolver.tokenize import tokenize


def record_candidates(record: dict[str, Any]) -> list[dict[str, Any]]:
    """Keep every learner analysis; merge identical surfaces without losing ambiguity."""
    by_form: dict[str, dict[str, Any]] = {}
    record_id = record.get("id")
    for form in record.get("forms") or []:
        surface = form.get("form")
        if not isinstance(surface, str) or not surface or not learner_usable(form):
            continue
        tokens = tokenize(surface)
        if len(tokens) != 1 or tokens[0].text != surface:
            continue
        analysis = {"tags": form["tags"], "features": to_oracle(form["tags"])}
        candidate = by_form.setdefault(surface, {"form": surface, "record": record_id, "analyses": []})
        if analysis not in candidate["analyses"]:
            candidate["analyses"].append(analysis)
    for candidate in by_form.values():
        candidate["analyses"].sort(key=lambda analysis: analysis["tags"])
    return [by_form[surface] for surface in sorted(by_form)]


def _admitted(candidate: dict[str, Any], requires: dict[str, str]) -> bool:
    required = {f"{group}={value}" for group, value in requires.items()}
    return any(required <= set(analysis["features"]) for analysis in candidate["analyses"])


def _group_values(candidate: dict[str, Any], group: str) -> set[str]:
    prefix = f"{group}="
    return {
        feature[len(prefix) :]
        for analysis in candidate["analyses"]
        for feature in analysis["features"]
        if feature.startswith(prefix)
    }


def item_candidates(item: dict[str, Any], words: dict[str, Any], activity_type: str) -> list[dict[str, Any]]:
    """Offer the key and only distractors excluded in the taught feature.

    The complete slot demand is authored and independently confirmed elsewhere.
    This function never infers it from the sentence or an answer tag.
    """
    options = item.get("options") or []
    if activity_type == "fill-in":
        key_text = item.get("answer")
        bound_ids = [item.get("record")]
        key_id = item.get("record")
    elif activity_type in {"quiz", "multiple-choice"}:
        index = item.get("_resolved_key_index", item.get("correct"))
        if type(index) is not int or not 0 <= index < len(options):
            return []
        option = options[index]
        key_text = option.get("text") if isinstance(option, dict) else option
        bound_ids = item.get("option_records") or []
        if len(bound_ids) != len(options):
            return []
        key_id = bound_ids[index]
    else:
        return []

    requires = item.get("requires")
    group = item.get("tests_feature")
    if not isinstance(requires, dict) or not requires or not isinstance(group, str) or group not in requires:
        return []
    records = {record.get("id"): record for record in words.get("words") or []}
    key_record = records.get(key_id)
    if key_record is None:
        return []
    key = next((c for c in record_candidates(key_record) if c["form"] == key_text), None)
    if key is None or not _admitted(key, requires):
        return []
    key_values = _group_values(key, group)
    if not key_values:
        return []

    offered: list[dict[str, Any]] = []
    for record_id in sorted(rid for rid in set(bound_ids) if isinstance(rid, str)):
        record = records.get(record_id)
        if record is None:
            continue
        for candidate in record_candidates(record):
            admitted = _admitted(candidate, requires)
            values = _group_values(candidate, group)
            if (record_id, candidate["form"]) == (key_id, key_text):
                include = True
            else:
                include = not admitted and bool(values) and values.isdisjoint(key_values)
            if include:
                required = {f"{name}={value}" for name, value in requires.items()}
                analyses = [
                    {**analysis, "admits_requires": required <= set(analysis["features"])}
                    for analysis in candidate["analyses"]
                ]
                offered.append(
                    {**candidate, "analyses": analyses, "admitted": admitted, "tests_feature_values": sorted(values)}
                )
    return offered
