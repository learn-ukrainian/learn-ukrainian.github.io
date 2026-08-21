#!/usr/bin/env python3
"""Fail-closed authorized candidate-only Cycle-006 v2 resolver."""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import stat
import sys
import tempfile
from pathlib import Path
from types import ModuleType
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
CYCLE = "phase3-v2-1-evaluation-cycle-006"
SOURCE_CYCLE = "phase3-v2-1-evaluation-cycle-005"
CYCLE006_AMENDMENT_SHA256 = "524e6eb4f18d38f104413fb32f421ff73c3d80bc411d338a6d8a31fabc087474"
AMENDMENT_SHA256 = CYCLE006_AMENDMENT_SHA256
CUSTODY_SHA256 = "7047e8459433376f3b690cfc2f15e115d77a701e79afb0ef2db184b44ea14726"
SOURCE_MANIFEST_SHA256 = "b8d290ffe945a6cc5d36345cbf234ccf79a7df98cb4199ffad0b778cd2b69fab"
MANIFEST_SHA256 = SOURCE_MANIFEST_SHA256
ORDERED_IDENTITY_COMMITMENT_SHA256 = "331fd7fbc42e43cb3c218d9c2b790df060c0a553ab7c3a7b3b557f9f2bc3c419"
LANES = {"clean_label": 40, "residual_label": 164}
ROW_COUNT = 10159
RESOLUTION_OUTPUT = "dual-label-final-cycle006-v2"
ADJUDICATION_OUTPUT = "dual-label-adjudication-cycle006-v2"
CYCLE005_OUTPUT_ROOTS = (
    "label-output",
    "label-output-gemini-v2",
    "dual-label-output",
    "label-output-grok-cycle006-v1",
    "label-output-gemini-cycle006-v1",
    "dual-label-adjudication-cycle006-v1",
    "dual-label-final-cycle006-v1",
)
COMPARE_MODULE = ROOT / "batch_state/phase3-compare-cycle006-dual-labels-v2.py"
ADJUDICATION_MODULE = ROOT / "batch_state/phase3-run-cycle006-dual-label-adjudication-v2.py"
# These are filled with the exact public source hashes after the files are
# materialized.  Synthetic tests may replace them with fixture hashes.
COMPARE_MODULE_SHA256 = "9697329128413dd81a35b9e8478511196e94d705e728dd5f8993401b9ca9fde3"
ADJUDICATION_MODULE_SHA256 = "a82438c8e5ab1ba2c1430f318e590b870c9b3eed52b508121fd7e4ce4fbf3584"


class Error(ValueError):
    def __init__(self, code: str):
        self.code = code
        super().__init__(code)


def canonical(value: Any) -> bytes:
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n").encode("utf-8")


