"""Real-Git evidence for the fresh execution and exact-snapshot invariant."""

from __future__ import annotations

import os
import subprocess
from pathlib import Path

import pytest

from scripts.orchestration.safe_git_context import CANONICAL_ORIGIN, GIT, SafeGitContext, SnapshotRefusal


def git(repo: Path, *args: str) -> str:
    env = {"PATH": os.defpath, "HOME": str(repo), "GIT_CONFIG_NOSYSTEM": "1", "GIT_CONFIG_GLOBAL": os.devnull}
    return subprocess.run([GIT, *args], cwd=repo, env=env, capture_output=True, text=True, check=True, timeout=60).stdout.strip()


@pytest.fixture
def source(tmp_path):
    repo = tmp_path / "source"
    remote = tmp_path / "remote.git"
    git(tmp_path, "init", "--bare", str(remote))
    git(tmp_path, "init", str(repo))
    git(repo, "config", "user.name", "fixture")
    git(repo, "config", "user.email", "fixture@example.com")
    for name in ("base", "deleted", "executable"):
        (repo / name).write_text(f"{name}\n")
    git(repo, "add", "-A")
    git(repo, "commit", "-m", "base")
    return repo, remote, git(repo, "rev-parse", "HEAD")


def context(source, tmp_path, **kwargs):
    repo, remote, _head = source
    return SafeGitContext(objects=repo / ".git/objects", temp_root=tmp_path, origin=str(remote), local_remote=True, **kwargs)


def plant_programs(repo, root, *, scope="--local", monkeypatch=None):
    """A single marker detects every worker-configured execution channel."""
    marker = root / "planted-program-ran"
    hooks = root / "planted-hooks"
    hooks.mkdir()
    script = f"#!/bin/sh\necho executed >> '{marker}'\nexit 0\n"
    for name in ("pre-push", "post-checkout", "post-index-change", "reference-transaction", "pre-commit", "commit-msg", "post-commit", "program"):
        path = hooks / name
        path.write_text(script)
        path.chmod(0o755)
    program = hooks / "program"
    included = root / "included.config"
    included.write_text(f'[core]\n\tfsmonitor = "{program}"\n')
    attributes = root / "external.attributes"
    attributes.write_text("* filter=evil\n")
    template = root / "planted-template"
    (template / "hooks").mkdir(parents=True)
    (template / "hooks/pre-push").write_text(script)
    (template / "hooks/pre-push").chmod(0o755)
    # Fixture setup itself must remain inert while planting settings.
    values = {
        "credential.helper": f"!{program}", "core.sshCommand": str(program),
        f"url.ext::{program}.pushInsteadOf": str(root / "origin.git"),
        "protocol.ext.allow": "always", "filter.evil.clean": str(program),
        "filter.evil.smudge": str(program), "core.attributesFile": str(attributes),
        "include.path": str(included), "core.fsmonitor": str(program), "core.hooksPath": str(hooks),
    }
    for key, value in values.items():
        git(repo, "config", scope, key, value)
    if monkeypatch is not None:
        for key, value in {
            "GIT_CONFIG_COUNT": "1", "GIT_CONFIG_KEY_0": "include.path", "GIT_CONFIG_VALUE_0": str(included),
            "GIT_SSH_COMMAND": str(program), "GIT_ASKPASS": str(program), "SSH_ASKPASS": str(program),
            "GIT_TEMPLATE_DIR": str(template), "GIT_EXEC_PATH": str(hooks),
            "GIT_CONFIG_GLOBAL": str(included), "GIT_CONFIG_SYSTEM": str(included),
            "GIT_DIR": str(repo / ".git"), "GIT_WORK_TREE": str(repo),
        }.items():
            monkeypatch.setenv(key, value)
    return marker


@pytest.mark.parametrize("token", [None, "synthetic-driver-identity"])
def test_only_one_driver_written_config_and_no_inherited_environment(source, tmp_path, monkeypatch, token):
    repo, _remote, _head = source
    marker = plant_programs(repo, tmp_path, monkeypatch=monkeypatch)
    with context(source, tmp_path, token=token) as safe:
        config = safe.checked("config", "--show-origin", "--list")
        assert {line.split("\t")[0] for line in config.splitlines()} == {f"file:{safe.git_dir}/config"}
        assert not (safe.git_dir / "commondir").exists()
        assert list((safe.git_dir / "hooks").glob("*")) == []
        assert os.path.isabs(GIT)
        assert safe.env["PATH"] == os.defpath
        assert "GIT_SSH_COMMAND" not in safe.env and "GIT_CONFIG_COUNT" not in safe.env
        first = safe.root
    assert not first.exists()
    with context(source, tmp_path) as second:
        assert second.root != first
    assert not marker.exists()


