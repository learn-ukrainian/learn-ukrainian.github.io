"""Neutral exact-target materialization for isolated review (issue #5285).

Materializes tracked source into a temporary snapshot *outside* the repository
with no live ``.git`` metadata. Project-controlled instructions/config land in
the snapshot only as inert file evidence and are never loaded as reviewer
configuration by this layer.

Safe local untracked (and dirty tracked) files are captured once into immutable
byte records; the mutable working tree is never reopened after validation for
overlay content. Source-state identity is recorded at capture and re-checked
against the original repository before review evidence is accepted.

Unchanged symlinks/gitlinks are represented inertly (no live links). Unchanged
binary context is copied as ordinary files. Changed symlinks/gitlinks/traversal
and unsafe changed inputs still fail closed.

A validated review bundle (patch + changed-path manifest + digests) is written
into the snapshot for the reviewer.
"""

from __future__ import annotations

import contextlib
import errno
import hashlib
import json
import os
import re
import shutil
import stat
import subprocess
import tempfile
from collections.abc import Iterable, Iterator, Mapping, Sequence
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from scripts.review.isolation import (
    ReviewIsolationError,
    is_sensitive_path,
    is_within,
    preflight_review_inputs,
    resolve_external_executable,
    safe_engine_path,
    secret_like_findings,
)

SNAPSHOT_FINGERPRINT_VERSION = "review-snapshot-v2"
BUNDLE_SCHEMA_VERSION = "review-bundle.v1"
SOURCE_STATE_VERSION = "review-source-state.v2"
INERT_LINK_MARKER = ".review-inert-link: v1"

# Specific diagnostics for denied filesystem cases.
DIAG_SYMLINK = "symlink_denied"
DIAG_GITLINK = "gitlink_denied"
DIAG_TRAVERSAL = "path_traversal_denied"
DIAG_BINARY = "binary_or_non_utf8_denied"
DIAG_DRIFT = "source_drift_invalidated"
DIAG_UNSAFE_PATH = "unsafe_path_denied"
DIAG_BUNDLE = "bundle_identity_mismatch"
DIAG_CHANGED_SECRET = "changed_secret_denied"
DIAG_BINARY_PATCH = "binary_patch_ambiguous"


def _is_git_binary_marker_line(line: bytes) -> bool:
    """True only for real Git binary-diff marker lines (not source mentioning them)."""
    stripped = line.strip()
    if stripped == b"GIT binary patch":
        return True
    return stripped.startswith(b"Binary files ") and stripped.endswith(b" differ")


def _patch_contains_binary_markers(patch_bytes: bytes) -> bool:
    return any(_is_git_binary_marker_line(line) for line in patch_bytes.splitlines())


class ReviewSnapshotError(ReviewIsolationError):
    """Neutral snapshot capture or validation failed closed."""


@dataclass(frozen=True)
class ImmutableFileRecord:
    """Validated file content that must not be re-read from the source tree."""

    rel_path: str
    content: bytes
    sha256: str
    mode: int = 0o644

    @staticmethod
    def from_bytes(rel_path: str, content: bytes, *, mode: int = 0o644) -> ImmutableFileRecord:
        return ImmutableFileRecord(
            rel_path=rel_path,
            content=content,
            sha256=hashlib.sha256(content).hexdigest(),
            mode=mode,
        )


@dataclass(frozen=True)
class InertLinkRecord:
    """Unchanged symlink/gitlink represented without a live host link."""

    rel_path: str
    kind: str  # symlink | gitlink
    target_or_oid: str
    mode: str


@dataclass(frozen=True)
class ReviewBundle:
    """Validated base→head patch + changed-path manifest inside the snapshot."""

    manifest_path: Path
    patch_path: Path
    patch_digest: str
    changed_paths: tuple[str, ...]
    base_sha: str | None
    head_sha: str
    identity: str

    def public_dict(self) -> dict[str, Any]:
        return {
            "schema_version": BUNDLE_SCHEMA_VERSION,
            "patch_digest": self.patch_digest,
            "changed_paths": list(self.changed_paths),
            "base_sha": self.base_sha,
            "head_sha": self.head_sha,
            "identity": self.identity,
        }


@dataclass(frozen=True)
class OverlayIdentityEntry:
    """One local overlay path identity for post-capture drift detection."""

    path: str
    state: str  # present | deleted | renamed_from
    sha256: str
    mode: int | None = None
    old_path: str | None = None
    status: str = ""

    def public_dict(self) -> dict[str, Any]:
        return {
            "path": self.path,
            "state": self.state,
            "sha256": self.sha256,
            "mode": self.mode,
            "old_path": self.old_path,
            "status": self.status,
        }


@dataclass(frozen=True)
class SourceStateIdentity:
    """Identity of the original repository at capture time (non-secret)."""

    version: str
    mode: str
    repo_root: str
    base_sha: str | None
    head_sha: str
    head_tree: str
    repo_head_at_capture: str
    status_digest: str
    overlay_digest: str
    identity: str
    overlay_entries: tuple[OverlayIdentityEntry, ...] = ()

    def public_dict(self) -> dict[str, Any]:
        return {
            "version": self.version,
            "mode": self.mode,
            "base_sha": self.base_sha,
            "head_sha": self.head_sha,
            "head_tree": self.head_tree,
            "repo_head_at_capture": self.repo_head_at_capture,
            "status_digest": self.status_digest,
            "overlay_digest": self.overlay_digest,
            "identity": self.identity,
            "overlay_entries": [e.public_dict() for e in self.overlay_entries],
        }


@dataclass(frozen=True)
class LocalReviewCapture:
    """Immutable local working-tree capture for sealed local-mode review."""

    dirty_tracked: tuple[ImmutableFileRecord, ...]
    untracked: tuple[ImmutableFileRecord, ...]
    deleted_paths: tuple[str, ...]
    rename_pairs: tuple[tuple[str, str], ...]
    changed_paths: tuple[str, ...]
    name_status: tuple[dict[str, str], ...]
    patch_bytes: bytes
    overlay_entries: tuple[OverlayIdentityEntry, ...]


@dataclass(frozen=True)
class ReviewSnapshot:
    """Immutable review evidence root (no live ``.git``)."""

    path: Path
    mode: str
    base_sha: str | None
    head_sha: str
    source_fingerprint: str
    changed_paths: tuple[str, ...]
    untracked_records: tuple[ImmutableFileRecord, ...] = ()
    metadata_path: Path | None = None
    patch_digest: str = ""
    source_state_id: str = ""
    bundle_identity: str = ""
    inert_links: tuple[InertLinkRecord, ...] = ()
    bundle: ReviewBundle | None = None
    source_state: SourceStateIdentity | None = None

    def read_evidence(self, rel_path: str) -> str:
        """Read UTF-8 evidence from the snapshot (never from the live tree)."""
        target = _safe_child(self.path, rel_path)
        if not target.is_file():
            raise ReviewSnapshotError(f"evidence_missing:{rel_path}")
        try:
            return target.read_text(encoding="utf-8")
        except UnicodeDecodeError as exc:
            raise ReviewSnapshotError(f"{DIAG_BINARY}:{rel_path}") from exc


@dataclass
class _SnapshotState:
    root: Path
    mode: str
    base_sha: str | None
    head_sha: str
    source_fingerprint: str
    changed_paths: tuple[str, ...]
    untracked_records: tuple[ImmutableFileRecord, ...]
    repo_root: Path
    source_state: SourceStateIdentity | None = None
    patch_digest: str = ""
    bundle_identity: str = ""
    sealed: bool = False
    cleaned: bool = False


def _safe_child(root: Path, rel_path: str) -> Path:
    if not rel_path or rel_path.startswith(("/", "\\")) or ".." in Path(rel_path).parts:
        raise ReviewSnapshotError(f"{DIAG_TRAVERSAL}:{rel_path!r}")
    if "\\" in rel_path:
        raise ReviewSnapshotError(f"{DIAG_UNSAFE_PATH}:{rel_path!r}")
    candidate = (root / rel_path).resolve(strict=False)
    if not is_within(candidate, root.resolve()):
        raise ReviewSnapshotError(f"{DIAG_TRAVERSAL}:{rel_path!r}")
    return candidate


def _git_env(repo_root: Path) -> dict[str, str]:
    env = {
        "PATH": safe_engine_path(repo_root),
        "GIT_CONFIG_GLOBAL": os.devnull,
        "GIT_CONFIG_NOSYSTEM": "1",
        "GIT_CONFIG_SYSTEM": os.devnull,
        "GIT_OPTIONAL_LOCKS": "0",
        "GIT_TERMINAL_PROMPT": "0",
        "GIT_NO_REPLACE_OBJECTS": "1",
        "LANG": "C.UTF-8",
        "LC_ALL": "C.UTF-8",
        "HOME": os.environ.get("HOME", str(Path.home())),
    }
    return env


def _run_git(
    git_bin: Path,
    args: list[str],
    *,
    cwd: Path,
    check: bool = True,
    text: bool = True,
) -> subprocess.CompletedProcess[str] | subprocess.CompletedProcess[bytes]:
    cmd = [
        str(git_bin),
        "--no-optional-locks",
        "-c",
        "core.fsmonitor=false",
        "-c",
        "core.hooksPath=/dev/null",
        "-c",
        "maintenance.auto=false",
        "-c",
        "gc.auto=0",
        "-c",
        "submodule.recurse=false",
        "-c",
        "fetch.recurseSubmodules=false",
        *args,
    ]
    result = subprocess.run(
        cmd,
        cwd=str(cwd),
        capture_output=True,
        text=text,
        env=_git_env(cwd),
        check=False,
    )
    if check and result.returncode != 0:
        detail = (
            result.stderr
            if isinstance(result.stderr, str)
            else (result.stderr or b"").decode("utf-8", errors="replace")
        )
        raise ReviewSnapshotError(f"git_failed:{' '.join(args)}:{detail.strip() or result.returncode}")
    return result


