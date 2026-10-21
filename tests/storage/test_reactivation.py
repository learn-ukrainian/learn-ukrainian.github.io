"""A retired classified A member may be published again by its owning group."""

from __future__ import annotations

import csv
import hashlib
import os
import signal
import subprocess
import sys
import threading
import time
from pathlib import Path

import pytest

from scripts.storage import artifacts, paths
from tests.storage.test_publish_set import _git, _repo


def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _retire_b(repo: Path) -> None:
    artifacts.publish_set(
        repo,
        "raw_source",
        [artifacts.ArtifactChange("remove", "raw/b.txt", None, _sha(b"B1"))],
        "fixture",
        expected_members={"raw/a.txt", "raw/b.txt"},
    )


def _allow_b(repo: Path) -> None:
    manifest = paths.load_manifest("raw_source", repo)
    manifest["registration_patterns"].append("data/raw/b*.txt")
    artifacts._json_write(paths.manifest_path("raw_source", repo), manifest)


def test_shrink_regrow_twice_preserves_lineage_and_transfer(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("LU_ARTIFACT_STORE", raising=False)
    repo = _repo(tmp_path)
    original = paths.load_manifest("raw_source", repo)
    original_b = next(item for item in original["entries"] if item["path"] == "data/raw/b.txt")
    original_b["rights"] = "cleared"
    original_b["attribution"] = "fixture provenance"
    artifacts._json_write(paths.manifest_path("raw_source", repo), original)
    _allow_b(repo)
    _retire_b(repo)
    assert {item["path"] for item in paths.load_manifest("raw_source", repo)["entries"]} == {"data/raw/a.txt"}

    stage = tmp_path / "b-stage"
    stage.write_bytes(b"B2")
    stage.chmod(0o755)
    companion = tmp_path / "k-stage"
    companion.write_bytes(b"K0-reactivated")
    assert artifacts.publish_set(
        repo,
        "raw_source",
        [artifacts.ArtifactChange("add", "raw/b.txt", stage, None)],
        "regenerator",
        companions=[artifacts.CompanionChange("registry/companion-0.json", companion, _sha(b"K0-old"))],
        expected_members={"raw/a.txt"},
    ) == {"raw/b.txt": _sha(b"B2")}
    first = paths.load_manifest("raw_source", repo)
    first_b = next(item for item in first["entries"] if item["path"] == "data/raw/b.txt")
    assert first_b["supersedes"] == _sha(b"B1")
    assert first_b["rights"] == "cleared" and first_b["attribution"] == "fixture provenance"
    assert first_b["mode"] == "100644" and (repo / "data/raw/b.txt").stat().st_mode & 0o777 == 0o644
    assert first_b["producer"] == "regenerator" and first_b["published_at"]
    assert not {"retired_at", "migrated_at", "pre_untrack_sha256", "git_blob"} & first_b.keys()
    assert first["set_descriptor"]["companions"] == {"registry/companion-0.json": _sha(b"K0-reactivated")}
    assert paths.artifact_set("raw_source", repo=repo).companions == {"registry/companion-0.json": b"K0-reactivated"}

    artifacts.publish_set(
        repo,
        "raw_source",
        [artifacts.ArtifactChange("remove", "raw/b.txt", None, _sha(b"B2"))],
        "fixture",
        expected_members={"raw/a.txt", "raw/b.txt"},
    )
    assert artifacts.write_artifact_set(
        repo,
        "raw_source",
        "regenerator",
        {"raw/b.txt": lambda target: target.write_bytes(b"B3")},
        expected_hashes={"raw/b.txt": None},
        expected_members={"raw/a.txt"},
    ) == {"raw/b.txt": _sha(b"B3")}
    final = paths.load_manifest("raw_source", repo)
    final_b = next(item for item in final["entries"] if item["path"] == "data/raw/b.txt")
    assert final_b["supersedes"] == _sha(b"B2")
    assert [item["sha256"] for item in final["retired"]] == [_sha(b"B1"), _sha(b"B2")]
    assert final["set_descriptor"]["members"] == ["raw/a.txt", "raw/b.txt"]
    assert paths.artifact_set("raw_source", repo=repo).artifacts == {"raw/a.txt": b"A1", "raw/b.txt": b"B3"}
    active = [("raw_source", item) for item in final["entries"]]
    assert artifacts.verify(repo, active) == 2
    assert artifacts.snapshot(repo, "P1") == 2
    store = paths.artifact_store_root(repo)
    assert [(store / _sha(value)).read_bytes() for value in (b"B1", b"B2", b"B3")] == [b"B1", b"B2", b"B3"]

    bundle = tmp_path / "reactivated.tar.gz"
    assert artifacts.export_group(repo, "raw_source", bundle) == 4  # A1 and three B versions.
    (repo / ".gitignore").write_text("data/raw/\n")
    _git(repo, "rm", "--cached", "data/raw/a.txt", "data/raw/b.txt")
    _git(repo, "add", ".gitignore", "registry")
    _git(repo, "commit", "-qm", "published reactivation")
    clone = tmp_path / "clone"
    _git(tmp_path, "clone", "-q", str(repo), str(clone))
    monkeypatch.setenv("LU_ARTIFACT_STORE", str(tmp_path / "imported-store"))
    assert artifacts.import_tarball(clone, bundle) == 4
    assert (
        artifacts.hydrate(clone, [("raw_source", item) for item in paths.load_manifest("raw_source", clone)["entries"]])
        == 2
    )
    assert (
        artifacts.verify(clone, [("raw_source", item) for item in paths.load_manifest("raw_source", clone)["entries"]])
        == 2
    )
    assert (clone / "data/raw/b.txt").read_bytes() == b"B3"
    imported = paths.artifact_store_root(clone)
    assert [(imported / _sha(value)).read_bytes() for value in (b"B1", b"B2", b"B3")] == [b"B1", b"B2", b"B3"]


@pytest.mark.parametrize(
    "invalid",
    [
        "wrong_group",
        "wrong_class",
        "no_retirement",
        "no_pattern",
        "active_owner",
        "retired_owner",
        "overlap_pattern",
        "occupied",
        "symlink",
        "stale_members",
        "missing_object",
        "corrupt_object",
        "missing_older_object",
    ],
)
def test_reactivation_refuses_before_managed_change(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, invalid: str
) -> None:
    monkeypatch.delenv("LU_ARTIFACT_STORE", raising=False)
    repo = _repo(tmp_path)
    _retire_b(repo)
    if invalid != "no_pattern":
        _allow_b(repo)
    if invalid == "missing_older_object":
        previous = tmp_path / "previous"
        previous.write_bytes(b"B2")
        artifacts.publish_set(
            repo,
            "raw_source",
            [artifacts.ArtifactChange("add", "raw/b.txt", previous, None)],
            "regenerator",
            expected_members={"raw/a.txt"},
        )
        artifacts.publish_set(
            repo,
            "raw_source",
            [artifacts.ArtifactChange("remove", "raw/b.txt", None, _sha(b"B2"))],
            "fixture",
            expected_members={"raw/a.txt", "raw/b.txt"},
        )
    manifest_path = paths.manifest_path("raw_source", repo)
    if invalid in {"wrong_group", "wrong_class"}:
        table = repo / artifacts.TABLE
        with table.open(newline="") as stream:
            rows = list(csv.DictReader(stream, delimiter="\t"))
        for row in rows:
            if row["path"] == "data/raw/b.txt":
                row["group" if invalid == "wrong_group" else "class"] = "other" if invalid == "wrong_group" else "K"
        with table.open("w", newline="") as stream:
            writer = csv.DictWriter(stream, fieldnames=rows[0].keys(), delimiter="\t")
            writer.writeheader()
            writer.writerows(rows)
    if invalid == "no_retirement":
        manifest = paths.load_manifest("raw_source", repo)
        manifest["retired"] = []
        artifacts._json_write(manifest_path, manifest)
    if invalid in {"active_owner", "retired_owner"}:
        owned = {"path": "data/raw/b.txt", "sha256": _sha(b"B1"), "size": 2, "store": _sha(b"B1")}
        other = {
            "schema": 1,
            "group": "other",
            "entries": [owned] if invalid == "active_owner" else [],
            "retired": [owned] if invalid == "retired_owner" else [],
        }
        artifacts._json_write(paths.manifest_path("other", repo), other)
    if invalid == "overlap_pattern":
        artifacts._json_write(
            paths.manifest_path("other", repo),
            {"schema": 1, "group": "other", "entries": [], "registration_patterns": ["data/raw/b*.txt"]},
        )
    target = repo / "data/raw/b.txt"
    if invalid == "occupied":
        target.write_bytes(b"occupied")
    if invalid == "symlink":
        foreign = tmp_path / "foreign"
        foreign.write_bytes(b"foreign")
        target.symlink_to(foreign)
    old_obj = paths.artifact_store_root(repo) / _sha(b"B1")
    if invalid in {"missing_object", "missing_older_object"}:
        old_obj.unlink()
    if invalid == "corrupt_object":
        old_obj.write_bytes(b"XX")
    stage = tmp_path / "stage"
    stage.write_bytes(b"B2")
    before_manifest = manifest_path.read_bytes()
    before_a = (repo / "data/raw/a.txt").read_bytes()
    before_k = (repo / "registry/companion-0.json").read_bytes()
    before_target = (
        target.is_symlink(),
        os.readlink(target) if target.is_symlink() else target.read_bytes() if target.exists() else None,
    )
    store = paths.artifact_store_root(repo)
    before_store = {item.name: item.read_bytes() for item in store.iterdir() if item.is_file()}
    with pytest.raises((ValueError, paths.MissingArtifactError)):
        artifacts.publish_set(
            repo,
            "raw_source",
            [artifacts.ArtifactChange("add", "raw/b.txt", stage, None)],
            "regenerator",
            expected_members=set() if invalid == "stale_members" else {"raw/a.txt"},
        )
    assert manifest_path.read_bytes() == before_manifest
    assert (repo / "data/raw/a.txt").read_bytes() == before_a
    assert (repo / "registry/companion-0.json").read_bytes() == before_k
    assert (
        target.is_symlink(),
        os.readlink(target) if target.is_symlink() else target.read_bytes() if target.exists() else None,
    ) == before_target
    assert {item.name: item.read_bytes() for item in store.iterdir() if item.is_file()} == before_store
    assert not artifacts._journal_path(repo, "raw_source", "@set").exists()


@pytest.mark.parametrize(
    "point",
    [
        *(f"store:{index}" for index in range(1, 7)),
        "prejournal",
        "journal_scratch",
        "journal",
        "temp_open",
        *(f"temp:{index}" for index in range(1, 5)),
        *(f"install:{index}" for index in range(1, 5)),
        "companion",
        "descriptor",
        "cleanup",
    ],
)
def test_sigkill_reactivation_at_every_boundary_recovers_twice(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, point: str
) -> None:
    monkeypatch.delenv("LU_ARTIFACT_STORE", raising=False)
    repo = _repo(tmp_path)
    _retire_b(repo)
    _allow_b(repo)
    stage = tmp_path / "staged"
    stage.mkdir()
    for name, content in {"a": b"A2", "b": b"B2", "new": b"N1", "k": b"K0-new"}.items():
        (stage / name).write_bytes(content)
    script = """
import os, signal, sys
from pathlib import Path
from scripts.storage import artifacts
repo, stage, point = Path(sys.argv[1]), Path(sys.argv[2]), sys.argv[3]
old_a = artifacts.paths.find_entry('raw_source', 'raw/a.txt', repo)['sha256']
sha_k = artifacts.paths.hash_file(repo / 'registry/companion-0.json')
changes = [artifacts.ArtifactChange('replace', 'raw/a.txt', stage / 'a', old_a),
           artifacts.ArtifactChange('add', 'raw/b.txt', stage / 'b', None),
           artifacts.ArtifactChange('add', 'raw/new-one.txt', stage / 'new', None)]
companions = [artifacts.CompanionChange('registry/companion-0.json', stage / 'k', sha_k)]
def kill(): os.kill(os.getpid(), signal.SIGKILL)
copy = artifacts._store_copy
copies = 0
def hooked_copy(*args):
    global copies
    copy(*args)
    copies += 1
    if point == f'store:{copies}': kill()
artifacts._store_copy = hooked_copy
open_file = artifacts.os.open
def hooked_open(path, flags, *args, **kwargs):
    fd = open_file(path, flags, *args, **kwargs)
    if point == 'journal_scratch' and '.lu-journal-' in str(path): kill()
    if point == 'temp_open' and '.lu-artifact-' in str(path): kill()
    return fd
artifacts.os.open = hooked_open
make_temp = artifacts._make_temp
temps = 0
def hooked_temp(*args):
    global temps
    temp = make_temp(*args)
    temps += 1
    if point == f'temp:{temps}': kill()
    return temp
artifacts._make_temp = hooked_temp
install = artifacts._install
installs = 0
def hooked_install(temp, target):
    global installs
    install(temp, target)
    installs += 1
    if point == f'install:{installs}' or (point == 'companion' and target.name == 'companion-0.json'):
        kill()
artifacts._install = hooked_install
write = artifacts._json_write
def hooked_write(path, value):
    if point == 'prejournal' and path == artifacts._journal_path(repo, 'raw_source', '@set'): kill()
    write(path, value)
    if point == 'journal' and path == artifacts._journal_path(repo, 'raw_source', '@set'): kill()
    if point == 'descriptor' and path == artifacts.paths.manifest_path('raw_source', repo): kill()
artifacts._json_write = hooked_write
unlink = Path.unlink
def hooked_unlink(self, *args, **kwargs):
    if point == 'cleanup' and self == artifacts._journal_path(repo, 'raw_source', '@set'): kill()
    return unlink(self, *args, **kwargs)
Path.unlink = hooked_unlink
artifacts.publish_set(repo, 'raw_source', changes, 'fixture', companions=companions,
                      expected_members={'raw/a.txt'})
"""
    result = subprocess.run(
        [sys.executable, "-c", script, str(repo), str(stage), point],
        cwd=Path(__file__).resolve().parents[2],
        check=False,
        timeout=30,
    )
    assert result.returncode == -signal.SIGKILL
    first = artifacts.recover_incomplete(repo)
    assert artifacts.recover_incomplete(repo) == 0
    assert first == (0 if point.startswith("store:") or point in {"prejournal", "journal_scratch"} else 1)
    committed = point in {"descriptor", "cleanup"}
    manifest = paths.load_manifest("raw_source", repo)
    assert {item["path"] for item in manifest["entries"]} == (
        {"data/raw/a.txt", "data/raw/b.txt", "data/raw/new-one.txt"} if committed else {"data/raw/a.txt"}
    )
    assert (repo / "data/raw/a.txt").read_bytes() == (b"A2" if committed else b"A1")
    if committed:
        assert (repo / "data/raw/b.txt").read_bytes() == b"B2"
    else:
        assert not (repo / "data/raw/b.txt").exists()
    assert (repo / "data/raw/new-one.txt").exists() == committed
    assert (repo / "registry/companion-0.json").read_bytes() == (b"K0-new" if committed else b"K0-old")
    assert [item["sha256"] for item in manifest["retired"]] == [_sha(b"B1")]
    assert (paths.artifact_store_root(repo) / _sha(b"B1")).read_bytes() == b"B1"
    assert not artifacts._journal_path(repo, "raw_source", "@set").exists()
    assert paths.artifact_set("raw_source", repo=repo).companions == (
        {"registry/companion-0.json": b"K0-new"} if committed else {}
    )


def test_reactivation_reader_waits_for_complete_a_and_k(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("LU_ARTIFACT_STORE", raising=False)
    repo = _repo(tmp_path)
    _retire_b(repo)
    _allow_b(repo)
    stage = tmp_path / "stage"
    stage.write_bytes(b"B2")
    companion = tmp_path / "k"
    companion.write_bytes(b"K0-new")
    pause = tmp_path / "pause"
    release = tmp_path / "release"
    script = """
import sys, time
from pathlib import Path
from scripts.storage import artifacts, paths
repo, stage, companion, pause, release = map(Path, sys.argv[1:])
sha_k = paths.hash_file(repo / 'registry/companion-0.json')
install = artifacts._install
def hooked_install(temp, target):
    install(temp, target)
    if target.name == 'b.txt':
        pause.write_text('ready')
        while not release.exists(): time.sleep(0.01)
artifacts._install = hooked_install
artifacts.publish_set(repo, 'raw_source', [artifacts.ArtifactChange('add', 'raw/b.txt', stage, None)],
    'regenerator', companions=[artifacts.CompanionChange('registry/companion-0.json', companion, sha_k)],
    expected_members={'raw/a.txt'})
"""
    child = subprocess.Popen(
        [sys.executable, "-c", script, str(repo), str(stage), str(companion), str(pause), str(release)],
        cwd=Path(__file__).resolve().parents[2],
    )
    try:
        deadline = time.monotonic() + 10
        while not pause.exists() and time.monotonic() < deadline:
            time.sleep(0.01)
        assert pause.exists()
        observed: list[paths.ArtifactSet] = []
        saw_pending = threading.Event()
        pending = paths._pending_publication

        def observed_pending(checkout: Path) -> bool:
            result = pending(checkout)
            if result:
                saw_pending.set()
            return result

        monkeypatch.setattr(paths, "_pending_publication", observed_pending)
        reader = threading.Thread(target=lambda: observed.append(paths.artifact_set("raw_source", repo=repo)))
        reader.start()
        assert saw_pending.wait(timeout=5)
        release.write_text("go")
        reader.join(timeout=10)
        assert not reader.is_alive()
        assert child.wait(timeout=10) == 0
        assert observed[0].artifacts == {"raw/a.txt": b"A1", "raw/b.txt": b"B2"}
        assert observed[0].companions == {"registry/companion-0.json": b"K0-new"}
    finally:
        release.write_text("go")
        if child.poll() is None:
            child.kill()
            child.wait(timeout=10)
