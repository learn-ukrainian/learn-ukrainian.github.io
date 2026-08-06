#!/usr/bin/env python3
"""Deterministic, text-free Phase 3 lexical coverage mechanics.

This module deliberately has no language classifier.  It reopens frozen source
inputs only to reproduce opaque identities and checks a *typed*, closed release
manifest.  Consequently it can prove structural and population mechanics, but
cannot assert ``SOURCE_COVERAGE_READY`` or make an attestation decision.
"""

from __future__ import annotations

import hashlib
import json
from collections import Counter
from collections.abc import Iterable, Mapping, Sequence
from pathlib import Path
from typing import Any

from scripts.projects.open_model_data import phase3_source_universe as universe
from scripts.projects.open_model_data import verify_phase3_source_universe_freeze as freeze

ROOT = Path(__file__).resolve().parents[3]
DATA = ROOT / "data/projects/open_model_data"
DEFAULT_SOURCE_UNIVERSE = DATA / "evidence/source_universe_v1"
ASSIGNED_DISPOSITION_AUDITOR = "controller_phase3_disposition_auditor_claude_01"
LEXICAL_FAMILIES = frozenset(freeze.LEXICAL_FAMILIES)
SHA256_LENGTH = 64
IMPLEMENTATION_PATH = "scripts/projects/open_model_data/phase3_lexical_coverage.py"


class LexicalCoverageError(ValueError):
    """A lexical coverage mechanism receipt is malformed or stale."""


def require(condition: bool, message: str) -> None:
    if not condition:
        raise LexicalCoverageError(message)


def canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def sha256_value(value: Any) -> str:
    return hashlib.sha256(canonical_json(value).encode("utf-8")).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    try:
        with path.open("rb") as handle:
            for chunk in iter(lambda: handle.read(1024 * 1024), b""):
                digest.update(chunk)
    except OSError as exc:
        raise LexicalCoverageError(f"cannot read artifact: {path}") from exc
    return digest.hexdigest()


def implementation_sha256() -> str:
    """Bind receipts to the exact deterministic mechanics being executed."""
    return sha256_file(ROOT / IMPLEMENTATION_PATH)


def _sha(value: object, label: str) -> str:
    require(
        isinstance(value, str) and len(value) == SHA256_LENGTH and all(char in "0123456789abcdef" for char in value),
        f"invalid SHA-256: {label}",
    )
    return value


def _exact(value: Mapping[str, Any], fields: set[str], label: str) -> None:
    require(set(value) == fields, f"unexpected {label} shape")


def _text_free(value: object, label: str = "artifact") -> None:
    forbidden = {"text", "source_text", "content", "definition", "sentence", "excerpt", "quote", "lemma", "form"}
    if isinstance(value, Mapping):
        for key, item in value.items():
            require(isinstance(key, str) and key not in forbidden, f"source-bearing field is forbidden: {label}")
            _text_free(item, label)
    elif isinstance(value, list):
        for item in value:
            _text_free(item, label)
    elif isinstance(value, str):
        require("\n" not in value and "\r" not in value, f"multiline value is forbidden: {label}")


def _read_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise LexicalCoverageError(f"cannot read JSON artifact: {path}") from exc
    require(isinstance(value, dict), f"JSON artifact must be an object: {path}")
    return value


def _lexical_contract_families(coverage_contract: Mapping[str, Any]) -> dict[str, Mapping[str, Any]]:
    families = coverage_contract.get("mandatory_families")
    require(isinstance(families, list), "coverage contract lacks mandatory families")
    result: dict[str, Mapping[str, Any]] = {}
    for family in families:
        require(isinstance(family, Mapping) and isinstance(family.get("family_id"), str), "invalid coverage family")
        if family.get("coverage_mode") == "lexical_structural_and_used_subset":
            result[str(family["family_id"])] = family
    require(set(result) == LEXICAL_FAMILIES, "coverage contract lexical family set mismatch")
    return result


def _assigned_auditor(role_contract: Mapping[str, Any]) -> str:
    seats = role_contract.get("seats")
    root = role_contract.get("root")
    require(isinstance(seats, list) and isinstance(root, Mapping), "role contract lacks seats or root")
    assigned = [seat for seat in seats if isinstance(seat, Mapping) and seat.get("role_id") == "disposition_auditor"]
    require(len(assigned) == 1, "role contract must name exactly one disposition auditor")
    auditor = assigned[0]
    require(
        auditor.get("assignment_state") == "assigned_verified" and auditor.get("controller_identity_attested") is True,
        "disposition auditor is not assigned and attested",
    )
    require(auditor.get("controller_identity_id") == ASSIGNED_DISPOSITION_AUDITOR, "wrong assigned disposition auditor")
    forbidden = {root.get("controller_identity_id")}
    forbidden.update(
        seat.get("controller_identity_id")
        for seat in seats
        if isinstance(seat, Mapping) and seat.get("role_id") == "rule_author_extractor"
    )
    require(ASSIGNED_DISPOSITION_AUDITOR not in forbidden, "root or rule author cannot attest lexical audit")
    return ASSIGNED_DISPOSITION_AUDITOR


