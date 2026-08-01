#!/usr/bin/env python3
"""Streaming, evidence-gated Ukrainian language-contact candidate detector.

The detector preserves source text and emits bounded review spans.  It does not
produce linguistic gold, automatic corrections, or source-admission decisions.
All network-capable evidence sources are represented by local, bounded caches or
explicit pending states during a corpus run.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import resource
import sqlite3
import sys
import tempfile
import unicodedata
from collections import Counter, OrderedDict
from collections.abc import Iterable, Iterator, Mapping, Sequence
from contextlib import closing
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator
from pymorphy3 import MorphAnalyzer

ROOT = Path(__file__).resolve().parents[3]
SCRIPTS_DIR = ROOT / "scripts"
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from scripts.lexicon.calque_corrections import (
    CURATED_CALQUES,
    PHRASAL_CALQUES,
)
from scripts.lexicon.load_relation_candidates import RelationHeritageLookup
from scripts.projects.open_model_data.inventory_existing_assets import WORD_RE
from scripts.verification.check_ru_morph import get_ru_confidence
from scripts.verification.vesum import verify_words

CONFIG_SCHEMA_PATH = ROOT / "data/projects/open_model_data/contracts/language_contact_config_v1.schema.json"
CANDIDATE_SCHEMA_PATH = ROOT / "data/projects/open_model_data/contracts/language_contact_candidate_v1.schema.json"
RECEIPT_SCHEMA_PATH = ROOT / "data/projects/open_model_data/contracts/language_contact_receipt_v1.schema.json"
DEFAULT_CONFIG_PATH = ROOT / "data/projects/open_model_data/detector/language_contact_config_v1.json"
DEFAULT_REGRESSION_FIXTURE = ROOT / "data/projects/open_model_data/detector/regression_fixture_v1.json"

SCHEMA_VERSION = "language_contact_receipt_v1"
CANDIDATE_SCHEMA_VERSION = "language_contact_candidate_v1"

IDENTIFIER_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")
CYRILLIC_RE = re.compile(r"[\u0400-\u052f]")
LATIN_WORD_RE = re.compile(r"(?<![A-Za-z])[A-Za-z][A-Za-z'-]{1,}(?![A-Za-z])")
NON_PRINTABLE_RE = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\x9f]")
MOJIBAKE_RE = re.compile(r"(?:Ã.|Â.|Ð.|Ñ.){2,}")
RUSSIAN_ORTHOGRAPHY_RE = re.compile(r"[ыэъё]", re.IGNORECASE)
APOSTROPHES = str.maketrans({"’": "'", "ʼ": "'", "‘": "'", "`": "'", "´": "'"})
STRESS_MARKS = frozenset({"\u0300", "\u0301"})
PROTECTED_PERIODS = frozenset(
    {
        "historical",
        "historical_documents",
        "historical_literary_ukrainian",
        "middle_ukrainian",
        "old_east_slavic",
        "regional_dialectal",
    }
)
PROTECTED_REGISTER_FRAGMENTS = ("dialect", "folk", "heritage", "histor", "regional", "archa")
QUOTE_PAIRS = {"«": "»", "“": "”", "„": "“", "\"": "\""}
SENTENCE_BOUNDARY_RE = re.compile(r"[.!?…;\n]")


@dataclass(frozen=True, slots=True)
class TokenSpan:
    """A lexical token with exact record-relative character offsets."""

    index: int
    start_char: int
    end_char: int
    surface: str
    normalized: str


@dataclass(frozen=True, slots=True)
class DetectionSpan:
    """A structural span extracted before lexical classification."""

    start_char: int
    end_char: int
    original_text: str
    discourse_role: str
    is_quoted: bool
    boundary_kind: str = "structure"


@dataclass(frozen=True, slots=True)
class Seed:
    """A positively observed reason to inspect one bounded token interval."""

    start_token: int
    end_token: int
    kind: str
    detail: str


@dataclass(frozen=True, slots=True)
class DetectorRunResult:
    """Paths and deterministic summary returned by one detector run."""

    summary: dict[str, Any]
    summary_path: Path
    candidates_path: Path

    @property
    def complete(self) -> bool:
        return bool(self.summary["coverage"]["complete"])


def canonical_json(value: Any) -> str:
    """Serialize JSON with a stable UTF-8 byte representation."""
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"), sort_keys=True)


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _stage_json(path: Path, value: Mapping[str, Any]) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            dir=path.parent,
            prefix=path.name,
            suffix=".tmp.json",
            delete=False,
        ) as handle:
            temporary = Path(handle.name)
            handle.write((canonical_json(value) + "\n").encode("utf-8"))
            handle.flush()
            os.fsync(handle.fileno())
        return temporary
    except Exception:
        if temporary is not None:
            temporary.unlink(missing_ok=True)
        raise


def _backup_path(output: Path) -> Path:
    with tempfile.NamedTemporaryFile(
        dir=output.parent,
        prefix=output.name,
        suffix=".rollback",
        delete=False,
    ) as handle:
        backup = Path(handle.name)
    return backup


def _promote_staged_artifacts(artifacts: Sequence[tuple[Path, Path]]) -> None:
    """Publish candidates plus receipt and restore prior outputs on failure."""
    outputs = [output.absolute() for _, output in artifacts]
    if len(set(outputs)) != len(outputs):
        raise ValueError("artifact outputs must be distinct")
    for temporary, output in artifacts:
        if not temporary.is_file():
            raise ValueError(f"staged artifact is missing: {temporary}")
        output.parent.mkdir(parents=True, exist_ok=True)
        if output.exists() and not output.is_file():
            raise ValueError(f"artifact destination is not a file: {output}")

    backups: list[tuple[Path, Path]] = []
    promoted: list[Path] = []
    try:
        for temporary, output in artifacts:
            if output.exists():
                backup = _backup_path(output)
                try:
                    os.replace(output, backup)
                except Exception:
                    backup.unlink(missing_ok=True)
                    raise
                backups.append((output, backup))
            os.replace(temporary, output)
            promoted.append(output)
    except Exception as exc:
        rollback_errors: list[str] = []
        for output in reversed(promoted):
            try:
                output.unlink(missing_ok=True)
            except OSError as rollback_exc:
                rollback_errors.append(f"remove {output}: {rollback_exc}")
        for output, backup in reversed(backups):
            try:
                if backup.exists():
                    os.replace(backup, output)
            except OSError as rollback_exc:
                rollback_errors.append(f"restore {output}: {rollback_exc}")
        for temporary, _ in artifacts:
            temporary.unlink(missing_ok=True)
        if rollback_errors:
            raise ValueError(
                "artifact promotion failed and rollback was incomplete: "
                + "; ".join(rollback_errors)
            ) from exc
        raise
    else:
        for _, backup in backups:
            backup.unlink(missing_ok=True)


def normalize_form(surface: str) -> str:
    """Return stress-insensitive, apostrophe-canonical lookup text."""
    normalized = unicodedata.normalize("NFKD", surface.translate(APOSTROPHES))
    without_marks = "".join(ch for ch in normalized if ch not in STRESS_MARKS)
    return unicodedata.normalize("NFC", without_marks).casefold()


def _offset_safe_casefold(text: str) -> str:
    """Normalize apostrophes/case without changing Ukrainian character offsets."""
    return text.translate(APOSTROPHES).lower()


def _load_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"cannot read JSON {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise ValueError(f"expected JSON object: {path}")
    return value


def _load_and_validate_config(path: Path) -> dict[str, Any]:
    schema = _load_json(CONFIG_SCHEMA_PATH)
    Draft202012Validator.check_schema(schema)
    config = _load_json(path)
    errors = sorted(Draft202012Validator(schema).iter_errors(config), key=lambda item: list(item.path))
    if errors:
        messages = [f"{'.'.join(str(p) for p in err.path) or '<root>'}: {err.message}" for err in errors]
        raise ValueError("detector config invalid:\n" + "\n".join(messages))
    return config


def _identifier(value: str) -> str:
    if IDENTIFIER_RE.fullmatch(value) is None:
        raise ValueError(f"unsafe SQLite identifier: {value!r}")
    return f'"{value}"'


def _connect_read_only(path: Path) -> sqlite3.Connection:
    if not path.is_file():
        raise FileNotFoundError(path)
    connection = sqlite3.connect(path.resolve().as_uri() + "?mode=ro", uri=True)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA query_only=ON")
    return connection


def _table_columns(connection: sqlite3.Connection, table: str) -> set[str]:
    return {str(row[1]) for row in connection.execute(f"PRAGMA table_info({_identifier(table)})")}


def _source_query(source: Mapping[str, Any], columns: set[str]) -> tuple[str, tuple[Any, ...]]:
    adapter = source["adapter"]
    required = {adapter["id_column"], adapter["text_column"], adapter["locator_column"]}
    for dimension in adapter["dimensions"].values():
        if "column" in dimension:
            required.add(dimension["column"])
    exclusion = adapter.get("exclude")
    if exclusion:
        required.add(exclusion["column"])
    missing = sorted(required - columns)
    if missing:
        raise ValueError(f"missing columns: {', '.join(missing)}")

    selections = [
        f'{_identifier(adapter["id_column"])} AS "__record_id"',
        f'{_identifier(adapter["text_column"])} AS "__text"',
        f'{_identifier(adapter["locator_column"])} AS "__locator"',
    ]
    for name, dimension in sorted(adapter["dimensions"].items()):
        if "column" in dimension:
            selections.append(f"{_identifier(dimension['column'])} AS {_identifier('__' + name)}")
    parameters: tuple[Any, ...] = ()
    where = ""
    if exclusion:
        values = tuple(exclusion["values"])
        placeholders = ",".join("?" for _ in values)
        where = f" WHERE {_identifier(exclusion['column'])} NOT IN ({placeholders})"
        parameters = values
    query = (
        f"SELECT {', '.join(selections)} FROM {_identifier(adapter['table'])}"
        f"{where} ORDER BY {_identifier(adapter['id_column'])} ASC, "
        f"{_identifier(adapter['locator_column'])} ASC"
    )
    return query, parameters


def tokenize_with_offsets(text: str) -> list[TokenSpan]:
    """Tokenize with the profiler's exact lexical-word definition and offsets."""
    return [
        TokenSpan(index, match.start(), match.end(), match.group(0), normalize_form(match.group(0)))
        for index, match in enumerate(WORD_RE.finditer(text))
    ]


