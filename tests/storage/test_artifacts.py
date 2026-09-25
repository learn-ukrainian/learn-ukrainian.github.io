"""Held-out storage mechanics in disposable Git repositories."""

from __future__ import annotations

import csv
import fcntl
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


def test_write_artifact_publishes_manifest_paths_and_writes_others_directly(repo: Path, tmp_path: Path) -> None:
    published = artifacts.write_artifact(
        repo / "data/raw/source.txt", "raw_source", "test", lambda dest: dest.write_bytes(b"charlie"), repo=repo
    )
    assert published == (repo / "data/raw/source.txt").resolve()
    item = entries(repo)[0][1]
    assert item["sha256"] == hashlib.sha256(b"charlie").hexdigest()
    assert item["supersedes"] == hashlib.sha256(b"alpha").hexdigest()
    assert (repo / "data/raw/source.txt").read_bytes() == b"charlie"
    assert artifacts.verify(repo, entries(repo)) == 1

    scratch = tmp_path / "scratch.txt"
    artifacts.write_artifact(scratch, "raw_source", "test", lambda dest: dest.write_bytes(b"delta"), repo=repo)
    assert scratch.read_bytes() == b"delta"
    assert entries(repo)[0][1]["sha256"] == hashlib.sha256(b"charlie").hexdigest()


def test_write_artifact_rejects_a_target_published_under_another_group(repo: Path) -> None:
    (repo / "data/other").mkdir()
    (repo / "data/other/map.json").write_bytes(b"{}")
    with (repo / "registry/artifacts/classification-v1.tsv").open("a", newline="") as stream:
        csv.writer(stream, delimiter="\t").writerow(
            ("data/other/map.json", "100644", "", "2", "A", "other_group", "external; preserve", "rule")
        )
    git(repo, "add", ".")
    git(repo, "commit", "-qm", "second group")
    assert artifacts.manifest_build(repo, "other_group", "HEAD") == 1
    manifest_before = (repo / "registry/artifacts/other_group.manifest.json").read_bytes()

    def write(dest: Path) -> None:
        dest.write_bytes(b"clobbered")

    with pytest.raises(ValueError, match="published artifact of group other_group, not raw_source"):
        artifacts.write_artifact(repo / "data/other/map.json", "raw_source", "test", write, repo=repo)
    assert (repo / "data/other/map.json").read_bytes() == b"{}"
    assert (repo / "registry/artifacts/other_group.manifest.json").read_bytes() == manifest_before
    assert not any(paths.artifact_store_root(repo).glob("publish-stage-*"))

    artifacts.write_artifact(repo / "data/other/map.json", "other_group", "test", write, repo=repo)
    assert (repo / "data/other/map.json").read_bytes() == b"clobbered"


def test_write_artifact_fails_closed_when_published_target_diverged(repo: Path) -> None:
    (repo / "data/raw/source.txt").write_bytes(b"edited in place")
    with pytest.raises(paths.MissingArtifactError, match=r"size|sha256"):
        artifacts.write_artifact(
            repo / "data/raw/source.txt", "raw_source", "test", lambda dest: dest.write_bytes(b"new"), repo=repo
        )
    assert (repo / "data/raw/source.txt").read_bytes() == b"edited in place"


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
    with pytest.raises(ValueError, match="sha256"):
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


def test_status_help_describes_its_read_only_report(capsys: pytest.CaptureFixture[str]) -> None:
    with pytest.raises(SystemExit, match="0"):
        artifacts._parser().parse_args(["status", "--help"])
    assert "without creating a store" in capsys.readouterr().out.replace("\n", " ")


