"""Manage migration manifests and the host-local content-addressed artifact store."""

from __future__ import annotations

import argparse
import contextlib
import csv
import datetime as dt
import fcntl
import fnmatch
import hashlib
import io
import json
import os
import re
import shutil
import subprocess
import sys
import tarfile
import tempfile
import time
import uuid
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

from scripts.storage import paths

ROOT = paths.ROOT
TABLE = "registry/artifacts/classification-v1.tsv"


def _now() -> str:
    return dt.datetime.now(dt.UTC).isoformat()


def _git(repo: Path, *args: str, input_bytes: bytes | None = None) -> bytes:
    return subprocess.run(
        ["git", *args], cwd=repo, input=input_bytes, capture_output=True, check=True, timeout=30
    ).stdout


def _json_write(path: Path, value: object) -> None:
    _mkdir_durable(path.parent)
    with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", dir=path.parent, delete=False) as stream:
        temp = Path(stream.name)
        try:
            json.dump(value, stream, indent=2, sort_keys=True)
            stream.write("\n")
            stream.flush()
            os.fsync(stream.fileno())
        except BaseException:
            temp.unlink(missing_ok=True)
            raise
    try:
        os.replace(temp, path)
        _fsync_dir(path.parent)
    finally:
        temp.unlink(missing_ok=True)


def _fsync_dir(directory: Path) -> None:
    fd = os.open(directory, os.O_RDONLY | os.O_DIRECTORY)
    try:
        os.fsync(fd)
    finally:
        os.close(fd)


def _mkdir_durable(directory: Path) -> None:
    missing = []
    cursor = directory
    while not cursor.exists():
        missing.append(cursor)
        cursor = cursor.parent
    for path in reversed(missing):
        path.mkdir()
        _fsync_dir(path.parent)


def _manifest_digest(value: object) -> str:
    return hashlib.sha256((json.dumps(value, indent=2, sort_keys=True) + "\n").encode()).hexdigest()


def _rows(repo: Path) -> list[dict[str, str]]:
    with (repo / TABLE).open(encoding="utf-8", newline="") as source:
        return list(csv.DictReader(source, delimiter="\t"))


def _phase(row: dict[str, str]) -> str:
    path = row["path"]
    if path.startswith("data/lexicon/"):
        return "P2"
    if path.startswith("data/projects/open_model_data/"):
        return "P3"
    if path.startswith(
        ("data/projects/ua_eval_harness/", "data/projects/ua_open_weight_eval/", "data/processed/", "data/datasets/")
    ):
        return "P4"
    return "P1"


def phase_groups(repo: Path, phase: str) -> set[str]:
    if phase not in {"P1", "P2", "P3", "P4", "P5"}:
        raise ValueError(f"unknown phase {phase!r}")
    return {row["group"] for row in _rows(repo) if row["class"] == "A" and _phase(row) == phase}


def _resolve_manifests_ref(repo: Path, ref: str) -> str:
    """Return the commit a ``--manifests-ref`` names, or explain how to fetch it."""
    proc = None
    if not ref.startswith("-"):
        proc = subprocess.run(
            ["git", "rev-parse", "--verify", "--quiet", f"{ref}^{{commit}}"],
            cwd=repo,
            capture_output=True,
            text=True,
            timeout=30,
        )
    if proc is None or proc.returncode != 0:
        raise ValueError(
            f"manifests ref {ref!r} does not resolve to a commit in {repo}; "
            "fetch the phase branch first, for example: git fetch origin <phase-branch>"
        )
    return proc.stdout.strip()


def _load_manifest(repo: Path, group: str, commit: str | None = None) -> dict:
    """Load a group manifest from the working tree, or from ``commit`` without touching the working tree."""
    if commit is None:
        return paths.load_manifest(group, repo)
    rel = paths.manifest_path(group, repo).relative_to(repo).as_posix()
    proc = subprocess.run(["git", "show", f"{commit}:{rel}"], cwd=repo, capture_output=True, timeout=30)
    if proc.returncode != 0:
        raise paths.MissingArtifactError(
            group, "*", f"check that {commit} is the phase branch head carrying {rel}", f"manifest missing at {commit}"
        )
    try:
        manifest = json.loads(proc.stdout)
    except json.JSONDecodeError as exc:
        raise ValueError(f"invalid manifest JSON at {commit}:{rel}: {exc}") from exc
    return paths.validate_manifest(manifest, group, f"{commit}:{rel}")


def _phase_entries(repo: Path, phase: str, *, manifests_commit: str | None = None) -> list[tuple[str, dict]]:
    selected = {row["path"] for row in _rows(repo) if row["class"] == "A" and _phase(row) == phase}
    result = []
    covered = set()
    for group in phase_groups(repo, phase):
        manifest = _load_manifest(repo, group, manifests_commit)
        result.extend((group, entry) for entry in manifest["entries"])
        covered.update(entry["path"] for entry in manifest["entries"] if entry["path"] in selected)
        covered.update(item["path"] for item in manifest.get("retired", []) if item["path"] in selected)
    if covered != selected:
        raise ValueError(f"phase {phase}: manifest coverage {len(covered)} != {len(selected)}")
    return result


def _all_manifests(repo: Path) -> list[tuple[str, dict]]:
    result = []
    for path in sorted((repo / "registry/artifacts").glob("*.manifest.json")):
        group = path.name.removesuffix(".manifest.json")
        for entry in paths.load_manifest(group, repo)["entries"]:
            result.append((group, entry))
    return result


def _migrated_a_trees(repo: Path) -> set[Path]:
    """Find phase A roots with installed manifests, using the frozen classification."""
    trees = set()
    rows = _rows(repo)
    for phase in {_phase(row) for row in rows if row["class"] == "A"}:
        phase_rows = [row for row in rows if row["class"] == "A" and _phase(row) == phase]
        if not any(paths.manifest_path(group, repo).is_file() for group in {row["group"] for row in phase_rows}):
            continue
        common = Path(os.path.commonpath([str(Path(row["path"]).parent) for row in phase_rows]))
        if len(common.parts) > 1:  # A phase spanning all of data/ has no single safe output tree.
            trees.add((repo / common).absolute())
    return trees


def _lexicon_host_state(repo: Path, target: Path) -> bool:
    """Keep the specific host-state ignore rules that predate the broad P2 ignore."""
    ignore = repo / ".gitignore"
    if not ignore.is_file():
        return False
    relative = target.relative_to(repo.absolute()).as_posix()
    for line in ignore.read_text(encoding="utf-8").splitlines():
        rule = line.strip()
        if rule == "/data/lexicon/":
            break
        if not rule.startswith("data/lexicon/"):
            continue
        if rule.endswith("/") and relative.startswith(rule):
            return True
        if "*" in rule and relative.count("/") == rule.count("/") and fnmatch.fnmatchcase(relative, rule):
            return True
        if relative == rule:
            return True
    return False


def _sha_blob(repo: Path, blob: str) -> str:
    proc = subprocess.Popen(["git", "cat-file", "blob", blob], cwd=repo, stdout=subprocess.PIPE)
    digest = hashlib.sha256()
    assert proc.stdout is not None
    for chunk in iter(lambda: proc.stdout.read(1024 * 1024), b""):
        digest.update(chunk)
    if proc.wait(timeout=120) != 0:
        raise ValueError(f"missing git blob {blob}")
    return digest.hexdigest()


def _blob_present(repo: Path, blob: str) -> bool:
    return (
        subprocess.run(
            ["git", "cat-file", "-e", f"{blob}^{{blob}}"],
            cwd=repo,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            timeout=30,
        ).returncode
        == 0
    )


def _entry_rel(entry: dict) -> str:
    path = entry["path"]
    if not path.startswith("data/"):
        raise ValueError(f"invalid manifest path {path!r}")
    return str(paths.checked_rel(path[5:]))


