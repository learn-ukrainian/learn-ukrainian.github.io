"""B1 regressions for bounded detached preservation, using disposable repositories."""

import hashlib
import json
import os
import subprocess

import pytest

from scripts.fleet import ignored_task_output as output
from scripts.fleet import terminal_abandon as writer
from tests.fleet.test_terminal_abandon import _recorded, invoke
from tests.fleet.test_terminal_abandon import succession as succession
from tests.fleet.test_terminal_abandon import writer_fixture as writer_fixture
from tests.fleet.test_terminal_abandon_10624 import _remove
from tests.orchestration.test_worktree_claims_cli import _git
from tests.orchestration.test_worktree_output_chokepoint import boundary_tree as original_boundary_tree
from tests.test_continuation_worktree_reap import abandon_cohort as abandon_cohort
from tests.test_continuation_worktree_reap import same_branch_pending_cohort as same_branch_pending_cohort
from tests.test_reused_worktree_retention import cohort as cohort


@pytest.fixture
def boundary_tree(tmp_path, monkeypatch, request):
    fixture = original_boundary_tree.__wrapped__(tmp_path, monkeypatch)
    if request.node.name == "test_thin_bundle_excludes_large_history":
        repo, tree, *_ = fixture
        history = repo / "historical.bin"
        history.write_bytes(os.urandom(2 * 1024 * 1024))
        _git(repo, "add", history.name)
        _git(repo, "commit", "-m", "large historical object")
        history.unlink()
        _git(repo, "add", history.name)
        _git(repo, "commit", "-m", "remove historical object")
        _git(repo, "update-ref", "refs/remotes/origin/main", _git(repo, "rev-parse", "main"))
        _git(tree, "reset", "--hard", "main")
    return fixture


def _detach(fixture):
    _git(fixture[1], "checkout", "--detach", fixture[-1])


def _bundles(fixture):
    return sorted(fixture[5].parent.glob("*.bundle"))


def test_thin_bundle_excludes_large_history(succession, capsys):
    fixture, _ = succession
    _detach(fixture)
    assert invoke(fixture) == 0
    capsys.readouterr()
    _, _, manifest = _recorded(fixture)
    bundle = fixture[0] / manifest["detached_bundle"]["path"]
    assert bundle.stat().st_size < 64 * 1024, "bundle must exclude the large pre-base history"


def test_thin_bundle_restore_after_removal(succession, tmp_path, capsys):
    fixture, _ = succession
    repo, _, _, _, _, _, head = fixture
    _detach(fixture)
    assert invoke(fixture) == 0
    capsys.readouterr()
    _, _, manifest = _recorded(fixture)
    bundle = repo / manifest["detached_bundle"]["path"]
    _remove(fixture)
    empty = tmp_path / "empty"
    empty.mkdir()
    _git(empty, "init")
    missing = subprocess.run(["git", "bundle", "verify", str(bundle)], cwd=empty, capture_output=True, timeout=30)
    assert missing.returncode != 0, "thin bundle must require the excluded base"
    assert manifest["base_sha"].encode() in missing.stderr
    _git(repo, "bundle", "verify", str(bundle))
    restored = tmp_path / "restored"
    _git(repo, "clone", "--no-local", "--single-branch", "--branch", "main", str(repo), str(restored))
    assert _git(restored, "rev-parse", "HEAD") == manifest["base_sha"]
    _git(restored, "fetch", str(bundle), "HEAD")
    _git(restored, "checkout", "--detach", "FETCH_HEAD")
    assert _git(restored, "rev-parse", "HEAD") == head
    assert (restored / "README.md").read_bytes() == b"unpublished abandoned implementation\n"


def test_bundle_verification_uses_surviving_primary(succession, monkeypatch, capsys):
    fixture, _ = succession
    _detach(fixture)
    original = output.artifacts.safe_git
    verified = []

    def git(args, **kwargs):
        if args[:2] == ["bundle", "verify"]:
            verified.append(kwargs["cwd"])
        return original(args, **kwargs)

    monkeypatch.setattr(output.artifacts, "safe_git", git)
    assert invoke(fixture) == 0
    capsys.readouterr()
    assert verified and all(cwd == fixture[0] for cwd in verified), "bundle verification must use primary"


