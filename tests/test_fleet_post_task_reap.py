"""Hermetic tests for scripts.fleet.post_task_reap.

Tests exercise the hard guards without touching the real checkout:
- never reap while task status is spawning/running
- never reap a dirty worktree
- never reap without binding task state to a registered dispatch worktree
- never reap ACP runtime paths by name/substring; only ``acp_runtime_paths`` in
  task state authorizes reaping
- liveness probe failure is fail-closed (retain) for both main and ACP paths
- default dry-run; --apply required for deletion
"""

from __future__ import annotations

import hashlib
import io
import json
import os
import re
import subprocess
import sys
import tarfile
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import pytest

from tests.orchestration.test_interrupted_caller_matrix import hashes
from tests.orchestration.test_interrupted_caller_matrix import interrupted_checkout as interrupted_checkout


@pytest.fixture
def interrupted_reap(interrupted_checkout, monkeypatch):
    """Bind the interrupted checkout to the real post-task reap guards."""
    repo, tree, tasks, record, result, output = interrupted_checkout
    monkeypatch.setattr(post_task_reap, "ROOT", repo)
    monkeypatch.setattr(post_task_reap, "_DISPATCH_WORKTREES_ROOT", repo / ".worktrees/dispatch")
    monkeypatch.setattr(post_task_reap, "_ACP_RUNTIME_ROOT", repo / ".worktrees/dispatch/acp")
    monkeypatch.setattr(post_task_reap, "_pid_alive", lambda _pid: False)
    monkeypatch.setattr(post_task_reap.pr_identity, "resolve_repo_slug", lambda _root: "octo/hermetic")
    monkeypatch.setattr(post_task_reap.pr_identity, "probe_open_pr_for_branch", lambda **_kwargs: (False, None))
    record.write_text(
        json.dumps(
            {
                "task_id": "interrupted",
                "agent": "codex",
                "status": "done",
                "run_nonce": "attempt",
                "pid": 999_999_999,
                "worktree_path": str(tree),
                "worktree_branch": "codex/interrupted",
                "worktree_reused": False,
                "result_file": str(result),
                "result_sha256": hashes([result])[0],
            }
        )
    )
    return repo, tree, tasks, record, result, output


def _leave_regenerable_output(tree):
    (tree / "package-lock.json").write_text('{"lockfileVersion": 3}')
    (tree / ".gitignore").write_text("node_modules/\n__pycache__/\n")
    _run(["git", "add", "package-lock.json", ".gitignore"], cwd=tree)
    _run(["git", "commit", "-m", "regenerable fixture"], cwd=tree)
    for name in ["node_modules/package/index.js", "__pycache__/module.pyc"]:
        path = tree / name
        path.parent.mkdir(parents=True)
        path.write_bytes(b"regenerable")


@pytest.mark.parametrize("status", ["failed", "cancelled", "done", "needs_finalize", "rate_limited", "unknown"])
@pytest.mark.parametrize("regenerable", [False, True])
def test_post_task_reap_interrupted_unique_work_retains_bytes(interrupted_reap, status, regenerable):
    repo, tree, tasks, record, result, output = interrupted_reap
    if regenerable:
        _leave_regenerable_output(tree)
    head = _run(["git", "rev-parse", "HEAD"], cwd=tree).stdout.strip()
    state = json.loads(record.read_text())
    state["status"] = status
    record.write_text(json.dumps(state))
    before = hashes([record, result, output])
    for _ in range(2):
        report = post_task_reap.post_task_reap(
            "interrupted",
            tasks_dir=tasks,
            repo_root=repo,
            apply=True,
            include_acp_runtime=False,
        )
        assert report["main_worktree"]["action"] in {"skipped", "retained"}, report
        assert report["main_worktree"]["reason"] == (
            "task status not terminal (status=unknown)" if status == "unknown" else "unpushed_head"
        ), report
        assert hashes([record, result, output]) == before and tree.exists()
        assert _run(["git", "rev-parse", "HEAD"], cwd=tree).stdout.strip() == head


def test_post_task_reap_interrupted_pushed_regenerable_work_is_removed(interrupted_reap, monkeypatch):
    repo, tree, tasks, _record, _result, output = interrupted_reap
    _leave_regenerable_output(tree)
    output.unlink()
    _run(["git", "push", "-u", "origin", "codex/interrupted"], cwd=tree)
    # Misclassifying either cache as unique output must block removal rather
    # than silently copying it and allowing the control to pass.
    monkeypatch.setattr(ignored_task_output, "MAX_PRESERVED_BYTES", 1)

    report = post_task_reap.post_task_reap(
        "interrupted", tasks_dir=tasks, repo_root=repo, apply=True, include_acp_runtime=False
    )

    assert report["main_worktree"]["action"] == "removed", report
    assert report["main_worktree"]["reason"] == "HEAD matches origin/codex/interrupted", report
    assert not tree.exists()
    assert not report["main_worktree"].get("preserved_artifacts")
    assert not (repo / "batch_state/preserved").exists()


sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

from scripts.fleet import ignored_task_output, post_task_reap
from tests import _worktree_artifact_links as links
from tests.worktree_prep_helpers import half_built_prep, leave_half_built


def test_s3_post_task_reap_preserves_tar_member_with_restored_old_mtime(hermetic_reap, tmp_path):
    repo, tasks = hermetic_reap
    task_id = "tar-output-9645"
    worktree = _add_dispatch_worktree(repo, "kimi", task_id)
    with (repo / ".git/info/exclude").open("a") as exclude:
        exclude.write(".cache/\n")
    payload = b"archived task output"
    archive = tmp_path / "fixture.tar"
    with tarfile.open(archive, "w") as bundle:
        member = tarfile.TarInfo(".cache/dl/archive_member.txt")
        member.mtime = 946684800
        member.size = len(payload)
        bundle.addfile(member, io.BytesIO(payload))
    started = datetime.now(UTC)
    subprocess.run(["tar", "-xf", str(archive), "-C", str(worktree)], check=True, timeout=30)
    source = worktree / ".cache/dl/archive_member.txt"
    assert source.stat().st_mtime < started.timestamp() <= source.stat().st_ctime
    recent = source.parent / "recent.txt"
    recent.write_bytes(b"recent")
    _write_task_state(tasks, task_id, "done", worktree)
    record_path = tasks / f"{task_id}.json"
    record = json.loads(record_path.read_text())
    record["started_at"] = started.isoformat()
    record_path.write_text(json.dumps(record))
    report = post_task_reap.post_task_reap(task_id, tasks_dir=tasks, repo_root=repo, apply=True)
    assert report["main_worktree"]["action"] == "removed", report
    assert not worktree.exists()
    receipt = json.loads(record_path.read_text())["preserved_artifacts"]
    assert receipt["count"] == 2 and receipt["bytes"] == len(payload) + 6
    location = repo / receipt["location"]
    assert (location / ".cache/dl/archive_member.txt").read_bytes() == payload
    assert (location / ".cache/dl/recent.txt").read_bytes() == b"recent"


def _safe_label(task_id: str) -> str:
    return re.sub(r"[^A-Za-z0-9._-]+", "-", task_id).strip("-._")[:32]