def digest(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def _pairs(items: list[tuple[str, Any]]) -> dict[str, Any]:
    value: dict[str, Any] = {}
    for key, item in items:
        if key in value:
            raise Error("json_binding_failure")
        value[key] = item
    return value


def _load(name: str, path: Path) -> ModuleType | None:
    if path.is_symlink() or not path.is_file():
        return None
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        return None
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    try:
        spec.loader.exec_module(module)
    except Exception:
        return None
    return module


CMP = _load("cycle006_v2_resolution_compare", COMPARE_MODULE)
ADJ = _load("cycle006_v2_resolution_adjudication", ADJUDICATION_MODULE)


def _regular(path: Path, mode: int | None = None) -> None:
    try:
        info = path.lstat()
    except OSError as exc:
        del exc
        raise Error("binding_failure") from None
    if stat.S_ISLNK(info.st_mode) or not stat.S_ISREG(info.st_mode):
        raise Error("binding_failure")
    if mode is not None and stat.S_IMODE(info.st_mode) != mode:
        raise Error("mode_drift")


def _directory(path: Path, mode: int | None = None) -> None:
    try:
        info = path.lstat()
    except OSError as exc:
        del exc
        raise Error("binding_failure") from None
    if stat.S_ISLNK(info.st_mode) or not stat.S_ISDIR(info.st_mode):
        raise Error("binding_failure")
    if mode is not None and stat.S_IMODE(info.st_mode) != mode:
        raise Error("mode_drift")


def _read(path: Path) -> tuple[Any, bytes]:
    _regular(path, 0o600)
    raw = path.read_bytes()
    try:
        return json.loads(raw.decode("utf-8", "strict"), object_pairs_hook=_pairs), raw
    except (UnicodeDecodeError, json.JSONDecodeError, Error) as exc:
        del exc
        raise Error("json_binding_failure") from None


def _package_custody(package: Path) -> str:
    """Return the hash of this materialized package's custody receipt."""
    path = package / "custody-receipt.json"
    _read(path)
    return digest(path.read_bytes())


def _atomic(path: Path, value: Any) -> str:
    if path.exists() or path.is_symlink():
        raise Error("immutable_output_exists")
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    _directory(path.parent, 0o700)
    data = canonical(value)
    fd, name = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    temporary = Path(name)
    try:
        with open(fd, "wb", closefd=True) as handle:
            handle.write(data)
            handle.flush()
        temporary.chmod(0o600)
        temporary.replace(path)
    except BaseException:
        temporary.unlink(missing_ok=True)
        raise
    return digest(data)


def _hash_bound(path: Path, expected: str) -> None:
    _regular(path)
    if expected.startswith("__") or digest(path.read_bytes()) != expected:
        raise Error("upstream_module_binding")


def _upstream() -> tuple[ModuleType, ModuleType]:
    if CMP is None or ADJ is None:
        raise Error("upstream_module_missing")
    _hash_bound(COMPARE_MODULE, COMPARE_MODULE_SHA256)
    _hash_bound(ADJUDICATION_MODULE, ADJUDICATION_MODULE_SHA256)
    adjudication_compare = getattr(ADJ, "CMP", None)
    if not isinstance(adjudication_compare, ModuleType):
        raise Error("upstream_module_binding")
    if (
        getattr(CMP, "CYCLE", None) != CYCLE
        or getattr(ADJ, "CYCLE", None) != CYCLE
        or getattr(adjudication_compare, "CYCLE", None) != CYCLE
        or getattr(CMP, "AMENDMENT_SHA256", None) != AMENDMENT_SHA256
        or getattr(ADJ, "AMENDMENT_SHA256", None) != AMENDMENT_SHA256
        or getattr(CMP, "CUSTODY_SHA256", None) != CUSTODY_SHA256
        or getattr(ADJ, "CUSTODY_SHA256", None) != CUSTODY_SHA256
        or getattr(CMP, "SOURCE_MANIFEST_SHA256", None) != SOURCE_MANIFEST_SHA256
        or getattr(ADJ, "SOURCE_MANIFEST_SHA256", None) != SOURCE_MANIFEST_SHA256
        or getattr(ADJ, "OUTPUT", None) != ADJUDICATION_OUTPUT
        or not hasattr(ADJ, "verify_packet")
        or not hasattr(ADJ, "inputs")
    ):
        raise Error("upstream_module_binding")
    return CMP, ADJ


def _identity(row: Any) -> tuple[str, str]:
    if not isinstance(row, dict):
        raise Error("identity_binding_failure")
    unit_id, unit_sha256 = row.get("unit_id"), row.get("unit_sha256")
    if (
        not isinstance(unit_id, str)
        or not isinstance(unit_sha256, str)
        or len(unit_sha256) != 64
        or any(character not in "0123456789abcdef" for character in unit_sha256)
    ):
        raise Error("identity_binding_failure")
    return unit_id, unit_sha256


def _identities(rows: list[Any]) -> list[tuple[str, str]]:
    values = [_identity(row) for row in rows]
    if len(values) != len(set(values)):
        raise Error("identity_uniqueness_failure")
    return values


def _package(package: Path) -> tuple[ModuleType, ModuleType, dict[str, Any]]:
    compare, adjudication = _upstream()
    _directory(package, 0o700)
    if any((package / name).exists() or (package / name).is_symlink() for name in CYCLE005_OUTPUT_ROOTS):
        raise Error("cycle005_output_dependency")
    try:
        value = compare.manifest(package)
    except Exception as exc:
        del exc
        raise Error("upstream_package_binding") from None
    if not isinstance(value, dict):
        raise Error("upstream_package_binding")
    return compare, adjudication, value


def _paths(package: Path, lane: str, index: int) -> tuple[Path, Path, Path]:
    out = package / RESOLUTION_OUTPUT / "final" / lane
    return out / f"decisions-{index:04d}.json", out / f"labels-{index:04d}.json", out / f"receipt-{index:04d}.json"


def _base_paths(package: Path, lane: str, index: int) -> tuple[Path, Path, Path]:
    out = package / ADJUDICATION_OUTPUT / "final" / lane
    return out / f"labels-{index:04d}.json", out / f"unresolved-{index:04d}.json", out / f"receipt-{index:04d}.json"


def _binding_fields(value: dict[str, Any], package: Path) -> bool:
    return (
        value.get("evaluation_cycle_id") == CYCLE
        and value.get("amendment_sha256") == AMENDMENT_SHA256
        and value.get("custody_receipt_raw_sha256") == _package_custody(package)
        and value.get("source_label_manifest_raw_sha256") == SOURCE_MANIFEST_SHA256
        and value.get("manifest_raw_sha256") == digest((package / "label-manifest.json").read_bytes())
        and value.get("ordered_identity_commitment_sha256") == ORDERED_IDENTITY_COMMITMENT_SHA256
    )


def request(
    path: Path, expected: list[dict[str, str]], package: Path
) -> tuple[list[dict[str, str]], str, dict[str, str] | None, bytes]:
    value, raw = _read(path)
    if not isinstance(value, dict) or not _binding_fields(value, package):
        raise Error("authorization_binding_failure")
    schema = value.get("schema_version")
    if schema == "phase3_cycle006_operator_resolution_request_v2":
        required = {
            "schema_version",
            "evaluation_cycle_id",
            "amendment_sha256",
            "custody_receipt_raw_sha256",
            "source_label_manifest_raw_sha256",
            "manifest_raw_sha256",
            "ordered_identity_commitment_sha256",
            "resolutions",
        }
        if set(value) != required:
            raise Error("authorization_schema_failure")
        authority, advisor = "operator", None
    elif schema == "phase3_cycle006_designated_advisor_resolution_request_v2":
        required = {
            "schema_version",
            "evaluation_cycle_id",
            "amendment_sha256",
            "custody_receipt_raw_sha256",
            "source_label_manifest_raw_sha256",
            "manifest_raw_sha256",
            "ordered_identity_commitment_sha256",
            "decision_authority",
            "advisor",
            "resolutions",
        }
        if set(value) != required:
            raise Error("authorization_schema_failure")
        authority, advisor = value.get("decision_authority"), value.get("advisor")
        if (
            authority != "designated_advisor"
            or not isinstance(advisor, dict)
            or set(advisor) != {"exact_model", "model_family", "harness", "task_id", "response_raw_sha256"}
            or advisor.get("exact_model") != "claude-fable-5"
            or advisor.get("model_family") != "anthropic"
            or advisor.get("harness") != "claude_acp"
            or any(not isinstance(advisor.get(key), str) for key in advisor)
            or len(advisor.get("response_raw_sha256", "")) != 64
            or any(character not in "0123456789abcdef" for character in advisor.get("response_raw_sha256", ""))
        ):
            raise Error("authorization_binding_failure")
    else:
        raise Error("authorization_schema_failure")
    rows = value.get("resolutions")
    if not isinstance(rows, list) or len(rows) != len(expected):
        raise Error("authorization_count_failure")
    expected_ids = [_identity(item) for item in expected]
    received: list[tuple[str, str]] = []
    for row in rows:
        if not isinstance(row, dict) or set(row) != {"unit_id", "unit_sha256", "selection"}:
            raise Error("authorization_schema_failure")
        if row.get("selection") not in {"grok", "gemini"}:
            raise Error("forbidden_candidate")
        received.append(_identity(row))
    if received != expected_ids or len(received) != len(set(received)):
        raise Error("authorization_identity_order_failure")
    return rows, authority, advisor, raw


def _external_json(path: Path, package: Path) -> tuple[dict[str, Any], bytes]:
    """Read an operator-supplied 0600 artifact that is outside the package."""
    try:
        if path.resolve(strict=True).is_relative_to(package.resolve()):
            raise Error("authorization_binding_failure")
    except OSError as exc:
        raise Error("authorization_binding_failure") from exc
    value, raw = _read(path)
    if not isinstance(value, dict) or raw != canonical(value):
        raise Error("authorization_schema_failure")
    return value, raw


def _authorization(
    path: Path,
    package: Path,
    request_path: Path,
    request_raw: bytes,
    authority: str,
    identities: list[dict[str, str]],
    advisor: dict[str, str] | None,
    advisor_response_path: Path | None,
) -> str:
    """Require an independent, immutable authorization artifact for each build."""
    try:
        if path.resolve(strict=True) == request_path.resolve(strict=True):
            raise Error("authorization_binding_failure")
    except OSError as exc:
        raise Error("authorization_binding_failure") from exc
    value, raw = _external_json(path, package)
    expected = {
        "schema_version": "phase3_cycle006_resolution_authorization_receipt_v2",
        "evaluation_cycle_id": CYCLE,
        "amendment_sha256": AMENDMENT_SHA256,
        "custody_receipt_raw_sha256": _package_custody(package),
        "source_label_manifest_raw_sha256": SOURCE_MANIFEST_SHA256,
        "manifest_raw_sha256": digest((package / "label-manifest.json").read_bytes()),
        "ordered_identity_commitment_sha256": ORDERED_IDENTITY_COMMITMENT_SHA256,
        "request_raw_sha256": digest(request_raw),
        "decision_authority": authority,
        "identity_order_sha256": digest(canonical([list(_identity(row)) for row in identities])),
        "nonce_sha256": value.get("nonce_sha256"),
        "text_free": True,
    }
    if (
        not isinstance(expected["nonce_sha256"], str)
        or len(expected["nonce_sha256"]) != 64
        or any(character not in "0123456789abcdef" for character in expected["nonce_sha256"])
    ):
        raise Error("authorization_schema_failure")
    if authority == "designated_advisor":
        if advisor is None or advisor_response_path is None:
            raise Error("authorization_binding_failure")
        response_value, response_raw = _external_json(advisor_response_path, package)
        del response_value
        response_hash = digest(response_raw)
        if response_hash != advisor.get("response_raw_sha256"):
            raise Error("authorization_binding_failure")
        expected["advisor_response_raw_sha256"] = response_hash
    elif authority != "operator" or advisor is not None or advisor_response_path is not None:
        raise Error("authorization_binding_failure")
    if (
        set(value) != set(expected) | {"receipt_sha256"}
        or any(value.get(key) != item for key, item in expected.items())
        or value.get("receipt_sha256") != digest(canonical(expected))
        or raw != canonical(value)
    ):
        raise Error("authorization_schema_failure")
    return digest(raw)


def _upstream_base(
    package: Path, lane: str, index: int, *, require_unresolved: bool = False
) -> tuple[
    ModuleType,
    ModuleType,
    dict[str, Any],
    list[dict[str, Any]],
    list[dict[str, Any]],
    list[dict[str, Any]],
    list[dict[str, str]],
    dict[tuple[str, str], dict[str, Any]],
    bytes,
    bytes,
]:
    compare, adjudication, manifest = _package(package)
    if lane not in LANES or not 1 <= index <= LANES[lane]:
        raise Error("packet_selector_failure")
    try:
        base = adjudication.verify_packet(package, lane, index)
        contents, grok, gemini, disagreements, _compare_receipt = adjudication.inputs(package, lane, index)
    except Error:
        raise
    except Exception as exc:
        del exc
        raise Error("upstream_packet_binding") from None
    base_labels_path, unresolved_path, base_receipt_path = _base_paths(package, lane, index)
    base_labels, _ = _read(base_labels_path)
    unresolved_value, unresolved_raw = _read(unresolved_path)
    _regular(base_receipt_path, 0o600)
    base_receipt_raw = base_receipt_path.read_bytes()
    source_rows = contents.get("rows") if isinstance(contents, dict) else None
    if (
        not isinstance(source_rows, list)
        or len(source_rows) != contents.get("row_count")
        or len(grok) != len(source_rows)
        or len(gemini) != len(source_rows)
        or not isinstance(base_labels, dict)
        or set(base_labels) != {"labels"}
        or not isinstance(base_labels["labels"], list)
        or not isinstance(unresolved_value, dict)
        or set(unresolved_value) != {"identities"}
        or not isinstance(unresolved_value["identities"], list)
    ):
        raise Error("coverage_failure")
    source_ids = _identities(source_rows)
    unresolved_ids = _identities(unresolved_value["identities"])
    accepted_ids = [_identity(item) for item in base_labels["labels"]]
    accepted_set = set(accepted_ids)
    if (
        accepted_ids != [identity for identity in source_ids if identity in accepted_set]
        or unresolved_ids != [identity for identity in source_ids if identity not in accepted_set]
        or not accepted_set.issubset(set(source_ids))
        or accepted_set.intersection(set(unresolved_ids))
        or accepted_set.union(set(unresolved_ids)) != set(source_ids)
        or len(accepted_ids) + len(unresolved_ids) != len(source_ids)
        or base.get("unresolved_count") != len(unresolved_ids)
        or len(disagreements)
        != sum(1 for left, right in zip(grok, gemini, strict=True) if compare.semantic(left) != compare.semantic(right))
    ):
        raise Error("identity_order_failure")
    if require_unresolved and not unresolved_ids:
        raise Error("no_unresolved_candidates")
    candidates: dict[tuple[str, str], tuple[dict[str, Any], dict[str, Any]]] = {}
    for source, left, right in zip(source_rows, grok, gemini, strict=True):
        key = _identity(source)
        if _identity(left) != key or _identity(right) != key or key in candidates:
            raise Error("candidate_identity_order_failure")
        candidates[key] = (left, right)
    accepted = {key: label for key, label in zip(accepted_ids, base_labels["labels"], strict=True)}
    return (
        compare,
        adjudication,
        manifest,
        source_rows,
        grok,
        gemini,
        unresolved_value["identities"],
        accepted,
        base_receipt_raw,
        unresolved_raw,
    )


def _effective(
    source_rows: list[dict[str, Any]],
    accepted: dict[tuple[str, str], dict[str, Any]],
    unresolved: list[dict[str, str]],
    grok: list[dict[str, Any]],
    gemini: list[dict[str, Any]],
    decisions: list[dict[str, str]],
) -> list[dict[str, Any]]:
    expected_unresolved = [_identity(row) for row in unresolved]
    if [_identity(row) for row in decisions] != expected_unresolved:
        raise Error("authorization_identity_order_failure")
    decision_map = {_identity(row): row["selection"] for row in decisions}
    candidates = {
        _identity(source): (left, right) for source, left, right in zip(source_rows, grok, gemini, strict=True)
    }
    result: list[dict[str, Any]] = []
    for source in source_rows:
        key = _identity(source)
        if key in accepted:
            label = accepted[key]
        elif decision_map.get(key) == "grok":
            label = candidates[key][0]
        elif decision_map.get(key) == "gemini":
            label = candidates[key][1]
        else:
            raise Error("missing_authorized_resolution")
        if label != candidates[key][0] and label != candidates[key][1]:
            raise Error("candidate_only_failure")
        result.append(label)
    if [_identity(label) for label in result] != [_identity(row) for row in source_rows]:
        raise Error("effective_identity_order_failure")
    return result


def build(
    package: Path,
    lane: str,
    index: int,
    request_path: Path,
    authorization_receipt_path: Path | None = None,
    advisor_response_path: Path | None = None,
) -> dict[str, Any]:
    try:
        if request_path.resolve(strict=True).is_relative_to(package.resolve()):
            raise Error("authorization_binding_failure")
    except OSError as exc:
        raise Error("authorization_binding_failure") from exc
    (
        _compare,
        _adjudication,
        _manifest_value,
        source_rows,
        grok,
        gemini,
        unresolved,
        accepted,
        base_receipt_raw,
        unresolved_raw,
    ) = _upstream_base(package, lane, index, require_unresolved=True)
    decisions, authority, advisor, request_raw = request(request_path, unresolved, package)
    if authorization_receipt_path is None:
        raise Error("authorization_binding_failure")
    authorization_hash = _authorization(
        authorization_receipt_path,
        package,
        request_path,
        request_raw,
        authority,
        decisions,
        advisor,
        advisor_response_path,
    )
    effective = _effective(source_rows, accepted, unresolved, grok, gemini, decisions)
    decision_path, labels_path, receipt_path = _paths(package, lane, index)
    existing = [path.exists() or path.is_symlink() for path in (decision_path, labels_path, receipt_path)]
    if any(existing):
        if not all(existing):
            raise Error("partial_resolution_seal")
        raise Error("immutable_output_exists")
    resolution_root = package / RESOLUTION_OUTPUT
    resolution_root.mkdir(parents=True, exist_ok=True, mode=0o700)
    resolution_root.chmod(0o700)
    (resolution_root / "final").mkdir(parents=True, exist_ok=True, mode=0o700)
    (resolution_root / "final").chmod(0o700)
    decision_value: dict[str, Any] = {
        "schema_version": "phase3_cycle006_operator_resolution_decisions_v2",
        "evaluation_cycle_id": CYCLE,
        "amendment_sha256": AMENDMENT_SHA256,
        "custody_receipt_raw_sha256": _package_custody(package),
        "source_label_manifest_raw_sha256": SOURCE_MANIFEST_SHA256,
        "manifest_raw_sha256": digest((package / "label-manifest.json").read_bytes()),
        "ordered_identity_commitment_sha256": ORDERED_IDENTITY_COMMITMENT_SHA256,
        "authorization_receipt_raw_sha256": authorization_hash,
        "resolutions": decisions,
    }
    if advisor is not None:
        decision_value["decision_authority"] = authority
        decision_value["advisor"] = advisor
    decision_hash = _atomic(decision_path, decision_value)
    labels_hash = _atomic(labels_path, {"labels": effective})
    receipt_schema = (
        "phase3_cycle006_designated_advisor_resolution_receipt_v2"
        if advisor is not None
        else "phase3_cycle006_operator_resolution_receipt_v2"
    )
    count_field = "designated_advisor_resolution_count" if advisor is not None else "operator_resolution_count"
    receipt: dict[str, Any] = {
        "schema_version": receipt_schema,
        "evaluation_cycle_id": CYCLE,
        "amendment_sha256": AMENDMENT_SHA256,
        "custody_receipt_raw_sha256": _package_custody(package),
        "source_label_manifest_raw_sha256": SOURCE_MANIFEST_SHA256,
        "manifest_raw_sha256": digest((package / "label-manifest.json").read_bytes()),
        "ordered_identity_commitment_sha256": ORDERED_IDENTITY_COMMITMENT_SHA256,
        "lane": lane,
        "packet_index": index,
        "row_count": len(source_rows),
        "base_final_receipt_raw_sha256": digest(base_receipt_raw),
        "base_unresolved_identities_raw_sha256": digest(unresolved_raw),
        "request_raw_sha256": digest(request_raw),
        "authorization_receipt_raw_sha256": authorization_hash,
        "decisions_sha256": decision_hash,
        "effective_labels_sha256": labels_hash,
        count_field: len(decisions),
        "accepted_count": len(effective),
        "remaining_unresolved_count": 0,
        "decision_authority": authority,
        "candidate_only": True,
        "text_free": True,
    }
    if advisor is not None:
        receipt["advisor"] = advisor
    receipt["receipt_sha256"] = digest(canonical(receipt))
    _atomic(receipt_path, receipt)
    return verify_packet(package, lane, index)


def verify_packet(package: Path, lane: str, index: int) -> dict[str, Any]:
    (
        _compare,
        _adjudication,
        _manifest_value,
        source_rows,
        grok,
        gemini,
        unresolved,
        accepted,
        base_receipt_raw,
        unresolved_raw,
    ) = _upstream_base(package, lane, index)
    decision_path, labels_path, receipt_path = _paths(package, lane, index)
    decisions, decision_raw = _read(decision_path)
    labels, labels_raw = _read(labels_path)
    receipt, receipt_raw = _read(receipt_path)
    if (
        not isinstance(decisions, dict)
        or decisions.get("schema_version") != "phase3_cycle006_operator_resolution_decisions_v2"
        or not _binding_fields(decisions, package)
        or not isinstance(labels, dict)
        or set(labels) != {"labels"}
        or not isinstance(labels["labels"], list)
        or labels_raw != canonical(labels)
        or not isinstance(receipt, dict)
        or receipt.get("evaluation_cycle_id") != CYCLE
        or receipt.get("candidate_only") is not True
        or receipt.get("remaining_unresolved_count") != 0
        or receipt.get("text_free") is not True
        or receipt.get("receipt_sha256")
        != digest(canonical({key: item for key, item in receipt.items() if key != "receipt_sha256"}))
    ):
        raise Error("resolution_receipt_failure")
    authority = decisions.get("decision_authority", "operator")
    advisor = decisions.get("advisor")
    required_decisions = {
        "schema_version",
        "evaluation_cycle_id",
        "amendment_sha256",
        "custody_receipt_raw_sha256",
        "source_label_manifest_raw_sha256",
        "manifest_raw_sha256",
        "ordered_identity_commitment_sha256",
        "authorization_receipt_raw_sha256",
        "resolutions",
    }
    if authority == "operator":
        if set(decisions) != required_decisions or advisor is not None:
            raise Error("resolution_decision_binding_failure")
    elif authority == "designated_advisor":
        if (
            set(decisions) != required_decisions | {"decision_authority", "advisor"}
            or not isinstance(advisor, dict)
            or set(advisor) != {"exact_model", "model_family", "harness", "task_id", "response_raw_sha256"}
            or advisor.get("exact_model") != "claude-fable-5"
            or advisor.get("model_family") != "anthropic"
            or advisor.get("harness") != "claude_acp"
            or any(not isinstance(advisor.get(key), str) for key in advisor)
            or len(advisor.get("response_raw_sha256", "")) != 64
            or any(character not in "0123456789abcdef" for character in advisor.get("response_raw_sha256", ""))
        ):
            raise Error("authorization_binding_failure")
    else:
        raise Error("authorization_binding_failure")
    if (
        not isinstance(decisions.get("authorization_receipt_raw_sha256"), str)
        or decisions.get("authorization_receipt_raw_sha256") != receipt.get("authorization_receipt_raw_sha256")
        or len(decisions["authorization_receipt_raw_sha256"]) != 64
        or any(character not in "0123456789abcdef" for character in decisions["authorization_receipt_raw_sha256"])
    ):
        raise Error("resolution_receipt_failure")
    if decision_raw != canonical(decisions):
        raise Error("resolution_decision_binding_failure")
    decision_rows = decisions.get("resolutions")
    if (
        not isinstance(decision_rows, list)
        or [_identity(row) for row in decision_rows] != [_identity(row) for row in unresolved]
        or any(
            not isinstance(row, dict)
            or set(row) != {"unit_id", "unit_sha256", "selection"}
            or row.get("selection") not in {"grok", "gemini"}
            for row in decision_rows
        )
    ):
        raise Error("resolution_identity_order_failure")
    expected = _effective(source_rows, accepted, unresolved, grok, gemini, decision_rows)
    if labels["labels"] != expected:
        raise Error("effective_label_drift")
    count_field = (
        "designated_advisor_resolution_count" if authority == "designated_advisor" else "operator_resolution_count"
    )
    schema_name = (
        "phase3_cycle006_designated_advisor_resolution_receipt_v2"
        if authority == "designated_advisor"
        else "phase3_cycle006_operator_resolution_receipt_v2"
    )
    expected_receipt: dict[str, Any] = {
        "schema_version": schema_name,
        "evaluation_cycle_id": CYCLE,
        "amendment_sha256": AMENDMENT_SHA256,
        "custody_receipt_raw_sha256": _package_custody(package),
        "source_label_manifest_raw_sha256": SOURCE_MANIFEST_SHA256,
        "manifest_raw_sha256": digest((package / "label-manifest.json").read_bytes()),
        "ordered_identity_commitment_sha256": ORDERED_IDENTITY_COMMITMENT_SHA256,
        "lane": lane,
        "packet_index": index,
        "row_count": len(source_rows),
        "base_final_receipt_raw_sha256": digest(base_receipt_raw),
        "base_unresolved_identities_raw_sha256": digest(unresolved_raw),
        "request_raw_sha256": receipt.get("request_raw_sha256"),
        "authorization_receipt_raw_sha256": receipt.get("authorization_receipt_raw_sha256"),
        "decisions_sha256": digest(decision_raw),
        "effective_labels_sha256": digest(labels_raw),
        count_field: len(decision_rows),
        "accepted_count": len(expected),
        "remaining_unresolved_count": 0,
        "decision_authority": authority,
        "candidate_only": True,
        "text_free": True,
    }
    if advisor is not None:
        expected_receipt["advisor"] = advisor
    if (
        not isinstance(expected_receipt["request_raw_sha256"], str)
        or len(expected_receipt["request_raw_sha256"]) != 64
        or any(character not in "0123456789abcdef" for character in expected_receipt["request_raw_sha256"])
        or not isinstance(expected_receipt["authorization_receipt_raw_sha256"], str)
        or len(expected_receipt["authorization_receipt_raw_sha256"]) != 64
        or any(
            character not in "0123456789abcdef" for character in expected_receipt["authorization_receipt_raw_sha256"]
        )
        or set(receipt) != set(expected_receipt) | {"receipt_sha256"}
        or any(receipt.get(key) != item for key, item in expected_receipt.items())
        or receipt_raw != canonical(receipt)
    ):
        raise Error("resolution_receipt_failure")
    return {
        "ok": True,
        "lane": lane,
        "packet_index": index,
        "accepted_count": len(expected),
        "remaining_unresolved_count": 0,
        "resolution_count": len(decision_rows),
        "decision_authority": authority,
        "text_free": True,
    }


def effective(package: Path, lane: str, index: int) -> dict[str, Any]:
    (
        _compare,
        _adjudication,
        _manifest_value,
        source_rows,
        _grok,
        _gemini,
        unresolved,
        accepted,
        _base_receipt_raw,
        _unresolved_raw,
    ) = _upstream_base(package, lane, index)
    paths = _paths(package, lane, index)
    present = [path.exists() or path.is_symlink() for path in paths]
    if not any(present):
        return {
            "labels": [accepted[_identity(row)] for row in source_rows if _identity(row) in accepted],
            "unresolved": unresolved,
            "accepted_count": len(accepted),
            "unresolved_count": len(unresolved),
            "operator_resolution_count": 0,
            "designated_advisor_resolution_count": 0,
        }
    if not all(present):
        raise Error("partial_resolution_seal")
    result = verify_packet(package, lane, index)
    labels, _ = _read(paths[1])
    return {
        "labels": labels["labels"],
        "unresolved": [],
        "accepted_count": result["accepted_count"],
        "unresolved_count": 0,
        "operator_resolution_count": result["resolution_count"] if result["decision_authority"] == "operator" else 0,
        "designated_advisor_resolution_count": result["resolution_count"]
        if result["decision_authority"] == "designated_advisor"
        else 0,
    }


def verify_complete(package: Path) -> dict[str, Any]:
    _package(package)
    accepted = unresolved = packets = 0
    for lane, count in LANES.items():
        for index in range(1, count + 1):
            result = effective(package, lane, index)
            accepted += result["accepted_count"]
            unresolved += result["unresolved_count"]
            packets += 1
    if packets != sum(LANES.values()) or accepted + unresolved != ROW_COUNT:
        raise Error("denominator_failure")
    return {
        "ok": unresolved == 0,
        "complete": unresolved == 0,
        "packet_count": packets,
        "row_count": ROW_COUNT,
        "accepted_count": accepted,
        "unresolved_count": unresolved,
        "residual_zero": unresolved == 0,
        "text_free": True,
    }


def _transport(ok: bool, result: dict[str, Any] | None = None, code: str | None = None) -> dict[str, Any]:
    value: dict[str, Any] = {
        "schema_version": "phase3_cycle006_operator_resolution_transport_receipt_v2",
        "evaluation_cycle_id": CYCLE,
        "amendment_sha256": AMENDMENT_SHA256,
        "ok": ok,
        "text_free": True,
    }
    if result is not None:
        for key in ("lane", "packet_index", "accepted_count", "remaining_unresolved_count"):
            if key in result:
                value[key] = result[key]
    if not ok:
        value["failure_code"] = code or "resolution_failure"
    return value


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--package", type=Path, required=True)
    parser.add_argument("--lane", choices=tuple(LANES))
    parser.add_argument("--packet-index", type=int)
    parser.add_argument("--request", type=Path)
    parser.add_argument("--authorization-receipt", type=Path)
    parser.add_argument("--advisor-response", type=Path)
    parser.add_argument("--verify-complete", action="store_true")
    args = parser.parse_args(argv)
    try:
        if args.verify_complete:
            result = verify_complete(args.package)
        elif args.lane is not None and args.packet_index is not None and args.request is not None:
            result = build(
                args.package,
                args.lane,
                args.packet_index,
                args.request,
                args.authorization_receipt,
                args.advisor_response,
            )
        else:
            raise Error("cli_selector_failure")
    except Error as exc:
        result = _transport(False, code=exc.code)
    except Exception:
        result = _transport(False, code="resolution_failure")
    else:
        result = _transport(True, result)
    print(json.dumps(result, sort_keys=True, separators=(",", ":")))
    return 0 if result.get("ok") else 2


if __name__ == "__main__":
    raise SystemExit(main())
