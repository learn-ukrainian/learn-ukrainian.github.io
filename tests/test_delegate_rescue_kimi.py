"""#9878: ``delegate.py rescue`` preserves a terminal Kimi task's work past its worktree push block.

Real git: a primary repository with a bare ``origin``, and one linked Kimi
dispatch worktree carrying the boundary ``kimi_boundary.install`` sets up.
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

import delegate
from scripts.agent_runtime import kimi_boundary
from tests.test_delegate import (  # noqa: F401
    _fixture_worktree_lock_dir,
    _keep_delegate_unit_tests_local,
    _sanitize_git_env_for_test,
    tmp_tasks_dir,
)
from tests.test_kimi_coding_only_admission import _FAKE_TOKEN, HOSTILE_GIT_ERRORS, assert_no_host_details

pytestmark = pytest.mark.usefixtures("tmp_tasks_dir")
_DRIVER_CONTEXT = delegate._rescue_execution_context

TASK_ID = "kimi-rescue"
BRANCH = f"kimi/{TASK_ID}"
RESCUE_REF = f"rescue/kimi/{delegate._x_agent_task_id('kimi', TASK_ID)}"
OWNED = "site/src/components/"
LABEL = "site/src/components/Label.tsx"


def _git(repo: Path, *args: str) -> str:
    env = {"PATH": os.defpath, "HOME": str(repo), "GIT_CONFIG_NOSYSTEM": "1", "GIT_CONFIG_GLOBAL": os.devnull}
    return subprocess.run(["git", *args], cwd=repo, env=env, check=True, capture_output=True, text=True, timeout=60).stdout


def _git_proc(repo: Path, *args: str) -> subprocess.CompletedProcess[str]:
    env = {"PATH": os.defpath, "HOME": str(repo), "GIT_CONFIG_NOSYSTEM": "1", "GIT_CONFIG_GLOBAL": os.devnull}
    return subprocess.run(["git", *args], cwd=repo, env=env, check=False, capture_output=True, text=True, timeout=60)


def _remote_heads(origin: Path) -> dict[str, str]:
    lines = _git(origin, "for-each-ref", "--format=%(refname:short) %(objectname)", "refs/heads").splitlines()
    return dict(line.split(" ", 1) for line in lines)


@pytest.fixture
def kimi_rescue(tmp_path, monkeypatch):
    """A failed Kimi task whose worktree holds the boundary; ``write(text, commit=...)`` leaves its work."""
    from scripts.orchestration import reap_worktrees

    _sanitize_git_env_for_test(monkeypatch)
    # These are real-Git mechanism tests, independent of a worker harness's
    # PATH shim (which rejects --no-verify for its own scanned pushes).
    monkeypatch.setenv("PATH", os.defpath)
    primary = tmp_path / "primary"
    origin = tmp_path / "origin.git"
    _git(tmp_path, "init", "--bare", "--initial-branch=main", str(origin))
    _git(tmp_path, "init", "--initial-branch=main", str(primary))
    for key, value in (("user.email", "test@example.com"), ("user.name", "test"), ("commit.gpgsign", "false")):
        _git(primary, "config", key, value)
    (primary / "README.md").write_text("base\n", encoding="utf-8")
    _git(primary, "add", "-A")
    _git(primary, "commit", "-m", "base")
    _git(primary, "remote", "add", "origin", str(origin))
    _git(primary, "push", "origin", "HEAD:refs/heads/main")
    worktree = primary / ".worktrees" / "dispatch" / "kimi" / TASK_ID
    worktree.parent.mkdir(parents=True)
    _git(primary, "worktree", "add", "-b", BRANCH, str(worktree), "HEAD")
    monkeypatch.setattr(delegate, "_REPO_ROOT", primary.resolve())
    from scripts.orchestration.safe_git_context import SafeGitContext
    monkeypatch.setattr(delegate, "_rescue_canonical_push_url", lambda: str(origin))
    monkeypatch.setattr(delegate, "_rescue_execution_context", lambda repo: SafeGitContext(
        objects=repo.git_dir / "objects", temp_root=tmp_path,
        origin=delegate._rescue_canonical_push_url(), local_remote=True,
    ))
    monkeypatch.setattr(reap_worktrees, "_active_task_ids", lambda: set())
    monkeypatch.setattr(reap_worktrees, "_live_cwd_paths", lambda _root: set())
    kimi_boundary.install(worktree, agent="kimi", base_ref="origin/main", owned_paths=[OWNED])
    state_path = delegate._state_path(TASK_ID)
    delegate._write_state_atomic(
        state_path,
        {
            "task_id": TASK_ID,
            "agent": "kimi",
            "status": "failed",
            "finished_at": "2020-01-01T00:00:00Z",
            "worktree_path": str(worktree.resolve()),
            "worktree_branch": BRANCH,
            "worktree_base": "main",
            "worktree_reused": False,
            "owned_paths": [OWNED],
        },
    )

    def write(text: str, *, commit: bool = False) -> None:
        label = worktree / LABEL
        label.parent.mkdir(parents=True, exist_ok=True)
        label.write_text(text, encoding="utf-8")
        if commit:
            _git(worktree, "add", "-A")
            _git(worktree, "commit", "--no-verify", "-m", "worker commit")

    return worktree.resolve(), origin, state_path, write


def _assert_push_block_intact(worktree: Path) -> None:
    assert kimi_boundary.is_installed(worktree)
    assert kimi_boundary.PUSH_BLOCK_URL in _git(worktree, "config", "--get-all", "remote.origin.pushurl").splitlines()
    proc = _git_proc(worktree, "push", "origin", "HEAD:refs/heads/worker-push")
    assert proc.returncode != 0 and "kimi-push-disabled" in proc.stderr


@pytest.mark.parametrize("committed", [False, True])
def test_rescue_pushes_clean_kimi_work_and_leaves_the_push_block_in_place(kimi_rescue, committed):
    worktree, origin, state_path, write = kimi_rescue
    write("export const label = 'Lesson';\n", commit=committed)

    result = delegate._rescue_task(state_path, apply=True)

    assert result["action"] == "rescued", result
    assert _remote_heads(origin)[RESCUE_REF] == result["head"]
    assert _git(origin, "show", f"{RESCUE_REF}:{LABEL}") == "export const label = 'Lesson';\n"
    state = delegate._read_state(state_path)
    assert (state["rescue_ref"], state["rescue_status"]) == (RESCUE_REF, "rescued")
    _assert_push_block_intact(worktree)
    assert "worker-push" not in _remote_heads(origin)


def test_rescue_dry_run_reports_clean_kimi_work_without_pushing(kimi_rescue):
    _worktree, origin, state_path, write = kimi_rescue
    write("export const label = 'Lesson';\n")

    result = delegate._rescue_task(state_path, apply=False)

    assert (result["action"], result["rescue_ref"]) == ("candidate", RESCUE_REF)
    assert RESCUE_REF not in _remote_heads(origin)


@pytest.mark.parametrize("committed", [False, True])
@pytest.mark.parametrize("apply", [False, True])
def test_rescue_refuses_kimi_work_that_fails_the_content_check(kimi_rescue, committed, apply):
    worktree, origin, state_path, write = kimi_rescue
    write("export const label = 'Урок';\n", commit=committed)
    head = _git(worktree, "rev-parse", "HEAD")
    status = _git(worktree, "status", "--porcelain")

    result = delegate._rescue_task(state_path, apply=apply)

    assert result["action"] == "error"
    assert result["failure_code"] == "kimi_content_refused"
    # #9878: the row names the typed cause; the refusal text, with its path, stays in the local .diag.
    assert result["reason"] == "kimi_content_refused"
    assert LABEL not in json.dumps(result)
    kept = delegate._diagnostic_path(TASK_ID).read_text(encoding="utf-8")
    assert "KIMI CODING-ONLY" in kept and LABEL in kept
    assert RESCUE_REF not in _remote_heads(origin)
    assert _git(worktree, "rev-parse", "HEAD") == head
    assert _git(worktree, "status", "--porcelain") == status
    assert delegate._read_state(state_path).get("rescue_ref") is None
    _assert_push_block_intact(worktree)


def test_rescue_checks_a_kimi_record_even_without_its_boundary(kimi_rescue):
    worktree, origin, state_path, write = kimi_rescue
    kimi_boundary.remove(worktree)
    write("export const label = 'Урок';\n")

    result = delegate._rescue_task(state_path, apply=True)

    assert (result["action"], result["failure_code"]) == ("error", "kimi_content_refused")
    assert RESCUE_REF not in _remote_heads(origin)


def test_rescue_ignores_a_shared_push_url_the_worker_changed(kimi_rescue, tmp_path):
    worktree, origin, state_path, write = kimi_rescue
    decoy = tmp_path / "decoy.git"
    _git(tmp_path, "init", "--bare", str(decoy))
    _git(worktree, "config", "--local", "remote.origin.pushurl", str(decoy))
    write("export const label = 'Lesson';\n", commit=True)

    result = delegate._rescue_task(state_path, apply=True)

    assert result["action"] == "rescued", result
    assert _remote_heads(origin)[RESCUE_REF] == result["head"]
    assert _remote_heads(decoy) == {}


def test_rescue_ignores_a_push_url_the_kimi_worktree_set_for_itself(kimi_rescue, tmp_path):
    """The canonical URL comes from the main repository, never the worker's worktree-scoped config."""
    worktree, origin, state_path, write = kimi_rescue
    decoy = tmp_path / "decoy.git"
    _git(tmp_path, "init", "--bare", str(decoy))
    _git(worktree, "config", "--worktree", "remote.origin.url", str(decoy))
    write("export const label = 'Lesson';\n", commit=True)

    result = delegate._rescue_task(state_path, apply=True)

    assert result["action"] == "rescued", result
    assert _remote_heads(origin)[RESCUE_REF] == result["head"]
    assert _remote_heads(decoy) == {}


