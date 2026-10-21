"""Crash, concurrency and membership proofs for group publication."""

from __future__ import annotations

import csv
import errno
import hashlib
import json
import signal
import subprocess
import sys
import threading
import time
from pathlib import Path

import pytest

from scripts.storage import artifacts, paths


def _git(repo: Path, *args: str) -> None:
    subprocess.run(["git", *args], cwd=repo, check=True, capture_output=True, timeout=30)


def _repo(tmp_path: Path, *, count: int = 2, companion_count: int = 1) -> Path:
    repo = tmp_path / "repo"
    repo.mkdir()
    _git(repo, "init", "-q")
    _git(repo, "config", "user.email", "test@example.invalid")
    _git(repo, "config", "user.name", "Test")
    (repo / "data/raw").mkdir(parents=True)
    (repo / "registry/artifacts").mkdir(parents=True)
    with (repo / "registry/artifacts/classification-v1.tsv").open("w", newline="") as stream:
        writer = csv.writer(stream, delimiter="\t")
        writer.writerow(("path", "mode", "blob", "size", "class", "group", "reason", "judgment"))
        for index in range(count):
            name = chr(ord("a") + index)
            data = f"{name.upper()}1".encode()
            (repo / "data/raw" / f"{name}.txt").write_bytes(data)
            writer.writerow((f"data/raw/{name}.txt", "100644", "", len(data), "A", "raw_source", "fixture", "test"))
    for index in range(companion_count):
        (repo / "registry" / f"companion-{index}.json").write_bytes(f"K{index}-old".encode())
    _git(repo, "add", ".")
    _git(repo, "commit", "-qm", "base")
    assert artifacts.manifest_build(repo, "raw_source", "HEAD") == count
    manifest = paths.load_manifest("raw_source", repo)
    manifest["registration_patterns"] = ["data/raw/new-*.txt"]
    artifacts._json_write(paths.manifest_path("raw_source", repo), manifest)
    return repo


def _plan(repo: Path, tmp_path: Path) -> tuple[list[artifacts.ArtifactChange], list[artifacts.CompanionChange]]:
    staged = tmp_path / "staged"
    staged.mkdir(exist_ok=True)
    (staged / "a").write_bytes(b"A2")
    (staged / "new").write_bytes(b"N1")
    (staged / "k").write_bytes(b"K0-new")
    old = paths.load_manifest("raw_source", repo)["entries"]
    changes = [
        artifacts.ArtifactChange("replace", "raw/a.txt", staged / "a", old[0]["sha256"]),
        artifacts.ArtifactChange("add", "raw/new-one.txt", staged / "new", None),
        artifacts.ArtifactChange("remove", "raw/b.txt", None, old[1]["sha256"]),
    ]
    companions = [
        artifacts.CompanionChange("registry/companion-0.json", staged / "k", hashlib.sha256(b"K0-old").hexdigest())
    ]
    return changes, companions


def _state(repo: Path) -> tuple[bytes | None, bytes | None, bytes | None, bytes, set[str]]:
    manifest = paths.load_manifest("raw_source", repo)

    def content(relative: str) -> bytes | None:
        path = repo / relative
        return path.read_bytes() if path.exists() else None

    return (
        content("data/raw/a.txt"),
        content("data/raw/b.txt"),
        content("data/raw/new-one.txt"),
        content("registry/companion-0.json"),
        {item["path"] for item in manifest["entries"]},
    )


OLD = (b"A1", b"B1", None, b"K0-old", {"data/raw/a.txt", "data/raw/b.txt"})
NEW = (b"A2", None, b"N1", b"K0-new", {"data/raw/a.txt", "data/raw/new-one.txt"})


@pytest.mark.parametrize(
    "point",
    [
        *(f"store:{index}" for index in range(1, 7)),
        "prejournal",
        "journal_scratch",
        "journal",
        "temp_open",
        *(f"temp:{index}" for index in range(1, 4)),
        *(f"install:{index}" for index in range(1, 5)),
        "companion",
        "descriptor",
        "cleanup",
    ],
)
def test_sigkill_at_every_publication_boundary_recovers_twice(tmp_path: Path, point: str) -> None:
    repo = _repo(tmp_path)
    _plan(repo, tmp_path)
    script = """
import os, signal, sys
from pathlib import Path
from scripts.storage import artifacts
repo, stage, point = Path(sys.argv[1]), Path(sys.argv[2]), sys.argv[3]
old_a = artifacts.paths.find_entry('raw_source', 'raw/a.txt', repo)['sha256']
old_b = artifacts.paths.find_entry('raw_source', 'raw/b.txt', repo)['sha256']
sha_k = artifacts.paths.hash_file(repo / 'registry/companion-0.json')
changes = [artifacts.ArtifactChange('replace', 'raw/a.txt', stage / 'a', old_a),
           artifacts.ArtifactChange('add', 'raw/new-one.txt', stage / 'new', None),
           artifacts.ArtifactChange('remove', 'raw/b.txt', None, old_b)]
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
                      expected_members={'raw/a.txt', 'raw/b.txt'})
"""
    unrelated = repo / "data/raw" / (".lu-artifact-" + "0" * 32 + "-999.tmp")
    unrelated.write_bytes(b"unrelated")
    journal_dir = paths.artifact_store_root(repo) / ".transactions"
    journal_dir.mkdir(parents=True)
    unrelated_journal = journal_dir / "tmp-unrelated-keep"
    unrelated_journal.write_bytes(b"unrelated journal scratch")
    unrelated_named = journal_dir / (".lu-journal-" + "0" * 32 + "-unrelated.tmp")
    unrelated_named.write_bytes(b"unrelated named file")
    result = subprocess.run(
        [sys.executable, "-c", script, str(repo), str(tmp_path / "staged"), point],
        cwd=Path(__file__).resolve().parents[2],
        check=False,
        timeout=30,
    )
    assert result.returncode == -signal.SIGKILL
    first = artifacts.recover_incomplete(repo)
    assert artifacts.recover_incomplete(repo) == 0
    assert not artifacts._journal_path(repo, "raw_source", "@set").exists()
    assert _state(repo) == (NEW if point in {"descriptor", "cleanup"} else OLD)
    assert first == (0 if point.startswith("store:") or point in {"prejournal", "journal_scratch"} else 1)
    assert unrelated.read_bytes() == b"unrelated"
    assert unrelated_journal.read_bytes() == b"unrelated journal scratch"
    assert unrelated_named.read_bytes() == b"unrelated named file"
    assert not any(artifacts._JOURNAL_SCRATCH.fullmatch(path.name) for path in journal_dir.iterdir())
    assert list((repo / "data").rglob(".lu-artifact-*.tmp")) == [unrelated]
    assert list((repo / "registry").rglob(".lu-artifact-*.tmp")) == []


def test_set_read_pins_a_and_k_and_creates_no_store(tmp_path: Path) -> None:
    repo = _repo(tmp_path)
    store = paths.artifact_store_root(repo)
    snapshot = paths.artifact_set("raw_source", repo=repo, members={"raw/a.txt", "raw/b.txt"})
    assert snapshot.artifacts == {"raw/a.txt": b"A1", "raw/b.txt": b"B1"}
    assert snapshot.companions == {}
    assert not store.exists()
    with pytest.raises(ValueError, match="membership"):
        paths.artifact_set("raw_source", repo=repo, members={"raw/a.txt"})
    changes, companions = _plan(repo, tmp_path)
    artifacts.publish_set(
        repo, "raw_source", changes, "fixture", companions=companions, expected_members={"raw/a.txt", "raw/b.txt"}
    )
    snapshot = paths.artifact_set("raw_source", repo=repo)
    assert snapshot.artifacts == {"raw/a.txt": b"A2", "raw/new-one.txt": b"N1"}
    assert snapshot.companions == {"registry/companion-0.json": b"K0-new"}
    assert not (store / ".verification-cache.json").exists()


