#!/usr/bin/env python3
"""Materialize qualified-human UA-GEC edits as complete-context v3 records.

The frozen v2 UA-GEC denominator stores edit fragments.  This adapter proves
that every one of those 8,937 identities maps back to the pinned public
UA-GEC checkout, reconstructs the complete source and corrected sentence, and
emits only records that satisfy the shared v3 linguistic representation.

It does not assign a phenomenon, decide modern-Ukrainian eligibility, label
held-out gold, select an evaluation partition, or authorize source authoring.
"""

from __future__ import annotations

import argparse
import difflib
import hashlib
import json
import os
import re
import sqlite3
import stat
import subprocess
import sys
import tempfile
from collections import Counter, defaultdict, deque
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from jsonschema import Draft202012Validator

from scripts.audit import ingest_ua_gec_gold as ua_gold
from scripts.projects.open_model_data import phase3_linguistic_representation as representation
from scripts.projects.open_model_data import phase3_source_unit_materialization as v2_materializer
from scripts.projects.open_model_data import phase3_source_universe as v2_source

ROOT = Path(__file__).resolve().parents[3]
DATA = ROOT / "data/projects/open_model_data"
SCHEMA_PATH = DATA / "contracts/phase3_ua_gec_complete_context_receipt_v1.schema.json"
SCRIPT_PATH = Path(__file__).resolve()
V2_SOURCE_UNIVERSE = DATA / "evidence/source_universe_v1"
PRIVATE_FILENAME = "ua_gec_complete_context_v1.jsonl"
PRIVATE_EXCLUSIONS_FILENAME = "ua_gec_complete_context_exclusions_v1.jsonl"
SCHEMA_VERSION = "phase3_ua_gec_complete_context_receipt_v1"
IMPLEMENTATION_VERSION = "phase3_ua_gec_complete_context_v1"
UA_GEC_REPOSITORY = "https://github.com/grammarly/ua-gec"
UA_GEC_COMMIT = "4757f72f192c4a41e4c8fb1d9690a948f87cf6d6"
UA_GEC_LICENSE = "CC BY 4.0"
PHASE3_REBOOT_V3_SHA256 = "5f22c7fc84ce6ca6d497fcf0437d72274a0bdb3aa1cf48cfebfe196e67dbd11d"
PHASE3_RECOVERY_V2_SHA256 = "298591094d1281629ea444707909b679d1a5368f3ad8afddf39120bc0c34532b"
EXPECTED_TAG_COUNTS = {
    "F/Calque": 2_397,
    "F/Collocation": 459,
    "G/Case": 5_024,
    "G/Gender": 1_057,
}
EXPECTED_UNIT_COUNT = sum(EXPECTED_TAG_COUNTS.values())
PRIVATE_DIR_MODE = 0o700
PRIVATE_FILE_MODE = 0o600


class UaGecCompleteContextError(ValueError):
    """The frozen UA-GEC denominator cannot be reconstructed safely."""


def require(condition: bool, message: str) -> None:
    if not condition:
        raise UaGecCompleteContextError(message)


def canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"), sort_keys=True)


def canonical_bytes(value: Any) -> bytes:
    return (canonical_json(value) + "\n").encode("utf-8")


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    try:
        with Path(path).open("rb") as stream:
            for chunk in iter(lambda: stream.read(1024 * 1024), b""):
                digest.update(chunk)
    except OSError as exc:
        raise UaGecCompleteContextError(f"cannot read artifact: {path}") from exc
    return digest.hexdigest()


def utc_now() -> str:
    return datetime.now(UTC).isoformat(timespec="seconds").replace("+00:00", "Z")


def _parse_timestamp(value: str, label: str) -> datetime:
    require(value.endswith("Z"), f"{label} must be UTC with a Z suffix")
    try:
        parsed = datetime.fromisoformat(value[:-1] + "+00:00")
    except ValueError as exc:
        raise UaGecCompleteContextError(f"{label} is not an ISO-8601 timestamp") from exc
    require(parsed.tzinfo == UTC, f"{label} must be UTC")
    return parsed


def _regular_file(path: Path, label: str) -> None:
    try:
        result = path.lstat()
    except OSError as exc:
        raise UaGecCompleteContextError(f"missing {label}: {path}") from exc
    require(stat.S_ISREG(result.st_mode) and not path.is_symlink(), f"{label} must be a regular file")


