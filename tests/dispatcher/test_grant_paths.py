"""The seven approved grant-path defect classes for #12188."""

import concurrent.futures
import copy
import json
import subprocess
import sys
import time
from pathlib import Path

import pytest

from scripts.dispatcher import cli, ownership, store, worker
from tests.dispatcher.test_core import MERGED, run_git
from tests.dispatcher.test_core import merged_delivery_world as merged_delivery_world
from tests.dispatcher.test_core import sandbox as sandbox


@pytest.fixture
def grant_task(tmp_path, monkeypatch):
    root = tmp_path / "repo"
    root.mkdir()
    run_git(root, "init", "-b", "main")
    monkeypatch.setenv("LU_TASKS_DIR", str(tmp_path / "tasks"))
    monkeypatch.delenv(ownership.TASK_ID_ENV, raising=False)
    monkeypatch.setenv("SESSION_HANDOFF_AGENT", "coordinator")
    record = dict(schema_version=2, task_id="worker", run_nonce="nonce", status="running",
                  mode="workspace-write", worktree_path=str(root), repository_id="org/repo",
                  owned_paths=["original.txt"], options={})
    store.record_path("worker").parent.mkdir()
    store.replace(record)
    return record


def grant(record, *paths, nonce=None):
    return store.grant_paths(record["task_id"], nonce or record["run_nonce"], list(paths),
                             "Approved fixture change", "message-approval")


class TestSupervisorWritePreservesGrant:
    def test_stale_writes_retries_and_nonce(self, grant_task):
        """A stale supervisor or a concurrent replacement must not wipe an issued grant."""
        stale = copy.deepcopy(grant_task)
        first = grant(grant_task, "extra.txt")
        assert first["grant"]["granted_by"] == "coordinator"
        assert first["grant"]["granted_by_authenticated"] is False
        with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
            results = [pool.submit(store.replace, copy.deepcopy(stale)),
                       pool.submit(grant, grant_task, "second.txt")]
            for result in results:
                result.result(timeout=5)
        with store.task_state_lock(store.record_path("worker")):
            store.replace(stale)  # the already-locked settlement path must not deadlock
        assert grant(grant_task, "extra.txt")["grant_id"] == first["grant_id"]
        current = store.read("worker")
        assert current["owned_paths"] == ["original.txt"]
        assert len(current["owned_path_grants"]) == 2
        assert ownership.effective_scope(current) == ["original.txt", "extra.txt", "second.txt"]
        before = store.record_path("worker").read_bytes()
        with pytest.raises(ValueError, match="nonce"):
            grant(grant_task, "third.txt", nonce="stale")
        with pytest.raises(ValueError, match="nonce"):
            store.replace(dict(stale, run_nonce="stale"))
        assert store.record_path("worker").read_bytes() == before


class TestSettlementClosesGrants:
    @pytest.mark.parametrize("status", ["running", "done", "cancelled"])
    def test_closed_grant_has_no_partial_mutation(self, grant_task, status, capsys):
        """A grant arriving after provider exit or terminal publication is refused."""
        grant(grant_task, "extra.txt")
        store.begin_settlement(grant_task)
        grant_task["status"] = status
        store.replace(grant_task)
        before = store.record_path("worker").read_bytes()
        assert cli.main(["grant-paths", "worker", "--run-nonce", "nonce", "--owned-path", "late.txt",
                         "--reason", "approved", "--approval-ref", "message-id"]) == 2
        assert "not settling" in capsys.readouterr().err
        assert store.record_path("worker").read_bytes() == before