def _paragraph_end(text: str, start: int) -> int:
    match = re.search(r"\n\s*\n", text[start:])
    return len(text) if match is None else start + match.start()


def segment_structure(text: str) -> list[DetectionSpan]:
    """Extract nested, imbalanced, and dash-dialogue structures with exact offsets.

    Imbalanced quotes are bounded by the paragraph that contains the opener.
    Nested ranges are retained; candidate clustering later chooses the smallest
    containing structural boundary.
    """
    if not text:
        return []
    spans: list[DetectionSpan] = []
    stack: list[tuple[str, int]] = []
    for index, char in enumerate(text):
        if stack and char == stack[-1][0]:
            closer, content_start = stack.pop()
            if index > content_start:
                role = "quotation"
                spans.append(
                    DetectionSpan(content_start, index, text[content_start:index], role, True, "paired_quote")
                )
            continue
        if char in QUOTE_PAIRS:
            closer = QUOTE_PAIRS[char]
            stack.append((closer, index + 1))
    for _closer, content_start in stack:
        end = _paragraph_end(text, content_start)
        if end > content_start:
            spans.append(
                DetectionSpan(
                    content_start,
                    end,
                    text[content_start:end],
                    "quotation",
                    True,
                    "imbalanced_quote_paragraph",
                )
            )

    dialogue_pattern = re.compile(r"(?m)^[ \t]*[—–-][ \t]+([^\n]+)")
    for match in dialogue_pattern.finditer(text):
        content_start, _line_end = match.span(1)
        content = match.group(1)
        attribution = re.search(r"\s+[—–-]\s+(?=[а-яіїєґА-ЯІЇЄҐ])", content)
        end = content_start + (attribution.start() if attribution else len(content.rstrip()))
        if end > content_start:
            spans.append(
                DetectionSpan(content_start, end, text[content_start:end], "dialogue", True, "dash_dialogue")
            )

    meta_pattern = re.compile(
        r"(?iu)(?:слово|форма|вираз|пишуть|кажуть|називається)\s*[:—-]\s*([^.!?\n]{1,240})"
    )
    for match in meta_pattern.finditer(text):
        start, end = match.span(1)
        spans.append(
            DetectionSpan(start, end, text[start:end], "metalinguistic_example", False, "metalinguistic_marker")
        )

    line_offset = 0
    for _line_number, line in enumerate(text.splitlines(keepends=True)):
        stripped = line.strip()
        content_start = line_offset + (len(line) - len(line.lstrip()))
        content_end = content_start + len(stripped)
        lowered = stripped.casefold()
        if lowered.startswith(("назва:", "заголовок:")):
            colon = line.find(":")
            start = line_offset + colon + 1
            start += len(text[start:content_end]) - len(text[start:content_end].lstrip())
            if content_end > start:
                spans.append(DetectionSpan(start, content_end, text[start:content_end], "title", False, "title_marker"))
        elif lowered.startswith(("епіграф:", "epigraph:")):
            colon = line.find(":")
            start = line_offset + colon + 1
            start += len(text[start:content_end]) - len(text[start:content_end].lstrip())
            if content_end > start:
                spans.append(
                    DetectionSpan(start, content_end, text[start:content_end], "epigraph", True, "epigraph_marker")
                )
        elif re.match(r"(?iu)^(?:цит\.|документ|джерело)\s*[:—-]", stripped):
            spans.append(
                DetectionSpan(
                    content_start,
                    content_end,
                    text[content_start:content_end],
                    "citation_or_document",
                    True,
                    "citation_marker",
                )
            )
        line_offset += len(line)

    unique = {(s.start_char, s.end_char, s.discourse_role, s.boundary_kind): s for s in spans if s.original_text}
    return sorted(unique.values(), key=lambda span: (span.start_char, span.end_char, span.discourse_role))


def _containing_structure(
    start: int,
    end: int,
    structures: Sequence[DetectionSpan],
) -> DetectionSpan | None:
    matches = [span for span in structures if span.start_char <= start and end <= span.end_char]
    return min(matches, key=lambda span: (span.end_char - span.start_char, span.start_char)) if matches else None


def _paragraph_bounds(text: str, start: int, end: int) -> tuple[int, int]:
    prior = list(re.finditer(r"\n\s*\n", text[:start]))
    left = prior[-1].end() if prior else 0
    following = re.search(r"\n\s*\n", text[end:])
    right = end + following.start() if following else len(text)
    return left, right


def _sentence_bounds(text: str, start: int, end: int, lower: int, upper: int) -> tuple[int, int]:
    previous = list(SENTENCE_BOUNDARY_RE.finditer(text[lower:start]))
    left = lower + previous[-1].end() if previous else lower
    following = SENTENCE_BOUNDARY_RE.search(text[end:upper])
    right = end + following.start() + 1 if following else upper
    return left, right


class BoundedCache:
    """Small deterministic LRU used to bound per-run evidence memory."""

    def __init__(self, max_entries: int):
        self.max_entries = max_entries
        self.values: OrderedDict[str, Any] = OrderedDict()
        self.hits = 0

    def get(self, key: str) -> Any:
        if key not in self.values:
            return None
        self.hits += 1
        value = self.values.pop(key)
        self.values[key] = value
        return value

    def put(self, key: str, value: Any) -> None:
        if key in self.values:
            self.values.pop(key)
        self.values[key] = value
        if len(self.values) > self.max_entries:
            self.values.popitem(last=False)


