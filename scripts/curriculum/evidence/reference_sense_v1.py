"""Exact reference matching with classified group notes and source atom provenance.

Closed label lists below are the only annotation vocabulary. Classify before
splitting: leading/trailing labels bind every atom; internal/unknown notes fail
closed. Unlabelled trailing parentheses are definitions, retained in signatures.
"""

from __future__ import annotations

import json
import re
import unicodedata
from collections.abc import Iterable
from dataclasses import dataclass

from . import sources

VERSION = "reference_sense_v1"
METHOD = "a1_reference_meaning.v1"
REF_FIELDS = ("table", "id", "row_sha256", "span_index", "atom_index", "span")
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
        "possessive",
        "reflexive",
        "uncountable",
        "countable",
        "predicative",
        "impersonal",
        "proper noun",
        "personal",
        "relative",
        "interrogative",
        "+ genitive",
        "+ accusative",
        "+ dative",
        "+ instrumental",
        "+ locative",
        "+ nominative",
        "+ vocative",
    }
)
# Canonical register names come from the existing selector's shared vocabulary.
RESTRICTING_LABELS = {
    **{label: label for label in sources.REGISTER_LABELS.values()},
    "paganism": "paganism",
    "short scale": "short scale",
    "long scale": "long scale",
    "canada": "canada",
    "canadian": "canada",
    "uk": "uk",
    "british": "uk",
    "us": "us",
    "american": "us",
    "australia": "australia",
    "australian": "australia",
    "new zealand": "new zealand",
    "ireland": "ireland",
    "irish": "ireland",
    "scotland": "scotland",
    "scottish": "scotland",
    "ukraine": "ukraine",
}
TOPIC_LABELS = {
    "sports": "sports",
    "sport": "sports",
    "medicine": "medicine",
    "medical": "medicine",
    "music": "music",
    "musical": "music",
    "furniture": "furniture",
    "anatomy": "anatomy",
    "anatomical": "anatomy",
    "mechanics": "mechanics",
    "mechanical": "mechanics",
    "biology": "biology",
    "botany": "botany",
    "zoology": "zoology",
    "chemistry": "chemistry",
    "physics": "physics",
    "mathematics": "mathematics",
    "mathematical": "mathematics",
    "linguistics": "linguistics",
    "grammar": "grammar",
    "computing": "computing",
    "computer science": "computing",
    "law": "law",
    "legal": "law",
    "religion": "religion",
    "military": "military",
    "agriculture": "agriculture",
    "architecture": "architecture",
    "astronomy": "astronomy",
    "geography": "geography",
    "geology": "geology",
    "economics": "economics",
    "finance": "finance",
    "psychology": "psychology",
    "technology": "technology",
}
LABELS = {**{label: None for label in GRAMMATICAL_ANNOTATIONS}, **RESTRICTING_LABELS, **TOPIC_LABELS}
_REGION_EDGE_LABELS = frozenset({"ukraine", "us", "uk"})
_REGISTER_PATTERNS = [
    (re.compile(r"^(?:" + pattern + r")$"), label) for pattern, label in sources.REGISTER_LABELS.items()
]
_LABEL_PATTERN = re.compile(
    r"(?<!\w)(?:"
    + "|".join([*sources.REGISTER_LABELS, *(re.escape(s) for s in sorted(LABELS, key=lambda s: (-len(s), s)))])
    + r")(?!\w)"
)


def normalize(text: str, pos: str) -> str:
    """Normalise equality; only complete grammatical notes disappear here."""
    value = " ".join(unicodedata.normalize("NFC", text).casefold().split())
    value = re.sub(
        r"\(([^()]*)\)|\[([^\[\]]*)\]",
        lambda m: "" if (m[1] or m[2]).rstrip(".").strip() in GRAMMATICAL_ANNOTATIONS else m[0],
        value,
    )
    value = " ".join(value.split()).rstrip(".!?;:").rstrip()
    return value.removeprefix("to ") if pos == "verb" else value


@dataclass(frozen=True)
class Group:
    head: str = ""
    labels: tuple[str, ...] = ()
    definitions: tuple[str, ...] = ()
    reason: str | None = None


