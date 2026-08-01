#!/usr/bin/env python3
"""Build non-human Ukrainian silver/protection records from detector candidates.

The factory is intentionally separate from qualified-human correction gold.  It
streams the exact detector artifact, rejects evaluation contamination, performs
cache-only dictionary enrichment, and records uncertainty whenever independent
evidence is insufficient.  It never calls a network adapter, admits an export,
or starts model training.
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
from collections import Counter, defaultdict
from collections.abc import Iterator, Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any, BinaryIO, TextIO

from jsonschema import Draft202012Validator, FormatChecker
from referencing import Registry, Resource

ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.projects.open_model_data import language_contact_detector as detector
from scripts.projects.open_model_data import model_view_exporter

CONTRACTS = ROOT / "data/projects/open_model_data/contracts"
CANDIDATE_SCHEMA = CONTRACTS / "language_contact_candidate_v1.schema.json"
DETECTOR_RECEIPT_SCHEMA = CONTRACTS / "language_contact_receipt_v1.schema.json"
OBSERVATION_SCHEMA = CONTRACTS / "language_contact_silver_observation_v1.schema.json"
RECORD_SCHEMA = CONTRACTS / "language_contact_silver_record_v1.schema.json"
RECEIPT_SCHEMA = CONTRACTS / "language_contact_silver_receipt_v1.schema.json"
ADMISSION_RECEIPT_SCHEMA = CONTRACTS / "corpus_admission_receipt_v1.schema.json"
OPERATOR_PACKET_SCHEMA = CONTRACTS / "corpus_admission_operator_packet_v1.schema.json"

DEFAULT_DETECTOR_CONFIG = ROOT / "data/projects/open_model_data/detector/language_contact_config_v1.json"
DEFAULT_ADMISSION_RECEIPT = (
    ROOT / "data/projects/open_model_data/admission/public_external_accepted_admission_receipt_v1.json"
)
DEFAULT_OPERATOR_PACKET = (
    ROOT / "data/projects/open_model_data/admission/public_external_operator_decision_packet_v1.json"
)
DEFAULT_V011_MANIFEST = ROOT / "data/projects/ua_eval_harness/heldout_manifest_v1.json"
DEFAULT_V02_PACKET = ROOT / "data/projects/ua_eval_harness/v0.2/review_packet_priority_v1.jsonl"

POLICY_VERSION = "language-contact-silver-policy-v1"
SCHEMA_VERSION = "language_contact_silver_record_v1"
RECEIPT_VERSION = "language_contact_silver_receipt_v1"
PROTECTED_PERIODS = frozenset({"middle_ukrainian", "old_east_slavic", "historical", "archaic"})
PROTECTED_REGISTER_FRAGMENTS = (
    "archa",
    "dialect",
    "folk",
    "heritage",
    "histor",
    "marked",
    "regional",
    "slang",
)
CORRECTION_CATEGORIES = frozenset(
    {
        "modern_narration_interference",
        "mixed_surzhyk_candidate",
        "ukrainian_phonetic_russian",
    }
)
AUTHORITATIVE_ALTERNATIVE_SOURCES = frozenset({"heritage_dictionary", "ukrainian_corpus", "ulif_dictua", "slovnyk_me"})
SLOVNYK_LOCATOR_RE = re.compile(r"^https://slovnyk\.me/dict/(?P<slug>[A-Za-z0-9_-]+)/.+$")


class SilverError(ValueError):
    """A silver input or output violates the frozen non-human boundary."""


def canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"), sort_keys=True)


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def sha256_text(value: str) -> str:
    return sha256_bytes(value.encode("utf-8"))


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def read_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise SilverError(f"cannot read JSON {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise SilverError(f"expected JSON object: {path}")
    return value


def require(condition: bool, message: str) -> None:
    if not condition:
        raise SilverError(message)


def validate(
    value: Mapping[str, Any],
    active: Draft202012Validator,
    label: str,
) -> None:
    errors = sorted(active.iter_errors(value), key=lambda item: list(item.path))
    if errors:
        path = ".".join(str(part) for part in errors[0].path) or "<root>"
        raise SilverError(f"{label} schema violation at {path}: {errors[0].message}")


def validate_candidate_integrity(candidate: Mapping[str, Any], label: str) -> None:
    span = candidate["span"]
    original = str(span["original_text"])
    start = int(span["start_char"])
    end = int(span["end_char"])
    core_start = int(span["core_start_char"])
    core_end = int(span["core_end_char"])
    require(end - start == len(original), f"{label} span length does not reconcile")
    require(start <= core_start < core_end <= end, f"{label} core bounds are invalid")
    require(
        str(span["span_hash"]) == sha256_text(original),
        f"{label} span hash does not match original_text",
    )


def candidate_core(candidate: Mapping[str, Any]) -> str:
    span = candidate["span"]
    relative_start = int(span["core_start_char"]) - int(span["start_char"])
    relative_end = int(span["core_end_char"]) - int(span["start_char"])
    return str(span["original_text"])[relative_start:relative_end]


def validators() -> dict[Path, Draft202012Validator]:
    paths = (
        CANDIDATE_SCHEMA,
        DETECTOR_RECEIPT_SCHEMA,
        OBSERVATION_SCHEMA,
        RECORD_SCHEMA,
        RECEIPT_SCHEMA,
        ADMISSION_RECEIPT_SCHEMA,
        OPERATOR_PACKET_SCHEMA,
    )
    schemas = {path: read_json(path) for path in paths}
    registry = Registry()
    for schema in schemas.values():
        Draft202012Validator.check_schema(schema)
        registry = registry.with_resource(str(schema["$id"]), Resource.from_contents(schema))
    return {
        path: Draft202012Validator(
            schema,
            registry=registry,
            format_checker=FormatChecker(),
        )
        for path, schema in schemas.items()
    }


@dataclass
class AtomicJsonl:
    output: Path
    handle: TextIO
    temporary: Path
    digest: Any
    records: int = 0
    bytes_written: int = 0

    @classmethod
    def open(cls, output: Path) -> AtomicJsonl:
        output.parent.mkdir(parents=True, exist_ok=True)
        handle = tempfile.NamedTemporaryFile(  # noqa: SIM115
            mode="w",
            encoding="utf-8",
            newline="",
            dir=output.parent,
            prefix=output.name,
            suffix=".tmp.jsonl",
            delete=False,
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
        return {
            "bytes": self.bytes_written,
            "records": self.records,
            "sha256": self.digest.hexdigest(),
        }

    def abort(self) -> None:
        if not self.handle.closed:
            self.handle.close()
        self.temporary.unlink(missing_ok=True)


def stage_json(path: Path, value: Mapping[str, Any]) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    handle = tempfile.NamedTemporaryFile(  # noqa: SIM115
        mode="w",
        encoding="utf-8",
        newline="\n",
        dir=path.parent,
        prefix=path.name,
        suffix=".tmp.json",
        delete=False,
    )
    temporary = Path(handle.name)
    try:
        with handle:
            handle.write(canonical_json(value) + "\n")
            handle.flush()
            os.fsync(handle.fileno())
        return temporary
    except Exception:
        temporary.unlink(missing_ok=True)
        raise


def promote_outputs(pairs: Sequence[tuple[Path, Path]]) -> None:
    backups: list[tuple[Path, Path]] = []
    promoted: list[Path] = []
    try:
        for _temporary, destination in pairs:
            if destination.exists():
                backup = destination.with_name(f".{destination.name}.backup-{sha256_text(str(destination))[:12]}")
                backup.unlink(missing_ok=True)
                os.replace(destination, backup)
                backups.append((destination, backup))
        for temporary, destination in pairs:
            os.replace(temporary, destination)
            promoted.append(destination)
    except Exception:
        for destination in promoted:
            destination.unlink(missing_ok=True)
        for destination, backup in backups:
            if backup.exists():
                os.replace(backup, destination)
        raise
    else:
        for _destination, backup in backups:
            backup.unlink(missing_ok=True)


def iter_jsonl_bytes(path: Path) -> Iterator[tuple[int, bytes, dict[str, Any]]]:
    try:
        handle: BinaryIO
        with path.open("rb") as handle:
            for line_number, raw in enumerate(handle, 1):
                if not raw.strip():
                    continue
                try:
                    value = json.loads(raw)
                except (UnicodeDecodeError, json.JSONDecodeError) as exc:
                    raise SilverError(f"invalid JSONL at {path}:{line_number}: {exc}") from exc
                if not isinstance(value, dict):
                    raise SilverError(f"expected object at {path}:{line_number}")
                yield line_number, raw, value
    except OSError as exc:
        raise SilverError(f"cannot read JSONL {path}: {exc}") from exc


def empty_artifact() -> dict[str, Any]:
    return {"bytes": 0, "records": 0, "sha256": sha256_bytes(b"")}


def observation_artifact(path: Path | None) -> dict[str, Any]:
    if path is None:
        return empty_artifact()
    return {"bytes": path.stat().st_size, "records": 0, "sha256": sha256_file(path)}


def load_observations(
    path: Path | None,
    *,
    active_validator: Draft202012Validator,
) -> tuple[dict[str, list[dict[str, Any]]], dict[str, Any], Counter[str], Counter[str]]:
    if path is None:
        return {}, empty_artifact(), Counter(), Counter()
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    by_kind: Counter[str] = Counter()
    by_source: Counter[str] = Counter()
    identities: dict[str, tuple[str, str]] = {}
    artifact = observation_artifact(path)
    for line_number, _raw, row in iter_jsonl_bytes(path):
        validate(row, active_validator, f"observation line {line_number}")
        observation_id = str(row["observation_id"])
        candidate_id = str(row["candidate_id"])
        require(observation_id not in identities, f"duplicate observation ID: {observation_id}")
        identities[observation_id] = (candidate_id, str(row["kind"]))
        if row["kind"] == "source_evidence" and row["source"] == "slovnyk_me":
            match = SLOVNYK_LOCATOR_RE.fullmatch(str(row["locator"]))
            require(match is not None, "slovnyk.me observation lacks a named-dictionary locator")
            require(
                match.group("slug").casefold() == str(row["source_identity"]).casefold(),
                "slovnyk.me source identity differs from the underlying dictionary slug",
            )
        grouped[candidate_id].append(row)
        by_kind[str(row["kind"])] += 1
        by_source[str(row.get("source") or row.get("model_family") or row.get("source_surface"))] += 1
    for candidate_id, rows in grouped.items():
        rows.sort(key=lambda item: item["observation_id"])
        for row in rows:
            if row["kind"] != "model_proposal":
                continue
            for target in row["challenge_targets"]:
                require(target in identities, f"model challenge target is absent: {target}")
                require(
                    identities[target][0] == candidate_id,
                    "model challenge crosses candidate identities",
                )
                require(target != row["observation_id"], "model proposal cannot challenge itself")
    artifact["records"] = sum(len(rows) for rows in grouped.values())
    return dict(grouped), artifact, by_kind, by_source


def normalized_alternative(value: str) -> str:
    return " ".join(unicodedata.normalize("NFC", value).split())


def normalized_token(value: str) -> str:
    return detector.normalize_form(value)


@dataclass
class AdapterCounter:
    adapter_id: str
    status: str
    source_snapshot: dict[str, Any] | None = None
    lookups: int = 0
    hits: int = 0
    misses: int = 0

    def receipt(self) -> dict[str, Any]:
        return {
            "adapter_id": self.adapter_id,
            "status": self.status,
            "source_snapshot": self.source_snapshot,
            "lookups": self.lookups,
            "hits": self.hits,
            "misses": self.misses,
        }


class CacheOnlyDictionaryAdapters:
    """Read existing ULIF/slovnyk caches without invoking any live fallback."""

    def __init__(self, database: Path):
        self.database = database
        self.connection: sqlite3.Connection | None = None
        self.ulif_rows: dict[str, dict[str, Any]] = {}
        self.slovnyk_available = False
        self.ulif = AdapterCounter(
            "sources.db:ulif_dictua_entries",
            "adapter_unavailable",
        )
        self.slovnyk = AdapterCounter(
            "sources.db:slovnyk_me_entries",
            "adapter_unavailable",
        )
        if not database.exists():
            return
        database_snapshot = {
            "bytes": database.stat().st_size,
            "records": 1,
            "sha256": sha256_file(database),
        }
        self.ulif.source_snapshot = database_snapshot
        self.slovnyk.source_snapshot = database_snapshot
        self.connection = sqlite3.connect(f"file:{database.resolve()}?mode=ro", uri=True)
        self.connection.row_factory = sqlite3.Row
        tables = {str(row[0]) for row in self.connection.execute("SELECT name FROM sqlite_master WHERE type = 'table'")}
        if "ulif_dictua_entries" in tables:
            rows = self.connection.execute(
                """
                SELECT normalized_query, canonical_headword, raw_response_ref,
                       response_sha256, parser_version, status
                FROM ulif_dictua_entries
                ORDER BY normalized_query
                """
            ).fetchall()
            self.ulif_rows = {str(row["normalized_query"]): dict(row) for row in rows}
            self.ulif.status = "bounded_cache"
        if "slovnyk_me_entries" in tables:
            required = {
                "dictionary_slug",
                "normalized_word",
                "source_url",
                "word",
                "is_dialect",
                "is_modern",
                "text",
                "snippet",
            }
            columns = {str(row[1]) for row in self.connection.execute("PRAGMA table_info(slovnyk_me_entries)")}
            if required <= columns:
                self.slovnyk_available = True
                self.slovnyk.status = "bounded_cache"

    def close(self) -> None:
        if self.connection is not None:
            self.connection.close()
            self.connection = None

    def counter_state(self) -> dict[str, tuple[int, int, int]]:
        return {
            "ulif": (self.ulif.lookups, self.ulif.hits, self.ulif.misses),
            "slovnyk": (
                self.slovnyk.lookups,
                self.slovnyk.hits,
                self.slovnyk.misses,
            ),
        }

    def restore_counter_state(self, state: Mapping[str, tuple[int, int, int]]) -> None:
        for name, counter in (("ulif", self.ulif), ("slovnyk", self.slovnyk)):
            counter.lookups, counter.hits, counter.misses = state[name]

    def _observation_id(self, candidate_id: str, source: str, identity: str, query: str) -> str:
        return "obs." + source.replace("_", "-") + "." + sha256_text("\0".join((candidate_id, source, identity, query)))

    def _core_tokens(self, candidate: Mapping[str, Any]) -> list[str]:
        span = candidate["span"]
        relative_start = int(span["core_start_char"]) - int(span["start_char"])
        relative_end = int(span["core_end_char"]) - int(span["start_char"])
        core = str(span["original_text"])[relative_start:relative_end]
        return sorted({token.normalized for token in detector.tokenize_with_offsets(core)})

    def observations(self, candidate_id: str, candidate: Mapping[str, Any]) -> list[dict[str, Any]]:
        result: list[dict[str, Any]] = []
        for token in self._core_tokens(candidate):
            self.ulif.lookups += 1
            ulif = self.ulif_rows.get(token)
            if ulif is None:
                self.ulif.misses += 1
            else:
                self.ulif.hits += 1
                status = {
                    "ok": "attested",
                    "not_found": "not_found",
                    "parse_error": "parse_error",
                }.get(str(ulif["status"]), "incomplete")
                headword = normalized_alternative(str(ulif["canonical_headword"] or token))
                alternatives = (
                    [{"text": headword, "transformation_path": ["ulif_dictua:canonical_headword"]}]
                    if status == "attested"
                    else []
                )
                result.append(
                    {
                        "schema_version": "language_contact_silver_observation_v1",
                        "observation_id": self._observation_id(candidate_id, "ulif", "ulif_dictua", token),
                        "candidate_id": candidate_id,
                        "kind": "source_evidence",
                        "source": "ulif_dictua",
                        "source_identity": "ulif_dictua",
                        "query": token,
                        "status": status,
                        "supports": "ukrainian_attestation" if status == "attested" else "no_conclusion",
                        "locator": "https://lcorp.ulif.org.ua/dictua/",
                        "parser_status": str(ulif["status"]),
                        "parser_version": str(ulif["parser_version"] or "unknown"),
                        "content_sha256": str(ulif["response_sha256"]),
                        "rights_posture": "bounded_internal_reference",
                        "raw_payload_export_allowed": False,
                        "alternatives": alternatives,
                    }
                )
            if not self.slovnyk_available or self.connection is None:
                continue
            self.slovnyk.lookups += 1
            rows = self.connection.execute(
                """
                SELECT dictionary_slug, normalized_word, source_url, word,
                       is_dialect, is_modern, text, snippet
                FROM slovnyk_me_entries
                WHERE normalized_word = ?
                ORDER BY dictionary_slug, source_url
                """,
                (token,),
            ).fetchall()
            if not rows:
                self.slovnyk.misses += 1
                continue
            self.slovnyk.hits += 1
            for row in rows:
                identity = str(row["dictionary_slug"])
                locator = str(row["source_url"])
                match = SLOVNYK_LOCATOR_RE.fullmatch(locator)
                if match is None or match.group("slug").casefold() != identity.casefold():
                    continue
                content = str(row["text"] or row["snippet"] or "")
                supports = "protected_variation" if bool(row["is_dialect"]) else "ukrainian_attestation"
                word = normalized_alternative(str(row["word"] or token))
                result.append(
                    {
                        "schema_version": "language_contact_silver_observation_v1",
                        "observation_id": self._observation_id(candidate_id, "slovnyk", identity, token),
                        "candidate_id": candidate_id,
                        "kind": "source_evidence",
                        "source": "slovnyk_me",
                        "source_identity": identity,
                        "query": token,
                        "status": "attested",
                        "supports": supports,
                        "locator": locator,
                        "parser_status": "ok",
                        "parser_version": "slovnyk-me-cache-v1",
                        "content_sha256": sha256_text(content),
                        "rights_posture": "bounded_internal_reference",
                        "raw_payload_export_allowed": False,
                        "alternatives": [{"text": word, "transformation_path": [f"slovnyk_me:{identity}:headword"]}],
                    }
                )
        return sorted(result, key=lambda item: item["observation_id"])


class GenreResolver:
    def __init__(self, config: Mapping[str, Any], input_root: Path):
        self.constants: dict[str, str] = {}
        self.dynamic: dict[str, dict[str, str]] = {}
        for source in config["sources"]:
            family = str(source["source_family"])
            adapter = source["adapter"]
            spec = adapter["dimensions"]["genre"]
            if "constant" in spec:
                self.constants[family] = str(spec["constant"])
                continue
            database = input_root / str(adapter["database"])
            require(database.exists(), f"genre source database unavailable: {database}")
            table = str(adapter["table"])
            id_column = str(adapter["id_column"])
            genre_column = str(spec["column"])
            require(table == "literary_texts", f"unsupported dynamic genre table: {table}")
            connection = sqlite3.connect(f"file:{database.resolve()}?mode=ro", uri=True)
            try:
                rows = connection.execute(f'SELECT "{id_column}", "{genre_column}" FROM "{table}"').fetchall()
            finally:
                connection.close()
            self.dynamic[family] = {str(record_id): str(genre or "unknown") for record_id, genre in rows}

    def genre(self, candidate: Mapping[str, Any]) -> str:
        family = str(candidate["source_family"])
        if family in self.constants:
            return self.constants[family]
        return self.dynamic.get(family, {}).get(str(candidate["record_id"]), "unknown")


def family_admission(
    receipt: Mapping[str, Any],
    operator_packet: Mapping[str, Any],
    *,
    receipt_path: Path,
    operator_packet_path: Path,
) -> tuple[dict[str, str], dict[str, str | None], str, str]:
    receipt_sha = sha256_file(receipt_path)
    packet_sha = sha256_file(operator_packet_path)
    require(
        receipt["operator_decision"]["packet_sha256"] == packet_sha,
        "admission receipt and operator packet hashes disagree",
    )
    packet_families = {str(item["source_family"]): item for item in operator_packet["families"]}
    require(
        len(packet_families) == len(operator_packet["families"]),
        "duplicate source family in operator packet",
    )
    dispositions: dict[str, str] = {}
    destinations: dict[str, str | None] = {}
    for family in receipt["families"]:
        name = str(family["source_family"])
        require(name in packet_families, f"operator packet lacks source family: {name}")
        nonzero = [disposition for disposition, counts in family["dispositions"].items() if int(counts["rows"]) > 0]
        require(len(nonzero) == 1, f"ambiguous family admission disposition: {name}")
        dispositions[name] = nonzero[0]
        require(
            packet_families[name]["current_disposition"] == nonzero[0],
            f"operator packet disposition mismatch: {name}",
        )
        destinations[name] = packet_families[name]["proposed_destination"]
    return dispositions, destinations, receipt_sha, packet_sha


def _signal(
    family: str,
    identity: str,
    supports: str,
    status: str = "attested",
) -> dict[str, str]:
    return {
        "family": family,
        "identity": identity,
        "supports": supports,
        "status": status,
    }


def detector_signals(candidate: Mapping[str, Any]) -> list[dict[str, str]]:
    evidence = candidate["evidence"]
    result = [
        _signal(
            "source_context",
            str(candidate["span"]["span_hash"]),
            "context_only",
        )
    ]
    period = str(candidate["metadata"]["period"]).casefold()
    register = str(candidate["metadata"]["register"]).casefold()
    if period in PROTECTED_PERIODS or any(fragment in register for fragment in PROTECTED_REGISTER_FRAGMENTS):
        result.append(
            _signal(
                "source_metadata",
                f"{candidate['metadata']['period']}:{candidate['metadata']['register']}",
                "protected_variation",
            )
        )
    role = str(candidate["classification"]["discourse_role"])
    if role not in {"narration", "unknown"}:
        result.append(_signal("discourse_structure", role, "quoted_or_multilingual"))
    for item in evidence["vesum"].get("tokens", []):
        attested = bool(item.get("analyses"))
        result.append(
            _signal(
                "vesum",
                str(item["surface"]),
                "ukrainian_attestation" if attested else "no_conclusion",
                "attested" if attested else "not_found",
            )
        )
    for item in evidence["russian_morphology"].get("tokens", []):
        confidence = float(item.get("confidence", 0.0))
        result.append(
            _signal(
                "russian_morphology",
                f"{item.get('token', '')}:{item.get('lemma', '')}:{confidence:.6f}",
                "russian_attestation" if confidence >= 0.7 else "no_conclusion",
                "attested" if confidence >= 0.7 else "ambiguous",
            )
        )
    for item in evidence["r2u"].get("lookups", []):
        hit = item.get("status") == "hit"
        result.append(
            _signal(
                "r2u",
                str(item.get("response_sha256") or item.get("query") or "cache-miss"),
                "alternative_candidate" if hit else "no_conclusion",
                "attested" if hit else "incomplete",
            )
        )
    for lookup in evidence["heritage"].get("lookups", []):
        for item in lookup.get("hits", []):
            result.append(
                _signal(
                    "heritage_dictionary",
                    f"{item['dictionary_identity']}:{item['matched_headword']}",
                    "protected_variation",
                )
            )
    for item in evidence.get("valid_word_routes", []):
        result.append(
            _signal(
                "vetted_route",
                f"{item['route_type']}:{item['evidence_key']}",
                "alternative_candidate",
            )
        )
    for item in evidence.get("reconstruction_candidates", []):
        if item.get("validated") is True:
            result.append(
                _signal(
                    "reconstruction",
                    f"{item['original_surface']}->{item['reconstructed_surface']}",
                    "russian_attestation",
                )
            )
    category = str(candidate["classification"]["category"])
    if category == "ocr_or_encoding_candidate":
        result.append(_signal("source_context", "detector:ocr", "technical_or_ocr"))
    if category == "proper_name":
        result.append(_signal("source_context", "detector:proper-name", "proper_name"))
    unique = {canonical_json(item): item for item in result}
    return [unique[key] for key in sorted(unique)]


def observation_signals(observations: Sequence[Mapping[str, Any]]) -> list[dict[str, str]]:
    result: list[dict[str, str]] = []
    for item in observations:
        kind = str(item["kind"])
        if kind == "source_evidence":
            family = str(item["source"])
            result.append(
                _signal(
                    family,
                    f"{item['source_identity']}:{item['observation_id']}",
                    str(item["supports"]),
                    str(item["status"]),
                )
            )
        elif kind == "model_proposal":
            result.append(
                _signal(
                    "model_proposal",
                    f"{item['model_family']}:{item['model']}:{item['harness']}:{item['observation_id']}",
                    "no_conclusion",
                )
            )
        else:
            result.append(
                _signal(
                    "hramatka_feedback",
                    str(item["observation_id"]),
                    "no_conclusion",
                )
            )
    unique = {canonical_json(item): item for item in result}
    return [unique[key] for key in sorted(unique)]


def supported_alternatives(
    observations: Sequence[Mapping[str, Any]],
) -> list[dict[str, Any]]:
    grouped: dict[str, dict[str, Any]] = {}
    for observation in observations:
        for alternative in observation.get("alternatives", []):
            text = normalized_alternative(str(alternative["text"]))
            key = unicodedata.normalize("NFC", text)
            row = grouped.setdefault(
                key,
                {
                    "text": text,
                    "supporting_observation_ids": set(),
                    "transformation_paths": set(),
                },
            )
            row["supporting_observation_ids"].add(str(observation["observation_id"]))
            row["transformation_paths"].add(tuple(str(value) for value in alternative["transformation_path"]))
    return [
        {
            "text": row["text"],
            "supporting_observation_ids": sorted(row["supporting_observation_ids"]),
            "transformation_paths": [list(path) for path in sorted(row["transformation_paths"])],
        }
        for _key, row in sorted(grouped.items())
    ]


def _has_attested(signals: Sequence[Mapping[str, Any]], family: str) -> bool:
    return any(item["family"] == family and item["status"] == "attested" for item in signals)


def _authoritative_support_count(
    alternative: Mapping[str, Any],
    observations_by_id: Mapping[str, Mapping[str, Any]],
) -> int:
    identities: set[tuple[str, str]] = set()
    for observation_id in alternative["supporting_observation_ids"]:
        observation = observations_by_id[observation_id]
        if (
            observation["kind"] == "source_evidence"
            and observation["source"] in AUTHORITATIVE_ALTERNATIVE_SOURCES
            and observation["status"] == "attested"
            and observation["supports"] in {"alternative_candidate", "ukrainian_attestation"}
        ):
            identities.add((str(observation["source"]), str(observation["source_identity"])))
    return len(identities)


def decide(
    candidate: Mapping[str, Any],
    observations: Sequence[Mapping[str, Any]],
) -> tuple[str, str, list[dict[str, Any]], list[dict[str, str]], list[str]]:
    signals = [*detector_signals(candidate), *observation_signals(observations)]
    unique = {canonical_json(item): item for item in signals}
    signals = [unique[key] for key in sorted(unique)]
    alternatives = supported_alternatives(observations)
    observations_by_id = {str(item["observation_id"]): item for item in observations}
    category = str(candidate["classification"]["category"])
    role = str(candidate["classification"]["discourse_role"])
    period = str(candidate["metadata"]["period"]).casefold()
    register = str(candidate["metadata"]["register"]).casefold()
    protected_metadata = period in PROTECTED_PERIODS or any(
        fragment in register for fragment in PROTECTED_REGISTER_FRAGMENTS
    )
    uncertainty = ["non-human evidence; not qualified Ukrainian adjudication"]

    if category == "protected_authentic_ukrainian":
        protective_sources = {
            family
            for family in (
                "heritage_dictionary",
                "vesum",
                "ulif_dictua",
                "slovnyk_me",
            )
            if _has_attested(signals, family)
        }
        if len(protective_sources) >= 2 or (protected_metadata and protective_sources):
            return "protected", "protected_variation", alternatives, signals, uncertainty
        uncertainty.append("protected detector route lacks a second independent attestation")
        return "unresolved", "protected_variation", alternatives, signals, uncertainty

    if category == "historical_unresolved":
        if protected_metadata and any(
            _has_attested(signals, family)
            for family in (
                "heritage_dictionary",
                "vesum",
                "ulif_dictua",
                "slovnyk_me",
            )
        ):
            return "protected", "historical_or_register", alternatives, signals, uncertainty
        uncertainty.append("historical/register metadata lacks independent lexical attestation")
        return "unresolved", "historical_or_register", alternatives, signals, uncertainty

    if category in {"russian_quotation", "other_language"}:
        if role not in {"narration", "unknown"} and (
            _has_attested(signals, "russian_morphology")
            or _has_attested(signals, "r2u")
            or category == "other_language"
        ):
            return "protected", "quoted_or_multilingual", alternatives, signals, uncertainty
        uncertainty.append("language span lacks structural and lexical corroboration")
        return "unresolved", "quoted_or_multilingual", alternatives, signals, uncertainty

    if category == "ocr_or_encoding_candidate":
        uncertainty.append("technical/OCR evidence is not a linguistic correction")
        return "unresolved", "technical_or_ocr", alternatives, signals, uncertainty

    if category == "proper_name":
        uncertainty.append("proper names cannot be normalized from morphology alone")
        return "unresolved", "proper_name", alternatives, signals, uncertainty

    if category == "valid_word_contact_candidate":
        uncertainty.append("lexical attestation cannot establish contextual sense for a valid-word contact candidate")
        return "unresolved", "unresolved", alternatives, signals, uncertainty

    if category in CORRECTION_CATEGORIES:
        safe_context = role == "narration" and period == "modern" and not protected_metadata
        base_corroboration = _has_attested(signals, "russian_morphology") and _has_attested(signals, "r2u")
        ranked = [
            (alternative, _authoritative_support_count(alternative, observations_by_id)) for alternative in alternatives
        ]
        maximum_support = max((count for _alternative, count in ranked), default=0)
        if safe_context and base_corroboration and maximum_support >= 1:
            grade = (
                "independently_triangulated_silver" if maximum_support >= 2 else "deterministic_source_backed_silver"
            )
            uncertainty.append("source-backed silver alternatives remain non-authoritative")
            return grade, "correction", alternatives, signals, uncertainty
        if any(item["kind"] == "model_proposal" for item in observations):
            uncertainty.append("model proposals lack independent source-backed promotion evidence")
            return "model_only_research", "unresolved", alternatives, signals, uncertainty
        uncertainty.append("correction evidence is incomplete; no automatic correction promoted")
        return "unresolved", "unresolved", alternatives, signals, uncertainty

    if any(item["kind"] == "model_proposal" for item in observations):
        uncertainty.append("model-only proposal is research evidence, not authority")
        return "model_only_research", "unresolved", alternatives, signals, uncertainty
    uncertainty.append("available evidence does not support a safe disposition")
    return "unresolved", "unresolved", alternatives, signals, uncertainty


def destination_views(grade: str, disposition: str) -> dict[str, str]:
    if disposition in {"protected_variation", "historical_or_register"}:
        modern = correction = preference = "protected"
    elif disposition == "quoted_or_multilingual":
        modern, correction, preference = "mask_span_from_loss", "not_applicable", "not_applicable"
    elif disposition == "correction" and grade in {
        "deterministic_source_backed_silver",
        "independently_triangulated_silver",
    }:
        modern, correction, preference = "unresolved", "silver_candidate", "silver_candidate"
    elif disposition == "acceptable_as_is":
        modern, correction, preference = "retain_original", "not_applicable", "not_applicable"
    else:
        modern = correction = preference = "unresolved"
    return {
        "faithful_literary": "retain_original",
        "modern_literary_ukrainian": modern,
        "correction": correction,
        "preference": preference,
    }


def observation_matches_evaluation(
    observation: Mapping[str, Any],
    registry: model_view_exporter.EvaluationExclusionRegistry,
) -> model_view_exporter.ExclusionMatch:
    values = [str(observation["query"])] if observation["kind"] == "source_evidence" else []
    values.extend(str(item["text"]) for item in observation.get("alternatives", []))
    for value in values:
        match = registry.match(value)
        if match.matched:
            return match
    return model_view_exporter.ExclusionMatch(False)


def registry_sha256(
    registry: model_view_exporter.EvaluationExclusionRegistry,
) -> str:
    return sha256_text(canonical_json(model_view_exporter.registry_receipt(registry)))


def build_record(
    candidate: Mapping[str, Any],
    *,
    observations: Sequence[Mapping[str, Any]],
    detector_receipt_sha256: str,
    genre: str,
    admission_disposition: str,
    admitted_destination: str | None,
    admission_receipt_sha256: str,
    operator_packet_sha256: str,
    evaluation_registry_sha256: str,
) -> dict[str, Any]:
    candidate_sha = sha256_text(canonical_json(candidate))
    candidate_id = f"lcc.{candidate_sha}"
    grade, disposition, alternatives, signals, uncertainty = decide(candidate, observations)
    if admission_disposition != "admitted" or admitted_destination is None:
        uncertainty = [*uncertainty, "source family is not admitted for any model destination"]
    elif "correction" not in admitted_destination:
        uncertainty = [*uncertainty, "source admission does not authorize the silver-correction destination"]
    decision = {
        "evidence_grade": grade,
        "disposition": disposition,
        "signals": signals,
        "alternatives": alternatives,
        "uncertainty": sorted(set(uncertainty)),
    }
    identity_projection = {
        "candidate_sha256": candidate_sha,
        "decision": decision,
        "observation_sha256": [sha256_text(canonical_json(item)) for item in observations],
        "policy_version": POLICY_VERSION,
    }
    return {
        "schema_version": SCHEMA_VERSION,
        "record_id": f"silver.{sha256_text(canonical_json(identity_projection))}",
        "candidate_id": candidate_id,
        "candidate_sha256": candidate_sha,
        "detector_receipt_sha256": detector_receipt_sha256,
        "policy_version": POLICY_VERSION,
        "detector_candidate": candidate,
        "observations": list(observations),
        "source_enrichment": {
            "genre": genre,
            "region": "unknown",
            "admission_disposition": admission_disposition,
            "admitted_destination": admitted_destination,
            "admission_receipt_sha256": admission_receipt_sha256,
            "operator_packet_sha256": operator_packet_sha256,
            "silver_use": "investigation_only",
            "correction_training_eligible": False,
            "redistribution_eligible": False,
        },
        "decision": decision,
        "destination_views": destination_views(grade, disposition),
        "evaluation_firewall": {
            "status": "clear",
            "algorithm_version": "foundry-eval-exclusion-v1",
            "registry_sha256": evaluation_registry_sha256,
        },
        "claim_boundary": {
            "human_reviewed": False,
            "qualified_human_gold": False,
            "headline_gold": False,
            "native_acceptance": False,
            "reviewer_reliability_counted": False,
            "model_training_or_export_eligible": False,
        },
        "human_upgrade": {
            "compatible_candidate_id": candidate_id,
            "target_contract": "correction_reviewer_decision_v1",
            "performed": False,
        },
    }


def _adapter_receipt(
    counters: Mapping[str, Counter[str]],
    cache_adapters: CacheOnlyDictionaryAdapters,
) -> dict[str, Any]:
    def candidate_adapter(name: str, adapter_id: str) -> dict[str, Any]:
        values = counters[name]
        return {
            "adapter_id": adapter_id,
            "status": "available",
            "source_snapshot": None,
            "lookups": values["lookups"],
            "hits": values["hits"],
            "misses": values["misses"],
        }

    return {
        "vesum": candidate_adapter("vesum", "detector:vesum-pinned"),
        "russian_morphology": candidate_adapter("russian_morphology", "detector:check_ru_morph-pinned"),
        "r2u": candidate_adapter("r2u", "detector:r2u-bounded-hash-cache"),
        "heritage": candidate_adapter("heritage", "detector:heritage-local-dictionaries"),
        "ukrainian_corpus": candidate_adapter("ukrainian_corpus", "detector:bounded-source-context"),
        "ulif_dictua": cache_adapters.ulif.receipt(),
        "slovnyk_me": cache_adapters.slovnyk.receipt(),
        "network": {"performed": False, "prohibited": True},
    }


def update_candidate_adapter_counts(
    candidate: Mapping[str, Any],
    counters: Mapping[str, Counter[str]],
) -> None:
    evidence = candidate["evidence"]
    for name, field in (
        ("vesum", "tokens"),
        ("russian_morphology", "tokens"),
        ("r2u", "lookups"),
        ("heritage", "lookups"),
    ):
        rows = list(evidence[name].get(field, []))
        counters[name]["lookups"] += len(rows)
        for row in rows:
            if name == "vesum":
                hit = bool(row.get("analyses"))
            elif name == "russian_morphology":
                hit = float(row.get("confidence", 0.0)) >= 0.7
            elif name == "r2u":
                hit = row.get("status") == "hit"
            else:
                hit = bool(row.get("hits"))
            counters[name]["hits" if hit else "misses"] += 1
    counters["ukrainian_corpus"]["lookups"] += 1
    counters["ukrainian_corpus"]["hits"] += 1


@dataclass(frozen=True)
class SilverRun:
    receipt: dict[str, Any]
    output_path: Path
    receipt_path: Path


def build_silver(
    *,
    candidates_path: Path,
    detector_receipt_path: Path,
    detector_config_path: Path,
    admission_receipt_path: Path,
    operator_packet_path: Path,
    input_root: Path,
    observations_path: Path | None,
    output_path: Path,
    receipt_path: Path,
    v011_manifest_path: Path = DEFAULT_V011_MANIFEST,
    v02_packet_path: Path = DEFAULT_V02_PACKET,
) -> SilverRun:
    active_validators = validators()
    detector_receipt = read_json(detector_receipt_path)
    validate(
        detector_receipt,
        active_validators[DETECTOR_RECEIPT_SCHEMA],
        "detector receipt",
    )
    admission_receipt = read_json(admission_receipt_path)
    validate(
        admission_receipt,
        active_validators[ADMISSION_RECEIPT_SCHEMA],
        "admission receipt",
    )
    operator_packet = read_json(operator_packet_path)
    validate(
        operator_packet,
        active_validators[OPERATOR_PACKET_SCHEMA],
        "operator packet",
    )
    dispositions, destinations, admission_sha, operator_sha = family_admission(
        admission_receipt,
        operator_packet,
        receipt_path=admission_receipt_path,
        operator_packet_path=operator_packet_path,
    )
    detector_receipt_sha = sha256_file(detector_receipt_path)
    detector_config_sha = sha256_file(detector_config_path)
    detector_config = read_json(detector_config_path)
    genre_resolver = GenreResolver(detector_config, input_root)
    observation_groups, observation_input, _supplied_kinds, _supplied_sources = load_observations(
        observations_path,
        active_validator=active_validators[OBSERVATION_SCHEMA],
    )
    evaluation_registry = model_view_exporter.build_exclusion_registry(
        v011_manifest=v011_manifest_path,
        v02_packet=v02_packet_path,
    )
    evaluation_registry_sha = registry_sha256(evaluation_registry)
    cache_adapters = CacheOnlyDictionaryAdapters(input_root / "data/sources.db")
    writer = AtomicJsonl.open(output_path)
    input_digest = hashlib.sha256()
    input_bytes = 0
    input_records = 0
    evaluation_matches: Counter[str] = Counter()
    emitted_observation_kinds: Counter[str] = Counter()
    emitted_observation_sources: Counter[str] = Counter()
    counts = {
        name: Counter()
        for name in (
            "evidence_grade",
            "disposition",
            "source_family",
            "period",
            "genre",
            "register",
            "category",
            "protected_or_uncertain_route",
        )
    }
    adapter_counts: dict[str, Counter[str]] = {
        name: Counter()
        for name in (
            "vesum",
            "russian_morphology",
            "r2u",
            "heritage",
            "ukrainian_corpus",
        )
    }
    seen_candidates: set[str] = set()
    output_artifact: dict[str, Any] | None = None
    receipt_temporary: Path | None = None
    try:
        for line_number, raw, candidate in iter_jsonl_bytes(candidates_path):
            input_digest.update(raw)
            input_bytes += len(raw)
            input_records += 1
            validate(
                candidate,
                active_validators[CANDIDATE_SCHEMA],
                f"detector candidate line {line_number}",
            )
            validate_candidate_integrity(
                candidate,
                f"detector candidate line {line_number}",
            )
            candidate_sha = sha256_text(canonical_json(candidate))
            candidate_id = f"lcc.{candidate_sha}"
            require(candidate_id not in seen_candidates, f"duplicate detector candidate: {candidate_id}")
            seen_candidates.add(candidate_id)
            supplied = observation_groups.get(candidate_id, [])

            # Evaluation candidates must not reach dictionary/cache adapters.  Check
            # their detector text and any externally supplied evidence first.
            match = evaluation_registry.match(str(candidate["span"]["original_text"]))
            if not match.matched:
                match = evaluation_registry.match(candidate_core(candidate))
            if not match.matched:
                for item in supplied:
                    match = observation_matches_evaluation(item, evaluation_registry)
                    if match.matched:
                        break
            if match.matched:
                evaluation_matches[str(match.method or "unknown")] += 1
                continue

            adapter_counter_state = cache_adapters.counter_state()
            generated = cache_adapters.observations(candidate_id, candidate)
            observations = sorted([*supplied, *generated], key=lambda item: item["observation_id"])
            observation_ids = [str(item["observation_id"]) for item in observations]
            require(len(observation_ids) == len(set(observation_ids)), f"duplicate observation for {candidate_id}")
            for item in generated:
                validate(item, active_validators[OBSERVATION_SCHEMA], "generated observation")

            for item in generated:
                match = observation_matches_evaluation(item, evaluation_registry)
                if match.matched:
                    break
            if match.matched:
                cache_adapters.restore_counter_state(adapter_counter_state)
                evaluation_matches[str(match.method or "unknown")] += 1
                continue

            for item in observations:
                emitted_observation_kinds[str(item["kind"])] += 1
                emitted_observation_sources[
                    str(item.get("source") or item.get("model_family") or item.get("source_surface"))
                ] += 1

            family = str(candidate["source_family"])
            require(family in dispositions, f"source family is absent from admission receipt: {family}")
            genre = genre_resolver.genre(candidate)
            update_candidate_adapter_counts(candidate, adapter_counts)
            record = build_record(
                candidate,
                observations=observations,
                detector_receipt_sha256=detector_receipt_sha,
                genre=genre,
                admission_disposition=dispositions[family],
                admitted_destination=destinations[family],
                admission_receipt_sha256=admission_sha,
                operator_packet_sha256=operator_sha,
                evaluation_registry_sha256=evaluation_registry_sha,
            )
            validate(record, active_validators[RECORD_SCHEMA], "silver record")
            writer.write(record)
            decision = record["decision"]
            counts["evidence_grade"][decision["evidence_grade"]] += 1
            counts["disposition"][decision["disposition"]] += 1
            counts["source_family"][family] += 1
            counts["period"][str(candidate["metadata"]["period"])] += 1
            counts["genre"][genre] += 1
            counts["register"][str(candidate["metadata"]["register"])] += 1
            counts["category"][str(candidate["classification"]["category"])] += 1
            if decision["evidence_grade"] in {"protected", "unresolved", "model_only_research"}:
                counts["protected_or_uncertain_route"][str(candidate["queue_route"])] += 1

        expected = detector_receipt["outputs"]["review_candidates"]
        actual_input = {
            "bytes": input_bytes,
            "records": input_records,
            "sha256": input_digest.hexdigest(),
        }
        require(actual_input == expected, "detector candidate artifact does not match its receipt")
        orphaned = sorted(set(observation_groups) - seen_candidates)
        require(not orphaned, f"observations reference absent candidates: {orphaned[:3]}")
        output_artifact = writer.finish()
        require(
            input_records == output_artifact["records"] + sum(evaluation_matches.values()),
            "candidate arithmetic does not reconcile",
        )
        evaluation_receipt = model_view_exporter.registry_receipt(evaluation_registry)
        receipt = {
            "schema_version": RECEIPT_VERSION,
            "policy_version": POLICY_VERSION,
            "detector_input": actual_input,
            "detector_receipt_sha256": detector_receipt_sha,
            "detector_config_sha256": detector_config_sha,
            "implementation": {
                "producer_logical_path": "scripts/projects/open_model_data/silver_evidence_factory.py",
                "producer_sha256": sha256_file(Path(__file__)),
                "contract_sha256": {
                    "observation": sha256_file(OBSERVATION_SCHEMA),
                    "record": sha256_file(RECORD_SCHEMA),
                    "receipt": sha256_file(RECEIPT_SCHEMA),
                },
            },
            "observation_input": observation_input,
            "output": output_artifact,
            "candidate_arithmetic": {
                "input_candidates": input_records,
                "output_records": output_artifact["records"],
                "evaluation_excluded": sum(evaluation_matches.values()),
            },
            "counts": {
                "by_evidence_grade": dict(sorted(counts["evidence_grade"].items())),
                "by_disposition": dict(sorted(counts["disposition"].items())),
                "by_source_family": dict(sorted(counts["source_family"].items())),
                "by_period": dict(sorted(counts["period"].items())),
                "by_genre": dict(sorted(counts["genre"].items())),
                "by_register": dict(sorted(counts["register"].items())),
                "by_category": dict(sorted(counts["category"].items())),
                "by_protected_or_uncertain_route": dict(sorted(counts["protected_or_uncertain_route"].items())),
                "observations_by_kind": dict(sorted(emitted_observation_kinds.items())),
                "observations_by_source": dict(sorted(emitted_observation_sources.items())),
            },
            "evaluation_exclusion": {
                "algorithm_version": "foundry-eval-exclusion-v1",
                "registry_sha256": evaluation_registry_sha,
                "artifacts": evaluation_receipt["artifacts"],
                "matches_by_method": dict(sorted(evaluation_matches.items())),
            },
            "source_admission": {
                "receipt_sha256": admission_sha,
                "operator_packet_sha256": operator_sha,
                "family_dispositions": dict(sorted(dispositions.items())),
                "family_destinations": dict(sorted(destinations.items())),
            },
            "evidence_adapters": _adapter_receipt(adapter_counts, cache_adapters),
            "hramatka": {
                "state": (
                    "bounded_feedback_ingested" if emitted_observation_kinds["hramatka_feedback"] else "empty_valid"
                ),
                "observations": emitted_observation_kinds["hramatka_feedback"],
                "blocking": False,
            },
            "claims": {
                "human_gold_created": False,
                "human_review_claimed": False,
                "precision_or_recall_claimed": False,
                "training_performed": False,
                "export_admission_created": False,
                "publication_performed": False,
            },
            "determinism": {
                "serialization": "UTF-8 canonical JSON with sorted keys and LF",
                "ordering": "detector input order; observations sorted by observation_id",
                "timestamps_omitted": True,
                "runtime_observations_omitted": True,
            },
        }
        validate(receipt, active_validators[RECEIPT_SCHEMA], "silver receipt")
        receipt_temporary = stage_json(receipt_path, receipt)
        promote_outputs(
            [
                (writer.temporary, output_path),
                (receipt_temporary, receipt_path),
            ]
        )
        return SilverRun(receipt, output_path, receipt_path)
    except Exception:
        writer.abort()
        if receipt_temporary is not None:
            receipt_temporary.unlink(missing_ok=True)
        raise
    finally:
        cache_adapters.close()


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--candidates", type=Path, required=True)
    parser.add_argument("--detector-receipt", type=Path, required=True)
    parser.add_argument("--detector-config", type=Path, default=DEFAULT_DETECTOR_CONFIG)
    parser.add_argument("--admission-receipt", type=Path, default=DEFAULT_ADMISSION_RECEIPT)
    parser.add_argument("--operator-packet", type=Path, default=DEFAULT_OPERATOR_PACKET)
    parser.add_argument("--input-root", type=Path, default=ROOT)
    parser.add_argument("--observations", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--receipt-output", type=Path, required=True)
    parser.add_argument("--v0-1-1-manifest", type=Path, default=DEFAULT_V011_MANIFEST)
    parser.add_argument("--v0-2-packet", type=Path, default=DEFAULT_V02_PACKET)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        run = build_silver(
            candidates_path=args.candidates,
            detector_receipt_path=args.detector_receipt,
            detector_config_path=args.detector_config,
            admission_receipt_path=args.admission_receipt,
            operator_packet_path=args.operator_packet,
            input_root=args.input_root,
            observations_path=args.observations,
            output_path=args.output,
            receipt_path=args.receipt_output,
            v011_manifest_path=args.v0_1_1_manifest,
            v02_packet_path=args.v0_2_packet,
        )
    except (OSError, SilverError, sqlite3.Error) as exc:
        print(f"silver-evidence-factory: {exc}", file=sys.stderr)
        return 2
    print(canonical_json(run.receipt))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
