"""Guard: tracked symlinks stay inside the repository with relative targets (#8803).

A tracked symlink's target is committed verbatim, so an absolute target leaks
the author's host layout (home directory, cloud-drive account folder) into the
public history, and a target outside the repository is dead on every other
host. Bulk data is reached through ``scripts.storage.topology.resolve_bulk_root``
instead (``docs/runbooks/storage-topology.md``).
"""

from __future__ import annotations

import posixpath
import re
import subprocess
from pathlib import Path

import pytest

pytestmark = [pytest.mark.repo_invariant, pytest.mark.repo_wide]

REPO_ROOT = Path(__file__).resolve().parents[2]
SYMLINK_MODE = "120000"
_WINDOWS_ABSOLUTE = re.compile(r"^(?:[A-Za-z]:|\\\\)")


def _git(root: Path, *args: str, stdin: bytes | None = None) -> bytes:
    return subprocess.run(
        ["git", "-C", str(root), *args],
        input=stdin,
        check=True,
        capture_output=True,
        timeout=60,
    ).stdout


def tracked_symlinks(root: Path) -> list[tuple[str, str]]:
    """Return ``(path, target)`` for every symlink entry in the git index."""
    entries: list[tuple[str, str]] = []
    for record in _git(root, "ls-files", "-s", "-z").split(b"\0"):
        if not record:
            continue
        meta, _, path = record.partition(b"\t")
        mode, object_id, _stage = meta.split(b" ")
        if mode.decode() == SYMLINK_MODE:
            entries.append((path.decode("utf-8", "surrogateescape"), object_id.decode()))
    if not entries:
        return []
    batch = "".join(f"{object_id}\n" for _path, object_id in entries).encode()
    output = _git(root, "cat-file", "--batch", stdin=batch)
    targets: list[tuple[str, str]] = []
    for path, _object_id in entries:
        header, _, output = output.partition(b"\n")
        size = int(header.split(b" ")[2])
        targets.append((path, output[:size].decode("utf-8", "surrogateescape")))
        output = output[size + 1 :]
    return targets


def symlink_violation(path: str, target: str) -> str | None:
    """Return why a tracked symlink is not allowed, or ``None`` when it is."""
    if target.startswith(("/", "~")) or _WINDOWS_ABSOLUTE.match(target):
        return "absolute target"
    resolved = posixpath.normpath(posixpath.join(posixpath.dirname(path), target))
    if resolved == ".." or resolved.startswith("../"):
        return "target outside the repository"
    return None


def _violations(root: Path) -> list[str]:
    # Report only path + reason: echoing the target would re-print the leak.
    return [
        f"{path}: {reason}"
        for path, target in tracked_symlinks(root)
        if (reason := symlink_violation(path, target)) is not None
    ]


def test_repository_has_no_escaping_or_absolute_tracked_symlinks() -> None:
    assert _violations(REPO_ROOT) == []


def test_untracked_data_links_stay_ignored() -> None:
    """Host-local links at the old paths must never be re-added by ``git add``."""
    for path in ("data/textbooks", "data/vesum"):
        result = subprocess.run(
            ["git", "-C", str(REPO_ROOT), "check-ignore", "-q", "--no-index", path],
            check=False,
            timeout=30,
        )
        assert result.returncode == 0, f"{path} is not gitignored"


@pytest.mark.parametrize(
    ("path", "target"),
    [
        ("data/textbooks", "/srv/bulk/learn-ukrainian-data/textbooks"),
        ("data/vesum", "~/bulk/vesum"),
        ("data/win", "C:\\bulk\\vesum"),
        ("data/unc", "\\\\share\\bulk"),
        ("data/up", "../../outside"),
        ("top", ".."),
    ],
)
def test_violations_are_detected(path: str, target: str) -> None:
    assert symlink_violation(path, target) is not None


@pytest.mark.parametrize(
    ("path", "target"),
    [
        ("data/link", "../scripts"),
        ("a/b/c", "../../d"),
        ("link", "same-dir-target"),
    ],
)
def test_in_repository_relative_targets_are_allowed(path: str, target: str) -> None:
    assert symlink_violation(path, target) is None


def test_guard_fails_on_a_staged_absolute_symlink(tmp_path: Path) -> None:
    """End-to-end on a scratch repository: the index scan catches bad links."""
    _git(tmp_path, "init", "-q")
    (tmp_path / "data").mkdir()
    (tmp_path / "data" / "inside").symlink_to("../README")
    (tmp_path / "data" / "absolute").symlink_to("/srv/bulk/textbooks")
    (tmp_path / "data" / "escaping").symlink_to("../../elsewhere")
    _git(tmp_path, "add", "data")

    assert sorted(_violations(tmp_path)) == [
        "data/absolute: absolute target",
        "data/escaping: target outside the repository",
    ]
