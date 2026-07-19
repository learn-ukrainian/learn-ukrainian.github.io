#!/usr/bin/env python3
"""Pure packet projections for bounded curriculum preparation.

Review and repair transitions remain owned by the canonical bounded-completion
helper.  This module has no transport, persistence, or controller loop.
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
    return [
        {
            "path": cell["path"],
            "source_sha256": cell["source_sha256"],
            "preparation_identity": cell["preparation_identity"],
        }
        for cell in cells
    ]


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
    if not targets:
        _fail("PACKET_EMPTY", "packet requires at least one target")
    if len(targets) > limit:
        _fail(
            "PACKET_LIMIT_EXCEEDED",
            "packet exceeds its finite limit",
            _rejection_receipt(targets, ["PACKET_LIMIT_EXCEEDED"]),
        )

    profiles: set[tuple[str, str, str, str]] = set()
    target_ids: set[str] = set()
    paths: set[str] = set()
    for target in targets:
        required = (
            "track",
            "slug",
            "profile_id",
            "profile_version",
            "family",
            "preparation_identity",
            "deterministic",
            "cells",
        )
        if not isinstance(target, Mapping) or any(field not in target for field in required):
            _fail("PACKET_TARGET_INVALID", "target is missing required fields")
        target_id = _target(target)
        if target_id in target_ids:
            _fail("PACKET_TARGET_DUPLICATE", f"duplicate target: {target_id}")
        target_ids.add(target_id)
        profiles.add(tuple(str(target[field]) for field in ("track", "profile_id", "profile_version", "family")))
        _sha(target["preparation_identity"], f"{target_id} preparation_identity")
        if not isinstance(target["deterministic"], Mapping) or not isinstance(
            target["deterministic"].get("passed"), bool
        ):
            _fail("DETERMINISTIC_RESULT_INVALID", f"{target_id} requires a boolean passed result")
        if not isinstance(target["cells"], list) or not target["cells"]:
            _fail("PACKET_TARGET_INVALID", f"{target_id} requires a finite cell list")
        for cell in target["cells"]:
            if not isinstance(cell, Mapping):
                _fail("PACKET_CELL_INVALID", f"{target_id} contains a non-object cell")
            path = cell.get("path")
            if not isinstance(path, str) or not path or path in paths:
                _fail("PACKET_CELL_INVALID", f"invalid or duplicate cell path: {path}")
            paths.add(path)
            _sha(cell.get("source_sha256"), f"{path} source_sha256")
    if len(profiles) != 1:
        _fail(
            "PACKET_HETEROGENEOUS",
            "track/profile/version/family must match",
            _rejection_receipt(targets, ["PACKET_HETEROGENEOUS"]),
        )

    deterministic_failures = [target for target in targets if target.get("deterministic", {}).get("passed") is not True]
    if deterministic_failures:
        codes = sorted(
            {
                str(code)
                for target in deterministic_failures
                for code in target.get("deterministic", {}).get("reason_codes", ["DETERMINISTIC_FAILURE"])
            }
        )
        _fail(
            "DETERMINISTIC_FAILURE",
            "local failure rejects before packet/model admission",
            _rejection_receipt(targets, codes),
        )

    prior = {(cell["target"], cell["path"]): cell for cell in prior_passes if cell.get("verdict") == "PASS"}
    scope = [
        {
            "target": _target(target),
            "profile_id": target["profile_id"],
            "profile_version": target["profile_version"],
            "family": target["family"],
            "preparation_identity": target["preparation_identity"],
        }
        for target in targets
    ]
    cells = []
    for target in targets:
        target_id = _target(target)
        for source in target["cells"]:
            previous = prior.get((target_id, source["path"]))
            reused = bool(
                previous
                and previous.get("source_sha256") == source["source_sha256"]
                and previous.get("preparation_identity") == target["preparation_identity"]
            )
            cells.append(
                {
                    "target": target_id,
                    "path": source["path"],
                    "source_sha256": source["source_sha256"],
                    "preparation_identity": target["preparation_identity"],
                    "reused_pass": reused,
                }
            )
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
    """Hash the packet's exact ordered source and preparation identities."""

    return bounded_completion.sha256_json(
        [
            {key: cell[key] for key in ("target", "path", "source_sha256", "preparation_identity")}
            for cell in packet["cells"]
        ]
    )