@pytest.fixture
def hermetic_reap(monkeypatch, tmp_path):
    """Redirect post_task_reap to a fresh git repo and task directory."""
    repo_root = tmp_path / "repo"
    tasks_dir = tmp_path / "tasks"
    tasks_dir.mkdir(parents=True)

    monkeypatch.setattr(post_task_reap, "ROOT", repo_root)
    monkeypatch.setenv("LU_TASKS_DIR", str(tasks_dir))
    monkeypatch.setattr(post_task_reap, "_DISPATCH_WORKTREES_ROOT", repo_root / ".worktrees" / "dispatch")
    monkeypatch.setattr(post_task_reap, "_ACP_RUNTIME_ROOT", repo_root / ".worktrees" / "dispatch" / "acp")

    _init_repo(repo_root)

    # Tests control process liveness so we stay independent of lsof availability.
    monkeypatch.setattr(post_task_reap, "_probe_path_liveness", lambda _path: False)
    monkeypatch.setattr(post_task_reap.reap_worktrees, "_live_cwd_paths", lambda _repo: set())
    # Deterministic empty active-task probe; individual tests override it.
    monkeypatch.setattr(post_task_reap.reap_worktrees, "_active_task_ids", lambda: set())

    def merged_pr(_repo: Path, branch: str | None):
        if branch is None:
            return [], None
        proc = _run(["git", "rev-parse", f"refs/heads/{branch}"], cwd=repo_root)
        head = (proc.stdout or "").strip() if proc.returncode == 0 else None
        return [post_task_reap.reap_worktrees.PullRequestState(1, "MERGED", head)], None

    monkeypatch.setattr(post_task_reap.reap_worktrees, "_query_pr_states", merged_pr)
    # The commit-SHA PR search is a PR guard too: a failed lookup keeps the
    # checkout, so the hermetic repo answers it instead of shelling out to gh.
    monkeypatch.setattr(post_task_reap.reap_worktrees, "_query_prs_by_head_sha", lambda _repo, _sha: ([], None))

    # Shared-probe control (#7127): the bound checkout resolves to a GitHub
    # repository and provably has no OPEN PR, unless a test overrides it.
    monkeypatch.setattr(post_task_reap.pr_identity, "resolve_repo_slug", lambda _root: "octo/hermetic")
    monkeypatch.setattr(
        post_task_reap.pr_identity,
        "probe_open_pr_for_branch",
        lambda **_kwargs: (False, None),
    )

    return repo_root, tasks_dir


def _git_env() -> dict[str, str]:
    return {
        key: value
        for key, value in os.environ.items()
        if not key.startswith("GIT_") and not key.startswith("PRE_COMMIT") and key != "AGENT_NO_MERGE"
    }


def _run(args: list[str], cwd: Path, check: bool = True) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        args,
        cwd=cwd,
        capture_output=True,
        text=True,
        check=check,
        timeout=30,
        env=_git_env(),
    )


def _init_repo(repo_root: Path) -> None:
    repo_root.mkdir(parents=True)
    remote = repo_root.parent / f"{repo_root.name}-origin.git"
    _run(["git", "init", "--bare", str(remote)], cwd=repo_root.parent)
    _run(["git", "init", "--initial-branch=main", str(repo_root)], cwd=repo_root.parent)
    _run(["git", "config", "user.email", "test@example.com"], cwd=repo_root)
    _run(["git", "config", "user.name", "Test User"], cwd=repo_root)
    (repo_root / "README.md").write_text("# test\n", encoding="utf-8")
    _run(["git", "add", "README.md"], cwd=repo_root)
    _run(["git", "commit", "-m", "initial"], cwd=repo_root)
    _run(["git", "remote", "add", "origin", str(remote)], cwd=repo_root)
    _run(["git", "push", "-u", "origin", "main"], cwd=repo_root)


def _add_dispatch_worktree(repo_root: Path, agent: str, task_id: str) -> Path:
    branch = f"{agent}/{task_id}"
    _run(["git", "branch", branch], cwd=repo_root)
    path = repo_root / ".worktrees" / "dispatch" / agent / task_id
    path.parent.mkdir(parents=True, exist_ok=True)
    _run(["git", "worktree", "add", str(path), branch], cwd=repo_root)
    return path


def _add_external_worktree(repo_root: Path, name: str) -> Path:
    branch = f"external/{name}"
    _run(["git", "branch", branch], cwd=repo_root)
    path = repo_root / ".worktrees" / name
    path.mkdir(parents=True, exist_ok=True)
    _run(["git", "worktree", "add", str(path), branch], cwd=repo_root)
    return path


def _add_acp_runtime_worktree(repo_root: Path, task_id: str, locked: bool = False) -> Path:
    label = _safe_label(task_id)
    path = repo_root / ".worktrees" / "dispatch" / "acp" / f"runtime-{label}-deadbeef"
    path.parent.mkdir(parents=True, exist_ok=True)
    _run(
        ["git", "worktree", "add", "--detach", "--no-checkout", str(path), "HEAD"],
        cwd=repo_root,
    )
    if locked:
        _run(
            ["git", "worktree", "lock", "--reason", f"active ACP execution {label}", str(path)],
            cwd=repo_root,
        )
    return path


def _write_task_state(
    tasks_dir: Path,
    task_id: str,
    status: str,
    worktree_path: Path | None,
    *,
    agent: str = "kimi",
    acp_runtime_paths: list[Path] | None = None,
    pid: int | None = None,
) -> None:
    state: dict[str, Any] = {
        "task_id": task_id,
        "agent": agent,
        "status": status,
    }
    if worktree_path is not None:
        state["worktree_path"] = str(worktree_path)
    if acp_runtime_paths:
        state["acp_runtime_paths"] = [str(p) for p in acp_runtime_paths]
    if pid is not None:
        state["pid"] = pid
    safe = task_id.replace("/", "_").replace("\\", "_")
    (tasks_dir / f"{safe}.json").write_text(json.dumps(state), encoding="utf-8")


def test_no_task_state(hermetic_reap):
    repo_root, tasks_dir = hermetic_reap
    report = post_task_reap.post_task_reap("missing-task", tasks_dir=tasks_dir, repo_root=repo_root)

    assert report["task_status"] is None
    assert report["main_worktree"]["action"] == "retained"
    assert "no task state" in report["main_worktree"]["reason"]