def manifest_build(repo: Path, group: str, pre: str) -> int:
    paths.checked_group(group)
    entries = []
    for row in _rows(repo):
        if row["class"] != "A" or row["group"] != group:
            continue
        rel = row["path"]
        disk = _safe_destination(repo, rel, "data")
        if not disk.is_file() or disk.is_symlink():
            raise ValueError(f"missing regular A file {rel}")
        blob = _git(repo, "rev-parse", f"{pre}:{rel}").decode().strip()
        mode = _git(repo, "ls-tree", pre, "--", rel).decode().split()[0]
        if mode != row["mode"] or (row["blob"] and blob != row["blob"]):
            raise ValueError(f"pre-phase Git tree differs from classification: {rel}")
        disk_sha = paths.hash_file(disk)
        if disk_sha != _sha_blob(repo, blob):
            raise ValueError(f"disk differs from pre-untrack blob: {rel}")
        entries.append(
            {
                "path": rel,
                "mode": row["mode"],
                "size": disk.stat().st_size,
                "sha256": disk_sha,
                "pre_untrack_sha256": disk_sha,
                "git_blob": blob,
                "producer": row["reason"].split(";", 1)[0],
                "rights": "uncleared",
                "store": disk_sha,
                "mtime_ns": disk.stat().st_mtime_ns,
                "migrated_at": _now(),
                "published_at": None,
            }
        )
    if not entries:
        raise ValueError(f"group {group!r} has no A rows")
    target = paths.manifest_path(group, repo)
    if target.exists():
        raise ValueError(f"manifest already exists: {target}")
    _json_write(target, {"schema": 1, "group": group, "entries": entries})
    return len(entries)


def _store_copy(source: Path, sha: str, store: Path) -> None:
    _mkdir_durable(store)
    target = store / sha
    if target.exists():
        if target.is_symlink() or paths.hash_file(target) != sha:
            raise ValueError(f"corrupt store object: {sha}")
        return
    with tempfile.NamedTemporaryFile(dir=store, delete=False) as stream:
        temp = Path(stream.name)
        try:
            with source.open("rb") as reader:
                shutil.copyfileobj(reader, stream)
            stream.flush()
            os.fsync(stream.fileno())
        except BaseException:
            temp.unlink(missing_ok=True)
            raise
    try:
        if paths.hash_file(temp) != sha:
            raise ValueError(f"source changed during store copy: {source}")
        os.replace(temp, target)
        _fsync_dir(store)
    finally:
        temp.unlink(missing_ok=True)


def snapshot(repo: Path, phase: str, *, manifests_ref: str | None = None) -> int:
    """Copy current active A versions into the host store after disk and lineage proof.

    ``manifests_ref`` reads the phase manifests from a Git ref (the unmerged phase branch), so a checkout
    still at the pre-phase commit can snapshot before the phase merges; the working tree is not changed.
    """
    commit = _resolve_manifests_ref(repo, manifests_ref) if manifests_ref is not None else None
    with _lock(repo):
        _recover_locked(repo)
        return _snapshot_locked(repo, phase, manifests_commit=commit)


def _snapshot_locked(repo: Path, phase: str, *, manifests_commit: str | None = None) -> int:
    entries = _phase_entries(repo, phase, manifests_commit=manifests_commit)
    store = paths.artifact_store_root(repo)
    for group, entry in entries:
        rel = _entry_rel(entry)
        source = _safe_destination(repo, entry["path"], "data")
        paths.verify_file(source, entry, group=group, rel=rel)
        blob = entry.get("git_blob")
        if blob and (not _blob_present(repo, blob) or _sha_blob(repo, blob) != entry.get("pre_untrack_sha256")):
            raise ValueError(f"pre-untrack blob proof failed: {entry['path']}")
        _store_copy(source, entry["sha256"], store)
    return len(entries)


def _restore_from_blob(repo: Path, blob: str, target: Path, sha: str) -> None:
    if not _blob_present(repo, blob):
        raise FileNotFoundError(f"git blob unavailable: {blob}")
    _mkdir_durable(target.parent)
    with tempfile.NamedTemporaryFile(dir=target.parent, delete=False) as stream:
        temp = Path(stream.name)
        try:
            proc = subprocess.Popen(["git", "cat-file", "blob", blob], cwd=repo, stdout=stream)
            if proc.wait(timeout=120) != 0:
                raise ValueError(f"git cat-file failed: {blob}")
        except BaseException:
            temp.unlink(missing_ok=True)
            raise
    try:
        if paths.hash_file(temp) != sha:
            raise ValueError(f"git blob hash differs from manifest: {blob}")
        os.replace(temp, target)
        _fsync_dir(target.parent)
    finally:
        temp.unlink(missing_ok=True)


def hydrate(
    repo: Path,
    entries: list[tuple[str, dict]],
    *,
    force_preserve: bool = False,
    groups: set[str] | None = None,
) -> int:
    with _lock(repo):
        _recover_locked(repo)
        return _hydrate_locked(repo, entries, force_preserve=force_preserve, groups=groups or set())


def _hydrate_locked(repo: Path, entries: list[tuple[str, dict]], *, force_preserve: bool, groups: set[str]) -> int:
    store = paths.artifact_store_root(repo)
    count = 0
    failures = []
    for group, entry in entries:
        try:
            _hydrate_one(repo, group, entry, store, force_preserve=force_preserve)
            count += 1
        except (OSError, ValueError) as exc:
            failures.append(f"{entry['path']}: {exc}")
    if failures:
        raise ValueError(f"hydrate: {len(failures)} artifact(s) failed:\n" + "\n".join(failures))
    for group in {group for group, _ in entries} | groups:
        manifest = paths.load_manifest(group, repo)
        active = {entry["path"] for entry in manifest["entries"]}
        retired: dict[str, set[str]] = {}
        for item in manifest.get("retired", []):
            retired.setdefault(item["path"], set()).add(item["sha256"])
        for path, known_hashes in retired.items():
            if path in active:
                continue
            target = _safe_destination(repo, path, "data")
            actual = _actual_sha(target)
            if actual is not None:
                if actual not in known_hashes:
                    raise ValueError(f"hydrate REFUSED divergent retired target: {path}")
                _install(None, target)
    return count


def _hydrate_one(repo: Path, group: str, entry: dict, store: Path, *, force_preserve: bool) -> None:
    rel = _entry_rel(entry)
    target = _safe_destination(repo, entry["path"], "data")
    sha = entry["sha256"]
    obj = store / sha
    valid_obj = (
        obj.is_file() and not obj.is_symlink() and obj.stat().st_size == entry["size"] and paths.hash_file(obj) == sha
    )
    blob = entry.get("git_blob")
    if target.is_file() and not target.is_symlink():
        target_sha = paths.hash_file(target)
        if target_sha == sha:
            if not valid_obj:
                if obj.exists() or obj.is_symlink():
                    print(f"warning: corrupt store object {sha}; repairing from target", file=sys.stderr)
                    _quarantine_corrupt_object(obj, store)
                _store_copy(target, sha, store)
            return
        if target_sha != sha:
            if not force_preserve:
                raise ValueError("REFUSED divergent target; use --force-preserve")
            _store_copy(target, target_sha, store)
            with (store / "divergent.jsonl").open("a", encoding="utf-8") as log:
                log.write(json.dumps({"path": entry["path"], "sha256": target_sha, "recorded_at": _now()}) + "\n")
                log.flush()
                os.fsync(log.fileno())
    elif target.exists() or target.is_symlink():
        raise ValueError("REFUSED non-regular target")
    if valid_obj:
        target.parent.mkdir(parents=True, exist_ok=True)
        _restore_from_store(obj, target, mode=entry.get("mode"))
    elif blob and _blob_present(repo, blob) and _sha_blob(repo, blob) == sha:
        if obj.exists() or obj.is_symlink():
            print(f"warning: corrupt store object {sha}; using git blob", file=sys.stderr)
        _restore_from_blob(repo, blob, target, sha)
        if obj.exists() or obj.is_symlink():
            _quarantine_corrupt_object(obj, store)
    else:
        raise paths.MissingArtifactError(
            group, rel, "import a verified tarball", "store object and git blob unavailable"
        )
    paths.verify_file(target, entry, group=group, rel=rel)
    _store_copy(target, sha, store)


