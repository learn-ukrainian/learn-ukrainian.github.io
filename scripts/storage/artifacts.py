"""Manage migration manifests and the host-local content-addressed artifact store."""

from __future__ import annotations

import argparse
import contextlib
import csv
import datetime as dt
import fcntl
import hashlib
import io
import json
import os
import shutil
import subprocess
import tarfile
import tempfile
import time
from collections.abc import Callable
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
    path.parent.mkdir(parents=True, exist_ok=True)
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
    finally:
        temp.unlink(missing_ok=True)


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


def _phase_entries(repo: Path, phase: str) -> list[tuple[str, dict]]:
    selected = {row["path"] for row in _rows(repo) if row["class"] == "A" and _phase(row) == phase}
    result = []
    for group in phase_groups(repo, phase):
        manifest = paths.load_manifest(group, repo)
        result.extend((group, entry) for entry in manifest["entries"] if entry["path"] in selected)
    if len(result) != len(selected):
        raise ValueError(f"phase {phase}: manifest coverage {len(result)} != {len(selected)}")
    return result


def _all_manifests(repo: Path) -> list[tuple[str, dict]]:
    result = []
    for path in sorted((repo / "registry/artifacts").glob("*.manifest.json")):
        group = path.name.removesuffix(".manifest.json")
        for entry in paths.load_manifest(group, repo)["entries"]:
            result.append((group, entry))
    return result


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
        disk = repo / rel
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
    store.mkdir(parents=True, exist_ok=True)
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
    finally:
        temp.unlink(missing_ok=True)


def snapshot(repo: Path, phase: str) -> int:
    with _lock(repo):
        return _snapshot_locked(repo, phase)


def _snapshot_locked(repo: Path, phase: str) -> int:
    entries = _phase_entries(repo, phase)
    store = paths.artifact_store_root(repo)
    for group, entry in entries:
        rel = _entry_rel(entry)
        source = repo / entry["path"]
        paths.verify_file(source, entry, group=group, rel=rel)
        blob = entry.get("git_blob")
        if not blob or not _blob_present(repo, blob) or _sha_blob(repo, blob) != entry.get("pre_untrack_sha256"):
            raise ValueError(f"pre-untrack blob proof failed: {entry['path']}")
        if entry["sha256"] != entry["pre_untrack_sha256"]:
            raise ValueError(f"snapshot requires migration version: {entry['path']}")
        _store_copy(source, entry["sha256"], store)
    return len(entries)


def _restore_from_blob(repo: Path, blob: str, target: Path, sha: str) -> None:
    if not _blob_present(repo, blob):
        raise FileNotFoundError(f"git blob unavailable: {blob}")
    target.parent.mkdir(parents=True, exist_ok=True)
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
    finally:
        temp.unlink(missing_ok=True)


def hydrate(repo: Path, entries: list[tuple[str, dict]], *, force_preserve: bool = False) -> int:
    with _lock(repo):
        return _hydrate_locked(repo, entries, force_preserve=force_preserve)


def _hydrate_locked(repo: Path, entries: list[tuple[str, dict]], *, force_preserve: bool) -> int:
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
    return count


def _hydrate_one(repo: Path, group: str, entry: dict, store: Path, *, force_preserve: bool) -> None:
    rel = _entry_rel(entry)
    target = repo / entry["path"]
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
                    print(f"warning: corrupt store object {sha}; repairing from target", file=__import__("sys").stderr)
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
        _restore_from_store(obj, target)
    elif blob and _blob_present(repo, blob) and _sha_blob(repo, blob) == sha:
        if obj.exists() or obj.is_symlink():
            print(f"warning: corrupt store object {sha}; using git blob", file=__import__("sys").stderr)
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


def verify(repo: Path, entries: list[tuple[str, dict]]) -> int:
    store = paths.artifact_store_root(repo)
    failures = []
    for group, entry in entries:
        try:
            paths.verify_file(repo / entry["path"], entry, group=group, rel=_entry_rel(entry))
            obj = store / entry["sha256"]
            if not obj.is_file() or obj.stat().st_size != entry["size"] or paths.hash_file(obj) != entry["sha256"]:
                raise ValueError(f"missing or corrupt store object: {entry['sha256']}")
        except (OSError, ValueError) as exc:
            failures.append(f"{entry['path']}: {exc}")
    if failures:
        raise ValueError(f"verify: {len(failures)} artifact(s) failed:\n" + "\n".join(failures))
    return len(entries)


@contextlib.contextmanager
def _lock(repo: Path):
    store = paths.artifact_store_root(repo)
    store.mkdir(parents=True, exist_ok=True)
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


def _recover_locked(repo: Path) -> int:
    store = paths.artifact_store_root(repo)
    journal_dir = store / ".transactions"
    count = 0
    for journal in sorted(journal_dir.glob("*.json")):
        record = json.loads(journal.read_text(encoding="utf-8"))
        if record.get("repo") != str(repo.resolve()):
            continue
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
        target = repo / "data" / rel
        target_sha = paths.hash_file(target) if target.is_file() and not target.is_symlink() else None
        if current_digest == new_digest and target_sha == record.get("new_sha256"):
            journal.unlink()
            count += 1
            continue
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
        count += 1
    return count


def recover_incomplete(repo: Path) -> int:
    """Roll back any publish interrupted after the durable journal was written."""
    if not (paths.artifact_store_root(repo) / ".transactions").is_dir():
        return 0
    with _lock(repo):
        return _recover_locked(repo)


