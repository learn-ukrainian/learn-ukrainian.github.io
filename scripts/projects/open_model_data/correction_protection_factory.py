#!/usr/bin/env python3
"""Build the evidence-graded Phase 3 correction/protection bundle.

The factory consumes the complete text-free Phase 2 complement, emits stand-off
source/evidence/case rows, and appends a public project-authored known-answer
layer.  It never changes source text, creates human gold, exports learning
data, calls a network service, or treats a model/VESUM result as authoritative.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import tempfile
from collections import Counter
from collections.abc import Iterator, Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any, TextIO

from jsonschema import Draft202012Validator, FormatChecker
from referencing import Registry, Resource

from scripts.projects.open_model_data.correction_protection_rules import iter_rule_matches

ROOT = Path(__file__).resolve().parents[3]
CONTRACTS = ROOT / "data/projects/open_model_data/contracts"
SOURCE_SCHEMA = CONTRACTS / "correction_protection_source_v1.schema.json"
EVIDENCE_SCHEMA = CONTRACTS / "correction_protection_evidence_v1.schema.json"
CASE_SCHEMA = CONTRACTS / "correction_protection_case_v1.schema.json"
DISAGREEMENT_SCHEMA = CONTRACTS / "correction_protection_disagreement_v1.schema.json"
BUNDLE_SCHEMA = CONTRACTS / "correction_protection_bundle_manifest_v1.schema.json"
MODEL_LANE_SCHEMA = CONTRACTS / "correction_protection_model_lane_v1.schema.json"
RELEASE_SCHEMA = CONTRACTS / "correction_protection_release_receipt_v1.schema.json"
PHASE2_SCHEMA = CONTRACTS / "prepared_data_complement_record_v1.schema.json"

DEFAULT_THRESHOLDS = (
    ROOT / "data/projects/open_model_data/detector/correction_protection_thresholds_v1.json"
)
DEFAULT_KNOWN_ANSWERS = (
    ROOT / "data/projects/open_model_data/detector/correction_protection_known_answers_v1.json"
)
DEFAULT_PHASE2_RECEIPT = (
    ROOT / "data/projects/open_model_data/evidence/prepared_data_complement_receipt_v1.json"
)
DEFAULT_EVAL_ARTIFACTS = (
    ROOT / "data/projects/ua_eval_harness/heldout_manifest_v1.json",
    ROOT / "data/projects/ua_eval_harness/evalset_v1.jsonl",
    ROOT / "data/projects/ua_eval_harness/v0.2/review_packet_priority_v1.jsonl",
)

CATEGORY_IDS = (
    "russian_lexical_inflectional_intrusion",
    "contextual_calque_government_valency",
    "modern_literary_ukrainian_control",
    "marked_russian_quotation_code_switch",
    "phonetic_russian_in_literature",
    "historical_archaic_ukrainian",
    "dialect_regional_heritage_folklore",
    "surzhyk_contested_contact",
)
HISTORICAL_PERIODS = frozenset({"middle_ukrainian", "old_east_slavic", "historical", "archaic"})
HERITAGE_GENRES = frozenset(
    {"carol", "duma", "ethnography", "folk_song", "folklore", "historical_song", "oral_history"}
)
HERITAGE_REGISTERS = frozenset({"dialect", "regional", "heritage", "folklore"})
EMPTY_SHA256 = hashlib.sha256(b"").hexdigest()


class FactoryError(ValueError):
    """A factory input or output violates the frozen Phase 3 boundary."""


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


def require(condition: bool, message: str) -> None:
    if not condition:
        raise FactoryError(message)


def read_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise FactoryError(f"cannot read JSON {path}: {exc}") from exc
    require(isinstance(value, dict), f"expected JSON object: {path}")
    return value


def artifact(path: Path, *, logical_path: str | None = None, records: int | None = None) -> dict[str, Any]:
    if records is None:
        records = sum(1 for _line in path.open("rb")) if path.suffix == ".jsonl" else 1
    return {
        "logical_path": logical_path or path.as_posix(),
        "records": records,
        "bytes": path.stat().st_size,
        "sha256": sha256_file(path),
    }


def validators() -> dict[Path, Draft202012Validator]:
    paths = (
        SOURCE_SCHEMA,
        EVIDENCE_SCHEMA,
        CASE_SCHEMA,
        DISAGREEMENT_SCHEMA,
        BUNDLE_SCHEMA,
        MODEL_LANE_SCHEMA,
        RELEASE_SCHEMA,
        PHASE2_SCHEMA,
    )
    schemas = {path: read_json(path) for path in paths}
    registry = Registry()
    for schema in schemas.values():
        Draft202012Validator.check_schema(schema)
        registry = registry.with_resource(str(schema["$id"]), Resource.from_contents(schema))
    return {
        path: Draft202012Validator(schema, registry=registry, format_checker=FormatChecker())
        for path, schema in schemas.items()
    }


def validate(value: Mapping[str, Any], active: Draft202012Validator, label: str) -> None:
    errors = sorted(active.iter_errors(value), key=lambda item: list(item.path))
    if errors:
        location = ".".join(str(part) for part in errors[0].path) or "<root>"
        raise FactoryError(f"{label} schema violation at {location}: {errors[0].message}")


def stable_id(namespace: str, payload: Mapping[str, Any]) -> str:
    return f"{namespace}:{sha256_text(canonical_json(payload))}"


def row_sha256(row: Mapping[str, Any]) -> str:
    return sha256_text(canonical_json(row) + "\n")


def claim_boundary() -> dict[str, bool]:
    return {
        "human_gold": False,
        "human_reviewed": False,
        "model_vote_authoritative": False,
        "vesum_absence_only_authoritative": False,
        "training_eligible": False,
        "upload_eligible": False,
        "accelerator_eligible": False,
    }


@dataclass
class JsonlWriter:
    destination: Path
    temporary: Path
    handle: TextIO
    digest: Any
    records: int = 0
    bytes_written: int = 0

    @classmethod
    def open(cls, destination: Path) -> JsonlWriter:
        destination.parent.mkdir(parents=True, exist_ok=True)
        handle = tempfile.NamedTemporaryFile(  # noqa: SIM115
            mode="w",
            encoding="utf-8",
            newline="",
            dir=destination.parent,
            prefix=f".{destination.name}.",
            suffix=".tmp",
            delete=False,
        )
        return cls(destination, Path(handle.name), handle, hashlib.sha256())

    def write(self, value: Mapping[str, Any]) -> str:
        encoded = (canonical_json(value) + "\n").encode("utf-8")
        self.handle.write(encoded.decode("utf-8"))
        self.digest.update(encoded)
        self.records += 1
        self.bytes_written += len(encoded)
        return sha256_bytes(encoded)

    def finish(self) -> dict[str, Any]:
        self.handle.flush()
        os.fsync(self.handle.fileno())
        self.handle.close()
        return {
            "logical_path": self.destination.as_posix(),
            "records": self.records,
            "bytes": self.bytes_written,
            "sha256": self.digest.hexdigest(),
        }

    def abort(self) -> None:
        if not self.handle.closed:
            self.handle.close()
        self.temporary.unlink(missing_ok=True)


def staged_json(destination: Path, value: Mapping[str, Any]) -> Path:
    destination.parent.mkdir(parents=True, exist_ok=True)
    handle = tempfile.NamedTemporaryFile(  # noqa: SIM115
        mode="w",
        encoding="utf-8",
        newline="\n",
        dir=destination.parent,
        prefix=f".{destination.name}.",
        suffix=".tmp",
        delete=False,
    )
    temporary = Path(handle.name)
    with handle:
        handle.write(canonical_json(value) + "\n")
        handle.flush()
        os.fsync(handle.fileno())
    return temporary


def promote(staged: list[tuple[Path, Path]]) -> None:
    for temporary, destination in staged:
        os.replace(temporary, destination)


def iter_jsonl(path: Path) -> Iterator[tuple[int, dict[str, Any]]]:
    with path.open(encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, 1):
            try:
                value = json.loads(line)
            except json.JSONDecodeError as exc:
                raise FactoryError(f"invalid JSONL {path}:{line_number}: {exc}") from exc
            require(isinstance(value, dict), f"expected object at {path}:{line_number}")
            yield line_number, value


def source_row(
    *,
    record_id: str,
    work_id: str,
    source_id: str,
    revision_pin: str,
    locator: str,
    content_sha256: str,
    axes: Mapping[str, str],
    decision_id: str,
    decision_sha256: str,
    capability_refs: list[str],
    start_offset: int,
    end_offset: int,
    context_sha256: str,
    context_text: str | None,
    publication_state: str,
    publication_refs: list[str],
) -> dict[str, Any]:
    identity = {
        "record_id": record_id,
        "work_id": work_id,
        "source_id": source_id,
        "revision_pin": revision_pin,
        "locator": locator,
        "start_offset": start_offset,
        "end_offset": end_offset,
        "context_sha256": context_sha256,
    }
    return {
        "schema_version": "correction_protection_source_v1",
        "source_locator_id": stable_id("cp_source", identity),
        "record_id": record_id,
        "work_id": work_id,
        "source_id": source_id,
        "revision_pin": revision_pin,
        "locator": locator,
        "content_sha256": content_sha256,
        "source_axes": dict(axes),
        "phase2_capability": {
            "decision_id": decision_id,
            "decision_sha256": decision_sha256,
            "evidence_refs": sorted(set(capability_refs)),
        },
        "context": {
            "start_offset": start_offset,
            "end_offset": end_offset,
            "context_sha256": context_sha256,
            "publication_capability_state": publication_state,
            "publication_capability_evidence_refs": sorted(set(publication_refs)),
            "context_text": context_text,
        },
    }


def evidence_row(
    *,
    channel: str,
    source_identity: str,
    source_version: str,
    locator: str,
    query: str | None,
    query_sha256: str,
    status: str,
    supports: str,
    retrieval_sha256: str,
    parser_id: str,
    parser_version: str,
    parser_status: str = "passed",
    model_proposal: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    identity = {
        "channel": channel,
        "source_identity": source_identity,
        "source_version": source_version,
        "locator": locator,
        "query_sha256": query_sha256,
        "supports": supports,
        "retrieval_sha256": retrieval_sha256,
        "model_proposal": model_proposal,
    }
    value: dict[str, Any] = {
        "schema_version": "correction_protection_evidence_v1",
        "evidence_id": stable_id("cp_evidence", identity),
        "channel": channel,
        "source_identity": source_identity,
        "source_version": source_version,
        "locator": locator,
        "query": query,
        "query_sha256": query_sha256,
        "status": status,
        "supports": supports,
        "receipt": {
            "retrieval_id": f"retrieval:{retrieval_sha256}",
            "retrieval_sha256": retrieval_sha256,
            "parser_id": parser_id,
            "parser_version": parser_version,
            "parser_status": parser_status,
        },
        "raw_payload_publication_allowed": False,
        "claim_boundary": {
            "authoritative": False,
            "human_gold": False,
            "model_vote_authoritative": False,
            "vesum_absence_only_authoritative": False,
        },
    }
    if model_proposal is not None:
        value["model_proposal"] = dict(model_proposal)
    return value


def evidence_ref(row: Mapping[str, Any]) -> dict[str, str]:
    return {
        "evidence_id": str(row["evidence_id"]),
        "channel": str(row["channel"]),
        "evidence_sha256": row_sha256(row),
    }


def case_row(
    *,
    source: Mapping[str, Any],
    source_sha256: str,
    start_offset: int,
    end_offset: int,
    surface_sha256: str,
    category_id: str,
    phenomenon: str,
    benchmark_role: str,
    gate: Mapping[str, Any],
    evidence: list[Mapping[str, Any]],
    disposition: str,
    replacement: str | None = None,
    disagreement_refs: list[str] | None = None,
) -> dict[str, Any]:
    identity = {
        "source_locator_id": source["source_locator_id"],
        "start_offset": start_offset,
        "end_offset": end_offset,
        "surface_sha256": surface_sha256,
        "category_id": category_id,
        "disposition": disposition,
    }
    value: dict[str, Any] = {
        "schema_version": "correction_protection_case_v1",
        "case_id": stable_id("cp_case", identity),
        "assurance_tier": "evidence_graded_non_gold",
        "authoritative": False,
        "phenomenon": phenomenon,
        "benchmark_role": benchmark_role,
        "evidence_grade": (
            "model_supported_non_gold"
            if any(row["channel"] == "model_proposal" for row in evidence)
            else "multi_channel"
            if len({row["channel"] for row in evidence}) > 1
            else "source_metadata_only"
        ),
        "source": {
            "source_locator_id": source["source_locator_id"],
            "source_locator_sha256": source_sha256,
        },
        "original": {
            "start_offset": start_offset,
            "end_offset": end_offset,
            "surface_sha256": surface_sha256,
            "immutable": True,
        },
        "evidence_refs": [evidence_ref(row) for row in evidence],
        "category_gate": {
            "category_id": category_id,
            "state": gate["state"],
            "correction_release_allowed": gate["correction_release_allowed"],
            "threshold_config_sha256": gate["threshold_config_sha256"],
            "evidence_refs": sorted(str(row["evidence_id"]) for row in evidence),
        },
        "disposition": disposition,
        "claim_boundary": claim_boundary(),
    }
    if replacement is not None:
        replacement_sha256 = sha256_text(replacement)
        proposal_payload = {
            "replacement_sha256": replacement_sha256,
            "original_surface_sha256": surface_sha256,
            "reversible": True,
        }
        value["proposal"] = {
            "replacement": replacement,
            **proposal_payload,
            "proposal_sha256": sha256_text(canonical_json(proposal_payload)),
        }
    if disagreement_refs:
        value["disagreement_refs"] = sorted(disagreement_refs)
    return value


def phase2_route(row: Mapping[str, Any]) -> tuple[str, str]:
    dimensions = row["dimensions"]
    period = str(dimensions["period"])
    genre = str(dimensions["genre"])
    register = str(dimensions["register"])
    if row["heldout_contamination"]["state"] == "matched":
        return "surzhyk_contested_contact", "excluded"
    if period in HISTORICAL_PERIODS:
        return "historical_archaic_ukrainian", "protected"
    if genre in HERITAGE_GENRES or register in HERITAGE_REGISTERS:
        return "dialect_regional_heritage_folklore", "protected"
    if int(row["signals"]["counts"]["russian_specific"]) > 0:
        return "surzhyk_contested_contact", "unresolved"
    return "modern_literary_ukrainian_control", "unresolved"


def known_answer_disposition(
    *,
    role: str,
    category_id: str,
    rule: Mapping[str, Any],
    correction_release_allowed: bool,
) -> str:
    """Return the same policy-bound disposition used by gates and emission."""
    allowed = tuple(
        str(value)
        for value in rule.get(
            "allowed_dispositions",
            ("correct", "correction", "protected", "excluded", "unresolved"),
        )
    )
    if role == "positive":
        disposition = (
            "correction"
            if correction_release_allowed and "correction" in allowed
            else "unresolved"
        )
    elif role == "acceptable_control":
        disposition = "correct" if "correct" in allowed else "protected"
    else:
        disposition = (
            "unresolved"
            if category_id == "surzhyk_contested_contact" or "protected" not in allowed
            else "protected"
        )
    require(disposition in allowed, f"{category_id}/{role} disposition {disposition!r} is not allowed")
    return disposition


def known_answer_correction_rules(known_answers: Mapping[str, Any]) -> list[dict[str, str]]:
    """Return every candidate correction rule before category gate decisions."""
    rules = [
        {
            "category_id": category_id,
            "surface": str(item["surface"]),
            "replacement": str(item["replacement"]),
        }
        for category_id in CATEGORY_IDS
        for item in known_answers["categories"][category_id].get("positive", [])
        if item.get("replacement") is not None
    ]
    return sorted(rules, key=lambda row: (-len(row["surface"]), row["category_id"]))


def correction_false_positives(
    items: list[dict[str, Any]],
    rules: list[dict[str, str]],
) -> int:
    """Count records on which the actual matcher proposes an unprotected correction."""
    return sum(
        any(not match.protected for match in iter_rule_matches(str(item["text"]), rules))
        for item in items
    )


def gate_results(
    known_answers: Mapping[str, Any],
    thresholds: Mapping[str, Any],
    *,
    model_proposal_lanes: int,
    model_dissent_lanes: int,
) -> dict[str, dict[str, Any]]:
    threshold_sha256 = sha256_text(canonical_json(thresholds) + "\n")
    candidate_rules = known_answer_correction_rules(known_answers)
    results: dict[str, dict[str, Any]] = {}
    for category_id in CATEGORY_IDS:
        specification = known_answers["categories"][category_id]
        rule = thresholds["categories"][category_id]
        counts = {role: len(specification.get(role, [])) for role in ("positive", "acceptable_control", "protected")}
        reasons: list[str] = []
        checks = (
            ("positive", "minimum_source_backed_positive_cases"),
            ("acceptable_control", "minimum_acceptable_controls"),
            ("protected", "minimum_protected_examples"),
        )
        for role, key in checks:
            minimum = int(rule.get(key, 0))
            if counts[role] < minimum:
                reasons.append(f"{role}={counts[role]} below {key}={minimum}")
        declared_canaries = {
            str(canary_id)
            for role in ("positive", "acceptable_control", "protected")
            for item in specification.get(role, [])
            for canary_id in item.get("canary_ids", [])
        }
        missing_canaries = sorted(set(rule.get("required_canaries", [])) - declared_canaries)
        if missing_canaries:
            reasons.append(f"missing required canaries: {', '.join(missing_canaries)}")
        if int(rule.get("minimum_distinct_periods", 0)):
            periods = {str(item.get("period", known_answers["defaults"]["period"])) for item in specification.get("protected", [])}
            if len(periods) < int(rule["minimum_distinct_periods"]):
                reasons.append("distinct period threshold not met")
        if int(rule.get("minimum_distinct_subtypes", 0)):
            subtypes = {str(item.get("register", known_answers["defaults"]["register"])) for item in specification.get("protected", [])}
            if len(subtypes) < int(rule["minimum_distinct_subtypes"]):
                reasons.append("distinct subtype threshold not met")
        non_model_channels = {
            str(evidence["channel"])
            for evidence in specification["evidence"]
            if evidence["channel"] != "model_proposal"
        }
        minimum_channels = int(rule.get("minimum_non_model_evidence_channels_per_correction", 0))
        if counts["positive"] and len(non_model_channels) < minimum_channels:
            reasons.append(
                f"non-model evidence channels={len(non_model_channels)} below "
                f"minimum_non_model_evidence_channels_per_correction={minimum_channels}"
            )
        minimum_proposal_lanes = int(rule.get("minimum_attributed_proposal_lanes", 0))
        if model_proposal_lanes < minimum_proposal_lanes:
            reasons.append(
                f"attributed proposal lanes={model_proposal_lanes} below "
                f"minimum_attributed_proposal_lanes={minimum_proposal_lanes}"
            )
        minimum_dissent_lanes = int(rule.get("minimum_attributed_dissent_lanes", 0))
        if model_dissent_lanes < minimum_dissent_lanes:
            reasons.append(
                f"attributed dissent lanes={model_dissent_lanes} below "
                f"minimum_attributed_dissent_lanes={minimum_dissent_lanes}"
            )
        protected_false_corrections = correction_false_positives(
            specification.get("protected", []),
            candidate_rules,
        )
        control_false_corrections = correction_false_positives(
            specification.get("acceptable_control", []),
            candidate_rules,
        )
        maximum_protected = int(rule.get("maximum_protected_false_corrections", 0))
        maximum_control = int(rule.get("maximum_control_false_corrections", 0))
        if protected_false_corrections > maximum_protected:
            reasons.append(
                f"protected false corrections={protected_false_corrections} above "
                f"maximum_protected_false_corrections={maximum_protected}"
            )
        if control_false_corrections > maximum_control:
            reasons.append(
                f"control false corrections={control_false_corrections} above "
                f"maximum_control_false_corrections={maximum_control}"
            )
        if rule["release_mode"] == "research_only":
            reasons.append("threshold policy fixes category as research-only")
        state = "research_only" if reasons else "passed"
        correction_allowed = state == "passed" and rule["release_mode"] == "eligible_if_gate_passes"
        results[category_id] = {
            "state": state,
            "research_only": state == "research_only",
            "correction_release_allowed": correction_allowed,
            "positive": counts["positive"],
            "acceptable_control": counts["acceptable_control"],
            "protected": counts["protected"],
            "protected_false_corrections": protected_false_corrections,
            "control_false_corrections": control_false_corrections,
            "false_corrections": protected_false_corrections + control_false_corrections,
            "threshold_config_sha256": threshold_sha256,
            "reasons": reasons,
        }
    return results


def output_paths(full_root: Path, public_root: Path) -> dict[str, Path]:
    return {
        "sources": full_root / "sources.jsonl",
        "evidence": full_root / "evidence.jsonl",
        "cases": full_root / "cases.jsonl",
        "disagreements": full_root / "disagreements.jsonl",
        "public_sources": public_root / "sources.jsonl",
        "public_evidence": public_root / "evidence.jsonl",
        "public_cases": public_root / "cases.jsonl",
        "public_disagreements": public_root / "disagreements.jsonl",
    }


def logical_output_paths() -> dict[str, str]:
    return {
        "sources": "full/sources.jsonl",
        "evidence": "full/evidence.jsonl",
        "cases": "full/cases.jsonl",
        "disagreements": "full/disagreements.jsonl",
        "public_sources": "public/sources.jsonl",
        "public_evidence": "public/evidence.jsonl",
        "public_cases": "public/cases.jsonl",
        "public_disagreements": "public/disagreements.jsonl",
    }


def phase2_source(row: Mapping[str, Any]) -> dict[str, Any]:
    dimensions = row["dimensions"]
    axes = {
        "source_family": str(row["source_family"]),
        "period": str(dimensions["period"]),
        "genre": str(dimensions["genre"]),
        "register": str(dimensions["register"]),
    }
    locator_binding = row["locator_binding"]
    canonical_url = locator_binding["canonical_url"]
    locator = str(canonical_url) if canonical_url else f"phase2:{locator_binding['locator_id']}"
    publication = row["capabilities"]["derived_redistribution"]
    capability_refs = list(publication["evidence_refs"])
    if not capability_refs:
        capability_refs = [f"phase2-policy:{row['policy_binding']['decision_id']}"]
    characters = int(row["signals"]["counts"]["characters"])
    return source_row(
        record_id=str(row["record_id"]),
        work_id=str(row["work_id"]),
        source_id=str(row["source_id"]),
        revision_pin=str(row["content_sha256"]),
        locator=locator,
        content_sha256=str(row["content_sha256"]),
        axes=axes,
        decision_id=str(row["policy_binding"]["decision_id"]),
        decision_sha256=str(row["policy_binding"]["policy_sha256"]),
        capability_refs=capability_refs,
        start_offset=0,
        end_offset=characters,
        context_sha256=str(row["content_sha256"]),
        context_text=None,
        publication_state="not_permitted",
        publication_refs=capability_refs,
    )


def phase2_evidence(row: Mapping[str, Any], source: Mapping[str, Any]) -> dict[str, Any]:
    return evidence_row(
        channel="source_metadata",
        source_identity=str(row["inventory_asset_id"]),
        source_version=str(row["phase1_binding"]["manifest_sha256"]),
        locator=str(source["locator"]),
        query=None,
        query_sha256=str(row["content_sha256"]),
        status="attested",
        supports="metadata_only",
        retrieval_sha256=str(row["locator_binding"]["locator_row_sha256"]),
        parser_id="phase2-prepared-complement-v1",
        parser_version=str(row["phase1_binding"]["generator_sha256"]),
    )


def canary_source(
    *,
    config: Mapping[str, Any],
    config_sha256: str,
    category_id: str,
    role: str,
    index: int,
    item: Mapping[str, Any],
) -> tuple[dict[str, Any], int, int]:
    text = str(item["text"])
    surface = str(item["surface"])
    start_offset = text.find(surface)
    require(start_offset >= 0, f"known answer surface missing: {category_id}/{role}/{index}")
    require(text.find(surface, start_offset + 1) < 0, f"known answer surface is ambiguous: {category_id}/{role}/{index}")
    end_offset = start_offset + len(surface)
    defaults = config["defaults"]
    axes = {
        "source_family": str(item.get("source_family", defaults["source_family"])),
        "period": str(item.get("period", defaults["period"])),
        "genre": str(item.get("genre", defaults["genre"])),
        "register": str(item.get("register", defaults["register"])),
    }
    identity = sha256_text(f"{config['config_id']}:{category_id}:{role}:{index}")[:24]
    source = source_row(
        record_id=f"fixture.phase3.{identity}",
        work_id=f"work.phase3.{identity}",
        source_id=f"source.phase3.{identity}",
        revision_pin=config_sha256,
        locator=f"repo:data/projects/open_model_data/detector/correction_protection_known_answers_v1.json#{category_id}/{role}/{index}",
        content_sha256=sha256_text(text),
        axes=axes,
        decision_id="decision.phase3-project-authored-canaries",
        decision_sha256=config_sha256,
        capability_refs=["rights:project-authored-short-canaries-v1"],
        start_offset=0,
        end_offset=len(text),
        context_sha256=sha256_text(text),
        context_text=text,
        publication_state="permitted_with_evidence",
        publication_refs=["rights:project-authored-short-canaries-v1"],
    )
    return source, start_offset, end_offset


def canary_evidence(
    *,
    config: Mapping[str, Any],
    config_sha256: str,
    category_id: str,
    item: Mapping[str, Any],
    source: Mapping[str, Any],
    model_proposals: Mapping[str, Mapping[str, Any]],
) -> list[dict[str, Any]]:
    surface = str(item["surface"])
    records = [
        evidence_row(
            channel="source_metadata",
            source_identity="phase3-project-authored-known-answer",
            source_version=config_sha256,
            locator=str(source["locator"]),
            query=surface,
            query_sha256=sha256_text(surface),
            status="attested",
            supports="context_only",
            retrieval_sha256=str(source["content_sha256"]),
            parser_id="phase3-known-answer-config-v1",
            parser_version=config_sha256,
        )
    ]
    for evidence in config["categories"][category_id]["evidence"]:
        query = str(item.get("evidence_key", surface))
        records.append(
            evidence_row(
                channel=str(evidence["channel"]),
                source_identity=str(evidence["source_identity"]),
                source_version=str(evidence["source_version"]),
                locator=str(evidence["locator"]),
                query=query,
                query_sha256=sha256_text(query),
                status=str(evidence["status"]),
                supports=str(evidence["supports"]),
                retrieval_sha256=sha256_text(
                    canonical_json({"source": evidence, "query_sha256": sha256_text(query)})
                ),
                parser_id="phase3-attributed-evidence-config-v1",
                parser_version=config_sha256,
            )
        )
    case_key = item.get("case_key")
    if isinstance(case_key, str) and case_key in model_proposals:
        proposal = model_proposals[case_key]
        proposal_text = str(proposal["proposal"])
        records.append(
            evidence_row(
                channel="model_proposal",
                source_identity=f"{proposal['family']}:{proposal['exact_model_id']}",
                source_version=str(proposal["raw_response_sha256"]),
                locator=f"model-lane:{proposal['task_id']}#{case_key}",
                query=str(item["surface"]),
                query_sha256=sha256_text(str(item["surface"])),
                status="ambiguous",
                supports="no_conclusion",
                retrieval_sha256=str(proposal["raw_response_sha256"]),
                parser_id="correction-protection-model-lane-v1",
                parser_version="v1",
                model_proposal={
                    "provider": proposal["provider"],
                    "family": proposal["family"],
                    "harness": proposal["harness"],
                    "exact_model_id": proposal["exact_model_id"],
                    "proposal": proposal_text,
                    "proposal_sha256": proposal["proposal_sha256"],
                    "dissent": proposal["dissent"],
                },
            )
        )
    return records


def load_model_proposals(
    path: Path | None,
    active: Mapping[Path, Draft202012Validator],
) -> tuple[dict[str, dict[str, Any]], dict[str, int]]:
    if path is None:
        return {}, {"proposal_lanes": 0, "dissent_lanes": 0}
    value = read_json(path)
    validate(value, active[MODEL_LANE_SCHEMA], "model lane evidence")
    proposals: dict[str, dict[str, Any]] = {}
    proposal_lanes = 0
    dissent_lanes = 0
    for lane in value["lanes"]:
        if not lane["gate_strengthening_allowed"]:
            continue
        qualifying = bool(lane["proposals"])
        proposal_lanes += int(qualifying)
        dissent_lanes += int(qualifying and any(str(item["dissent"]).strip() for item in lane["proposals"]))
        for proposal in lane["proposals"]:
            require(
                sha256_text(str(proposal["proposal"])) == proposal["proposal_sha256"],
                f"model proposal hash mismatch: {proposal['case_key']}",
            )
            case_key = str(proposal["case_key"])
            require(case_key not in proposals, f"duplicate strengthening model proposal: {case_key}")
            proposals[case_key] = {
                **proposal,
                "provider": lane["provider"],
                "family": lane["family"],
                "harness": lane["harness"],
                "exact_model_id": lane["exact_model_id"],
                "task_id": lane["task_id"],
                "raw_response_sha256": lane["raw_response_sha256"],
            }
    return proposals, {"proposal_lanes": proposal_lanes, "dissent_lanes": dissent_lanes}


def build_artifacts(
    *,
    phase2_input: Path,
    phase2_receipt_path: Path,
    thresholds_path: Path,
    known_answers_path: Path,
    full_output_root: Path,
    public_output_root: Path,
    model_evidence_path: Path | None,
) -> tuple[dict[str, Any], dict[str, Any]]:
    active = validators()
    thresholds = read_json(thresholds_path)
    known_answers = read_json(known_answers_path)
    phase2_receipt = read_json(phase2_receipt_path)
    require(tuple(known_answers["categories"]) == CATEGORY_IDS, "known-answer category order/set drifted")
    require(tuple(thresholds["categories"]) == CATEGORY_IDS, "threshold category order/set drifted")
    expected_phase2 = phase2_receipt["outputs"]["complement"]
    require(sha256_file(phase2_input) == expected_phase2["sha256"], "Phase 2 complement hash mismatch")
    if model_evidence_path is not None:
        require(model_evidence_path.is_file(), f"missing model evidence: {model_evidence_path}")
    model_proposals, model_gate_counts = load_model_proposals(model_evidence_path, active)
    expected_model_keys = {
        str(item["case_key"])
        for item in known_answers["categories"]["contextual_calque_government_valency"]["positive"]
    }
    if expected_model_keys != set(model_proposals):
        model_gate_counts = {"proposal_lanes": 0, "dissent_lanes": 0}
    gates = gate_results(
        known_answers,
        thresholds,
        model_proposal_lanes=model_gate_counts["proposal_lanes"],
        model_dissent_lanes=model_gate_counts["dissent_lanes"],
    )

    from scripts.projects.open_model_data import correction_factory as evaluation

    evaluation_registry = evaluation.load_evaluation_registry()
    evaluation_texts = evaluation_registry.v011_texts + evaluation_registry.v02_texts
    exact_matches = 0
    near_matches = 0
    for specification in known_answers["categories"].values():
        for role in ("positive", "acceptable_control", "protected"):
            for item in specification.get(role, []):
                text = str(item["text"])
                exact = sha256_text(text) in (evaluation_registry.v011_exact | evaluation_registry.v02_exact)
                near = evaluation._near_duplicate(text, evaluation_texts)
                exact_matches += int(exact)
                near_matches += int(near and not exact)
    require(exact_matches == 0 and near_matches == 0, "public known answers overlap evaluation sources")

    paths = output_paths(full_output_root, public_output_root)
    writers = {name: JsonlWriter.open(path) for name, path in paths.items()}
    counters: dict[str, Counter[str]] = {
        "category": Counter(),
        "role": Counter(),
        "disposition": Counter(),
        "evidence_grade": Counter(),
        "source_family": Counter(),
        "period": Counter(),
        "genre": Counter(),
        "register": Counter(),
    }
    try:
        for line_number, row in iter_jsonl(phase2_input):
            validate(row, active[PHASE2_SCHEMA], f"Phase 2 row {line_number}")
            source = phase2_source(row)
            validate(source, active[SOURCE_SCHEMA], f"source row {line_number}")
            source_sha = writers["sources"].write(source)
            evidence = phase2_evidence(row, source)
            validate(evidence, active[EVIDENCE_SCHEMA], f"evidence row {line_number}")
            writers["evidence"].write(evidence)
            category_id, disposition = phase2_route(row)
            case = case_row(
                source=source,
                source_sha256=source_sha,
                start_offset=0,
                end_offset=int(row["signals"]["counts"]["characters"]),
                surface_sha256=str(row["content_sha256"]),
                category_id=category_id,
                phenomenon="Source-blind Phase 2 stand-off candidate; no span-level linguistic claim",
                benchmark_role="full_corpus_candidate",
                gate=gates[category_id],
                evidence=[evidence],
                disposition=disposition,
            )
            validate(case, active[CASE_SCHEMA], f"case row {line_number}")
            writers["cases"].write(case)
            counters["category"][category_id] += 1
            counters["role"]["full_corpus_candidate"] += 1
            counters["disposition"][disposition] += 1
            counters["evidence_grade"][case["evidence_grade"]] += 1
            for axis in ("source_family", "period", "genre", "register"):
                counters[axis][source["source_axes"][axis]] += 1

        config_sha256 = sha256_file(known_answers_path)
        for category_id in CATEGORY_IDS:
            specification = known_answers["categories"][category_id]
            for role in ("positive", "acceptable_control", "protected"):
                for index, item in enumerate(specification.get(role, [])):
                    source, start_offset, end_offset = canary_source(
                        config=known_answers,
                        config_sha256=config_sha256,
                        category_id=category_id,
                        role=role,
                        index=index,
                        item=item,
                    )
                    validate(source, active[SOURCE_SCHEMA], f"public source {category_id}/{role}/{index}")
                    source_sha = writers["sources"].write(source)
                    writers["public_sources"].write(source)
                    evidence = canary_evidence(
                        config=known_answers,
                        config_sha256=config_sha256,
                        category_id=category_id,
                        item=item,
                        source=source,
                        model_proposals=model_proposals,
                    )
                    for evidence_row_value in evidence:
                        validate(evidence_row_value, active[EVIDENCE_SCHEMA], f"public evidence {category_id}/{role}/{index}")
                        writers["evidence"].write(evidence_row_value)
                        writers["public_evidence"].write(evidence_row_value)
                    disposition = known_answer_disposition(
                        role=role,
                        category_id=category_id,
                        rule=thresholds["categories"][category_id],
                        correction_release_allowed=gates[category_id]["correction_release_allowed"],
                    )
                    replacement = str(item["replacement"]) if disposition == "correction" else None
                    case = case_row(
                        source=source,
                        source_sha256=source_sha,
                        start_offset=start_offset,
                        end_offset=end_offset,
                        surface_sha256=sha256_text(str(item["surface"])),
                        category_id=category_id,
                        phenomenon=str(specification["phenomenon"]),
                        benchmark_role="protected_example" if role == "protected" else role,
                        gate=gates[category_id],
                        evidence=evidence,
                        disposition=disposition,
                        replacement=replacement,
                    )
                    model_rows = [row for row in evidence if row["channel"] == "model_proposal"]
                    if model_rows:
                        model_row = model_rows[0]
                        model = model_row["model_proposal"]
                        disagreement_payload = {
                            "case_id": case["case_id"],
                            "proposal_sha256": model["proposal_sha256"],
                            "dissent": model["dissent"],
                        }
                        disagreement_id = stable_id("cp_disagreement", disagreement_payload)
                        disagreement = {
                            "schema_version": "correction_protection_disagreement_v1",
                            "disagreement_id": disagreement_id,
                            "case_id": case["case_id"],
                            "proposals": [
                                {
                                    "provider": model["provider"],
                                    "family": model["family"],
                                    "harness": model["harness"],
                                    "exact_model_id": model["exact_model_id"],
                                    "proposal": model["proposal"],
                                    "proposal_sha256": model["proposal_sha256"],
                                    "evidence_refs": [str(row["evidence_id"]) for row in evidence],
                                    "dissent": model["dissent"],
                                }
                            ],
                            "evidence_refs": [str(row["evidence_id"]) for row in evidence],
                            "challenge": "Source-constrained model proposal with explicit alternatives; exact rewrite remains non-gold and reversible.",
                            "consensus": {
                                "state": "model_only",
                                "human_reviewed": False,
                                "human_gold": False,
                                "authoritative": False,
                            },
                            "claim_boundary": {
                                "assurance_tier": "evidence_graded_non_gold",
                                "authoritative": False,
                            },
                        }
                        validate(disagreement, active[DISAGREEMENT_SCHEMA], f"disagreement {category_id}/{role}/{index}")
                        writers["disagreements"].write(disagreement)
                        writers["public_disagreements"].write(disagreement)
                        case["disagreement_refs"] = [disagreement_id]
                    validate(case, active[CASE_SCHEMA], f"public case {category_id}/{role}/{index}")
                    writers["cases"].write(case)
                    writers["public_cases"].write(case)
                    counters["category"][category_id] += 1
                    counters["role"]["protected_example" if role == "protected" else role] += 1
                    counters["disposition"][disposition] += 1
                    counters["evidence_grade"][case["evidence_grade"]] += 1
                    for axis in ("source_family", "period", "genre", "register"):
                        counters[axis][source["source_axes"][axis]] += 1

        # Model evidence is bound as input in this slice; disagreement records are
        # emitted only after the exact proposal/dissent contract is validated.
        output_metadata = {name: writer.finish() for name, writer in writers.items()}
    except Exception:
        for writer in writers.values():
            writer.abort()
        raise

    for name, metadata in output_metadata.items():
        metadata["logical_path"] = logical_output_paths()[name]
    index = {
        "schema_version": "correction_protection_build_index_v1",
        "inputs": {
            "phase2_complement": artifact(phase2_input, logical_path="phase2/complement.jsonl"),
            "phase2_receipt": artifact(phase2_receipt_path, logical_path="phase2/receipt.json"),
            "thresholds": artifact(thresholds_path, logical_path=thresholds_path.relative_to(ROOT).as_posix()),
            "known_answers": artifact(known_answers_path, logical_path=known_answers_path.relative_to(ROOT).as_posix()),
            **(
                {"model_evidence": artifact(model_evidence_path, logical_path="private/model-evidence.json")}
                if model_evidence_path is not None
                else {}
            ),
        },
        "outputs": output_metadata,
        "counts": {name: dict(sorted(counter.items())) for name, counter in counters.items()},
        "category_gates": gates,
        "evaluation_firewall": {
            "exact_matches": exact_matches,
            "near_matches": near_matches,
            "v011_manifest_sha256": evaluation_registry.v011_manifest_sha256,
            "v02_packet_sha256": evaluation_registry.v02_packet_sha256,
        },
    }
    return index, {name: writer.temporary for name, writer in writers.items()}


def compact_release_gate(gate: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "state": gate["state"],
        "research_only": gate["research_only"],
        "correction_release_allowed": gate["correction_release_allowed"],
        "positive": gate["positive"],
        "acceptable_control": gate["acceptable_control"],
        "protected": gate["protected"],
        "protected_false_corrections": gate["protected_false_corrections"],
        "control_false_corrections": gate["control_false_corrections"],
        "false_corrections": gate["false_corrections"],
        "threshold_config_sha256": gate["threshold_config_sha256"],
        "reasons": gate["reasons"],
    }


def release_artifact(value: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "logical_path": value["logical_path"],
        "records": value["records"],
        "sha256": value["sha256"],
    }


def build_manifest_and_receipt(
    *,
    index: Mapping[str, Any],
    candidate_index_path: Path,
    second_index_path: Path,
    manifest_path: Path,
    receipt_path: Path,
    full_output_root: Path,
    candidate_full_root: Path,
) -> tuple[dict[str, Any], dict[str, Any]]:
    candidate_index = read_json(candidate_index_path)
    require(candidate_index["outputs"] == index["outputs"], "independent build output hashes differ")
    require(candidate_index["counts"] == index["counts"], "independent build counts differ")
    require(candidate_index["category_gates"] == index["category_gates"], "independent gate results differ")
    require(candidate_full_root.resolve() != full_output_root.resolve(), "comparison output roots must be distinct")

    candidate_index_artifact = artifact(candidate_index_path, logical_path="first/build-index.json")
    second_index_artifact = artifact(second_index_path, logical_path="second/build-index.json")
    bundle_payload = {
        "inputs": index["inputs"],
        "outputs": index["outputs"],
        "counts": index["counts"],
        "category_gates": index["category_gates"],
    }
    manifest = {
        "schema_version": "correction_protection_bundle_manifest_v1",
        "bundle_id": stable_id("cp_bundle", bundle_payload),
        "inputs": index["inputs"],
        "outputs": index["outputs"],
        "record_counts": {name: int(value["records"]) for name, value in index["outputs"].items()},
        "category_counts": index["counts"]["category"],
        "role_counts": index["counts"]["role"],
        "disposition_counts": index["counts"]["disposition"],
        "category_gates": {
            category: {
                key: value
                for key, value in gate.items()
                if key
                in {
                    "state",
                    "correction_release_allowed",
                    "positive",
                    "acceptable_control",
                    "protected",
                    "protected_false_corrections",
                    "control_false_corrections",
                    "false_corrections",
                    "threshold_config_sha256",
                    "reasons",
                }
            }
            for category, gate in index["category_gates"].items()
        },
        "public_known_answers": {
            "records": int(index["outputs"]["public_cases"]["records"]),
            "learning_eligible": False,
            "held_back_equivalent": False,
            "source_text_rights": "project_authored_short_canaries",
        },
        "evaluation_firewall": {
            "registry_artifacts": {
                path.name: artifact(path, logical_path=path.relative_to(ROOT).as_posix())
                for path in DEFAULT_EVAL_ARTIFACTS
            },
            "exact_matches": int(index["evaluation_firewall"]["exact_matches"]),
            "near_matches": int(index["evaluation_firewall"]["near_matches"]),
            "learning_exports_created": False,
        },
        "two_build_identity": {
            "comparison_algorithm": "independent-bundle-artifact-sha256-v1",
            "first_manifest": candidate_index_artifact,
            "second_manifest": second_index_artifact,
            "artifact_hashes_identical": True,
            "distinct_output_roots": True,
        },
        "consumer_decisions": [
            "flag a passed evidence-backed correction proposal",
            "protect source-conditioned Ukrainian or quoted language from normalization",
            "filter or abstain when only source metadata or disputed evidence is available",
            "measure non-erasure on public known answers without admitting them to learning exports",
            "align a locally controlled source by revision-pinned stand-off locator and offsets",
        ],
        "claim_boundary": {
            "assurance_tier": "evidence_graded_non_gold",
            "authoritative": False,
            "human_gold": False,
            "human_reviewed": False,
            "project_model_training_performed": False,
            "local_model_inference_performed": False,
            "external_advisory_model_evidence_used": "model_evidence" in index["inputs"],
            "upload_performed": False,
        },
    }
    active = validators()
    validate(manifest, active[BUNDLE_SCHEMA], "bundle manifest")

    manifest_bytes = (canonical_json(manifest) + "\n").encode("utf-8")
    manifest_logical_path = (
        manifest_path.relative_to(ROOT).as_posix()
        if manifest_path.is_absolute() and manifest_path.is_relative_to(ROOT)
        else manifest_path.as_posix()
    )
    manifest_artifact = {
        "logical_path": manifest_logical_path,
        "records": 1,
        "sha256": sha256_bytes(manifest_bytes),
    }
    receipt = {
        "schema_version": "correction_protection_release_receipt_v1",
        "inputs": {name: release_artifact(value) for name, value in index["inputs"].items()},
        "schemas": {
            path.name: sha256_file(path)
            for path in (
                SOURCE_SCHEMA,
                EVIDENCE_SCHEMA,
                CASE_SCHEMA,
                DISAGREEMENT_SCHEMA,
                BUNDLE_SCHEMA,
                MODEL_LANE_SCHEMA,
                RELEASE_SCHEMA,
            )
        },
        "config": {
            "thresholds": index["inputs"]["thresholds"]["sha256"],
            "known_answers": index["inputs"]["known_answers"]["sha256"],
        },
        "output": manifest_artifact,
        "counts": {
            "source_records": int(index["outputs"]["sources"]["records"]),
            "evidence_records": int(index["outputs"]["evidence"]["records"]),
            "case_records": int(index["outputs"]["cases"]["records"]),
            "public_known_answers": int(index["outputs"]["public_cases"]["records"]),
        },
        "category_gates": {
            category: compact_release_gate(gate) for category, gate in index["category_gates"].items()
        },
        "axes_coverage": {
            axis: index["counts"][axis] for axis in ("source_family", "period", "genre", "register")
        },
        "dispositions": {
            disposition: int(index["counts"]["disposition"].get(disposition, 0))
            for disposition in ("correct", "correction", "protected", "excluded", "unresolved")
        },
        "evidence_grades": index["counts"]["evidence_grade"],
        "disagreement": release_artifact(index["outputs"]["disagreements"]),
        "rights_and_publication": {
            "rights_decision_refs": ["phase2:prepared-data-complement-receipt-v1"],
            "publication_decision_refs": ["rights:project-authored-short-canaries-v1", "phase2:metadata-only"],
            "raw_payloads_published": False,
        },
        "contamination_registry": release_artifact(
            artifact(
                ROOT / "data/projects/ua_eval_harness/heldout_manifest_v1.json",
                logical_path="data/projects/ua_eval_harness/heldout_manifest_v1.json",
            )
        ),
        "determinism": {
            "algorithm": "phase2-input-order-plus-category-role-index-canonical-json-v1",
            "algorithm_sha256": sha256_text("phase2-input-order-plus-category-role-index-canonical-json-v1"),
            "serialization": "UTF-8 canonical JSON with sorted keys and LF",
            "timestamps_omitted": True,
        },
        "held_back_strategy": {
            "locator": "batch_state/issue-6333/heldback/phase3-v1",
            "public_repo_copy": False,
        },
        "safety": {
            "project_model_training": False,
            "local_model_inference": False,
            "external_advisory_model_evidence_used": "model_evidence" in index["inputs"],
            "upload": False,
            "accelerator": False,
            "human_gold": False,
            "authoritative": False,
        },
    }
    validate(receipt, active[RELEASE_SCHEMA], "release receipt")
    return manifest, receipt


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("candidate", "build"))
    parser.add_argument("--phase2-input", type=Path, required=True)
    parser.add_argument("--phase2-receipt", type=Path, default=DEFAULT_PHASE2_RECEIPT)
    parser.add_argument("--thresholds", type=Path, default=DEFAULT_THRESHOLDS)
    parser.add_argument("--known-answers", type=Path, default=DEFAULT_KNOWN_ANSWERS)
    parser.add_argument("--full-output-dir", type=Path, required=True)
    parser.add_argument("--public-output-dir", type=Path, required=True)
    parser.add_argument("--index-output", type=Path, required=True)
    parser.add_argument("--model-evidence", type=Path)
    parser.add_argument("--comparison-index", type=Path)
    parser.add_argument("--comparison-full-output-dir", type=Path)
    parser.add_argument("--manifest-output", type=Path)
    parser.add_argument("--receipt-output", type=Path)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if args.mode == "build":
        require(args.comparison_index is not None, "build requires --comparison-index")
        require(args.comparison_full_output_dir is not None, "build requires --comparison-full-output-dir")
        require(args.manifest_output is not None, "build requires --manifest-output")
        require(args.receipt_output is not None, "build requires --receipt-output")
    else:
        require(args.comparison_index is None, "candidate cannot accept --comparison-index")
        require(args.manifest_output is None and args.receipt_output is None, "candidate cannot release")

    index, temporary_outputs = build_artifacts(
        phase2_input=args.phase2_input,
        phase2_receipt_path=args.phase2_receipt,
        thresholds_path=args.thresholds,
        known_answers_path=args.known_answers,
        full_output_root=args.full_output_dir,
        public_output_root=args.public_output_dir,
        model_evidence_path=args.model_evidence,
    )
    staged: list[tuple[Path, Path]] = [
        (temporary_outputs[name], destination)
        for name, destination in output_paths(args.full_output_dir, args.public_output_dir).items()
    ]
    index_temporary = staged_json(args.index_output, index)
    staged.append((index_temporary, args.index_output))
    try:
        if args.mode == "build":
            # The second index must exist for its own artifact hash, so promote
            # the byte-complete data/index before creating the release metadata.
            promote(staged)
            staged = []
            manifest, receipt = build_manifest_and_receipt(
                index=index,
                candidate_index_path=args.comparison_index,
                second_index_path=args.index_output,
                manifest_path=args.manifest_output,
                receipt_path=args.receipt_output,
                full_output_root=args.full_output_dir,
                candidate_full_root=args.comparison_full_output_dir,
            )
            manifest_temporary = staged_json(args.manifest_output, manifest)
            receipt_temporary = staged_json(args.receipt_output, receipt)
            promote(
                [
                    (manifest_temporary, args.manifest_output),
                    (receipt_temporary, args.receipt_output),
                ]
            )
        else:
            promote(staged)
            staged = []
    finally:
        for temporary, _destination in staged:
            temporary.unlink(missing_ok=True)


if __name__ == "__main__":
    main()