def test_set_read_of_sparse_checkout_does_not_create_state(tmp_path: Path) -> None:
    repo = _repo(tmp_path)
    store = paths.artifact_store_root(repo)
    (repo / "data/raw/b.txt").unlink()
    before = {path.relative_to(repo) for path in repo.rglob("*") if path.is_file()}
    with pytest.raises(FileNotFoundError):
        paths.artifact_set("raw_source", repo=repo)
    after = {path.relative_to(repo) for path in repo.rglob("*") if path.is_file()}
    assert before == after
    assert not store.exists()


def test_set_read_rejects_companion_hash_drift(tmp_path: Path) -> None:
    repo = _repo(tmp_path)
    changes, companions = _plan(repo, tmp_path)
    artifacts.publish_set(
        repo, "raw_source", changes, "fixture", companions=companions, expected_members={"raw/a.txt", "raw/b.txt"}
    )
    (repo / "registry/companion-0.json").write_bytes(b"tampered")
    with pytest.raises(ValueError, match="companion changed"):
        paths.artifact_set("raw_source", repo=repo)


def test_set_publication_checks_unchanged_members_before_install(tmp_path: Path) -> None:
    repo = _repo(tmp_path, count=3)
    changes, companions = _plan(repo, tmp_path)
    (repo / "data/raw/c.txt").write_bytes(b"tampered")
    before = _state(repo)
    with pytest.raises(paths.MissingArtifactError, match=r"sha256|size"):
        artifacts.publish_set(
            repo,
            "raw_source",
            changes,
            "fixture",
            companions=companions,
            expected_members={"raw/a.txt", "raw/b.txt", "raw/c.txt"},
        )
    assert _state(repo) == before


def test_set_publication_preserves_unchanged_member_in_store(tmp_path: Path) -> None:
    repo = _repo(tmp_path, count=3)
    changes, companions = _plan(repo, tmp_path)
    artifacts.publish_set(
        repo,
        "raw_source",
        changes,
        "fixture",
        companions=companions,
        expected_members={"raw/a.txt", "raw/b.txt", "raw/c.txt"},
    )
    manifest = paths.load_manifest("raw_source", repo)
    active = [("raw_source", entry) for entry in manifest["entries"]]
    assert artifacts.verify(repo, active) == 3
    assert (paths.artifact_store_root(repo) / hashlib.sha256(b"C1").hexdigest()).read_bytes() == b"C1"


