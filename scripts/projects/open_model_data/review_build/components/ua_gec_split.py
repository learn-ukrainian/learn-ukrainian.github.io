"""WP1 official-reader file store and independently recomputed RB-1 splits.

Virtual annotation rows retain complete, unmodified source/target file fields.
Their sentence spans and control metadata come from the official reader. Neither
matching whitespace nor edit alignment changes the text exported by candidates.
"""

from __future__ import annotations

import csv
import importlib.util
import math
import re
import sys
import unicodedata
from bisect import bisect_left
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path

from ..attribution import Attribution
from ..contract import Citation, Value, canonical, digest
from ..errors import require
from ..roles import sentence_hash

LAYERS = ("gec-only", "gec-fluency")
CORPUS = {
    "store": "ua-gec",
    "table": "corpus",
    "split": "split",
    "document": "document",
    "author": "author",
    "layer": "layer",
    "text": "source_sentence",
}
REGISTER_FORM = (
    "UA-GEC (Syvokon, Nahorna, Kuchmiichuk, Osidach, UNLP 2023), "
    "https://github.com/grammarly/ua-gec, CC BY 4.0, changes indicated."
)


def official_corpus(root: Path, layer: str):
    """Load the held official package without changing the shared environment."""
    package = root / "python" / "ua_gec"
    if "ua_gec" not in sys.modules:
        spec = importlib.util.spec_from_file_location(
            "ua_gec", package / "__init__.py", submodule_search_locations=[str(package)]
        )
        require(spec is not None and spec.loader is not None, "reader_unavailable")
        module = importlib.util.module_from_spec(spec)
        sys.modules["ua_gec"] = module
        try:
            spec.loader.exec_module(module)
        except BaseException:
            del sys.modules["ua_gec"]
            raise
    module = sys.modules["ua_gec"]
    require(Path(module.__file__).resolve() == (package / "__init__.py").resolve(), "reader_identity")
    corpus = module.Corpus(partition="all", annotation_layer=layer)
    # The upstream reader has no root parameter. Its data directory is the only
    # override; parsing, metadata expansion and sentence indices stay upstream.
    corpus._data_dir = root / "data" / layer
    return corpus


def line_spans(raw: str, sentences: list[str]) -> list[tuple[int, int]]:
    """Authenticate the official reader's LF-separated sentence indexing."""
    require(raw.rstrip("\n").split("\n") == sentences, "sentence_file_binding")
    result, offset = [], 0
    for sentence in sentences:
        result.append((offset, offset + len(sentence)))
        offset += len(sentence) + 1
    return result


def sentence_spans(original: str, sentences: list[str]) -> list[tuple[int, int]]:
    """Map official sentence characters back to the complete annotated source.

    Upstream splitting changes whitespace; no non-whitespace character may
    change or disappear. These offsets never change exported file bytes.
    """
    positions = [m.start() for m in re.finditer(r"\S", original)]
    compact = "".join(original[p] for p in positions)
    offset, spans = 0, []
    for sentence in sentences:
        text = "".join(sentence.split())
        if not text:
            position = positions[offset] if offset < len(positions) else len(original)
            spans.append((position, position))
            continue
        if compact[offset : offset + len(text)] != text:
            # A calque denominator cannot be reconstructed by guessing.
            require(False, "annotation_sentence_binding")
        spans.append((positions[offset], positions[offset + len(text) - 1] + 1))
        offset += len(text)
    require(offset == len(compact), "annotation_sentence_binding")
    return spans


def sentence_edits(original: str, sentences: list[str], annotations) -> tuple[list[list[str]], set[int]]:
    """Bind character edits to sentences; ambiguous boundaries withhold both."""
    spans = sentence_spans(original, sentences)
    edits = [[] for _ in sentences]
    ambiguous = set()
    for annotation in annotations:
        start, end = annotation.start, annotation.end
        require(0 <= start <= end <= len(original), "annotation_span")
        tag = annotation.meta.get("error_type")
        require(isinstance(tag, str) and bool(tag), "annotation_type")
        owners = [
            i
            for i, (lo, hi) in enumerate(spans)
            if (start < end and start < hi and end > lo) or (start == end and lo <= start <= hi)
        ]
        if not owners:
            # Whitespace-only boundary edits affect both neighboring sentences.
            owners = [
                i
                for i in range(len(spans))
                if start <= (spans[i + 1][0] if i + 1 < len(spans) else len(original))
                and end >= (spans[i - 1][1] if i else 0)
            ]
            ambiguous.update(owners)
        if len(owners) != 1 or any(not (spans[i][0] <= start <= end <= spans[i][1]) for i in owners):
            ambiguous.update(owners)
        require(bool(owners), "annotation_sentence_binding")
        for i in owners:
            edits[i].append(tag)
    return edits, ambiguous