class VesumBatchAdapter:
    """Pinned VESUM batch lookups with a bounded cross-record cache."""

    def __init__(self, database: Path, batch_size: int, cache_entries: int):
        self.database = database
        self.batch_size = batch_size
        self.cache = BoundedCache(cache_entries)
        self.forms_queried = 0
        self.lookup_batches = 0

    def lookup(self, forms: Iterable[str]) -> dict[str, list[dict[str, Any]]]:
        ordered = sorted(set(forms))
        result: dict[str, list[dict[str, Any]]] = {}
        missing: list[str] = []
        for form in ordered:
            cached = self.cache.get(form)
            if cached is None:
                missing.append(form)
            else:
                result[form] = cached
        for index in range(0, len(missing), self.batch_size):
            chunk = missing[index : index + self.batch_size]
            matches = verify_words(chunk, db_path=self.database)
            self.lookup_batches += 1
            self.forms_queried += len(chunk)
            for form in chunk:
                analyses = sorted(
                    matches.get(form, []),
                    key=lambda item: (str(item.get("lemma", "")), str(item.get("pos", "")), str(item.get("tags", ""))),
                )
                self.cache.put(form, analyses)
                result[form] = analyses
        return result


class RussianMorphAdapter:
    """Russian-shadow adapter backed only by check_ru_morph.get_ru_confidence."""

    def __init__(self, cache_entries: int):
        self.cache = BoundedCache(cache_entries)
        self.calls = 0

    def lookup(self, form: str) -> dict[str, Any]:
        cached = self.cache.get(form)
        if cached is not None:
            return cached
        confidence, lemma = get_ru_confidence(form)
        value = {"token": form, "confidence": round(float(confidence), 6), "lemma": lemma}
        self.calls += 1
        self.cache.put(form, value)
        return value


class R2UEvidenceCache:
    """Rights-safe hashes and headword-match states from bounded r2u adapter calls."""

    def __init__(self, path: Path):
        self.path = path
        payload = _load_json(path)
        if payload.get("schema_version") != "r2u_evidence_cache_v1":
            raise ValueError(f"unsupported R2U cache schema: {path}")
        entries = payload.get("entries")
        if not isinstance(entries, list):
            raise ValueError(f"R2U cache entries must be a list: {path}")
        actual_hash = sha256_text(canonical_json(entries))
        if actual_hash != payload.get("entries_sha256"):
            raise ValueError(f"R2U cache hash mismatch: {path}")
        self.cache_id = str(payload["cache_id"])
        self.entries = {normalize_form(str(entry["query"])): dict(entry) for entry in entries}
        self.lookups = 0
        self.hits = 0
        self.misses = 0

    def has_surface_match(self, surface: str) -> bool:
        entry = self.entries.get(normalize_form(surface))
        return bool(entry and entry.get("headword_match") == "surface")

    def lookup(self, surface: str, lemma: str | None = None) -> dict[str, Any]:
        self.lookups += 1
        for query_kind, query in (("surface", surface), ("lemma", lemma or "")):
            entry = self.entries.get(normalize_form(query))
            if entry and entry.get("headword_match") in {"surface", "lemma"}:
                self.hits += 1
                return {
                    "status": "hit",
                    "query": entry["query"],
                    "query_kind": query_kind,
                    "headword_match": entry["headword_match"],
                    "result_count": entry["result_count"],
                    "response_sha256": entry["response_sha256"],
                }
        self.misses += 1
        return {"status": "miss", "query": normalize_form(surface), "query_kind": "surface"}


class HeritageEvidenceAdapter(RelationHeritageLookup):
    """Exact local Грінченко/ЕСУМ/СУМ lookup with named hit provenance."""

    def __init__(self, db_path: Path, cache_entries: int, max_headwords: int):
        super().__init__(db_path)
        self.detail_cache = BoundedCache(cache_entries)
        self.lemma_cache = BoundedCache(cache_entries)
        self.lookups = 0
        self.hits = 0
        self.misses = 0
        self.uk_morph = MorphAnalyzer(lang="uk")
        self.max_headwords = max_headwords
        self.headwords: dict[str, tuple[str, ...]] = {}
        self._load_exact_headwords()

    def _load_exact_headwords(self) -> None:
        """Build one bounded in-memory index over the adapter's exact tables.

        The source tables do not all have headword indexes.  Scanning them once
        avoids an O(dictionary-size) table scan for every routed form.
        """
        self.open()
        assert self._conn is not None
        identities: dict[str, set[str]] = {}
        for table, column, identity in (
            ("grinchenko", "word", "Грінченко"),
            ("esum_etymology_meta", "lemma", "ЕСУМ"),
            ("sum11", "word", "СУМ-11"),
        ):
            try:
                rows = self._conn.execute(
                    f"SELECT {_identifier(column)} FROM {_identifier(table)} ORDER BY {_identifier(column)}"
                )
            except sqlite3.DatabaseError:
                continue
            for row in rows:
                headword = normalize_form(str(row[0] or ""))
                if headword:
                    identities.setdefault(headword, set()).add(identity)
                    if len(identities) > self.max_headwords:
                        raise ValueError(
                            f"heritage headword index exceeds configured maximum {self.max_headwords}"
                        )
        self.headwords = {
            headword: tuple(sorted(dictionary_identities))
            for headword, dictionary_identities in identities.items()
        }

    def lemma_candidates(self, surface: str) -> list[str]:
        normalized = normalize_form(surface)
        cached = self.lemma_cache.get(normalized)
        if cached is not None:
            return cached
        lemmas = sorted(
            {normalize_form(parse.normal_form) for parse in self.uk_morph.parse(normalized)[:4]}
        )
        self.lemma_cache.put(normalized, lemmas)
        return lemmas

    def may_attest(self, surface: str) -> bool:
        normalized = normalize_form(surface)
        return normalized in self.headwords or any(
            lemma in self.headwords for lemma in self.lemma_candidates(normalized)
        )

    def lookup(self, surface: str) -> dict[str, Any]:
        normalized = normalize_form(surface)
        cached = self.detail_cache.get(normalized)
        if cached is not None:
            return cached
        self.lookups += 1
        lemmas = self.lemma_candidates(normalized)
        queries = [normalized, *[lemma for lemma in lemmas if lemma != normalized]]
        hits: list[dict[str, str]] = []
        for query in queries:
            for identity in self.headwords.get(query, ()):
                hits.append({"dictionary_identity": identity, "matched_headword": query})
        value = {
            "status": "hit" if hits else "miss",
            "surface": normalized,
            "lemma_candidates": lemmas,
            "hits": sorted(hits, key=lambda item: (item["dictionary_identity"], item["matched_headword"])),
        }
        if hits:
            self.hits += 1
        else:
            self.misses += 1
        self.detail_cache.put(normalized, value)
        return value


class EvidenceRuntime:
    """Run-scoped, bounded, read-only evidence adapters and counters."""

    def __init__(self, config: Mapping[str, Any], input_root: Path):
        vesum_path = input_root / str(config["vesum"]["database"])
        if not vesum_path.is_file():
            raise FileNotFoundError(f"VESUM database inaccessible: {vesum_path}")
        self.vesum = VesumBatchAdapter(
            vesum_path,
            int(config["vesum"]["batch_size"]),
            int(config["vesum"]["cache_entries"]),
        )
        self.ru_morph = RussianMorphAdapter(int(config["ru_morph"]["cache_entries"]))
        cache_path = ROOT / str(config["r2u_cache"]["file"])
        self.r2u = R2UEvidenceCache(cache_path)
        sources_path = input_root / str(config["heritage"]["database"])
        self.heritage_available = sources_path.is_file()
        self.heritage = (
            HeritageEvidenceAdapter(
                sources_path,
                int(config["heritage"]["cache_entries"]),
                int(config["heritage"]["max_headwords"]),
            )
            if self.heritage_available
            else None
        )
        self.offsets_rejected = 0
        self.rows_without_prefilter_signal = 0
        self.rows_with_prefilter_signal = 0
        self.expensive_lookups_avoided = 0

    def close(self) -> None:
        if self.heritage is not None:
            self.heritage.close()


def _find_token_index(tokens: Sequence[TokenSpan], char_offset: int, *, prefer_end: bool = False) -> int | None:
    for token in tokens:
        if token.start_char <= char_offset < token.end_char:
            return token.index
        if not prefer_end and token.start_char >= char_offset:
            return token.index
        if prefer_end and token.end_char > char_offset:
            return token.index
    return tokens[-1].index if tokens and prefer_end else None


