"""#11342: worktree reuse never silently deletes a terminal task's ignored evidence.

Root cause: dispatch preparation applies a cone sparse-checkout to a reused
worktree, and ``git sparse-checkout set`` removes untracked/ignored directories
inside a tracked cone directory. Reuse is now refused while a released task's
ignored output has no retrieval receipt, so the evidence survives until the
owner preserves it.
"""

from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path

import pytest

from scripts import delegate
from scripts.fleet import ignored_task_output as output


def _git(*args: str, cwd: Path) -> None:
    subprocess.run(["git", *args], cwd=cwd, check=True, capture_output=True, text=True, timeout=30)


@pytest.fixture
def worktree(tmp_path, monkeypatch):
    repo = tmp_path / "repo"
    repo.mkdir()
    _git("init", "-q", "-b", "main", cwd=repo)
    _git("config", "user.email", "a@b.c", cwd=repo)
    _git("config", "user.name", "test", cwd=repo)
    # The real repository tracks files directly under batch_state and tracks a
    # tree the default sparse profile excludes. Both are what makes reuse run
    # ``git sparse-checkout set`` and remove the ignored evidence directory.
    (repo / "batch_state").mkdir()
    (repo / "batch_state" / "tracked.txt").write_text("tracked\n")
    (repo / "curriculum" / "x").mkdir(parents=True)
    (repo / "curriculum" / "x" / "c.yaml").write_text("c\n")
    (repo / ".gitignore").write_text("batch_state/*\n")
    _git("add", "-A", cwd=repo)
    _git("add", "-f", "batch_state/tracked.txt", cwd=repo)
    _git("commit", "-qm", "init", cwd=repo)
    wt = tmp_path / "wt"
    _git("worktree", "add", "-q", str(wt), "-b", "task", "main", cwd=repo)
    _git("sparse-checkout", "disable", cwd=wt)
    evidence = wt / "batch_state" / "cto" / "publish" / "review-1"
    evidence.mkdir(parents=True)
    (evidence / "evidence.md").write_text("evidence\n")
    tasks = tmp_path / "tasks"
    tasks.mkdir()
    monkeypatch.setenv("LU_TASKS_DIR", str(tasks))
    monkeypatch.setattr(delegate, "_REPO_ROOT", repo)
    return repo, wt, tasks


def _task_record(worktree: Path, *, status: str = "no_deliverable", receipt: dict | None = None) -> dict:
    record = {
        "task_id": "previous-review",
        "run_nonce": "nonce-1",
        "status": status,
        "worktree_path": str(worktree),
        "cwd": str(worktree),
        "worktree_reused": False,
        "ignored_output_baseline": {
            "schema": "ignored-baseline.v1",
            "task_id": "previous-review",
            "run_nonce": "nonce-1",
            "paths": [],
            "directory_identity": [1, 2],
        },
    }
    if receipt is not None:
        record["preserved_artifacts"] = receipt
    return record


def _head(worktree: Path) -> str:
    return subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=worktree, text=True, timeout=30).strip()


def _legacy_receipt(repo, wt, tasks):
    record_path = tasks / "previous-review.json"
    record = json.loads(record_path.read_text())
    receipt, _ = output.capture_abandon_output(wt, primary=repo, record=record)
    output.publish_abandon_output(wt, primary=repo, record=record, locator=receipt)
    receipt.update(
        schema=output.PRESERVED_ARTIFACTS_SCHEMA,
        task_id="previous-review", run_nonce="nonce-1",
        worktree_sha256=hashlib.sha256(str(wt.resolve()).encode()).hexdigest(),
        retrieval_proof_sha256=output.verify_retrieval(repo, receipt),
    )
    record["preserved_artifacts"] = receipt
    record_path.write_text(json.dumps(record))
    return receipt


def _reuse(worktree: Path):
    return delegate._ensure_worktree(
        agent="codex",
        task_id="successor",
        raw_path=str(worktree),
        base="main",
        branch="task",
        resolved_base_sha=_head(worktree),
        full_checkout=False,
    )