# --- #9878 review probes: rescue runs nothing the worker's worktree configured ---------------


def _seat(kimi_rescue, seat: str) -> str:
    """Make the fixture's task a ``seat`` task; the rescue ref it gets."""
    worktree, _origin, state_path, _write = kimi_rescue
    if seat != "kimi":
        kimi_boundary.remove(worktree)
        state = delegate._read_state(state_path)
        delegate._write_state_atomic(state_path, {**state, "agent": seat})
    return f"rescue/{seat}/{delegate._x_agent_task_id(seat, TASK_ID)}"


def _worktree_hooks(worktree: Path, tmp_path: Path) -> Path:
    """A worktree-scoped ``core.hooksPath``: every hook leaves a marker; pre-commit also swaps in Cyrillic."""
    hooks = tmp_path / "worker-hooks"
    hooks.mkdir()
    marker = tmp_path / "hook-ran"
    swap = f"printf \"export const label = 'Урок';\\n\" > {LABEL}\ngit add {LABEL}\n"
    for name in ("pre-commit", "commit-msg", "post-commit", "pre-push", "post-checkout", "reference-transaction"):
        hook = hooks / name
        hook.write_text(f"#!/bin/sh\necho {name} >> '{marker}'\n{swap if name == 'pre-commit' else ''}exit 0\n")
        hook.chmod(0o755)
    _git(worktree, "config", "--worktree", "core.hooksPath", str(hooks))
    return marker