def resolve_head_identity(
    repo_root: Path,
    *,
    git_bin: Path | None = None,
    ref: str = "HEAD",
) -> str:
    """Resolve and return the full SHA for ``ref`` using trusted git."""
    git = git_bin or resolve_external_executable("git", reject_root=repo_root)
    proc = _run_git(git, ["rev-parse", "--verify", f"{ref}^{{commit}}"], cwd=repo_root)
    assert isinstance(proc.stdout, str)
    sha = proc.stdout.strip()
    if not re_full_sha(sha):
        raise ReviewSnapshotError(f"invalid_sha:{sha!r}")
    return sha


@contextlib.contextmanager
def _neutral_local_git_view(
    repo_root: Path,
    *,
    git_bin: Path,
    head_sha: str,
) -> Iterator[list[str]]:
    """Yield Git-dir/work-tree args backed by copied index and neutral config."""
    index_proc = _run_git(
        git_bin,
        ["rev-parse", "--path-format=absolute", "--git-path", "index"],
        cwd=repo_root,
    )
    common_proc = _run_git(
        git_bin,
        ["rev-parse", "--path-format=absolute", "--git-common-dir"],
        cwd=repo_root,
    )
    assert isinstance(index_proc.stdout, str)
    assert isinstance(common_proc.stdout, str)
    index_path = Path(index_proc.stdout.strip())
    common_dir = Path(common_proc.stdout.strip())
    objects_dir = common_dir / "objects"
    if not index_path.is_absolute() or not objects_dir.is_dir():
        raise ReviewSnapshotError("neutral_git_source_paths_invalid")
    index_bytes, _index_mode = _read_regular_file_stable(
        index_path.parent,
        index_path.name,
        allow_binary=True,
    )
    neutral_parent = Path(tempfile.mkdtemp(prefix="lu-review-neutral-git-"))
    neutral = neutral_parent / "git"
    try:
        _run_git(
            git_bin,
            ["init", "--bare", "--template=", str(neutral)],
            cwd=neutral_parent,
        )
        (neutral / "HEAD").write_text(f"{head_sha}\n", encoding="ascii")
        (neutral / "index").write_bytes(index_bytes)
        info = neutral / "objects" / "info"
        info.mkdir(parents=True, exist_ok=True)
        (info / "alternates").write_text(
            f"{objects_dir.resolve()}\n",
            encoding="utf-8",
        )
        yield [
            f"--git-dir={neutral}",
            f"--work-tree={repo_root}",
            "-c",
            "core.bare=false",
        ]
    finally:
        shutil.rmtree(neutral_parent, ignore_errors=True)


_FULL_SHA_RE = re.compile(r"^[0-9a-f]{40}$")


def re_full_sha(value: str) -> bool:
    return bool(_FULL_SHA_RE.fullmatch(value))


def compute_source_fingerprint(
    *,
    mode: str,
    base_sha: str | None,
    head_sha: str,
    changed_paths: tuple[str, ...],
    file_records: Mapping[str, bytes],
    patch_digest: str = "",
    source_state_id: str = "",
) -> str:
    """Deterministic fingerprint over identity + exact captured file bytes."""
    hasher = _source_fingerprint_hasher(
        mode=mode,
        base_sha=base_sha,
        head_sha=head_sha,
        changed_paths=changed_paths,
        patch_digest=patch_digest,
        source_state_id=source_state_id,
    )
    for path in sorted(file_records):
        blob = file_records[path]
        _update_fingerprint_record(hasher, path=path, size=len(blob), chunks=(blob,))
    return hasher.hexdigest()


