"""Build and verify text-free, capability-specific Phase 2 complements.

This is evidence routing, not a legal opinion or a data admission tool.  It
does not read source text, download content, create a learning view, train a
model, or publish an artifact.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import tempfile
from collections import Counter
from collections.abc import Iterable, Iterator, Mapping
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator

from scripts.projects.open_model_data import document_signal_manifest as phase1_signals
from scripts.projects.open_model_data import source_work_locator_index as locator_index_builder

ROOT = Path(__file__).resolve().parents[3]
CONTRACTS = ROOT / "data/projects/open_model_data/contracts"
CAPABILITIES = (
    "acquisition_retention",
    "local_preparation",
    "local_model_learning",
    "raw_redistribution",
    "derived_redistribution",
    "dataset_publication",
    "model_publication",
)
STATES = frozenset(("evidenced", "unresolved", "blocked", "excluded"))
ROUTES = frozenset(("candidate", "metadata_only", "blocked", "excluded"))
SCHEMAS = {
    "phase1_row": "document_signal_record_v1.schema.json",
    "phase1_receipt": "document_signal_receipt_v1.schema.json",
    "policy": "source_capability_policy_v1.schema.json",
    "complement": "prepared_data_complement_record_v1.schema.json",
    "worklist": "evidence_resolution_item_v1.schema.json",
    "receipt": "prepared_data_complement_receipt_v1.schema.json",
    "locator": "source_work_locator_v1.schema.json",
}


class ComplementError(ValueError):
    """The requested evidence artifact cannot be safely built or verified."""


def canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"), sort_keys=True)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _read(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ComplementError(f"cannot read JSON {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise ComplementError(f"expected JSON object: {path}")
    return value


def _validator(name: str) -> Draft202012Validator:
    schema = _read(CONTRACTS / name)
    Draft202012Validator.check_schema(schema)
    return Draft202012Validator(schema)


def _validate(value: Mapping[str, Any], validator: Draft202012Validator, label: str) -> None:
    errors = sorted(validator.iter_errors(value), key=lambda error: list(error.path))
    if errors:
        error = errors[0]
        where = ".".join(str(part) for part in error.path) or "<root>"
        raise ComplementError(f"{label} schema failure at {where}: {error.message}")


def _artifact(path: Path, records: int | None = None) -> dict[str, Any]:
    if not path.is_file():
        raise ComplementError(f"missing artifact: {path}")
    if records is None:
        with path.open("rb") as handle:
            records = sum(1 for _ in handle)
    return {"bytes": path.stat().st_size, "records": records, "sha256": sha256_file(path)}


def _stage(path: Path, content: bytes) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            dir=path.parent, prefix=f".{path.name}.", suffix=".tmp", delete=False
        ) as handle:
            temporary = Path(handle.name)
            handle.write(content)
            handle.flush()
            os.fsync(handle.fileno())
        return temporary
    except OSError:
        if temporary is not None:
            temporary.unlink(missing_ok=True)
        raise


def _replace(source: Path, target: Path) -> None:
    """A test seam for one atomic promotion operation."""
    os.replace(source, target)


def _promote(staged: list[tuple[Path, Path]]) -> None:
    """Atomically promote a bundle as far as the filesystem permits.

    Existing outputs are moved aside first.  On any injected or filesystem
    failure the old bundle is restored and all new partials are removed.  The
    caller orders ``staged`` so that the receipt is the final commit marker.
    """
    backups: list[tuple[Path, Path]] = []
    installed: list[Path] = []
    try:
        for _temporary, output in staged:
            if output.exists():
                backup = output.with_name(f".{output.name}.rollback")
                backup.unlink(missing_ok=True)
                os.replace(output, backup)
                backups.append((backup, output))
        for temporary, output in staged:
            _replace(temporary, output)
            installed.append(output)
    except OSError as exc:
        for output in installed:
            output.unlink(missing_ok=True)
        for backup, output in backups:
            if backup.exists():
                os.replace(backup, output)
        for temporary, _output in staged:
            temporary.unlink(missing_ok=True)
        raise ComplementError("partial output promotion failed; prior outputs restored") from exc
    for backup, _output in backups:
        backup.unlink(missing_ok=True)


def _jsonl(path: Path, validator: Draft202012Validator, label: str) -> Iterator[dict[str, Any]]:
    try:
        with path.open(encoding="utf-8") as handle:
            for line_number, line in enumerate(handle, start=1):
                if not line.endswith("\n") or not line.strip():
                    raise ComplementError(f"{label} has a blank or unterminated row at {line_number}")
                try:
                    value = json.loads(line)
                except json.JSONDecodeError as exc:
                    raise ComplementError(f"{label} invalid JSON at {line_number}") from exc
                if not isinstance(value, dict):
                    raise ComplementError(f"{label} row {line_number} is not an object")
                _validate(value, validator, f"{label} row {line_number}")
                yield value
    except OSError as exc:
        raise ComplementError(f"cannot read {label}: {exc}") from exc


def _route(state: str) -> str:
    return {"evidenced": "candidate", "unresolved": "metadata_only", "blocked": "blocked", "excluded": "excluded"}[
        state
    ]


def _decision_id(policy_hash: str, scope_id: str, source_id: str | None) -> str:
    value = "|".join((policy_hash, scope_id, source_id or "family-default"))
    return "decision." + hashlib.sha256(value.encode("utf-8")).hexdigest()[:24]


def _validate_policy(
    policy: Mapping[str, Any], validator: Draft202012Validator
) -> tuple[dict[str, Any], dict[str, Any]]:
    _validate(policy, validator, "policy")
    if tuple(policy["capabilities"]) != CAPABILITIES:
        raise ComplementError("policy capabilities must be the canonical ordered capability list")
    catalog = {item["evidence_id"]: item for item in policy["evidence_catalog"]}
    if len(catalog) != len(policy["evidence_catalog"]):
        raise ComplementError("duplicate evidence catalog id")
    families = {item["source_family"]: item for item in policy["family_defaults"]}
    if len(families) != len(policy["family_defaults"]):
        raise ComplementError("duplicate policy family default")
    overrides = {item["source_id"]: item for item in policy["source_overrides"]}
    if len(overrides) != len(policy["source_overrides"]):
        raise ComplementError("duplicate source override")
    for label, scope in [*families.items(), *overrides.items()]:
        for capability, decision in scope["decisions"].items():
            if decision["state"] not in STATES:
                raise ComplementError(f"unknown decision state for {label}/{capability}")
            unknown = sorted(set(decision["evidence_refs"]) - set(catalog))
            if unknown:
                raise ComplementError(f"unknown evidence reference for {label}/{capability}: {unknown[0]}")
            if decision["state"] == "evidenced":
                if not decision["evidence_refs"] or decision["missing_evidence_keys"]:
                    raise ComplementError("evidenced decision requires evidence and no missing evidence keys")
            elif not decision["missing_evidence_keys"]:
                raise ComplementError("non-evidenced decision requires exact missing evidence keys")
    return families, overrides


def _phase1_inputs(phase1_manifest: Path, phase1_receipt: Path, validator: Draft202012Validator) -> dict[str, Any]:
    phase1 = _read(phase1_receipt)
    _validate(phase1, validator, "Phase 1 receipt")
    try:
        phase1_signals.verify_existing(manifest_path=phase1_manifest, receipt_path=phase1_receipt)
    except (phase1_signals.ManifestError, OSError, json.JSONDecodeError) as exc:
        raise ComplementError(f"invalid Phase 1 binding: {exc}") from exc
    expected = phase1["outputs"]["manifest"]
    actual = _artifact(phase1_manifest)
    if expected != actual:
        raise ComplementError("Phase 1 manifest exact artifact drift")
    return phase1


def _binding(source: Mapping[str, Any], static: Mapping[str, str]) -> dict[str, str]:
    return {
        "record_sha256": hashlib.sha256(canonical_json(source).encode("utf-8")).hexdigest(),
        **static,
    }


def _make_row(
    source: Mapping[str, Any],
    ordinal: int,
    phase1: Mapping[str, Any],
    phase1_manifest: Path,
    phase1_receipt: Path,
    policy: Mapping[str, Any],
    policy_hash: str,
    phase1_static: Mapping[str, str],
    family: Mapping[str, Any],
    override: Mapping[str, Any] | None,
    locator: Mapping[str, Any],
    locator_index_sha256: str,
) -> dict[str, Any]:
    scope = (
        family
        if override is None
        else {"scope_id": override["scope_id"], "decisions": {**family["decisions"], **override["decisions"]}}
    )
    decisions = scope["decisions"]
    capability_routes = {capability: _route(decisions[capability]["state"]) for capability in CAPABILITIES}
    faithful = (
        "candidate"
        if all(decisions[name]["state"] == "evidenced" for name in ("local_preparation", "local_model_learning"))
        else "metadata_only"
    )
    return {
        "schema_version": "prepared_data_complement_record_v1",
        "ordinal": ordinal,
        "record_id": source["record_id"],
        "source_id": source["source_id"],
        "work_id": source["work_id"],
        "source_family": source["source_family"],
        "inventory_asset_id": source["inventory_asset_id"],
        "dimensions": source["dimensions"],
        "content_sha256": source["content_sha256"],
        "admission_evidence_state": source["admission_evidence_state"],
        "capability_evidence": source["capability_evidence"],
        "signals": source["signals"],
        "exact_duplicate": source["exact_duplicate"],
        "near_duplicate": source["near_duplicate"],
        "heldout_contamination": source["heldout_contamination"],
        "protection_state": "not_classified_phase2",
        "phase1_binding": _binding(source, phase1_static),
        "policy_binding": {
            "policy_id": policy["policy_id"],
            "policy_sha256": policy_hash,
            "scope_id": scope["scope_id"],
            "decision_id": _decision_id(policy_hash, scope["scope_id"], source["source_id"] if override else None),
            "context": policy["context"],
        },
        "capabilities": decisions,
        "locator_binding": {
            "locator_id": locator["locator_id"],
            "source_id": locator["source_id"],
            "work_id": locator["work_id"],
            "canonical_url": locator["canonical_url"],
            "locator_row_sha256": hashlib.sha256(canonical_json(locator).encode("utf-8")).hexdigest(),
            "locator_index_sha256": locator_index_sha256,
        },
        "routes": {
            "capabilities": capability_routes,
            "representations": {
                "faithful": faithful,
                "loss_masked": "not_classified_phase2",
                "protected": "not_classified_phase2",
            },
        },
    }


def _counts() -> dict[str, Counter[str]]:
    return {axis: Counter() for axis in ("family", "source", "period", "genre", "register", "origin")}


def _receipt(
    phase1_manifest: Path,
    phase1_receipt: Path,
    policy_path: Path,
    locator_artifact: Mapping[str, Any],
    complement: dict[str, Any],
    worklist: dict[str, Any],
    counters: Mapping[str, Counter[str]],
    route_totals: Mapping[str, Counter[str]],
    representation_totals: Mapping[str, Counter[str]],
    records: int,
    locator_by_family: Mapping[str, int],
    textbook_grades: Mapping[str, int],
) -> dict[str, Any]:
    schema_hashes = {name: sha256_file(CONTRACTS / filename) for name, filename in SCHEMAS.items()}
    phase1_artifact = _artifact(phase1_manifest)
    phase1_receipt_artifact = _artifact(phase1_receipt)
    policy_artifact = _artifact(policy_path, 1)
    identity = "|".join(
        (
            phase1_artifact["sha256"],
            phase1_receipt_artifact["sha256"],
            policy_artifact["sha256"],
            locator_artifact["sha256"],
        )
    )
    return {
        "schema_version": "prepared_data_complement_receipt_v1",
        "receipt_id": "complement-receipt." + hashlib.sha256(identity.encode("utf-8")).hexdigest()[:24],
        "inputs": {
            "phase1_manifest": phase1_artifact,
            "phase1_receipt": phase1_receipt_artifact,
            "policy": policy_artifact,
            "locator_index": locator_artifact,
            "schemas": schema_hashes,
            "generator": sha256_file(Path(__file__)),
        },
        "outputs": {"complement": complement, "worklist": worklist},
        "coverage": {
            "complete": True,
            "records": records,
            "locator_mappings": sum(locator_by_family.values()),
            "locator_by_family": dict(sorted(locator_by_family.items())),
            "by_textbook_grade": dict(sorted(textbook_grades.items())),
            **{f"by_{axis}": dict(sorted(counters[axis].items())) for axis in counters},
        },
        "route_totals": {capability: dict(sorted(route_totals[capability].items())) for capability in CAPABILITIES},
        "representation_totals": {name: dict(sorted(total.items())) for name, total in representation_totals.items()},
        "algorithm": {
            "ordering": "Phase1 ordinal ascending; worklist source_id then capability",
            "serialization": "UTF-8 canonical JSON sorted keys LF",
            "phase1_binding": "validated Phase1 record and receipt schemas plus exact artifacts",
            "locator_binding": "one exact locator row per Phase1 source_id/work_id pair",
            "receipt_last_commit_marker": True,
        },
        "resources": {
            "streaming": True,
            "source_passes": 1,
            "bounded_state": "one Phase1 row plus complete text-free locator map, aggregate counters, source/work pair counts, and per-source locator references",
        },
        "safety": {
            "training": False,
            "model": False,
            "download": False,
            "upload": False,
            "publication": False,
            "text_emitted": False,
            "evaluation_fingerprints_emitted": False,
        },
    }


def _locators(
    path: Path, validator: Draft202012Validator
) -> tuple[dict[tuple[str, str], dict[str, Any]], dict[str, Any], dict[str, int]]:
    if path.name.endswith(locator_index_builder.COMPACT_OUTPUT_SUFFIX):
        try:
            rows = locator_index_builder.compact_rows(path)
        except locator_index_builder.LocatorError as exc:
            raise ComplementError(f"invalid compact locator index: {exc}") from exc
    else:
        rows = list(_jsonl(path, validator, "locator index"))
    artifact = _artifact(path, len(rows))
    if rows != sorted(
        rows, key=lambda x: (x["source_family"], x["source_id"], x["work_id"], canonical_json(x["source_locator"]))
    ):
        raise ComplementError("locator index is reordered")
    result = {(row["source_id"], row["work_id"]): row for row in rows}
    if len(result) != len(rows):
        raise ComplementError("locator index has duplicate source/work mappings")
    return result, artifact, dict(sorted(Counter(row["source_family"] for row in rows).items()))


def build(
    *,
    phase1_manifest: Path,
    phase1_receipt: Path,
    policy_path: Path,
    complement_output: Path,
    receipt_output: Path,
    worklist_output: Path,
    locator_index: Path,
) -> dict[str, Any]:
    validators = {name: _validator(filename) for name, filename in SCHEMAS.items()}
    phase1 = _phase1_inputs(phase1_manifest, phase1_receipt, validators["phase1_receipt"])
    policy = _read(policy_path)
    families, overrides = _validate_policy(policy, validators["policy"])
    policy_hash = sha256_file(policy_path)
    phase1_static = {
        "manifest_sha256": sha256_file(phase1_manifest),
        "receipt_sha256": sha256_file(phase1_receipt),
        "record_schema_sha256": sha256_file(CONTRACTS / SCHEMAS["phase1_row"]),
        "receipt_schema_sha256": sha256_file(CONTRACTS / SCHEMAS["phase1_receipt"]),
        "generator_sha256": phase1["inputs"]["generator_sha256"],
    }
    locators, locator_artifact, locator_by_family = _locators(locator_index, validators["locator"])
    source_groups: dict[str, tuple[int, dict[str, Any]]] = {}
    phase_pairs: set[tuple[str, str]] = set()
    phase_pair_counts: Counter[tuple[str, str]] = Counter()
    locator_references: dict[str, set[tuple[str, str, str | None, str]]] = {}
    counters, route_totals = _counts(), {capability: Counter() for capability in CAPABILITIES}
    representation_totals = {
        "faithful": Counter({"candidate": 0, "metadata_only": 0}),
        "loss_masked": Counter({"not_classified_phase2": 0}),
        "protected": Counter({"not_classified_phase2": 0}),
    }
    complement_temp = worklist_temp = receipt_temp = None
    try:
        complement_temp = _stage(complement_output, b"")
        records = 0
        with complement_temp.open("ab") as handle:
            for ordinal, source in enumerate(_jsonl(phase1_manifest, validators["phase1_row"], "Phase 1 manifest")):
                if source["ordinal"] != ordinal:
                    raise ComplementError("Phase 1 manifest is reordered")
                family = families.get(source["source_family"])
                if family is None:
                    raise ComplementError(f"missing policy family default: {source['source_family']}")
                override = overrides.get(source["source_id"])
                if override is not None and override["source_family"] != source["source_family"]:
                    raise ComplementError("source override family disagrees with Phase 1 row")
                pair = (source["source_id"], source["work_id"])
                phase_pairs.add(pair)
                phase_pair_counts[pair] += 1
                locator = locators.get(pair)
                if (
                    locator is None
                    or locator["source_family"] != source["source_family"]
                    or locator["inventory_asset_id"] != source["inventory_asset_id"]
                ):
                    raise ComplementError("missing or mismatched locator for Phase 1 source/work")
                row = _make_row(
                    source,
                    ordinal,
                    phase1,
                    phase1_manifest,
                    phase1_receipt,
                    policy,
                    policy_hash,
                    phase1_static,
                    family,
                    override,
                    locator,
                    locator_artifact["sha256"],
                )
                _validate(row, validators["complement"], "complement")
                handle.write((canonical_json(row) + "\n").encode("utf-8"))
                records += 1
                previous = source_groups.get(source["source_id"])
                source_groups[source["source_id"]] = (
                    (previous[0] if previous else 0) + 1,
                    previous[1] if previous else row,
                )
                locator_references.setdefault(source["source_id"], set()).add(
                    (
                        locator["locator_id"],
                        locator["work_id"],
                        locator["canonical_url"],
                        row["locator_binding"]["locator_row_sha256"],
                    )
                )
                for axis, value in (
                    ("family", row["source_family"]),
                    ("source", row["source_id"]),
                    ("period", row["dimensions"]["period"]),
                    ("genre", row["dimensions"]["genre"]),
                    ("register", row["dimensions"]["register"]),
                    ("origin", row["dimensions"]["origin"]),
                ):
                    counters[axis][value] += 1
                for capability, route in row["routes"]["capabilities"].items():
                    route_totals[capability][route] += 1
                for representation, state in row["routes"]["representations"].items():
                    representation_totals[representation][state] += 1
            handle.flush()
            os.fsync(handle.fileno())
        if records != phase1["outputs"]["manifest"]["records"]:
            raise ComplementError("Phase 1 coverage count drift")
        if set(locators) != phase_pairs:
            raise ComplementError("locator index has missing or extra source/work mapping")
        for pair, count in phase_pair_counts.items():
            if locators[pair]["affected_records"] != count:
                raise ComplementError("locator affected_records disagrees with Phase 1 source/work coverage")
        textbook_grades: Counter[str] = Counter()
        for locator in locators.values():
            if locator["source_family"] == "public_textbooks":
                textbook_grades[str(locator["metadata"].get("grade") or "missing")] += locator["affected_records"]
        unused_overrides = sorted(set(overrides) - set(source_groups))
        if unused_overrides:
            raise ComplementError(f"source override does not match any Phase 1 source: {unused_overrides[0]}")
        worklist_temp = _stage(worklist_output, b"")
        worklist_records = 0
        with worklist_temp.open("ab") as handle:
            for source_id in sorted(source_groups):
                affected_records, first = source_groups[source_id]
                for capability in CAPABILITIES:
                    decision = first["capabilities"][capability]
                    if decision["state"] == "evidenced":
                        continue
                    item = {
                        "schema_version": "evidence_resolution_item_v1",
                        "work_item_id": "resolution."
                        + hashlib.sha256(
                            f"{source_id}|{capability}|{first['policy_binding']['decision_id']}".encode()
                        ).hexdigest()[:24],
                        "source_id": source_id,
                        "source_family": first["source_family"],
                        "capability": capability,
                        "state": decision["state"],
                        "route": first["routes"]["capabilities"][capability],
                        "policy_binding": {
                            key: first["policy_binding"][key]
                            for key in ("policy_id", "scope_id", "decision_id", "context")
                        },
                        "locator_references": [
                            {
                                "locator_id": locator_id,
                                "work_id": work_id,
                                "canonical_url": canonical_url,
                                "locator_row_sha256": row_sha256,
                            }
                            for locator_id, work_id, canonical_url, row_sha256 in sorted(locator_references[source_id])
                        ],
                        "affected_records": affected_records,
                        "missing_evidence_keys": decision["missing_evidence_keys"],
                        "evidence_refs": decision["evidence_refs"],
                        "priority": "high" if capability in ("local_preparation", "local_model_learning") else "normal",
                    }
                    _validate(item, validators["worklist"], "worklist")
                    handle.write((canonical_json(item) + "\n").encode("utf-8"))
                    worklist_records += 1
            handle.flush()
            os.fsync(handle.fileno())
        complement_artifact = _artifact(complement_temp, records)
        worklist_artifact = _artifact(worklist_temp, worklist_records)
        receipt = _receipt(
            phase1_manifest,
            phase1_receipt,
            policy_path,
            locator_artifact,
            complement_artifact,
            worklist_artifact,
            counters,
            route_totals,
            representation_totals,
            records,
            locator_by_family,
            textbook_grades,
        )
        _validate(receipt, validators["receipt"], "receipt")
        receipt_temp = _stage(receipt_output, (canonical_json(receipt) + "\n").encode("utf-8"))
        _promote(
            [(complement_temp, complement_output), (worklist_temp, worklist_output), (receipt_temp, receipt_output)]
        )
        return receipt
    finally:
        for temporary in (complement_temp, worklist_temp, receipt_temp):
            if temporary is not None:
                temporary.unlink(missing_ok=True)


def verify(
    *,
    policy_path: Path,
    phase1_manifest: Path,
    phase1_receipt: Path,
    complement: Path,
    worklist: Path,
    receipt: Path,
    locator_index: Path,
) -> bool:
    """Rebuild into a private temporary bundle and require byte-exact equality."""
    supplied = _read(receipt)
    _validate(supplied, _validator(SCHEMAS["receipt"]), "receipt")
    with tempfile.TemporaryDirectory(prefix="phase2-complement-verify-") as directory:
        root = Path(directory)
        expected_complement, expected_worklist, expected_receipt = (
            root / "complement.jsonl",
            root / "worklist.jsonl",
            root / "receipt.json",
        )
        build(
            phase1_manifest=phase1_manifest,
            phase1_receipt=phase1_receipt,
            policy_path=policy_path,
            complement_output=expected_complement,
            worklist_output=expected_worklist,
            receipt_output=expected_receipt,
            locator_index=locator_index,
        )
        for label, actual, expected in (
            ("complement", complement, expected_complement),
            ("worklist", worklist, expected_worklist),
            ("receipt", receipt, expected_receipt),
        ):
            if not actual.is_file() or actual.read_bytes() != expected.read_bytes():
                raise ComplementError(f"{label} drift: missing, tampered, truncated, reordered, or extra rows")
    return True


def filter_rows(path: Path, capability: str, state: str, route: str | None, faithful: bool = False) -> Iterable[str]:
    """Yield source-blind (text-free) rows matching one independent capability."""
    if capability not in CAPABILITIES:
        raise ComplementError("unknown capability")
    if state not in STATES:
        raise ComplementError("unknown state")
    if route is not None and route not in ROUTES:
        raise ComplementError("unknown route")
    validator = _validator(SCHEMAS["complement"])
    for row in _jsonl(path, validator, "complement"):
        if (
            row["capabilities"][capability]["state"] == state
            and (route is None or row["routes"]["capabilities"][capability] == route)
            and (not faithful or row["routes"]["representations"]["faithful"] == "candidate")
        ):
            yield canonical_json(row)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    build_parser = sub.add_parser("build")
    for name in (
        "phase1_manifest",
        "phase1_receipt",
        "policy",
        "complement_output",
        "receipt_output",
        "worklist_output",
    ):
        build_parser.add_argument("--" + name.replace("_", "-"), type=Path, required=True)
    build_parser.add_argument("--locator-index", type=Path, required=True)
    verify_parser = sub.add_parser("verify")
    for name in ("policy", "phase1_manifest", "phase1_receipt", "complement", "worklist", "receipt"):
        verify_parser.add_argument("--" + name.replace("_", "-"), type=Path, required=True)
    verify_parser.add_argument("--locator-index", type=Path, required=True)
    filter_parser = sub.add_parser("filter")
    filter_parser.add_argument("--complement", type=Path, required=True)
    filter_parser.add_argument("--capability", required=True)
    filter_parser.add_argument("--state", required=True)
    filter_parser.add_argument("--route")
    filter_parser.add_argument("--faithful", action="store_true")
    args = parser.parse_args(argv)
    try:
        if args.command == "build":
            build(
                phase1_manifest=args.phase1_manifest,
                phase1_receipt=args.phase1_receipt,
                policy_path=args.policy,
                complement_output=args.complement_output,
                receipt_output=args.receipt_output,
                worklist_output=args.worklist_output,
                locator_index=args.locator_index,
            )
        elif args.command == "verify":
            verify(
                policy_path=args.policy,
                phase1_manifest=args.phase1_manifest,
                phase1_receipt=args.phase1_receipt,
                complement=args.complement,
                worklist=args.worklist,
                receipt=args.receipt,
                locator_index=args.locator_index,
            )
        else:
            for row in filter_rows(args.complement, args.capability, args.state, args.route, args.faithful):
                print(row)
    except (ComplementError, OSError, json.JSONDecodeError) as exc:
        parser.error(str(exc))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