def _quarantine_corrupt_object(obj: Path, store: Path) -> None:
    quarantine = store / ".corrupt"
    quarantine.mkdir(exist_ok=True)
    os.replace(obj, quarantine / f"{obj.name}-{time.time_ns()}")


def verify(repo: Path, entries: list[tuple[str, dict]], *, groups: set[str] | None = None) -> int:
    store = paths.artifact_store_root(repo)
    failures = []
    for group, entry in entries:
        try:
            paths.verify_file(_safe_destination(repo, entry["path"], "data"), entry, group=group, rel=_entry_rel(entry))
            obj = store / entry["sha256"]
            if not obj.is_file() or obj.stat().st_size != entry["size"] or paths.hash_file(obj) != entry["sha256"]:
                raise ValueError(f"missing or corrupt store object: {entry['sha256']}")
        except (OSError, ValueError) as exc:
            failures.append(f"{entry['path']}: {exc}")
    for group in {group for group, _ in entries} | (groups or set()):
        manifest = paths.load_manifest(group, repo)
        for item in manifest.get("retired", []):
            try:
                _checked_store_object(store, item["sha256"], item["size"])
            except (OSError, ValueError) as exc:
                failures.append(f"{group} retired {item['path']}: {exc}")
        if "set_descriptor" in manifest:
            try:
                paths.artifact_set(group, repo=repo)
                active = {entry["path"] for entry in manifest["entries"]}
                for item in manifest.get("retired", []):
                    if item["path"] not in active and _safe_destination(repo, item["path"], "data").exists():
                        raise ValueError(f"retired path remains: {item['path']}")
            except (OSError, ValueError) as exc:
                failures.append(f"{group} set: {exc}")
    if failures:
        raise ValueError(f"verify: {len(failures)} artifact(s) failed:\n" + "\n".join(failures))
    return len(entries)


@contextlib.contextmanager
def _lock(repo: Path):
    store = paths.artifact_store_root(repo)
    _mkdir_durable(store)
    with (store / ".publish.lock").open("a+b") as stream:
        fcntl.flock(stream, fcntl.LOCK_EX)
        try:
            for leftover in store.glob("tmp*"):
                if leftover.is_file() and not leftover.is_symlink() and time.time() - leftover.stat().st_mtime > 3600:
                    leftover.unlink()
            yield
        finally:
            fcntl.flock(stream, fcntl.LOCK_UN)


def _journal_path(repo: Path, group: str, rel: str) -> Path:
    key = hashlib.sha256(f"{repo.resolve()}:{group}:{rel}".encode()).hexdigest()
    return paths.artifact_store_root(repo) / ".transactions" / f"{key}.json"


class RecoveryError(ValueError):
    """A publish journal cannot be recovered automatically; every artifacts command stops until it is resolved."""


def _recovery_remediation(journal: Path) -> str:
    command = "/home/ops/learn-ukrainian/.venv/bin/python -m scripts.storage.artifacts"
    return (
        f"remediation: every `{command}` command (status and verify included) runs recovery first and stops "
        "on this journal, so start with plain shell tools:\n"
        f"  1. inspect the journal: `cat {journal}` (single-file fields repo, group, rel, old_sha256, "
        "new_sha256, new_manifest_digest, manifest; set journals have rows and companions).\n"
        "  2. in that repo compare every A and K row by hash: `sha256sum data/<rel>` and "
        "`sha256sum registry/artifacts/<group>.manifest.json` against old_sha256 / new_sha256 and "
        "new_manifest_digest, and against the sha256 the manifest lists for data/<rel>.\n"
        "  3a. interrupted publish (target is old_sha256 or new_sha256, manifest is the journal's 'manifest' "
        "field or new_manifest_digest): restore the prior or the completed state, then "
        f"`{command} status` rolls back or clears the journal.\n"
        f"  3b. stale journal (manifest changed through a later commit and the target matches the manifest): "
        f"retire it with `mv {journal} {journal}.resolved`.\n"
        f"  4. confirm with `{command} verify --group <group>`."
    )


def _recover_locked(repo: Path) -> int:
    store = paths.artifact_store_root(repo)
    journal_dir = store / ".transactions"
    count = 0
    for journal in sorted(journal_dir.glob("*.json")):
        try:
            count += _recover_journal(repo, store, journal)
        except (OSError, ValueError, KeyError, TypeError, AttributeError) as exc:
            raise RecoveryError(
                f"publish recovery failed for journal {journal}: {exc}\n{_recovery_remediation(journal)}"
            ) from exc
    return count


def _checkout_gone_reason(repo: Path, owner: Path) -> str | None:
    """Return None when ``owner`` is provably a deleted checkout, "" when it is alive, else why we cannot tell.

    ``Path.exists()`` is also False on an unmounted filesystem or an unsearchable parent, so a journal is
    only pruned when the parent is readable, the checkout itself is definitively absent, and the primary's
    ``git worktree list`` does not still register it (an unmounted worktree stays registered).
    """
    parent = owner.parent
    if not parent.is_dir() or not os.access(parent, os.R_OK | os.X_OK):
        return f"parent {parent} is missing or unreadable, so the checkout may only be unreachable"
    try:
        os.lstat(owner)
    except FileNotFoundError:
        pass
    except OSError as exc:
        return f"cannot stat the checkout ({exc})"
    else:
        return ""
    try:
        listing = subprocess.run(
            ["git", "worktree", "list", "--porcelain"],
            cwd=repo,
            capture_output=True,
            text=True,
            timeout=30,
            check=True,
        ).stdout
    except (OSError, subprocess.SubprocessError) as exc:
        return f"cannot list git worktrees ({exc})"
    if any(line == f"worktree {owner}" for line in listing.splitlines()):
        return "still registered in `git worktree list` (run `git worktree prune` once it is truly gone)"
    return None


def _recover_journal(repo: Path, store: Path, journal: Path) -> int:
    """Roll one journal back or clear it; return 1 when handled, 0 when it belongs to another checkout."""
    record = json.loads(journal.read_text(encoding="utf-8"))
    owner = record.get("repo")
    if not isinstance(owner, str) or not owner:
        raise ValueError(f"invalid publish recovery record: {journal}")
    if owner != str(repo.resolve()):
        reason = _checkout_gone_reason(repo, Path(owner))
        if reason is None:
            journal.unlink()
            print(f"artifacts: pruned publish journal {journal} of deleted checkout {owner}", file=sys.stderr)
        elif reason:
            print(f"artifacts: kept publish journal {journal} of checkout {owner}: {reason}", file=sys.stderr)
        return 0
    if record.get("schema") == 2:
        return _recover_set_journal(repo, store, journal, record)
    group = paths.checked_group(record["group"])
    rel = str(paths.checked_rel(record["rel"]))
    manifest = record["manifest"]
    if manifest.get("group") != group or not isinstance(manifest.get("entries"), list):
        raise ValueError(f"invalid publish recovery record: {journal}")
    old = next((item for item in manifest["entries"] if item.get("path") == f"data/{rel}"), None)
    if old is None or old.get("sha256") != record["old_sha256"]:
        raise ValueError(f"inconsistent publish recovery record: {journal}")
    manifest_path = paths.manifest_path(group, repo)
    current_digest = hashlib.sha256(manifest_path.read_bytes()).hexdigest()
    old_digest = _manifest_digest(manifest)
    new_digest = record.get("new_manifest_digest")
    if current_digest not in {old_digest, new_digest} or not isinstance(new_digest, str):
        raise ValueError(f"publish recovery REFUSED: manifest changed after journal {journal}")
    target = _safe_destination(repo, f"data/{rel}", "data")
    target_sha = paths.hash_file(target) if target.is_file() and not target.is_symlink() else None
    if current_digest == new_digest and target_sha == record.get("new_sha256"):
        journal.unlink()
        return 1
    if target_sha not in {None, old["sha256"], record.get("new_sha256")}:
        raise ValueError(f"publish recovery REFUSED: target changed after journal {target}")
    obj = store / old["sha256"]
    if not obj.is_file() or obj.stat().st_size != old["size"] or paths.hash_file(obj) != old["sha256"]:
        raise ValueError(f"missing prior store object for publish recovery: {old['sha256']}")
    target.parent.mkdir(parents=True, exist_ok=True)
    _restore_from_store(obj, target)
    _json_write(manifest_path, manifest)
    paths.verify_file(target, old, group=group, rel=rel)
    journal.unlink()
    return 1


