"""The `.agent` reaper must not be redirectable between validation and deletion.

A cross-family review proved the previous shell implementation deleted a file
OUTSIDE the repository: it validated a path, then deleted by that same path, and a
symlink swapped in between the two steps redirected the deletion
(`TOCTOU_FILE_EXTERNAL_VICTIM=DELETED`, same for `rmdir`).

That window is reachable in normal operation, not only under attack: `.agent/` is
written by agents, deploy runs while other agents are live, and deploy runs with
the operator's full privileges.

`test_fd_bound_deletion_survives_path_swap` is the load-bearing one. It performs
the swap explicitly between opening the directory and unlinking, and asserts the
external victim survives. `test_path_based_deletion_would_have_escaped` pins the
old behaviour so the guarantee cannot silently regress to path semantics.
"""

from __future__ import annotations

import errno
import importlib.util
import os
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
MODULE_PATH = REPO_ROOT / "scripts" / "deploy" / "reap_agent_mirrors.py"

spec = importlib.util.spec_from_file_location("reap_agent_mirrors_under_test", MODULE_PATH)
assert spec and spec.loader
reaper = importlib.util.module_from_spec(spec)
spec.loader.exec_module(reaper)


def _fixture(tmp_path: Path) -> tuple[Path, Path, Path]:
    """agent root with a real nested target, plus an external victim directory."""
    agent = tmp_path / "proj" / ".agent"
    (agent / "sub").mkdir(parents=True)
    inner = agent / "sub" / "victim.txt"
    inner.write_text("inner", encoding="utf-8")

    outside = tmp_path / "outside"
    outside.mkdir()
    external = outside / "victim.txt"
    external.write_text("external", encoding="utf-8")
    return agent, inner, external


def test_fd_bound_deletion_survives_path_swap(tmp_path: Path) -> None:
    """Swap the parent to an external symlink AFTER the fd is open.

    The unlink must still land inside the directory that was actually opened.
    """
    agent, inner, external = _fixture(tmp_path)

    parent_fd, opened = reaper._walk_to_parent(str(agent), ["sub", "victim.txt"])
    try:
        # The race: between validation/open and deletion, redirect the path.
        (agent / "sub").rename(tmp_path / "sub-moved")
        (agent / "sub").symlink_to(external.parent, target_is_directory=True)
        assert (agent / "sub").is_symlink()

        os.unlink("victim.txt", dir_fd=parent_fd)
    finally:
        reaper._close_all(opened)

    assert external.exists(), "external victim was deleted through the swapped path"
    assert external.read_text(encoding="utf-8") == "external"
    assert not (tmp_path / "sub-moved" / "victim.txt").exists(), (
        "the real in-.agent target should have been removed"
    )
    # After the swap the ORIGINAL path resolves through the symlink to the external
    # file, which is exactly why path-based deletion was dangerous: the same string
    # now names a different file. The fd-bound unlink above ignored that entirely.
    assert inner.exists(), "sanity: the swapped path should now resolve outside .agent"
    assert inner.resolve() == external.resolve()


def test_path_based_deletion_would_have_escaped(tmp_path: Path) -> None:
    """Pin the OLD behaviour, so a regression to path semantics is visible.

    This documents why the fd walk exists: the same swap against a path-based
    unlink destroys the external file.
    """
    agent, _inner, external = _fixture(tmp_path)

    (agent / "sub").rename(tmp_path / "sub-moved")
    (agent / "sub").symlink_to(external.parent, target_is_directory=True)

    os.unlink(str(agent / "sub" / "victim.txt"))  # path-based: follows the symlink

    assert not external.exists(), (
        "expected the path-based deletion to escape; if this fails the fixture no longer "
        "reproduces the original defect and the guarantee above proves nothing"
    )


def test_symlinked_component_is_refused(tmp_path: Path) -> None:
    agent, _inner, external = _fixture(tmp_path)
    (agent / "escape").symlink_to(external.parent, target_is_directory=True)

    removed, message = reaper.reap_entry(str(agent), "f", "escape/victim.txt")

    assert removed is False
    assert "escape/victim.txt" in message
    assert external.exists(), "external victim deleted through a symlinked component"


def test_symlinked_leaf_declared_as_file_is_refused(tmp_path: Path) -> None:
    agent, _inner, external = _fixture(tmp_path)
    (agent / "leafptr").symlink_to(external)

    removed, message = reaper.reap_entry(str(agent), "f", "leafptr")

    assert removed is False
    assert "symlinked leaf" in message
    assert external.exists(), "external target deleted through a symlinked leaf"
    assert (agent / "leafptr").is_symlink(), "the link itself should be left alone for kind 'f'"


def test_symlink_leaf_declared_as_link_removes_only_the_link(tmp_path: Path) -> None:
    agent, _inner, external = _fixture(tmp_path)
    (agent / "leafptr").symlink_to(external)

    removed, _message = reaper.reap_entry(str(agent), "l", "leafptr")

    assert removed is True
    assert not (agent / "leafptr").exists()
    assert external.exists(), "removing a link must never remove its target"


def test_legitimate_nested_file_is_still_reaped(tmp_path: Path) -> None:
    """A guard that refuses everything is also broken."""
    agent, inner, _external = _fixture(tmp_path)

    removed, message = reaper.reap_entry(str(agent), "f", "sub/victim.txt")

    assert removed is True, message
    assert not inner.exists()


