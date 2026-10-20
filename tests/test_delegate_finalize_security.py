"""Hostile Git state must never select publication history, refs or transport."""

from __future__ import annotations

import ast
import contextlib
import hashlib
import inspect
import struct
import subprocess
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


def publish(publication, *, owned_paths=None, task_id="security-finalize"):
    worktree, _origin, base, _marker = publication
    return delegate._auto_finalize_dirty_worktree(
        worktree=worktree,
        task_id=task_id,
        agent="codex",
        branch="codex/finalize",
        base_branch="main",
        base_sha=base,
        owned_paths=["artifact.txt"] if owned_paths is None else owned_paths,
    )


def refs(origin):
    return _git_out(origin, "for-each-ref", "--format=%(refname) %(objectname)")


def git_input(worktree, *args, data):
    return subprocess.run(
        ["git", *args],
        cwd=worktree,
        input=data,
        text=True,
        capture_output=True,
        check=True,
        timeout=30,
        env=delegate._sanitized_git_env(),
    ).stdout.strip()


@pytest.mark.parametrize("component", ["..", ".", ".git", ".GIT"])
def test_crafted_intermediate_tree_path_is_refused(publication, component):
    worktree, origin, base, marker = publication
    oid = git_input(worktree, "hash-object", "-w", "--stdin", data="hostile hook\n")
    kind, mode = "blob", "100644"
    for name in reversed(["a", component, ".githooks", "pre-push"]):
        oid = git_input(worktree, "mktree", data=f"{mode} {kind} {oid}\t{name}\n")
        kind, mode = "tree", "40000"
    entries = _git_out(worktree, "ls-tree", base)
    nested = _git_out(worktree, "ls-tree", oid)
    tree = git_input(worktree, "mktree", data=entries + nested)
    hostile = _git_out(worktree, "commit-tree", tree, "-p", base, "-m", "crafted intermediate").strip()
    clean_tree = _git_out(worktree, "rev-parse", f"{base}^{{tree}}").strip()
    head = _git_out(worktree, "commit-tree", clean_tree, "-p", hostile, "-m", "clean final tree").strip()
    _git_out(worktree, "update-ref", "refs/heads/codex/finalize", head)
    history = _git_out(worktree, "log", "--format=", "--name-only", f"{base}..{head}")
    assert f"a/{component}/.githooks/pre-push" in history

    result = publish(publication, owned_paths=["a"])

    assert not result.ok
    assert result.error == "auto_finalize_fsck_failed"
    assert "refs/heads/codex/finalize" not in refs(origin)
    assert not marker.exists()
    assert delegate._resolve_sha(worktree) == head


@pytest.mark.parametrize("prefix", [".GITHOOKS", ".Githooks", "scripts/Pre_commit"])
def test_mixed_case_protected_history_is_refused(publication, prefix):
    worktree, origin, _base, marker = publication
    path = f"{prefix}/worker"
    (worktree / path).parent.mkdir(parents=True, exist_ok=True)
    write_commit(worktree, path)
    _git_out(worktree, "rm", path)
    _git_out(worktree, "commit", "-m", "revert protected change")
    head = delegate._resolve_sha(worktree)

    result = publish(publication, owned_paths=[prefix])

    assert not result.ok
    assert result.error == "auto_finalize_validation_changed"
    assert "refs/heads/codex/finalize" not in refs(origin)
    assert not marker.exists()
    assert delegate._resolve_sha(worktree) == head


@pytest.mark.parametrize("attack", ["gitlink", "filter", "attributes-only"])
def test_reverted_gitlink_or_filter_is_refused(publication, attack):
    worktree, origin, base, marker = publication
    if attack == "gitlink":
        _git_out(worktree, "update-index", "--add", "--cacheinfo", f"160000,{base},artifact.txt")
        _git_out(worktree, "commit", "-m", "intermediate gitlink")
        _git_out(worktree, "update-index", "--force-remove", "artifact.txt")
        code = "rescue_new_gitlink"
    else:
        if attack == "filter":
            write_commit(worktree)
        target = "artifact.txt" if attack == "filter" else "README.md"
        _git_out(worktree, "cat-file", "-e", f"HEAD:{target}")
        write_commit(worktree, ".gitattributes", f"{target} filter=worker\n")
        _git_out(worktree, "rm", ".gitattributes")
        code = "rescue_filtered_path"
    _git_out(worktree, "commit", "-m", "remove intermediate hazard")
    head = delegate._resolve_sha(worktree)

    result = publish(publication, owned_paths=["artifact.txt", ".gitattributes"])

    assert not result.ok
    assert result.error == code
    assert "refs/heads/codex/finalize" not in refs(origin)
    assert not marker.exists()
    assert delegate._resolve_sha(worktree) == head