def recover_incomplete(repo: Path) -> int:
    """Roll back any publish interrupted after the durable journal was written."""
    if not (paths.artifact_store_root(repo) / ".transactions").is_dir():
        return 0
    with _lock(repo):
        return _recover_locked(repo)


@dataclass(frozen=True)
class ArtifactChange:
    """An explicit group member mutation; paths are relative to ``data/``."""

    operation: str  # add, replace, remove
    rel: str
    source: Path | None
    expected_sha256: str | None


@dataclass(frozen=True)
class CompanionChange:
    """A tracked companion mutation; path is relative to the repository root."""

    path: str
    source: Path
    expected_sha256: str | None


def _safe_destination(repo: Path, relative: str, root: str) -> Path:
    return paths.checked_destination(repo, relative, root)


def _source_info(source: Path, destinations: set[Path], repo: Path) -> tuple[str, int, str]:
    if not source.is_file() or source.is_symlink():
        raise ValueError(f"missing regular staging file: {source}")
    resolved = source.resolve()
    if (
        resolved in destinations
        or resolved.is_relative_to((repo / "data").resolve())
        or resolved.is_relative_to((repo / "registry").resolve())
    ):
        raise ValueError("publish source must be a separate staging file")
    stat = source.stat()
    return paths.hash_file(source), stat.st_size, f"100{stat.st_mode & 0o777:03o}"


def _registration_allowed(manifest: dict, path: str) -> bool:
    for pattern in manifest.get("registration_patterns", []):
        if not isinstance(pattern, str) or not pattern.startswith("data/"):
            raise ValueError("invalid group registration pattern")
        parent, _, name = pattern.rpartition("/")
        if (
            not 1 <= pattern.count("*") <= 2
            or any(char in parent for char in "*?[]")
            or any(char in name for char in "?[]")
            or len(name.replace("*", "")) < 5
        ):
            raise ValueError(f"registration pattern is not narrow: {pattern}")
        if path.rpartition("/")[0] == parent and fnmatch.fnmatchcase(path, pattern):
            return True
    return False


def _actual_sha(target: Path) -> str | None:
    if target.is_symlink() or (target.exists() and not target.is_file()):
        raise ValueError(f"REFUSED non-regular target: {target}")
    return paths.hash_file(target) if target.is_file() else None


def _actual_mode(target: Path) -> str | None:
    return f"100{target.stat().st_mode & 0o777:03o}" if target.is_file() and not target.is_symlink() else None


def _git_mode(mode: str) -> str:
    return "100755" if int(mode, 8) & 0o111 else "100644"


def _make_temp(target: Path, source: Path, sha: str, mode: str, temp: Path, mtime_ns: int) -> Path:
    _mkdir_durable(target.parent)
    with os.fdopen(os.open(temp, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600), "wb") as stream:
        try:
            with source.open("rb") as reader:
                shutil.copyfileobj(reader, stream)
            os.fchmod(stream.fileno(), int(mode, 8) & 0o777)
            stream.flush()
            os.utime(stream.fileno(), ns=(mtime_ns, mtime_ns))
            os.fsync(stream.fileno())
        except BaseException:
            temp.unlink(missing_ok=True)
            raise
    if paths.hash_file(temp) != sha:
        temp.unlink(missing_ok=True)
        raise ValueError(f"staging file changed during publish: {source}")
    return temp


_SET_TEMP_NAME = re.compile(r"\.lu-artifact-[0-9a-f]{32}-[0-9]+\.tmp\Z")


def _set_temp_paths(repo: Path, record: dict) -> list[Path]:
    """Validate journal-owned temp names before removing any of them."""
    rows = record["rows"] + record["companions"]
    temps = []
    for row in rows:
        name = row.get("temp")
        if name is None:
            continue  # Journals written before named temps remain recoverable.
        if not isinstance(name, str) or not _SET_TEMP_NAME.fullmatch(name) or row.get("new_sha256") is None:
            raise ValueError(f"invalid publish recovery temp: {row['path']}")
        target = _safe_destination(repo, row["path"], "data" if row["kind"] == "artifact" else "registry")
        temp = target.with_name(name)
        if temp.is_symlink() or (temp.exists() and not temp.is_file()):
            raise ValueError(f"publish recovery REFUSED non-regular temp: {temp}")
        temps.append(temp)
    if len(set(temps)) != len(temps):
        raise ValueError("duplicate publish recovery temps")
    return temps


def _cleanup_set_temps(repo: Path, record: dict) -> None:
    for temp in _set_temp_paths(repo, record):
        if not temp.exists():
            continue
        temp.unlink(missing_ok=True)
        _fsync_dir(temp.parent)


def _install(temp: Path | None, target: Path) -> None:
    if temp is None:
        target.unlink(missing_ok=True)
    else:
        os.replace(temp, target)
    _fsync_dir(target.parent)


def _checked_store_object(store: Path, sha: str, size: int) -> Path:
    obj = store / sha
    if not obj.is_file() or obj.is_symlink() or obj.stat().st_size != size or paths.hash_file(obj) != sha:
        raise ValueError(f"missing or corrupt store object: {sha}")
    return obj


def _finish_journal(journal: Path, record: dict) -> None:
    journal.unlink()
    try:
        _fsync_dir(journal.parent)
    except OSError:
        # Keep recovery visible when a one-shot directory sync failure follows
        # the unlink. A persistent storage failure still propagates.
        _json_write(journal, record)
        raise


def _verify_set_state(repo: Path, group: str, manifest: dict) -> None:
    active = {entry["path"] for entry in manifest["entries"]}
    for entry in manifest["entries"]:
        target = _safe_destination(repo, entry["path"], "data")
        paths.verify_file(target, entry, group=group, rel=entry["path"][5:])
        if entry.get("mode") and _git_mode(_actual_mode(target)) != entry["mode"]:
            raise ValueError(f"set member mode differs: {entry['path']}")
    for relative, sha in manifest.get("set_descriptor", {}).get("companions", {}).items():
        if _actual_sha(_safe_destination(repo, relative, "registry")) != sha:
            raise ValueError(f"set companion differs: {relative}")
    for entry in manifest.get("retired", []):
        if entry["path"] not in active and _actual_sha(_safe_destination(repo, entry["path"], "data")) is not None:
            raise ValueError(f"retired path remains: {entry['path']}")