def test_non_empty_directory_is_preserved(tmp_path: Path) -> None:
    """Runtime scratch shares directories with deployed content (#4741)."""
    agent, _inner, _external = _fixture(tmp_path)
    (agent / "sub" / "agent-written.md").write_text("live", encoding="utf-8")

    removed, _message = reaper.reap_entry(str(agent), "d", "sub")

    assert removed is False
    assert (agent / "sub" / "agent-written.md").exists()


@pytest.mark.parametrize("relative", ["../outside/victim.txt", "/etc/passwd", "a/../../b", ""])
def test_lexically_unsafe_entries_refused(relative: str) -> None:
    assert reaper.path_is_lexically_safe(relative) is False


def _open_fd_count() -> int:
    """Best-effort open-fd count; the leak assertion needs a delta, not a total."""
    return len(os.listdir("/dev/fd")) if os.path.isdir("/dev/fd") else -1


def test_missing_manifest_still_validates_the_root_first(tmp_path: Path, capsys) -> None:
    """Review P1: the root check must run BEFORE the missing-manifest early return.

    With the old ordering a first run exited 0 without ever looking at the root, and
    deploy_prompts.sh then rsynced into `.agent/` by path — so a symlinked root
    redirected deploy WRITES outside the repo.
    """
    outside = tmp_path / "outside"
    outside.mkdir()
    link_root = tmp_path / "agent-link"
    link_root.symlink_to(outside, target_is_directory=True)

    rc = reaper.main(
        [
            "--agent-root", str(link_root),
            "--manifest", str(tmp_path / "does-not-exist.manifest"),
            "--source-root", str(tmp_path / "src"),
        ]
    )

    assert rc == 1, "a symlinked root must be refused even when no manifest exists yet"
    err = capsys.readouterr().err
    assert "not a real directory" in err
    assert "preserving all existing paths during migration" not in err


def test_refused_entries_do_not_leak_directory_fds(tmp_path: Path) -> None:
    """Review P2: a corrupt manifest could exhaust the fd table and deny the reap."""
    agent, _inner, _external = _fixture(tmp_path)

    before = _open_fd_count()
    outcomes = [
        reaper.reap_entry(str(agent), "f", "NONEXISTENT_COMPONENT/victim.txt")[0]
        for _ in range(8)
    ]
    after = _open_fd_count()

    assert outcomes == [False] * 8
    if before >= 0:
        assert after - before == 0, f"leaked {after - before} fds across 8 refused entries"


def test_internal_error_is_reported_and_fails_loudly(tmp_path: Path, monkeypatch, capsys) -> None:
    """A silently-skipped reap is a false-green, so real errors must set the exit code.

    Refusals deliberately do NOT fail deploy — preserving a file we were unsure about
    is the safe outcome, and a symlink an agent legitimately left in .agent/ must not
    block every deploy.
    """
    agent, inner, _external = _fixture(tmp_path)
    manifest = tmp_path / "m.manifest"
    manifest.write_text("f\tsub/victim.txt\n", encoding="utf-8")
    src = tmp_path / "src"
    src.mkdir()

    def boom(*_args, **_kwargs):
        raise RuntimeError("synthetic internal failure")

    monkeypatch.setattr(reaper, "reap_entry", boom)
    rc = reaper.main(
        ["--agent-root", str(agent), "--manifest", str(manifest), "--source-root", str(src)]
    )

    assert rc == 1, "an internal error must not report success"
    assert "internal error" in capsys.readouterr().err
    assert inner.exists(), "the entry must be left alone when the reap errored"


def test_refused_symlinked_leaf_is_preserved_without_failing_reap(
    tmp_path: Path, capsys
) -> None:
    """A deliberate unsafe refusal preserves the entry but remains a successful reap."""
    agent, _inner, external = _fixture(tmp_path)
    (agent / "leafptr").symlink_to(external)
    manifest = tmp_path / "m.manifest"
    manifest.write_text("f\tleafptr\n", encoding="utf-8")
    source = tmp_path / "src"
    source.mkdir()

    rc = reaper.main(
        ["--agent-root", str(agent), "--manifest", str(manifest), "--source-root", str(source)]
    )

    assert rc == 0, "a deliberate unsafe refusal must not fail deploy"
    assert (agent / "leafptr").is_symlink()
    assert external.exists()
    assert "symlinked leaf declared 'f'" in capsys.readouterr().err


def test_operational_unlink_error_fails_reap_and_names_entry(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    """Unexpected filesystem failures must not be relabelled as safe refusals."""
    agent, inner, _external = _fixture(tmp_path)
    manifest = tmp_path / "m.manifest"
    manifest.write_text("f\tsub/victim.txt\n", encoding="utf-8")
    source = tmp_path / "src"
    source.mkdir()

    def fail_unlink(*_args, **_kwargs) -> None:
        raise OSError(errno.EIO, "Input/output error")

    monkeypatch.setattr(reaper.os, "unlink", fail_unlink)
    rc = reaper.main(
        ["--agent-root", str(agent), "--manifest", str(manifest), "--source-root", str(source)]
    )

    assert rc == 1, "an operational unlink failure must fail the reap"
    assert inner.exists(), "the failed unlink must leave its entry intact"
    assert "operational error reaping 'sub/victim.txt'" in capsys.readouterr().err