def _worker_snapshot(worktree: Path) -> tuple[bytes, str, str, bytes]:
    """The worker's index, HEAD, branch and changed file, read without letting git rewrite the index."""
    index = Path(_git(worktree, "rev-parse", "--path-format=absolute", "--git-path", "index").strip())
    return (
        index.read_bytes(),
        _git(worktree, "rev-parse", "HEAD"),
        _git(worktree, "symbolic-ref", "HEAD"),
        (worktree / LABEL).read_bytes(),
    )


def _registered_worktrees(worktree: Path) -> list[str]:
    return [
        line for line in _git(worktree, "worktree", "list", "--porcelain").splitlines() if line.startswith("worktree ")
    ]


@pytest.mark.parametrize("seat", ["kimi", "cursor"])
@pytest.mark.parametrize("committed", [False, True])
def test_rescue_runs_no_hook_of_the_worker_worktree(kimi_rescue, tmp_path, committed, seat):
    worktree, origin, state_path, write = kimi_rescue
    rescue_ref = _seat(kimi_rescue, seat)
    write("export const label = 'Lesson';\n", commit=committed)
    marker = _worktree_hooks(worktree, tmp_path)
    before, registered = _worker_snapshot(worktree), _registered_worktrees(worktree)

    result = delegate._rescue_task(state_path, apply=True)

    assert result["action"] == "rescued", result
    assert not marker.exists(), marker.read_text()
    assert _remote_heads(origin)[rescue_ref] == result["head"]
    assert _git(origin, "show", f"{rescue_ref}:{LABEL}") == "export const label = 'Lesson';\n"
    assert _worker_snapshot(worktree) == before  # rescue never writes the worker's worktree
    assert _registered_worktrees(worktree) == registered  # the publish worktree is gone
    if seat == "kimi":
        _assert_push_block_intact(worktree)


