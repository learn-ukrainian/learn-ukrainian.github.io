"""Produce fail-closed, content-blind admission dispositions for an existing corpus.

The runner is deliberately not an exporter.  It reads source text only long
enough to count lexical words and test the frozen evaluation registry; its
manifest contains hashes and logical identifiers, never text or host paths.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import resource
import sqlite3
import sys
import tempfile
import time
from collections import Counter
from collections.abc import Iterator, Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any, TextIO

from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.projects.open_model_data.inventory_existing_assets import WORD_RE
from scripts.projects.open_model_data.model_view_exporter import (
    build_exclusion_registry,
    registry_receipt,
)

CONTRACTS = ROOT / "data/projects/open_model_data/contracts"
CONFIG_SCHEMA = CONTRACTS / "corpus_admission_config_v1.schema.json"
RECEIPT_SCHEMA = CONTRACTS / "corpus_admission_receipt_v1.schema.json"


class AdmissionError(ValueError):
    """Raised when a corpus cannot be processed without weakening a gate."""


@dataclass(frozen=True)
class AdmissionRun:
    """The deterministic receipt and coverage outcome from one admission pass."""

    receipt: dict[str, Any]
    receipt_path: Path

    @property
    def complete(self) -> bool:
        return bool(self.receipt["coverage"]["complete"])


def canonical_json(value: Any) -> str:
    """Serialize stable UTF-8 JSON suitable for byte-for-byte receipts."""
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"), sort_keys=True)


def sha256_file(path: Path) -> str:
    """Hash an artifact without loading it into memory."""
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _read_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise AdmissionError(f"cannot read JSON {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise AdmissionError(f"expected JSON object: {path}")
    return value


def _validator(path: Path) -> Draft202012Validator:
    schema = _read_json(path)
    Draft202012Validator.check_schema(schema)
    return Draft202012Validator(schema)


def _validate(value: Mapping[str, Any], validator: Draft202012Validator, label: str) -> None:
    errors = sorted(validator.iter_errors(value), key=lambda error: list(error.path))
    if errors:
        location = ".".join(str(part) for part in errors[0].path) or "<root>"
        raise AdmissionError(f"{label} does not satisfy its schema at {location}: {errors[0].message}")


def _identifier(value: str) -> str:
    if not value.replace("_", "a").isalnum() or value[:1].isdigit():
        raise AdmissionError(f"unsafe SQLite identifier: {value!r}")
    return f'"{value}"'


def _connect_read_only(path: Path) -> sqlite3.Connection:
    if not path.is_file() or path.stat().st_size == 0:
        raise FileNotFoundError(path)
    connection = sqlite3.connect(path.resolve().as_uri() + "?mode=ro", uri=True)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA query_only=ON")
    return connection


def _value(row: sqlite3.Row, name: str, specification: Mapping[str, Any]) -> str:
    value = specification.get("constant")
    if "column" in specification:
        value = row[f"attribute_{name}"]
    normalized = str(value or "").strip()
    return normalized if normalized else "unknown"


def _opaque_id(prefix: str, value: str) -> str:
    """Return a stable non-locator identifier for a source/work/record grouping."""
    return f"{prefix}.{hashlib.sha256(value.encode('utf-8')).hexdigest()[:24]}"


def _atomic_json(path: Path, value: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(dir=path.parent, prefix=path.name, suffix=".tmp", delete=False) as handle:
            temporary = Path(handle.name)
            handle.write((canonical_json(value) + "\n").encode("utf-8"))
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)


@dataclass
class AtomicJsonl:
    """Write a local manifest atomically while retaining only a running hash."""

    output: Path
    handle: TextIO
    temporary: Path
    digest: Any
    records: int = 0
    bytes_written: int = 0

    @classmethod
    def open(cls, output: Path) -> AtomicJsonl:
        output.parent.mkdir(parents=True, exist_ok=True)
        handle = tempfile.NamedTemporaryFile(  # noqa: SIM115 - closed by finish/abort
            mode="w", encoding="utf-8", newline="", dir=output.parent,
            prefix=output.name, suffix=".tmp", delete=False,
        )
        return cls(output, handle, Path(handle.name), hashlib.sha256())

    def write(self, value: Mapping[str, Any]) -> None:
        encoded = (canonical_json(value) + "\n").encode("utf-8")
        self.handle.write(encoded.decode("utf-8"))
        self.digest.update(encoded)
        self.records += 1
        self.bytes_written += len(encoded)

    def finish(self) -> dict[str, Any]:
        self.handle.flush()
        os.fsync(self.handle.fileno())
        self.handle.close()
        return {"bytes": self.bytes_written, "records": self.records, "sha256": self.digest.hexdigest()}

    def replace(self) -> None:
        os.replace(self.temporary, self.output)

    def abort(self) -> None:
        if not self.handle.closed:
            self.handle.close()
        self.temporary.unlink(missing_ok=True)


def _profile_sources(profile: Mapping[str, Any]) -> dict[str, Mapping[str, Any]]:
    sources = profile.get("sources")
    if not isinstance(sources, list):
        raise AdmissionError("profile config lacks sources")
    result = {str(source.get("source_family")): source for source in sources if isinstance(source, dict)}
    if len(result) != len(sources):
        raise AdmissionError("profile config has duplicate or invalid source families")
    return result


def _source_query(profile_source: Mapping[str, Any], family: Mapping[str, Any]) -> str:
    adapter = profile_source["adapter"]
    attributes = family["attributes"]
    selected = {
        "record_id": adapter["id_column"],
        "text": adapter["text_column"],
        "source_group": family["source_group_column"],
        "work_group": family["work_group_column"],
    }
    for name, specification in attributes.items():
        if "column" in specification:
            selected[f"attribute_{name}"] = specification["column"]
    query_columns = [f"{_identifier(column)} AS {_identifier(alias)}" for alias, column in sorted(selected.items())]
    where = ""
    exclusion = adapter.get("exclude")
    if exclusion:
        values = exclusion["values"]
        literals = ", ".join("?" for _ in values)
        where = f" WHERE {_identifier(exclusion['column'])} NOT IN ({literals})"
    query = (
        f"SELECT {', '.join(query_columns)} FROM {_identifier(adapter['table'])}{where} "
        f"ORDER BY {_identifier(adapter['id_column'])} ASC"
    )
    return query


def _query_parameters(profile_source: Mapping[str, Any]) -> tuple[str, ...]:
    exclusion = profile_source["adapter"].get("exclude")
    return tuple(exclusion["values"]) if exclusion else ()


def _unresolved_reasons(evidence: Mapping[str, Any]) -> list[str]:
    required = ("provenance", "acquisition", "snapshot", "rights", "origin", "contamination")
    return [f"{name}_{evidence.get(name, 'missing')}" for name in required if evidence.get(name) != "complete"]


def _disposition(
    *, evidence: Mapping[str, Any], destination: str | None, contamination: str | None
) -> tuple[str, list[str]]:
    if contamination is not None:
        return "excluded", [f"evaluation_contamination_{contamination}"]
    reasons = _unresolved_reasons(evidence)
    if reasons:
        return "unresolved", reasons
    if destination is None:
        return "investigation_only", ["destination_not_declared"]
    # Human acceptance is intentionally outside this runner.  A complete
    # family can be proposed, but this program never emits training_eligible.
    return "proposed_admission", ["operator_acceptance_required"]


def _empty_receipt(config: Mapping[str, Any], profile: Mapping[str, Any], inaccessible: list[dict[str, str]]) -> dict[str, Any]:
    expected_rows = sum(int(source["expected"]["rows"]) for source in profile["sources"])
    expected_words = sum(int(source["expected"]["lexical_words"]) for source in profile["sources"])
    zero = {name: {"rows": 0, "lexical_words": 0} for name in ("excluded", "investigation_only", "proposed_admission", "unresolved")}
    return {
        "schema_version": "corpus_admission_receipt_v1", "admission_id": config["admission_id"],
        "coverage": {"complete": False, "expected_rows": expected_rows, "expected_lexical_words": expected_words,
                     "processed_rows": 0, "processed_lexical_words": 0, "inaccessible_families": inaccessible},
        "dispositions": zero, "families": [], "evaluation_exclusion": {"applied": False, "reason": "source_database_inaccessible"},
        "outputs": {"manifest": {"bytes": 0, "records": 0, "sha256": hashlib.sha256(b"").hexdigest()}},
        "determinism": {"manifest_order": "source family, SQLite record id", "serialization": "UTF-8 canonical JSON with sorted keys and LF", "timestamps_omitted": True},
        "training_eligible_emitted": False,
    }


def admit_corpus(*, config_path: Path, input_root: Path, manifest_output: Path, receipt_output: Path, runtime_output: Path | None = None) -> AdmissionRun:
    """Process every configured row, or emit an incomplete receipt without drops."""
    config = _read_json(config_path)
    _validate(config, _validator(CONFIG_SCHEMA), "admission config")
    profile = _read_json(input_root / config["profile_config"])
    profile_sources = _profile_sources(profile)
    families = list(config["families"])
    family_names = [str(family["source_family"]) for family in families]
    if len(family_names) != len(set(family_names)):
        raise AdmissionError("admission config has duplicate source families")
    unknown = {family["source_family"] for family in families} - set(profile_sources)
    if unknown:
        raise AdmissionError(f"admission family absent from profile: {sorted(unknown)}")

    inaccessible: list[dict[str, str]] = []
    for family in families:
        source = profile_sources[family["source_family"]]
        database = input_root / source["adapter"]["database"]
        try:
            with _connect_read_only(database) as connection:
                columns = {str(row[1]) for row in connection.execute(f"PRAGMA table_info({_identifier(source['adapter']['table'])})")}
                needed = {source["adapter"]["id_column"], source["adapter"]["text_column"], family["source_group_column"], family["work_group_column"]}
                needed.update(spec["column"] for spec in family["attributes"].values() if "column" in spec)
                missing = sorted(needed - columns)
                if missing:
                    raise AdmissionError("missing columns: " + ", ".join(missing))
        except (FileNotFoundError, sqlite3.Error, AdmissionError) as exc:
            inaccessible.append({"source_family": family["source_family"], "reason": type(exc).__name__})
    if inaccessible:
        receipt = _empty_receipt(config, profile, sorted(inaccessible, key=lambda item: item["source_family"]))
        _validate(receipt, _validator(RECEIPT_SCHEMA), "incomplete admission receipt")
        _atomic_json(receipt_output, receipt)
        manifest_output.parent.mkdir(parents=True, exist_ok=True)
        manifest_output.write_bytes(b"")
        return AdmissionRun(receipt=receipt, receipt_path=receipt_output)

    started = time.monotonic()
    registry = build_exclusion_registry(
        v011_manifest=ROOT / "data/projects/ua_eval_harness/heldout_manifest_v1.json",
        v02_packet=ROOT / "data/projects/ua_eval_harness/v0.2/review_packet_priority_v1.jsonl",
    )
    disposition_counts: dict[str, Counter[str]] = {name: Counter() for name in ("excluded", "investigation_only", "proposed_admission", "unresolved")}
    family_results: list[dict[str, Any]] = []
    processed_rows = processed_words = 0
    seen_record_ids: set[str] = set()
    manifest = AtomicJsonl.open(manifest_output)
    try:
        for family in families:
            source = profile_sources[family["source_family"]]
            database = input_root / source["adapter"]["database"]
            rows = words = 0
            by_disposition: dict[str, Counter[str]] = {name: Counter() for name in disposition_counts}
            with _connect_read_only(database) as connection:
                cursor = connection.execute(_source_query(source, family), _query_parameters(source))
                for row in cursor:
                    raw_record_id = str(row["record_id"])
                    record_id = _opaque_id(f"record.{family['source_family']}", raw_record_id)
                    if record_id in seen_record_ids:
                        raise AdmissionError(f"duplicate record identity in manifest: {record_id}")
                    seen_record_ids.add(record_id)
                    text = str(row["text"] or "")
                    word_count = len(WORD_RE.findall(text))
                    match = registry.match(text)
                    disposition, reasons = _disposition(
                        evidence=family["evidence"], destination=family["proposed_destination"], contamination=match.method if match.matched else None,
                    )
                    attributes = {
                        name: _value(row, name, spec)
                        for name, spec in sorted(family["attributes"].items())
                    }
                    manifest.write({
                        "attributes": attributes, "disposition": disposition,
                        "evidence_state": dict(sorted(family["evidence"].items())), "reasons": reasons,
                        "record_id": record_id, "source_family": family["source_family"],
                        "source_group_id": _opaque_id(f"source.{family['source_family']}", str(row["source_group"] or "unknown")),
                        "word_count": word_count, "work_group_id": _opaque_id(f"work.{family['source_family']}", str(row["work_group"] or "unknown")),
                    })
                    rows += 1
                    words += word_count
                    processed_rows += 1
                    processed_words += word_count
                    disposition_counts[disposition]["rows"] += 1
                    disposition_counts[disposition]["lexical_words"] += word_count
                    by_disposition[disposition]["rows"] += 1
                    by_disposition[disposition]["lexical_words"] += word_count
            expected = source["expected"]
            family_results.append({"source_family": family["source_family"], "actual": {"rows": rows, "lexical_words": words}, "expected": expected,
                                   "matches_expected": rows == expected["rows"] and words == expected["lexical_words"],
                                   "dispositions": {name: {"rows": by_disposition[name]["rows"], "lexical_words": by_disposition[name]["lexical_words"]} for name in sorted(by_disposition)}})
        artifact = manifest.finish()
        manifest.replace()
    except Exception:
        manifest.abort()
        raise

    expected_rows = sum(int(source["expected"]["rows"]) for source in profile["sources"])
    expected_words = sum(int(source["expected"]["lexical_words"]) for source in profile["sources"])
    complete = processed_rows == expected_rows and processed_words == expected_words and all(item["matches_expected"] for item in family_results)
    receipt = {
        "schema_version": "corpus_admission_receipt_v1", "admission_id": config["admission_id"],
        "coverage": {"complete": complete, "expected_rows": expected_rows, "expected_lexical_words": expected_words,
                     "processed_rows": processed_rows, "processed_lexical_words": processed_words, "inaccessible_families": []},
        "dispositions": {name: {"rows": disposition_counts[name]["rows"], "lexical_words": disposition_counts[name]["lexical_words"]} for name in sorted(disposition_counts)},
        "families": sorted(family_results, key=lambda item: item["source_family"]),
        "evaluation_exclusion": {"applied": True, **registry_receipt(registry)}, "outputs": {"manifest": artifact},
        "determinism": {"manifest_order": "configuration source-family order, SQLite record id", "serialization": "UTF-8 canonical JSON with sorted keys and LF", "timestamps_omitted": True},
        "training_eligible_emitted": False,
    }
    _validate(receipt, _validator(RECEIPT_SCHEMA), "admission receipt")
    _atomic_json(receipt_output, receipt)
    if runtime_output is not None:
        _atomic_json(
            runtime_output,
            {
                "peak_rss_raw": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
                "peak_rss_unit": "platform_rusage_ru_maxrss",
                "schema_version": "corpus_admission_runtime_v1",
                "wall_seconds": round(time.monotonic() - started, 6),
            },
        )
    return AdmissionRun(receipt=receipt, receipt_path=receipt_output)


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Fail-closed admission pass for the existing Ukrainian corpus")
    parser.add_argument("--config", type=Path, default=ROOT / "data/projects/open_model_data/admission/public_external_full_corpus_admission_v1.json")
    parser.add_argument("--input-root", type=Path, default=ROOT)
    parser.add_argument("--manifest-output", type=Path, required=True)
    parser.add_argument("--receipt-output", type=Path, required=True)
    parser.add_argument("--runtime-output", type=Path)
    args = parser.parse_args(argv)
    try:
        result = admit_corpus(config_path=args.config, input_root=args.input_root, manifest_output=args.manifest_output, receipt_output=args.receipt_output, runtime_output=args.runtime_output)
    except AdmissionError as exc:
        parser.error(str(exc))
    print(canonical_json(result.receipt))
    return 0 if result.complete else 2


if __name__ == "__main__":
    raise SystemExit(main())
