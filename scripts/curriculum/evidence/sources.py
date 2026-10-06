"""The word store's sole boundary to dictionaries and morphology tools.

Use one Sources instance per build (and close it). Results preserve source
bytes; normalization applies only to lookup inputs. Database wrappers share one
read-only connection that pins a single SQLite snapshot for the whole session
(a deferred read transaction; in WAL mode a concurrent writer keeps committing
and the session keeps seeing the rows it started with). The identity of a
sources.db read is the digest of the rows returned, never a digest of the file:
that is what an evidence lock cites and what verification recomputes (rows-v2).
VESUM is a static file and keeps its metadata/file identity.
"""

import hashlib
import json
import os
import re
import shutil
import sqlite3
import time
import unicodedata
import urllib.error
import urllib.request
from collections.abc import Callable, Iterable, Mapping
from contextlib import closing, suppress
from dataclasses import dataclass, field
from datetime import UTC, datetime
from email.utils import parsedate_to_datetime
from functools import lru_cache
from pathlib import Path
from typing import Any

from scripts.lexicon.runner.ulif_dictua_parse import lookup_ulif_label
from scripts.lib.readonly_sqlite import SQLiteConnection
from scripts.lib.readonly_sqlite import open_readonly as _open_readonly
from scripts.rag.config import VESUM_DB_PATH
from scripts.rag.word_identity import APOSTROPHES, normalize_evidence_form
from scripts.verification import stress, vesum
from scripts.wiki.sources_db import normalize_ulif_dictua_query, using_connection
from scripts.wiki.sum20_official import live_article_predicate_for

from . import codes, config, db_identity, tags

BATCH_SIZE = 500
SOURCES_DB_SCHEME = "rows-v2"
SOURCES_DB_META_SCHEME = db_identity.SOURCES_DB_META_SCHEME
LEGACY_SOURCES_DB_SCHEME = "file-v1"
REPO_ROOT = Path(__file__).resolve().parents[3]
journal_mode_from_header = db_identity.journal_mode_from_header
# VESUM uses noun/adj for pronouns; dmklinger uses pronoun (and particle for
# determiners). Preserve the requested VESUM POS as the result key.
GLOSS_POS = {
    "noun": ("noun", "pronoun"),
    "verb": ("verb",),
    "adj": ("adjective", "adj", "pronoun", "particle"),
    "adv": ("adverb",),
    "numr": ("numeral",),
    "part": ("particle",),
    "prep": ("preposition", "particle"),
    "conj": ("conjunction", "particle"),
    "intj": ("interjection",),
}
KAIKKI_ATTRIBUTION = "Wiktionary via Kaikki.org, CC BY-SA 3.0"
KAIKKI_POS = {
    "pron": "PRON",
    "det": "DET",
    "prep": "ADP",
    "conj": "CCONJ",
    "particle": "PART",
    "adv": "ADV",
    "adj": "ADJ",
    "noun": "NOUN",
    "verb": "VERB",
    "num": "NUM",
}
STORE_POS = {
    "noun": {"NOUN"},
    "verb": {"VERB"},
    "adj": {"ADJ"},
    "adv": {"ADV"},
    "numr": {"NUM"},
    "part": {"PART"},
    "prep": {"ADP"},
    "conj": {"CCONJ", "SCONJ"},
}
ALPHABET_GUARD_POS = {"prep", "conj", "part"}

# Requirement-receipt locators. Numeric dictionary ids name source rows, not
# headword guesses. Canonical VESUM locators are exact N-M source_location
# keys. Legacy bare N may name an entry_id or forms_all.id (both occur in
# rev 6.5 receipts); neither namespace grants admission without word binding.
RECEIPT_EVIDENCE_STORES = {
    "vesum": ("forms_all", "source_location (canonical); entry_id / id (legacy)"),
    "pravopys": ("2019.pravopys.net/sections/<number>/", "section"),
    "textbook": ("textbooks", "chunk_id"),
    "grinchenko": ("grinchenko", "id"),
    "sum20": ("sum20_articles", "wordid"),
    "vts": ("slovnyk_me_entries", "id (dictionary_slug=vts)"),
    "ulif": ("ulif_dictua_entries", "id"),
}


def _normalize_text_evidence(text: str) -> str:
    """Remove soft typesetting breaks, preserving spaces without a newline."""
    return re.sub(r"\u00ad(?:[ \t]*\r?\n[ \t]*)?", "", normalize_evidence_form(text)).replace("\u2011", "-")


def _contains_evidence_form(text: str, form: str) -> bool:
    """Match a whole word or exact phrase independent of typesetting breaks.

    Witnesses need at least two letters, including paradigm variants; standalone
    one-letter options cannot bind text kinds. Longer function words can bind by
    occurrence: this establishes identity, never their contextual correctness.
    Strip soft hyphens, fold non-breaking hyphens, and try line-end hyphens
    both joined and kept. Collapse whitespace in the witness and option so
    phrase identity preserves adjacent words rather than PDF line wrapping.
    """
    text = _normalize_text_evidence(text)
    line_end_hyphen = r"(?<=[^\W\d_])-[ \t]*\r?\n[ \t]*(?=[^\W\d_])"
    texts = [re.sub(line_end_hyphen, replacement, text) for replacement in ("", "-")]
    form = _normalize_text_evidence(form)
    form = re.sub(r"\s+", " ", form)
    return bool(
        sum(char.isalpha() for char in form) >= 2
        and any(
            re.search(r"(?<![\w'-])" + re.escape(form) + r"(?![\w'-])", re.sub(r"\s+", " ", candidate))
            for candidate in texts
        )
    )


def is_alphabet_letter_gloss(row: dict) -> bool:
    """Reject source rows mislabeled as a particle or pronoun but defining a letter."""
    raw = row.get("translations") or "[]"
    try:
        translations = json.loads(raw) if isinstance(raw, str) else raw
    except (TypeError, ValueError):
        translations = [raw]
    first = str(translations[0]) if isinstance(translations, list) and translations else ""
    return bool(re.search(r"\bletter\b.*\balphabet\b|\balphabet\b.*\bletter\b", first, re.IGNORECASE))


def has_incompatible_function_label(row: dict, pos: str) -> bool:
    """Reject a source gloss that explicitly labels a different function POS."""
    if pos not in {"prep", "conj", "part"}:
        return False
    raw = row.get("translations") or "[]"
    try:
        translations = json.loads(raw) if isinstance(raw, str) else raw
    except (TypeError, ValueError):
        translations = [raw]
    first = str(translations[0]) if isinstance(translations, list) and translations else ""
    label = re.search(r"\((preposition|conjunction|particle)\)\s*$", first, re.IGNORECASE)
    return bool(
        label and label.group(1).lower() != {"prep": "preposition", "conj": "conjunction", "part": "particle"}[pos]
    )


@dataclass(frozen=True)
class SourceResult[T]:
    raw: T
    content_hash: str
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class ParadigmResult(SourceResult[dict]):
    forms_by_entry: dict[int, list[dict]] = field(default_factory=dict)


def normalize_spelling(word: str) -> str:
    return word.translate(APOSTROPHES)


def standard_file_lines(content: str) -> list[str]:
    """The Standard's lines as ``grep -n`` and editors number them: split at LF only, 1-based by index + 1.

    ``str.splitlines`` also splits at form feeds (and CR, VT, U+2028 and other separators); the
    Standard holds 139 page-break form feeds, so its line N was not the line N an arc, an editor or
    ``grep -n`` cites (#9487: the Standard's 4.1.1 is at 571, ``splitlines`` put it at 585). Form
    feeds and CRs stay inside the line text; only the LF terminators are dropped.
    """
    lines = content.split("\n")
    if lines and lines[-1] == "":
        lines.pop()
    return lines


def read_standard_lines(path: Path) -> list[str]:
    """The Standard file's LF lines, decoded without newline translation (a CR stays text, as in ``grep``)."""
    return standard_file_lines(path.read_bytes().decode("utf-8"))


def _file_hash(path: Path) -> str:
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def _signature(path: Path) -> tuple[int, int, int, int] | None:
    if not path.exists():
        return None
    stat = path.stat()
    return stat.st_ino, stat.st_size, stat.st_mtime_ns, stat.st_ctime_ns


def _sources_path() -> Path:
    path = REPO_ROOT / "data/sources.db"
    if path.is_file():
        return path
    from scripts.guardrails.worktree_containment import resolve_main_root

    return resolve_main_root(REPO_ROOT) / "data/sources.db"


def _kaikki_path() -> Path:
    if override := os.environ.get("LEXICON_KAIKKI_SIDE_DB"):
        return Path(override)
    path = REPO_ROOT / "data/lexicon/side/kaikki.sqlite"
    if path.is_file():
        return path
    from scripts.guardrails.worktree_containment import resolve_main_root

    return resolve_main_root(REPO_ROOT) / "data/lexicon/side/kaikki.sqlite"


