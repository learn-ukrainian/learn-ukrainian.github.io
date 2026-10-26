"""Real-worktree cap and proof regressions for #11387."""

import hashlib
import json
import os

import pytest

from scripts.fleet import ignored_task_output as output
from scripts.fleet import regenerable_output as classifier
from tests import test_fleet_post_task_reap as fixtures


def _assert_record_only(primary, receipt):
    assert receipt["mode"] == "record-only"
    assert receipt["copied_bytes"] == 0
    assert "location" not in receipt


def _assert_entry(receipt, name, payload):
    entry = next(item for item in receipt["paths"] if item["path"] == str(name))
    assert entry == {"path": str(name), "size": len(payload), "sha256": hashlib.sha256(payload).hexdigest()}


hermetic_base = fixtures.hermetic_reap


@pytest.fixture
def hermetic_reap(hermetic_base):
    repo, tasks = hermetic_base
    with classifier.copy_proof_run(primary=repo, tasks=tasks):
        yield repo, tasks


def prepare(hermetic_reap):
    repo, tasks = hermetic_reap
    (repo / ".gitignore").write_text(
        ".worktrees/\nbatch_state/\nnode_modules/\n.venv/\nsite/dist/\n.cache/\ndata/\nscreenshots/\n"
    )
    (repo / "package-lock.json").write_text('{"lockfileVersion": 3}')
    (repo / "requirements.txt").write_text("pytest==8.4.2\n")
    fixtures._run(["git", "add", ".gitignore", "package-lock.json", "requirements.txt"], cwd=repo)
    fixtures._run(["git", "commit", "-m", "fixture inputs"], cwd=repo)
    fixtures._run(["git", "push", "origin", "main"], cwd=repo)
    tree = fixtures._add_dispatch_worktree(repo, "codex", "proof-cap")
    fixtures._write_task_state(tasks, "proof-cap", "done", tree, agent="codex")
    return repo, tasks, tree


def put(root, name, payload=b"output"):
    path = root / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(payload)
    return path


def reap(repo, tasks):
    return fixtures.post_task_reap.post_task_reap(
        "proof-cap", tasks_dir=tasks, repo_root=repo, apply=True, include_acp_runtime=False
    )["main_worktree"]


@pytest.mark.parametrize("name", [
    "node_modules/pkg/index.js", ".venv/lib/package.py", "site/dist/index.html",
    ".cache/arbitrary.bin", "data/atlas.db", "screenshots/page.png",
])
def test_proven_output_over_real_cap_is_reaped(hermetic_reap, name):
    """Regenerable bytes must never consume the unchanged preservation budget."""
    repo, tasks, tree = prepare(hermetic_reap)
    source = put(tree, name)
    with source.open("wb") as stream:
        stream.truncate(output.MAX_PRESERVED_BYTES + 1)
    if name.startswith(".venv/"):
        put(tree, ".venv/pyvenv.cfg", b"home = toolchain\nversion = 3.12.15\n")
    if name.startswith(("data/", ".cache/", "screenshots/")):
        copy = put(repo, name)
        with copy.open("wb") as stream:
            stream.truncate(output.MAX_PRESERVED_BYTES + 1)
    row = reap(repo, tasks)
    assert row["action"] == "removed", row
    assert not tree.exists()
    assert row["freed_bytes"] >= output.MAX_PRESERVED_BYTES + 1
    assert not row["preserved_artifacts"]


@pytest.mark.parametrize("name", ["data/atlas.db", ".cache/arbitrary.bin", ".venv/lib/package.py"])
@pytest.mark.parametrize("proof", ["absent", "different", "symlink"])
def test_unproven_names_get_record_only_receipts(hermetic_reap, monkeypatch, name, proof):
    """Copy-proof exclusions stay strict while residue cleanup records metadata."""
    repo, tasks, tree = prepare(hermetic_reap)
    put(tree, name, b"only-copy" * 32)
    if proof != "absent":
        external = put(repo, name, b"wrongcopy" * 32)
        if proof == "symlink":
            outside = put(repo, "outside", b"only-copy" * 32)
            external.unlink()
            external.symlink_to(outside)
    monkeypatch.setattr(output, "MAX_PRESERVED_BYTES", 16)
    row = reap(repo, tasks)
    assert row["action"] == "removed" and not tree.exists(), row
    receipt = row["preserved_artifacts"]
    _assert_record_only(repo, receipt)
    assert receipt["count"] == 1 and receipt["bytes"] == len(b"only-copy" * 32)
    assert receipt["paths_truncated"] is True and receipt["paths"] == []
    assert not (repo / "batch_state/preserved").exists()


@pytest.mark.parametrize("evidence_size", [16, 33])
def test_mixed_output_preserves_evidence_and_excludes_only_proven_bytes(hermetic_reap, monkeypatch, evidence_size):
    repo, tasks, tree = prepare(hermetic_reap)
    put(tree, "data/atlas.db", b"derived" * 100)
    put(repo, "data/atlas.db", b"derived" * 100)
    put(tree, ".cache/evidence.txt", b"e" * evidence_size)
    monkeypatch.setattr(output, "MAX_PRESERVED_BYTES", 32)
    row = reap(repo, tasks)
    receipt = row["preserved_artifacts"]
    assert row["action"] == "removed" and not tree.exists(), row
    _assert_record_only(repo, receipt)
    assert receipt["count"] == 1 and receipt["bytes"] == evidence_size
    assert receipt["paths_truncated"] is True and receipt["paths"] == []
    assert not (repo / "batch_state/preserved").exists()