def select_review_paths(
    packet: Mapping[str, Any],
    *,
    phase: str,
    failed_paths: Sequence[str] = (),
    changed_paths: Sequence[str] = (),
    pass_paths: Sequence[str] = (),
    requested_paths: Sequence[str] | None = None,
) -> list[str]:
    """Select INITIAL non-reused or FINAL changed-and-failed cells exactly."""

    if phase == "INITIAL":
        eligible = [cell["path"] for cell in packet["cells"] if not cell["reused_pass"]]
    elif phase == "FINAL":
        failed = set(failed_paths)
        changed = set(changed_paths)
        eligible = [cell["path"] for cell in packet["cells"] if cell["path"] in failed & changed]
    else:
        _fail("REVIEW_PHASE_INVALID", f"unsupported review phase: {phase}")
    selected = list(eligible if requested_paths is None else requested_paths)
    if len(selected) == 1 and selected[0] in set(pass_paths) and selected[0] not in set(changed_paths):
        _fail("UNCHANGED_PASS_SINGLETON_REVIEW", "unchanged PASS singleton re-review is forbidden")
    if not selected or selected != eligible:
        _fail("REVIEW_SCOPE_INVALID", f"{phase} review must use exact eligible paths")
    return selected


def pending_dispatch_receipt(
    packet: Mapping[str, Any],
    run: Mapping[str, Any],
    *,
    phase: str,
    paths: Sequence[str],
) -> dict[str, Any]:
    """Project the compact receipt that callers persist before dispatch."""

    if phase not in {"INITIAL", "FINAL"}:
        _fail("REVIEW_PHASE_INVALID", f"unsupported review phase: {phase}")
    selected = [cell for path in paths for cell in packet["cells"] if cell["path"] == path]
    if len(selected) != len(paths):
        _fail("REVIEW_SCOPE_INVALID", "pending receipt contains an unknown path")
    return {
        "phase": phase,
        "paths": list(paths),
        "hashes": _cell_hashes(selected),
        "reason_codes": ["INITIAL_NON_REUSED_ONLY" if phase == "INITIAL" else "FINAL_CHANGED_FAILED_ONLY"],
        "counts": {
            "model_calls": run["measurements"]["model_call_count"] + 1,
            "repairs": run["measurements"]["repair_count"],
        },
    }


def terminal_hold_receipt(
    packet: Mapping[str, Any],
    run: Mapping[str, Any],
    *,
    failed_paths: Sequence[str],
    blockers: Sequence[Mapping[str, str]],
    date: str,
    evidence_url: str,
    token_count: int | None = None,
    cost_usd: float | None = None,
) -> dict[str, Any]:
    """Project canonical per-target HOLD payloads after helper exhaustion."""

    if not run["terminal"] or run["measurements"]["final_quality_disposition"] != "BLOCKED_BUDGET_EXHAUSTED":
        _fail("HOLD_NOT_AUTHORIZED", "canonical helper has not exhausted the review budget")
    fields = ("path", "reason_code", "reason", "owner", "evidence", "unblock_condition")
    if [item.get("path") for item in blockers] != list(failed_paths) or any(
        not all(item.get(field) for field in fields) for item in blockers
    ):
        _fail("BLOCKER_LEDGER_INCOMPLETE", "every failed path requires complete blocker evidence")
    if not date or not evidence_url.startswith(("http://", "https://")):
        _fail("HOLD_RECEIPT_INCOMPLETE", "date and HTTP(S) reviewed evidence URL are required")

    by_path = {item["path"]: item for item in blockers}
    failed_cells = [cell for cell in packet["cells"] if cell["path"] in failed_paths]
    if [cell["path"] for cell in failed_cells] != list(failed_paths):
        _fail("HOLD_RECEIPT_INCOMPLETE", "failed paths must be exact packet paths in order")
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
        "paths": list(failed_paths),
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