@pytest.mark.parametrize("condition", ["claim", "preservation", "dirty"])
def test_rescue_retains_source_without_calling_worktree_removal(kimi_rescue, monkeypatch, condition):
    from scripts.fleet import ignored_task_output
    from scripts.orchestration import worktree_claims

    worktree, origin, state_path, write = kimi_rescue
    write("export const label = 'Lesson';\n")
    if condition == "claim":
        claim = {"task_id": "attached-worker", "status": "running", "worktree_path": str(worktree)}
        delegate._write_state_atomic(delegate._state_path("attached-worker"), claim)
    elif condition == "preservation":
        exclude = delegate._rescue_repo(worktree).git_dir / "info/exclude"
        exclude.write_text(exclude.read_text() + "\nbatch_state/\n")
        output = worktree / "batch_state/output.bin"
        output.parent.mkdir()
        output.write_bytes(b"preserve me\x00\xff")
    else:
        (worktree / "untracked.txt").write_text("preserve me\n")
    before, registered = _worker_snapshot(worktree), _registered_worktrees(worktree)

    def forbidden(*_args, **_kwargs):
        pytest.fail("rescue must retain its source without attempting preservation or worktree removal")

    monkeypatch.setattr(worktree_claims, "remove_unclaimed_worktree", forbidden)
    monkeypatch.setattr(worktree_claims, "git_worktree_remove", forbidden)
    monkeypatch.setattr(ignored_task_output, "preserve_worktree_artifacts", forbidden)

    result = delegate._rescue_task(state_path, apply=True)

    assert result["action"] == "rescued", result
    assert _remote_heads(origin)[RESCUE_REF] == result["head"]
    assert worktree.is_dir() and (worktree / ".git").is_file()
    assert _worker_snapshot(worktree) == before
    assert _registered_worktrees(worktree) == registered
    if condition == "claim":
        assert delegate._read_state(delegate._state_path("attached-worker")) == claim
    elif condition == "preservation":
        assert output.read_bytes() == b"preserve me\x00\xff"
        assert _git_proc(origin, "cat-file", "-e", f"{result['head']}:batch_state/output.bin").returncode != 0
    else:
        assert (worktree / "untracked.txt").read_text() == "preserve me\n"
        assert _git(origin, "show", f"{result['head']}:untracked.txt") == "preserve me\n"
    _assert_push_block_intact(worktree)


@pytest.mark.parametrize("committed", [False, True])
def test_a_worktree_url_rewrite_receives_nothing(kimi_rescue, tmp_path, committed):
    worktree, origin, state_path, write = kimi_rescue
    decoy = tmp_path / "decoy.git"
    _git(tmp_path, "init", "--bare", str(decoy))
    _git(worktree, "config", "--worktree", f"url.{decoy}.insteadOf", str(origin))
    write("export const label = 'Lesson';\n", commit=committed)

    result = delegate._rescue_task(state_path, apply=True)

    assert result["action"] == "rescued", result
    assert _remote_heads(origin)[RESCUE_REF] == result["head"]
    assert _remote_heads(decoy) == {}


