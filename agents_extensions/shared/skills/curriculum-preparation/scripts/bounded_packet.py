#!/usr/bin/env python3
"""Pure packet projections for bounded curriculum preparation.

Review and repair transitions remain owned by the canonical bounded-completion
helper. This module has no transport, persistence, or controller loop.
"""

from __future__ import annotations

import importlib.util
import sys
from collections.abc import Mapping, Sequence
from copy import deepcopy
from pathlib import Path
from typing import Any

_HELPER = Path(__file__).resolve().parents[2] / "track-completion/scripts/bounded_completion.py"
_SPEC = importlib.util.spec_from_file_location("preparation_bounded_completion", _HELPER)
if _SPEC is None or _SPEC.loader is None:  # pragma: no cover - broken installation
    raise RuntimeError(f"Cannot load bounded-completion helper: {_HELPER}")
bounded_completion = importlib.util.module_from_spec(_SPEC)
sys.modules[_SPEC.name] = bounded_completion
_SPEC.loader.exec_module(bounded_completion)

_SCOPE_FIELDS = ("target", "profile_id", "profile_version", "family", "manifest_sha256")
_HASH_FIELDS = ("path", "source_sha256", "preparation_identity")


class PreparationPacketError(RuntimeError):
    """Fail-closed packet rejection with an optional compact receipt."""

    def __init__(self, code: str, message: str, receipt: Mapping[str, Any] | None = None) -> None:
        self.code = code
        self.receipt = deepcopy(dict(receipt)) if receipt else None
        super().__init__(f"[{code}] {message}")


def _fail(code: str, message: str, receipt: Mapping[str, Any] | None = None) -> None:
    raise PreparationPacketError(code, message, receipt)


def _sha(value: object, label: str) -> str:
    if not (
        isinstance(value, str) and len(value) == 64 and all(character in "0123456789abcdef" for character in value)
    ):
        _fail("IDENTITY_INVALID", f"{label} must be a lowercase SHA-256")
    return value


def _target(target: Mapping[str, Any]) -> str:
    return f"{target['track']}/{target['slug']}"


def _cell_hashes(cells: Sequence[Mapping[str, Any]]) -> list[dict[str, str]]:
    return [{field: cell[field] for field in _HASH_FIELDS} for cell in cells]


def _source_identity(scope: Sequence[Mapping[str, Any]], cells: Sequence[Mapping[str, Any]]) -> str:
    return bounded_completion.sha256_json(
        {
            "scope": list(scope),
            "cells": [
                {
                    "target": cell["target"],
                    **{field: cell[field] for field in _HASH_FIELDS},
                }
                for cell in cells
            ],
        }
    )


def _rejection_receipt(targets: Sequence[Mapping[str, Any]], reason_codes: Sequence[str]) -> dict[str, Any]:
    cells = [
        {
            "path": cell.get("path"),
            "source_sha256": cell.get("source_sha256"),
            "preparation_identity": target.get("preparation_identity"),
        }
        for target in targets
        for cell in target.get("cells", [])
    ]
    return {
        "paths": [cell["path"] for cell in cells],
        "hashes": cells,
        "reason_codes": list(reason_codes),
        "counts": {"model_calls": 0, "repairs": 0},
    }