def publish(repo: Path, group: str, rel: str, source: Path, producer: str) -> str:
    paths.checked_rel(rel)
    with _lock(repo):
        _recover_locked(repo)
        manifest = paths.load_manifest(group, repo)
        entry = paths.find_entry(group, rel, repo)
        target = repo / "data" / rel
        if source.resolve() == target.resolve():
            raise ValueError("publish source must be a separate staging file")
        if not source.is_file() or source.is_symlink():
            raise ValueError(f"missing staging file: {source}")
        paths.verify_file(target, entry, group=group, rel=rel)
        sha = paths.hash_file(source)
        size = source.stat().st_size
        store = paths.artifact_store_root(repo)
        _store_copy(target, entry["sha256"], store)
        _store_copy(source, sha, store)
        replacement = {
            **entry,
            "size": size,
            "sha256": sha,
            "store": sha,
            "producer": producer,
            "published_at": _now(),
            "supersedes": entry["sha256"],
            "mtime_ns": None,
        }
        new_manifest = {
            **manifest,
            "entries": [replacement if item["path"] == entry["path"] else item for item in manifest["entries"]],
        }
        # The lock excludes writers. The old object is kept for rollback if a rename fails.
        target.parent.mkdir(parents=True, exist_ok=True)
        with tempfile.NamedTemporaryFile(dir=target.parent, delete=False) as stream:
            temp = Path(stream.name)
            try:
                with source.open("rb") as reader:
                    shutil.copyfileobj(reader, stream)
                stream.flush()
                os.fsync(stream.fileno())
            except BaseException:
                temp.unlink(missing_ok=True)
                raise
        journal = _journal_path(repo, group, rel)
        try:
            if paths.hash_file(temp) != sha:
                raise ValueError("staging file changed during publish")
            # The rename preserves the temporary file's timestamp.
            replacement["mtime_ns"] = temp.stat().st_mtime_ns
            _json_write(
                journal,
                {
                    "repo": str(repo.resolve()),
                    "group": group,
                    "rel": rel,
                    "old_sha256": entry["sha256"],
                    "new_sha256": sha,
                    "new_manifest_digest": _manifest_digest(new_manifest),
                    "manifest": manifest,
                },
            )
            os.replace(temp, target)
            replacement["mtime_ns"] = target.stat().st_mtime_ns
            _json_write(paths.manifest_path(group, repo), new_manifest)
        except BaseException:
            if journal.exists():
                _recover_locked(repo)
            raise
        finally:
            temp.unlink(missing_ok=True)
        paths.verify_file(target, replacement, group=group, rel=rel)
        journal.unlink()
        return sha


def write_artifact(
    target: Path, group: str, producer: str, write: Callable[[Path], object], *, repo: Path = ROOT
) -> Path:
    """Run ``write`` for ``target``; publish through a staging file when it is a manifest artifact.

    A producer's default output may be a published A path (spec section 3: only ``publish`` writes it).
    The target is resolved against every A manifest: a path owned by ``group`` is published, a path owned by
    any other group raises ``ValueError`` and nothing is written. Any other output path, such as a scratch or
    test path, is written directly.
    """
    data_root = (repo / "data").resolve()
    resolved = Path(target).resolve()
    if resolved.is_relative_to(data_root):
        rel = resolved.relative_to(data_root).as_posix()
        owners = sorted({owner for owner, entry in _all_manifests(repo) if entry["path"] == f"data/{rel}"})
        if owners and group not in owners:
            raise ValueError(f"data/{rel} is a published artifact of group {', '.join(owners)}, not {group}")
        if owners:
            with tempfile.TemporaryDirectory(prefix="publish-stage-") as staging:
                staged = Path(staging) / resolved.name
                write(staged)
                publish(repo, group, rel, staged, producer)
            return resolved
    write(Path(target))
    return Path(target)


def _restore_from_store(object_path: Path, target: Path) -> None:
    with tempfile.NamedTemporaryFile(dir=target.parent, delete=False) as stream:
        temp = Path(stream.name)
        try:
            with object_path.open("rb") as reader:
                shutil.copyfileobj(reader, stream)
        except BaseException:
            temp.unlink(missing_ok=True)
            raise
    try:
        os.replace(temp, target)
    finally:
        temp.unlink(missing_ok=True)


def export_group(repo: Path, group: str, output: Path) -> int:
    manifest = paths.load_manifest(group, repo)
    store = paths.artifact_store_root(repo)
    objects = {}
    for entry in manifest["entries"]:
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
        expected = {entry["sha256"]: entry["size"] for entry in manifest["entries"]}
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
    snap = sub.add_parser("snapshot", help="Copy and hash a phase's migration A files into the host store.")
    snap.add_argument("--phase", required=True, help="Migration phase P1, P2, P3, P4, or P5.")
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
            count = snapshot(repo, args.phase)
        elif args.command == "hydrate":
            entries = (
                _phase_entries(repo, args.phase)
                if args.phase
                else [(args.group, entry) for entry in paths.load_manifest(args.group, repo)["entries"]]
            )
            count = hydrate(repo, entries, force_preserve=args.force_preserve)
        elif args.command == "verify":
            entries = (
                [(args.group, entry) for entry in paths.load_manifest(args.group, repo)["entries"]]
                if args.group
                else _all_manifests(repo)
            )
            count = verify(repo, entries)
        elif args.command == "publish":
            print(publish(repo, args.group, args.path, args.source, args.producer))
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
        print(f"{args.command}: {error}", file=__import__("sys").stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
