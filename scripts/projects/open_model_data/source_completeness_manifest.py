"""Ordered structural source accounting for #10512; never source clearance."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
import uuid
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator, validators

ROOT = Path(__file__).resolve().parents[3]
MATRIX = ROOT / "registry/atlas/source-completeness/required-source-matrix.md"
CONTRACT = MATRIX.with_name("manifest-contract.md")
STATES = ("verified-complete", "missing", "corrupt", "quarantined", "genuinely_absent")
STAGES = ("acquisition", "raw_custody", "parsing", "admission")
VERSION = "source-completeness.v1"
TEXT = {"type": "string", "minLength": 1, "pattern": r"\S"}
DIGEST = {"type": "string", "minLength": 64, "maxLength": 64, "pattern": "^[0-9a-f]{64}$"}
EvidenceValidator = validators.extend(
    Draft202012Validator,
    type_checker=Draft202012Validator.TYPE_CHECKER.redefine("integer", lambda _checker, value: type(value) is int),
)


class InvalidEvidence(ValueError):
    """Evidence is malformed, ambiguous, inconsistent, or digest-drifted."""


class EvidenceArgumentParser(argparse.ArgumentParser):
    def error(self, message: str) -> None:
        raise InvalidEvidence("invalid CLI arguments; use --help")


def _object(properties: dict, required: list[str] | None = None) -> dict:
    return {
        "type": "object",
        "properties": properties,
        "required": list(properties) if required is None else required,
        "additionalProperties": False,
    }


def _array(items: dict, minimum: int = 0) -> dict:
    return {"type": "array", "items": items, "minItems": minimum}


REF = _object({"path": TEXT, "sha256": DIGEST, "schema_version": TEXT, "locator": TEXT})
IDENTITY = _object(
    {
        "key": TEXT,
        "homonym": {"anyOf": [TEXT, {"type": "null"}]},
        "sense": {"anyOf": [TEXT, {"type": "null"}]},
        "path": _array(TEXT),
        "occurrence": {"type": "integer", "minimum": 0},
    }
)
UNIT = _object({"identity": IDENTITY, "locator": TEXT, "sha256": DIGEST})
FIELD = _object({"name": TEXT, "applicability": {"enum": ["applicable", "not_applicable"]}, "reason": TEXT})
REQUIREMENT = _object(
    {"requirement_id": TEXT, "gap": TEXT, "owner": TEXT, "fields": _array(FIELD, 1), "consumers": _array(TEXT, 1)}
)
BOUNDARY = {
    "range_id": TEXT,
    "requirement_id": TEXT,
    "edition": TEXT,
    "range": TEXT,
    "snapshot": TEXT,
    "source_locator": TEXT,
    "register_kind": {"enum": ["checked_register", "unchecked_extension", "source_index"]},
    "retrieved_at": TEXT,
}
RANGE = _object(
    {
        **BOUNDARY,
        "membership": {"enum": ["KNOWN", "UNKNOWN"]},
        "index": {"anyOf": [REF, {"type": "null"}]},
        "units": _array(UNIT),
    }
)
LINK = _object({"range_id": TEXT, "identity": IDENTITY})
MEMBER = _object({"member_id": TEXT, "locator": TEXT, "source_units": _array(LINK)})
RECORD = _object(
    {
        "range_id": TEXT,
        "identity": IDENTITY,
        "source_unit_sha256": DIGEST,
        "field": TEXT,
        "stage": TEXT,
        "state": {"enum": list(STATES)},
        "reason": TEXT,
        "evidence": _array(REF),
        "absence_evidence": {"anyOf": [REF, {"type": "null"}]},
    }
)


def _envelope(kind: str, properties: dict) -> dict:
    return _object({"schema_version": {"const": f"{kind}.v1"}, **properties})


SCHEMAS = {
    "requirements": _envelope("source-requirements", {"matrix_sha256": DIGEST, "requirements": _array(REQUIREMENT, 1)}),
    "source_manifest": _envelope(
        "source-manifest", {"requirements_sha256": DIGEST, "origin": {"const": "source_side"}, "ranges": _array(RANGE)}
    ),
    "stage_evidence": _envelope("stage-evidence", {"source_manifest_sha256": DIGEST, "records": _array(RECORD)}),
    "lexical_universe": _envelope(
        "lexical-universe",
        {
            "source_manifest_sha256": DIGEST,
            "membership": {"enum": ["KNOWN", "UNKNOWN"]},
            "index": {"anyOf": [REF, {"type": "null"}]},
            "members": _array(MEMBER),
        },
    ),
    "legacy_membership": _envelope(
        "legacy-membership",
        {
            "source_manifest_sha256": DIGEST,
            "membership": {"enum": ["KNOWN", "UNKNOWN"]},
            "expected_obligation": {"type": "integer", "const": 123},
            "index": {"anyOf": [REF, {"type": "null"}]},
            "members": _array(MEMBER),
        },
    ),
}


def _bytes(value: Any) -> bytes:
    return (
        json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False) + "\n"
    ).encode("utf-8")


def _sha(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def _unique_pairs(pairs: list[tuple[str, Any]]) -> dict:
    result: dict = {}
    for key, value in pairs:
        if key in result:
            raise InvalidEvidence("duplicate JSON object key")
        result[key] = value
    return result


def _read(path: Path) -> tuple[bytes, Any]:
    try:
        raw = path.read_bytes()
        value = json.loads(raw.decode("utf-8"), object_pairs_hook=_unique_pairs, parse_constant=_bad_constant)
        _bytes(value)
        return raw, value
    except (OSError, ValueError, UnicodeError, RecursionError) as exc:
        raise InvalidEvidence("unreadable or invalid JSON input") from exc


def _bad_constant(value: str) -> None:
    raise InvalidEvidence(f"non-JSON constant: {value}")


def _validate(value: Any, schema: dict, label: str) -> None:
    errors = list(EvidenceValidator(schema).iter_errors(value))
    if errors:
        error = errors[0]
        location = ".".join(map(str, error.absolute_path)) or "root"
        raise InvalidEvidence(f"{label}.{location}: {error.validator} failed")


def _resolve(path: Path) -> Path:
    """Resolve a path, reporting every resolution failure as OSError for the caller's exit boundary."""
    try:
        return path.resolve()
    except (OSError, RuntimeError, ValueError) as exc:
        # Python 3.12 raises RuntimeError for symlink loops and ValueError for embedded NULs.
        raise OSError("path cannot be resolved") from exc