def admit_packet(
    targets: Sequence[Mapping[str, Any]],
    *,
    limit: int,
    prior_passes: Sequence[Mapping[str, Any]] = (),
) -> dict[str, Any]:
    """Admit one finite homogeneous packet and mark only exact PASS reuse."""

    if isinstance(limit, bool) or not isinstance(limit, int) or limit <= 0:
        _fail("PACKET_LIMIT_INVALID", "limit must be a positive integer")
    if not targets or any(not isinstance(target, Mapping) for target in targets):
        _fail("PACKET_EMPTY", "packet requires at least one target")
    if len(targets) > limit:
        _fail(
            "PACKET_LIMIT_EXCEEDED",
            "packet exceeds its finite limit",
            _rejection_receipt(targets, ["PACKET_LIMIT_EXCEEDED"]),
        )

    scope: list[dict[str, str]] = []
    cells: list[dict[str, Any]] = []
    deterministic_failures: list[Mapping[str, Any]] = []
    try:
        for target in targets:
            target_id = _target(target)
            manifest = _sha(target["manifest_sha256"], f"{target_id} manifest_sha256")
            preparation = _sha(target["preparation_identity"], f"{target_id} preparation_identity")
            scope.append(
                {
                    "target": target_id,
                    "profile_id": str(target["profile_id"]),
                    "profile_version": str(target["profile_version"]),
                    "family": str(target["family"]),
                    "manifest_sha256": manifest,
                }
            )
            deterministic = target["deterministic"]
            if not isinstance(deterministic, Mapping) or not isinstance(deterministic.get("passed"), bool):
                _fail("DETERMINISTIC_RESULT_INVALID", f"{target_id} requires a boolean passed result")
            if not deterministic["passed"]:
                deterministic_failures.append(target)
            sources = target["cells"]
            if not isinstance(sources, list) or not sources:
                _fail("PACKET_TARGET_INVALID", f"{target_id} requires a finite cell list")
            for source in sources:
                path = source["path"]
                cells.append(
                    {
                        "target": target_id,
                        "path": path,
                        "source_sha256": _sha(source["source_sha256"], f"{path} source_sha256"),
                        "preparation_identity": preparation,
                    }
                )
    except (KeyError, TypeError) as exc:
        _fail("PACKET_TARGET_INVALID", f"packet target/cell is malformed: {exc}")

    target_ids = [entry["target"] for entry in scope]
    paths = [cell["path"] for cell in cells]
    if len(set(target_ids)) != len(target_ids):
        _fail("PACKET_TARGET_DUPLICATE", "packet targets must be unique")
    if len(set(paths)) != len(paths) or any(not isinstance(path, str) or not path for path in paths):
        _fail("PACKET_CELL_INVALID", "packet cell paths must be non-empty and unique")
    if (
        len({entry["target"].split("/", maxsplit=1)[0] for entry in scope}) != 1
        or len({tuple(entry[field] for field in _SCOPE_FIELDS if field != "target") for entry in scope}) != 1
    ):
        _fail(
            "PACKET_HETEROGENEOUS",
            "track/profile/version/family/manifest must match",
            _rejection_receipt(targets, ["PACKET_HETEROGENEOUS"]),
        )

    if deterministic_failures:
        codes = sorted(
            {
                str(code)
                for target in deterministic_failures
                for code in target["deterministic"].get("reason_codes", ["DETERMINISTIC_FAILURE"])
            }
        ) or ["DETERMINISTIC_FAILURE"]
        _fail(
            "DETERMINISTIC_FAILURE",
            "local failure rejects before packet/model admission",
            _rejection_receipt(targets, codes),
        )

    prior = {(cell["target"], cell["path"]): cell for cell in prior_passes if cell.get("verdict") == "PASS"}
    scope_by_target = {entry["target"]: entry for entry in scope}
    for cell in cells:
        binding = {**scope_by_target[cell["target"]], **{field: cell[field] for field in _HASH_FIELDS}}
        previous = prior.get((cell["target"], cell["path"]))
        cell["reused_pass"] = bool(previous and all(previous.get(field) == value for field, value in binding.items()))
    return {
        "scope": scope,
        "scope_sha256": bounded_completion.sha256_json(scope),
        "paths": [cell["path"] for cell in cells],
        "hashes": _cell_hashes(cells),
        "reason_codes": ["EXACT_PASS_REUSED"] if any(cell["reused_pass"] for cell in cells) else [],
        "counts": {
            "model_calls": 0,
            "repairs": 0,
            "reused_pass_cells": sum(cell["reused_pass"] for cell in cells),
        },
        "cells": cells,
    }


def source_identity(packet: Mapping[str, Any]) -> str:
    """Hash exact immutable scope plus ordered source/preparation cells."""

    return _source_identity(packet["scope"], packet["cells"])


def _receipt_cells(packet: Mapping[str, Any], receipt: Mapping[str, Any]) -> list[dict[str, str]]:
    paths = receipt.get("paths")
    hashes = receipt.get("hashes")
    if (
        not isinstance(paths, list)
        or not isinstance(hashes, list)
        or any(not isinstance(path, str) for path in paths)
        or any(not isinstance(item, Mapping) for item in hashes)
        or len(set(paths)) != len(paths)
        or [item.get("path") for item in hashes] != paths
    ):
        _fail("PENDING_RECEIPT_INVALID", "pending paths and hashes must match exactly")
    current = {cell["path"]: cell for cell in packet["cells"]}
    if any(path not in current for path in paths):
        _fail("PENDING_RECEIPT_INVALID", "pending receipt contains an unknown packet path")
    return [
        {
            "target": current[item["path"]]["target"],
            "path": item["path"],
            "source_sha256": _sha(item.get("source_sha256"), "pending source_sha256"),
            "preparation_identity": _sha(item.get("preparation_identity"), "pending preparation_identity"),
        }
        for item in hashes
    ]


