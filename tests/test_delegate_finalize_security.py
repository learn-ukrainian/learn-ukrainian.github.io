"""Hostile Git state must never select publication history, refs or transport."""

from __future__ import annotations

import ast
import contextlib
import inspect
import sys
from pathlib import Path

import pytest

import delegate
from scripts.orchestration.safe_git_context import SafeGitContext
from tests.test_delegate import _agy_dispatch_worktree, _git_out, _sanitize_git_env_for_test


@pytest.fixture
def publication(tmp_path, monkeypatch):
    _sanitize_git_env_for_test(monkeypatch)
    worktree = _agy_dispatch_worktree(tmp_path, "codex/finalize")
    origin = tmp_path / "origin.git"
    # Driver-controlled synthetic validation, frozen before worker changes.
    hooks = worktree / ".githooks"
    hooks.mkdir(exist_ok=True)
    marker = tmp_path / "trusted-validation"
    hook = hooks / "pre-push"
    hook.write_text(f'#!/bin/sh\nprintf checked >> "{marker}"\n')
    hook.chmod(0o755)
    (hooks / "pre_push_gate.py").write_text("ADMISSION_MAX_WAIT_S = 1\nADMISSION_WAIT_S = 1\n")
    _git_out(worktree, "add", ".githooks")
    _git_out(worktree, "commit", "-m", "trusted base validation")
    base = _git_out(worktree, "rev-parse", "HEAD").strip()
    _git_out(worktree, "push", "origin", "HEAD:refs/heads/main")

    @contextlib.contextmanager
    def execution(source, **_kwargs):
        assert source == worktree
        with SafeGitContext(
            objects=worktree / ".git/objects", temp_root=tmp_path, origin=str(origin), local_remote=True
        ) as context:
            context.source_git_dir = worktree / ".git"
            context.driver_base = base
            context.interpreter = Path(sys.executable)
            yield context

    monkeypatch.setattr(delegate, "_finalize_execution_context", execution, raising=False)
    monkeypatch.setenv("LU_TASKS_DIR", str(tmp_path / "tasks"))
    return worktree, origin, base, marker


def write_commit(worktree, name="artifact.txt", content="owned\n"):
    (worktree / name).write_text(content)
    _git_out(worktree, "add", name)
    _git_out(worktree, "commit", "-m", "worker change")
    return _git_out(worktree, "rev-parse", "HEAD").strip()


def publish(publication):
    worktree, _origin, base, _marker = publication
    return delegate._auto_finalize_dirty_worktree(
        worktree=worktree,
        task_id="security-finalize",
        agent="codex",
        branch="codex/finalize",
        base_branch="main",
        base_sha=base,
        owned_paths=["artifact.txt"],
    )


def refs(origin):
    return _git_out(origin, "for-each-ref", "--format=%(refname) %(objectname)")


def test_finalize_history_protected_paths_are_source_literals():
    tree = ast.parse(inspect.getsource(delegate._finalize_history))
    protected = next(
        node.value
        for node in ast.walk(tree)
        if isinstance(node, ast.Assign)
        and any(isinstance(target, ast.Name) and target.id == "protected" for target in node.targets)
    )
    assert isinstance(protected, ast.Tuple)
    assert all(isinstance(entry, ast.Constant) and isinstance(entry.value, str) for entry in protected.elts)
    assert ast.literal_eval(protected) == (
        ".githooks/",
        "scripts/pre_commit/",
        "scripts/common/test_slots",
        ".pre-commit-config.yaml",
        ".venv",
    )


@pytest.mark.parametrize("path", ["scripts/common/test_slots.py", "scripts/common/test_slots_extra.py"])
def test_test_slots_history_is_refused_before_validation(publication, path):
    worktree, origin, base, marker = publication
    (worktree / path).parent.mkdir(parents=True, exist_ok=True)
    head = write_commit(worktree, path, "worker changed validation\n")
    result = delegate._auto_finalize_dirty_worktree(
        worktree=worktree,
        task_id="security-finalize",
        agent="codex",
        branch="codex/finalize",
        base_branch="main",
        base_sha=base,
        owned_paths=["scripts/common"],
    )
    assert not result.ok
    assert result.error == "auto_finalize_validation_changed"
    assert "refs/heads/codex/finalize" not in refs(origin)
    assert not marker.exists()
    assert delegate._resolve_sha(worktree) == head


