#!/usr/bin/env python3
"""Repo-health canary: detect (and optionally remove) self-referential /
looping ``node_modules`` symlinks that break every ``npm`` invocation.

A ``node_modules`` symlink that points at **itself** (e.g.
``learn-ukrainian/node_modules -> learn-ukrainian/node_modules``) is an
infinite symlink loop. ``npm run <script>`` assembles its child process'
``PATH`` by walking the directory tree **upward** and prepending every
ancestor ``node_modules/.bin``. Resolving the looping ancestor makes the
``spawn`` syscall return ``ELOOP`` (errno -62), so npm dies **before printing
anything** — the build fails instantly with exit 194 and an empty log, and it
looks like "Astro is broken" when Astro is fine. See the autopsy at
``docs/bug-autopsies/node-modules-eloop-symlink.md``.

The loop is never committed (``node_modules`` is gitignored) so CI cannot catch
it — only a local canary can. ``scripts/delegate.py`` then *propagates* the bad
root symlink into every dispatch worktree, multiplying it. This canary removes
the loop wherever it finds it so no session inherits a broken build.

It removes ONLY symlinks whose resolution raises ``ELOOP`` (self-referential or
circular). A valid ``node_modules`` symlink (a worktree pointing at the main
checkout's real ``node_modules``) resolves fine and is left untouched; a real
``node_modules`` directory is not a symlink and is ignored.

Usage::

    python scripts/audit/check_self_symlinks.py          # check only; exit 1 if a loop exists
    python scripts/audit/check_self_symlinks.py --fix     # remove looping links; exit 0
    python scripts/audit/check_self_symlinks.py --fix -q  # silent unless it had to fix
"""

from __future__ import annotations

import argparse
import errno
import os
import sys
from pathlib import Path


def _is_looping_symlink(path: Path) -> bool:
    """True iff ``path`` is a symlink whose resolution loops (``ELOOP``).

    A self-referential link (``X -> X``) or a circular chain (``A -> B -> A``)
    makes ``os.stat`` (which follows the link) raise ``OSError(ELOOP)``. A
    valid link to an existing target stats cleanly → False. A merely *dangling*
    link (target missing → ``ENOENT``) is a different, less-severe problem and
    is intentionally NOT removed here.
    """
    if not path.is_symlink():
        return False
    try:
        os.stat(path)  # follows the link
    except OSError as exc:
        return exc.errno == errno.ELOOP
    return False


def _candidate_symlinks(repo: Path) -> list[Path]:
    """Known ``node_modules`` locations that an upward npm PATH walk traverses.

    The repo-root and ``starlight`` links are the lethal pair for the main
    site build. ``.worktrees`` is swept (without following symlinks, so loops
    are never traversed) because delegate-provisioned worktrees mirror the root
    link.
    """
    candidates: list[Path] = [
        repo / "node_modules",
        repo / "starlight" / "node_modules",
    ]
    worktrees = repo / ".worktrees"
    if worktrees.is_dir():
        for dirpath, dirnames, filenames in os.walk(worktrees, followlinks=False):
            for name in list(dirnames):
                if name == "node_modules":
                    candidates.append(Path(dirpath) / name)
                    # Never descend into a node_modules (real or symlink).
                    dirnames.remove(name)
                elif name == ".git":
                    dirnames.remove(name)
            # A self/looping ``node_modules`` symlink fails ``is_dir()`` (ELOOP),
            # so os.walk lists it under ``filenames``, not ``dirnames``.
            for name in filenames:
                if name == "node_modules":
                    candidate = Path(dirpath) / name
                    if candidate.is_symlink():
                        candidates.append(candidate)
    return candidates


def find_looping_symlinks(repo: Path) -> list[Path]:
    """Return all looping ``node_modules`` symlinks under ``repo`` (deduped)."""
    seen: set[str] = set()
    out: list[Path] = []
    for path in _candidate_symlinks(repo):
        key = str(path)
        if key in seen:
            continue
        seen.add(key)
        if _is_looping_symlink(path):
            out.append(path)
    return out


def check_self_symlinks(repo: Path, *, fix: bool) -> tuple[bool, str]:
    """Check for looping ``node_modules`` symlinks under ``repo``.

    Returns ``(ok, message)``. ``ok`` is True when none are found, or when they
    were found and ``fix`` removed them. ``ok`` is False when loops exist and
    ``fix`` is not set (every npm build under ``repo`` is broken).
    """
    looping = find_looping_symlinks(repo)
    if not looping:
        return True, "no looping node_modules symlinks (ok)"

    rel = ", ".join(str(p.relative_to(repo)) if p.is_relative_to(repo) else str(p)
                    for p in looping)
    if not fix:
        return False, (
            f"looping node_modules symlink(s) — every `npm` build is BROKEN "
            f"(spawn ELOOP): {rel}. Re-run with --fix."
        )

    removed: list[str] = []
    for path in looping:
        try:
            path.unlink()  # removes the link itself, never a real directory
            removed.append(str(path.relative_to(repo)) if path.is_relative_to(repo) else str(path))
        except OSError as exc:
            return False, f"failed to remove looping symlink {path}: {exc}"
    return True, (
        f"removed {len(removed)} looping node_modules symlink(s) "
        f"(npm builds were broken; ELOOP): {', '.join(removed)}"
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Detect/remove self-referential node_modules symlinks that "
                    "break npm with spawn ELOOP.",
    )
    parser.add_argument(
        "--fix",
        action="store_true",
        help="remove any looping node_modules symlink found",
    )
    parser.add_argument(
        "-q",
        "--quiet",
        action="store_true",
        help="suppress the OK message (still reports a fix)",
    )
    parser.add_argument(
        "--repo",
        type=Path,
        default=Path(__file__).resolve().parents[2],
        help="repo path to check (default: this project root)",
    )
    args = parser.parse_args(argv)

    ok, message = check_self_symlinks(args.repo, fix=args.fix)
    if not ok:
        print(f"❌ {message}", file=sys.stderr)
        return 1
    if "removed" in message:
        print(f"⚠️  {message}", file=sys.stderr)
    elif not args.quiet:
        print(f"✅ {message}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
