#!/usr/bin/env python3
"""Verify the single Phase 3 anti-grinding entropy receipt contract.

This module verifies a nonce *reveal* against a separately committed,
nonce-free artifact.  It never creates a nonce, searches seed preimages,
selects an auditor, or retries a draw.
"""

from __future__ import annotations

import hashlib
import json
import re
import subprocess
from collections.abc import Mapping
from pathlib import Path, PurePosixPath
from typing import Any

from jsonschema import Draft202012Validator

from scripts.projects.open_model_data import phase3_functional_roles as functional_roles

ROOT = Path(__file__).resolve().parents[3]
SCHEMA_PATH = ROOT / "data/projects/open_model_data/contracts/phase3_audit_entropy_receipt_v1.schema.json"
SCHEMA_VERSION = "phase3_audit_entropy_receipt_v1"
COMMITMENT_SCHEMA_VERSION = "phase3_audit_entropy_commitment_v1"
COMMITMENT_DIRECTORY = "data/projects/open_model_data/audit_entropy_commitments"
SHA256 = re.compile(r"^[a-f0-9]{64}$")
SHA1 = re.compile(r"^[a-f0-9]{40}$")


class AuditEntropyError(ValueError):
    """An entropy receipt is incomplete, mutable, or not first-contained."""


def canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"), sort_keys=True)


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise AuditEntropyError(message)


def _read_schema() -> dict[str, Any]:
    try:
        value = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise AuditEntropyError("approved entropy receipt schema is unavailable") from exc
    _require(isinstance(value, dict), "approved entropy receipt schema is invalid")
    return value


def _validate_schema(value: Mapping[str, Any], definition: str, label: str) -> dict[str, Any]:
    schema = _read_schema()
    wrapper = {"$schema": schema["$schema"], "$defs": schema["$defs"], "$ref": f"#/$defs/{definition}"}
    Draft202012Validator.check_schema(wrapper)
    errors = sorted(Draft202012Validator(wrapper).iter_errors(dict(value)), key=lambda error: list(error.path))
    _require(not errors, f"{label} schema violation")
    return dict(value)


def _git(repo_root: Path, *args: str, check: bool = True) -> bytes:
    completed = subprocess.run(
        ["git", "-C", str(repo_root), *args],
        check=False,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
    )
    if check and completed.returncode != 0:
        raise AuditEntropyError("required local git object is unavailable")
    return completed.stdout if completed.returncode == 0 else b""


def _git_ok(repo_root: Path, *args: str) -> bool:
    return subprocess.run(
        ["git", "-C", str(repo_root), *args],
        check=False,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    ).returncode == 0


def _safe_repo_path(value: str) -> str:
    path = PurePosixPath(value)
    _require(not path.is_absolute() and value != "." and ".." not in path.parts, "artifact path escapes repository")
    _require(all(part not in {"", ".", ".git"} for part in path.parts), "artifact path is invalid")
    return path.as_posix()


def _first_parent_path_history(repo_root: Path, path: str) -> list[str]:
    """Return only mainline commits that changed ``path``, oldest first."""
    history = _git(
        repo_root, "log", "--first-parent", "--full-history", "--reverse", "--format=%H", "refs/remotes/origin/main", "--", path,
    ).decode("ascii").splitlines()
    _require(bool(history), "origin/main path history is unavailable")
    return history


def _artifact_at(repo_root: Path, commit: str, path: str) -> bytes | None:
    if not _git_ok(repo_root, "cat-file", "-e", f"{commit}:{path}"):
        return None
    return _git(repo_root, "show", f"{commit}:{path}")