@pytest.mark.parametrize("contents", ["regenerable_only", "mixed", "oversized_output", "symlink", "unpublished_manifest", "oversized_manifest"])
def test_post_task_reap_regenerable_classification(hermetic_reap, monkeypatch, tmp_path, contents):
    repo, tasks = hermetic_reap
    (repo / "site").mkdir()
    (repo / "site/package-lock.json").write_text('{"lockfileVersion": 3}')
    (repo / ".gitignore").write_text(
        "node_modules\n__pycache__/\n.pytest_cache/\n.ruff_cache/\n.mypy_cache/\n"
        "site/src/data/lexicon-manifest.json\nignored/\n"
    )
    pointer = repo / "site/src/data/lexicon-manifest.pointer.json"
    pointer.parent.mkdir(parents=True)
    pointer.write_text(json.dumps({"json_sha256": hashlib.sha256(b"x" * 64).hexdigest()}))
    _run(["git", "add", "site/package-lock.json", ".gitignore", "site/src/data/lexicon-manifest.pointer.json"], cwd=repo)
    _run(["git", "commit", "-m", "fixture lock and ignored patterns"], cwd=repo)
    _run(["git", "push", "origin", "main"], cwd=repo)
    task_id = "regenerable-9828"
    worktree = _add_dispatch_worktree(repo, "codex", task_id)
    outside = tmp_path / "outside-output"
    outside.mkdir()
    (outside / "unique.txt").write_bytes(b"unique outside output")
    if contents == "symlink":
        (worktree / "site/node_modules").symlink_to(outside)
    else:
        for name in [
            "site/node_modules/package/index.js",
            "nested/__pycache__/module.pyc",
            "nested/.pytest_cache/cache.bin",
            ".ruff_cache/cache.bin",
            ".mypy_cache/cache.bin",
        ]:
            path = worktree / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(b"x" * 64)
        # Dependency links are skipped with the real dependency directory;
        # removing the worktree unlinks them without deleting their targets.
        (worktree / "site/node_modules/outside-link").symlink_to(outside)
    if contents in {"mixed", "oversized_output"}:
        (worktree / "ignored").mkdir()
        (worktree / "ignored/answer.txt").write_bytes(b"answer" if contents == "mixed" else b"x" * 32)
    unpublished = b'{"entries": ["promoted"]}'
    if contents in {"unpublished_manifest", "oversized_manifest"}:
        (worktree / "site/src/data/lexicon-manifest.json").write_bytes(
            unpublished if contents == "unpublished_manifest" else b"x" * 64
        )
    cap = {"unpublished_manifest": 32, "symlink": 4096}.get(contents, 16)
    monkeypatch.setattr(ignored_task_output, "MAX_PRESERVED_BYTES", cap)
    _write_task_state(tasks, task_id, "done", worktree, agent="codex")
    report = post_task_reap.post_task_reap(task_id, tasks_dir=tasks, repo_root=repo, apply=True)
    row = report["main_worktree"]
    assert (outside / "unique.txt").read_bytes() == b"unique outside output"
    if contents == "symlink":
        assert row["action"] == "removed" and not worktree.exists(), row
        receipt = row["preserved_artifacts"]
        entry = next(item for item in receipt["paths"] if item["path"] == "site/node_modules")
        assert entry["type"] == "symlink"
        assert entry["target"] == str(outside)
        copied = repo / receipt["location"] / entry["path"]
        assert copied.is_file() and not copied.is_symlink()
        assert b"unique outside output" not in copied.read_bytes()
        return
    if contents == "oversized_output":
        assert row["action"] == "skipped" and worktree.exists(), row
        assert "exceeds preservation cap" in row["reason"]
        assert not (repo / "batch_state/preserved").exists()
    else:
        assert row["action"] == "removed" and not worktree.exists(), row
        # #10061: hydrate:manifest writes the ignored manifest, so neither
        # unpublished bytes nor bytes above the cap require preservation.
        if contents in {"regenerable_only", "unpublished_manifest", "oversized_manifest"}:
            assert not row.get("preserved_artifacts")
            assert not (repo / "batch_state/preserved").exists()
        else:
            receipt = row["preserved_artifacts"]
            assert receipt["count"] == 1 and receipt["bytes"] == 6
            assert [entry["path"] for entry in receipt["paths"]] == ["ignored/answer.txt"]
            assert (repo / receipt["location"] / "ignored/answer.txt").read_bytes() == b"answer"


@pytest.mark.parametrize(
    "tree_owner,tasks_owner", [("sibling", "public"), ("sibling", "sibling"), ("public", "sibling")]
)
@pytest.mark.parametrize("repo_hint", ["public", "sibling"])
@pytest.mark.parametrize("cache_state", ["cold", "stale"])
def test_retention_lookup_leaves_primaries_byte_identical(
    hermetic_reap, tmp_path, monkeypatch, tree_owner, tasks_owner, repo_hint, cache_state
):
    public, _ = hermetic_reap
    sibling = tmp_path / "sibling"
    _init_repo(sibling)
    roots = {"public": public, "sibling": sibling}
    monkeypatch.setattr(post_task_reap.worktree_claims, "public_primary_root", lambda: public)
    task_id = "retention-cache-9797"
    worktree = _add_dispatch_worktree(roots[tree_owner], "codex", task_id)
    tasks = roots[tasks_owner] / "batch_state/tasks"
    tasks.mkdir(parents=True)
    record = {
        "task_id": task_id,
        "status": "done",
        "worktree_path": str(worktree),
        "worktree_reused": False,
        "run_nonce": "retention-cache-run",
    }
    (tasks / f"{task_id}.json").write_text(json.dumps(record))
    cache = post_task_reap.ignored_task_output._identity_cache_path(tasks)
    if cache_state == "stale":
        cache.write_bytes(b"stale identity cache\n")
    # Dispatch already owns this persistent lock; reap must not create it.
    hint = roots[repo_hint]
    with post_task_reap.worktree_claims.worktree_lock(
        worktree, lock_dir=post_task_reap.worktree_claims.repository_lock_dir(hint)
    ):
        pass

    def snapshot(root):
        return {
            str(path.relative_to(root)): (path.read_bytes(), path.stat().st_mtime_ns)
            for path in root.rglob("*")
            if path.is_file()
        }

    before = {name: snapshot(root) for name, root in roots.items()}
    report = post_task_reap.post_task_reap(task_id, tasks_dir=tasks, repo_root=hint, apply=True, release_retention=True)
    # The lookup ran, but missing retrieval proof still refuses release.
    assert report["errors"] == ["retention release requires an existing passing retrieval receipt"]
    assert report["main_worktree"]["action"] == "retained"
    assert worktree.exists()
    assert {name: snapshot(root) for name, root in roots.items()} == before


def test_retention_lookup_publishes_for_public_tree_and_canonical_tasks(hermetic_reap, monkeypatch):
    public, _ = hermetic_reap
    monkeypatch.setattr(post_task_reap.worktree_claims, "public_primary_root", lambda: public)
    task_id = "public-retention-cache-9797"
    worktree = _add_dispatch_worktree(public, "codex", task_id)
    tasks = public / "batch_state/tasks"
    tasks.mkdir(parents=True)
    (tasks / f"{task_id}.json").write_text(
        json.dumps(
            {
                "task_id": task_id,
                "status": "done",
                "worktree_path": str(worktree),
                "worktree_reused": False,
                "run_nonce": "public-retention-run",
            }
        )
    )
    report = post_task_reap.post_task_reap(
        task_id, tasks_dir=tasks, repo_root=public, apply=True, release_retention=True
    )
    assert report["errors"] == ["retention release requires an existing passing retrieval receipt"]
    assert post_task_reap.ignored_task_output._identity_cache_path(tasks).is_file()


@pytest.mark.parametrize("runtime", [False, True])
@pytest.mark.parametrize("artifact_name", ["batch_state/report.txt", ".cache/transcriptions/page.txt"])
def test_post_task_reap_preserves_ignored_artifacts(hermetic_reap, runtime, artifact_name):
    repo, tasks = hermetic_reap
    task_id = "preserve-post-task"
    worktree = _add_acp_runtime_worktree(repo, task_id) if runtime else _add_dispatch_worktree(repo, "kimi", task_id)
    with (repo / ".git/info/exclude").open("a") as exclude:
        exclude.write("batch_state/\n.cache/\n")
    artifact = worktree / artifact_name
    artifact.parent.mkdir(parents=True)
    artifact.write_bytes(b"post-task evidence")
    _write_task_state(
        tasks, task_id, "done", None if runtime else worktree, acp_runtime_paths=[worktree] if runtime else None
    )
    path = tasks / f"{task_id}.json"
    report = post_task_reap.post_task_reap(task_id, tasks_dir=tasks, repo_root=repo, apply=True)

    row = report["acp_runtimes"][0] if runtime else report["main_worktree"]
    assert row["action"] == "removed", row
    assert not worktree.exists()
    state = json.loads(path.read_text())
    receipt = row["preserved_artifacts"]
    assert state["preserved_artifacts"] == receipt
    assert receipt["retrieval_proof_sha256"] == receipt["content_sha256"]
    assert receipt["count"] == 1
    assert receipt["bytes"] == len(b"post-task evidence")
    assert ((repo / receipt["location"]) / artifact_name).read_bytes() == b"post-task evidence"