def test_a_url_rewrite_cannot_fake_the_remote_verification(kimi_rescue, tmp_path):
    """Shared rewrites affect neither the bare-context push nor its remote proof."""
    _worktree, origin, state_path, write = kimi_rescue
    decoy = tmp_path / "decoy.git"
    _git(tmp_path, "init", "--bare", str(decoy))
    _git(tmp_path / "primary", "config", f"url.{decoy}.insteadOf", str(origin))
    write("export const label = 'Lesson';\n", commit=True)

    result = delegate._rescue_task(state_path, apply=True)

    assert result["action"] == "rescued", result
    assert _remote_heads(origin)[RESCUE_REF] == result["head"]
    assert _remote_heads(decoy) == {}


def test_a_repeated_rescue_of_the_same_uncommitted_work_is_already_rescued(kimi_rescue):
    _worktree, origin, state_path, write = kimi_rescue
    write("export const label = 'Lesson';\n")
    first = delegate._rescue_task(state_path, apply=True)

    again = delegate._rescue_task(state_path, apply=True)

    assert first["action"] == "rescued", first
    assert again == {"task_id": TASK_ID, "action": "skipped", "reason": "already rescued at HEAD"}
    assert _remote_heads(origin)[RESCUE_REF] == first["head"]


# --- #9878: a rescue row carries only the typed cause; git's error stays in the local .diag ----------

# The kinds git reports for a remote it never reached.
_UNREACHABLE = {"dns_hostname", "ssh_dns_hostname", "ipv6_interface"}


def _fail_rescue_git(monkeypatch, subcommand: str, stderr: str) -> None:
    """Every rescue ``git <subcommand>`` exits 128 with ``stderr``; the argv carries the host paths git saw."""
    real_git = delegate._rescue_git

    def failing(cwd, *args, **kwargs):
        if args and args[0] == subcommand:
            argv = ["git", *kwargs.get("git_options", ()), *args]
            return subprocess.CompletedProcess(argv, 128, "", stderr)
        return real_git(cwd, *args, **kwargs)

    monkeypatch.setattr(delegate, "_rescue_git", failing)


def _assert_kept_locally(task_id: str, stderr: str, code: str) -> None:
    lines = delegate._diagnostic_path(task_id).read_text(encoding="utf-8").splitlines()
    (entry,) = (json.loads(line) for line in lines)
    assert (entry["source"], entry["code"]) == ("rescue", code)
    if _FAKE_TOKEN in stderr:
        assert _FAKE_TOKEN not in entry["diagnostic"] and "Authentication failed for" in entry["diagnostic"]
    else:
        assert stderr.splitlines()[0] in entry["diagnostic"]


@pytest.mark.parametrize("kind", sorted(HOSTILE_GIT_ERRORS))
def test_a_rescue_push_error_row_carries_only_its_typed_cause(kimi_rescue, monkeypatch, capsys, kind):
    worktree, origin, _state_path, write = kimi_rescue
    write("export const label = 'Lesson';\n", commit=True)
    registered = _registered_worktrees(worktree)
    stderr = HOSTILE_GIT_ERRORS[kind]
    _fail_rescue_git(monkeypatch, "push", stderr)
    code = "remote_unreachable" if kind in _UNREACHABLE else "rescue_push_failed"

    assert delegate.cmd_rescue(argparse.Namespace(task_id=TASK_ID, all_stale=False, older_than=None, apply=True)) == 1
    summary = capsys.readouterr().out
    (result,) = json.loads(summary)["tasks"]

    assert (result["action"], result["failure_code"]) == ("error", code)
    assert result["reason"] == f"{code}, git push, exit 128"
    assert result["diagnostic"].endswith(f"{TASK_ID}.diag")
    assert_no_host_details(summary, worktree, origin)
    assert "fatal:" not in summary and "Could not" not in summary
    _assert_kept_locally(TASK_ID, stderr, code)
    assert RESCUE_REF not in _remote_heads(origin)
    assert _registered_worktrees(worktree) == registered


