"""Only byte-identical, committed release pins may exempt local Atlas output."""

import gzip
import hashlib
import json
import os
import shutil
import subprocess
from pathlib import Path

import pytest

from scripts.common import github_client
from scripts.fleet import ignored_task_output as output
from scripts.fleet import regenerable_output as patterns
from tests import test_fleet_post_task_reap as reap_fixtures
from tests.orchestration import test_worktree_artifacts as fixtures

checkout = fixtures.checkout
hermetic_reap = reap_fixtures.hermetic_reap
MANIFEST = "site/src/data/lexicon-manifest.json"
PRACTICE = "site/public/lexicon/practice-index.A1.json"
POINTER = "site/src/data/lexicon-manifest.pointer.json"
PRACTICE_POINTER = "site/src/data/lexicon-practice-deck.pointer.json"


@pytest.fixture(autouse=True)
def release_store(monkeypatch):
    """Hermetic upload store with metadata derived from real compressed bytes."""

    def listing(args, **kwargs):
        assert args[:2] == ["gh", "api"]
        assert kwargs["timeout"] == 10 and kwargs["fresh"] is True
        store = Path(kwargs["cwd"]).parent / "release-store.json"
        assets = json.loads(store.read_text()) if store.exists() else []
        return subprocess.CompletedProcess(args, 0, json.dumps({"assets": assets}))

    monkeypatch.setattr(github_client, "run", listing)


def upload_fixture(repo, pointer, source):
    store = repo.parent / "release-store.json"
    assets = json.loads(store.read_text()) if store.exists() else []
    gz = repo.parent / (Path(source).name + ".gz")
    with (repo / source).open("rb") as src, gzip.open(gz, "wb") as dst:
        shutil.copyfileobj(src, dst)
    compressed = gz.read_bytes()
    pointer.update(gz_bytes=len(compressed), gz_sha256=hashlib.sha256(compressed).hexdigest())
    assets = [asset for asset in assets if asset["browser_download_url"] != pointer["asset_url"]]
    assets.append(
        {
            "browser_download_url": pointer["asset_url"],
            "state": "uploaded",
            "size": len(compressed),
            "digest": "sha256:" + hashlib.sha256(compressed).hexdigest(),
        }
    )
    store.write_text(json.dumps(assets))


def git(repo, *args):
    return subprocess.run(
        ["git", *args],
        cwd=repo,
        env=output.artifacts._safe_git_env(),
        check=True,
        capture_output=True,
        timeout=30,
    ).stdout


def pinned_checkout(checkout):
    repo, _, _ = checkout
    (repo / ".gitignore").write_text("node_modules/\nsite/src/data/*.json\nsite/public/\nignored/\ndata/\n")
    payload = b'{"version":"0.1","entries":[],"manifest_fingerprint":{"schema_version":1,"fingerprint":"abc"}}'
    fixtures.artifact(checkout, MANIFEST, payload)
    shard = b'{"counts":{"lexemes":0}}'
    fixtures.artifact(checkout, PRACTICE, shard)
    pointer = {
        "asset_url": "https://github.com/learn-ukrainian/learn-ukrainian.github.io/releases/download/atlas-manifest/test.json.gz",
        "release_tag": "atlas-manifest",
        "manifest_version": "0.1",
        "manifest_fingerprint": "abc",
        "fingerprint_schema_version": 1,
        "json_bytes": len(payload),
        "json_sha256": hashlib.sha256(payload).hexdigest(),
    }
    practice_pointer = {
        "asset_url": "https://github.com/learn-ukrainian/learn-ukrainian.github.io/releases/download/atlas-practice-deck/test.json.gz",
        "release_tag": "atlas-practice-deck",
        "deck_version": "test",
        "package_schema_version": 1,
        "package_bytes": len(shard),
        "package_sha256": hashlib.sha256(shard).hexdigest(),
        "file_count": 1,
        "files": [
            {
                "path": "practice-index.A1.json",
                "bytes": len(shard),
                "sha256": hashlib.sha256(shard).hexdigest(),
                "kind": "index",
                "level": "A1",
            }
        ],
    }
    upload_fixture(repo, pointer, MANIFEST)
    upload_fixture(repo, practice_pointer, PRACTICE)
    fixtures.artifact(checkout, POINTER, json.dumps(pointer).encode())
    fixtures.artifact(checkout, PRACTICE_POINTER, json.dumps(practice_pointer).encode())
    fixtures.artifact(checkout, "site/package-lock.json", b'{"lockfileVersion":3}')
    source_root = Path(__file__).resolve().parents[2]
    for name in ("hydrate-manifest.mjs", "hydrate-practice-deck.mjs"):
        relative = f"site/scripts/{name}"
        fixtures.artifact(checkout, relative, (source_root / relative).read_bytes())
    git(repo, "add", "-f", ".gitignore", POINTER, PRACTICE_POINTER, "site/package-lock.json", "site/scripts")
    git(repo, "-c", "user.name=Test", "-c", "user.email=test@example.invalid", "commit", "-m", "fixture pins")
    return payload, shard


