"""Hermetic proofs for the Phase 3 nonce commitment/reveal boundary."""

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
        ["git", "-C", str(repo), *args], check=True, stdout=subprocess.PIPE, text=True, timeout=30,
    ).stdout.strip()


def _commit(repo: Path, message: str) -> str:
    _git(repo, "add", ".")
    _git(repo, "commit", "-m", message)
    return _git(repo, "rev-parse", "HEAD")


def _repo(tmp_path: Path) -> tuple[Path, str, bytes]:
    repo = tmp_path / "entropy-repo"
    repo.mkdir(parents=True)
    _git(repo, "init", "--initial-branch=main")
    _git(repo, "config", "user.email", "entropy@example.test")
    _git(repo, "config", "user.name", "Entropy Test")
    (repo / "README").write_text("initial\n", encoding="utf-8")
    _commit(repo, "initial")
    artifact = b'{"sampler":"fixed-v1"}\n'
    (repo / "frozen").mkdir()
    (repo / "frozen" / "sampler-plan.json").write_bytes(artifact)
    plan_commit = _commit(repo, "freeze sampler plan")
    return repo, plan_commit, artifact


def _commitment(plan_commit: str, artifact: bytes, *, nonce: str = "c" * 64) -> dict[str, object]:
    role_id = "disposition_auditor"
    ledger = functional_roles.verify_value(functional_roles.read_json(functional_roles.LEDGER_PATH))
    commitment: dict[str, object] = {
        "schema_version": entropy.COMMITMENT_SCHEMA_VERSION,
        "text_free": True,
        "purpose": "pravopys_delta",
        "frozen_universe_sha256": "a" * 64,
        "frozen_population_sha256": "b" * 64,
        "sampler_plan_path": "frozen/sampler-plan.json",
        "sampler_plan_sha256": hashlib.sha256(artifact).hexdigest(),
        "sampler_plan_first_containing_merge_sha": plan_commit,
        "auditor_role_id": role_id,
        "auditor_task_id": functional_roles.ROLE_TASKS[role_id],
        "base_contract_sha256": functional_roles.BASE_SHA256,
        "amendment_sha256": functional_roles.AMENDMENT_SHA256,
        "combined_contract_sha256": functional_roles.COMBINED_SHA256,
        "functional_role_contract_sha256": functional_roles.sha256_file(functional_roles.LEDGER_PATH),
        "conflict_graph_sha256": functional_roles.conflict_graph_sha256(ledger),
        "evaluation_cycle_id": ledger["evaluation_cycle"]["evaluation_cycle_id"],
        "author_or_root_choices": False,
        "root_choice_count": 0,
        "reroll_count": 0,
    }
    binding = entropy._pre_nonce_binding(commitment)
    commitment["pre_nonce_binding_sha256"] = hashlib.sha256(entropy.canonical_json(binding).encode("utf-8")).hexdigest()
    commitment["auditor_nonce_commitment_sha256"] = hashlib.sha256(nonce.encode("ascii")).hexdigest()
    return commitment


def _add_commitment(repo: Path, commitment: dict[str, object]) -> tuple[str, str, str]:
    path = entropy.commitment_path_for(entropy._pre_nonce_binding(commitment))
    target = repo / path
    target.parent.mkdir(parents=True, exist_ok=True)
    payload = entropy.canonical_json(commitment).encode("utf-8")
    target.write_bytes(payload)
    return path, hashlib.sha256(payload).hexdigest(), _commit(repo, "commit auditor nonce hash")


def _receipt(path: str, commitment_sha256: str, commitment_commit: str, *, nonce: str = "c" * 64) -> dict[str, str | bool]:
    return {
        "schema_version": entropy.SCHEMA_VERSION,
        "text_free": True,
        "commitment_path": path,
        "commitment_sha256": commitment_sha256,
        "commitment_first_containing_merge_sha": commitment_commit,
        "auditor_nonce": nonce,
    }


def _verify(receipt: dict[str, str | bool], repo: Path) -> dict[str, str]:
    return entropy.verify_entropy_receipt(
        receipt,
        purpose="pravopys_delta",
        frozen_bundle_sha256="a" * 64,
        frozen_population_sha256="b" * 64,
        auditor_role_id="disposition_auditor",
        auditor_task_id="phase3-v2-1-disposition-audit",
        repo_root=repo,
    )


def _valid(tmp_path: Path) -> tuple[Path, dict[str, str | bool], dict[str, object]]:
    repo, plan_commit, artifact = _repo(tmp_path)
    commitment = _commitment(plan_commit, artifact)
    path, commitment_sha256, commitment_commit = _add_commitment(repo, commitment)
    _git(repo, "update-ref", "refs/remotes/origin/main", commitment_commit)
    return repo, _receipt(path, commitment_sha256, commitment_commit), commitment


def test_valid_prior_commitment_and_seed_are_deterministic(tmp_path: Path) -> None:
    repo, receipt, _ = _valid(tmp_path)
    first, second = _verify(receipt, repo), _verify(receipt, repo)
    assert first == second
    assert first["derived_seed"] == hashlib.sha256(bytes.fromhex("a" * 64) + bytes.fromhex("c" * 64)).hexdigest()


