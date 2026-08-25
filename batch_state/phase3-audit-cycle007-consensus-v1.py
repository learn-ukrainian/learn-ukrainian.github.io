#!/usr/bin/env python3
"""Deterministic consensus audit and source-authority review for Cycle 007."""

from __future__ import annotations

import argparse
import contextlib
import hashlib
import json
import os
import shutil
import stat
import subprocess
import tempfile
from collections import defaultdict
from collections.abc import Mapping
from pathlib import Path
from typing import Any

from scripts.projects.open_model_data import phase3_cycle007_evidence_contract as contract
from scripts.projects.open_model_data import phase3_cycle007_evidence_validator as validator

ROOT = Path(__file__).resolve().parents[1]
CYCLE = "phase3-v2-1-evaluation-cycle-007"
EVALUATION_CYCLE_ID = CYCLE
AMENDMENT_SHA256 = "4f2e3e58964cae391c3933ffdce531296a0744808b0154231ca513049602fea0"
CYCLE007_AMENDMENT_SHA256 = AMENDMENT_SHA256
SOURCE_CUSTODY_SHA256 = "7047e8459433376f3b690cfc2f15e115d77a701e79afb0ef2db184b44ea14726"
CUSTODY_SHA256 = SOURCE_CUSTODY_SHA256
SOURCE_MANIFEST_SHA256 = "b8d290ffe945a6cc5d36345cbf234ccf79a7df98cb4199ffad0b778cd2b69fab"
MANIFEST_SHA256 = SOURCE_MANIFEST_SHA256
ORDERED_IDENTITY_COMMITMENT_SHA256 = "331fd7fbc42e43cb3c218d9c2b790df060c0a553ab7c3a7b3b557f9f2bc3c419"

LANES = {"clean_label": 40, "residual_label": 164}
OUTPUT = "consensus-audit-cycle007-v1"
COMPARE_OUTPUT = "dual-label-output-cycle007-v1"
MODEL = "Claude Sonnet 4.6 (Thinking)"
FAMILY = "anthropic"
HARNESS = "agy"
MAX_STRUCTURAL_ATTEMPTS = 2
MAX_REVIEW_BATCH_TARGETS = 50

FAILURE_CODES = frozenset(
    {
        "audit_population_drift",
        "sample_size_drift",
        "stratum_selection_drift",
        "rank_calculation_drift",
        "seed_calculation_drift",
        "unsupported_acceptance_finding",
        "incorrect_positive_finding",
        "russianism_accepted_finding",
        "surzhyk_accepted_finding",
        "foreign_or_insufficient_evidence_finding",
        "terminal_audit_finding",
        "incomplete_risk_review",
        "review_missing",
        "review_identity_drift",
        "review_result_drift",
        "reviewer_binding_drift",
        "provider_transport_failure",
        "stream_json_invalid",
        "terminal_result_count_drift",
        "structured_output_envelope_drift",
        "binding_failure",
        "mode_drift",
    }
)


class Error(ValueError):
    def __init__(self, code: str):
        self.code = code if code in FAILURE_CODES else "terminal_audit_finding"
        self.failure_code = self.code
        super().__init__(self.code)


class TerminalAuditFindingError(Error):
    pass


def canonical(value: Any) -> bytes:
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n").encode("utf-8")