def _recover_set_journal(repo: Path, store: Path, journal: Path, record: dict) -> int:
    group = paths.checked_group(record["group"])
    old_manifest = paths.validate_manifest(record["manifest"], group, str(journal))
    new_manifest = paths.validate_manifest(record["new_manifest"], group, str(journal))
    manifest_path = paths.manifest_path(group, repo)
    current_digest = hashlib.sha256(manifest_path.read_bytes()).hexdigest()
    old_digest = record["old_manifest_digest"]
    new_digest = record["new_manifest_digest"]
    if (
        current_digest not in {old_digest, new_digest}
        or new_digest != _manifest_digest(new_manifest)
        or old_digest != _manifest_digest(old_manifest)
    ):
        raise ValueError(f"publish recovery REFUSED: manifest changed after journal {journal}")
    rows = record["rows"] + record["companions"]
    if len({row["path"] for row in rows}) != len(rows):
        raise ValueError(f"duplicate publish recovery rows: {journal}")
    _set_temp_paths(repo, record)
    old_entries = {entry["path"]: entry for entry in old_manifest["entries"]}
    new_entries = {entry["path"]: entry for entry in new_manifest["entries"]}
    for row in record["rows"]:
        old = old_entries.get(row["path"])
        new = new_entries.get(row["path"])
        if (old["sha256"] if old else None) != row["old_sha256"] or (new["sha256"] if new else None) != row[
            "new_sha256"
        ]:
            raise ValueError(f"inconsistent publish recovery row: {row['path']}")
    checked = []
    for row in rows:
        target = _safe_destination(repo, row["path"], "data" if row["kind"] == "artifact" else "registry")
        actual = _actual_sha(target)
        state = (actual, _actual_mode(target))
        if state not in {
            (row["old_sha256"], row["old_mode"]),
            (row["new_sha256"], row["new_mode"]),
        }:
            raise ValueError(f"publish recovery REFUSED: target changed after journal {target}")
        checked.append((row, target, actual))
    if current_digest == new_digest:
        if any(actual != row["new_sha256"] for row, _, actual in checked):
            raise ValueError(f"publish recovery REFUSED: committed set incomplete {journal}")
        for row, _, _ in checked:
            if row["new_sha256"] is not None:
                _checked_store_object(store, row["new_sha256"], row["new_size"])
        if record.get("strict_set", True):
            _verify_set_state(repo, group, new_manifest)
    else:
        # Validate every rollback source before changing any live pathname.
        for row, _, _ in checked:
            if row["old_sha256"] is not None:
                _checked_store_object(store, row["old_sha256"], row["old_size"])
        for row, target, actual in checked:
            if actual == row["old_sha256"]:
                continue
            if row["old_sha256"] is None:
                _install(None, target)
            else:
                _restore_from_store(store / row["old_sha256"], target, mode=row["old_mode"])
        _json_write(manifest_path, old_manifest)
        if record.get("strict_set", True):
            _verify_set_state(repo, group, old_manifest)
    _cleanup_set_temps(repo, record)
    _finish_journal(journal, record)
    return 1


def publish_set(
    repo: Path,
    group: str,
    artifacts: list[ArtifactChange],
    producer: str,
    *,
    companions: list[CompanionChange] | None = None,
    expected_members: set[str],
) -> dict[str, str | None]:
    """Publish one group's complete intended change set under one durable descriptor."""
    with _lock(repo):
        _recover_locked(repo)
        return _publish_set_locked(repo, group, artifacts, producer, companions or [], expected_members)