@pytest.mark.parametrize("apply", [False, True])
@pytest.mark.parametrize("kind", sorted(HOSTILE_GIT_ERRORS))
def test_a_rescue_remote_query_error_row_carries_only_its_typed_cause(kimi_rescue, monkeypatch, apply, kind):
    worktree, origin, state_path, write = kimi_rescue
    write("export const label = 'Lesson';\n", commit=True)
    stderr = HOSTILE_GIT_ERRORS[kind]
    _fail_rescue_git(monkeypatch, "ls-remote", stderr)
    code = "remote_unreachable" if kind in _UNREACHABLE else "rescue_remote_unverified"

    result = delegate._rescue_task(state_path, apply=apply)

    assert (result["action"], result["failure_code"]) == ("error", code)
    assert result["reason"] == f"{code}, git ls-remote, exit 128"
    assert_no_host_details(json.dumps(result), worktree, origin)
    _assert_kept_locally(TASK_ID, stderr, code)


@pytest.mark.parametrize("kind", sorted(HOSTILE_GIT_ERRORS))
def test_a_rescue_kimi_check_that_cannot_read_the_changes_refuses_with_its_typed_cause(kimi_rescue, monkeypatch, kind):
    worktree, origin, state_path, write = kimi_rescue
    write("export const label = 'Lesson';\n", commit=True)
    stderr = HOSTILE_GIT_ERRORS[kind]
    _fail_rescue_git(monkeypatch, "diff-tree", stderr)

    result = delegate._rescue_task(state_path, apply=True)

    assert (result["action"], result["failure_code"]) == ("error", "kimi_content_refused")
    assert result["reason"] == "kimi_content_refused; diff_command_failed, git diff-tree, exit 128"
    assert_no_host_details(json.dumps(result, ensure_ascii=False), worktree, origin)
    _assert_kept_locally(TASK_ID, stderr, "diff_command_failed")
    assert RESCUE_REF not in _remote_heads(origin)


def test_an_unexpected_rescue_exception_is_typed_by_its_class(kimi_rescue, monkeypatch):
    worktree, origin, state_path, write = kimi_rescue
    write("export const label = 'Lesson';\n", commit=True)

    def unreachable_mount(*_args, **_kwargs):
        raise OSError(f"cannot stat {HOSTILE_GIT_ERRORS['home_relative_mount']}")

    monkeypatch.setattr(delegate, "_rescue_canonical_push_url", unreachable_mount)
    result = delegate._rescue_task(state_path, apply=True)

    assert (result["action"], result["failure_code"]) == ("error", "rescue_step_failed")
    assert result["reason"] == "rescue_step_failed, OSError"
    assert_no_host_details(json.dumps(result), worktree, origin)
    _assert_kept_locally(TASK_ID, "cannot stat", "rescue_step_failed")


@pytest.mark.parametrize("scope", ["--local", "--worktree"])
@pytest.mark.parametrize("committed", [False, True])
def test_rescue_full_flow_runs_no_worker_configured_program(kimi_rescue, tmp_path, monkeypatch, scope, committed):
    from tests.orchestration.test_safe_git_context import plant_programs

    worktree, origin, state_path, write = kimi_rescue
    write("export const label = 'Lesson';\n", commit=committed)
    marker = plant_programs(worktree, tmp_path, scope=scope, monkeypatch=monkeypatch)
    checked = []
    real_check = delegate._kimi_tree_refusal
    real_git = delegate._rescue_git
    configs = []

    def check(context, base, agent, *, tree):
        checked.append(tree)
        config = context.run("config", "--show-origin", "--list").stdout
        configs.append(config)
        assert {line.split("\t")[0] for line in config.splitlines()} == {f"file:{context.git_dir}/config"}
        return real_check(context, base, agent, tree=tree)

    def push(context, *args, **kwargs):
        if args[0] == "push":
            assert "--no-verify" in args
            sha = args[-1].split(":")[0]
            assert context.checked("rev-parse", f"{sha}^{{tree}}") == checked[-1]
        return real_git(context, *args, **kwargs)

    monkeypatch.setattr(delegate, "_kimi_tree_refusal", check)
    monkeypatch.setattr(delegate, "_rescue_git", push)
    result = delegate._rescue_task(state_path, apply=True)

    assert result["action"] == "rescued", result
    assert checked and configs
    assert not marker.exists()
    assert _remote_heads(origin)[RESCUE_REF] == result["head"]
    assert _git(origin, "rev-parse", f"{result['head']}^{{tree}}").strip() == checked[-1]