def _checkout_commit(checkout: Path) -> str:
    require(checkout.is_dir() and not checkout.is_symlink(), "UA-GEC checkout must be a real directory")
    try:
        result = subprocess.run(
            ["git", "-C", str(checkout), "rev-parse", "HEAD"],
            check=True,
            capture_output=True,
            text=True,
        )
    except (OSError, subprocess.CalledProcessError) as exc:
        raise UaGecCompleteContextError("cannot verify UA-GEC checkout commit") from exc
    commit = result.stdout.strip()
    require(commit == UA_GEC_COMMIT, "UA-GEC checkout is not at the pinned commit")
    try:
        status_result = subprocess.run(
            ["git", "-C", str(checkout), "status", "--porcelain=v1", "--untracked-files=no"],
            check=True,
            capture_output=True,
            text=True,
        )
    except (OSError, subprocess.CalledProcessError) as exc:
        raise UaGecCompleteContextError("cannot verify UA-GEC checkout cleanliness") from exc
    require(not status_result.stdout, "UA-GEC checkout has modified tracked files")
    return commit


def _normalize_edit_text(value: str) -> str:
    return re.sub(r"\s+", " ", value.strip())


def _annotation_key(
    partition: str,
    doc_id: str,
    annotator_id: str,
    tag: str,
    error: str,
    correction: str,
) -> tuple[str, str, str, str, str, str]:
    return (
        partition,
        doc_id,
        annotator_id,
        tag,
        _normalize_edit_text(error),
        _normalize_edit_text(correction),
    )


@dataclass(frozen=True, slots=True)
class RawAnnotation:
    """One parsed annotation plus its exact inline evidence bytes."""

    raw: str
    tag: str
    error: str
    correction: str
    source_start: int
    source_end: int
    target_start: int
    target_end: int
    raw_source_start: int
    raw_source_end: int
    raw_target_start: int
    raw_target_end: int
    line: int
    occurrence: int


@dataclass(frozen=True, slots=True)
class ParsedAnnotatedDocument:
    """A UA-GEC annotation file projected to source/target text."""

    source_text: str
    corrected_text: str
    annotations: tuple[RawAnnotation, ...]


@dataclass(frozen=True, slots=True)
class ContextWindow:
    """Absolute complete-sentence bounds in source and corrected documents."""

    source_start: int
    source_end: int
    target_start: int
    target_end: int
    source_document_start: int
    source_document_end: int
    target_document_start: int
    target_document_end: int


@dataclass(frozen=True, slots=True)
class TargetSentence:
    """One exact line from target-sentences aligned to parsed corrected text."""

    target_start: int
    target_end: int
    target_document_start: int
    target_document_end: int
    line: int


@dataclass(frozen=True, slots=True)
class SourceSentence:
    """One exact line from source-sentences aligned to parsed source text."""

    source_start: int
    source_end: int
    source_document_start: int
    source_document_end: int
    line: int


def parse_annotated_document(text: str) -> ParsedAnnotatedDocument:
    """Parse an entire annotated file without dropping source context."""
    parsed = ua_gold.parse_annotated_text(text)
    matches = list(ua_gold.UA_GEC_ANN_RE.finditer(text))
    require(len(matches) == len(parsed.annotations), "UA-GEC annotation parser occurrence drift")
    raw_bounds: list[tuple[int, int, int, int]] = []
    last = 0
    source_position = 0
    target_position = 0
    for match in matches:
        prefix = text[last : match.start()]
        source_position += len(prefix)
        target_position += len(prefix)
        raw_error = match.group(1)
        raw_correction = match.group(2)
        raw_bounds.append(
            (
                source_position,
                source_position + len(raw_error),
                target_position,
                target_position + len(raw_correction),
            )
        )
        source_position += len(raw_error)
        target_position += len(raw_correction)
        last = match.end()
    annotations = tuple(
        RawAnnotation(
            raw=match.group(0),
            tag=annotation.tag,
            error=annotation.error,
            correction=annotation.correction,
            source_start=annotation.source_start,
            source_end=annotation.source_end,
            target_start=annotation.target_start,
            target_end=annotation.target_end,
            raw_source_start=bounds[0],
            raw_source_end=bounds[1],
            raw_target_start=bounds[2],
            raw_target_end=bounds[3],
            line=annotation.line,
            occurrence=index,
        )
        for index, (match, annotation, bounds) in enumerate(
            zip(matches, parsed.annotations, raw_bounds, strict=True), start=1
        )
    )
    return ParsedAnnotatedDocument(parsed.source_text, parsed.target_text, annotations)


def _target_sentences(parsed: ParsedAnnotatedDocument, target_document: str) -> list[TargetSentence]:
    """Align authoritative target-sentences lines to the parsed target stream.

    Punctuation heuristics split abbreviations such as ``Св.`` and therefore
    cannot establish complete sentence context.  UA-GEC's target-sentences
    files are the immutable sentence-boundary authority.  Lines that do not
    occur exactly in the parsed target are left unmatched; affected frozen
    units are excluded explicitly later.
    """
    sentences: list[TargetSentence] = []
    parsed_cursor = 0
    document_cursor = 0
    for line_number, raw_line in enumerate(target_document.splitlines(keepends=True), start=1):
        line_without_break = raw_line.rstrip("\r\n")
        leading = len(line_without_break) - len(line_without_break.lstrip())
        text = line_without_break.strip()
        document_start = document_cursor + leading
        document_end = document_start + len(text)
        document_cursor += len(raw_line)
        if not text:
            continue
        target_start = parsed.corrected_text.find(text, parsed_cursor)
        if target_start < 0:
            continue
        target_end = target_start + len(text)
        sentences.append(
            TargetSentence(
                target_start=target_start,
                target_end=target_end,
                target_document_start=document_start,
                target_document_end=document_end,
                line=line_number,
            )
        )
        parsed_cursor = target_end
    return sentences


