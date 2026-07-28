#!/usr/bin/env python3
"""Build and verify the pinned held-out UA-GEC calque + grammar manifest.

Every ``gec-fluency/test`` M2 sentence with an ``F/Calque`` or ``G/*`` edit
is included. Every other test sentence gets a hash-only exclusion receipt.
Selection is quota-free and has no product or private-data input.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
import subprocess
import sys
from collections import Counter, defaultdict
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[3]
DEFAULT_CONFIG = ROOT / "data/projects/ua_eval_harness/heldout_manifest_config.json"
DEFAULT_OUTPUT = ROOT / "data/projects/ua_eval_harness/heldout_manifest_v1.json"
DEFAULT_UA_GEC_ROOT = ROOT / "data/ua-gec"
SCHEMA_VERSION = "ua_gec_heldout_manifest.v1"
ITEM_FIELDS = [
    "id",
    "doc_id",
    "sentence_index",
    "author_id",
    "is_native",
    "source_language",
    "annotator_ids",
    "is_sensitive",
    "source",
    "source_sha256",
    "observed_tags",
    "eligible_tags",
    "references",
]
REFERENCE_FIELDS = ["annotator_index", "target", "target_sha256", "edits"]
EDIT_FIELDS = ["start", "end", "tag", "replacement"]
EXCLUSION_FIELDS = ["id", "doc_id", "sentence_index", "source_sha256", "observed_tags"]


class ManifestError(ValueError):
    """Pinned provenance or manifest-integrity failure."""


@dataclass(frozen=True, slots=True)
class M2Edit:
    start: int
    end: int
    tag: str
    replacement: str
    annotator: str


@dataclass(frozen=True, slots=True)
class M2Sentence:
    doc_id: str
    sentence_index: int
    source: str
    edits: tuple[M2Edit, ...]

    @property
    def record_id(self) -> str:
        return f"ua-gec-test-{self.doc_id}-s{self.sentence_index:04d}"


def _sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _sha256_text(value: str) -> str:
    return _sha256_bytes(value.encode("utf-8"))


def _canonical_sha256(value: Any) -> str:
    raw = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return _sha256_text(raw)


def _load_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ManifestError(f"cannot load JSON {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise ManifestError(f"expected a JSON object in {path}")
    return value


def _mapping(value: Any, label: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise ManifestError(f"{label} must be an object")
    return value


def _git_head(repo: Path) -> str:
    result = subprocess.run(
        ["git", "-C", str(repo), "rev-parse", "HEAD"],
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode:
        raise ManifestError(f"UA-GEC root is not a readable Git checkout: {repo}")
    return result.stdout.strip()


def verify_upstream(root: Path, config: Mapping[str, Any]) -> None:
    """Fail closed unless the checkout and all relevant upstream bytes are pinned."""
    upstream = _mapping(config.get("upstream"), "config.upstream")
    commit = str(upstream.get("commit", ""))
    if len(commit) != 40 or _git_head(root) != commit:
        raise ManifestError(f"UA-GEC checkout must be pinned at {commit}")
    for relative, expected in _mapping(upstream.get("files"), "config.upstream.files").items():
        path = root / str(relative)
        if not path.is_file():
            raise ManifestError(f"missing pinned upstream file: {relative}")
        if _sha256_bytes(path.read_bytes()) != expected:
            raise ManifestError(f"upstream hash mismatch for {relative}")
    license_text = (root / "LICENSE").read_text(encoding="utf-8", errors="replace")
    if "Attribution 4.0 International" not in license_text:
        raise ManifestError("UA-GEC license evidence does not identify CC BY 4.0")
    readme = (root / "README.md").read_text(encoding="utf-8", errors="replace")
    if f"Version {upstream.get('version')} released" not in readme:
        raise ManifestError("UA-GEC README does not attest the configured version")


def parse_m2(path: Path) -> list[M2Sentence]:
    """Parse the sentence and edit subset of M2 used by this manifest."""
    try:
        blocks = path.read_text(encoding="utf-8").strip().split("\n\n")
    except OSError as exc:
        raise ManifestError(f"cannot read M2 input {path}: {exc}") from exc
    current_doc: str | None = None
    sentence_index = 0
    sentences: list[M2Sentence] = []
    for block in blocks:
        lines = block.splitlines()
        if not lines:
            continue
        marker = re.fullmatch(r"S # (?P<doc_id>\d{4})", lines[0])
        if marker:
            current_doc = marker.group("doc_id")
            sentence_index = 0
            if not current_doc:
                raise ManifestError("empty document id in M2 input")
            continue
        if not lines[0].startswith("S ") or current_doc is None:
            raise ManifestError(f"unexpected M2 block header: {lines[0]}")
        sentence_index += 1
        source = lines[0][2:]
        token_count = len(source.split())
        edits: list[M2Edit] = []
        for line in lines[1:]:
            parts = line.split("|||")
            if not line.startswith("A ") or len(parts) != 6:
                raise ManifestError(f"malformed M2 annotation line: {line}")
            span = parts[0].split()
            if len(span) != 3:
                raise ManifestError(f"malformed M2 span: {parts[0]}")
            start, end = int(span[1]), int(span[2])
            tag = parts[1]
            if tag == "noop":
                continue
            if start < 0 or end < start or end > token_count:
                raise ManifestError(f"invalid span {start}:{end} for {current_doc}/{sentence_index}")
            edits.append(M2Edit(start, end, tag, parts[2], parts[5]))
        sentences.append(M2Sentence(current_doc, sentence_index, source, tuple(edits)))
    if not sentences:
        raise ManifestError("M2 input contains no sentences")
    return sentences


def load_metadata(path: Path) -> tuple[dict[str, dict[str, str]], set[str], set[str]]:
    """Load document metadata and prove author-level train/test separation."""
    try:
        with path.open(encoding="utf-8-sig", newline="") as handle:
            rows = list(csv.DictReader(handle))
    except OSError as exc:
        raise ManifestError(f"cannot read UA-GEC metadata: {exc}") from exc
    required = {
        "id",
        "author_id",
        "is_native",
        "source_language",
        "annotator_id",
        "partition",
        "is_sensitive",
    }
    if not rows or not required.issubset(rows[0]):
        raise ManifestError("UA-GEC metadata is empty or missing required columns")
    by_id: dict[str, dict[str, str]] = {}
    authors: dict[str, set[str]] = {"train": set(), "test": set()}
    for row in rows:
        doc_id = row["id"]
        partition = row["partition"]
        if doc_id in by_id:
            raise ManifestError(f"duplicate metadata id: {doc_id}")
        if partition not in authors or not row["author_id"]:
            raise ManifestError(f"invalid metadata for document {doc_id}")
        by_id[doc_id] = row
        authors[partition].add(row["author_id"])
    overlap = authors["train"] & authors["test"]
    if overlap:
        raise ManifestError(f"train/test author overlap detected ({len(overlap)} authors)")
    return by_id, authors["train"], authors["test"]


def _in_scope(tag: str, predicate: Mapping[str, Any]) -> bool:
    exact = {str(value) for value in predicate.get("included_exact_tags", [])}
    prefixes = tuple(str(value) for value in predicate.get("included_tag_prefixes", []))
    return tag in exact or tag.startswith(prefixes)


def _selected(sentence: M2Sentence, predicate: Mapping[str, Any]) -> dict[str, list[M2Edit]]:
    selected: dict[str, list[M2Edit]] = defaultdict(list)
    for edit in sentence.edits:
        if _in_scope(edit.tag, predicate):
            selected[edit.annotator].append(edit)
    for annotator, edits in selected.items():
        edits.sort(key=lambda edit: (edit.start, edit.end, edit.tag, edit.replacement))
        previous_end = -1
        for edit in edits:
            if edit.start < previous_end:
                raise ManifestError(f"overlapping edits for {sentence.record_id} annotator {annotator}")
            previous_end = max(previous_end, edit.end)
    return dict(sorted(selected.items()))


def apply_edits(source: str, edits: Sequence[Mapping[str, Any] | M2Edit]) -> str:
    """Apply non-overlapping token edits from right to left."""
    tokens = source.split()
    normalized: list[tuple[int, int, str]] = []
    for edit in edits:
        if isinstance(edit, M2Edit):
            normalized.append((edit.start, edit.end, edit.replacement))
        else:
            normalized.append((int(edit["start"]), int(edit["end"]), str(edit["replacement"])))
    for start, end, replacement in sorted(normalized, reverse=True):
        tokens[start:end] = replacement.split() if replacement else []
    return " ".join(tokens)


def build_manifest(root: Path, config: Mapping[str, Any]) -> dict[str, Any]:
    """Build included public records and exclusion receipts."""
    if config.get("schema_version") != "ua_gec_heldout_config.v1":
        raise ManifestError("unsupported config schema")
    predicate = _mapping(config.get("predicate"), "config.predicate")
    if predicate.get("partition") != "test" or predicate.get("annotation_layer") != "gec-fluency":
        raise ManifestError("v1 must use gec-fluency/test")
    if predicate.get("arbitrary_item_quota") is not None:
        raise ManifestError("arbitrary item quotas are forbidden")
    verify_upstream(root, config)
    upstream = _mapping(config["upstream"], "config.upstream")
    m2_rel = "data/gec-fluency/test/gec-fluency.test.m2"
    sentences = parse_m2(root / m2_rel)
    metadata, train_authors, test_authors = load_metadata(root / "data/metadata.csv")
    m2_docs = {sentence.doc_id for sentence in sentences}
    metadata_test_docs = {doc_id for doc_id, row in metadata.items() if row["partition"] == "test"}
    if m2_docs != metadata_test_docs:
        raise ManifestError("M2 document ids do not exactly match metadata test documents")

    items: list[list[Any]] = []
    exclusions: list[list[Any]] = []
    tag_counts: Counter[str] = Counter()
    reference_count = 0
    edit_count = 0
    for sentence in sentences:
        row = metadata[sentence.doc_id]
        if row["partition"] != "test":
            raise ManifestError(f"non-test metadata for {sentence.record_id}")
        selected = _selected(sentence, predicate)
        observed_tags = sorted({edit.tag for edit in sentence.edits})
        if not selected:
            exclusions.append(
                [
                    sentence.record_id,
                    sentence.doc_id,
                    sentence.sentence_index,
                    _sha256_text(sentence.source),
                    observed_tags,
                ]
            )
            continue
        references: list[list[Any]] = []
        eligible_tags: set[str] = set()
        for annotator, edits in selected.items():
            target = apply_edits(sentence.source, edits)
            serialized = [[e.start, e.end, e.tag, e.replacement] for e in edits]
            references.append([annotator, target, _sha256_text(target), serialized])
            reference_count += 1
            edit_count += len(edits)
            tag_counts.update(edit.tag for edit in edits)
            eligible_tags.update(edit.tag for edit in edits)
        items.append(
            [
                sentence.record_id,
                sentence.doc_id,
                sentence.sentence_index,
                row["author_id"],
                row["is_native"] == "1",
                row["source_language"] or None,
                sorted(row["annotator_id"].split()),
                row["is_sensitive"] == "1",
                sentence.source,
                _sha256_text(sentence.source),
                observed_tags,
                sorted(eligible_tags),
                references,
            ]
        )

    payload = {"items": items, "exclusions": exclusions}
    manifest = {
        "schema_version": SCHEMA_VERSION,
        "manifest_id": config["manifest_id"],
        "task": "minimal-edit Ukrainian calque and grammar correction",
        "attribution": {
            "dataset": "UA-GEC",
            "repository": upstream["repository"],
            "source_commit": upstream["commit"],
            "source_version": upstream["version"],
            "license": upstream["license"],
            "license_url": upstream["license_url"],
            "citation": upstream["citation"],
            "modifications": (
                "Deterministic derivative of pinned UA-GEC gec-fluency/test. "
                "Targets apply only F/Calque and G/* edits per annotator; other edits "
                "remain unchanged. Excluded sentences retain hash-only receipts."
            ),
        },
        "predicate": dict(predicate),
        "record_layouts": {
            "item": ITEM_FIELDS,
            "reference": REFERENCE_FIELDS,
            "edit": EDIT_FIELDS,
            "exclusion": EXCLUSION_FIELDS,
        },
        "record_semantics": {
            "inclusion_reason": "has_calque_or_grammar_edit",
            "exclusion_reason": predicate["exclusion_reason"],
            "upstream_locator": f"{m2_rel} + doc_id + sentence_index",
            "annotator_ids": "metadata.csv annotator_id values; upstream metadata namespace",
            "reference_annotator_index": (
                "M2 annotation final field; upstream zero-based reference index, "
                "not an index into item.annotator_ids"
            ),
        },
        "integrity": {
            "upstream_files": dict(upstream["files"]),
            "payload_sha256": _canonical_sha256(payload),
            "train_test_author_overlap": 0,
        },
        "counts": {
            "upstream_test_documents": len(m2_docs),
            "upstream_test_authors": len(test_authors),
            "upstream_train_authors": len(train_authors),
            "upstream_test_sentences": len(sentences),
            "included_sentences": len(items),
            "excluded_sentences": len(exclusions),
            "references": reference_count,
            "eligible_edits": edit_count,
            "eligible_edits_by_tag": dict(sorted(tag_counts.items())),
        },
        **payload,
    }
    validate_manifest(manifest)
    return manifest


def validate_manifest(manifest: Mapping[str, Any]) -> None:
    """Validate a committed manifest without an upstream checkout."""
    if manifest.get("schema_version") != SCHEMA_VERSION:
        raise ManifestError("unsupported manifest schema")
    predicate = _mapping(manifest.get("predicate"), "manifest.predicate")
    counts = _mapping(manifest.get("counts"), "manifest.counts")
    integrity = _mapping(manifest.get("integrity"), "manifest.integrity")
    layouts = _mapping(manifest.get("record_layouts"), "manifest.record_layouts")
    semantics = _mapping(manifest.get("record_semantics"), "manifest.record_semantics")
    if layouts != {
        "item": ITEM_FIELDS,
        "reference": REFERENCE_FIELDS,
        "edit": EDIT_FIELDS,
        "exclusion": EXCLUSION_FIELDS,
    }:
        raise ManifestError("record layouts do not match the v1 schema")
    if semantics.get("exclusion_reason") != predicate.get("exclusion_reason"):
        raise ManifestError("exclusion semantics do not match the predicate")
    items, exclusions = manifest.get("items"), manifest.get("exclusions")
    if not isinstance(items, list) or not isinstance(exclusions, list):
        raise ManifestError("items and exclusions must be arrays")
    if any(not isinstance(record, list) or len(record) != len(ITEM_FIELDS) for record in items):
        raise ManifestError("invalid compact item record")
    if any(not isinstance(record, list) or len(record) != len(EXCLUSION_FIELDS) for record in exclusions):
        raise ManifestError("invalid compact exclusion record")
    ids = [str(record[0]) for record in [*items, *exclusions]]
    if len(ids) != len(set(ids)):
        raise ManifestError("duplicate record ids")
    if len(items) != counts.get("included_sentences"):
        raise ManifestError("included sentence count mismatch")
    if len(exclusions) != counts.get("excluded_sentences"):
        raise ManifestError("excluded sentence count mismatch")
    if len(ids) != counts.get("upstream_test_sentences"):
        raise ManifestError("sentence disposition count mismatch")

    tags: Counter[str] = Counter()
    references = edits_count = 0
    for item in items:
        item_id = str(item[0])
        source = str(item[8])
        if not source or item[9] != _sha256_text(source):
            raise ManifestError(f"source hash mismatch: {item_id}")
        item_references = item[12]
        if not isinstance(item_references, list) or not item_references:
            raise ManifestError(f"missing references: {item_id}")
        for reference in item_references:
            if not isinstance(reference, list) or len(reference) != len(REFERENCE_FIELDS):
                raise ManifestError(f"invalid compact reference: {item_id}")
            target = str(reference[1])
            edits = reference[3]
            if not isinstance(edits, list) or not edits:
                raise ManifestError(f"missing edits: {item_id}")
            if reference[2] != _sha256_text(target):
                raise ManifestError(f"target hash mismatch: {item_id}")
            edit_objects: list[dict[str, Any]] = []
            for edit in edits:
                if not isinstance(edit, list) or len(edit) != len(EDIT_FIELDS):
                    raise ManifestError(f"invalid compact edit: {item_id}")
                edit_object = dict(zip(EDIT_FIELDS, edit, strict=True))
                edit_objects.append(edit_object)
                tag = str(edit_object["tag"])
                if not _in_scope(tag, predicate):
                    raise ManifestError(f"out-of-scope edit: {item_id}")
                tags[tag] += 1
            if apply_edits(source, edit_objects) != target:
                raise ManifestError(f"target/edit mismatch: {item_id}")
            references += 1
            edits_count += len(edits)
    for exclusion in exclusions:
        if not exclusion[3]:
            raise ManifestError(f"invalid exclusion receipt: {exclusion[0]}")
    if references != counts.get("references"):
        raise ManifestError("reference count mismatch")
    if edits_count != counts.get("eligible_edits"):
        raise ManifestError("edit count mismatch")
    if dict(sorted(tags.items())) != counts.get("eligible_edits_by_tag"):
        raise ManifestError("tag count mismatch")
    payload = {"items": items, "exclusions": exclusions}
    if integrity.get("payload_sha256") != _canonical_sha256(payload):
        raise ManifestError("payload hash mismatch")


def write_manifest(path: Path, manifest: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(manifest, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n",
        encoding="utf-8",
    )


def _summary(manifest: Mapping[str, Any]) -> str:
    counts = manifest["counts"]
    return (
        f"UA-GEC held-out manifest valid: {counts['included_sentences']} included, "
        f"{counts['excluded_sentences']} excluded, {counts['references']} references, "
        f"{counts['eligible_edits']} eligible edits"
    )


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--ua-gec-root", type=Path, default=DEFAULT_UA_GEC_ROOT)
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--check", action="store_true")
    mode.add_argument("--verify-existing", action="store_true")
    args = parser.parse_args(argv)
    try:
        if args.verify_existing:
            manifest = _load_json(args.output)
            validate_manifest(manifest)
        else:
            manifest = build_manifest(args.ua_gec_root, _load_json(args.config))
            if args.check:
                if manifest != _load_json(args.output):
                    raise ManifestError(f"committed manifest is stale: {args.output}")
            else:
                write_manifest(args.output, manifest)
        print(_summary(manifest))
        return 0
    except ManifestError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