def _rolling_update(digest: Any, value: Mapping[str, Any]) -> None:
    encoded = canonical_json(value).encode("utf-8")
    digest.update(len(encoded).to_bytes(8, "big"))
    digest.update(encoded)


def _structural_summary(family_id: str, units: Iterable[Mapping[str, Any]]) -> dict[str, Any]:
    """Reproduce the freezer binding hash while retaining only aggregate state."""
    rolling = hashlib.sha256()
    duplicate_rolling = hashlib.sha256()
    count = 0
    parse_counts: Counter[str] = Counter()
    provenance: dict[str, Any] | None = None
    for unit in units:
        binding = {
            "unit_id": unit["unit_id"],
            "unit_sha256": unit["unit_sha256"],
            "duplicate_group_id": unit["duplicate_group_id"],
            "parse_status": unit["parse_status"],
            "provenance": unit["provenance"],
        }
        _rolling_update(rolling, binding)
        _rolling_update(
            duplicate_rolling, {"unit_id": unit["unit_id"], "duplicate_group_id": unit["duplicate_group_id"]}
        )
        current = dict(unit["provenance"])
        if provenance is None:
            provenance = current
        else:
            require(provenance == current, f"lexical provenance drift: {family_id}")
        parse_counts[str(unit["parse_status"])] += 1
        count += 1
    require(provenance is not None, f"lexical family has no units: {family_id}")
    return {
        "family_id": family_id,
        "unit_count": count,
        "ordered_rolling_sha256": rolling.hexdigest(),
        "duplicate_group_observation_total": count,
        "duplicate_group_rolling_sha256": duplicate_rolling.hexdigest(),
        "parse_status_counts": dict(sorted(parse_counts.items())),
        "provenance": provenance,
    }


def reopen_structural_universe(
    *, coverage_contract: Mapping[str, Any], sources_db: Path, vesum_db: Path, r2u_cache: Path
) -> list[dict[str, Any]]:
    """Stream the thirteen frozen lexical families using the freezer enumerators.

    The source freezer owns identity formation.  This function intentionally
    calls those exact enumerators instead of recreating row, VESUM, or R2U IDs.
    """
    families = _lexical_contract_families(coverage_contract)
    source_hash, vesum_hash = universe.sha256_file(sources_db), universe.sha256_file(vesum_db)
    source_db = universe._connect(sources_db)
    vesum: Any | None = None
    try:
        vesum = universe._connect(vesum_db)
        streams: list[tuple[str, Iterable[Mapping[str, Any]]]] = []
        for family_id, table in universe.SOURCES_FAMILIES.items():
            if family_id in LEXICAL_FAMILIES:
                streams.append(
                    (family_id, universe._database_units(source_db, table, family_id, families[family_id], source_hash))
                )
        streams.append(
            (
                "lexical_vesum",
                universe._database_units(vesum, "forms", "lexical_vesum", families["lexical_vesum"], vesum_hash),
            )
        )
        streams.append(("lexical_r2u", universe._r2u_units(r2u_cache, families["lexical_r2u"])))
        summaries = [_structural_summary(family_id, stream) for family_id, stream in streams]
        require({item["family_id"] for item in summaries} == LEXICAL_FAMILIES, "reopened lexical family set mismatch")
        for summary in summaries:
            expected = families[summary["family_id"]].get("input_identity", {}).get("observed_input_total")
            require(summary["unit_count"] == expected, f"reopened lexical count mismatch: {summary['family_id']}")
        return sorted(summaries, key=lambda item: item["family_id"])
    finally:
        source_db.close()
        if vesum is not None:
            vesum.close()


def _source_bindings(source_universe_dir: Path) -> tuple[dict[str, Any], str, dict[str, Any], str]:
    freeze.validate(source_universe_dir, repo_root=ROOT)
    receipt_path = source_universe_dir / freeze.RECEIPT_FILE
    structural_path = source_universe_dir / freeze.STRUCTURAL_FILE
    receipt, structural = _read_json(receipt_path), _read_json(structural_path)
    return receipt, sha256_file(receipt_path), structural, sha256_file(structural_path)