def _source_sentences(parsed: ParsedAnnotatedDocument, source_document: str) -> list[SourceSentence]:
    """Align authoritative source-sentences lines to the parsed source stream."""
    sentences: list[SourceSentence] = []
    parsed_cursor = 0
    document_cursor = 0
    for line_number, raw_line in enumerate(source_document.splitlines(keepends=True), start=1):
        line_without_break = raw_line.rstrip("\r\n")
        leading = len(line_without_break) - len(line_without_break.lstrip())
        text = line_without_break.strip()
        document_start = document_cursor + leading
        document_end = document_start + len(text)
        document_cursor += len(raw_line)
        if not text:
            continue
        source_start = parsed.source_text.find(text, parsed_cursor)
        if source_start < 0:
            continue
        source_end = source_start + len(text)
        sentences.append(
            SourceSentence(
                source_start=source_start,
                source_end=source_end,
                source_document_start=document_start,
                source_document_end=document_end,
                line=line_number,
            )
        )
        parsed_cursor = source_end
    return sentences


def _sentence_for_annotation(annotation: RawAnnotation, sentences: Sequence[TargetSentence]) -> TargetSentence | None:
    candidates = []
    for sentence in sentences:
        if annotation.target_start == annotation.target_end:
            contains = sentence.target_start <= annotation.target_start <= sentence.target_end
        else:
            contains = sentence.target_start <= annotation.target_start and annotation.target_end <= sentence.target_end
        if contains:
            candidates.append(sentence)
    if not candidates:
        return None
    return min(candidates, key=lambda item: (item.target_end - item.target_start, item.target_start))


def _target_boundary_to_source(parsed: ParsedAnnotatedDocument, position: int, *, right_bias: bool) -> int:
    """Map a parsed-target boundary to source coordinates using inline edits."""
    require(0 <= position <= len(parsed.corrected_text), "target boundary is outside parsed target")
    source_cursor = 0
    target_cursor = 0
    for annotation in parsed.annotations:
        if position < annotation.raw_target_start:
            return source_cursor + (position - target_cursor)
        if position == annotation.raw_target_start:
            if annotation.raw_target_start == annotation.raw_target_end and right_bias:
                return annotation.raw_source_end
            return annotation.raw_source_start
        if position < annotation.raw_target_end:
            return annotation.raw_source_end if right_bias else annotation.raw_source_start
        if position == annotation.raw_target_end:
            return annotation.raw_source_end
        source_cursor = annotation.raw_source_end
        target_cursor = annotation.raw_target_end
    return source_cursor + (position - target_cursor)


def _context_window(
    parsed: ParsedAnnotatedDocument,
    sentence: TargetSentence,
    source_sentences: Sequence[SourceSentence],
) -> ContextWindow | None:
    source_start = _target_boundary_to_source(parsed, sentence.target_start, right_bias=False)
    source_end = _target_boundary_to_source(parsed, sentence.target_end, right_bias=True)
    require(0 <= source_start <= source_end <= len(parsed.source_text), "aligned source sentence is invalid")
    source_sentence = next(
        (item for item in source_sentences if item.source_start == source_start and item.source_end == source_end),
        None,
    )
    if source_sentence is None:
        return None
    return ContextWindow(
        source_start=source_start,
        source_end=source_end,
        target_start=sentence.target_start,
        target_end=sentence.target_end,
        source_document_start=source_sentence.source_document_start,
        source_document_end=source_sentence.source_document_end,
        target_document_start=sentence.target_document_start,
        target_document_end=sentence.target_document_end,
    )


def _edits(source: str, target: str) -> list[dict[str, Any]]:
    matcher = difflib.SequenceMatcher(a=source, b=target, autojunk=False)
    edits: list[dict[str, Any]] = []
    for operation, source_start, source_end, target_start, target_end in matcher.get_opcodes():
        if operation == "equal":
            continue
        edits.append(
            {
                "start": source_start,
                "end": source_end,
                "replacement": target[target_start:target_end],
            }
        )
    require(edits, "qualified-human context has no effective correction")
    return edits


def _contains_lexical(text: str) -> bool:
    return any(character.isalpha() or character.isdigit() for character in text)