def _find_vetted_routes(
    text: str,
    tokens: Sequence[TokenSpan],
    config: Mapping[str, Any],
) -> list[Seed]:
    seeds: list[Seed] = []
    lowered = _offset_safe_casefold(text)
    phrases: list[tuple[str, str, str]] = []
    for phrase in sorted(PHRASAL_CALQUES, key=lambda item: (-len(item), item)):
        phrases.append((_offset_safe_casefold(phrase), "vetted_phrasal_calque_or_collocation", f"PHRASAL_CALQUES:{phrase}"))
    for route in config["valid_word_routes"]:
        phrases.append((_offset_safe_casefold(route["pattern"]), str(route["route_kind"]), str(route["source_key"])))
    occupied: list[tuple[int, int]] = []
    for phrase, kind, detail in phrases:
        start = 0
        while True:
            index = lowered.find(phrase, start)
            if index < 0:
                break
            end = index + len(phrase)
            if not any(index < prior_end and prior_start < end for prior_start, prior_end in occupied):
                first = _find_token_index(tokens, index)
                last = _find_token_index(tokens, max(index, end - 1), prefer_end=True)
                if first is not None and last is not None:
                    seeds.append(Seed(first, last, kind, detail))
                    occupied.append((index, end))
            start = end
    curated = {normalize_form(item): item for item in CURATED_CALQUES}
    for token in tokens:
        if token.normalized in curated:
            seeds.append(
                Seed(token.index, token.index, "vetted_lexical_calque", f"CURATED_CALQUES:{curated[token.normalized]}")
            )
    return seeds


def _latin_and_ocr_seeds(text: str, tokens: Sequence[TokenSpan], min_latin_words: int) -> list[Seed]:
    seeds: list[Seed] = []
    latin_matches = list(LATIN_WORD_RE.finditer(text))
    run: list[re.Match[str]] = []
    for match in latin_matches:
        if run and match.start() - run[-1].end() > 24:
            if len(run) >= min_latin_words:
                first = _find_token_index(tokens, run[0].start())
                last = _find_token_index(tokens, run[-1].end() - 1, prefer_end=True)
                if first is not None and last is not None:
                    seeds.append(Seed(first, last, "other_language_run", "unicode_latin_run"))
            run = []
        run.append(match)
    if len(run) >= min_latin_words:
        first = _find_token_index(tokens, run[0].start())
        last = _find_token_index(tokens, run[-1].end() - 1, prefer_end=True)
        if first is not None and last is not None:
            seeds.append(Seed(first, last, "other_language_run", "unicode_latin_run"))
    for match in [*NON_PRINTABLE_RE.finditer(text), *MOJIBAKE_RE.finditer(text)]:
        token_index = _find_token_index(tokens, match.start())
        if token_index is None:
            token_index = _find_token_index(tokens, match.end(), prefer_end=True)
        if token_index is not None:
            seeds.append(Seed(token_index, token_index, "ocr_or_encoding", "control_or_mojibake_signal"))
    return seeds


def _adjacent_unknown_members(
    text: str,
    tokens: Sequence[TokenSpan],
    vesum_matches: Mapping[str, Sequence[Mapping[str, Any]]],
    max_gap: int,
    min_chars: int,
) -> set[int]:
    hyphens = "-‐‑‒–—"
    unknown = [
        token.index
        for token in tokens
        if (
            not vesum_matches.get(token.normalized)
            and not token.surface[:1].isupper()
            and CYRILLIC_RE.search(token.surface) is not None
            and len(token.normalized) >= min_chars
            and not (token.start_char > 0 and text[token.start_char - 1] in hyphens)
            and not (token.end_char < len(text) and text[token.end_char] in hyphens)
        )
    ]
    members: set[int] = set()
    run: list[int] = []
    for index in unknown:
        if run and index - run[-1] > max_gap + 1:
            if len(run) >= 2:
                members.update(run)
            run = []
        run.append(index)
    if len(run) >= 2:
        members.update(run)
    return members


def _seed_record(
    *,
    text: str,
    tokens: Sequence[TokenSpan],
    vesum_matches: Mapping[str, Sequence[Mapping[str, Any]]],
    config: Mapping[str, Any],
    runtime: EvidenceRuntime,
) -> tuple[list[Seed], dict[int, dict[str, Any]], dict[int, dict[str, Any]], dict[int, dict[str, Any]]]:
    seeds = _find_vetted_routes(text, tokens, config)
    seeds.extend(_latin_and_ocr_seeds(text, tokens, int(config["prefilter"]["min_latin_run_words"])))
    anchors = {normalize_form(value) for value in config["prefilter"]["russian_anchors"]}
    phonetic_map = {normalize_form(key): normalize_form(value) for key, value in config["reconstruction"]["mappings"].items()}
    adjacent_unknown = _adjacent_unknown_members(
        text,
        tokens,
        vesum_matches,
        int(config["prefilter"]["max_unknown_gap_tokens"]),
        int(config["prefilter"]["min_adjacent_form_chars"]),
    )
    ru_by_token: dict[int, dict[str, Any]] = {}
    r2u_by_token: dict[int, dict[str, Any]] = {}
    heritage_by_token: dict[int, dict[str, Any]] = {}
    threshold = float(config["ru_morph"]["threshold"])

    for token in tokens:
        known_ukrainian = bool(vesum_matches.get(token.normalized))
        is_anchor = token.normalized in anchors or RUSSIAN_ORTHOGRAPHY_RE.search(token.normalized) is not None
        is_phonetic = token.normalized in phonetic_map
        touches_hyphen = bool(
            (token.start_char > 0 and text[token.start_char - 1] in "-‐‑‒–—")
            or (token.end_char < len(text) and text[token.end_char] in "-‐‑‒–—")
        )
        heritage_possible = bool(
            not known_ukrainian
            and not token.surface[:1].isupper()
            and len(token.normalized) >= int(config["prefilter"]["min_heritage_form_chars"])
            and not touches_hyphen
            and runtime.heritage is not None
            and runtime.heritage.may_attest(token.normalized)
        )
        should_query_morph = bool(
            is_anchor
            or token.index in adjacent_unknown
            or heritage_possible
            or runtime.r2u.has_surface_match(token.normalized)
        )
        if not should_query_morph and not is_phonetic:
            runtime.expensive_lookups_avoided += 1
            continue
        if should_query_morph:
            ru = runtime.ru_morph.lookup(token.normalized)
            ru_by_token[token.index] = ru
            high_ru = float(ru["confidence"]) >= threshold
            if high_ru:
                r2u = runtime.r2u.lookup(token.normalized, ru.get("lemma"))
                r2u_by_token[token.index] = r2u
                if heritage_possible and runtime.heritage is not None:
                    heritage = runtime.heritage.lookup(token.normalized)
                    heritage_by_token[token.index] = heritage
                if is_anchor:
                    seeds.append(Seed(token.index, token.index, "russian_anchor", token.normalized))
                if r2u.get("status") == "hit" and not known_ukrainian:
                    seeds.append(Seed(token.index, token.index, "r2u_ru_morph", token.normalized))
                if (
                    heritage_by_token.get(token.index, {}).get("status") == "hit"
                    and not token.surface[:1].isupper()
                ):
                    seeds.append(Seed(token.index, token.index, "heritage_rescue", token.normalized))
                if token.index in adjacent_unknown:
                    seeds.append(Seed(token.index, token.index, "adjacent_unknown_ru_morph", token.normalized))
        if (
            token.surface[:1].isupper()
            and RUSSIAN_ORTHOGRAPHY_RE.search(token.normalized) is not None
            and not known_ukrainian
        ):
            seeds.append(Seed(token.index, token.index, "proper_name_orthography", token.normalized))
        if is_phonetic:
            seeds.append(Seed(token.index, token.index, "phonetic_mapping", f"{token.normalized}->{phonetic_map[token.normalized]}"))
    return seeds, ru_by_token, r2u_by_token, heritage_by_token


