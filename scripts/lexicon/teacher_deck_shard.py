"""Build the teacher-table practice shard and cloze file (#8843 P1).

Inputs are the table entries from ``sync_teacher_table_deck``, public Word
Atlas articles in ``data/atlas.db``, VESUM, the reviewed synonym verdicts, and
sentences from ``data/sources.db`` (the teacher's lesson texts plus textbooks).
Every Ukrainian string in the output comes from one of those sources: items are
selected and assembled by rule, never written or rewritten here.

The artifact contract (schema, card identity, eligibility rules) is documented
in ``docs/practice/teacher-deck-artifacts.md``; P2 builds against it and the
independent checker ``scripts/audit/check_teacher_deck.py`` enforces it without
importing this module.
"""

from __future__ import annotations

import gzip
import hashlib
import json
import random
import re
import sqlite3
from collections.abc import Callable, Iterable, Sequence
from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path
from typing import Any

from scripts.audit.generate_practice_deck import (
    PROJECT_ROOT,
    TEACHER_CLOZE_GZIP_LIMIT,
    TEACHER_DECK_GZIP_LIMIT,
    RealVesumVerifier,
    VesumVerifier,
    _build_classify_items,
    _build_lexeme,
    _build_paradigm_items,
    _match_initial_capitalization,
    _option_pos_bucket,
    _plain,
    _section_items,
    _stress_payload,
    _synonym_option,
    _valid_synonym_distractors,
    build_synonym_verdict_sets,
    read_synonym_verdicts,
)
from scripts.audit.generate_sentence_inventory import (
    LATIN_CHAR_RE,
    LEADING_QUIZ_MARKER_RE,
    SENTENCE_SPLIT_RE,
    TEXTBOOK_LICENSE,
    UK_TOKEN_RE,
    _is_source_sentence_noise,
    _normalise,
    _tokens,
    _vesum_token_variants,
)
from scripts.ingest.private_teacher_lessons_ingest import DATE_START
from scripts.ingest.private_teacher_lessons_ingest import SOURCE_FILE as TEACHER_LESSON_SOURCE
from scripts.lexicon.build_teacher_deck_cloze import contains_private_teacher_name
from scripts.lexicon.sync_teacher_table_deck import DECK_ID, normalize_uk_key
from scripts.practice.extract_textbook_error_corrections import is_intentional_error_context

SCHEMA = "atlas-practice-teacher-deck"
CLOZE_SCHEMA = "atlas-practice-teacher-cloze"
COVERAGE_SCHEMA = "atlas-practice-teacher-coverage"
MANIFEST_SCHEMA = "atlas-practice-teacher-manifest"
SCHEMA_VERSION = 1
LEVEL = "teacher"
DECK_FILE = "practice-deck.teacher.json"
CLOZE_FILE = "practice-cloze.teacher.json"
COVERAGE_FILE = "coverage.json"
FROZEN_KEYS_FILE = "frozen-keys.json"
MANIFEST_FILE = "manifest.json"
PUBLISHED_FILES = (DECK_FILE, CLOZE_FILE)
CARD_KINDS = ("recognition", "production", "cloze", "grammar")
GRAMMAR_MODES = ("stress", "paradigm", "classify", "synonym", "antonym")
BLANK = "___"
MAX_CLOZE_PER_ENTRY = 3
CHOICE_DISTRACTORS = 3
# The teacher deck has no CEFR placement; level-gated classify sets (aspect,
# declension, POS) open at this floor, as for an intermediate learner.
GRAMMAR_LEVEL_FLOOR = "B1"
LEVEL_RANK = {level: index for index, level in enumerate(("A1", "A2", "B1", "B2", "C1", "C2"))}
TEXTBOOK_SEARCH_LIMIT = 250
TEXTBOOK_EXCLUDED_PREFIXES = ("ulp", "private-")
DOCUMENT_CONTEXT_LABEL_UK = "Контекст з документа"  # existing site label (document-importer.ts)
ENGLISH_ARTICLES = frozenset({"a", "an", "the"})
# Function words ignored when matching the teacher's English against an Atlas
# sense gloss (mechanical sense rule (c)); aspect markers are not meanings.
# fmt: off
ENGLISH_STOPWORDS = frozenset(
    {
        "a", "an", "the", "to", "of", "in", "on", "at", "for", "with", "by", "from", "into", "onto", "up",
        "down", "out", "off", "over", "about", "as", "and", "or", "not", "no", "be", "is", "are", "was",
        "were", "been", "being", "do", "does", "did", "have", "has", "had", "get", "it", "its", "one",
        "oneself", "someone", "somebody", "something", "sb", "sth", "smb", "smth", "self", "impf", "perf",
        "pf", "ipf", "imperf", "etc",
    }
)
# fmt: on
IMPF_MARKER_RE = re.compile(r"\((?:impf|imperf|ipf)\.?\)", re.IGNORECASE)
PERF_MARKER_RE = re.compile(r"\((?:perf|pf)\.?\)", re.IGNORECASE)
ASPECT_MARKER_RE = re.compile(r"\s*\((?:impf|imperf|ipf|perf|pf)\.?\)", re.IGNORECASE)
# Verb aspect comes from VESUM (forms_all tags) and checked ULIF entries, never
# from the teacher's markers. ``dual`` = biaspectual (ULIF "недоконаного і доконаного виду").
ULIF_ASPECT_LABELS = {
    "дієслово недоконаного виду": "imperf",
    "дієслово доконаного виду": "perf",
    "дієслово недоконаного і доконаного виду": "dual",
}
ASPECT_LABELS_EN = {"imperf": "impf.", "perf": "pf.", "dual": "impf./pf."}
ASPECT_BASES = ("agree", "vesum-only", "ulif-only", "conflict", "homograph", "none")
CLASSIFY_ASPECT = {"imperf": "imperfective", "perf": "perfective"}
ENGLISH_TOKEN_RE = re.compile(r"[\w'’-]+|/")
CYRILLIC_RE = re.compile(r"[А-ЩЬЮЯЄІЇҐа-щьюяєіїґ]")
SENTENCE_END = (".", "!", "?", "…")
# VESUM tag parts that define a surface form's grammatical slot; distractors are
# inflected into the same slot so the options differ only lexically.
# fmt: off
CORE_TAG_PARTS = frozenset(
    {
        "m", "f", "n", "p", "s", "v_naz", "v_rod", "v_dav", "v_zna", "v_oru", "v_mis", "v_kly", "inf",
        "pres", "futr", "past", "impr", "1", "2", "3", "ranim", "rinanim", "compb", "compc", "comps",
    }
)
# fmt: on


class TeacherDeckBuildError(RuntimeError):
    """The teacher deck cannot be built without violating its contract."""


# --------------------------------------------------------------------------- English rules


def english_parts(english: str) -> list[str]:
    """Normalised meaning parts (spec: split on ';' and ',', lower-case, drop a
    leading 'to ', the articles a/an/the and parenthetical text, collapse spaces)."""

    parts: list[str] = []
    for raw in re.split(r"[;,]", english):
        text = re.sub(r"\([^)]*\)", " ", raw).replace("(", " ").replace(")", " ").casefold()
        text = " ".join(text.split())
        text = re.sub(r"^to\s+", "", text)
        words = [word for word in text.split() if word not in ENGLISH_ARTICLES]
        text = " ".join(words).strip(" .!?:;\"'")
        if text:
            parts.append(text)
    return parts


def _word_seq(part: str) -> tuple[str, ...]:
    return tuple(ENGLISH_TOKEN_RE.findall(part))


def _contains_words(outer: tuple[str, ...], inner: tuple[str, ...]) -> bool:
    if not inner or len(inner) > len(outer):
        return False
    width = len(inner)
    return any(outer[index : index + width] == inner for index in range(len(outer) - width + 1))


def parts_overlap(left: Sequence[str], right: Sequence[str]) -> bool:
    for a in left:
        seq_a = _word_seq(a)
        for b in right:
            seq_b = _word_seq(b)
            if a == b or _contains_words(seq_a, seq_b) or _contains_words(seq_b, seq_a):
                return True
    return False


def aspect_split(left: Sequence[str], right: Sequence[str], left_aspect: str | None, right_aspect: str | None) -> bool:
    """Spec: entries whose normalised English is otherwise identical are told apart
    by a source-derived aspect difference (imperf vs perf) shown in the prompt."""

    return {left_aspect, right_aspect} == {"imperf", "perf"} and set(left) == set(right)


def overlap_graph(
    entries: Sequence[dict[str, Any]], aspects: dict[str, str | None] | None = None
) -> tuple[dict[str, list[str]], dict[str, list[str]]]:
    """Entry id -> sorted ids of entries whose English meaning overlaps, and entry
    id -> sorted aspect partners (same English, imperf vs perf: not an overlap)."""

    aspects = aspects or {}
    parts = {str(entry["entryId"]): english_parts(str(entry["en"])) for entry in entries}
    by_token: dict[str, set[str]] = {}
    for entry_id, entry_parts in parts.items():
        for part in entry_parts:
            for token in set(_word_seq(part)):
                if token != "/":
                    by_token.setdefault(token, set()).add(entry_id)
    graph: dict[str, set[str]] = {entry_id: set() for entry_id in parts}
    partners: dict[str, set[str]] = {entry_id: set() for entry_id in parts}
    for entry_id, entry_parts in parts.items():
        candidates: set[str] = set()
        for part in entry_parts:
            for token in set(_word_seq(part)):
                candidates |= by_token.get(token, set())
        for other in candidates:
            if other == entry_id or other in graph[entry_id] or other in partners[entry_id]:
                continue
            if not parts_overlap(entry_parts, parts[other]):
                continue
            target = (
                partners
                if aspect_split(entry_parts, parts[other], aspects.get(entry_id), aspects.get(other))
                else graph
            )
            target[entry_id].add(other)
            target[other].add(entry_id)
    return (
        {entry_id: sorted(others) for entry_id, others in graph.items()},
        {entry_id: sorted(others) for entry_id, others in partners.items()},
    )