def test_set_reader_waits_during_install_and_returns_new_generation(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repo = _repo(tmp_path)
    _plan(repo, tmp_path)
    pause = tmp_path / "paused"
    release = tmp_path / "release"
    script = """
import sys, time
from pathlib import Path
from scripts.storage import artifacts
repo, stage, pause, release = map(Path, sys.argv[1:])
old_a = artifacts.paths.find_entry('raw_source', 'raw/a.txt', repo)['sha256']
old_b = artifacts.paths.find_entry('raw_source', 'raw/b.txt', repo)['sha256']
sha_k = artifacts.paths.hash_file(repo / 'registry/companion-0.json')
changes = [artifacts.ArtifactChange('replace', 'raw/a.txt', stage / 'a', old_a),
           artifacts.ArtifactChange('add', 'raw/new-one.txt', stage / 'new', None),
           artifacts.ArtifactChange('remove', 'raw/b.txt', None, old_b)]
companions = [artifacts.CompanionChange('registry/companion-0.json', stage / 'k', sha_k)]
install = artifacts._install
def hooked_install(temp, target):
    install(temp, target)
    if target.name == 'a.txt':
        pause.write_text('ready')
        while not release.exists(): time.sleep(0.01)
artifacts._install = hooked_install
artifacts.publish_set(repo, 'raw_source', changes, 'fixture', companions=companions,
                      expected_members={'raw/a.txt', 'raw/b.txt'})
"""
    child = subprocess.Popen(
        [sys.executable, "-c", script, str(repo), str(tmp_path / "staged"), str(pause), str(release)],
        cwd=Path(__file__).resolve().parents[2],
    )
    try:
        deadline = time.monotonic() + 10
        while not pause.exists() and time.monotonic() < deadline:
            time.sleep(0.01)
        assert pause.exists()
        outcome: list[paths.ArtifactSet] = []
        saw_pending = threading.Event()
        pending = paths._pending_publication

        def observed_pending(checkout: Path) -> bool:
            result = pending(checkout)
            if result:
                saw_pending.set()
            return result

        monkeypatch.setattr(paths, "_pending_publication", observed_pending)
        reader = threading.Thread(target=lambda: outcome.append(paths.artifact_set("raw_source", repo=repo)))
        reader.start()
        assert saw_pending.wait(timeout=5)
        release.write_text("go")
        reader.join(timeout=10)
        assert not reader.is_alive()
        assert child.wait(timeout=10) == 0
        assert outcome[0].artifacts == {"raw/a.txt": b"A2", "raw/new-one.txt": b"N1"}
        assert outcome[0].companions == {"registry/companion-0.json": b"K0-new"}
    finally:
        release.write_text("go")
        if child.poll() is None:
            child.kill()
            child.wait(timeout=10)


@pytest.mark.parametrize(
    "invalid",
    ["duplicate", "escape", "symlink", "ownership", "unregistered", "stale_hash", "stale_members", "dirty_k"],
)
def test_invalid_plan_refused_before_live_change(tmp_path: Path, invalid: str) -> None:
    repo = _repo(tmp_path)
    changes, companions = _plan(repo, tmp_path)
    expected = {"raw/a.txt", "raw/b.txt"}
    if invalid == "duplicate":
        changes.append(changes[0])
    elif invalid == "escape":
        changes[1] = artifacts.ArtifactChange("add", "../escape", changes[1].source, None)
    elif invalid == "symlink":
        (repo / "data/raw/new-one.txt").symlink_to(tmp_path / "outside")
    elif invalid == "ownership":
        item = {"path": "data/raw/new-one.txt", "size": 2, "sha256": "0" * 64, "store": "0" * 64}
        artifacts._json_write(
            paths.manifest_path("other_group", repo), {"schema": 1, "group": "other_group", "entries": [item]}
        )
    elif invalid == "unregistered":
        changes[1] = artifacts.ArtifactChange("add", "raw/other.txt", changes[1].source, None)
    elif invalid == "stale_hash":
        changes[0] = artifacts.ArtifactChange("replace", "raw/a.txt", changes[0].source, "0" * 64)
    elif invalid == "stale_members":
        expected = {"raw/a.txt"}
    else:
        (repo / "registry/companion-0.json").write_bytes(b"dirty")
    before = _state(repo)
    manifest_before = paths.manifest_path("raw_source", repo).read_bytes()
    with pytest.raises((ValueError, paths.MissingArtifactError)):
        artifacts.publish_set(repo, "raw_source", changes, "fixture", companions=companions, expected_members=expected)
    assert _state(repo) == before
    assert paths.manifest_path("raw_source", repo).read_bytes() == manifest_before
    assert not artifacts._journal_path(repo, "raw_source", "@set").exists()


@pytest.mark.parametrize("shape", ["root_parent", "inner_parent", "grandparent"])
def test_in_root_symlinked_parent_refused_before_live_change(tmp_path: Path, shape: str) -> None:
    repo = _repo(tmp_path)
    changes, companions = _plan(repo, tmp_path)
    if shape == "root_parent":
        (repo / "data/raw").rename(repo / "data/raw.real")
        (repo / "data/raw").symlink_to("raw.real", target_is_directory=True)
        destination = repo / "data/raw.real"
    else:
        destination = repo / "data/other"
        destination.mkdir()
        (destination / "sentinel").write_bytes(b"other group")
        linked = repo / "data/raw/nest"
        linked.symlink_to("../other", target_is_directory=True)
        if shape == "inner_parent":
            new_rel = "raw/nest/new-one.txt"
        else:
            (destination / "deep").mkdir()
            (destination / "deep/sentinel").write_bytes(b"grandparent")
            new_rel = "raw/nest/deep/new-one.txt"
        manifest_path = paths.manifest_path("raw_source", repo)
        manifest = paths.load_manifest("raw_source", repo)
        manifest["registration_patterns"] = [f"data/{new_rel.rpartition('/')[0]}/new-*.txt"]
        artifacts._json_write(manifest_path, manifest)
        changes[1] = artifacts.ArtifactChange("add", new_rel, changes[1].source, None)
    before = {path.relative_to(destination): path.read_bytes() for path in destination.rglob("*") if path.is_file()}
    old_state = _state(repo)
    manifest_before = paths.manifest_path("raw_source", repo).read_bytes()
    with pytest.raises(ValueError, match="symlink component in artifact path"):
        artifacts.publish_set(
            repo,
            "raw_source",
            changes,
            "fixture",
            companions=companions,
            expected_members={"raw/a.txt", "raw/b.txt"},
        )
    assert _state(repo) == old_state
    assert paths.manifest_path("raw_source", repo).read_bytes() == manifest_before
    assert {
        path.relative_to(destination): path.read_bytes() for path in destination.rglob("*") if path.is_file()
    } == before
    assert not artifacts._journal_path(repo, "raw_source", "@set").exists()


def test_read_hydrate_and_publish_refuse_in_root_symlinked_parent(tmp_path: Path) -> None:
    repo = _repo(tmp_path)
    source = tmp_path / "new"
    source.write_bytes(b"A2")
    (repo / "data/raw").rename(repo / "data/raw.real")
    (repo / "data/raw").symlink_to("raw.real", target_is_directory=True)
    entry = paths.find_entry("raw_source", "raw/a.txt", repo)
    before = (repo / "data/raw.real/a.txt").read_bytes()
    with pytest.raises(ValueError, match="symlink component"):
        paths.artifact_set("raw_source", repo=repo)
    with pytest.raises(ValueError, match="symlink component"):
        artifacts.publish(repo, "raw_source", "raw/a.txt", source, "fixture")
    with pytest.raises(ValueError, match="symlink component"):
        artifacts.hydrate(repo, [("raw_source", entry)])
    assert (repo / "data/raw.real/a.txt").read_bytes() == before
    assert not artifacts._journal_path(repo, "raw_source", "@set").exists()


@pytest.mark.parametrize("entry_point", ["publish", "publish_set"])
def test_symlinked_data_refuses_before_store_creation(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, entry_point: str
) -> None:
    monkeypatch.delenv("LU_ARTIFACT_STORE", raising=False)
    repo = _repo(tmp_path)
    changes, companions = _plan(repo, tmp_path)
    (repo / "data").rename(repo / "data.real")
    foreign = tmp_path / "foreign"
    foreign.mkdir()
    (foreign / "sentinel").write_bytes(b"untouched")
    (repo / "data").symlink_to(foreign, target_is_directory=True)
    before = sorted((path.relative_to(foreign), path.read_bytes()) for path in foreign.rglob("*") if path.is_file())
    source = changes[0].source
    assert source is not None

    with pytest.raises(ValueError, match="symlink component in artifact path"):
        if entry_point == "publish":
            artifacts.publish(repo, "raw_source", "raw/a.txt", source, "fixture")
        else:
            artifacts.publish_set(
                repo,
                "raw_source",
                changes,
                "fixture",
                companions=companions,
                expected_members={"raw/a.txt", "raw/b.txt"},
            )

    assert (
        sorted((path.relative_to(foreign), path.read_bytes()) for path in foreign.rglob("*") if path.is_file())
        == before
    )
    assert sorted(path.relative_to(foreign) for path in foreign.rglob("*")) == [Path("sentinel")]
    assert (repo / "data").is_symlink()
    assert (repo / "data.real/raw/a.txt").read_bytes() == b"A1"
    assert (repo / "data.real/raw/b.txt").read_bytes() == b"B1"


def test_symlinked_store_refuses_before_lock_creation(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("LU_ARTIFACT_STORE", raising=False)
    repo = _repo(tmp_path)
    changes, companions = _plan(repo, tmp_path)
    foreign = tmp_path / "foreign"
    foreign.mkdir()
    (foreign / "sentinel").write_bytes(b"untouched")
    (repo / "data/.artifact-store").symlink_to(foreign, target_is_directory=True)

    with pytest.raises(ValueError, match="symlink component in artifact path"):
        artifacts.publish_set(
            repo,
            "raw_source",
            changes,
            "fixture",
            companions=companions,
            expected_members={"raw/a.txt", "raw/b.txt"},
        )

    assert sorted(path.name for path in foreign.iterdir()) == ["sentinel"]
    assert (foreign / "sentinel").read_bytes() == b"untouched"
    assert _state(repo) == OLD


def test_engine_temp_collision_preserves_unrelated_file_before_journal(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repo = _repo(tmp_path)
    changes, companions = _plan(repo, tmp_path)
    collision = repo / "data/raw" / (".lu-artifact-" + "0" * 32 + "-0.tmp")
    collision.write_bytes(b"unrelated")
    monkeypatch.setattr(artifacts.uuid, "uuid4", lambda: artifacts.uuid.UUID(int=0))
    with pytest.raises(ValueError, match="engine temp name collision"):
        artifacts.publish_set(
            repo,
            "raw_source",
            changes,
            "fixture",
            companions=companions,
            expected_members={"raw/a.txt", "raw/b.txt"},
        )
    assert collision.read_bytes() == b"unrelated"
    assert _state(repo) == OLD
    assert not artifacts._journal_path(repo, "raw_source", "@set").exists()


def test_retirement_and_recovery_refuse_in_root_symlinked_parent(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repo = _repo(tmp_path)
    old_b = paths.find_entry("raw_source", "raw/b.txt", repo)["sha256"]
    artifacts.publish_set(
        repo,
        "raw_source",
        [artifacts.ArtifactChange("remove", "raw/b.txt", None, old_b)],
        "fixture",
        expected_members={"raw/a.txt", "raw/b.txt"},
    )
    (repo / "data/raw/b.txt").write_bytes(b"B1")
    (repo / "data/raw").rename(repo / "data/raw.real")
    (repo / "data/raw").symlink_to("raw.real", target_is_directory=True)
    with pytest.raises(ValueError, match="symlink component"):
        artifacts.hydrate(repo, [], groups={"raw_source"})
    assert (repo / "data/raw.real/b.txt").read_bytes() == b"B1"
    (repo / "data/raw").unlink()
    (repo / "data/raw.real").rename(repo / "data/raw")
    (repo / "data/raw/b.txt").unlink()

    source = tmp_path / "new-a"
    source.write_bytes(b"A2")
    change = artifacts.ArtifactChange(
        "replace", "raw/a.txt", source, paths.find_entry("raw_source", "raw/a.txt", repo)["sha256"]
    )
    # Keep a committed journal to exercise recovery's path guard directly.
    with monkeypatch.context() as patch:
        patch.setattr(artifacts, "_finish_journal", lambda _journal, _record: None)
        artifacts.publish_set(repo, "raw_source", [change], "fixture", expected_members={"raw/a.txt"})
    journal = artifacts._journal_path(repo, "raw_source", "@set")
    assert journal.exists()
    (repo / "data/raw").rename(repo / "data/raw.real")
    (repo / "data/raw").symlink_to("raw.real", target_is_directory=True)
    before = (repo / "data/raw.real/a.txt").read_bytes()
    with pytest.raises(artifacts.RecoveryError, match="symlink component"):
        artifacts.recover_incomplete(repo)
    assert journal.exists()
    assert (repo / "data/raw.real/a.txt").read_bytes() == before
    (repo / "data/raw").unlink()
    (repo / "data/raw.real").rename(repo / "data/raw")
    assert artifacts.recover_incomplete(repo) == 1


def test_add_replace_remove_snapshot_clone_hydrate_and_retirement(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repo = _repo(tmp_path)
    changes, companions = _plan(repo, tmp_path)
    artifacts.publish_set(
        repo, "raw_source", changes, "fixture", companions=companions, expected_members={"raw/a.txt", "raw/b.txt"}
    )
    assert _state(repo) == NEW
    assert artifacts.snapshot(repo, "P1") == 2
    store = paths.artifact_store_root(repo)
    (repo / ".gitignore").write_text("data/raw/\n")
    _git(repo, "rm", "--cached", "data/raw/a.txt", "data/raw/b.txt")
    _git(repo, "add", ".gitignore", "registry")
    _git(repo, "commit", "-qm", "published set")
    clone = tmp_path / "fresh"
    _git(tmp_path, "clone", "-q", str(repo), str(clone))
    assert not (clone / "data/raw/a.txt").exists()
    (clone / "data/raw").mkdir(parents=True)
    (clone / "data/raw/b.txt").write_bytes(b"B1")
    monkeypatch.setenv("LU_ARTIFACT_STORE", str(store))
    active = [("raw_source", entry) for entry in paths.load_manifest("raw_source", clone)["entries"]]
    assert artifacts.hydrate(clone, active) == 2
    assert _state(clone) == NEW
    assert artifacts.verify(clone, active) == 2
    (clone / "data/raw/b.txt").write_bytes(b"unknown")
    with pytest.raises(ValueError, match="divergent retired"):
        artifacts.hydrate(clone, active)
    assert (clone / "data/raw/b.txt").read_bytes() == b"unknown"


@pytest.mark.parametrize("artifact_count,companion_count", [(8, 1), (1, 2)])
def test_fixture_producer_set_shapes(tmp_path: Path, artifact_count: int, companion_count: int) -> None:
    repo = _repo(tmp_path, count=artifact_count, companion_count=companion_count)
    staged = tmp_path / "staged"
    staged.mkdir()
    manifest = paths.load_manifest("raw_source", repo)
    changes = []
    expected = set()
    for index, entry in enumerate(manifest["entries"]):
        rel = entry["path"][5:]
        expected.add(rel)
        source = staged / f"a-{index}"
        source.write_bytes(f"new-{index}".encode())
        changes.append(artifacts.ArtifactChange("replace", rel, source, entry["sha256"]))
    companions = []
    for index in range(companion_count):
        source = staged / f"k-{index}"
        source.write_bytes(f"K{index}-new".encode())
        companions.append(
            artifacts.CompanionChange(
                f"registry/companion-{index}.json",
                source,
                hashlib.sha256(f"K{index}-old".encode()).hexdigest(),
            )
        )
    published = artifacts.publish_set(
        repo, "raw_source", changes, "fixture", companions=companions, expected_members=expected
    )
    assert len(published) == artifact_count
    snapshot = paths.artifact_set("raw_source", repo=repo, members=expected)
    assert len(snapshot.artifacts) == artifact_count
    assert len(snapshot.companions) == companion_count
    assert artifacts.verify(repo, [("raw_source", entry) for entry in snapshot.manifest["entries"]]) == artifact_count


def test_failed_install_and_rollback_preserve_journal_until_recovery(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repo = _repo(tmp_path)
    changes, companions = _plan(repo, tmp_path)
    install = artifacts._install
    restore = artifacts._restore_from_store
    calls = 0

    def fail_install(temp: Path | None, target: Path) -> None:
        nonlocal calls
        install(temp, target)
        calls += 1
        if calls == 1:
            raise OSError(errno.ENOSPC, "injected ENOSPC after rename")

    def fail_rollback(*args: object, **kwargs: object) -> None:
        raise OSError(errno.EIO, "injected rollback failure")

    monkeypatch.setattr(artifacts, "_install", fail_install)
    monkeypatch.setattr(artifacts, "_restore_from_store", fail_rollback)
    with pytest.raises(artifacts.RecoveryError, match="rollback failure"):
        artifacts.publish_set(
            repo, "raw_source", changes, "fixture", companions=companions, expected_members={"raw/a.txt", "raw/b.txt"}
        )
    journal = artifacts._journal_path(repo, "raw_source", "@set")
    assert journal.exists()
    with pytest.raises(ValueError, match="did not settle"):
        paths.artifact_set("raw_source", repo=repo, retries=2)
    monkeypatch.setattr(artifacts, "_install", install)
    monkeypatch.setattr(artifacts, "_restore_from_store", restore)
    assert artifacts.recover_incomplete(repo) == 1
    assert artifacts.recover_incomplete(repo) == 0
    assert not journal.exists()
    assert _state(repo) == OLD


@pytest.mark.parametrize("failure", ["rename", "fsync"])
def test_failed_manifest_rename_or_install_fsync_rolls_back(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, failure: str
) -> None:
    repo = _repo(tmp_path)
    changes, companions = _plan(repo, tmp_path)
    replace = artifacts.os.replace
    if failure == "rename":

        def fail_replace(source: Path, target: Path) -> None:
            if Path(target) == paths.manifest_path("raw_source", repo):
                raise OSError(errno.EIO, "injected rename failure")
            replace(source, target)

        monkeypatch.setattr(artifacts.os, "replace", fail_replace)
    else:
        fsync = artifacts._fsync_dir
        raised = False

        def fail_fsync(directory: Path) -> None:
            nonlocal raised
            if directory == repo / "data/raw" and not raised:
                raised = True
                raise OSError(errno.EIO, "injected fsync failure")
            fsync(directory)

        monkeypatch.setattr(artifacts, "_fsync_dir", fail_fsync)
    with pytest.raises(artifacts.RecoveryError if failure == "rename" else OSError, match="injected"):
        artifacts.publish_set(
            repo, "raw_source", changes, "fixture", companions=companions, expected_members={"raw/a.txt", "raw/b.txt"}
        )
    if failure == "rename":
        journal = artifacts._journal_path(repo, "raw_source", "@set")
        assert journal.exists()
        monkeypatch.setattr(artifacts.os, "replace", replace)
        assert artifacts.recover_incomplete(repo) == 1
    assert _state(repo) == OLD


def test_missing_old_store_object_blocks_recovery_and_set_reads(tmp_path: Path) -> None:
    repo = _repo(tmp_path)
    _plan(repo, tmp_path)
    script = """
import os, signal, sys
from pathlib import Path
from scripts.storage import artifacts
repo, stage = map(Path, sys.argv[1:])
a = artifacts.paths.find_entry('raw_source', 'raw/a.txt', repo)['sha256']
b = artifacts.paths.find_entry('raw_source', 'raw/b.txt', repo)['sha256']
k = artifacts.paths.hash_file(repo / 'registry/companion-0.json')
changes = [artifacts.ArtifactChange('replace','raw/a.txt',stage/'a',a),
           artifacts.ArtifactChange('add','raw/new-one.txt',stage/'new',None),
           artifacts.ArtifactChange('remove','raw/b.txt',None,b)]
companions = [artifacts.CompanionChange('registry/companion-0.json',stage/'k',k)]
install = artifacts._install
def interrupt(temp, target):
    install(temp, target)
    os.kill(os.getpid(), signal.SIGKILL)
artifacts._install = interrupt
artifacts.publish_set(repo,'raw_source',changes,'fixture',companions=companions,
                      expected_members={'raw/a.txt','raw/b.txt'})
"""
    result = subprocess.run(
        [sys.executable, "-c", script, str(repo), str(tmp_path / "staged")],
        cwd=Path(__file__).resolve().parents[2],
        timeout=30,
    )
    assert result.returncode == -signal.SIGKILL
    old_sha = hashlib.sha256(b"A1").hexdigest()
    old_obj = paths.artifact_store_root(repo) / old_sha
    old_obj.unlink()
    journal = artifacts._journal_path(repo, "raw_source", "@set")
    with pytest.raises(artifacts.RecoveryError, match="missing or corrupt store object"):
        artifacts.recover_incomplete(repo)
    assert journal.exists()
    with pytest.raises(ValueError, match="did not settle"):
        paths.artifact_set("raw_source", repo=repo, retries=2)
    old_obj.write_bytes(b"A1")
    assert artifacts.recover_incomplete(repo) == 1
    assert artifacts.recover_incomplete(repo) == 0
    assert _state(repo) == OLD


def test_registered_single_member_writer_and_set_writer(tmp_path: Path) -> None:
    repo = _repo(tmp_path)
    registered = repo / "data/raw/new-two.txt"
    artifacts.write_artifact(registered, "raw_source", "fixture", lambda target: target.write_bytes(b"N2"), repo=repo)
    assert registered.read_bytes() == b"N2"
    manifest = paths.load_manifest("raw_source", repo)
    assert {item["path"] for item in manifest["entries"]} == {
        "data/raw/a.txt",
        "data/raw/b.txt",
        "data/raw/new-two.txt",
    }
    expected = {item["path"][5:] for item in manifest["entries"]}
    hash_a = next(item["sha256"] for item in manifest["entries"] if item["path"] == "data/raw/a.txt")
    result = artifacts.write_artifact_set(
        repo,
        "raw_source",
        "fixture",
        {"raw/a.txt": lambda target: target.write_bytes(b"A3")},
        expected_hashes={"raw/a.txt": hash_a},
        expected_members=expected,
        removals={"raw/new-two.txt": hashlib.sha256(b"N2").hexdigest()},
    )
    assert result == {"raw/a.txt": hashlib.sha256(b"A3").hexdigest(), "raw/new-two.txt": None}
    assert not registered.exists()


def test_publish_set_cli_plan(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    repo = _repo(tmp_path)
    changes, companions = _plan(repo, tmp_path)
    plan = {
        "group": "raw_source",
        "producer": "fixture",
        "expected_members": ["raw/a.txt", "raw/b.txt"],
        "artifacts": [
            {
                "operation": item.operation,
                "rel": item.rel,
                "source": str(item.source) if item.source else None,
                "expected_sha256": item.expected_sha256,
            }
            for item in changes
        ],
        "companions": [
            {"path": item.path, "source": str(item.source), "expected_sha256": item.expected_sha256}
            for item in companions
        ],
    }
    plan_file = tmp_path / "plan.json"
    plan_file.write_text(json.dumps(plan))
    assert artifacts.main(["publish-set", "--plan", str(plan_file)], repo=repo) == 0
    assert json.loads(capsys.readouterr().out)["raw/b.txt"] is None
    assert _state(repo) == NEW


def test_hydrate_and_verify_group_with_only_retired_members(tmp_path: Path) -> None:
    repo = _repo(tmp_path, count=1, companion_count=0)
    sha = paths.find_entry("raw_source", "raw/a.txt", repo)["sha256"]
    assert artifacts.publish_set(
        repo,
        "raw_source",
        [artifacts.ArtifactChange("remove", "raw/a.txt", None, sha)],
        "fixture",
        expected_members={"raw/a.txt"},
    ) == {"raw/a.txt": None}
    assert paths.artifact_set("raw_source", repo=repo).artifacts == {}
    target = repo / "data/raw/a.txt"
    target.write_bytes(b"A1")
    assert artifacts.hydrate(repo, [], groups={"raw_source"}) == 0
    assert not target.exists()
    assert artifacts.verify(repo, [], groups={"raw_source"}) == 0


def test_p2_registration_patterns_bound_dated_and_per_book_names() -> None:
    root = Path(__file__).resolve().parents[2]
    parked = paths.load_manifest("lexicon_parked", root)
    headwords = paths.load_manifest("lexicon_headword_candidates", root)
    assert artifacts._registration_allowed(parked, "data/lexicon/parked/parked-thin-entries-2026-09-27.json")
    assert artifacts._registration_allowed(
        headwords, "data/lexicon/source-inventory/grade-09/new-book-headwords-1.yaml"
    )
    assert not artifacts._registration_allowed(headwords, "data/lexicon/source-inventory/grade-09/other.json")
    assert not artifacts._registration_allowed(headwords, "data/lexicon/source-inventory/grade-12/new-headwords.yaml")


@pytest.mark.parametrize("failure_point", ["descriptor", "cleanup"])
def test_failed_post_commit_fsync_keeps_journal_until_recovery(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, failure_point: str
) -> None:
    repo = _repo(tmp_path)
    changes, companions = _plan(repo, tmp_path)
    fsync = artifacts._fsync_dir
    transaction_syncs = 0
    failed = False

    def fail_once(directory: Path) -> None:
        nonlocal transaction_syncs, failed
        if directory == artifacts._journal_path(repo, "raw_source", "@set").parent:
            transaction_syncs += 1
        should_fail = (failure_point == "descriptor" and directory == repo / "registry/artifacts") or (
            failure_point == "cleanup" and transaction_syncs == 2 and directory.name == ".transactions"
        )
        if should_fail and not failed:
            failed = True
            raise OSError(errno.EIO, "injected post-commit fsync failure")
        fsync(directory)

    monkeypatch.setattr(artifacts, "_fsync_dir", fail_once)
    with pytest.raises(OSError, match="post-commit fsync"):
        artifacts.publish_set(
            repo,
            "raw_source",
            changes,
            "fixture",
            companions=companions,
            expected_members={"raw/a.txt", "raw/b.txt"},
        )
    journal = artifacts._journal_path(repo, "raw_source", "@set")
    assert journal.exists()
    with pytest.raises(ValueError, match="did not settle"):
        paths.artifact_set("raw_source", repo=repo, retries=2)
    monkeypatch.setattr(artifacts, "_fsync_dir", fsync)
    assert artifacts.recover_incomplete(repo) == 1
    assert artifacts.recover_incomplete(repo) == 0
    assert _state(repo) == NEW


def _digest(repo: Path) -> str:
    return artifacts._manifest_digest(paths.artifact_set("raw_source", repo=repo).manifest)


def _members(repo: Path) -> set[str]:
    return {item["path"][5:] for item in paths.load_manifest("raw_source", repo)["entries"]}


def _a_snapshot(repo: Path) -> tuple:
    """A entry metadata plus live bytes, mtime, and mode. Companion bytes are not included."""
    manifest = paths.load_manifest("raw_source", repo)
    files = []
    for entry in manifest["entries"]:
        path = repo / entry["path"]
        stat = path.stat()
        files.append((path.read_bytes(), stat.st_mtime_ns, stat.st_mode & 0o777))
    return (manifest["entries"], manifest.get("retired", []), tuple(files))


def _frozen(repo: Path) -> tuple:
    manifest = paths.load_manifest("raw_source", repo)
    stamps = []
    relatives = [entry["path"] for entry in manifest["entries"]]
    relatives.extend(sorted(manifest.get("set_descriptor", {}).get("companions", {})))
    for relative in relatives:
        path = repo / relative
        if path.is_symlink() or not path.is_file():
            stamps.append((relative, None))
            continue
        stat = path.stat()
        stamps.append((relative, path.read_bytes(), stat.st_mtime_ns, stat.st_mode & 0o777))
    return (
        paths.manifest_path("raw_source", repo).read_bytes(),
        tuple(stamps),
        artifacts._journal_path(repo, "raw_source", "@set").exists(),
    )


def _bind_companions(repo: Path, tmp_path: Path, count: int) -> None:
    """Bind the first ``count`` companions at their committed bytes, via one real A replace."""
    staged_a = tmp_path / "bind-a"
    staged_a.write_bytes(b"A-bound")
    manifest = paths.load_manifest("raw_source", repo)
    old_a = next(item["sha256"] for item in manifest["entries"] if item["path"] == "data/raw/a.txt")
    companions = []
    for index in range(count):
        relative = f"registry/companion-{index}.json"
        source = tmp_path / f"bind-k-{index}"
        source.write_bytes((repo / relative).read_bytes())
        companions.append(artifacts.CompanionChange(relative, source, hashlib.sha256(source.read_bytes()).hexdigest()))
    artifacts.publish_set(
        repo,
        "raw_source",
        [artifacts.ArtifactChange("replace", "raw/a.txt", staged_a, old_a)],
        "fixture",
        companions=companions,
        expected_members={item["path"][5:] for item in manifest["entries"]},
    )


def _stage_companion(tmp_path: Path, name: str, content: bytes) -> Path:
    path = tmp_path / name
    path.write_bytes(content)
    return path


def _bound_repo(tmp_path: Path, name: str) -> Path:
    root = tmp_path / name
    root.mkdir()
    repo = _repo(root)
    _bind_companions(repo, root, 1)
    return repo


def test_companion_only_api_helper_and_cli_leave_a_unchanged(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    repo = _bound_repo(tmp_path, "api")
    before = _a_snapshot(repo)
    members = _members(repo)
    recipe = repo / "registry/companion-0.json"
    staged = _stage_companion(tmp_path, "k-api", b"K-api")
    result = artifacts.publish_set(
        repo,
        "raw_source",
        [],
        "api",
        companions=[
            artifacts.CompanionChange("registry/companion-0.json", staged, hashlib.sha256(b"K0-old").hexdigest())
        ],
        expected_members=members,
        expected_manifest=_digest(repo),
    )
    assert result == {}
    assert not result
    assert recipe.read_bytes() == b"K-api"
    assert _a_snapshot(repo) == before

    repo = _bound_repo(tmp_path, "helper")
    before = _a_snapshot(repo)
    members = _members(repo)
    recipe = repo / "registry/companion-0.json"
    helper = artifacts.write_artifact_set(
        repo,
        "raw_source",
        "helper",
        {},
        expected_hashes={},
        expected_members=members,
        companions={
            "registry/companion-0.json": (
                hashlib.sha256(b"K0-old").hexdigest(),
                lambda target: target.write_bytes(b"K-helper"),
            )
        },
        expected_manifest=_digest(repo),
    )
    assert helper == {}
    assert not helper
    assert recipe.read_bytes() == b"K-helper"
    assert _a_snapshot(repo) == before

    repo = _bound_repo(tmp_path, "cli")
    before = _a_snapshot(repo)
    members = _members(repo)
    recipe = repo / "registry/companion-0.json"
    staged_cli = _stage_companion(tmp_path, "k-cli", b"K-cli")
    plan = {
        "group": "raw_source",
        "producer": "cli",
        "expected_members": sorted(members),
        "expected_manifest": _digest(repo),
        "artifacts": [],
        "companions": [
            {
                "path": "registry/companion-0.json",
                "source": str(staged_cli),
                "expected_sha256": hashlib.sha256(b"K0-old").hexdigest(),
            }
        ],
    }
    plan_file = tmp_path / "plan.json"
    plan_file.write_text(json.dumps(plan))
    assert artifacts.main(["publish-set", "--plan", str(plan_file)], repo=repo) == 0
    assert json.loads(capsys.readouterr().out) == {}
    assert recipe.read_bytes() == b"K-cli"
    assert _a_snapshot(repo) == before
    snapshot = paths.artifact_set("raw_source", repo=repo)
    assert snapshot.artifacts["raw/a.txt"] == b"A-bound"
    assert snapshot.artifacts["raw/b.txt"] == b"B1"
    assert snapshot.companions == {"registry/companion-0.json": b"K-cli"}
    assert artifacts.verify(repo, [("raw_source", entry) for entry in snapshot.manifest["entries"]]) == 2


@pytest.mark.parametrize(
    "fault",
    [
        "stale_members",
        "stale_k_hash",
        "stale_manifest",
        "dirty_changed_k",
        "dirty_mode",
        "empty_request",
        "unbound_companion",
        "missing_companion",
        "corrupt_store_object",
        "missing_manifest_digest",
    ],
)
def test_companion_only_refusals_leave_the_group_unchanged(tmp_path: Path, fault: str) -> None:
    repo = _repo(tmp_path, companion_count=2)
    _bind_companions(repo, tmp_path, 1)
    members = _members(repo)
    digest = _digest(repo)
    recipe = "registry/companion-0.json"
    staged = _stage_companion(tmp_path, "k-next", b"K-next")
    companions = [artifacts.CompanionChange(recipe, staged, hashlib.sha256(b"K0-old").hexdigest())]
    expected_manifest: str | None = digest
    match = "stale expected hash"
    if fault == "stale_members":
        members = {"raw/a.txt"}
        match = "stale expected membership"
    elif fault == "stale_k_hash":
        companions = [artifacts.CompanionChange(recipe, staged, "0" * 64)]
    elif fault == "stale_manifest":
        replacement = _stage_companion(tmp_path, "b2", b"B2")
        old_b = paths.find_entry("raw_source", "raw/b.txt", repo)["sha256"]
        artifacts.publish_set(
            repo,
            "raw_source",
            [artifacts.ArtifactChange("replace", "raw/b.txt", replacement, old_b)],
            "fixture",
            expected_members=members,
        )
        expected_manifest = digest
        match = "stale expected manifest"
    elif fault == "dirty_changed_k":
        first = _stage_companion(tmp_path, "k-mid", b"K-mid")
        artifacts.publish_set(
            repo,
            "raw_source",
            [],
            "fixture",
            companions=[artifacts.CompanionChange(recipe, first, hashlib.sha256(b"K0-old").hexdigest())],
            expected_members=members,
            expected_manifest=digest,
        )
        companions = [artifacts.CompanionChange(recipe, staged, hashlib.sha256(b"K-mid").hexdigest())]
        expected_manifest = _digest(repo)
        match = "dirty K companion:"
    elif fault == "dirty_mode":
        (repo / recipe).chmod(0o755)
        same = _stage_companion(tmp_path, "k-same", b"K0-old")
        companions = [artifacts.CompanionChange(recipe, same, hashlib.sha256(b"K0-old").hexdigest())]
        match = "dirty K companion mode"
    elif fault == "empty_request":
        frozen = _frozen(repo)
        with pytest.raises(ValueError, match="artifact or companion"):
            artifacts.publish_set(
                repo,
                "raw_source",
                [],
                "fixture",
                companions=[],
                expected_members=members,
                expected_manifest=digest,
            )
        assert _frozen(repo) == frozen
        with pytest.raises(ValueError, match="artifact or companion"):
            artifacts.write_artifact_set(
                repo,
                "raw_source",
                "fixture",
                {},
                expected_hashes={},
                expected_members=members,
                expected_manifest=digest,
            )
        assert _frozen(repo) == frozen
        plan = tmp_path / "empty.json"
        plan.write_text(
            json.dumps(
                {
                    "group": "raw_source",
                    "producer": "fixture",
                    "expected_members": sorted(members),
                    "expected_manifest": digest,
                    "artifacts": [],
                    "companions": [],
                }
            )
        )
        assert artifacts.main(["publish-set", "--plan", str(plan)], repo=repo) == 1
        assert _frozen(repo) == frozen
        return
    elif fault == "unbound_companion":
        other = _stage_companion(tmp_path, "k1", b"K1-new")
        companions = [
            artifacts.CompanionChange("registry/companion-1.json", other, hashlib.sha256(b"K1-old").hexdigest())
        ]
        match = "not bound to the group"
    elif fault == "missing_companion":
        (repo / recipe).unlink()
        match = "set companion differs"
    elif fault == "corrupt_store_object":
        (paths.artifact_store_root(repo) / hashlib.sha256(b"K0-old").hexdigest()).write_bytes(b"XX")
        match = "corrupt store object"
    else:
        expected_manifest = None
        match = "expected manifest digest"
    frozen = _frozen(repo)
    with pytest.raises(ValueError, match=match):
        artifacts.publish_set(
            repo,
            "raw_source",
            [],
            "fixture",
            companions=companions,
            expected_members=members,
            expected_manifest=expected_manifest,
        )
    assert _frozen(repo) == frozen
    assert not artifacts._journal_path(repo, "raw_source", "@set").exists()


def test_prepare_prepare_run_verify_identical_recipe_without_commit(tmp_path: Path) -> None:
    repo = _repo(tmp_path)
    _bind_companions(repo, tmp_path, 1)
    members = _members(repo)
    recipe = repo / "registry/companion-0.json"
    commits = subprocess.run(
        ["git", "rev-list", "--count", "HEAD"], cwd=repo, capture_output=True, text=True, check=True, timeout=30
    )
    prepared = _stage_companion(tmp_path, "recipe-v2", b"RECIPE-V2")
    assert (
        artifacts.publish_set(
            repo,
            "raw_source",
            [],
            "prepare",
            companions=[
                artifacts.CompanionChange("registry/companion-0.json", prepared, hashlib.sha256(b"K0-old").hexdigest())
            ],
            expected_members=members,
            expected_manifest=_digest(repo),
        )
        == {}
    )
    assert recipe.read_bytes() == b"RECIPE-V2"
    a_after_prepare = _a_snapshot(repo)
    manifest_bytes = paths.manifest_path("raw_source", repo).read_bytes()
    recipe_mtime = recipe.stat().st_mtime_ns
    recipe_mode = recipe.stat().st_mode
    repeated = _stage_companion(tmp_path, "recipe-v2-again", b"RECIPE-V2")
    assert (
        artifacts.publish_set(
            repo,
            "raw_source",
            [],
            "prepare",
            companions=[
                artifacts.CompanionChange(
                    "registry/companion-0.json", repeated, hashlib.sha256(b"RECIPE-V2").hexdigest()
                )
            ],
            expected_members=members,
            expected_manifest=_digest(repo),
        )
        == {}
    )
    assert paths.manifest_path("raw_source", repo).read_bytes() == manifest_bytes
    assert recipe.stat().st_mtime_ns == recipe_mtime
    assert recipe.stat().st_mode == recipe_mode
    assert not artifacts._journal_path(repo, "raw_source", "@set").exists()
    run_output = _stage_companion(tmp_path, "run-b", b"B-run")
    old_b = paths.find_entry("raw_source", "raw/b.txt", repo)["sha256"]
    published = artifacts.publish_set(
        repo,
        "raw_source",
        [artifacts.ArtifactChange("replace", "raw/b.txt", run_output, old_b)],
        "run",
        companions=[
            artifacts.CompanionChange("registry/companion-0.json", repeated, hashlib.sha256(b"RECIPE-V2").hexdigest())
        ],
        expected_members=members,
        expected_manifest=_digest(repo),
    )
    assert published == {"raw/b.txt": hashlib.sha256(b"B-run").hexdigest()}
    assert recipe.read_bytes() == b"RECIPE-V2"
    assert recipe.stat().st_mtime_ns == recipe_mtime
    assert _a_snapshot(repo)[0][0]["path"] == "data/raw/a.txt"
    assert (repo / "data/raw/a.txt").read_bytes() == a_after_prepare[2][0][0]
    assert (repo / "data/raw/a.txt").stat().st_mtime_ns == a_after_prepare[2][0][1]
    head = subprocess.run(
        ["git", "show", "HEAD:registry/companion-0.json"], cwd=repo, capture_output=True, check=True, timeout=30
    )
    assert head.stdout == b"K0-old"
    assert (
        subprocess.run(
            ["git", "rev-list", "--count", "HEAD"], cwd=repo, capture_output=True, text=True, check=True, timeout=30
        ).stdout
        == commits.stdout
    )
    snapshot = paths.artifact_set("raw_source", repo=repo)
    assert snapshot.companions == {"registry/companion-0.json": b"RECIPE-V2"}
    assert snapshot.artifacts == {"raw/a.txt": b"A-bound", "raw/b.txt": b"B-run"}
    assert artifacts.verify(repo, [("raw_source", entry) for entry in snapshot.manifest["entries"]]) == 2


def test_companion_only_journal_records_only_changed_k_rows(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    repo = _repo(tmp_path, companion_count=2)
    _bind_companions(repo, tmp_path, 2)
    saved: dict[str, dict] = {}
    finish = artifacts._finish_journal

    def keep(journal: Path, record: dict) -> None:
        saved["record"] = record
        finish(journal, record)

    monkeypatch.setattr(artifacts, "_finish_journal", keep)
    unchanged = _stage_companion(tmp_path, "k0-same", b"K0-old")
    changed = _stage_companion(tmp_path, "k1-new", b"K1-new")
    before = _a_snapshot(repo)
    unchanged_mtime = (repo / "registry/companion-0.json").stat().st_mtime_ns
    assert (
        artifacts.publish_set(
            repo,
            "raw_source",
            [],
            "fixture",
            companions=[
                artifacts.CompanionChange(
                    "registry/companion-0.json", unchanged, hashlib.sha256(b"K0-old").hexdigest()
                ),
                artifacts.CompanionChange("registry/companion-1.json", changed, hashlib.sha256(b"K1-old").hexdigest()),
            ],
            expected_members=_members(repo),
            expected_manifest=_digest(repo),
        )
        == {}
    )
    record = saved["record"]
    assert record["schema"] == 2
    assert record["rows"] == []
    assert [row["path"] for row in record["companions"]] == ["registry/companion-1.json"]
    assert record["new_manifest"]["entries"] == record["manifest"]["entries"]
    assert record["new_manifest"].get("retired", []) == record["manifest"].get("retired", [])
    assert _a_snapshot(repo) == before
    assert (repo / "registry/companion-0.json").stat().st_mtime_ns == unchanged_mtime
    assert (repo / "registry/companion-1.json").read_bytes() == b"K1-new"


@pytest.mark.parametrize(
    "point",
    [
        *(f"store:{index}" for index in range(1, 7)),
        "prejournal",
        "journal_scratch",
        "journal",
        "temp_open",
        *(f"temp:{index}" for index in range(1, 4)),
        *(f"install:{index}" for index in range(1, 5)),
        "companion",
        "descriptor",
        "cleanup",
    ],
)
def test_sigkill_companion_only_at_every_boundary_recovers_twice(tmp_path: Path, point: str) -> None:
    repo = _repo(tmp_path, companion_count=4)
    _bind_companions(repo, tmp_path, 4)
    stage = tmp_path / "k-only"
    stage.mkdir()
    for index in range(4):
        (stage / f"k{index}").write_bytes(f"K{index}-new".encode())
    digest = _digest(repo)
    before_a = _a_snapshot(repo)
    script = """
import os, signal, sys
from pathlib import Path
from scripts.storage import artifacts
repo, stage, point, expected_manifest = Path(sys.argv[1]), Path(sys.argv[2]), sys.argv[3], sys.argv[4]
companions = []
for index in range(4):
    relative = f'registry/companion-{index}.json'
    companions.append(artifacts.CompanionChange(
        relative, stage / f'k{index}', artifacts.paths.hash_file(repo / relative)))
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
artifacts.publish_set(repo, 'raw_source', [], 'fixture', companions=companions,
                      expected_members={'raw/a.txt', 'raw/b.txt'},
                      expected_manifest=expected_manifest)
"""
    unrelated = repo / "data/raw" / (".lu-artifact-" + "0" * 32 + "-999.tmp")
    unrelated.write_bytes(b"unrelated")
    journal_dir = paths.artifact_store_root(repo) / ".transactions"
    journal_dir.mkdir(parents=True, exist_ok=True)
    unrelated_journal = journal_dir / "tmp-unrelated-keep"
    unrelated_journal.write_bytes(b"unrelated journal scratch")
    unrelated_named = journal_dir / (".lu-journal-" + "0" * 32 + "-unrelated.tmp")
    unrelated_named.write_bytes(b"unrelated named file")
    result = subprocess.run(
        [sys.executable, "-c", script, str(repo), str(stage), point, digest],
        cwd=Path(__file__).resolve().parents[2],
        check=False,
        timeout=30,
    )
    assert result.returncode == -signal.SIGKILL
    first = artifacts.recover_incomplete(repo)
    assert artifacts.recover_incomplete(repo) == 0
    assert not artifacts._journal_path(repo, "raw_source", "@set").exists()
    assert first == (0 if point.startswith("store:") or point in {"prejournal", "journal_scratch"} else 1)
    committed = point in {"descriptor", "cleanup"}
    assert _a_snapshot(repo) == before_a
    manifest = paths.load_manifest("raw_source", repo)
    expected_companions = {}
    for index in range(4):
        content = f"K{index}-new".encode() if committed else f"K{index}-old".encode()
        assert (repo / f"registry/companion-{index}.json").read_bytes() == content
        expected_companions[f"registry/companion-{index}.json"] = hashlib.sha256(content).hexdigest()
    assert manifest["set_descriptor"]["companions"] == expected_companions
    assert manifest["set_descriptor"]["members"] == ["raw/a.txt", "raw/b.txt"]
    snapshot = paths.artifact_set("raw_source", repo=repo)
    assert snapshot.artifacts == {"raw/a.txt": b"A-bound", "raw/b.txt": b"B1"}
    assert snapshot.companions == {
        f"registry/companion-{index}.json": (f"K{index}-new".encode() if committed else f"K{index}-old".encode())
        for index in range(4)
    }
    assert unrelated.read_bytes() == b"unrelated"
    assert unrelated_journal.read_bytes() == b"unrelated journal scratch"
    assert unrelated_named.read_bytes() == b"unrelated named file"
    assert not any(artifacts._JOURNAL_SCRATCH.fullmatch(path.name) for path in journal_dir.iterdir())
    assert list((repo / "data").rglob(".lu-artifact-*.tmp")) == [unrelated]
    assert list((repo / "registry").rglob(".lu-artifact-*.tmp")) == []


def test_companion_only_reader_waits_for_the_complete_generation(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repo = _repo(tmp_path)
    _bind_companions(repo, tmp_path, 1)
    stage = tmp_path / "k"
    stage.write_bytes(b"K0-new")
    pause = tmp_path / "paused"
    release = tmp_path / "release"
    a_mtime = (repo / "data/raw/a.txt").stat().st_mtime_ns
    script = """
import sys, time
from pathlib import Path
from scripts.storage import artifacts
repo, stage, pause, release = map(Path, sys.argv[1:5])
expected_manifest = sys.argv[5]
sha_k = artifacts.paths.hash_file(repo / 'registry/companion-0.json')
install = artifacts._install
def hooked_install(temp, target):
    install(temp, target)
    if target.name == 'companion-0.json':
        pause.write_text('ready')
        while not release.exists(): time.sleep(0.01)
artifacts._install = hooked_install
artifacts.publish_set(repo, 'raw_source', [], 'fixture',
    companions=[artifacts.CompanionChange('registry/companion-0.json', stage, sha_k)],
    expected_members={'raw/a.txt', 'raw/b.txt'}, expected_manifest=expected_manifest)
"""
    child = subprocess.Popen(
        [
            sys.executable,
            "-c",
            script,
            str(repo),
            str(stage),
            str(pause),
            str(release),
            _digest(repo),
        ],
        cwd=Path(__file__).resolve().parents[2],
    )
    try:
        deadline = time.monotonic() + 10
        while not pause.exists() and time.monotonic() < deadline and child.poll() is None:
            time.sleep(0.01)
        assert pause.exists()
        outcome: list[paths.ArtifactSet] = []
        saw_pending = threading.Event()
        pending = paths._pending_publication

        def observed_pending(checkout: Path) -> bool:
            result = pending(checkout)
            if result:
                saw_pending.set()
            return result

        monkeypatch.setattr(paths, "_pending_publication", observed_pending)
        reader = threading.Thread(target=lambda: outcome.append(paths.artifact_set("raw_source", repo=repo)))
        reader.start()
        assert saw_pending.wait(timeout=5)
        release.write_text("go")
        reader.join(timeout=10)
        assert not reader.is_alive()
        assert child.wait(timeout=10) == 0
        assert outcome[0].artifacts == {"raw/a.txt": b"A-bound", "raw/b.txt": b"B1"}
        assert outcome[0].companions == {"registry/companion-0.json": b"K0-new"}
        assert (repo / "data/raw/a.txt").stat().st_mtime_ns == a_mtime
    finally:
        release.write_text("go")
        if child.poll() is None:
            child.kill()
            child.wait(timeout=10)


def test_companion_only_recovery_refuses_missing_store_object(tmp_path: Path) -> None:
    repo = _repo(tmp_path)
    _bind_companions(repo, tmp_path, 1)
    stage = tmp_path / "k"
    stage.write_bytes(b"K0-new")
    script = """
import os, signal, sys
from pathlib import Path
from scripts.storage import artifacts
repo, stage, expected_manifest = Path(sys.argv[1]), Path(sys.argv[2]), sys.argv[3]
sha_k = artifacts.paths.hash_file(repo / 'registry/companion-0.json')
install = artifacts._install
def interrupt(temp, target):
    install(temp, target)
    os.kill(os.getpid(), signal.SIGKILL)
artifacts._install = interrupt
artifacts.publish_set(repo, 'raw_source', [], 'fixture',
    companions=[artifacts.CompanionChange('registry/companion-0.json', stage, sha_k)],
    expected_members={'raw/a.txt', 'raw/b.txt'}, expected_manifest=expected_manifest)
"""
    result = subprocess.run(
        [sys.executable, "-c", script, str(repo), str(stage), _digest(repo)],
        cwd=Path(__file__).resolve().parents[2],
        check=False,
        timeout=30,
    )
    assert result.returncode == -signal.SIGKILL
    old_obj = paths.artifact_store_root(repo) / hashlib.sha256(b"K0-old").hexdigest()
    old_obj.unlink()
    journal = artifacts._journal_path(repo, "raw_source", "@set")
    with pytest.raises(artifacts.RecoveryError, match="missing or corrupt store object"):
        artifacts.recover_incomplete(repo)
    assert journal.exists()
    with pytest.raises(ValueError, match="did not settle"):
        paths.artifact_set("raw_source", repo=repo, retries=2)
    old_obj.write_bytes(b"K0-old")
    assert artifacts.recover_incomplete(repo) == 1
    assert artifacts.recover_incomplete(repo) == 0
    assert (repo / "registry/companion-0.json").read_bytes() == b"K0-old"
    assert (repo / "data/raw/a.txt").read_bytes() == b"A-bound"
    assert paths.artifact_set("raw_source", repo=repo).companions == {"registry/companion-0.json": b"K0-old"}
