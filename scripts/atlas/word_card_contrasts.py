"""Contrast-only admission for word-card projections (#8982).

This checks structure, source roles and assertion bindings, not whether a cited
passage proves a distortion. Linguistic admission still needs source review.
"""

from __future__ import annotations

import copy
from collections.abc import Iterable

from scripts.open_dataset.russification import (
    QuarantineError,
    QuarantineGate,
    _fold,
    _strings,
    build_contrastive_subset,
    validate_default_split,
)


def sum11_quotations(assertions: Iterable[dict]) -> Iterable[str]:
    """Retain known quotation bodies even when their assertions are withdrawn."""
    for assertion in assertions:
        if assertion.get("source_id") != "sum11":
            continue
        value = assertion.get("value")
        if isinstance(value, dict):
            pair = value.get("soviet_colonization_context")
            imposed = pair.get("imposed") if isinstance(pair, dict) else None
            value = imposed.get("text") if isinstance(imposed, dict) else None
        if isinstance(value, str) and value.strip():
            yield value


def validate_card_contrasts(card: dict, *, sum11_texts: Iterable[str] = ()) -> int:
    """Require red-flagged, sense-bound pairs and reject quotations elsewhere.

    Contrast values are {red_flag: true, soviet_colonization_context: <pair>};
    <pair> uses the existing russification-contrast.v1 input contract. Its id
    alone is the assertion's value_norm, so resolutions never detach a quote
    from its correction. An independently frozen inventory can also detect
    unlabelled quotations absent from this card's own pairs.
    """
    try:
        return _validate_card_contrasts(card, sum11_texts=sum11_texts)
    except (TypeError, AttributeError, KeyError) as exc:
        raise QuarantineError("invalid_contrast_card") from exc


def _validate_card_contrasts(card: dict, *, sum11_texts: Iterable[str]) -> int:
    assertions = card.get("assertions", [])
    senses = card.get("senses", [])
    if (
        not isinstance(assertions, list) or not all(isinstance(a, dict) for a in assertions)
        or not isinstance(senses, list) or not all(isinstance(s, dict) for s in senses)
        or any(not isinstance(s.get("fields", {}), dict) for s in senses)
    ):
        raise QuarantineError("invalid_contrast_card")
    identified = [a for a in assertions if "assertion_id" in a]
    by_id = {a["assertion_id"]: a for a in identified}
    if len(by_id) != len(identified):
        raise QuarantineError("duplicate_contrast_assertion")
    sense_ids = {s.get("sense_id") for s in senses}
    pairs = []
    contrast_ids = set()
    for assertion in assertions:
        if assertion.get("field") != "russification_exposed":
            continue
        note = assertion.get("value")
        if (
            not isinstance(note, dict)
            or set(note) != {"red_flag", "soviet_colonization_context"}
            or note["red_flag"] is not True
        ):
            raise QuarantineError("red_flagged_contrast_required")
        pair = note["soviet_colonization_context"]
        build_contrastive_subset([pair], opt_in=True)
        if (
            not isinstance(assertion.get("assertion_id"), str)
            or not assertion["assertion_id"].strip()
            or assertion.get("subject") != {"kind": "sense", "id": pair["sense_id"]}
            or pair["sense_id"] not in sense_ids
            or assertion.get("value_norm") != pair["pair_id"]
            or assertion.get("licence_ref", {}).get("register_source_id") != "sum11"
            or any(assertion.get(k) != pair["imposed"]["citation"][k]
                   for k in ("source_id", "snapshot_id", "locator"))
        ):
            raise QuarantineError("contrast_assertion_binding_required")
        norm = pair["norm"]
        target = by_id.get(norm["assertion_id"], {})
        if (
            target.get("status") != "active"
            or target.get("tier") not in {1, 2}
            or target.get("subject") != assertion["subject"]
            or target.get("field") == "russification_exposed"
            or target.get("value") != norm["text"]
            or target.get("review", {}).get("status") == "rejected"
            or target.get("mapping", {}).get("confidence", "high") not in {"high", "medium"}
            or target.get("mapping", {}).get("ambiguous", False)
            or any(target.get(k) != norm["citation"][k] for k in ("source_id", "snapshot_id", "locator"))
            or target.get("licence_ref", {}).get("register_source_id") != norm["citation"]["source_id"]
        ):
            raise QuarantineError("modern_norm_assertion_binding_required")
        pairs.append(pair)
        contrast_ids.add(assertion["assertion_id"])
    # Validate together: duplicate pair ids and contamination across pairs fail.
    build_contrastive_subset(pairs, opt_in=True)
    inventory = [*sum11_texts, *(p["imposed"]["text"] for p in pairs)]
    validate_default_split([p["norm"] for p in pairs], sum11_texts=inventory)
    quotations = QuarantineGate(inventory).quotations
    # Citation identifiers may name the source; surrounding metadata may not
    # repeat its quotation outside the validated pair.
    if quotations is not None:
        for assertion in assertions:
            if assertion.get("assertion_id") in contrast_ids:
                metadata = {k: v for k, v in assertion.items() if k != "value"}
                if any(next(quotations.iter(_fold(text)), None) is not None for text in _strings(metadata)):
                    raise QuarantineError("sum11_outside_contrast_pair")
    remaining = dict(card)
    remaining["assertions"] = [a for a in assertions if a.get("assertion_id") not in contrast_ids]
    remaining["senses"] = []
    resolutions = []
    for sense in senses:
        fields = dict(sense.get("fields", {}))
        if "russification_exposed" in fields:
            resolution = copy.deepcopy(fields.pop("russification_exposed"))
            if (
                not isinstance(resolution, dict)
                or not isinstance(resolution.get("values", []), list)
                or not all(isinstance(entry, dict) for entry in resolution.get("values", []))
            ):
                raise QuarantineError("invalid_contrast_card")
            for entry in resolution.get("values", []):
                # This fixed lineage id is metadata, never dictionary text.
                if entry.get("independence_groups") == ["G-SUM11"]:
                    entry["independence_groups"] = []
            resolutions.append(resolution)
        remaining["senses"].append({**sense, "fields": fields})
    validate_default_split([remaining, *resolutions], sum11_texts=inventory)
    return len(pairs)
