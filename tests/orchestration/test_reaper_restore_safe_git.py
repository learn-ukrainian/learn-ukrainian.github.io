"""Real-Git restore tripwires and preserved-byte proofs for #9978."""

from __future__ import annotations

import os
import shlex
import subprocess

import pytest

from scripts.orchestration import execution_safe_git as safe
from scripts.orchestration import reaper_lifecycle as lifecycle
from tests.orchestration.test_worktree_claims_cli import _git, _primary


@pytest.fixture
def restore_case(tmp_path):
    repo = _primary(tmp_path)
    payload = b"preserved\r\n$Id$\n\x00\xff"
    (repo / "payload.bin").write_bytes(payload)
    _git(repo, "add", "payload.bin")
    _git(repo, "commit", "-m", "preserved payload")
    sha = _git(repo, "rev-parse", "HEAD")
    ref = "refs/reaper-rescue/exact"
    _git(repo, "update-ref", ref, sha)
    target = repo / ".worktrees/dispatch/codex/restored"
    return repo, target, ref, sha, payload


def _restore(case):
    repo, target, ref, _sha, _payload = case
    return lifecycle.restore_worktree(
        repo, recovery_ref=ref, branch="codex/restored", worktree_path=target,
    )


def _config(repo, scope, key, value):
    _git(repo, "config", "extensions.worktreeConfig", "true")
    _git(repo, "config", *(["--worktree"] if scope == "worktree" else []), key, value)


@pytest.mark.parametrize("scope", ["common", "worktree"])
@pytest.mark.parametrize("program", ["post-checkout", "fsmonitor", "smudge"])
def test_restore_configured_program_markers(restore_case, tmp_path, scope, program):
    repo, target, ref, sha, payload = restore_case
    marker = tmp_path / "executed"
    executable = tmp_path / "tripwire"
    executable.write_text(
        f"#!/bin/sh\nprintf executed >> {shlex.quote(str(marker))}\n"
        + ("cat\nprintf transformed\n" if program == "smudge" else "printf '\\0'\n")
    )
    executable.chmod(0o700)
    if program == "smudge":
        (repo / ".gitattributes").write_text("payload.bin filter=tripwire\n")
        _git(repo, "add", ".gitattributes")
        _git(repo, "commit", "-m", "preserved filter attribute")
        sha = _git(repo, "rev-parse", "HEAD")
        _git(repo, "update-ref", ref, sha)
        _config(repo, scope, "filter.tripwire.smudge", str(executable))
        _config(repo, scope, "filter.tripwire.required", "true")
    elif program == "fsmonitor":
        _config(repo, scope, "core.fsmonitor", str(executable))
    else:
        hooks = tmp_path / "hooks"
        hooks.mkdir()
        hook = hooks / "post-checkout"
        hook.write_bytes(executable.read_bytes())
        hook.chmod(0o700)
        _config(repo, scope, "core.hooksPath", str(hooks))

    result = _restore(restore_case)
    assert not marker.exists(), f"restore executed configured {scope} {program}"
    if program == "smudge":
        assert result == (False, "restore_filter_attribute")
        assert not target.exists()
        assert safe.run_git(["show-ref", "--verify", "refs/heads/codex/restored"], cwd=repo).returncode != 0
    else:
        assert result == (True, None)
        assert (target / "payload.bin").read_bytes() == payload
        assert safe.run_git(["cat-file", "blob", f"{sha}:payload.bin"], cwd=repo, capture_output=True).stdout == payload


@pytest.mark.parametrize("scope", ["common", "worktree"])
@pytest.mark.parametrize("driver", ["clean", "process"])
def test_restore_refuses_other_filter_programs(restore_case, tmp_path, scope, driver):
    repo, target, ref, _sha, _payload = restore_case
    # A macro in the preserved tree must be expanded even when the primary's
    # current attribute files no longer contain it.
    (repo / ".gitattributes").write_text("[attr]restore-filter filter=tripwire\npayload.bin restore-filter\n")
    _git(repo, "add", ".gitattributes")
    _git(repo, "commit", "-m", "filter macro")
    _git(repo, "update-ref", ref, _git(repo, "rev-parse", "HEAD"))
    (repo / ".gitattributes").write_text("")
    marker = tmp_path / "executed"
    _config(repo, scope, f"filter.tripwire.{driver}", f"touch {shlex.quote(str(marker))}")
    assert _restore(restore_case) == (False, "restore_filter_attribute")
    assert not marker.exists()
    assert not target.exists()


@pytest.mark.parametrize("attribute", ["text", "eol=crlf", "crlf", "ident", "working-tree-encoding=UTF-16LE"])
@pytest.mark.parametrize("location", ["commit", "info"])
def test_restore_refuses_byte_transformations(restore_case, attribute, location):
    repo, target, ref, _sha, _payload = restore_case
    if location == "commit":
        (repo / ".gitattributes").write_text(f"payload.bin {attribute}\n")
        _git(repo, "add", ".gitattributes")
        _git(repo, "commit", "-m", "byte transformation")
        _git(repo, "update-ref", ref, _git(repo, "rev-parse", "HEAD"))
    else:
        (repo / ".git/info/attributes").write_text(f"payload.bin {attribute}\n")
    assert _restore(restore_case) == (False, "restore_transform_attribute")
    assert not target.exists()