@pytest.mark.parametrize("capped", [False, True])
def test_never_uploaded_pointer_preserves_only_copy(checkout, monkeypatch, capped):
    payload, _ = pinned_checkout(checkout)
    repo, primary, _ = checkout
    monkeypatch.setattr(
        github_client, "run", lambda *args, **kwargs: subprocess.CompletedProcess(args, 0, '{"assets":[]}')
    )
    if capped:
        monkeypatch.setattr(output, "MAX_PRESERVED_BYTES", 1)
    tracked = set(output.artifacts._git_paths(repo, "--cached"))
    assert not patterns.is_regenerable_ignored_path(MANIFEST, worktree=repo, tracked=tracked)
    ok, reason, receipt = fixtures.guard(checkout)
    assert ok is not capped
    assert {entry["path"] for entry in receipt["paths"]} == {MANIFEST, PRACTICE}
    if capped:
        assert "exceeds preservation cap" in reason
        assert (repo / MANIFEST).read_bytes() == payload
    else:
        assert (primary / receipt["location"] / MANIFEST).read_bytes() == payload


def test_reviewer_unuploaded_pointer_manifest_requires_preservation(checkout, monkeypatch):
    # Regression form of 9828-review-probe-test.py. The pointer commit has
    # never reached main and its asset is absent from the release store.
    payload, _ = pinned_checkout(checkout)
    repo = checkout[0]
    head = git(repo, "rev-parse", "HEAD").strip()
    assert head and (repo / MANIFEST).read_bytes() == payload
    monkeypatch.setattr(github_client, "run", lambda *args, **kwargs: subprocess.CompletedProcess(args, 0, '{"assets":[]}'))
    ok, reason, receipt = fixtures.guard(checkout)
    assert ok and not reason and receipt is not None
    assert (checkout[1] / receipt["location"] / MANIFEST).read_bytes() == payload


@pytest.mark.parametrize("change", ["digest", "digestless", "size", "url", "state", "duplicate", "shape"])
def test_asset_listing_must_match_pointer(checkout, monkeypatch, change):
    pinned_checkout(checkout)
    repo = checkout[0]
    assets = json.loads((repo.parent / "release-store.json").read_text())
    if change == "digest":
        assets[0]["digest"] = "sha256:" + "0" * 64
    elif change == "digestless":
        assets[0].pop("digest")
    elif change == "size":
        assets[0]["size"] += 1
    elif change == "url":
        assets[0]["browser_download_url"] += "-other"
    elif change == "state":
        assets[0]["state"] = "starter"
    elif change == "duplicate":
        assets.append(assets[0])
    else:
        assets = None
    monkeypatch.setattr(
        github_client,
        "run",
        lambda *args, **kwargs: subprocess.CompletedProcess(args, 0, json.dumps({"assets": assets})),
    )
    tracked = set(output.artifacts._git_paths(repo, "--cached"))
    assert not patterns.is_regenerable_ignored_path(MANIFEST, worktree=repo, tracked=tracked)
    assert MANIFEST in output._ignored_output_files(repo, checkout[1], {})


