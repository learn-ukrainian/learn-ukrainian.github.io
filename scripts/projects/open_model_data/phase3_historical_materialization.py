#!/usr/bin/env python3
"""Stream a bounded historical-corpus canary into the protected v3 model.

Only explicitly ``orv-uk`` UD documents and PluG2 rows whose source-language
metadata is exactly ``UK`` enter the candidate output.  Historical text is
written to a caller-supplied private directory; the receipt is text-free.
"""

from __future__ import annotations

import argparse
import csv
import gzip
import hashlib
import json
import math
import os
import re
import shutil
import stat
import tempfile
import unicodedata
import zipfile
from collections import Counter
from collections.abc import Iterable, Iterator, Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Any

from jsonschema import Draft202012Validator

from scripts.projects.open_model_data.phase3_historical_representation import (
    build_historical_representation,
)
from scripts.projects.open_model_data.phase3_linguistic_representation import (
    canonical_json,
    sha256_bytes,
    sha256_text,
    sha256_value,
)

ROOT = Path(__file__).resolve().parents[3]
RECEIPT_SCHEMA_PATH = (
    ROOT / "data/projects/open_model_data/contracts/phase3_historical_materialization_receipt_v1.schema.json"
)

UD_COLLECTION_ID = "ud-old-east-slavic-ruthenian-05a029e00ccf"
UD_COMMIT = "05a029e00ccf1a374c91a22d17fb6310e646d628"
UD_EXPECTED_SHA256 = {
    "orv_ruthenian-ud-dev.conllu": "a2047c4c734dab0a5b68f888979a3ca14670d217d7dcc11bb12b775f2dbbfd1d",
    "orv_ruthenian-ud-test.conllu": "f34964cee7d6a38b3dd39ceb4dbde38a4fd9aacd8512272c19318027e044ea0d",
    "orv_ruthenian-ud-train.conllu": "fc13f73dc71e5fac95938eba424b3d5236bfa8edd8ce7bd0e28db2d28a2f9680",
}
UD_EXPECTED_DENOMINATOR = {"documents": 82, "sentences": 1311, "token_rows": 35081}

PLUG2_COLLECTION_ID = "plug2-zenodo-19482961"
PLUG2_DOI = "10.5281/zenodo.19482961"
PLUG2_ARCHIVE_SHA256 = "ff1ff139049539fc7c9ab69b006c12444567989758738baa948cfa0837aabe23"
PLUG2_METADATA_SHA256 = "a9f79149606b570ebd6895020292eb06016d883e5c75dcb38a6e2cfd15378494"
PLUG2_EXPECTED_DENOMINATOR = {
    "documents": 56245,
    "token_sum": 74497787,
    "uk_documents": 56080,
    "non_uk_or_unknown_documents": 165,
}

MAX_CANARY_FRACTION = 0.01
OUTPUT_CEILING_GIB = 5.0
RECEIPT_SCHEMA_VERSION = "phase3_historical_materialization_receipt_v1"


class HistoricalMaterializationError(ValueError):
    """An input identity, role boundary, or deterministic invariant failed."""


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise HistoricalMaterializationError(message)


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _verify_hash(path: Path, expected: str) -> None:
    _require(path.is_file(), f"missing input: {path}")
    actual = file_sha256(path)
    _require(actual == expected, f"SHA-256 mismatch for {path.name}: expected {expected}, got {actual}")


def _rights(license_name: str) -> dict[str, Any]:
    return {
        "status": "admitted",
        "license": license_name,
        "reuse_scope": "public_training",
        "attribution_required": True,
    }


def _select_canary(keys: Sequence[str], fraction: float, *, salt: str) -> list[str]:
    _require(0 < fraction <= MAX_CANARY_FRACTION, "canary fraction must be in (0, 0.01]")
    _require(bool(keys), "cannot select a canary from an empty denominator")
    count = max(1, math.ceil(len(keys) * fraction))
    return sorted(keys, key=lambda key: (sha256_text(f"{salt}:{key}"), key))[:count]


@dataclass(frozen=True)
class UdToken:
    token_id: str
    form: str
    lemma: str | None
    upos: str | None
    feats: dict[str, str]
    head: str | None
    deprel: str | None
    misc: str


@dataclass(frozen=True)
class UdSentence:
    source_file: str
    source_file_sha256: str
    document_id: str
    language: str | None
    created: str | None
    title: str | None
    sent_id: str
    source_comment_text: str | None
    tokens: tuple[UdToken, ...]