def _well_formed_kaikki_gloss(gloss: str) -> bool:
    """Refuse source fragments and usage notes before copying an English gloss."""
    if gloss.lstrip().startswith((")", "]", "”", ",", ";", ".")):
        return False
    brackets: list[str] = []
    curly_open = False
    straight_quotes = 0
    for char in gloss:
        if "CYRILLIC" in unicodedata.name(char, ""):
            return False
        if char in "([":
            brackets.append(char)
        elif char in ")]":
            if not brackets or brackets.pop() != {")": "(", "]": "["}[char]:
                return False
        elif char == "“":
            if curly_open:
                return False
            curly_open = True
        elif char == "”":
            if not curly_open:
                return False
            curly_open = False
        elif char == '"':
            straight_quotes += 1
    return not brackets and not curly_open and straight_quotes % 2 == 0


def aligned_kaikki_senses(payload: dict | None, pos: str, pronoun_entry: bool) -> tuple[list[str], str | None]:
    """Only a single source POS can align with a VESUM store record."""
    if payload is None:
        return [], "kaikki_absent"
    source_pos = payload.get("pos")
    if not isinstance(source_pos, list) or len(source_pos) != 1:
        return [], "kaikki_multi_pos"
    expected = STORE_POS.get(pos, set()).copy()
    if pos == "noun" and pronoun_entry:
        expected = {"PRON"}
    elif pos == "adj" and pronoun_entry:
        expected = {"PRON", "DET"}
    if KAIKKI_POS.get(source_pos[0]) not in expected:
        return [], "kaikki_pos_mismatch"
    glosses = payload.get("glosses")
    if not isinstance(glosses, list) or not glosses or not all(isinstance(g, str) and g for g in glosses):
        return [], "kaikki_no_gloss"
    if not all(_well_formed_kaikki_gloss(gloss) for gloss in glosses):
        return [], "kaikki_malformed"
    return glosses, None


def aligned_kaikki_gloss(payload: dict | None, pos: str, pronoun_entry: bool) -> tuple[str | None, str | None]:
    """Compatibility accessor: never return a joined sense dump."""
    result = select_gloss({"lemma": "", "pos": pos}, [], payload, pronoun_entry=pronoun_entry)
    return result.gloss, result.reason


def unstressed_headword(text: str) -> str:
    """An exact spelling index key; remove stress, preserving all other letters."""
    nfd = unicodedata.normalize("NFD", normalize_spelling(text))
    return unicodedata.normalize("NFC", nfd.replace("\u0301", "").replace("\u0300", ""))


def is_learner_gloss(gloss: Any) -> bool:
    """The shared D2 bound, applied to source spans and stored learner values."""
    return bool(
        isinstance(gloss, str)
        and gloss.strip()
        and ";" not in gloss
        and len(gloss) <= 60
        and len(gloss.split()) <= 8
        and _well_formed_kaikki_gloss(gloss)
    )


@dataclass(frozen=True)
class GlossSelection:
    gloss: str | None = None
    source: str | None = None
    ref: dict | None = None
    reason: str | None = None
    candidates: tuple[dict, ...] = ()
    by_reference: bool = False
    basis: dict | None = None


# Anna Ohoiko's A1 dictionary, when it supplies the English itself.
REFERENCE_SOURCE = "ohoiko_reference"
# A request's ``meaning`` (the lesson's sense) that no open-dictionary candidate spells.
MEANING_SOURCE = "request_meaning"


# Shared closed patterns and canonical names for both selectors.
REGISTER_LABELS = {
    r"figurativ\w*": "figurative",
    r"colloq\w*": "colloquial",
    r"dialect\w*": "dialectal",
    r"obsolet\w*": "obsolete",
    r"obsolesc\w*": "obsolescent",
    r"archai\w*": "archaic",
    r"rare(?:ly)?": "rare",
    r"historic(?:al(?:ly)?)?": "historical",
    r"non[- ]?standard": "nonstandard",
    r"poetic(?:al)?": "poetic",
    r"ironic(?:ally)?": "ironic",
    **{
        label: label
        for label in (
            "dated",
            "informal",
            "slang",
            "vulgar",
            "technical",
            "formal",
            "literary",
            "derogatory",
            "pejorative",
            "offensive",
            "euphemistic",
            "humorous",
            "regional",
            "familiar",
            "childish",
            "endearing",
            "endearment",
            "proscribed",
            "uncommon",
            "rude",
            "taboo",
            "jocular",
            "polite",
            "psychology",
            "chemistry",
            "anatomy",
            "linguistics",
        )
    },
}
_REGISTER_LABEL = re.compile(r"\b(?:" + "|".join(REGISTER_LABELS) + r")\b", re.I)
_GRAMMATICAL_LABEL = re.compile(
    r"(?:preposition|prepositional phrase|conjunction|particle|interjection|determiner|"
    r"(?:interrogative|relative|personal|possessive) pronoun|noun|verb|adjective|adverb|"
    r"(?:in)?transitive|\+\s*(?:nominative|genitive|dative|accusative|instrumental|locative|vocative)"
    r"(?:\s+or(?:\s+more rarely)?\s+(?:nominative|genitive|dative|accusative|instrumental|locative|vocative))*)",
    re.I,
)


def _outer_notes(sense: str) -> list[str]:
    """Read whole outer bracket notes, without promoting nested annotations."""
    notes, depth, start = [], 0, 0
    for index, char in enumerate(sense):
        if char in "([":
            if depth == 0:
                start = index + 1
            depth += 1
        elif char in ")]":
            depth -= 1
            if depth == 0:
                notes.append(sense[start:index].strip())
    return notes


def _register_note(note: str) -> bool:
    """Only complete register labels, optionally mixed with grammar, restrict."""
    labels = re.split(r"\s*[,;]\s*", note)
    register = [bool(_REGISTER_LABEL.fullmatch(label.rstrip("."))) for label in labels]
    return any(register) and all(
        marked or _GRAMMATICAL_LABEL.fullmatch(label) for label, marked in zip(labels, register, strict=True)
    )


def _gloss_head(span: str, *, keep_qualifiers: bool = False) -> str:
    """Remove balanced edge labels; optionally retain meaning-bearing qualifiers."""
    span = span.strip().rstrip("?!").rstrip()
    while span.startswith(("(", "[")):
        depth = 0
        for index, char in enumerate(span):
            if char in "([":
                depth += 1
            elif char in ")]":
                depth -= 1
            if depth == 0:
                span = span[index + 1 :].strip()
                break
        else:
            return span
    while span.endswith((")", "]")):
        depth = 0
        for index in range(len(span) - 1, -1, -1):
            char = span[index]
            if char in ")]":
                depth += 1
            elif char in "([":
                depth -= 1
            if depth == 0:
                # Numeric scale changes the quantity, not just its annotation.
                annotation = span[index + 1 : -1].strip()
                if span[index:].casefold() in {"(short scale)", "(long scale)"} or (
                    keep_qualifiers and not _GRAMMATICAL_LABEL.fullmatch(annotation) and not _register_note(annotation)
                ):
                    return span
                span = span[:index].strip().rstrip("?!").rstrip()
                break
        else:
            return span
    return span


def _sub_senses(sense: str) -> list[str]:
    """Split semicolons outside balanced notes, preserving source order."""
    if not _well_formed_kaikki_gloss(sense):
        return []
    parts, start, depth = [], 0, 0
    for index, char in enumerate(sense):
        if char in "([":
            depth += 1
        elif char in ")]":
            depth -= 1
        elif char == ";" and depth == 0:
            parts.append(sense[start:index].strip())
            start = index + 1
    parts.append(sense[start:].strip())
    return parts


def _sense_spans(sense: str) -> list[str]:
    """Split sub-senses and short alternatives; keep definition commas."""
    parts = _sub_senses(sense)
    if len(parts) != 1:
        return [span for part in parts for span in _sense_spans(part)]
    head = _gloss_head(sense)
    if re.match(
        r"(?:verbal noun of|alternative form|alternative spelling|a |an |the |augmentative particle|expressing )",
        head,
        re.I,
    ):
        return []
    spans, start, depth = [], 0, 0
    for index, char in enumerate(sense):
        if char in "([":
            depth += 1
        elif char in ")]":
            depth -= 1
        elif char == "," and depth == 0:
            spans.append(sense[start:index].strip())
            start = index + 1
    spans.append(sense[start:].strip())
    definition = re.search(r"\b(?:used to|which|whose|covering|extending|typically|often|etc|et cetera)\b", head, re.I)
    if definition or not all(is_learner_gloss(_gloss_head(span)) for span in spans):
        spans = [sense.strip()]
    return [
        span
        for span in spans
        if span
        and not re.match(
            r"(?:verbal noun of|alternative form|alternative spelling|a |an |the |augmentative particle|expressing )",
            _gloss_head(span),
            re.I,
        )
    ]