@pytest.mark.parametrize(
    "error",
    [
        OSError("unavailable"),
        subprocess.TimeoutExpired("gh", 10),
        subprocess.CalledProcessError(1, "gh"),
        ValueError("bad JSON"),
    ],
)
def test_asset_listing_error_fails_closed(checkout, monkeypatch, error):
    pinned_checkout(checkout)

    def fail(*args, **kwargs):
        raise error

    monkeypatch.setattr(github_client, "run", fail)
    assert MANIFEST in output._ignored_output_files(checkout[0], checkout[1], {})


@pytest.mark.parametrize("state", ["valid", "mismatch", "symlink", "ancestor-link", "unignored"])
@pytest.mark.parametrize("stem,name", [("lexicon-manifest", MANIFEST), ("lexicon-practice-deck", PRACTICE)])
def test_kept_gzip_requires_safe_matching_bytes(checkout, monkeypatch, stem, name, state):
    pinned_checkout(checkout)
    repo, primary, _ = checkout
    kept = f"site/src/data/{stem}.json.gz"
    gz = repo.parent / (Path(name).name + ".gz")
    if state != "unignored":
        (repo / ".gitignore").write_text((repo / ".gitignore").read_text() + "site/src/data/*.gz\n")
    else:
        (repo / ".gitignore").write_text((repo / ".gitignore").read_text().replace("data/\n", "/data/\n"))
    if state == "symlink":
        (repo / kept).symlink_to(gz)
    else:
        fixtures.artifact(checkout, kept, gz.read_bytes() if state != "mismatch" else b"x" * gz.stat().st_size)
    if state == "ancestor-link":
        (repo / kept).parent.rename(repo.parent / "saved-data")
        (repo / kept).parent.symlink_to(repo.parent / "saved-data", target_is_directory=True)

    def no_network(*args, **kwargs):
        raise AssertionError("kept gzip must avoid a network lookup")

    original = github_client.run
    tag = "atlas-manifest" if stem == "lexicon-manifest" else "atlas-practice-deck"
    monkeypatch.setattr(
        github_client,
        "run",
        lambda args, **kwargs: no_network() if args[-1].endswith(tag) else original(args, **kwargs),
    )
    tracked = set(output.artifacts._git_paths(repo, "--cached"))
    assert patterns.is_regenerable_ignored_path(name, worktree=repo, tracked=tracked) is (state == "valid")
    if state != "ancestor-link":
        files = output._ignored_output_files(repo, primary, {})
        assert (kept in files) is (state != "unignored")
        assert (name in files) is (state != "valid")
    if state == "valid":
        ok, reason, receipt = fixtures.guard(checkout)
        assert ok and not reason
        assert (primary / receipt["location"] / kept).read_bytes() == gz.read_bytes()
        monkeypatch.setattr(output, "MAX_PRESERVED_BYTES", 1)
        ok, reason, _ = fixtures.guard(checkout)
        assert not ok and "exceeds preservation cap" in reason


@pytest.mark.parametrize("total_bytes", [760_367_968, 788_933_556])
def test_observed_size_regenerable_tree_has_no_preservation(checkout, total_bytes):
    payload, shard = pinned_checkout(checkout)
    repo = checkout[0]
    # Model the actual 268,927,409-byte manifest, with valid JSON followed by
    # whitespace. Sparse dependency bytes supply the rest of each observed total.
    manifest_size = 268_927_409
    digest = hashlib.sha256(payload)
    remaining = manifest_size - len(payload)
    with (repo / MANIFEST).open("ab") as stream:
        while remaining:
            chunk = b" " * min(1024 * 1024, remaining)
            stream.write(chunk)
            digest.update(chunk)
            remaining -= len(chunk)
    pointer = json.loads((repo / POINTER).read_bytes())
    pointer.update(json_bytes=manifest_size, json_sha256=digest.hexdigest())
    upload_fixture(repo, pointer, MANIFEST)
    (repo / POINTER).write_text(json.dumps(pointer))
    git(repo, "add", "-f", POINTER)
    git(repo, "-c", "user.name=Test", "-c", "user.email=test@example.invalid", "commit", "-m", "fixture large pin")
    bulk = fixtures.artifact(checkout, "site/node_modules/package/index.js", b"")
    with bulk.open("wb") as stream:
        stream.truncate(total_bytes - manifest_size - len(shard))
    assert (
        sum((checkout[0] / name).stat().st_size for name in (MANIFEST, PRACTICE, "site/node_modules/package/index.js"))
        == total_bytes
    )
    assert fixtures.guard(checkout) == (True, "", None)
    assert not (checkout[1] / "batch_state/preserved").exists()


