"""Lemma and grammatical slot binding for dictionary-backed paradigm stress (#9820)."""

from __future__ import annotations

from typing import Any

from scripts.verification.stress import _strip_stress, verify_stress
from scripts.verification.ulif_stress import analysis_features, readings, select_analyses


def resolve_paradigm_stress(lemma: str, form: str, tags: str, pos: str) -> dict[str, Any] | None:
    """Prefer the matching ULIF slot; withhold missing or conflicting readings.

    The fallback oracle receives the same lemma and tags. An unlabelled reading
    cannot authenticate a grammatical slot, even when the oracle reports ok.
    """
    if not lemma or not form or not tags or not pos:
        return None
    analysis = {"lemma": lemma, "tags": tags, "pos": pos}
    supplied = analysis_features(analysis)
    if not any(tag.startswith("upos=") for tag in supplied):
        return None
    slot = {tag for tag in supplied if tag.split("=", 1)[0] in {"upos", "Case", "Number"}}
    candidates = readings(form, supplied=supplied, lemma=lemma, vesum=[analysis])
    candidates = [match for match in candidates if slot <= set(match["required_tags"])]
    if not candidates:
        result = verify_stress(form, lemma=lemma, tags=tags)
        if result["status"] != "ok":
            return None
        candidates = result["matches"]
        if not candidates or any(
            not slot <= set(match.get("required_tags", []))
            or not select_analyses(match.get("vesum_analyses", []), supplied, lemma)
            for match in candidates
        ):
            return None
    choices = {match["stressed_form"] for match in candidates}
    if len(choices) != 1:
        return None
    stressed = choices.pop()
    if _strip_stress(stressed) != _strip_stress(form) or stressed == form:
        return None
    return {
        "form": stressed,
        "source": "+".join(sorted({match["source"] for match in candidates})),
    }
