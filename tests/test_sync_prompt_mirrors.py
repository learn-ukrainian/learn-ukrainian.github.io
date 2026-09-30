"""The deploy mirror copy matches rsync -a, including anchored excludes."""

from __future__ import annotations

import os
import subprocess
from pathlib import Path

from scripts.deploy.sync_prompt_mirrors import sync_tree


def _tree(root: Path) -> dict[str, tuple[str, object]]:
    found: dict[str, tuple[str, object]] = {}
    for path in sorted(root.rglob("*")):
        relative = path.relative_to(root).as_posix()
        if path.is_symlink():
            found[relative] = ("symlink", os.readlink(path))
        elif path.is_dir():
            found[relative] = ("dir", path.stat().st_mode & 0o777)
        else:
            found[relative] = ("file", (path.read_bytes(), path.stat().st_mode & 0o777))
    return found


def test_sync_tree_matches_rsync_delete_and_anchored_excludes(tmp_path: Path) -> None:
    """Root ``*-epic`` stays, nested ``skills/drive-epic`` copies, extras delete."""
    source = tmp_path / "src"
    (source / "hooks").mkdir(parents=True)
    hook = source / "hooks" / "kept.sh"
    hook.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
    hook.chmod(0o755)
    link = source / "hooks" / "link.pyc"
    link.symlink_to("kept.sh")
    (source / "skills" / "drive-epic").mkdir(parents=True)
    (source / "skills" / "drive-epic" / "SKILL.md").write_text("skill\n", encoding="utf-8")
    (source / "skills" / "post-build-review").mkdir()
    (source / "skills" / "post-build-review" / "SKILL.md").write_text("shared\n", encoding="utf-8")
    (source / "docs").mkdir()
    (source / "docs" / "note.md").write_text("source note\n", encoding="utf-8")

    patterns = ("/*-epic", "/docs/", "/skills/post-build-review/")

    def seed(destination: Path) -> None:
        epic = destination / "hist-epic"
        epic.mkdir(parents=True)
        (epic / "HANDOFF.md").write_text("keep\n", encoding="utf-8")
        (destination / "stale.txt").write_text("gone\n", encoding="utf-8")
        kept_doc = destination / "docs"
        kept_doc.mkdir()
        (kept_doc / "local.md").write_text("local\n", encoding="utf-8")

    ours = tmp_path / "ours"
    reference = tmp_path / "rsync"
    seed(ours)
    seed(reference)
    sync_tree(source, ours, patterns, delete=True)
    command = ["rsync", "-a", "--delete", f"{source}/", f"{reference}/"]
    for pattern in patterns:
        command.extend(["--exclude", pattern])
    subprocess.run(command, check=True, timeout=30)
    assert _tree(ours) == _tree(reference)

    # A copy without --delete leaves a destination-only file in place.
    extra = ours / "stale-overlay.txt"
    extra.write_text("stay\n", encoding="utf-8")
    reference_extra = reference / "stale-overlay.txt"
    reference_extra.write_text("stay\n", encoding="utf-8")
    sync_tree(source, ours, patterns, delete=False)
    subprocess.run(
        ["rsync", "-a", f"{source}/", f"{reference}/", *(arg for pattern in patterns for arg in ("--exclude", pattern))],
        check=True,
        timeout=30,
    )
    assert extra.read_text(encoding="utf-8") == "stay\n"
    assert _tree(ours) == _tree(reference)
