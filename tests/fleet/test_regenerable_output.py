"""Build-writer examples and preservation boundaries for #10061."""

import os
import subprocess

import pytest

from scripts.fleet import ignored_task_output as output
from scripts.fleet import regenerable_output as patterns
from tests import test_fleet_post_task_reap as reap_fixtures
from tests.orchestration import test_worktree_artifacts as fixtures

checkout = fixtures.checkout
hermetic_reap = reap_fixtures.hermetic_reap

# Independent concrete examples from the writers cited by the classifier.
BUILD_OUTPUTS = [
    "site/dist/index.html",
    "site/dist/b1/unit/lesson/index.html",
    "site/dist/b2/unit/lesson/index.html",
    "site/dist/api/lexicon/search/00.json",
    "site/dist/lexicon/example/index.html",
    "site/src/data/lexicon-manifest.json",
    "site/src/data/lexicon-manifest.json.tmp",
    *[
        f"site/public/lexicon/practice-{kind}.A1.json"
        for kind in (
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
        )
    ],
    "site/public/lexicon/practice-index.A1.json.tmp",
    "site/public/lexicon/practice-deck.teacher.json",
    "site/public/lexicon/practice-cloze.teacher.json",
    *[f"site/public/api/lexicon/practice-{kind}.C1.json" for kind in ("index", "lexemes", "cloze")],
    "site/public/lexicon/search/00.json",
    "site/public/atlas/current.json",
    "site/public/atlas/.current-123-abcdef12.json",
    "site/public/atlas/versions/v1/manifest.json",
    "site/public/atlas/versions/.export-123-abcdef12/manifest.json",
    "site/public/atlas/versions/v1/entries/00.json.gz",
    "site/public/atlas/versions/v1/search/articles/00.json.gz",
    "site/public/atlas/versions/v1/search/aliases/00.json.gz",
    *[f"site/public/atlas/versions/v1/decks/A1/{kind}.json.gz" for kind in ("index", "lexemes", "cloze")],
    "site/public/audio/pronunciation/manifest.json",
]


def ignore_site(repo):
    # Broad fixture ignore rules also exercise ignored *unlisted* output.
    (repo / ".gitignore").write_text("site\ndata/\nignored/\n")


@pytest.mark.parametrize("name", BUILD_OUTPUTS)
def test_build_output_skips_preservation_and_cap(checkout, monkeypatch, name):
    repo, primary, _ = checkout
    ignore_site(repo)
    fixtures.artifact(checkout, name, b"rebuildable" * 10)
    monkeypatch.setattr(output, "MAX_PRESERVED_BYTES", 1)
    monkeypatch.setattr(output.artifacts, "_fingerprint", lambda *_args, **_kwargs: pytest.fail("build bytes read"))
    assert patterns.is_regenerable_ignored_path(name, worktree=repo, tracked=set())
    assert output._ignored_output_files(repo, primary, {}) == []
    assert fixtures.guard(checkout) == (True, "", None)


@pytest.mark.parametrize(
    "name",
    [
        "ignored/large.bin",
        "site/public/unlisted.json",
        "site/public/api/lexicon/private.json",
        "site/public/lexicon/practice-unknown.A1.json",
        "site/public/lexicon/practice-imperative.A1.json.tmp",
        "site/public/lexicon/practice-cloze.A1.json/only-copy.json",
        "site/public/atlas/notes.json",
        "site/public/audio/pronunciation/only-copy.wav",
        "site/src/data/unlisted.json",
        "site/src/data/lexicon-manifest.staged.json",
        "site/src/data/lexicon-manifest.json.gz",
        "data/atlas.db",
        "site/dist/example.db",
        "site/dist/example.sqlite3",
        "site/dist/example.db.gz",
        "site/dist/example.db-wal",
        "site/dist/example.sqlite3-shm",
        "site/dist/nested/example.duckdb",
        "site/src/data/example.db",
    ],
)
def test_unlisted_ignored_output_still_blocks(checkout, monkeypatch, name):
    repo, primary, _ = checkout
    ignore_site(repo)
    path = fixtures.artifact(checkout, name, b"unique output" * 100)
    monkeypatch.setattr(output, "MAX_PRESERVED_BYTES", 10)
    assert not patterns.is_regenerable_ignored_path(name, worktree=repo, tracked=set())
    assert output._ignored_output_files(repo, primary, {}) == [name]
    ok, reason, receipt = fixtures.guard(checkout)
    assert not ok and "exceeds preservation cap" in reason
    assert receipt["count"] == 1 and receipt["bytes"] == path.stat().st_size
    assert path.exists()