def _gloss_homonyms(word: dict, entries: Iterable[dict], pronoun_entry: bool) -> list[dict]:
    """Match spelling and coarse POS only; gender never binds a learner sense."""
    matched = []
    extra_labels = {
        "займенник": {"noun", "adj"} if pronoun_entry else set(),
        "сполучник": {"conj"},
        "частка": {"part"},
        "вигук": {"intj"},
        "прийменник": {"prep"},
        "числівник": {"numr"},
        "множинний іменник": {"noun"},
    }
    for entry in entries:
        if unstressed_headword(entry.get("canonical_headword", "")) != unstressed_headword(word["lemma"]):
            continue
        label = entry.get("grammatical_label", "").split(",", 1)[0].strip()
        grammar = lookup_ulif_label(label)
        positions = set(grammar.tags) if grammar else extra_labels.get(label, {label})
        # Mixed-gender ULIF noun labels still establish noun POS. The gender
        # itself must never select one homonym over another.
        if label.startswith("іменник "):
            positions.add("noun")
        if word["pos"] in positions:
            matched.append(entry)
    return matched


def _same_head(left: str, right: str) -> bool:
    """Duplicate or singular/plural variants of one head are not two meanings."""
    left, right = left.casefold(), right.casefold()
    if left == right:
        return True
    short, long_ = sorted((left, right), key=len)
    return long_ in {short + "s", short + "es"} or (short.endswith("y") and long_ == short[:-1] + "ies")


def _note_lead(note: Any) -> str:
    """A request note names its meaning before the first colon ("Write and copy: ...")."""
    return note.split(":", 1)[0] if isinstance(note, str) and ":" in note else ""


def _pinned_rows(word: dict, rows: list[dict]) -> list[dict]:
    """Rows spelled as the pinned ULIF key, else as the pinned VESUM entry's stressed lemma."""
    ulif = word.get("ulif")
    key = ulif.get("key", []) if isinstance(ulif, dict) else []
    spellings = {normalize_spelling(key[0])} if key else set()
    if not spellings:
        spellings = {
            normalize_spelling(form["stressed"])
            for form in word.get("forms", [])
            if form.get("stressed") and unstressed_headword(form.get("form", "")) == unstressed_headword(word["lemma"])
        }
    return [row for row in rows if normalize_spelling(row["word"]) in spellings]


def _gloss_pools(word: dict, rows: list[dict], payload: dict | None, pronoun_entry: bool | None) -> dict:
    """Every parsed candidate, in source order, and the pools a selection reads."""
    lemma, pos = word["lemma"], word["pos"]
    if pronoun_entry is None:
        pronoun_entry = any("pron" in form.get("tags", "").split(":") for form in word.get("forms", []))
    rows = filter_pronominal_gloss_rows(rows, lemma, pos, pronoun_entry)
    # A mixed-POS Kaikki entry does not say which gloss belongs to which POS.
    senses, reason = aligned_kaikki_senses(payload, pos, pronoun_entry)

    def sense_candidates(sense: str, source: str, row: dict | None) -> list[dict]:
        if pos in ALPHABET_GUARD_POS and has_incompatible_function_label({"translations": [sense]}, pos):
            return []
        found = []
        for part in _sub_senses(sense):
            restricted = any(_register_note(note) for note in _outer_notes(part))
            for span in _sense_spans(part):
                head = _gloss_head(span)
                if not head or ";" in head:
                    continue
                bare = head.removeprefix("to ") if pos == "verb" else head
                shown = "to " + bare if pos == "verb" else head
                found.append({"span": shown, "head": bare, "restricted": restricted, "source": source, "row": row})
        return found

    def row_candidates(row: dict) -> list[dict]:
        raw = row.get("translations") or []
        try:
            translations = json.loads(raw) if isinstance(raw, str) else raw
        except (ValueError, TypeError):
            translations = [raw]
        if not isinstance(translations, list):
            return []
        return [
            c
            for sense in translations
            if isinstance(sense, str)
            for c in sense_candidates(sense, "dmklinger_uk_en", row)
        ]

    by_row = [(row, row_candidates(row)) for row in rows]
    kaikki = [c for sense in senses for c in sense_candidates(sense, "kaikki_wiktionary", None)]
    every = [c for _, found in by_row for c in found] + kaikki
    pinned = _pinned_rows(word, rows)
    # ULIF decides the homonym only when its pinned entry excludes some rows.
    ordered = pinned if pinned and len(pinned) < len(rows) else rows
    pools = [[c for c in found if is_learner_gloss(c["span"])] for row, found in by_row if row in ordered]
    if ordered is not rows:
        # Kaikki names no homonym, so under a pin it may only give English the
        # pinned row also gives; an excluded homonym's gloss never re-enters.
        kaikki = [c for c in kaikki if any(_same_head(c["head"], p["head"]) for pool in pools for p in pool)]
    pools.append([c for c in kaikki if is_learner_gloss(c["span"])])
    return {
        "rows": rows,
        "senses": senses,
        "reason": reason,
        "every": every,
        "kaikki": kaikki,
        "pools": pools,
        "ulif_pinned": ordered is not rows,
    }


def reference_pool(
    word: dict, rows: list[dict], payload: dict | None, *, pronoun_entry: bool | None = None
) -> tuple[list[dict], bool]:
    """Learner candidates a reference meaning may choose, in source order, and whether ULIF pinned the rows."""
    found = _gloss_pools(word, rows, payload, pronoun_entry)
    return [c for pool in found["pools"] for c in pool], found["ulif_pinned"]


def select_gloss(
    word: dict,
    rows: list[dict],
    payload: dict | None,
    *,
    pronoun_entry: bool | None = None,
    ulif_entries: Iterable[dict] = (),
    reference: Mapping[str, str] | None = None,
) -> GlossSelection:
    """One plain learner meaning: the sense the lesson uses, as a primer would give it.

    The request note and the record's pinned ULIF/VESUM entry decide the sense
    (cached DictUA entries carry homonyms, not definitions); the open bilingual
    dictionaries only supply its English word. A homonym or a second meaning
    never withholds. Choose (a) the request's ``meaning`` (the candidate
    spelled the same, else the meaning itself), otherwise the candidate the
    note's lead clause (before the first colon) names, (b) the row of the pinned ULIF key or VESUM
    stressed lemma, (c) the ``reference`` (Anna Ohoiko's A1 dictionary, as a
    ``sense_bindings`` binding: ``match`` ``dictionary`` names a candidate's
    displayed gloss, ``book`` her own short gloss when no candidate equals
    it), (d) the first row with an unrestricted sense (Kaikki when no
    dmklinger row has one; a mixed-POS Kaikki entry gives none). The gloss
    is the first head of that row's first unrestricted sub-sense. Only when
    Kaikki lists no variant of that head at all, and Kaikki's first
    unrestricted head is another unrestricted head of the same row, that
    shared head is the plain meaning ("generic we" → "we"). Trailing notes
    are not shown; verbs keep a leading ``to``. Withhold only when no source
    row or reference exists or no head is a learner gloss; a reference that
    no longer applies is ``reference_binding_invalid``. ``ulif_entries`` is
    accepted for callers; ULIF binds through ``word["ulif"]["key"]``.
    """
    found = _gloss_pools(word, rows, payload, pronoun_entry)
    rows, every, kaikki, pools = found["rows"], found["every"], found["kaikki"], found["pools"]
    diagnostic = tuple(
        {"gloss": c["span"], "source": c["source"], "id": c["row"]["id"] if c["row"] else None} for c in every
    )

    def book_gloss() -> GlossSelection:
        """Her own gloss stands only where no open-dictionary candidate equals it and ULIF pinned no row."""
        if reference["match"] != "book" or found["ulif_pinned"] or not is_learner_gloss(reference["gloss"]):
            return GlossSelection(reason="reference_binding_invalid", candidates=diagnostic)
        return GlossSelection(reference["gloss"], REFERENCE_SOURCE, candidates=diagnostic, by_reference=True)

    learner = [c for c in every if is_learner_gloss(c["span"])]
    meaning = word.get("meaning")
    if meaning is not None:
        # The request's meaning is the lesson's sense; a dictionary candidate spelled the same is cited.
        named = [c for c in learner if c["span"].casefold() == meaning.casefold()]
        if not named:
            if not is_learner_gloss(meaning):
                return GlossSelection(reason=codes.GLOSS_NOT_LEARNER_SENSE, candidates=diagnostic)
            return GlossSelection(meaning, MEANING_SOURCE, candidates=diagnostic)
    elif not rows and not found["senses"]:
        if reference is not None:
            return book_gloss()
        return GlossSelection(reason=found["reason"] or codes.GLOSS_MISSING, candidates=diagnostic)
    else:
        lead = _note_lead(word.get("note"))
        named = [c for c in learner if lead and re.search(r"(?<!\w)" + re.escape(c["head"]) + r"(?!\w)", lead, re.I)]
    chosen = named[0] if named else None
    by_reference = False
    if chosen is None and reference is not None:
        chosen = next((c for pool in pools for c in pool if c["span"] == reference["gloss"]), None)
        if chosen is None:
            return book_gloss()
        by_reference = True
    if chosen is None:
        # A row with only dialectal or archaic senses has no plain meaning to give.
        pool = next((p for p in pools if any(not c["restricted"] for c in p)), next((p for p in pools if p), []))
        plain = [c for c in pool if not c["restricted"]] or pool
        chosen = plain[0] if plain else None
        agreed = next((c for c in kaikki if not c["restricted"] and is_learner_gloss(c["span"])), None)
        attested = chosen is None or any(_same_head(chosen["head"], c["head"]) for c in kaikki)
        if agreed and not attested and chosen["source"] != agreed["source"]:
            chosen = next((c for c in plain if _same_head(c["head"], agreed["head"])), chosen)
    if chosen is None:
        return GlossSelection(reason=codes.GLOSS_MISSING, candidates=diagnostic)
    row = chosen["row"]
    ref = {"table": "dmklinger_uk_en", "id": row["id"], "row_sha256": row_digest(row)} if row else None
    return GlossSelection(chosen["span"], chosen["source"], ref, candidates=diagnostic, by_reference=by_reference)


