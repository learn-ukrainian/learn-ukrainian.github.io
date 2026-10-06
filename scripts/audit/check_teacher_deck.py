#!/usr/bin/env python3
"""Independent structural checker for the built teacher-table deck (#8843).

This script deliberately re-implements every rule it checks (table extraction,
key normalisation, entry ids, the source-derived verb aspect from VESUM and
checked ULIF entries, the learner-facing English, the overlapping-English rule,
the Atlas join with its mechanical sense rule and identity conflicts, the
same-slot cloze distractor rule, the lesson-sentence fragment rules and the
review ledger) with the standard library and the shared SQLite reader boundary only.
The reader boundary supplies no checking or generation rules. It must never import the generator
(``scripts/lexicon/teacher_deck_shard.py``), the table sync, or the CEFR
exporter: a shared bug would otherwise pass its own check.
"""

from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import re
import sqlite3
import sys
import unicodedata
import xml.etree.ElementTree as ET
import zipfile
from collections import Counter
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from scripts.lib.readonly_sqlite import SQLiteConnection
from scripts.lib.readonly_sqlite import open_readonly as _open_readonly

WORD_NS = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"}
HEADING = "Combined Master Vocabulary Table (#3)"
DECK_FILE = "practice-deck.teacher.json"
CLOZE_FILE = "practice-cloze.teacher.json"
MANIFEST_FILE = "manifest.json"
FROZEN_FILE = "frozen-keys.json"
COVERAGE_FILE = "coverage.json"
DECK_SCHEMA = ("atlas-practice-teacher-deck", 1)
CLOZE_SCHEMA = ("atlas-practice-teacher-cloze", 1)
CARD_KINDS = ("recognition", "production", "cloze", "grammar")
GRAMMAR_ARRAYS = {"stress": "stressId", "paradigm": "paradigmId", "classify": "classifyId", "synonym": "synonymId"}
GRAMMAR_MODES = ("stress", "paradigm", "classify", "synonym", "antonym")
MAX_CLOZE = 3
UK_TOKEN = re.compile(r"[А-ЩЬЮЯЄІЇҐа-щьюяєіїґ]+(?:[ʼ'’-][А-ЩЬЮЯЄІЇҐа-щьюяєіїґ]+)*")
EN_TOKEN = re.compile(r"[\w'’-]+|/")
LATIN = re.compile(r"[A-Za-z]")
APOSTROPHES = str.maketrans({"’": "'", "ʼ": "'", "‘": "'", "`": "'", "´": "'", "′": "'"})
TEACHER_IMPF = re.compile(r"\((?:impf|imperf|ipf)\.?\)", re.IGNORECASE)
TEACHER_PERF = re.compile(r"\((?:perf|pf)\.?\)", re.IGNORECASE)
TEACHER_MARKER = re.compile(r"\s*\((?:impf|imperf|ipf|perf|pf)\.?\)", re.IGNORECASE)
ULIF_VERB_LABELS = {
    "дієслово недоконаного виду": "imperf",
    "дієслово доконаного виду": "perf",
    "дієслово недоконаного і доконаного виду": "dual",
}
EN_ASPECT_LABEL = {"imperf": "impf.", "perf": "pf.", "dual": "impf./pf."}
CLASSIFY_ANSWER = {"imperf": "imperfective", "perf": "perfective"}
# Words that never decide an Atlas sense match (function words, aspect markers).
SENSE_STOPWORDS = frozenset(
    [
        "a",
        "an",
        "the",
        "to",
        "of",
        "in",
        "on",
        "at",
        "for",
        "with",
        "by",
        "from",
        "into",
        "onto",
        "up",
        "down",
        "out",
        "off",
        "over",
        "about",
        "as",
        "and",
        "or",
        "not",
        "no",
        "be",
        "is",
        "are",
        "was",
        "were",
        "been",
        "being",
        "do",
        "does",
        "did",
        "have",
        "has",
        "had",
        "get",
        "it",
        "its",
        "one",
        "oneself",
        "someone",
        "somebody",
        "something",
        "sb",
        "sth",
        "smb",
        "smth",
        "self",
        "impf",
        "perf",
        "pf",
        "ipf",
        "imperf",
        "etc",
    ]
)
# School part-of-speech words for an Atlas ``pos`` label; a label naming exactly one is that part of speech.
POS_WORDS = {
    "noun": ("іменник", "noun", "abbreviation", "proper noun", "plural noun", "propn"),
    "adjective": ("прикметник", "adj", "adjective"),
    "numeral": ("числівник", "num", "numr", "numeral", "number"),
    "pronoun": ("займенник", "pronoun", "pron", "negative pronoun"),
    "verb": ("дієслово", "verb", "infinitive", "imperative"),
    "adverb": ("прислівник", "присл", "adv", "adverb"),
    "preposition": ("прийменник", "приймен.", "preposition", "prep"),
    "conjunction": ("сполучник", "спол.", "conjunction", "conj"),
    "particle": ("частка", "particle", "part"),
    "interjection": ("вигук", "interjection", "interj", "intj"),
}
# VESUM tag parts that fix a form's grammatical slot (case, number, gender, person, tense, …).
SLOT_TAG_PARTS = frozenset(
    [
        "m",
        "f",
        "n",
        "p",
        "s",
        "v_naz",
        "v_rod",
        "v_dav",
        "v_zna",
        "v_oru",
        "v_mis",
        "v_kly",
        "inf",
        "pres",
        "futr",
        "past",
        "impr",
        "1",
        "2",
        "3",
        "ranim",
        "rinanim",
        "compb",
        "compc",
        "comps",
    ]
)
LEDGER_SCHEMA = ("atlas-practice-teacher-withheld", 1)
LEDGER_CODES = frozenset({"ERR", "AMBIG", "FRAG", "PRIV"})
TASK_VERBS = [
    "Визначте",
    "Поясніть",
    "Запишіть",
    "Використайте",
    "Випишіть",
    "Перепишіть",
    "Складіть",
    "Вставте",
    "Заповніть",
    "Доповніть",
    "Підкресліть",
    "Утворіть",
    "Розставте",
    "Виправте",
    "Замініть",
    "Перекладіть",
    "Доберіть",
    "Позначте",
    "Продовжте",
    "Перекажіть",
    "Відредагуйте",
    "Розкрийте",
    "Об'єднайте",
    "Об’єднайте",
]
CUT_ABBREVIATIONS = ["ім", "див", "напр", "вул", "просп", "пров", "проф", "акад", "св", "м", "с", "т", "чол", "жін"]
LETTER = r"[^\W\d_]"
FRAGMENT_SHAPES = (
    ("outline arrow", re.compile("→")),
    ("slash alternative", re.compile(LETTER + r" ?/ ?" + LETTER)),
    (
        "parenthesised number or gloss",
        re.compile(r"\([^()]*\d[^()]*\)|\( *[a-zа-щьюяєіїґ][a-zа-щьюяєіїґ'’ʼ -]*\)|\((?![^()]*\))"),
    ),
    ("copied citation marker", re.compile(r"\[\d+\]")),
    ("leading section label", re.compile("^" + LETTER + r"[\w'’ʼ-]*(?: +[\w'’ʼ-]+){0,2}:(?: |$)")),
    ("worksheet task", re.compile(r"^(?:\d+[.)] *)?(?:" + "|".join(TASK_VERBS) + r")(?![\w'’ʼ-])")),
    ("truncated abbreviation", re.compile(r"(?:^|[ (])(?:" + "|".join(CUT_ABBREVIATIONS) + r")\.$", re.IGNORECASE)),
)