def _verify_first_containing(
    *, repo_root: Path, path: str, expected_sha256: str, declared_commit: str, require_first_path_introduction: bool,
) -> int:
    """Prove the declared commit is the first mainline commit with path/bytes."""
    _require(SHA1.fullmatch(declared_commit) is not None, "first-containing commit SHA is invalid")
    _require(_git_ok(repo_root, "merge-base", "--is-ancestor", declared_commit, "refs/remotes/origin/main"), "declared commit is not reachable from origin/main")
    history = _first_parent_path_history(repo_root, path)
    _require(declared_commit in history, "declared commit is not on origin/main first-parent path history")
    matches = [
        index for index, commit in enumerate(history)
        if (artifact := _artifact_at(repo_root, commit, path)) is not None and sha256_bytes(artifact) == expected_sha256
    ]
    _require(bool(matches), "declared artifact bytes are absent from origin/main")
    declared_index = history.index(declared_commit)
    _require(matches[0] == declared_index, "declared commit is not the true first-containing commit")
    if require_first_path_introduction:
        _require(
            all(_artifact_at(repo_root, commit, path) is None for commit in history[:declared_index]),
            "deterministic commitment path was previously introduced",
        )
    return declared_index


def _expected_functional_binding(role_id: str, task_id: str) -> dict[str, str]:
    try:
        ledger = functional_roles.verify_value(functional_roles.read_json(functional_roles.LEDGER_PATH))
        binding = functional_roles.binding_for_role(ledger, role_id)
    except functional_roles.FunctionalRoleError as exc:
        raise AuditEntropyError("functional-role ledger is unavailable or invalid") from exc
    _require(binding["task_id"] == task_id, "entropy commitment auditor role/task binding drift")
    return {
        "base_contract_sha256": functional_roles.BASE_SHA256,
        "amendment_sha256": functional_roles.AMENDMENT_SHA256,
        "combined_contract_sha256": functional_roles.COMBINED_SHA256,
        "functional_role_contract_sha256": functional_roles.sha256_file(functional_roles.LEDGER_PATH),
        "conflict_graph_sha256": functional_roles.conflict_graph_sha256(ledger),
        "evaluation_cycle_id": str(ledger["evaluation_cycle"]["evaluation_cycle_id"]),
    }


def _pre_nonce_binding(commitment: Mapping[str, Any]) -> dict[str, Any]:
    return {
        key: commitment[key]
        for key in (
            "schema_version", "purpose", "frozen_universe_sha256", "frozen_population_sha256",
            "sampler_plan_path", "sampler_plan_sha256", "sampler_plan_first_containing_merge_sha",
            "auditor_role_id", "auditor_task_id", "base_contract_sha256", "amendment_sha256",
            "combined_contract_sha256", "functional_role_contract_sha256", "conflict_graph_sha256",
            "evaluation_cycle_id", "author_or_root_choices", "root_choice_count", "reroll_count",
        )
    }


def commitment_path_for(binding: Mapping[str, Any]) -> str:
    """Return the one permitted path for a fixed pre-nonce audit binding."""
    return f"{COMMITMENT_DIRECTORY}/{sha256_bytes(canonical_json(dict(binding)).encode('utf-8'))}.json"


