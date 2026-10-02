"""Source-faithful ULIF form readings and conservative grammatical joins."""

from __future__ import annotations

import json
from typing import Any

from scripts.curriculum.evidence.tags import TagMapper
from scripts.lexicon.runner.ulif_dictua_parse import lookup_ulif_label
from scripts.wiki.sources_db import normalize_ulif_dictua_query, ulif_stress_rows


def _features(row: dict) -> set[str]:
    """Map the existing parser's VESUM atoms and entry label to UD features."""
    atoms = set(json.loads(row["grammatical_tags"]))
    label = row["grammatical_label"].split(",", 1)[0].strip()
    grammar = lookup_ulif_label(label)
    if grammar:
        atoms.update(grammar.tags)
    # Additional entry POS labels not mapped by the forms parser.
    labels = {
        "сполучник": ("conj",),
        "займенник": ("noun", "pron"),
        "прізвище": ("noun", "prop"),
        "власна назва": ("noun", "prop"),
        "множинний іменник": ("noun", "p"),
        "вигук": ("intj",),
        "прийменник": ("prep",),
        "частка": ("part",),
        "числівник": ("numr",),
        "числівник кількісний": ("numr",),
        "числівник порядковий": ("adj", "numr"),
        "дієприкметник": ("adj", "adjp"),
    }
    atoms.update(labels.get(label, ()))
    features = set(TagMapper()(":".join(sorted(atoms))))
    # ULIF marks proper headwords by case even under a generic noun label.
    if "upos=NOUN" in features and row.get("canonical_headword", "")[:1].isupper():
        features.discard("upos=NOUN")
        features.add("upos=PROPN")
    if label == "присудкове слово":
        features.add("upos=X")
    return features


def analysis_features(analysis: dict) -> set[str]:
    """Preserve pronoun/proper-name POS rather than the coarse VESUM column."""
    features = set(TagMapper()(analysis.get("tags", "")))
    # VESUM's noun:numr is a nominal numeral, with POS noun in its analysis.
    if analysis.get("pos") == "noun" and "upos=NOUN" in features:
        features.discard("upos=NUM")
    if analysis.get("pos") == "noninfl" and "predic" in analysis.get("tags", "").split(":"):
        features.add("upos=X")
    return features


def select_analyses(vesum: list[dict], supplied: set[str], lemma: str | None) -> list[dict]:
    """Caller context selects VESUM analyses before either stress source."""
    from scripts.verification.stress import _strip_stress

    bare = normalize_ulif_dictua_query(_strip_stress(lemma)) if lemma else None
    return [
        v
        for v in vesum
        if (bare is None or normalize_ulif_dictua_query(_strip_stress(v.get("lemma", ""))) == bare)
        and compatible(analysis_features(v), supplied)
    ]


def joined_analyses(row: dict, vesum: list[dict]) -> list[dict]:
    """A row must positively join the entry lemma and a known, matching POS."""
    from scripts.verification.stress import _strip_stress

    lemma = normalize_ulif_dictua_query(_strip_stress(row["entry_key"].rsplit("#", 1)[0]))
    features = _features(row)
    pos = {t for t in features if t.startswith("upos=")}
    return [
        v
        for v in vesum
        if lemma == normalize_ulif_dictua_query(_strip_stress(v.get("lemma", "")))
        and len(pos) == 1
        and any(t.startswith("upos=") for t in analysis_features(v))
        and compatible(features, analysis_features(v))
    ]


def compatible(required: set[str], supplied: set[str]) -> bool:
    """No shared feature may conflict; unknown features cannot select a reading."""

    def values(tags: set[str]) -> dict[str, set[str]]:
        grouped: dict[str, set[str]] = {}
        for tag in tags:
            if "=" in tag:
                key, value = tag.split("=", 1)
                grouped.setdefault(key, set()).add(value)
        return grouped

    left, right = values(required), values(supplied)
    return all(left[key] & right[key] for key in left.keys() & right.keys())


def readings(form: str, *, supplied: set[str], lemma: str | None, vesum: list[dict]) -> list[dict[str, Any]]:
    """Return each stress choice once, retaining every supporting form row."""
    from scripts.verification.stress import (
        _build_match,
        _stress_positions_in_marked_string,
        _strip_stress,
    )

    rows = ulif_stress_rows(form)
    if lemma or form != form.lower():
        for spelling in (form.lower(), form.title()):
            rows += [row for row in ulif_stress_rows(spelling) if row not in rows]
    selected: list[tuple[dict, set[str], list[dict]]] = []
    for row in rows:
        indices = json.loads(row["stress_vowel_indices"])
        if not indices or any(i < 0 or i >= len(form) for i in indices):
            continue
        if lemma:
            bare = normalize_ulif_dictua_query(_strip_stress(lemma))
            if row["normalized_query"] != bare:
                continue
            if _stress_positions_in_marked_string(lemma)[1] and (
                _stress_positions_in_marked_string(lemma)[1]
                != _stress_positions_in_marked_string(row["canonical_headword"])[1]
            ):
                continue
        features = _features(row)
        if supplied and not compatible(features, supplied):
            continue
        witnesses = joined_analyses(row, select_analyses(vesum, supplied, lemma))
        if not witnesses:
            continue
        selected.append((row, features, witnesses))

    # If a supplied case/number is represented, omit lemma-only rows, which
    # otherwise could reintroduce a stress rejected by the paradigm filter.
    grammatical = {t.split("=", 1)[0] for t in supplied} & {"Case", "Number", "Tense", "Person", "VerbForm"}
    if grammatical and any(not row["is_lemma"] for row, _, _ in selected):
        selected = [(row, features, witnesses) for row, features, witnesses in selected if not row["is_lemma"]]

    grouped: dict[tuple[int, ...], dict] = {}
    for row, features, witnesses in selected:
        indices = tuple(json.loads(row["stress_vowel_indices"]))
        match = grouped.get(indices)
        if match is None:
            match = _build_match(form, [i + 1 for i in indices], sorted(features), override_applied=False)
            match.update(
                source="ulif", evidence=[], grammatical_tags=[], vesum_analyses=[], dual_stress=False, variants=[]
            )
            grouped[indices] = match
        match["evidence"].append(
            {
                k: row[k]
                for k in (
                    "id",
                    "entry_id",
                    "entry_key",
                    "source_page_sha256",
                    "source_entry_fingerprint",
                    "grammatical_tags",
                )
            }
        )
        match["grammatical_tags"].append(json.loads(row["grammatical_tags"]))
        match["dual_stress"] |= bool(row["dual_stress_flag"])
        for witness in witnesses:
            if witness not in match["vesum_analyses"]:
                match["vesum_analyses"].append(witness)
        if row["dual_stress_flag"] and "-" not in form:
            match["variants"] = [form[: i + 1] + "\u0301" + form[i + 1 :] for i in indices]
        else:
            match["variants"] = [match["stressed_form"]]
    for match in grouped.values():
        if match["dual_stress"] and "-" not in form:
            from scripts.verification.teaching_stress import sourced_teaching_choice

            choice = sourced_teaching_choice(form, match["vowel_indices"])
            if choice:
                match.update(choice)
        witnesses = match["vesum_analyses"]
        match["vesum"] = witnesses[0] if len(witnesses) == 1 else None
    return list(grouped.values())