def _parse_feats(value: str) -> dict[str, str]:
    if value == "_":
        return {}
    pairs: dict[str, str] = {}
    for item in value.split("|"):
        _require("=" in item, f"malformed CoNLL-U feature: {item}")
        key, raw_value = item.split("=", 1)
        _require(key not in pairs, f"duplicate CoNLL-U feature: {key}")
        pairs[key] = raw_value
    return pairs


def parse_conllu(path: Path, *, source_file_sha256: str) -> list[UdSentence]:
    document: dict[str, str | None] = {"id": None, "lang": None, "created": None, "title": None}
    sentence_meta: dict[str, str | None] = {"sent_id": None, "text": None}
    token_rows: list[UdToken] = []
    sentences: list[UdSentence] = []

    def flush() -> None:
        nonlocal sentence_meta, token_rows
        if not token_rows:
            sentence_meta = {"sent_id": None, "text": None}
            return
        _require(bool(document["id"]), f"sentence without document id in {path.name}")
        _require(bool(sentence_meta["sent_id"]), f"sentence without sent_id in {path.name}")
        token_ids = [token.token_id for token in token_rows]
        _require(len(token_ids) == len(set(token_ids)), f"duplicate CoNLL-U token id in {sentence_meta['sent_id']}")
        sentences.append(
            UdSentence(
                source_file=path.name,
                source_file_sha256=source_file_sha256,
                document_id=str(document["id"]),
                language=document["lang"],
                created=document["created"],
                title=document["title"],
                sent_id=str(sentence_meta["sent_id"]),
                source_comment_text=sentence_meta["text"],
                tokens=tuple(token_rows),
            )
        )
        sentence_meta = {"sent_id": None, "text": None}
        token_rows = []

    with path.open(encoding="utf-8") as handle:
        for raw_line in handle:
            line = raw_line.rstrip("\n\r")
            if not line:
                flush()
                continue
            if line.startswith("# ") and "=" in line:
                key, value = (part.strip() for part in line[2:].split("=", 1))
                if key in {"newdoc", "newdoc id", "newdoc_id"}:
                    flush()
                    document = {"id": value, "lang": None, "created": None, "title": None}
                elif key == "lang":
                    document["lang"] = value
                elif key == "created":
                    document["created"] = value
                elif key == "title":
                    document["title"] = value
                elif key == "sent_id":
                    sentence_meta["sent_id"] = value
                elif key == "text":
                    sentence_meta["text"] = value
                continue
            if line.startswith("#"):
                continue
            columns = line.split("\t")
            _require(len(columns) == 10, f"malformed CoNLL-U row in {path.name}")
            raw_id = columns[0]
            if "-" in raw_id or "." in raw_id:
                continue
            _require(raw_id.isdigit(), f"non-integer CoNLL-U token id: {raw_id}")
            token_rows.append(
                UdToken(
                    token_id=raw_id,
                    form=columns[1],
                    lemma=None if columns[2] == "_" else columns[2],
                    upos=None if columns[3] == "_" else columns[3],
                    feats=_parse_feats(columns[5]),
                    head=None if columns[6] in {"_", "0"} else columns[6],
                    deprel=None if columns[7] == "_" else columns[7],
                    misc=columns[9],
                )
            )
    flush()
    return sentences


def _ud_surface(sentence: UdSentence) -> tuple[str, list[tuple[int, int]]]:
    comment = sentence.source_comment_text
    if comment and comment != "[Omitted long context line]":
        spans: list[tuple[int, int]] = []
        cursor = 0
        for index, token in enumerate(sentence.tokens):
            if index:
                previous = sentence.tokens[index - 1]
                if "SpaceAfter=No" not in previous.misc.split("|"):
                    whitespace_start = cursor
                    while cursor < len(comment) and comment[cursor].isspace():
                        cursor += 1
                    _require(
                        cursor > whitespace_start,
                        f"CoNLL-U # text omits an encoded token boundary: {sentence.sent_id}",
                    )
            _require(
                comment.startswith(token.form, cursor),
                f"CoNLL-U # text disagrees with token rows: {sentence.sent_id}",
            )
            start = cursor
            cursor += len(token.form)
            spans.append((start, cursor))
        _require(
            cursor == len(comment),
            f"CoNLL-U # text has trailing content outside token rows: {sentence.sent_id}",
        )
        return comment, spans

    parts: list[str] = []
    spans: list[tuple[int, int]] = []
    cursor = 0
    for index, token in enumerate(sentence.tokens):
        start = cursor
        parts.append(token.form)
        cursor += len(token.form)
        spans.append((start, cursor))
        if index < len(sentence.tokens) - 1 and "SpaceAfter=No" not in token.misc.split("|"):
            parts.append(" ")
            cursor += 1
    text = "".join(parts)
    return text, spans