def replay_alignment(original: str, sentences: list[str], targets: list[str], annotations) -> list[str | None]:
    """Authenticate each target against only this annotator's sentence edits.

    Compare with upstream whitespace collapsed, never letters or punctuation
    stripped. A gap-only punctuation edit may attach to either neighbour; only
    that edit's literal replacement can be added at the corresponding edge.
    Edits crossing sentence characters or non-punctuation gap edits are
    boundary_ambiguous. Targets shifted by deletion are unaligned even if file
    line counts agree. No replay text is exported.
    """
    spans = sentence_spans(original, sentences)
    _, ambiguous = sentence_edits(original, sentences, annotations)
    reasons = []
    for i, (lo, hi) in enumerate(spans):
        local, gaps = [], []
        unsafe = False
        for ann in annotations:
            if lo <= ann.start <= ann.end <= hi:
                local.append(ann)
            elif i in ambiguous:
                left = spans[i - 1][1] if i else 0
                right = spans[i + 1][0] if i + 1 < len(spans) else len(original)
                before = i > 0 and left <= ann.start <= ann.end <= lo
                after = i + 1 < len(spans) and hi <= ann.start <= ann.end <= right
                if not (before or after):
                    # Ignore remote edits, but refuse an overlapping boundary.
                    unsafe |= ann.start < hi and ann.end > lo
                    continue
                replacement = ann.suggestions[0] if ann.suggestions else original[ann.start : ann.end]

                def punct(text):
                    return all(c.isspace() or unicodedata.category(c).startswith("P") for c in text)

                if not punct(original[ann.start : ann.end]) or not punct(replacement):
                    unsafe = True
                else:
                    gaps.append((before, replacement))
        if unsafe:
            reasons.append("boundary_ambiguous")
            continue
        # Project annotation offsets onto the learner line's character map.
        # Keep its whitespace unless an actual annotation replaces that region.
        source = sentences[i]
        original_positions = [m.start() + lo for m in re.finditer(r"\S", original[lo:hi])]
        learner_positions = [m.start() for m in re.finditer(r"\S", source)]

        def boundary(
            position,
            *,
            original_positions=original_positions,
            learner_positions=learner_positions,
        ):
            index = bisect_left(original_positions, position)
            if index < len(original_positions) and original_positions[index] == position:
                return learner_positions[index]
            if index and position == original_positions[index - 1] + 1:
                return learner_positions[index - 1] + 1
            if 0 < index < len(original_positions):
                original_gap = original_positions[index] - original_positions[index - 1]
                learner_gap = learner_positions[index] - learner_positions[index - 1]
                if original_gap == learner_gap:
                    return learner_positions[index - 1] + position - original_positions[index - 1]
                # Splitting collapsed a whitespace run; its interior offsets
                # have no unique image on the learner line. Never choose one.
                return None
            return 0 if not original_positions else None

        text, cursor = [], 0
        mapped_ambiguous = False
        for ann in sorted(local, key=lambda a: (a.start, a.end)):
            start = boundary(ann.start)
            end = start if ann.start == ann.end else boundary(ann.end)
            if start is None or end is None or start < cursor:
                mapped_ambiguous = True
                break
            text.append(source[cursor:start])
            # The official reader unescapes newline suggestions after replay.
            text.append(ann.suggestions[0].replace("\\n", "\n") if ann.suggestions else source[start:end])
            cursor = end
        if mapped_ambiguous:
            reasons.append("boundary_ambiguous")
            continue
        text.append(source[cursor:])
        variants = {"".join(text)}
        for before, replacement in gaps:
            variants |= {replacement + value if before else value + replacement for value in variants}
        target = " ".join(targets[i].split()) if i < len(targets) else None
        match = target is not None and any(" ".join(value.split()) == target for value in variants)
        reasons.append(None if match else "boundary_ambiguous" if gaps else "unaligned")
    return reasons


@dataclass(frozen=True)
class SplitManifest:
    train_documents: frozenset[str]
    dev_authors: frozenset[str]
    dev_documents: frozenset[str]
    test_hashes: frozenset[str]
    overlap_sentences: frozenset[tuple[str, int]]

    def counts(self) -> dict[str, int]:
        return {
            "train_documents": len(self.train_documents),
            "dev_authors": len(self.dev_authors),
            "dev_documents": len(self.dev_documents & self.train_documents),
            "overlap_sentences": len(self.overlap_sentences),
        }


