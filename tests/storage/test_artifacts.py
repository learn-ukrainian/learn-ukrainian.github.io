"""Held-out storage mechanics in disposable Git repositories."""

from __future__ import annotations

import csv
import hashlib
import io
import json
import os
import signal
import subprocess
import sys
import tarfile
from pathlib import Path

import pytest

from scripts.storage import artifacts, paths


def git(repo: Path, *args: str) -> str:
    return subprocess.check_output(["git", *args], cwd=repo, text=True, timeout=30).strip()


@pytest.fixture
def repo(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    monkeypatch.delenv("LU_ARTIFACT_STORE", raising=False)
    root = tmp_path / "repo"
    root.mkdir()
    subprocess.run(["git", "init", "-q", root], check=True, timeout=30)
    subprocess.run(["git", "config", "user.email", "test@example.invalid"], cwd=root, check=True, timeout=30)
    subprocess.run(["git", "config", "user.name", "Test"], cwd=root, check=True, timeout=30)
    (root / "data/raw").mkdir(parents=True)
    (root / "data/raw/source.txt").write_bytes(b"alpha")
    (root / "registry/artifacts").mkdir(parents=True)
    with (root / "registry/artifacts/classification-v1.tsv").open("w", newline="") as stream:
        writer = csv.writer(stream, delimiter="\t")
        writer.writerow(("path", "mode", "blob", "size", "class", "group", "reason", "judgment"))
        writer.writerow(("data/raw/source.txt", "100644", "", "5", "A", "raw_source", "external; preserve", "rule"))
    subprocess.run(["git", "add", "."], cwd=root, check=True, timeout=30)
    subprocess.run(["git", "commit", "-qm", "base"], cwd=root, check=True, timeout=30)
    assert artifacts.manifest_build(root, "raw_source", "HEAD") == 1
    return root


def entries(repo: Path) -> list[tuple[str, dict]]:
    return [("raw_source", entry) for entry in paths.load_manifest("raw_source", repo)["entries"]]


def test_manifest_build_and_snapshot_verify_disk_against_blob(repo: Path) -> None:
    assert artifacts.snapshot(repo, "P1") == 1
    item = entries(repo)[0][1]
    blob = git(repo, "rev-parse", "HEAD:data/raw/source.txt")
    assert item["git_blob"] == blob
    assert item["pre_untrack_sha256"] == hashlib.sha256(b"alpha").hexdigest()
    assert (paths.artifact_store_root(repo) / item["sha256"]).read_bytes() == b"alpha"
    (repo / "data/raw/source.txt").write_bytes(b"other")
    with pytest.raises(ValueError, match="disk differs"):
        (repo / "registry/artifacts/raw_source.manifest.json").unlink()
        artifacts.manifest_build(repo, "raw_source", "HEAD")


def test_store_first_hydrate_in_shallow_clone(repo: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    artifacts.snapshot(repo, "P1")
    subprocess.run(["git", "add", "registry"], cwd=repo, check=True, timeout=30)
    subprocess.run(
        ["git", "rm", "--cached", "data/raw/source.txt"], cwd=repo, check=True, stdout=subprocess.DEVNULL, timeout=30
    )
    (repo / ".gitignore").write_text("data/\n")
    subprocess.run(["git", "add", ".gitignore"], cwd=repo, check=True, timeout=30)
    subprocess.run(["git", "commit", "-qm", "untrack"], cwd=repo, check=True, timeout=30)
    shallow = tmp_path / "shallow"
    subprocess.run(["git", "clone", "-q", "--depth", "1", f"file://{repo}", str(shallow)], check=True, timeout=30)
    assert git(shallow, "rev-parse", "--is-shallow-repository") == "true"
    item = entries(shallow)[0][1]
    assert (
        subprocess.run(
            ["git", "cat-file", "-e", item["git_blob"]], cwd=shallow, stderr=subprocess.DEVNULL, timeout=30
        ).returncode
        != 0
    )
    monkeypatch.setenv("LU_ARTIFACT_STORE", str(paths.artifact_store_root(repo)))
    assert artifacts.hydrate(shallow, entries(shallow)) == 1
    assert (shallow / "data/raw/source.txt").read_bytes() == b"alpha"
    assert artifacts.verify(shallow, entries(shallow)) == 1


def test_import_rejects_tampered_object(repo: Path, tmp_path: Path) -> None:
    artifacts.snapshot(repo, "P1")
    bundle = tmp_path / "group.tar.gz"
    assert artifacts.export_group(repo, "raw_source", bundle) == 1
    bad = tmp_path / "bad.tar.gz"
    with tarfile.open(bundle, "r:gz") as source, tarfile.open(bad, "w:gz") as target:
        for member in source.getmembers():
            stream = source.extractfile(member)
            assert stream is not None
            data = stream.read()
            if member.name.startswith("objects/"):
                data = b"omega"
            info = tarfile.TarInfo(member.name)
            info.size = len(data)
            target.addfile(info, io.BytesIO(data))
    with pytest.raises(ValueError, match="tampered"):
        artifacts.import_tarball(repo, bad)


def test_publish_rollback_on_failed_manifest_replace(
    repo: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    stage = tmp_path / "stage"
    stage.write_bytes(b"bravo")
    original_write = artifacts._json_write

    def fail_manifest(path: Path, value: object) -> None:
        if path == repo / "registry/artifacts/raw_source.manifest.json":
            raise RuntimeError("injected interruption")
        original_write(path, value)

    monkeypatch.setattr(artifacts, "_json_write", fail_manifest)
    with pytest.raises(RuntimeError, match="injected interruption"):
        artifacts.publish(repo, "raw_source", "raw/source.txt", stage, "test")
    monkeypatch.setattr(artifacts, "_json_write", original_write)
    assert (repo / "data/raw/source.txt").read_bytes() == b"alpha"
    assert paths.load_manifest("raw_source", repo)["entries"][0]["sha256"] == hashlib.sha256(b"alpha").hexdigest()
    assert (
        artifacts.publish(repo, "raw_source", "raw/source.txt", stage, "test") == hashlib.sha256(b"bravo").hexdigest()
    )
    assert artifacts.verify(repo, entries(repo)) == 1
    assert entries(repo)[0][1]["supersedes"] == hashlib.sha256(b"alpha").hexdigest()


def test_killed_mid_publish_recovers_old_version(repo: Path, tmp_path: Path) -> None:
    stage = tmp_path / "stage"
    stage.write_bytes(b"bravo")
    script = """
import os
import signal
import sys
from pathlib import Path
from scripts.storage import artifacts
repo, stage = map(Path, sys.argv[1:])
original = artifacts._json_write
def interrupt(path, value):
    if path == repo / 'registry/artifacts/raw_source.manifest.json':
        os.kill(os.getpid(), signal.SIGKILL)
    return original(path, value)
artifacts._json_write = interrupt
artifacts.publish(repo, 'raw_source', 'raw/source.txt', stage, 'test')
"""
    result = subprocess.run(
        [sys.executable, "-c", script, str(repo), str(stage)], cwd=Path(__file__).resolve().parents[2], timeout=30
    )
    assert result.returncode == -signal.SIGKILL
    assert artifacts.recover_incomplete(repo) == 1
    assert (repo / "data/raw/source.txt").read_bytes() == b"alpha"
    assert artifacts.verify(repo, entries(repo)) == 1


def test_gating_verify_hashes_same_size_restored_mtime(repo: Path) -> None:
    target = repo / "data/raw/source.txt"
    stamp = target.stat().st_mtime_ns
    assert paths.artifact_path("raw_source", "raw/source.txt", repo=repo) == target
    target.write_bytes(b"omega")
    os.utime(target, ns=(stamp, stamp))
    with pytest.raises(paths.MissingArtifactError, match="sha256"):
        artifacts.verify(repo, entries(repo))


def test_paths_reject_traversal_and_dispatch_store(repo: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    with pytest.raises(ValueError, match="relative path"):
        paths.artifact_path("raw_source", "../escape", repo=repo)
    worktree = tmp_path / "dispatch"
    subprocess.run(["git", "worktree", "add", "-qb", "test-dispatch", str(worktree)], cwd=repo, check=True, timeout=30)
    assert paths.artifact_store_root(worktree) == repo / "data/.artifact-store"
    monkeypatch.setenv("LU_ARTIFACT_STORE", str(worktree / "data/store"))
    with pytest.raises(ValueError, match="dispatch worktree"):
        paths.artifact_store_root(worktree)


def test_manifest_json_has_migration_fields(repo: Path) -> None:
    manifest = json.loads((repo / "registry/artifacts/raw_source.manifest.json").read_text())
    assert set(manifest["entries"][0]) >= {
        "git_blob",
        "pre_untrack_sha256",
        "migrated_at",
        "size",
        "sha256",
        "producer",
        "rights",
    }


def test_status_does_not_create_a_store_without_transactions(repo: Path) -> None:
    store = paths.artifact_store_root(repo)
    assert not store.exists()
    assert artifacts.main(["status"], repo=repo) == 0
    assert not store.exists()