def _edit_shape(source: str, edits: Sequence[Mapping[str, Any]]) -> str:
    if all(not _contains_lexical(source[item["start"] : item["end"]] + str(item["replacement"])) for item in edits):
        return "punctuation_only"
    if len(edits) > 1:
        return "multi_edit"
    edit = edits[0]
    original = source[edit["start"] : edit["end"]]
    replacement = str(edit["replacement"])
    if edit["start"] == edit["end"]:
        return "insertion"
    if not replacement:
        return "deletion"
    source_tokens = [item["normalized_text"].casefold() for item in representation.tokenize(original)]
    target_tokens = [item["normalized_text"].casefold() for item in representation.tokenize(replacement)]
    if len(source_tokens) >= 2 and source_tokens != target_tokens and Counter(source_tokens) == Counter(target_tokens):
        return "reordering"
    return "substitution"


def _target_path(checkout: Path, annotation_path: Path) -> Path:
    relative = annotation_path.relative_to(checkout / "data")
    require(len(relative.parts) == 4 and relative.parts[2] == "annotated", "unexpected UA-GEC annotation path")
    return (
        checkout / "data" / relative.parts[0] / relative.parts[1] / "target-sentences" / (annotation_path.stem + ".txt")
    )


def _source_sentence_path(checkout: Path, annotation_path: Path) -> Path:
    relative = annotation_path.relative_to(checkout / "data")
    require(len(relative.parts) == 4 and relative.parts[2] == "annotated", "unexpected UA-GEC annotation path")
    match = re.fullmatch(r"(?P<doc_id>[^.]+)\.a\d+", annotation_path.stem)
    require(match is not None, "unexpected UA-GEC document name")
    return (
        checkout
        / "data"
        / relative.parts[0]
        / relative.parts[1]
        / "source-sentences"
        / (match.group("doc_id") + ".src.txt")
    )


def _path_identity(checkout: Path, path: Path) -> tuple[str, str, str]:
    relative = path.relative_to(checkout / "data")
    require(len(relative.parts) == 4, "unexpected UA-GEC document path")
    match = re.fullmatch(r"(?P<doc_id>[^.]+)\.a(?P<annotator>\d+)", path.stem)
    require(match is not None, "unexpected UA-GEC document name")
    return f"{relative.parts[0]}/{relative.parts[1]}", match.group("doc_id"), match.group("annotator")


def _load_v2_units(source_universe: Path, database: Path) -> list[dict[str, Any]]:
    ledgers, _receipt_hash = v2_materializer._load_freeze(source_universe)
    _regular_file(database, "sources database")
    source_hash = sha256_file(database)
    try:
        with v2_source._connect(database) as connection:
            rows = v2_materializer._rebuild_database(connection, "ua_gec", ledgers["ua_gec"], source_hash)
    except (sqlite3.Error, v2_materializer.MaterializationError, v2_source.FreezeError) as exc:
        raise UaGecCompleteContextError("frozen v2 UA-GEC identities do not reconstruct from the database") from exc
    require(len(rows) == EXPECTED_UNIT_COUNT, "frozen v2 UA-GEC denominator drift")
    return rows


def _unit_queues(rows: Sequence[Mapping[str, Any]]) -> dict[tuple[str, str, str, str, str, str], deque[str]]:
    queues: dict[tuple[str, str, str, str, str, str], deque[str]] = defaultdict(deque)
    counts: Counter[str] = Counter()
    for row in rows:
        record = row["source_record"]
        key = _annotation_key(
            record["partition"],
            record["doc_id"],
            str(record["annotator_id"]),
            record["error_type"],
            record["error"],
            record["correct"],
        )
        queues[key].append(row["unit_id"])
        counts[record["error_type"]] += 1
    require(dict(counts) == EXPECTED_TAG_COUNTS, "frozen v2 UA-GEC tag denominator drift")
    return queues


def _correction_evidence(
    annotations: Sequence[RawAnnotation],
    *,
    locator_base: Mapping[str, Any],
    document_sha256: str,
    source_text: str,
    corrected_text: str,
) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    for annotation in annotations:
        locator = {
            **locator_base,
            "line": annotation.line,
            "annotation_occurrence": annotation.occurrence,
            "error_type": annotation.tag,
        }
        items.append(
            {
                "kind": "ua_gec",
                "evidence_id": f"ua-gec-qualified-human:{representation.sha256_value(locator)}",
                "locator": locator,
                "locator_sha256": representation.sha256_value(locator),
                "source_document_bytes_sha256": document_sha256,
                "evidence_text": annotation.raw,
                "evidence_text_sha256": representation.sha256_text(annotation.raw),
                "source_context_sha256": representation.sha256_text(source_text),
                "corrected_context_sha256": representation.sha256_text(corrected_text),
                "qualified_human": True,
                "authority": "qualified_human",
            }
        )
    return items