def pending_dispatch_receipt(
    packet: Mapping[str, Any],
    run: Mapping[str, Any],
    *,
    initial_receipt: Mapping[str, Any] | None = None,
    blocker_paths: Sequence[str] = (),
) -> dict[str, Any]:
    """Derive phase and exact eligible paths, then project pre-dispatch proof."""

    active_source = source_identity(packet)
    if active_source != run.get("learner_source_sha256"):
        _fail("PACKET_RUN_SOURCE_DRIFT", "packet identity differs from the canonical bounded run")
    protocol = run.get("review_protocol_identity")
    if not isinstance(protocol, Mapping):
        _fail("PACKET_RUN_PROTOCOL_INVALID", "bounded run lacks a frozen protocol identity")
    try:
        phase = bounded_completion.semantic_review_phase(
            run,
            review_protocol_identity=protocol,
            learner_source_sha256=active_source,
        )
    except bounded_completion.BoundedCompletionError as exc:
        _fail(exc.code, str(exc))

    if phase == "INITIAL":
        if initial_receipt is not None or blocker_paths:
            _fail("INITIAL_RECEIPT_UNEXPECTED", "INITIAL dispatch cannot consume prior review authority")
        selected = [cell for cell in packet["cells"] if not cell["reused_pass"]]
    else:
        if initial_receipt is None or initial_receipt.get("phase") != "INITIAL":
            _fail("INITIAL_RECEIPT_REQUIRED", "FINAL dispatch requires the persisted INITIAL receipt")
        if initial_receipt.get("scope_sha256") != packet["scope_sha256"]:
            _fail("INITIAL_RECEIPT_SCOPE_DRIFT", "INITIAL receipt scope differs from the current packet")
        if initial_receipt.get("protocol_identity_sha256") != protocol["identity_sha256"]:
            _fail("INITIAL_RECEIPT_PROTOCOL_DRIFT", "INITIAL receipt protocol differs from the bounded run")
        if initial_receipt.get("paths") != [cell["path"] for cell in packet["cells"] if not cell["reused_pass"]]:
            _fail("INITIAL_RECEIPT_SCOPE_DRIFT", "INITIAL receipt does not cover exact non-reused cells")
        reviewed_cells = _receipt_cells(packet, initial_receipt)
        prior_hashes = {cell["path"]: cell for cell in reviewed_cells}
        initial_cells = [
            {
                **cell,
                **{
                    field: prior_hashes.get(cell["path"], cell)[field]
                    for field in ("source_sha256", "preparation_identity")
                },
            }
            for cell in packet["cells"]
        ]
        if _source_identity(packet["scope"], initial_cells) != initial_receipt.get("reviewed_source_identity"):
            _fail("INITIAL_RECEIPT_IDENTITY_INVALID", "INITIAL receipt hashes do not reproduce its identity")
        initial_review = run["reviews"][0] if run.get("reviews") else None
        if not initial_review or initial_review["learner_source_sha256"] != initial_receipt["reviewed_source_identity"]:
            _fail("INITIAL_RECEIPT_IDENTITY_INVALID", "INITIAL receipt is not bound to canonical review evidence")
        expected_blockers = [path for path in initial_receipt["paths"] if path in set(blocker_paths)]
        if not blocker_paths or list(blocker_paths) != expected_blockers:
            _fail("BLOCKER_SCOPE_INVALID", "blocker paths must be an ordered subset of INITIAL paths")
        selected = [
            cell
            for cell in packet["cells"]
            if cell["path"] in blocker_paths
            and any(
                cell[field] != prior_hashes[cell["path"]][field] for field in ("source_sha256", "preparation_identity")
            )
        ]
        if len(selected) != len(blocker_paths):
            _fail("FINAL_REVIEW_NO_HASH_CHANGE", "every initially failed cell requires an exact hash change")

    return {
        "phase": phase,
        "scope_sha256": packet["scope_sha256"],
        "reviewed_source_identity": active_source,
        "protocol_identity_sha256": protocol["identity_sha256"],
        "paths": [cell["path"] for cell in selected],
        "hashes": _cell_hashes(selected),
        "reason_codes": ["INITIAL_NON_REUSED_ONLY" if phase == "INITIAL" else "FINAL_HASH_CHANGED_BLOCKERS_ONLY"],
        "counts": {
            "model_calls": run["measurements"]["model_call_count"] + 1,
            "repairs": run["measurements"]["repair_count"],
        },
    }