def _ud_tokens(sentence: UdSentence, text: str, spans: Sequence[tuple[int, int]]) -> list[dict[str, Any]]:
    tokens: list[dict[str, Any]] = []
    for index, (source_token, (start, end)) in enumerate(zip(sentence.tokens, spans, strict=True), start=1):
        _require(text[start:end] == source_token.form, f"stale UD token span: {sentence.sent_id}:{source_token.token_id}")
        has_lexical_character = any(
            unicodedata.category(char)[0] in {"L", "N", "M"} or char == "_" for char in source_token.form
        )
        tokens.append(
            {
                "token_id": f"tok:{index:06d}",
                "kind": "word" if has_lexical_character else "punctuation",
                "text": source_token.form,
                "normalized_text": unicodedata.normalize("NFC", source_token.form),
                "start": start,
                "end": end,
                "paragraph_index": 0,
                "sentence_index": 0,
            }
        )
    return tokens


def _ud_analyses(sentence: UdSentence, text: str, spans: Sequence[tuple[int, int]]) -> list[dict[str, Any]]:
    analyses: list[dict[str, Any]] = []
    analysis_id_by_token = {
        token.token_id: f"ud-analysis:{sentence.sent_id}:{token.token_id}" for token in sentence.tokens
    }
    heads = {token.token_id: token.head for token in sentence.tokens}
    for token_id in heads:
        seen = {token_id}
        head = heads[token_id]
        while head is not None:
            _require(head in heads, f"UD dependency head is unknown: {sentence.sent_id}:{head}")
            _require(head not in seen, f"UD dependency cycle: {sentence.sent_id}:{head}")
            seen.add(head)
            head = heads[head]
    for index, (source_token, (start, end)) in enumerate(zip(sentence.tokens, spans, strict=True), start=1):
        _require(text[start:end] == source_token.form, f"stale UD analysis span: {sentence.sent_id}:{source_token.token_id}")
        token_ids = [f"tok:{index:06d}"]
        analyses.append(
            {
                "analysis_id": analysis_id_by_token[source_token.token_id],
                "layer_id": "original_diplomatic",
                "source_token_id": source_token.token_id,
                "source_surface": source_token.form,
                "token_ids": token_ids,
                "lemma": source_token.lemma,
                "pos": source_token.upos,
                "morph": source_token.feats,
                "head_analysis_id": (None if source_token.head is None else analysis_id_by_token[source_token.head]),
                "dependency": source_token.deprel,
                "ambiguity": [],
            }
        )
    return analyses


def _unresolved_periodization(evidence_id: str) -> list[dict[str, Any]]:
    return [
        {
            "framework_id": "materialization-unresolved",
            "framework_label": "No periodization inferred during source materialization",
            "stage_id": "unresolved",
            "stage_label": "Unresolved pending qualified historical adjudication",
            "start_year": None,
            "end_year": None,
            "status": "unresolved",
            "attribution": "Phase 3 deterministic materializer",
            "evidence_ids": [evidence_id],
            "ambiguity": ["Competing scholarly periodizations remain separate downstream evidence."],
        }
    ]


def _year_context(raw_year: str | None) -> tuple[int | None, int | None, str]:
    if raw_year and re.fullmatch(r"[0-9]{4}", raw_year):
        year = int(raw_year)
        return year, year, "exact"
    return None, None, "unknown"