@pytest.mark.parametrize("kind", ["filter", "embedded", "gitlink", "unreadable", "changing"])
def test_rescue_typed_snapshot_refusals_publish_nothing(kimi_rescue, tmp_path, monkeypatch, kind):
    from scripts.orchestration.safe_git_context import SafeGitContext

    worktree, origin, state_path, write = kimi_rescue
    write("export const label = 'Lesson';\n")
    expected = {
        "filter": "rescue_filtered_path", "embedded": "rescue_embedded_repository",
        "gitlink": "rescue_new_gitlink", "unreadable": "rescue_input_unreadable",
        "changing": "rescue_input_changed",
    }[kind]
    if kind == "filter":
        (worktree / ".gitattributes").write_text(f"{LABEL} filter=lfs\n")
    elif kind == "embedded":
        nested = worktree / OWNED / "nested"
        nested.mkdir()
        _git(nested, "init")
        (nested / "content").write_text("retained\n")
    elif kind == "gitlink":
        head = _git(worktree, "rev-parse", "HEAD").strip()
        _git(worktree, "update-index", "--add", "--cacheinfo", f"160000,{head},{OWNED}nested")
        _git(worktree, "commit", "--no-verify", "-m", "gitlink")
        (worktree / OWNED / "nested").mkdir()
    elif kind == "unreadable":
        (worktree / LABEL).chmod(0)
    else:
        real = SafeGitContext.run
        def change_after_add(context, *args, **kwargs):
            result = real(context, *args, **kwargs)
            if args[:2] == ("add", "-A"):
                (worktree / LABEL).write_text("changed during capture\n")
            return result
        monkeypatch.setattr(SafeGitContext, "run", change_after_add)
    pushes = []
    real_git = delegate._rescue_git
    def observe(context, *args, **kwargs):
        if args[0] == "push":
            pushes.append(args)
        return real_git(context, *args, **kwargs)
    monkeypatch.setattr(delegate, "_rescue_git", observe)

    result = delegate._rescue_task(state_path, apply=True)

    assert (result["action"], result["failure_code"]) == ("error", expected), result
    assert not pushes and RESCUE_REF not in _remote_heads(origin)
    assert worktree.exists() and (worktree / LABEL).exists()


@pytest.mark.parametrize("mutation", ["file", "head"])
def test_rescue_refuses_inputs_changed_after_content_check(kimi_rescue, monkeypatch, mutation):
    worktree, origin, state_path, write = kimi_rescue
    write("export const label = 'Lesson';\n")
    original = delegate._kimi_tree_refusal
    def changing(context, base, agent, *, tree):
        verdict = original(context, base, agent, tree=tree)
        if mutation == "file":
            write("changed after checking\n")
        else:
            _git(worktree, "checkout", "--detach")
        return verdict
    monkeypatch.setattr(delegate, "_kimi_tree_refusal", changing)
    result = delegate._rescue_task(state_path, apply=True)
    assert result["failure_code"] == "rescue_input_changed", result
    assert RESCUE_REF not in _remote_heads(origin)


@pytest.mark.parametrize("token", [None, "synthetic-driver-identity"])
def test_driver_context_pins_destination_and_supplies_identity_explicitly(kimi_rescue, monkeypatch, token):
    from scripts.agent_runtime import agent_github_identity
    from scripts.orchestration.safe_git_context import CANONICAL_ORIGIN

    worktree, _origin, _state_path, _write = kimi_rescue
    supplied = []
    def identity(**kwargs):
        supplied.append(kwargs)
        return agent_github_identity.GitHubIdentity(token, "test")
    monkeypatch.setattr(agent_github_identity, "resolve_agent_github_identity", identity)
    monkeypatch.setattr(delegate, "_rescue_canonical_push_url", lambda: CANONICAL_ORIGIN)
    repo = delegate._rescue_repo(worktree)
    if token is None:
        with pytest.raises(delegate._RescueFailure) as refused:
            _DRIVER_CONTEXT(repo)
        assert refused.value.cause.code == "rescue_identity_unavailable"
    else:
        with _DRIVER_CONTEXT(repo) as context:
            assert context.checked("config", "remote.origin.url") == CANONICAL_ORIGIN
            assert context.checked("config", "http." + CANONICAL_ORIGIN + ".extraHeader").startswith("Authorization: Basic ")
    assert supplied[0]["repository"] == "learn-ukrainian/learn-ukrainian.github.io"