def classify(text: str) -> Group:
    """Read balanced outer notes, including nested labels, before atom splitting.

    Prefix notes must consist entirely of known labels. Suffix prose with no
    labels is a definition; nested labels may qualify that prose. Comma/semicolon
    label lists with an unknown member and internal notes have uncertain scope.
    """
    if not sources._well_formed_kaikki_gloss(text):
        return Group(reason="uncertain_scope")
    prefix = re.match(r"^\s*([\w -]+):\s*(.+)$", text, re.DOTALL)
    if prefix:
        label = normalize(prefix[1], "noun")
        if label not in TOPIC_LABELS and (
            label in RESTRICTING_LABELS or any(pattern.fullmatch(label) for pattern, _ in _REGISTER_PATTERNS)
        ):
            return Group(reason="unknown_label")
        group = classify(prefix[2])
        if label not in TOPIC_LABELS:
            # Unknown prefixes remain unselectable, but a well-scoped head
            # can still compete with a bare sense of that same atom.
            return Group(
                group.head,
                tuple(sorted({*group.labels, "topic:" + label})),
                group.definitions,
                group.reason or "unknown_label",
            )
        return Group(group.head, tuple(sorted({*group.labels, TOPIC_LABELS[label]})), group.definitions, group.reason)
    notes, stack, start = [], [], 0
    for index, char in enumerate(text):
        if char in "([":
            if not stack:
                start = index
            stack.append(char)
        elif char in ")]":
            stack.pop()
            if not stack:
                notes.append((start, index + 1, text[start + 1 : index]))
    if not notes:
        return Group(text.strip())
    # Pure grammatical notes have no scope and disappear even between atoms.
    ignored = [n for n in notes if normalize(n[2], "noun") in GRAMMATICAL_ANNOTATIONS]
    if ignored:
        for start, end, _ in reversed(ignored):
            text = text[:start] + text[end:]
        return classify(text)
    # Only contiguous prefix and suffix notes have a definite group scope.
    head_start, head_end = 0, len(text.rstrip().rstrip(".!?;:"))
    leading, trailing = [], []
    for note in notes:
        if not text[head_start : note[0]].strip():
            leading.append(note)
            head_start = note[1]
        else:
            break
    for note in reversed(notes[len(leading) :]):
        if not text[note[1] : head_end].strip():
            trailing.append(note)
            head_end = note[0]
        else:
            break
    if len(leading) + len(trailing) != len(notes):
        return Group(reason="uncertain_scope")
    labels, definitions = set(), []
    for note in notes:
        value = " ".join(unicodedata.normalize("NFC", note[2]).casefold().split())
        if value.startswith(("(", "[")) and classify(value).reason:
            return Group(reason="unknown_label")
        matches = list(_LABEL_PATTERN.finditer(value))
        # Country abbreviations/names inside prose are definition text. Only a
        # whole edge note or nested parenthetical is a region label.
        matches = [
            m
            for m in matches
            if m[0] not in _REGION_EDGE_LABELS
            or (value.strip(" .") == m[0] or re.search(r"[\[(]\s*" + re.escape(m[0]) + r"\s*[\])]", value))
        ]
        for match in matches:
            canonical = LABELS.get(match[0])
            if match[0] not in LABELS:
                canonical = next(label for pattern, label in _REGISTER_PATTERNS if pattern.fullmatch(match[0]))
            if canonical is not None:
                labels.add(canonical)
        remainder = value
        for match in reversed(matches):
            remainder = remainder[: match.start()] + remainder[match.end() :]
        remainder = remainder.strip(" ()[],;/+.!:")
        if note in leading and remainder:
            return Group(reason="unknown_label")
        if not remainder:
            continue
        # A partly recognised flat label list is not definitional prose.
        if matches and not any(c in value for c in "()[]") and any(c in value for c in ",;/"):
            return Group(reason="unknown_label")
        definitions.append(value)
    head = text[head_start:head_end].strip()
    if not head:
        return Group(reason="uncertain_scope")
    return Group(head, tuple(sorted(labels)), tuple(definitions))


def source_atoms(head: str) -> tuple[str, ...]:
    """Source spelling, in order; only the three specified separators split."""
    return tuple(part.strip() for part in re.split(r"[,;/]", head) if part.strip())


def atoms(text: str, pos: str) -> tuple[str, ...]:
    """Compatibility accessor for normalized heads of a classified group."""
    group = classify(text)
    return () if group.reason else tuple(dict.fromkeys(normalize(a, pos) for a in source_atoms(group.head)))


def row_spans(row: dict) -> list[tuple[str, str]]:
    """Existing parser positions, with the complete unsplit annotation group."""
    raw = row.get("translations") or []
    try:
        raw = json.loads(raw) if isinstance(raw, str) else raw
    except (ValueError, TypeError):
        return []
    if not isinstance(raw, list):
        return []
    return [
        (span, sense)
        for sense in raw
        if isinstance(sense, str)
        for part in sources._sub_senses(sense)
        for span in sources._sense_spans(part)
    ]