def test_rejects_offline_self_attested_same_receipt_pattern(tmp_path: Path) -> None:
    repo, plan_commit, artifact = _repo(tmp_path)
    commitment = _commitment(plan_commit, artifact)
    commitment["auditor_nonce"] = "c" * 64
    path, digest, commit = _add_commitment(repo, commitment)
    _git(repo, "update-ref", "refs/remotes/origin/main", commit)
    with pytest.raises(entropy.AuditEntropyError, match="nonce commitment schema violation"):
        _verify(_receipt(path, digest, commit), repo)


def test_rejects_delete_readd_as_false_first_containing(tmp_path: Path) -> None:
    repo, _, artifact = _repo(tmp_path)
    (repo / "frozen" / "sampler-plan.json").unlink()
    _commit(repo, "delete plan")
    (repo / "frozen" / "sampler-plan.json").write_bytes(artifact)
    readd_commit = _commit(repo, "re-add same plan")
    commitment = _commitment(readd_commit, artifact)
    path, digest, commit = _add_commitment(repo, commitment)
    _git(repo, "update-ref", "refs/remotes/origin/main", commit)
    with pytest.raises(entropy.AuditEntropyError, match="true first-containing"):
        _verify(_receipt(path, digest, commit), repo)


@pytest.mark.parametrize(("field", "value"), [("reroll_count", 1), ("author_or_root_choices", True)])
def test_rejects_reroll_or_root_choice_in_commitment(tmp_path: Path, field: str, value: object) -> None:
    repo, plan_commit, artifact = _repo(tmp_path)
    commitment = _commitment(plan_commit, artifact)
    commitment[field] = value
    path, digest, commit = _add_commitment(repo, commitment)
    _git(repo, "update-ref", "refs/remotes/origin/main", commit)
    with pytest.raises(entropy.AuditEntropyError, match="nonce commitment schema violation"):
        _verify(_receipt(path, digest, commit), repo)


def test_rejects_second_commitment_for_same_deterministic_path(tmp_path: Path) -> None:
    repo, receipt, commitment = _valid(tmp_path)
    commitment["auditor_nonce_commitment_sha256"] = hashlib.sha256(("d" * 64).encode("ascii")).hexdigest()
    path, digest, later = _add_commitment(repo, commitment)
    _git(repo, "update-ref", "refs/remotes/origin/main", later)
    with pytest.raises(entropy.AuditEntropyError, match="previously introduced"):
        _verify(_receipt(path, digest, later, nonce="d" * 64), repo)
    assert receipt["commitment_path"] == path


def test_rejects_commitment_containing_nonce_and_nonce_mismatch(tmp_path: Path) -> None:
    repo, plan_commit, artifact = _repo(tmp_path)
    commitment = _commitment(plan_commit, artifact)
    commitment["auditor_nonce"] = "c" * 64
    path, digest, commit = _add_commitment(repo, commitment)
    _git(repo, "update-ref", "refs/remotes/origin/main", commit)
    with pytest.raises(entropy.AuditEntropyError, match="nonce commitment schema violation"):
        _verify(_receipt(path, digest, commit), repo)
    repo, receipt, _ = _valid(tmp_path / "mismatch")
    wrong = copy.deepcopy(receipt)
    wrong["auditor_nonce"] = "d" * 64
    with pytest.raises(entropy.AuditEntropyError, match="does not open"):
        _verify(wrong, repo)


def test_rejects_plan_not_earlier_than_nonce_commitment(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    repo, receipt, _ = _valid(tmp_path)
    original = entropy._git_ok
    merge_base_calls = 0

    def ordered_git_ok(repo_root: Path, *args: str) -> bool:
        nonlocal merge_base_calls
        if args[:2] == ("merge-base", "--is-ancestor"):
            merge_base_calls += 1
            return merge_base_calls < 3
        return original(repo_root, *args)

    monkeypatch.setattr(entropy, "_git_ok", ordered_git_ok)
    with pytest.raises(entropy.AuditEntropyError, match="not committed before"):
        _verify(receipt, repo)


def test_first_containing_scans_only_path_change_history(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    repo, receipt, _ = _valid(tmp_path)
    for number in range(24):
        (repo / "README").write_text(f"unrelated {number}\n", encoding="utf-8")
        tip = _commit(repo, f"unrelated {number}")
    _git(repo, "update-ref", "refs/remotes/origin/main", tip)
    calls = 0
    original = entropy._artifact_at

    def count_artifact(*args: object, **kwargs: object) -> bytes | None:
        nonlocal calls
        calls += 1
        return original(*args, **kwargs)

    monkeypatch.setattr(entropy, "_artifact_at", count_artifact)
    _verify(receipt, repo)
    assert calls <= 3


def test_entropy_schema_is_parseable_and_closed() -> None:
    schema = json.loads(entropy.SCHEMA_PATH.read_text(encoding="utf-8"))
    Draft202012Validator.check_schema(schema)
    assert schema["$defs"]["reveal"]["additionalProperties"] is False
    assert schema["$defs"]["commitment"]["additionalProperties"] is False
