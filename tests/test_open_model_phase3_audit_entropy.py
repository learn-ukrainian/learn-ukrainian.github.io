"""Hermetic proofs for the approved Phase 3 anti-grinding receipt verifier."""

from __future__ import annotations

import copy
import hashlib
import json
import subprocess
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator

from scripts.projects.open_model_data import phase3_audit_entropy as entropy
from scripts.projects.open_model_data import phase3_functional_roles as functional_roles


def _git(repo: Path, *args: str) -> str:
    return subprocess.run(
        ["git", "-C", str(repo), *args], check=True, stdout=subprocess.PIPE, text=True,
    ).stdout.strip()


def _commit(repo: Path, message: str) -> str:
    _git(repo, "add", ".")
    _git(repo, "commit", "-m", message)
    return _git(repo, "rev-parse", "HEAD")


def _repo(tmp_path: Path) -> tuple[Path, str, bytes]:
    repo = tmp_path / "entropy-repo"
    repo.mkdir()
    _git(repo, "init", "--initial-branch=main")
    _git(repo, "config", "user.email", "entropy@example.test")
    _git(repo, "config", "user.name", "Entropy Test")
    (repo / "README").write_text("initial\n", encoding="utf-8")
    _commit(repo, "initial")
    artifact = b'{"sampler":"fixed-v1"}\n'
    (repo / "frozen").mkdir()
    (repo / "frozen" / "sampler-plan.json").write_bytes(artifact)
    commit = _commit(repo, "freeze sampler plan")
    _git(repo, "update-ref", "refs/remotes/origin/main", commit)
    return repo, commit, artifact


def _receipt(commit: str, artifact: bytes) -> dict[str, object]:
    role_id = "disposition_auditor"
    ledger = functional_roles.verify_value(functional_roles.read_json(functional_roles.LEDGER_PATH))
    nonce = "c" * 64
    return {
        "schema_version": entropy.SCHEMA_VERSION,
        "text_free": True,
        "purpose": "pravopys_delta",
        "frozen_universe_sha256": "a" * 64,
        "frozen_population_sha256": "b" * 64,
        "sampler_plan_sha256": hashlib.sha256(artifact).hexdigest(),
        "frozen_artifact_path": "frozen/sampler-plan.json",
        "frozen_artifact_sha256": hashlib.sha256(artifact).hexdigest(),
        "auditor_role_id": role_id,
        "auditor_task_id": functional_roles.ROLE_TASKS[role_id],
        "base_contract_sha256": functional_roles.BASE_SHA256,
        "amendment_sha256": functional_roles.AMENDMENT_SHA256,
        "combined_contract_sha256": functional_roles.COMBINED_SHA256,
        "functional_role_contract_sha256": functional_roles.sha256_file(functional_roles.LEDGER_PATH),
        "conflict_graph_sha256": functional_roles.conflict_graph_sha256(ledger),
        "evaluation_cycle_id": ledger["evaluation_cycle"]["evaluation_cycle_id"],
        "auditor_only_nonce_commitment": True,
        "nonce_commitment_count": 1,
        "auditor_nonce_commitment_sha256": hashlib.sha256(nonce.encode("ascii")).hexdigest(),
        "auditor_nonce": nonce,
        "author_or_root_choices": False,
        "root_choice_count": 0,
        "reroll_count": 0,
        "first_containing_merge_sha": commit,
    }


def _verify(receipt: dict[str, object], repo: Path) -> dict[str, str]:
    return entropy.verify_entropy_receipt(
        receipt,
        purpose="pravopys_delta",
        frozen_bundle_sha256="a" * 64,
        frozen_population_sha256="b" * 64,
        auditor_role_id="disposition_auditor",
        auditor_task_id="phase3-v2-1-disposition-audit",
        repo_root=repo,
    )


def test_valid_first_containing_proof_and_seed_are_deterministic(tmp_path: Path) -> None:
    repo, commit, artifact = _repo(tmp_path)
    receipt = _receipt(commit, artifact)
    first = _verify(receipt, repo)
    second = _verify(receipt, repo)
    assert first == second
    assert first["derived_seed"] == hashlib.sha256(bytes.fromhex("a" * 64) + bytes.fromhex("c" * 64)).hexdigest()
    assert first["first_containing_merge_sha"] == commit
    assert first["entropy_receipt_sha256"] == hashlib.sha256(
        entropy.canonical_json(receipt).encode("utf-8"),
    ).hexdigest()


def test_rejects_parent_that_already_contains_same_frozen_artifact(tmp_path: Path) -> None:
    repo, _, artifact = _repo(tmp_path)
    (repo / "README").write_text("second\n", encoding="utf-8")
    later = _commit(repo, "unrelated follow-up")
    _git(repo, "update-ref", "refs/remotes/origin/main", later)
    with pytest.raises(entropy.AuditEntropyError, match="first parent already contains"):
        _verify(_receipt(later, artifact), repo)


@pytest.mark.parametrize(
    ("field", "value", "expected"),
    [
        ("auditor_task_id", "phase3-v2-1-textbook-nonhit-audit", "auditor role/task"),
        ("evaluation_cycle_id", "phase3-v2-1-evaluation-cycle-999", "schema violation"),
        ("frozen_universe_sha256", "d" * 64, "frozen universe"),
    ],
)
def test_rejects_role_task_cycle_and_frozen_hash_drift(
    tmp_path: Path, field: str, value: object, expected: str,
) -> None:
    repo, commit, artifact = _repo(tmp_path)
    receipt = _receipt(commit, artifact)
    receipt[field] = value
    with pytest.raises(entropy.AuditEntropyError, match=expected):
        _verify(receipt, repo)


@pytest.mark.parametrize(
    ("field", "value"),
    [("reroll_count", 1), ("author_or_root_choices", True), ("root_choice_count", 1)],
)
def test_rejects_reroll_or_root_choice(tmp_path: Path, field: str, value: object) -> None:
    repo, commit, artifact = _repo(tmp_path)
    receipt = _receipt(commit, artifact)
    receipt[field] = value
    with pytest.raises(entropy.AuditEntropyError, match=r"schema violation|root choice or reroll"):
        _verify(receipt, repo)


def test_rejects_nonce_commitment_mismatch_and_open_receipt(tmp_path: Path) -> None:
    repo, commit, artifact = _repo(tmp_path)
    receipt = _receipt(commit, artifact)
    receipt["auditor_nonce_commitment_sha256"] = "0" * 64
    with pytest.raises(entropy.AuditEntropyError, match="nonce commitment mismatch"):
        _verify(receipt, repo)
    opened = copy.deepcopy(_receipt(commit, artifact))
    opened["unbound_note"] = "not allowed"
    with pytest.raises(entropy.AuditEntropyError, match="schema violation"):
        _verify(opened, repo)


def test_entropy_schema_is_parseable_and_closed() -> None:
    schema = json.loads(entropy.SCHEMA_PATH.read_text(encoding="utf-8"))
    Draft202012Validator.check_schema(schema)
    assert schema["additionalProperties"] is False