@pytest.mark.parametrize("name", BUILD_OUTPUTS)
def test_tracked_build_path_is_never_regenerable(checkout, name):
    repo, primary, _ = checkout
    ignore_site(repo)
    fixtures.artifact(checkout, name)
    subprocess.run(
        ["git", "add", "-f", "--", name],
        cwd=repo,
        env=output.artifacts._safe_git_env(),
        check=True,
        capture_output=True,
        timeout=30,
    )
    tracked = set(output.artifacts._git_paths(repo, "--cached"))
    assert not patterns.is_regenerable_ignored_path(name, worktree=repo, tracked=tracked)
    # Tracked content belongs to Git, never to the ignored-output inventory.
    assert output._ignored_output_files(repo, primary, {"response": f"Output `{name}`."}) == []


@pytest.mark.parametrize("link_name", ["site", "site/dist", "site/dist/link"])
def test_build_symlink_and_descendants_are_not_regenerable(checkout, link_name):
    repo, primary, _ = checkout
    ignore_site(repo)
    outside = repo.parent / "outside"
    target = outside / ("dist/index.html" if link_name == "site" else "index.html")
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(b"only copy")
    link = repo / link_name
    link.parent.mkdir(parents=True, exist_ok=True)
    link.symlink_to(outside, target_is_directory=True)
    name = f"{link_name}/" + ("dist/index.html" if link_name == "site" else "index.html")
    assert not patterns.is_regenerable_ignored_path(link_name, worktree=repo, tracked=set())
    assert not patterns.is_regenerable_ignored_path(name, worktree=repo, tracked=set())
    assert link_name in output._ignored_output_files(repo, primary, {})
    assert target.read_bytes() == b"only copy"


@pytest.mark.parametrize(
    "name",
    [
        "",
        "/site/dist/index.html",
        "site/dist/../index.html",
        "site/dist/.venv/index.html",
    ],
)
def test_invalid_build_paths_are_refused(checkout, name):
    assert not patterns.is_regenerable_ignored_path(name, worktree=checkout[0], tracked=set())


def test_real_build_directory_is_not_a_subtree_exemption(checkout):
    repo, primary, _ = checkout
    ignore_site(repo)
    fixtures.artifact(checkout, "site/dist/index.html")
    fixtures.artifact(checkout, "site/dist/example.db")
    assert not patterns.is_regenerable_ignored_path("site/dist", worktree=repo, tracked=set())
    assert output._ignored_output_files(repo, primary, {}) == ["site/dist/example.db"]


def test_nonregular_build_output_is_refused(checkout):
    repo = checkout[0]
    name = "site/dist/pipe.json"
    pipe = repo / name
    pipe.parent.mkdir(parents=True)
    os.mkfifo(pipe)
    assert not patterns.is_regenerable_ignored_path(name, worktree=repo, tracked=set())


def test_site_outputs_do_not_change_delegate_auto_finalize():
    assert not patterns.is_disposable_auto_finalize_path("site/dist/index.html")
    assert not patterns.is_disposable_auto_finalize_path("site/src/data/lexicon-manifest.json")


@pytest.mark.parametrize(
    "remaining", [None, "data/atlas.db", "site/public/unlisted.json", "site/src/data/unlisted.json"]
)
def test_common_reaper_removes_only_regenerable_build_output(hermetic_reap, monkeypatch, remaining):
    repo, tasks = hermetic_reap
    ignore_site(repo)
    reap_fixtures._run(["git", "add", ".gitignore"], cwd=repo)
    reap_fixtures._run(["git", "commit", "-m", "fixture build ignores"], cwd=repo)
    reap_fixtures._run(["git", "push", "origin", "main"], cwd=repo)
    tree = reap_fixtures._add_dispatch_worktree(repo, "codex", "site-build-10061")
    for name in [*BUILD_OUTPUTS, *([remaining] if remaining else [])]:
        path = tree / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(b"x" * 64)
    reap_fixtures._write_task_state(tasks, "site-build-10061", "done", tree, agent="codex")
    monkeypatch.setattr(output, "MAX_PRESERVED_BYTES", 1)
    report = reap_fixtures.post_task_reap.post_task_reap(
        "site-build-10061", tasks_dir=tasks, repo_root=repo, apply=True, include_acp_runtime=False
    )
    row = report["main_worktree"]
    if remaining:
        assert row["action"] == "skipped" and tree.exists(), report
        assert "exceeds preservation cap" in row["reason"]
        assert [entry["path"] for entry in row["preserved_artifacts"]["paths"]] == [remaining]
    else:
        assert row["action"] == "removed" and not tree.exists(), report
        assert not row.get("preserved_artifacts")
    assert not (repo / "batch_state/preserved").exists()