def digest(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def pairs(items: list[tuple[str, Any]]) -> dict[str, Any]:
    value: dict[str, Any] = {}
    for key, item in items:
        if key in value:
            raise Error("binding_failure")
        value[key] = item
    return value


def _regular(path: Path, mode: int | None = 0o600) -> None:
    try:
        info = path.lstat()
    except OSError:
        raise Error("binding_failure") from None
    if stat.S_ISLNK(info.st_mode) or not stat.S_ISREG(info.st_mode):
        raise Error("binding_failure")
    if mode is not None and stat.S_IMODE(info.st_mode) != mode:
        raise Error("mode_drift")


def _directory(path: Path, mode: int | None = 0o700) -> None:
    try:
        info = path.lstat()
    except OSError:
        raise Error("binding_failure") from None
    if stat.S_ISLNK(info.st_mode) or not stat.S_ISDIR(info.st_mode):
        raise Error("binding_failure")
    if mode is not None and stat.S_IMODE(info.st_mode) != mode:
        raise Error("mode_drift")


def _private_directory(package: Path, path: Path) -> None:
    """Create a package subtree and enforce private modes on every new level."""
    path.mkdir(parents=True, exist_ok=True, mode=0o700)
    current = path
    while current != package:
        current.chmod(0o700)
        current = current.parent
    _directory(package, 0o700)


def read(path: Path, label: str = "sealed value") -> Any:
    try:
        _regular(path, 0o600)
        return json.loads(path.read_bytes().decode("utf-8", "strict"), object_pairs_hook=pairs)
    except (OSError, UnicodeDecodeError, json.JSONDecodeError, Error):
        raise Error("binding_failure") from None


def atomic(path: Path, value: Any, *, raw: bool = False) -> str:
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    _directory(path.parent, 0o700)
    data = value if raw else canonical(value)
    if not isinstance(data, bytes):
        raise Error("binding_failure")
    if path.exists() or path.is_symlink():
        _regular(path, 0o600)
        if path.read_bytes() != data:
            raise Error("binding_failure")
        return digest(data)
    fd, name = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    temporary = Path(name)
    try:
        with open(fd, "wb", closefd=True) as handle:
            handle.write(data)
            handle.flush()
            os.fsync(handle.fileno())
        temporary.chmod(0o600)
        temporary.replace(path)
        os.chmod(path, 0o600)
    except BaseException:
        temporary.unlink(missing_ok=True)
        raise
    return digest(data)


def seed_clean_consensus(
    custody_sha256: str, manifest_sha256: str, ordered_identity_commitment_sha256: str
) -> str:
    raw = f"phase3-cycle007-consensus-audit-v1\n{custody_sha256}{manifest_sha256}{ordered_identity_commitment_sha256}"
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def rank_row(seed: str, lane: str, unit_id: str, unit_sha256: str) -> str:
    raw = f"{seed}{lane}{unit_id}{unit_sha256}"
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def compute_zero_event_bound(population_count: int) -> float:
    if population_count <= 0:
        return 0.0
    return 1.0 - (0.05 ** (1.0 / population_count))


_PACKAGE_MANIFEST_FIELDS = frozenset(
    {
        "schema_version",
        "evaluation_cycle_id",
        "source_evaluation_cycle_id",
        "text_free",
        "custody_receipt_raw_sha256",
        "ordered_identity_commitment_sha256",
        "identity_union_commitment_sha256",
        "ordered_packet_commitment_sha256",
        "packet_count",
        "row_count",
        "lane_row_counts",
        "packets",
        "receipt_sha256",
    }
)
_PACKAGE_PACKET_FIELDS = frozenset(
    {"lane", "packet_index", "canonical_basename", "row_count", "raw_sha256", "packet_identity_set_sha256"}
)


def _unsigned_hash(value: Mapping[str, Any]) -> str:
    return digest(canonical({key: item for key, item in value.items() if key != "receipt_sha256"}))


def _package_packet_snapshot(package: Path) -> dict[str, Any]:
    """Load and independently reconcile the package's frozen packet boundary.

    The audit must consume the materialization manifest as a frozen package
    boundary, while also proving every listed packet and row is present on
    disk.  Hardcoded lane packet counts are only a source-cycle sanity check;
    they are never used as the iteration boundary.
    """
    custody_path = package / "custody-receipt.json"
    manifest_path = package / "manifest.json"
    _regular(custody_path, 0o600)
    _regular(manifest_path, 0o600)
    custody_raw = custody_path.read_bytes()
    custody = read(custody_path, "custody receipt")
    manifest_raw = manifest_path.read_bytes()
    manifest = read(manifest_path, "materialization manifest")
    if (
        not isinstance(custody, dict)
        or not isinstance(manifest, dict)
        or not _PACKAGE_MANIFEST_FIELDS.issubset(manifest)
        or manifest.get("schema_version") != "phase3_cycle007_materialization_manifest_v1"
        or manifest.get("evaluation_cycle_id") != CYCLE
        or manifest.get("source_evaluation_cycle_id") != "phase3-v2-1-evaluation-cycle-005"
        or manifest.get("text_free") is not True
        or manifest.get("custody_receipt_raw_sha256") != digest(custody_raw)
        or manifest.get("receipt_sha256") != _unsigned_hash(manifest)
        or not isinstance(manifest.get("packets"), list)
        or not isinstance(manifest.get("lane_row_counts"), dict)
        or set(manifest["lane_row_counts"]) != set(LANES)
        or not isinstance(manifest.get("packet_count"), int)
        or isinstance(manifest.get("packet_count"), bool)
        or manifest["packet_count"] != len(manifest["packets"])
        or not isinstance(manifest.get("row_count"), int)
        or isinstance(manifest.get("row_count"), bool)
        or manifest["row_count"] < 0
        or any(
            not isinstance(value, int) or isinstance(value, bool) or value < 0
            for value in manifest["lane_row_counts"].values()
        )
    ):
        raise Error("binding_failure")
    if (
        not isinstance(custody, dict)
        or custody.get("receipt_sha256") != _unsigned_hash(custody)
        or custody.get("packet_count") != manifest["packet_count"]
        or custody.get("row_count") != manifest["row_count"]
        or custody.get("lane_row_counts") != manifest["lane_row_counts"]
        or custody.get("ordered_identity_commitment_sha256")
        != manifest["ordered_identity_commitment_sha256"]
        or custody.get("identity_union_commitment_sha256") != manifest["identity_union_commitment_sha256"]
        or custody.get("ordered_packet_commitment_sha256") != manifest["ordered_packet_commitment_sha256"]
        or manifest.get("ordered_packet_commitment_sha256")
        != digest(canonical(manifest["packets"]))
        or manifest.get("ordered_identity_commitment_sha256") != ORDERED_IDENTITY_COMMITMENT_SHA256
    ):
        raise Error("binding_failure")

    packet_records: list[dict[str, Any]] = []
    packet_keys: set[tuple[str, int]] = set()
    for item in manifest["packets"]:
        if not isinstance(item, dict) or not _PACKAGE_PACKET_FIELDS.issubset(item):
            raise Error("binding_failure")
        lane = item.get("lane")
        packet_index = item.get("packet_index")
        key = (lane, packet_index)
        if (
            lane not in LANES
            or not isinstance(packet_index, int)
            or isinstance(packet_index, bool)
            or packet_index < 1
            or key in packet_keys
            or item.get("canonical_basename") != f"packet-{packet_index:04d}.json"
            or not isinstance(item.get("row_count"), int)
            or isinstance(item.get("row_count"), bool)
            or item["row_count"] < 0
            or not isinstance(item.get("raw_sha256"), str)
            or len(item["raw_sha256"]) != 64
            or any(char not in "0123456789abcdef" for char in item["raw_sha256"])
            or not isinstance(item.get("packet_identity_set_sha256"), str)
            or len(item["packet_identity_set_sha256"]) != 64
            or any(char not in "0123456789abcdef" for char in item["packet_identity_set_sha256"])
        ):
            raise Error("binding_failure")
        packet_keys.add(key)
        packet_records.append(item)

    packet_data_lookup: dict[tuple[str, int], dict[str, Any]] = {}
    ordered_identities: list[list[Any]] = []
    seen_identities: list[tuple[str, str]] = []
    lane_rows: dict[str, int] = {lane: 0 for lane in LANES}
    listed_names: dict[str, set[str]] = {lane: set() for lane in LANES}
    for item in packet_records:
        lane = item["lane"]
        packet_index = item["packet_index"]
        listed_names[lane].add(item["canonical_basename"])
    for lane in LANES:
        lane_dir = package / lane
        _directory(lane_dir, 0o700)
        actual_names = {entry.name for entry in lane_dir.iterdir()}
        if actual_names != listed_names[lane]:
            raise Error("binding_failure")

    for item in packet_records:
        lane = item["lane"]
        packet_index = item["packet_index"]
        packet_path = package / lane / item["canonical_basename"]
        _regular(packet_path, 0o600)
        packet_raw = packet_path.read_bytes()
        packet = read(packet_path, f"packet {lane}/{packet_index}")
        rows = packet.get("rows")
        if (
            not isinstance(rows, list)
            or packet.get("packet_identity_set_sha256") != item["packet_identity_set_sha256"]
            or len(rows) != item["row_count"]
            or digest(packet_raw) != item["raw_sha256"]
        ):
            raise Error("binding_failure")
        packet_identities: list[tuple[str, str]] = []
        for row_index, row in enumerate(rows):
            if (
                not isinstance(row, Mapping)
                or not isinstance(row.get("unit_id"), str)
                or not isinstance(row.get("unit_sha256"), str)
                or len(row["unit_sha256"]) != 64
                or any(char not in "0123456789abcdef" for char in row["unit_sha256"])
            ):
                raise Error("binding_failure")
            identity = (row["unit_id"], row["unit_sha256"])
            packet_identities.append(identity)
            ordered_identities.append([lane, packet_index, row_index, identity[0], identity[1]])
            seen_identities.append(identity)
        if digest(canonical(sorted(packet_identities))) != item["packet_identity_set_sha256"]:
            raise Error("binding_failure")
        lane_rows[lane] += len(rows)
        packet_data_lookup[(lane, packet_index)] = packet

    if (
        len(seen_identities) != manifest["row_count"]
        or len(seen_identities) != len(set(seen_identities))
        or lane_rows != manifest["lane_row_counts"]
        or digest(canonical(ordered_identities)) != manifest["ordered_identity_commitment_sha256"]
        or digest(canonical(sorted(seen_identities))) != manifest["identity_union_commitment_sha256"]
    ):
        raise Error("binding_failure")
    return {
        "custody": custody,
        "manifest": manifest,
        "custody_raw_sha256": digest(custody_raw),
        "manifest_raw_sha256": digest(manifest_raw),
        "packet_records": packet_records,
        "packet_data_lookup": packet_data_lookup,
        "ordered_identities": ordered_identities,
        "seen_identities": seen_identities,
    }


def _assert_partition_exhaustive(
    packet_rows: list[Mapping[str, Any]],
    clean_records: list[Mapping[str, Any]],
    risk_records: list[Mapping[str, Any]],
    disagreement_records: list[Mapping[str, Any]],
) -> None:
    """Require clean/risk/disagreement rows to partition one packet exactly."""
    expected = [(row.get("unit_id"), row.get("unit_sha256")) for row in packet_rows]
    if any(not isinstance(identity[0], str) or not isinstance(identity[1], str) for identity in expected):
        raise Error("audit_population_drift")
    partition = [*clean_records, *risk_records, *disagreement_records]
    partition_identities = [_identity(record) for record in partition]
    if (
        len(partition_identities) != len(expected)
        or len(partition_identities) != len(set(partition_identities))
        or set(partition_identities) != set(expected)
    ):
        raise Error("audit_population_drift")


def sample_clean_consensus(
    package: Path,
    clean_consensus_records: list[dict[str, Any]],
    *,
    ordered_identity_commitment_sha256: str | None = None,
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    custody_sha256 = digest((package / "custody-receipt.json").read_bytes())
    manifest_sha256 = digest((package / "manifest.json").read_bytes())
    ordered_identity_commitment = ordered_identity_commitment_sha256 or ORDERED_IDENTITY_COMMITMENT_SHA256
    # The amendment freezes the source Cycle 005 custody/manifest values, not
    # this materialization's private receipt hashes, as sampler seed inputs.
    seed = seed_clean_consensus(SOURCE_CUSTODY_SHA256, SOURCE_MANIFEST_SHA256, ordered_identity_commitment)

    population_count = len(clean_consensus_records)

    # Attach ranks
    for r in clean_consensus_records:
        u_id = r["source_row"]["unit_id"]
        u_sha = r["source_row"]["unit_sha256"]
        r["rank"] = rank_row(seed, r["lane"], u_id, u_sha)

    # Group into strata
    strata: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for r in clean_consensus_records:
        lane = r["lane"]
        label = r["label"]
        if lane == "clean_label":
            code = label.get("decision_code", "unknown")
            strata[f"clean:{code}"].append(r)
        elif lane == "residual_label":
            for p in label.get("phenomena", []):
                p_id = p.get("phenomenon_id", "unknown")
                p_code = p.get("decision_code", "unknown")
                strata[f"residual:{p_id}:{p_code}"].append(r)

    # Sort each stratum by rank ascending and take top 10
    selected_by_unit: dict[tuple[str, str], dict[str, Any]] = {}
    for _stratum_name, stratum_rows in sorted(strata.items()):
        sorted_stratum = sorted(stratum_rows, key=lambda x: x["rank"])
        top_10 = sorted_stratum[:10]
        for row in top_10:
            uid = (row["source_row"]["unit_id"], row["source_row"]["unit_sha256"])
            if uid not in selected_by_unit:
                selected_by_unit[uid] = row

    mandatory_union = list(selected_by_unit.values())

    if population_count <= 600:
        # Whole population
        sample = sorted(clean_consensus_records, key=lambda x: x["rank"])
    elif len(mandatory_union) >= 600:
        # Expand rather than truncate
        sample = mandatory_union
    else:
        # Fill to 600 from remaining population by global rank
        remaining = [
            r
            for r in clean_consensus_records
            if (r["source_row"]["unit_id"], r["source_row"]["unit_sha256"]) not in selected_by_unit
        ]
        remaining_sorted = sorted(remaining, key=lambda x: x["rank"])
        needed = 600 - len(mandatory_union)
        sample = mandatory_union + remaining_sorted[:needed]

    sample_sorted = sorted(
        sample,
        key=lambda x: (x["lane"], x["source_row"]["unit_id"], x["source_row"]["unit_sha256"]),
    )

    bound = compute_zero_event_bound(len(sample_sorted))

    sample_identities = [(r["source_row"]["unit_id"], r["source_row"]["unit_sha256"]) for r in sample_sorted]
    sample_commitment = digest(canonical(sample_identities))

    sample_receipt = {
        "schema_version": "phase3_cycle007_clean_consensus_sample_receipt_v1",
        "evaluation_cycle_id": CYCLE,
        "amendment_sha256": AMENDMENT_SHA256,
        "custody_receipt_raw_sha256": custody_sha256,
        "source_label_manifest_raw_sha256": SOURCE_MANIFEST_SHA256,
        "manifest_raw_sha256": manifest_sha256,
        "ordered_identity_commitment_sha256": ordered_identity_commitment,
        "population_count": population_count,
        "audited_count": len(sample_sorted),
        "one_sided_95_bound": bound,
        "seed": seed,
        "seed_source_custody_sha256": SOURCE_CUSTODY_SHA256,
        "seed_source_manifest_sha256": SOURCE_MANIFEST_SHA256,
        "strata_counts": {k: len(v) for k, v in sorted(strata.items())},
        "sample_identity_commitment_sha256": sample_commitment,
        "text_free": True,
    }
    sample_receipt["receipt_sha256"] = digest(canonical(sample_receipt))
    return sample_receipt, sample_sorted


def _identity(record: Mapping[str, Any]) -> tuple[str, str]:
    source = record.get("source_row")
    if not isinstance(source, Mapping) or not isinstance(source.get("unit_id"), str) or not isinstance(source.get("unit_sha256"), str):
        raise Error("audit_population_drift")
    return source["unit_id"], source["unit_sha256"]


def _strata_for(record: Mapping[str, Any]) -> list[str]:
    label = record.get("label")
    if not isinstance(label, Mapping):
        raise Error("stratum_selection_drift")
    if record.get("lane") == "clean_label":
        return [f"clean:{label.get('decision_code', 'unknown')}"]
    if record.get("lane") == "residual_label":
        phenomena = label.get("phenomena")
        if not isinstance(phenomena, list):
            raise Error("stratum_selection_drift")
        return [f"residual:{item.get('phenomenon_id', 'unknown')}:{item.get('decision_code', 'unknown')}" for item in phenomena if isinstance(item, Mapping)]
    raise Error("stratum_selection_drift")


def seal_sampler(
    package: Path,
    clean_records: list[dict[str, Any]],
    risk_records: list[dict[str, Any]],
    sample_records: list[dict[str, Any]],
    sample_receipt: Mapping[str, Any],
) -> dict[str, Any]:
    """Seal the entire population, exclusions, ranks, strata, and selection before review."""
    clean = [
        {
            "lane": record["lane"],
            "packet_index": record["packet_index"],
            "unit_id": _identity(record)[0],
            "unit_sha256": _identity(record)[1],
            "rank": record.get("rank"),
            "strata": _strata_for(record),
        }
        for record in clean_records
    ]
    risk = [(record["lane"], record["packet_index"], *_identity(record)) for record in risk_records]
    selected = [(record["lane"], record["packet_index"], *_identity(record)) for record in sample_records]
    if any(not isinstance(item["rank"], str) or len(item["rank"]) != 64 for item in clean):
        raise Error("rank_calculation_drift")
    out = package / OUTPUT
    _private_directory(package, out)
    private_seal = {
        "schema_version": "phase3_cycle007_clean_consensus_sampler_seal_v1",
        "evaluation_cycle_id": CYCLE,
        "sample_receipt_sha256": sample_receipt["receipt_sha256"],
        "clean_population": clean,
        "risk_exclusions": risk,
        "selected_identities": selected,
    }
    private_hash = atomic(out / "clean-consensus-sampler-seal.json", private_seal)
    receipt = {
        "schema_version": "phase3_cycle007_clean_consensus_sampler_seal_receipt_v1",
        "evaluation_cycle_id": CYCLE,
        "amendment_sha256": AMENDMENT_SHA256,
        "clean_population_count": len(clean),
        "risk_exclusion_count": len(risk),
        "selected_count": len(selected),
        "clean_population_identity_commitment_sha256": digest(canonical([(item["lane"], item["packet_index"], item["unit_id"], item["unit_sha256"]) for item in clean])),
        "risk_exclusion_identity_commitment_sha256": digest(canonical(risk)),
        "rank_and_strata_commitment_sha256": digest(canonical([(item["lane"], item["packet_index"], item["unit_id"], item["unit_sha256"], item["rank"], item["strata"]) for item in clean])),
        "selected_identity_commitment_sha256": digest(canonical(selected)),
        "private_sampler_seal_sha256": private_hash,
        "sample_receipt_sha256": sample_receipt["receipt_sha256"],
        "text_free": True,
    }
    receipt["receipt_sha256"] = digest(canonical(receipt))
    atomic(out / "clean-consensus-sampler-seal-receipt.json", receipt)
    return receipt


def _missing_normative_risk(record: Mapping[str, Any], row_evidence: Mapping[str, Any]) -> bool:
    """A scored residual decision without any current-normative record is risky."""
    label = record.get("label")
    if not isinstance(label, Mapping) or not isinstance(label.get("phenomena"), list):
        return False
    scored = any(
        isinstance(phenomenon, Mapping)
        and phenomenon.get("decision_code") in {"positive", "acceptable_control", "protected"}
        for phenomenon in label["phenomena"]
    )
    if not scored:
        return False
    normative = [item for item in row_evidence.get("evidence", []) if isinstance(item, Mapping) and item.get("channel") == "pravopys_2026_normative"]
    return not normative or any(item.get("status") != "attested" or item.get("supports") == "no_conclusion" for item in normative)


def audit_row_evidence(
    record: dict[str, Any],
    row_evidence: Mapping[str, Any],
) -> None:
    """Check a reviewed/audited consensus row for any terminal audit findings."""
    source_row = record["source_row"]
    label = record["label"]
    evidence_records = list(row_evidence.get("evidence", []))

    # Check for Russianism/Surzhyk accepted as standard
    is_neg = (
        source_row.get("is_negative_control") is True
        or source_row.get("negative_control") is True
        or source_row.get("is_russianism_control") is True
        or source_row.get("is_surzhyk_control") is True
        or source_row.get("control_type") in {"russianism", "surzhyk", "source_conflict"}
        or source_row.get("family_id") in {"russianism", "surzhyk", "source_conflict"}
    )
    if is_neg:
        if label.get("decision_code") == "agree":
            raise TerminalAuditFindingError("russianism_accepted_finding")
        if "phenomena" in label:
            for p in label.get("phenomena", []):
                if p.get("decision_code") == "positive":
                    raise TerminalAuditFindingError("russianism_accepted_finding")

    # Check for unsupported acceptance or incorrect positive
    if label.get("decision_code") == "agree":
        suff = validator.classify_sufficiency(row_evidence)
        if suff != "sufficient":
            raise TerminalAuditFindingError("unsupported_acceptance_finding")
        # Evidence references must exist and be valid
        by_id = {str(r["evidence_id"]): r for r in evidence_records}
        cited = [by_id.get(eid) for eid in label.get("evidence_ids", [])]
        if any(c is None for c in cited) or not any(c is not None and contract.is_sufficient_positive(c) for c in cited):
            raise TerminalAuditFindingError("foreign_or_insufficient_evidence_finding")

    if "phenomena" in label:
        for p in label.get("phenomena", []):
            if p.get("decision_code") in {"positive", "acceptable_control", "protected"}:
                suff = validator.classify_sufficiency(row_evidence, phenomenon_id=p.get("phenomenon_id"))
                if suff != "sufficient":
                    raise TerminalAuditFindingError("unsupported_acceptance_finding")
                by_id = {str(r["evidence_id"]): r for r in evidence_records}
                cited = [by_id.get(eid) for eid in p.get("evidence_ids", [])]
                if any(c is None for c in cited) or not any(c is not None and contract.is_sufficient_positive(c) for c in cited):
                    raise TerminalAuditFindingError("foreign_or_insufficient_evidence_finding")


def _stop(package: Path, code: str) -> None:
    """Write one private, text-free terminal receipt; never overwrite it."""
    path = package / OUTPUT / "provider-stop.json"
    if path.exists() or path.is_symlink():
        return
    _private_directory(package, path.parent)
    atomic(
        path,
        {
            "schema_version": "phase3_cycle007_consensus_audit_stop_v1",
            "evaluation_cycle_id": CYCLE,
            "amendment_sha256": AMENDMENT_SHA256,
            "failure_code": code if code in FAILURE_CODES else "terminal_audit_finding",
            "new_provider_calls_allowed": False,
            "text_free": True,
        },
    )


def _review_schema(count: int) -> dict[str, Any]:
    return {
        "type": "object",
        "additionalProperties": False,
        "required": ["reviews"],
        "properties": {
            "reviews": {
                "type": "array",
                "minItems": count,
                "maxItems": count,
                "items": {
                    "type": "object",
                    "additionalProperties": False,
                    "required": ["lane", "packet_index", "unit_id", "unit_sha256", "source_evidence_sha256", "outcome"],
                    "properties": {
                        "lane": {"enum": ["clean_label", "residual_label"]},
                        "packet_index": {"type": "integer", "minimum": 1},
                        "unit_id": {"type": "string"},
                        "unit_sha256": {"type": "string", "pattern": "^[0-9a-f]{64}$"},
                        "source_evidence_sha256": {"type": "string", "pattern": "^[0-9a-f]{64}$"},
                        "outcome": {
                            "enum": [
                                "pass",
                                "unsupported_acceptance",
                                "incorrect_positive",
                                "russianism_accepted",
                                "surzhyk_accepted",
                                "foreign_or_insufficient_evidence",
                            ]
                        },
                    },
                },
            }
        },
    }


def _targets(risk_records: list[dict[str, Any]], sample_records: list[dict[str, Any]], evidence: Mapping[tuple[str, str], Mapping[str, Any]]) -> list[dict[str, Any]]:
    targets: list[dict[str, Any]] = []
    seen: set[tuple[str, str]] = set()
    for scope, records in (("risk", risk_records), ("clean_sample", sample_records)):
        for record in records:
            identity = _identity(record)
            if identity in seen or identity not in evidence:
                raise Error("audit_population_drift")
            seen.add(identity)
            targets.append(
                {
                    "scope": scope,
                    "lane": record["lane"],
                    "packet_index": record["packet_index"],
                    "source_row": record["source_row"],
                    "label": record["label"],
                    "row_evidence": evidence[identity],
                    "source_evidence_sha256": digest(canonical(evidence[identity])),
                }
            )
    return targets


def _review_batches(targets: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Use the frozen packet boundary as the bounded live-review work unit."""
    grouped: dict[tuple[str, int], list[dict[str, Any]]] = defaultdict(list)
    for target in targets:
        grouped[(target["lane"], target["packet_index"])].append(target)
    batches: list[dict[str, Any]] = []
    for batch_index, ((lane, packet_index), members) in enumerate(sorted(grouped.items()), 1):
        ordered = sorted(members, key=lambda item: (item["scope"], item["source_row"]["unit_id"], item["source_row"]["unit_sha256"]))
        if len(ordered) > MAX_REVIEW_BATCH_TARGETS:
            raise Error("audit_population_drift")
        identities = [(item["lane"], item["packet_index"], item["source_row"]["unit_id"], item["source_row"]["unit_sha256"]) for item in ordered]
        batches.append(
            {
                "batch_index": batch_index,
                "lane": lane,
                "packet_index": packet_index,
                "target_count": len(ordered),
                "identity_commitment_sha256": digest(canonical(identities)),
                "targets": ordered,
            }
        )
    return batches


def _batch_descriptors(batches: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Persist metadata only; the canonical plan owns the full target payload once."""
    return [
        {
            "batch_index": batch["batch_index"],
            "lane": batch["lane"],
            "packet_index": batch["packet_index"],
            "target_count": batch["target_count"],
            "identity_commitment_sha256": batch["identity_commitment_sha256"],
        }
        for batch in batches
    ]


def seal_review_plan(
    package: Path,
    risk_records: list[dict[str, Any]],
    sample_records: list[dict[str, Any]],
    evidence: Mapping[tuple[str, str], Mapping[str, Any]],
    sample_receipt: Mapping[str, Any],
    *,
    evidence_manifest_sha256: str = "0" * 64,
    source_identity_sha256: str = "0" * 64,
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    """Seal exact source-bearing targets before any source-authority review call."""
    targets = _targets(risk_records, sample_records, evidence)
    batches = _review_batches(targets)
    out = package / OUTPUT
    _private_directory(package, out)
    identity_rows = [(item["lane"], item["packet_index"], item["source_row"]["unit_id"], item["source_row"]["unit_sha256"]) for item in targets]
    plan = {
        "schema_version": "phase3_cycle007_consensus_source_review_plan_v1",
        "evaluation_cycle_id": CYCLE,
        "amendment_sha256": AMENDMENT_SHA256,
        "sample_receipt_sha256": sample_receipt["receipt_sha256"],
        "risk_target_count": len(risk_records),
        "clean_sample_target_count": len(sample_records),
        "target_identity_commitment_sha256": digest(canonical(identity_rows)),
        "evidence_manifest_raw_sha256": evidence_manifest_sha256,
        "sources_identity_commitment_sha256": source_identity_sha256,
        "batches": _batch_descriptors(batches),
        "targets": targets,
    }
    plan_hash = atomic(out / "source-review-plan.json", plan)
    receipt = {
        "schema_version": "phase3_cycle007_consensus_source_review_plan_receipt_v1",
        "evaluation_cycle_id": CYCLE,
        "amendment_sha256": AMENDMENT_SHA256,
        "risk_target_count": len(risk_records),
        "clean_sample_target_count": len(sample_records),
        "target_identity_commitment_sha256": plan["target_identity_commitment_sha256"],
        "review_batch_count": len(batches),
        "review_batch_union_commitment_sha256": digest(canonical([item["identity_commitment_sha256"] for item in batches])),
        "evidence_manifest_raw_sha256": evidence_manifest_sha256,
        "sources_identity_commitment_sha256": source_identity_sha256,
        "source_review_plan_sha256": plan_hash,
        "sample_receipt_sha256": sample_receipt["receipt_sha256"],
        "text_free": True,
    }
    receipt["receipt_sha256"] = digest(canonical(receipt))
    atomic(out / "source-review-plan-receipt.json", receipt)
    return receipt, targets


def _structured(raw: bytes) -> Any:
    try:
        events = [json.loads(line, object_pairs_hook=pairs) for line in raw.decode("utf-8", "strict").splitlines() if line.strip()]
    except (UnicodeDecodeError, json.JSONDecodeError, Error) as exc:
        raise Error("stream_json_invalid") from exc
    init = [item for item in events if isinstance(item, dict) and item.get("event") == "init"]
    result = [item for item in events if isinstance(item, dict) and item.get("event") == "result"]
    if len(init) != 1 or len(result) != 1 or not events or events[0] is not init[0] or events[-1] is not result[0]:
        raise Error("terminal_result_count_drift")
    if not isinstance(init[0].get("init"), dict) or init[0]["init"].get("model") != MODEL:
        raise Error("structured_output_envelope_drift")
    output = result[0].get("result")
    if not isinstance(output, dict) or output.get("status") != "SUCCESS" or not isinstance(output.get("structured_output"), dict):
        raise Error("structured_output_envelope_drift")
    return output["structured_output"]


def _command(provider: Path, schema_path: Path) -> list[str]:
    return [str(provider), "--model", MODEL, "--mode", "plan", "--sandbox", "--disable-slash-commands", "--input-format", "stream-json", "--output-format", "stream-json", "--json-schema", str(schema_path)]


def _provider_mode(provider: Path, expected_agy_sha256: str | None, synthetic_provider: bool) -> None:
    if synthetic_provider:
        if expected_agy_sha256 is not None:
            raise Error("mode_drift")
        try:
            if provider.is_symlink():
                raise Error("mode_drift")
            resolved = provider.resolve(strict=True)
            if not resolved.is_file():
                raise Error("mode_drift")
        except OSError as exc:
            raise Error("mode_drift") from exc
        return
    if not isinstance(expected_agy_sha256, str) or len(expected_agy_sha256) != 64 or any(c not in "0123456789abcdef" for c in expected_agy_sha256):
        raise Error("binding_failure")
    try:
        if provider.is_symlink():
            raise Error("binding_failure")
        resolved = provider.resolve(strict=True)
        if not resolved.is_file() or digest(resolved.read_bytes()) != expected_agy_sha256:
            raise Error("binding_failure")
    except OSError as exc:
        raise Error("binding_failure") from exc


def validate_review_results(targets: list[dict[str, Any]], payload: Any) -> list[dict[str, Any]]:
    if not isinstance(payload, dict) or set(payload) != {"reviews"} or not isinstance(payload["reviews"], list) or len(payload["reviews"]) != len(targets):
        raise Error("incomplete_risk_review")
    expected = [
        (target["lane"], target["packet_index"], target["source_row"]["unit_id"], target["source_row"]["unit_sha256"], target["source_evidence_sha256"])
        for target in targets
    ]
    actual: list[tuple[Any, ...]] = []
    for review in payload["reviews"]:
        if not isinstance(review, dict) or set(review) != {"lane", "packet_index", "unit_id", "unit_sha256", "source_evidence_sha256", "outcome"}:
            raise Error("review_result_drift")
        actual.append((review["lane"], review["packet_index"], review["unit_id"], review["unit_sha256"], review["source_evidence_sha256"]))
    if len(actual) != len(set(actual)):
        raise Error("review_identity_drift")
    if actual != expected:
        raise Error("review_identity_drift")
    finding_codes = {
        "unsupported_acceptance": "unsupported_acceptance_finding",
        "incorrect_positive": "incorrect_positive_finding",
        "russianism_accepted": "russianism_accepted_finding",
        "surzhyk_accepted": "surzhyk_accepted_finding",
        "foreign_or_insufficient_evidence": "foreign_or_insufficient_evidence_finding",
    }
    for review in payload["reviews"]:
        if review["outcome"] in finding_codes:
            raise TerminalAuditFindingError(finding_codes[review["outcome"]])
        if review["outcome"] != "pass":
            raise Error("review_result_drift")
    return payload["reviews"]


def _review_envelope(targets: list[dict[str, Any]], source_binding: Mapping[str, Any] | None = None) -> bytes:
    text = (
        "You are the fresh source-qualified Cycle 007 consensus auditor. Review every immutable target and its supplied frozen Sources MCP evidence, which is authoritative over model memory. "
        "Return pass only if the label is source-supported; otherwise return the exact terminal finding. Do not rewrite labels or explain.\n"
        "--- BEGIN IMMUTABLE SOURCE REVIEW TARGETS JSON ---\n"
        + canonical({"source_binding": source_binding or {}, "targets": targets}).decode("utf-8")
        + "--- END IMMUTABLE SOURCE REVIEW TARGETS JSON ---\n"
    )
    return canonical({"event": "user", "message": {"content": [{"type": "text", "text": text}]}})


def _provider_review(
    package: Path,
    targets: list[dict[str, Any]],
    provider: Path,
    *,
    expected_agy_sha256: str | None,
    synthetic_provider: bool,
    source_binding: Mapping[str, Any],
) -> tuple[list[dict[str, Any]], dict[str, Any], int, str]:
    _provider_mode(provider, expected_agy_sha256, synthetic_provider)
    runtime = Path(tempfile.mkdtemp(prefix=".cycle007-consensus-review-", dir=package))
    os.chmod(runtime, 0o700)
    stdin_path, schema_path, raw_path = runtime / "prompt.stdin", runtime / "response-schema.json", runtime / "provider.raw"
    envelope = _review_envelope(targets, source_binding)
    try:
        atomic(stdin_path, envelope, raw=True)
        atomic(schema_path, _review_schema(len(targets)))
        for attempt in range(1, MAX_STRUCTURAL_ATTEMPTS + 1):
            if not synthetic_provider:
                try:
                    if digest(provider.resolve(strict=True).read_bytes()) != expected_agy_sha256:
                        raise Error("binding_failure")
                except OSError as exc:
                    raise Error("binding_failure") from exc
            with stdin_path.open("rb") as stdin_handle, raw_path.open("xb") as raw_handle:
                os.chmod(raw_path, 0o600)
                result = subprocess.run(_command(provider, schema_path), stdin=stdin_handle, stdout=raw_handle, stderr=subprocess.DEVNULL, check=False, shell=False)
            if result.returncode:
                raise Error("provider_transport_failure")
            try:
                reviews = validate_review_results(targets, _structured(raw_path.read_bytes()))
            except TerminalAuditFindingError:
                raise
            except Error as exc:
                raw_path.unlink(missing_ok=True)
                if exc.failure_code not in {"stream_json_invalid", "terminal_result_count_drift", "structured_output_envelope_drift"} or attempt == MAX_STRUCTURAL_ATTEMPTS:
                    raise
                continue
            return reviews, {"exact_model": MODEL, "model_family": FAMILY, "harness": HARNESS}, attempt, digest(envelope)
        raise Error("stream_json_invalid")
    finally:
        stdin_path.unlink(missing_ok=True)
        raw_path.unlink(missing_ok=True)
        schema_path.unlink(missing_ok=True)
        shutil.rmtree(runtime, ignore_errors=True)


def _human_review(targets: list[dict[str, Any]], value: Any) -> tuple[list[dict[str, Any]], dict[str, Any], int, str]:
    if not isinstance(value, dict) or set(value) != {"reviewer", "reviews"} or not isinstance(value["reviewer"], dict):
        raise Error("reviewer_binding_drift")
    reviewer = value["reviewer"]
    if set(reviewer) != {"exact_model", "model_family", "harness", "source_qualified"} or reviewer.get("model_family") != "human" or reviewer.get("harness") != "local-operator" or reviewer.get("source_qualified") is not True or not isinstance(reviewer.get("exact_model"), str) or not reviewer["exact_model"]:
        raise Error("reviewer_binding_drift")
    reviews = validate_review_results(targets, {"reviews": value["reviews"]})
    return reviews, reviewer, 0, digest(canonical(value))


def _verify_review_plan(package: Path, targets: list[dict[str, Any]], plan_receipt: Mapping[str, Any]) -> None:
    path = package / OUTPUT / "source-review-plan.json"
    _regular(path, 0o600)
    if digest(path.read_bytes()) != plan_receipt.get("source_review_plan_sha256"):
        raise Error("binding_failure")
    plan = read(path, "source review plan")
    identities = [(item["lane"], item["packet_index"], item["source_row"]["unit_id"], item["source_row"]["unit_sha256"]) for item in targets]
    batches = _review_batches(targets)
    if (
        not isinstance(plan, dict)
        or plan.get("targets") != targets
        or plan.get("batches") != _batch_descriptors(batches)
        or plan.get("target_identity_commitment_sha256") != digest(canonical(identities))
        or plan_receipt.get("target_identity_commitment_sha256") != digest(canonical(identities))
        or plan_receipt.get("review_batch_count") != len(batches)
        or plan_receipt.get("review_batch_union_commitment_sha256") != digest(canonical([item["identity_commitment_sha256"] for item in batches]))
        or plan.get("evidence_manifest_raw_sha256") != plan_receipt.get("evidence_manifest_raw_sha256")
        or plan.get("sources_identity_commitment_sha256") != plan_receipt.get("sources_identity_commitment_sha256")
    ):
        raise Error("binding_failure")


def _source_review(
    package: Path,
    targets: list[dict[str, Any]],
    plan_receipt: Mapping[str, Any],
    *,
    provider: Path | None = None,
    expected_agy_sha256: str | None = None,
    synthetic_provider: bool = False,
    human_review_result: Any | None = None,
    fixture_override: Any | None = None,
) -> dict[str, Any]:
    """Run exactly one explicit human or Anthropic-family review transport."""
    _verify_review_plan(package, targets, plan_receipt)
    batches = _review_batches(targets)
    source_binding = {
        "evidence_manifest_raw_sha256": plan_receipt["evidence_manifest_raw_sha256"],
        "sources_identity_commitment_sha256": plan_receipt["sources_identity_commitment_sha256"],
        "source_review_plan_sha256": plan_receipt["source_review_plan_sha256"],
    }
    batch_receipts: list[dict[str, Any]] = []
    batch_attempts: dict[int, int] = {}
    if fixture_override is not None:
        if not synthetic_provider:
            raise Error("mode_drift")
        all_reviews = validate_review_results(targets, fixture_override)
        reviewer, attempts, input_hash = {"exact_model": "synthetic-fixture", "model_family": "synthetic", "harness": "fixture"}, 0, digest(canonical(fixture_override))
    elif human_review_result is not None:
        all_reviews, reviewer, attempts, input_hash = _human_review(targets, human_review_result)
    elif provider is not None:
        all_reviews = []
        reviewer: dict[str, Any] | None = None
        attempts = 0
        input_hash = digest(canonical([]))
        for batch in batches:
            reviews, current_reviewer, current_attempts, current_input_hash = _provider_review(
                package,
                batch["targets"],
                provider,
                expected_agy_sha256=expected_agy_sha256,
                synthetic_provider=synthetic_provider,
                source_binding=source_binding,
            )
            if reviewer is None:
                reviewer = current_reviewer
            elif reviewer != current_reviewer:
                raise Error("reviewer_binding_drift")
            all_reviews.extend(reviews)
            attempts += current_attempts
            batch_attempts[batch["batch_index"]] = current_attempts
            input_hash = digest(canonical([input_hash, current_input_hash]))
        if reviewer is None:
            raise Error("review_missing")
    else:
        raise Error("review_missing")
    by_identity = {
        (review["lane"], review["packet_index"], review["unit_id"], review["unit_sha256"], review["source_evidence_sha256"]): review
        for review in all_reviews
    }
    if len(by_identity) != len(targets):
        raise Error("review_identity_drift")
    ordered_reviews: list[dict[str, Any]] = []
    out = package / OUTPUT
    _private_directory(package, out)
    for batch in batches:
        expected = [
            (target["lane"], target["packet_index"], target["source_row"]["unit_id"], target["source_row"]["unit_sha256"], target["source_evidence_sha256"])
            for target in batch["targets"]
        ]
        batch_reviews = [by_identity.get(identity) for identity in expected]
        if any(review is None for review in batch_reviews):
            raise Error("incomplete_risk_review")
        result = {"reviews": batch_reviews}
        validate_review_results(batch["targets"], result)
        result_hash = atomic(out / f"source-review-results-batch-{batch['batch_index']:04d}.json", result)
        receipt = {
            "schema_version": "phase3_cycle007_consensus_source_review_batch_receipt_v1",
            "evaluation_cycle_id": CYCLE,
            "amendment_sha256": AMENDMENT_SHA256,
            "source_review_plan_sha256": plan_receipt["source_review_plan_sha256"],
            "batch_index": batch["batch_index"],
            "lane": batch["lane"],
            "packet_index": batch["packet_index"],
            "identity_commitment_sha256": batch["identity_commitment_sha256"],
            "reviewed_count": len(batch_reviews),
            "review_result_sha256": result_hash,
            "review_input_sha256": input_hash if provider is None else digest(_review_envelope(batch["targets"], source_binding)),
            "evidence_manifest_raw_sha256": plan_receipt["evidence_manifest_raw_sha256"],
            "sources_identity_commitment_sha256": plan_receipt["sources_identity_commitment_sha256"],
            "reviewer": reviewer,
            "attempt_count": batch_attempts.get(batch["batch_index"], 0),
            "terminal_findings_count": 0,
            "text_free": True,
        }
        receipt["receipt_sha256"] = digest(canonical(receipt))
        atomic(out / f"source-review-batch-receipt-{batch['batch_index']:04d}.json", receipt)
        batch_receipts.append(receipt)
        ordered_reviews.extend(batch_reviews)
    if len(ordered_reviews) != len(targets):
        raise Error("incomplete_risk_review")
    result_hash = atomic(out / "source-review-results.json", {"reviews": ordered_reviews})
    receipt = {
        "schema_version": "phase3_cycle007_consensus_source_review_receipt_v1",
        "evaluation_cycle_id": CYCLE,
        "amendment_sha256": AMENDMENT_SHA256,
        "source_review_plan_sha256": plan_receipt["source_review_plan_sha256"],
        "target_identity_commitment_sha256": plan_receipt["target_identity_commitment_sha256"],
        "reviewed_count": len(ordered_reviews),
        "review_result_sha256": result_hash,
        "review_input_sha256": input_hash,
        "reviewer": reviewer,
        "attempt_count": attempts,
        "review_batch_count": len(batch_receipts),
        "review_batch_receipt_union_sha256": digest(canonical([item["receipt_sha256"] for item in batch_receipts])),
        "evidence_manifest_raw_sha256": plan_receipt["evidence_manifest_raw_sha256"],
        "sources_identity_commitment_sha256": plan_receipt["sources_identity_commitment_sha256"],
        "terminal_findings_count": 0,
        "text_free": True,
    }
    receipt["receipt_sha256"] = digest(canonical(receipt))
    atomic(out / "source-review-receipt.json", receipt)
    return receipt


def source_review(
    package: Path,
    targets: list[dict[str, Any]],
    plan_receipt: Mapping[str, Any],
    *,
    provider: Path | None = None,
    expected_agy_sha256: str | None = None,
    synthetic_provider: bool = False,
    human_review_result: Any | None = None,
    fixture_override: Any | None = None,
) -> dict[str, Any]:
    try:
        return _source_review(
            package,
            targets,
            plan_receipt,
            provider=provider,
            expected_agy_sha256=expected_agy_sha256,
            synthetic_provider=synthetic_provider,
            human_review_result=human_review_result,
            fixture_override=fixture_override,
        )
    except Error as exc:
        with contextlib.suppress(Error):
            _stop(package, exc.failure_code)
        raise


def _run_audit(
    package: Path,
    *,
    provider: Path | None = None,
    expected_agy_sha256: str | None = None,
    synthetic_provider: bool = False,
    human_review_result: Any | None = None,
    fixture_override: Any | None = None,
) -> dict[str, Any]:
    """Execute 100% review of risk-triggered consensus and sample audit of clean consensus."""
    _directory(package, 0o700)
    package_snapshot = _package_packet_snapshot(package)
    package_manifest = package_snapshot["manifest"]
    package_commitment = package_manifest["ordered_identity_commitment_sha256"]
    package_manifest_sha256 = package_snapshot["manifest_raw_sha256"]
    compare_dir = package / COMPARE_OUTPUT
    _directory(compare_dir, 0o700)
    compare_names: dict[str, set[str]] = {lane: set() for lane in LANES}
    for packet_record in package_snapshot["packet_records"]:
        lane = packet_record["lane"]
        index = packet_record["packet_index"]
        compare_names[lane].update(
            {
                f"clean-consensus-{index:04d}.json",
                f"risk-consensus-{index:04d}.json",
                f"disagreements-{index:04d}.json",
            }
        )
    for lane, expected_names in compare_names.items():
        lane_dir = compare_dir / lane
        _directory(lane_dir, 0o700)
        if {entry.name for entry in lane_dir.iterdir()} != expected_names:
            raise Error("audit_population_drift")

    if (package / OUTPUT / "provider-stop.json").exists():
        raise Error("binding_failure")
    # Load all clean-consensus and risk-consensus records.
    clean_records: list[dict[str, Any]] = []
    risk_records: list[dict[str, Any]] = []

    # Read sidecars into lookup
    evidence_manifest_path = package / "evidence" / "manifest.json"
    _regular(evidence_manifest_path, 0o600)
    ev_manifest = read(evidence_manifest_path, "evidence manifest")
    expected_identity = {k: ev_manifest.get(k) for k in validator._IDENTITY_FIELDS}
    validator.validate_manifest(ev_manifest, expected_identity=expected_identity)
    evidence_manifest_sha256 = digest(evidence_manifest_path.read_bytes())
    sources_identity_sha256 = digest(canonical(expected_identity))

    sidecar_lookup: dict[tuple[str, int], dict[str, Any]] = {}
    for entry in ev_manifest["sidecars"]:
        p_idx = entry["packet_index"]
        lane = entry["lane"]
        sidecar_path = package / "evidence" / f"sidecar-{p_idx:04d}.json"
        _regular(sidecar_path, 0o600)
        s_data = read(sidecar_path, f"sidecar {p_idx}")
        validator.validate_sidecar(s_data, expected_identity=expected_identity)
        sidecar_lookup[(lane, p_idx)] = s_data

    # Map row unit to row_evidence
    unit_evidence_map: dict[tuple[str, str], dict[str, Any]] = {}
    for s_data in sidecar_lookup.values():
        for r_ev in s_data.get("rows", []):
            unit_evidence_map[(r_ev["unit_id"], r_ev["unit_sha256"])] = r_ev

    for packet_record in package_snapshot["packet_records"]:
        lane = packet_record["lane"]
        index = packet_record["packet_index"]
        lane_dir = compare_dir / lane
        _directory(lane_dir, 0o700)
        clean_p = lane_dir / f"clean-consensus-{index:04d}.json"
        risk_p = lane_dir / f"risk-consensus-{index:04d}.json"
        disagreement_p = lane_dir / f"disagreements-{index:04d}.json"
        _regular(clean_p, 0o600)
        _regular(risk_p, 0o600)
        _regular(disagreement_p, 0o600)
        c_val = read(clean_p, f"clean consensus {lane}/{index}")
        r_val = read(risk_p, f"risk consensus {lane}/{index}")
        d_val = read(disagreement_p, f"disagreements {lane}/{index}")
        if not all(isinstance(value, dict) and isinstance(value.get("records"), list) for value in (c_val, r_val, d_val)):
            raise Error("audit_population_drift")
        packet = package_snapshot["packet_data_lookup"][(lane, index)]
        _assert_partition_exhaustive(packet["rows"], c_val["records"], r_val["records"], d_val["records"])
        for r in c_val.get("records", []):
            clean_records.append({**r, "lane": lane, "packet_index": index})
        for r in r_val.get("records", []):
            risk_records.append({**r, "lane": lane, "packet_index": index})

    # Seal the exact clean sample and source-bearing review plan before any provider/human call.
    sample_receipt, sample_records = sample_clean_consensus(
        package,
        clean_records,
        ordered_identity_commitment_sha256=package_commitment,
    )
    out_dir = package / OUTPUT
    _private_directory(package, out_dir)
    atomic(out_dir / "clean-consensus-sample.json", sample_receipt)
    sampler_seal_receipt = seal_sampler(package, clean_records, risk_records, sample_records, sample_receipt)
    for record in clean_records:
        evidence = unit_evidence_map.get(_identity(record))
        if evidence is None or _missing_normative_risk(record, evidence):
            raise Error("audit_population_drift")
    plan_receipt, targets = seal_review_plan(
        package,
        risk_records,
        sample_records,
        unit_evidence_map,
        sample_receipt,
        evidence_manifest_sha256=evidence_manifest_sha256,
        source_identity_sha256=sources_identity_sha256,
    )
    review_receipt = source_review(
        package,
        targets,
        plan_receipt,
        provider=provider,
        expected_agy_sha256=expected_agy_sha256,
        synthetic_provider=synthetic_provider,
        human_review_result=human_review_result,
        fixture_override=fixture_override,
    )
    # Mechanical checks are a guardrail, never a substitute for the sealed source review above.
    for record in [*risk_records, *sample_records]:
        evidence = unit_evidence_map.get(_identity(record))
        if evidence is None:
            raise Error("binding_failure")
        audit_row_evidence(record, evidence)

    # Write risk review receipt
    risk_review_receipt = {
        "schema_version": "phase3_cycle007_risk_review_receipt_v1",
        "evaluation_cycle_id": CYCLE,
        "amendment_sha256": AMENDMENT_SHA256,
        "custody_receipt_raw_sha256": digest((package / "custody-receipt.json").read_bytes()),
        "source_label_manifest_raw_sha256": SOURCE_MANIFEST_SHA256,
        "manifest_raw_sha256": package_manifest_sha256,
        "ordered_identity_commitment_sha256": package_commitment,
        "risk_population_count": len(risk_records),
        "reviewed_count": len(risk_records),
        "source_review_receipt_sha256": review_receipt["receipt_sha256"],
        "reviewer": review_receipt["reviewer"],
        "terminal_findings_count": 0,
        "text_free": True,
    }
    risk_review_receipt["receipt_sha256"] = digest(canonical(risk_review_receipt))
    atomic(out_dir / "risk-review-receipt.json", risk_review_receipt)

    # Write clean audit receipt
    clean_audit_receipt = {
        "schema_version": "phase3_cycle007_clean_audit_receipt_v1",
        "evaluation_cycle_id": CYCLE,
        "amendment_sha256": AMENDMENT_SHA256,
        "custody_receipt_raw_sha256": digest((package / "custody-receipt.json").read_bytes()),
        "source_label_manifest_raw_sha256": SOURCE_MANIFEST_SHA256,
        "manifest_raw_sha256": package_manifest_sha256,
        "ordered_identity_commitment_sha256": package_commitment,
        "clean_population_count": len(clean_records),
        "audited_count": len(sample_records),
        "one_sided_95_bound": sample_receipt["one_sided_95_bound"],
        "source_review_receipt_sha256": review_receipt["receipt_sha256"],
        "reviewer": review_receipt["reviewer"],
        "terminal_findings_count": 0,
        "text_free": True,
    }
    clean_audit_receipt["receipt_sha256"] = digest(canonical(clean_audit_receipt))
    atomic(out_dir / "clean-audit-receipt.json", clean_audit_receipt)

    # Batch receipt
    batch_receipt = {
        "schema_version": "phase3_cycle007_consensus_audit_batch_receipt_v1",
        "evaluation_cycle_id": CYCLE,
        "amendment_sha256": AMENDMENT_SHA256,
        "custody_receipt_raw_sha256": digest((package / "custody-receipt.json").read_bytes()),
        "source_label_manifest_raw_sha256": SOURCE_MANIFEST_SHA256,
        "manifest_raw_sha256": package_manifest_sha256,
        "ordered_identity_commitment_sha256": package_commitment,
        "risk_population_count": len(risk_records),
        "risk_reviewed_count": len(risk_records),
        "clean_population_count": len(clean_records),
        "clean_audited_count": len(sample_records),
        "one_sided_95_bound": sample_receipt["one_sided_95_bound"],
        "sample_receipt_sha256": sample_receipt["receipt_sha256"],
        "sampler_seal_receipt_sha256": sampler_seal_receipt["receipt_sha256"],
        "source_review_plan_receipt_sha256": plan_receipt["receipt_sha256"],
        "source_review_receipt_sha256": review_receipt["receipt_sha256"],
        "reviewer": review_receipt["reviewer"],
        "terminal_findings_count": 0,
        "passed": True,
        "text_free": True,
    }
    batch_receipt["receipt_sha256"] = digest(canonical(batch_receipt))
    atomic(out_dir / "batch-receipt.json", batch_receipt)
    return batch_receipt


def run_audit(
    package: Path,
    *,
    provider: Path | None = None,
    expected_agy_sha256: str | None = None,
    synthetic_provider: bool = False,
    human_review_result: Any | None = None,
    fixture_override: Any | None = None,
) -> dict[str, Any]:
    """Fail closed on every missing, malformed, semantic, or transport review outcome."""
    try:
        return _run_audit(
            package,
            provider=provider,
            expected_agy_sha256=expected_agy_sha256,
            synthetic_provider=synthetic_provider,
            human_review_result=human_review_result,
            fixture_override=fixture_override,
        )
    except Error as exc:
        with contextlib.suppress(Error):
            _stop(package, exc.failure_code)
        raise


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--package", type=Path, required=True)
    transport = parser.add_mutually_exclusive_group(required=True)
    transport.add_argument("--provider-bin", type=Path, help="explicit real AGY executable")
    transport.add_argument("--test-provider-bin", type=Path, help="explicit synthetic fixture transport only")
    transport.add_argument("--human-review-result", type=Path, help="explicit private human source-review result")
    parser.add_argument("--expected-agy-executable-sha", help="required exact AGY hash for real Anthropic review")
    args = parser.parse_args(argv)
    try:
        human_result = read(args.human_review_result, "human review result") if args.human_review_result else None
        provider = args.provider_bin or args.test_provider_bin
        result = run_audit(
            args.package,
            provider=provider,
            expected_agy_sha256=args.expected_agy_executable_sha,
            synthetic_provider=args.test_provider_bin is not None,
            human_review_result=human_result,
        )
    except Error as exc:
        result = {"ok": False, "failure_code": exc.failure_code, "text_free": True}
    except Exception:
        result = {"ok": False, "failure_code": "terminal_audit_finding", "text_free": True}
    else:
        result = {"ok": True, **result}
    print(json.dumps(result, sort_keys=True, separators=(",", ":")))
    return 0 if result.get("ok") else 2


if __name__ == "__main__":
    raise SystemExit(main())
