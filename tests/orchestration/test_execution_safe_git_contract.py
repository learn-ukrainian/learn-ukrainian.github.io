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


@pytest.mark.parametrize("failure", [None, "add", "commit", "index-moved", "ref-moved"])
def test_scoped_commit_keeps_unowned_index_and_admits_only_closed_operations(tmp_path, monkeypatch, failure):
    from scripts.lib.git_identity import git_identity_env
    from scripts.orchestration.safe_git_context import SafeGitContext, SnapshotRefusal

    repo = _primary(tmp_path)
    _git(repo, "branch", "codex/scoped")
    _git(repo, "symbolic-ref", "HEAD", "refs/heads/codex/scoped")
    head = _git(repo, "rev-parse", "HEAD")
    (repo / "unowned.txt").write_bytes(b"staged\r\n")
    _git(repo, "add", "unowned.txt")
    (repo / "unowned.txt").write_bytes(b"current\r\n")
    filename = "-literal\nfile.txt"
    (repo / filename).write_bytes(b"owned\r\n\x00")
    original_index = (repo / ".git/index").read_bytes()
    real_run = subprocess.run
    operations = []

    def observe(argv, **kwargs):
        if "--literal-pathspecs" in argv:
            step = next((word for word in ("add", "commit") if word in argv), None)
            if step:
                operations.append(step)
                assert "--pathspec-from-file=-" in argv and "--pathspec-file-nul" in argv
                assert kwargs["input"] == filename
                if failure == step:
                    return subprocess.CompletedProcess(argv, 1, "", "refused")
                if failure == "index-moved" and step == "commit":
                    (repo / ".git/index").write_bytes(original_index + b"concurrent")
                if failure == "ref-moved" and step == "commit":
                    _git(repo, "commit", "--allow-empty", "-m", "concurrent")
        return real_run(argv, **kwargs)

    monkeypatch.setattr(safe.subprocess, "run", observe)
    with SafeGitContext(objects=repo / ".git/objects", temp_root=tmp_path) as context:
        context.source_git_dir = repo / ".git"

        def prepare(**kwargs):
            return safe.prepare_scoped_commit(
                context,
                worktree=repo,
                branch="codex/scoped",
                expected_head=head,
                paths=(filename,),
                subject="scoped",
                body="Refs #10931",
                trailer="X-Agent: codex/scoped",
                identity=git_identity_env("codex"),
                **kwargs,
            )

        if failure in {"index-moved", "ref-moved"}:
            with pytest.raises(SnapshotRefusal, match="auto_finalize_head_moved"):
                prepare()
            assert not (repo / ".git/index.lock").exists()
            if failure == "index-moved":
                assert _git(repo, "rev-parse", "HEAD") == head
                assert (repo / ".git/index").read_bytes() == original_index + b"concurrent"
            else:
                assert _git(repo, "rev-parse", "HEAD") != head
                assert _git(repo, "show", "HEAD:unowned.txt") == "staged"
            assert (repo / filename).read_bytes() == b"owned\r\n\x00"
            return
        result = prepare()
    assert operations == (["add"] if failure == "add" else ["add", "commit"])
    if failure:
        assert result.process.returncode == 1 and result.step == failure
        assert _git(repo, "rev-parse", "HEAD") == head
        assert (repo / ".git/index").read_bytes() == original_index
    else:
        assert result.process.returncode == 0
        assert _git(repo, "diff-tree", "--no-commit-id", "--name-only", "-r", "-z", "HEAD") == filename + "\0"
        assert _git(repo, "show", ":unowned.txt") == "staged"
        assert (repo / "unowned.txt").read_bytes() == b"current\r\n"


@pytest.mark.parametrize(
    "override",
    [
        {"paths": ()},
        {"paths": (".",)},
        {"expected_head": "HEAD"},
        {"paths": ("../outside",)},
        {"paths": ("/outside",)},
        {"paths": ("with\0nul",)},
        {"branch": "--force"},
        {"subject": "message\nX-Agent: injected/task"},
        {"body": "X-Agent: injected/task"},
        {"trailer": "Other: value"},
        {"trailer": "X-Agent: codex/task\nX-Agent: other/task"},
        {"identity": {"GIT_CONFIG_COUNT": "1"}},
    ],
)
def test_scoped_preparation_rejects_unbounded_inputs_before_mutation(tmp_path, override):
    from scripts.lib.git_identity import git_identity_env
    from scripts.orchestration.safe_git_context import SafeGitContext

    repo = _primary(tmp_path)
    head = _git(repo, "rev-parse", "HEAD")
    index = (repo / ".git/index").read_bytes()
    with SafeGitContext(objects=repo / ".git/objects", temp_root=tmp_path) as context:
        context.source_git_dir = repo / ".git"
        args = {
            "worktree": repo,
            "branch": "codex/scoped",
            "expected_head": head,
            "paths": ("file",),
            "subject": "scoped",
            "body": "Refs #10931",
            "trailer": "X-Agent: codex/task",
            "identity": git_identity_env("codex"),
        }
        with pytest.raises(ValueError, match="unsupported scoped preparation"):
            safe.prepare_scoped_commit(context, **{**args, **override})
    assert _git(repo, "rev-parse", "HEAD") == head
    assert (repo / ".git/index").read_bytes() == index