def test_running_skip(hermetic_reap):
    repo_root, tasks_dir = hermetic_reap
    worktree = _add_dispatch_worktree(repo_root, "kimi", "running-task")
    _write_task_state(tasks_dir, "running-task", "running", worktree)

    report = post_task_reap.post_task_reap("running-task", tasks_dir=tasks_dir, repo_root=repo_root)

    assert report["task_status"] == "running"
    assert report["main_worktree"]["action"] == "retained"
    assert "still active" in report["main_worktree"]["reason"]
    assert worktree.exists()


def test_spawning_skip(hermetic_reap):
    repo_root, tasks_dir = hermetic_reap
    worktree = _add_dispatch_worktree(repo_root, "kimi", "spawning-task")
    _write_task_state(tasks_dir, "spawning-task", "spawning", worktree)

    report = post_task_reap.post_task_reap("spawning-task", tasks_dir=tasks_dir, repo_root=repo_root)

    assert report["main_worktree"]["action"] == "retained"
    assert "still active" in report["main_worktree"]["reason"]
    assert worktree.exists()


def test_dirty_skip(hermetic_reap):
    repo_root, tasks_dir = hermetic_reap
    worktree = _add_dispatch_worktree(repo_root, "kimi", "dirty-task")
    _write_task_state(tasks_dir, "dirty-task", "done", worktree)
    (worktree / "new_file.txt").write_text("dirty", encoding="utf-8")

    report = post_task_reap.post_task_reap("dirty-task", tasks_dir=tasks_dir, repo_root=repo_root)

    assert report["main_worktree"]["action"] == "retained"
    assert "uncommitted changes" in report["main_worktree"]["reason"]
    assert worktree.exists()


def test_clean_terminal_reap_dry_run(hermetic_reap):
    repo_root, tasks_dir = hermetic_reap
    worktree = _add_dispatch_worktree(repo_root, "kimi", "clean-task")
    _write_task_state(tasks_dir, "clean-task", "done", worktree)

    report = post_task_reap.post_task_reap("clean-task", tasks_dir=tasks_dir, repo_root=repo_root)

    assert report["main_worktree"]["action"] == "would_remove"
    assert report["main_worktree"]["reason"] == "PR #1 MERGED"
    assert worktree.exists()


def test_clean_terminal_reap_apply(hermetic_reap):
    repo_root, tasks_dir = hermetic_reap
    worktree = _add_dispatch_worktree(repo_root, "kimi", "clean-task")
    _write_task_state(tasks_dir, "clean-task", "done", worktree)

    report = post_task_reap.post_task_reap("clean-task", tasks_dir=tasks_dir, repo_root=repo_root, apply=True)

    assert report["main_worktree"]["action"] == "removed"
    assert report["main_worktree"]["error"] is None
    assert not worktree.exists()


def _no_pr_states(_repo: Path, _branch: str | None):
    return [], None


def test_no_pr_terminal_reap_dry_run(hermetic_reap, monkeypatch):
    """A terminal task with no PR and a clean tree reaps even without GitHub."""
    repo_root, tasks_dir = hermetic_reap
    worktree = _add_dispatch_worktree(repo_root, "kimi", "no-pr-task")
    _write_task_state(tasks_dir, "no-pr-task", "done", worktree)
    monkeypatch.setattr(post_task_reap.reap_worktrees, "_query_pr_states", _no_pr_states)
    # Simulate the delegate active-task API being unavailable: the canonical
    # Class-A settled-dispatch path fails closed on it, so the no-PR fallback
    # must carry the reap after post_task_reap's own guards pass.
    monkeypatch.setattr(post_task_reap.reap_worktrees, "_active_task_ids", lambda: None)

    report = post_task_reap.post_task_reap("no-pr-task", tasks_dir=tasks_dir, repo_root=repo_root)

    assert report["main_worktree"]["action"] == "would_remove"
    assert "settled dispatch" in report["main_worktree"]["reason"]
    assert worktree.exists()


def test_no_pr_terminal_reap_apply(hermetic_reap, monkeypatch):
    repo_root, tasks_dir = hermetic_reap
    worktree = _add_dispatch_worktree(repo_root, "kimi", "no-pr-task")
    _write_task_state(tasks_dir, "no-pr-task", "done", worktree)
    monkeypatch.setattr(post_task_reap.reap_worktrees, "_query_pr_states", _no_pr_states)
    monkeypatch.setattr(post_task_reap.reap_worktrees, "_active_task_ids", lambda: None)

    report = post_task_reap.post_task_reap("no-pr-task", tasks_dir=tasks_dir, repo_root=repo_root, apply=True)

    assert report["main_worktree"]["action"] == "removed"
    assert report["main_worktree"]["error"] is None
    assert not worktree.exists()


def test_post_task_reap_unpushed_local_commit_is_retained(hermetic_reap, monkeypatch):
    """post_task_reap retains worktree when local commits have not been pushed to origin."""
    repo_root, tasks_dir = hermetic_reap
    worktree = _add_dispatch_worktree(repo_root, "kimi", "unpushed-task")
    (worktree / "unpushed.txt").write_text("local only\n", encoding="utf-8")
    _run(["git", "add", "unpushed.txt"], cwd=worktree)
    _run(["git", "commit", "-m", "local commit"], cwd=worktree)
    _write_task_state(tasks_dir, "unpushed-task", "done", worktree)
    monkeypatch.setattr(post_task_reap.reap_worktrees, "_query_pr_states", _no_pr_states)

    report = post_task_reap.post_task_reap("unpushed-task", tasks_dir=tasks_dir, repo_root=repo_root, apply=True)

    assert report["main_worktree"]["action"] in {"skipped", "retained"}
    assert report["main_worktree"]["reason"] == "unpushed_head"
    assert worktree.exists()
    assert (worktree / "unpushed.txt").read_text(encoding="utf-8") == "local only\n"


def test_no_pr_timeout_terminal_reap_apply(hermetic_reap, monkeypatch):
    """timeout is terminal for post_task_reap but outside the canonical Class-A
    set; the no-PR fallback must reap it when the tree is clean and PID dead."""
    repo_root, tasks_dir = hermetic_reap
    worktree = _add_dispatch_worktree(repo_root, "kimi", "timeout-task")
    _write_task_state(tasks_dir, "timeout-task", "timeout", worktree)
    monkeypatch.setattr(post_task_reap.reap_worktrees, "_query_pr_states", _no_pr_states)

    report = post_task_reap.post_task_reap("timeout-task", tasks_dir=tasks_dir, repo_root=repo_root, apply=True)

    assert report["main_worktree"]["action"] == "removed"
    assert report["main_worktree"]["error"] is None
    assert not worktree.exists()


def test_no_pr_needs_finalize_terminal_reap_apply(hermetic_reap, monkeypatch):
    repo_root, tasks_dir = hermetic_reap
    worktree = _add_dispatch_worktree(repo_root, "kimi", "finalize-task")
    _write_task_state(tasks_dir, "finalize-task", "needs_finalize", worktree)
    monkeypatch.setattr(post_task_reap.reap_worktrees, "_query_pr_states", _no_pr_states)

    report = post_task_reap.post_task_reap("finalize-task", tasks_dir=tasks_dir, repo_root=repo_root, apply=True)

    assert report["main_worktree"]["action"] == "removed"
    assert report["main_worktree"]["error"] is None
    assert not worktree.exists()