@pytest.mark.parametrize(
    "route",
    [
        "pre-commit",
        "prepare-commit-msg",
        "commit-msg",
        "post-commit",
        "reference-transaction",
        "post-index-change",
        "fsmonitor",
        "trailer-command",
        "trailer-cmd",
        "filter",
        "filter-tracked",
    ],
)
def test_source_preparation_cannot_execute_worker_configuration(publication, tmp_path, route):
    worktree, origin, _base, marker = publication
    if route == "filter-tracked":
        write_commit(worktree)
    artifact = worktree / "artifact.txt"
    artifact.write_bytes(b"owned\r\n")
    executed = tmp_path / "source-preparation-executed"
    program = tmp_path / "source-program"
    program.write_text(
        f'#!/bin/sh\nprintf executed >> "{executed}"\n'
        "git -c core.hooksPath=/dev/null update-ref refs/heads/unvalidated-hook-write HEAD\ncat\n"
    )
    program.chmod(0o755)
    if route.startswith("trailer-"):
        _git_out(worktree, "config", f"trailer.X-Agent.{route.removeprefix('trailer-')}", str(program))
    elif route.startswith("filter"):
        (worktree / ".gitattributes").write_text("artifact.txt filter=worker\n")
        _git_out(worktree, "config", "filter.worker.clean", str(program))
    elif route == "fsmonitor":
        _git_out(worktree, "config", "core.fsmonitor", str(program))
    else:
        hook = worktree / ".githooks" / route
        hook.write_bytes(program.read_bytes())
        hook.chmod(0o755)
        _git_out(worktree, "config", "core.hooksPath", ".githooks")
    result = publish(publication)
    assert not executed.exists(), "worker code ran during finalization preparation"
    assert "refs/heads/unvalidated-hook-write" not in refs(worktree)
    assert artifact.read_bytes() == b"owned\r\n"
    if route.startswith("filter"):
        assert not result.ok
        assert "refs/heads/codex/finalize" not in refs(origin)
        assert not marker.exists()
    # Source hook files themselves remain unowned dirty files. Publication may
    # refuse those inputs; it must never execute them, even before a refusal.


def test_replacement_cannot_hide_original_unowned_history(publication):
    worktree, origin, base, marker = publication
    original = write_commit(worktree, "README.md", "unowned secret history\n")
    reverted = write_commit(worktree, "README.md", "base\n")
    write_commit(worktree)
    tree = _git_out(worktree, "rev-parse", f"{base}^{{tree}}").strip()
    masked = _git_out(worktree, "commit-tree", tree, "-p", base, "-m", "mask original").strip()
    _git_out(worktree, "replace", original, masked)
    mask_revert = _git_out(worktree, "commit-tree", tree, "-p", original, "-m", "mask revert").strip()
    _git_out(worktree, "replace", reverted, mask_revert)
    result = publish(publication)
    assert not result.ok, "replacement objects concealed the original unowned commit"
    assert "refs/heads/codex/finalize" not in refs(origin)
    assert not marker.exists()


def test_follow_tags_cannot_publish_an_unowned_ref(publication):
    worktree, origin, _base, marker = publication
    write_commit(worktree)
    _git_out(worktree, "tag", "-a", "unauthorized", "-m", "unowned ref")
    _git_out(worktree, "config", "push.followTags", "true")
    result = publish(publication)
    assert "refs/tags/unauthorized" not in refs(origin), "implicit tag escaped branch-only publication"
    assert result.ok, result.error
    assert marker.read_text() == "checked"


def test_receivepack_cannot_redirect_a_write(publication, tmp_path):
    worktree, origin, _base, marker = publication
    write_commit(worktree)
    unintended = tmp_path / "unintended.git"
    _git_out(tmp_path, "init", "--bare", str(unintended))
    program = tmp_path / "redirect"
    program.write_text(f'#!/bin/sh\nexec git-receive-pack "{unintended}"\n')
    program.chmod(0o755)
    _git_out(worktree, "config", "remote.origin.receivepack", str(program))
    result = publish(publication)
    assert refs(unintended) == "", "write reached the unauthorized endpoint before verification"
    assert result.ok, result.error
    assert "refs/heads/codex/finalize" in refs(origin)
    assert marker.read_text() == "checked"