def content_words(text: str) -> set[str]:
    words: set[str] = set()
    for part in english_parts(text):
        words.update(token for token in _word_seq(part) if token != "/" and token not in ENGLISH_STOPWORDS)
    return words


def teacher_aspect(english: str) -> set[str]:
    """The teacher's own aspect markers — reported against the sources, never used as the aspect."""

    aspects: set[str] = set()
    if IMPF_MARKER_RE.search(english):
        aspects.add("imperf")
    if PERF_MARKER_RE.search(english):
        aspects.add("perf")
    return aspects


def teacher_implies_verb(english: str) -> bool:
    raw_parts = [part.strip().casefold() for part in re.split(r"[;,]", english) if part.strip()]
    if teacher_aspect(english):
        return True
    return bool(raw_parts) and all(part.startswith("to ") for part in raw_parts)


def display_english(teacher_en: str, aspect: str | None) -> str:
    """Learner-facing English: the teacher's aspect markers are stripped (a meaning
    that becomes a duplicate is dropped) and the source-derived label appended."""

    text = teacher_en
    if ASPECT_MARKER_RE.search(teacher_en):
        parts: list[str] = []
        for raw in ASPECT_MARKER_RE.sub("", teacher_en).split(";"):
            part = " ".join(raw.split())
            if part and part.casefold() not in {kept.casefold() for kept in parts}:
                parts.append(part)
        text = "; ".join(parts)
    label = ASPECT_LABELS_EN.get(aspect or "")
    return f"{text} ({label})" if label else text


def _entry_class(entry: dict[str, Any], atlas_pos: str | None) -> str:
    """Distractor grouping class: Atlas POS for single words, source-derived verbness otherwise."""

    teacher_class = "verb" if entry.get("aspect") is not None else "other"
    if entry["multiword"]:
        return f"phrase-{teacher_class}"
    bucket = _option_pos_bucket(atlas_pos) if atlas_pos else ""
    return bucket or teacher_class


def _seeded_rng(*parts: str) -> random.Random:
    digest = hashlib.sha256("\x1f".join(parts).encode("utf-8")).hexdigest()
    return random.Random(int(digest[:16], 16))


# --------------------------------------------------------------------------- inputs


