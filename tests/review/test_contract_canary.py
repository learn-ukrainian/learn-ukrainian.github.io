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


TASKS: dict[str, tuple[dict, str]] = {}
REAL_LOAD_TASK = canary._load_task


@pytest.fixture(autouse=True)
def tasks(monkeypatch: pytest.MonkeyPatch) -> dict[str, tuple[dict, str]]:
    """The settled task records receipts name, in place of the dispatcher store."""
    TASKS.clear()

    def load(task_id: str) -> tuple[dict, str]:
        if task_id not in TASKS:
            raise ValueError("task not found")
        return TASKS[task_id]

    monkeypatch.setattr(canary, "_load_task", load)
    return TASKS


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
        "review_profile": "code",
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
        record = task(route, head)
        TASKS[record["task_id"]] = (record, RECEIPT)
        receipt = canary.build_receipt(record, RECEIPT, head=head)
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
        ({"review_profile": "ukrainian"}, "did not settle through the receipt gate"),
        ({"review_attempt": "/manifest.json"}, "did not settle through the receipt gate"),
        ({"dispatcher_code": {"head": "f" * 40, "clean": True}}, "candidate's clean dispatcher"),
        ({"dispatcher_code": None}, "candidate's clean dispatcher"),
        ({"agent": "kimi"}, "not a required reviewer route"),
        ({"model": "claude-fable-5-1"}, "not a formal reviewer"),
        ({"result_sha256": "0" * 64}, "does not match"),
    ],
)
def test_record_refuses_a_task_that_is_not_canary_evidence(repo, changes: dict, why: str) -> None:
    _, head = repo
    with pytest.raises(canary.CanaryError, match=why):
        canary.build_receipt(task("claude", head, **changes), RECEIPT, head=head)


def test_a_verdict_line_is_not_a_canonical_receipt(repo) -> None:
    _, head = repo
    text = "VERDICT: APPROVE\n"
    record = task("claude", head, result_sha256=hashlib.sha256(text.encode()).hexdigest())
    with pytest.raises(canary.CanaryError, match="canonical receipt"):
        canary.build_receipt(record, text, head=head)


def test_receipts_bound_to_another_route_or_head_refuse(repo) -> None:
    root, head = repo
    write_all(root, head)
    path = canary.receipt_root(root) / head / "agy.json"
    receipt = json.loads(path.read_text())
    path.write_text(json.dumps({**receipt, "dispatcher_head": "0" * 40}))
    assert canary.refusal([CONTRACT_FILE], head, root) == "unverifiable: receipt for agy does not match its task"
    path.write_text("[" * 100_000 + "]" * 100_000)  # too deeply nested to decode: refuse, never crash
    assert canary.refusal([CONTRACT_FILE], head, root) == "unverifiable: receipt for agy"
    path.write_text(json.dumps({**receipt, "route": "codex"}))
    assert canary.refusal([CONTRACT_FILE], head, root) == "unverifiable: receipt for agy"
    path.write_text(json.dumps({**receipt, "eligible_as_review": True}))
    assert canary.refusal([CONTRACT_FILE], head, root) == "unverifiable: receipt for agy"
    # The same receipts do not carry to a new head.
    (root / CONTRACT_FILE).write_text("CONTRACT = 2\n", encoding="utf-8")
    _git(root, "commit", "-qam", "change")
    assert canary.refusal([CONTRACT_FILE], _git(root, "rev-parse", "HEAD"), root).startswith("missing: ")


def test_a_receipt_must_still_match_its_settled_task(repo, tasks) -> None:
    root, head = repo
    write_all(root, head)
    record, _ = tasks.pop("contract-canary-1-codex")
    assert canary.refusal([CONTRACT_FILE], head, root) == "unverifiable: task behind the receipt for codex"
    tasks["contract-canary-1-codex"] = ({**record, "status": "failed"}, RECEIPT)
    assert canary.refusal([CONTRACT_FILE], head, root) == "unverifiable: task behind the receipt for codex"
    tasks["contract-canary-1-codex"] = (record, RECEIPT)
    path = canary.receipt_root(root) / head / "codex.json"
    path.write_text(json.dumps({**json.loads(path.read_text()), "model": "gpt-6-astra"}))
    assert canary.refusal([CONTRACT_FILE], head, root) == "unverifiable: receipt for codex does not match its task"


def test_a_reply_with_carriage_returns_keeps_its_byte_digest(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    # The dispatcher digests the result file's bytes; reading it must not translate newlines.
    from scripts.dispatcher import store

    reply = RECEIPT.replace(",", ",\r\n")
    result = tmp_path / "t.result"
    result.write_bytes(reply.encode())
    head = "c" * 40
    record = task("claude", head, result_file=str(result), result_sha256=hashlib.sha256(result.read_bytes()).hexdigest())
    monkeypatch.setattr(store, "read", lambda task_id: record)
    _, text = REAL_LOAD_TASK("t")
    assert canary.build_receipt(record, text, head=head)["result_sha256"] == record["result_sha256"]


def test_the_gate_trusts_the_candidate_settlement_not_mains_contract(repo, tasks) -> None:
    # A breaking contract change: main's parser would refuse the reply the candidate settled done.
    root, head = repo
    write_all(root, head)
    reply = json.dumps({"schema_version": "code-review-findings.v2", "verdict": "approve"})
    record, _ = tasks["contract-canary-1-codex"]
    tasks["contract-canary-1-codex"] = ({**record, "result_sha256": hashlib.sha256(reply.encode()).hexdigest()}, reply)
    path = canary.receipt_root(root) / head / "codex.json"
    path.write_text(json.dumps({**json.loads(path.read_text()), "result_sha256": tasks["contract-canary-1-codex"][0]["result_sha256"]}))
    assert canary.refusal([CONTRACT_FILE], head, root) is None
    with pytest.raises(canary.CanaryError, match="canonical receipt"):
        canary.build_receipt(tasks["contract-canary-1-codex"][0], reply, head=head)


def test_the_gate_itself_is_a_contract_path() -> None:
    assert canary.touches_contract(["scripts/review/contract_canary.py"])


def test_a_change_outside_the_contract_needs_no_canary(repo) -> None:
    root, _ = repo
    # No git read at all: an unknown head does not matter outside the contract.
    assert canary.refusal(["scripts/example.py", "docs/review-protocol.md"], "not-a-sha", root) is None