def _corroborating_evidence(
    *,
    locator: Mapping[str, Any],
    document_sha256: str,
    corrected_text: str,
) -> list[dict[str, Any]]:
    return [
        {
            "evidence_id": f"ua-gec-target-sentence:{representation.sha256_value(locator)}",
            "locator": dict(locator),
            "locator_sha256": representation.sha256_value(locator),
            "source_document_bytes_sha256": document_sha256,
            "retrieved_text": corrected_text,
            "retrieved_text_sha256": representation.sha256_text(corrected_text),
            "retrieval_status": "exact",
        }
    ]


def _record_for_window(
    *,
    checkout: Path,
    annotation_path: Path,
    source_sentence_path: Path,
    target_path: Path,
    parsed: ParsedAnnotatedDocument,
    window: ContextWindow,
    annotations: Sequence[RawAnnotation],
    unit_ids: Sequence[str],
    source_document: str,
    target_document: str,
) -> dict[str, Any]:
    partition, doc_id, annotator = _path_identity(checkout, annotation_path)
    source_text = parsed.source_text[window.source_start : window.source_end]
    corrected_text = parsed.corrected_text[window.target_start : window.target_end]
    require(source_text and corrected_text, "complete sentence context is empty")
    require(
        source_document[window.source_document_start : window.source_document_end] == source_text,
        "source sentence is not exact in source corpus document",
    )
    require(
        target_document[window.target_document_start : window.target_document_end] == corrected_text,
        "corrected sentence is not exact in target corpus document",
    )
    edits = _edits(source_text, corrected_text)
    require(
        all(not (item["start"] == 0 and item["end"] == len(source_text)) for item in edits),
        "complete-sentence replacement has no strictly larger construction span",
    )
    annotation_relative = annotation_path.relative_to(checkout).as_posix()
    target_relative = target_path.relative_to(checkout).as_posix()
    source_hash = sha256_file(annotation_path)
    source_sentence_hash = sha256_file(source_sentence_path)
    target_hash = sha256_file(target_path)
    locator_base = {
        "repository": UA_GEC_REPOSITORY,
        "commit": UA_GEC_COMMIT,
        "path": annotation_relative,
        "partition": partition,
        "doc_id": doc_id,
        "annotator": annotator,
    }
    frozen_locator = {
        **locator_base,
        "source_start": window.source_start,
        "source_end": window.source_end,
        "target_start": window.target_start,
        "target_end": window.target_end,
        "source_sentence_path": source_sentence_path.relative_to(checkout).as_posix(),
        "source_sentence_document_bytes_sha256": source_sentence_hash,
        "source_sentence_document_start": window.source_document_start,
        "source_sentence_document_end": window.source_document_end,
        "v2_unit_ids": list(unit_ids),
        "v2_unit_count": len(unit_ids),
    }
    target_locator = {
        "repository": UA_GEC_REPOSITORY,
        "commit": UA_GEC_COMMIT,
        "path": target_relative,
        "partition": partition,
        "doc_id": doc_id,
        "annotator": annotator,
        "target_document_start": window.target_document_start,
        "target_document_end": window.target_document_end,
        "selection": "exact complete corrected sentence",
    }
    secondary = sorted({"qualified_human_correction", *[item.tag for item in annotations]})
    return representation.build_representation(
        document_or_edition_identity=f"ua-gec@{UA_GEC_COMMIT}:{annotation_relative}",
        frozen_locator=frozen_locator,
        source_document_bytes_sha256=source_hash,
        source_text=source_text,
        paragraph_span={"start": 0, "end": len(source_text)},
        sentence_span={"start": 0, "end": len(source_text)},
        edit_shape=_edit_shape(source_text, edits),
        edits=edits,
        minimal_edit_spans=[{"start": item["start"], "end": item["end"]} for item in edits],
        construction_spans=[{"start": 0, "end": len(source_text)}],
        unchanged_function_word_token_ids=[],
        primary_role_id="corrected_example",
        correction_evidence=_correction_evidence(
            annotations,
            locator_base=locator_base,
            document_sha256=source_hash,
            source_text=source_text,
            corrected_text=corrected_text,
        ),
        corroborating_corpus_evidence=_corroborating_evidence(
            locator=target_locator,
            document_sha256=target_hash,
            corrected_text=corrected_text,
        ),
        rights={"status": "public_qualified_human_corpus", "license": UA_GEC_LICENSE},
        secondary_attributes=secondary,
        scope="complete UA-GEC sentence; semantic phenomenon pending qualified review",
        exceptions=["annotation tag is evidence metadata, not a frozen semantic phenomenon label"],
        register="mixed_public_corpus",
        period="contemporary",
        genre="ua_gec_source_sentence",
        evidence_grade="qualified_human_with_exact_target_corpus_retrieval",
        consumer_views=("research_only",),
    )


