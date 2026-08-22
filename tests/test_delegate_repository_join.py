"""#7083: delegate repository attribution and the Work projection delegate join.

Root cause of the issue: delegate task states carried no authoritative
``repository`` / ``repository_id`` claim, so the repository-scoped production
loader behind the Work projection dropped every row — class4 reported
``delegate_tasks.count=0`` and ``dispatch.task_ids=[]`` while the unscoped
``/api/delegate/tasks`` inventory listed 23 rows including ``cf-pr-7072*``.

The fix stamps the dispatch target's authoritative ``owner/repo`` slug into
task state at dispatch time (and backfills legacy states via
``delegate.py backfill-repository``), so the scoped join admits exactly the
rows the unscoped inventory already shows. The privacy contract is unchanged:
rows with foreign, missing, or conflicting claims stay excluded from the
repository-scoped public view.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

import delegate

from scripts.api import delegate_router
from scripts.work.normalize import build_projection
from scripts.work.sources_public import (
    DEFAULT_PUBLIC_REPOSITORY,
    collect_public_sections,
)

PUBLIC_REPO = DEFAULT_PUBLIC_REPOSITORY
PRIVATE_REPO = "other-org/other-private-repo"


@pytest.fixture
def tmp_tasks_dir(tmp_path, monkeypatch):
    """Isolate delegate + delegate_router state scans in a tmp directory."""
    tasks_dir = tmp_path / "tasks"
    tasks_dir.mkdir()
    monkeypatch.setattr(delegate, "_TASKS_DIR", tasks_dir)
    monkeypatch.setattr(delegate_router, "TASKS_DIR", tasks_dir)
    # The router keeps a process-wide scan cache keyed by tasks-dir path;
    # force a cold read so each test sees only its own fixture rows.
    monkeypatch.setattr(delegate_router, "_TASK_STATE_CACHE", {})
    monkeypatch.setattr(delegate_router, "_LAST_TASKS_DIR_STR", "")
    return tasks_dir


def _git_repo_with_origin(path: Path, origin_url: str | None) -> Path:
    path.mkdir(parents=True, exist_ok=True)
    subprocess.run(["git", "init"], cwd=path, check=True, capture_output=True)
    if origin_url is not None:
        subprocess.run(
            ["git", "remote", "add", "origin", origin_url],
            cwd=path,
            check=True,
            capture_output=True,
        )
    return path


def _write_state(tasks_dir: Path, task_id: str, **fields) -> Path:
    state = {
        "task_id": task_id,
        "agent": "kimi",
        "status": "done",
        "started_at": datetime.now(UTC).isoformat(),
        "duration_s": 1.0,
    }
    state.update(fields)
    delegate._write_state_atomic(tasks_dir / f"{task_id}.json", state)
    return tasks_dir / f"{task_id}.json"


# ---------------------------------------------------------------------------
# _parse_github_owner_repo
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("url", "expected"),
    [
        ("https://github.com/learn-ukrainian/learn-ukrainian.github.io", PUBLIC_REPO),
        ("https://github.com/learn-ukrainian/learn-ukrainian.github.io.git", PUBLIC_REPO),
        ("https://github.com/learn-ukrainian/learn-ukrainian.github.io/", PUBLIC_REPO),
        ("http://github.com/learn-ukrainian/learn-ukrainian.github.io.git", PUBLIC_REPO),
        ("git@github.com:learn-ukrainian/learn-ukrainian.github.io.git", PUBLIC_REPO),
        ("ssh://git@github.com/learn-ukrainian/learn-ukrainian.github.io.git", PUBLIC_REPO),
        ("git://github.com/learn-ukrainian/learn-ukrainian.github.io", PUBLIC_REPO),
        ("https://user@github.com/learn-ukrainian/learn-ukrainian.github.io.git", PUBLIC_REPO),
        ("https://GitHub.COM/learn-ukrainian/learn-ukrainian.github.io.git", PUBLIC_REPO),
        ("  https://github.com/learn-ukrainian/learn-ukrainian.github.io.git  ", PUBLIC_REPO),
        # Non-GitHub or unparseable remotes must fail closed.
        ("https://gitlab.com/learn-ukrainian/learn-ukrainian.github.io.git", None),
        ("https://github.com.evil.example/learn-ukrainian/learn-ukrainian.github.io", None),
        ("git@github.com.evil.example:learn-ukrainian/learn-ukrainian.github.io.git", None),
        ("/local/path/to/repo", None),
        ("file:///local/path/to/repo.git", None),
        ("https://github.com/only-owner", None),
        ("", None),
        (None, None),
    ],
)
def test_parse_github_owner_repo(url, expected):
    assert delegate._parse_github_owner_repo(url) == expected


# ---------------------------------------------------------------------------
# _resolve_dispatch_repository
# ---------------------------------------------------------------------------


def test_resolve_dispatch_repository_reads_target_origin(tmp_path):
    repo = _git_repo_with_origin(tmp_path / "clone", f"https://github.com/{PUBLIC_REPO}.git")
    assert delegate._resolve_dispatch_repository(repo) == PUBLIC_REPO
    assert delegate._resolve_dispatch_repository(str(repo)) == PUBLIC_REPO


def test_resolve_dispatch_repository_fails_closed_without_origin(tmp_path):
    repo = _git_repo_with_origin(tmp_path / "clone", None)
    assert delegate._resolve_dispatch_repository(repo) is None


def test_resolve_dispatch_repository_fails_closed_for_missing_path(tmp_path):
    missing = tmp_path / "does-not-exist"
    assert delegate._resolve_dispatch_repository(missing) is None
    assert delegate._resolve_dispatch_repository(None) is None
    assert delegate._resolve_dispatch_repository("") is None


def test_resolve_dispatch_repository_binds_primary_for_reaped_worktree(tmp_path, monkeypatch):
    """An auto worktree under the primary binds the primary's origin by
    construction — even after the worktree itself has been reaped (#7083
    backfill must still reach those rows)."""
    primary = _git_repo_with_origin(tmp_path / "primary", f"git@github.com:{PUBLIC_REPO}.git")
    monkeypatch.setattr(delegate, "_REPO_ROOT", primary)
    reaped = primary / ".worktrees" / "dispatch" / "kimi" / "infra-7083-delegate-join"
    assert not reaped.exists()
    assert delegate._resolve_dispatch_repository(reaped) == PUBLIC_REPO
    assert delegate._resolve_dispatch_repository(primary) == PUBLIC_REPO


def test_resolve_dispatch_repository_does_not_bind_foreign_sibling(tmp_path, monkeypatch):
    primary = _git_repo_with_origin(tmp_path / "primary", f"https://github.com/{PUBLIC_REPO}.git")
    monkeypatch.setattr(delegate, "_REPO_ROOT", primary)
    sibling = _git_repo_with_origin(tmp_path / "sibling", f"https://github.com/{PRIVATE_REPO}.git")
    assert delegate._resolve_dispatch_repository(sibling) == PRIVATE_REPO


# ---------------------------------------------------------------------------
# dispatch-time stamping
# ---------------------------------------------------------------------------


def test_dispatch_dry_run_stamps_repository(tmp_tasks_dir, tmp_path, monkeypatch):
    """A dispatch binds its state to the target checkout's origin (#7083)."""
    for warn in (
        "_warn_node_modules_integrity",
        "_warn_venv_integrity",
        "_warn_worktree_cleanup_integrity",
        "_warn_if_monitor_api_unreachable",
    ):
        monkeypatch.setattr(delegate, warn, lambda: None)
    target = _git_repo_with_origin(tmp_path / "sibling", f"https://github.com/{PUBLIC_REPO}.git")
    args = delegate.build_parser().parse_args(
        [
            "dispatch",
            "--agent",
            "codex",
            "--task-id",
            "cf-pr-7072-dry-run",
            "--initiator",
            "codex",
            "--prompt",
            "review the PR",
            "--cwd",
            str(target),
            "--dry-run",
        ],
    )

    assert delegate.cmd_dispatch(args) == 0

    state = delegate._read_state(tmp_tasks_dir / "cf-pr-7072-dry-run.json")
    assert state is not None
    assert state["repository"] == PUBLIC_REPO


