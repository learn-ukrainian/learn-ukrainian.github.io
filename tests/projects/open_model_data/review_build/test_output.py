import os
from pathlib import Path

import pytest

from scripts.projects.open_model_data.review_build import output
from scripts.projects.open_model_data.review_build.errors import BuildError


@pytest.fixture(autouse=True)
def synthetic_mount(monkeypatch):
    # CI may run on overlay; test a declared synthetic ext4 mount, never bypass
    # the production filesystem check. Its real parser is tested separately.
    monkeypatch.setattr(output, "filesystem", lambda path: "ext4")


def test_private_directories_files_and_read(tmp_path):
    target = tmp_path / "SYNTHETIC-out" / "nested"
    with output.OutputGuard(target) as guard:
        guard.write("C1/records.jsonl", b"SYNTHETIC text\n")
        assert guard.read("C1/records.jsonl") == b"SYNTHETIC text\n"
        guard.write("C1/records.jsonl", b"SYNTHETIC replacement\n")
        assert guard.read("C1/records.jsonl") == b"SYNTHETIC replacement\n"
        for path in (target, target.parent, target / "C1"):
            assert path.stat().st_mode & 0o777 == 0o700
        assert (target / "C1/records.jsonl").stat().st_mode & 0o777 == 0o600
        for name in ("../escape", "/absolute", "a//b", "a/./b", "SYNTHETIC\ntext"):
            with pytest.raises(BuildError):
                guard.write(name, b"SYNTHETIC")


@pytest.mark.parametrize("entry", ["directory", "worktree-file", "broken-symlink"])
def test_git_ancestor_refusal(tmp_path, entry):
    repo = tmp_path / "SYNTHETIC-repo"
    repo.mkdir()
    git = repo / ".git"
    if entry == "directory":
        git.mkdir()
    elif entry == "worktree-file":
        git.write_text("SYNTHETIC gitdir")
    else:
        git.symlink_to(repo / "SYNTHETIC-missing")
    with pytest.raises(BuildError, match="repository_output"):
        output.OutputGuard(repo / "nested" / "output")
    assert not (repo / "nested").exists()


def test_explicit_repository_private_infra_and_worktree_roots(tmp_path):
    for name in ("SYNTHETIC-repository", "SYNTHETIC-worktree", "SYNTHETIC-infra"):
        protected = tmp_path / name
        with pytest.raises(BuildError, match="repository_output"):
            output.OutputGuard(protected / "output", (protected,))


@pytest.mark.parametrize("position", ["leaf", "ancestor", "before-dotdot"])
def test_symlink_components_refused_before_resolution(tmp_path, position):
    real = tmp_path / "SYNTHETIC-real"
    real.mkdir(mode=0o700)
    link = tmp_path / "SYNTHETIC-link"
    link.symlink_to(real, target_is_directory=True)
    path = link if position == "leaf" else link / "output" if position == "ancestor" else link / ".." / "output"
    with pytest.raises(BuildError, match="symlink_output"):
        output.OutputGuard(path)


@pytest.mark.parametrize("kind", ["filesystem", "mount-unreadable", "acl-unreadable", "mode", "owner", "acl", "access"])
def test_each_guard_refusal(tmp_path, monkeypatch, kind):
    target = tmp_path / "SYNTHETIC-out"
    target.mkdir(mode=0o700)
    if kind == "filesystem":
        monkeypatch.setattr(output, "filesystem", lambda path: "nfs")
    elif kind == "mount-unreadable":

        def fail(path):
            raise PermissionError("SYNTHETIC private text")

        monkeypatch.setattr(output, "filesystem", fail)
    elif kind == "acl-unreadable":
        monkeypatch.setattr(os, "listxattr", lambda fd: (_ for _ in ()).throw(PermissionError("SYNTHETIC")))
    elif kind == "mode":
        target.chmod(0o750)
    elif kind == "owner":
        monkeypatch.setattr(os, "getuid", lambda: target.stat().st_uid + 1)
    elif kind == "acl":
        monkeypatch.setattr(os, "listxattr", lambda fd: ["system.posix_acl_access"])
    elif kind == "access":
        monkeypatch.setattr(os, "open", lambda *args, **kwargs: (_ for _ in ()).throw(PermissionError("SYNTHETIC")))
    with pytest.raises(BuildError):
        output.OutputGuard(target)