@pytest.mark.parametrize("name,pointer", [(MANIFEST, POINTER), (PRACTICE, PRACTICE_POINTER)])
@pytest.mark.parametrize(
    "state",
    [
        "pinned",
        "modified",
        "untracked",
        "unignored",
        "staged-pointer",
        "modified-pointer",
        "uncommitted-command",
        "symlink",
        "ancestor-link",
    ],
)
def test_release_output_requires_committed_pin_and_local_ignored_bytes(checkout, name, pointer, state):
    pinned_checkout(checkout)
    repo = checkout[0]
    file = repo / name
    if state == "modified":
        file.write_bytes(b"unpublished work")
    elif state == "untracked":
        git(repo, "rm", "--cached", "--", pointer)
    elif state == "unignored":
        (repo / ".gitignore").write_text("ignored/\n")
    elif state in {"staged-pointer", "modified-pointer"}:
        value = json.loads((repo / pointer).read_bytes())
        value["release_tag"] = "unpublished"
        (repo / pointer).write_text(json.dumps(value))
        if state == "staged-pointer":
            git(repo, "add", "-f", pointer)
    elif state == "uncommitted-command":
        command = "hydrate-manifest.mjs" if name == MANIFEST else "hydrate-practice-deck.mjs"
        git(repo, "rm", "--cached", f"site/scripts/{command}")
    elif state in {"symlink", "ancestor-link"}:
        outside = repo.parent / "outside"
        outside.mkdir()
        (outside / file.name).write_bytes(file.read_bytes())
        file.unlink()
        if state == "symlink":
            file.symlink_to(outside / file.name)
        else:
            # Move, never remove, the pointer siblings before replacing the parent.
            file.parent.rename(repo.parent / "saved-parent")
            file.parent.symlink_to(outside, target_is_directory=True)
    tracked = set(output.artifacts._git_paths(repo, "--cached"))
    assert patterns.is_regenerable_ignored_path(name, worktree=repo, tracked=tracked) is (state == "pinned")


def test_mixed_pinned_release_preserves_only_unique_output(checkout):
    pinned_checkout(checkout)
    fixtures.artifact(checkout, "ignored/answer.txt", b"unique answer")
    ok, reason, receipt = fixtures.guard(checkout)
    assert ok and not reason
    assert [entry["path"] for entry in receipt["paths"]] == ["ignored/answer.txt"]
    assert (checkout[1] / receipt["location"] / "ignored/answer.txt").read_bytes() == b"unique answer"


def test_database_provenance_remains_a_cap_refusal(checkout):
    pinned_checkout(checkout)
    database = fixtures.artifact(checkout, "data/atlas.db", b"")
    with database.open("wb") as stream:
        stream.truncate(462_831_616)
    ok, reason, receipt = fixtures.guard(checkout)
    assert not ok and "exceeds preservation cap" in reason
    assert receipt["bytes"] == 462_831_616
    assert [entry["path"] for entry in receipt["paths"]] == ["data/atlas.db"]
    assert database.exists()


