"""Exact reference matching. Private meanings are inputs, never diagnostics.

Parser positions follow `_sense_spans` over `_sub_senses` in source order.
Only the closed grammatical labels below can disappear. All other notes,
including register, domain, scale and anatomical/mechanical qualifiers, bind.
"""

from __future__ import annotations

import json
import re
import unicodedata
from collections.abc import Iterable

from . import sources

VERSION = "reference_sense_v1"
METHOD = "a1_reference_meaning.v1"
GRAMMATICAL_ANNOTATIONS = frozenset(
    {
        "noun",
        "verb",
        "adjective",
        "adverb",
        "pronoun",
        "determiner",
        "particle",
        "interjection",
        "preposition",
        "conjunction",
        "transitive",
        "intransitive",
        "perfective",
        "imperfective",
        "plural",
        "singular",
        "masculine",
        "feminine",
        "neuter",
    }
)


def normalize(text: str, pos: str) -> str:
    """Normalise spelling and approved grammar only; retain meaning qualifiers."""
    value = " ".join(unicodedata.normalize("NFC", text).casefold().split())
    value = re.sub(
        r"\(([^()]*)\)|\[([^\[\]]*)\]",
        lambda m: "" if (m[1] or m[2]).rstrip(".").strip() in GRAMMATICAL_ANNOTATIONS else m[0],
        value,
    )
    value = " ".join(value.split()).rstrip(".!?;:").rstrip()
    return value.removeprefix("to ") if pos == "verb" else value


def atoms(text: str, pos: str) -> tuple[str, ...]:
    """Split complete alternatives outside notes; suffix notes bind the group.

    Internal/multiple notes leave uncertain scope unsplit. A suffix qualifier
    is attached to every atom, so a bare match cannot evade its restriction.
    """
    value = normalize(text, pos)
    notes = list(re.finditer(r"\([^()]*\)|\[[^\[\]]*\]", value))
    suffix = ""
    if notes:
        if len(notes) != 1 or notes[0].end() != len(value):
            return (value,)
        suffix = " " + notes[0][0]
        value = value[: notes[0].start()].strip()
    if not sources._well_formed_kaikki_gloss(value):
        return ()
    parts = re.split(r"\s*(?:[,;/]|\bor\b)\s*", value)
    return tuple(dict.fromkeys(normalize(part + suffix, pos) for part in parts if part.strip()))


def row_spans(row: dict) -> list[tuple[str, str]]:
    """Return (exact visible span, group context) in the existing parser order."""
    raw = row.get("translations") or []
    try:
        raw = json.loads(raw) if isinstance(raw, str) else raw
    except (ValueError, TypeError):
        return []
    if not isinstance(raw, list):
        return []
    return [
        (span, part)
        for sense in raw
        if isinstance(sense, str)
        for part in sources._sub_senses(sense)
        for span in sources._sense_spans(part)
    ]


def candidates(word: dict, rows: list[dict], *, pronoun_entry: bool | None = None) -> list[dict]:
    """Recheck lemma and POS even for callers that bypass the batched lookup."""
    lemma, pos = word["lemma"], word["pos"]
    if pronoun_entry is None:
        pronoun_entry = any("pron" in f.get("tags", "").split(":") for f in word.get("forms", []))
    rows = [
        r
        for r in rows
        if sources.unstressed_headword(r["word"]) == sources.unstressed_headword(lemma)
        and r["pos"] in sources.GLOSS_POS.get(pos, (pos,))
        and not (pos in sources.ALPHABET_GUARD_POS and sources.is_alphabet_letter_gloss(r))
        and not sources.has_incompatible_function_label(r, pos)
    ]
    labelled = [r for r in rows if r["pos"] == {"prep": "preposition", "conj": "conjunction"}.get(pos)]
    if labelled:
        rows = [r for r in rows if r["pos"] != "particle"]
    rows = sources.filter_pronominal_gloss_rows(rows, lemma, pos, pronoun_entry)
    result = []
    for row in sorted(rows, key=lambda r: r["id"]):
        for index, (span, group) in enumerate(row_spans(row)):
            if not sources.is_learner_gloss(span):
                continue
            context = span
            # Preserve the trailing group's qualifier on earlier alternatives.
            note = re.search(r"(\([^()]*\)|\[[^\[\]]*\])\s*$", group)
            if note and note[0].strip() not in span:
                context += " " + note[0].strip()
            result.append(
                {
                    "table": "dmklinger_uk_en",
                    "id": row["id"],
                    "row_sha256": sources.row_digest(row),
                    "span_index": index,
                    "span": span,
                    "atoms": atoms(context, pos),
                    "headword": row["word"],
                }
            )
    return result


def select(
    word: dict,
    rows: list[dict],
    meaning: str,
    payload: dict | None = None,
    *,
    ulif_entries: Iterable[dict] = (),
    pronoun_entry: bool | None = None,
) -> sources.GlossSelection:
    """Exact atoms only; every reference head must resolve to one visible span."""
    pool = candidates(word, rows, pronoun_entry=pronoun_entry)
    heads = atoms(meaning, word["pos"])
    if not heads:
        return sources.GlossSelection(reason="reference_no_match")
    matches = [[c for c in pool if head in c["atoms"]] for head in heads]
    # A stressed, uniquely bound ULIF homonym can restrict rows. Shared-spelling
    # homonyms may be resolved only by a unique matching sense across all rows.
    pronoun = (
        pronoun_entry
        if pronoun_entry is not None
        else any("pron" in f.get("tags", "").split(":") for f in word.get("forms", []))
    )
    homonyms = sources._gloss_homonyms(word, ulif_entries, pronoun)
    key = word.get("ulif", {}).get("key", []) if isinstance(word.get("ulif"), dict) else []
    bound = [e for e in homonyms if key == [e["canonical_headword"], e["homonym_index"]]]
    if (
        bound
        and sum(
            sources.normalize_spelling(e["canonical_headword"]) == sources.normalize_spelling(key[0]) for e in homonyms
        )
        == 1
    ):
        matches = [
            [c for c in group if sources.normalize_spelling(c["headword"]) == sources.normalize_spelling(key[0])]
            for group in matches
        ]
    if any(len({c["span"] for c in group}) > 1 for group in matches):
        return sources.GlossSelection(reason="reference_ambiguous")
    if any(not group for group in matches):
        if len(heads) > 1:
            return sources.GlossSelection(reason="reference_multi_head")
        senses, _ = sources.aligned_kaikki_senses(payload, word["pos"], pronoun)
        only = any(heads[0] in atoms(s, word["pos"]) for s in senses if sources.is_learner_gloss(s))
        return sources.GlossSelection(reason="reference_kaikki_only" if only else "reference_no_match")
    if len({group[0]["span"] for group in matches}) != 1:
        return sources.GlossSelection(reason="reference_multi_head")
    chosen = min((c for group in matches for c in group), key=lambda c: (c["id"], c["span_index"]))
    ref = {k: chosen[k] for k in ("table", "id", "row_sha256", "span_index", "span")}
    return sources.GlossSelection(chosen["span"], "dmklinger_uk_en", ref)