class TestHooksAndSettlementShareScope:
    def test_paused_task_resumes_in_same_worktree_and_wait_reports_usage(self, sandbox):
        """The same running task accepts a grant at both hook stages and settlement only."""
        sandbox.env.pop(ownership.TASK_ID_ENV, None)
        sandbox.env["PYTHONDONTWRITEBYTECODE"] = "1"
        task_id, nonce = task = sandbox.dispatch("blocked", "--mode", "workspace-write",
                                               "--owned-path", "original.txt")
        path = sandbox.tasks / f"{task_id}.json"
        deadline = time.monotonic() + 10
        while not (sandbox.tasks / f"{task_id}.started").exists():
            assert time.monotonic() < deadline
            time.sleep(0.02)
        initial = json.loads(path.read_text())
        tree = Path(initial["worktree_path"])
        task_env = {**sandbox.env, ownership.TASK_ID_ENV: task_id}

        def hook(stage, updates=None):
            return subprocess.run([sys.executable, "-m", "scripts.dispatcher.ownership", "--worktree", str(tree), stage],
                                  cwd=tree, env=task_env, input=updates, capture_output=True, text=True, timeout=30)

        (tree / "extra.txt").write_text("approved change\n")
        run_git(tree, "add", "extra.txt")
        assert hook("staged").returncode == 1
        args = ["grant-paths", task_id, "--run-nonce", nonce, "--owned-path", "extra.txt",
                "--reason", "Approved fixture change", "--approval-ref", "message-approval"]
        receipt = json.loads(sandbox.cli(*args).stdout)
        assert receipt["effective_scope"] == ["original.txt", "extra.txt"]
        assert json.loads(sandbox.cli(*args).stdout)["grant_id"] == receipt["grant_id"]
        assert hook("staged").returncode == 0
        (tree / "second.txt").write_text("unapproved change\n")
        run_git(tree, "add", "second.txt")
        refused = hook("staged")
        assert refused.returncode == 1 and "second.txt" in refused.stderr
        run_git(tree, "reset", "--", "second.txt")
        (tree / "second.txt").unlink()
        run_git(tree, "commit", "-m", "approved extra path")
        head = run_git(tree, "rev-parse", "HEAD")
        updates = f"refs/heads/task {head} refs/heads/task {'0' * 40}\n"
        assert hook("push", updates).returncode == 0
        run_git(tree, "push", "origin", "HEAD")
        (tree / "second.txt").write_text("unapproved change\n")
        run_git(tree, "add", "second.txt")
        run_git(tree, "commit", "-m", "second path")
        refused = hook("push", f"refs/heads/task {run_git(tree, 'rev-parse', 'HEAD')} refs/heads/task {'0' * 40}\n")
        assert refused.returncode == 1 and "second.txt" in refused.stderr
        run_git(tree, "push", "origin", "HEAD")
        record = dict(json.loads(path.read_text()), status="done", error=None,
                      worktree_dirty_on_exit=False, commits_ahead=2, push_state="pushed",
                      head_sha=run_git(tree, "rev-parse", "HEAD"))
        worker._enforce_delivery(record)
        assert (record["status"], record["error"]) == ("no_deliverable", "outside_owned_paths: second.txt")
        run_git(tree, "revert", "--no-edit", "HEAD")
        # A revert still counts as outside scope; remove the unapproved local history before release.
        run_git(tree, "reset", "--hard", head)
        # A disposable remote permits this test-only restoration; no production branch is involved.
        run_git(tree, "push", "--force-with-lease", "origin", "HEAD")
        assert run_git(tree, "status", "--porcelain") == ""
        Path(initial["prompt_file"]).with_suffix(".release").touch()
        result = sandbox.settle(task)
        assert result["task_id"] == task_id and result["run_nonce"] == nonce
        assert result["worktree_path"] == initial["worktree_path"] and result["provider_pgid"] == initial["provider_pgid"]
        assert result["owned_path_grants_used"] == [{"path": "extra.txt", "grant_id": receipt["grant_id"]}]
        assert result["owned_path_grants"] == [receipt["grant"]]
        assert result["settling_at"]


class TestSelfAndDescendantRefusal:
    @pytest.mark.parametrize("caller", ["worker", "child", "grandchild"])
    def test_ancestry_guard(self, grant_task, monkeypatch, caller):
        """A worker cannot approve its own scope, directly or through a child task."""
        store.replace(dict(grant_task, task_id="child", parent_task_id="worker"))
        store.replace(dict(grant_task, task_id="grandchild", parent_task_id="child"))
        monkeypatch.setenv(ownership.TASK_ID_ENV, caller)
        before = store.record_path("worker").read_bytes()
        with pytest.raises(ValueError, match="self or descendant"):
            grant(grant_task, "extra.txt")
        assert store.record_path("worker").read_bytes() == before