@pytest.mark.parametrize(
    "kind",
    [
        "index",
        "lexemes",
        "cloze",
        "stress",
        "classify",
        "paradigm",
        "synonym",
        "heritage",
        "paronym",
        "antonym",
        "homonym",
        "imperative",
    ],
)
@pytest.mark.parametrize("level", ["A1", "A2", "B1", "B2", "C1"])
def test_every_hydrated_practice_kind_and_level_needs_its_own_pin(checkout, kind, level):
    _, shard = pinned_checkout(checkout)
    repo = checkout[0]
    name = f"site/public/lexicon/practice-{kind}.{level}.json"
    fixtures.artifact(checkout, name, shard)
    pointer = json.loads((repo / PRACTICE_POINTER).read_bytes())
    pointer["deck_version"] = f"fixture-{kind}-{level}"
    pointer["files"][0].update(path=Path(name).name, kind=kind, level=level)
    (repo / PRACTICE_POINTER).write_text(json.dumps(pointer))
    git(repo, "add", "-f", PRACTICE_POINTER)
    git(repo, "-c", "user.name=Test", "-c", "user.email=test@example.invalid", "commit", "-m", "fixture shard pin")
    tracked = set(output.artifacts._git_paths(repo, "--cached"))
    assert patterns.is_regenerable_ignored_path(name, worktree=repo, tracked=tracked)
    (repo / name).write_bytes(b"x" * len(shard))
    assert not patterns.is_regenerable_ignored_path(name, worktree=repo, tracked=tracked)


@pytest.mark.parametrize("change", ["leaf-replace", "ancestor-replace", "ancestor-link", "grow", "rewrite"])
def test_release_hash_rejects_changes_during_read(checkout, monkeypatch, change):
    payload, _ = pinned_checkout(checkout)
    repo = checkout[0]
    file = repo / MANIFEST
    read = os.read
    changed = False

    def race(fd, size):
        nonlocal changed
        chunk = read(fd, size)
        if not changed:
            changed = True
            if change == "leaf-replace":
                file.rename(file.with_suffix(".saved"))
                file.write_bytes(b"x" * len(payload))
            elif change in {"ancestor-replace", "ancestor-link"}:
                file.parent.rename(repo.parent / "saved-parent")
                if change == "ancestor-link":
                    file.parent.symlink_to(repo.parent / "saved-parent", target_is_directory=True)
                else:
                    file.parent.mkdir()
                    file.write_bytes(b"x" * len(payload))
            elif change == "grow":
                with file.open("ab") as stream:
                    stream.write(b"new output")
            else:
                file.write_bytes(b"x" * len(payload))
        return chunk

    monkeypatch.setattr(os, "read", race)
    assert not patterns._matches_release_pin(repo, Path(MANIFEST), (len(payload), hashlib.sha256(payload).hexdigest()))


@pytest.mark.parametrize(
    "mutation",
    [
        "missing-size",
        "bad-hash",
        "bad-url",
        "bad-shape",
        "duplicate-shard",
        "unsafe-shard",
        "unlisted-shard",
        "missing-key",
        "non-object",
    ],
)
@pytest.mark.parametrize("pointer", [POINTER, PRACTICE_POINTER])
def test_unverifiable_committed_pointer_never_authorizes_removal(checkout, pointer, mutation):
    pinned_checkout(checkout)
    repo = checkout[0]
    value = json.loads((repo / pointer).read_bytes())
    if mutation == "missing-size":
        if pointer == POINTER:
            value.pop("json_bytes")
        else:
            value["files"][0].pop("bytes")
    elif mutation == "bad-hash":
        if pointer == POINTER:
            value["json_sha256"] = "bad"
        else:
            value["files"][0]["sha256"] = "bad"
    elif mutation == "bad-url":
        value["asset_url"] = "https://example.invalid/unproven"
    elif mutation == "missing-key":
        value.pop("gz_sha256")
    elif mutation == "non-object":
        value = []
    elif pointer == POINTER:
        value["manifest_version"] = None
    elif mutation == "bad-shape":
        value["files"] = [None]
    elif mutation == "duplicate-shard":
        value["files"] *= 2
        value["file_count"] = 2
    else:
        value["files"][0]["path"] = "../../answer.json" if mutation == "unsafe-shard" else "private.json"
    (repo / pointer).write_text(json.dumps(value))
    git(repo, "add", "-f", pointer)
    git(repo, "-c", "user.name=Test", "-c", "user.email=test@example.invalid", "commit", "-m", "fixture bad pin")
    tracked = set(output.artifacts._git_paths(repo, "--cached"))
    name = MANIFEST if pointer == POINTER else PRACTICE
    assert not patterns.is_regenerable_ignored_path(name, worktree=repo, tracked=tracked)