# ----------------------------------------------------------------------------- own rules


def norm_key(value: str) -> str:
    text = unicodedata.normalize("NFD", value)
    text = "".join(char for char in text if char not in {"́", "̀"})
    text = unicodedata.normalize("NFC", text).translate(APOSTROPHES)
    return " ".join(text.split()).casefold()


def expected_entry_id(key: str) -> str:
    return "tt-" + hashlib.sha256(key.encode("utf-8")).hexdigest()[:12]


def meaning_parts(english: str) -> list[tuple[str, ...]]:
    parts = []
    for raw in re.split(r"[;,]", english):
        text = re.sub(r"\([^)]*\)", " ", raw)
        text = text.replace("(", " ").replace(")", " ").lower()
        text = " ".join(text.split())
        if text.startswith("to "):
            text = text[3:]
        text = " ".join(word for word in text.split() if word not in {"a", "an", "the"}).strip(" .!?:;\"'")
        if text:
            parts.append(tuple(EN_TOKEN.findall(text)))
    return parts


def _inside(outer: tuple[str, ...], inner: tuple[str, ...]) -> bool:
    size = len(inner)
    return 0 < size <= len(outer) and any(outer[i : i + size] == inner for i in range(len(outer) - size + 1))


def meanings_overlap(left: list[tuple[str, ...]], right: list[tuple[str, ...]]) -> bool:
    return any(a == b or _inside(a, b) or _inside(b, a) for a in left for b in right)


def own_overlaps(
    entries: list[dict[str, Any]], aspects: dict[str, str | None]
) -> tuple[dict[str, set[str]], dict[str, set[str]]]:
    """(overlaps, aspect partners): an overlapping pair with identical normalised English
    and source-derived aspects imperf vs perf is a partner pair, not an overlap."""

    parts = {entry["entryId"]: meaning_parts(entry["en"]) for entry in entries}
    ids = sorted(parts)
    result: dict[str, set[str]] = {entry_id: set() for entry_id in ids}
    partners: dict[str, set[str]] = {entry_id: set() for entry_id in ids}
    for index, left in enumerate(ids):
        for right in ids[index + 1 :]:
            if meanings_overlap(parts[left], parts[right]):
                split = {aspects.get(left), aspects.get(right)} == {"imperf", "perf"} and set(parts[left]) == set(
                    parts[right]
                )
                bucket = partners if split else result
                bucket[left].add(right)
                bucket[right].add(left)
    return result, partners


# ----------------------------------------------------------------------------- own aspect rule


class AspectLookup:
    """Own read-only lemma lookup: VESUM ``forms_all`` tags and checked ULIF labels."""

    def __init__(self, vesum: SQLiteConnection, sources: SQLiteConnection) -> None:
        self.vesum = vesum
        self.sources = sources
        self.cache: dict[str, tuple[set[str], bool, set[str], bool]] = {}

    def lemma(self, word: str) -> tuple[set[str], bool, set[str], bool]:
        if word not in self.cache:
            v_aspects: set[str] = set()
            v_other = False
            for pos, tags in self.vesum.execute("SELECT pos, tags FROM forms_all WHERE lemma = ?", (word,)):
                if pos == "verb":
                    v_aspects |= {part for part in tags.split(":") if part in ("imperf", "perf")}
                else:
                    v_other = True
            u_aspects: set[str] = set()
            u_other = False
            for (label,) in self.sources.execute(
                "SELECT grammatical_label FROM ulif_dictua_entries WHERE normalized_query = ? AND homonym_checked = 1 "
                "AND status = 'ok'",
                (word,),
            ):
                if label in ULIF_VERB_LABELS:
                    u_aspects.add(ULIF_VERB_LABELS[label])
                elif label:
                    u_other = True
            self.cache[word] = (v_aspects, v_other, u_aspects, u_other)
        return self.cache[word]


def teacher_markers(english: str) -> set[str]:
    found = set()
    if TEACHER_IMPF.search(english):
        found.add("imperf")
    if TEACHER_PERF.search(english):
        found.add("perf")
    return found


def teacher_says_verb(english: str) -> bool:
    pieces = [piece.strip().lower() for piece in re.split(r"[;,]", english) if piece.strip()]
    return bool(teacher_markers(english)) or (bool(pieces) and all(piece.startswith("to ") for piece in pieces))


def decide_aspect(vesum: set[str], ulif: set[str]) -> tuple[str, str]:
    """VESUM gives a biaspectual verb as two lemmas, like two homographs; ULIF's dual label decides."""

    def one(values: set[str]) -> str | None:
        return None if not values else (min(values) if len(values) == 1 else "both")

    v, u = one(vesum), one(ulif)
    if v is not None and u is not None:
        if v == u and v != "both":
            return v, "agree"
        if (v, u) == ("both", "dual"):
            return "dual", "agree"
        return ("unknown", "homograph") if (v, u) == ("both", "both") else ("unknown", "conflict")
    if v is not None:
        return ("unknown" if v == "both" else v), "vesum-only"
    if u is not None:
        return ("unknown" if u == "both" else u), "ulif-only"
    return "unknown", "none"


def own_aspect(entry: dict[str, Any], lookup: AspectLookup) -> dict[str, Any] | None:
    english = str(entry.get("teacherEn") or "")
    says_verb = teacher_says_verb(english)
    words = [norm_key(token) for token in UK_TOKEN.findall(entry["key"])] if entry["multiword"] else [entry["key"]]
    head = None
    for word in words:
        v_aspects, v_other, u_aspects, u_other = lookup.lemma(word)
        if (v_aspects or u_aspects) and (says_verb or not (v_other or u_other)):
            head = word
            break
    if head is None:
        if not says_verb:
            return None
        # A verb meaning that no source attests as a verb (even if it is a noun there): unknown.
        value, basis, v_aspects, u_aspects = "unknown", "none", set(), set()
    else:
        v_aspects, _v_other, u_aspects, _u_other = lookup.lemma(head)
        value, basis = decide_aspect(v_aspects, u_aspects)
    markers = teacher_markers(english)
    agrees = None
    if markers and value in ("imperf", "perf"):
        agrees = markers == {value}
    elif markers and value == "dual":
        agrees = True
    return {
        "value": value,
        "basis": basis,
        "lemma": head,
        "vesum": sorted(v_aspects),
        "ulif": sorted(u_aspects),
        "teacherMarker": "+".join(sorted(markers)) or None,
        "markerAgrees": agrees,
    }


def own_display(teacher_en: str, value: str | None) -> str:
    text = teacher_en
    if TEACHER_MARKER.search(teacher_en):
        kept: list[str] = []
        for piece in TEACHER_MARKER.sub("", teacher_en).split(";"):
            piece = " ".join(piece.split())
            if piece and piece.lower() not in [k.lower() for k in kept]:
                kept.append(piece)
        text = "; ".join(kept)
    return f"{text} ({EN_ASPECT_LABEL[value]})" if value in EN_ASPECT_LABEL else text