def test_scoped_preparation_value_error_is_typed_and_retains_local_commit(publication):
    worktree, origin, _base, marker = publication
    head = write_commit(worktree)
    (worktree / "artifact.txt").write_text("dirty owned work\n")

    result = publish(publication, task_id="security\nX-Agent: injected")

    assert not result.ok
    assert result.error == "auto_finalize_preparation_refused"
    assert result.commit_sha == head
    assert delegate._resolve_sha(worktree) == head
    assert (worktree / "artifact.txt").read_text() == "dirty owned work\n"
    assert "refs/heads/codex/finalize" not in refs(origin)
    assert not marker.exists()


def test_unchanged_base_filter_allows_unrelated_attribute_edit(publication):
    worktree, origin, _base, marker = publication
    base = write_commit(worktree, ".gitattributes", "README.md filter=existing\n")
    head = write_commit(worktree, ".gitattributes", "README.md filter=existing\n# unrelated comment\n")

    result = publish((worktree, origin, base, marker), owned_paths=[".gitattributes"])

    assert result.ok, result.error
    assert "refs/heads/codex/finalize " + head in refs(origin)
    assert marker.read_text() == "checked"


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


def test_poisoned_intermediate_commit_graph_cannot_hide_protected_path(publication):
    worktree, origin, base, marker = publication
    (worktree / "a").mkdir()
    harmless = write_commit(worktree, "a/owned")
    harmless_tree = _git_out(worktree, "rev-parse", f"{harmless}^{{tree}}").strip()
    hidden = write_commit(worktree, ".githooks/pre-push", "#!/bin/sh\nexit 0\n")
    _git_out(worktree, "restore", f"--source={base}", "--staged", "--worktree", ".githooks/pre-push")
    _git_out(worktree, "commit", "-m", "revert hidden hook")
    head = delegate._resolve_sha(worktree)
    _git_out(worktree, "commit-graph", "write", "--reachable")
    graph = worktree / ".git/objects/info/commit-graph"
    data = bytearray(graph.read_bytes())
    assert data[:6] == b"CGPH\x01\x01", "probe requires the SHA-1 commit-graph format"
    chunks = {
        bytes(data[offset : offset + 4]): struct.unpack_from(">Q", data, offset + 4)[0]
        for offset in range(8, 8 + data[6] * 12, 12)
    }
    count = struct.unpack_from(">I", data, chunks[b"OIDF"] + 255 * 4)[0]
    oids = [bytes(data[chunks[b"OIDL"] + i * 20 : chunks[b"OIDL"] + (i + 1) * 20]) for i in range(count)]
    record = chunks[b"CDAT"] + oids.index(bytes.fromhex(hidden)) * 36
    data[record : record + 20] = bytes.fromhex(harmless_tree)
    data[-20:] = hashlib.sha1(data[:-20]).digest()
    graph.chmod(0o644)
    graph.write_bytes(data)
    concealed = _git_out(worktree, "-c", "core.commitGraph=true", "log", "--format=", "--name-only", f"{base}..{head}")
    assert ".githooks/pre-push" not in concealed
    assert "a/owned" in concealed
    real = _git_out(worktree, "-c", "core.commitGraph=false", "diff-tree", "-r", "--name-only", harmless, hidden)
    assert ".githooks/pre-push" in real

    result = publish(publication, owned_paths=["a", ".githooks"])

    assert not result.ok
    assert result.error == "auto_finalize_validation_changed"
    assert "refs/heads/codex/finalize" not in refs(origin)
    assert not marker.exists()
    assert delegate._resolve_sha(worktree) == head


def test_publication_uses_only_the_copied_objects(publication, monkeypatch):
    worktree, origin, _base, marker = publication
    head = write_commit(worktree)
    blob = _git_out(worktree, "rev-parse", "HEAD:artifact.txt").strip()
    prepare = SafeGitContext.prepare_validation

    def mutate_source_after_validation(context, **kwargs):
        assert "GIT_ALTERNATE_OBJECT_DIRECTORIES" not in context.env
        assert not (context.git_dir / "objects/info/alternates").exists()
        assert context.checked("config", "core.commitGraph") == "false"
        assert context.checked("config", "core.useReplaceRefs") == "false"
        # Damage a source object only after the isolated copy passed fsck.
        # Both checkout and push must continue using that verified copy.
        source_blob = worktree / ".git/objects" / blob[:2] / blob[2:]
        source_blob.chmod(0o644)
        source_blob.write_bytes(b"corrupt worker object")
        prepare(context, **kwargs)

    monkeypatch.setattr(SafeGitContext, "prepare_validation", mutate_source_after_validation)

    result = publish(publication)

    assert result.ok, result.error
    assert "refs/heads/codex/finalize " + head in refs(origin)
    assert _git_out(origin, "show", f"{head}:artifact.txt") == "owned\n"
    assert marker.read_text() == "checked"