def _distinct(values: list[Any], label: str) -> None:
    keys = [_bytes(value) for value in values]
    if len(set(keys)) != len(keys):
        raise InvalidEvidence(f"duplicate {label}")


def _compare_units(expected: list[dict], actual: list[dict]) -> None:
    """Report source-index discrepancies without printing source identities or text."""
    expected_keys = [_bytes(unit["identity"]) for unit in expected]
    actual_keys = [_bytes(unit["identity"]) for unit in actual]
    missing = len(set(expected_keys) - set(actual_keys))
    extra = len(set(actual_keys) - set(expected_keys))
    if missing or extra:
        raise InvalidEvidence(f"source-index membership mismatch: missing={missing}, extra={extra}")
    if expected_keys != actual_keys:
        raise InvalidEvidence("source-index identity order mismatch")
    for ordinal, (wanted, found) in enumerate(zip(expected, actual, strict=True)):
        for field in ("locator", "sha256"):
            if wanted[field] != found[field]:
                raise InvalidEvidence(f"source-index {field} mismatch at ordinal={ordinal}")


class Inputs:
    """Read exact input bytes once and retain every transitive artifact binding."""

    def __init__(self, paths: dict[str, Path]):
        self.documents: dict[str, Any] = {}
        self.bindings: dict[str, dict] = {}
        self.paths: set[Path] = set()
        for name, path in paths.items():
            raw, value = _read(path)
            _validate(value, SCHEMAS[name], name)
            self.paths.add(_resolve(path))
            self.documents[name] = value
            self.bindings[name] = {"sha256": _sha(raw), "bytes": len(raw), "schema_version": value["schema_version"]}
        self.artifacts: list[dict] = []
        self._artifact_keys: set[bytes] = set()

    def reference(self, ref: dict, base: Path, *, structured: bool = False) -> Any:
        try:
            path = _resolve(base / ref["path"])
            raw = path.read_bytes()
        except (OSError, ValueError) as exc:
            raise InvalidEvidence("referenced artifact unavailable") from exc
        if _sha(raw) != ref["sha256"]:
            raise InvalidEvidence("referenced artifact digest mismatch")
        self.paths.add(path)
        binding = {**ref, "bytes": len(raw)}
        artifact_key = _bytes(binding)
        if artifact_key not in self._artifact_keys:
            self.artifacts.append(binding)
            self._artifact_keys.add(artifact_key)
        if structured:
            reread, value = _read(path)
            if reread != raw or not isinstance(value, dict) or value.get("schema_version") != ref["schema_version"]:
                raise InvalidEvidence("referenced artifact schema/version drift")
            return value
        return None