# ---------------------------------------------------------------------------
# backfill-repository
# ---------------------------------------------------------------------------


def _backfill_args(apply: bool) -> argparse.Namespace:
    return delegate.build_parser().parse_args(["backfill-repository", *(["--apply"] if apply else [])])


def test_backfill_repository_dry_run_writes_nothing(tmp_tasks_dir, tmp_path, capsys):
    clone = _git_repo_with_origin(tmp_path / "clone", f"https://github.com/{PUBLIC_REPO}.git")
    state_path = _write_state(tmp_tasks_dir, "cf-pr-7072-kimi", cwd=str(clone))

    assert delegate.cmd_backfill_repository(_backfill_args(apply=False)) == 0

    state = json.loads(state_path.read_text(encoding="utf-8"))
    assert "repository" not in state
    out = capsys.readouterr().out
    assert "dry-run" in out
    assert "stamped=1" in out
    assert "re-run with --apply" in out


def test_backfill_repository_apply_stamps_legacy_states(tmp_tasks_dir, tmp_path, capsys):
    clone = _git_repo_with_origin(tmp_path / "clone", f"https://github.com/{PUBLIC_REPO}.git")
    _write_state(tmp_tasks_dir, "cf-pr-7072-kimi", cwd=str(clone))
    _write_state(tmp_tasks_dir, "infra-7083-delegate-join", worktree_path=str(clone))

    assert delegate.cmd_backfill_repository(_backfill_args(apply=True)) == 0

    for task_id in ("cf-pr-7072-kimi", "infra-7083-delegate-join"):
        state = json.loads((tmp_tasks_dir / f"{task_id}.json").read_text(encoding="utf-8"))
        assert state["repository"] == PUBLIC_REPO
    assert "stamped=2" in capsys.readouterr().out