@pytest.mark.parametrize(
    "attack",
    [
        "replace-commit",
        "replace-tree",
        "packed-replace",
        "grafts",
        "graft-config",
        "shallow",
        "alternates",
        "http-alternates",
    ],
)
def test_worker_object_metadata_is_a_typed_refusal(publication, attack):
    worktree, origin, base, marker = publication
    intermediate = write_commit(worktree)
    head = write_commit(worktree, content="final owned\n")
    if attack.startswith("replace") or attack == "packed-replace":
        old, new = intermediate, base
        if attack == "replace-tree":
            old, new = [_git_out(worktree, "rev-parse", f"{oid}^{{tree}}").strip() for oid in (intermediate, base)]
        _git_out(worktree, "replace", old, new)
        if attack == "packed-replace":
            _git_out(worktree, "pack-refs", "--all")
    elif attack == "graft-config":
        grafts = worktree / ".git/custom-grafts"
        grafts.write_text(intermediate + "\n")
        _git_out(worktree, "config", "core.graftFile", str(grafts))
    else:
        name, content = {
            "grafts": ("info/grafts", intermediate + "\n"),
            "shallow": ("shallow", intermediate + "\n"),
            "alternates": ("objects/info/alternates", str(worktree / ".git/objects") + "\n"),
            "http-alternates": ("objects/info/http-alternates", "https://invalid.invalid/objects\n"),
        }[attack]
        (worktree / ".git" / name).write_text(content)

    result = publish(publication)

    assert not result.ok
    assert result.error == "auto_finalize_object_hardening_violation"
    assert "refs/heads/codex/finalize" not in refs(origin)
    assert not marker.exists()
    assert delegate._resolve_sha(worktree) == head


@pytest.mark.parametrize(
    "component", [".git ", ".git.", "GIT~1", ".g\u200cit", "\uff0e\uff47\uff49\uff54", ".git\\hooks"]
)
def test_platform_alias_tree_names_are_refused(publication, component):
    worktree, origin, base, marker = publication
    blob = git_input(worktree, "hash-object", "-w", "--stdin", data="hostile\n")
    nested = git_input(worktree, "mktree", data=f"100644 blob {blob}\tworker\n")
    tree = git_input(worktree, "mktree", data=f"040000 tree {nested}\t{component}\n")
    tree = git_input(worktree, "mktree", data=f"040000 tree {tree}\ta\n" + _git_out(worktree, "ls-tree", base))
    intermediate = _git_out(worktree, "commit-tree", tree, "-p", base, "-m", "platform alias").strip()
    clean = _git_out(worktree, "rev-parse", f"{base}^{{tree}}").strip()
    head = _git_out(worktree, "commit-tree", clean, "-p", intermediate, "-m", "clean tip").strip()
    _git_out(worktree, "update-ref", "refs/heads/codex/finalize", head)

    result = publish(publication, owned_paths=["a"])

    assert not result.ok
    assert result.error == (
        "auto_finalize_invalid_tree_path" if component == "\uff0e\uff47\uff49\uff54" else "auto_finalize_fsck_failed"
    )
    assert "refs/heads/codex/finalize" not in refs(origin)
    assert not marker.exists()
    assert delegate._resolve_sha(worktree) == head


@pytest.mark.parametrize("prefix", ["\u017fcripts/pre_commit", "\uff53cripts/pre_commit"])
def test_unicode_protected_prefix_is_refused(publication, prefix):
    worktree, origin, _base, marker = publication
    (worktree / prefix).mkdir(parents=True)
    head = write_commit(worktree, f"{prefix}/worker")

    result = publish(publication, owned_paths=[prefix])

    assert not result.ok
    assert result.error == "auto_finalize_validation_changed"
    assert "refs/heads/codex/finalize" not in refs(origin)
    assert not marker.exists()
    assert delegate._resolve_sha(worktree) == head


@pytest.mark.parametrize("shape", ["side-branch", "octopus"])
@pytest.mark.parametrize("path", ["unowned.txt", ".githooks/worker"])
def test_non_first_parent_history_is_checked(publication, shape, path):
    worktree, origin, base, marker = publication
    _git_out(worktree, "checkout", "-b", "side", base)
    head = write_commit(worktree, path)
    _git_out(worktree, "rm", path)
    _git_out(worktree, "commit", "-m", "revert side branch hazard")
    side = delegate._resolve_sha(worktree)
    _git_out(worktree, "checkout", "codex/finalize")
    first = write_commit(worktree)
    parents = ["-p", first, "-p", side]
    if shape == "octopus":
        third = _git_out(worktree, "commit-tree", f"{base}^{{tree}}", "-p", base, "-m", "third parent").strip()
        parents += ["-p", third]
    head = _git_out(worktree, "commit-tree", f"{first}^{{tree}}", *parents, "-m", "merge").strip()
    _git_out(worktree, "update-ref", "refs/heads/codex/finalize", head)

    result = publish(publication, owned_paths=["artifact.txt", ".githooks"])

    assert not result.ok
    assert result.error == (
        "auto_finalize_validation_changed" if path.startswith(".githooks") else "auto_finalize_committed_scope_unowned"
    )
    assert "refs/heads/codex/finalize" not in refs(origin)
    assert not marker.exists()
    assert delegate._resolve_sha(worktree) == head