def filter_pronominal_gloss_rows(rows: list[dict], lemma: str, pos: str, pronoun_entry: bool) -> list[dict]:
    """Keep the existing VESUM pronoun and determiner sense preference."""
    if pos not in {"noun", "adj"}:
        return rows
    if pronoun_entry:
        allowed = {"pronoun"} if pos == "noun" else {"pronoun", "particle"}
    else:
        allowed = {"noun"} if pos == "noun" else {"adjective", "adj"}
    selected = [row for row in rows if row["pos"] in allowed]
    if pronoun_entry:
        selected = [row for row in selected if not is_alphabet_letter_gloss(row)]
    if pronoun_entry and pos == "adj":
        # Preserve the existing grammatical alignment: attributive determiners
        # vs independent pronouns. This cannot choose among lexical meanings
        # within that POS class; select_gloss still refuses those ambiguities.
        preferred = "pronoun" if lemma == "свій" else "particle"
        preferred_rows = [row for row in selected if row["pos"] == preferred]
        if preferred_rows:
            selected = preferred_rows
    return selected


def _canonical(value: Any) -> bytes:
    # ensure_ascii=False keeps Ukrainian bytes readable; bytes values raise (no cited table has a BLOB).
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def row_digest(row: Mapping[str, Any]) -> str:
    """Identity of one source row exactly as the accessor returned it (no column excluded)."""
    if not isinstance(row, Mapping):
        raise TypeError(f"row_digest expects a row mapping, got {type(row).__name__}")
    return hashlib.sha256(_canonical(dict(row))).hexdigest()


def batch_digest(batch: Mapping[Any, Any]) -> str:
    """Identity of a keyed batch read: canonical sorted list of [key-as-list, value] pairs."""
    pairs = []
    for key, value in batch.items():
        key_list = [*key] if isinstance(key, tuple) else [key]
        pairs.append([key_list, value])
    pairs.sort(key=lambda pair: pair[0])
    return hashlib.sha256(_canonical(pairs)).hexdigest()


def aggregate_digest(cited: Iterable[tuple[str, str]]) -> str:
    """built_with.sources_db under rows-v2: sorted unique [locator, row_sha256] pairs; no rows → sha256("[]")."""
    pairs = sorted({(str(locator), str(digest)) for locator, digest in cited})
    return hashlib.sha256(_canonical([list(pair) for pair in pairs])).hexdigest()


def open_readonly(path: Path) -> SQLiteConnection:
    conn = _open_readonly(Path(path).resolve())
    conn.row_factory = sqlite3.Row
    return conn


def open_snapshot(path: Path) -> SQLiteConnection:
    """Read-only connection pinned to one snapshot for its lifetime.

    isolation_level=None keeps Python's sqlite3 module from issuing its own
    BEGIN/COMMIT; the explicit deferred BEGIN plus the probe read is what fixes
    the read mark (a bare BEGIN pins nothing until the first read).
    """
    conn = _open_readonly(Path(path).resolve(), isolation_level=None)
    try:
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA busy_timeout=30000")
        conn.execute("BEGIN")
        conn.execute("SELECT 1 FROM sqlite_master LIMIT 1").fetchone()
    except BaseException:
        conn.close()
        raise
    return conn