def _matrix_requirements(requirements: dict) -> list[dict]:
    raw = MATRIX.read_bytes()
    if requirements["matrix_sha256"] != _sha(raw):
        raise InvalidEvidence("canonical requirements matrix digest mismatch")
    rows = re.findall(r"^\| (SRC-[A-Z0-9]+) \|.*? (G-[A-Z0-9]+):", raw.decode(), re.M)
    actual = requirements["requirements"]
    if len(rows) != 20 or [(r["requirement_id"], r["gap"]) for r in actual] != rows:
        raise InvalidEvidence("all 20 ordered matrix requirements and gaps must be preserved")
    for row in actual:
        if row["owner"] != "open-model-data":
            raise InvalidEvidence("matrix gap owner must remain open-model-data")
        _distinct([f["name"] for f in row["fields"]], "requirement field")
        _distinct(row["consumers"], "consumer")
        if not any(f["applicability"] == "applicable" for f in row["fields"]):
            raise InvalidEvidence("a source requirement cannot be removed through not-applicable fields")
    return actual


def _ranges(inputs: Inputs, base: Path, requirements: dict) -> dict[str, dict]:
    result: dict[str, dict] = {}
    source = inputs.documents["source_manifest"]
    if source["requirements_sha256"] != inputs.bindings["requirements"]["sha256"]:
        raise InvalidEvidence("requirements binding digest mismatch")
    for row in source["ranges"]:
        if row["range_id"] in result or row["requirement_id"] not in requirements:
            raise InvalidEvidence("duplicate range or extra requirement")
        try:
            if not row["retrieved_at"].endswith("Z"):
                raise ValueError("UTC required")
            parsed = datetime.fromisoformat(row["retrieved_at"].replace("Z", "+00:00"))
            if parsed.tzinfo is None or "T" not in row["retrieved_at"]:
                raise ValueError("UTC date and time required")
        except ValueError as exc:
            raise InvalidEvidence("retrieved_at must be an actual UTC timestamp") from exc
        if row["membership"] == "UNKNOWN":
            if row["units"] or row["index"] is not None:
                raise InvalidEvidence("UNKNOWN range cannot assert unit membership")
        else:
            if row["index"] is None:
                raise InvalidEvidence("known range requires independent source index")
            index = inputs.reference(row["index"], base, structured=True)
            _validate(index, _envelope("source-index", {**BOUNDARY, "units": _array(UNIT)}), "source-index")
            if any(index[key] != row[key] for key in BOUNDARY):
                raise InvalidEvidence("source-index boundary mismatch")
            _distinct([unit["identity"] for unit in index["units"]], "source-index identity")
            _distinct([unit["identity"] for unit in row["units"]], "source identity")
            _distinct([unit["locator"] for unit in index["units"]], "source-index locator")
            _distinct([unit["locator"] for unit in row["units"]], "source locator")
            _compare_units(index["units"], row["units"])
        result[row["range_id"]] = row
    return result