def sentence_digest(sentence: str) -> str:
    return hashlib.sha256(" ".join(unicodedata.normalize("NFC", sentence).split()).encode("utf-8")).hexdigest()


def fragment_shape(sentence: str) -> str | None:
    return next((name for name, pattern in FRAGMENT_SHAPES if pattern.search(sentence)), None)


def content_words(english: str) -> set[str]:
    return {token for part in meaning_parts(english) for token in part if token != "/" and token not in SENSE_STOPWORDS}


def own_sense(english: str, senses: list[str]) -> tuple[str, int | None]:
    """Single sense usable; several senses need exactly one sharing a content word."""

    if not senses:
        return "no-sense", None
    if len(senses) == 1:
        return "single-sense", 0
    words = content_words(english)
    hits = [index for index, sense in enumerate(senses) if words & content_words(sense)]
    if len(hits) == 1:
        return "unique-match", hits[0]
    return ("ambiguous" if hits else "no-match"), None


def pos_word(pos: Any) -> str:
    text = pos.strip().casefold() if isinstance(pos, str) else ""
    found: list[str] = []
    for part in re.split(r"\s*[,;/|+]\s*", text):
        for name, words in POS_WORDS.items():
            hit = any(
                part == w or part.startswith((f"{w}:", f"{w}.")) or (w != "part" and part.startswith(f"{w} "))
                for w in words
            )
            if hit and name not in found:
                found.append(name)
    if len(found) == 1:
        return found[0]
    return "phrase" if text == "phrase" else ""


def slot(tags: str) -> tuple[str, ...]:
    parts = tags.split(":")
    return (parts[0], *sorted(part for part in parts[1:] if part in SLOT_TAG_PARTS))


def atlas_articles(atlas: SQLiteConnection) -> dict[str, list[dict[str, Any]]]:
    grouped: dict[str, list[dict[str, Any]]] = {}
    for (raw,) in atlas.execute(
        "SELECT payload_json FROM article_payloads WHERE is_public_route = 1 ORDER BY route_order"
    ):
        payload = json.loads(raw)
        if isinstance(payload, dict) and isinstance(payload.get("lemma"), str):
            grouped.setdefault(norm_key(payload["lemma"]), []).append(payload)
    return grouped


def article_senses(article: dict[str, Any]) -> list[str]:
    english = ((article.get("enrichment") or {}).get("translation") or {}).get("en")
    if isinstance(english, str):
        english = [english]
    if not isinstance(english, list):
        return []
    return [" ".join(item.split()) for item in english if isinstance(item, str) and item.strip()]


def load_ledger(path: Path, report: Report) -> tuple[dict[str, str], set[str]]:
    """Withheld sentence digests -> code, and kept digests; the ledger must carry hashes, never text."""

    payload = json.loads(path.read_text(encoding="utf-8"))
    if (payload.get("schema"), payload.get("schemaVersion")) != LEDGER_SCHEMA:
        report.fail("review ledger schema/version mismatch")
    withheld: dict[str, str] = {}
    for row in payload.get("withheld", []):
        if set(row) != {"sentenceSha256", "code", "reviewer", "reviewedAt"} or row.get("code") not in LEDGER_CODES:
            report.fail(f"review ledger: malformed withheld record {sorted(row)}")
            continue
        withheld[str(row["sentenceSha256"])] = str(row["code"])
    kept = set()
    for row in payload.get("kept", []):
        if set(row) != {"sentenceSha256", "reviewer", "reviewedAt"}:
            report.fail(f"review ledger: malformed kept record {sorted(row)}")
            continue
        kept.add(str(row["sentenceSha256"]))
    if any(not re.fullmatch(r"[0-9a-f]{64}", digest) for digest in (*withheld, *kept)):
        report.fail("review ledger: a record is not a SHA-256 digest")
    if kept & set(withheld):
        report.fail("review ledger: a sentence is both kept and withheld")
    return withheld, kept


def extract_table(docx: Path, heading: str) -> tuple[str, list[tuple[int, str, str]]]:
    """Own extraction: (row number, Ukrainian, English) for every data row after *heading*."""

    data = docx.read_bytes()
    with zipfile.ZipFile(docx) as archive:
        root = ET.fromstring(archive.read("word/document.xml"))
    body = root.find("w:body", WORD_NS)
    if body is None:
        raise ValueError("DOCX has no body")

    def text_of(node: ET.Element) -> str:
        return "".join(t.text or "" for t in node.iter(f"{{{WORD_NS['w']}}}t"))

    children = list(body)
    start = next(
        (i for i, child in enumerate(children) if child.tag.endswith("}p") and text_of(child) == heading), None
    )
    if start is None:
        raise ValueError(f"heading not found: {heading!r}")
    table = next((child for child in children[start + 1 :] if child.tag.endswith("}tbl")), None)
    if table is None:
        raise ValueError("no table after heading")
    rows = []
    for tr in table.findall("w:tr", WORD_NS):
        cells = []
        for tc in tr.findall("w:tc", WORD_NS):
            paragraphs = [" ".join(text_of(p).split()) for p in tc.findall("w:p", WORD_NS)]
            cells.append(" ".join(" ".join(p for p in paragraphs if p).split()))
        rows.append(cells)
    header = [cell.casefold() for cell in rows[0]]
    en_col = header.index("english")
    uk_col = header.index("ukrainian") if "ukrainian" in header else header.index("current")
    out = []
    for number, cells in enumerate(rows[1:], start=1):
        uk = cells[uk_col] if uk_col < len(cells) else ""
        en = cells[en_col] if en_col < len(cells) else ""
        out.append((number, uk, en))
    return hashlib.sha256(data).hexdigest(), out


# ----------------------------------------------------------------------------- checker


class Report:
    def __init__(self) -> None:
        self.errors: list[str] = []

    def fail(self, message: str) -> None:
        self.errors.append(message)


def _load(path: Path, report: Report) -> dict[str, Any] | None:
    if not path.exists():
        report.fail(f"missing artifact: {path.name}")
        return None
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        report.fail(f"unreadable artifact {path.name}: {exc}")
        return None
    return payload if isinstance(payload, dict) else None


def check_manifest(deck_dir: Path, manifest: dict[str, Any], report: Report) -> None:
    for record in manifest.get("files", []):
        path = deck_dir / str(record.get("path"))
        if not path.exists():
            report.fail(f"manifest file missing: {record.get('path')}")
            continue
        data = path.read_bytes()
        if hashlib.sha256(data).hexdigest() != record.get("sha256") or len(data) != record.get("bytes"):
            report.fail(f"manifest hash/size mismatch: {record.get('path')}")
        payload = json.loads(data)
        if payload.get("schema") != record.get("schema") or payload.get("schemaVersion") != record.get("schemaVersion"):
            report.fail(f"manifest schema mismatch: {record.get('path')}")
        budget = record.get("gzipBudget")
        compressed = len(gzip.compress(data, compresslevel=9, mtime=0))
        if isinstance(budget, int) and compressed > budget:
            report.fail(f"{record.get('path')}: gzip {compressed} B exceeds budget {budget} B")
    names = {record.get("path") for record in manifest.get("files", [])}
    for required in (DECK_FILE, CLOZE_FILE, FROZEN_FILE):
        if required not in names:
            report.fail(f"manifest does not reference {required}")