def test_backfill_repository_stamps_foreign_slug_truthfully(tmp_tasks_dir, tmp_path):
    """A sibling-repo task is stamped with its real foreign identity; the
    scoped public view keeps dropping it (fail closed, no false join)."""
    clone = _git_repo_with_origin(tmp_path / "clone", f"git@github.com:{PRIVATE_REPO}.git")
    _write_state(tmp_tasks_dir, "sibling-task", cwd=str(clone))

    assert delegate.cmd_backfill_repository(_backfill_args(apply=True)) == 0

    state = json.loads((tmp_tasks_dir / "sibling-task.json").read_text(encoding="utf-8"))
    assert state["repository"] == PRIVATE_REPO
    scoped = delegate_router.list_delegate_tasks(status="all", limit=500, repository=PUBLIC_REPO)
    assert scoped["total"] == 0


def test_backfill_repository_preserves_existing_claims(tmp_tasks_dir, tmp_path, capsys):
    clone = _git_repo_with_origin(tmp_path / "clone", f"https://github.com/{PUBLIC_REPO}.git")
    _write_state(tmp_tasks_dir, "claimed", cwd=str(clone), repository=PUBLIC_REPO)
    conflict_path = _write_state(
        tmp_tasks_dir,
        "conflicted",
        cwd=str(clone),
        repository=PUBLIC_REPO,
        repository_id=PRIVATE_REPO,
    )

    assert delegate.cmd_backfill_repository(_backfill_args(apply=True)) == 0

    conflicted = json.loads(conflict_path.read_text(encoding="utf-8"))
    assert conflicted["repository"] == PUBLIC_REPO
    assert conflicted["repository_id"] == PRIVATE_REPO
    out = capsys.readouterr().out
    assert "already_attributed=1" in out
    assert "conflicts=1" in out
    assert "stamped=0" in out


def test_backfill_repository_leaves_unprovable_targets_unclassified(tmp_tasks_dir, capsys):
    _write_state(tmp_tasks_dir, "no-target")
    _write_state(tmp_tasks_dir, "gone-target", cwd="/nonexistent/reaped/clone")

    assert delegate.cmd_backfill_repository(_backfill_args(apply=True)) == 0

    for task_id in ("no-target", "gone-target"):
        state = json.loads((tmp_tasks_dir / f"{task_id}.json").read_text(encoding="utf-8"))
        assert "repository" not in state
    assert "unresolved=2" in capsys.readouterr().out


