#!/usr/bin/env python3
"""Fail-closed hidden-output audit for the Pages artifact (#11194).

``deploy-pages.yml`` emits ``.well-known/learn-ukrainian-deployment-<sha>.txt``
(body: the deployed commit SHA plus a newline) so a public reader can prove which
revision is live. ``actions/upload-pages-artifact`` drops every dot-named path
unless ``include-hidden-files`` is ``true``, and with that input set it would
publish *every* hidden path in the directory. This audit runs immediately before
upload and allows exactly one hidden output:

- ``<dist>/.well-known/`` — a real directory, not a symlink, whose only child is
- ``learn-ukrainian-deployment-<sha>.txt`` — a regular, non-symlink file whose
  bytes are exactly ``<sha>\\n``.

Any other dot-named file or directory at any depth fails the job before upload.
The scan follows directory symlinks, as the action's ``tar --dereference`` does,
so a hidden path reached through a visible symlink is also refused.

Usage::

    .venv/bin/python scripts/deploy/verify_pages_deployment_marker.py site/dist --sha "$GITHUB_SHA"
"""

from __future__ import annotations

import argparse
import os
import re
import stat
import sys
from collections.abc import Iterable, Sequence
from pathlib import Path

WELL_KNOWN = ".well-known"
MARKER_PREFIX = "learn-ukrainian-deployment-"
SHA_RE = re.compile(r"[0-9a-f]{40}")
MAX_REPORTED_PATHS = 20


class MarkerAuditError(Exception):
    """The artifact directory is not safe to upload with hidden files included."""


def marker_name(sha: str) -> str:
    """Return the marker file name the workflow emits for ``sha``."""
    return f"{MARKER_PREFIX}{sha}.txt"


def validate_sha(sha: str | None) -> str:
    """Return ``sha`` if it is a full lowercase 40-hex commit id, else raise."""
    if not sha:
        raise MarkerAuditError("deployment SHA is missing or empty")
    if not SHA_RE.fullmatch(sha):
        raise MarkerAuditError("deployment SHA is not a full lowercase 40-hex commit id")
    return sha


def _check_marker(dist: Path, sha: str) -> Path:
    well_known = dist / WELL_KNOWN
    try:
        well_known_stat = well_known.lstat()
    except FileNotFoundError as exc:
        raise MarkerAuditError(f"{WELL_KNOWN}/ is missing; the deployment marker was not emitted") from exc
    if stat.S_ISLNK(well_known_stat.st_mode):
        raise MarkerAuditError(f"{WELL_KNOWN} is a symlink")
    if not stat.S_ISDIR(well_known_stat.st_mode):
        raise MarkerAuditError(f"{WELL_KNOWN} is not a directory")

    expected = marker_name(sha)
    children = sorted(os.listdir(well_known))
    unexpected = [name for name in children if name != expected]
    if unexpected:
        raise MarkerAuditError(
            f"{WELL_KNOWN}/ has unexpected entries: {_format_paths(f'{WELL_KNOWN}/{name}' for name in unexpected)}"
        )
    if expected not in children:
        raise MarkerAuditError(f"{WELL_KNOWN}/{expected} is missing")

    marker = well_known / expected
    marker_stat = marker.lstat()
    if stat.S_ISLNK(marker_stat.st_mode):
        raise MarkerAuditError(f"{WELL_KNOWN}/{expected} is a symlink")
    if not stat.S_ISREG(marker_stat.st_mode):
        raise MarkerAuditError(f"{WELL_KNOWN}/{expected} is not a regular file")
    if marker.read_bytes() != f"{sha}\n".encode("ascii"):
        raise MarkerAuditError(f"{WELL_KNOWN}/{expected} body is not exactly the SHA followed by one newline")
    return marker


def find_hidden_paths(dist: Path) -> list[str]:
    """Return every dot-named path under ``dist`` except the root ``.well-known``.

    Directory symlinks are followed (with cycle protection) because the Pages
    action archives with ``tar --dereference``.
    """
    hidden: list[str] = []
    visited: set[tuple[int, int]] = set()
    pending: list[tuple[Path, str]] = [(dist, "")]
    while pending:
        directory, rel_dir = pending.pop()
        dir_stat = directory.stat()
        identity = (dir_stat.st_dev, dir_stat.st_ino)
        if identity in visited:
            continue
        visited.add(identity)
        with os.scandir(directory) as entries:
            for entry in entries:
                rel = f"{rel_dir}{entry.name}"
                if entry.name.startswith("."):
                    if rel != WELL_KNOWN:
                        hidden.append(rel)
                    continue
                if entry.is_dir(follow_symlinks=True):
                    pending.append((Path(entry.path), f"{rel}/"))
    return sorted(hidden)


def _format_paths(paths: Iterable[str]) -> str:
    items = list(paths)
    shown = ", ".join(items[:MAX_REPORTED_PATHS])
    if len(items) > MAX_REPORTED_PATHS:
        shown += f", ... and {len(items) - MAX_REPORTED_PATHS} more"
    return shown


def audit(dist: Path, sha: str | None) -> Path:
    """Verify ``dist`` is safe to upload with hidden files included; return the marker path."""
    checked_sha = validate_sha(sha)
    try:
        dist_stat = dist.lstat()
    except FileNotFoundError as exc:
        raise MarkerAuditError(f"artifact directory {dist} does not exist") from exc
    if stat.S_ISLNK(dist_stat.st_mode) or not stat.S_ISDIR(dist_stat.st_mode):
        raise MarkerAuditError(f"artifact directory {dist} is not a real directory")

    marker = _check_marker(dist, checked_sha)
    hidden = find_hidden_paths(dist)
    if hidden:
        raise MarkerAuditError(f"unexpected hidden paths would be published: {_format_paths(hidden)}")
    return marker


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Refuse a Pages artifact unless its only hidden output is the exact-SHA .well-known deployment marker."
        ),
    )
    parser.add_argument("dist", type=Path, help="Built site directory passed to upload-pages-artifact.")
    parser.add_argument("--sha", required=True, help='Deployed commit SHA, normally "$GITHUB_SHA".')
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        marker = audit(args.dist, args.sha)
    except (MarkerAuditError, OSError) as exc:
        print(f"::error title=Pages marker audit refused::{exc}", file=sys.stderr)
        return 1
    print(f"pages marker audit: {marker.relative_to(args.dist).as_posix()} is the only hidden output")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
