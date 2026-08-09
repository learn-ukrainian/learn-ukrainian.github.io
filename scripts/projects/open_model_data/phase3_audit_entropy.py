#!/usr/bin/env python3
"""Verify the single Phase 3 anti-grinding entropy receipt contract.

The verifier only checks an auditor-supplied receipt.  It never creates a
nonce, searches seed preimages, selects an auditor, or retries a draw.
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


def _validate_receipt_shape(receipt: Mapping[str, Any]) -> dict[str, Any]:
    value = dict(receipt)
    schema = _read_schema()
    Draft202012Validator.check_schema(schema)
    errors = sorted(Draft202012Validator(schema).iter_errors(value), key=lambda error: list(error.path))
    _require(not errors, "approved entropy receipt schema violation")
    return value


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
    completed = subprocess.run(
        ["git", "-C", str(repo_root), *args],
        check=False,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    return completed.returncode == 0


def _safe_repo_path(value: str) -> str:
    path = PurePosixPath(value)
    _require(not path.is_absolute() and value != "." and ".." not in path.parts, "frozen artifact path escapes repository")
    _require(all(part not in {"", ".", ".git"} for part in path.parts), "frozen artifact path is invalid")
    return path.as_posix()


def _verify_first_containing_artifact(
    receipt: Mapping[str, Any], *, repo_root: Path,
) -> None:
    commit = str(receipt["first_containing_merge_sha"])
    artifact_path = _safe_repo_path(str(receipt["frozen_artifact_path"]))
    _require(SHA1.fullmatch(commit) is not None, "first-containing commit SHA is invalid")
    _require(repo_root.is_dir(), "repository root is unavailable")
    _git(repo_root, "cat-file", "-e", f"{commit}^{{commit}}")
    _require(_git_ok(repo_root, "merge-base", "--is-ancestor", commit, "refs/remotes/origin/main"), "declared commit is not reachable from origin/main")
    first_parent_commits = _git(repo_root, "rev-list", "--first-parent", "refs/remotes/origin/main").decode("ascii").splitlines()
    _require(commit in first_parent_commits, "declared commit is not on origin/main first-parent history")
    artifact = _git(repo_root, "show", f"{commit}:{artifact_path}")
    _require(sha256_bytes(artifact) == receipt["frozen_artifact_sha256"], "frozen artifact bytes do not match receipt")
    parent = _git(repo_root, "rev-parse", f"{commit}^").decode("ascii").strip()
    if _git_ok(repo_root, "cat-file", "-e", f"{parent}:{artifact_path}"):
        parent_artifact = _git(repo_root, "show", f"{parent}:{artifact_path}")
        _require(sha256_bytes(parent_artifact) != receipt["frozen_artifact_sha256"], "first parent already contains frozen artifact")


def _expected_functional_binding(role_id: str, task_id: str) -> dict[str, str]:
    try:
        ledger = functional_roles.verify_value(functional_roles.read_json(functional_roles.LEDGER_PATH))
        binding = functional_roles.binding_for_role(ledger, role_id)
    except functional_roles.FunctionalRoleError as exc:
        raise AuditEntropyError("functional-role ledger is unavailable or invalid") from exc
    _require(binding["task_id"] == task_id, "entropy receipt auditor role/task binding drift")
    return {
        "base_contract_sha256": functional_roles.BASE_SHA256,
        "amendment_sha256": functional_roles.AMENDMENT_SHA256,
        "combined_contract_sha256": functional_roles.COMBINED_SHA256,
        "functional_role_contract_sha256": functional_roles.sha256_file(functional_roles.LEDGER_PATH),
        "conflict_graph_sha256": functional_roles.conflict_graph_sha256(ledger),
        "evaluation_cycle_id": str(ledger["evaluation_cycle"]["evaluation_cycle_id"]),
    }


def _canonical_tuple(receipt: Mapping[str, Any]) -> dict[str, Any]:
    return {
        key: receipt[key]
        for key in (
            "schema_version", "purpose", "frozen_universe_sha256", "frozen_population_sha256",
            "sampler_plan_sha256", "frozen_artifact_path", "frozen_artifact_sha256", "auditor_role_id",
            "auditor_task_id", "base_contract_sha256", "amendment_sha256", "combined_contract_sha256",
            "functional_role_contract_sha256", "conflict_graph_sha256", "evaluation_cycle_id",
            "auditor_nonce_commitment_sha256", "first_containing_merge_sha",
        )
    }


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
    """Verify one committed auditor nonce and derive its only permitted seed."""
    _require(isinstance(receipt, Mapping), "approved entropy receipt must be an object")
    for value in (frozen_bundle_sha256, frozen_population_sha256):
        _require(isinstance(value, str) and SHA256.fullmatch(value) is not None, "caller supplied invalid frozen hash")
    value = _validate_receipt_shape(receipt)
    _require(value["schema_version"] == SCHEMA_VERSION and value["text_free"] is True, "entropy receipt is not text-free v1")
    _require(value["purpose"] == purpose, "entropy receipt purpose drift")
    _require(value["frozen_universe_sha256"] == frozen_bundle_sha256, "entropy receipt frozen universe drift")
    _require(value["frozen_population_sha256"] == frozen_population_sha256, "entropy receipt frozen population drift")
    _require(value["sampler_plan_sha256"] == value["frozen_artifact_sha256"], "sampler plan is not the frozen committed artifact")
    _require(value["auditor_role_id"] == auditor_role_id and value["auditor_task_id"] == auditor_task_id, "entropy receipt auditor role/task drift")
    _require(
        value["auditor_only_nonce_commitment"] is True
        and value["nonce_commitment_count"] == 1
        and value["author_or_root_choices"] is False
        and value["root_choice_count"] == 0
        and value["reroll_count"] == 0,
        "entropy receipt permits root choice or reroll",
    )
    _require(
        value["auditor_nonce_commitment_sha256"] == sha256_bytes(value["auditor_nonce"].encode("ascii")),
        "auditor nonce commitment mismatch",
    )
    expected = _expected_functional_binding(auditor_role_id, auditor_task_id)
    _require(all(value[key] == expected[key] for key in expected), "entropy receipt functional-role binding drift")
    _verify_first_containing_artifact(value, repo_root=repo_root)
    canonical_tuple_sha256 = sha256_bytes(canonical_json(_canonical_tuple(value)).encode("utf-8"))
    derived_seed = sha256_bytes(bytes.fromhex(value["frozen_universe_sha256"]) + bytes.fromhex(value["auditor_nonce"]))
    return {
        "derived_seed": derived_seed,
        "entropy_receipt_sha256": sha256_bytes(canonical_json(value).encode("utf-8")),
        "first_containing_merge_sha": value["first_containing_merge_sha"],
        "canonical_tuple_sha256": canonical_tuple_sha256,
    }