def validate_structural_audit(
    receipt: Mapping[str, Any],
    *,
    source_universe_dir: Path = DEFAULT_SOURCE_UNIVERSE,
    coverage_contract: Mapping[str, Any],
    role_contract: Mapping[str, Any],
    sources_db: Path,
    vesum_db: Path,
    r2u_cache: Path,
) -> dict[str, Any]:
    """Validate an independent, complete reopening audit; never assign readiness."""
    _text_free(receipt, "lexical structural audit")
    _exact(
        receipt,
        {
            "schema_version",
            "text_free",
            "source_universe_receipt_sha256",
            "source_universe_payload_manifest_sha256",
            "lexical_structural_freeze_sha256",
            "coverage_contract_sha256",
            "role_contract_sha256",
            "implementation_sha256",
            "repair_generation",
            "auditor_controller_identity_id",
            "families",
        },
        "lexical structural audit",
    )
    require(
        receipt["schema_version"] == "phase3_lexical_structural_audit_v1" and receipt["text_free"] is True,
        "invalid lexical structural audit header",
    )
    require(
        isinstance(receipt["repair_generation"], int) and receipt["repair_generation"] >= 0, "invalid repair generation"
    )
    require(
        receipt["auditor_controller_identity_id"] == _assigned_auditor(role_contract),
        "structural audit identity is not the assigned auditor",
    )
    source_receipt, source_hash, frozen, frozen_hash = _source_bindings(source_universe_dir)
    require(receipt["source_universe_receipt_sha256"] == source_hash, "stale source freeze receipt")
    require(
        receipt["source_universe_payload_manifest_sha256"]
        == source_receipt["artifact_manifest"]["payload_manifest_sha256"],
        "stale source payload manifest",
    )
    require(receipt["lexical_structural_freeze_sha256"] == frozen_hash, "stale lexical structural freeze")
    require(receipt["coverage_contract_sha256"] == sha256_value(coverage_contract), "stale coverage contract")
    require(receipt["role_contract_sha256"] == sha256_value(role_contract), "stale role contract")
    require(receipt["implementation_sha256"] == implementation_sha256(), "stale lexical coverage implementation")
    frozen_summaries = {item["family_id"]: item for item in frozen.get("families", [])}
    reopened = {
        item["family_id"]: item
        for item in reopen_structural_universe(
            coverage_contract=coverage_contract, sources_db=sources_db, vesum_db=vesum_db, r2u_cache=r2u_cache
        )
    }
    observed: dict[str, Mapping[str, Any]] = {}
    for family in receipt["families"]:
        require(isinstance(family, Mapping), "structural audit family must be an object")
        _exact(
            family,
            {
                "family_id",
                "unit_count",
                "ordered_rolling_sha256",
                "duplicate_group_observation_total",
                "duplicate_group_rolling_sha256",
                "parse_status_counts",
                "provenance",
            },
            "structural audit family",
        )
        family_id = family.get("family_id")
        require(
            isinstance(family_id, str) and family_id in LEXICAL_FAMILIES and family_id not in observed,
            "unknown or duplicate structural audit family",
        )
        observed[family_id] = family
        for name in (
            "unit_count",
            "ordered_rolling_sha256",
            "duplicate_group_observation_total",
            "duplicate_group_rolling_sha256",
            "parse_status_counts",
            "provenance",
        ):
            require(family[name] == reopened[family_id][name], f"reopened lexical {name} mismatch: {family_id}")
        require(
            family["ordered_rolling_sha256"] == frozen_summaries[family_id]["ordered_rolling_sha256"],
            f"frozen lexical identity mismatch: {family_id}",
        )
        require(
            family["unit_count"] == frozen_summaries[family_id]["unit_count"],
            f"frozen lexical count mismatch: {family_id}",
        )
    require(
        set(observed) == LEXICAL_FAMILIES == set(frozen_summaries) == set(reopened),
        "complete thirteen-family structural audit required",
    )
    return {
        "ok": True,
        "structural_audit_verified": True,
        "family_count": len(observed),
        "status": "STRUCTURAL_MECHANICS_ONLY_NOT_SOURCE_COVERAGE_READY",
    }


def _pointer_token(value: str) -> str:
    return value.replace("~", "~0").replace("/", "~1")


def _generic_lexical_use(value: Mapping[str, Any]) -> bool:
    """Recognize legacy/generic lexical locators that must be typed exactly."""
    channel = value.get("channel")
    if isinstance(channel, str) and channel.casefold() in {"r2u", "vesum"}:
        return True
    for key, item in value.items():
        if (
            isinstance(key, str)
            and key in {"family_id", "lexical_family_id", "lexical_source_family"}
            and isinstance(item, str)
            and item in LEXICAL_FAMILIES
        ):
            return True
        if isinstance(item, str) and ("data/vesum.db" in item or "r2u-cache" in item or "r2u_cache" in item):
            return True
    return False