class Sources:
    """Build-scoped source access. Caller owns batching progress and final reports."""

    def __init__(
        self,
        *,
        sources_db: Path | None = None,
        kaikki_db: Path | None = None,
        vesum_db: Path | None = None,
        standard_path: Path | None = None,
        report: Callable[[str], None] | None = None,
        wal_ceiling_bytes: int | None = None,
        free_disk_floor_bytes: int | None = None,
    ):
        self.sources_db = Path(sources_db) if sources_db is not None else _sources_path()
        self.kaikki_db = Path(kaikki_db) if kaikki_db is not None else _kaikki_path()
        self._kaikki_conn: SQLiteConnection | None = None
        self._kaikki_content_sha256: str | None = None
        self.vesum_db = Path(vesum_db) if vesum_db is not None else VESUM_DB_PATH
        self.standard_path = (
            Path(standard_path)
            if standard_path is not None
            else REPO_ROOT / "docs/l2-uk-en/UKRAINIAN-STATE-STANDARD-2024.txt"
        )
        self.mapper = tags.TagMapper(report=report)
        self.report = report
        self.wal_ceiling_bytes = int(wal_ceiling_bytes) if wal_ceiling_bytes is not None else config.wal_ceiling_bytes()
        self.free_disk_floor_bytes = (
            int(free_disk_floor_bytes) if free_disk_floor_bytes is not None else config.free_disk_floor_bytes()
        )
        self._conn: SQLiteConnection | None = None
        self._fingerprints: dict[Path, tuple[tuple, str, dict]] = {}
        self._vesum_snapshot: tuple[tuple, str, dict] | None = None
        self.journal_mode: str | None = None
        self._snapshot_started: float | None = None
        self._wal_bytes_start: int | None = None
        self._receipt_evidence: dict[str, list[dict]] = {}
        self._receipt_identities: dict[str, Any] = {}
        self._receipt_words: dict[str, list[dict]] = {}
        self._receipt_paradigms: dict[str, list[dict]] = {}
        self._gloss_index: dict[str, list[dict]] | None = None

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        self.close()

    def close(self) -> None:
        """Release the pinned snapshot (rollback, never commit) and report its lifetime."""
        self._receipt_evidence.clear()
        self._receipt_identities.clear()
        self._receipt_words.clear()
        self._receipt_paradigms.clear()
        self._gloss_index = None
        if self._kaikki_conn is not None:
            side, self._kaikki_conn = self._kaikki_conn, None
            with closing(side), suppress(sqlite3.Error):
                side.execute("ROLLBACK")
        if self._conn is None:
            return
        conn, self._conn = self._conn, None
        try:
            with closing(conn), suppress(sqlite3.Error):
                conn.execute("ROLLBACK")
        finally:
            age = self.snapshot_age()
            self._progress_line(
                f"snapshot: released after {age:.1f}s; journal_mode: {self.journal_mode}; "
                f"wal_bytes: {self._wal_bytes_start} -> {self.wal_bytes()}"
            )
            self._snapshot_started = None

    # -- snapshot observability -------------------------------------------------

    def snapshot_age(self) -> float:
        """Seconds since the sources.db snapshot was pinned; 0.0 when none is open."""
        if self._snapshot_started is None:
            return 0.0
        return time.monotonic() - self._snapshot_started

    def wal_bytes(self) -> int:
        """Current size of the sources.db WAL sidecar (0 when absent)."""
        wal = Path(f"{self.sources_db}-wal")
        try:
            return wal.stat().st_size
        except OSError:
            return 0

    def free_disk_bytes(self) -> int:
        """Free bytes on the volume holding sources.db."""
        return shutil.disk_usage(self.sources_db.parent if self.sources_db.parent.exists() else Path.cwd()).free

    def snapshot_report(self) -> dict[str, Any]:
        return {
            "journal_mode": self.journal_mode,
            "wal_bytes": self.wal_bytes(),
            "wal_bytes_start": self._wal_bytes_start,
            "snapshot_seconds": round(self.snapshot_age(), 3),
            "free_disk_bytes": self.free_disk_bytes(),
        }

    def _guard(self) -> None:
        """Stop before the next read when the pinned snapshot exceeds its WAL or free-disk budget."""
        wal = self.wal_bytes()
        free = self.free_disk_bytes()
        reason = None
        if wal > self.wal_ceiling_bytes:
            reason = f"WAL {wal} bytes exceeds ceiling {self.wal_ceiling_bytes} bytes"
        elif free < self.free_disk_floor_bytes:
            reason = f"free disk {free} bytes below floor {self.free_disk_floor_bytes} bytes"
        if reason is None:
            return
        age = self.snapshot_age()
        self.close()
        raise RuntimeError(f"{codes.SNAPSHOT_LIMIT}: {reason}; snapshot released after {age:.1f}s")

    def _file_fingerprint(self, path: Path) -> tuple[str, dict]:
        wal = Path(f"{path}-wal")
        signature = (_signature(path), _signature(wal))
        if signature[0] is None:
            raise FileNotFoundError(f"{codes.SOURCE_UNAVAILABLE}: {str(path)!r}")
        if path in self._fingerprints:
            before, digest, metadata = self._fingerprints[path]
            if before != signature:
                raise ValueError(f"{codes.SOURCE_CHANGED}: {str(path)!r} during source session")
            return digest, metadata
        db_digest = _file_hash(path)
        metadata = {"db_sha256": db_digest}
        digest = db_digest
        if signature[1] is not None and signature[1][1]:
            metadata["wal_sha256"] = _file_hash(wal)
            digest = hashlib.sha256(json.dumps(metadata, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
        if signature != (_signature(path), _signature(wal)):
            raise ValueError(f"{codes.SOURCE_CHANGED}: {str(path)!r} while hashing")
        self._fingerprints[path] = (signature, digest, metadata)
        return digest, metadata

    def _sources_db_meta_identity(self) -> tuple[str, dict]:
        """Cheap, honestly labelled identity of the sources.db file: metadata only, never its body.

        The review receipt ledger records this per attempt. It is not a content
        hash: hashing the multi-gigabyte file per process is what raced the
        ULIF walk (#8527). The content evidence of a sources.db read is the
        receipt's full stored result (rows-v2). The digest is the sha256 of the
        canonical metadata JSON so readers expecting a 64-hex string stay valid.
        """
        try:
            return db_identity.sources_db_meta_identity(self.sources_db, self.journal_mode)
        except OSError as exc:
            raise FileNotFoundError(f"{codes.SOURCE_UNAVAILABLE}: {str(self.sources_db)!r}") from exc

    def _db(self) -> SQLiteConnection:
        if self._conn is None:
            if not self.sources_db.is_file():
                raise FileNotFoundError(f"{codes.SOURCE_UNAVAILABLE}: {str(self.sources_db)!r}")
            self._conn = open_snapshot(self.sources_db)
            self._snapshot_started = time.monotonic()
            self.journal_mode = str(self._conn.execute("PRAGMA journal_mode").fetchone()[0]).lower()
            self._wal_bytes_start = self.wal_bytes()
            self._progress_line(
                f"snapshot: pinned; journal_mode: {self.journal_mode}; wal_bytes: {self._wal_bytes_start}; "
                f"free_disk_bytes: {self.free_disk_bytes()}"
            )
        self._guard()
        return self._conn

    def _db_result[T](self, raw: T) -> SourceResult[T]:
        """rows-v2: the identity of a DB read is the digest of the rows it returned."""
        return SourceResult(raw, batch_digest(raw), {"scheme": SOURCES_DB_SCHEME})

    def _vesum_identity(self) -> tuple[str, dict]:
        # Metadata is the canonical content identity, not an incidental DB file hash.
        signature = (_signature(self.vesum_db), _signature(Path(f"{self.vesum_db}-wal")))
        if self._vesum_snapshot is not None:
            before, digest, metadata = self._vesum_snapshot
            if signature != before:
                raise ValueError(f"{codes.SOURCE_CHANGED}: VESUM during source session")
            return digest, dict(metadata)
        with closing(open_readonly(self.vesum_db)) as conn:
            exists = conn.execute("SELECT 1 FROM sqlite_master WHERE name='vesum_build_metadata'").fetchone()
            metadata = dict(conn.execute("SELECT key, value FROM vesum_build_metadata")) if exists else {}
        digest = metadata.get("canonical_jsonl_sha256")
        if not isinstance(digest, str) or len(digest) != 64 or any(ch not in "0123456789abcdef" for ch in digest):
            digest, file_metadata = self._file_fingerprint(self.vesum_db)
            metadata.update(file_metadata)
        if signature != (_signature(self.vesum_db), _signature(Path(f"{self.vesum_db}-wal"))):
            raise ValueError(f"{codes.SOURCE_CHANGED}: VESUM while reading metadata")
        self._vesum_snapshot = (signature, digest, dict(metadata))
        return digest, metadata

    def inspect_lemma_forms(self, lemma: str, pos: str) -> ParadigmResult:
        digest, metadata = self._vesum_identity()
        raw = vesum.inspect_lemma(normalize_spelling(lemma), db_path=self.vesum_db).as_dict()
        if raw["status"] == "unavailable":
            raise ValueError(f"{codes.SOURCE_UNAVAILABLE}: VESUM inspection for {lemma!r}")
        grouped: dict[int, list[dict]] = {}
        for form in raw["forms"]:
            if form["pos"] == pos:
                grouped.setdefault(form["entry_id"], []).append(form)
        if self._vesum_identity()[0] != digest:
            raise ValueError(f"{codes.SOURCE_CHANGED}: VESUM for {lemma!r}")
        return ParadigmResult(raw, digest, metadata, grouped)

    def inspect_many(self, requests: Iterable[tuple[str, str]]) -> dict[tuple[str, str], ParadigmResult]:
        unique = list(dict.fromkeys((normalize_spelling(lemma), pos) for lemma, pos in requests))
        results = {}
        for start in range(0, len(unique), BATCH_SIZE):
            for lemma, pos in unique[start : start + BATCH_SIZE]:
                results[lemma, pos] = self.inspect_lemma_forms(lemma, pos)
            self._progress("paradigms", min(start + BATCH_SIZE, len(unique)), len(unique))
        return results

    def verify_words(self, words: Iterable[str], pos: str | None = None) -> SourceResult[dict]:
        requested = list(dict.fromkeys(map(normalize_spelling, words)))
        digest, metadata = self._vesum_identity()
        raw = {}
        for start in range(0, len(requested), BATCH_SIZE):
            raw.update(vesum.verify_words(requested[start : start + BATCH_SIZE], pos_filter=pos, db_path=self.vesum_db))
            self._progress("words", min(start + BATCH_SIZE, len(requested)), len(requested))
        if self._vesum_identity()[0] != digest:
            raise ValueError(f"{codes.SOURCE_CHANGED}: VESUM batch")
        return SourceResult(raw, digest, metadata)

    def resolve_evidence_ids(self, evidence_ids: Iterable[str]) -> SourceResult[dict[str, list[dict]]]:
        """Resolve receipt locators on this session, preserving source-row identity.

        Unknown keys return empty rows; unavailable stores raise to the receipt
        boundary, which converts them to a named refusal. No fuzzy/headword or
        cross-dictionary fallback. VESUM's static-file identity is checked on
        both sides of a read, as in inspect_many; sources.db uses _db's pinned
        read-only snapshot. Правопис uses the existing accessor once per section
        and retains those bytes for the session, never a second network lookup.
        """
        requested = list(dict.fromkeys(evidence_ids))
        pending = [eid for eid in requested if eid not in self._receipt_evidence]
        if any(eid.startswith("vesum:") for eid in requested):
            digest, metadata = self._vesum_identity()
            self._receipt_identities["vesum"] = {"content_hash": digest, **metadata}
            vesum_ids = [eid for eid in pending if eid.startswith("vesum:")]
            if vesum_ids:
                numbers = {eid[6:]: eid for eid in vesum_ids if re.fullmatch(r"[1-9][0-9]*", eid[6:])}
                locations = {eid[6:]: eid for eid in vesum_ids if re.fullmatch(r"[1-9][0-9]*-[1-9][0-9]*", eid[6:])}
                result = {eid: [] for eid in vesum_ids}
                # Neither entry_id nor source_location is indexed in the real
                # store. Batch them in one scan rather than scanning per option.
                keys = list(numbers)
                ranges = list(locations)
                if keys or ranges:
                    with closing(open_readonly(self.vesum_db)) as conn:
                        for start in range(0, max(len(keys), len(ranges)), BATCH_SIZE):
                            ns, rs = keys[start : start + BATCH_SIZE], ranges[start : start + BATCH_SIZE]
                            nslots, rslots = ",".join("?" for _ in ns), ",".join("?" for _ in rs)
                            rows = conn.execute(
                                f"SELECT * FROM forms_all WHERE id IN ({nslots}) OR entry_id IN ({nslots}) "
                                f"OR source_location IN ({rslots}) ORDER BY id",
                                [*ns, *ns, *rs],
                            )
                            for row in rows:
                                matches = {
                                    numbers.get(str(row["id"])),
                                    numbers.get(str(row["entry_id"])),
                                    locations.get(row["source_location"]),
                                } - {None}
                                # Derived lookup keys are not source evidence.
                                # Preserve cited-row digests across store versions.
                                source_row = {
                                    key: value
                                    for key, value in dict(row).items()
                                    if key not in {"word_form_folded", "lemma_folded"}
                                }
                                for eid in matches:
                                    result[eid].append(source_row)
                self._vesum_identity()
                self._receipt_evidence.update(result)
        for eid in pending:
            kind, _, key = eid.partition(":")
            if kind == "vesum":
                continue
            if kind not in RECEIPT_EVIDENCE_STORES or not key:
                self._receipt_evidence[eid] = []
                continue
            if kind == "pravopys":
                from scripts.rag.source_query import PRAVOPYS_BASE, pravopys_section

                if not re.fullmatch(r"[1-9][0-9]*", key) or len(key) > 2 or not 1 <= int(key) <= 61:
                    self._receipt_evidence[eid] = []
                    continue
                section = pravopys_section(int(key), report_unavailable=True)
                if section and section.get("status") == "unavailable":
                    raise ValueError(f"{codes.SOURCE_UNAVAILABLE}: {eid}")
                self._receipt_evidence[eid] = [section] if section else []
                self._receipt_identities["pravopys"] = {
                    "scheme": "pravopys-live-section-v1",
                    "origin": PRAVOPYS_BASE,
                }
                continue
            if kind != "textbook" and (not re.fullmatch(r"[1-9][0-9]*", key) or len(key) > 19):
                self._receipt_evidence[eid] = []
                continue
            table, column = {
                "textbook": ("textbooks", "chunk_id"),
                "grinchenko": ("grinchenko", "id"),
                "sum20": ("sum20_articles", "wordid"),
                "vts": ("slovnyk_me_entries", "id"),
                "ulif": ("ulif_dictua_entries", "id"),
            }[kind]
            condition = " AND dictionary_slug = 'vts'" if kind == "vts" else ""
            if kind == "sum20":  # a quarantined СУМ-20 row is never evidence (#9609)
                condition = f" AND {live_article_predicate_for(self._db())}"
            rows = self._db().execute(f"SELECT * FROM {table} WHERE {column} = ?{condition} ORDER BY id", (key,))
            self._receipt_evidence[eid] = [dict(row) for row in rows]
            self._receipt_identities["sources_db"] = {"scheme": SOURCES_DB_SCHEME}
        raw = {eid: self._receipt_evidence[eid] for eid in requested}
        identities = {
            kind: value
            for kind, value in self._receipt_identities.items()
            if (kind == "vesum" and any(eid.startswith("vesum:") for eid in requested))
            or (kind == "pravopys" and any(eid.startswith("pravopys:") for eid in requested))
            or (kind == "sources_db" and any(eid.partition(":")[0] not in {"vesum", "pravopys"} for eid in requested))
        }
        return SourceResult(raw, batch_digest(raw), identities)

    def _receipt_vesum_rows(
        self,
        values: Iterable[str],
        *,
        paradigm: bool = False,
    ) -> SourceResult[dict[str, list[dict]]]:
        """Read attested analyses or paradigms using Unicode word identity.

        Prefer build-time indexed folded keys; retain the compatibility view's
        marker exclusions and original four-column shape. Older stores use exact
        given, casefolded, upper, title, capitalised and per-hyphen-part capitalised
        candidates, then normalized filtering. Unreachable spellings in older
        stores fail closed. Cache within the checked static identity.
        """
        requested = list(dict.fromkeys(values))
        digest, metadata = self._vesum_identity()
        cache = self._receipt_paradigms if paradigm else self._receipt_words
        pending = [value for value in requested if value not in cache]
        column = "lemma" if paradigm else "word_form"
        if pending:
            with closing(open_readonly(self.vesum_db)) as conn:
                folded_column = f"{column}_folded"
                has_folded = folded_column in {row[1] for row in conn.execute("PRAGMA table_info(forms_all)")}
                for start in range(0, len(pending), BATCH_SIZE):
                    batch = pending[start : start + BATCH_SIZE]
                    candidates = (
                        batch
                        if has_folded
                        else sorted(
                            {
                                candidate
                                for value in batch
                                for candidate in (
                                    value,
                                    value.casefold(),
                                    value.upper(),
                                    value.title(),
                                    value.capitalize(),
                                    "-".join(part.capitalize() for part in value.split("-")),
                                )
                            }
                        )
                    )
                    slots = ",".join("?" for _ in candidates)
                    condition = (
                        f"{column} IN (SELECT {column} FROM forms_all WHERE {folded_column} IN ({slots}))"
                        if has_folded
                        else f"{column} IN ({slots})"
                    )
                    rows = conn.execute(
                        f"SELECT word_form, lemma, pos, tags FROM forms "
                        f"WHERE {condition} "
                        "ORDER BY word_form, lemma, pos, tags",
                        candidates,
                    )
                    found = {value: [] for value in batch}
                    for row in rows:
                        normalized = normalize_evidence_form(row[column])
                        if normalized in found:
                            found[normalized].append(dict(row))
                    cache.update(found)
        self._vesum_identity()
        return SourceResult({value: cache[value] for value in requested}, digest, metadata)

    def bind_evidence_forms(
        self,
        resolved: SourceResult[dict[str, list[dict]]],
        citations: Iterable[tuple[str, str]],
    ) -> SourceResult[dict[tuple[str, str], bool]]:
        """Bind citations to the option's word, for valid and invalid judgements.

        Dictionary headwords/lemmas or word_form must casefold-equal the option
        or an attested VESUM lemma. Legacy VESUM integers bind through either
        resolved namespace; canonical N-M remains preferred. Text kinds require
        a whole-word occurrence of the option or any attested paradigm form of
        its VESUM lemmas. Stress/apostrophe normalization also applies. No guessed
        lemmas, definition matches, or metadata witnesses. Binding establishes
        word identity, never correctness of the contextual language judgement.
        Only ULIF rows with status='ok' provide witnesses, for both judgements.
        Text soft hyphens are stripped and line-end hyphens tried joined and
        kept before matching. Standalone
        one-letter options and one-letter paradigm witnesses cannot bind text;
        longer function words can bind by occurrence. Multi-word options require
        the exact phrase after whitespace collapse, never independent token matches.
        """
        fields = {
            "vesum": ("word_form", "lemma"),
            "pravopys": ("text",),
            "textbook": ("text",),
            "grinchenko": ("word",),
            "sum20": ("headword", "stressed_headword"),
            "vts": ("word",),
            "ulif": ("canonical_headword",),
        }
        raw = {}
        pending = {}
        for eid, text in dict.fromkeys(citations):
            kind = eid.partition(":")[0]
            is_text = kind in {"pravopys", "textbook"}
            form = _normalize_text_evidence(text) if is_text else normalize_evidence_form(text)
            witnesses = [
                normalize_evidence_form(row[field])
                for row in resolved.raw[eid]
                if kind != "ulif" or row.get("status") == "ok"
                for field in fields.get(kind, ())
                if isinstance(row.get(field), str)
            ]
            supported = any(
                _contains_evidence_form(value, form) if is_text else bool(form and value == form) for value in witnesses
            )
            raw[eid, text] = supported
            if not supported and (
                not is_text or (sum(char.isalpha() for char in form) >= 2 and not any(char.isspace() for char in form))
            ):
                pending[eid, text] = (form, witnesses, is_text)
        analyses = self._receipt_vesum_rows(form for form, _, _ in pending.values()) if pending else None
        text_lemmas = {
            normalize_evidence_form(row["lemma"])
            for form, _, is_text in pending.values()
            if is_text
            for row in analyses.raw[form]
        }
        paradigms = self._receipt_vesum_rows(text_lemmas, paradigm=True) if text_lemmas else None
        for citation, (form, witnesses, is_text) in pending.items():
            lemmas = {normalize_evidence_form(row["lemma"]) for row in analyses.raw[form]}
            if is_text:
                forms = (
                    {normalize_evidence_form(row["word_form"]) for lemma in lemmas for row in paradigms.raw[lemma]}
                    if paradigms is not None
                    else set()
                )
                raw[citation] = any(_contains_evidence_form(value, variant) for value in witnesses for variant in forms)
            else:
                raw[citation] = any(value in lemmas for value in witnesses)
        metadata = {"normalization": "stress-apostrophes-casefold-v2"}
        if analyses is not None:
            metadata["vesum"] = {"content_hash": analyses.content_hash, **analyses.metadata}
            metadata["analyses_sha256"] = batch_digest(analyses.raw)
        if paradigms is not None:
            metadata["paradigms_sha256"] = batch_digest(paradigms.raw)
        return SourceResult(raw, batch_digest(raw), metadata)

    def stress_for_form(self, form: str, vesum_tags: str, *, lemma: str | None = None) -> SourceResult[dict]:
        """Return the oracle envelope unchanged. Builder handles monosyllables first."""
        mapped_tags = self.mapper(vesum_tags)
        selectors = {"tags": mapped_tags}
        if lemma is not None:
            selectors["lemma"] = lemma
        with using_connection(self._db()):
            raw = stress.verify_stress(normalize_spelling(form), **selectors)
        # The trie alone does not identify exact-form override changes.
        override_digest = _file_hash(stress.STRESS_OVERRIDES_PATH) if stress.STRESS_OVERRIDES_PATH.exists() else None
        return SourceResult(raw, raw["source"]["digest"], {"overrides_sha256": override_digest})

    def stress_many(self, requests: Iterable[tuple[str, str]]) -> dict[tuple[str, str], SourceResult[dict]]:
        requested = list(dict.fromkeys((normalize_spelling(form), tag) for form, tag in requests))
        result = {}
        for start in range(0, len(requested), BATCH_SIZE):
            for form, tag in requested[start : start + BATCH_SIZE]:
                result[form, tag] = self.stress_for_form(form, tag)
            self._progress("stress", min(start + BATCH_SIZE, len(requested)), len(requested))
        return result

    def ulif_entries(self, lemmas: Iterable[str]) -> SourceResult[dict[str, list[dict]]]:
        """Raw DictUA groups keyed by caller spelling, looked up by the oracle's key.

        Case folding identifies the cache group only. Stress readings still
        require the oracle's positive lemma and POS join to VESUM; a checked
        common-word group cannot establish a proper-name stress reading.
        """
        conn = self._db()
        requested = list(dict.fromkeys(map(normalize_spelling, lemmas)))
        queries = list(dict.fromkeys(map(normalize_ulif_dictua_query, requested)))
        groups: dict[str, list[dict]] = {query: [] for query in queries}
        result: dict[str, list[dict]] = {lemma: [] for lemma in requested}
        for start in range(0, len(queries), BATCH_SIZE):
            batch = queries[start : start + BATCH_SIZE]
            slots = ",".join("?" for _ in batch)
            rows = conn.execute(
                f"SELECT * FROM ulif_dictua_entries WHERE normalized_query IN ({slots}) ORDER BY normalized_query, homonym_index, id",
                batch,
            ).fetchall()
            entries = {row["id"]: dict(row) for row in rows}
            for row in entries.values():
                row["sections"] = []
                groups[row["normalized_query"]].append(row)
            if entries:
                # Join on requested spellings to stay within SQLite's variable cap.
                sections = conn.execute(
                    f"SELECT s.* FROM ulif_dictua_sections s JOIN ulif_dictua_entries e ON e.id=s.entry_id WHERE e.normalized_query IN ({slots}) ORDER BY s.entry_id, s.kind, s.source_order, s.id",
                    batch,
                )
                for section in sections:
                    entries[section["entry_id"]]["sections"].append(dict(section))
            self._progress("ulif", min(start + BATCH_SIZE, len(queries)), len(queries))
        for lemma in requested:
            result[lemma] = groups[normalize_ulif_dictua_query(lemma)]
        return self._db_result(result)

    @staticmethod
    def ulif_group_checked(entries: list[dict]) -> bool:
        return bool(entries) and all(row.get("homonym_checked") == 1 and row.get("status") == "ok" for row in entries)

    def gloss_rows(self, requests: Iterable[tuple[str, str]]) -> SourceResult[dict[tuple[str, str], list[dict]]]:
        """Stress-free spelling index + explicit POS, retaining original rows.

        The index belongs to this pinned read snapshot; collisions survive for
        select_gloss to bind against the record's ULIF stressed key.
        """
        conn = self._db()
        if self._gloss_index is None:
            self._gloss_index = {}
            for row in conn.execute("SELECT * FROM dmklinger_uk_en ORDER BY id"):
                self._gloss_index.setdefault(unstressed_headword(row["word"]), []).append(dict(row))
        requested = list(dict.fromkeys((normalize_spelling(lemma), pos) for lemma, pos in requests))
        result = {key: [] for key in requested}
        for start in range(0, len(requested), BATCH_SIZE):
            batch = requested[start : start + BATCH_SIZE]
            words = list(dict.fromkeys(lemma for lemma, _ in batch))
            rows = [row for word in words for row in self._gloss_index.get(unstressed_headword(word), [])]
            for key in batch:
                labelled = [
                    row
                    for row in rows
                    if unstressed_headword(row["word"]) == unstressed_headword(key[0])
                    and row["pos"] == {"prep": "preposition", "conj": "conjunction"}.get(key[1])
                ]
                result[key] = [
                    dict(row)
                    for row in rows
                    if unstressed_headword(row["word"]) == unstressed_headword(key[0])
                    and row["pos"] in GLOSS_POS.get(key[1], (key[1],))
                    and not (key[1] in ALPHABET_GUARD_POS and is_alphabet_letter_gloss(dict(row)))
                    and not has_incompatible_function_label(dict(row), key[1])
                    and not (key[1] in {"prep", "conj"} and labelled and row["pos"] == "particle")
                ]
            self._progress("glosses", min(start + BATCH_SIZE, len(requested)), len(requested))
        return self._db_result(result)

    def formula_rows(self, word: dict) -> SourceResult[list[dict]]:
        """Exact formula/declared-alias headwords, with no lexical POS filter."""
        from .formulas import headword, printed_headword

        names = {printed_headword(word["text"]), *(headword(a) for a in word.get("aliases", []))}
        rows = [
            dict(r)
            for r in self._db().execute("SELECT * FROM dmklinger_uk_en ORDER BY id")
            if headword(r["word"]) in names
        ]
        return SourceResult(rows, batch_digest({"formula": rows}), {"scheme": SOURCES_DB_SCHEME})

    def kaikki_rows(self, lemmas: Iterable[str]) -> SourceResult[dict[str, dict | None]]:
        """Read exact lemma keys from the immutable, locally built Kaikki side DB."""
        if self._kaikki_conn is None:
            if not self.kaikki_db.is_file():
                raise FileNotFoundError(f"{codes.SOURCE_UNAVAILABLE}: kaikki side DB missing: {self.kaikki_db}")
            conn = open_snapshot(self.kaikki_db)
            try:
                meta = dict(conn.execute("SELECT key, value FROM meta"))
                digest = meta.get("content_sha256", "")
                if (
                    (meta.get("schema_version"), meta.get("kind")) != ("side-db-v1", "kaikki")
                    or not re.fullmatch(r"[0-9a-f]{64}", digest)
                    or int(meta.get("row_count", "-1")) != conn.execute("SELECT COUNT(*) FROM kaikki").fetchone()[0]
                ):
                    raise ValueError(f"{codes.SOURCE_UNAVAILABLE}: invalid kaikki side DB metadata")
            except BaseException:
                conn.close()
                raise
            self._kaikki_conn = conn
            self._kaikki_content_sha256 = digest
        requested = list(dict.fromkeys(lemmas))
        result: dict[str, dict | None] = {lemma: None for lemma in requested}
        for start in range(0, len(requested), BATCH_SIZE):
            batch = requested[start : start + BATCH_SIZE]
            if not batch:
                continue
            slots = ",".join("?" for _ in batch)
            for row in self._kaikki_conn.execute(
                f"SELECT lemma_key, payload FROM kaikki WHERE lemma_key IN ({slots})", batch
            ):
                result[row["lemma_key"]] = json.loads(row["payload"])
        return SourceResult(result, self._kaikki_content_sha256, {"attribution": KAIKKI_ATTRIBUTION})

    def cefr_levels(self, lemmas: Iterable[str]) -> SourceResult[dict]:
        """Raw PULS hits; consumers must reject the upstream helper's prefix fallback."""
        from scripts.wiki import sources_db

        with sources_db.using_connection(self._db()):
            raw = sources_db.query_cefr_levels(list(dict.fromkeys(map(normalize_spelling, lemmas))))
        return self._db_result(raw)

    def heritage(self, words: Iterable[str]) -> SourceResult[dict]:
        from scripts.wiki import sources_db

        with sources_db.using_connection(self._db()):
            raw = {}
            requested = list(dict.fromkeys(map(normalize_spelling, words)))
            for index, word in enumerate(requested, 1):
                hits = sources_db.search_heritage(word, include_live_slovnyk=False)
                # Each hit is a deterministic projection of the dictionary rows it was
                # read from on this snapshot; its digest is the identity the word record cites.
                for hit in hits:
                    hit["row_sha256"] = heritage_hit_digest(hit)
                raw[word] = hits
                if index % BATCH_SIZE == 0 or index == len(requested):
                    self._progress("heritage", index, len(requested))
        return self._db_result(raw)

    def russian_patterns(self, words: Iterable[str]) -> SourceResult[dict]:
        from scripts.lexicon import calque_corrections
        from scripts.verification import check_ru_morph

        requested = list(dict.fromkeys(map(normalize_spelling, words)))
        verified = self.verify_words(requested)
        raw = check_ru_morph.check_russian_patterns_batch(
            requested, verified_words={word for word, hits in verified.raw.items() if hits}
        )
        # Hash the actual morphology dictionaries and implementation inputs.
        files = [Path(check_ru_morph.__file__), Path(calque_corrections.__file__)]
        for analyzer in (check_ru_morph._morph_ru, check_ru_morph._morph_uk):
            files.extend(sorted(Path(analyzer.dictionary.path).rglob("*")))
        hashes = [_file_hash(path) for path in files if path.is_file()]
        hashes.append(verified.content_hash)
        digest = hashlib.sha256("\n".join(hashes).encode()).hexdigest()
        return SourceResult(raw, digest, {"vesum": verified.content_hash})

    def tag_inventory(self) -> SourceResult[dict]:
        digest, metadata = self._vesum_identity()
        with closing(open_readonly(self.vesum_db)) as conn:
            atoms = sorted(
                {atom for row in conn.execute("SELECT DISTINCT tags FROM forms_all") for atom in row[0].split(":")}
            )
            markers = [row[0] for row in conn.execute("SELECT DISTINCT marker FROM form_markers ORDER BY marker")]
        return SourceResult({"atoms": atoms, "markers": markers}, digest, metadata)

    def search_resources(
        self, query: str, *, mode: str = "text", free_only: bool = True, limit: int = 20
    ) -> list[dict]:
        """Search catalogue suggestions within this read-only sources snapshot."""
        from scripts.ingest.resource_catalogue_ingest import search_resources

        return search_resources(self._db(), query, mode=mode, free_only=free_only, limit=limit)

    def get_textbook_chunk(self, chunk_id: str | int) -> dict | None:
        conn = self._db()
        sql = """
            SELECT t.*, s.page_start AS page
            FROM textbooks t
            LEFT JOIN textbook_sections s ON t.parent_section_id = s.section_id
            WHERE t.chunk_id = ?
        """
        row = conn.execute(sql, (str(chunk_id),)).fetchone()
        if row is None:
            return None
        res = dict(row)
        if res.get("page") is not None:
            res["page"] = int(res["page"])
        return res

    def get_textbook_file_chunks(self, source_file: str) -> list[dict]:
        conn = self._db()
        sql = """
            SELECT t.*, s.page_start AS page, s.section_number
            FROM textbooks t
            LEFT JOIN textbook_sections s ON t.parent_section_id = s.section_id
            WHERE t.source_file = ?
            ORDER BY s.section_number, t.parent_section_id, t.id
        """
        rows = conn.execute(sql, (source_file,)).fetchall()
        result = []
        for r in rows:
            d = dict(r)
            if d.get("page") is not None:
                d["page"] = int(d["page"])
            result.append(d)
        return result

    def get_literary_chunk(self, chunk_id: str | int) -> dict | None:
        conn = self._db()
        row = conn.execute("SELECT * FROM literary_texts WHERE chunk_id = ?", (str(chunk_id),)).fetchone()
        return dict(row) if row is not None else None

    def get_literary_file_chunks(self, source_file: str) -> list[dict]:
        conn = self._db()
        rows = conn.execute("SELECT * FROM literary_texts WHERE source_file = ? ORDER BY id", (source_file,)).fetchall()
        return [dict(r) for r in rows]

    def find_ua_gec_error(self, error: str, correct: str) -> list[dict]:
        conn = self._db()
        rows = conn.execute(
            "SELECT id, error, correct, error_type, doc_id, annotator_id, partition, is_native, source_lang FROM ua_gec_errors WHERE error = ? AND correct = ? ORDER BY id",
            (error, correct),
        ).fetchall()
        return [dict(r) for r in rows]

    def get_ua_gec_error_by_id(self, error_id: int) -> dict | None:
        conn = self._db()
        row = conn.execute("SELECT * FROM ua_gec_errors WHERE id = ?", (int(error_id),)).fetchone()
        return dict(row) if row is not None else None

    def get_style_guide_entry(self, entry_id: int) -> dict | None:
        conn = self._db()
        row = conn.execute("SELECT * FROM style_guide WHERE id = ?", (int(entry_id),)).fetchone()
        return dict(row) if row is not None else None

    def get_standard_file_hash(self) -> str:
        if not self.standard_path.is_file():
            raise FileNotFoundError(f"{codes.SOURCE_UNAVAILABLE}: Standard file not found at {self.standard_path}")
        return _file_hash(self.standard_path)

    def get_standard_lines(self, start_line: int, end_line: int) -> tuple[str, str]:
        if not self.standard_path.is_file():
            raise FileNotFoundError(f"{codes.SOURCE_UNAVAILABLE}: Standard file not found at {self.standard_path}")
        file_hash = _file_hash(self.standard_path)
        lines = read_standard_lines(self.standard_path)
        total_lines = len(lines)
        if start_line < 1 or end_line < start_line or end_line > total_lines:
            raise ValueError(
                f"{codes.INVALID_REQUEST}: line range {start_line}-{end_line} out of bounds (1..{total_lines})"
            )
        selected_lines = lines[start_line - 1 : end_line]
        text = "\n".join(selected_lines)
        return text, file_hash

    def check_url(self, url: str, timeout: float = 10.0) -> dict[str, Any]:
        return check_url(url, timeout=timeout)

    def _progress(self, kind: str, count: int, total: int) -> None:
        self._progress_line(f"{kind}: {count}/{total}")

    def _progress_line(self, line: str) -> None:
        if self.report:
            self.report(line)


def heritage_hit_digest(hit: Mapping[str, Any]) -> str:
    """Identity of one heritage hit as copied into a word record (its own row_sha256 excluded)."""
    return row_digest({key: value for key, value in hit.items() if key != "row_sha256"})


# Same honest identifying form used by LinkChecker (its FAQ). This is a robot,
# not a claim to be a particular browser. RFC 9110 §10.2.3 defines Retry-After.
LINKCHECK_USER_AGENT = (
    "Mozilla/5.0 (compatible; learn-ukrainian-linkcheck/1.0; "
    "+https://github.com/learn-ukrainian/learn-ukrainian.github.io)"
)
URL_CHECK_ATTEMPTS = 3
URL_RETRY_CAP = 5.0


def _url_retry_delay(retry_after: str | None, attempt: int) -> float:
    """Bound backoff and either Retry-After representation to five seconds."""
    delay = 0.5 * 2**attempt
    if retry_after:
        try:
            if retry_after.isascii() and retry_after.isdecimal():
                requested = float(retry_after)
            else:
                requested = (parsedate_to_datetime(retry_after) - datetime.now(UTC)).total_seconds()
            delay = max(delay, requested)
        except (ValueError, TypeError, OverflowError):
            pass
    return min(delay, URL_RETRY_CAP)


def check_url(url: str, timeout: float = 10.0) -> dict[str, Any]:
    """GET with robot identification, redirects and bounded transient retries.

    Return only the existing pack ``checked`` fields. Verification classifies
    final statuses; only 200 passes. Exhausted connection failures raise.
    """
    if timeout is None or timeout <= 0:
        raise ValueError("check_url requires a positive timeout")
    req = urllib.request.Request(url, headers={"User-Agent": LINKCHECK_USER_AGENT})
    for attempt in range(URL_CHECK_ATTEMPTS):
        retry_after = None
        try:
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                result = {
                    "http_status": resp.status,
                    "final_url": resp.geturl(),
                    "content_type": resp.headers.get_content_type() if resp.headers else None,
                    "date": datetime.now(UTC).strftime("%Y-%m-%d"),
                }
                retry_after = resp.headers.get("Retry-After") if resp.headers else None
        except urllib.error.HTTPError as exc:
            try:
                result = {
                    "http_status": exc.code,
                    "final_url": exc.geturl(),
                    "content_type": exc.headers.get_content_type() if exc.headers else None,
                    "date": datetime.now(UTC).strftime("%Y-%m-%d"),
                }
                retry_after = exc.headers.get("Retry-After") if exc.headers else None
            finally:
                exc.close()
        except (urllib.error.URLError, TimeoutError, OSError) as exc:
            if attempt == URL_CHECK_ATTEMPTS - 1:
                raise ConnectionError(f"Failed to check URL {url} after {URL_CHECK_ATTEMPTS} attempts: {exc}") from exc
            time.sleep(_url_retry_delay(None, attempt))
            continue
        if result["http_status"] != 429 and not 500 <= result["http_status"] <= 599:
            return result
        if attempt == URL_CHECK_ATTEMPTS - 1:
            return result
        time.sleep(_url_retry_delay(retry_after, attempt))


@lru_cache(maxsize=1)
def _default() -> Sources:
    return Sources()


def inspect_lemma_forms(lemma: str, pos: str) -> ParadigmResult:
    return _default().inspect_lemma_forms(lemma, pos)


def stress_for_form(form: str, vesum_tags: str) -> SourceResult[dict]:
    return _default().stress_for_form(form, vesum_tags)