def _role_for_seed(seed: Seed, tokens: Sequence[TokenSpan], structures: Sequence[DetectionSpan]) -> str:
    token = tokens[seed.start_token]
    structure = _containing_structure(token.start_char, tokens[seed.end_token].end_char, structures)
    return structure.discourse_role if structure else "narration"


def _cluster_seeds(
    seeds: Sequence[Seed],
    tokens: Sequence[TokenSpan],
    structures: Sequence[DetectionSpan],
    max_gap_tokens: int,
    max_core_chars: int,
) -> list[list[Seed]]:
    ordered = sorted(seeds, key=lambda seed: (seed.start_token, seed.end_token, seed.kind, seed.detail))
    clusters: list[list[Seed]] = []
    for seed in ordered:
        if not clusters:
            clusters.append([seed])
            continue
        current = clusters[-1]
        start = min(item.start_token for item in current)
        end = max(item.end_token for item in current)
        same_role = _role_for_seed(seed, tokens, structures) == _role_for_seed(current[0], tokens, structures)
        merged_chars = tokens[max(end, seed.end_token)].end_char - tokens[min(start, seed.start_token)].start_char
        if same_role and seed.start_token - end <= max_gap_tokens + 1 and merged_chars <= max_core_chars:
            current.append(seed)
        else:
            clusters.append([seed])
    return clusters


def _bounded_candidate_span(
    *,
    text: str,
    tokens: Sequence[TokenSpan],
    structures: Sequence[DetectionSpan],
    cluster: Sequence[Seed],
    context_tokens: int,
    max_chars: int,
) -> tuple[int, int, int, int, str, str] | None:
    core_first = min(seed.start_token for seed in cluster)
    core_last = max(seed.end_token for seed in cluster)
    core_start = tokens[core_first].start_char
    core_end = tokens[core_last].end_char
    if core_end - core_start > max_chars:
        return None
    structure = _containing_structure(core_start, core_end, structures)
    if structure:
        lower, upper = structure.start_char, structure.end_char
        role = structure.discourse_role
        boundary_kind = structure.boundary_kind
    else:
        lower, upper = _paragraph_bounds(text, core_start, core_end)
        lower, upper = _sentence_bounds(text, core_start, core_end, lower, upper)
        role = "narration"
        boundary_kind = "sentence_or_paragraph"
    first = max(0, core_first - context_tokens)
    last = min(len(tokens) - 1, core_last + context_tokens)
    while first < core_first and tokens[first].start_char < lower:
        first += 1
    while last > core_last and tokens[last].end_char > upper:
        last -= 1
    start = max(lower, tokens[first].start_char)
    end = min(upper, tokens[last].end_char)
    while end - start > max_chars and (first < core_first or last > core_last):
        left_context = core_start - start
        right_context = end - core_end
        if right_context >= left_context and last > core_last:
            last -= 1
            end = min(upper, tokens[last].end_char)
        elif first < core_first:
            first += 1
            start = max(lower, tokens[first].start_char)
        else:
            break
    if end <= start or end - start > max_chars:
        return None
    return start, end, core_start, core_end, role, boundary_kind


def _reconstruct_phonetic(
    *,
    cluster: Sequence[Seed],
    tokens: Sequence[TokenSpan],
    config: Mapping[str, Any],
    runtime: EvidenceRuntime,
) -> list[dict[str, Any]]:
    mappings = {normalize_form(key): normalize_form(value) for key, value in config["reconstruction"]["mappings"].items()}
    mapped_indices = sorted(
        {
            index
            for seed in cluster
            if seed.kind == "phonetic_mapping"
            for index in range(seed.start_token, seed.end_token + 1)
            if tokens[index].normalized in mappings
        }
    )
    anchor_count = sum(seed.kind == "russian_anchor" for seed in cluster)
    if len(mapped_indices) < 2 and not (mapped_indices and anchor_count):
        return []
    results: list[dict[str, Any]] = []
    threshold = float(config["reconstruction"]["score_threshold"])
    for index in mapped_indices[: int(config["reconstruction"]["max_candidates_per_span"])]:
        token = tokens[index]
        target = mappings[token.normalized]
        ru = runtime.ru_morph.lookup(target)
        r2u = runtime.r2u.lookup(target, ru.get("lemma"))
        validated = float(ru["confidence"]) >= threshold and r2u["status"] == "hit"
        results.append(
            {
                "original_surface": token.surface,
                "reconstructed_surface": target,
                "reconstructed_lemma": str(ru.get("lemma") or ""),
                "transformation_path": [f"configured:{token.normalized}->{target}"],
                "ru_morph": ru,
                "r2u_cache": r2u,
                "validated": validated,
            }
        )
    return results


def _classify_cluster(
    *,
    cluster: Sequence[Seed],
    tokens: Sequence[TokenSpan],
    role: str,
    period: str,
    register: str,
    vesum_matches: Mapping[str, Sequence[Mapping[str, Any]]],
    ru_by_token: Mapping[int, Mapping[str, Any]],
    r2u_by_token: Mapping[int, Mapping[str, Any]],
    heritage_by_token: Mapping[int, Mapping[str, Any]],
    reconstructions: Sequence[Mapping[str, Any]],
    threshold: float,
) -> dict[str, str] | None:
    kinds = {seed.kind for seed in cluster}
    if "ocr_or_encoding" in kinds:
        return _classification("ocr_or_encoding_candidate", "uncertain", "ocr_or_encoding_candidate", role, "human_review_required", "high", "technical_review")
    if "other_language_run" in kinds:
        return _classification("other_language", "other_language", "standard_orthography", role, "retain_with_language_metadata", "high", "retain_other_language")
    valid = [seed for seed in cluster if seed.kind.startswith("vetted_")]
    if valid:
        return _classification("valid_word_contact_candidate", "ukrainian", "standard_orthography", role, "correction_candidate", "medium", "valid_word_review")

    suspicious_indices = sorted({index for seed in cluster for index in range(seed.start_token, seed.end_token + 1)})
    heritage_hits = [index for index in suspicious_indices if heritage_by_token.get(index, {}).get("status") == "hit"]
    high_ru = [
        index
        for index in suspicious_indices
        if float(ru_by_token.get(index, {}).get("confidence", 0.0)) >= threshold
    ]
    r2u_hits = [index for index in suspicious_indices if r2u_by_token.get(index, {}).get("status") == "hit"]
    anchors = [seed for seed in cluster if seed.kind == "russian_anchor"]
    adjacency_hits = [seed for seed in cluster if seed.kind == "adjacent_unknown_ru_morph"]
    valid_reconstructions = [item for item in reconstructions if item.get("validated") is True]

    if heritage_hits and high_ru:
        return _classification("protected_authentic_ukrainian", "ukrainian", "standard_orthography", role, "protected_historical_or_register_variation", "high", "protected_rescue")
    if (period in PROTECTED_PERIODS or any(item in register.casefold() for item in PROTECTED_REGISTER_FRAGMENTS)) and (high_ru or anchors or valid_reconstructions):
        return _classification("historical_unresolved", "historical_east_slavic_unresolved", "historical_orthography", role, "protected_historical_or_register_variation", "medium", "historical_review")
    if valid_reconstructions:
        return _classification("ukrainian_phonetic_russian", "russian", "ukrainian_phonetic_rendering_of_russian", role, "retain_with_language_metadata", "high", "unresolved_review")

    capitalized_specific = [
        index
        for index in suspicious_indices
        if tokens[index].surface[:1].isupper() and RUSSIAN_ORTHOGRAPHY_RE.search(tokens[index].normalized)
    ]
    lower_high_ru = [index for index in high_ru if index not in capitalized_specific]

    corroborated = bool(high_ru) and bool(r2u_hits or anchors)
    adjacent_corroborated = len(set(high_ru)) >= 2 and len(adjacency_hits) >= 2
    quoted_role = role in {
        "quotation",
        "dialogue",
        "epigraph",
        "citation_or_document",
        "metalinguistic_example",
    }
    # A structural quote plus an R2U hit or configured Russian anchor is
    # enough to route quoted Russian.  Two Russian-morphology hits alone are
    # not: creative, dialectal, and historical Ukrainian frequently produces
    # that pattern and must stay explicitly uncertain.
    if capitalized_specific and not lower_high_ru and quoted_role:
        return _classification("uncertain", "uncertain", "standard_orthography", role, "human_review_required", "low", "unresolved_review")
    if quoted_role and corroborated:
        return _classification("russian_quotation", "russian", "standard_orthography", role, "mask_from_modern_ukrainian_loss", "high", "quoted_russian")
    if capitalized_specific and not lower_high_ru:
        return _classification("proper_name", "uncertain", "standard_orthography", role, "retain_faithful", "medium", "proper_name_review")
    if not corroborated and not adjacent_corroborated:
        return None
    if adjacent_corroborated and not corroborated:
        return _classification("uncertain", "uncertain", "standard_orthography", role, "human_review_required", "medium", "unresolved_review")
    known_ukrainian = sum(bool(vesum_matches.get(tokens[index].normalized)) for index in suspicious_indices)
    if len(set(high_ru)) >= 2 and known_ukrainian:
        return _classification("mixed_surzhyk_candidate", "mixed_ukrainian_russian", "standard_orthography", role, "human_review_required", "medium", "unresolved_review")
    return _classification("modern_narration_interference", "russian", "standard_orthography", role, "correction_candidate", "high", "modern_interference_review")