def _typed_envelope(
    value: Mapping[str, Any],
    *,
    artifact: Mapping[str, Any],
    pointer: str,
    line: int | None,
) -> dict[str, Any]:
    _exact(value, {"family_id", "unit_id", "unit_sha256"}, "embedded lexical unit reference")
    anchor = {"json_pointer": pointer, "jsonl_line": line}
    return _validate_typed_reference(
        {
            "family_id": value["family_id"],
            "unit_id": value["unit_id"],
            "unit_sha256": value["unit_sha256"],
            "evidence_locator": {
                "kind": "release_artifact_immutable_locator",
                "artifact_id": artifact["artifact_id"],
                "artifact_sha256": artifact["sha256"],
                "path": artifact["path"],
                "anchor_sha256": sha256_value(anchor),
            },
        },
        files={artifact["artifact_id"]: artifact},
    )


def _scan_release_value(
    value: object,
    *,
    artifact: Mapping[str, Any],
    pointer: str,
    line: int | None,
    results: list[dict[str, Any]],
) -> None:
    if isinstance(value, Mapping):
        envelope = value.get("lexical_unit_reference")
        if envelope is not None:
            require(isinstance(envelope, Mapping), "embedded lexical unit reference must be an object")
            results.append(
                _typed_envelope(envelope, artifact=artifact, pointer=f"{pointer}/lexical_unit_reference", line=line)
            )
        elif _generic_lexical_use(value):
            raise LexicalCoverageError("generic lexical use lacks an exact typed unit reference")
        for key, item in value.items():
            if key != "lexical_unit_reference":
                _scan_release_value(
                    item, artifact=artifact, pointer=f"{pointer}/{_pointer_token(str(key))}", line=line, results=results
                )
    elif isinstance(value, list):
        for index, item in enumerate(value):
            _scan_release_value(item, artifact=artifact, pointer=f"{pointer}/{index}", line=line, results=results)
    elif isinstance(value, str) and ("data/vesum.db" in value or "r2u-cache" in value or "r2u_cache" in value):
        raise LexicalCoverageError("generic lexical locator lacks an exact typed unit reference")


def extract_typed_lexical_references(files: Sequence[Mapping[str, Any]], *, release_root: Path) -> list[dict[str, Any]]:
    """Deterministically scan every closed release JSON/JSONL artifact before audit."""
    results: list[dict[str, Any]] = []
    for artifact in files:
        path = release_root / str(artifact["path"])
        suffix = path.suffix.casefold()
        require(suffix in {".json", ".jsonl"}, f"release artifact is not JSON or JSONL: {path.name}")
        try:
            if suffix == ".json":
                _scan_release_value(
                    json.loads(path.read_text(encoding="utf-8")),
                    artifact=artifact,
                    pointer="",
                    line=None,
                    results=results,
                )
            else:
                with path.open(encoding="utf-8") as handle:
                    for line_number, raw in enumerate(handle, start=1):
                        require(raw.endswith("\n"), f"JSONL release row lacks newline: {path.name}:{line_number}")
                        _scan_release_value(
                            json.loads(raw), artifact=artifact, pointer="", line=line_number, results=results
                        )
        except (OSError, json.JSONDecodeError) as exc:
            raise LexicalCoverageError(f"cannot parse closed release artifact: {path.name}") from exc
    keys = [
        (
            item["family_id"],
            item["unit_id"],
            item["evidence_locator"]["artifact_id"],
            item["evidence_locator"]["anchor_sha256"],
        )
        for item in results
    ]
    require(len(keys) == len(set(keys)), "duplicate embedded lexical reference")
    return sorted(
        results,
        key=lambda item: (
            item["family_id"],
            item["unit_id"],
            item["evidence_locator"]["artifact_id"],
            item["evidence_locator"]["anchor_sha256"],
        ),
    )