def build_ud_record(sentence: UdSentence) -> dict[str, Any]:
    text, spans = _ud_surface(sentence)
    locator = {
        "dataset_id": UD_COLLECTION_ID,
        "commit_sha": UD_COMMIT,
        "source_file": sentence.source_file,
        "newdoc_id": sentence.document_id,
        "sent_id": sentence.sent_id,
    }
    metadata = {
        "newdoc_id": sentence.document_id,
        "lang": sentence.language,
        "created": sentence.created,
        "title": sentence.title,
    }
    source_evidence_id = "ud-source-record"
    metadata_evidence_id = "ud-source-metadata"
    rights = _rights("CC BY-SA 4.0")
    min_year, max_year, certainty = _year_context(sentence.created)
    tokens = _ud_tokens(sentence, text, spans)
    analyses = _ud_analyses(sentence, text, spans)
    return build_historical_representation(
        record_id=f"ud-orv-uk:{sha256_value(locator)[:24]}",
        collection_identity=f"{UD_COLLECTION_ID}@{UD_COMMIT}",
        document_or_edition_identity=sentence.document_id,
        source_record_identity=sentence.sent_id,
        frozen_locator=locator,
        source_document_bytes_sha256=sentence.source_file_sha256,
        source_record_bytes_sha256=sha256_text(text),
        historical_context={
            "min_year": min_year,
            "max_year": max_year,
            "date_certainty": certainty,
            "region": None,
            "polity": None,
            "genre": None,
            "manuscript_or_inscription_identity": sentence.title,
            "script": "Cyrillic",
            "orthography": None,
        },
        text_layers=[
            {
                "layer_id": "original_diplomatic",
                "text": text,
                "tokens": tokens,
                "authority": "source_transcription",
                "evidence_ids": [source_evidence_id],
            }
        ],
        alignments=[],
        periodizations=_unresolved_periodization(metadata_evidence_id),
        language_labels=[
            {
                "label": "orv-uk",
                "label_kind": "corpus_annotation",
                "attribution": "Universal Dependencies Old East Slavic-Ruthenian",
                "scope": sentence.document_id,
                "status": "attested",
                "evidence_ids": [metadata_evidence_id],
                "ambiguity": [],
            }
        ],
        language_layers=[
            {
                "language_layer_id": "ud-primary-orv-uk",
                "label": "orv-uk",
                "role": "primary",
                "status": "attested",
                "evidence_ids": [metadata_evidence_id],
                "ambiguity": [],
            }
        ],
        linguistic_features=[],
        interpretations=[],
        linguistic_analyses=analyses,
        analysis_provenance={
            "status": "present",
            "resource_identity": "Universal Dependencies Old East Slavic-Ruthenian",
            "resource_version": UD_COMMIT,
            "license": "CC BY-SA 4.0",
            "tokenization_alignment": "exact",
        },
        evidence=[
            {
                "evidence_id": source_evidence_id,
                "kind": "source_record",
                "locator": locator,
                "source_document_bytes_sha256": sentence.source_file_sha256,
                "evidence_text": text,
                "text_exposure": "verbatim",
                "authority": "source_transcription",
                "rights": rights,
            },
            {
                "evidence_id": metadata_evidence_id,
                "kind": "source_metadata",
                "locator": {**locator, "component": "document_comments"},
                "source_document_bytes_sha256": sentence.source_file_sha256,
                "evidence_text": canonical_json(metadata),
                "text_exposure": "metadata_only",
                "authority": "source_transcription",
                "rights": rights,
            },
        ],
        rights=rights,
        derived_bundles=("historical_recognition", "language_label_disambiguation"),
        derived_bundle_rights=[
            {"bundle_id": "historical_recognition", "rights": rights},
            {"bundle_id": "language_label_disambiguation", "rights": rights},
        ],
    )


def _safe_member_path(name: str) -> PurePosixPath:
    raw_parts = name.split("/")
    _require(all(part not in {"", ".", ".."} for part in raw_parts), f"unsafe ZIP member: {name}")
    path = PurePosixPath(name)
    _require(not path.is_absolute(), f"unsafe absolute ZIP member: {name}")
    _require("\\" not in name, f"unsafe ZIP member separator: {name}")
    return path


def load_plug2_metadata(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle, delimiter="|", quotechar='"')
        _require(reader.fieldnames is not None and "path" in reader.fieldnames, "PluG2 metadata lacks path")
        rows = [dict(row) for row in reader]
    paths = [row["path"] for row in rows]
    _require(len(paths) == len(set(paths)), "duplicate PluG2 metadata path")
    for name in paths:
        _safe_member_path(name)
    return rows


def _metadata_nonnegative_int(row: Mapping[str, str], key: str) -> int:
    raw_value = row.get(key)
    try:
        value = int(raw_value) if raw_value is not None else -1
    except ValueError as exc:
        raise HistoricalMaterializationError(f"invalid PluG2 integer field {key}: {raw_value!r}") from exc
    _require(value >= 0, f"invalid PluG2 nonnegative field {key}: {raw_value!r}")
    return value