def terminal_hold_receipt(
    packet: Mapping[str, Any],
    run: Mapping[str, Any],
    *,
    final_receipt: Mapping[str, Any],
    blockers: Sequence[Mapping[str, str]],
    date: str,
    evidence_url: str,
    still_failing_paths: Sequence[str] | None = None,
    token_count: int | None = None,
    cost_usd: float | None = None,
) -> dict[str, Any]:
    """Project per-target HOLDs only from the exact FINAL reviewed scope."""

    if not run["terminal"] or run["measurements"]["final_quality_disposition"] != "BLOCKED_BUDGET_EXHAUSTED":
        _fail("HOLD_NOT_AUTHORIZED", "canonical helper has not exhausted the review budget")
    if final_receipt.get("phase") != "FINAL":
        _fail("HOLD_SCOPE_INVALID", "terminal HOLD requires the FINAL pending receipt")
    if (
        final_receipt.get("scope_sha256") != packet["scope_sha256"]
        or final_receipt.get("reviewed_source_identity") != source_identity(packet)
        or final_receipt.get("reviewed_source_identity") != run["learner_source_sha256"]
        or final_receipt.get("protocol_identity_sha256") != run["review_protocol_identity"]["identity_sha256"]
        or final_receipt.get("counts")
        != {
            "model_calls": run["measurements"]["model_call_count"],
            "repairs": run["measurements"]["repair_count"],
        }
    ):
        _fail("PENDING_RECEIPT_STALE", "FINAL receipt is not bound to the terminal packet/run")
    reviewed_cells = _receipt_cells(packet, final_receipt)
    current = {cell["path"]: cell for cell in packet["cells"]}
    if any(any(cell[field] != current[cell["path"]][field] for field in _HASH_FIELDS) for cell in reviewed_cells):
        _fail("PENDING_RECEIPT_STALE", "FINAL receipt hashes differ from the terminal packet")
    final_paths = final_receipt["paths"]
    failed_paths = list(final_paths if still_failing_paths is None else still_failing_paths)
    if not failed_paths or failed_paths != [path for path in final_paths if path in set(failed_paths)]:
        _fail("HOLD_SCOPE_INVALID", "HOLD paths must be an ordered FINAL-reviewed subset")

    fields = ("path", "reason_code", "reason", "owner", "evidence", "unblock_condition")
    if [item.get("path") for item in blockers] != failed_paths or any(
        not all(item.get(field) for field in fields) for item in blockers
    ):
        _fail("BLOCKER_LEDGER_INCOMPLETE", "blockers must match every HOLD path exactly")
    if not date or not evidence_url.startswith(("http://", "https://")):
        _fail("HOLD_RECEIPT_INCOMPLETE", "date and HTTP(S) reviewed evidence URL are required")

    by_path = {item["path"]: item for item in blockers}
    failed_cells = [current[path] for path in failed_paths]
    holds: dict[str, dict[str, Any]] = {}
    for target in dict.fromkeys(cell["target"] for cell in failed_cells):
        target_cells = [cell for cell in failed_cells if cell["target"] == target]
        target_blockers = [by_path[cell["path"]] for cell in target_cells]
        holds[target] = {
            "status": "pass",
            "reviewer_family": run["review_protocol_identity"]["reviewer_family"],
            "date": date,
            "evidence_url": evidence_url,
            "active": True,
            "reason": "; ".join(dict.fromkeys(item["reason"] for item in target_blockers)),
            "owner": "; ".join(dict.fromkeys(item["owner"] for item in target_blockers)),
            "checked_evidence": [
                f"{by_path[cell['path']]['evidence']}; {cell['path']} sha256={cell['source_sha256']}"
                for cell in target_cells
            ],
            "unblock_condition": "; ".join(dict.fromkeys(item["unblock_condition"] for item in target_blockers)),
        }
    receipt: dict[str, Any] = {
        "next_action": "stop",
        "paths": failed_paths,
        "hashes": _cell_hashes(failed_cells),
        "reason_codes": ["PREPARATION_REVIEW_BUDGET_EXHAUSTED", "PREPARATION_HOLD_ACTIVE"],
        "counts": {
            "model_calls": run["measurements"]["model_call_count"],
            "repairs": run["measurements"]["repair_count"],
        },
        "holds": holds,
    }
    if token_count is not None:
        receipt["token_count"] = token_count
    if cost_usd is not None:
        receipt["cost_usd"] = cost_usd
    return receipt