def test_no_pr_open_pr_retain(hermetic_reap, monkeypatch):
    """An open PR must block the no-PR terminal reap even when everything else
    (terminal, clean, dead PID) passes."""
    repo_root, tasks_dir = hermetic_reap
    worktree = _add_dispatch_worktree(repo_root, "kimi", "open-pr-task")
    _write_task_state(tasks_dir, "open-pr-task", "done", worktree)

    def open_pr(_repo: Path, _branch: str | None):
        return [post_task_reap.reap_worktrees.PullRequestState(9, "OPEN", "deadbeef")], None

    # The canonical path declines on the OPEN PR; the shared probe (#7127)
    # must independently confirm it for the no-PR fallback.
    monkeypatch.setattr(post_task_reap.reap_worktrees, "_query_pr_states", open_pr)
    monkeypatch.setattr(
        post_task_reap.pr_identity,
        "probe_open_pr_for_branch",
        lambda **_kwargs: (True, None),
    )

    report = post_task_reap.post_task_reap("open-pr-task", tasks_dir=tasks_dir, repo_root=repo_root, apply=True)

    assert report["main_worktree"]["action"] in {"skipped", "retained"}
    assert "open PR" in report["main_worktree"]["reason"]
    assert worktree.exists()


def test_no_pr_fallback_open_pr_retain(hermetic_reap, monkeypatch):
    """When the canonical reaper declines without PR info, the shared probe
    (#7127) must independently confirm an open PR and retain the worktree."""
    repo_root, tasks_dir = hermetic_reap
    worktree = _add_dispatch_worktree(repo_root, "kimi", "open-pr-fallback-task")
    _write_task_state(tasks_dir, "open-pr-fallback-task", "done", worktree)

    monkeypatch.setattr(post_task_reap.reap_worktrees, "_query_pr_states", _no_pr_states)
    monkeypatch.setattr(post_task_reap.reap_worktrees, "_active_task_ids", lambda: None)
    monkeypatch.setattr(
        post_task_reap.pr_identity,
        "probe_open_pr_for_branch",
        lambda **_kwargs: (True, None),
    )

    report = post_task_reap.post_task_reap(
        "open-pr-fallback-task", tasks_dir=tasks_dir, repo_root=repo_root, apply=True
    )

    assert report["main_worktree"]["action"] == "retained"
    assert "open PR" in report["main_worktree"]["reason"]
    assert worktree.exists()


def test_no_pr_probe_unknown_retain(hermetic_reap, monkeypatch):
    """An unknown shared-probe answer (malformed gh row, outage, …) is
    fail-closed: the no-PR fallback must retain, never delete on a guess."""
    repo_root, tasks_dir = hermetic_reap
    worktree = _add_dispatch_worktree(repo_root, "kimi", "pr-unknown-task")
    _write_task_state(tasks_dir, "pr-unknown-task", "done", worktree)

    monkeypatch.setattr(post_task_reap.reap_worktrees, "_query_pr_states", _no_pr_states)
    # Force the no-PR fallback (which consults the shared probe) by failing the
    # canonical Class-A settled-dispatch activity probe, as in the dry-run test.
    monkeypatch.setattr(post_task_reap.reap_worktrees, "_active_task_ids", lambda: None)
    monkeypatch.setattr(
        post_task_reap.pr_identity,
        "probe_open_pr_for_branch",
        lambda **_kwargs: (None, "gh pr list returned a malformed row (not an object)"),
    )

    report = post_task_reap.post_task_reap("pr-unknown-task", tasks_dir=tasks_dir, repo_root=repo_root, apply=True)

    assert report["main_worktree"]["action"] == "retained"
    assert "PR guard unavailable" in report["main_worktree"]["reason"]
    assert worktree.exists()


def test_no_pr_pr_probe_error_retain(hermetic_reap, monkeypatch):
    """A PR probe error is fail-closed: the no-PR fallback must retain."""
    repo_root, tasks_dir = hermetic_reap
    worktree = _add_dispatch_worktree(repo_root, "kimi", "pr-error-task")
    _write_task_state(tasks_dir, "pr-error-task", "done", worktree)
    monkeypatch.setattr(
        post_task_reap.reap_worktrees,
        "_query_pr_states",
        lambda _repo, _branch: ([], "gh unavailable"),
    )

    report = post_task_reap.post_task_reap("pr-error-task", tasks_dir=tasks_dir, repo_root=repo_root, apply=True)

    assert report["main_worktree"]["action"] == "skipped"
    assert "PR guard unavailable" in report["main_worktree"]["reason"]
    assert worktree.exists()


def test_terminal_failed_reap_apply(hermetic_reap):
    repo_root, tasks_dir = hermetic_reap
    worktree = _add_dispatch_worktree(repo_root, "kimi", "failed-task")
    _write_task_state(tasks_dir, "failed-task", "failed", worktree)

    report = post_task_reap.post_task_reap("failed-task", tasks_dir=tasks_dir, repo_root=repo_root, apply=True)

    assert report["main_worktree"]["action"] == "removed"
    assert not worktree.exists()


def test_ambiguous_retain_no_state_path(hermetic_reap):
    repo_root, tasks_dir = hermetic_reap
    worktree = _add_dispatch_worktree(repo_root, "kimi", "ambiguous-task")
    _write_task_state(tasks_dir, "ambiguous-task", "done", worktree_path=None)

    report = post_task_reap.post_task_reap("ambiguous-task", tasks_dir=tasks_dir, repo_root=repo_root)

    assert report["main_worktree"]["action"] == "retained"
    assert "unknown ownership" in report["main_worktree"]["reason"]
    assert worktree.exists()


def test_ambiguous_retain_outside_dispatch(hermetic_reap):
    repo_root, tasks_dir = hermetic_reap
    external = _add_external_worktree(repo_root, "external-task")
    _write_task_state(tasks_dir, "external-task", "done", external)

    report = post_task_reap.post_task_reap("external-task", tasks_dir=tasks_dir, repo_root=repo_root)

    assert report["main_worktree"]["action"] == "retained"
    assert "outside .worktrees/dispatch" in report["main_worktree"]["reason"]
    assert external.exists()


def test_ambiguous_retain_unregistered_directory(hermetic_reap):
    repo_root, tasks_dir = hermetic_reap
    bogus = repo_root / ".worktrees" / "dispatch" / "kimi" / "bogus-task"
    bogus.mkdir(parents=True)
    _write_task_state(tasks_dir, "bogus-task", "done", bogus)

    report = post_task_reap.post_task_reap("bogus-task", tasks_dir=tasks_dir, repo_root=repo_root)

    assert report["main_worktree"]["action"] == "retained"
    assert "not a registered git worktree" in report["main_worktree"]["reason"]
    assert bogus.exists()