def _members(inputs: Inputs, name: str, base: Path, ranges: dict) -> list[dict]:
    document = inputs.documents[name]
    if document["membership"] == "UNKNOWN":
        if document["members"] or document["index"] is not None:
            raise InvalidEvidence("UNKNOWN membership cannot assert members")
        return []
    if document["index"] is None:
        raise InvalidEvidence("membership requires independent source-side index")
    index = inputs.reference(document["index"], base, structured=True)
    _validate(
        index,
        _envelope(
            "membership-index",
            {
                "origin": {"const": "source_side"},
                "members": _array(MEMBER),
                "provenance": _object(
                    {
                        "source_locator": TEXT,
                        "source_snapshot": TEXT,
                        "consumer_version": TEXT,
                        "role": {"const": "original_legacy123" if name == "legacy_membership" else "lexical_universe"},
                    }
                ),
            },
        ),
        name,
    )
    if index["members"] != document["members"]:
        raise InvalidEvidence("membership index missing/extra/order drift")
    members = document["members"]
    _distinct([m["member_id"] for m in members], "member identity")
    if name == "legacy_membership" and len(members) != 123:
        raise InvalidEvidence("original legacy obligation requires exactly 123 members")
    indexed_identities = {name: {_bytes(u["identity"]) for u in row["units"]} for name, row in ranges.items()}
    for member in members:
        _distinct(member["source_units"], "member link")
        for link in member["source_units"]:
            identities = indexed_identities.get(link["range_id"])
            if identities is None or _bytes(link["identity"]) not in identities:
                raise InvalidEvidence("member links to unknown/extra source identity")
    return members


def _records(inputs: Inputs, base: Path, ranges: dict, requirements: dict) -> dict:
    records: dict = {}
    ordering: dict = defaultdict(list)
    unit_indexes = {
        name: {_bytes(u["identity"]): (ordinal, u) for ordinal, u in enumerate(row["units"])}
        for name, row in ranges.items()
    }
    for record in inputs.documents["stage_evidence"]["records"]:
        row = ranges.get(record["range_id"])
        if row is None or row["membership"] != "KNOWN":
            raise InvalidEvidence("stage evidence for unknown/extra range")
        requirement = requirements[row["requirement_id"]]
        fields = {f["name"]: f for f in requirement["fields"]}
        if record["field"] not in fields or fields[record["field"]]["applicability"] != "applicable":
            raise InvalidEvidence("stage evidence for extra/not-applicable field")
        if record["stage"] not in (*STAGES, *(f"consumer:{c}" for c in requirement["consumers"])):
            raise InvalidEvidence("extra stage/consumer")
        units = unit_indexes[row["range_id"]]
        identity = _bytes(record["identity"])
        if identity not in units:
            raise InvalidEvidence("extra stage identity")
        if units[identity][1]["sha256"] != record["source_unit_sha256"]:
            raise InvalidEvidence("stage source-unit digest mismatch")
        key = (row["range_id"], identity, record["field"], record["stage"])
        if key in records:
            raise InvalidEvidence("duplicate stage identity")
        order_key = (row["range_id"], record["field"], record["stage"])
        ordering[order_key].append(units[identity][0])
        for ref in record["evidence"]:
            inputs.reference(ref, base)
        if (
            record["state"] in ("verified-complete", "corrupt", "quarantined", "genuinely_absent")
            and not record["evidence"]
        ):
            raise InvalidEvidence("state requires retained evidence")
        if (
            record["state"] == "verified-complete"
            and record["stage"] in ("acquisition", "raw_custody")
            and record["source_unit_sha256"] not in [ref["sha256"] for ref in record["evidence"]]
        ):
            raise InvalidEvidence("acquisition/raw custody must bind exact source bytes")
        if record["state"] == "genuinely_absent":
            if row["register_kind"] == "unchecked_extension" or record["stage"] in STAGES[:2]:
                raise InvalidEvidence("unchecked not_found/acquisition cannot prove absence")
            if record["absence_evidence"] is None:
                raise InvalidEvidence("absence requires positive source evidence")
            evidence = inputs.reference(record["absence_evidence"], base, structured=True)
            _validate(evidence.get("identity"), IDENTITY, "source-absence.identity")
            expected = {
                "schema_version": "source-absence.v1",
                "source_manifest_sha256": inputs.bindings["source_manifest"]["sha256"],
                "range_id": row["range_id"],
                "identity": record["identity"],
                "field": record["field"],
                "locator": row["source_locator"],
            }
            if evidence != expected:
                raise InvalidEvidence("positive source absence binding mismatch")
        elif record["absence_evidence"] is not None:
            raise InvalidEvidence("unexpected absence evidence")
        records[key] = record
    for positions in ordering.values():
        if positions != sorted(positions):
            raise InvalidEvidence("reordered stage identities")
    for key, record in records.items():
        if record["state"] == "genuinely_absent":
            for stage in STAGES[:2]:
                predecessor = records.get((*key[:3], stage))
                if predecessor is None or predecessor["state"] != "verified-complete":
                    raise InvalidEvidence("missing/damaged acquisition or raw custody cannot prove absence")
    return records


