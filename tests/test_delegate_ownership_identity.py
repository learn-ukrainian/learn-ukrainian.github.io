"""Filesystem identity discovery and conservative probe-failure behavior (#11375)."""

import os
from pathlib import Path

import pytest

from scripts.guardrails import delegate_ownership as ownership


@pytest.mark.parametrize("layout", ["primary", "relative", "absolute", "symlink", "gitdir-symlink"])
@pytest.mark.parametrize("common_kind", ["absent", "relative", "absolute"])
def test_filesystem_identity_follows_checkout_and_common_directory(tmp_path, monkeypatch, layout, common_kind):
    """Relative pointers, external Git directories and symlinks must retain one identity."""
    checkout = tmp_path / "checkout"
    checkout.mkdir()
    git_dir = checkout / ".git" if layout == "primary" else tmp_path / "git store "
    git_dir.mkdir()
    if layout == "relative":
        (checkout / ".git").write_bytes(b"gitdir: ../git store \r\n")
    elif layout == "absolute":
        (checkout / ".git").write_bytes(b"gitdir: " + os.fsencode(git_dir) + b"\n")
    elif layout == "symlink":
        (checkout / ".git").symlink_to(git_dir, target_is_directory=True)
    elif layout == "gitdir-symlink":
        alias = tmp_path / "git-alias"
        alias.symlink_to(git_dir, target_is_directory=True)
        (checkout / ".git").write_text("gitdir: ../git-alias\n")
    common = git_dir
    if common_kind != "absent":
        common = tmp_path / "common store "
        common.mkdir()
        target = os.path.relpath(common, git_dir) if common_kind == "relative" else str(common)
        (git_dir / "commondir").write_bytes(os.fsencode(target) + b"\n")
    nested = checkout / "one" / "two"
    nested.mkdir(parents=True)
    alias = tmp_path / "checkout-alias"
    alias.symlink_to(checkout, target_is_directory=True)
    assert ownership._repository_identity(alias / "one" / "two") == str(common.resolve())
    monkeypatch.chdir(nested)
    assert ownership._repository_identity(None) == str(common.resolve())


@pytest.mark.parametrize("damage", [
    "missing-marker", "garbled-marker", "empty-pointer", "missing-gitdir", "file-gitdir",
    "nul-pointer", "broken-marker", "loop-marker", "empty-common", "missing-common",
    "file-common", "directory-common", "broken-common", "nul-common", "missing-cwd", "file-cwd",
])
def test_unresolved_metadata_admits_disjoint_work_and_keeps_same_ledger_conflicts(tmp_path, damage):
    """Bad identity metadata must add a typed note, never a new admission refusal."""
    checkout = tmp_path / "checkout"
    checkout.mkdir()
    marker = checkout / ".git"
    if damage == "missing-cwd":
        checkout /= "missing"
    elif damage == "file-cwd":
        checkout /= "file"
        checkout.touch()
    elif damage == "garbled-marker":
        marker.write_text("not a git pointer\n")
    elif damage == "empty-pointer":
        marker.write_text("gitdir: \n")
    elif damage == "missing-gitdir":
        marker.write_text("gitdir: ../missing\n")
    elif damage == "file-gitdir":
        (tmp_path / "file").touch()
        marker.write_text("gitdir: ../file\n")
    elif damage == "nul-pointer":
        marker.write_bytes(b"gitdir: invalid\x00path\n")
    elif damage == "broken-marker":
        marker.symlink_to(tmp_path / "missing")
    elif damage == "loop-marker":
        marker.symlink_to(marker)
    elif damage != "missing-marker":
        marker.mkdir()
        common = marker / "commondir"
        if damage == "empty-common":
            common.write_text("")
        elif damage == "missing-common":
            common.write_text("../missing\n")
        elif damage == "file-common":
            (tmp_path / "file").touch()
            common.write_text(str(tmp_path / "file"))
        elif damage == "directory-common":
            common.mkdir()
        elif damage == "broken-common":
            common.symlink_to(tmp_path / "missing")
        elif damage == "nul-common":
            common.write_bytes(b"invalid\x00path\n")
    ledger_path = tmp_path / "ownership.sqlite3"
    known = tmp_path / "known"
    (known / ".git").mkdir(parents=True)
    holder = ownership.OwnershipLedger(ledger_path, task_state_dir=tmp_path, cwd=known)
    assert holder.admit(task_id="holder", mode="workspace-write", owned_paths=["tests/unit.py"], pid=os.getpid()).admitted
    unknown = ownership.OwnershipLedger(ledger_path, task_state_dir=tmp_path, cwd=checkout)
    assert unknown.repository_identity is None
    for task, path, admitted in (("disjoint", "docs/readme.md", True), ("overlap", "tests/unit.py", False)):
        result = unknown.admit(task_id=task, mode="workspace-write", owned_paths=[path], pid=os.getpid())
        assert result.admitted is admitted
        assert result.notes == ["repository_identity_unresolved"]


@pytest.mark.parametrize("operation", ["lstat", "read_bytes", "resolve"])
@pytest.mark.parametrize("error", [PermissionError, ValueError, RuntimeError])
def test_filesystem_probe_exceptions_never_escape_ledger_construction(tmp_path, monkeypatch, operation, error):
    """An identity read failure must not become a ledger-error dispatch refusal."""
    checkout = tmp_path / "checkout"
    checkout.mkdir()
    marker = checkout / ".git"
    marker.write_text("gitdir: ../unused\n")
    original = getattr(Path, operation)

    def fail_probe(path, *args, **kwargs):
        if path == (checkout if operation == "resolve" else marker):
            raise error("identity probe unavailable")
        return original(path, *args, **kwargs)

    monkeypatch.setattr(Path, operation, fail_probe)
    ledger = ownership.OwnershipLedger(tmp_path / "ownership.sqlite3", task_state_dir=tmp_path, cwd=checkout)
    result = ledger.admit(task_id="writer", mode="workspace-write", owned_paths=["tests/unit.py"], pid=os.getpid())
    assert result.admitted
    assert result.repository_id is None
    assert result.notes == ["repository_identity_unresolved"]


def test_nearest_garbled_marker_does_not_borrow_parent_repository(tmp_path):
    """A broken nested checkout must not silently acquire its parent's identity."""
    (tmp_path / ".git").mkdir()
    nested = tmp_path / "nested"
    nested.mkdir()
    (nested / ".git").write_text("garbled\n")
    assert ownership._repository_identity(nested) is None