def _source_fingerprint_hasher(
    *,
    mode: str,
    base_sha: str | None,
    head_sha: str,
    changed_paths: tuple[str, ...],
    patch_digest: str,
    source_state_id: str,
) -> Any:
    """Initialize the stable fingerprint prefix shared by memory/disk callers."""
    hasher = hashlib.sha256()
    hasher.update(SNAPSHOT_FINGERPRINT_VERSION.encode("utf-8"))
    hasher.update(b"\0")
    meta = {
        "mode": mode,
        "base_sha": base_sha or "",
        "head_sha": head_sha,
        "changed_paths": list(changed_paths),
        "patch_digest": patch_digest,
        "source_state_id": source_state_id,
    }
    hasher.update(json.dumps(meta, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8"))
    return hasher


def _update_fingerprint_record(
    hasher: Any,
    *,
    path: str,
    size: int,
    chunks: Iterable[bytes],
) -> None:
    hasher.update(b"\0path:")
    hasher.update(path.encode("utf-8"))
    hasher.update(b"\0len:")
    hasher.update(f"{size}".encode("ascii"))
    hasher.update(b"\0")
    observed = 0
    for chunk in chunks:
        observed += len(chunk)
        hasher.update(chunk)
    if observed != size:
        raise ReviewSnapshotError(
            f"fingerprint_size_mismatch:{path}:expected={size}:actual={observed}"
        )


def _fingerprint_snapshot_tree(
    root: Path,
    *,
    mode: str,
    base_sha: str | None,
    head_sha: str,
    changed_paths: tuple[str, ...],
    patch_digest: str,
    source_state_id: str,
) -> str:
    """Stream a private snapshot into the fingerprint without buffering blobs."""
    paths: list[str] = []
    for dirpath, dirnames, filenames in os.walk(root, followlinks=False):
        base = Path(dirpath)
        if base.is_symlink():
            raise ReviewSnapshotError(f"{DIAG_SYMLINK}:{base}")
        for name in dirnames:
            child = base / name
            if child.is_symlink():
                raise ReviewSnapshotError(f"{DIAG_SYMLINK}:{child}")
        for name in filenames:
            full = base / name
            if full.is_symlink():
                raise ReviewSnapshotError(f"{DIAG_SYMLINK}:{full}")
            rel = full.relative_to(root).as_posix()
            if rel != ".review-snapshot-metadata.json":
                paths.append(rel)

    hasher = _source_fingerprint_hasher(
        mode=mode,
        base_sha=base_sha,
        head_sha=head_sha,
        changed_paths=changed_paths,
        patch_digest=patch_digest,
        source_state_id=source_state_id,
    )
    for rel in sorted(paths):
        full = root / rel
        before = full.stat()
        if not stat.S_ISREG(before.st_mode):
            raise ReviewSnapshotError(f"fingerprint_non_regular:{rel}")

        def _chunks(path: Path = full) -> Iterator[bytes]:
            with path.open("rb") as handle:
                while chunk := handle.read(1024 * 1024):
                    yield chunk

        _update_fingerprint_record(
            hasher,
            path=rel,
            size=before.st_size,
            chunks=_chunks(),
        )
        after = full.stat()
        if (
            before.st_dev,
            before.st_ino,
            before.st_size,
            before.st_mtime_ns,
            before.st_ctime_ns,
        ) != (
            after.st_dev,
            after.st_ino,
            after.st_size,
            after.st_mtime_ns,
            after.st_ctime_ns,
        ):
            raise ReviewSnapshotError(f"{DIAG_DRIFT}:fingerprint_read_race:{rel}")
    return hasher.hexdigest()


def _read_regular_file_stable(
    repo_root: Path,
    rel_path: str,
    *,
    allow_binary: bool = False,
) -> tuple[bytes, int]:
    """Read through root-anchored no-follow descriptors and return bytes/mode."""
    rel = _validate_rel_path(rel_path)
    nofollow = getattr(os, "O_NOFOLLOW", 0)
    directory = getattr(os, "O_DIRECTORY", 0)
    cloexec = getattr(os, "O_CLOEXEC", 0)
    if not nofollow or not directory:
        raise ReviewSnapshotError("stable_read_no_nofollow_support")
    root_fd = -1
    current_fd = -1
    file_fd = -1
    try:
        root_fd = os.open(
            str(repo_root),
            os.O_RDONLY | nofollow | directory | cloexec,
        )
        current_fd = root_fd
        parts = Path(rel).parts
        for component in parts[:-1]:
            next_fd = os.open(
                component,
                os.O_RDONLY | nofollow | directory | cloexec,
                dir_fd=current_fd,
            )
            if current_fd != root_fd:
                os.close(current_fd)
            current_fd = next_fd
        file_fd = os.open(
            parts[-1],
            os.O_RDONLY | nofollow | cloexec,
            dir_fd=current_fd,
        )
        before = os.fstat(file_fd)
        if not stat.S_ISREG(before.st_mode):
            raise ReviewSnapshotError(f"non_regular_file:{rel}")
        chunks: list[bytes] = []
        while True:
            chunk = os.read(file_fd, 1024 * 1024)
            if not chunk:
                break
            chunks.append(chunk)
        after = os.fstat(file_fd)
        identity_before = (
            before.st_dev,
            before.st_ino,
            stat.S_IFMT(before.st_mode),
            before.st_size,
            before.st_mtime_ns,
            before.st_ctime_ns,
        )
        identity_after = (
            after.st_dev,
            after.st_ino,
            stat.S_IFMT(after.st_mode),
            after.st_size,
            after.st_mtime_ns,
            after.st_ctime_ns,
        )
        if identity_before != identity_after:
            raise ReviewSnapshotError(f"{DIAG_DRIFT}:overlay_read_race:{rel}")
        data = b"".join(chunks)
        if len(data) != before.st_size:
            raise ReviewSnapshotError(f"{DIAG_DRIFT}:overlay_read_size:{rel}")
        mode = int(before.st_mode & 0o777)
    except ReviewSnapshotError:
        raise
    except OSError as exc:
        diagnostic = DIAG_SYMLINK if exc.errno in {errno.ELOOP, errno.ENOTDIR} else "read_failed"
        raise ReviewSnapshotError(f"{diagnostic}:{rel}:{exc}") from exc
    finally:
        if file_fd >= 0:
            os.close(file_fd)
        if current_fd >= 0 and current_fd != root_fd:
            os.close(current_fd)
        if root_fd >= 0:
            os.close(root_fd)
    if not allow_binary:
        if b"\x00" in data:
            raise ReviewSnapshotError(f"{DIAG_BINARY}:{rel}")
        try:
            data.decode("utf-8")
        except UnicodeDecodeError as exc:
            raise ReviewSnapshotError(f"{DIAG_BINARY}:{rel}") from exc
    return data, mode


def capture_untracked_records(
    repo_root: Path,
    rel_paths: Iterable[str],
) -> tuple[ImmutableFileRecord, ...]:
    """Validate and immutably capture untracked paths (never reopened later)."""
    records: list[ImmutableFileRecord] = []
    root = repo_root.resolve()
    texts: dict[str, str] = {}
    for rel in rel_paths:
        if not rel or ".." in Path(rel).parts or rel.startswith(("/", "\\")):
            raise ReviewSnapshotError(f"{DIAG_TRAVERSAL}:{rel!r}")
        data, mode = _read_regular_file_stable(root, rel, allow_binary=False)
        rec = ImmutableFileRecord.from_bytes(rel, data, mode=mode)
        records.append(rec)
        texts[rel] = data.decode("utf-8")
    preflight_review_inputs(paths=[r.rel_path for r in records], texts=texts)
    return tuple(records)


def _list_tree_entries(
    git_bin: Path,
    repo_root: Path,
    treeish: str,
) -> list[tuple[str, str, str, str]]:
    """Return exact ``(mode, type, oid, path)`` entries for ``treeish``."""
    proc = _run_git(
        git_bin,
        ["ls-tree", "-r", "-z", "--full-tree", treeish],
        cwd=repo_root,
    )
    assert isinstance(proc.stdout, str)
    entries: list[tuple[str, str, str, str]] = []
    seen: set[str] = set()
    for raw in proc.stdout.split("\0"):
        if not raw:
            continue
        try:
            meta, path = raw.split("\t", 1)
            mode, obj_type, oid = meta.split(" ", 2)
        except ValueError as exc:
            raise ReviewSnapshotError(f"malformed_ls_tree:{raw!r}") from exc
        path = _validate_rel_path(path)
        if path in seen:
            raise ReviewSnapshotError(f"duplicate_ls_tree_path:{path}")
        if not re_full_sha(oid):
            raise ReviewSnapshotError(f"malformed_ls_tree_oid:{path}:{oid!r}")
        seen.add(path)
        entries.append((mode, obj_type, oid, path))
    return entries


def _validate_rel_path(name: str) -> str:
    if not name or name.startswith(("/", "\\")) or ".." in Path(name).parts:
        raise ReviewSnapshotError(f"{DIAG_TRAVERSAL}:{name!r}")
    if "\\" in name or name.startswith("./"):
        # normalize ./foo
        name = name[2:] if name.startswith("./") else name
        if "\\" in name or ".." in Path(name).parts:
            raise ReviewSnapshotError(f"{DIAG_UNSAFE_PATH}:{name!r}")
    return name


def _inert_link_bytes(kind: str, target_or_oid: str, mode: str) -> bytes:
    payload = (
        f"{INERT_LINK_MARKER}\n"
        f"type: {kind}\n"
        f"mode: {mode}\n"
        f"target: {target_or_oid}\n"
        f"note: inert metadata only — not a live filesystem link\n"
    )
    return payload.encode("utf-8")


def _read_batch_header(stream: Any, *, expected_oid: str) -> int:
    """Parse one interactive ``git cat-file --batch`` header."""
    raw = stream.readline()
    if not raw:
        raise ReviewSnapshotError(f"cat_file_batch_header_missing:{expected_oid}")
    try:
        oid_raw, obj_type_raw, size_raw = raw.rstrip(b"\n").split(b" ", 2)
        actual_oid = oid_raw.decode("ascii")
        obj_type = obj_type_raw.decode("ascii")
        size = int(size_raw)
    except (ValueError, UnicodeDecodeError) as exc:
        raise ReviewSnapshotError(f"cat_file_batch_header_malformed:{expected_oid}") from exc
    if actual_oid != expected_oid or obj_type != "blob" or size < 0:
        raise ReviewSnapshotError(
            f"cat_file_batch_identity:{expected_oid}:{actual_oid}:{obj_type}:{size}"
        )
    return size


def _write_all(fd: int, data: bytes) -> None:
    view = memoryview(data)
    while view:
        written = os.write(fd, view)
        if written <= 0:
            raise ReviewSnapshotError("cat_file_batch_disk_write_failed")
        view = view[written:]


def _stream_batch_body(stream: Any, *, size: int, destination_fd: int) -> None:
    """Copy one exact batch body to disk with bounded memory."""
    remaining = size
    while remaining:
        chunk = stream.read(min(1024 * 1024, remaining))
        if not chunk:
            raise ReviewSnapshotError("cat_file_batch_body_truncated")
        _write_all(destination_fd, chunk)
        remaining -= len(chunk)
    if stream.read(1) != b"\n":
        raise ReviewSnapshotError("cat_file_batch_body_malformed")


def _read_small_batch_body(stream: Any, *, size: int, path: str) -> bytes:
    """Read bounded symlink metadata from a batch stream."""
    if size > 1024 * 1024:
        raise ReviewSnapshotError(f"{DIAG_UNSAFE_PATH}:{path}:link_target_too_large")
    data = stream.read(size)
    if len(data) != size or stream.read(1) != b"\n":
        raise ReviewSnapshotError(f"cat_file_batch_body_malformed:{path}")
    return data


def _materialize_tree_from_blobs(
    git_bin: Path,
    repo_root: Path,
    treeish: str,
    dest: Path,
    *,
    changed_paths: set[str],
) -> tuple[InertLinkRecord, ...]:
    """Materialize exact ``ls-tree`` blob OIDs without archive attributes.

    Unchanged symlinks/gitlinks become inert regular-file metadata.
    Changed specials fail closed. Unchanged binaries are copied as-is.
    Reading blobs by OID avoids repository-controlled ``export-ignore`` and
    ``export-subst`` transformations and preserves leading-dot paths exactly.
    """
    entries = _list_tree_entries(git_bin, repo_root, treeish)
    inert: list[InertLinkRecord] = []
    for mode, obj_type, _oid, path in entries:
        is_changed = path in changed_paths
        if is_changed and (obj_type == "commit" or mode == "160000"):
            raise ReviewSnapshotError(f"{DIAG_GITLINK}:{path}")
        if is_changed and (obj_type == "symlink" or mode == "120000"):
            raise ReviewSnapshotError(f"{DIAG_SYMLINK}:{path}")
        if not (
            obj_type == "commit"
            or mode == "160000"
            or (obj_type == "blob" and mode in {"100644", "100755", "120000"})
        ):
            raise ReviewSnapshotError(f"unsupported_tree_entry:{path}:mode={mode}:type={obj_type}")

    command = [
        str(git_bin),
        "--no-optional-locks",
        "-c",
        "core.fsmonitor=false",
        "cat-file",
        "--batch",
    ]
    proc = subprocess.Popen(
        command,
        cwd=str(repo_root),
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        env=_git_env(repo_root),
    )
    assert proc.stdin is not None
    assert proc.stdout is not None
    assert proc.stderr is not None
    try:
        for mode, obj_type, oid, path in entries:
            target = _safe_child(dest, path)
            target.parent.mkdir(parents=True, exist_ok=True)
            if obj_type == "commit" or mode == "160000":
                data = _inert_link_bytes("gitlink", oid, "160000")
                target.write_bytes(data)
                inert.append(
                    InertLinkRecord(
                        rel_path=path,
                        kind="gitlink",
                        target_or_oid=oid,
                        mode="160000",
                    )
                )
            else:
                proc.stdin.write(oid.encode("ascii") + b"\n")
                proc.stdin.flush()
                size = _read_batch_header(proc.stdout, expected_oid=oid)
                if mode == "120000":
                    raw_target = _read_small_batch_body(proc.stdout, size=size, path=path)
                    try:
                        link_target = raw_target.decode("utf-8", errors="strict")
                    except UnicodeDecodeError as exc:
                        raise ReviewSnapshotError(f"{DIAG_UNSAFE_PATH}:{path}") from exc
                    if "\0" in link_target or "\n" in link_target:
                        raise ReviewSnapshotError(f"{DIAG_UNSAFE_PATH}:{path}")
                    data = _inert_link_bytes("symlink", link_target, "120000")
                    target.write_bytes(data)
                    inert.append(
                        InertLinkRecord(
                            rel_path=path,
                            kind="symlink",
                            target_or_oid=link_target,
                            mode="120000",
                        )
                    )
                else:
                    fd = os.open(
                        target,
                        os.O_WRONLY
                        | os.O_CREAT
                        | os.O_EXCL
                        | getattr(os, "O_NOFOLLOW", 0),
                        0o400,
                    )
                    try:
                        _stream_batch_body(proc.stdout, size=size, destination_fd=fd)
                    finally:
                        os.close(fd)
                    if target.stat().st_size != size:
                        raise ReviewSnapshotError(f"tree_blob_integrity_failed:{path}:{oid}")
                    if path in changed_paths:
                        data = target.read_bytes()
                        if is_sensitive_path(path):
                            raise ReviewSnapshotError(f"sensitive_path:{path}")
                        if b"\x00" in data:
                            raise ReviewSnapshotError(f"{DIAG_BINARY}:{path}")
                        try:
                            text = data.decode("utf-8", errors="strict")
                        except UnicodeDecodeError as exc:
                            raise ReviewSnapshotError(f"{DIAG_BINARY}:{path}") from exc
                        hits = secret_like_findings(text)
                        if hits:
                            raise ReviewSnapshotError(
                                f"{DIAG_CHANGED_SECRET}:{path}:{','.join(hits)}"
                            )
            target.chmod(0o444)
        proc.stdin.close()
        returncode = proc.wait()
        detail = proc.stderr.read().decode("utf-8", errors="replace").strip()
        if returncode != 0:
            raise ReviewSnapshotError(
                f"git_cat_file_batch_failed:{detail or returncode}"
            )
        if proc.stdout.read(1):
            raise ReviewSnapshotError("cat_file_batch_trailing_bytes")
    except BaseException:
        with contextlib.suppress(OSError, ProcessLookupError):
            proc.kill()
        with contextlib.suppress(OSError):
            proc.wait(timeout=5)
        raise

    return tuple(inert)


def _write_records(dest: Path, records: Iterable[ImmutableFileRecord]) -> dict[str, bytes]:
    written: dict[str, bytes] = {}
    for rec in records:
        target = _safe_child(dest, rec.rel_path)
        # Overlays may replace already-extracted read-only archive members.
        if target.exists():
            if target.is_dir() and not target.is_symlink():
                try:
                    target.rmdir()
                except OSError as exc:
                    raise ReviewSnapshotError(
                        f"overlay_directory_not_empty:{rec.rel_path}"
                    ) from exc
            else:
                target.chmod(0o644)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(rec.content)
        target.chmod(0o444)
        on_disk = target.read_bytes()
        if hashlib.sha256(on_disk).hexdigest() != rec.sha256:
            raise ReviewSnapshotError(f"record_integrity_failed:{rec.rel_path}")
        written[rec.rel_path] = rec.content
    return written


def _capture_deleted_records(
    git_bin: Path,
    repo_root: Path,
    *,
    revision: str,
    paths: Iterable[str],
) -> tuple[ImmutableFileRecord, ...]:
    """Capture old-side regular-file bytes for deletion evidence."""
    records: list[ImmutableFileRecord] = []
    for rel_path in sorted(set(paths)):
        path = _validate_rel_path(rel_path)
        tree = _run_git(
            git_bin,
            ["ls-tree", "-z", revision, "--", path],
            cwd=repo_root,
            text=False,
            check=False,
        )
        if tree.returncode != 0 or not tree.stdout:
            raise ReviewSnapshotError(f"deleted_evidence_missing:{path}")
        assert isinstance(tree.stdout, (bytes, bytearray))
        header, separator, listed_path = bytes(tree.stdout).rstrip(b"\0").partition(b"\t")
        fields = header.split()
        if not separator or len(fields) != 3 or listed_path.decode("utf-8", errors="strict") != path:
            raise ReviewSnapshotError(f"deleted_evidence_malformed:{path}")
        mode_raw, object_type, _oid = fields
        if mode_raw == b"120000":
            raise ReviewSnapshotError(f"{DIAG_SYMLINK}:{path}")
        if mode_raw == b"160000":
            raise ReviewSnapshotError(f"{DIAG_GITLINK}:{path}")
        if object_type != b"blob" or mode_raw not in {b"100644", b"100755"}:
            raise ReviewSnapshotError(
                f"deleted_evidence_unsupported:{path}:mode={mode_raw.decode(errors='replace')}"
            )
        blob = _run_git(
            git_bin,
            ["cat-file", "-p", f"{revision}:{path}"],
            cwd=repo_root,
            text=False,
            check=False,
        )
        if blob.returncode != 0 or not isinstance(blob.stdout, (bytes, bytearray)):
            raise ReviewSnapshotError(f"deleted_evidence_missing:{path}")
        content = bytes(blob.stdout)
        if b"\0" in content:
            raise ReviewSnapshotError(f"{DIAG_BINARY}:{path}")
        try:
            text = content.decode("utf-8", errors="strict")
        except UnicodeDecodeError as exc:
            raise ReviewSnapshotError(f"{DIAG_BINARY}:{path}") from exc
        if is_sensitive_path(path):
            raise ReviewSnapshotError(f"sensitive_path:{path}")
        hits = secret_like_findings(text)
        if hits:
            raise ReviewSnapshotError(
                f"{DIAG_CHANGED_SECRET}:{path}:{','.join(hits)}"
            )
        records.append(
            ImmutableFileRecord.from_bytes(
                path,
                content,
                mode=0o755 if mode_raw == b"100755" else 0o644,
            )
        )
    return tuple(records)


def _set_tree_read_only(root: Path) -> None:
    for dirpath, dirnames, filenames in os.walk(root, followlinks=False):
        base = Path(dirpath)
        for name in dirnames:
            p = base / name
            if p.is_symlink():
                raise ReviewSnapshotError(f"{DIAG_SYMLINK}:{p}")
            p.chmod(p.stat().st_mode & ~stat.S_IWUSR & ~stat.S_IWGRP & ~stat.S_IWOTH)
        for name in filenames:
            p = base / name
            if p.is_symlink():
                raise ReviewSnapshotError(f"{DIAG_SYMLINK}:{p}")
            p.chmod(0o444)
    root.chmod(root.stat().st_mode & ~stat.S_IWUSR & ~stat.S_IWGRP & ~stat.S_IWOTH)


def _set_tree_writable(root: Path) -> None:
    if not root.exists():
        return
    for dirpath, dirnames, filenames in os.walk(root, followlinks=False):
        base = Path(dirpath)
        for name in [*dirnames, *filenames]:
            p = base / name
            try:
                if p.is_symlink():
                    continue
                mode = p.stat().st_mode
                p.chmod(mode | stat.S_IWUSR)
            except OSError:
                continue
    with contextlib.suppress(OSError):
        root.chmod(root.stat().st_mode | stat.S_IWUSR)


def derive_changed_paths_and_patch(
    repo_root: Path,
    *,
    base_sha: str,
    head_sha: str,
    git_bin: Path | None = None,
) -> tuple[tuple[str, ...], bytes, list[dict[str, str]]]:
    """Exact base→head changed paths + full patch (no truncation).

    Returns ``(changed_paths, patch_bytes, name_status_entries)``.
    Fail-closed on renames with traversal, changed symlinks/gitlinks, and
    ambiguous binary patches that cannot be validated.
    """
    root = repo_root.resolve()
    git = git_bin or resolve_external_executable("git", reject_root=root)
    if not re_full_sha(base_sha) or not re_full_sha(head_sha):
        raise ReviewSnapshotError("invalid_sha_for_diff")

    # Raw name-status with renames (null-separated).
    ns = _run_git(
        git,
        ["diff", "--name-status", "-z", "--find-renames", base_sha, head_sha],
        cwd=root,
    )
    assert isinstance(ns.stdout, str)
    entries: list[dict[str, str]] = []
    paths: list[str] = []
    tokens = [t for t in ns.stdout.split("\0") if t]
    i = 0
    while i < len(tokens):
        status = tokens[i]
        i += 1
        if not status:
            continue
        code = status[0]
        if code in {"R", "C"}:
            if i + 1 >= len(tokens):
                raise ReviewSnapshotError("malformed_name_status_rename")
            old_p = _validate_rel_path(tokens[i])
            new_p = _validate_rel_path(tokens[i + 1])
            i += 2
            entries.append({"status": status, "old_path": old_p, "path": new_p, "kind": "rename"})
            paths.extend([old_p, new_p])
        else:
            if i >= len(tokens):
                raise ReviewSnapshotError("malformed_name_status")
            p = _validate_rel_path(tokens[i])
            i += 1
            entries.append({"status": status, "path": p, "kind": "path"})
            paths.append(p)

    # Detect changed specials via raw diff.
    raw = _run_git(
        git,
        ["diff", "--raw", "-z", "--find-renames", base_sha, head_sha],
        cwd=root,
    )
    assert isinstance(raw.stdout, str)
    raw_tokens = [t for t in raw.stdout.split("\0") if t]
    # format: :oldmode newmode oldoid newoid status\0path[\0path2]
    j = 0
    while j < len(raw_tokens):
        meta = raw_tokens[j]
        j += 1
        if not meta.startswith(":"):
            continue
        parts = meta[1:].split()
        if len(parts) < 5:
            continue
        old_mode, new_mode = parts[0], parts[1]
        status = parts[4]
        path1 = _validate_rel_path(raw_tokens[j]) if j < len(raw_tokens) else ""
        j += 1
        path2 = ""
        if status[0] in {"R", "C"} and j < len(raw_tokens):
            path2 = _validate_rel_path(raw_tokens[j])
            j += 1
        for mode in (old_mode, new_mode):
            if mode == "120000":
                raise ReviewSnapshotError(f"{DIAG_SYMLINK}:{path2 or path1}")
            if mode == "160000":
                raise ReviewSnapshotError(f"{DIAG_GITLINK}:{path2 or path1}")

    # Full patch including binary markers (no truncation).
    patch_proc = _run_git(
        git,
        ["diff", "--binary", "--find-renames", "--no-ext-diff", "--no-textconv", base_sha, head_sha],
        cwd=root,
        text=False,
    )
    assert isinstance(patch_proc.stdout, (bytes, bytearray))
    patch_bytes = bytes(patch_proc.stdout)

    preflight_paths = list(dict.fromkeys(paths))
    for p in preflight_paths:
        if is_sensitive_path(p):
            raise ReviewSnapshotError(f"sensitive_path:{p}")

    # Scan full changed content per path (no truncation) + full patch sections.
    _preflight_changed_contents(
        git,
        root,
        base_sha=base_sha,
        head_sha=head_sha,
        paths=preflight_paths,
        entries=entries,
        patch_bytes=patch_bytes,
    )

    # Ambiguous binary patches: refuse when there is patch body but no paths.
    if not preflight_paths and patch_bytes.strip():
        raise ReviewSnapshotError(f"{DIAG_BINARY_PATCH}:paths_empty_with_patch")

    return tuple(dict.fromkeys(preflight_paths)), patch_bytes, entries


def _preflight_changed_contents(
    git_bin: Path,
    repo_root: Path,
    *,
    base_sha: str,
    head_sha: str,
    paths: Sequence[str],
    entries: list[dict[str, str]],
    patch_bytes: bytes,
) -> None:
    """Fail closed on secret-like material in changed names/content/patch.

    Scans every changed path's full blob(s) and the complete patch without
    truncation or path-based exemptions. Secrets are denied in tests/,
    fixtures, docs, examples, and production paths alike.
    """
    deleted: set[str] = set()
    for entry in entries:
        status = entry.get("status", "")
        if status.startswith("D"):
            deleted.add(entry.get("path", ""))

    for path in paths:
        if not path:
            continue
        # Prefer head blob; fall back to base for pure deletions.
        blob: bytes | None = None
        for rev in (head_sha, base_sha):
            if path in deleted and rev == head_sha:
                continue
            proc = _run_git(
                git_bin,
                ["cat-file", "-e", f"{rev}:{path}"],
                cwd=repo_root,
                check=False,
            )
            if proc.returncode != 0:
                continue
            show = _run_git(
                git_bin,
                ["cat-file", "-p", f"{rev}:{path}"],
                cwd=repo_root,
                text=False,
                check=False,
            )
            if show.returncode == 0 and isinstance(show.stdout, (bytes, bytearray)):
                blob = bytes(show.stdout)
                break
        if blob is None:
            continue
        # Changed/added/renamed binary or non-UTF-8 content cannot be secret-scanned safely.
        if b"\x00" in blob:
            raise ReviewSnapshotError(f"{DIAG_BINARY}:{path}")
        try:
            text = blob.decode("utf-8")
        except UnicodeDecodeError as exc:
            raise ReviewSnapshotError(f"{DIAG_BINARY}:{path}") from exc
        hits = secret_like_findings(text)
        if hits:
            raise ReviewSnapshotError(f"{DIAG_CHANGED_SECRET}:{path}:{','.join(hits)}")

    # Full patch scan without truncation or path-based exemptions.
    # Ambiguous Git binary patches are fail-closed (cannot validate secret semantics).
    if _patch_contains_binary_markers(patch_bytes):
        raise ReviewSnapshotError(f"{DIAG_BINARY_PATCH}:changed_binary_patch")
    try:
        patch_text = patch_bytes.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise ReviewSnapshotError(f"{DIAG_BINARY_PATCH}:non_utf8_patch") from exc
    current_path: str | None = None
    section: list[str] = []

    def _flush() -> None:
        nonlocal section, current_path
        if current_path is None:
            section = []
            return
        body = "\n".join(section)
        section = []
        hits = secret_like_findings(body)
        if hits:
            raise ReviewSnapshotError(f"{DIAG_CHANGED_SECRET}:patch:{current_path}:{','.join(hits)}")

    for line in patch_text.splitlines():
        if line.startswith("diff --git "):
            _flush()
            # diff --git a/foo b/bar
            parts = line.split()
            current_path = None
            if len(parts) >= 4:
                right = parts[3]
                if right.startswith("b/"):
                    current_path = right[2:]
            section = [line]
            continue
        section.append(line)
    _flush()


def _overlay_entries_digest(entries: Sequence[OverlayIdentityEntry]) -> str:
    hasher = hashlib.sha256()
    for entry in sorted(entries, key=lambda e: (e.path, e.state, e.old_path or "")):
        payload = entry.public_dict()
        hasher.update(json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8"))
        hasher.update(b"\0")
    return hasher.hexdigest()


def capture_source_state_identity(
    repo_root: Path,
    *,
    mode: str,
    base_sha: str | None,
    head_sha: str,
    git_bin: Path | None = None,
    overlay_records: Sequence[ImmutableFileRecord] = (),
    overlay_entries: Sequence[OverlayIdentityEntry] = (),
) -> SourceStateIdentity:
    """Record original-repo identity at capture for post-review drift checks."""
    root = repo_root.resolve()
    git = git_bin or resolve_external_executable("git", reject_root=root)
    head_tree_proc = _run_git(git, ["rev-parse", f"{head_sha}^{{tree}}"], cwd=root)
    assert isinstance(head_tree_proc.stdout, str)
    head_tree = head_tree_proc.stdout.strip()
    bare_proc = _run_git(git, ["rev-parse", "--is-bare-repository"], cwd=root)
    assert isinstance(bare_proc.stdout, str)
    is_bare = bare_proc.stdout.strip() == "true"
    if mode == "local" or not is_bare:
        repo_head_proc = _run_git(git, ["rev-parse", "HEAD"], cwd=root)
        assert isinstance(repo_head_proc.stdout, str)
        repo_head = repo_head_proc.stdout.strip()
        if mode == "local" and repo_head != head_sha:
            raise ReviewSnapshotError(f"{DIAG_DRIFT}:local_head_at_capture:expected={head_sha}:actual={repo_head}")
        if mode == "local":
            with _neutral_local_git_view(root, git_bin=git, head_sha=head_sha) as neutral_git:
                status_proc = _run_git(
                    git,
                    [*neutral_git, "status", "--porcelain", "--untracked-files=all", "-z"],
                    cwd=root,
                )
        else:
            status_proc = _run_git(
                git,
                ["status", "--porcelain", "--untracked-files=all", "-z"],
                cwd=root,
            )
        assert isinstance(status_proc.stdout, str)
        status_text = status_proc.stdout
    else:
        if overlay_records or overlay_entries:
            raise ReviewSnapshotError(f"{DIAG_DRIFT}:remote_overlay_forbidden")
        # Remote reviews use a private bare object repository. Its exact
        # commit/tree identity is authoritative; there is intentionally no
        # working-tree status surface to inspect or race.
        repo_head = head_sha
        status_text = ""
    status_digest = hashlib.sha256(status_text.encode("utf-8")).hexdigest()
    entries = list(overlay_entries)
    if not entries and overlay_records:
        for rec in overlay_records:
            entries.append(
                OverlayIdentityEntry(
                    path=rec.rel_path,
                    state="present",
                    sha256=rec.sha256,
                    mode=rec.mode,
                    status="overlay",
                )
            )
    overlay_digest = _overlay_entries_digest(entries)
    payload = {
        "version": SOURCE_STATE_VERSION,
        "mode": mode,
        "repo_root": str(root),
        "base_sha": base_sha or "",
        "head_sha": head_sha,
        "head_tree": head_tree,
        "repo_head_at_capture": repo_head,
        "status_digest": status_digest,
        "overlay_digest": overlay_digest,
        "overlay_entries": [e.public_dict() for e in entries],
    }
    identity = hashlib.sha256(json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()
    return SourceStateIdentity(
        version=SOURCE_STATE_VERSION,
        mode=mode,
        repo_root=str(root),
        base_sha=base_sha,
        head_sha=head_sha,
        head_tree=head_tree,
        repo_head_at_capture=repo_head,
        status_digest=status_digest,
        overlay_digest=overlay_digest,
        identity=identity,
        overlay_entries=tuple(entries),
    )


def _live_path_digest(repo_root: Path, rel_path: str) -> tuple[str, int]:
    """Read a live path once for drift compare; fail closed on specials."""
    try:
        data, mode = _read_regular_file_stable(
            repo_root,
            rel_path,
            allow_binary=True,
        )
    except ReviewSnapshotError as exc:
        raise ReviewSnapshotError(f"{DIAG_DRIFT}:overlay_read:{rel_path}:{exc}") from exc
    return hashlib.sha256(data).hexdigest(), mode


def verify_source_state_identity(
    identity: SourceStateIdentity,
    *,
    git_bin: Path | None = None,
) -> None:
    """Fail if the original repository has drifted since capture.

    Compares immutable Git identity, porcelain status, and every captured
    overlay entry's live content/mode/path/deletion/rename state. Content
    drift is detected even when porcelain status text is unchanged.
    """
    root = Path(identity.repo_root)
    if not root.is_dir():
        raise ReviewSnapshotError(f"{DIAG_DRIFT}:repo_missing")
    git = git_bin or resolve_external_executable("git", reject_root=root)
    current = capture_source_state_identity(
        root,
        mode=identity.mode,
        base_sha=identity.base_sha,
        head_sha=identity.head_sha,
        git_bin=git,
        overlay_entries=identity.overlay_entries,
    )
    if current.head_tree != identity.head_tree:
        raise ReviewSnapshotError(f"{DIAG_DRIFT}:head_tree:expected={identity.head_tree}:actual={current.head_tree}")
    if current.repo_head_at_capture != identity.repo_head_at_capture:
        raise ReviewSnapshotError(
            f"{DIAG_DRIFT}:repo_head:expected={identity.repo_head_at_capture}:actual={current.repo_head_at_capture}"
        )
    if current.status_digest != identity.status_digest:
        raise ReviewSnapshotError(
            f"{DIAG_DRIFT}:working_tree_status:expected={identity.status_digest}:actual={current.status_digest}"
        )
    if current.base_sha != identity.base_sha or current.head_sha != identity.head_sha:
        raise ReviewSnapshotError(f"{DIAG_DRIFT}:target_mismatch")

    # Re-read live overlay bytes/modes; never trust capture-time digest alone.
    present_entries = tuple(entry for entry in identity.overlay_entries if entry.state == "present")

    def _captured_replacement(path: Path, rel_path: str) -> bool:
        """Allow a tracked deletion replaced by captured file/descendant bytes."""
        if path.is_symlink():
            return False
        if path.is_file():
            return any(entry.path == rel_path for entry in present_entries)
        if path.is_dir():
            prefix = rel_path.rstrip("/") + "/"
            return any(entry.path.startswith(prefix) for entry in present_entries)
        return False

    for entry in identity.overlay_entries:
        full = root / entry.path
        if entry.state == "deleted":
            if (full.exists() or full.is_symlink()) and not _captured_replacement(full, entry.path):
                raise ReviewSnapshotError(f"{DIAG_DRIFT}:overlay_deleted_reappeared:{entry.path}")
            continue
        if entry.state == "renamed_from":
            old = root / (entry.old_path or entry.path)
            if old.exists() or old.is_symlink():
                old_rel = entry.old_path or entry.path
                if not _captured_replacement(old, old_rel):
                    raise ReviewSnapshotError(f"{DIAG_DRIFT}:overlay_rename_old_present:{old_rel}")
            continue
        live_digest, live_mode = _live_path_digest(root, entry.path)
        if live_digest != entry.sha256:
            raise ReviewSnapshotError(
                f"{DIAG_DRIFT}:overlay_content:{entry.path}:expected={entry.sha256}:actual={live_digest}"
            )
        if entry.mode is not None and live_mode != (entry.mode & 0o777):
            raise ReviewSnapshotError(
                f"{DIAG_DRIFT}:overlay_mode:{entry.path}:expected={entry.mode & 0o777:o}:actual={live_mode:o}"
            )
    if current.overlay_digest != identity.overlay_digest:
        raise ReviewSnapshotError(
            f"{DIAG_DRIFT}:overlay_digest:expected={identity.overlay_digest}:actual={current.overlay_digest}"
        )


def _write_review_bundle(
    dest: Path,
    *,
    mode: str,
    base_sha: str | None,
    head_sha: str,
    changed_paths: tuple[str, ...],
    patch_bytes: bytes,
    name_status: list[dict[str, str]],
    inert_links: tuple[InertLinkRecord, ...],
    deleted_records: tuple[ImmutableFileRecord, ...],
    source_state: SourceStateIdentity | None,
) -> ReviewBundle:
    bundle_dir = dest / ".review-bundle"
    bundle_dir.mkdir(parents=True, exist_ok=True)
    patch_path = bundle_dir / "patch.diff"
    patch_path.write_bytes(patch_bytes)
    patch_path.chmod(0o444)
    patch_digest = hashlib.sha256(patch_bytes).hexdigest()

    manifest: dict[str, Any] = {
        "schema_version": BUNDLE_SCHEMA_VERSION,
        "mode": mode,
        "base_sha": base_sha,
        "head_sha": head_sha,
        "changed_paths": list(changed_paths),
        "name_status": name_status,
        "patch_digest": patch_digest,
        "patch_bytes": len(patch_bytes),
        "inert_links": [
            {
                "path": link.rel_path,
                "kind": link.kind,
                "mode": link.mode,
                # Target recorded for review context; not a live link.
                "target_or_oid": link.target_or_oid,
            }
            for link in inert_links
        ],
        "deleted_files": [
            {
                "path": record.rel_path,
                "mode": record.mode,
                "sha256": record.sha256,
                "bytes": len(record.content),
                "content": record.content.decode("utf-8", errors="strict"),
            }
            for record in deleted_records
        ],
        "source_state": source_state.public_dict() if source_state else None,
    }
    identity = hashlib.sha256(
        json.dumps(
            {
                "patch_digest": patch_digest,
                "changed_paths": list(changed_paths),
                "base_sha": base_sha or "",
                "head_sha": head_sha,
                "mode": mode,
            },
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
    ).hexdigest()
    manifest["identity"] = identity
    manifest_path = bundle_dir / "manifest.json"
    manifest_path.write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    manifest_path.chmod(0o444)
    # Convenience changed-paths list.
    paths_path = bundle_dir / "changed-paths.json"
    paths_path.write_text(json.dumps(list(changed_paths), indent=2) + "\n", encoding="utf-8")
    paths_path.chmod(0o444)
    return ReviewBundle(
        manifest_path=manifest_path,
        patch_path=patch_path,
        patch_digest=patch_digest,
        changed_paths=changed_paths,
        base_sha=base_sha,
        head_sha=head_sha,
        identity=identity,
    )


def verify_review_bundle(snapshot: ReviewSnapshot) -> str:
    """Re-validate bundle identity from on-disk snapshot contents."""
    bundle_dir = snapshot.path / ".review-bundle"
    manifest_path = bundle_dir / "manifest.json"
    patch_path = bundle_dir / "patch.diff"
    if not manifest_path.is_file() or not patch_path.is_file():
        raise ReviewSnapshotError(f"{DIAG_BUNDLE}:missing")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    deleted_files = manifest.get("deleted_files", [])
    if not isinstance(deleted_files, list):
        raise ReviewSnapshotError(f"{DIAG_BUNDLE}:deleted_files")
    for entry in deleted_files:
        if not isinstance(entry, dict):
            raise ReviewSnapshotError(f"{DIAG_BUNDLE}:deleted_file_entry")
        path = entry.get("path")
        content = entry.get("content")
        digest = entry.get("sha256")
        byte_count = entry.get("bytes")
        if not isinstance(path, str) or not isinstance(content, str):
            raise ReviewSnapshotError(f"{DIAG_BUNDLE}:deleted_file_shape")
        encoded = content.encode("utf-8")
        if byte_count != len(encoded) or digest != hashlib.sha256(encoded).hexdigest():
            raise ReviewSnapshotError(f"{DIAG_BUNDLE}:deleted_file_digest:{path}")
    patch_bytes = patch_path.read_bytes()
    patch_digest = hashlib.sha256(patch_bytes).hexdigest()
    if patch_digest != manifest.get("patch_digest"):
        raise ReviewSnapshotError(f"{DIAG_BUNDLE}:patch_digest")
    if patch_digest != snapshot.patch_digest and snapshot.patch_digest:
        raise ReviewSnapshotError(f"{DIAG_BUNDLE}:snapshot_patch_digest")
    expected = hashlib.sha256(
        json.dumps(
            {
                "patch_digest": patch_digest,
                "changed_paths": list(manifest.get("changed_paths") or []),
                "base_sha": manifest.get("base_sha") or "",
                "head_sha": manifest.get("head_sha") or "",
                "mode": manifest.get("mode") or "",
            },
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
    ).hexdigest()
    if expected != manifest.get("identity"):
        raise ReviewSnapshotError(f"{DIAG_BUNDLE}:identity")
    if snapshot.bundle_identity and expected != snapshot.bundle_identity:
        raise ReviewSnapshotError(f"{DIAG_BUNDLE}:snapshot_identity")
    if list(manifest.get("changed_paths") or []) != list(snapshot.changed_paths):
        raise ReviewSnapshotError(f"{DIAG_BUNDLE}:changed_paths")
    return expected


def materialize_review_snapshot(
    repo_root: Path,
    *,
    mode: str,
    head_sha: str,
    base_sha: str | None = None,
    base_ref: str | None = None,
    changed_paths: tuple[str, ...] | None = None,
    untracked_records: tuple[ImmutableFileRecord, ...] = (),
    dirty_tracked_records: tuple[ImmutableFileRecord, ...] = (),
    deleted_paths: tuple[str, ...] = (),
    rename_pairs: tuple[tuple[str, str], ...] = (),
    overlay_entries: tuple[OverlayIdentityEntry, ...] = (),
    name_status: list[dict[str, str]] | None = None,
    git_bin: Path | None = None,
    temp_parent: Path | None = None,
    patch_bytes: bytes | None = None,
    local_capture: LocalReviewCapture | None = None,
) -> tuple[ReviewSnapshot, _SnapshotState]:
    """Build a neutral temporary snapshot outside the repository.

    ``base_ref`` is accepted as an alias for resolving ``base_sha`` when the
    latter is omitted. For branch/PR/commit modes with a base, the exact
    base→head changed-path set and full patch are derived and secret-scanned
    before materialization (fail closed).

    Local mode may pass ``local_capture`` (preferred) so patch, deletions,
    renames, and overlays come from one immutable capture — never a later
    mutable reread of the working tree.
    """
    root = repo_root.resolve()
    if temp_parent is not None and is_within(temp_parent.resolve(), root):
        raise ReviewSnapshotError("temp_parent_inside_repo")

    git = git_bin or resolve_external_executable("git", reject_root=root)
    if not re_full_sha(head_sha):
        raise ReviewSnapshotError(f"invalid_sha:{head_sha!r}")

    resolved_base = base_sha
    if resolved_base is None and base_ref:
        resolved_base = resolve_head_identity(root, git_bin=git, ref=base_ref)
    if resolved_base is not None and not re_full_sha(resolved_base):
        raise ReviewSnapshotError(f"invalid_sha:{resolved_base!r}")

    if local_capture is not None:
        dirty_tracked_records = local_capture.dirty_tracked
        untracked_records = local_capture.untracked
        deleted_paths = local_capture.deleted_paths
        rename_pairs = local_capture.rename_pairs
        overlay_entries = local_capture.overlay_entries
        name_status = list(local_capture.name_status)
        if patch_bytes is None:
            patch_bytes = local_capture.patch_bytes
        if changed_paths is None or changed_paths == ():
            changed_paths = local_capture.changed_paths

    resolved_name_status: list[dict[str, str]] = list(name_status or [])
    derived_patch = patch_bytes
    derived_paths: tuple[str, ...]

    if mode in {"branch", "pr", "commit"} and resolved_base:
        d_paths, d_patch, resolved_name_status = derive_changed_paths_and_patch(
            root, base_sha=resolved_base, head_sha=head_sha, git_bin=git
        )
        if changed_paths is None or changed_paths == ():
            derived_paths = d_paths
            derived_patch = d_patch
        else:
            # Caller-supplied paths must match the exact derived set.
            if tuple(changed_paths) != d_paths:
                # Allow caller to pass a subset only if equal as sets? No — exact.
                if set(changed_paths) != set(d_paths):
                    raise ReviewSnapshotError(
                        f"changed_paths_mismatch:supplied={len(changed_paths)}:derived={len(d_paths)}"
                    )
                derived_paths = d_paths
            else:
                derived_paths = d_paths
            derived_patch = d_patch if derived_patch is None else derived_patch
    else:
        derived_paths = tuple(changed_paths or ())
        if derived_patch is None:
            derived_patch = b""
        # Local nonempty change sets require a faithful nonempty patch.
        # When callers supply immutable overlay records without a patch (unit
        # tests / partial seams), synthesize from captured bytes only — never
        # reread the mutable working tree.
        if mode == "local" and derived_paths and not (derived_patch or b"").strip():
            synthesized = b""
            for rec in (*dirty_tracked_records, *untracked_records):
                synthesized += _synthetic_untracked_diff(
                    rec.rel_path,
                    rec.content,
                    mode=rec.mode,
                )
            for rel in deleted_paths:
                synthesized += (
                    f"diff --git a/{rel} b/{rel}\ndeleted file mode 100644\n--- a/{rel}\n+++ /dev/null\n"
                ).encode()
            for old, new in rename_pairs:
                synthesized += (f"diff --git a/{old} b/{new}\nrename from {old}\nrename to {new}\n").encode()
            if not synthesized.strip():
                raise ReviewSnapshotError("local_patch_empty_for_nonempty_changes")
            derived_patch = synthesized

    # Preflight overlay + changed paths before any engine could see them.
    # Full base→head patch/content scan already ran inside derive_* for
    # branch/pr/commit modes; do not re-scan the unified patch as one blob
    # (test fixtures that assert detector patterns would false-positive).
    preflight_paths = list(derived_paths)
    preflight_paths.extend(r.rel_path for r in untracked_records)
    preflight_paths.extend(r.rel_path for r in dirty_tracked_records)
    preflight_paths.extend(deleted_paths)
    preflight_paths.extend(old for old, _new in rename_pairs)
    preflight_texts: dict[str, str] = {
        r.rel_path: r.content.decode("utf-8") for r in (*untracked_records, *dirty_tracked_records)
    }
    preflight_review_inputs(paths=preflight_paths, texts=preflight_texts)

    overlays = (*dirty_tracked_records, *untracked_records)
    source_state = capture_source_state_identity(
        root,
        mode=mode,
        base_sha=resolved_base,
        head_sha=head_sha,
        git_bin=git,
        overlay_records=overlays,
        overlay_entries=overlay_entries,
    )

    parent = temp_parent or Path(tempfile.gettempdir())
    parent.mkdir(parents=True, exist_ok=True)
    if is_within(parent.resolve(), root):
        raise ReviewSnapshotError("tmpdir_inside_repo")

    dest = Path(tempfile.mkdtemp(prefix="lu-review-snap-", dir=str(parent)))
    try:
        remove_paths = set(deleted_paths)
        remove_paths.update(old for old, _new in rename_pairs)
        for entry in resolved_name_status:
            status = str(entry.get("status") or "")
            if status.startswith("D") and entry.get("path"):
                remove_paths.add(str(entry["path"]))
            if entry.get("old_path"):
                remove_paths.add(str(entry["old_path"]))
        deleted_records = _capture_deleted_records(
            git,
            root,
            revision=resolved_base or head_sha,
            paths=remove_paths,
        )
        inert_links = _materialize_tree_from_blobs(
            git,
            root,
            head_sha,
            dest,
            changed_paths=set(derived_paths),
        )
        # Apply deletion/rename-old semantics so snapshot paths match the target.
        for rel in sorted(remove_paths):
            target = _safe_child(dest, rel)
            if target.exists() or target.is_symlink():
                if target.is_dir() and not target.is_symlink():
                    # Git trees never contain directory entries. A directory at
                    # an old file path therefore consists only of descendants
                    # present in the exact head (file -> directory replacement)
                    # and must survive old-side evidence removal.
                    continue
                else:
                    target.unlink()
        _write_records(dest, overlays)

        if (dest / ".git").exists():
            raise ReviewSnapshotError("snapshot_contains_git_metadata")

        # Refuse any live symlink left in the tree.
        for dirpath, dirnames, filenames in os.walk(dest, followlinks=False):
            base = Path(dirpath)
            for name in [*dirnames, *filenames]:
                p = base / name
                if p.is_symlink():
                    raise ReviewSnapshotError(f"{DIAG_SYMLINK}:{p}")

        # The reviewer receives only changed-path evidence. Unchanged inert
        # symlink targets can contain unrelated local paths or identifiers and
        # must not be serialized into the prompt bundle.
        changed_inert_links = tuple(link for link in inert_links if link.rel_path in set(derived_paths))
        bundle = _write_review_bundle(
            dest,
            mode=mode,
            base_sha=resolved_base,
            head_sha=head_sha,
            changed_paths=derived_paths,
            patch_bytes=derived_patch or b"",
            name_status=resolved_name_status,
            inert_links=changed_inert_links,
            deleted_records=deleted_records,
            source_state=source_state,
        )
        fingerprint = _fingerprint_snapshot_tree(
            dest,
            mode=mode,
            base_sha=resolved_base,
            head_sha=head_sha,
            changed_paths=derived_paths,
            patch_digest=bundle.patch_digest,
            source_state_id=source_state.identity,
        )
        meta = {
            "schema_version": "review-snapshot-metadata.v2",
            "fingerprint_version": SNAPSHOT_FINGERPRINT_VERSION,
            "mode": mode,
            "base_sha": resolved_base,
            "head_sha": head_sha,
            "source_fingerprint": fingerprint,
            "changed_paths": list(derived_paths),
            "untracked": [r.rel_path for r in untracked_records],
            "patch_digest": bundle.patch_digest,
            "bundle_identity": bundle.identity,
            "source_state": source_state.public_dict(),
            "inert_link_count": len(changed_inert_links),
            "isolation": {
                "project_instructions": "inert_evidence_only",
                "live_git": False,
                "writable": False,
                "live_symlinks": False,
            },
        }
        meta_path = dest / ".review-snapshot-metadata.json"
        meta_path.write_text(
            json.dumps(meta, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        meta_path.chmod(0o444)
        _set_tree_read_only(dest)

        snapshot = ReviewSnapshot(
            path=dest,
            mode=mode,
            base_sha=resolved_base,
            head_sha=head_sha,
            source_fingerprint=fingerprint,
            changed_paths=derived_paths,
            untracked_records=untracked_records,
            metadata_path=meta_path,
            patch_digest=bundle.patch_digest,
            source_state_id=source_state.identity,
            bundle_identity=bundle.identity,
            inert_links=inert_links,
            bundle=bundle,
            source_state=source_state,
        )
        state = _SnapshotState(
            root=dest,
            mode=mode,
            base_sha=resolved_base,
            head_sha=head_sha,
            source_fingerprint=fingerprint,
            changed_paths=derived_paths,
            untracked_records=untracked_records,
            repo_root=root,
            source_state=source_state,
            patch_digest=bundle.patch_digest,
            bundle_identity=bundle.identity,
            sealed=True,
        )
        return snapshot, state
    except Exception:
        _cleanup_snapshot(dest)
        raise


def verify_snapshot_fingerprint(snapshot: ReviewSnapshot) -> str:
    """Re-hash snapshot on-disk contents; raise on drift vs recorded fingerprint."""
    current = _fingerprint_snapshot_tree(
        snapshot.path,
        mode=snapshot.mode,
        base_sha=snapshot.base_sha,
        head_sha=snapshot.head_sha,
        changed_paths=snapshot.changed_paths,
        patch_digest=snapshot.patch_digest,
        source_state_id=snapshot.source_state_id,
    )
    if current != snapshot.source_fingerprint:
        raise ReviewSnapshotError(f"{DIAG_DRIFT}:expected={snapshot.source_fingerprint}:actual={current}")
    return current


def verify_review_acceptance(
    snapshot: ReviewSnapshot,
    *,
    git_bin: Path | None = None,
    expected_policy_version: str | None = None,
    expected_capability_digest: str | None = None,
    expected_engine: str | None = None,
    isolation_evidence: Mapping[str, Any] | None = None,
    require_isolation_evidence: bool = False,
    expected_prompt_sha256: str | None = None,
    expected_prompt_transport: str | None = None,
) -> dict[str, str]:
    """Full post-review gate: snapshot, source, bundle, isolation evidence bind.

    When ``require_isolation_evidence`` is true (bridge acceptance path),
    missing/stale/mismatched/malformed evidence fails closed. Reviewer-writable
    files are never authoritative — evidence must come from trusted process
    memory (runner Result.isolation_evidence).

    ``expected_capability_digest`` must not be a tautological copy of the same
    evidence field; when set, it is an independent trusted-runner value.
    """
    verify_snapshot_fingerprint(snapshot)
    verify_review_bundle(snapshot)
    if snapshot.source_state is not None:
        verify_source_state_identity(snapshot.source_state, git_bin=git_bin)

    if require_isolation_evidence and not isolation_evidence:
        raise ReviewSnapshotError(f"{DIAG_DRIFT}:isolation_evidence_missing")

    if isolation_evidence is not None:
        from scripts.review.isolation import ISOLATION_POLICY_VERSION as _IPV
        from scripts.review.isolation import ReviewIsolationError as _RIE
        from scripts.review.isolation import validate_isolation_evidence

        expected_pol = expected_policy_version or _IPV
        try:
            validate_isolation_evidence(
                isolation_evidence,
                expected_engine=expected_engine,
                expected_policy_version=expected_pol,
                snapshot_fingerprint=snapshot.source_fingerprint,
                source_state_id=snapshot.source_state_id,
                patch_digest=snapshot.patch_digest,
                bundle_identity=snapshot.bundle_identity,
                base_sha=snapshot.base_sha,
                head_sha=snapshot.head_sha,
                changed_paths=snapshot.changed_paths,
                expected_capability_digest=expected_capability_digest,
                expected_prompt_sha256=expected_prompt_sha256,
                expected_prompt_transport=expected_prompt_transport,
            )
        except _RIE as exc:
            raise ReviewSnapshotError(f"{DIAG_DRIFT}:{exc}") from exc

    return {
        "snapshot_fingerprint": snapshot.source_fingerprint,
        "source_state_id": snapshot.source_state_id,
        "bundle_identity": snapshot.bundle_identity,
        "patch_digest": snapshot.patch_digest,
    }


def _cleanup_snapshot(path: Path) -> None:
    if not path.exists():
        return
    _set_tree_writable(path)
    shutil.rmtree(path, ignore_errors=False)


def cleanup_snapshot_state(state: _SnapshotState) -> None:
    """Remove the temporary snapshot root; safe to call multiple times."""
    if state.cleaned:
        return
    try:
        _cleanup_snapshot(state.root)
    finally:
        state.cleaned = True


@contextlib.contextmanager
def provision_review_snapshot(
    repo_root: Path,
    *,
    mode: str,
    head_sha: str,
    base_sha: str | None = None,
    base_ref: str | None = None,
    changed_paths: tuple[str, ...] | None = None,
    untracked_records: tuple[ImmutableFileRecord, ...] = (),
    dirty_tracked_records: tuple[ImmutableFileRecord, ...] = (),
    deleted_paths: tuple[str, ...] = (),
    rename_pairs: tuple[tuple[str, str], ...] = (),
    overlay_entries: tuple[OverlayIdentityEntry, ...] = (),
    name_status: list[dict[str, str]] | None = None,
    local_capture: LocalReviewCapture | None = None,
    git_bin: Path | None = None,
    temp_parent: Path | None = None,
    verify_after: bool = True,
    patch_bytes: bytes | None = None,
) -> Iterator[ReviewSnapshot]:
    """Context manager: materialize snapshot, verify drift, always cleanup."""
    snapshot, state = materialize_review_snapshot(
        repo_root,
        mode=mode,
        head_sha=head_sha,
        base_sha=base_sha,
        base_ref=base_ref,
        changed_paths=changed_paths,
        untracked_records=untracked_records,
        dirty_tracked_records=dirty_tracked_records,
        deleted_paths=deleted_paths,
        rename_pairs=rename_pairs,
        overlay_entries=overlay_entries,
        name_status=name_status,
        local_capture=local_capture,
        git_bin=git_bin,
        temp_parent=temp_parent,
        patch_bytes=patch_bytes,
    )
    try:
        yield snapshot
        if verify_after:
            verify_review_acceptance(snapshot, git_bin=git_bin)
    finally:
        cleanup_snapshot_state(state)


def _synthetic_untracked_diff(rel_path: str, content: bytes, *, mode: int = 0o644) -> bytes:
    """Build a unified diff for an untracked file from immutable captured bytes."""
    git_mode = "100755" if mode & 0o111 else "100644"
    text = content.decode("utf-8")
    lines = text.splitlines()
    body = "\n".join(f"+{line}" for line in lines)
    if text and not text.endswith("\n"):
        body += "\n\\ No newline at end of file"
    elif text.endswith("\n") and lines:
        pass
    header = (
        f"diff --git a/{rel_path} b/{rel_path}\n"
        f"new file mode {git_mode}\n"
        f"--- /dev/null\n"
        f"+++ b/{rel_path}\n"
        f"@@ -0,0 +1,{max(len(lines), 1) if text else 0} @@\n"
    )
    if not text:
        return (
            f"diff --git a/{rel_path} b/{rel_path}\nnew file mode {git_mode}\n--- /dev/null\n+++ b/{rel_path}\n"
        ).encode()
    return (header + body + ("\n" if not body.endswith("\n") else "")).encode()


def capture_local_review_state(
    repo_root: Path,
    *,
    git_bin: Path | None = None,
    expected_head_sha: str | None = None,
) -> LocalReviewCapture:
    """Capture a complete immutable local review target (paths + patch + overlays).

    Includes staged and unstaged tracked modifications, untracked additions,
    deletions, renames/copies, and mode changes. Content is read once into
    immutable records; the mutable tree is never reopened for bundle bytes.
    """
    root = repo_root.resolve()
    git = git_bin or resolve_external_executable("git", reject_root=root)
    if expected_head_sha is not None:
        before = resolve_head_identity(root, git_bin=git)
        if before != expected_head_sha:
            raise ReviewSnapshotError(
                f"{DIAG_DRIFT}:local_head_before_capture:expected={expected_head_sha}:actual={before}"
            )
    capture_head = expected_head_sha or resolve_head_identity(root, git_bin=git)
    with _neutral_local_git_view(root, git_bin=git, head_sha=capture_head) as neutral_git:
        proc = _run_git(
            git,
            [*neutral_git, "status", "--porcelain", "--untracked-files=all", "-z"],
            cwd=root,
        )
    assert isinstance(proc.stdout, str)
    captured_status = proc.stdout
    dirty: list[ImmutableFileRecord] = []
    untracked: list[ImmutableFileRecord] = []
    deleted: list[str] = []
    renames: list[tuple[str, str]] = []
    changed: list[str] = []
    name_status: list[dict[str, str]] = []
    overlay_entries: list[OverlayIdentityEntry] = []

    entries = [e for e in proc.stdout.split("\0") if e]
    i = 0
    while i < len(entries):
        entry = entries[i]
        if len(entry) < 3:
            i += 1
            continue
        status = entry[:2]
        path = entry[3:]
        # Porcelain v1 ``-z`` reverses the human-readable rename order:
        # the status entry names the destination, followed by the source.
        if status[0] in {"R", "C"} or status[1] in {"R", "C"}:
            if i + 1 >= len(entries):
                raise ReviewSnapshotError("malformed_porcelain_rename")
            new_p = _validate_rel_path(path)
            old_p = _validate_rel_path(entries[i + 1])
            i += 2
            renames.append((old_p, new_p))
            deleted.append(old_p)
            changed.extend([old_p, new_p])
            name_status.append(
                {
                    "status": status.strip() or "R",
                    "old_path": old_p,
                    "path": new_p,
                    "kind": "rename",
                }
            )
            try:
                data, mode = _read_regular_file_stable(root, new_p, allow_binary=False)
            except ReviewSnapshotError as exc:
                raise ReviewSnapshotError(f"rename_target_invalid:{new_p}:{exc}") from exc
            rec = ImmutableFileRecord.from_bytes(new_p, data, mode=mode)
            dirty.append(rec)
            overlay_entries.append(
                OverlayIdentityEntry(
                    path=new_p,
                    state="present",
                    sha256=rec.sha256,
                    mode=mode,
                    old_path=old_p,
                    status=status,
                )
            )
            overlay_entries.append(
                OverlayIdentityEntry(
                    path=old_p,
                    state="renamed_from",
                    sha256="",
                    mode=None,
                    old_path=old_p,
                    status=status,
                )
            )
            continue

        i += 1
        if not path or path.endswith("/"):
            continue
        path = _validate_rel_path(path)
        full = root / path
        if full.is_symlink():
            raise ReviewSnapshotError(f"{DIAG_SYMLINK}:{path}")

        xy = status
        if xy == "??":
            data, mode = _read_regular_file_stable(root, path, allow_binary=False)
            rec = ImmutableFileRecord.from_bytes(path, data, mode=mode)
            untracked.append(rec)
            changed.append(path)
            name_status.append({"status": "A", "path": path, "kind": "untracked"})
            overlay_entries.append(
                OverlayIdentityEntry(
                    path=path,
                    state="present",
                    sha256=rec.sha256,
                    mode=mode,
                    status="??",
                )
            )
            continue

        # Deletion: staged (D ) / unstaged ( D) / both (DD).
        if "D" in xy:
            deleted.append(path)
            changed.append(path)
            name_status.append({"status": "D", "path": path, "kind": "delete"})
            overlay_entries.append(
                OverlayIdentityEntry(
                    path=path,
                    state="deleted",
                    sha256="",
                    mode=None,
                    status=xy,
                )
            )
            continue

        if not full.exists():
            # Treat missing path as deletion even if status is odd.
            deleted.append(path)
            changed.append(path)
            name_status.append({"status": "D", "path": path, "kind": "delete"})
            overlay_entries.append(
                OverlayIdentityEntry(
                    path=path,
                    state="deleted",
                    sha256="",
                    mode=None,
                    status=xy,
                )
            )
            continue

        data, mode = _read_regular_file_stable(root, path, allow_binary=False)
        rec = ImmutableFileRecord.from_bytes(path, data, mode=mode)
        dirty.append(rec)
        changed.append(path)
        name_status.append({"status": xy.strip() or "M", "path": path, "kind": "modify"})
        overlay_entries.append(
            OverlayIdentityEntry(
                path=path,
                state="present",
                sha256=rec.sha256,
                mode=mode,
                status=xy,
            )
        )

    # Immutable tracked patch (staged + unstaged vs HEAD), then append untracked.
    with _neutral_local_git_view(root, git_bin=git, head_sha=capture_head) as neutral_git:
        tracked_patch_proc = _run_git(
            git,
            [
                *neutral_git,
                "diff",
                "HEAD",
                "--binary",
                "--find-renames",
                "--no-ext-diff",
                "--no-textconv",
            ],
            cwd=root,
            text=False,
        )
    assert isinstance(tracked_patch_proc.stdout, (bytes, bytearray))
    patch_bytes = bytes(tracked_patch_proc.stdout)
    if _patch_contains_binary_markers(patch_bytes):
        raise ReviewSnapshotError(f"{DIAG_BINARY_PATCH}:local_changed_binary")
    # Reject null-byte / non-UTF-8 tracked patches (binary changes).
    if b"\x00" in patch_bytes:
        raise ReviewSnapshotError(f"{DIAG_BINARY_PATCH}:local_non_utf8_patch")
    try:
        patch_bytes.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise ReviewSnapshotError(f"{DIAG_BINARY_PATCH}:local_non_utf8_patch") from exc

    for rec in untracked:
        patch_bytes += _synthetic_untracked_diff(
            rec.rel_path,
            rec.content,
            mode=rec.mode,
        )

    # Secret-scan patch sections and overlay texts (no path exemptions).
    if patch_bytes.strip():
        _preflight_changed_contents(
            git,
            root,
            base_sha="HEAD",
            head_sha="HEAD",
            paths=[p for p in changed if p not in {r.rel_path for r in untracked}],
            entries=name_status,
            patch_bytes=patch_bytes,
        )
    preflight_review_inputs(
        paths=changed,
        texts={r.rel_path: r.content.decode("utf-8") for r in (*dirty, *untracked)},
    )

    ordered_paths = tuple(dict.fromkeys(changed))
    if ordered_paths and not patch_bytes.strip():
        raise ReviewSnapshotError("local_patch_empty_for_nonempty_changes")
    if expected_head_sha is not None:
        after = resolve_head_identity(root, git_bin=git)
        if after != expected_head_sha:
            raise ReviewSnapshotError(
                f"{DIAG_DRIFT}:local_head_after_capture:expected={expected_head_sha}:actual={after}"
            )
    with _neutral_local_git_view(root, git_bin=git, head_sha=capture_head) as neutral_git:
        after_status = _run_git(
            git,
            [*neutral_git, "status", "--porcelain", "--untracked-files=all", "-z"],
            cwd=root,
        )
    assert isinstance(after_status.stdout, str)
    if after_status.stdout != captured_status:
        raise ReviewSnapshotError(f"{DIAG_DRIFT}:local_status_during_capture")

    return LocalReviewCapture(
        dirty_tracked=tuple(dirty),
        untracked=tuple(untracked),
        deleted_paths=tuple(dict.fromkeys(deleted)),
        rename_pairs=tuple(dict.fromkeys(renames)),
        changed_paths=ordered_paths,
        name_status=tuple(name_status),
        patch_bytes=patch_bytes,
        overlay_entries=tuple(overlay_entries),
    )


def capture_local_overlays(
    repo_root: Path,
    *,
    git_bin: Path | None = None,
) -> tuple[tuple[ImmutableFileRecord, ...], tuple[ImmutableFileRecord, ...], tuple[str, ...]]:
    """Backward-compatible wrapper around :func:`capture_local_review_state`.

    Returns ``(dirty_tracked, untracked, changed_paths)``. Prefer
    ``capture_local_review_state`` for full local fidelity (patch/deletes).
    """
    capture = capture_local_review_state(repo_root, git_bin=git_bin)
    return capture.dirty_tracked, capture.untracked, capture.changed_paths