@pytest.mark.parametrize("kind", ["symlink", "fifo", "ancestor"])
def test_proof_never_follows_links_or_special_files(hermetic_reap, kind):
    repo, _, tree = prepare(hermetic_reap)
    put(repo, "data/atlas.db", b"same")
    if kind == "ancestor":
        (tree / "data").symlink_to(repo / "data", target_is_directory=True)
    else:
        source = tree / "data/atlas.db"
        source.parent.mkdir()
        if kind == "symlink":
            source.symlink_to(repo / "data/atlas.db")
        else:
            os.mkfifo(source)
    assert not classifier.is_regenerable_ignored_path(
        "data/atlas.db", worktree=tree, tracked=set(), ignored={"data/atlas.db"}
    )
    assert (repo / "data/atlas.db").read_bytes() == b"same"


@pytest.mark.parametrize("changed", ["source", "external"])
def test_changed_identity_during_copy_hash_cannot_lend_proof(hermetic_reap, monkeypatch, changed):
    repo, _, tree = prepare(hermetic_reap)
    source = put(tree, "data/atlas.db", b"same")
    external = put(repo, "data/atlas.db", b"same")
    original = classifier.os.read
    replaced = False

    def replace_during_read(fd, size):
        nonlocal replaced
        result = original(fd, size)
        if not replaced:
            replaced = True
            target = source if changed == "source" else external
            replacement = target.with_suffix(".new")
            replacement.write_bytes(b"new!")
            replacement.replace(target)
        return result

    monkeypatch.setattr(classifier.os, "read", replace_during_read)
    assert not classifier.is_regenerable_ignored_path(
        "data/atlas.db", worktree=tree, tracked=set(), ignored={"data/atlas.db"}
    )


@pytest.mark.parametrize("kind", ["symlink", "fifo"])
def test_public_reaper_records_unproven_links_and_special_entries_without_following(hermetic_reap, monkeypatch, kind):
    repo, tasks, tree = prepare(hermetic_reap)
    source = tree / ".cache/unsafe"
    source.parent.mkdir()
    outside = put(repo, "outside", b"untouched")
    if kind == "symlink":
        source.symlink_to(outside)
    else:
        os.mkfifo(source)
    monkeypatch.setattr(output, "MAX_PRESERVED_BYTES", 1)
    row = reap(repo, tasks)
    if kind == "fifo":
        assert row["action"] in {"skipped", "error"} and tree.exists(), row
        assert os.path.lexists(source)
        assert outside.read_bytes() == b"untouched"
        return
    assert row["action"] == "removed" and not tree.exists(), row
    receipt = row["preserved_artifacts"]
    _assert_record_only(repo, receipt)
    assert receipt["inventory_error"] in {"inventory_failed", "inventory_incomplete"}
    assert receipt["count"] == 0
    assert not (repo / "batch_state/preserved").exists()
    assert outside.read_bytes() == b"untouched"


@pytest.mark.parametrize("mutation", ["cfg_link", "dirty_input", "staged_input", "hardlink"])
def test_environment_proof_refuses_unrebuildable_or_external_files(hermetic_reap, monkeypatch, mutation):
    repo, _, tree = prepare(hermetic_reap)
    source = put(tree, ".venv/lib/package.py", b"unique" * 50)
    cfg = put(tree, ".venv/pyvenv.cfg", b"home = toolchain\n")
    if mutation == "cfg_link":
        cfg.unlink()
        cfg.symlink_to(put(repo, "configuration", b"home = toolchain\n"))
    elif mutation == "hardlink":
        os.link(source, repo / "outside-environment")
    else:
        (tree / "requirements.txt").write_text("different\n")
        if mutation == "staged_input":
            fixtures._run(["git", "add", "requirements.txt"], cwd=tree)
            (tree / "requirements.txt").write_bytes((repo / "requirements.txt").read_bytes())
    assert not classifier.is_regenerable_ignored_path(
        ".venv/lib/package.py", worktree=tree, tracked={"requirements.txt"}, ignored={".venv/lib/package.py"}
    )


def test_record_only_receipt_cannot_lend_byte_copy_proof(hermetic_reap, monkeypatch):
    repo, tasks, tree = prepare(hermetic_reap)
    put(tree, "screenshots/page.png", b"archived screenshot" * 30)
    ok, reason, receipt = output.preserve_worktree_artifacts(
        tree, primary=repo, tasks_dir=tasks, task_id="proof-cap", repo_root=repo
    )
    assert ok, reason
    monkeypatch.setattr(output, "MAX_PRESERVED_BYTES", 1)
    record = json.loads((tasks / "proof-cap.json").read_text())
    assert record["preserved_artifacts"] == receipt
    _assert_record_only(repo, receipt)
    _assert_entry(receipt, "screenshots/page.png", b"archived screenshot" * 30)
    with classifier.copy_proof_run(primary=repo, tasks=tasks):
        assert output._ignored_output_files(tree, repo, record) == ["screenshots/page.png"]
    assert not (repo / "batch_state/preserved").exists()


@pytest.mark.parametrize("name", [".venv/lib/only.db", "node_modules/pkg/only.db", "site/dist/only.db"])
def test_environment_and_build_proof_cannot_discard_database_content(hermetic_reap, monkeypatch, name):
    repo, tasks, tree = prepare(hermetic_reap)
    put(tree, ".venv/pyvenv.cfg", b"home = toolchain\n")
    put(tree, name, b"only database" * 50)
    monkeypatch.setattr(output, "MAX_PRESERVED_BYTES", 32)
    row = reap(repo, tasks)
    assert row["action"] == "removed" and not tree.exists(), row
    receipt = row["preserved_artifacts"]
    _assert_record_only(repo, receipt)
    assert receipt["count"] == 1 and receipt["bytes"] == len(b"only database" * 50)
    assert receipt["paths_truncated"] is True and receipt["paths"] == []