def split_manifest(rows: list[dict]) -> SplitManifest:
    """Recompute whole-author carve-out; the framework recomputes it again."""
    authors = defaultdict(set)
    tests = {sentence_hash(r["source_sentence"]) for r in rows if r["split"] == "test"}
    for row in rows:
        if row["split"] == "train" and row["layer"] == "gec-only":
            authors[row["author"]].add(row["document"])
    train = set().union(*authors.values()) if authors else set()
    target = math.ceil(len(train) / 10)
    dev_authors, dev_documents = set(), set()
    for author in sorted(authors, key=lambda a: digest(("omd-rb1-dev" + a).encode())):
        if len(dev_documents) >= target:
            break
        dev_authors.add(author)
        dev_documents.update(authors[author])
    dev_documents.update(r["document"] for r in rows if r["author"] in dev_authors)
    overlaps = {
        (r["document"], r["sentence_index"])
        for r in rows
        if r["split"] == "train" and r["layer"] == "gec-only" and sentence_hash(r["source_sentence"]) in tests
    }
    return SplitManifest(*(frozenset(s) for s in (train, dev_authors, dev_documents, tests, overlaps)))


def exclusion(row: dict, splits: SplitManifest) -> str | None:
    if row["split"] == "test":
        return "test_source"
    if row["document"] in splits.dev_documents:
        return "dev_source"
    if row["is_sensitive"] == 1:
        return "sensitive_source"
    if sentence_hash(row["source_sentence"]) in splits.test_hashes:
        return "ruler_overlap"
    return None


class UaGecFileStore:
    """Pinned file fields addressed by official annotation file + sentence index."""

    def __init__(self, root: Path | None = None):
        # The registry installs one shared unbound adapter. Extraction replaces
        # it with a fresh store in each SnapshotReader, after reading the request.
        self.root = root.resolve() if root is not None else None
        self._hashes: dict[str, str] = {}
        self._rows: dict[tuple[str, str], dict] = {}
        self._corpus: list[dict] = []
        if self.root is None:
            return
        self.metadata = list(csv.DictReader(self._read("data/metadata.csv").splitlines()))
        require(len({r["id"] for r in self.metadata}) == len(self.metadata), "metadata_duplicate")
        for relative in ("README.md", "LICENSE"):
            self._read(relative)
        for path in sorted((self.root / "python" / "ua_gec").glob("*.py")):
            self._read(path.relative_to(self.root).as_posix())
        for layer in LAYERS:
            for document in official_corpus(self.root, layer):
                self._document(document, layer)
        self.splits = split_manifest(self._corpus)

    def _read(self, relative: str) -> str:
        require(self.root is not None, "source_input_unavailable")
        path = self.root / relative
        require(not path.is_symlink() and path.resolve().is_relative_to(self.root), "source_file_path")
        raw = path.read_bytes()
        sha = digest(raw)
        require(relative not in self._hashes or self._hashes[relative] == sha, "source_file_changed")
        self._hashes[relative] = sha
        return raw.decode("utf-8")

    def _document(self, document, layer: str) -> None:
        meta = document.meta
        require(meta.partition in {"train", "test"} and type(meta.is_sensitive) is bool, "metadata_binding")
        base = f"data/{layer}/{meta.partition}"
        annotation_file = f"{base}/annotated/{meta.doc_id}.a{meta.annotator_id}.ann"
        table = f"data/{layer}"
        annotation = self._read(annotation_file)
        require(annotation == str(document.annotated), "annotation_file_binding")
        source = self._read(f"{base}/source-sentences/{meta.doc_id}.src.txt")
        target = self._read(f"{base}/target-sentences/{meta.doc_id}.a{meta.annotator_id}.txt")
        source_sentences, target_sentences = document.source_sentences, document.target_sentences
        source_spans = line_spans(source, source_sentences)
        target_spans = line_spans(target, target_sentences)
        annotations = document.annotated.get_annotations()
        edits, ambiguous = sentence_edits(document.source, source_sentences, annotations)
        alignment = replay_alignment(document.source, source_sentences, target_sentences, annotations)
        for i, sentence in enumerate(source_sentences):
            key = f"file={annotation_file};sentence={i}"
            row = {
                "row_key": key,
                "table": table,
                "source_id": "ua_gec",
                "split": meta.partition,
                "document": meta.doc_id,
                "author": meta.author_id,
                "annotator": meta.annotator_id,
                "layer": layer,
                "is_sensitive": int(meta.is_sensitive),
                "submission_type": meta.submission_type,
                "source_language": meta.source_language,
                "sentence_index": i,
                "source": source,
                "target": target,
                "source_sentence": sentence,
                "target_sentence": target_sentences[i] if i < len(target_sentences) else "",
                "source_span": source_spans[i],
                "target_span": target_spans[i] if i < len(target_spans) else None,
                "edits": edits[i],
                "aligned": alignment[i] is None,
                "alignment_reason": alignment[i],
                "edit_aligned": i not in ambiguous,
            }
            require((table, key) not in self._rows, "duplicate_unit_query")
            self._rows[table, key] = row
            self._corpus.append(row)

    def row(self, table: str, row_key: str) -> dict:
        require(self.root is not None, "source_input_unavailable")
        require((table, row_key) in self._rows, "row_unavailable")
        return dict(self._rows[table, row_key])

    def all_rows(self, table: str) -> list[dict]:
        require(self.root is not None, "source_input_unavailable")
        require(table == "corpus", "corpus_table")
        return [dict(r) for r in self._corpus]

    def units(self, query: dict) -> list[str]:
        require(self.root is not None, "source_input_unavailable")
        require(
            query.get("kind") == "official_reader"
            and query.get("store") == "ua-gec"
            and query.get("split") == "train"
            and query.get("layer") in LAYERS,
            "unit_query",
        )
        require(query.get("selection") in {"all_sentences", "contains_calque"}, "unit_query")
        # Count from held official-reader rows, never the candidate stream.
        return [
            r["row_key"]
            for r in self._corpus
            if r["split"] == query["split"]
            and r["layer"] == query["layer"]
            and (query["selection"] == "all_sentences" or "F/Calque" in r["edits"])
        ]

    def file_hashes(self) -> dict[str, str]:
        require(self.root is not None, "source_input_unavailable")
        for relative in tuple(self._hashes):
            self._read(relative)
        return dict(sorted(self._hashes.items()))

    def compatibility(self) -> list[dict]:
        return [
            {
                "store": "ua-gec",
                "table": table,
                "source_id": "ua_gec",
                "role": "ua_gec",
                "source_column": "source_id",
                "source_values": ["ua_gec"],
                "sensitive": "is_sensitive",
                "split": "split",
                "document": "document",
                "text": "source_sentence",
                "layer": "layer",
                "edits": "edits",
            }
            for table in sorted({r["table"] for r in self._corpus})
        ]