def _atlas_census(path: Path, inputs: Inputs, ordered: list[dict], ranges: dict[str, dict]) -> dict:
    """Observe exact Atlas lemma/source-key matches without inferring source membership.

    atlas-census.v1 retains entry ordinals, verbatim lemmas/slugs and every matched
    range/identity. Counts use entries, including repeated lemmas, as denominator.
    Partial/unknown source inventories have null full-coverage counts and separate
    supplied-known counts. All input, matrix and accounting-contract bytes are bound.
    This observational artifact cannot approve Candidate A or replace source-side
    lexical-universe/legacy membership, stage evidence or independent reconciliation.
    """
    raw, document = _read(path)
    _validate(
        document,
        {
            "type": "object",
            "required": ["version", "entries"],
            "properties": {
                "version": {"const": "0.1"},
                "entries": _array(
                    {
                        "type": "object",
                        "required": ["lemma", "url_slug"],
                        "properties": {"lemma": TEXT, "url_slug": TEXT},
                    }
                ),
            },
        },
        "atlas-manifest",
    )
    entries = document["entries"]
    _distinct([entry["url_slug"] for entry in entries], "Atlas URL slug")
    inputs.paths.add(_resolve(path))
    inputs.bindings["atlas_manifest"] = {
        "sha256": _sha(raw),
        "bytes": len(raw),
        "schema_version": "atlas-manifest:0.1",
    }
    contract_raw = CONTRACT.read_bytes()
    inputs.paths.add(_resolve(CONTRACT))
    inputs.paths.add(_resolve(MATRIX))
    keys = Counter(entry["lemma"] for entry in entries)
    matches: dict[str, list[dict]] = defaultdict(list)
    coverage = []
    for requirement in ordered:
        requirement_id = requirement["requirement_id"]
        selected = [row for row in ranges.values() if row["requirement_id"] == requirement_id]
        known = [row for row in selected if row["membership"] == "KNOWN"]
        known_keys: set[str] = set()
        matched_units = 0
        for row in known:
            for unit in row["units"]:
                key = unit["identity"]["key"]
                known_keys.add(key)
                if key in keys:
                    matched_units += 1
                    matches[key].append(
                        {
                            "requirement_id": requirement_id,
                            "range_id": row["range_id"],
                            "identity": unit["identity"],
                        }
                    )
        matched_entries = sum(keys[key] for key in known_keys)
        partitioned = bool(selected) and len(known) == len(selected)
        coverage.append(
            {
                "requirement_id": requirement_id,
                "gap": requirement["gap"],
                "owner": requirement["owner"],
                "partition_status": "PARTITIONED" if partitioned else "UNPARTITIONED",
                "entry_count": len(entries),
                "exact_key_matched_entry_count": matched_entries if partitioned else None,
                "no_exact_key_match_entry_count": len(entries) - matched_entries if partitioned else None,
                "supplied_known_matched_entry_count": matched_entries,
                "supplied_known_matched_unit_count": matched_units,
            }
        )
    return {
        "schema_version": "atlas-census.v1",
        "evidence_role": "exact_key_observation_only",
        "programme_completeness": "UNRESOLVED",
        "contract_sha256": _sha(contract_raw),
        "matrix_sha256": inputs.documents["requirements"]["matrix_sha256"],
        "inputs": dict(inputs.bindings),
        "required_requirement_count": 20,
        "entry_count": len(entries),
        "distinct_lemma_count": len(keys),
        "requirements": coverage,
        "entries": [
            {
                "ordinal": ordinal,
                "lemma": entry["lemma"],
                "url_slug": entry["url_slug"],
                "source_key_matches": matches.get(entry["lemma"], []),
            }
            for ordinal, entry in enumerate(entries)
        ],
    }