def check_source_table(
    deck: dict[str, Any], frozen: dict[str, Any], table: tuple[str, list[tuple[int, str, str]]], report: Report
) -> dict[str, Any]:
    docx_sha, rows = table
    if frozen.get("docxSha256") != docx_sha:
        report.fail("frozen key list was recorded for a different DOCX")
    source_keys = list(dict.fromkeys(uk for _n, uk, _en in rows if uk))
    if frozen.get("keys") != source_keys:
        report.fail("frozen key list differs from the independent table extraction")
    groups: dict[str, list[tuple[int, str, str]]] = {}
    for row in rows:
        if row[1]:
            groups.setdefault(norm_key(row[1]), []).append(row)
    by_key = {entry["key"]: entry for entry in deck["entries"]}
    if set(by_key) != set(groups):
        missing = sorted(set(groups) - set(by_key))[:5]
        extra = sorted(set(by_key) - set(groups))[:5]
        report.fail(f"deck keys differ from the table (missing {missing}, extra {extra})")
    merges = []
    for key, group in groups.items():
        entry = by_key.get(key)
        if entry is None:
            continue
        meanings: list[str] = []
        for _n, _uk, en in group:
            if en and en.casefold() not in {m.casefold() for m in meanings}:
                meanings.append(en)
        if entry.get("teacherEn") != "; ".join(meanings):
            report.fail(
                f"{entry['entryId']}: teacher English {entry.get('teacherEn')!r} != table meanings {meanings!r}"
            )
        if entry["sourceRows"] != [n for n, _uk, _en in group]:
            report.fail(f"{entry['entryId']}: source rows differ from the table")
        if entry["uk"] != group[0][1]:
            report.fail(f"{entry['entryId']}: Ukrainian {entry['uk']!r} is not the earliest row's spelling")
        if len(group) > 1:
            merges.append(
                {"uk": entry["uk"], "rows": [n for n, _u, _e in group], "differentEnglish": len(meanings) > 1}
            )
    return {"rows": len(rows), "sourceKeys": len(source_keys), "merges": merges}


def check_aspects(
    deck: dict[str, Any], lookup: AspectLookup | None, report: Report
) -> dict[str, dict[str, Any] | None]:
    """Own source-derived aspect per entry (or the declared one when no databases were
    given), checked against the deck's ``aspect`` record and learner-facing ``en``."""

    aspects: dict[str, dict[str, Any] | None] = {}
    for entry in deck["entries"]:
        declared = entry.get("aspect")
        expected = own_aspect(entry, lookup) if lookup is not None else declared
        aspects[entry["entryId"]] = expected
        if lookup is not None and declared != expected:
            report.fail(f"{entry['entryId']}: aspect {declared!r} != sources {expected!r}")
        value = (expected or {}).get("value")
        if entry.get("en") != own_display(str(entry.get("teacherEn") or ""), value):
            report.fail(
                f"{entry['entryId']}: English {entry.get('en')!r} is not the teacher's English with markers "
                f"replaced by the source aspect ({value})"
            )
    return aspects


def check_atlas(
    deck: dict[str, Any],
    coverage: dict[str, Any] | None,
    articles: dict[str, list[dict[str, Any]]],
    aspects: dict[str, dict[str, Any] | None],
    report: Report,
) -> dict[str, tuple[str, int | None]]:
    """Own Atlas join: article per key, identity conflicts, and the mechanical sense rule.
    Returns entry id -> (sense rule, sense index) for entries joined to an article."""

    senses: dict[str, tuple[str, int | None]] = {}
    conflicts: dict[str, str] = {}
    for entry in deck["entries"]:
        entry_id = entry["entryId"]
        found = articles.get(entry["key"], [])
        declared = entry.get("atlas")
        if len(found) > 1:
            conflicts[entry_id] = "homograph:"
        elif found and not entry["multiword"]:
            aspect = aspects.get(entry_id)
            bucket = pos_word(found[0].get("pos"))
            if aspect is not None and aspect.get("lemma") and bucket and bucket != "verb":
                conflicts[entry_id] = "part of speech: VESUM/ULIF"
        if not found or len(found) > 1:
            if declared is not None:
                report.fail(
                    f"{entry_id}: joined to Atlas {declared.get('slug')!r} but the key names {len(found)} articles"
                )
            continue
        article = found[0]
        rule, index = own_sense(str(entry.get("en") or ""), article_senses(article))
        senses[entry_id] = (rule, index)
        if declared is None:
            report.fail(f"{entry_id}: not joined although the Atlas has one article {article.get('url_slug')!r}")
            continue
        if declared.get("slug") != article.get("url_slug") or declared.get("pos") != article.get("pos"):
            report.fail(f"{entry_id}: Atlas join {declared.get('slug')!r} is not the key's article")
        if (declared.get("senseRule"), declared.get("senseIndex")) != (rule, index):
            report.fail(
                f"{entry_id}: Atlas sense {declared.get('senseRule')}/{declared.get('senseIndex')} "
                f"!= mechanical rule {rule}/{index}"
            )
        if bool(declared.get("identityConflict")) != (entry_id in conflicts):
            report.fail(
                f"{entry_id}: identityConflict {declared.get('identityConflict')} differs from the Atlas/sources"
            )
    listed = {
        row.get("entryId"): str(row.get("reason", ""))
        for row in ((coverage or {}).get("residuals") or {}).get("identityConflicts", [])
    }
    if set(listed) != set(conflicts):
        report.fail(
            f"identity conflicts differ from the Atlas/sources (listed only {sorted(set(listed) - set(conflicts))[:3]}, "
            f"missing {sorted(set(conflicts) - set(listed))[:3]})"
        )
    for entry_id, prefix in conflicts.items():
        if entry_id in listed and not listed[entry_id].startswith(prefix):
            report.fail(f"{entry_id}: identity conflict reason {listed[entry_id]!r} is not {prefix!r}")
    return senses


