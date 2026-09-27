"""Content-tree pollution guard (#8631): snapshot/compare helpers and the session hooks.

The helpers under test live in ``tests.conftest``. Each test builds a throwaway
git repo in ``tmp_path``; nothing here touches the real checkout's ``curriculum/``.
"""

from __future__ import annotations

import subprocess
from pathlib import Path
from types import SimpleNamespace

import pytest

import tests.conftest as guard

pytestmark = pytest.mark.reads_content


def _git(root: Path, *args: str) -> None:
    subprocess.run(
        ["git", "-C", str(root), *args],
        check=True,
        capture_output=True,
        timeout=60,
    )


@pytest.fixture
def repo(tmp_path: Path) -> Path:
    root = tmp_path / "repo"
    (root / "curriculum").mkdir(parents=True)
    (root / "curriculum" / "tracked.txt").write_text("x\n", encoding="utf-8")
    _git(root, "init", "-q")
    _git(root, "-c", "user.name=t", "-c", "user.email=t@example.com", "add", ".")
    _git(root, "-c", "user.name=t", "-c", "user.email=t@example.com", "commit", "-q", "-m", "init")
    return root


def test_unchanged_tree_reports_no_changes(repo: Path) -> None:
    before = guard._content_tree_snapshot(repo)
    assert before == frozenset()
    assert guard._content_tree_changes(before, guard._content_tree_snapshot(repo)) == ([], [])


def test_new_untracked_file_is_reported_with_its_path(repo: Path) -> None:
    before = guard._content_tree_snapshot(repo)
    stray = repo / "curriculum" / "l2-uk-en" / "a1" / "my-morning" / "wiki_completeness_gate.json"
    stray.parent.mkdir(parents=True)
    stray.write_text("{}\n", encoding="utf-8")

    changes = guard._content_tree_changes(before, guard._content_tree_snapshot(repo))

    assert changes == (["?? curriculum/l2-uk-en/a1/my-morning/wiki_completeness_gate.json"], [])


def test_pre_existing_dirt_is_not_blamed_on_the_session(repo: Path) -> None:
    (repo / "curriculum" / "already-there.json").write_text("{}\n", encoding="utf-8")
    before = guard._content_tree_snapshot(repo)
    assert before == frozenset({"?? curriculum/already-there.json"})
    assert guard._content_tree_changes(before, guard._content_tree_snapshot(repo)) == ([], [])


def test_modified_tracked_file_is_reported(repo: Path) -> None:
    before = guard._content_tree_snapshot(repo)
    (repo / "curriculum" / "tracked.txt").write_text("changed\n", encoding="utf-8")

    assert guard._content_tree_changes(before, guard._content_tree_snapshot(repo)) == ([" M curriculum/tracked.txt"], [])


def test_deleting_a_pre_existing_untracked_file_is_reported(repo: Path) -> None:
    stray = repo / "curriculum" / "already-there.json"
    stray.write_text("{}\n", encoding="utf-8")
    before = guard._content_tree_snapshot(repo)
    stray.unlink()

    changes = guard._content_tree_changes(before, guard._content_tree_snapshot(repo))

    assert changes == ([], ["?? curriculum/already-there.json"])


def test_restoring_a_pre_existing_tracked_modification_is_reported(repo: Path) -> None:
    tracked = repo / "curriculum" / "tracked.txt"
    tracked.write_text("operator edit\n", encoding="utf-8")
    before = guard._content_tree_snapshot(repo)
    _git(repo, "checkout", "--", "curriculum/tracked.txt")

    changes = guard._content_tree_changes(before, guard._content_tree_snapshot(repo))

    assert changes == ([], [" M curriculum/tracked.txt"])


def test_outside_git_is_a_noop(tmp_path: Path) -> None:
    root = tmp_path / "not-a-repo"
    (root / "curriculum").mkdir(parents=True)

    before = guard._content_tree_snapshot(root)
    (root / "curriculum" / "stray.json").write_text("{}\n", encoding="utf-8")

    assert before is None
    assert guard._content_tree_changes(before, guard._content_tree_snapshot(root)) == ([], [])


def test_subdirectory_of_an_outer_repo_is_a_noop(repo: Path) -> None:
    nested = repo / "vendored"
    nested.mkdir()

    assert guard._content_tree_snapshot(nested) is None


def _session(**config_attrs: object) -> SimpleNamespace:
    return SimpleNamespace(config=SimpleNamespace(**config_attrs), exitstatus=pytest.ExitCode.OK)


def test_session_fails_and_names_the_new_path(
    repo: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setattr(guard, "_REPO_ROOT", repo)
    session = _session()
    guard.pytest_sessionstart(session)
    (repo / "curriculum" / "leak.json").write_text("{}\n", encoding="utf-8")

    guard.pytest_sessionfinish(session, 0)

    assert session.exitstatus == pytest.ExitCode.TESTS_FAILED
    assert "curriculum/leak.json" in capsys.readouterr().out


def test_session_fails_when_a_pre_existing_file_is_removed(
    repo: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setattr(guard, "_REPO_ROOT", repo)
    (repo / "curriculum" / "already-there.json").write_text("{}\n", encoding="utf-8")
    session = _session()
    guard.pytest_sessionstart(session)
    (repo / "curriculum" / "already-there.json").unlink()

    guard.pytest_sessionfinish(session, 0)

    out = capsys.readouterr().out
    assert session.exitstatus == pytest.ExitCode.TESTS_FAILED
    assert "removed since session start" in out
    assert "added since session start" not in out
    assert "?? curriculum/already-there.json" in out


def test_failure_message_names_the_session_and_concurrent_writers(
    repo: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setattr(guard, "_REPO_ROOT", repo)
    session = _session()
    guard.pytest_sessionstart(session)
    (repo / "curriculum" / "leak.json").write_text("{}\n", encoding="utf-8")

    guard.pytest_sessionfinish(session, 0)

    out = capsys.readouterr().out
    assert "changed during the test session" in out
    assert "operator build" in out
    assert "added since session start" in out


def test_session_passes_when_nothing_changed(repo: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(guard, "_REPO_ROOT", repo)
    session = _session()
    guard.pytest_sessionstart(session)

    guard.pytest_sessionfinish(session, 0)

    assert session.exitstatus == pytest.ExitCode.OK


def test_xdist_worker_takes_no_snapshot_and_never_enforces(repo: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(guard, "_REPO_ROOT", repo)
    session = _session(workerinput={"workerid": "gw0"})

    guard.pytest_sessionstart(session)
    (repo / "curriculum" / "leak.json").write_text("{}\n", encoding="utf-8")
    guard.pytest_sessionfinish(session, 0)

    assert not hasattr(session.config, guard._CONTENT_TREE_SNAPSHOT_KEY)
    assert session.exitstatus == pytest.ExitCode.OK


def test_session_outside_git_is_a_noop(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(guard, "_REPO_ROOT", tmp_path)
    session = _session()
    guard.pytest_sessionstart(session)
    (tmp_path / "curriculum").mkdir()
    (tmp_path / "curriculum" / "leak.json").write_text("{}\n", encoding="utf-8")

    guard.pytest_sessionfinish(session, 0)

    assert session.exitstatus == pytest.ExitCode.OK