def _publish_set_locked(
    repo: Path,
    group: str,
    artifacts: list[ArtifactChange],
    producer: str,
    companions: list[CompanionChange],
    expected_members: set[str],
    *,
    strict_set: bool = True,
) -> dict[str, str | None]:
    manifest = paths.load_manifest(group, repo)
    before = {item["path"][5:]: item for item in manifest["entries"]}
    if set(before) != expected_members:
        raise ValueError("stale expected membership")
    if not artifacts or not producer:
        raise ValueError("publish set requires artifacts and producer")
    if strict_set:
        _verify_set_state(repo, group, manifest)
    if len({change.rel for change in artifacts}) != len(artifacts):
        raise ValueError("duplicate artifact rows")
    if len({change.path for change in companions}) != len(companions):
        raise ValueError("duplicate companion rows")
    destinations: set[Path] = set()
    for change in artifacts:
        destinations.add(_safe_destination(repo, f"data/{change.rel}", "data").absolute())
    for change in companions:
        if not change.path.startswith("registry/"):
            raise ValueError("companion must be under registry/")
        destinations.add(_safe_destination(repo, change.path, "registry").absolute())
    if len(destinations) != len(artifacts) + len(companions):
        raise ValueError("duplicate destinations")
    other_owners = {item["path"]: owner for owner, item in _all_manifests(repo) if owner != group}
    other_patterns = []
    for other_manifest in sorted((repo / "registry/artifacts").glob("*.manifest.json")):
        owner = other_manifest.name.removesuffix(".manifest.json")
        if owner != group:
            other = paths.load_manifest(owner, repo)
            other_patterns.append((owner, other))
            for item in other.get("retired", []):
                other_owners[item["path"]] = owner
    classified = {row["path"] for row in _rows(repo)}
    new_entries = dict(before)
    retired = list(manifest.get("retired", []))
    store = paths.artifact_store_root(repo)
    row_records: list[dict] = []
    companion_records: list[dict] = []
    prepared: list[tuple[Path | None, Path]] = []
    journal = _journal_path(repo, group, "@set")
    try:
        for change in artifacts:
            rel = str(paths.checked_rel(change.rel))
            path = f"data/{rel}"
            target = _safe_destination(repo, path, "data")
            old = before.get(rel)
            if path in other_owners:
                raise ValueError(f"ownership conflict: {path} belongs to {other_owners[path]}")
            if change.operation not in {"add", "replace", "remove"}:
                raise ValueError(f"invalid artifact operation: {change.operation}")
            if change.operation == "add":
                if old is not None or change.expected_sha256 is not None or _actual_sha(target) is not None:
                    raise ValueError(f"add requires prior absence: {path}")
                if path in classified:
                    raise ValueError(f"classified path has no active manifest owner: {path}")
                if any(_registration_allowed(other, path) for _, other in other_patterns):
                    raise ValueError(f"registration ownership conflict: {path}")
                if not _registration_allowed(manifest, path):
                    raise ValueError(f"unregistered addition: {path}")
            else:
                if old is None or change.expected_sha256 != old["sha256"]:
                    raise ValueError(f"stale expected hash: {path}")
                paths.verify_file(target, old, group=group, rel=rel)
            if change.operation == "remove":
                if change.source is not None:
                    raise ValueError(f"remove must not have a source: {path}")
                new_entries.pop(rel)
                retired.append({**old, "retired_at": _now()})
                sha, size, mode = None, None, None
            else:
                if change.source is None:
                    raise ValueError(f"missing source: {path}")
                sha, size, source_mode = _source_info(change.source, destinations, repo)
                mode = old["mode"] if old else _git_mode(source_mode)
                new_entries[rel] = {
                    **(old or {}),
                    "path": path,
                    "mode": mode,
                    "size": size,
                    "sha256": sha,
                    "store": sha,
                    "producer": producer,
                    "published_at": _now(),
                    "mtime_ns": None,
                    **({"supersedes": old["sha256"]} if old else {"rights": "uncleared", "git_blob": None}),
                }
            row_records.append(
                {
                    "kind": "artifact",
                    "path": path,
                    "old_sha256": old["sha256"] if old else None,
                    "old_size": old["size"] if old else None,
                    "old_mode": _actual_mode(target) if old else None,
                    "new_sha256": sha,
                    "new_size": size,
                    "new_mode": _actual_mode(target) if old and sha is not None else source_mode if sha else None,
                }
            )
        for change in companions:
            if change.path.startswith("registry/artifacts/"):
                raise ValueError(f"companion conflicts with artifact metadata: {change.path}")
            target = _safe_destination(repo, change.path, "registry")
            actual = _actual_sha(target)
            if actual != change.expected_sha256:
                raise ValueError(f"dirty K companion or stale expected hash: {change.path}")
            tracked = subprocess.run(["git", "show", f"HEAD:{change.path}"], cwd=repo, capture_output=True, timeout=30)
            if (tracked.returncode == 0) != (actual is not None) or (
                actual is not None and hashlib.sha256(tracked.stdout).hexdigest() != actual
            ):
                raise ValueError(f"dirty K companion: {change.path}")
            if actual is not None:
                tree_line = _git(repo, "ls-tree", "HEAD", "--", change.path).decode().split()
                if not tree_line or tree_line[0] != _git_mode(_actual_mode(target)):
                    raise ValueError(f"dirty K companion mode: {change.path}")
            sha, size, source_mode = _source_info(change.source, destinations, repo)
            mode = f"100{target.stat().st_mode & 0o777:03o}" if actual is not None else source_mode
            companion_records.append(
                {
                    "kind": "companion",
                    "path": change.path,
                    "old_sha256": actual,
                    "old_size": target.stat().st_size if actual is not None else None,
                    "old_mode": mode if actual is not None else None,
                    "new_sha256": sha,
                    "new_size": size,
                    "new_mode": mode,
                }
            )
        # All live versions and staged inputs have been checked. The store copies are
        # durable before any published pathname changes.
        if strict_set:
            changed = {change.rel for change in artifacts}
            for rel, entry in before.items():
                if rel not in changed:
                    _store_copy(_safe_destination(repo, entry["path"], "data"), entry["sha256"], store)
        for row, change in zip(row_records, artifacts, strict=True):
            target = _safe_destination(repo, row["path"], "data")
            if row["old_sha256"] is not None:
                _store_copy(target, row["old_sha256"], store)
            if row["new_sha256"] is not None:
                assert change.source is not None
                _store_copy(change.source, row["new_sha256"], store)
        for row, change in zip(companion_records, companions, strict=True):
            target = _safe_destination(repo, row["path"], "registry")
            if row["old_sha256"] is not None:
                _store_copy(target, row["old_sha256"], store)
            _store_copy(change.source, row["new_sha256"], store)
        for row in row_records + companion_records:
            if row["old_sha256"] is not None:
                _checked_store_object(store, row["old_sha256"], row["old_size"])
            if row["new_sha256"] is not None:
                _checked_store_object(store, row["new_sha256"], row["new_size"])
        transaction = uuid.uuid4().hex
        for index, row in enumerate(row_records + companion_records):
            if row["new_sha256"] is None:
                row["temp"] = None
                continue
            row["temp"] = f".lu-artifact-{transaction}-{index}.tmp"
            target = _safe_destination(repo, row["path"], "data" if row["kind"] == "artifact" else "registry")
            planned_temp = target.with_name(row["temp"])
            try:
                planned_temp.lstat()
            except FileNotFoundError:
                pass
            else:
                raise ValueError(f"engine temp name collision: {planned_temp}")
            row["temp_mtime_ns"] = time.time_ns()
            if row["kind"] == "artifact":
                new_entries[row["path"][5:]]["mtime_ns"] = row["temp_mtime_ns"]
        previous_companions = manifest.get("set_descriptor", {}).get("companions", {})
        for relative, sha in previous_companions.items():
            if relative not in {row["path"] for row in companion_records}:
                target = _safe_destination(repo, relative, "registry")
                if _actual_sha(target) != sha:
                    raise ValueError(f"dirty K companion: {relative}")
                if strict_set:
                    _store_copy(target, sha, store)
        new_manifest = {
            **manifest,
            "entries": [
                new_entries[item["path"][5:]] for item in manifest["entries"] if item["path"][5:] in new_entries
            ]
            + [new_entries[rel] for rel in sorted(set(new_entries) - set(before))],
            "retired": retired,
            "set_descriptor": {
                "members": sorted(new_entries),
                "companions": {
                    **previous_companions,
                    **{row["path"]: row["new_sha256"] for row in companion_records},
                },
            },
        }
        paths.validate_manifest(new_manifest, group, "planned publication")
        if strict_set:
            for entry in new_manifest["entries"] + new_manifest["retired"]:
                _checked_store_object(store, entry["sha256"], entry["size"])
            for sha in new_manifest["set_descriptor"]["companions"].values():
                obj = store / sha
                _checked_store_object(store, sha, obj.stat().st_size)
        record = {
            "schema": 2,
            "repo": str(repo.resolve()),
            "group": group,
            "strict_set": strict_set,
            "rows": row_records,
            "companions": companion_records,
            "manifest": manifest,
            "old_manifest_digest": hashlib.sha256(paths.manifest_path(group, repo).read_bytes()).hexdigest(),
            "new_manifest": new_manifest,
            "new_manifest_digest": _manifest_digest(new_manifest),
        }
        _json_write(journal, record)
        for row in row_records + companion_records:
            target = _safe_destination(repo, row["path"], "data" if row["kind"] == "artifact" else "registry")
            if row["new_sha256"] is None:
                prepared.append((None, target))
                continue
            temp = _make_temp(
                target,
                store / row["new_sha256"],
                row["new_sha256"],
                row["new_mode"],
                target.with_name(row["temp"]),
                row["temp_mtime_ns"],
            )
            prepared.append((temp, target))
        for temp, target in prepared:
            _install(temp, target)
        for row in row_records + companion_records:
            target = _safe_destination(repo, row["path"], "data" if row["kind"] == "artifact" else "registry")
            if _actual_sha(target) != row["new_sha256"]:
                raise ValueError(f"installed set differs: {row['path']}")
        if strict_set:
            _verify_set_state(repo, group, new_manifest)
        _json_write(paths.manifest_path(group, repo), new_manifest)
        _finish_journal(journal, record)
        return {row["path"][5:]: row["new_sha256"] for row in row_records}
    except BaseException:
        if journal.exists():
            current_digest = hashlib.sha256(paths.manifest_path(group, repo).read_bytes()).hexdigest()
            if current_digest != _manifest_digest(new_manifest):
                _recover_locked(repo)
        raise
    finally:
        for temp, _ in prepared:
            if temp is not None:
                temp.unlink(missing_ok=True)


def publish(repo: Path, group: str, rel: str, source: Path, producer: str) -> str:
    """Publish one existing member through the set engine (legacy caller contract)."""
    paths.checked_rel(rel)
    with _lock(repo):
        _recover_locked(repo)
        manifest = paths.load_manifest(group, repo)
        old = next((item for item in manifest["entries"] if item["path"] == f"data/{rel}"), None)
        if old is None:
            paths.find_entry(group, rel, repo)  # Preserve the legacy missing-entry error.
        result = _publish_set_locked(
            repo,
            group,
            [ArtifactChange("replace", rel, source, old["sha256"])],
            producer,
            [],
            {item["path"][5:] for item in manifest["entries"]},
            strict_set=False,
        )
        return result[rel]


def write_artifact_set(
    repo: Path,
    group: str,
    producer: str,
    writes: dict[str, Callable[[Path], object]],
    *,
    expected_hashes: dict[str, str | None],
    expected_members: set[str],
    removals: dict[str, str] | None = None,
    companions: dict[str, tuple[str | None, Callable[[Path], object]]] | None = None,
) -> dict[str, str | None]:
    """Stage all writer outputs, then publish their explicit membership change."""
    removals = removals or {}
    companions = companions or {}
    if set(writes) != set(expected_hashes) or set(writes) & set(removals):
        raise ValueError("write set needs one expected hash per write and no duplicate removals")
    with tempfile.TemporaryDirectory(prefix="artifact-set-stage-") as staging:
        stage = Path(staging)
        changes = []
        companion_changes = []
        for index, (rel, write) in enumerate(writes.items()):
            source = stage / f"artifact-{index}"
            write(source)
            expected = expected_hashes[rel]
            changes.append(ArtifactChange("add" if expected is None else "replace", rel, source, expected))
        for rel, expected in removals.items():
            changes.append(ArtifactChange("remove", rel, None, expected))
        for index, (relative, (expected, write)) in enumerate(companions.items()):
            source = stage / f"companion-{index}"
            write(source)
            companion_changes.append(CompanionChange(relative, source, expected))
        return publish_set(
            repo, group, changes, producer, companions=companion_changes, expected_members=expected_members
        )