def test_detached_bundle_cap_refuses_and_cleans(succession, monkeypatch, capsys):
    fixture, _ = succession
    _detach(fixture)
    monkeypatch.setattr(output, "MAX_DETACHED_BUNDLE_BYTES", 1, raising=False)
    assert invoke(fixture) == 2, "bundle above cap must refuse"
    refusal = json.loads(capsys.readouterr().out)
    assert refusal["code"] == "PRESERVATION_LIMIT"
    assert "MAX_DETACHED_BUNDLE_BYTES" in refusal["reason"] and "1 bytes" in refusal["reason"]
    assert not _bundles(fixture)
    assert not list(fixture[5].parent.glob(".head-bundle-*"))


@pytest.mark.parametrize("failure", ["capture", "validator", "activity", "manifest", "output_publish", "record_write"])
def test_fresh_bundle_removed_on_every_publication_refusal(succession, monkeypatch, capsys, failure):
    fixture, _ = succession
    _, tree, tasks, *_ = fixture
    _detach(fixture)

    def refuse(*args, **kwargs):
        raise ValueError("injected publication refusal")

    if failure == "capture":
        monkeypatch.setattr(output, "capture_abandon_output", refuse)
    elif failure == "validator":
        monkeypatch.setattr(output, "terminal_abandon_creator", refuse)
    elif failure == "activity":
        original = writer._activity
        calls = 0

        def activity(*args, **kwargs):
            nonlocal calls
            calls += 1
            if calls == 2:
                raise writer.Refusal("LIVE_OR_WANTED", "injected publication refusal")
            return original(*args, **kwargs)

        monkeypatch.setattr(writer, "_activity", activity)
    elif failure == "manifest":
        original = writer.os.replace

        def replace(source, target):
            if target.name.startswith("terminal-abandon-"):
                refuse()
            return original(source, target)

        monkeypatch.setattr(writer.os, "replace", replace)
    elif failure == "output_publish":
        monkeypatch.setattr(output, "publish_abandon_output", refuse)
    else:
        # The record's first write is its pending, not yet consumable, form (#10657).
        monkeypatch.setattr(writer, "_write_pending", refuse)
    assert invoke(fixture) == 2
    capsys.readouterr()
    assert tree.exists()
    assert "worktree_abandon" not in json.loads((tasks / "boundary.json").read_bytes())
    assert not writer.pending_record_path(tasks / "boundary.json").exists()
    assert not _bundles(fixture), "refused publication must remove its freshly created bundle"
    assert not list(fixture[5].parent.glob(".head-bundle-*"))
    assert not list(fixture[5].parent.glob("terminal-abandon-*.json"))


def test_refused_retry_does_not_leak_bundles(succession, monkeypatch, capsys):
    fixture, _ = succession
    _detach(fixture)

    def refuse(*args, **kwargs):
        raise ValueError("injected refusal")

    with monkeypatch.context() as patch:
        patch.setattr(output, "capture_abandon_output", refuse)
        for _ in range(2):
            assert invoke(fixture) == 2
            capsys.readouterr()
            assert not _bundles(fixture), "refused retries must not retain a bundle"
    assert invoke(fixture) == 0
    capsys.readouterr()
    before = {path: (path.stat().st_ino, path.read_bytes()) for path in _bundles(fixture)}
    assert len(before) == 1
    assert invoke(fixture) == 0
    assert json.loads(capsys.readouterr().out)["outcome"] == "already_recorded"
    assert {path: (path.stat().st_ino, path.read_bytes()) for path in _bundles(fixture)} == before