def _validate_release_manifest(manifest: Mapping[str, Any], *, release_root: Path) -> tuple[str, list[dict[str, Any]]]:
    _text_free(manifest, "release manifest")
    _exact(
        manifest,
        {"schema_version", "text_free", "release_files", "release_artifact_manifest_sha256"},
        "release manifest",
    )
    require(
        manifest["schema_version"] == "phase3_lexical_release_manifest_v1" and manifest["text_free"] is True,
        "invalid release manifest header",
    )
    base = {key: value for key, value in manifest.items() if key != "release_artifact_manifest_sha256"}
    require(manifest["release_artifact_manifest_sha256"] == sha256_value(base), "release manifest hash mismatch")
    files = manifest["release_files"]
    require(isinstance(files, list), "release manifest release-files array required")
    file_ids: set[str] = set()
    expected_paths: set[str] = set()
    for item in files:
        require(isinstance(item, Mapping), "release file must be an object")
        _exact(item, {"artifact_id", "path", "sha256"}, "release file")
        artifact_id, path = item["artifact_id"], item["path"]
        require(
            isinstance(artifact_id, str) and artifact_id and artifact_id not in file_ids,
            "duplicate or invalid release artifact id",
        )
        require(
            isinstance(path, str)
            and path
            and not Path(path).is_absolute()
            and ".." not in Path(path).parts
            and path not in expected_paths,
            "unsafe or duplicate release file path",
        )
        _sha(item["sha256"], "release file")
        actual = release_root / path
        require(
            actual.is_file() and not actual.is_symlink() and sha256_file(actual) == item["sha256"],
            f"missing, stale, or altered release file: {path}",
        )
        file_ids.add(artifact_id)
        expected_paths.add(path)
    actual_paths = {
        path.relative_to(release_root).as_posix()
        for path in release_root.rglob("*")
        if path.is_file() and not path.is_symlink()
    }
    require(actual_paths == expected_paths, "release file closure mismatch")
    return manifest["release_artifact_manifest_sha256"], [dict(item) for item in files]


def _validate_typed_reference(
    reference: Mapping[str, Any], *, files: Mapping[str, Mapping[str, Any]]
) -> dict[str, Any]:
    _exact(reference, {"family_id", "unit_id", "unit_sha256", "evidence_locator"}, "typed lexical reference")
    family_id, unit_id = reference.get("family_id"), reference.get("unit_id")
    require(isinstance(family_id, str) and family_id in LEXICAL_FAMILIES, "unknown typed lexical family")
    suffix = unit_id.rsplit(".", 1)[-1] if isinstance(unit_id, str) else ""
    require(
        isinstance(unit_id, str)
        and unit_id.startswith(f"unit.{family_id}.")
        and len(suffix) == SHA256_LENGTH
        and all(char in "0123456789abcdef" for char in suffix),
        "generic or untyped lexical unit locator",
    )
    _sha(reference.get("unit_sha256"), "typed lexical unit hash")
    locator = reference.get("evidence_locator")
    require(isinstance(locator, Mapping), "immutable evidence locator must be an object")
    _exact(locator, {"kind", "artifact_id", "artifact_sha256", "path", "anchor_sha256"}, "immutable evidence locator")
    require(locator["kind"] == "release_artifact_immutable_locator", "generic database-only locator is forbidden")
    artifact_id = locator.get("artifact_id")
    require(isinstance(artifact_id, str) and artifact_id in files, "unresolved release artifact target")
    file = files[artifact_id]
    require(
        locator.get("artifact_sha256") == file["sha256"] and locator.get("path") == file["path"],
        "evidence locator is not bound to an immutable release artifact",
    )
    _sha(locator.get("anchor_sha256"), "release evidence anchor")
    return {
        "family_id": family_id,
        "unit_id": unit_id,
        "unit_sha256": reference["unit_sha256"],
        "evidence_locator": dict(locator),
    }