def test_reap_pending_reservation_refuses_bound_task(hermetic_reap):
    repo_root, tasks_dir = hermetic_reap
    worktree = _add_dispatch_worktree(repo_root, "kimi", "pending-task")
    _write_task_state(tasks_dir, "pending-task", "done", worktree)
    post_task_reap.reaper_lifecycle.mark_reap_pending(
        repo_root,
        worktree_path=worktree,
        branch="kimi/pending-task",
        head=_run(["git", "rev-parse", "HEAD"], cwd=worktree).stdout.strip(),
        task_id="pending-task",
    )

    report = post_task_reap.post_task_reap("pending-task", tasks_dir=tasks_dir, repo_root=repo_root, apply=True)

    assert report["main_worktree"]["action"] == "retained"
    assert report["main_worktree"]["reason"] == "reap-pending reservation blocks a new task bind"
    assert worktree.exists()


def test_main_worktree_retain_when_pid_alive(hermetic_reap, monkeypatch):
    repo_root, tasks_dir = hermetic_reap
    worktree = _add_dispatch_worktree(repo_root, "kimi", "pid-alive-task")
    _write_task_state(tasks_dir, "pid-alive-task", "done", worktree, pid=12345)

    monkeypatch.setattr(post_task_reap, "_pid_alive", lambda _pid: True)

    report = post_task_reap.post_task_reap("pid-alive-task", tasks_dir=tasks_dir, repo_root=repo_root, apply=True)

    assert report["main_worktree"]["action"] == "retained"
    assert "live process" in report["main_worktree"]["reason"]
    assert worktree.exists()


def test_main_worktree_retain_when_pid_liveness_fails(hermetic_reap, monkeypatch):
    repo_root, tasks_dir = hermetic_reap
    worktree = _add_dispatch_worktree(repo_root, "kimi", "pid-error-task")
    _write_task_state(tasks_dir, "pid-error-task", "done", worktree, pid=12345)

    monkeypatch.setattr(post_task_reap, "_pid_alive", lambda _pid: None)

    report = post_task_reap.post_task_reap("pid-error-task", tasks_dir=tasks_dir, repo_root=repo_root, apply=True)

    assert report["main_worktree"]["action"] == "retained"
    assert "liveness probe failed" in report["main_worktree"]["reason"]
    assert worktree.exists()

    # MUTATION-CHECK: if the main-worktree liveness check stopped failing closed,
    # an errored probe would have allowed removal.
    monkeypatch.setattr(post_task_reap, "_pid_alive", lambda _pid: False)
    mutated = post_task_reap.post_task_reap("pid-error-task", tasks_dir=tasks_dir, repo_root=repo_root, apply=True)
    assert mutated["main_worktree"]["action"] == "removed"


def test_acp_runtime_reap_when_process_gone(hermetic_reap):
    repo_root, tasks_dir = hermetic_reap
    main_worktree = _add_dispatch_worktree(repo_root, "kimi", "acp-task")
    acp_path = _add_acp_runtime_worktree(repo_root, "acp-task", locked=False)
    _write_task_state(tasks_dir, "acp-task", "done", main_worktree, acp_runtime_paths=[acp_path])

    report = post_task_reap.post_task_reap("acp-task", tasks_dir=tasks_dir, repo_root=repo_root, apply=True)

    assert report["main_worktree"]["action"] == "removed"
    assert len(report["acp_runtimes"]) == 1
    assert report["acp_runtimes"][0]["action"] == "removed"
    assert report["acp_runtimes"][0]["path"] == str(acp_path)
    assert not acp_path.exists()


def test_post_task_reap_preserves_another_reviews_input_until_terminal(hermetic_reap):
    repo_root, tasks_dir = hermetic_reap
    acp_path = _add_acp_runtime_worktree(repo_root, "input-owner", locked=False)
    _write_task_state(tasks_dir, "input-owner", "done", None, acp_runtime_paths=[acp_path])
    state = tasks_dir / "reviewer.json"
    record = {"task_id": "reviewer", "status": "running", "review_contract": {"input_root": str(acp_path)}}
    state.write_text(json.dumps(record))
    report = post_task_reap.post_task_reap("input-owner", tasks_dir=tasks_dir, repo_root=repo_root, apply=True)
    assert report["acp_runtimes"][0]["action"] == "retained"
    assert "review input root claimed by active task reviewer" in report["acp_runtimes"][0]["reason"]
    assert acp_path.exists()
    record["status"] = "crashed"
    state.write_text(json.dumps(record))
    report = post_task_reap.post_task_reap("input-owner", tasks_dir=tasks_dir, repo_root=repo_root, apply=True)
    assert report["acp_runtimes"][0]["action"] == "removed"
    assert not acp_path.exists()


def test_acp_runtime_retain_while_process_alive(hermetic_reap, monkeypatch):
    repo_root, tasks_dir = hermetic_reap
    main_worktree = _add_dispatch_worktree(repo_root, "kimi", "acp-task")
    acp_path = _add_acp_runtime_worktree(repo_root, "acp-task", locked=False)
    _write_task_state(tasks_dir, "acp-task", "done", main_worktree, acp_runtime_paths=[acp_path])

    # Simulate a live process holding the ACP runtime path.
    monkeypatch.setattr(post_task_reap, "_probe_path_liveness", lambda _path: True)

    report = post_task_reap.post_task_reap("acp-task", tasks_dir=tasks_dir, repo_root=repo_root)

    assert report["main_worktree"]["action"] == "would_remove"
    assert len(report["acp_runtimes"]) == 1
    assert report["acp_runtimes"][0]["action"] == "retained"
    assert "live process" in report["acp_runtimes"][0]["reason"]
    assert acp_path.exists()

    # MUTATION-CHECK: disabling the liveness check turns a live ACP runtime
    # path into a would-remove candidate.  The retain assertion above would fail.
    monkeypatch.setattr(post_task_reap, "_probe_path_liveness", lambda _path: False)
    mutated = post_task_reap.post_task_reap("acp-task", tasks_dir=tasks_dir, repo_root=repo_root)
    assert mutated["acp_runtimes"][0]["action"] == "would_remove"


def test_acp_runtime_retain_liveness_probe_failed(hermetic_reap, monkeypatch):
    repo_root, tasks_dir = hermetic_reap
    main_worktree = _add_dispatch_worktree(repo_root, "kimi", "acp-error-task")
    acp_path = _add_acp_runtime_worktree(repo_root, "acp-error-task", locked=False)
    _write_task_state(tasks_dir, "acp-error-task", "done", main_worktree, acp_runtime_paths=[acp_path])

    # Simulate a liveness probe that errors out instead of returning a result.
    monkeypatch.setattr(post_task_reap, "_probe_path_liveness", lambda _path: None)

    report = post_task_reap.post_task_reap("acp-error-task", tasks_dir=tasks_dir, repo_root=repo_root)

    assert report["main_worktree"]["action"] == "would_remove"
    assert len(report["acp_runtimes"]) == 1
    assert report["acp_runtimes"][0]["action"] == "retained"
    assert "liveness probe failed" in report["acp_runtimes"][0]["reason"]
    assert acp_path.exists()

    # MUTATION-CHECK: fail-closed means an errored probe must retain the path.
    # If the code treated an errored probe as "process gone", this would remove.
    monkeypatch.setattr(post_task_reap, "_probe_path_liveness", lambda _path: False)
    mutated = post_task_reap.post_task_reap("acp-error-task", tasks_dir=tasks_dir, repo_root=repo_root, apply=True)
    assert mutated["acp_runtimes"][0]["action"] == "removed"