def test_bundle_hashing_never_materializes_payload(succession, monkeypatch, capsys):
    fixture, _ = succession
    _detach(fixture)
    original = output.artifacts._read_preserved_bytes

    def read(path, **kwargs):
        assert path.suffix != ".bundle" and not path.name.startswith(".head-bundle-"), (
            "bundle hashing must stream instead of reading the full payload"
        )
        return original(path, **kwargs)

    monkeypatch.setattr(output.artifacts, "_read_preserved_bytes", read)
    assert invoke(fixture) == 0
    capsys.readouterr()
    _, _, manifest = _recorded(fixture)
    saved = manifest["detached_bundle"]
    assert hashlib.sha256((fixture[0] / saved["path"]).read_bytes()).hexdigest() == saved["sha256"]
    assert invoke(fixture) == 0
    capsys.readouterr()
    _remove(fixture)


def test_streaming_digest_bounds_reads_and_checks_digest(tmp_path, monkeypatch):
    saved = tmp_path / "batch_state/saved.bundle"
    saved.parent.mkdir()
    payload = b"preserved bytes\n" * (160 * 1024)
    saved.write_bytes(payload)
    locator = {"path": "batch_state/saved.bundle", "sha256": hashlib.sha256(payload).hexdigest()}
    reads = []
    original = os.read

    def read(fd, size):
        reads.append(size)
        return original(fd, size)

    monkeypatch.setattr(os, "read", read)
    assert output._abandon_file(tmp_path, locator, read_payload=False) == b""
    assert len(reads) > 1 and max(reads) <= 1024 * 1024
    assert output._abandon_file(tmp_path, locator) == payload
    with pytest.raises(ValueError, match="digest invalid"):
        output._abandon_file(tmp_path, dict(locator, sha256="0" * 64), read_payload=False)


@pytest.mark.parametrize("kind", ["leaf_link", "parent_link", "fifo", "directory"])
def test_streaming_digest_refuses_links_and_nonregular_files(tmp_path, kind):
    root = tmp_path / "batch_state"
    root.mkdir()
    outside = tmp_path / "outside"
    outside.mkdir()
    (outside / "bytes").write_bytes(b"private bytes")
    saved = root / "saved"
    if kind == "leaf_link":
        saved.symlink_to(outside / "bytes")
    elif kind == "parent_link":
        saved.symlink_to(outside, target_is_directory=True)
        saved = saved / "bytes"
    elif kind == "fifo":
        os.mkfifo(saved)
    else:
        saved.mkdir()
    with pytest.raises((OSError, ValueError)):
        output._abandon_regular(tmp_path, saved, read_payload=False)


def test_streaming_digest_refuses_mid_read_mutation(tmp_path, monkeypatch):
    saved = tmp_path / "batch_state/saved.bundle"
    saved.parent.mkdir()
    saved.write_bytes(b"first bytes")
    original = os.read

    def read(fd, size):
        chunk = original(fd, size)
        saved.write_bytes(b"other bytes of a different size")
        return chunk

    monkeypatch.setattr(os, "read", read)
    with pytest.raises(ValueError, match="changed during hashing"):
        output._abandon_regular(tmp_path, saved, read_payload=False)


def test_existing_bundle_reused_at_cap_and_kept_on_refusal(succession, monkeypatch, capsys):
    fixture, _ = succession
    repo, tree, _, _, _, supplied, head = fixture
    _detach(fixture)
    base = json.loads(supplied.read_bytes())["base_sha"]
    locator, created = writer._detached_bundle(tree, supplied.parent, repo, head, base)
    assert created == repo / locator["path"]
    before = created.stat().st_ino
    monkeypatch.setattr(output, "MAX_DETACHED_BUNDLE_BYTES", created.stat().st_size)

    def refuse(*args, **kwargs):
        raise ValueError("injected refusal after reuse")

    with monkeypatch.context() as patch:
        patch.setattr(output, "capture_abandon_output", refuse)
        assert invoke(fixture) == 2
        capsys.readouterr()
    assert created.stat().st_ino == before
    assert invoke(fixture) == 0
    capsys.readouterr()
    assert _bundles(fixture) == [created]
    assert created.stat().st_ino == before