def candidates(
    word: dict,
    rows: list[dict],
    *,
    pronoun_entry: bool | None = None,
    report: dict | None = None,
    include_competitors: bool = False,
) -> list[dict]:
    """Classify before splitting; recheck lemma/POS before any candidate."""
    if word.get("kind") == "formula":
        from .formulas import headword, printed_headword

        names = {printed_headword(word["text"]), *(headword(a) for a in word.get("aliases", []))}
        rows = [r for r in rows if headword(r["word"]) in names]
        # Re-enter the same parser with each row's exact identity, without the lexical POS gates.
        result = []
        for row in sorted(rows, key=lambda r: r["id"]):
            result.extend(
                candidates({"lemma": row["word"], "pos": row["pos"], "formula_parser": True}, [row], report=report)
            )
        return result
    lemma, pos = word["lemma"], word["pos"]
    if pronoun_entry is None:
        pronoun_entry = any("pron" in f.get("tags", "").split(":") for f in word.get("forms", []))
    rows = (
        rows
        if word.get("formula_parser")
        else [
            r
            for r in rows
            if sources.unstressed_headword(r["word"]) == sources.unstressed_headword(lemma)
            and r["pos"] in sources.GLOSS_POS.get(pos, (pos,))
            and not (pos in sources.ALPHABET_GUARD_POS and sources.is_alphabet_letter_gloss(r))
            and not sources.has_incompatible_function_label(r, pos)
        ]
    )
    labelled = [r for r in rows if r["pos"] == {"prep": "preposition", "conj": "conjunction"}.get(pos)]
    if labelled and not word.get("formula_parser"):
        rows = [r for r in rows if r["pos"] != "particle"]
    if not word.get("formula_parser"):
        rows = sources.filter_pronominal_gloss_rows(rows, lemma, pos, pronoun_entry)
    result = []
    for row in sorted(rows, key=lambda r: r["id"]):
        for index, (span, context) in enumerate(row_spans(row)):
            group = classify(context)
            if group.reason:
                if report is not None:
                    field = group.reason + "_spans"
                    report[field] = report.get(field, 0) + 1
                if not include_competitors or group.reason != "unknown_label" or not group.head:
                    continue
            # The parser may already split commas/semicolons. Classify its span
            # only to remove notes; labels always come from the complete group.
            local = classify(span)
            if local.reason and (local.reason != "unknown_label" or not local.head):
                continue
            for atom_index, atom in enumerate(source_atoms(local.head)):
                if not sources.is_learner_gloss(atom):
                    continue
                result.append(
                    {
                        "table": "dmklinger_uk_en",
                        "id": row["id"],
                        "row_sha256": sources.row_digest(row),
                        "span_index": index,
                        "atom_index": atom_index,
                        "span": atom,
                        "atoms": (normalize(atom, pos),),
                        "labels": group.labels,
                        "definitions": group.definitions,
                        "headword": row["word"],
                        **({"competition_only": True} if group.reason or local.reason else {}),
                    }
                )
    return result


def display_signature(candidate: dict) -> tuple:
    """Duplicate collapse follows the text and restrictions the learner sees."""
    return candidate["span"], tuple(candidate["labels"])


def signature(candidate: dict) -> tuple:
    """The source sense retains its definition even though it is not displayed."""
    return (*display_signature(candidate), tuple(candidate["definitions"]))


def select(
    word: dict,
    rows: list[dict],
    meaning: str,
    payload: dict | None = None,
    *,
    ulif_entries: Iterable[dict] = (),
    pronoun_entry: bool | None = None,
    report: dict | None = None,
) -> sources.GlossSelection:
    """Every head must resolve to the same displayed atom and label signature."""
    pool = candidates(word, rows, pronoun_entry=pronoun_entry, report=report, include_competitors=True)
    reference = classify(meaning)
    heads = atoms(meaning, word["pos"])
    if not heads:
        return sources.GlossSelection(reason="reference_no_match")
    matches = [
        [c for c in pool if head in c["atoms"] and reference.labels == c["labels"] and not c.get("competition_only")]
        for head in heads
    ]
    topic_labels = set(TOPIC_LABELS.values())
    competitors = [
        [
            c
            for c in pool
            if head in c["atoms"]
            and set(reference.labels) < set(c["labels"])
            and all(
                label in topic_labels or label.startswith("topic:")
                for label in set(c["labels"]) - set(reference.labels)
            )
        ]
        for head in heads
    ]
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
        competitors = [
            [c for c in group if sources.normalize_spelling(c["headword"]) == sources.normalize_spelling(key[0])]
            for group in competitors
        ]
    if any(
        selected and any(signature(other) != signature(c) for other in competing for c in selected)
        for selected, competing in zip(matches, competitors, strict=True)
    ):
        return sources.GlossSelection(reason="reference_ambiguous")
    if any(len({display_signature(c) for c in group}) > 1 for group in matches):
        return sources.GlossSelection(reason="reference_ambiguous")
    if any(not group for group in matches):
        if len(heads) > 1:
            return sources.GlossSelection(reason="reference_multi_head")
        senses, _ = sources.aligned_kaikki_senses(payload, word["pos"], pronoun)
        only = any(heads[0] in atoms(s, word["pos"]) and classify(s).labels == reference.labels for s in senses)
        return sources.GlossSelection(reason="reference_kaikki_only" if only else "reference_no_match")
    if len({signature(group[0]) for group in matches}) != 1:
        return sources.GlossSelection(reason="reference_multi_head")
    chosen = min((c for group in matches for c in group), key=lambda c: (c["id"], c["span_index"], c["atom_index"]))
    ref = {k: chosen[k] for k in REF_FIELDS}
    return sources.GlossSelection(chosen["span"], "dmklinger_uk_en", ref, candidates=(chosen,))