def check_entries(
    deck: dict[str, Any],
    frozen: dict[str, Any],
    overlaps: dict[str, set[str]],
    partners: dict[str, set[str]],
    report: Report,
) -> None:
    entries = deck["entries"]
    by_id = {entry["entryId"]: entry for entry in entries}
    if len(by_id) != len(entries):
        report.fail("duplicate entry ids")
    covered: Counter[str] = Counter()
    first_seen = [entry.get("firstSeen") for entry in entries]
    if not all(isinstance(value, int) for value in first_seen) or len(set(first_seen)) != len(first_seen):
        report.fail("firstSeen order keys must be unique integers")
    for entry in entries:
        entry_id = entry["entryId"]
        key = norm_key(entry["uk"])
        if entry["key"] != key or entry_id != expected_entry_id(key):
            report.fail(f"{entry_id}: id/key not derived from the normalised Ukrainian key")
        for source_key in entry["sourceKeys"]:
            covered[source_key] += 1
            if norm_key(source_key) != key:
                report.fail(f"{entry_id}: source key {source_key!r} normalises elsewhere")
        english = str(entry.get("en") or "")
        if not english or not LATIN.search(english) or english.casefold() == entry["uk"].casefold():
            report.fail(f"{entry_id}: recognition meaning is not the teacher's English")
        cards = entry.get("cards", {})
        for kind in CARD_KINDS:
            card = cards.get(kind)
            if card is not None and card.get("cardId") != f"{entry_id}:{kind}":
                report.fail(f"{entry_id}: {kind} card id must be {entry_id}:{kind}")
        if cards.get("recognition") is None:
            report.fail(f"{entry_id}: missing recognition card")
        if set(entry.get("conflicts", [])) != overlaps.get(entry_id, set()):
            report.fail(f"{entry_id}: conflicts list differs from the overlapping-English rule")
        if set(entry.get("aspectPartners", [])) != partners.get(entry_id, set()):
            report.fail(f"{entry_id}: aspect partners differ from the source-aspect rule")
        if cards.get("production") is not None and overlaps.get(entry_id):
            report.fail(
                f"{entry_id}: EN->UK production card although its English overlaps {sorted(overlaps[entry_id])[:3]}"
            )
        if cards.get("production") is None and not overlaps.get(entry_id):
            report.fail(f"{entry_id}: unique English meaning but no EN->UK production card")
        for direction, prompt_field, answer_field in (("recognition", "uk", "en"), ("production", "en", "uk")):
            choice = (cards.get(direction) or {}).get("choice")
            if choice:
                check_choice(entry, choice, direction, prompt_field, answer_field, by_id, overlaps, report)
        no_grammar = entry["multiword"] or not entry.get("atlas") or entry["atlas"].get("identityConflict")
        if no_grammar and cards.get("grammar") is not None:
            report.fail(f"{entry_id}: grammar card without an unconflicted single-word Atlas article")
    frozen_keys = frozen.get("keys", [])
    for source_key in frozen_keys:
        if covered[source_key] != 1:
            report.fail(f"frozen key {source_key!r} covered by {covered[source_key]} entries")
    if set(covered) - set(frozen_keys):
        report.fail("deck carries source keys that are not in the frozen key list")


def check_choice(
    entry: dict[str, Any],
    choice: dict[str, Any],
    direction: str,
    prompt_field: str,
    answer_field: str,
    by_id: dict[str, dict[str, Any]],
    overlaps: dict[str, set[str]],
    report: Report,
) -> None:
    entry_id = entry["entryId"]
    options = choice.get("options", [])
    labels = [str(option.get("label", "")).casefold() for option in options]
    answers = [option for option in options if option.get("kind") == "answer"]
    if choice.get("prompt") != entry[prompt_field]:
        report.fail(f"{entry_id}: {direction} choice prompt is not the entry's {prompt_field}")
    if len(options) != 4 or len(set(labels)) != 4:
        report.fail(f"{entry_id}: {direction} choice needs 4 unique options")
    if len(answers) != 1 or answers[0].get("entryId") != entry_id or answers[0].get("label") != entry[answer_field]:
        report.fail(f"{entry_id}: {direction} choice must contain its answer exactly once")
    if str(choice.get("prompt", "")).casefold() in labels:
        report.fail(f"{entry_id}: {direction} option equals the prompt")
    ids = [option.get("entryId") for option in options]
    for option in options:
        other = by_id.get(option.get("entryId"))
        if other is None or option.get("label") != other[answer_field]:
            report.fail(f"{entry_id}: {direction} option label does not come from its entry")
    if any(b in overlaps.get(a, set()) for a in ids for b in ids if a != b):
        report.fail(f"{entry_id}: {direction} choice groups entries whose meanings overlap")


def check_cloze(
    deck: dict[str, Any],
    cloze: dict[str, Any],
    overlaps: dict[str, set[str]],
    partners: dict[str, set[str]],
    report: Report,
    vesum: SQLiteConnection | None,
    sources: SQLiteConnection | None,
    senses: dict[str, tuple[str, int | None]] | None = None,
    withheld: dict[str, str] | None = None,
    kept: set[str] | None = None,
) -> dict[str, Any]:
    """Check every cloze item; with *kept* (publication mode) every served teacher-lesson
    sentence must also have a kept review record."""

    by_id = {entry["entryId"]: entry for entry in deck["entries"]}
    per_entry: dict[str, list[dict[str, Any]]] = {}
    seen_ids: set[str] = set()
    lesson_texts = _lesson_texts(sources) if sources is not None else {}
    lesson_digests: set[str] = set()
    for item in cloze.get("cloze", []):
        cloze_id = item.get("clozeId")
        entry = by_id.get(item.get("entryId"))
        if entry is None:
            report.fail(f"{cloze_id}: unknown entry")
            continue
        if cloze_id in seen_ids:
            report.fail(f"{cloze_id}: duplicate cloze id")
        seen_ids.add(cloze_id)
        per_entry.setdefault(entry["entryId"], []).append(item)
        if item.get("cardId") != f"{entry['entryId']}:cloze":
            report.fail(f"{cloze_id}: card id must be <entryId>:cloze")
        sentence = str(item.get("sentence", ""))
        if sentence.count("___") != 1 or "____" in sentence:
            report.fail(f"{cloze_id}: sentence must contain exactly one ___ blank")
        options = item.get("options", [])
        labels = [norm_key(str(option.get("label", ""))) for option in options]
        answers = [option for option in options if option.get("kind") == "answer"]
        if len(options) != 4 or len(set(labels)) != 4:
            report.fail(f"{cloze_id}: needs 4 unique options")
        if len(answers) != 1 or answers[0].get("label") != item.get("form"):
            report.fail(f"{cloze_id}: the blank's form must be the one answer among the options")
        if norm_key(sentence) in labels:
            report.fail(f"{cloze_id}: an option equals the prompt")
        for option in options:
            if option.get("kind") == "answer":
                continue
            other_id = option.get("entryId")
            same_meaning = overlaps.get(entry["entryId"], set()) | partners.get(entry["entryId"], set())
            if other_id == entry["entryId"] or other_id in same_meaning:
                report.fail(f"{cloze_id}: distractor {option.get('label')!r} shares the answer's meaning")
            if other_id not in by_id:
                report.fail(f"{cloze_id}: distractor is not a deck entry")
        form = str(item.get("form", ""))
        restored = sentence.replace("___", form, 1)
        digest = sentence_digest(restored)
        if withheld is not None and digest in withheld:
            report.fail(f"{cloze_id}: serves a sentence the language review withheld ({withheld[digest]})")
        if item.get("source") == "teacher-lesson":
            lesson_digests.add(digest)
            if kept is not None and digest not in kept and digest not in (withheld or {}):
                report.fail(f"{cloze_id}: serves a teacher-lesson sentence with no language-review record")
            shape = fragment_shape(restored)
            if shape:
                report.fail(f"{cloze_id}: teacher-lesson sentence is worksheet debris ({shape})")
        distractor_entries = [by_id.get(o.get("entryId")) for o in options if o.get("kind") != "answer"]
        if entry["multiword"]:
            key_tokens = [norm_key(t) for t in UK_TOKEN.findall(entry["key"])]
            if " ".join(key_tokens) != entry["key"] or [norm_key(t) for t in UK_TOKEN.findall(form)] != key_tokens:
                report.fail(f"{cloze_id}: multiword cloze without the whole phrase verbatim")
            if any(other is not None and not other["multiword"] for other in distractor_entries):
                report.fail(f"{cloze_id}: a single-word distractor in a phrase cloze")
        elif vesum is not None:
            rows = [
                (norm_key(lemma), tags)
                for variant in {
                    form,
                    form.casefold(),
                    form.translate(APOSTROPHES),
                    form.translate(APOSTROPHES).casefold(),
                }
                for lemma, tags in vesum.execute("SELECT lemma, tags FROM forms WHERE word_form = ?", (variant,))
            ]
            if {lemma for lemma, _tags in rows} != {entry["key"]}:
                report.fail(f"{cloze_id}: blank form {form!r} is not an unambiguous VESUM form of {entry['key']!r}")
            check_slots(item, {slot(tags) for _lemma, tags in rows}, by_id, vesum, report)
        if senses is not None and entry.get("atlas"):
            rule, index = senses.get(entry["entryId"], ("", None))
            if item.get("source") == "textbook" and index is None:
                report.fail(f"{cloze_id}: textbook sentence although the Atlas sense rule is {rule or 'unresolved'}")
            if (item.get("atlasSense") or {}).get("senseIndex") != index:
                report.fail(f"{cloze_id}: atlasSense index differs from the mechanical sense rule ({index})")
        if sources is not None and not _sentence_in_source(sources, item, restored, lesson_texts):
            report.fail(f"{cloze_id}: restored sentence not found verbatim in its source")
    for entry_id, items in per_entry.items():
        if len(items) > MAX_CLOZE:
            report.fail(f"{entry_id}: more than {MAX_CLOZE} cloze sentences")
        kinds = [item.get("source") for item in items]
        if "textbook" in kinds and "teacher-lesson" in kinds[kinds.index("textbook") :]:
            report.fail(f"{entry_id}: teacher-lesson sentences must come before textbook sentences")
        card = by_id[entry_id]["cards"].get("cloze") or {}
        if card.get("clozeIds") != [item["clozeId"] for item in items]:
            report.fail(f"{entry_id}: cloze card ids differ from its cloze items")
    for entry_id, entry in by_id.items():
        if entry["cards"].get("cloze") and entry_id not in per_entry:
            report.fail(f"{entry_id}: cloze card without cloze items")
    lesson_items = [item for item in cloze.get("cloze", []) if item.get("source") == "teacher-lesson"]
    return {"lessonItems": len(lesson_items), "lessonSentences": len(lesson_digests)}