@pytest.mark.parametrize("dirty", [False, True])
def test_full_flow_canary_and_exact_checked_remote_commit(source, tmp_path, monkeypatch, dirty):
    repo, remote, base = source
    (repo / "base").write_text("committed\n")
    git(repo, "add", "-A")
    git(repo, "commit", "-m", "worker")
    head = git(repo, "rev-parse", "HEAD")
    if dirty:
        (repo / "base").write_text("uncommitted\n")
        (repo / "deleted").unlink()
        (repo / "executable").chmod(0o755)
        (repo / "link").symlink_to("outside-do-not-follow")
        (repo / ".gitignore").write_text("ignored\n")
        (repo / "ignored").write_text("excluded\n")
    index_before = (repo / ".git/index").read_bytes()
    marker = plant_programs(repo, tmp_path, monkeypatch=monkeypatch)
    with context(source, tmp_path) as safe:
        assert safe.read_source_ref(repo / ".git", "HEAD").stdout.strip() == head
        tree = safe.capture(repo, head)
        safe.refuse_tree(base, tree)
        checked_tree = tree
        commit = safe.checked("commit-tree", tree, "-p", head, "-m", "rescue") if dirty else head
        assert safe.checked("rev-parse", f"{commit}^{{tree}}") == checked_tree
        assert safe.run("push", "--no-verify", "origin", f"{commit}:refs/heads/rescue", network=True).returncode == 0
        assert safe.checked("ls-remote", "--heads", "origin", "refs/heads/rescue").split()[0] == commit
        assert safe.checked("config", "--show-origin", "--list").count("file:") > 0
        if dirty:
            records = safe.checked("ls-tree", "-r", commit)
            assert "120000 blob" in records and "100755 blob" in records
            assert "\tdeleted" not in records and "\tignored" not in records
            assert safe.checked("show", f"{commit}:link") == "outside-do-not-follow"
            assert safe.checked("show", f"{commit}:base") == "uncommitted"
    assert git(remote, "rev-parse", "refs/heads/rescue") == commit
    assert (repo / ".git/index").read_bytes() == index_before
    assert not marker.exists()


@pytest.mark.parametrize("committed", [False, True])
@pytest.mark.parametrize("filter_name", ["lfs", "evil"])
def test_named_filters_refused_before_push(source, tmp_path, committed, filter_name):
    repo, remote, base = source
    (repo / ".gitattributes").write_text(f"base filter={filter_name}\n")
    (repo / "base").write_text("changed\n")
    head = base
    if committed:
        git(repo, "add", "-A")
        git(repo, "commit", "-m", "filtered")
        head = git(repo, "rev-parse", "HEAD")
    with context(source, tmp_path) as safe:
        with pytest.raises(SnapshotRefusal, match="rescue_filtered_path"):
            tree = safe.capture(repo, head)
            safe.refuse_tree(base, tree)
    assert git(remote, "for-each-ref") == ""
    assert (repo / "base").read_text() == "changed\n"


def test_deleted_filtered_path_is_also_refused(source, tmp_path):
    repo, remote, _ = source
    (repo / ".gitattributes").write_text("base filter=lfs\n")
    git(repo, "add", "-A")
    git(repo, "commit", "-m", "attributes")
    head = git(repo, "rev-parse", "HEAD")
    (repo / "base").unlink()
    (repo / ".gitattributes").unlink()
    with context(source, tmp_path) as safe:
        with pytest.raises(SnapshotRefusal, match="rescue_filtered_path"):
            safe.capture(repo, head)
    assert git(remote, "for-each-ref") == ""


def test_new_committed_gitlink_refused(source, tmp_path):
    repo, remote, base = source
    git(repo, "update-index", "--add", "--cacheinfo", f"160000,{base},nested")
    git(repo, "commit", "-m", "gitlink")
    head = git(repo, "rev-parse", "HEAD")
    with context(source, tmp_path) as safe:
        with pytest.raises(SnapshotRefusal, match="rescue_new_gitlink"):
            safe.refuse_tree(base, head)
    assert git(remote, "for-each-ref") == ""


def test_sparse_capture_preserves_absent_skip_worktree_entries(source, tmp_path):
    repo, _remote, head = source
    git(repo, "update-index", "--skip-worktree", "deleted")
    (repo / "deleted").unlink()
    (repo / "base").write_text("changed\n")
    with context(source, tmp_path) as safe:
        tree = safe.capture(repo, head, worker_index=repo / ".git/index")
        assert safe.checked("show", f"{tree}:deleted") == "deleted"
        assert safe.checked("show", f"{tree}:base") == "changed"


@pytest.mark.parametrize("url", ["ssh://github.com/repo", "ext::program", "https://example.com/other", "kimi-push-disabled://blocked"])
def test_noncanonical_destination_refused(source, tmp_path, url):
    repo, _remote, _head = source
    with pytest.raises(SnapshotRefusal, match="rescue_push_url_unavailable"):
        SafeGitContext(objects=repo / ".git/objects", temp_root=tmp_path, origin=url)


def test_default_destination_is_driver_pinned(source, tmp_path):
    repo, _remote, _head = source
    with SafeGitContext(objects=repo / ".git/objects", temp_root=tmp_path) as safe:
        assert safe.checked("config", "remote.origin.url") == CANONICAL_ORIGIN
        assert safe.checked("config", "protocol.allow") == "never"
        assert safe.checked("config", "protocol.https.allow") == "always"
        assert safe.run("config", "protocol.file.allow").returncode == 1


def test_source_repository_exclusions_are_preserved_as_data(source, tmp_path):
    repo, _remote, head = source
    exclude = repo / ".git/info/exclude"
    exclude.write_text("local-output\n")
    (repo / "local-output").write_text("excluded\n")
    (repo / "base").write_text("included\n")
    with context(source, tmp_path) as safe:
        tree = safe.capture(repo, head, exclude_file=exclude)
        assert safe.checked("show", f"{tree}:base") == "included"
        assert safe.run("cat-file", "-e", f"{tree}:local-output").returncode != 0
        safe.verify_inputs()
        exclude.write_text("changed\n")
        with pytest.raises(SnapshotRefusal, match="rescue_input_changed"):
            safe.verify_inputs()


def test_working_attributes_cannot_hide_a_named_filter_from_the_captured_tree(source, tmp_path):
    repo, _remote, head = source
    (repo / ".gitignore").write_text(".gitattributes\n")
    (repo / ".gitattributes").write_text("base filter=evil\n")
    (repo / "base").write_text("changed\n")
    with context(source, tmp_path) as safe:
        with pytest.raises(SnapshotRefusal, match="rescue_filtered_path"):
            safe.capture(repo, head)
