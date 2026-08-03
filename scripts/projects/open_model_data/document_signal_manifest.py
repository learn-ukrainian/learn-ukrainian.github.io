"""Emit a deterministic, text-free document-signal evidence manifest.

This is diagnostic evidence only.  It never admits data, alters source data,
runs a model, or makes a duplicate/contamination finding erase a record.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sqlite3
import sys
import tempfile
import unicodedata
from collections import Counter
from collections.abc import Iterator, Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any, BinaryIO

from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.projects.open_model_data.inventory_existing_assets import WORD_RE
from scripts.projects.open_model_data.model_view_exporter import build_exclusion_registry, registry_receipt

CONTRACTS = ROOT / "data/projects/open_model_data/contracts"
ROW_SCHEMA = CONTRACTS / "document_signal_record_v1.schema.json"
RECEIPT_SCHEMA = CONTRACTS / "document_signal_receipt_v1.schema.json"
IDENTIFIER_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")
URL_RE = re.compile(r"(?:https?://|www\.)[^\s]+", re.IGNORECASE)
APOSTROPHE_VARIANTS = frozenset("'`´‘’ʼ")
STRESS = frozenset(("\u0300", "\u0301"))


class ManifestError(ValueError):
    """The manifest cannot be safely produced or verified."""


def canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"), sort_keys=True)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _read_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ManifestError(f"cannot read JSON {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise ManifestError(f"expected JSON object: {path}")
    return value


def _validator(path: Path) -> Draft202012Validator:
    schema = _read_json(path)
    Draft202012Validator.check_schema(schema)
    return Draft202012Validator(schema)


def _validate(value: Mapping[str, Any], validator: Draft202012Validator, label: str) -> None:
    errors = sorted(validator.iter_errors(value), key=lambda error: list(error.path))
    if errors:
        error = errors[0]
        where = ".".join(str(part) for part in error.path) or "<root>"
        raise ManifestError(f"{label} schema failure at {where}: {error.message}")


def _identifier(value: str) -> str:
    if IDENTIFIER_RE.fullmatch(value) is None:
        raise ManifestError(f"unsafe SQLite identifier: {value!r}")
    return f'"{value}"'


def _opaque_id(prefix: str, value: str) -> str:
    return f"{prefix}.{hashlib.sha256(value.encode('utf-8')).hexdigest()[:24]}"


def _connect(path: Path) -> sqlite3.Connection:
    if not path.is_file() or path.stat().st_size == 0:
        raise FileNotFoundError(path)
    connection = sqlite3.connect(path.resolve().as_uri() + "?mode=ro", uri=True)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA query_only=ON")
    return connection


def _dimension(row: sqlite3.Row, source: Mapping[str, Any], name: str) -> str:
    spec = source["adapter"]["dimensions"][name]
    raw = spec.get("constant") if "constant" in spec else row[f"dimension_{name}"]
    return str(raw or "").strip() or "unknown"


def _query(
    source: Mapping[str, Any], admission: Mapping[str, Any] | None, columns: set[str]
) -> tuple[str, tuple[str, ...]]:
    adapter = source["adapter"]
    needed = {adapter["id_column"], adapter["text_column"], adapter["locator_column"]}
    needed.update(item["column"] for item in adapter["dimensions"].values() if "column" in item)
    if admission is not None:
        needed.update((admission["source_group_column"], admission["work_group_column"]))
    excluded = adapter.get("exclude")
    if excluded:
        needed.add(excluded["column"])
    missing = sorted(needed - columns)
    if missing:
        raise ManifestError("missing source columns: " + ", ".join(missing))
    fields = [
        f'{_identifier(adapter["id_column"])} AS "raw_id"',
        f'{_identifier(adapter["text_column"])} AS "text"',
        f'{_identifier(adapter["locator_column"])} AS "locator"',
    ]
    for name, spec in sorted(adapter["dimensions"].items()):
        if "column" in spec:
            fields.append(f"{_identifier(spec['column'])} AS {_identifier('dimension_' + name)}")
    if admission is not None:
        fields.extend(
            (
                f'{_identifier(admission["source_group_column"])} AS "source_group"',
                f'{_identifier(admission["work_group_column"])} AS "work_group"',
            )
        )
    params: tuple[str, ...] = ()
    where = ""
    if excluded:
        params = tuple(str(value) for value in excluded["values"])
        where = f" WHERE {_identifier(excluded['column'])} NOT IN ({','.join('?' for _ in params)})"
    return (
        f"SELECT {', '.join(fields)} FROM {_identifier(adapter['table'])}{where} "
        f"ORDER BY {_identifier(adapter['id_column'])} ASC, {_identifier(adapter['locator_column'])} ASC",
        params,
    )


def _signals(text: str) -> dict[str, Any]:
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    line_hashes = [hashlib.sha256(line.encode("utf-8")).hexdigest() for line in lines]
    repetitions = sum(count - 1 for count in Counter(line_hashes).values() if count > 1)
    return {
        "counts": {
            "characters": len(text),
            "utf8_bytes": len(text.encode("utf-8")),
            "lexical_words": len(WORD_RE.findall(text)),
            "lines": len(text.splitlines()),
            "cyrillic": sum("\u0400" <= char <= "\u052f" for char in text),
            "latin": sum(("a" <= char.lower() <= "z") for char in text),
            "digits": sum(char.isdigit() for char in text),
            "ukrainian_specific": sum(char.casefold() in "іїєґ" for char in text),
            "russian_specific": sum(char.casefold() in "ёыэъ" for char in text),
        },
        "normalization": {
            "nfc_changed": unicodedata.normalize("NFC", text) != text,
            "nfkc_changed": unicodedata.normalize("NFKC", text) != text,
            "apostrophe_variants": sum(char in APOSTROPHE_VARIANTS for char in text),
            "stress_marks": sum(char in STRESS for char in text),
            "control_characters": sum(char not in "\n\r\t" and unicodedata.category(char) == "Cc" for char in text),
            "replacement_characters": text.count("\ufffd"),
        },
        "boilerplate": {"repeated_nonblank_lines": repetitions, "url_like_tokens": len(URL_RE.findall(text))},
    }


def _near_fingerprint(text: str) -> dict[str, Any]:
    """Return bounded partition-minhash evidence, never a duplicate verdict."""
    normalized = " ".join(unicodedata.normalize("NFKC", text).casefold().split())
    tokens = normalized.split()
    grams = [" ".join(tokens[index : index + 3]) for index in range(max(0, len(tokens) - 2))]
    if not grams:
        grams = [normalized] if normalized else [""]
    unique_grams = sorted(set(grams))
    fingerprint = hashlib.sha256("\x1f".join(unique_grams).encode("utf-8")).hexdigest()
    minima: list[str | None] = [None] * 8
    for gram in unique_grams:
        digest = hashlib.sha256(f"document-signal-partition-minhash-v1:{gram}".encode()).hexdigest()
        band = int(digest[:2], 16) % len(minima)
        if minima[band] is None or digest < minima[band]:
            minima[band] = digest
    bands = [
        value[:16]
        if value is not None
        else hashlib.sha256(f"document-signal-empty-band-v1:{index}:{fingerprint}".encode()).hexdigest()[:16]
        for index, value in enumerate(minima)
    ]
    return {
        "algorithm": "nfkc-casefold-word-3gram-partition-minhash-v1",
        "fingerprint": fingerprint,
        "bands": bands,
        "state": "unresolved_candidate_only_no_automatic_erasure",
    }


def _capability_evidence(
    source: Mapping[str, Any], admission: Mapping[str, Any], admission_receipt: Mapping[str, Any]
) -> dict[str, str]:
    """Expose capability states without inferring training authorization."""
    admission_evidence = admission["evidence"]
    family = str(source["source_family"])
    disposition = "family_mixed_or_unknown"
    for family_receipt in admission_receipt.get("families", []):
        if str(family_receipt.get("source_family")) != family:
            continue
        actual_rows = int(family_receipt.get("actual", {}).get("rows", 0))
        active = [
            name
            for name, counts in family_receipt.get("dispositions", {}).items()
            if int(counts.get("rows", 0)) == actual_rows and actual_rows > 0
        ]
        if len(active) == 1:
            disposition = f"family_all_{active[0]}"
        break
    undecided = "not_decided_by_document_signal_manifest"
    return {
        "rights_evidence": str(admission_evidence.get("rights", "unknown")),
        "origin_evidence": str(admission_evidence.get("origin", "unknown")),
        "contamination_evidence": str(admission_evidence.get("contamination", "unknown")),
        "admission_disposition": disposition,
        "raw_text_redistribution": undecided,
        "local_model_learning": undecided,
        "model_training": undecided,
        "dataset_publication": undecided,
        "learning_view_emission": (
            "not_emitted_by_admission_receipt"
            if admission_receipt.get("training_eligible_emitted") is False
            else "not_determined_by_document_signal_manifest"
        ),
    }


def _stage(path: Path, content: bytes) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(dir=path.parent, prefix=path.name, suffix=".tmp", delete=False) as handle:
            temporary = Path(handle.name)
            handle.write(content)
            handle.flush()
            os.fsync(handle.fileno())
        return temporary
    except OSError:
        if temporary is not None:
            temporary.unlink(missing_ok=True)
        raise


@dataclass
class _StagedJsonl:
    """Incrementally write canonical JSONL without retaining rows in memory."""

    temporary: Path
    handle: BinaryIO
    digest: Any
    bytes_written: int = 0
    records: int = 0

    @classmethod
    def open(cls, output: Path) -> _StagedJsonl:
        output.parent.mkdir(parents=True, exist_ok=True)
        handle = tempfile.NamedTemporaryFile(  # noqa: SIM115 - closed by finish or abort
            mode="w+b", dir=output.parent, prefix=output.name, suffix=".tmp.jsonl", delete=False
        )
        return cls(temporary=Path(handle.name), handle=handle, digest=hashlib.sha256())

    def write(self, value: Mapping[str, Any]) -> None:
        encoded = (canonical_json(value) + "\n").encode("utf-8")
        self.handle.write(encoded)
        self.digest.update(encoded)
        self.bytes_written += len(encoded)
        self.records += 1

    def finish(self) -> dict[str, Any]:
        self.handle.flush()
        os.fsync(self.handle.fileno())
        self.handle.close()
        return {"bytes": self.bytes_written, "records": self.records, "sha256": self.digest.hexdigest()}

    def abort(self) -> None:
        if not self.handle.closed:
            self.handle.close()
        self.temporary.unlink(missing_ok=True)


def _promote(items: Sequence[tuple[Path, Path]]) -> None:
    """Promote all staged artifacts, restoring the prior pair if one fails."""
    backups: list[tuple[Path, Path]] = []
    promoted: list[Path] = []
    temporary_paths = [temporary for temporary, _output in items]
    for temporary, output in items:
        output.parent.mkdir(parents=True, exist_ok=True)
        if not temporary.is_file():
            raise ManifestError(f"staged artifact is missing: {temporary}")
        if output.exists() and not output.is_file():
            raise ManifestError(f"artifact destination is not a file: {output}")
    try:
        for temporary, output in items:
            if output.exists():
                descriptor, name = tempfile.mkstemp(dir=output.parent, prefix=output.name, suffix=".rollback")
                os.close(descriptor)
                backup = Path(name)
                os.replace(output, backup)
                backups.append((output, backup))
            os.replace(temporary, output)
            promoted.append(output)
    except OSError as exc:
        for output in reversed(promoted):
            output.unlink(missing_ok=True)
        for output, backup in reversed(backups):
            if backup.exists():
                os.replace(backup, output)
        raise ManifestError("atomic artifact promotion failed") from exc
    finally:
        for temporary in temporary_paths:
            temporary.unlink(missing_ok=True)
    for _output, backup in backups:
        backup.unlink(missing_ok=True)


def _admissions(config: Mapping[str, Any]) -> dict[str, Mapping[str, Any]]:
    families = config.get("families")
    if not isinstance(families, list):
        raise ManifestError("admission config lacks families")
    result = {str(item.get("source_family")): item for item in families if isinstance(item, dict)}
    if len(result) != len(families):
        raise ManifestError("invalid or duplicate admission source family")
    return result


def _stream(
    profile: Mapping[str, Any], admissions: Mapping[str, Mapping[str, Any]], input_root: Path
) -> Iterator[tuple[Mapping[str, Any], Mapping[str, Any], sqlite3.Row]]:
    for source in profile.get("sources", []):
        family = str(source.get("source_family"))
        admission = admissions.get(family)
        if admission is None:
            raise ManifestError(f"profile source absent from admission config: {family}")
        database = input_root / str(source["adapter"]["database"])
        with _connect(database) as connection:
            columns = {
                str(row[1])
                for row in connection.execute(f"PRAGMA table_info({_identifier(source['adapter']['table'])})")
            }
            query, params = _query(source, admission, columns)
            for row in connection.execute(query, params):
                yield source, admission, row


def _artifact(path: Path, records: int) -> dict[str, Any]:
    return {"bytes": path.stat().st_size, "records": records, "sha256": sha256_file(path)}


def build_manifest(
    *, config_path: Path, input_root: Path, manifest_output: Path, receipt_output: Path, spool_path: Path | None = None
) -> dict[str, Any]:
    """Perform two deterministic source passes and atomically publish both artifacts."""
    config = _read_json(config_path)
    for key in ("schema_version", "profile_config", "admission_config", "admission_receipt"):
        if key not in config:
            raise ManifestError(f"document signal config lacks {key}")
    profile_path = input_root / str(config["profile_config"])
    admission_path = input_root / str(config["admission_config"])
    admission_receipt_path = input_root / str(config["admission_receipt"])
    profile, admission_config = _read_json(profile_path), _read_json(admission_path)
    admission_receipt = _read_json(admission_receipt_path)
    admissions = _admissions(admission_config)
    if not admission_receipt.get("coverage", {}).get("complete", False):
        raise ManifestError("admission receipt is incomplete")
    row_validator, receipt_validator = _validator(ROW_SCHEMA), _validator(RECEIPT_SCHEMA)
    registry = build_exclusion_registry(
        v011_manifest=ROOT / "data/projects/ua_eval_harness/heldout_manifest_v1.json",
        v02_packet=ROOT / "data/projects/ua_eval_harness/v0.2/review_packet_priority_v1.jsonl",
    )
    manifest_output.parent.mkdir(parents=True, exist_ok=True)
    receipt_output.parent.mkdir(parents=True, exist_ok=True)
    owned_spool = spool_path is None
    if spool_path is None:
        descriptor, name = tempfile.mkstemp(prefix="document-signal-", suffix=".sqlite3", dir=manifest_output.parent)
        os.close(descriptor)
        spool_path = Path(name)
    else:
        spool_path.parent.mkdir(parents=True, exist_ok=True)
    manifest: _StagedJsonl | None = None
    receipt_temporary: Path | None = None
    try:
        with sqlite3.connect(spool_path) as spool:
            spool.execute(
                "CREATE TABLE records (ordinal INTEGER PRIMARY KEY, content_hash TEXT NOT NULL, record_id TEXT NOT NULL UNIQUE)"
            )
            for ordinal, (source, _admission, row) in enumerate(_stream(profile, admissions, input_root)):
                record_id = _opaque_id(f"record.{source['source_family']}", str(row["raw_id"]))
                content_hash = hashlib.sha256(str(row["text"] or "").encode("utf-8")).hexdigest()
                spool.execute("INSERT INTO records VALUES (?, ?, ?)", (ordinal, content_hash, record_id))
            spool.execute("CREATE INDEX records_hash ON records(content_hash)")
            spool.commit()
            manifest = _StagedJsonl.open(manifest_output)
            source_counts: Counter[str] = Counter()
            evidence_counts: Counter[str] = Counter()
            capability_counts: Counter[str] = Counter()
            signal_counts: Counter[str] = Counter()
            seen = 0
            for ordinal, (source, admission, row) in enumerate(_stream(profile, admissions, input_root)):
                text = str(row["text"] or "")
                family = str(source["source_family"])
                record_id = _opaque_id(f"record.{family}", str(row["raw_id"]))
                content_hash = hashlib.sha256(text.encode("utf-8")).hexdigest()
                duplicate_count = int(
                    spool.execute("SELECT count(*) FROM records WHERE content_hash = ?", (content_hash,)).fetchone()[0]
                )
                match = registry.match(text)
                source_group = str(row["source_group"] or "unknown")
                work_group = str(row["work_group"] or "unknown")
                capability = _capability_evidence(source, admission, admission_receipt)
                row_value = {
                    "schema_version": "document_signal_record_v1",
                    "ordinal": ordinal,
                    "record_id": record_id,
                    "source_id": _opaque_id(f"source.{family}", source_group),
                    "work_id": _opaque_id(f"work.{family}", work_group),
                    "source_family": family,
                    "inventory_asset_id": source["inventory_asset_id"],
                    "dimensions": {
                        name: _dimension(row, source, name) for name in ("period", "genre", "register", "origin")
                    },
                    "admission_evidence_state": dict(sorted(admission["evidence"].items())),
                    "capability_evidence": capability,
                    "content_sha256": content_hash,
                    "signals": _signals(text),
                    "exact_duplicate": {"group_id": _opaque_id("duplicate", content_hash), "count": duplicate_count},
                    "near_duplicate": _near_fingerprint(text),
                    "heldout_contamination": {
                        "state": "matched" if match.matched else "clear",
                        "method": match.method,
                        "semantics": "signal_only_no_automatic_erasure",
                    },
                }
                _validate(row_value, row_validator, "document signal row")
                manifest.write(row_value)
                source_counts[family] += 1
                evidence_counts["|".join(f"{key}={value}" for key, value in sorted(admission["evidence"].items()))] += 1
                capability_counts["|".join(f"{key}={value}" for key, value in sorted(capability.items()))] += 1
                counts = row_value["signals"]["counts"]
                normalization = row_value["signals"]["normalization"]
                boilerplate = row_value["signals"]["boilerplate"]
                signal_counts["heldout_matched_records"] += int(match.matched)
                signal_counts["exact_duplicate_records"] += int(duplicate_count > 1)
                signal_counts["mixed_cyrillic_latin_records"] += int(counts["cyrillic"] > 0 and counts["latin"] > 0)
                signal_counts["ukrainian_and_russian_specific_letter_records"] += int(
                    counts["ukrainian_specific"] > 0 and counts["russian_specific"] > 0
                )
                signal_counts["nfc_changed_records"] += int(normalization["nfc_changed"])
                signal_counts["nfkc_changed_records"] += int(normalization["nfkc_changed"])
                signal_counts["replacement_character_records"] += int(normalization["replacement_characters"] > 0)
                signal_counts["control_character_records"] += int(normalization["control_characters"] > 0)
                signal_counts["repeated_nonblank_line_records"] += int(boilerplate["repeated_nonblank_lines"] > 0)
                signal_counts["url_like_token_records"] += int(boilerplate["url_like_tokens"] > 0)
                seen += 1
            signal_counts["exact_duplicate_groups"] = int(
                spool.execute(
                    "SELECT count(*) FROM (SELECT content_hash FROM records GROUP BY content_hash HAVING count(*) > 1)"
                ).fetchone()[0]
            )
        if manifest is None:
            raise ManifestError("manifest writer was not initialized")
        expected_by_family = {str(item["source_family"]): int(item["expected"]["rows"]) for item in profile["sources"]}
        expected_rows = sum(expected_by_family.values())
        if seen != expected_rows or dict(source_counts) != expected_by_family:
            raise ManifestError(
                f"incomplete corpus coverage: expected {expected_by_family}, observed {dict(source_counts)}"
            )
        artifact = manifest.finish()
        receipt = {
            "schema_version": "document_signal_receipt_v1",
            "manifest_id": str(config.get("manifest_id", "document-signal-manifest-v1")),
            "inputs": {
                "generator_sha256": sha256_file(Path(__file__)),
                "config_sha256": sha256_file(config_path),
                "profile_sha256": sha256_file(profile_path),
                "admission_config_sha256": sha256_file(admission_path),
                "admission_receipt_sha256": sha256_file(admission_receipt_path),
                "row_schema_sha256": sha256_file(ROW_SCHEMA),
                "receipt_schema_sha256": sha256_file(RECEIPT_SCHEMA),
                "evaluation_registry": registry_receipt(registry),
            },
            "outputs": {"manifest": artifact},
            "coverage": {
                "complete": True,
                "expected_rows": expected_rows,
                "processed_rows": seen,
                "source_families": dict(sorted(source_counts.items())),
            },
            "signal_states": {
                "admission_evidence": dict(sorted(evidence_counts.items())),
                "capability_evidence": dict(sorted(capability_counts.items())),
                "document_signals": dict(sorted(signal_counts.items())),
            },
            "algorithm": {
                "ordering": "profile configuration source order, SQLite id, locator",
                "serialization": "UTF-8 canonical JSON sorted keys LF",
                "exact_duplicates": "sqlite sha256 content groups",
                "near_duplicates": "NFKC casefold word-3gram partition-minhash bands; unresolved candidate only",
                "timestamps_omitted": True,
            },
            "resources": {
                "streaming": True,
                "sqlite_spool": True,
                "source_passes": 2,
                "runtime_bound": (
                    "bounded evaluation registry, one source record, and SQLite spool; "
                    "no corpus text retained in output"
                ),
            },
            "safety": {
                "contains_text": False,
                "uses_model": False,
                "training": False,
                "upload": False,
                "publication": False,
                "source_databases_read_only": True,
            },
        }
        _validate(receipt, receipt_validator, "document signal receipt")
        receipt_temporary = _stage(receipt_output, (canonical_json(receipt) + "\n").encode("utf-8"))
        _promote(((manifest.temporary, manifest_output), (receipt_temporary, receipt_output)))
        return receipt
    finally:
        if manifest is not None:
            manifest.abort()
        if receipt_temporary is not None:
            receipt_temporary.unlink(missing_ok=True)
        if owned_spool:
            spool_path.unlink(missing_ok=True)


def verify_existing(*, manifest_path: Path, receipt_path: Path) -> bool:
    receipt = _read_json(receipt_path)
    _validate(receipt, _validator(RECEIPT_SCHEMA), "document signal receipt")
    current_contracts = {
        "generator_sha256": sha256_file(Path(__file__)),
        "row_schema_sha256": sha256_file(ROW_SCHEMA),
        "receipt_schema_sha256": sha256_file(RECEIPT_SCHEMA),
    }
    for key, current_hash in current_contracts.items():
        if receipt["inputs"][key] != current_hash:
            raise ManifestError(f"receipt input drift: {key}")
    digest = hashlib.sha256()
    records = 0
    validator = _validator(ROW_SCHEMA)
    previous = -1
    with manifest_path.open("rb") as handle:
        for line in handle:
            digest.update(line)
            records += 1
            value = json.loads(line.decode("utf-8"))
            _validate(value, validator, "document signal row")
            if value["ordinal"] != previous + 1:
                raise ManifestError("manifest ordering is not deterministic")
            previous = value["ordinal"]
    expected = receipt["outputs"]["manifest"]
    if expected != {"bytes": manifest_path.stat().st_size, "records": records, "sha256": digest.hexdigest()}:
        raise ManifestError("manifest artifact hash/count/size mismatch")
    return True


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path)
    parser.add_argument("--input-root", type=Path, default=ROOT)
    parser.add_argument("--manifest-output", type=Path)
    parser.add_argument("--receipt-output", type=Path)
    parser.add_argument("--spool", type=Path)
    parser.add_argument("--verify-existing", action="store_true")
    args = parser.parse_args(argv)
    try:
        if args.verify_existing:
            if args.manifest_output is None or args.receipt_output is None:
                raise ManifestError("--verify-existing requires outputs")
            verify_existing(manifest_path=args.manifest_output, receipt_path=args.receipt_output)
        else:
            if args.config is None or args.manifest_output is None or args.receipt_output is None:
                raise ManifestError("--config and both outputs are required")
            build_manifest(
                config_path=args.config,
                input_root=args.input_root,
                manifest_output=args.manifest_output,
                receipt_output=args.receipt_output,
                spool_path=args.spool,
            )
    except (ManifestError, OSError, sqlite3.Error, json.JSONDecodeError) as exc:
        parser.error(str(exc))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