def check_slots(
    item: dict[str, Any],
    wanted: set[tuple[str, ...]],
    by_id: dict[str, dict[str, Any]],
    vesum: SQLiteConnection,
    report: Report,
) -> None:
    """Same-slot rule: a single-word distractor is a form of its own single-word entry that
    fills every grammatical slot the blank's form fills, and is not a form of the answer."""

    answer_key = by_id[item["entryId"]]["key"]
    answer_forms = {answer_key} | {
        norm_key(row[0]) for row in vesum.execute("SELECT word_form FROM forms WHERE lemma = ?", (answer_key,))
    }
    for option in item.get("options", []):
        if option.get("kind") == "answer":
            continue
        other = by_id.get(option.get("entryId"))
        if other is None:
            continue
        label = str(option.get("label", ""))
        if other["multiword"]:
            report.fail(f"{item.get('clozeId')}: phrase distractor {label!r} in a single-word cloze")
            continue
        surfaces = {label, label[:1].lower() + label[1:]}
        slots = {
            slot(tags)
            for word_form, tags in vesum.execute("SELECT word_form, tags FROM forms WHERE lemma = ?", (other["key"],))
            if word_form in surfaces
        }
        if not slots or not wanted <= slots:
            report.fail(
                f"{item.get('clozeId')}: distractor {label!r} does not fill the blank's grammatical slot "
                f"as a form of {other['key']!r}"
            )
        if norm_key(label) in answer_forms:
            report.fail(f"{item.get('clozeId')}: distractor {label!r} is a form of the answer's lemma")


def _lesson_texts(sources: SQLiteConnection) -> dict[str, list[str]]:
    texts: dict[str, list[str]] = {}
    for (text,) in sources.execute("SELECT text FROM textbooks WHERE source_file = 'private-teacher-lessons-a'"):
        first = text.split("\n", 1)[0]
        match = re.match(r"^(\d{2})[./](\d{2})[./](\d{4})", first)
        if match:
            day, month, year = match.groups()
            texts.setdefault(f"{year}-{month}-{day}", []).append(" ".join(text.split()))
    return texts


def _dehyphenate(text: str) -> str:
    return " ".join(re.sub(r"(?<=[А-ЩЬЮЯЄІЇҐа-щьюяєіїґ])-\s+(?=[А-ЩЬЮЯЄІЇҐа-щьюяєіїґ])", "", text).split())


def _sentence_in_source(
    sources: SQLiteConnection, item: dict[str, Any], restored: str, lesson_texts: dict[str, list[str]]
) -> bool:
    locator = (item.get("attribution") or {}).get("locator")
    if item.get("source") == "teacher-lesson":
        return any(restored in text for text in lesson_texts.get(str(locator), []))
    row = sources.execute("SELECT text FROM textbooks WHERE chunk_id = ?", (locator,)).fetchone()
    return bool(row) and restored in _dehyphenate(row[0])


def check_grammar(
    deck: dict[str, Any], aspects: dict[str, dict[str, Any] | None], coverage: dict[str, Any] | None, report: Report
) -> None:
    for item in deck.get("classify", []):
        value = (aspects.get(item.get("entryId")) or {}).get("value")
        for one in item.get("sets", []):
            if one.get("setId") == "aspect" and one.get("answer") != CLASSIFY_ANSWER.get(value):
                report.fail(
                    f"{item.get('classifyId')}: aspect answer {one.get('answer')!r} but the sources say {value}"
                )
    for row in ((coverage or {}).get("residuals") or {}).get("identityConflicts", []):
        if not str(row.get("reason", "")).startswith(("homograph:", "part of speech: VESUM/ULIF")):
            report.fail(
                f"{row.get('entryId')}: identity conflict not grounded in the Atlas/sources: {row.get('reason')!r}"
            )
    items_by_id: dict[str, dict[str, Any]] = {}
    for array, id_field in GRAMMAR_ARRAYS.items():
        for item in deck.get(array, []):
            items_by_id[str(item.get(id_field))] = {**item, "_array": array}
            if item.get("cardId") != f"{item.get('entryId')}:grammar":
                report.fail(f"{item.get(id_field)}: grammar item card id must be <entryId>:grammar")
            if array in {"paradigm", "synonym"}:
                options = item.get("options", [])
                labels = [str(option.get("label", "")) for option in options]
                answer = item.get("form") if array == "paradigm" else item.get("answer")
                answers = [option for option in options if option.get("kind") == "answer"]
                if len(set(labels)) != len(labels) or len(answers) != 1 or answers[0].get("label") != answer:
                    report.fail(f"{item.get(id_field)}: grammar options must hold the answer exactly once")
                if array == "synonym" and item.get("prompt") in labels:
                    report.fail(f"{item.get(id_field)}: an option equals the prompt")
    for entry in deck["entries"]:
        card = entry["cards"].get("grammar")
        for ref in (card or {}).get("items", []):
            item = items_by_id.get(str(ref.get("id")))
            if item is None or item.get("entryId") != entry["entryId"]:
                report.fail(f"{entry['entryId']}: grammar reference {ref.get('id')!r} does not resolve")
                continue
            expected = item.get("polarity") if item["_array"] == "synonym" else item["_array"]
            if ref.get("mode") != expected:
                report.fail(f"{entry['entryId']}: grammar reference mode {ref.get('mode')!r} != {expected!r}")