def account(paths: dict[str, Path], *, atlas_manifest: Path | None = None) -> tuple[dict[str, bytes], dict]:
    """Validate independent inventories and account for all supplied units and members."""
    if set(paths) != set(SCHEMAS):
        raise InvalidEvidence("all five explicit input artifacts are required")
    inputs = Inputs(paths)
    ordered = _matrix_requirements(inputs.documents["requirements"])
    requirements = {r["requirement_id"]: r for r in ordered}
    source_sha = inputs.bindings["source_manifest"]["sha256"]
    for name in ("stage_evidence", "lexical_universe", "legacy_membership"):
        if inputs.documents[name]["source_manifest_sha256"] != source_sha:
            raise InvalidEvidence(f"{name} source-manifest digest mismatch")
    ranges = _ranges(inputs, paths["source_manifest"].parent, requirements)
    membership = {
        name: _members(inputs, name, paths[name].parent, ranges) for name in ("lexical_universe", "legacy_membership")
    }
    records = _records(inputs, paths["stage_evidence"].parent, ranges, requirements)
    gaps: list[dict] = []

    def gap(
        requirement: dict,
        field: str,
        stage: str,
        reason: str,
        evidence: list,
        range_id: str | None = None,
        identity: dict | None = None,
    ) -> None:
        gaps.append(
            {
                "requirement_id": requirement["requirement_id"],
                "field": field,
                "stage": stage,
                "gap": requirement["gap"],
                "owner": requirement["owner"],
                "reason": reason,
                "evidence": evidence,
                "range_id": range_id,
                "identity": identity,
            }
        )

    outputs: dict[str, bytes] = {}
    dispositions: list[dict] = []
    totals: dict[str, Counter] = defaultdict(Counter)
    for requirement in ordered:
        requirement_id = requirement["requirement_id"]
        selected = [r for r in ranges.values() if r["requirement_id"] == requirement_id]
        units_out: list[dict] = []
        range_out: list[dict] = []
        before = len(gaps)
        if not selected:
            for field in requirement["fields"]:
                if field["applicability"] == "applicable":
                    gap(requirement, field["name"], "universe", "required range UNKNOWN; UNPARTITIONED", [])
        for row in selected:
            counts: dict[str, Counter] = defaultdict(Counter)
            if row["membership"] == "UNKNOWN":
                for field in requirement["fields"]:
                    if field["applicability"] == "applicable":
                        gap(requirement, field["name"], "universe", "range UNKNOWN; UNPARTITIONED", [], row["range_id"])
            for ordinal, unit in enumerate(row["units"]):
                partitions: list[dict] = []
                for field in requirement["fields"]:
                    if field["applicability"] == "not_applicable":
                        partitions.append(
                            {"field": field["name"], "state": "not_applicable", "reason": field["reason"]}
                        )
                        continue
                    for stage in (*STAGES, *(f"consumer:{c}" for c in requirement["consumers"])):
                        record = records.get((row["range_id"], _bytes(unit["identity"]), field["name"], stage))
                        state = record["state"] if record else "missing"
                        reason = record["reason"] if record else "no supplied stage evidence"
                        evidence = record["evidence"] if record else []
                        partitions.append(
                            {
                                "field": field["name"],
                                "stage": stage,
                                "state": state,
                                "reason": reason,
                                "evidence": evidence,
                                "absence_evidence": record["absence_evidence"] if record else None,
                            }
                        )
                        counts[stage][state] += 1
                        totals[stage][state] += 1
                        if state in ("missing", "corrupt", "quarantined"):
                            gap(requirement, field["name"], stage, reason, evidence, row["range_id"], unit["identity"])
                states = {p["state"] for p in partitions if p["state"] != "not_applicable"}
                field_states = {p["state"] for p in partitions if p.get("stage") not in (*STAGES[:2], None)}
                state = next(
                    (s for s in ("corrupt", "quarantined", "missing") if s in states),
                    "genuinely_absent" if field_states == {"genuinely_absent"} else "verified-complete",
                )
                units_out.append(
                    {
                        **unit,
                        "range_id": row["range_id"],
                        "ordinal": ordinal,
                        "structural_partition": state,
                        "fields": partitions,
                    }
                )
            unit_states = Counter(u["structural_partition"] for u in units_out if u["range_id"] == row["range_id"])
            range_out.append(
                {
                    **{k: row[k] for k in BOUNDARY},
                    "membership": row["membership"],
                    "unit_count": len(row["units"]) if row["membership"] == "KNOWN" else None,
                    "partition_status": "PARTITIONED" if row["membership"] == "KNOWN" else "UNPARTITIONED",
                    "unit_partitions": {s: unit_states[s] for s in STATES} if row["membership"] == "KNOWN" else None,
                    "stage_counts": {
                        stage: {s: counts[stage][s] for s in STATES}
                        for stage in (*STAGES, *(f"consumer:{c}" for c in requirement["consumers"]))
                    }
                    if row["membership"] == "KNOWN"
                    else None,
                }
            )
        disposition = {
            "requirement_id": requirement_id,
            "gap": requirement["gap"],
            "owner": requirement["owner"],
            "partition_status": "PARTITIONED"
            if selected and all(r["membership"] == "KNOWN" for r in selected)
            else "UNPARTITIONED",
            "supplied_unit_count": len(units_out),
            "gap_count": len(gaps) - before,
        }
        dispositions.append(disposition)
        outputs[f"{requirement_id}.json"] = _bytes(
            {
                "schema_version": VERSION,
                "requirement": requirement,
                "disposition": disposition,
                "ranges": range_out,
                "units": units_out,
            }
        )
    members_out: dict = {}
    for name, members in membership.items():
        document = inputs.documents[name]
        members_out[name] = {
            "membership": document["membership"],
            "members": members,
            "member_count": len(members) if document["membership"] == "KNOWN" else None,
        }
        requirement = requirements["SRC-LEGACY123"]
        if name == "lexical_universe":
            requirement = {**requirement, "requirement_id": None, "gap": "G-UNIVERSE"}
        if document["membership"] == "UNKNOWN":
            gap(
                requirement,
                "*",
                name,
                "membership UNKNOWN; UNPARTITIONED",
                [],
            )
        for member in members:
            if not member["source_units"]:
                gap(requirement, member["member_id"], name, "member source linkage unresolved", [])
    members_out["legacy_membership"]["expected_obligation"] = 123
    outputs["members.json"] = _bytes({"schema_version": VERSION, **members_out})
    if atlas_manifest is not None:
        outputs["atlas-census.json"] = _bytes(_atlas_census(atlas_manifest, inputs, ordered, ranges))
    status = "INCOMPLETE_DIAGNOSTIC" if gaps else "STRUCTURALLY_ACCOUNTED"
    receipt = {
        "schema_version": VERSION,
        "status": status,
        "inputs": inputs.bindings,
        "artifacts": inputs.artifacts,
        "matrix_sha256": inputs.documents["requirements"]["matrix_sha256"],
        "requirements": dispositions,
        "stage_counts": {stage: {s: c[s] for s in STATES} for stage, c in totals.items()},
        "stage_count_scope": "supplied known unit-field obligations only",
        "gaps": gaps,
        "gap_count": len(gaps),
        "required_requirement_count": 20,
        "supplied_unit_count": sum(len(r["units"]) for r in ranges.values()),
        "lexical_member_count": members_out["lexical_universe"]["member_count"],
        "legacy_member_count": members_out["legacy_membership"]["member_count"],
        "legacy_expected_obligation": 123,
        "programme_completeness": "UNRESOLVED",
        "external_prerequisites": [
            "source-authority edition/range/field/universe approval",
            "independent strict snapshot boundary",
            "independent exact-input lexical fidelity and reconciliation",
            "all five original #10512 acceptance criteria",
        ],
        "outputs": [{"path": name, "sha256": _sha(raw), "bytes": len(raw)} for name, raw in outputs.items()],
    }
    # Publication may never replace any direct or transitive evidence file.
    receipt["_input_paths"] = inputs.paths
    return outputs, receipt