def test_tracked_file_wins_over_stale_ignored_inventory(checkout):
    repo = checkout[0]
    name = "site/dist/index.html"
    (repo / ".gitignore").write_text("site/dist/\n")
    fixtures.artifact(checkout, name)
    ignored = set(output.artifacts._git_paths(repo, "--others", "--ignored", "--exclude-standard"))
    assert name in ignored
    git(repo, "add", "-f", name)
    tracked = set(output.artifacts._git_paths(repo, "--cached"))
    assert not patterns.is_regenerable_ignored_path(name, worktree=repo, tracked=tracked, ignored=ignored)


def test_build_file_symlink_is_preserved_without_reading_target(checkout):
    repo, primary, _ = checkout
    name = "site/dist/index.html"
    (repo / ".gitignore").write_text("site/dist/\n")
    outside = repo.parent / "outside.html"
    outside.write_bytes(b"only outside copy")
    link = repo / name
    link.parent.mkdir(parents=True)
    link.symlink_to(outside)
    assert not patterns.is_regenerable_ignored_path(name, worktree=repo, tracked=set())
    ok, reason, receipt = fixtures.guard(checkout)
    assert ok and not reason
    assert receipt["paths"][0]["type"] == "symlink"
    assert b"only outside copy" not in (primary / receipt["location"] / name).read_bytes()
    assert outside.read_bytes() == b"only outside copy"


@pytest.mark.parametrize("part", ["pointer", "command"])
def test_skip_worktree_cannot_conceal_modified_release_proof(checkout, part):
    pinned_checkout(checkout)
    repo = checkout[0]
    name = POINTER if part == "pointer" else "site/scripts/hydrate-manifest.mjs"
    git(repo, "update-index", "--skip-worktree", name)
    with (repo / name).open("ab") as stream:
        stream.write(b"\nchanged")
    tracked = set(output.artifacts._git_paths(repo, "--cached"))
    assert not patterns.is_regenerable_ignored_path(MANIFEST, worktree=repo, tracked=tracked)


def test_reap_pinned_hardlinks_leaves_outside_names_and_bytes_intact(hermetic_reap, monkeypatch, tmp_path):
    repo, tasks = hermetic_reap
    payload, shard = pinned_checkout((repo, repo, tasks))
    reap_fixtures._run(["git", "push", "origin", "main"], cwd=repo)
    tree = reap_fixtures._add_dispatch_worktree(repo, "codex", "pinned-hardlink-9828")
    (tree.parent / "release-store.json").write_bytes((repo.parent / "release-store.json").read_bytes())
    outside = tmp_path / "other-manifest.json"
    os.link(repo / MANIFEST, outside)
    os.link(repo / MANIFEST, tree / MANIFEST)
    target = tree / PRACTICE
    target.parent.mkdir(parents=True)
    target.write_bytes(shard)
    assert outside.stat().st_nlink == 3
    reap_fixtures._write_task_state(tasks, "pinned-hardlink-9828", "done", tree, agent="codex")
    monkeypatch.setattr(output, "MAX_PRESERVED_BYTES", 1)
    dry = reap_fixtures.post_task_reap.post_task_reap(
        "pinned-hardlink-9828", tasks_dir=tasks, repo_root=repo, apply=False, include_acp_runtime=False
    )
    assert tree.exists() and not dry["apply"]
    report = reap_fixtures.post_task_reap.post_task_reap(
        "pinned-hardlink-9828", tasks_dir=tasks, repo_root=repo, apply=True, include_acp_runtime=False
    )
    assert report["main_worktree"]["action"] == "removed", report
    assert set(dry) == set(report)
    assert set(dry["main_worktree"]) == set(report["main_worktree"])
    assert not tree.exists()
    assert not report["main_worktree"].get("preserved_artifacts")
    assert outside.read_bytes() == (repo / MANIFEST).read_bytes() == payload
    assert outside.stat().st_nlink == 2
