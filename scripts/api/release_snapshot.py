"""Build and maintain immutable API release snapshots.

The API process runs code from ``.runtime/api/releases/<full-sha>`` while
using selected mutable data directories from the live checkout.  This module
keeps publication deliberately small and explicit so the shell launcher and
its tests share the same atomicity and pruning rules.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import subprocess
import tarfile
from collections.abc import Callable, Iterable, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from scripts.git_context import sanitized_git_env
from scripts.release_layout import (
    LIVE_DATA_PATHS,
    MANIFEST_NAME,
    RELEASE_SHA_RE,
    RELEASES_RELATIVE_PATH,
)

ARCHIVE_PATHS: tuple[str, ...] = ("scripts", "schemas")


class ReleaseSnapshotError(RuntimeError):
    """Raised when a release cannot be safely built, validated, or published."""


@dataclass(frozen=True)
class ReleaseManifest:
    """Content-addressed description of the archived code tree."""

    sha: str
    file_count: int
    tree_sha256: str

    def as_dict(self) -> dict[str, str | int]:
        return {
            "sha": self.sha,
            "file_count": self.file_count,
            "tree_sha256": self.tree_sha256,
        }


@dataclass(frozen=True)
class PruneResult:
    """Result of an ownership-aware release cleanup attempt."""

    removed: tuple[str, ...]
    kept: tuple[str, ...]
    skipped: bool = False
    reason: str | None = None


def releases_root(repo_root: Path) -> Path:
    """Return the fixed release directory under a live checkout."""
    return repo_root.resolve() / RELEASES_RELATIVE_PATH


def _validate_sha(sha: str) -> str:
    normalized = sha.strip().lower()
    if not RELEASE_SHA_RE.fullmatch(normalized):
        raise ReleaseSnapshotError("release SHA must be a full 40-character hexadecimal commit ID")
    return normalized


def _safe_archive_path(root: Path, name: str) -> Path:
    """Return a tar member destination only when it stays inside ``root``."""
    member_path = Path(name)
    if member_path.is_absolute() or ".." in member_path.parts:
        raise ReleaseSnapshotError(f"unsafe path in git archive: {name!r}")
    target = (root / member_path).resolve(strict=False)
    try:
        target.relative_to(root.resolve())
    except ValueError as exc:
        raise ReleaseSnapshotError(f"git archive path escapes staging directory: {name!r}") from exc
    return target


def _extract_archive(repo_root: Path, sha: str, staging_dir: Path) -> None:
    """Extract the selected tracked code paths into a new staging directory."""
    command = [
        "git",
        "-C",
        str(repo_root),
        "archive",
        "--format=tar",
        sha,
        *ARCHIVE_PATHS,
    ]
    process = subprocess.Popen(
        command,
        env=sanitized_git_env(),
        stderr=subprocess.PIPE,
        stdout=subprocess.PIPE,
    )
    assert process.stdout is not None
    try:
        with tarfile.open(fileobj=process.stdout, mode="r|") as archive:
            for member in archive:
                target = _safe_archive_path(staging_dir, member.name)
                if member.isdir():
                    target.mkdir(parents=True, exist_ok=True)
                    target.chmod(member.mode & 0o777)
                    continue
                if member.isreg():
                    source = archive.extractfile(member)
                    if source is None:
                        raise ReleaseSnapshotError(f"could not read archived file: {member.name}")
                    target.parent.mkdir(parents=True, exist_ok=True)
                    with source, target.open("wb") as destination:
                        shutil.copyfileobj(source, destination)
                    target.chmod(member.mode & 0o777)
                    continue
                if member.issym():
                    link_target = Path(member.linkname)
                    if link_target.is_absolute() or ".." in link_target.parts:
                        raise ReleaseSnapshotError(f"unsafe symlink in git archive: {member.name!r}")
                    target.parent.mkdir(parents=True, exist_ok=True)
                    target.symlink_to(member.linkname)
                    continue
                raise ReleaseSnapshotError(f"unsupported entry in git archive: {member.name!r}")
    finally:
        process.stdout.close()

    stderr = process.stderr.read().decode("utf-8", errors="replace") if process.stderr else ""
    if process.wait() != 0:
        raise ReleaseSnapshotError(f"git archive failed for {sha}: {stderr.strip()}")


def _archive_files(release_dir: Path) -> Iterable[Path]:
    for source_dir in ARCHIVE_PATHS:
        directory = release_dir / source_dir
        if not directory.is_dir():
            raise ReleaseSnapshotError(f"release archive is missing {source_dir}/")
        for path in sorted(directory.rglob("*")):
            if path.is_file() and not path.is_symlink():
                yield path


def _manifest_for(release_dir: Path, sha: str) -> ReleaseManifest:
    """Calculate a stable digest of archived files, names, and contents."""
    digest = hashlib.sha256()
    file_count = 0
    for path in _archive_files(release_dir):
        relative_path = path.relative_to(release_dir).as_posix().encode("utf-8")
        digest.update(relative_path)
        digest.update(b"\0")
        with path.open("rb") as handle:
            for block in iter(lambda: handle.read(1024 * 1024), b""):
                digest.update(block)
        digest.update(b"\0")
        file_count += 1
    return ReleaseManifest(sha=sha, file_count=file_count, tree_sha256=digest.hexdigest())


def _write_manifest(release_dir: Path, manifest: ReleaseManifest) -> None:
    (release_dir / MANIFEST_NAME).write_text(
        json.dumps(manifest.as_dict(), sort_keys=True, indent=2) + "\n",
        encoding="utf-8",
    )


def verify_release(release_dir: Path, sha: str | None = None) -> ReleaseManifest:
    """Verify the recorded archive manifest before reuse or publication."""
    manifest_path = release_dir / MANIFEST_NAME
    try:
        payload: dict[str, Any] = json.loads(manifest_path.read_text(encoding="utf-8"))
        recorded = ReleaseManifest(
            sha=_validate_sha(str(payload["sha"])),
            file_count=int(payload["file_count"]),
            tree_sha256=str(payload["tree_sha256"]),
        )
    except (KeyError, TypeError, ValueError, OSError, json.JSONDecodeError) as exc:
        raise ReleaseSnapshotError(f"invalid release manifest at {manifest_path}") from exc
    if sha is not None and recorded.sha != _validate_sha(sha):
        raise ReleaseSnapshotError(f"release manifest SHA does not match requested SHA: {recorded.sha}")

    calculated = _manifest_for(release_dir, recorded.sha)
    if calculated != recorded:
        raise ReleaseSnapshotError(f"release manifest verification failed for {release_dir}")
    return recorded


def _link_live_data(repo_root: Path, staging_dir: Path) -> None:
    """Link mutable runtime data from the live checkout into a snapshot."""
    for relative_name in LIVE_DATA_PATHS:
        source = repo_root / relative_name
        if not source.exists():
            raise ReleaseSnapshotError(f"live data path is missing: {source}")
        target = staging_dir / relative_name
        target.parent.mkdir(parents=True, exist_ok=True)
        if target.exists() or target.is_symlink():
            raise ReleaseSnapshotError(f"release data link collides with archived path: {relative_name}")
        target.symlink_to(source.resolve(), target_is_directory=source.is_dir())


def publish_current(releases_dir: Path, sha: str) -> Path:
    """Atomically point ``current`` at an already-verified release directory."""
    sha = _validate_sha(sha)
    release_dir = releases_dir / sha
    verify_release(release_dir, sha)
    temporary_link = releases_dir / f".current-{os.getpid()}"
    if temporary_link.exists() or temporary_link.is_symlink():
        temporary_link.unlink()
    # A relative target keeps the pointer relocatable while the replace keeps
    # readers from ever observing a missing or partially-written ``current``.
    temporary_link.symlink_to(sha, target_is_directory=True)
    os.replace(temporary_link, releases_dir / "current")
    return release_dir


def build_release(
    repo_root: Path,
    sha: str,
    *,
    before_publish: Callable[[Path], None] | None = None,
) -> tuple[Path, bool]:
    """Create or reuse an immutable snapshot and atomically publish it.

    ``before_publish`` exists for deterministic crash-boundary tests. A process
    killed at this point leaves only a staging directory; ``current`` still
    references the preceding release.

    A crash after staging is renamed but before ``current`` is swapped can
    leave an orphaned, complete release directory. It is safe: ``current``
    still references the preceding release, and the next build for the same
    SHA verifies, reuses, and publishes that complete directory.
    """
    repo_root = repo_root.resolve()
    sha = _validate_sha(sha)
    releases_dir = releases_root(repo_root)
    releases_dir.mkdir(parents=True, exist_ok=True)
    final_dir = releases_dir / sha

    if final_dir.exists():
        if not final_dir.is_dir() or final_dir.is_symlink():
            raise ReleaseSnapshotError(f"release path is not a directory: {final_dir}")
        verify_release(final_dir, sha)
        publish_current(releases_dir, sha)
        return final_dir, True

    staging_dir = releases_dir / f".staging-{os.getpid()}"
    if staging_dir.exists() or staging_dir.is_symlink():
        shutil.rmtree(staging_dir)
    staging_dir.mkdir()
    try:
        _extract_archive(repo_root, sha, staging_dir)
        manifest = _manifest_for(staging_dir, sha)
        _write_manifest(staging_dir, manifest)
        verify_release(staging_dir, sha)
        _link_live_data(repo_root, staging_dir)
        if before_publish is not None:
            before_publish(staging_dir)
        os.rename(staging_dir, final_dir)
        publish_current(releases_dir, sha)
    except Exception:
        shutil.rmtree(staging_dir, ignore_errors=True)
        raise
    return final_dir, False


def _release_directories(releases_dir: Path) -> list[Path]:
    if not releases_dir.is_dir():
        return []
    return sorted(
        (
            path
            for path in releases_dir.iterdir()
            if path.is_dir() and not path.is_symlink() and RELEASE_SHA_RE.fullmatch(path.name)
        ),
        key=lambda path: path.stat().st_mtime_ns,
        reverse=True,
    )


def _live_release_shas(
    releases_dir: Path,
    *,
    lsof_command: Sequence[str] = ("lsof", "-n", "-P", "-d", "cwd", "-Fpn"),
    runner: Callable[..., subprocess.CompletedProcess[str]] = subprocess.run,
) -> set[str] | None:
    """Return release SHAs with a live process cwd, or ``None`` if unknown.

    ``lsof`` already omits exited processes. Failing closed when it cannot be
    queried is intentional: pruning is an optimization, but deleting code used
    by a running API is a correctness failure.
    """
    try:
        result = runner(
            list(lsof_command),
            capture_output=True,
            text=True,
            check=False,
        )
    except OSError:
        return None
    if result.returncode != 0:
        return None

    root = releases_dir.resolve()
    live: set[str] = set()
    current_pid: str | None = None
    for line in result.stdout.splitlines():
        if line.startswith("p"):
            current_pid = line[1:]
            continue
        if not current_pid or not line.startswith("n"):
            continue
        cwd = Path(line[1:])
        try:
            relative = cwd.resolve().relative_to(root)
        except (OSError, ValueError):
            continue
        if relative.parts and RELEASE_SHA_RE.fullmatch(relative.parts[0]):
            live.add(relative.parts[0])
    return live


def _protected_release_shas(
    releases_dir: Path,
    *,
    keep: int,
    runner: Callable[..., subprocess.CompletedProcess[str]],
) -> set[str] | None:
    """Return the release SHAs protected at this instant, or ``None`` if unknown."""
    releases = _release_directories(releases_dir)
    live = _live_release_shas(releases_dir, runner=runner)
    if live is None:
        return None

    protected = {path.name for path in releases[:keep]} | live
    current_link = releases_dir / "current"
    if current_link.is_symlink():
        try:
            current_relative = current_link.resolve().relative_to(releases_dir.resolve())
        except (OSError, ValueError):
            current_relative = Path()
        if current_relative.parts and RELEASE_SHA_RE.fullmatch(current_relative.parts[0]):
            protected.add(current_relative.parts[0])
    return protected


def prune_releases(
    repo_root: Path,
    *,
    keep: int = 3,
    runner: Callable[..., subprocess.CompletedProcess[str]] = subprocess.run,
) -> PruneResult:
    """Remove only old, unowned releases while retaining the newest ``keep``.

    The current pointer and live process set are re-read immediately before
    every deletion. This narrows the lsof TOCTOU window, but cannot remove it:
    manual concurrent pruning or a process that changes cwd after the check can
    still race deletion. ``services.sh`` stops the old API before starting the
    replacement, which narrows the normal restart window further.
    """
    if keep < 1:
        raise ValueError("keep must be at least one")
    directory = releases_root(repo_root)
    releases = _release_directories(directory)

    removed: list[str] = []
    for release in releases:
        protected = _protected_release_shas(directory, keep=keep, runner=runner)
        if protected is None:
            return PruneResult(
                removed=tuple(removed),
                kept=tuple(path.name for path in _release_directories(directory)),
                skipped=True,
                reason="lsof unavailable",
            )
        if release.name in protected:
            continue
        shutil.rmtree(release)
        removed.append(release.name)
    return PruneResult(
        removed=tuple(removed),
        kept=tuple(path.name for path in _release_directories(directory)),
    )


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    build = subparsers.add_parser("build", help="build and publish one API release")
    build.add_argument("--repo-root", type=Path, required=True)
    build.add_argument("--sha", required=True)
    prune = subparsers.add_parser("prune", help="prune inactive API releases")
    prune.add_argument("--repo-root", type=Path, required=True)
    prune.add_argument("--keep", type=int, default=3)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    if args.command == "build":
        release_dir, _reused = build_release(args.repo_root, args.sha)
        print(release_dir)
        return 0
    result = prune_releases(args.repo_root, keep=args.keep)
    print(
        json.dumps(
            {
                "removed": list(result.removed),
                "kept": list(result.kept),
                "skipped": result.skipped,
                "reason": result.reason,
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
