"""The review-contract canary gate (#12399): routes, receipts and refusals."""

from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path

import pytest

from scripts.common.git_context import sanitized_git_env
from scripts.review import contract_canary as canary

CONTRACT_FILE = "scripts/review/review_contract.py"
RECEIPT = json.dumps({
    "schema_version": "code-review-findings.v1",
    "overall": {"correctness": "correct", "explanation": "No defects.", "confidence": 0.9},
    "findings": [],
})
MODELS = {
    "agy": "gemini-3.8-flash-high",
    "claude": "claude-sonnet-5-5",
    "codex": "gpt-6.1-sol",
    "cursor": "grok-4.7-high",
    "muse": "muse-wonder-full-1.0",
}


def _git(repo: Path, *args: str) -> str:
    return subprocess.run(
        ["git", *args], cwd=repo, check=True, capture_output=True, text=True, env=sanitized_git_env(), timeout=10
    ).stdout.strip()


@pytest.fixture
def repo(tmp_path: Path) -> tuple[Path, str]:
    root = tmp_path / "repo"
    (root / "scripts/review").mkdir(parents=True)
    _git(root, "init", "-q", "-b", "trunk")
    _git(root, "config", "user.email", "test@example.com")
    _git(root, "config", "user.name", "Test")
    (root / CONTRACT_FILE).write_text("CONTRACT = 1\n", encoding="utf-8")
    _git(root, "add", ".")
    _git(root, "commit", "-q", "-m", "init")
    return root, _git(root, "rev-parse", "HEAD")


def task(route: str, head: str, **changes: object) -> dict:
    record = {
        "task_id": f"contract-canary-1-{route}",
        "status": "done",
        "mode": "read-only",
        "require_review_verdict": True,
        "schema_version": 2,
        "head_sha": head,
        "worktree_start_sha": head,
        "review_branch": None,
        "pr": None,
        "agent": route,
        "model": MODELS[route],
        "dispatcher_code": {"root": "/candidate", "head": head, "clean": True},
        "result_sha256": hashlib.sha256(RECEIPT.encode()).hexdigest(),
    }
    record.update(changes)
    return record


def write_all(root: Path, head: str) -> None:
    for route in canary.required_routes():
        receipt = canary.build_receipt(task(route, head), RECEIPT, pr=1, head=head, root=root)
        path = canary.receipt_root(root) / head / f"{route}.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(receipt), encoding="utf-8")


def test_routes_come_from_the_catalog_and_an_empty_list_blocks(repo, monkeypatch: pytest.MonkeyPatch) -> None:
    root, head = repo
    # Muse is required too: the catalog, not the issue text, names the routes.
    assert canary.required_routes() == ("agy", "claude", "codex", "cursor", "muse")
    monkeypatch.setattr(canary, "_formal_candidates", lambda: {})
    assert canary.refusal([CONTRACT_FILE], head, root) == "unverifiable: reviewer routes unavailable"


def test_contract_change_is_refused_until_every_route_has_a_receipt(repo) -> None:
    root, head = repo
    assert canary.refusal([CONTRACT_FILE], head, root) == "missing: agy,claude,codex,cursor,muse"
    write_all(root, head)
    (canary.receipt_root(root) / head / "muse.json").unlink()
    assert canary.refusal([CONTRACT_FILE], head, root) == "missing: muse"
    write_all(root, head)
    assert canary.refusal([CONTRACT_FILE, "docs/x.md"], head, root) is None
    stored = json.loads((canary.receipt_root(root) / head / "codex.json").read_text())
    assert stored["eligible_as_review"] is False


@pytest.mark.parametrize(
    ("changes", "why"),
    [
        ({"head_sha": "f" * 40}, "did not review the PR head"),
        ({"worktree_start_sha": "f" * 40}, "did not review the PR head"),
        ({"review_branch": "claude/x"}, "branch- or PR-pinned"),
        ({"pr": 1}, "branch- or PR-pinned"),
        ({"status": "failed"}, "did not settle done"),
        ({"dispatcher_code": {"head": "f" * 40, "clean": True}}, "candidate's clean dispatcher"),
        ({"dispatcher_code": None}, "candidate's clean dispatcher"),
        ({"agent": "kimi"}, "not a required reviewer route"),
        ({"model": "claude-fable-5-1"}, "not a formal reviewer"),
        ({"result_sha256": "0" * 64}, "does not match"),
    ],
)
def test_record_refuses_a_task_that_is_not_canary_evidence(repo, changes: dict, why: str) -> None:
    root, head = repo
    with pytest.raises(canary.CanaryError, match=why):
        canary.build_receipt(task("claude", head, **changes), RECEIPT, pr=1, head=head, root=root)


def test_a_verdict_line_is_not_a_canonical_receipt(repo) -> None:
    root, head = repo
    text = "VERDICT: APPROVE\n"
    record = task("claude", head, result_sha256=hashlib.sha256(text.encode()).hexdigest())
    with pytest.raises(canary.CanaryError, match="canonical receipt"):
        canary.build_receipt(record, text, pr=1, head=head, root=root)


def test_receipts_bound_to_other_contract_bytes_or_routes_refuse(repo) -> None:
    root, head = repo
    write_all(root, head)
    path = canary.receipt_root(root) / head / "agy.json"
    receipt = json.loads(path.read_text())
    path.write_text(json.dumps({**receipt, "contract_fingerprint": "0" * 64}))
    assert canary.refusal([CONTRACT_FILE], head, root).startswith("stale: receipt for agy")
    path.write_text(json.dumps({**receipt, "route": "codex"}))
    assert canary.refusal([CONTRACT_FILE], head, root) == "unverifiable: receipt for agy"
    path.write_text(json.dumps({**receipt, "eligible_as_review": True}))
    assert canary.refusal([CONTRACT_FILE], head, root) == "unverifiable: receipt for agy"
    # The same receipts do not carry to a new head.
    (root / CONTRACT_FILE).write_text("CONTRACT = 2\n", encoding="utf-8")
    _git(root, "commit", "-qam", "change")
    assert canary.refusal([CONTRACT_FILE], _git(root, "rev-parse", "HEAD"), root).startswith("missing: ")


def test_a_change_outside_the_contract_needs_no_canary(repo) -> None:
    root, _ = repo
    # No git read at all: an unknown head does not matter outside the contract.
    assert canary.refusal(["scripts/example.py", "docs/review-protocol.md"], "not-a-sha", root) is None