def _classification(
    category: str,
    language_identity: str,
    representation: str,
    discourse_role: str,
    downstream_disposition: str,
    confidence: str,
    queue_route: str,
) -> dict[str, str]:
    return {
        "category": category,
        "language_identity": language_identity,
        "representation": representation,
        "discourse_role": discourse_role,
        "downstream_disposition": downstream_disposition,
        "confidence": confidence,
        "queue_route": queue_route,
    }


def _candidate_evidence(
    *,
    cluster: Sequence[Seed],
    tokens: Sequence[TokenSpan],
    vesum_matches: Mapping[str, Sequence[Mapping[str, Any]]],
    ru_by_token: Mapping[int, Mapping[str, Any]],
    r2u_by_token: Mapping[int, Mapping[str, Any]],
    heritage_by_token: Mapping[int, Mapping[str, Any]],
    reconstructions: Sequence[Mapping[str, Any]],
    runtime: EvidenceRuntime,
    config: Mapping[str, Any],
) -> dict[str, Any]:
    core_indices = {
        index
        for seed in cluster
        for index in range(seed.start_token, seed.end_token + 1)
    }
    evidence_tokens = [token for token in tokens if token.index in core_indices]
    queried_ru = [dict(ru_by_token[token.index]) for token in evidence_tokens if token.index in ru_by_token]
    queried_r2u = [
        {"surface": token.normalized, **dict(r2u_by_token[token.index])}
        for token in evidence_tokens
        if token.index in r2u_by_token
    ]
    queried_heritage = [
        dict(heritage_by_token[token.index]) for token in evidence_tokens if token.index in heritage_by_token
    ]
    valid_routes = [
        {"route_type": seed.kind, "evidence_key": seed.detail}
        for seed in cluster
        if seed.kind.startswith("vetted_")
    ]
    return {
        "vesum": {
            "adapter_id": str(config["vesum"]["interface"]),
            "snapshot_id": str(config["vesum"]["snapshot_id"]),
            "status": "used",
            "tokens": [
                {
                    "surface": token.surface,
                    "lookup_form": token.normalized,
                    "analyses": list(vesum_matches.get(token.normalized, [])),
                }
                for token in evidence_tokens
            ],
        },
        "russian_morphology": {
            "adapter_id": "scripts.verification.check_ru_morph.get_ru_confidence",
            "status": "used" if queried_ru else "not_queried",
            "tokens": queried_ru,
        },
        "r2u": {
            "adapter_id": "scripts.rag.source_query.r2u_translate",
            "cache_id": runtime.r2u.cache_id,
            "status": "used" if queried_r2u or reconstructions else "not_queried",
            "lookups": queried_r2u,
        },
        "heritage": {
            "adapter_id": "scripts.lexicon.load_relation_candidates.RelationHeritageLookup",
            "database": str(config["heritage"]["database"]),
            "status": (
                "used"
                if queried_heritage
                else "not_queried"
                if runtime.heritage_available
                else "adapter_unavailable"
            ),
            "lookups": queried_heritage,
        },
        "external_pending": [
            {
                "adapter_id": "scripts.rag.source_query.ulif_lookup",
                "dictionary_identity": "ULIF DictUA underlying module pending",
                "status": "lookup_pending" if valid_routes else "not_queried",
            },
            {
                "adapter_id": "scripts.rag.source_query.slovnyk_me_lookup",
                "dictionary_identity": "underlying slovnyk.me dictionary not selected",
                "status": "lookup_pending" if valid_routes or queried_heritage else "not_queried",
            },
        ],
        "reconstruction_candidates": list(reconstructions),
        "valid_word_routes": valid_routes,
        "network_performed": False,
    }


def run_detector_on_text(
    *,
    text: str,
    record_id: str,
    locator: str,
    source_family: str,
    source_record_id: str,
    period: str,
    register: str,
    origin: str,
    vesum_matches: Mapping[str, Sequence[Mapping[str, Any]]],
    config: Mapping[str, Any] | None = None,
    runtime: EvidenceRuntime | None = None,
    candidate_validator: Draft202012Validator | None = None,
    input_root: Path = ROOT,
) -> list[dict[str, Any]]:
    """Emit only positively evidenced, bounded candidates from one record."""
    active_config = dict(config or _load_and_validate_config(DEFAULT_CONFIG_PATH))
    owns_runtime = runtime is None
    active_runtime = runtime or EvidenceRuntime(active_config, input_root)
    try:
        tokens = tokenize_with_offsets(text)
        if not tokens:
            active_runtime.rows_without_prefilter_signal += 1
            return []
        structures = segment_structure(text)
        seeds, ru_by_token, r2u_by_token, heritage_by_token = _seed_record(
            text=text,
            tokens=tokens,
            vesum_matches=vesum_matches,
            config=active_config,
            runtime=active_runtime,
        )
        if not seeds:
            active_runtime.rows_without_prefilter_signal += 1
            return []
        active_runtime.rows_with_prefilter_signal += 1
        span_config = active_config["span"]
        clusters = _cluster_seeds(
            seeds,
            tokens,
            structures,
            int(span_config["max_cluster_gap_tokens"]),
            int(span_config["max_chars"]),
        )
        record_hash = sha256_text(text)
        candidates: list[dict[str, Any]] = []
        active_validator = candidate_validator or Draft202012Validator(_load_json(CANDIDATE_SCHEMA_PATH))
        seen: set[tuple[int, int, str]] = set()
        for cluster in clusters:
            bounded = _bounded_candidate_span(
                text=text,
                tokens=tokens,
                structures=structures,
                cluster=cluster,
                context_tokens=int(span_config["context_tokens"]),
                max_chars=int(span_config["max_chars"]),
            )
            if bounded is None:
                active_runtime.offsets_rejected += 1
                continue
            start, end, core_start, core_end, role, boundary_kind = bounded
            reconstructions = _reconstruct_phonetic(
                cluster=cluster,
                tokens=tokens,
                config=active_config,
                runtime=active_runtime,
            )
            classification = _classify_cluster(
                cluster=cluster,
                tokens=tokens,
                role=role,
                period=period,
                register=register,
                vesum_matches=vesum_matches,
                ru_by_token=ru_by_token,
                r2u_by_token=r2u_by_token,
                heritage_by_token=heritage_by_token,
                reconstructions=reconstructions,
                threshold=float(active_config["ru_morph"]["threshold"]),
            )
            if classification is None:
                continue
            dedupe = (core_start, core_end, classification["category"])
            if dedupe in seen:
                continue
            seen.add(dedupe)
            span_text = text[start:end]
            candidate = {
                "schema_version": CANDIDATE_SCHEMA_VERSION,
                "source_record_id": source_record_id,
                "source_family": source_family,
                "locator": locator,
                "record_id": record_id,
                "record_hash": record_hash,
                "span": {
                    "start_char": start,
                    "end_char": end,
                    "core_start_char": core_start,
                    "core_end_char": core_end,
                    "original_text": span_text,
                    "span_hash": sha256_text(span_text),
                    "boundary_kind": boundary_kind,
                    "max_chars": int(span_config["max_chars"]),
                },
                "classification": {key: value for key, value in classification.items() if key != "queue_route"},
                "metadata": {"period": period, "register": register, "origin": origin},
                "evidence": _candidate_evidence(
                    cluster=cluster,
                    tokens=tokens,
                    vesum_matches=vesum_matches,
                    ru_by_token=ru_by_token,
                    r2u_by_token=r2u_by_token,
                    heritage_by_token=heritage_by_token,
                    reconstructions=reconstructions,
                    runtime=active_runtime,
                    config=active_config,
                ),
                "automatic_error_label": False,
                "review_state": "unresolved",
                "queue_route": classification["queue_route"],
            }
            errors = sorted(active_validator.iter_errors(candidate), key=lambda item: list(item.path))
            if errors:
                path = ".".join(str(value) for value in errors[0].path) or "<root>"
                raise ValueError(f"candidate schema violation at {path}: {errors[0].message}")
            candidates.append(candidate)
        return candidates
    finally:
        if owns_runtime:
            active_runtime.close()