def test_reuse_refuses_and_keeps_unretrieved_terminal_evidence(worktree):
    _repo, wt, tasks = worktree
    (tasks / "previous-review.json").write_text(json.dumps(_task_record(wt)))

    with pytest.raises(RuntimeError, match="worktree_reuse_evidence_unretrieved"):
        _reuse(wt)

    assert (wt / "batch_state/cto/publish/review-1/evidence.md").read_text() == "evidence\n"


def test_reuse_allows_terminal_evidence_after_a_verified_receipt(worktree):
    repo, wt, tasks = worktree
    (tasks / "previous-review.json").write_text(json.dumps(_task_record(wt)))
    receipt = _legacy_receipt(repo, wt, tasks)
    assert receipt is not None and receipt["schema"] == output.PRESERVED_ARTIFACTS_SCHEMA

    _path, _branch, telemetry = _reuse(wt)

    assert telemetry["reused"] is True


def test_reuse_refuses_a_forged_receipt_and_keeps_the_evidence(worktree):
    """A digest-shaped string is a claim, not retrieval: the preserved copy must exist and verify."""
    _repo, wt, tasks = worktree
    receipt = {
        "schema": output.PRESERVED_ARTIFACTS_SCHEMA,
        "task_id": "previous-review",
        "run_nonce": "nonce-1",
        "location": "batch_state/preserved/previous-review/missing",
        "paths": [{"path": "batch_state/cto/publish/review-1/evidence.md", "size": 9, "sha256": "a" * 64}],
        "content_sha256": "b" * 64,
        "retrieval_proof_sha256": "forged",
    }
    (tasks / "previous-review.json").write_text(json.dumps(_task_record(wt, receipt=receipt)))

    with pytest.raises(RuntimeError, match="worktree_reuse_evidence_unverified"):
        _reuse(wt)

    assert (wt / "batch_state/cto/publish/review-1/evidence.md").read_text() == "evidence\n"


def test_reuse_refuses_a_stale_receipt_after_the_source_changed(worktree):
    """The old receipt covers the old bytes; the new bytes were never retrieved."""
    repo, wt, tasks = worktree
    source = wt / "batch_state/cto/publish/review-1/evidence.md"
    (tasks / "previous-review.json").write_text(json.dumps(_task_record(wt)))
    _legacy_receipt(repo, wt, tasks)
    source.write_text("new unique evidence, after successful retrieval\n")

    with pytest.raises(RuntimeError, match="worktree_reuse_evidence_unverified"):
        _reuse(wt)

    assert source.read_text() == "new unique evidence, after successful retrieval\n"


def test_reuse_refuses_a_receipt_location_outside_the_task_preserved_root(worktree):
    """A receipt that points at another task's copy is not this task's retrieval."""
    repo, wt, tasks = worktree
    (tasks / "previous-review.json").write_text(json.dumps(_task_record(wt)))
    receipt = _legacy_receipt(repo, wt, tasks)
    other = dict(receipt)
    other["location"] = receipt["location"].replace(
        "batch_state/preserved/previous-review/", "batch_state/preserved/another-task/"
    )
    (tasks / "previous-review.json").write_text(json.dumps(_task_record(wt, receipt=other)))

    with pytest.raises(RuntimeError, match="worktree_reuse_evidence_unverified"):
        _reuse(wt)

    assert (wt / "batch_state/cto/publish/review-1/evidence.md").read_text() == "evidence\n"


def test_reuse_allows_a_live_task_without_a_retrieval_receipt(worktree):
    _repo, wt, tasks = worktree
    (tasks / "previous-review.json").write_text(json.dumps(_task_record(wt, status="running")))

    _path, _branch, telemetry = _reuse(wt)

    assert telemetry["reused"] is True


def test_reuse_allows_a_terminal_task_with_no_ignored_output(worktree):
    _repo, wt, tasks = worktree
    evidence_dir = wt / "batch_state" / "cto"
    for path in sorted(evidence_dir.rglob("*"), reverse=True):
        path.unlink() if path.is_file() else path.rmdir()
    evidence_dir.rmdir()
    (tasks / "previous-review.json").write_text(json.dumps(_task_record(wt)))

    _path, _branch, telemetry = _reuse(wt)

    assert telemetry["reused"] is True