def test_kimi_checks_exact_blob_bytes_including_crlf(kimi_rescue, monkeypatch):
    from scripts.agent_runtime import kimi_admission

    worktree, origin, state_path, write = kimi_rescue
    write("export const label = 'Lesson';\n")
    data = b"export const label = 'Lesson';\r\n"
    (worktree / LABEL).write_bytes(data)
    seen = []
    original = kimi_admission.refuse_kimi_changes
    def inspect(agent, changes, **kwargs):
        changes = list(changes)
        seen.extend(changes)
        return original(agent, changes, **kwargs)
    monkeypatch.setattr(kimi_admission, "refuse_kimi_changes", inspect)
    result = delegate._rescue_task(state_path, apply=True)
    assert result["action"] == "rescued", result
    assert next(change.after for change in seen if change.path == LABEL) == data
    from scripts.orchestration.safe_git_context import SafeGitContext
    with SafeGitContext(objects=origin / "objects", origin=str(origin), local_remote=True, temp_root=worktree.parent) as context:
        assert context.run("cat-file", "blob", f"{result['head']}:{LABEL}", binary=True).stdout == data


def test_rescue_preserves_symlink_to_a_large_target_without_reading_the_target(kimi_rescue, tmp_path):
    worktree, origin, state_path, write = kimi_rescue
    write("export const label = 'Lesson';\n")
    outside = tmp_path / "large-target"
    outside.write_bytes(b"x" * (delegate._RESCUE_MAX_FILE_BYTES + 1))
    link = worktree / OWNED / "link"
    target = os.path.relpath(outside, link.parent)
    link.symlink_to(target)
    result = delegate._rescue_task(state_path, apply=True)
    assert result["action"] == "rescued", result
    assert _git(origin, "show", f"{result['head']}:{OWNED}link").strip() == target
    assert "120000" in _git(origin, "ls-tree", result["head"], f"{OWNED}link")


@pytest.mark.parametrize("apply", [False, True])
def test_rescue_skips_a_worktree_that_was_already_removed(kimi_rescue, apply):
    """A reaped worktree has nothing to preserve: skipped, never a FileNotFoundError row."""
    worktree, _origin, state_path, _write = kimi_rescue
    _git(worktree.parents[3], "worktree", "remove", "--force", str(worktree))
    assert not worktree.exists()

    result = delegate._rescue_task(state_path, apply=apply)

    assert result["action"] == "skipped"
    assert result["reason"] == "worktree already removed"


def test_rescue_skips_a_directory_without_git_metadata(kimi_rescue, tmp_path):
    worktree, _origin, state_path, _write = kimi_rescue
    _git(worktree.parents[3], "worktree", "remove", "--force", str(worktree))
    worktree.mkdir(parents=True)
    (worktree / "leftover.txt").write_text("residue\n", encoding="utf-8")

    result = delegate._rescue_task(state_path, apply=True)

    assert result["action"] == "skipped"
    assert result["reason"] == "not a registered dispatch worktree"


def test_all_stale_rescue_exits_zero_when_only_removed_worktrees_remain(kimi_rescue, capsys):
    worktree, _origin, _state_path, _write = kimi_rescue
    _git(worktree.parents[3], "worktree", "remove", "--force", str(worktree))

    status = delegate.cmd_rescue(argparse.Namespace(all_stale=True, older_than="6h", task_id=None, apply=False))

    payload = json.loads(capsys.readouterr().out)
    assert status == 0
    assert payload["summary"]["error"] == 0
    assert payload["summary"]["skipped"] >= 1