def write_artifact(
    target: Path, group: str, producer: str, write: Callable[[Path], object], *, repo: Path = ROOT
) -> Path:
    """Run ``write`` for ``target``; publish through a staging file when it is a manifest artifact.

    A producer's default output may be a published A path (spec section 3: only ``publish`` writes it).
    The target is resolved against every A manifest: a path owned by ``group`` is published, a path owned by
    any other group raises ``ValueError`` and nothing is written. An unregistered output under a
    migrated A tree is refused; specific pre-existing host-state paths and scratch paths remain direct.
    """
    data_root = (repo / "data").absolute()
    lexical_target = Path(os.path.abspath(target))
    resolved = Path(target).resolve()
    manifests = _all_manifests(repo)
    trees = _migrated_a_trees(repo)

    def ownership(path: Path) -> tuple[str | None, list[str]]:
        if not path.is_relative_to(data_root):
            return None, []
        rel = path.relative_to(data_root).as_posix()
        return rel, sorted({owner for owner, entry in manifests if entry["path"] == f"data/{rel}"})

    lexical_rel, lexical_owners = ownership(lexical_target)
    resolved_rel, resolved_owners = ownership(resolved)
    for rel, owners in ((lexical_rel, lexical_owners), (resolved_rel, resolved_owners)):
        if owners and group not in owners:
            raise ValueError(f"data/{rel} is a published artifact of group {', '.join(owners)}, not {group}")
    if lexical_owners and lexical_target != resolved:
        raise ValueError(f"data/{lexical_rel} is a published artifact reached through a symlink")
    for path, rel, owners in ((lexical_target, lexical_rel, lexical_owners), (resolved, resolved_rel, resolved_owners)):
        if (
            rel is not None
            and not owners
            and any(path.is_relative_to(tree) for tree in trees)
            and not _lexicon_host_state(repo, path)
        ):
            if (
                path != resolved
                or rel != resolved_rel
                or not paths.manifest_path(group, repo).is_file()
                or not (_registration_allowed(paths.load_manifest(group, repo), f"data/{rel}"))
            ):
                raise ValueError(
                    f"data/{rel} is under a migrated artifact tree but has no manifest entry; "
                    "register the output in its artifact group before writing"
                )
            if any(row["path"] == f"data/{rel}" and row["group"] != group for row in _rows(repo)):
                raise ValueError(f"data/{rel} is classified in another artifact group")
            with tempfile.TemporaryDirectory(prefix="publish-stage-") as staging:
                staged = Path(staging) / resolved.name
                write(staged)
                manifest = paths.load_manifest(group, repo)
                publish_set(
                    repo,
                    group,
                    [ArtifactChange("add", rel, staged, None)],
                    producer,
                    expected_members={item["path"][5:] for item in manifest["entries"]},
                )
            return resolved
    rel = lexical_rel if lexical_owners else resolved_rel if resolved_owners else None
    if rel is not None and (lexical_owners or resolved_owners):
        with tempfile.TemporaryDirectory(prefix="publish-stage-") as staging:
            staged = Path(staging) / resolved.name
            write(staged)
            publish(repo, group, rel, staged, producer)
        return resolved
    write(Path(target))
    return Path(target)


def _restore_from_store(object_path: Path, target: Path, *, mode: str | None = None) -> None:
    _mkdir_durable(target.parent)
    with tempfile.NamedTemporaryFile(dir=target.parent, delete=False) as stream:
        temp = Path(stream.name)
        try:
            with object_path.open("rb") as reader:
                shutil.copyfileobj(reader, stream)
            if mode is not None:
                os.fchmod(stream.fileno(), int(mode, 8) & 0o777)
            stream.flush()
            os.fsync(stream.fileno())
        except BaseException:
            temp.unlink(missing_ok=True)
            raise
    try:
        os.replace(temp, target)
        _fsync_dir(target.parent)
    finally:
        temp.unlink(missing_ok=True)


def export_group(repo: Path, group: str, output: Path) -> int:
    manifest = paths.load_manifest(group, repo)
    store = paths.artifact_store_root(repo)
    objects = {}
    for entry in manifest["entries"] + manifest.get("retired", []):
        sha = entry["sha256"]
        obj = store / sha
        if not obj.is_file() or obj.stat().st_size != entry["size"] or paths.hash_file(obj) != sha:
            raise ValueError(f"missing or corrupt store object: {sha}")
        objects[sha] = obj
    with tarfile.open(output, "w:gz") as archive:
        data = json.dumps(manifest, sort_keys=True).encode()
        info = tarfile.TarInfo("manifest.json")
        info.size = len(data)
        archive.addfile(info, io.BytesIO(data))
        for sha, obj in sorted(objects.items()):
            archive.add(obj, arcname=f"objects/{sha}", recursive=False)
    return len(objects)


def import_tarball(repo: Path, tarball: Path) -> int:
    with _lock(repo):
        _recover_locked(repo)
        return _import_tarball_locked(repo, tarball)