def publish(output_dir: Path, outputs: dict[str, bytes], receipt: dict) -> None:
    """Publish into a new directory; the final receipt alone commits the bundle.

    Existing identical bundles are verified, never rewritten. A failed/interrupted
    directory has no receipt and is refused on retry; choose a fresh output path.
    """
    output_dir = output_dir.absolute()
    protected = receipt["_input_paths"]
    public_receipt = {k: v for k, v in receipt.items() if k != "_input_paths"}
    managed = os.environ.get("TMPDIR")
    reports = ROOT / "batch_state/reports"
    resolved = _resolve(output_dir)
    roots = [_resolve(reports)] + ([_resolve(Path(managed))] if managed else [])
    if not any(resolved.is_relative_to(root) and resolved != root for root in roots):
        raise OSError("output directory must be below managed TMPDIR or ignored reports")
    if any(p == resolved or resolved in p.parents for p in protected):
        raise OSError("output directory overlaps input evidence")
    for parent in (output_dir, *output_dir.parents):
        if parent.is_symlink():
            raise OSError("output path cannot contain symlinks")
    files = {**outputs, "manifest-receipt.json": _bytes(public_receipt)}
    if output_dir.exists():
        if (
            not output_dir.is_dir()
            or {p.name for p in output_dir.iterdir()} != set(files)
            or any(p.is_symlink() or not p.is_file() or p.read_bytes() != files[p.name] for p in output_dir.iterdir())
        ):
            raise OSError("existing output is incomplete or differs; use a fresh output directory")
        return
    output_dir.mkdir(parents=True)
    try:
        for name, raw in files.items():
            staging_path = output_dir / f".staging-{uuid.uuid4().hex}"
            with open(staging_path, "wb") as handle:
                handle.write(raw)
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(staging_path, output_dir / name)
            # Persist preceding manifests before the receipt can commit them.
            descriptor = os.open(output_dir, os.O_RDONLY | os.O_DIRECTORY)
            try:
                os.fsync(descriptor)
            finally:
                os.close(descriptor)
    except BaseException:
        (output_dir / "manifest-receipt.json").unlink(missing_ok=True)
        raise