def _iter_batches(cursor: sqlite3.Cursor, batch_size: int) -> Iterator[list[sqlite3.Row]]:
    while rows := cursor.fetchmany(batch_size):
        yield rows


def _dimension(row: sqlite3.Row, source: Mapping[str, Any], name: str) -> str:
    dimension = source["adapter"]["dimensions"].get(name, {})
    if dimension.get("constant"):
        return str(dimension["constant"])
    key = "__" + name
    try:
        value = row[key]
    except IndexError:
        return "unknown"
    return str(value or "unknown")


def _runtime_evidence_receipt(runtime: EvidenceRuntime) -> dict[str, Any]:
    heritage = runtime.heritage
    return {
        "vesum": {
            "adapter_id": "scripts.verification.vesum.verify_words",
            "lookup_batches": runtime.vesum.lookup_batches,
            "forms_queried": runtime.vesum.forms_queried,
            "cache_hits": runtime.vesum.cache.hits,
        },
        "russian_morphology": {
            "adapter_id": "scripts.verification.check_ru_morph.get_ru_confidence",
            "lookups": runtime.ru_morph.calls,
            "cache_hits": runtime.ru_morph.cache.hits,
        },
        "heritage": {
            "adapter_id": "scripts.lexicon.load_relation_candidates.RelationHeritageLookup",
            "status": "available" if runtime.heritage_available else "adapter_unavailable",
            "lookups": heritage.lookups if heritage else 0,
            "hits": heritage.hits if heritage else 0,
            "misses": heritage.misses if heritage else 0,
            "cache_hits": heritage.detail_cache.hits if heritage else 0,
        },
        "r2u": {
            "adapter_id": "scripts.rag.source_query.r2u_translate",
            "mode": "bounded_hashed_local_cache",
            "cache_id": runtime.r2u.cache_id,
            "lookups": runtime.r2u.lookups,
            "hits": runtime.r2u.hits,
            "misses": runtime.r2u.misses,
        },
        "ulif": {"status": "lookup_pending", "network_lookups_performed": 0},
        "slovnyk_me": {"status": "lookup_pending", "network_lookups_performed": 0},
        "network": {
            "prohibited_during_run": True,
            "lookups_performed": 0,
            "expensive_local_lookups_avoided": runtime.expensive_lookups_avoided,
        },
    }