def _import_tarball_locked(repo: Path, tarball: Path) -> int:
    with tarfile.open(tarball, "r:gz") as archive:
        manifest_member = archive.getmember("manifest.json")
        if not manifest_member.isfile():
            raise ValueError("archive manifest is not a regular file")
        manifest_stream = archive.extractfile(manifest_member)
        assert manifest_stream is not None
        manifest = json.load(manifest_stream)
        group = paths.checked_group(manifest["group"])
        local = paths.load_manifest(group, repo)
        local_entries = {entry["path"]: (entry["sha256"], entry["size"]) for entry in local["entries"]}
        imported_entries = {entry["path"]: (entry["sha256"], entry["size"]) for entry in manifest["entries"]}
        if imported_entries != local_entries:
            raise ValueError("import manifest differs from checkout manifest")
        imported_retired = {(entry["path"], entry["sha256"], entry["size"]) for entry in manifest.get("retired", [])}
        local_retired = {(entry["path"], entry["sha256"], entry["size"]) for entry in local.get("retired", [])}
        if imported_retired != local_retired:
            raise ValueError("import retirement metadata differs from checkout manifest")
        expected = {entry["sha256"]: entry["size"] for entry in manifest["entries"] + manifest.get("retired", [])}
        members = {member.name: member for member in archive.getmembers() if member.name != "manifest.json"}
        if set(members) != {f"objects/{sha}" for sha in expected}:
            raise ValueError("archive object set differs from manifest")
        store = paths.artifact_store_root(repo)
        store.mkdir(parents=True, exist_ok=True)
        for sha, size in expected.items():
            member = members[f"objects/{sha}"]
            if not member.isfile() or member.size != size:
                raise ValueError(f"invalid object {sha}")
            reader = archive.extractfile(member)
            assert reader is not None
            with tempfile.NamedTemporaryFile(dir=store, delete=False) as stream:
                temp = Path(stream.name)
                try:
                    digest = hashlib.sha256()
                    while chunk := reader.read(1024 * 1024):
                        digest.update(chunk)
                        stream.write(chunk)
                except BaseException:
                    temp.unlink(missing_ok=True)
                    raise
            try:
                if digest.hexdigest() != sha or temp.stat().st_size != size:
                    raise ValueError(f"tampered object {sha}")
                os.replace(temp, store / sha)
            finally:
                temp.unlink(missing_ok=True)
    return len(expected)


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Manage manifests and host-local artifacts for the data/ split.\nUse before and after migration phases; do not write published A paths directly.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Examples:\n  /home/ops/learn-ukrainian/.venv/bin/python -m scripts.storage.artifacts manifest build --group raw_source --pre HEAD\n"
            "  /home/ops/learn-ukrainian/.venv/bin/python -m scripts.storage.artifacts snapshot --phase P1\n"
            "  /home/ops/learn-ukrainian/.venv/bin/python -m scripts.storage.artifacts snapshot --phase P2 --manifests-ref origin/<phase-branch>\n"
            "  /home/ops/learn-ukrainian/.venv/bin/python -m scripts.storage.artifacts hydrate --group raw_source\n"
            "Outputs: tracked registry/artifacts manifests; untracked host store objects and hydrated data files.\n"
            "Exit codes: 0 = success; 1 = missing, corrupt, or failed operation; 2 = invalid arguments.\n"
            "Related: issue #8809 spec v3.3 sections 3, 4, and 8."
        ),
    )
    sub = parser.add_subparsers(
        dest="command", required=True, help="Artifact operation; use COMMAND --help for its arguments."
    )
    manifest = sub.add_parser(
        "manifest",
        help="Create pre-untrack migration entries.",
        description="Build a migration manifest from the pre-phase Git commit and matching disk bytes.",
    )
    manifest_sub = manifest.add_subparsers(dest="manifest_command", required=True, help="Manifest operation.")
    build = manifest_sub.add_parser("build", help="Build a group migration manifest after disk/blob verification.")
    build.add_argument("--group", required=True, help="Classification group, for example raw_source.")
    build.add_argument("--pre", required=True, help="Pre-untrack commit containing A files, for example origin/main.")
    snap = sub.add_parser(
        "snapshot",
        help="Copy and hash a phase's current active A files into the host store.",
        description=(
            "Copy a phase's active A files into the host store after verifying their manifest hashes.\n"
            "Run in every long-lived checkout before the phase PR merges; use --manifests-ref while the\n"
            "phase manifests exist only on the unmerged phase branch."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Example (checkout still at main, phase branch fetched first with git fetch origin <phase-branch>):\n"
            "  /home/ops/learn-ukrainian/.venv/bin/python -m scripts.storage.artifacts snapshot --phase P2 --manifests-ref origin/<phase-branch>\n"
            "Outputs: store objects only; the working tree, index, and branch are unchanged.\n"
            "Exit codes: 0 = every phase artifact stored; 1 = missing ref or manifest, or failed proof; 2 = invalid arguments."
        ),
    )
    snap.add_argument("--phase", required=True, help="Migration phase P1, P2, P3, P4, or P5.")
    snap.add_argument(
        "--manifests-ref",
        metavar="REF",
        help=(
            "Git ref whose registry/artifacts/<group>.manifest.json files are read with git show, for example "
            "origin/<phase-branch>; the ref must be fetched first (default: the working-tree manifests)."
        ),
    )
    hyd = sub.add_parser("hydrate", help="Restore current files from host store, then available Git blobs.")
    hyd.add_argument(
        "--force-preserve",
        action="store_true",
        help="Preserve divergent target bytes in store and divergent log before replacing them (default: refuse).",
    )
    exclusive = hyd.add_mutually_exclusive_group(required=True)
    exclusive.add_argument("--group", help="Classification group to hydrate, for example raw_source.")
    exclusive.add_argument("--phase", help="Migration phase to hydrate, for example P1.")
    ver = sub.add_parser("verify", help="Always hash current artifact files against manifests.")
    ver.add_argument("--group", help="Optional group; default checks every manifest, for example raw_source.")
    pub = sub.add_parser(
        "publish", help="Publish staged bytes and replace a current manifest version under an exclusive lock."
    )
    pub.add_argument("--group", required=True, help="Existing artifact group, for example raw_source.")
    pub.add_argument("--path", required=True, help="Target path relative to data/, for example raw/pravopys.html.")
    pub.add_argument("--source", required=True, type=Path, help="Separate staging file containing the new bytes.")
    pub.add_argument(
        "--producer", required=True, help="Producer name or command to record, for example scripts/build_raw.py."
    )
    pub_set = sub.add_parser(
        "publish-set",
        help="Publish explicit add/replace/remove rows and tracked companions as one group set.",
        description=(
            "Publish a staged A and K change set with one crash-recoverable group descriptor.\n"
            "Use after all outputs are staged and validated; do not point sources at live data or registry paths."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Example: /home/ops/learn-ukrainian/.venv/bin/python -m scripts.storage.artifacts "
            "publish-set --plan /tmp/group-plan.json\n"
            "Plan JSON: group, producer, expected_members (data-relative strings), artifacts "
            "(operation, rel, source, expected_sha256), companions (path, source, expected_sha256).\n"
            "Outputs: published A paths, tracked K companions, group manifest, and host store objects; "
            "prints the new A hashes.\n"
            "Exit codes: 0 = durable commit; 1 = refused or failed publication; 2 = invalid CLI arguments.\n"
            "Related: issue #8907 and docs/runbooks/storage-topology.md."
        ),
    )
    pub_set.add_argument(
        "--plan",
        required=True,
        type=Path,
        help="JSON plan with group, producer, expected_members, artifacts and companions; sources are staged paths.",
    )
    exp = sub.add_parser("export", help="Verify and write a group tarball for another required host.")
    exp.add_argument("--group", required=True, help="Classification group, for example raw_source.")
    exp.add_argument(
        "--output", required=True, type=Path, help="Output tarball path, for example /tmp/raw-source.tar.gz."
    )
    imp = sub.add_parser("import", help="Verify every tarball object against the local tracked manifest.")
    imp.add_argument("tarball", type=Path, help="Tarball produced by export, for example /tmp/raw-source.tar.gz.")
    sub.add_parser(
        "status",
        help="Show manifest entry counts and current store availability.",
        description="Report manifest entry counts and available store objects without creating a store.",
    )
    return parser


def main(argv: list[str] | None = None, *, repo: Path = ROOT) -> int:
    args = _parser().parse_args(argv)
    try:
        # An abrupt process death cannot run publish's in-process rollback.
        # Restore the prior version before any subsequent operation observes it.
        recover_incomplete(repo)
        if args.command == "manifest":
            count = manifest_build(repo, args.group, args.pre)
        elif args.command == "snapshot":
            count = snapshot(repo, args.phase, manifests_ref=args.manifests_ref)
        elif args.command == "hydrate":
            entries = (
                _phase_entries(repo, args.phase)
                if args.phase
                else [(args.group, entry) for entry in paths.load_manifest(args.group, repo)["entries"]]
            )
            count = hydrate(
                repo,
                entries,
                force_preserve=args.force_preserve,
                groups=phase_groups(repo, args.phase) if args.phase else {args.group},
            )
        elif args.command == "verify":
            entries = (
                [(args.group, entry) for entry in paths.load_manifest(args.group, repo)["entries"]]
                if args.group
                else _all_manifests(repo)
            )
            count = verify(
                repo,
                entries,
                groups={args.group}
                if args.group
                else {
                    path.name.removesuffix(".manifest.json")
                    for path in (repo / "registry/artifacts").glob("*.manifest.json")
                },
            )
        elif args.command == "publish":
            print(publish(repo, args.group, args.path, args.source, args.producer))
            return 0
        elif args.command == "publish-set":
            plan = json.loads(args.plan.read_text(encoding="utf-8"))
            changes = [
                ArtifactChange(
                    row["operation"],
                    row["rel"],
                    Path(row["source"]) if row.get("source") else None,
                    row.get("expected_sha256"),
                )
                for row in plan["artifacts"]
            ]
            companion_changes = [
                CompanionChange(row["path"], Path(row["source"]), row.get("expected_sha256"))
                for row in plan.get("companions", [])
            ]
            result = publish_set(
                repo,
                plan["group"],
                changes,
                plan["producer"],
                companions=companion_changes,
                expected_members=set(plan["expected_members"]),
            )
            print(json.dumps(result, sort_keys=True))
            return 0
        elif args.command == "export":
            count = export_group(repo, args.group, args.output)
        elif args.command == "import":
            count = import_tarball(repo, args.tarball)
        else:
            entries = _all_manifests(repo)
            store = paths.artifact_store_root(repo)
            present = sum((store / entry["sha256"]).is_file() for _, entry in entries)
            print(
                f"manifests={len({group for group, _ in entries})} entries={len(entries)} store_objects_present={present}"
            )
            return 0
        print(f"{args.command}: {count} artifact(s)")
        return 0
    except (OSError, ValueError, KeyError, subprocess.CalledProcessError, tarfile.TarError) as error:
        print(f"{args.command}: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