def main(argv: list[str] | None = None) -> int:
    parser = EvidenceArgumentParser(
        description="Produce ordered source-unit manifests and independent stage partitions.\n"
        "Use for structural diagnostics; never source approval or Phase 1 exit.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""Example:
  .venv/bin/python -m scripts.projects.open_model_data.source_completeness_manifest \\
    --requirements requirements.json --source-manifest source.json \\
    --stage-evidence stages.json --lexical-universe universe.json \\
    --legacy-membership legacy.json --output-dir "$TMPDIR/accounting"
Add --atlas-manifest site/src/data/lexicon-manifest.json to census Candidate A.
Outputs: SRC-*.json ordered manifests, members.json, manifest-receipt.json last.
With --atlas-manifest, also atlas-census.json (atlas-census.v1): ordered entries,
exact-key observations for all 20 sources, input/matrix/contract hashes. Unknown
source coverage stays null. Matches never prove source/field completeness or an
approved lexical universe. All five independent accounting inputs remain required.
No source/store writes. Existing byte-identical outputs are verified on rerun.
Exit codes: 0 STRUCTURALLY_ACCOUNTED; 2 INCOMPLETE_DIAGNOSTIC;
3 INVALID_EVIDENCE; 4 PUBLICATION_FAILURE. Neither 0 nor 2 certifies completeness.
Related: registry/atlas/source-completeness/manifest-contract.md; #10512, #9401.
""",
    )
    for name in SCHEMAS:
        parser.add_argument(
            "--" + name.replace("_", "-"),
            required=True,
            type=Path,
            help=f"Explicit {name.replace('_', ' ')} JSON v1 input, e.g. {name}.json; see contract.",
        )
    parser.add_argument(
        "--atlas-manifest",
        type=Path,
        help="Optional Atlas version 0.1 JSON, e.g. site/src/data/lexicon-manifest.json; default: no census.",
    )
    parser.add_argument(
        "--output-dir",
        required=True,
        type=Path,
        help="New managed staging directory below TMPDIR or ignored reports, e.g. $TMPDIR/accounting.",
    )
    try:
        args = parser.parse_args(argv)
        outputs, receipt = account({name: getattr(args, name) for name in SCHEMAS}, atlas_manifest=args.atlas_manifest)
    except (InvalidEvidence, OSError) as exc:
        print(f"INVALID_EVIDENCE: {exc}", file=sys.stderr)
        return 3
    try:
        publish(args.output_dir, outputs, receipt)
    except OSError as exc:
        print(f"PUBLICATION_FAILURE: {exc}", file=sys.stderr)
        return 4
    print(json.dumps({"status": receipt["status"], "gap_count": receipt["gap_count"]}, sort_keys=True))
    return 0 if receipt["status"] == "STRUCTURALLY_ACCOUNTED" else 2


if __name__ == "__main__":
    raise SystemExit(main())