def test_acp_runtime_retain_dirty(hermetic_reap):
    repo_root, tasks_dir = hermetic_reap
    main_worktree = _add_dispatch_worktree(repo_root, "kimi", "acp-dirty-task")
    acp_path = _add_acp_runtime_worktree(repo_root, "acp-dirty-task", locked=False)
    (acp_path / "dirt.txt").write_text("dirt", encoding="utf-8")
    _write_task_state(tasks_dir, "acp-dirty-task", "done", main_worktree, acp_runtime_paths=[acp_path])

    report = post_task_reap.post_task_reap("acp-dirty-task", tasks_dir=tasks_dir, repo_root=repo_root, apply=True)

    assert report["main_worktree"]["action"] == "removed"
    assert len(report["acp_runtimes"]) == 1
    assert report["acp_runtimes"][0]["action"] == "retained"
    assert "uncommitted changes" in report["acp_runtimes"][0]["reason"]
    assert acp_path.exists()


def test_acp_runtime_retain_unbound_name(hermetic_reap):
    """An ACP path whose name happens to contain the task label is not enough."""
    repo_root, tasks_dir = hermetic_reap
    main_worktree = _add_dispatch_worktree(repo_root, "kimi", "acp-unbound-task")
    # Path that the old name-matching logic would have claimed.
    acp_path = repo_root / ".worktrees" / "dispatch" / "acp" / "runtime-review-acp-unbound-task-12345"
    acp_path.parent.mkdir(parents=True, exist_ok=True)
    _run(
        ["git", "worktree", "add", "--detach", "--no-checkout", str(acp_path), "HEAD"],
        cwd=repo_root,
    )
    _write_task_state(tasks_dir, "acp-unbound-task", "done", main_worktree)

    report = post_task_reap.post_task_reap("acp-unbound-task", tasks_dir=tasks_dir, repo_root=repo_root, apply=True)

    assert report["main_worktree"]["action"] == "removed"
    assert report["acp_runtimes"] == []
    assert acp_path.exists()


def test_acp_runtime_retain_unregistered(hermetic_reap):
    repo_root, tasks_dir = hermetic_reap
    main_worktree = _add_dispatch_worktree(repo_root, "kimi", "acp-unreg-task")
    bogus_acp = repo_root / ".worktrees" / "dispatch" / "acp" / "runtime-acp-unreg-task-bogus"
    bogus_acp.mkdir(parents=True)
    _write_task_state(tasks_dir, "acp-unreg-task", "done", main_worktree, acp_runtime_paths=[bogus_acp])

    report = post_task_reap.post_task_reap("acp-unreg-task", tasks_dir=tasks_dir, repo_root=repo_root, apply=True)

    assert report["main_worktree"]["action"] == "removed"
    assert len(report["acp_runtimes"]) == 1
    assert report["acp_runtimes"][0]["action"] == "retained"
    assert "not a registered git worktree" in report["acp_runtimes"][0]["reason"]
    assert bogus_acp.exists()


def test_acp_runtime_retain_while_task_active(hermetic_reap):
    repo_root, tasks_dir = hermetic_reap
    main_worktree = _add_dispatch_worktree(repo_root, "kimi", "acp-active-task")
    acp_path = _add_acp_runtime_worktree(repo_root, "acp-active-task", locked=False)
    _write_task_state(tasks_dir, "acp-active-task", "running", main_worktree, acp_runtime_paths=[acp_path])

    report = post_task_reap.post_task_reap("acp-active-task", tasks_dir=tasks_dir, repo_root=repo_root)

    # Main worktree retained because task is active; ACP runtimes are not even
    # evaluated while the task is active.
    assert report["main_worktree"]["action"] == "retained"
    assert report["acp_runtimes"] == []
    assert acp_path.exists()


def test_cli_dry_run_default(hermetic_reap, capsys):
    repo_root, tasks_dir = hermetic_reap
    worktree = _add_dispatch_worktree(repo_root, "kimi", "cli-task")
    _write_task_state(tasks_dir, "cli-task", "done", worktree)

    code = post_task_reap.main(["--task-id", "cli-task", "--tasks-dir", str(tasks_dir), "--repo-root", str(repo_root)])
    captured = capsys.readouterr()

    assert code == 0
    report = json.loads(captured.out)
    assert report["main_worktree"]["action"] == "would_remove"
    assert worktree.exists()


def test_cli_apply_flag(hermetic_reap, capsys):
    repo_root, tasks_dir = hermetic_reap
    worktree = _add_dispatch_worktree(repo_root, "kimi", "cli-apply-task")
    _write_task_state(tasks_dir, "cli-apply-task", "done", worktree)

    code = post_task_reap.main(
        [
            "--task-id",
            "cli-apply-task",
            "--tasks-dir",
            str(tasks_dir),
            "--repo-root",
            str(repo_root),
            "--apply",
        ]
    )
    captured = capsys.readouterr()

    assert code == 0
    report = json.loads(captured.out)
    assert report["main_worktree"]["action"] == "removed"
    assert not worktree.exists()


def test_cli_no_acp_runtime(hermetic_reap, capsys):
    repo_root, tasks_dir = hermetic_reap
    main_worktree = _add_dispatch_worktree(repo_root, "kimi", "no-acp-task")
    acp_path = _add_acp_runtime_worktree(repo_root, "no-acp-task", locked=False)
    _write_task_state(tasks_dir, "no-acp-task", "done", main_worktree, acp_runtime_paths=[acp_path])

    code = post_task_reap.main(
        [
            "--task-id",
            "no-acp-task",
            "--tasks-dir",
            str(tasks_dir),
            "--repo-root",
            str(repo_root),
            "--apply",
            "--no-include-acp-runtime",
        ]
    )
    captured = capsys.readouterr()

    assert code == 0
    report = json.loads(captured.out)
    assert report["main_worktree"]["action"] == "removed"
    assert report["acp_runtimes"] == []
    assert acp_path.exists()


def _half_built_dispatch(
    repo_root: Path,
    tasks_dir: Path,
    task_id: str,
    *,
    status: str,
    pid: Any,
    reserved: bool = True,
) -> Path:
    """A dispatch worktree a killed ``git worktree add`` left: locked ``initializing``, partial (#8663)."""
    worktree = _add_dispatch_worktree(repo_root, "claude", task_id)
    leave_half_built(worktree, drop=("README.md",))
    state = {
        "task_id": task_id,
        "agent": "claude",
        "status": status,
        "pid": pid,
        "run_nonce": "nonce-8663",
        "worktree_path": str(worktree),
    }
    if reserved:
        state["worktree_prep"] = half_built_prep(worktree, run_nonce="nonce-8663")
    tasks_dir.mkdir(parents=True, exist_ok=True)
    (tasks_dir / f"{task_id}.json").write_text(json.dumps(state), encoding="utf-8")
    return worktree


def test_initializing_leftover_is_reported_through_p0_reaper_and_kept(hermetic_reap):
    repo_root, _ = hermetic_reap
    # The canonical reaper reads records from the control plane's batch_state.
    tasks_dir = repo_root / "batch_state" / "tasks"
    worktree = _half_built_dispatch(repo_root, tasks_dir, "impl-8663-r3", status="failed", pid=None)
    head = _run(["git", "rev-parse", "refs/heads/claude/impl-8663-r3"], cwd=repo_root).stdout.strip()

    report = post_task_reap.post_task_reap("impl-8663-r3", tasks_dir=tasks_dir, repo_root=repo_root, apply=True)

    main = report["main_worktree"]
    assert main["action"] == "skipped"
    assert main["reason"].startswith("needs_attention: initializing_leftover; task-id=impl-8663-r3")
    assert main["needs_attention"]["kind"] == "initializing_leftover"
    [finding] = report["needs_attention"]
    assert finding["path"] == str(worktree)
    assert finding["command"].startswith("verify first: ")
    assert finding["evidence"]["head"] == head
    assert report["errors"] == []
    assert worktree.is_dir()
    listing = _run(["git", "worktree", "list", "--porcelain"], cwd=repo_root).stdout
    assert "locked initializing" in listing
    assert _run(["git", "rev-parse", "refs/heads/claude/impl-8663-r3"], cwd=repo_root).stdout.strip() == head


