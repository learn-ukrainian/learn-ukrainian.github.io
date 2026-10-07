"""Citation role admission derived from pinned rows, never candidate claims."""

import json
import math
import re
import unicodedata
from collections import defaultdict

from .contract import Candidate, Citation, digest, values
from .errors import require
from .snapshot import SnapshotReader


def sentence_hash(text: str) -> str:
    return digest(" ".join(unicodedata.normalize("NFC", text).casefold().split()).encode("utf-8"))


class SourceRoles:
    def __init__(self, reader: SnapshotReader, compatibility: list[dict], corpus: dict | None = None):
        self.reader = reader
        self.compatibility = {}
        for entry in compatibility:
            key = (entry["store"], entry["table"], entry["source_id"])
            require(key not in self.compatibility, "role_duplicate")
            require(entry["role"] in {"modern", "sum11", "ua_gec", "textbook", "forbidden"}, "role_spec")
            require(
                isinstance(entry.get("source_column"), str)
                and bool(entry["source_column"])
                and isinstance(entry.get("source_values"), list)
                and bool(entry["source_values"]),
                "role_spec",
            )
            self.compatibility[key] = entry
            sensitive = entry.get("sensitive", "is_sensitive" if entry["role"] == "ua_gec" else None)
            require(sensitive is None or (isinstance(sensitive, str) and bool(sensitive)), "role_spec")
            require(entry["role"] != "ua_gec" or sensitive is not None, "role_spec")
        self.dev_authors: set[str] = set()
        self.dev_documents: set[str] = set()
        self.test_hashes: set[str] = set()
        self.corpus = corpus
        if corpus:
            self._splits(corpus)

    def _splits(self, spec: dict) -> None:
        rows = self.reader.all_rows(spec["store"], spec["table"])
        documents = defaultdict(set)
        train_documents = set()
        for row in rows:
            if row[spec["split"]] == "test":
                self.test_hashes.add(sentence_hash(row[spec["text"]]))
            elif row[spec["split"]] == "train" and row[spec["layer"]] == "gec-only":
                document = str(row[spec["document"]])
                documents[str(row[spec["author"]])].add(document)
                train_documents.add(document)
        target = math.ceil(len(train_documents) / 10)
        for author in sorted(documents, key=lambda a: digest(("omd-rb1-dev" + a).encode())):
            if len(self.dev_documents) >= target:
                break
            self.dev_authors.add(author)
            self.dev_documents.update(documents[author])
        for row in rows:
            if str(row[spec["author"]]) in self.dev_authors:
                self.dev_documents.add(str(row[spec["document"]]))

    def check(self, citation: Citation, candidate: Candidate, bindings: set[str], rejected_slot: str = "") -> None:
        key = (citation.store, citation.table, citation.source_id)
        require(key in self.compatibility, "source_compatibility")
        spec = self.compatibility[key]
        row = self.reader.row(citation)
        require(
            spec["source_column"] in row and row[spec["source_column"]] in spec["source_values"], "source_compatibility"
        )
        source_file = str(row.get(spec.get("source_file", "source_file"), ""))
        require(
            not any(name.startswith("zno_") for name in (citation.source_id, source_file, citation.table)),
            "forbidden_source",
        )
        require(spec["role"] != "forbidden", "forbidden_source")
        sensitive = spec.get("sensitive", "is_sensitive" if spec["role"] == "ua_gec" else None)
        if sensitive is not None:
            require(sensitive in row and row[sensitive] in {0, "0", 1, "1"}, "sensitivity_unavailable")
            require(row[sensitive] not in {1, "1"}, "sensitive_source")
        if spec["role"] == "sum11" or citation.source_id == "sum11":
            require(
                spec["role"] == "sum11"
                and candidate.component == "C7"
                and "contrast_pair" in bindings
                and "c7_opt_in" in candidate.flags
                and "soviet_colonization_context" in candidate.flags,
                "sum11_role",
            )
            occurrences = [value for value in values(candidate) if citation in value.citations]
            require(
                bool(occurrences)
                and all(value in candidate.context and value.slot == rejected_slot for value in occurrences),
                "sum11_role",
            )
            require(
                row.get(spec.get("risk", "sovietization_risk")) is not None
                and row.get(spec.get("keywords", "sovietization_keywords")) is not None,
                "sum11_markers",
            )
        if spec["role"] == "ua_gec":
            require(self.corpus is not None, "split_unavailable")
            split = row[spec["split"]]
            require(split == "train", "test_source")
            require(str(row[spec["document"]]) not in self.dev_documents, "dev_source")
            require(sentence_hash(row[spec["text"]]) not in self.test_hashes, "ruler_overlap")
            if candidate.component in {"C6", "C6a", "C6b"}:
                edits = row[spec["edits"]]
                edits = json.loads(edits) if isinstance(edits, str) else edits
                require(
                    row[spec["layer"]] == "gec-fluency" and bool(edits) and all(edit == "F/Calque" for edit in edits),
                    "mixed_edit",
                )
        if spec["role"] == "textbook":
            require(source_file in spec["allowlisted_files"], "textbook_allowlist")
            require(
                bool(re.fullmatch(r"(?:[1-9]|1[01]|10-11)-klas-.+|uni-.+", source_file)),
                "textbook_grade",
            )
        if "quarantine" in spec:
            require(not row[spec["quarantine"]], "quarantined_source")

    def metadata(self, citation: Citation) -> dict:
        spec = self.compatibility[citation.store, citation.table, citation.source_id]
        result = {"source_role": spec["role"]}
        if spec["role"] == "sum11":
            row = self.reader.row(citation)
            result.update(
                sovietization_risk=row[spec.get("risk", "sovietization_risk")],
                sovietization_keywords=row[spec.get("keywords", "sovietization_keywords")],
            )
        return result