def reconstruct(
    *,
    checkout: Path,
    database: Path,
    source_universe: Path = V2_SOURCE_UNIVERSE,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """Return eligible complete-context records and text-free accounting."""
    commit = _checkout_commit(checkout)
    rows = _load_v2_units(source_universe, database)
    queues = _unit_queues(rows)
    initial_keys = set(queues)
    records: list[dict[str, Any]] = []
    exclusions: Counter[str] = Counter()
    excluded_units: Counter[str] = Counter()
    excluded_unit_records: list[dict[str, str]] = []
    represented_units = 0
    encountered_tags: Counter[str] = Counter()
    source_documents: set[str] = set()
    target_documents: set[str] = set()

    annotation_paths = sorted((checkout / "data").glob("*/*/annotated/*.ann"))
    require(annotation_paths, "UA-GEC checkout contains no annotated documents")
    for annotation_path in annotation_paths:
        _regular_file(annotation_path, "UA-GEC annotated document")
        target_path = _target_path(checkout, annotation_path)
        source_sentence_path = _source_sentence_path(checkout, annotation_path)
        _regular_file(target_path, "UA-GEC target document")
        _regular_file(source_sentence_path, "UA-GEC source-sentences document")
        partition, doc_id, annotator = _path_identity(checkout, annotation_path)
        parsed = parse_annotated_document(annotation_path.read_text(encoding="utf-8", errors="strict"))
        source_document = source_sentence_path.read_text(encoding="utf-8", errors="strict")
        target_document = target_path.read_text(encoding="utf-8", errors="strict")
        source_sentences = _source_sentences(parsed, source_document)
        target_sentences = _target_sentences(parsed, target_document)
        included: list[tuple[RawAnnotation, str]] = []
        for annotation in parsed.annotations:
            if annotation.tag not in EXPECTED_TAG_COUNTS:
                continue
            key = _annotation_key(partition, doc_id, annotator, annotation.tag, annotation.error, annotation.correction)
            require(key in initial_keys and queues[key], "pinned UA-GEC annotation is absent from frozen v2 units")
            unit_id = queues[key].popleft()
            included.append((annotation, unit_id))
            encountered_tags[annotation.tag] += 1
        if not included:
            continue

        windows: dict[ContextWindow, list[tuple[RawAnnotation, str]]] = defaultdict(list)
        for annotation, unit_id in included:
            sentence = _sentence_for_annotation(annotation, target_sentences)
            if sentence is None:
                exclusions["target_sentence_not_exactly_aligned"] += 1
                excluded_units["target_sentence_not_exactly_aligned"] += 1
                excluded_unit_records.append({"unit_id": unit_id, "reason": "target_sentence_not_exactly_aligned"})
                continue
            window = _context_window(parsed, sentence, source_sentences)
            if window is None:
                exclusions["source_target_sentence_boundary_mismatch"] += 1
                excluded_units["source_target_sentence_boundary_mismatch"] += 1
                excluded_unit_records.append({"unit_id": unit_id, "reason": "source_target_sentence_boundary_mismatch"})
                continue
            windows[window].append((annotation, unit_id))
        for window in sorted(windows, key=lambda item: (item.source_start, item.source_end, item.target_start)):
            members = windows[window]
            context_annotations = [
                item
                for item in parsed.annotations
                if window.source_start <= item.source_start <= item.source_end
                and item.source_end <= window.source_end
                and window.target_start <= item.target_start <= window.target_end
                and item.target_end <= window.target_end
            ]
            unit_ids = [unit_id for _annotation, unit_id in members]
            try:
                record = _record_for_window(
                    checkout=checkout,
                    annotation_path=annotation_path,
                    source_sentence_path=source_sentence_path,
                    target_path=target_path,
                    parsed=parsed,
                    window=window,
                    annotations=context_annotations,
                    unit_ids=unit_ids,
                    source_document=source_document,
                    target_document=target_document,
                )
            except (UaGecCompleteContextError, representation.LinguisticRepresentationError) as exc:
                reason = str(exc)
                if "not exact in target corpus" in reason:
                    code = "corrected_context_not_exactly_retrievable"
                elif "strictly larger construction" in reason:
                    code = "no_larger_construction_context"
                else:
                    raise UaGecCompleteContextError(
                        f"unexpected complete-context reconstruction failure: {annotation_path}"
                    ) from exc
                exclusions[code] += 1
                excluded_units[code] += len(unit_ids)
                excluded_unit_records.extend({"unit_id": unit_id, "reason": code} for unit_id in unit_ids)
                continue
            records.append(record)
            represented_units += len(unit_ids)
            source_documents.add(annotation_path.relative_to(checkout).as_posix())
            target_documents.add(target_path.relative_to(checkout).as_posix())

    remaining = sum(len(queue) for queue in queues.values())
    require(remaining == 0, "frozen v2 UA-GEC units are missing from the pinned checkout")
    require(dict(encountered_tags) == EXPECTED_TAG_COUNTS, "pinned UA-GEC tag counts drift")
    require(represented_units + sum(excluded_units.values()) == EXPECTED_UNIT_COUNT, "context accounting drift")
    require(
        len(excluded_unit_records) == len({item["unit_id"] for item in excluded_unit_records}),
        "duplicate excluded frozen unit identity",
    )
    require(
        len(records) == len({record["document"]["frozen_locator_sha256"] for record in records}),
        "duplicate context identity",
    )
    records.sort(key=lambda item: item["document"]["frozen_locator_sha256"])
    accounting = {
        "checkout_commit": commit,
        "annotated_document_count": len(annotation_paths),
        "source_document_count_with_eligible_context": len(source_documents),
        "target_document_count_with_eligible_context": len(target_documents),
        "v2_unit_count": EXPECTED_UNIT_COUNT,
        "v2_tag_counts": dict(sorted(encountered_tags.items())),
        "eligible_context_record_count": len(records),
        "eligible_v2_unit_count": represented_units,
        "excluded_context_candidate_count_by_reason": dict(sorted(exclusions.items())),
        "excluded_v2_unit_count_by_reason": dict(sorted(excluded_units.items())),
        "excluded_v2_units": sorted(excluded_unit_records, key=lambda item: item["unit_id"]),
        "all_v2_units_mapped": True,
        "all_eligible_records_validate": True,
    }
    return records, accounting


def _schema_validator() -> Draft202012Validator:
    try:
        schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise UaGecCompleteContextError("cannot read complete-context receipt schema") from exc
    Draft202012Validator.check_schema(schema)
    return Draft202012Validator(schema)


def validate_receipt(receipt: Mapping[str, Any]) -> dict[str, Any]:
    value = dict(receipt)
    errors = sorted(_schema_validator().iter_errors(value), key=lambda item: list(item.path))
    require(not errors, f"receipt schema violation: {errors[0].message if errors else ''}")
    body = {key: item for key, item in value.items() if key != "receipt_sha256"}
    require(value["receipt_sha256"] == sha256_bytes(canonical_bytes(body)), "receipt body hash drift")
    require(value["provider_calls"] is False, "provider calls are forbidden")
    require(
        _parse_timestamp(value["started_at"], "started_at") <= _parse_timestamp(value["completed_at"], "completed_at"),
        "receipt completion precedes its start",
    )
    require(
        value["gates"]["source_authoring_blocked"] is True, "context materialization cannot authorize source authoring"
    )
    require(value["gates"]["semantic_labels_present"] is False, "context materialization cannot claim semantic labels")
    require(value["gates"]["cycle002_labels_diagnostic_only"] is True, "Cycle 002 diagnostic disposition drift")
    denominator = value["denominator"]
    context = value["complete_context"]
    require(
        sum(denominator["v2_tag_counts"].values()) == denominator["v2_ua_gec_unit_count"],
        "tag denominator accounting drift",
    )
    require(
        context["eligible_v2_unit_count"] + sum(context["excluded_v2_unit_count_by_reason"].values())
        == denominator["v2_ua_gec_unit_count"],
        "complete-context unit accounting drift",
    )
    require(
        context["private_exclusions_jsonl_rows"] == sum(context["excluded_v2_unit_count_by_reason"].values()),
        "private exclusion row accounting drift",
    )
    return value


def _prepare_private_output(path: Path) -> None:
    parent = path.parent
    if parent.exists():
        require(parent.is_dir() and not parent.is_symlink(), "private output parent must be a real directory")
        require(stat.S_IMODE(parent.stat().st_mode) == PRIVATE_DIR_MODE, "private output directory must be mode 0700")
    else:
        parent.mkdir(parents=True, mode=PRIVATE_DIR_MODE)
        os.chmod(parent, PRIVATE_DIR_MODE)
    require(not path.exists(), "private complete-context output already exists")


def _atomic_write(path: Path, payload: bytes, mode: int) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(dir=path.parent, prefix=f".{path.name}.", delete=False) as handle:
        temporary = Path(handle.name)
        handle.write(payload)
        handle.flush()
        os.fsync(handle.fileno())
    os.chmod(temporary, mode)
    os.replace(temporary, path)


def materialize(
    *,
    checkout: Path,
    database: Path,
    source_universe: Path,
    private_output: Path,
    private_exclusions_output: Path,
    public_receipt: Path,
    started_at: str,
    completed_at: str | None,
) -> dict[str, Any]:
    records, accounting = reconstruct(checkout=checkout, database=database, source_universe=source_universe)
    effective_completed_at = completed_at or utc_now()
    payload = b"".join(canonical_bytes(record) for record in records)
    exclusion_payload = b"".join(canonical_bytes(item) for item in accounting["excluded_v2_units"])
    v2_receipt = source_universe / "source-universe-freeze-receipt.json"
    v2_ledger = source_universe / "ua_gec.units.jsonl"
    receipt: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "implementation_version": IMPLEMENTATION_VERSION,
        "text_free": True,
        "provider_calls": False,
        "started_at": started_at,
        "completed_at": effective_completed_at,
        "bindings": {
            "phase3_reboot_prompt_v3_sha256": PHASE3_REBOOT_V3_SHA256,
            "phase3_recovery_prompt_v2_sha256": PHASE3_RECOVERY_V2_SHA256,
            "implementation_sha256": sha256_file(SCRIPT_PATH),
            "receipt_schema_sha256": sha256_file(SCHEMA_PATH),
            "representation_implementation_sha256": sha256_file(representation.__file__),
            "representation_schema_sha256": sha256_file(representation.SCHEMA_PATH),
            "v2_source_universe_receipt_sha256": sha256_file(v2_receipt),
            "v2_ua_gec_ledger_sha256": sha256_file(v2_ledger),
            "sources_database_sha256": sha256_file(database),
            "ua_gec_repository": UA_GEC_REPOSITORY,
            "ua_gec_commit": accounting["checkout_commit"],
            "ua_gec_license": UA_GEC_LICENSE,
        },
        "denominator": {
            "v2_ua_gec_unit_count": accounting["v2_unit_count"],
            "v2_tag_counts": accounting["v2_tag_counts"],
            "all_v2_units_mapped": accounting["all_v2_units_mapped"],
        },
        "complete_context": {
            "annotated_document_count": accounting["annotated_document_count"],
            "source_document_count_with_eligible_context": accounting["source_document_count_with_eligible_context"],
            "target_document_count_with_eligible_context": accounting["target_document_count_with_eligible_context"],
            "eligible_context_record_count": accounting["eligible_context_record_count"],
            "eligible_v2_unit_count": accounting["eligible_v2_unit_count"],
            "excluded_context_candidate_count_by_reason": accounting["excluded_context_candidate_count_by_reason"],
            "excluded_v2_unit_count_by_reason": accounting["excluded_v2_unit_count_by_reason"],
            "all_eligible_records_validate": accounting["all_eligible_records_validate"],
            "private_jsonl_sha256": sha256_bytes(payload),
            "private_jsonl_bytes": len(payload),
            "private_exclusions_jsonl_sha256": sha256_bytes(exclusion_payload),
            "private_exclusions_jsonl_bytes": len(exclusion_payload),
            "private_exclusions_jsonl_rows": len(accounting["excluded_v2_units"]),
        },
        "gates": {
            "complete_context_materialization_ready": True,
            "semantic_labels_present": False,
            "cycle002_labels_diagnostic_only": True,
            "source_authoring_blocked": True,
            "evaluation_partition_frozen": False,
            "source_coverage_ready": False,
            "phase3_complete": False,
            "phase4_blocked": True,
        },
    }
    receipt["receipt_sha256"] = sha256_bytes(canonical_bytes(receipt))
    validate_receipt(receipt)
    _prepare_private_output(private_output)
    _prepare_private_output(private_exclusions_output)
    _atomic_write(private_output, payload, PRIVATE_FILE_MODE)
    _atomic_write(private_exclusions_output, exclusion_payload, PRIVATE_FILE_MODE)
    _atomic_write(
        public_receipt,
        json.dumps(receipt, ensure_ascii=False, indent=2, sort_keys=True).encode("utf-8") + b"\n",
        PRIVATE_FILE_MODE,
    )
    return receipt


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--ua-gec-root", type=Path, required=True)
    parser.add_argument("--database", type=Path, required=True)
    parser.add_argument("--source-universe", type=Path, default=V2_SOURCE_UNIVERSE)
    parser.add_argument("--private-output", type=Path, required=True)
    parser.add_argument("--private-exclusions-output", type=Path)
    parser.add_argument("--public-receipt", type=Path, required=True)
    parser.add_argument("--started-at")
    parser.add_argument("--completed-at")
    args = parser.parse_args(argv)
    private_exclusions_output = args.private_exclusions_output or (
        args.private_output.parent / PRIVATE_EXCLUSIONS_FILENAME
    )
    receipt = materialize(
        checkout=args.ua_gec_root,
        database=args.database,
        source_universe=args.source_universe,
        private_output=args.private_output,
        private_exclusions_output=private_exclusions_output,
        public_receipt=args.public_receipt,
        started_at=args.started_at or utc_now(),
        completed_at=args.completed_at,
    )
    print(canonical_json({"ok": True, "receipt_sha256": receipt["receipt_sha256"], "gates": receipt["gates"]}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
