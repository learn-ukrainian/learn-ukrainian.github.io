"""Copy-proof regressions for regenerable ignored output (#11387)."""

import json
import os

import pytest

from scripts.fleet import ignored_task_output as output
from scripts.fleet import regenerable_output as classifier
from tests.orchestration.test_worktree_git import _add_dispatch_worktree, _run, _write_task_state
from tests.orchestration.test_worktree_git import hermetic_repo as hermetic_repo


@pytest.fixture
def proof_repo(hermetic_repo):
    repo, tasks = hermetic_repo
    with classifier.copy_proof_run(primary=repo, tasks=tasks):
        yield repo, tasks


def prepare(proof_repo):
    repo, tasks = proof_repo
    (repo / ".gitignore").write_text(
        ".worktrees/\nbatch_state/\nnode_modules/\n.venv/\nsite/dist/\n.cache/\ndata/\nscreenshots/\n"
    )
    (repo / "package-lock.json").write_text('{"lockfileVersion": 3}')
    (repo / "requirements.txt").write_text("pytest==8.4.2\n")
    _run(["git", "add", ".gitignore", "package-lock.json", "requirements.txt"], cwd=repo)
    _run(["git", "commit", "-m", "fixture inputs"], cwd=repo)
    _run(["git", "push", "origin", "main"], cwd=repo)
    tree = _add_dispatch_worktree(repo, "codex", "proof-cap")
    _write_task_state(tasks, "proof-cap", "done", tree, agent="codex")
    return repo, tasks, tree


def put(root, name, payload=b"output"):
    path = root / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(payload)
    return path


@pytest.mark.parametrize("kind", ["symlink", "fifo", "ancestor"])
def test_proof_never_follows_links_or_special_files(proof_repo, kind):
    repo, _, tree = prepare(proof_repo)
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
def test_changed_identity_during_copy_hash_cannot_lend_proof(proof_repo, monkeypatch, changed):
    repo, _, tree = prepare(proof_repo)
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


@pytest.mark.parametrize("mutation", ["cfg_link", "dirty_input", "staged_input", "hardlink"])
def test_environment_proof_refuses_unrebuildable_or_external_files(proof_repo, monkeypatch, mutation):
    repo, _, tree = prepare(proof_repo)
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
            _run(["git", "add", "requirements.txt"], cwd=tree)
            (tree / "requirements.txt").write_bytes((repo / "requirements.txt").read_bytes())
    assert not classifier.is_regenerable_ignored_path(
        ".venv/lib/package.py", worktree=tree, tracked={"requirements.txt"}, ignored={".venv/lib/package.py"}
    )


def test_recorded_archive_is_verified_before_exclusion(proof_repo, monkeypatch):
    repo, tasks, tree = prepare(proof_repo)
    put(tree, "screenshots/page.png", b"archived screenshot" * 30)
    record = json.loads((tasks / "proof-cap.json").read_text())
    receipt, _ = output.capture_abandon_output(tree, primary=repo, record=record)
    output.publish_abandon_output(tree, primary=repo, record=record, locator=receipt)
    record["preserved_artifacts"] = receipt
    (tasks / "proof-cap.json").write_text(json.dumps(record))
    monkeypatch.setattr(output, "MAX_PRESERVED_BYTES", 1)
    # Use the actual bound canonical receipt, rather than a filename assertion.
    record = json.loads((tasks / "proof-cap.json").read_text())
    assert record["preserved_artifacts"]["location"] == receipt["location"]
    with classifier.copy_proof_run(primary=repo, tasks=tasks):
        assert output._ignored_output_files(tree, repo, record) == []
    (repo / receipt["location"] / "screenshots/page.png").write_bytes(b"wrong archive")
    with classifier.copy_proof_run(primary=repo, tasks=tasks):
        assert output._ignored_output_files(tree, repo, record) == ["screenshots/page.png"]
