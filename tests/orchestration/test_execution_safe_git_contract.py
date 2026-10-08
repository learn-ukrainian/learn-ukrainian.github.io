"""Real Git proves binary inventories and caller-selected output modes (#9914)."""

from __future__ import annotations

import subprocess

import pytest

from scripts.orchestration import execution_safe_git as safe
from scripts.orchestration import reap_worktrees, worktree_artifacts
from tests.orchestration.test_worktree_claims_cli import _git, _primary


@pytest.mark.parametrize("options", [{}, {"text": False}, {"text": True}])
@pytest.mark.parametrize("case", ["success", "config-failure", "attribute-refusal"])
def test_runner_binary_probes_and_caller_output_contract(tmp_path, monkeypatch, options, case):
    repo = _primary(tmp_path)
    if case == "config-failure":
        (repo / ".git/config").write_text("[invalid\n")
    if case == "attribute-refusal":
        (repo / ".gitattributes").write_text("*.txt text\n")
        (repo / "exact.txt").write_bytes(b"exact\r\n")

    real_run = subprocess.run
    calls = []

    def observe(argv, **kwargs):
        result = real_run(argv, **kwargs)
        calls.append((argv, kwargs, result))
        return result

    monkeypatch.setattr(safe.subprocess, "run", observe)
    # add exercises binary config/index and both check-attr inventories even
    # when the caller asks for text. Ordinary status exercises local reads.
    command = ["status", "--porcelain"] if case == "config-failure" else ["add", "-A"]
    profile = "local" if case == "config-failure" else "commit"
    result = safe.run_git(command, cwd=repo, profile=profile, capture_output=True, **options)
    output_type = str if options.get("text") else bytes
    assert isinstance(result.stdout, output_type)
    assert isinstance(result.stderr, output_type)
    assert result.returncode == (0 if case == "success" else 1 if case == "attribute-refusal" else 128)
    if case == "attribute-refusal":
        assert result.stderr == (
            "preserve_transform_attribute" if options.get("text") else b"preserve_transform_attribute"
        )
    # Success ends with the caller's command. A refusal returns an inventory
    # result; every executed command in that case is a binary probe.
    probes = calls[:-1] if case == "success" else calls
    assert probes
    for _argv, kwargs, probe in probes:
        assert kwargs["text"] is False
        assert isinstance(probe.stdout, bytes)
        assert isinstance(probe.stderr, bytes)
    if case == "success":
        assert any("check-attr" in argv for argv, _kwargs, _result in probes)


def test_reaper_text_and_artifact_binary_inventory_callers(tmp_path):
    repo = _primary(tmp_path)
    filename = "with\nnewline.txt"
    (repo / filename).write_bytes(b"exact\r\n")
    _git(repo, "add", filename)

    status = reap_worktrees._run(["git", "status", "--porcelain"], cwd=repo)
    assert status.returncode == 0
    assert isinstance(status.stdout, str)
    assert "with\\nnewline.txt" in status.stdout
    assert filename in worktree_artifacts._git_paths(repo, "--cached")