def test_initializing_lock_with_recorded_pid_stays_retained(hermetic_reap):
    repo_root, _ = hermetic_reap
    tasks_dir = repo_root / "batch_state" / "tasks"
    worktree = _half_built_dispatch(repo_root, tasks_dir, "impl-8663-pid", status="failed", pid=424242)

    report = post_task_reap.post_task_reap("impl-8663-pid", tasks_dir=tasks_dir, repo_root=repo_root, apply=True)

    assert report["main_worktree"]["action"] == "retained"
    assert report["main_worktree"]["reason"] == "registered worktree is locked"
    assert worktree.exists()


def test_initializing_lock_without_a_reservation_stays_retained(hermetic_reap):
    repo_root, _ = hermetic_reap
    tasks_dir = repo_root / "batch_state" / "tasks"
    worktree = _half_built_dispatch(repo_root, tasks_dir, "impl-8663-reuse", status="failed", pid=None, reserved=False)

    report = post_task_reap.post_task_reap("impl-8663-reuse", tasks_dir=tasks_dir, repo_root=repo_root, apply=True)

    assert report["main_worktree"]["action"] == "retained"
    assert report["main_worktree"]["reason"] == "registered worktree is locked"
    assert worktree.exists()


@pytest.mark.parametrize("runtime", [False, True])
@pytest.mark.parametrize("reference", ["root", "./", "ignored", ".pytest_cache/cache.txt", "ignored/report.txt"])
def test_post_task_reap_result_named_file_scope(hermetic_reap, runtime, reference):
    repo, tasks = hermetic_reap
    task_id = "named-file-scope"
    worktree = _add_acp_runtime_worktree(repo, task_id) if runtime else _add_dispatch_worktree(repo, "kimi", task_id)
    with (repo / ".git/info/exclude").open("a") as exclude:
        exclude.write("ignored/\n.pytest_cache/\n")
    for name in ["ignored/report.txt", ".pytest_cache/cache.txt"]:
        source = worktree / name
        source.parent.mkdir(parents=True, exist_ok=True)
        source.write_bytes(b"named evidence")
    _write_task_state(
        tasks, task_id, "done", None if runtime else worktree, acp_runtime_paths=[worktree] if runtime else None
    )
    path = tasks / f"{task_id}.json"
    record = json.loads(path.read_text())
    named = str(worktree) if reference == "root" else reference
    record["response"] = f"Result: `{named}`."
    path.write_text(json.dumps(record))
    report = post_task_reap.post_task_reap(task_id, tasks_dir=tasks, repo_root=repo, apply=True)
    row = report["acp_runtimes"][0] if runtime else report["main_worktree"]
    assert row["action"] == "removed", row
    assert not worktree.exists()
    state = json.loads(path.read_text())
    receipt = row["preserved_artifacts"]
    assert state["preserved_artifacts"] == receipt
    location = repo / receipt["location"]
    assert (location / "ignored/report.txt").read_bytes() == b"named evidence"
    assert not (location / ".pytest_cache/cache.txt").exists()
    assert receipt["count"] == 1


def test_acp_artifact_copy_failure_retains_runtime(hermetic_reap, monkeypatch):
    from scripts.orchestration import worktree_artifacts

    repo, tasks = hermetic_reap
    task_id = "acp-copy-failure"
    runtime = _add_acp_runtime_worktree(repo, task_id, locked=True)
    with (repo / ".git/info/exclude").open("a") as exclude:
        exclude.write("batch_state/\n")
    source = runtime / "batch_state/report.txt"
    source.parent.mkdir()
    source.write_bytes(b"must survive failed copy")
    _write_task_state(tasks, task_id, "done", None, acp_runtime_paths=[runtime])

    def fail_copy(*_args):
        raise OSError("injected ACP copy failure")

    monkeypatch.setattr(worktree_artifacts, "_write_verified_bytes", fail_copy)
    report = post_task_reap.post_task_reap(task_id, tasks_dir=tasks, repo_root=repo, apply=True)
    row = report["acp_runtimes"][0]
    assert row["action"] == "retained", row
    assert "injected ACP copy failure" in row["reason"]
    assert source.read_bytes() == b"must survive failed copy"
    assert not (repo / "batch_state/preserved" / task_id / "batch_state/report.txt").exists()


@pytest.mark.parametrize("runtime", [False, True])
@pytest.mark.parametrize("scenario", links.SCENARIOS)
def test_post_task_reap_named_symlink_preserves_or_refuses(hermetic_reap, tmp_path, runtime, scenario):
    repo, tasks = hermetic_reap
    task_id = "named-link"
    worktree = _add_acp_runtime_worktree(repo, task_id) if runtime else _add_dispatch_worktree(repo, "kimi", task_id)
    with (repo / ".git/info/exclude").open("a") as exclude:
        exclude.write("ignored/\n")
    named, preserved, target = links.build_named_link(worktree, repo, tmp_path / "outside", scenario)
    _write_task_state(
        tasks, task_id, "done", None if runtime else worktree, acp_runtime_paths=[worktree] if runtime else None
    )
    path = tasks / f"{task_id}.json"
    record = {**json.loads(path.read_text()), "response": links.worker_response(named)}
    if runtime:
        record["cwd"] = str(worktree)  # Exercise named-artifact checks with a bound runtime record.
    path.write_text(json.dumps(record))
    report = post_task_reap.post_task_reap(task_id, tasks_dir=tasks, repo_root=repo, apply=True)
    row = report["acp_runtimes"][0] if runtime else report["main_worktree"]
    links.restore_access(worktree)
    state = json.loads(path.read_text())
    if preserved is None and target is not None:  # Outbound targets outlive the checkout.
        assert target.read_bytes() == links.PAYLOAD
    location = repo / Path(
        state.get("preserved_artifacts", {}).get("location", repo / "batch_state/preserved" / task_id)
    )
    if scenario in links.REFUSALS:
        assert row["action"] == ("retained" if runtime else "skipped"), row
        assert links.REFUSALS[scenario] in row["reason"], row
        assert links.REFUSALS[scenario] in state["artifact_preservation_error"]
        assert worktree.exists()
        return
    assert row["action"] == "removed", row
    assert not worktree.exists()
    assert "artifact_preservation_error" not in state
    if scenario == "outbound_batch_state":
        entry = next(item for item in state["preserved_artifacts"]["paths"] if item.get("type") == "symlink")
        assert entry["path"] == "ignored/link" and entry["target"] == str(target)
        copied = location / entry["path"]
        assert copied.is_file() and not copied.is_symlink() and links.PAYLOAD not in copied.read_bytes()
        assert state["preserved_artifacts"]["count"] == 1
    elif preserved is None:
        assert not location.exists()
    else:
        link_path, link_target = links.IGNORED_LINK[scenario]
        assert (location / preserved).read_bytes() == links.PAYLOAD
        entries = {item["path"]: item for item in state["preserved_artifacts"]["paths"]}
        assert entries[link_path]["type"] == "symlink" and entries[link_path]["target"] == link_target
        assert state["preserved_artifacts"]["count"] == 2