def test_hydrate_refuses_divergence_and_force_preserves(repo: Path) -> None:
    artifacts.snapshot(repo, "P1")
    target = repo / "data/raw/source.txt"
    target.write_bytes(b"local edit")
    with pytest.raises(ValueError, match="REFUSED divergent"):
        artifacts.hydrate(repo, entries(repo))
    assert target.read_bytes() == b"local edit"
    assert artifacts.hydrate(repo, entries(repo), force_preserve=True) == 1
    assert target.read_bytes() == b"alpha"
    store = paths.artifact_store_root(repo)
    divergent_sha = hashlib.sha256(b"local edit").hexdigest()
    assert (store / divergent_sha).read_bytes() == b"local edit"
    assert json.loads((store / "divergent.jsonl").read_text().splitlines()[0])["sha256"] == divergent_sha


def test_hydrate_collects_missing_and_corrupt_store_falls_back_to_blob(
    repo: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    artifacts.snapshot(repo, "P1")
    item = entries(repo)[0][1]
    store = paths.artifact_store_root(repo)
    (store / item["sha256"]).write_bytes(b"wrong")
    (repo / item["path"]).unlink()
    assert artifacts.hydrate(repo, entries(repo)) == 1
    assert "using git blob" in capsys.readouterr().err
    assert (store / item["sha256"]).read_bytes() == b"alpha"
    assert [path.read_bytes() for path in (store / ".corrupt").iterdir()] == [b"wrong"]
    missing = {**item, "path": "data/raw/second.txt", "sha256": "0" * 64, "git_blob": None}
    (repo / item["path"]).unlink()
    missing_again = {**missing, "path": "data/raw/third.txt"}
    with pytest.raises(ValueError, match=r"2 artifact\(s\) failed") as error:
        artifacts.hydrate(repo, [("raw_source", missing), ("raw_source", missing_again)])
    assert "second.txt" in str(error.value) and "third.txt" in str(error.value)
    with pytest.raises(ValueError, match=r"2 artifact\(s\) failed"):
        artifacts.verify(repo, [("raw_source", missing), ("raw_source", missing_again)])


def test_recovery_checks_manifest_digest_and_completed_publish(repo: Path, tmp_path: Path) -> None:
    artifacts.snapshot(repo, "P1")
    old = paths.load_manifest("raw_source", repo)
    stage = tmp_path / "stage"
    stage.write_bytes(b"bravo")
    artifacts.publish(repo, "raw_source", "raw/source.txt", stage, "test")
    new = paths.load_manifest("raw_source", repo)
    journal = artifacts._journal_path(repo, "raw_source", "raw/source.txt")
    record = {
        "repo": str(repo.resolve()),
        "group": "raw_source",
        "rel": "raw/source.txt",
        "old_sha256": old["entries"][0]["sha256"],
        "new_sha256": new["entries"][0]["sha256"],
        "new_manifest_digest": artifacts._manifest_digest(new),
        "manifest": old,
    }
    artifacts._json_write(journal, record)
    assert artifacts.recover_incomplete(repo) == 1
    assert (repo / "data/raw/source.txt").read_bytes() == b"bravo"
    assert paths.load_manifest("raw_source", repo) == new
    artifacts._json_write(journal, record)
    changed = {**new, "extra": "later"}
    artifacts._json_write(paths.manifest_path("raw_source", repo), changed)
    with pytest.raises(ValueError, match="manifest changed"):
        artifacts.recover_incomplete(repo)
    assert (repo / "data/raw/source.txt").read_bytes() == b"bravo"
    artifacts._json_write(paths.manifest_path("raw_source", repo), old)
    assert artifacts.recover_incomplete(repo) == 1
    assert (repo / "data/raw/source.txt").read_bytes() == b"alpha"


def test_publish_records_placed_mtime_and_sweeps_stale_store_temp(repo: Path, tmp_path: Path) -> None:
    stage = tmp_path / "stage"
    stage.write_bytes(b"bravo")
    store = paths.artifact_store_root(repo)
    store.mkdir()
    stale = store / "tmpold"
    stale.write_bytes(b"orphan")
    os.utime(stale, (0, 0))
    artifacts.publish(repo, "raw_source", "raw/source.txt", stage, "test")
    assert not stale.exists()
    assert entries(repo)[0][1]["mtime_ns"] == (repo / "data/raw/source.txt").stat().st_mtime_ns


def test_failed_store_copy_removes_temporary_file(repo: Path) -> None:
    store = paths.artifact_store_root(repo)
    source = repo / "data/raw/source.txt"
    with pytest.raises(ValueError, match="source changed during store copy"):
        artifacts._store_copy(source, "0" * 64, store)
    assert list(store.glob("tmp*")) == []


def test_artifact_path_caches_root_and_reloads_changed_manifest(repo: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    target = repo / "data/raw/source.txt"
    assert paths.artifact_path("raw_source", "raw/source.txt", repo=repo) == target
    monkeypatch.setattr(
        paths.subprocess,
        "check_output",
        lambda *args, **kwargs: (_ for _ in ()).throw(AssertionError("git rev-parse repeated")),
    )
    assert paths.artifact_path("raw_source", "raw/source.txt", repo=repo) == target
    manifest_path = paths.manifest_path("raw_source", repo)
    manifest = json.loads(manifest_path.read_text())
    manifest["entries"][0]["sha256"] = "0" * 64
    manifest["entries"][0]["store"] = "0" * 64
    artifacts._json_write(manifest_path, manifest)
    with pytest.raises(paths.MissingArtifactError, match="sha256"):
        paths.artifact_path("raw_source", "raw/source.txt", repo=repo)


def test_snapshot_hydrate_and_import_hold_publish_lock(
    repo: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    original_copy = artifacts._store_copy
    checked = []

    def locked_copy(source: Path, sha: str, store: Path) -> None:
        with (store / ".publish.lock").open("a+b") as lock:
            with pytest.raises(BlockingIOError):
                fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        checked.append(source)
        original_copy(source, sha, store)

    monkeypatch.setattr(artifacts, "_store_copy", locked_copy)
    assert artifacts.snapshot(repo, "P1") == 1
    (repo / "data/raw/source.txt").unlink()
    assert artifacts.hydrate(repo, entries(repo)) == 1
    assert len(checked) == 2
    bundle = tmp_path / "bundle.tar.gz"
    artifacts.export_group(repo, "raw_source", bundle)
    original_replace = artifacts.os.replace

    def locked_replace(source: Path, target: Path) -> None:
        if Path(target).parent == paths.artifact_store_root(repo):
            with (paths.artifact_store_root(repo) / ".publish.lock").open("a+b") as lock:
                with pytest.raises(BlockingIOError):
                    fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        original_replace(source, target)

    monkeypatch.setattr(artifacts.os, "replace", locked_replace)
    assert artifacts.import_tarball(repo, bundle) == 1


def _phase_branch_with_manifest(repo: Path) -> str:
    """Commit the built manifest on a phase branch and return the checkout to the pre-phase commit."""
    base = git(repo, "symbolic-ref", "--short", "HEAD")
    git(repo, "checkout", "-qb", "phase")
    git(repo, "add", "registry")
    git(repo, "commit", "-qm", "phase manifests")
    git(repo, "checkout", "-q", base)
    return base


def test_snapshot_reads_manifests_from_ref_before_phase_merges(
    repo: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setenv("LU_ARTIFACT_STORE", str(tmp_path / "store"))
    base = _phase_branch_with_manifest(repo)
    manifest_file = repo / "registry/artifacts/raw_source.manifest.json"
    assert not manifest_file.exists()
    head = git(repo, "rev-parse", "HEAD")
    assert artifacts.main(["snapshot", "--phase", "P1"], repo=repo) == 1
    assert "manifest missing" in capsys.readouterr().err

    assert artifacts.main(["snapshot", "--phase", "P1", "--manifests-ref", "phase"], repo=repo) == 0
    sha = hashlib.sha256(b"alpha").hexdigest()
    assert (tmp_path / "store" / sha).read_bytes() == b"alpha"
    assert git(repo, "status", "--porcelain") == ""
    assert not manifest_file.exists()
    assert (git(repo, "symbolic-ref", "--short", "HEAD"), git(repo, "rev-parse", "HEAD")) == (base, head)


def test_snapshot_manifests_ref_still_proves_disk_against_blob(
    repo: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("LU_ARTIFACT_STORE", str(tmp_path / "store"))
    _phase_branch_with_manifest(repo)
    (repo / "data/raw/source.txt").write_bytes(b"omega")
    with pytest.raises(paths.MissingArtifactError, match="sha256"):
        artifacts.snapshot(repo, "P1", manifests_ref="phase")
    assert not (tmp_path / "store" / hashlib.sha256(b"omega").hexdigest()).exists()


def test_snapshot_manifests_ref_missing_ref_or_manifest_is_a_clear_error(
    repo: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setenv("LU_ARTIFACT_STORE", str(tmp_path / "store"))
    (repo / "registry/artifacts/raw_source.manifest.json").unlink()
    assert artifacts.main(["snapshot", "--phase", "P1", "--manifests-ref", "origin/nope"], repo=repo) == 1
    err = capsys.readouterr().err
    assert "'origin/nope' does not resolve to a commit" in err and "git fetch origin <phase-branch>" in err
    assert artifacts.main(["snapshot", "--phase", "P1", "--manifests-ref", "HEAD"], repo=repo) == 1
    assert "manifest missing at" in capsys.readouterr().err
    assert list((tmp_path / "store").glob("[0-9a-f]*")) == []


def test_snapshot_help_documents_manifests_ref(capsys: pytest.CaptureFixture[str]) -> None:
    with pytest.raises(SystemExit, match="0"):
        artifacts._parser().parse_args(["snapshot", "--help"])
    out = capsys.readouterr().out
    assert "--manifests-ref REF" in out
    assert "snapshot --phase P2 --manifests-ref origin/<phase-branch>" in out


def test_failed_recovery_names_journal_and_remediation_for_every_command(
    repo: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    journal = artifacts._journal_path(repo, "raw_source", "raw/source.txt")
    journal.parent.mkdir(parents=True)
    journal.write_text("{not json", encoding="utf-8")
    for argv in (["status"], ["verify"]):
        assert artifacts.main(argv, repo=repo) == 1
        err = capsys.readouterr().err
        assert f"publish recovery failed for journal {journal}" in err
        assert "remediation: inspect" in err
        assert "scripts.storage.artifacts status" in err and "verify --group <group>" in err
        assert f"mv {journal} {journal}.resolved" in err
    with pytest.raises(artifacts.RecoveryError, match="remediation"):
        artifacts.publish(repo, "raw_source", "raw/source.txt", repo / "data/raw/source.txt", "test")


def test_recovery_prunes_journals_of_deleted_checkouts_only(
    repo: Path, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    journal_dir = paths.artifact_store_root(repo) / ".transactions"
    journal_dir.mkdir(parents=True)
    live_other = tmp_path / "other-checkout"
    live_other.mkdir()
    gone = journal_dir / "gone.json"
    kept = journal_dir / "kept.json"
    artifacts._json_write(gone, {"repo": str(tmp_path / "deleted-worktree"), "group": "raw_source"})
    artifacts._json_write(kept, {"repo": str(live_other), "group": "raw_source"})
    assert artifacts.recover_incomplete(repo) == 0
    assert not gone.exists()
    assert kept.exists()
    assert f"pruned publish journal {gone} of deleted checkout {tmp_path / 'deleted-worktree'}" in (
        capsys.readouterr().err
    )


def test_artifacts_imports_sys_plainly() -> None:
    source = Path(artifacts.__file__).read_text(encoding="utf-8")
    assert "__import__(" not in source
    assert "\nimport sys\n" in source