def _ro_connect(path: Path) -> sqlite3.Connection:
    if not path.exists():
        raise TeacherDeckBuildError(f"missing input database: {path}")
    conn = sqlite3.connect(f"file:{path.resolve()}?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row
    return conn


def _sha256_lines(values: Iterable[str]) -> str:
    digest = hashlib.sha256()
    for value in values:
        digest.update(value.encode("utf-8"))
        digest.update(b"\n")
    return digest.hexdigest()


def read_atlas_articles(atlas_db: Path) -> tuple[dict[str, list[dict[str, Any]]], dict[str, str]]:
    """Public Atlas articles grouped by normalised lemma, plus manifest metadata."""

    conn = _ro_connect(atlas_db)
    try:
        grouped: dict[str, list[dict[str, Any]]] = {}
        for row in conn.execute(
            "SELECT payload_json FROM article_payloads WHERE is_public_route=1 ORDER BY route_order"
        ):
            payload = json.loads(row["payload_json"])
            if isinstance(payload, dict) and isinstance(payload.get("lemma"), str):
                grouped.setdefault(normalize_uk_key(payload["lemma"]), []).append(payload)
        metadata = {str(row[0]): str(row[1]) for row in conn.execute("SELECT key, value_json FROM manifest_metadata")}
    finally:
        conn.close()
    return grouped, metadata


def atlas_senses(article: dict[str, Any]) -> list[str]:
    """Atlas English senses = the article's ``enrichment.translation.en`` glosses."""

    enrichment = article.get("enrichment")
    translation = enrichment.get("translation") if isinstance(enrichment, dict) else None
    english = translation.get("en") if isinstance(translation, dict) else None
    if isinstance(english, str):
        english = [english]
    if not isinstance(english, list):
        return []
    return [" ".join(str(item).split()) for item in english if isinstance(item, str) and item.strip()]


def resolve_sense(teacher_en: str, senses: list[str]) -> dict[str, Any]:
    """Mechanical sense rule: single sense usable; multi-sense needs one unique match."""

    teacher_words = content_words(teacher_en)
    matched = [index for index, sense in enumerate(senses) if teacher_words & content_words(sense)]
    if not senses:
        return {"rule": "no-sense", "usable": False, "senseIndex": None, "matched": []}
    if len(senses) == 1:
        return {"rule": "single-sense", "usable": True, "senseIndex": 0, "matched": matched}
    if len(matched) == 1:
        return {"rule": "unique-match", "usable": True, "senseIndex": matched[0], "matched": matched}
    return {"rule": "ambiguous" if matched else "no-match", "usable": False, "senseIndex": None, "matched": matched}


class FormAnalyzer:
    """Cached VESUM form analysis (form -> lemma/pos/tags) and lemma paradigms."""

    def __init__(self, vesum_db: Path) -> None:
        self.vesum_db = vesum_db
        self._forms: dict[str, list[dict[str, str]]] = {}
        self._lemma_forms: dict[str, list[dict[str, str]]] = {}
        self._token_rows: dict[str, list[dict[str, str]]] = {}
        self._form_slots: dict[str, list[tuple[str, frozenset[tuple[str, ...]]]]] = {}

    def prefetch(self, tokens: Iterable[str]) -> None:
        from scripts.verification.vesum import verify_words

        pending = sorted({variant for token in tokens for variant in _vesum_token_variants(token)} - self._forms.keys())
        for start in range(0, len(pending), 400):
            chunk = pending[start : start + 400]
            for word, rows in verify_words(chunk, db_path=self.vesum_db).items():
                self._forms[word] = [dict(row) for row in rows]

    def analyses(self, token: str) -> list[dict[str, str]]:
        cached = self._token_rows.get(token)
        if cached is not None:
            return cached
        self.prefetch([token])
        seen: set[tuple[str, str, str]] = set()
        rows: list[dict[str, str]] = []
        for variant in _vesum_token_variants(token):
            for row in self._forms.get(variant, []):
                key = (row["lemma"], row["pos"], row["tags"])
                if key not in seen:
                    seen.add(key)
                    rows.append(row)
        self._token_rows[token] = rows
        return rows

    def lemmas(self, token: str) -> frozenset[str]:
        return frozenset(_canonical(row["lemma"]) for row in self.analyses(token))

    def lemma_forms(self, lemma: str) -> list[dict[str, str]]:
        from scripts.verification.vesum import verify_lemma

        if lemma not in self._lemma_forms:
            self._lemma_forms[lemma] = [dict(row) for row in verify_lemma(lemma, db_path=self.vesum_db)]
        return self._lemma_forms[lemma]

    def canonical_forms(self, lemma: str) -> frozenset[str]:
        return frozenset(_canonical(row["word_form"]) for row in self.lemma_forms(lemma)) | {lemma}

    def form_slots(self, lemma: str) -> list[tuple[str, frozenset[tuple[str, ...]]]]:
        """Sorted surfaces of *lemma*, each with every grammatical slot it fills."""

        if lemma not in self._form_slots:
            slots: dict[str, set[tuple[str, ...]]] = {}
            for row in self.lemma_forms(lemma):
                slots.setdefault(row["word_form"], set()).add(core_tag(row["tags"]))
            self._form_slots[lemma] = [(form, frozenset(found)) for form, found in sorted(slots.items())]
        return self._form_slots[lemma]

    def has_verb(self, tokens: Sequence[str]) -> bool:
        return any(row["pos"] == "verb" for token in tokens for row in self.analyses(token))


def core_tag(tags: str) -> tuple[str, ...]:
    parts = tags.split(":")
    return (parts[0], *sorted(part for part in parts[1:] if part in CORE_TAG_PARTS))


# --------------------------------------------------------------------------- aspect (VESUM + checked ULIF)


@dataclass(frozen=True)
class LemmaEvidence:
    """What the two sources say about one lemma spelling."""

    vesum: frozenset[str]  # aspects on VESUM verb lemmas with this spelling ⊆ {imperf, perf}
    vesum_other_pos: bool  # VESUM also has a non-verb lemma with this spelling
    ulif: frozenset[str]  # aspects of checked ULIF verb entries ⊆ {imperf, perf, dual}
    ulif_other_pos: bool  # a checked ULIF entry with a non-verb label

    @property
    def verb(self) -> bool:
        return bool(self.vesum or self.ulif)

    @property
    def other_pos(self) -> bool:
        return self.vesum_other_pos or self.ulif_other_pos


class AspectSources:
    """Read-only lemma lookups in VESUM ``forms_all`` and checked ULIF entries."""

    def __init__(self, vesum_db: Path, sources_db: Path) -> None:
        self._vesum = _ro_connect(vesum_db)
        self._sources = _ro_connect(sources_db)
        self._cache: dict[str, LemmaEvidence] = {}
        self.ulif_rows: set[tuple[str, int, str]] = set()

    def close(self) -> None:
        self._vesum.close()
        self._sources.close()

    def evidence(self, lemma: str) -> LemmaEvidence:
        cached = self._cache.get(lemma)
        if cached is not None:
            return cached
        vesum: set[str] = set()
        vesum_other = False
        for row in self._vesum.execute("SELECT DISTINCT pos, tags FROM forms_all WHERE lemma = ?", (lemma,)):
            if row["pos"] == "verb":
                vesum.update(part for part in str(row["tags"]).split(":") if part in {"imperf", "perf"})
            else:
                vesum_other = True
        ulif: set[str] = set()
        ulif_other = False
        for row in self._sources.execute(
            "SELECT homonym_index, grammatical_label FROM ulif_dictua_entries "
            "WHERE normalized_query = ? AND homonym_checked = 1 AND status = 'ok' ORDER BY homonym_index",
            (lemma,),
        ):
            label = str(row["grammatical_label"])
            if label in ULIF_ASPECT_LABELS:
                ulif.add(ULIF_ASPECT_LABELS[label])
                self.ulif_rows.add((lemma, int(row["homonym_index"]), label))
            elif label:
                ulif_other = True
        found = LemmaEvidence(frozenset(vesum), vesum_other, frozenset(ulif), ulif_other)
        self._cache[lemma] = found
        return found


def _one_source(values: frozenset[str]) -> str | None:
    if not values:
        return None
    return next(iter(values)) if len(values) == 1 else "both"


def resolve_aspect(evidence: LemmaEvidence) -> tuple[str, str]:
    """(aspect, basis). VESUM lists a biaspectual verb as two lemmas (imperf + perf),
    exactly like two homograph verbs, so only ULIF's dual label tells them apart."""

    vesum, ulif = _one_source(evidence.vesum), _one_source(evidence.ulif)
    if vesum and ulif:
        if vesum == ulif and vesum in {"imperf", "perf"}:
            return vesum, "agree"
        if vesum == "both" and ulif == "dual":
            return "dual", "agree"
        if vesum == "both" and ulif == "both":
            return "unknown", "homograph"
        return "unknown", "conflict"
    if vesum:
        return (vesum, "vesum-only") if vesum != "both" else ("unknown", "vesum-only")
    if ulif:
        return (ulif, "ulif-only") if ulif != "both" else ("unknown", "ulif-only")
    return "unknown", "none"


def _is_verb_lemma(evidence: LemmaEvidence, teacher_says_verb: bool) -> bool:
    # A spelling that is also a noun/adjective lemma (мати "mother" / "to have")
    # is read as the verb only when the teacher's English is a verb meaning.
    return evidence.verb and (teacher_says_verb or not evidence.other_pos)


def entry_aspect(entry: dict[str, Any], sources: AspectSources) -> dict[str, Any] | None:
    """Source-derived aspect record of a verb entry; ``None`` for non-verb entries.

    Single words look up the key. A phrase looks up its first token that the
    sources know as a verb lemma (its governing verb, e.g. ``вийти`` in ``Вийти з ладу``).
    """

    teacher_en = str(entry["teacherEn"])
    says_verb = teacher_implies_verb(teacher_en)
    lemma: str | None = None
    evidence: LemmaEvidence | None = None
    if entry["multiword"]:
        for token in UK_TOKEN_RE.findall(str(entry["key"])):
            candidate = _canonical(token)
            found = sources.evidence(candidate)
            if _is_verb_lemma(found, says_verb):
                lemma, evidence = candidate, found
                break
        if lemma is None and not says_verb:
            return None
    else:
        found = sources.evidence(str(entry["key"]))
        if _is_verb_lemma(found, says_verb):
            lemma, evidence = str(entry["key"]), found
        elif not (says_verb and not found.verb and not found.other_pos):
            return None
    aspect, basis = resolve_aspect(evidence) if evidence else ("unknown", "none")
    marker = teacher_aspect(teacher_en)
    agrees: bool | None = None
    if marker and aspect in {"imperf", "perf"}:
        agrees = marker == {aspect}
    elif marker and aspect == "dual":
        agrees = True
    return {
        "value": aspect,
        "basis": basis,
        "lemma": lemma,
        "vesum": sorted(evidence.vesum) if evidence else [],
        "ulif": sorted(evidence.ulif) if evidence else [],
        "teacherMarker": "+".join(sorted(marker)) or None,
        "markerAgrees": agrees,
    }


# --------------------------------------------------------------------------- sentences


@dataclass(frozen=True)
class SourceSentence:
    text: str
    source: str  # "teacher-lesson" | "textbook"
    locator: str
    title: str | None = None
    english: str | None = None
    order: tuple[Any, ...] = ()


def _lesson_date(text: str) -> str:
    first_line = text.split("\n", 1)[0].strip()
    match = DATE_START.match(first_line)
    if not match:
        return ""
    day, month, year = match.groups()
    return f"{year}-{month}-{day}"


def _sentence_shape_ok(sentence: str, *, max_tokens: int, max_chars: int) -> bool:
    tokens = _tokens(sentence)
    return (
        3 <= len(tokens) <= max_tokens
        and 15 <= len(sentence) <= max_chars
        and sentence.endswith(SENTENCE_END)
        and not sentence.isupper()
        and BLANK[:2] not in sentence
        and "http" not in sentence.casefold()
    )


def teacher_lesson_sentences(conn: sqlite3.Connection) -> list[SourceSentence]:
    """Ukrainian sentences from the teacher's lessons, newest lesson first.

    Lessons alternate an English line with its Ukrainian rendering; when a
    Ukrainian line is one sentence directly after an English-only line, that
    English line is kept as the sentence's translation.
    """

    lessons = [
        (_lesson_date(row["text"]), str(row["chunk_id"]), str(row["text"]))
        for row in conn.execute(
            "SELECT chunk_id, text FROM textbooks WHERE source_file = ? ORDER BY chunk_id", (TEACHER_LESSON_SOURCE,)
        )
    ]
    lessons.sort(key=lambda lesson: (lesson[0], lesson[1]), reverse=True)
    sentences: list[SourceSentence] = []
    seen: set[str] = set()
    for lesson_rank, (lesson_date, chunk_id, text) in enumerate(lessons):
        previous_english: str | None = None
        for line_index, raw_line in enumerate(text.split("\n")[1:]):
            line = " ".join(raw_line.split())
            if not line:
                continue
            has_latin = bool(LATIN_CHAR_RE.search(line))
            has_cyrillic = bool(CYRILLIC_RE.search(line))
            if has_latin and not has_cyrillic:
                previous_english = line
                continue
            if has_latin or not has_cyrillic:
                previous_english = None
                continue
            parts = [part.strip(" \t—–") for part in SENTENCE_SPLIT_RE.split(_normalise(line)) if part.strip()]
            english = previous_english if len(parts) == 1 else None
            previous_english = None
            for part_index, sentence in enumerate(parts):
                if not _sentence_shape_ok(sentence, max_tokens=30, max_chars=250):
                    continue
                if contains_private_teacher_name(sentence) or (english and contains_private_teacher_name(english)):
                    continue
                folded = sentence.casefold()
                if folded in seen:
                    continue
                seen.add(folded)
                sentences.append(
                    SourceSentence(
                        text=sentence,
                        source="teacher-lesson",
                        locator=lesson_date or chunk_id,
                        english=english,
                        order=(lesson_rank, line_index, part_index),
                    )
                )
    return sentences


def _textbook_rows(conn: sqlite3.Connection, match_query: str) -> list[sqlite3.Row]:
    columns = {str(row[1]) for row in conn.execute("PRAGMA table_info(textbooks)")}
    where = " ".join("AND lower(coalesce(source.source_file, '')) NOT LIKE ?" for _ in TEXTBOOK_EXCLUDED_PREFIXES)
    params: list[Any] = [match_query, *(f"{prefix}%" for prefix in TEXTBOOK_EXCLUDED_PREFIXES)]
    order = ""
    if "subject" in columns:
        order = "CASE WHEN lower(coalesce(source.subject, '')) IN ('ukrmova', 'bukvar') THEN 0 ELSE 1 END, "
    sql = f"""
        SELECT source.text, source.title, source.chunk_id
        FROM textbooks_fts AS fts JOIN textbooks AS source ON source.id = fts.rowid
        WHERE textbooks_fts MATCH ? AND source.source_file != '{TEACHER_LESSON_SOURCE}' {where}
        ORDER BY {order}bm25(textbooks_fts), source.id
        LIMIT {TEXTBOOK_SEARCH_LIMIT}
    """
    try:
        return list(conn.execute(sql, params))
    except sqlite3.OperationalError:
        return []


def textbook_sentences(
    conn: sqlite3.Connection, match_query: str, accept: Callable[[str], bool]
) -> Iterable[SourceSentence]:
    """Readable textbook sentences for which the cheap *accept* test holds."""

    for rank, row in enumerate(_textbook_rows(conn, match_query)):
        text = row["text"]
        if not isinstance(text, str):
            continue
        for index, raw in enumerate(SENTENCE_SPLIT_RE.split(_normalise(text))):
            sentence = raw.strip(" \t\n—–")
            quiz = LEADING_QUIZ_MARKER_RE.match(sentence)
            if quiz:
                sentence = sentence[quiz.end() :].lstrip(" \t\n—–")
            if not accept(sentence) or not _sentence_shape_ok(sentence, max_tokens=18, max_chars=180):
                continue
            if sentence.count("*") > 1 or _is_source_sentence_noise(sentence) or is_intentional_error_context(sentence):
                continue
            yield SourceSentence(
                text=sentence,
                source="textbook",
                locator=str(row["chunk_id"]),
                title=row["title"] if isinstance(row["title"], str) and row["title"].strip() else None,
                order=(rank, index),
            )


# --------------------------------------------------------------------------- cloze


@dataclass
class ClozeTarget:
    entry: dict[str, Any]
    lemma: str | None  # VESUM lemma for single-word entries
    phrase: tuple[str, ...] | None  # verbatim token sequence for multiword entries
    reason: str | None = None


@lru_cache(maxsize=200_000)
def _canonical(token: str) -> str:
    return normalize_uk_key(token)


def cloze_target(entry: dict[str, Any]) -> ClozeTarget:
    key = str(entry["key"])
    tokens = tuple(_canonical(token) for token in UK_TOKEN_RE.findall(key))
    if not tokens or " ".join(tokens) != key:
        return ClozeTarget(entry, None, None, "key has annotation punctuation; no verbatim phrase possible")
    if entry["multiword"]:
        return ClozeTarget(entry, None, tokens)
    return ClozeTarget(entry, key, None)


def _single_match(sentence: str, target: ClozeTarget, analyzer: FormAnalyzer) -> tuple[int, int, str, list[str]] | None:
    """Locate the one token whose VESUM analyses all belong to the target lemma."""

    hits: list[tuple[int, int, str, list[str]]] = []
    for match in UK_TOKEN_RE.finditer(sentence):
        lemmas = analyzer.lemmas(match.group())
        if not lemmas:
            continue
        if lemmas == {target.lemma}:
            rows = analyzer.analyses(match.group())
            hits.append((match.start(), match.end(), match.group(), sorted({row["tags"] for row in rows})))
        elif target.lemma in lemmas:
            return None  # the sentence has an ambiguous form of the target
    return hits[0] if len(hits) == 1 else None


def _phrase_match(sentence: str, target: ClozeTarget) -> tuple[int, int, str] | None:
    matches = list(UK_TOKEN_RE.finditer(sentence))
    canon = [_canonical(match.group()) for match in matches]
    width = len(target.phrase or ())
    spans = [
        (matches[index].start(), matches[index + width - 1].end())
        for index in range(len(canon) - width + 1)
        if tuple(canon[index : index + width]) == target.phrase
    ]
    if len(spans) != 1:
        return None
    start, end = spans[0]
    return start, end, sentence[start:end]


@dataclass
class DeckContext:
    entries: list[dict[str, Any]]
    by_id: dict[str, dict[str, Any]]
    overlaps: dict[str, list[str]]
    atlas: dict[str, dict[str, Any] | None]
    classes: dict[str, str]
    related: dict[str, set[str]] = field(default_factory=dict)  # Atlas synonym/antonym lemmas
    partners: dict[str, list[str]] = field(default_factory=dict)  # aspect partners (same English)

    def same_meaning(self, entry_id: str) -> set[str]:
        """Entries a distractor must never come from: overlaps, aspect partners (both
        forms may fit one sentence), and the entry itself."""

        return set(self.overlaps.get(entry_id, [])) | set(self.partners.get(entry_id, [])) | {entry_id}


def _single_distractors(
    target: ClozeTarget,
    tags: list[str],
    answer_form: str,
    ctx: DeckContext,
    analyzer: FormAnalyzer,
    seed: str,
) -> list[dict[str, str]]:
    entry_id = str(target.entry["entryId"])
    wanted = frozenset(core_tag(tag) for tag in tags)
    answer_forms = analyzer.canonical_forms(target.lemma or "")
    blocked = ctx.same_meaning(entry_id)
    related = ctx.related.get(entry_id, set())
    candidates: list[tuple[str, str]] = []
    for other in ctx.entries:
        other_id = str(other["entryId"])
        if other_id in blocked or other["multiword"] or other["key"] in related:
            continue
        # The distractor must fill every slot the answer form can fill, so it is
        # grammatical wherever the answer is and differs only lexically.
        for label, slots in analyzer.form_slots(str(other["key"])):
            if wanted <= slots and _canonical(label) not in answer_forms:
                candidates.append((other_id, _match_initial_capitalization(label, answer_form)))
                break
    return _pick_distractors(candidates, answer_form, seed)


def _phrase_distractors(target: ClozeTarget, answer_form: str, ctx: DeckContext, seed: str) -> list[dict[str, str]]:
    entry_id = str(target.entry["entryId"])
    blocked = ctx.same_meaning(entry_id)
    wanted_class = ctx.classes[entry_id]
    candidates: list[tuple[str, str]] = []
    for other in ctx.entries:
        other_id = str(other["entryId"])
        if other_id in blocked or not other["multiword"] or ctx.classes[other_id] != wanted_class:
            continue
        if cloze_target(other).phrase is None:
            continue
        candidates.append((other_id, _match_initial_capitalization(str(other["uk"]), answer_form)))
    return _pick_distractors(candidates, answer_form, seed)


def _pick_distractors(candidates: list[tuple[str, str]], answer_form: str, seed: str) -> list[dict[str, str]]:
    unique: dict[str, tuple[str, str]] = {}
    for other_id, label in sorted(candidates):
        folded = _canonical(label)
        if folded != _canonical(answer_form) and folded not in unique:
            unique[folded] = (other_id, label)
    pool = sorted(unique.values())
    if len(pool) < CHOICE_DISTRACTORS:
        return []
    picked = _seeded_rng(seed).sample(pool, CHOICE_DISTRACTORS)
    return [{"entryId": other_id, "label": label} for other_id, label in picked]


def _lemma_id(ctx: DeckContext, entry_id: str) -> str:
    article = ctx.atlas.get(entry_id)
    return str(article["url_slug"]) if article else entry_id


def _cloze_item(
    target: ClozeTarget,
    sentence: SourceSentence,
    span: tuple[int, int, str],
    distractors: list[dict[str, str]],
    index: int,
    ctx: DeckContext,
    sense: dict[str, Any] | None,
) -> dict[str, Any]:
    entry = target.entry
    entry_id = str(entry["entryId"])
    start, end, form = span
    clozed = sentence.text[:start] + BLANK + sentence.text[end:]
    options = [
        {
            "optionId": "opt_ans",
            "label": form,
            "lemmaId": _lemma_id(ctx, entry_id),
            "entryId": entry_id,
            "kind": "answer",
        },
        *[
            {
                "optionId": f"opt_dec_{number}",
                "label": option["label"],
                "lemmaId": _lemma_id(ctx, option["entryId"]),
                "entryId": option["entryId"],
                "kind": "distractor",
            }
            for number, option in enumerate(distractors)
        ],
    ]
    answer = options.pop(0)
    options.insert(_seeded_rng(entry_id, "cloze-position", str(index)).randrange(len(options) + 1), answer)
    article = ctx.atlas.get(entry_id)
    item: dict[str, Any] = {
        "clozeId": f"{entry_id}:cloze:{index}",
        "entryId": entry_id,
        "cardId": f"{entry_id}:cloze",
        "lemmaId": _lemma_id(ctx, entry_id),
        "lemma": str(entry["uk"]),
        "sentenceFrameId": "tframe_" + hashlib.sha1(sentence.text.encode("utf-8")).hexdigest()[:12],
        "sentence": clozed,
        "blankCase": "context",
        "form": form,
        "caseRule": {
            "code": "document-context",
            "labelUk": DOCUMENT_CONTEXT_LABEL_UK,
            "labelEn": "Teacher lesson sentence" if sentence.source == "teacher-lesson" else "Textbook sentence",
        },
        "options": options,
        "source": sentence.source,
    }
    if sentence.english:
        item["clozeEn"] = sentence.english
    if sentence.source == "textbook":
        attribution: dict[str, Any] = {
            "source": "textbook",
            "label": "Ukrainian school textbook",
            "locator": sentence.locator,
        }
        if sentence.title:
            attribution["title"] = sentence.title
        item["attribution"] = attribution
        item["license"] = dict(TEXTBOOK_LICENSE)
    else:
        item["attribution"] = {"source": "teacher-lesson", "label": "Teacher's lesson", "locator": sentence.locator}
    if article is not None:
        item["atlasSense"] = {
            "slug": str(article["url_slug"]),
            "senseIndex": sense["senseIndex"] if sense else None,
            "basis": "provenance" if sentence.source == "teacher-lesson" else (sense or {}).get("rule"),
        }
    return item


def _presence_test(target: ClozeTarget, analyzer: FormAnalyzer) -> Callable[[str], bool]:
    """Cheap pre-filter: the sentence contains a surface of the target at all."""

    if target.phrase:
        first = target.phrase[0]
        return lambda sentence: any(_canonical(token) == first for token in UK_TOKEN_RE.findall(sentence))
    forms = analyzer.canonical_forms(target.lemma or "")
    return lambda sentence: any(_canonical(token) in forms for token in UK_TOKEN_RE.findall(sentence))


def _fts_query(target: ClozeTarget, analyzer: FormAnalyzer) -> str | None:
    if target.phrase:
        return '"' + " ".join(target.phrase).replace('"', "") + '"'
    forms = sorted({row["word_form"] for row in analyzer.lemma_forms(target.lemma or "")} | {target.lemma or ""})
    forms = [form for form in forms if form and '"' not in form]
    return " OR ".join(f'"{form}"' for form in forms[:80]) if forms else None


def build_cloze(
    ctx: DeckContext,
    senses: dict[str, dict[str, Any]],
    lesson_sentences: list[SourceSentence],
    sources_conn: sqlite3.Connection,
    analyzer: FormAnalyzer,
) -> tuple[list[dict[str, Any]], dict[str, str], list[dict[str, Any]], list[str]]:
    """Return cloze items, per-entry no-cloze reasons, public lesson sentences, textbook sentences used."""

    analyzer.prefetch(token for sentence in lesson_sentences for token in _tokens(sentence.text))
    by_lemma: dict[str, list[int]] = {}
    by_token: dict[str, list[int]] = {}
    for index, sentence in enumerate(lesson_sentences):
        for token in set(_tokens(sentence.text)):
            by_token.setdefault(_canonical(token), []).append(index)
            for lemma in analyzer.lemmas(token):
                by_lemma.setdefault(lemma, []).append(index)

    def lesson_candidates(target: ClozeTarget) -> list[SourceSentence]:
        if target.phrase:
            indices = set(by_token.get(target.phrase[0], []))
        else:
            indices = set(by_lemma.get(target.lemma or "", []))
        return [lesson_sentences[index] for index in sorted(indices)]

    items: list[dict[str, Any]] = []
    residuals: dict[str, str] = {}
    public_lessons: list[dict[str, Any]] = []
    textbook_used: list[str] = []
    for entry in ctx.entries:
        entry_id = str(entry["entryId"])
        target = cloze_target(entry)
        if target.reason:
            residuals[entry_id] = target.reason
            continue
        sense = senses.get(entry_id)
        sources: list[Iterable[SourceSentence]] = [lesson_candidates(target)]
        textbook_note = None
        if sense is None:
            textbook_note = "not in the Atlas: textbook sentences need a usable Atlas sense"
        elif not sense["usable"]:
            textbook_note = f"Atlas sense rule '{sense['rule']}': textbook sentences withheld"
        else:
            query = _fts_query(target, analyzer)
            if query:
                sources.append(textbook_sentences(sources_conn, query, _presence_test(target, analyzer)))
        found = 0
        rejected_for_distractors = 0
        seen_sentences: set[str] = set()
        for source in sources:
            for sentence in source:
                if found >= MAX_CLOZE_PER_ENTRY:
                    break
                folded = sentence.text.casefold()
                if folded in seen_sentences:
                    continue
                if target.phrase:
                    span = _phrase_match(sentence.text, target)
                    if span is None:
                        continue
                    distractors = _phrase_distractors(target, span[2], ctx, f"{entry_id}:cloze:{found}")
                else:
                    if sentence.source == "textbook":
                        tokens = _tokens(sentence.text)
                        analyzer.prefetch(tokens)
                        if not analyzer.has_verb(tokens):
                            continue
                    single = _single_match(sentence.text, target, analyzer)
                    if single is None:
                        continue
                    start, end, form, tags = single
                    span = (start, end, form)
                    distractors = _single_distractors(target, tags, form, ctx, analyzer, f"{entry_id}:cloze:{found}")
                if not distractors:
                    rejected_for_distractors += 1
                    continue
                seen_sentences.add(folded)
                item = _cloze_item(target, sentence, span, distractors, found, ctx, sense)
                items.append(item)
                found += 1
                if sentence.source == "teacher-lesson":
                    public_lessons.append(
                        {
                            "entryId": entry_id,
                            "clozeId": item["clozeId"],
                            "lesson": sentence.locator,
                            "sentence": sentence.text,
                        }
                    )
                else:
                    textbook_used.append(f"{sentence.locator}\x1f{sentence.text}")
        if found == 0:
            if rejected_for_distractors:
                residuals[entry_id] = "attesting sentence found but fewer than 3 valid same-form distractors"
            elif target.phrase:
                residuals[entry_id] = "no sentence contains the whole phrase verbatim" + (
                    f" ({textbook_note})" if textbook_note else ""
                )
            else:
                residuals[entry_id] = "no sentence attests an unambiguous form of the entry" + (
                    f" ({textbook_note})" if textbook_note else ""
                )
    return items, residuals, public_lessons, textbook_used


# --------------------------------------------------------------------------- choice


def _choice(
    entry: dict[str, Any],
    ctx: DeckContext,
    direction: str,
) -> tuple[dict[str, Any] | None, str | None]:
    """UK->EN (recognition) or EN->UK (production) meaning choice with 4 options."""

    entry_id = str(entry["entryId"])
    prompt_field, answer_field = ("uk", "en") if direction == "recognition" else ("en", "uk")
    prompt = str(entry[prompt_field])
    answer_label = str(entry[answer_field])
    blocked = set(ctx.overlaps.get(entry_id, [])) | {entry_id}
    same_class = ctx.classes[entry_id]
    pool = [
        other
        for other in ctx.entries
        if str(other["entryId"]) not in blocked
        and str(other[answer_field]).casefold() not in {answer_label.casefold(), prompt.casefold()}
    ]
    preferred = [other for other in pool if ctx.classes[str(other["entryId"])] == same_class]
    rng = _seeded_rng(entry_id, direction, "choice")
    chosen: list[dict[str, Any]] = []
    for candidates in (preferred, pool):
        shuffled = sorted(candidates, key=lambda other: str(other["entryId"]))
        rng.shuffle(shuffled)
        for other in shuffled:
            if len(chosen) == CHOICE_DISTRACTORS:
                break
            other_id = str(other["entryId"])
            label = str(other[answer_field]).casefold()
            if any(
                other_id == str(picked["entryId"])
                or other_id in ctx.overlaps.get(str(picked["entryId"]), [])
                or label == str(picked[answer_field]).casefold()
                for picked in chosen
            ):
                continue
            chosen.append(other)
    if len(chosen) < CHOICE_DISTRACTORS:
        return None, f"only {len(chosen)} non-overlapping distractors available"
    options = [{"entryId": entry_id, "label": answer_label, "kind": "answer"}] + [
        {"entryId": str(other["entryId"]), "label": str(other[answer_field]), "kind": "distractor"} for other in chosen
    ]
    answer = options.pop(0)
    options.insert(rng.randrange(len(options) + 1), answer)
    return {
        "choiceId": f"{entry_id}:{direction}:choice",
        "direction": "uk-en" if direction == "recognition" else "en-uk",
        "prompt": prompt,
        "options": options,
    }, None


# --------------------------------------------------------------------------- grammar


def _grammar_lexeme(lexeme: dict[str, Any]) -> dict[str, Any]:
    gated = dict(lexeme)
    level = lexeme.get("cefr")
    gated["cefr"] = (
        level if level in LEVEL_RANK and LEVEL_RANK[level] >= LEVEL_RANK[GRAMMAR_LEVEL_FLOOR] else GRAMMAR_LEVEL_FLOOR
    )
    return gated


def identity_conflict(entry: dict[str, Any], articles: list[dict[str, Any]]) -> str | None:
    """Grammar identity is unsafe when the key names several Atlas articles, or when
    the sources know the single word as a verb but its Atlas article is not a verb.
    The teacher's aspect markers never create a conflict (they are only reported)."""

    if len(articles) > 1:
        return f"homograph: {len(articles)} Atlas articles share the key ({', '.join(str(a['url_slug']) for a in articles)})"
    if entry["multiword"]:
        return None  # multiword entries never get grammar modes, so no grammar identity to protect
    article = articles[0]
    aspect = entry.get("aspect")
    bucket = _option_pos_bucket(article.get("pos"))
    if aspect is not None and aspect["lemma"] and bucket and bucket != "verb":
        return f"part of speech: VESUM/ULIF know the key as a verb, Atlas article is '{article.get('pos')}'"
    return None


def _source_aspect_classify(items: list[dict[str, Any]], aspect: str | None) -> list[dict[str, Any]]:
    """Keep an aspect classify set only when it matches the source-derived aspect."""

    wanted = CLASSIFY_ASPECT.get(aspect or "")
    kept: list[dict[str, Any]] = []
    for item in items:
        item["sets"] = [
            one for one in item["sets"] if one.get("setId") != "aspect" or (wanted and one.get("answer") == wanted)
        ]
        if item["sets"]:
            kept.append(item)
    return kept


def build_grammar(
    entry: dict[str, Any],
    article: dict[str, Any],
    sense: dict[str, Any],
    verifier: VesumVerifier,
    deck_lexemes: list[dict[str, Any]],
    atlas_by_key: dict[str, list[dict[str, Any]]],
    verdicts: tuple[set[tuple[str, str, str]], set[tuple[str, str, str]]],
    ctx: DeckContext,
    lexeme: dict[str, Any],
) -> dict[str, list[dict[str, Any]]]:
    entry_id = str(entry["entryId"])
    card_id = f"{entry_id}:grammar"
    atlas_ref = {"slug": str(article["url_slug"]), "senseIndex": sense["senseIndex"]}
    gated = _grammar_lexeme(lexeme)
    modes: dict[str, list[dict[str, Any]]] = {mode: [] for mode in ("stress", "paradigm", "classify", "synonym")}

    def tag(item: dict[str, Any], id_field: str, suffix: str) -> dict[str, Any]:
        item[id_field] = f"{entry_id}:{suffix}"
        item.update({"entryId": entry_id, "cardId": card_id, "atlas": atlas_ref})
        return item

    stress = _stress_payload(article)
    if stress:
        modes["stress"].append(
            tag({"lemmaId": gated["lemmaId"], "lemma": gated["lemma"], **stress}, "stressId", "stress")
        )
    aspect = (entry.get("aspect") or {}).get("value")
    classify = _build_classify_items(article, gated, vesum_aspect=CLASSIFY_ASPECT.get(aspect or ""))
    for item in _source_aspect_classify(classify, aspect):
        modes["classify"].append(tag(item, "classifyId", "classify"))
    for index, item in enumerate(_build_paradigm_items(gated)):
        modes["paradigm"].append(tag(item, "paradigmId", f"paradigm:{index}"))
    if sense["usable"]:
        approved, _rejected = verdicts
        plain = _plain(str(gated["lemma"]))
        blocked_ids = ctx.same_meaning(entry_id)
        related = ctx.related.get(entry_id, set())
        pool = [
            candidate
            for candidate in deck_lexemes
            if candidate["entryId"] not in blocked_ids and _plain(candidate["lemma"]) not in related
        ]
        for pair in sorted(approved):
            if plain not in pair[:2]:
                continue
            other_plain = pair[1] if pair[0] == plain else pair[0]
            others = atlas_by_key.get(normalize_uk_key(other_plain), [])
            if len(others) != 1:
                continue
            target = _build_lexeme(others[0], verifier)
            if target is None:
                continue
            target = _grammar_lexeme(target)
            distractors = [
                candidate
                for candidate in _valid_synonym_distractors(target, gated, pool)
                if _plain(candidate["lemma"]) != _plain(target["lemma"])
            ][:3]
            if len(distractors) < 3:
                continue
            polarity = pair[2]
            synonym_id = f"{entry_id}:{polarity}:{target['lemmaId']}"
            options = [
                _synonym_option(target["lemma"], target["lemmaId"], "answer"),
                *[_synonym_option(d["lemma"], d["lemmaId"], "distractor") for d in distractors],
            ]
            answer_index = int(hashlib.sha1(synonym_id.encode("utf-8")).hexdigest()[:2], 16) % len(options)
            answer = options.pop(0)
            options.insert(answer_index, answer)
            item = {
                "lemmaId": gated["lemmaId"],
                "targetLemmaId": target["lemmaId"],
                "polarity": polarity,
                "prompt": gated["lemma"],
                "answer": target["lemma"],
                "options": options,
                "source": "synonym-pair-verdicts",
            }
            modes["synonym"].append(tag(item, "synonymId", f"{polarity}:{target['lemmaId']}"))
    return modes


# --------------------------------------------------------------------------- build


@dataclass(frozen=True)
class TeacherDeckInputs:
    atlas_db: Path
    sources_db: Path
    vesum_db: Path
    synonym_verdicts: Path


@dataclass
class TeacherDeckBuild:
    deck: dict[str, Any]
    cloze: dict[str, Any]
    coverage: dict[str, Any]
    input_versions: dict[str, Any]
    public_lesson_sentences: list[dict[str, Any]]


def _deck_version(*payloads: dict[str, Any]) -> str:
    digest = hashlib.sha256()
    for payload in payloads:
        digest.update(json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8"))
    return "teacher-v1-" + digest.hexdigest()[:16]


def _with_source_aspect(entry: dict[str, Any], sources: AspectSources) -> dict[str, Any]:
    """Keep the teacher's English as ``teacherEn``; ``en`` becomes the learner-facing
    English with the teacher's markers replaced by the source-derived aspect label."""

    derived = {**entry, "teacherEn": str(entry["en"])}
    derived["aspect"] = entry_aspect(derived, sources)
    derived["en"] = display_english(derived["teacherEn"], (derived["aspect"] or {}).get("value"))
    return derived


def build_teacher_deck(entries: list[dict[str, Any]], inputs: TeacherDeckInputs) -> TeacherDeckBuild:
    atlas_by_key, atlas_metadata = read_atlas_articles(inputs.atlas_db)
    verifier = RealVesumVerifier(inputs.vesum_db)
    analyzer = FormAnalyzer(inputs.vesum_db)
    verdict_payload = read_synonym_verdicts(inputs.synonym_verdicts)
    approved, rejected, _a2 = build_synonym_verdict_sets(verdict_payload)
    verdicts = (approved - rejected, rejected)

    aspect_sources = AspectSources(inputs.vesum_db, inputs.sources_db)
    try:
        entries = [_with_source_aspect(entry, aspect_sources) for entry in entries]
        ulif_aspect_rows = sorted(aspect_sources.ulif_rows)
    finally:
        aspect_sources.close()
    by_id = {str(entry["entryId"]): entry for entry in entries}
    overlaps, partners = overlap_graph(
        entries, {str(entry["entryId"]): (entry["aspect"] or {}).get("value") for entry in entries}
    )
    atlas: dict[str, dict[str, Any] | None] = {}
    senses: dict[str, dict[str, Any]] = {}
    residual_no_atlas: list[dict[str, Any]] = []
    conflicts: dict[str, str] = {}
    gloss_differences: list[dict[str, Any]] = []
    sense_review: list[dict[str, Any]] = []
    analyzer.prefetch(str(entry["key"]) for entry in entries if not entry["multiword"])
    for entry in entries:
        entry_id = str(entry["entryId"])
        articles = atlas_by_key.get(str(entry["key"]), [])
        if not articles:
            atlas[entry_id] = None
            residual_no_atlas.append({"entryId": entry_id, "uk": entry["uk"], "reason": "no public Atlas article"})
            continue
        conflict = identity_conflict(entry, articles)
        article = articles[0]
        if conflict and len(articles) > 1:
            atlas[entry_id] = None
            conflicts[entry_id] = conflict
            continue
        atlas[entry_id] = article
        if conflict:
            conflicts[entry_id] = conflict
        sense_list = atlas_senses(article)
        sense = resolve_sense(str(entry["en"]), sense_list)
        senses[entry_id] = sense
        if sense["rule"] == "single-sense" and not sense["matched"]:
            gloss_differences.append(
                {"entryId": entry_id, "uk": entry["uk"], "en": entry["en"], "atlasEnglish": sense_list[0]}
            )
        if not sense["usable"]:
            sense_review.append(
                {
                    "entryId": entry_id,
                    "uk": entry["uk"],
                    "en": entry["en"],
                    "rule": sense["rule"],
                    "atlasSenses": sense_list,
                    "matchedSenses": sense["matched"],
                }
            )

    classes = {
        entry_id: _entry_class(entry, (atlas[entry_id] or {}).get("pos") if atlas[entry_id] else None)
        for entry_id, entry in by_id.items()
    }
    related: dict[str, set[str]] = {}
    for entry_id, article in atlas.items():
        if article is not None:
            related[entry_id] = {
                _plain(item) for section in ("synonyms", "antonyms") for item in _section_items(article, section)
            }
    ctx = DeckContext(entries, by_id, overlaps, atlas, classes, related, partners)

    lexemes: dict[str, dict[str, Any]] = {}
    for entry_id, article in atlas.items():
        if article is not None and not by_id[entry_id]["multiword"] and entry_id not in conflicts:
            lexeme = _build_lexeme(article, verifier)
            if lexeme is not None:
                lexeme["entryId"] = entry_id
                lexemes[entry_id] = lexeme
    deck_lexemes = [_grammar_lexeme(lexeme) for _, lexeme in sorted(lexemes.items())]

    mode_items: dict[str, list[dict[str, Any]]] = {mode: [] for mode in ("stress", "paradigm", "classify", "synonym")}
    grammar_refs: dict[str, list[dict[str, str]]] = {}
    for entry in entries:
        entry_id = str(entry["entryId"])
        lexeme = lexemes.get(entry_id)
        article = atlas.get(entry_id)
        if lexeme is None or article is None:
            continue
        built = build_grammar(
            entry, article, senses[entry_id], verifier, deck_lexemes, atlas_by_key, verdicts, ctx, lexeme
        )
        refs: list[dict[str, str]] = []
        for mode, items in built.items():
            id_field = {
                "stress": "stressId",
                "paradigm": "paradigmId",
                "classify": "classifyId",
                "synonym": "synonymId",
            }[mode]
            for item in items:
                mode_items[mode].append(item)
                ref_mode = item.get("polarity", mode) if mode == "synonym" else mode
                refs.append({"mode": ref_mode, "id": item[id_field]})
        if refs:
            grammar_refs[entry_id] = refs

    sources_conn = _ro_connect(inputs.sources_db)
    try:
        lesson_sentences = teacher_lesson_sentences(sources_conn)
        cloze_items, no_cloze, public_lessons, textbook_used = build_cloze(
            ctx, senses, lesson_sentences, sources_conn, analyzer
        )
        textbook_rows = sources_conn.execute(
            "SELECT count(*) FROM textbooks WHERE source_file != ?", (TEACHER_LESSON_SOURCE,)
        ).fetchone()[0]
        lesson_digest = _sha256_lines(
            f"{row[0]}\x1f{row[1]}"
            for row in sources_conn.execute(
                "SELECT chunk_id, text FROM textbooks WHERE source_file = ? ORDER BY chunk_id", (TEACHER_LESSON_SOURCE,)
            )
        )
        lesson_units = sources_conn.execute(
            "SELECT count(*) FROM textbooks WHERE source_file = ?", (TEACHER_LESSON_SOURCE,)
        ).fetchone()[0]
    finally:
        sources_conn.close()
    cloze_by_entry: dict[str, list[str]] = {}
    for item in cloze_items:
        cloze_by_entry.setdefault(item["entryId"], []).append(item["clozeId"])

    deck_entries: list[dict[str, Any]] = []
    refused: list[dict[str, Any]] = []
    production_omitted: list[dict[str, Any]] = []
    for entry in entries:
        entry_id = str(entry["entryId"])
        article = atlas.get(entry_id)
        recognition_choice, recognition_refusal = _choice(entry, ctx, "recognition")
        if recognition_refusal:
            refused.append(
                {"entryId": entry_id, "uk": entry["uk"], "card": "recognition", "reason": recognition_refusal}
            )
        cards: dict[str, Any] = {
            "recognition": {"cardId": f"{entry_id}:recognition", "choice": recognition_choice},
            "production": None,
            "cloze": None,
            "grammar": None,
        }
        if overlaps[entry_id]:
            production_omitted.append(
                {
                    "entryId": entry_id,
                    "uk": entry["uk"],
                    "en": entry["en"],
                    "overlapsWith": [
                        {"entryId": other, "uk": by_id[other]["uk"], "en": by_id[other]["en"]}
                        for other in overlaps[entry_id]
                    ],
                }
            )
        else:
            production_choice, production_refusal = _choice(entry, ctx, "production")
            if production_refusal:
                refused.append(
                    {"entryId": entry_id, "uk": entry["uk"], "card": "production", "reason": production_refusal}
                )
            cards["production"] = {"cardId": f"{entry_id}:production", "choice": production_choice}
        if cloze_by_entry.get(entry_id):
            cards["cloze"] = {"cardId": f"{entry_id}:cloze", "clozeIds": cloze_by_entry[entry_id]}
        if grammar_refs.get(entry_id):
            cards["grammar"] = {"cardId": f"{entry_id}:grammar", "items": grammar_refs[entry_id]}
        sense = senses.get(entry_id)
        deck_entries.append(
            {
                "entryId": entry_id,
                "key": entry["key"],
                "uk": entry["uk"],
                "en": entry["en"],
                "teacherEn": entry["teacherEn"],
                "aspect": entry["aspect"],
                "firstSeen": entry["firstSeen"],
                "multiword": entry["multiword"],
                "sourceRows": entry["sourceRows"],
                "sourceKeys": entry["sourceKeys"],
                "atlas": None
                if article is None
                else {
                    "slug": str(article["url_slug"]),
                    "pos": article.get("pos"),
                    "senseRule": sense["rule"] if sense else None,
                    "senseIndex": sense["senseIndex"] if sense else None,
                    "identityConflict": entry_id in conflicts,
                },
                "conflicts": overlaps[entry_id],
                "aspectPartners": partners[entry_id],
                "matching": True,
                "cards": cards,
            }
        )

    deck: dict[str, Any] = {
        "schema": SCHEMA,
        "schemaVersion": SCHEMA_VERSION,
        "deckId": DECK_ID,
        "deckVersion": "",
        "level": LEVEL,
        "source": "teacher-table",
        "cardKinds": list(CARD_KINDS),
        "clozeFile": CLOZE_FILE,
        "entries": deck_entries,
        **{mode: items for mode, items in mode_items.items()},
    }
    cloze: dict[str, Any] = {
        "schema": CLOZE_SCHEMA,
        "schemaVersion": SCHEMA_VERSION,
        "deckId": DECK_ID,
        "deckVersion": "",
        "level": LEVEL,
        "source": "teacher-lessons+textbooks",
        "cloze": cloze_items,
    }
    version = _deck_version(deck, cloze)
    deck["deckVersion"] = version
    cloze["deckVersion"] = version

    counts = mode_counts(deck, cloze)
    deck["counts"] = counts
    coverage = {
        "schema": COVERAGE_SCHEMA,
        "schemaVersion": SCHEMA_VERSION,
        "deckVersion": version,
        "counts": counts,
        "residuals": {
            "noAtlas": residual_no_atlas,
            "identityConflicts": [
                {"entryId": entry_id, "uk": by_id[entry_id]["uk"], "reason": reason}
                for entry_id, reason in sorted(conflicts.items(), key=lambda item: by_id[item[0]]["firstSeen"])
            ],
            "productionOmitted": production_omitted,
            "refusedGroups": refused,
            "noCloze": [
                {"entryId": entry_id, "uk": by_id[entry_id]["uk"], "reason": reason}
                for entry_id, reason in sorted(no_cloze.items(), key=lambda item: by_id[item[0]]["firstSeen"])
            ],
            "senseReview": sense_review,
            "glossDifferences": gloss_differences,
            "aspectUnknown": [
                {"entryId": str(entry["entryId"]), "uk": entry["uk"], "en": entry["teacherEn"], **entry["aspect"]}
                for entry in entries
                if entry["aspect"] and entry["aspect"]["value"] == "unknown"
            ],
            "aspectMarkerDisagreements": [
                {"entryId": str(entry["entryId"]), "uk": entry["uk"], "en": entry["teacherEn"], **entry["aspect"]}
                for entry in entries
                if entry["aspect"] and entry["aspect"]["markerAgrees"] is False
            ],
        },
    }
    input_versions = {
        "atlas": {
            "manifestVersion": atlas_metadata.get("version"),
            "generatedAt": atlas_metadata.get("generated_at"),
            "joinedArticlesSha256": _sha256_lines(
                json.dumps(article, ensure_ascii=False, sort_keys=True)
                for _, article in sorted((k, v) for k, v in atlas.items() if v is not None)
            ),
        },
        "sources": {
            "teacherLessonUnits": lesson_units,
            "teacherLessonsSha256": lesson_digest,
            "textbookRows": textbook_rows,
            "textbookSentencesSha256": _sha256_lines(sorted(textbook_used)),
        },
        "vesum": _vesum_metadata(inputs.vesum_db),
        "ulifAspect": {
            "checkedVerbRows": len(ulif_aspect_rows),
            "checkedVerbRowsSha256": _sha256_lines("\x1f".join(map(str, row)) for row in ulif_aspect_rows),
        },
        "synonymVerdictsSha256": hashlib.sha256(inputs.synonym_verdicts.read_bytes()).hexdigest(),
    }
    return TeacherDeckBuild(deck, cloze, coverage, input_versions, public_lessons)


def _vesum_metadata(vesum_db: Path) -> dict[str, str]:
    conn = _ro_connect(vesum_db)
    try:
        return {str(row[0]): str(row[1]) for row in conn.execute("SELECT key, value FROM vesum_build_metadata")}
    except sqlite3.Error:
        return {}
    finally:
        conn.close()


def mode_counts(deck: dict[str, Any], cloze: dict[str, Any]) -> dict[str, Any]:
    entries = deck["entries"]
    per_entry_modes: dict[str, set[str]] = {str(entry["entryId"]): set() for entry in entries}
    for entry in entries:
        cards = entry["cards"]
        modes = per_entry_modes[str(entry["entryId"])]
        modes.add("recognition-flashcard")
        if cards["recognition"]["choice"]:
            modes.add("recognition-choice")
        if entry["matching"]:
            modes.add("matching")
        if cards["production"]:
            modes.add("production-flashcard")
            if cards["production"]["choice"]:
                modes.add("production-choice")
        if cards["cloze"]:
            modes.add("cloze")
        for ref in (cards["grammar"] or {}).get("items", []):
            modes.add(ref["mode"])
    names = [
        "recognition-flashcard",
        "recognition-choice",
        "matching",
        "production-flashcard",
        "production-choice",
        "cloze",
        *GRAMMAR_MODES,
    ]
    by_shape = {
        "single": [e for e in entries if not e["multiword"]],
        "multiword": [e for e in entries if e["multiword"]],
    }
    matrix = {
        name: {
            shape: sum(1 for entry in group if name in per_entry_modes[str(entry["entryId"])])
            for shape, group in by_shape.items()
        }
        for name in names
    }
    aspect: dict[str, dict[str, dict[str, int]]] = {}
    for shape, group in by_shape.items():
        table: dict[str, dict[str, int]] = {}
        for entry in group:
            if entry.get("aspect"):
                cell = table.setdefault(entry["aspect"]["basis"], {})
                cell[entry["aspect"]["value"]] = cell.get(entry["aspect"]["value"], 0) + 1
        aspect[shape] = {basis: dict(sorted(table[basis].items())) for basis in ASPECT_BASES if basis in table}
    return {
        "entries": len(entries),
        "singleWord": len(by_shape["single"]),
        "multiword": len(by_shape["multiword"]),
        "atlasJoined": sum(1 for entry in entries if entry["atlas"]),
        "withoutProduction": sum(1 for entry in entries if not entry["cards"]["production"]),
        "aspectPartnerEntries": sum(1 for entry in entries if entry.get("aspectPartners")),
        "verbAspect": aspect,
        "entriesByMode": matrix,
        "items": {
            "cloze": len(cloze["cloze"]),
            "clozeTeacherLesson": sum(1 for item in cloze["cloze"] if item["source"] == "teacher-lesson"),
            "clozeTextbook": sum(1 for item in cloze["cloze"] if item["source"] == "textbook"),
            **{mode: len(deck.get(mode, [])) for mode in ("stress", "paradigm", "classify", "synonym")},
        },
    }


# --------------------------------------------------------------------------- validation + rendering


def validate_teacher_deck(deck: dict[str, Any], cloze: dict[str, Any]) -> list[str]:
    """Generator-side structural gate (the independent checker repeats this separately)."""

    errors: list[str] = []
    entries = {str(entry["entryId"]): entry for entry in deck["entries"]}
    for entry_id, entry in entries.items():
        if not str(entry.get("en") or "").strip():
            errors.append(f"{entry_id}: no teacher English")
        for direction in ("recognition", "production"):
            card = entry["cards"][direction]
            choice = card and card["choice"]
            if not choice:
                continue
            labels = [str(option["label"]).casefold() for option in choice["options"]]
            answers = [option for option in choice["options"] if option["kind"] == "answer"]
            if len(answers) != 1 or answers[0]["entryId"] != entry_id or len(set(labels)) != len(labels):
                errors.append(f"{entry_id}: {direction} choice must have one answer among unique options")
            if str(choice["prompt"]).casefold() in labels:
                errors.append(f"{entry_id}: {direction} option equals prompt")
            ids = [option["entryId"] for option in choice["options"]]
            if any(b in entries[a]["conflicts"] for a in ids for b in ids if a != b):
                errors.append(f"{entry_id}: {direction} choice groups overlapping meanings")
        if entry["cards"]["production"] and entry["conflicts"]:
            errors.append(f"{entry_id}: production card despite overlapping meaning")
    for item in cloze["cloze"]:
        labels = [_canonical(str(option["label"])) for option in item["options"]]
        answers = [option for option in item["options"] if option["kind"] == "answer"]
        if item["sentence"].count(BLANK) != 1 or "____" in item["sentence"]:
            errors.append(f"{item['clozeId']}: sentence must contain exactly one blank")
        if (
            len(item["options"]) != 4
            or len(set(labels)) != 4
            or len(answers) != 1
            or answers[0]["label"] != item["form"]
        ):
            errors.append(f"{item['clozeId']}: cloze needs 4 unique options with the form as the one answer")
    return errors


def render_json(payload: dict[str, Any], *, list_keys: Sequence[str] = ()) -> bytes:
    """Deterministic JSON; the named top-level lists get one item per line for readable diffs."""

    if not list_keys:
        return (json.dumps(payload, ensure_ascii=False, indent=2) + "\n").encode("utf-8")
    lines = ["{"]
    keys = list(payload.keys())
    for index, key in enumerate(keys):
        comma = "," if index < len(keys) - 1 else ""
        value = payload[key]
        rendered_key = json.dumps(key, ensure_ascii=False)
        if key in list_keys and isinstance(value, list) and value:
            lines.append(f"  {rendered_key}: [")
            for item_index, item in enumerate(value):
                item_comma = "," if item_index < len(value) - 1 else ""
                lines.append("    " + json.dumps(item, ensure_ascii=False, separators=(",", ":")) + item_comma)
            lines.append(f"  ]{comma}")
        else:
            lines.append(f"  {rendered_key}: {json.dumps(value, ensure_ascii=False, separators=(',', ':'))}{comma}")
    lines.append("}")
    return ("\n".join(lines) + "\n").encode("utf-8")


def gzip_size(data: bytes) -> int:
    return len(gzip.compress(data, compresslevel=9, mtime=0))


BUDGETS = {DECK_FILE: TEACHER_DECK_GZIP_LIMIT, CLOZE_FILE: TEACHER_CLOZE_GZIP_LIMIT}


def render_published_set(
    build: TeacherDeckBuild,
    frozen_keys: dict[str, Any],
) -> dict[str, bytes]:
    """All files of the published set, including the manifest that pins them."""

    files = {
        DECK_FILE: render_json(build.deck, list_keys=("entries", "stress", "paradigm", "classify", "synonym")),
        CLOZE_FILE: render_json(build.cloze, list_keys=("cloze",)),
        COVERAGE_FILE: render_json(build.coverage),
        FROZEN_KEYS_FILE: render_json(frozen_keys, list_keys=("keys",)),
    }
    over = [
        f"{name}: gzip {gzip_size(files[name])} B > budget {limit} B"
        for name, limit in BUDGETS.items()
        if gzip_size(files[name]) > limit
    ]
    if over:
        raise TeacherDeckBuildError("teacher deck exceeds its delivery budget: " + "; ".join(over))
    schema_of = {
        DECK_FILE: SCHEMA,
        CLOZE_FILE: CLOZE_SCHEMA,
        COVERAGE_FILE: COVERAGE_SCHEMA,
        FROZEN_KEYS_FILE: str(frozen_keys["schema"]),
    }
    manifest = {
        "schema": MANIFEST_SCHEMA,
        "schemaVersion": SCHEMA_VERSION,
        "deckId": DECK_ID,
        "deckVersion": build.deck["deckVersion"],
        "docxSha256": frozen_keys["docxSha256"],
        "inputs": build.input_versions,
        "counts": build.deck["counts"],
        "files": [
            {
                "path": name,
                "schema": schema_of[name],
                "schemaVersion": SCHEMA_VERSION if name != FROZEN_KEYS_FILE else frozen_keys["schemaVersion"],
                "published": name in PUBLISHED_FILES,
                "bytes": len(data),
                "gzipBytes": gzip_size(data),
                "gzipBudget": BUDGETS.get(name),
                "sha256": hashlib.sha256(data).hexdigest(),
            }
            for name, data in files.items()
        ],
    }
    files[MANIFEST_FILE] = render_json(manifest)
    return files


# --------------------------------------------------------------------------- lesson-sentence risk report

REVIEW_FILE = "lesson-sentence-review.json"
REVIEW_SCHEMA = "teacher-lesson-sentence-review"
REVIEW_FLAGS = ("proper_noun_tokens", "vesum_unknown_tokens", "digits_or_contact")
PROPER_NAME_TAGS = frozenset({"prop", "fname", "lname", "pname"})  # VESUM: pname = patronymic
CONTACT_PATTERNS = (
    ("email", re.compile(r"[\w.+-]+@[\w-]+(?:\.[\w-]+)+")),
    ("url", re.compile(r"(?:https?://|www\.)\S+|\b[\w-]+\.(?:com|net|org|ua|info|io|me)\b", re.IGNORECASE)),
    ("phone", re.compile(r"\+?\d[\d\s().-]{5,}\d")),
    ("digits", re.compile(r"\d+")),
)


def _contact_hits(sentence: str) -> list[dict[str, str]]:
    hits: list[dict[str, str]] = []
    taken: list[tuple[int, int]] = []
    for kind, pattern in CONTACT_PATTERNS:
        for match in pattern.finditer(sentence):
            if any(start <= match.start() and match.end() <= end for start, end in taken):
                continue
            taken.append(match.span())
            hits.append({"kind": kind, "text": match.group()})
    return hits


def lesson_sentence_flags(sentence: str, analyzer: FormAnalyzer) -> dict[str, list[Any]]:
    """Deterministic privacy/language-review flags for one teacher-lesson sentence."""

    proper: list[dict[str, Any]] = []
    unknown: list[str] = []
    for index, match in enumerate(UK_TOKEN_RE.finditer(sentence)):
        token = match.group()
        rows = analyzer.analyses(token)
        reasons: list[str] = []
        if index > 0 and token[:1].isupper():
            reasons.append("capitalised-not-sentence-start")
        tags = sorted({part for row in rows for part in row["tags"].split(":") if part in PROPER_NAME_TAGS})
        reasons.extend(f"vesum:{tag}" for tag in tags)
        if reasons:
            proper.append({"token": token, "reasons": reasons})
        if not rows:
            unknown.append(token)
    return {"proper_noun_tokens": proper, "vesum_unknown_tokens": unknown, "digits_or_contact": _contact_hits(sentence)}


def lesson_sentence_review(build: TeacherDeckBuild, vesum_db: Path) -> dict[str, Any]:
    """Every teacher-lesson cloze sentence with its flags (local review artifact, never published)."""

    analyzer = FormAnalyzer(vesum_db)
    analyzer.prefetch(token for row in build.public_lesson_sentences for token in _tokens(row["sentence"]))
    by_id = {str(entry["entryId"]): entry for entry in build.deck["entries"]}
    sentences = []
    for row in build.public_lesson_sentences:
        flags = lesson_sentence_flags(row["sentence"], analyzer)
        sentences.append(
            {
                "clozeId": row["clozeId"],
                "entryId": row["entryId"],
                "entry": by_id[row["entryId"]]["uk"],
                "lessonDate": row["lesson"],
                "sentence": row["sentence"],
                "flags": flags,
            }
        )
    counts = {flag: sum(1 for row in sentences if row["flags"][flag]) for flag in REVIEW_FLAGS}
    return {
        "schema": REVIEW_SCHEMA,
        "schemaVersion": SCHEMA_VERSION,
        "deckVersion": build.deck["deckVersion"],
        "note": (
            "Local review artifact, never published. Lesson logs may hold the learner's own attempts: "
            "flags are deterministic hints for the language review and the privacy scan, nothing is removed."
        ),
        "counts": {"sentences": len(sentences), "flaggedSentences": counts},
        "sentences": sentences,
    }


def default_inputs() -> TeacherDeckInputs:
    return TeacherDeckInputs(
        atlas_db=PROJECT_ROOT / "data/atlas.db",
        sources_db=PROJECT_ROOT / "data/sources.db",
        vesum_db=PROJECT_ROOT / "data/vesum.db",
        synonym_verdicts=PROJECT_ROOT / "registry/lexicon/synonym_pair_verdicts.yaml",
    )