# ---------------------------------------------------------------------------
# Work projection join (acceptance for #7083)
# ---------------------------------------------------------------------------

_PR_7072 = {
    "number": 7072,
    "title": "fix: example pull request",
    "state": "OPEN",
    "isDraft": False,
    "headRefName": "kimi/example",
    "headRefOid": "deadbeef",
    "createdAt": "2026-08-20T00:00:00Z",
    "updatedAt": "2026-08-22T00:00:00Z",
    "reviewDecision": None,
    "statusCheckRollup": [],
    "mergeStateStatus": "CLEAN",
    "labels": [],
    "assignees": [],
    "url": f"https://github.com/{PUBLIC_REPO}/pull/7072",
}


def _fake_gh_runner(args, _timeout):
    if "issue" in args:
        return 0, "[]", ""
    if "pr" in args:
        return 0, json.dumps([_PR_7072]), ""
    return 1, "", f"unexpected gh args: {args}"


def _collect_and_build():
    sections = collect_public_sections(
        gh_runner=_fake_gh_runner,
        streams_loader=lambda: {},
        fleet_reviews_loader=lambda _limit, _offset, _repo: {"reviews": [], "total": 0},
    )
    return sections, build_projection(sections)


def _pr_item(projection, number: int) -> dict:
    for item in projection["items"]:
        if item["resource_kind"] == "pr" and item["remote_id"] == str(number):
            return item
    raise AssertionError(f"PR {number} missing from projection")


def test_projection_delegate_tasks_count_matches_inventory(tmp_tasks_dir):
    """Acceptance: class4 delegate_tasks count matches /api/delegate/tasks and
    cf-pr-* tasks join onto their PR's dispatch projection."""
    _write_state(tmp_tasks_dir, "cf-pr-7072-kimi", repository=PUBLIC_REPO)
    _write_state(tmp_tasks_dir, "cf-pr-7072-grok", repository=PUBLIC_REPO)

    sections, projection = _collect_and_build()

    unscoped = delegate_router.list_delegate_tasks(status="all", limit=500)
    scoped = delegate_router.list_delegate_tasks(status="all", limit=500, repository=PUBLIC_REPO)
    assert sections["delegate_tasks"].status == "ok"
    assert sections["delegate_tasks"].count == unscoped["total"] == scoped["total"] == 2
    assert projection["denominator"]["class4"]["delegate_tasks"] is True

    dispatch = _pr_item(projection, 7072)["projections"]["dispatch"]
    assert sorted(dispatch["task_ids"]) == ["cf-pr-7072-grok", "cf-pr-7072-kimi"]
    assert dispatch["unresolved"] is False


def test_projection_joins_backfilled_history_and_still_fails_closed(tmp_tasks_dir, tmp_path):
    """End-to-end #7083 regression: legacy rows reproduce count=0, the
    backfill joins them into the projection, and foreign rows stay out."""
    clone = _git_repo_with_origin(tmp_path / "clone", f"https://github.com/{PUBLIC_REPO}.git")
    _write_state(tmp_tasks_dir, "cf-pr-7072-kimi", cwd=str(clone))  # legacy: no claim
    _write_state(tmp_tasks_dir, "cf-pr-7072-foreign", repository=PRIVATE_REPO)

    sections, projection = _collect_and_build()
    assert sections["delegate_tasks"].count == 0  # the reported symptom
    assert _pr_item(projection, 7072)["projections"]["dispatch"]["task_ids"] == []

    assert delegate.cmd_backfill_repository(_backfill_args(apply=True)) == 0

    sections, projection = _collect_and_build()
    scoped = delegate_router.list_delegate_tasks(status="all", limit=500, repository=PUBLIC_REPO)
    assert sections["delegate_tasks"].count == scoped["total"] == 1
    dispatch = _pr_item(projection, 7072)["projections"]["dispatch"]
    assert dispatch["task_ids"] == ["cf-pr-7072-kimi"]
    # The foreign task never joins the public projection, even after backfill.
    assert json.dumps(projection).count("cf-pr-7072-foreign") == 0
    assert PRIVATE_REPO not in json.dumps(projection)