@pytest.mark.parametrize("kind", ["symlink-file", "hardlink", "file-mode", "symlink-dir", "dir-mode", "git-in-child"])
def test_descriptor_relative_writes_refuse_unsafe_existing_entries(tmp_path, kind):
    target = tmp_path / "SYNTHETIC-out"
    with output.OutputGuard(target) as guard:
        child = target / "C1"
        child.mkdir(mode=0o700)
        file = child / "records.jsonl"
        if kind == "symlink-file":
            file.symlink_to(tmp_path / "SYNTHETIC-victim")
        elif kind == "hardlink":
            victim = tmp_path / "SYNTHETIC-victim"
            victim.write_bytes(b"SYNTHETIC untouched")
            os.link(victim, file)
        elif kind == "file-mode":
            file.write_bytes(b"SYNTHETIC untouched")
            file.chmod(0o644)
        elif kind == "symlink-dir":
            (target / "alias").symlink_to(child)
        elif kind == "dir-mode":
            child.chmod(0o755)
        else:
            (child / ".git").write_text("SYNTHETIC gitdir")
        name = "alias/records.jsonl" if kind == "symlink-dir" else "C1/records.jsonl"
        with pytest.raises((BuildError, OSError)):
            guard.write(name, b"SYNTHETIC replacement")
        if kind in {"hardlink", "file-mode"}:
            assert file.read_bytes() == b"SYNTHETIC untouched"


def test_filesystem_parser_longest_mount_and_escaped_path(tmp_path, monkeypatch):
    real_method = Path.read_text
    mount = str(tmp_path).replace(" ", r"\040")
    info = f"1 0 0:1 / / rw - ext4 /dev/SYNTHETIC rw\n2 1 0:2 / {mount} rw - nfs SYNTHETIC rw\n"
    monkeypatch.undo()
    monkeypatch.setattr(
        Path,
        "read_text",
        lambda path, *a, **kw: info if str(path) == "/proc/self/mountinfo" else real_method(path, *a, **kw),
    )
    assert output.filesystem(tmp_path / "output") == "nfs"
    assert output.filesystem(Path("/SYNTHETIC")) == "ext4"
    with pytest.raises(BuildError, match="filesystem_refused"):
        output.OutputGuard(tmp_path / "output")
    monkeypatch.setattr(Path, "read_text", lambda *a, **kw: "")
    with pytest.raises(BuildError, match="filesystem_unknown"):
        output.filesystem(tmp_path)


def test_private_umask_is_applied_and_restored_even_on_exception():
    initial = os.umask(0o022)
    try:
        with pytest.raises(ValueError), output.private_umask():
            observed = os.umask(0o077)
            assert observed == 0o077
            raise ValueError("SYNTHETIC failure")
        observed = os.umask(0o022)
        assert observed == 0o022
    finally:
        os.umask(initial)


def test_open_output_cannot_be_moved_into_a_repository(tmp_path):
    target = tmp_path / "SYNTHETIC-out"
    with output.OutputGuard(target) as guard:
        repo = tmp_path / "SYNTHETIC-repo"
        repo.mkdir()
        (repo / ".git").mkdir()
        target.rename(repo / "moved")
        with pytest.raises(BuildError, match="output_path_changed"):
            guard.write("records.jsonl", b"SYNTHETIC private text")
        assert not (repo / "moved/records.jsonl").exists()


def test_repository_marker_added_after_admission_refuses_write(tmp_path):
    target = tmp_path / "SYNTHETIC-out"
    with output.OutputGuard(target) as guard:
        (target / ".git").mkdir()
        with pytest.raises(BuildError, match="repository_output"):
            guard.write("records.jsonl", b"SYNTHETIC private text")
        assert not (target / "records.jsonl").exists()


def test_relative_symlink_path_before_dotdot_is_refused(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / "SYNTHETIC-real").mkdir()
    (tmp_path / "SYNTHETIC-link").symlink_to(tmp_path / "SYNTHETIC-real", target_is_directory=True)
    with pytest.raises(BuildError, match="symlink_output"):
        output.OutputGuard(Path("SYNTHETIC-link/../output"))
    assert not (tmp_path / "output").exists()
    with output.OutputGuard(Path("SYNTHETIC-relative-out")) as guard:
        guard.write("records.jsonl", b"SYNTHETIC private text")
        assert guard.read("records.jsonl") == b"SYNTHETIC private text"