def _read_commitment(repo_root: Path, receipt: Mapping[str, Any]) -> tuple[dict[str, Any], bytes]:
    path = _safe_repo_path(str(receipt["commitment_path"]))
    commit = str(receipt["commitment_first_containing_merge_sha"])
    payload = _artifact_at(repo_root, commit, path)
    _require(payload is not None, "nonce commitment artifact is missing")
    _require(sha256_bytes(payload) == receipt["commitment_sha256"], "nonce commitment bytes do not match receipt")
    try:
        value = json.loads(payload.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise AuditEntropyError("nonce commitment artifact is not JSON") from exc
    _require(isinstance(value, dict), "nonce commitment artifact is not an object")
    commitment = _validate_schema(value, "commitment", "nonce commitment")
    _require(commitment["schema_version"] == COMMITMENT_SCHEMA_VERSION and commitment["text_free"] is True, "nonce commitment is not text-free v1")
    return commitment, payload


def verify_entropy_receipt(
    receipt: Mapping[str, Any],
    *,
    purpose: str,
    frozen_bundle_sha256: str,
    frozen_population_sha256: str,
    auditor_role_id: str,
    auditor_task_id: str,
    repo_root: Path = ROOT,
) -> dict[str, str]:
    """Verify one nonce reveal against its earlier immutable commitment."""
    _require(isinstance(receipt, Mapping), "approved entropy receipt must be an object")
    for value in (frozen_bundle_sha256, frozen_population_sha256):
        _require(isinstance(value, str) and SHA256.fullmatch(value) is not None, "caller supplied invalid frozen hash")
    _require(repo_root.is_dir(), "repository root is unavailable")
    reveal = _validate_schema(receipt, "reveal", "approved entropy receipt")
    _require(reveal["schema_version"] == SCHEMA_VERSION and reveal["text_free"] is True, "entropy receipt is not text-free v1")
    commitment_path = _safe_repo_path(str(reveal["commitment_path"]))
    _verify_first_containing(
        repo_root=repo_root,
        path=commitment_path,
        expected_sha256=str(reveal["commitment_sha256"]),
        declared_commit=str(reveal["commitment_first_containing_merge_sha"]),
        require_first_path_introduction=True,
    )
    commitment, _ = _read_commitment(repo_root, reveal)
    _require(commitment["purpose"] == purpose, "entropy commitment purpose drift")
    _require(commitment["frozen_universe_sha256"] == frozen_bundle_sha256, "entropy commitment frozen universe drift")
    _require(commitment["frozen_population_sha256"] == frozen_population_sha256, "entropy commitment frozen population drift")
    _require(commitment["auditor_role_id"] == auditor_role_id and commitment["auditor_task_id"] == auditor_task_id, "entropy commitment auditor role/task drift")
    expected = _expected_functional_binding(auditor_role_id, auditor_task_id)
    _require(all(commitment[key] == expected[key] for key in expected), "entropy commitment functional-role binding drift")
    pre_nonce_binding = _pre_nonce_binding(commitment)
    _require(commitment["pre_nonce_binding_sha256"] == sha256_bytes(canonical_json(pre_nonce_binding).encode("utf-8")), "pre-nonce binding hash drift")
    _require(commitment_path == commitment_path_for(pre_nonce_binding), "commitment path is not deterministic for its pre-nonce binding")
    plan_path = _safe_repo_path(str(commitment["sampler_plan_path"]))
    _verify_first_containing(
        repo_root=repo_root,
        path=plan_path,
        expected_sha256=str(commitment["sampler_plan_sha256"]),
        declared_commit=str(commitment["sampler_plan_first_containing_merge_sha"]),
        require_first_path_introduction=False,
    )
    _require(
        commitment["sampler_plan_first_containing_merge_sha"] != reveal["commitment_first_containing_merge_sha"]
        and _git_ok(
            repo_root,
            "merge-base",
            "--is-ancestor",
            str(commitment["sampler_plan_first_containing_merge_sha"]),
            str(reveal["commitment_first_containing_merge_sha"]),
        ),
        "sampler plan was not committed before nonce commitment",
    )
    _require(
        commitment["auditor_nonce_commitment_sha256"] == sha256_bytes(reveal["auditor_nonce"].encode("ascii")),
        "auditor nonce does not open prior commitment",
    )
    canonical_tuple = {
        "commitment_sha256": reveal["commitment_sha256"],
        "commitment_first_containing_merge_sha": reveal["commitment_first_containing_merge_sha"],
        "pre_nonce_binding_sha256": commitment["pre_nonce_binding_sha256"],
        "auditor_nonce_commitment_sha256": commitment["auditor_nonce_commitment_sha256"],
    }
    return {
        "derived_seed": sha256_bytes(bytes.fromhex(commitment["frozen_universe_sha256"]) + bytes.fromhex(reveal["auditor_nonce"])),
        "entropy_receipt_sha256": sha256_bytes(canonical_json(reveal).encode("utf-8")),
        "first_containing_merge_sha": str(reveal["commitment_first_containing_merge_sha"]),
        "canonical_tuple_sha256": sha256_bytes(canonical_json(canonical_tuple).encode("utf-8")),
    }