def inspect_plug2_archive(path: Path) -> dict[str, zipfile.ZipInfo]:
    files: dict[str, zipfile.ZipInfo] = {}
    with zipfile.ZipFile(path) as archive:
        for info in archive.infolist():
            member = _safe_member_path(info.filename[:-1] if info.is_dir() else info.filename)
            if info.is_dir():
                continue
            unix_mode = info.external_attr >> 16
            _require(not stat.S_ISLNK(unix_mode), f"unsafe ZIP symlink member: {info.filename}")
            _require(member.parts[0] == "PLuG2_texts", f"unexpected PluG2 ZIP root: {info.filename}")
            relative = PurePosixPath(*member.parts[1:]).as_posix()
            _require(relative not in files, f"duplicate PluG2 ZIP member: {relative}")
            files[relative] = info
    return files


def paragraph_units(text: str) -> list[tuple[int, int, str]]:
    units: list[tuple[int, int, str]] = []
    for match in re.finditer(r"[^\r\n]+", text):
        value = match.group(0)
        if value.strip():
            units.append((match.start(), match.end(), value))
    return units


def build_plug2_record(
    *,
    row: Mapping[str, str],
    member_bytes: bytes,
    paragraph_index: int,
    paragraph_start: int,
    paragraph_end: int,
    paragraph_text: str,
    archive_sha256: str = PLUG2_ARCHIVE_SHA256,
    metadata_sha256: str = PLUG2_METADATA_SHA256,
) -> dict[str, Any]:
    _require(row.get("doc.original") == "UK", "non-UK PluG2 row cannot enter Ukrainian candidate output")
    document_sha256 = sha256_bytes(member_bytes)
    locator = {
        "dataset_id": PLUG2_COLLECTION_ID,
        "doi": PLUG2_DOI,
        "archive_sha256": archive_sha256,
        "member_path": row["path"],
        "paragraph_index": paragraph_index,
        "paragraph_start": paragraph_start,
        "paragraph_end": paragraph_end,
        "offset_basis": "unicode_code_points",
    }
    source_evidence_id = "plug2-source-record"
    metadata_evidence_id = "plug2-source-metadata"
    rights = _rights("CC BY 4.0")
    min_year, max_year, certainty = _year_context(row.get("doc.date"))
    genre_parts = [value for value in (row.get("doc.style"), row.get("doc.genre")) if value]
    return build_historical_representation(
        record_id=f"plug2-uk:{sha256_value(locator)[:24]}",
        collection_identity=f"{PLUG2_COLLECTION_ID}:{PLUG2_DOI}",
        document_or_edition_identity=row["path"],
        source_record_identity=f"{row['path']}#paragraph={paragraph_index}",
        frozen_locator=locator,
        source_document_bytes_sha256=document_sha256,
        source_record_bytes_sha256=sha256_text(paragraph_text),
        historical_context={
            "min_year": min_year,
            "max_year": max_year,
            "date_certainty": certainty,
            "region": row.get("doc.authorLocCode") or None,
            "polity": None,
            "genre": "+".join(genre_parts) or None,
            "manuscript_or_inscription_identity": row.get("doc.name") or row["path"],
            "script": "Cyrillic",
            "orthography": row.get("doc.orthography") or None,
        },
        text_layers=[
            {
                "layer_id": "original_diplomatic",
                "text": paragraph_text,
                "authority": "source_transcription",
                "evidence_ids": [source_evidence_id],
            }
        ],
        alignments=[],
        periodizations=_unresolved_periodization(metadata_evidence_id),
        language_labels=[
            {
                "label": "UK",
                "label_kind": "corpus_annotation",
                "attribution": "PluG2 metadata",
                "scope": row["path"],
                "status": "attested",
                "evidence_ids": [metadata_evidence_id],
                "ambiguity": [],
            }
        ],
        language_layers=[
            {
                "language_layer_id": "plug2-primary-uk",
                "label": "UK",
                "role": "primary",
                "status": "attested",
                "evidence_ids": [metadata_evidence_id],
                "ambiguity": [],
            }
        ],
        linguistic_features=[],
        interpretations=[],
        evidence=[
            {
                "evidence_id": source_evidence_id,
                "kind": "source_record",
                "locator": locator,
                "source_document_bytes_sha256": document_sha256,
                "evidence_text": paragraph_text,
                "text_exposure": "verbatim",
                "authority": "source_transcription",
                "rights": rights,
            },
            {
                "evidence_id": metadata_evidence_id,
                "kind": "source_metadata",
                "locator": {**locator, "component": "PluG2_metadata.psv"},
                "source_document_bytes_sha256": metadata_sha256,
                "evidence_text": canonical_json(dict(row)),
                "text_exposure": "metadata_only",
                "authority": "source_transcription",
                "rights": rights,
            },
        ],
        rights=rights,
        derived_bundles=("historical_recognition", "language_label_disambiguation"),
        derived_bundle_rights=[
            {"bundle_id": "historical_recognition", "rights": rights},
            {"bundle_id": "language_label_disambiguation", "rights": rights},
        ],
    )