class TestSealedEnvelopeRefusal:
    @pytest.mark.parametrize("binding", [
        {"mode": "read-only"}, {"review_attempt": {}}, {"advisory_envelope": {}},
        {"advisory_binding_sha256": "bound"}, {"driver_brief": {}},
        {"research_task_family": "bounded_implementation"}, {"bounded": True},
        {"options": {"advisory_task": "advisor"}},
    ])
    def test_admission_cannot_be_widened(self, grant_task, binding):
        """A grant cannot mutate the scope sealed into an admission or review envelope."""
        store.replace(dict(grant_task, **binding))
        before = store.record_path("worker").read_bytes()
        with pytest.raises(ValueError, match="sealed"):
            grant(grant_task, "extra.txt")
        assert store.record_path("worker").read_bytes() == before


class TestGrantPathValidation:
    @pytest.mark.parametrize("bad", ["*", "tests/**", "tests/?.py", "../escape", "tests/../escape", ".", "/",
                                        "/absolute", "tests/./x", "tests/line\nfeed", "tests/zero\u200bwidth",
                                        "tests/line\u2028separator", "C:/escape", ":(top)escape", "escape/link"])
    def test_invalid_requests_are_atomic_and_brackets_are_literal(self, grant_task, bad, tmp_path):
        """Literal grant validation rejects escapes and sparse trees without interpreting brackets."""
        root = Path(grant_task["worktree_path"])
        (root / "escape").symlink_to(tmp_path, target_is_directory=True)
        before = store.record_path("worker").read_bytes()
        with pytest.raises(ValueError):
            grant(grant_task, "valid.txt", bad)
        assert store.record_path("worker").read_bytes() == before
        receipt = grant(grant_task, "tests/[id].py")
        assert ownership.outside_owned(["tests/[id].py", "tests/else.py"], receipt["effective_scope"]) == ["tests/else.py"]
        generated = grant(grant_task, "scripts/lexicon/fix.py")
        assert generated["owned_paths"] == ["scripts/lexicon/fix.py", "site/src/data/lexicon-manifest.fingerprint.json"]
        (root / "data").mkdir()
        (root / "data/excluded.txt").write_text("excluded\n")
        run_git(root, "add", "data")
        run_git(root, "-c", "user.name=Stub", "-c", "user.email=stub@example.invalid", "commit", "-m", "sparse input")
        run_git(root, "sparse-checkout", "set", "--no-cone", "/*", "!/data/")
        before = store.record_path("worker").read_bytes()
        with pytest.raises(ValueError, match="sparse-excluded"):
            grant(grant_task, "valid.txt", "data/new.txt")
        assert store.record_path("worker").read_bytes() == before


class TestMergedPRRecoveryUsesGrant:
    def test_merged_delivery_uses_effective_scope(self, merged_delivery_world):
        """Merged-PR recovery must honour a grant and still reject another ungranted path."""
        world = merged_delivery_world
        world.record["run_nonce"] = "nonce"
        world.record["owned_path_grants"] = [dict(task_id="merge-probe", run_nonce="nonce",
                                                      grant_id="grant", owned_paths=["extra.txt"])]
        world.accept(77)
        world.prs[77], world.files[77] = MERGED, ["extra.txt"]
        worker._enforce_delivery(world.record)
        assert (world.record["status"], world.record["error"]) == ("done", None)
        assert world.record["owned_path_grants_used"] == [{"path": "extra.txt", "grant_id": "grant"}]
        world.files[77] = ["extra.txt", "second.txt"]
        worker._enforce_delivery(world.record)
        assert (world.record["status"], world.record["error"]) == ("no_deliverable", "outside_owned_paths: second.txt")