@pytest.mark.parametrize("existing_branch", [False, True])
def test_restore_exact_bytes_with_implicit_eol_and_sparse_config(restore_case, existing_branch):
    repo, target, _ref, sha, _payload = restore_case
    filename = "directory/with\nnewline.txt"
    (repo / "directory").mkdir()
    (repo / filename).write_bytes(b"preserved\r\n$Id$\n")
    _git(repo, "add", filename)
    _git(repo, "commit", "-m", "unusual path")
    sha = _git(repo, "rev-parse", "HEAD")
    _git(repo, "update-ref", restore_case[2], sha)
    if existing_branch:
        _git(repo, "branch", "codex/restored", sha)
    _config(repo, "worktree", "core.autocrlf", "true")
    _config(repo, "worktree", "core.eol", "crlf")
    _git(repo, "sparse-checkout", "set", "--no-cone", "/.gitignore")
    assert _restore(restore_case) == (True, None)
    for path in [".gitignore", "payload.bin", filename]:
        stored = safe.run_git(["cat-file", "blob", f"{sha}:{path}"], cwd=repo, capture_output=True)
        assert stored.returncode == 0
        assert (target / path).read_bytes() == stored.stdout


@pytest.mark.parametrize("options", [{}, {"text": False}, {"text": True}, {"text": True, "check": True}])
def test_checkout_refusal_output_contract(restore_case, options):
    repo, target, _ref, sha, _payload = restore_case
    (repo / ".git/info/attributes").write_text("payload.bin filter=unused\n")
    command = ["worktree", "add", "-b", "codex/restored", str(target), sha]
    if options.get("check"):
        with pytest.raises(subprocess.CalledProcessError, match="non-zero"):
            safe.run_git(command, cwd=repo, profile="checkout", capture_output=True, **options)
    else:
        result = safe.run_git(command, cwd=repo, profile="checkout", capture_output=True, **options)
        assert result.returncode == 1
        assert result.stderr == ("restore_filter_attribute" if options.get("text") else b"restore_filter_attribute")
    assert not target.exists()


@pytest.mark.parametrize("command", [
    ["worktree", "add", "/unused", "HEAD"],
    ["worktree", "remove", "/unused"],
    ["worktree", "add", "--force", "/unused", "HEAD"],
    ["worktree", "add", "relative", "HEAD"],
    ["worktree", "add", "/unused", "--orphan"],
    ["worktree", "add", "-B", "replacement", "/unused", "HEAD"],
])
def test_checkout_profile_is_explicit_and_restricted(restore_case, command):
    repo = restore_case[0]
    profile = "local" if command == ["worktree", "add", "/unused", "HEAD"] else "checkout"
    with pytest.raises(ValueError, match="unsupported"):
        safe.run_git(command, cwd=repo, profile=profile)


@pytest.mark.parametrize("failure", ["config", "tree", "attributes"])
def test_checkout_probe_failure_never_creates_worktree(restore_case, monkeypatch, failure):
    repo, target, _ref, sha, _payload = restore_case
    if failure == "config":
        (repo / ".git/config").write_text("[invalid\n")
    elif failure == "tree":
        sha = "0" * 40
    else:
        run = subprocess.run

        def fail_attributes(argv, **kwargs):
            if "check-attr" in argv:
                return subprocess.CompletedProcess(argv, 1, b"", b"attribute probe failed")
            return run(argv, **kwargs)

        monkeypatch.setattr(safe.subprocess, "run", fail_attributes)
    result = safe.run_git(
        ["worktree", "add", "-b", "codex/restored", str(target), sha],
        cwd=repo, profile="checkout", capture_output=True, text=True,
    )
    assert result.returncode != 0
    assert not target.exists()


@pytest.mark.parametrize("existing_branch", [False, True])
def test_restore_git_process_denominator(restore_case, monkeypatch, existing_branch):
    repo, _target, _ref, sha, _payload = restore_case
    if existing_branch:
        _git(repo, "branch", "codex/restored", sha)
    run = subprocess.run
    commands = []

    def observe(argv, **kwargs):
        assert "core.fsmonitor=false" in argv
        assert f"core.hooksPath={os.devnull}" in argv
        # Scalar controls precede the non-executing config inventory too.
        offset = 3  # executable, --no-pager, --no-lazy-fetch
        while argv[offset] == "-c":
            offset += 2
        commands.append(argv[offset:])
        return run(argv, **kwargs)

    monkeypatch.setattr(safe.subprocess, "run", observe)
    assert _restore(restore_case) == (True, None)
    assert [command[0] for command in commands] == [
        "config", "rev-parse", "config", "rev-parse",
        "config", "ls-tree", "check-attr", "worktree",
    ]
    assert commands[-1][:2] == ["worktree", "add"]