def cited_value(row: dict, slot: str, field: str) -> Value:
    sentence = row[f"{field}_sentence"]
    span = row[f"{field}_span"]
    citation = Citation(
        "ua_gec",
        "ua-gec",
        row["table"],
        row["row_key"],
        field,
        f"UA-GEC {row['layer']} {row['split']}; document {row['document']}; "
        f"annotator {row['annotator']}; sentence {row['sentence_index']}",
        digest(row[field].encode("utf-8")),
    )
    # Empty accounting values never pass the quotation gate. Their source key
    # remains available for independently derived unit accounting.
    return Value(slot, sentence, (citation,), span, "verbatim")


class UaGecAttribution:
    """Map only the complete registered form, authenticated by held metadata."""

    def __init__(self, store: UaGecFileStore | None = None):
        self.store = store

    def resolve(self, form, citation, row, reader) -> Attribution:
        require(citation.source_id == "ua_gec" and row["source_id"] == "ua_gec", "attribution_unresolved")
        store = self.store if self.store is not None else reader.files["ua-gec"]
        readme = store._read("README.md")
        bibliography = re.search(r"@inproceedings\{syvokon-etal-2023-ua,(.*?)\n\}", readme, re.S)
        require(bibliography is not None, "attribution_unresolved")
        text = " ".join(bibliography[1].split())
        required = (
            'author = "Syvokon, Oleksiy and Nahorna, Olena and Kuchmiichuk, Pavlo and Osidach, Nastasiia"',
            'booktitle = "Proceedings of the Second Ukrainian Natural Language Processing Workshop (UNLP)"',
            'year = "2023"',
        )
        require(all(value in text for value in required), "attribution_unresolved")
        require("https://github.com/grammarly/ua-gec" in readme, "attribution_unresolved")
        licence = store._read("LICENSE")
        require("Attribution 4.0 International" in licence, "attribution_unresolved")
        require(" ".join(form.split()) == REGISTER_FORM, "attribution_unresolved")
        return Attribution(REGISTER_FORM, form)


def parser_hashes() -> dict[str, str]:
    """Pin WP1 code explicitly: the WP0 code pin scans only its own directory."""
    root = Path(__file__).parent
    return {
        p.name: digest(p.read_bytes())
        for p in sorted(root.glob("*.py"))
        if p.name
        in {
            "ua_gec_split.py",
            "c1_ua_gec.py",
            "c6a_calque.py",
            "ua_gec_component.py",
            "ua_gec_mutations.py",
            "c1.py",
            "c6a.py",
        }
    }


def manifest_bytes(store: UaGecFileStore) -> bytes:
    splits = store.splits
    return (
        canonical(
            {
                "schema": "ua-gec-split.v1",
                "counts": splits.counts(),
                "dev_authors": sorted(splits.dev_authors),
                "dev_documents": sorted(splits.dev_documents),
                "test_hashes": sorted(splits.test_hashes),
                "overlap_sentences": sorted(splits.overlap_sentences),
                "files": store.file_hashes(),
            }
        )
        + b"\n"
    )