def matrix(deck: dict[str, Any]) -> dict[str, dict[str, int]]:
    names = [
        "recognition-flashcard",
        "recognition-choice",
        "matching",
        "production-flashcard",
        "production-choice",
        "cloze",
        *GRAMMAR_MODES,
    ]
    table = {name: {"single": 0, "multiword": 0} for name in names}
    for entry in deck["entries"]:
        shape = "multiword" if entry["multiword"] else "single"
        cards = entry["cards"]
        modes = {"recognition-flashcard"}
        if cards["recognition"].get("choice"):
            modes.add("recognition-choice")
        if entry.get("matching"):
            modes.add("matching")
        if cards.get("production"):
            modes.add("production-flashcard")
            if cards["production"].get("choice"):
                modes.add("production-choice")
        if cards.get("cloze"):
            modes.add("cloze")
        modes.update(ref.get("mode") for ref in (cards.get("grammar") or {}).get("items", []))
        for mode in modes:
            if mode in table:
                table[mode][shape] += 1
    return table


def aspect_counts(deck: dict[str, Any], aspects: dict[str, dict[str, Any] | None]) -> dict[str, dict[str, int]]:
    counts: dict[str, dict[str, int]] = {"single": {}, "multiword": {}}
    for entry in deck["entries"]:
        aspect = aspects.get(entry["entryId"])
        if aspect:
            cell = f"{aspect['basis']}:{aspect['value']}"
            shape = counts["multiword" if entry["multiword"] else "single"]
            shape[cell] = shape.get(cell, 0) + 1
    return {shape: dict(sorted(cells.items())) for shape, cells in counts.items()}


def residuals(
    deck: dict[str, Any],
    coverage: dict[str, Any] | None,
    overlaps: dict[str, set[str]],
    aspects: dict[str, dict[str, Any] | None],
) -> dict[str, list]:
    by_id = {entry["entryId"]: entry for entry in deck["entries"]}
    reasons: dict[str, dict[str, str]] = {}
    for name, rows in ((coverage or {}).get("residuals") or {}).items():
        for row in rows:
            if isinstance(row, dict) and "reason" in row:
                reasons.setdefault(name, {})[row["entryId"]] = row["reason"]
    out: dict[str, list] = {
        "noAtlas": [],
        "identityConflicts": [],
        "productionOmitted": [],
        "refusedGroups": [],
        "noCloze": [],
        "aspectUnknown": [],
        "aspectMarkerDisagreements": [],
    }
    for entry_id, entry in by_id.items():
        atlas = entry.get("atlas")
        if atlas is None:
            reason = reasons.get("identityConflicts", {}).get(entry_id) or reasons.get("noAtlas", {}).get(entry_id)
            bucket = "identityConflicts" if entry_id in reasons.get("identityConflicts", {}) else "noAtlas"
            out[bucket].append((entry["uk"], reason or "no public Atlas article"))
        elif atlas.get("identityConflict"):
            out["identityConflicts"].append((entry["uk"], reasons.get("identityConflicts", {}).get(entry_id, "")))
        if overlaps.get(entry_id):
            partners = ", ".join(
                by_id[other]["uk"] for other in sorted(overlaps[entry_id], key=lambda o: by_id[o]["uk"])
            )
            out["productionOmitted"].append((entry["uk"], f"{entry['en']!r} overlaps: {partners}"))
        cards = entry["cards"]
        if not cards["recognition"].get("choice"):
            out["refusedGroups"].append((entry["uk"], "recognition choice: no unambiguous group"))
        if cards.get("production") and not cards["production"].get("choice"):
            out["refusedGroups"].append((entry["uk"], "production choice: no unambiguous group"))
        if not cards.get("cloze"):
            out["noCloze"].append((entry["uk"], reasons.get("noCloze", {}).get(entry_id, "")))
        aspect = aspects.get(entry_id)
        if aspect:
            evidence = (
                f"{entry.get('teacherEn')!r}: sources {aspect['value']} ({aspect['basis']}; VESUM "
                f"{'/'.join(aspect['vesum']) or '-'}, ULIF {'/'.join(aspect['ulif']) or '-'}; lemma {aspect['lemma']})"
            )
            if aspect["value"] == "unknown":
                out["aspectUnknown"].append((entry["uk"], evidence))
            if aspect["markerAgrees"] is False:
                out["aspectMarkerDisagreements"].append((entry["uk"], evidence))
    return out


def _read_only(path: Path | None) -> SQLiteConnection | None:
    if path is None:
        return None
    if not path.exists():
        raise FileNotFoundError(path)
    return _open_readonly(path.resolve())


def run(args: argparse.Namespace) -> tuple[Report, dict[str, Any]]:
    report = Report()
    deck_dir: Path = args.deck_dir
    manifest = _load(deck_dir / MANIFEST_FILE, report)
    deck = _load(deck_dir / DECK_FILE, report)
    cloze = _load(deck_dir / CLOZE_FILE, report)
    frozen = _load(deck_dir / FROZEN_FILE, report)
    coverage = _load(deck_dir / COVERAGE_FILE, Report())
    summary: dict[str, Any] = {}
    if manifest is None or deck is None or cloze is None or frozen is None:
        return report, summary
    if (deck.get("schema"), deck.get("schemaVersion")) != DECK_SCHEMA:
        report.fail("deck schema/version mismatch")
    if (cloze.get("schema"), cloze.get("schemaVersion")) != CLOZE_SCHEMA:
        report.fail("cloze schema/version mismatch")
    if not (manifest.get("deckVersion") == deck.get("deckVersion") == cloze.get("deckVersion")):
        report.fail("deckVersion differs between manifest, deck and cloze")
    check_manifest(deck_dir, manifest, report)
    if args.expect_keys is not None and len(frozen.get("keys", [])) != args.expect_keys:
        report.fail(f"frozen key list has {len(frozen.get('keys', []))} keys, expected {args.expect_keys}")
    if args.docx:
        summary["table"] = check_source_table(deck, frozen, extract_table(args.docx, args.heading), report)
    withheld, kept = load_ledger(args.withheld, report) if getattr(args, "withheld", None) else (None, set())
    required_kept = kept if getattr(args, "publication", False) else None
    vesum = _read_only(args.vesum_db)
    sources = _read_only(args.sources_db)
    atlas = _read_only(getattr(args, "atlas_db", None))
    try:
        lookup = AspectLookup(vesum, sources) if vesum is not None and sources is not None else None
        aspects = check_aspects(deck, lookup, report)
        values = {entry_id: (aspect or {}).get("value") for entry_id, aspect in aspects.items()}
        overlaps, partners = own_overlaps(deck["entries"], values)
        check_entries(deck, frozen, overlaps, partners, report)
        senses = check_atlas(deck, coverage, atlas_articles(atlas), aspects, report) if atlas is not None else None
        summary["lesson"] = check_cloze(
            deck, cloze, overlaps, partners, report, vesum, sources, senses, withheld, required_kept
        )
    finally:
        for conn in (vesum, sources, atlas):
            if conn is not None:
                conn.close()
    summary["atlasVerified"] = atlas is not None
    summary["withheldVerified"] = withheld is not None
    summary["reviewRequired"] = required_kept is not None
    check_grammar(deck, aspects, coverage, report)
    summary["entries"] = len(deck["entries"])
    summary["frozenKeys"] = len(frozen.get("keys", []))
    summary["cloze"] = len(cloze.get("cloze", []))
    summary["aspectVerified"] = lookup is not None
    summary["aspect"] = aspect_counts(deck, aspects)
    summary["matrix"] = matrix(deck)
    summary["entriesByShape"] = {
        "single": sum(1 for entry in deck["entries"] if not entry["multiword"]),
        "multiword": sum(1 for entry in deck["entries"] if entry["multiword"]),
    }
    summary["residuals"] = residuals(deck, coverage, overlaps, aspects)
    return report, summary