@pytest.mark.parametrize(
    "key,value",
    [
        ("url.ALTERNATE.insteadOf", "ORIGIN"),
        ("url.ALTERNATE.pushInsteadOf", "ORIGIN"),
        ("remote.origin.pushurl", "ALTERNATE"),
        ("push.default", "matching"),
        ("remote.origin.push", "refs/heads/*:refs/heads/*"),
        ("core.sshCommand", "PROGRAM"),
        ("credential.helper", "!PROGRAM"),
        ("http.proxy", "http://invalid.invalid:1"),
        ("include.path", "INCLUDE"),
        ("includeIf.gitdir:*/.path", "INCLUDE"),
    ],
)
def test_worker_transport_configuration_never_selects_the_destination(publication, tmp_path, key, value):
    worktree, origin, _base, marker = publication
    head = write_commit(worktree)
    unintended = tmp_path / "unintended.git"
    _git_out(tmp_path, "init", "--bare", str(unintended))
    ran = tmp_path / "hostile-program-ran"
    program = tmp_path / "hostile-program"
    program.write_text(f'#!/bin/sh\ntouch "{ran}"\nexit 1\n')
    program.chmod(0o755)
    include = tmp_path / "hostile-config"
    include.write_text(f'[remote "origin"]\n receivepack = {program}\n pushurl = {unintended}\n')
    key = key.replace("ALTERNATE", str(unintended))
    value = (
        value.replace("ORIGIN", str(origin))
        .replace("ALTERNATE", str(unintended))
        .replace("PROGRAM", str(program))
        .replace("INCLUDE", str(include))
    )
    _git_out(worktree, "config", key, value)
    result = publish(publication)
    assert result.ok, result.error
    assert "refs/heads/codex/finalize " + head in refs(origin)
    assert refs(unintended) == "" and not ran.exists()
    assert marker.read_text() == "checked"


@pytest.mark.parametrize(
    "name,value",
    [
        ("GIT_CONFIG_PARAMETERS", "'push.followTags=true'"),
        ("GIT_CONFIG_COUNT", "1"),
        ("GIT_SSH_COMMAND", "false"),
        ("GIT_EXEC_PATH", "/nonexistent/git-exec-path"),
        ("GIT_REPLACE_REF_BASE", "refs/hostile-replacements/"),
    ],
)
def test_inherited_git_environment_is_not_publication_authority(publication, monkeypatch, name, value):
    worktree, origin, _base, marker = publication
    head = write_commit(worktree)
    _git_out(worktree, "tag", "-a", "unauthorized", "-m", "unowned tag")
    monkeypatch.setenv(name, value)
    if name == "GIT_CONFIG_COUNT":
        monkeypatch.setenv("GIT_CONFIG_KEY_0", "push.followTags")
        monkeypatch.setenv("GIT_CONFIG_VALUE_0", "true")
    result = publish(publication)
    assert result.ok, result.error
    monkeypatch.delenv(name)
    assert "refs/heads/codex/finalize " + head in refs(origin)
    assert "refs/tags/unauthorized" not in refs(origin)
    assert marker.read_text() == "checked"


@pytest.mark.parametrize("attack", ["common-hook", "worktree-hook", "committed-hook"])
def test_hook_substitution_is_refused_before_publication(publication, tmp_path, attack):
    worktree, origin, _base, marker = publication
    head = write_commit(worktree)
    if attack == "committed-hook":
        head = write_commit(worktree, ".githooks/pre-push", "#!/bin/sh\nexit 0\n")
    elif attack == "worktree-hook":
        _git_out(worktree, "config", "extensions.worktreeConfig", "true")
        _git_out(worktree, "config", "--worktree", "core.hooksPath", str(tmp_path))
    else:
        _git_out(worktree, "config", "core.hooksPath", str(tmp_path))
    result = publish(publication)
    assert not result.ok
    assert "refs/heads/codex/finalize" not in refs(origin)
    assert not marker.exists()
    assert delegate._resolve_sha(worktree) == head


def test_forged_tracking_ref_is_not_delivery(publication):
    worktree, origin, _base, _marker = publication
    head = write_commit(worktree)
    _git_out(worktree, "update-ref", "refs/remotes/origin/codex/finalize", head)
    _git_out(worktree, "branch", "--set-upstream-to=origin/codex/finalize")
    assert delegate._count_unpushed_commits(worktree, "codex/finalize") > 0
    assert "refs/heads/codex/finalize" not in refs(origin)


def test_explicit_push_without_upstream_is_delivered(publication):
    worktree, _origin, _base, _marker = publication
    write_commit(worktree)
    _git_out(worktree, "push", "origin", "HEAD:refs/heads/codex/finalize")
    _git_out(worktree, "update-ref", "-d", "refs/remotes/origin/codex/finalize")
    assert delegate._count_unpushed_commits(worktree, "codex/finalize") == 0


def test_forged_base_tracking_ref_cannot_hide_completed_commits(publication):
    worktree, _origin, base, _marker = publication
    head = write_commit(worktree)
    _git_out(worktree, "update-ref", "refs/remotes/origin/main", head)
    assert delegate._count_commits_ahead(worktree, "origin/main", base_sha=base, publication=True) == 1