def aggregate_typed_occurrences(references: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    """Turn many release occurrences into the exact set of used lexical units."""
    grouped: dict[tuple[str, str], dict[str, Any]] = {}
    for occurrence in references:
        key = (occurrence["family_id"], occurrence["unit_id"])
        current = grouped.get(key)
        if current is None:
            grouped[key] = {
                "family_id": occurrence["family_id"],
                "unit_id": occurrence["unit_id"],
                "unit_sha256": occurrence["unit_sha256"],
                "evidence_locators": [occurrence["evidence_locator"]],
            }
        else:
            require(
                current["unit_sha256"] == occurrence["unit_sha256"], "conflicting hashes for one typed lexical unit"
            )
            current["evidence_locators"].append(occurrence["evidence_locator"])
    rows: list[dict[str, Any]] = []
    for item in grouped.values():
        locators = sorted(item["evidence_locators"], key=canonical_json)
        require(
            locators and len({canonical_json(locator) for locator in locators}) == len(locators),
            "duplicate lexical occurrence locator",
        )
        rows.append({**item, "evidence_locators": locators})
    return sorted(rows, key=lambda item: (item["family_id"], item["unit_id"]))


def _resolve_used_references(
    references: Sequence[Mapping[str, Any]],
    *,
    coverage_contract: Mapping[str, Any],
    sources_db: Path,
    vesum_db: Path,
    r2u_cache: Path,
) -> list[dict[str, Any]]:
    """Resolve only the used subset while streaming all 7.3M source units."""
    pending = {(item["family_id"], item["unit_id"]): item for item in aggregate_typed_occurrences(references)}
    resolved: list[dict[str, Any]] = []
    # Reuse the same family streams as the complete structural reproduction.
    families = _lexical_contract_families(coverage_contract)
    source_hash, vesum_hash = universe.sha256_file(sources_db), universe.sha256_file(vesum_db)
    source_db = universe._connect(sources_db)
    vesum: Any | None = None
    try:
        vesum = universe._connect(vesum_db)
        streams: list[tuple[str, Iterable[Mapping[str, Any]]]] = []
        for family_id, table in universe.SOURCES_FAMILIES.items():
            if family_id in LEXICAL_FAMILIES:
                streams.append(
                    (family_id, universe._database_units(source_db, table, family_id, families[family_id], source_hash))
                )
        streams.extend(
            (
                (
                    "lexical_vesum",
                    universe._database_units(vesum, "forms", "lexical_vesum", families["lexical_vesum"], vesum_hash),
                ),
                ("lexical_r2u", universe._r2u_units(r2u_cache, families["lexical_r2u"])),
            )
        )
        for family_id, stream in streams:
            for unit in stream:
                key = (family_id, unit["unit_id"])
                item = pending.pop(key, None)
                if item is not None:
                    require(
                        item["unit_sha256"] == unit["unit_sha256"], f"typed lexical unit hash mismatch: {family_id}"
                    )
                    resolved.append(item)
    finally:
        source_db.close()
        if vesum is not None:
            vesum.close()
    require(not pending, "unresolved typed lexical target")
    return sorted(resolved, key=lambda item: (item["family_id"], item["unit_id"]))


def freeze_used_subset_population(
    release_manifest: Mapping[str, Any],
    *,
    release_root: Path,
    source_universe_dir: Path = DEFAULT_SOURCE_UNIVERSE,
    coverage_contract: Mapping[str, Any],
    role_contract: Mapping[str, Any],
    sources_db: Path,
    vesum_db: Path,
    r2u_cache: Path,
    repair_generation: int,
) -> dict[str, Any]:
    """Freeze the exact typed used population before a census decision exists."""
    require(isinstance(repair_generation, int) and repair_generation >= 0, "invalid repair generation")
    source_receipt, source_hash, structural, structural_hash = _source_bindings(source_universe_dir)
    manifest_hash, file_rows = _validate_release_manifest(release_manifest, release_root=release_root)
    files = {item["artifact_id"]: item for item in file_rows}
    references = [
        _validate_typed_reference(item, files=files)
        for item in extract_typed_lexical_references(file_rows, release_root=release_root)
    ]
    resolved = _resolve_used_references(
        references, coverage_contract=coverage_contract, sources_db=sources_db, vesum_db=vesum_db, r2u_cache=r2u_cache
    )
    structural_hashes = {item["family_id"]: item["ordered_rolling_sha256"] for item in structural["families"]}
    families: list[dict[str, Any]] = []
    for family_id in sorted(LEXICAL_FAMILIES):
        rows = [item for item in resolved if item["family_id"] == family_id]
        families.append(
            {
                "family_id": family_id,
                "structural_universe_sha256": structural_hashes[family_id],
                "used_subset_total": len(rows),
                "rows": rows,
                "used_subset_population_sha256": sha256_value(rows),
            }
        )
    base = {
        "schema_version": "phase3_lexical_used_subset_population_freeze_v1",
        "text_free": True,
        "source_universe_receipt_sha256": source_hash,
        "source_universe_payload_manifest_sha256": source_receipt["artifact_manifest"]["payload_manifest_sha256"],
        "lexical_structural_freeze_sha256": structural_hash,
        "release_artifact_manifest_sha256": manifest_hash,
        "release_files_sha256": sha256_value(file_rows),
        "coverage_contract_sha256": sha256_value(coverage_contract),
        "role_contract_sha256": sha256_value(role_contract),
        "implementation_sha256": implementation_sha256(),
        "repair_generation": repair_generation,
        "families": families,
    }
    return {**base, "population_freeze_sha256": sha256_value(base)}


def validate_complete_census(
    census: Mapping[str, Any],
    population_freeze: Mapping[str, Any],
    *,
    role_contract: Mapping[str, Any],
    prohibited_identity_ids: Sequence[str] = (),
) -> dict[str, Any]:
    """Require an exact, complete, non-sampled census of the frozen used set."""
    _text_free(census, "lexical complete census")
    _exact(
        census,
        {
            "schema_version",
            "text_free",
            "source_universe_receipt_sha256",
            "source_universe_payload_manifest_sha256",
            "lexical_structural_freeze_sha256",
            "coverage_contract_sha256",
            "role_contract_sha256",
            "population_freeze_sha256",
            "implementation_sha256",
            "repair_generation",
            "seed_required",
            "auditor_controller_identity_id",
            "families",
        },
        "lexical complete census",
    )
    require(
        census["schema_version"] == "phase3_lexical_complete_census_v2" and census["text_free"] is True,
        "invalid lexical census header",
    )
    require(census["seed_required"] is False, "lexical census is complete and must not use a seed")
    require(census["implementation_sha256"] == implementation_sha256(), "stale lexical coverage implementation")
    require(
        census["auditor_controller_identity_id"] == _assigned_auditor(role_contract),
        "lexical census identity is not the assigned auditor",
    )
    require(
        ASSIGNED_DISPOSITION_AUDITOR not in set(prohibited_identity_ids),
        "root or rule author cannot attest lexical census",
    )
    _exact(
        population_freeze,
        {
            "schema_version",
            "text_free",
            "source_universe_receipt_sha256",
            "source_universe_payload_manifest_sha256",
            "lexical_structural_freeze_sha256",
            "release_artifact_manifest_sha256",
            "release_files_sha256",
            "coverage_contract_sha256",
            "role_contract_sha256",
            "implementation_sha256",
            "repair_generation",
            "families",
            "population_freeze_sha256",
        },
        "used-subset population freeze",
    )
    base = {key: value for key, value in population_freeze.items() if key != "population_freeze_sha256"}
    require(
        population_freeze["schema_version"] == "phase3_lexical_used_subset_population_freeze_v1"
        and population_freeze["text_free"] is True
        and population_freeze["population_freeze_sha256"] == sha256_value(base),
        "invalid population freeze",
    )
    require(
        population_freeze["implementation_sha256"] == implementation_sha256(), "stale population-freeze implementation"
    )
    require(
        population_freeze["role_contract_sha256"] == sha256_value(role_contract),
        "stale population-freeze role contract",
    )
    require(
        census["population_freeze_sha256"] == population_freeze["population_freeze_sha256"]
        and census["repair_generation"] == population_freeze["repair_generation"],
        "stale lexical census population or repair generation",
    )
    for name in (
        "source_universe_receipt_sha256",
        "source_universe_payload_manifest_sha256",
        "lexical_structural_freeze_sha256",
        "coverage_contract_sha256",
        "role_contract_sha256",
        "implementation_sha256",
    ):
        require(census[name] == population_freeze[name], f"stale lexical census binding: {name}")
    expected = {item["family_id"]: item for item in population_freeze["families"]}
    require(
        set(expected) == LEXICAL_FAMILIES and len(expected) == len(population_freeze["families"]),
        "population freeze must cover all lexical families exactly once",
    )
    for family_id, family in expected.items():
        _exact(
            family,
            {"family_id", "structural_universe_sha256", "used_subset_total", "rows", "used_subset_population_sha256"},
            "used-subset population family",
        )
        rows = family["rows"]
        require(
            isinstance(rows, list) and family["used_subset_total"] == len(rows), "used-subset population total mismatch"
        )
        require(
            family["used_subset_population_sha256"] == sha256_value(rows), "used-subset population row hash mismatch"
        )
        unit_ids: set[str] = set()
        for row in rows:
            require(isinstance(row, Mapping), "used-subset population row must be an object")
            _exact(row, {"family_id", "unit_id", "unit_sha256", "evidence_locators"}, "used-subset population row")
            require(
                row["family_id"] == family_id and isinstance(row["unit_id"], str) and row["unit_id"] not in unit_ids,
                "duplicate or mismatched used-subset unit",
            )
            unit_ids.add(row["unit_id"])
            _sha(row["unit_sha256"], "used-subset population unit hash")
            locators = row["evidence_locators"]
            require(
                isinstance(locators, list)
                and locators
                and locators == sorted(locators, key=canonical_json)
                and len({canonical_json(locator) for locator in locators}) == len(locators),
                "used-subset occurrence locators must be nonempty, unique, and canonical",
            )
    observed: set[str] = set()
    total = 0
    for family in census["families"]:
        require(isinstance(family, Mapping), "census family must be an object")
        _exact(family, {"family_id", "used_subset_total", "rows", "used_subset_census_sha256"}, "census family")
        family_id = family.get("family_id")
        require(
            isinstance(family_id, str) and family_id in expected and family_id not in observed,
            "missing or duplicate census family",
        )
        observed.add(family_id)
        rows = family["rows"]
        require(isinstance(rows, list) and family["used_subset_total"] == len(rows), "census total mismatch")
        for row in rows:
            require(isinstance(row, Mapping), "census row must be an object")
            _exact(row, {"family_id", "unit_id", "unit_sha256", "decision_code", "evidence_locators"}, "census row")
            require(
                row["family_id"] == family_id and row["decision_code"] == "agree",
                "non-agree census result blocks coverage",
            )
        expected_rows = [{**row, "decision_code": "agree"} for row in expected[family_id]["rows"]]
        require(
            canonical_json(sorted(rows, key=lambda item: item["unit_id"])) == canonical_json(expected_rows),
            "census omission, addition, substitution, duplicate, or locator drift",
        )
        require(family["used_subset_census_sha256"] == sha256_value(expected_rows), "census row hash mismatch")
        total += len(rows)
    require(
        observed == set(expected) == LEXICAL_FAMILIES,
        "census must include zero-used and nonzero-used rows for all thirteen families",
    )
    return {
        "ok": True,
        "complete_census": True,
        "seed_required": False,
        "family_count": len(observed),
        "used_unit_count": total,
        "status": "MECHANICS_ONLY_NOT_SOURCE_COVERAGE_READY",
    }


def validate_lexical_bundle(
    bundle: Mapping[str, Any],
    *,
    structural_audit: Mapping[str, Any],
    population_freeze: Mapping[str, Any],
    census: Mapping[str, Any],
    role_contract: Mapping[str, Any],
    coverage_contract: Mapping[str, Any],
    sources_db: Path,
    vesum_db: Path,
    r2u_cache: Path,
    source_universe_dir: Path = DEFAULT_SOURCE_UNIVERSE,
    repo_root: Path = ROOT,
) -> dict[str, Any]:
    """Bind all mechanical receipts to the exact first origin/main landing."""
    from scripts.projects.open_model_data import phase3_disposition_audit as audit

    _text_free(bundle, "lexical coverage bundle")
    _exact(
        bundle,
        {
            "schema_version",
            "text_free",
            "source_universe_receipt_sha256",
            "source_universe_payload_manifest_sha256",
            "lexical_structural_freeze_sha256",
            "coverage_contract_sha256",
            "role_contract_sha256",
            "structural_audit_sha256",
            "population_freeze_sha256",
            "complete_census_sha256",
            "release_artifact_manifest_sha256",
            "implementation_sha256",
            "repair_generation",
            "first_containing_squash_merge_sha",
        },
        "lexical coverage bundle",
    )
    require(
        bundle["schema_version"] == "phase3_lexical_coverage_bundle_v1" and bundle["text_free"] is True,
        "invalid lexical bundle header",
    )
    validate_structural_audit(
        structural_audit,
        source_universe_dir=source_universe_dir,
        coverage_contract=coverage_contract,
        role_contract=role_contract,
        sources_db=sources_db,
        vesum_db=vesum_db,
        r2u_cache=r2u_cache,
    )
    validate_complete_census(census, population_freeze, role_contract=role_contract)
    for name in (
        "source_universe_receipt_sha256",
        "source_universe_payload_manifest_sha256",
        "lexical_structural_freeze_sha256",
        "coverage_contract_sha256",
        "role_contract_sha256",
        "implementation_sha256",
        "repair_generation",
    ):
        require(
            structural_audit[name] == population_freeze[name] == census[name] == bundle[name],
            f"lexical bundle binding mismatch: {name}",
        )
    require(
        population_freeze["coverage_contract_sha256"] == sha256_value(coverage_contract),
        "stale population-freeze coverage contract",
    )
    require(bundle["structural_audit_sha256"] == sha256_value(structural_audit), "structural audit binding mismatch")
    require(
        bundle["population_freeze_sha256"] == population_freeze["population_freeze_sha256"],
        "population freeze binding mismatch",
    )
    require(bundle["complete_census_sha256"] == sha256_value(census), "complete census binding mismatch")
    require(
        bundle["release_artifact_manifest_sha256"] == population_freeze["release_artifact_manifest_sha256"],
        "release manifest binding mismatch",
    )
    require(
        bundle["implementation_sha256"] == implementation_sha256() == population_freeze["implementation_sha256"],
        "implementation binding mismatch",
    )
    require(
        bundle["repair_generation"] == population_freeze["repair_generation"] == census["repair_generation"],
        "repair generation binding mismatch",
    )
    first = audit._first_containing_squash_merge(population_freeze, repo_root=repo_root)
    require(
        bundle["first_containing_squash_merge_sha"] == first, "earliest containing origin/main merge lineage mismatch"
    )
    return {"ok": True, "bundle_verified": True, "status": "MECHANICS_ONLY_NOT_SOURCE_COVERAGE_READY"}