def render(report: Report, summary: dict[str, Any], limit: int | None) -> str:
    lines = [f"teacher deck check: {'PASS' if not report.errors else 'FAIL'} ({len(report.errors)} errors)"]
    for error in report.errors[: limit or None]:
        lines.append(f"  ERROR {error}")
    if limit and len(report.errors) > limit:
        lines.append(f"  … {len(report.errors) - limit} more errors")
    if not summary:
        return "\n".join(lines)
    table = summary.get("table")
    if table:
        different = sum(1 for merge in table["merges"] if merge["differentEnglish"])
        lines.append(
            f"source table: {table['rows']} rows, {table['sourceKeys']} distinct keys, "
            f"{len(table['merges'])} merged entries ({different} with different English)"
        )
    lines.append(
        f"entries: {summary['entries']} (frozen source keys: {summary['frozenKeys']}); cloze items: {summary['cloze']}"
    )
    lines.append(
        f"teacher-lesson cloze: {summary['lesson']['lessonItems']} items, {summary['lesson']['lessonSentences']} "
        f"distinct sentences; fragment rules re-checked; withheld ledger "
        f"{'re-checked' if summary['withheldVerified'] else 'not given'}"
        f"{' (publication: every served lesson sentence kept)' if summary['reviewRequired'] else ''}; Atlas join, sense rule and identity "
        f"conflicts {'re-derived' if summary['atlasVerified'] else 'not re-derived (no --atlas-db)'}"
    )
    for shape, cells in summary["aspect"].items():
        lines.append(
            f"verb aspect ({shape}{'' if summary['aspectVerified'] else ', declared — not re-derived'}): "
            + (", ".join(f"{cell} {n}" for cell, n in cells.items()) or "none")
        )
    without = {
        shape: summary["entriesByShape"][shape] - summary["matrix"]["production-flashcard"][shape]
        for shape in ("single", "multiword")
    }
    lines.append(
        f"entries without an EN->UK card: {sum(without.values())} "
        f"({without['single']} single-word, {without['multiword']} multiword)"
    )
    lines.append(f"{'mode':<24}{'single':>8}{'multiword':>11}")
    for mode, counts in summary["matrix"].items():
        lines.append(f"{mode:<24}{counts['single']:>8}{counts['multiword']:>11}")
    for name, rows in summary["residuals"].items():
        lines.append(f"residual {name}: {len(rows)}")
        for uk, reason in rows[: limit or None]:
            lines.append(f"  - {uk}: {reason}")
        if limit and len(rows) > limit:
            lines.append(f"  … {len(rows) - limit} more")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Independently check a built teacher-table deck (#8843) against its structural contract.\n"
            "Use after every refresh and in review; it never imports the generator it checks."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""Examples:
  .venv/bin/python scripts/audit/check_teacher_deck.py --deck-dir data/lexicon/teacher-deck
  .venv/bin/python scripts/audit/check_teacher_deck.py --deck-dir /tmp/deck --docx /private/master.docx \\
      --expect-keys 1134 --vesum-db data/vesum.db --sources-db data/sources.db --atlas-db data/atlas.db \\
      --withheld site/src/data/lexicon-teacher-deck-withheld.json --publication
Outputs: PASS/FAIL, errors, the eligibility matrix and residual lists on stdout;
  --json writes the same as JSON. Read-only: databases open with mode=ro.
Exit codes: 0 PASS; 1 structural errors; 2 unreadable inputs.
Related: docs/practice/teacher-deck-artifacts.md; scripts/lexicon/teacher_deck.py; #8843.
""",
    )
    parser.add_argument(
        "--deck-dir", type=Path, required=True, help="Directory holding the published set (manifest.json, …)."
    )
    parser.add_argument(
        "--docx", type=Path, help="Private master DOCX for the independent table comparison (default: skip)."
    )
    parser.add_argument("--heading", default=HEADING, help=f"Exact table heading (default: {HEADING!r}).")
    parser.add_argument("--expect-keys", type=int, help="Required frozen key count, e.g. 1134 (default: not pinned).")
    parser.add_argument("--vesum-db", type=Path, help="VESUM DB to verify single-word cloze forms (default: skip).")
    parser.add_argument(
        "--sources-db", type=Path, help="sources.db to verify cloze sentences verbatim (default: skip)."
    )
    parser.add_argument(
        "--atlas-db",
        type=Path,
        help="Word Atlas DB to re-derive the Atlas join, sense rule and identity conflicts (default: skip).",
    )
    parser.add_argument(
        "--withheld",
        type=Path,
        help="Language-review ledger; fails when a withheld sentence is served (default: skip).",
    )
    parser.add_argument(
        "--publication",
        action="store_true",
        help="Publication mode (needs --withheld): every served teacher-lesson sentence needs a kept record "
        "(default: unreviewed sentences allowed, as in the review queue).",
    )
    parser.add_argument(
        "--limit", type=int, default=0, help="Max listed errors/residual rows per list; 0 = all (default 0)."
    )
    parser.add_argument("--json", type=Path, help="Optional JSON report path (default: none).")
    args = parser.parse_args(argv)
    if args.publication and args.withheld is None:
        parser.error("--publication needs --withheld")
    try:
        report, summary = run(args)
    except (OSError, ValueError, KeyError, zipfile.BadZipFile, sqlite3.Error) as exc:
        print(f"teacher deck check: cannot read inputs ({type(exc).__name__}: {exc})", file=sys.stderr)
        return 2
    print(render(report, summary, args.limit or None))
    if args.json:
        args.json.write_text(
            json.dumps({"ok": not report.errors, "errors": report.errors, **summary}, ensure_ascii=False, indent=2)
            + "\n",
            encoding="utf-8",
        )
    return 0 if not report.errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