def stream_detector(
    *,
    config_path: Path,
    input_root: Path,
    summary_output: Path,
    candidates_output: Path,
) -> DetectorRunResult:
    """Stream the configured corpus with bounded memory and deterministic bytes."""
    config = _load_and_validate_config(config_path)
    runtime = EvidenceRuntime(config, input_root)
    expected_rows = sum(source["expected"]["rows"] for source in config["sources"])
    expected_words = sum(source["expected"]["lexical_words"] for source in config["sources"])
    counts: Counter[str] = Counter()
    category_counts: Counter[str] = Counter()
    queue_counts: Counter[str] = Counter()
    dimensions = {name: Counter() for name in ("source_family", "period", "register")}
    source_results: list[dict[str, Any]] = []
    inaccessible_sources: list[dict[str, str]] = []
    samples: dict[tuple[str, str, str, str], str] = {}
    candidates_output.parent.mkdir(parents=True, exist_ok=True)
    candidate_handle = tempfile.NamedTemporaryFile(  # noqa: SIM115 - closed by the streaming block
        mode="w",
        encoding="utf-8",
        newline="\n",
        dir=candidates_output.parent,
        prefix=candidates_output.name,
        suffix=".tmp.jsonl",
        delete=False,
    )
    temporary_candidates = Path(candidate_handle.name)
    candidate_validator = Draft202012Validator(_load_json(CANDIDATE_SCHEMA_PATH))
    stream_succeeded = False
    try:
        with candidate_handle as output:
            for source in config["sources"]:
                database_path = input_root / source["adapter"]["database"]
                source_rows = source_words = 0
                connection: sqlite3.Connection | None = None
                try:
                    connection = _connect_read_only(database_path)
                    query, parameters = _source_query(source, _table_columns(connection, source["adapter"]["table"]))
                except (FileNotFoundError, sqlite3.Error, ValueError) as exc:
                    if connection is not None:
                        connection.close()
                    inaccessible_sources.append({"source_family": source["source_family"], "reason": type(exc).__name__})
                    continue
                with closing(connection):
                    cursor = connection.execute(query, parameters)
                    for rows in _iter_batches(cursor, int(config["record_batch_size"])):
                        prepared: list[tuple[sqlite3.Row, str, list[TokenSpan]]] = []
                        forms: set[str] = set()
                        for row in rows:
                            text = str(row["__text"] or "")
                            tokens = tokenize_with_offsets(text)
                            prepared.append((row, text, tokens))
                            forms.update(token.normalized for token in tokens)
                        vesum_matches = runtime.vesum.lookup(forms)
                        for row, text, tokens in prepared:
                            word_count = len(tokens)
                            source_rows += 1
                            source_words += word_count
                            counts["processed_rows"] += 1
                            counts["processed_lexical_words"] += word_count
                            record_id = str(row["__record_id"])
                            locator_value = str(row["__locator"])
                            locator = f"sqlite:{source['adapter']['database']}#{source['adapter']['table']}/{locator_value}"
                            period = _dimension(row, source, "period")
                            register = _dimension(row, source, "register")
                            origin = _dimension(row, source, "origin")
                            detected = run_detector_on_text(
                                text=text,
                                record_id=record_id,
                                locator=locator,
                                source_family=source["source_family"],
                                source_record_id=f"{source['inventory_asset_id']}:{record_id}",
                                period=period,
                                register=register,
                                origin=origin,
                                vesum_matches=vesum_matches,
                                config=config,
                                runtime=runtime,
                                candidate_validator=candidate_validator,
                                input_root=input_root,
                            )
                            for candidate in detected:
                                output.write(canonical_json(candidate) + "\n")
                                category = candidate["classification"]["category"]
                                queue_route = candidate["queue_route"]
                                category_counts[category] += 1
                                queue_counts[queue_route] += 1
                                dimensions["source_family"][source["source_family"]] += 1
                                dimensions["period"][period] += 1
                                dimensions["register"][register] += 1
                                key = (source["source_family"], category, period, register)
                                if key not in samples:
                                    span = candidate["span"]
                                    samples[key] = f"{locator}@{span['start_char']}:{span['end_char']}#{span['span_hash']}"
                expected = source["expected"]
                source_results.append(
                    {
                        "actual": {"rows": source_rows, "lexical_words": source_words},
                        "expected": expected,
                        "inventory_asset_id": source["inventory_asset_id"],
                        "matches_expected": source_rows == expected["rows"] and source_words == expected["lexical_words"],
                        "source_family": source["source_family"],
                    }
                )
        stream_succeeded = True
    finally:
        runtime.close()
        if not stream_succeeded:
            temporary_candidates.unlink(missing_ok=True)

    processed_rows = counts["processed_rows"]
    processed_words = counts["processed_lexical_words"]
    all_sources_match = len(source_results) == len(config["sources"]) and all(
        result["matches_expected"] for result in source_results
    )
    total_candidates = sum(category_counts.values())
    unresolved_routes = {
        key: value
        for key, value in sorted(queue_counts.items())
        if key in {"unresolved_review", "historical_review", "valid_word_review", "technical_review", "proper_name_review"}
    }
    receipt = {
        "schema_version": SCHEMA_VERSION,
        "detector_id": config["detector_id"],
        "source_snapshot_id": config["source_snapshot_id"],
        "coverage": {
            "complete": not inaccessible_sources and all_sources_match,
            "expected_rows": expected_rows,
            "expected_lexical_words": expected_words,
            "processed_rows": processed_rows,
            "processed_lexical_words": processed_words,
            "dropped_rows": max(0, expected_rows - processed_rows),
            "dropped_lexical_words": max(0, expected_words - processed_words),
            "inaccessible_sources": sorted(inaccessible_sources, key=lambda item: (item["source_family"], item["reason"])),
            "source_results": sorted(source_results, key=lambda item: item["source_family"]),
        },
        "candidate_arithmetic": {
            "total_candidates": total_candidates,
            "unresolved_review_queue": sum(unresolved_routes.values()),
            "protected_rescues": queue_counts["protected_rescue"],
            "quoted_russian": queue_counts["quoted_russian"],
            "modern_interference_candidates": queue_counts["modern_interference_review"],
            "other_routes": total_candidates
            - sum(unresolved_routes.values())
            - queue_counts["protected_rescue"]
            - queue_counts["quoted_russian"]
            - queue_counts["modern_interference_review"],
            "queue_route_counts": dict(sorted(queue_counts.items())),
        },
        "yields_by_category": dict(sorted(category_counts.items())),
        "yields_by_source_family": dict(sorted(dimensions["source_family"].items())),
        "yields_by_period": dict(sorted(dimensions["period"].items())),
        "yields_by_register": dict(sorted(dimensions["register"].items())),
        "offsets_rejected": runtime.offsets_rejected,
        "prefilter": {
            "rows_with_signal": runtime.rows_with_prefilter_signal,
            "rows_without_signal": runtime.rows_without_prefilter_signal,
        },
        "evidence_source_usage": _runtime_evidence_receipt(runtime),
        "deterministic_sample_locators": [samples[key] for key in sorted(samples)],
        "outputs": {
            "review_candidates": {
                "bytes": temporary_candidates.stat().st_size,
                "records": total_candidates,
                "sha256": sha256_file(temporary_candidates),
            }
        },
        "claims": {
            "correction_gold_created": False,
            "precision_or_recall_claimed": False,
            "source_admission_changed": False,
            "training_or_publication_performed": False,
        },
        "determinism": {
            "serialization": "UTF-8 canonical JSON with sorted keys and LF",
            "candidate_order": "config source order, SQLite record id, bounded span offset",
            "timestamps_omitted": True,
            "runtime_and_rss_omitted": True,
        },
    }
    receipt_temporary: Path | None = None
    try:
        if receipt["candidate_arithmetic"]["other_routes"] < 0:
            raise AssertionError("candidate route arithmetic became negative")
        if sum(queue_counts.values()) != total_candidates:
            raise AssertionError("queue-route arithmetic does not match candidates")
        for dimension_name, dimension_counts in dimensions.items():
            if sum(dimension_counts.values()) != total_candidates:
                raise AssertionError(
                    f"{dimension_name} arithmetic does not match candidates"
                )
        partition_total = (
            receipt["candidate_arithmetic"]["unresolved_review_queue"]
            + receipt["candidate_arithmetic"]["protected_rescues"]
            + receipt["candidate_arithmetic"]["quoted_russian"]
            + receipt["candidate_arithmetic"]["modern_interference_candidates"]
            + receipt["candidate_arithmetic"]["other_routes"]
        )
        if partition_total != total_candidates:
            raise AssertionError("candidate partition does not match total candidates")
        if (
            receipt["prefilter"]["rows_with_signal"]
            + receipt["prefilter"]["rows_without_signal"]
            != processed_rows
        ):
            raise AssertionError("prefilter row arithmetic does not match processed rows")
        validator = Draft202012Validator(_load_json(RECEIPT_SCHEMA_PATH))
        errors = sorted(validator.iter_errors(receipt), key=lambda item: list(item.path))
        if errors:
            path = ".".join(str(value) for value in errors[0].path) or "<root>"
            raise ValueError(f"receipt schema violation at {path}: {errors[0].message}")
        receipt_temporary = _stage_json(summary_output, receipt)
        _promote_staged_artifacts(
            [
                (temporary_candidates, candidates_output),
                (receipt_temporary, summary_output),
            ]
        )
    finally:
        temporary_candidates.unlink(missing_ok=True)
        if receipt_temporary is not None:
            receipt_temporary.unlink(missing_ok=True)
    return DetectorRunResult(receipt, summary_output, candidates_output)


def run_regression_tests(
    fixture_path: Path = DEFAULT_REGRESSION_FIXTURE,
    *,
    input_root: Path = ROOT,
) -> None:
    """Execute the frozen rights-safe regression fixture against real local evidence."""
    config = _load_and_validate_config(DEFAULT_CONFIG_PATH)
    runtime = EvidenceRuntime(config, input_root)
    fixture = _load_json(fixture_path)
    failures: list[str] = []
    try:
        for case in fixture.get("cases", []):
            tokens = tokenize_with_offsets(case["text"])
            vesum_matches = runtime.vesum.lookup(token.normalized for token in tokens)
            detected = run_detector_on_text(
                text=case["text"],
                record_id=case["id"],
                locator=f"sqlite:fixture.db#cases/{case['id']}",
                source_family=case["source_family"],
                source_record_id=f"fixture:{case['id']}",
                period=case["period"],
                register=case["register"],
                origin=case["origin"],
                vesum_matches=vesum_matches,
                config=config,
                runtime=runtime,
                input_root=input_root,
            )
            expected = case.get("expected_categories", [])
            actual = [candidate["classification"]["category"] for candidate in detected]
            if actual != expected:
                failures.append(f"{case['id']}: expected {expected}, got {actual}")
    finally:
        runtime.close()
    if failures:
        raise ValueError("regression failures:\n" + "\n".join(failures))


def main() -> None:
    parser = argparse.ArgumentParser(description="Ukrainian language-contact detector")
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG_PATH)
    parser.add_argument("--input-root", type=Path, default=ROOT)
    parser.add_argument(
        "--summary-output",
        type=Path,
        default=ROOT / "data/projects/open_model_data/detector/language_contact_receipt_v1.json",
    )
    parser.add_argument(
        "--candidates-output",
        type=Path,
        default=Path(tempfile.gettempdir()) / "language_contact_candidates_v1.jsonl",
    )
    parser.add_argument("--regression-test", action="store_true")
    args = parser.parse_args()
    if args.regression_test:
        run_regression_tests(input_root=args.input_root)
        return
    before = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    result = stream_detector(
        config_path=args.config,
        input_root=args.input_root,
        summary_output=args.summary_output,
        candidates_output=args.candidates_output,
    )
    after = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    print(
        canonical_json(
            {
                "candidate_sha256": result.summary["outputs"]["review_candidates"]["sha256"],
                "complete": result.complete,
                "lexical_words": result.summary["coverage"]["processed_lexical_words"],
                "max_rss_raw": max(before, after),
                "max_rss_unit": "platform_rusage_ru_maxrss",
                "rows": result.summary["coverage"]["processed_rows"],
            }
        )
    )


if __name__ == "__main__":
    main()