def _write_jsonl_gzip(path: Path, records: Iterable[Mapping[str, Any]]) -> tuple[int, int, str]:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.tmp")
    count = 0
    try:
        with (
            temporary.open("wb") as raw_handle,
            gzip.GzipFile(filename="", mode="wb", fileobj=raw_handle, mtime=0) as gzip_handle,
        ):
            for record in records:
                gzip_handle.write(canonical_json(record).encode("utf-8") + b"\n")
                count += 1
        os.replace(temporary, path)
    finally:
        if temporary.exists():
            temporary.unlink()
    return count, path.stat().st_size, file_sha256(path)


def _validate_receipt(receipt: Mapping[str, Any]) -> None:
    schema = json.loads(RECEIPT_SCHEMA_PATH.read_text(encoding="utf-8"))
    Draft202012Validator.check_schema(schema)
    errors = sorted(Draft202012Validator(schema).iter_errors(receipt), key=lambda item: list(item.path))
    if errors:
        location = "/".join(str(part) for part in errors[0].path) or "receipt"
        raise HistoricalMaterializationError(f"receipt schema violation at {location}: {errors[0].message}")


def _write_receipt(path: Path, receipt: Mapping[str, Any]) -> None:
    _validate_receipt(receipt)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.tmp")
    temporary.write_text(json.dumps(receipt, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    os.replace(temporary, path)


def _projection_gib(output_bytes: int, selected_tokens: int, denominator_tokens: int) -> float:
    _require(selected_tokens > 0, "selected token denominator must be positive")
    projected = output_bytes * denominator_tokens / selected_tokens
    return projected / (1024**3)


def _inside_git_checkout(path: Path) -> bool:
    return any((candidate / ".git").exists() for candidate in (path, *path.parents))


def materialize_canary(
    *,
    ud_dir: Path,
    plug2_archive: Path,
    plug2_metadata: Path,
    private_output_dir: Path,
    receipt_output: Path,
    ud_fraction: float = 0.01,
    plug2_fraction: float = 0.001,
    expected_ud_sha256: Mapping[str, str] = UD_EXPECTED_SHA256,
    expected_plug2_archive_sha256: str = PLUG2_ARCHIVE_SHA256,
    expected_plug2_metadata_sha256: str = PLUG2_METADATA_SHA256,
    expected_ud_denominator: Mapping[str, int] = UD_EXPECTED_DENOMINATOR,
    expected_plug2_denominator: Mapping[str, int] = PLUG2_EXPECTED_DENOMINATOR,
) -> dict[str, Any]:
    """Audit complete denominators and materialize deterministic bounded samples."""
    _require(
        not _inside_git_checkout(private_output_dir.resolve()),
        "private text output cannot be inside a Git checkout",
    )
    _require(
        receipt_output.parent.resolve() == private_output_dir.resolve(),
        "receipt must be written inside the immutable canary output directory",
    )
    _require(not private_output_dir.exists(), "immutable canary output directory already exists")
    for filename, expected_hash in expected_ud_sha256.items():
        _verify_hash(ud_dir / filename, expected_hash)
    _verify_hash(plug2_archive, expected_plug2_archive_sha256)
    _verify_hash(plug2_metadata, expected_plug2_metadata_sha256)

    all_ud: list[UdSentence] = []
    for filename in sorted(expected_ud_sha256):
        all_ud.extend(parse_conllu(ud_dir / filename, source_file_sha256=expected_ud_sha256[filename]))
    ud_candidates = [item for item in all_ud if item.language == "orv-uk"]
    ud_documents = {item.document_id for item in ud_candidates}
    ud_token_rows = sum(len(item.tokens) for item in ud_candidates)
    actual_ud_denominator = {
        "documents": len(ud_documents),
        "sentences": len(ud_candidates),
        "token_rows": ud_token_rows,
    }
    _require(actual_ud_denominator == dict(expected_ud_denominator), "UD candidate denominator drift")
    ud_by_id = {item.sent_id: item for item in ud_candidates}
    _require(len(ud_by_id) == len(ud_candidates), "duplicate UD candidate sent_id")
    selected_ud_ids = _select_canary(sorted(ud_by_id), ud_fraction, salt=UD_COLLECTION_ID)
    selected_ud = [ud_by_id[item] for item in selected_ud_ids]
    selected_ud_token_rows = sum(len(item.tokens) for item in selected_ud)

    rows = load_plug2_metadata(plug2_metadata)
    archive_files = inspect_plug2_archive(plug2_archive)
    metadata_paths = {row["path"] for row in rows}
    _require(metadata_paths == set(archive_files), "PluG2 metadata/archive path-set mismatch")
    original_counts = Counter((row.get("doc.original") or "UNKNOWN") for row in rows)
    orthography_counts = Counter((row.get("doc.orthography") or "unlabeled") for row in rows)
    token_sum = sum(_metadata_nonnegative_int(row, "doc.tokenCount") for row in rows)
    uk_rows = {row["path"]: row for row in rows if row.get("doc.original") == "UK"}
    actual_plug2_denominator = {
        "documents": len(rows),
        "token_sum": token_sum,
        "uk_documents": len(uk_rows),
        "non_uk_or_unknown_documents": len(rows) - len(uk_rows),
    }
    _require(actual_plug2_denominator == dict(expected_plug2_denominator), "PluG2 denominator drift")
    selected_plug2_paths = _select_canary(sorted(uk_rows), plug2_fraction, salt=PLUG2_COLLECTION_ID)
    selected_plug2_tokens = sum(
        _metadata_nonnegative_int(uk_rows[path], "doc.tokenCount") for path in selected_plug2_paths
    )
    candidate_plug2_tokens = sum(_metadata_nonnegative_int(row, "doc.tokenCount") for row in uk_rows.values())

    plug2_record_counter = 0

    def plug2_records() -> Iterator[Mapping[str, Any]]:
        nonlocal plug2_record_counter
        with zipfile.ZipFile(plug2_archive) as archive:
            for member_path in selected_plug2_paths:
                info = archive_files[member_path]
                raw_bytes = archive.read(info)
                try:
                    document_text = raw_bytes.decode("utf-8")
                except UnicodeDecodeError as exc:
                    raise HistoricalMaterializationError(f"PluG2 member is not UTF-8: {member_path}") from exc
                units = paragraph_units(document_text)
                _require(bool(units), f"PluG2 document has no non-empty paragraphs: {member_path}")
                for paragraph_index, (start, end, value) in enumerate(units):
                    plug2_record_counter += 1
                    yield build_plug2_record(
                        row=uk_rows[member_path],
                        member_bytes=raw_bytes,
                        paragraph_index=paragraph_index,
                        paragraph_start=start,
                        paragraph_end=end,
                        paragraph_text=value,
                        archive_sha256=expected_plug2_archive_sha256,
                        metadata_sha256=expected_plug2_metadata_sha256,
                    )

    private_output_dir.parent.mkdir(parents=True, exist_ok=True)
    staging_dir = Path(
        tempfile.mkdtemp(
            prefix=f".{private_output_dir.name}.staging-",
            dir=private_output_dir.parent,
        )
    )
    try:
        ud_output = staging_dir / "ud-orv-uk-canary.jsonl.gz"
        ud_record_count, ud_output_bytes, ud_output_sha256 = _write_jsonl_gzip(
            ud_output, (build_ud_record(item) for item in selected_ud)
        )
        plug2_output = staging_dir / "plug2-uk-canary.jsonl.gz"
        plug2_record_count, plug2_output_bytes, plug2_output_sha256 = _write_jsonl_gzip(plug2_output, plug2_records())
        _require(plug2_record_count == plug2_record_counter, "PluG2 record counter drift")

        ud_projection = _projection_gib(ud_output_bytes, selected_ud_token_rows, actual_ud_denominator["token_rows"])
        plug2_projection = _projection_gib(plug2_output_bytes, selected_plug2_tokens, candidate_plug2_tokens)
        total_projection = ud_projection + plug2_projection
        _require(total_projection <= OUTPUT_CEILING_GIB, "projected compressed output exceeds 5 GiB ceiling")

        receipt: dict[str, Any] = {
            "schema_version": RECEIPT_SCHEMA_VERSION,
            "mode": "canary",
            "text_free": True,
            "inputs": {
                "ud": {
                    "dataset_id": UD_COLLECTION_ID,
                    "commit_sha": UD_COMMIT,
                    "file_sha256": dict(expected_ud_sha256),
                },
                "plug2": {
                    "dataset_id": PLUG2_COLLECTION_ID,
                    "doi": PLUG2_DOI,
                    "archive_sha256": expected_plug2_archive_sha256,
                    "metadata_sha256": expected_plug2_metadata_sha256,
                },
            },
            "denominators": {
                "ud_explicit_orv_uk": actual_ud_denominator,
                "ud_other_or_unresolved_sentences": len(all_ud) - len(ud_candidates),
                "plug2": actual_plug2_denominator,
                "plug2_original_counts": dict(sorted(original_counts.items())),
                "plug2_orthography_counts": dict(sorted(orthography_counts.items())),
                "plug2_candidate_uk_token_sum": candidate_plug2_tokens,
            },
            "selection": {
                "algorithm": "sha256(dataset_id + ':' + immutable_unit_id), ascending",
                "ud_fraction": ud_fraction,
                "ud_selected_sentences": len(selected_ud_ids),
                "ud_selection_sha256": sha256_value(selected_ud_ids),
                "plug2_fraction": plug2_fraction,
                "plug2_selected_documents": len(selected_plug2_paths),
                "plug2_selection_sha256": sha256_value(selected_plug2_paths),
            },
            "outputs": {
                "ud": {
                    "filename": ud_output.name,
                    "records": ud_record_count,
                    "bytes": ud_output_bytes,
                    "sha256": ud_output_sha256,
                },
                "plug2": {
                    "filename": plug2_output.name,
                    "records": plug2_record_count,
                    "bytes": plug2_output_bytes,
                    "sha256": plug2_output_sha256,
                },
            },
            "projection": {
                "ud_compressed_gib": ud_projection,
                "plug2_compressed_gib": plug2_projection,
                "total_compressed_gib": total_projection,
                "ceiling_gib": OUTPUT_CEILING_GIB,
                "within_ceiling": True,
            },
            "residuals": {
                "ud_untagged_or_other_excluded": True,
                "plug2_non_uk_or_unknown_excluded": True,
                "unlabeled_orthography_not_inferred": True,
                "periodization_unresolved_pending_qualified_evidence": True,
                "full_materialization_authorized": False,
            },
            "safeguards": {
                "historical_forms_protected": True,
                "modern_correction_eligible": False,
                "provider_calls": False,
                "phase4_authorized": False,
            },
        }
        _write_receipt(staging_dir / receipt_output.name, receipt)
        os.replace(staging_dir, private_output_dir)
        return receipt
    finally:
        if staging_dir.exists():
            shutil.rmtree(staging_dir)


def _parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--ud-dir", type=Path, required=True)
    parser.add_argument("--plug2-archive", type=Path, required=True)
    parser.add_argument("--plug2-metadata", type=Path, required=True)
    parser.add_argument("--private-output-dir", type=Path, required=True)
    parser.add_argument("--receipt-output", type=Path, required=True)
    parser.add_argument("--ud-fraction", type=float, default=0.01)
    parser.add_argument("--plug2-fraction", type=float, default=0.001)
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = _parse_args(argv)
    try:
        receipt = materialize_canary(
            ud_dir=args.ud_dir,
            plug2_archive=args.plug2_archive,
            plug2_metadata=args.plug2_metadata,
            private_output_dir=args.private_output_dir,
            receipt_output=args.receipt_output,
            ud_fraction=args.ud_fraction,
            plug2_fraction=args.plug2_fraction,
        )
    except HistoricalMaterializationError as exc:
        print(canonical_json({"status": "blocked", "error": str(exc)}))
        return 2
    print(canonical_json({"status": "canary_complete", "receipt_sha256": sha256_value(receipt)}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
