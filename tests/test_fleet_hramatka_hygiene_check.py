"""Hermetic tests for scripts.fleet.hramatka_hygiene_check.

No live `gh` or network calls: the GitHub reader is always injected. Git
worktree state is exercised against a throwaway repo under tmp_path, never
the real checkout.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import Any

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

from scripts.fleet import hramatka_hygiene_check as hygiene

PUBLIC = hygiene.PUBLIC_REPOSITORY
PRIVATE = hygiene.PRIVATE_REPOSITORY
EPIC = hygiene.PUBLIC_EPIC
BOARD = hygiene.PRIVATE_BOARD

CLEAN_BODY = (
    "Tracking epic for Hramatka.\n\n"
    f"Planning queue: private BOARD [{PRIVATE}#{BOARD}]"
    f"(https://github.com/{PRIVATE}/issues/{BOARD}).\n"
)


def _run(args: list[str], cwd: Path, check: bool = True) -> subprocess.CompletedProcess[str]:
    return subprocess.run(args, cwd=cwd, capture_output=True, text=True, check=check, timeout=30)


def _init_repo(repo_root: Path) -> None:
    repo_root.mkdir(parents=True)
    _run(["git", "init"], cwd=repo_root)
    _run(["git", "config", "user.email", "test@example.com"], cwd=repo_root)
    _run(["git", "config", "user.name", "Test User"], cwd=repo_root)
    (repo_root / "README.md").write_text("# test\n", encoding="utf-8")
    _run(["git", "add", "README.md"], cwd=repo_root)
    _run(["git", "commit", "-m", "initial"], cwd=repo_root)


def _add_dispatch_worktree(repo_root: Path, agent: str, task_id: str) -> Path:
    branch = f"{agent}/{task_id}"
    _run(["git", "branch", branch], cwd=repo_root)
    path = repo_root / ".worktrees" / "dispatch" / agent / task_id
    path.parent.mkdir(parents=True, exist_ok=True)
    _run(["git", "worktree", "add", str(path), branch], cwd=repo_root)
    return path


def _write_task_state(tasks_dir: Path, task_id: str, status: str, worktree_path: Path) -> None:
    tasks_dir.mkdir(parents=True, exist_ok=True)
    state = {"task_id": task_id, "status": status, "worktree_path": str(worktree_path)}
    safe = task_id.replace("/", "_")
    (tasks_dir / f"{safe}.json").write_text(json.dumps(state), encoding="utf-8")


def _reader(bodies: dict[tuple[str, int], dict[str, Any]]) -> hygiene.IssueReader:
    def _read(repo: str, number: int) -> dict[str, Any]:
        key = (repo, number)
        if key not in bodies:
            raise hygiene.GhUnavailable(f"no fixture for {repo}#{number}")
        return bodies[key]

    return _read


def _unavailable(_repo: str, _number: int) -> dict[str, Any]:
    raise hygiene.GhUnavailable("simulated outage")


@pytest.fixture
def hermetic_repo(tmp_path):
    repo_root = tmp_path / "repo"
    tasks_dir = tmp_path / "tasks"
    _init_repo(repo_root)
    return repo_root, tasks_dir


def _no_open_prs(_repo_root: Path, _branch: str | None) -> bool:
    """Default hermetic PR probe: nothing has an open PR."""
    return False


def _open_pr_for(*branches: str):
    """PR probe that reports an OPEN PR for exactly ``branches``."""
    wanted = set(branches)

    def _probe(_repo_root: Path, branch: str | None) -> bool:
        return branch in wanted

    return _probe


def _base_kwargs(repo_root: Path, tasks_dir: Path, **overrides: Any) -> dict[str, Any]:
    kwargs = {
        "repo_root": repo_root,
        "dispatch_worktrees_root": repo_root / ".worktrees" / "dispatch",
        "tasks_dir": tasks_dir,
        "disk_path": repo_root,
        "open_pr_probe": _no_open_prs,
    }
    kwargs.update(overrides)
    return kwargs


# --- policy / receipt shape -------------------------------------------------


def test_policy_version_is_a_stable_string() -> None:
    assert isinstance(hygiene.POLICY_VERSION, str)
    assert hygiene.POLICY_VERSION


def test_receipt_has_every_documented_key(hermetic_repo) -> None:
    repo_root, tasks_dir = hermetic_repo
    reader = _reader(
        {(PUBLIC, EPIC): {"number": EPIC, "body": CLEAN_BODY}, (PRIVATE, BOARD): {"number": BOARD, "body": ""}}
    )

    receipt = hygiene.hygiene_check(reader=reader, **_base_kwargs(repo_root, tasks_dir))

    for key in ("policy_version", "epic_charter_ok", "queue_pointer_ok", "zombie_worktrees", "df", "status"):
        assert key in receipt


# --- verified path -----------------------------------------------------------


def test_verified_when_epic_clean_pointer_present_no_zombies(hermetic_repo) -> None:
    repo_root, tasks_dir = hermetic_repo
    reader = _reader(
        {(PUBLIC, EPIC): {"number": EPIC, "body": CLEAN_BODY}, (PRIVATE, BOARD): {"number": BOARD, "body": ""}}
    )

    receipt = hygiene.hygiene_check(reader=reader, **_base_kwargs(repo_root, tasks_dir))

    assert receipt["status"] == "verified"
    assert receipt["epic_charter_ok"] is True
    assert receipt["queue_pointer_ok"] is True
    assert receipt["zombie_worktrees"] == []
    assert receipt["reasons"] == []


def test_cli_exit_zero_on_verified(hermetic_repo, capsys) -> None:
    repo_root, tasks_dir = hermetic_repo
    reader = _reader(
        {(PUBLIC, EPIC): {"number": EPIC, "body": CLEAN_BODY}, (PRIVATE, BOARD): {"number": BOARD, "body": ""}}
    )

    exit_code = hygiene.main(
        [
            "--repo-root",
            str(repo_root),
            "--dispatch-worktrees-root",
            str(repo_root / ".worktrees" / "dispatch"),
            "--tasks-dir",
            str(tasks_dir),
            "--disk-path",
            str(repo_root),
        ],
        reader=reader,
    )

    assert exit_code == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["status"] == "verified"


# --- stale: epic charter --------------------------------------------------


def test_stale_when_epic_has_live_unchecked_checkbox(hermetic_repo) -> None:
    repo_root, tasks_dir = hermetic_repo
    body = CLEAN_BODY + "\n- [ ] still open item\n- [x] done item\n"
    reader = _reader({(PUBLIC, EPIC): {"number": EPIC, "body": body}, (PRIVATE, BOARD): {"number": BOARD, "body": ""}})

    receipt = hygiene.hygiene_check(reader=reader, **_base_kwargs(repo_root, tasks_dir))

    assert receipt["status"] == "stale"
    assert receipt["epic_charter_ok"] is False
    assert any("live" in reason for reason in receipt["reasons"])


def test_all_checked_checkboxes_do_not_count_as_live(hermetic_repo) -> None:
    repo_root, tasks_dir = hermetic_repo
    body = CLEAN_BODY + "\n- [x] fully done item\n"
    reader = _reader({(PUBLIC, EPIC): {"number": EPIC, "body": body}, (PRIVATE, BOARD): {"number": BOARD, "body": ""}})

    receipt = hygiene.hygiene_check(reader=reader, **_base_kwargs(repo_root, tasks_dir))

    assert receipt["epic_charter_ok"] is True


# --- stale: missing pointer -------------------------------------------------


def test_stale_when_349_pointer_missing(hermetic_repo) -> None:
    repo_root, tasks_dir = hermetic_repo
    body = "Tracking epic for Hramatka. No pointer here."
    reader = _reader({(PUBLIC, EPIC): {"number": EPIC, "body": body}, (PRIVATE, BOARD): {"number": BOARD, "body": ""}})

    receipt = hygiene.hygiene_check(reader=reader, **_base_kwargs(repo_root, tasks_dir))

    assert receipt["status"] == "stale"
    assert receipt["queue_pointer_ok"] is False
    assert any("pointer" in reason for reason in receipt["reasons"])


def test_pointer_short_form_is_also_accepted(hermetic_repo) -> None:
    repo_root, tasks_dir = hermetic_repo
    body = f"Queue: {PRIVATE}#{BOARD} is the priority board."
    reader = _reader({(PUBLIC, EPIC): {"number": EPIC, "body": body}, (PRIVATE, BOARD): {"number": BOARD, "body": ""}})

    receipt = hygiene.hygiene_check(reader=reader, **_base_kwargs(repo_root, tasks_dir))

    assert receipt["queue_pointer_ok"] is True


# --- unknown: GitHub unreachable --------------------------------------------


def test_unknown_when_public_epic_api_unreachable(hermetic_repo) -> None:
    repo_root, tasks_dir = hermetic_repo

    receipt = hygiene.hygiene_check(reader=_unavailable, **_base_kwargs(repo_root, tasks_dir))

    assert receipt["status"] == "unknown"
    assert receipt["epic_charter_ok"] is None
    assert receipt["queue_pointer_ok"] is None


def test_unknown_when_private_board_api_unreachable_even_if_epic_looks_clean(hermetic_repo) -> None:
    repo_root, tasks_dir = hermetic_repo

    def reader(repo: str, number: int) -> dict[str, Any]:
        if (repo, number) == (PUBLIC, EPIC):
            return {"number": EPIC, "body": CLEAN_BODY}
        raise hygiene.GhUnavailable("private repo unreachable")

    receipt = hygiene.hygiene_check(reader=reader, **_base_kwargs(repo_root, tasks_dir))

    assert receipt["status"] == "unknown"
    # The public-side checks still ran and are reported, but never launder
    # into a "verified" result.
    assert receipt["epic_charter_ok"] is True
    assert receipt["queue_pointer_ok"] is True


def test_cli_exit_two_on_unknown(hermetic_repo, capsys) -> None:
    repo_root, tasks_dir = hermetic_repo

    exit_code = hygiene.main(
        ["--repo-root", str(repo_root), "--tasks-dir", str(tasks_dir)],
        reader=_unavailable,
    )

    assert exit_code == 2
    assert json.loads(capsys.readouterr().out)["status"] == "unknown"


# --- stale: zombie worktrees -------------------------------------------------


def _reader_clean() -> hygiene.IssueReader:
    return _reader(
        {(PUBLIC, EPIC): {"number": EPIC, "body": CLEAN_BODY}, (PRIVATE, BOARD): {"number": BOARD, "body": ""}}
    )


def test_stale_when_terminal_task_worktree_still_registered(hermetic_repo) -> None:
    repo_root, tasks_dir = hermetic_repo
    worktree = _add_dispatch_worktree(repo_root, "kimi", "finished-task")
    _write_task_state(tasks_dir, "finished-task", "done", worktree)

    receipt = hygiene.hygiene_check(reader=_reader_clean(), **_base_kwargs(repo_root, tasks_dir))

    assert receipt["status"] == "stale"
    assert len(receipt["zombie_worktrees"]) == 1
    assert receipt["zombie_worktrees"][0]["task_id"] == "finished-task"
    assert receipt["zombie_worktrees"][0]["status"] == "done"


def test_not_zombie_when_task_still_running(hermetic_repo) -> None:
    repo_root, tasks_dir = hermetic_repo
    worktree = _add_dispatch_worktree(repo_root, "kimi", "live-task")
    _write_task_state(tasks_dir, "live-task", "running", worktree)

    receipt = hygiene.hygiene_check(reader=_reader_clean(), **_base_kwargs(repo_root, tasks_dir))

    assert receipt["status"] == "verified"
    assert receipt["zombie_worktrees"] == []


def test_terminal_worktree_with_open_pr_is_not_a_zombie(hermetic_repo) -> None:
    """post_task_reap deliberately RETAINS a terminal-task worktree whose
    branch still has an open PR ("open PR present for bound worktree branch").
    Counting it here would demand a state the sanctioned reaper refuses to
    produce, holding the gate at `stale` for as long as any lane has a PR in
    flight."""
    repo_root, tasks_dir = hermetic_repo
    worktree = _add_dispatch_worktree(repo_root, "kimi", "pr-open-task")
    _write_task_state(tasks_dir, "pr-open-task", "done", worktree)

    receipt = hygiene.hygiene_check(
        reader=_reader_clean(),
        **_base_kwargs(repo_root, tasks_dir, open_pr_probe=_open_pr_for("kimi/pr-open-task")),
    )

    assert receipt["status"] == "verified"
    assert receipt["zombie_worktrees"] == []


def test_open_pr_exemption_is_per_branch_not_blanket(hermetic_repo) -> None:
    """Only the branch with the open PR is exempt; a sibling terminal
    worktree without one is still reported."""
    repo_root, tasks_dir = hermetic_repo
    kept = _add_dispatch_worktree(repo_root, "kimi", "pr-open-task")
    _write_task_state(tasks_dir, "pr-open-task", "done", kept)
    orphan = _add_dispatch_worktree(repo_root, "agy", "no-pr-task")
    _write_task_state(tasks_dir, "no-pr-task", "failed", orphan)

    receipt = hygiene.hygiene_check(
        reader=_reader_clean(),
        **_base_kwargs(repo_root, tasks_dir, open_pr_probe=_open_pr_for("kimi/pr-open-task")),
    )

    assert receipt["status"] == "stale"
    assert [z["task_id"] for z in receipt["zombie_worktrees"]] == ["no-pr-task"]


def test_unknown_pr_state_still_counts_the_worktree(hermetic_repo) -> None:
    """The exemption needs a PROVABLE open PR. A probe that cannot confirm one
    must not excuse a worktree — this gate never passes on a guess."""
    repo_root, tasks_dir = hermetic_repo
    worktree = _add_dispatch_worktree(repo_root, "kimi", "unknown-pr-task")
    _write_task_state(tasks_dir, "unknown-pr-task", "done", worktree)

    receipt = hygiene.hygiene_check(
        reader=_reader_clean(),
        **_base_kwargs(repo_root, tasks_dir, open_pr_probe=_no_open_prs),
    )

    assert receipt["status"] == "stale"
    assert [z["task_id"] for z in receipt["zombie_worktrees"]] == ["unknown-pr-task"]


def test_duplicate_branch_worktrees_are_never_exempted(hermetic_repo) -> None:
    """One open PR speaks for one checkout. A branch registered by two
    worktrees leaves both counted, even with an open PR on that branch."""
    repo_root, tasks_dir = hermetic_repo
    first = _add_dispatch_worktree(repo_root, "kimi", "dup-task")
    _write_task_state(tasks_dir, "dup-task", "done", first)

    second = repo_root / ".worktrees" / "dispatch" / "kimi" / "dup-task-copy"
    _run(["git", "worktree", "add", "--detach", str(second), "kimi/dup-task"], cwd=repo_root)
    _run(["git", "checkout", "kimi/dup-task", "--ignore-other-worktrees"], cwd=second, check=False)
    _write_task_state(tasks_dir, "dup-task-copy", "done", second)

    receipt = hygiene.hygiene_check(
        reader=_reader_clean(),
        **_base_kwargs(repo_root, tasks_dir, open_pr_probe=_open_pr_for("kimi/dup-task")),
    )

    assert receipt["status"] == "stale"
    assert "dup-task" in {z["task_id"] for z in receipt["zombie_worktrees"]}


# --- the real _branch_has_open_pr probe (no injected stand-in) -------------


def _gh_result(stdout: str, returncode: int = 0):
    return subprocess.CompletedProcess(args=[], returncode=returncode, stdout=stdout, stderr="")


def _probe_with(monkeypatch, result: Any) -> bool:
    def _fake_run(*_args: Any, **_kwargs: Any):
        if isinstance(result, BaseException):
            raise result
        return result

    monkeypatch.setattr(hygiene.subprocess, "run", _fake_run)
    return hygiene._branch_has_open_pr(Path("/nonexistent"), "kimi/some-task")


_OPEN_ROW = {
    "number": 7120,
    "state": "OPEN",
    "headRefName": "kimi/some-task",
    "isCrossRepository": False,
}


def test_probe_true_only_for_a_well_formed_open_same_repo_row(monkeypatch) -> None:
    assert _probe_with(monkeypatch, _gh_result(json.dumps([_OPEN_ROW]))) is True


@pytest.mark.parametrize(
    ("label", "payload"),
    [
        ("empty list", "[]"),
        ("null body", "null"),
        ("object not list", "{}"),
        ("null row", "[null]"),
        ("empty row", "[{}]"),
        ("row is a string", '["open"]'),
        ("malformed json", "not json"),
        ("empty stdout", ""),
    ],
)
def test_probe_fails_closed_on_untrusted_payloads(monkeypatch, label: str, payload: str) -> None:
    """`[{}]` and `[null]` are successful-but-untrusted shapes: a partially
    understood response is an unknown, and unknowns never exempt."""
    assert _probe_with(monkeypatch, _gh_result(payload)) is False, label


@pytest.mark.parametrize(
    ("label", "row"),
    [
        ("closed state", {**_OPEN_ROW, "state": "CLOSED"}),
        ("merged state", {**_OPEN_ROW, "state": "MERGED"}),
        ("state missing", {k: v for k, v in _OPEN_ROW.items() if k != "state"}),
        ("fork head", {**_OPEN_ROW, "isCrossRepository": True}),
        ("cross-repo unknown", {k: v for k, v in _OPEN_ROW.items() if k != "isCrossRepository"}),
        ("different branch", {**_OPEN_ROW, "headRefName": "kimi/other-task"}),
        ("head missing", {k: v for k, v in _OPEN_ROW.items() if k != "headRefName"}),
        ("number missing", {k: v for k, v in _OPEN_ROW.items() if k != "number"}),
        ("number not int", {**_OPEN_ROW, "number": "7120"}),
        ("number bool", {**_OPEN_ROW, "number": True}),
        ("number non-positive", {**_OPEN_ROW, "number": 0}),
    ],
)
def test_probe_rejects_rows_that_do_not_bind_to_this_branch(monkeypatch, label, row) -> None:
    """A same-named branch on a fork, or after a force-push/rename, must not
    excuse a stale local worktree."""
    assert _probe_with(monkeypatch, _gh_result(json.dumps([row]))) is False, label


def test_probe_one_bad_row_poisons_a_good_one(monkeypatch) -> None:
    payload = json.dumps([_OPEN_ROW, {}])
    assert _probe_with(monkeypatch, _gh_result(payload)) is False


def test_probe_fails_closed_on_nonzero_exit(monkeypatch) -> None:
    assert _probe_with(monkeypatch, _gh_result(json.dumps([_OPEN_ROW]), returncode=1)) is False


def test_probe_fails_closed_on_timeout(monkeypatch) -> None:
    assert _probe_with(monkeypatch, subprocess.TimeoutExpired(cmd="gh", timeout=1)) is False


def test_probe_fails_closed_on_subprocess_error(monkeypatch) -> None:
    assert _probe_with(monkeypatch, OSError("gh missing")) is False


def test_probe_returns_false_for_detached_worktree() -> None:
    """A detached worktree has no branch identity to probe."""
    assert hygiene._branch_has_open_pr(Path("/nonexistent"), None) is False


def test_probe_queries_an_explicit_repository(monkeypatch) -> None:
    """Without --repo the answer depends on cwd, so a worktree could be
    excused by a PR in a different repository."""
    seen: dict[str, Any] = {}

    def _fake_run(cmd: list[str], **_kwargs: Any):
        seen["cmd"] = cmd
        return _gh_result("[]")

    monkeypatch.setattr(hygiene.subprocess, "run", _fake_run)
    hygiene._branch_has_open_pr(Path("/nonexistent"), "kimi/some-task")

    cmd = seen["cmd"]
    assert "--repo" in cmd
    assert cmd[cmd.index("--repo") + 1] == hygiene.PUBLIC_REPOSITORY
    assert cmd[cmd.index("--head") + 1] == "kimi/some-task"


def test_registered_worktree_entries_handles_detached_and_flushes_last(hermetic_repo) -> None:
    """Detached entries carry no branch, and the final entry must still be
    emitted after the parse loop ends."""
    repo_root, _tasks_dir = hermetic_repo
    detached = repo_root / ".worktrees" / "dispatch" / "kimi" / "detached-task"
    detached.parent.mkdir(parents=True, exist_ok=True)
    _run(["git", "worktree", "add", "--detach", str(detached)], cwd=repo_root)

    entries = hygiene._registered_worktree_entries(repo_root)

    assert entries is not None
    by_name = {path.name: branch for path, branch in entries}
    assert by_name["detached-task"] is None
    assert len(entries) == len({path for path, _ in entries})


def test_registered_worktree_entries_reports_branches(hermetic_repo) -> None:
    repo_root, _tasks_dir = hermetic_repo
    _add_dispatch_worktree(repo_root, "kimi", "branch-task")

    entries = hygiene._registered_worktree_entries(repo_root)

    assert entries is not None
    by_name = {path.name: branch for path, branch in entries}
    assert by_name["branch-task"] == "kimi/branch-task"


def test_unbound_worktree_is_not_flagged_zombie(hermetic_repo) -> None:
    """A worktree with no matching task-state file is not detectable evidence
    either way — it must not be reported as a zombie."""
    repo_root, tasks_dir = hermetic_repo
    _add_dispatch_worktree(repo_root, "kimi", "unbound-task")
    # No task-state file written for "unbound-task".

    receipt = hygiene.hygiene_check(reader=_reader_clean(), **_base_kwargs(repo_root, tasks_dir))

    assert receipt["status"] == "verified"
    assert receipt["zombie_worktrees"] == []
    assert receipt["zombie_worktrees_detectable"] is True


def test_zombie_detection_not_detectable_when_git_worktree_list_fails(hermetic_repo, monkeypatch) -> None:
    repo_root, tasks_dir = hermetic_repo

    def fake_run(args, **kwargs):
        if args[:2] == ["git", "worktree"]:
            return subprocess.CompletedProcess(args, 1, stdout="", stderr="boom")
        return subprocess.run(args, timeout=30, **kwargs)

    monkeypatch.setattr(hygiene.subprocess, "run", fake_run)

    receipt = hygiene.hygiene_check(reader=_reader_clean(), **_base_kwargs(repo_root, tasks_dir))

    assert receipt["zombie_worktrees"] == []
    assert receipt["zombie_worktrees_detectable"] is False
    # Not detectable is a soft-fail, not a stale verdict on its own.
    assert receipt["status"] == "verified"


# --- disk ---------------------------------------------------------------


def test_stale_when_disk_use_at_or_above_high_water(hermetic_repo, monkeypatch) -> None:
    repo_root, tasks_dir = hermetic_repo
    monkeypatch.setattr(hygiene.shutil, "disk_usage", lambda _path: _fake_usage(100, 96, 4))

    receipt = hygiene.hygiene_check(reader=_reader_clean(), high_water_percent=95, **_base_kwargs(repo_root, tasks_dir))

    assert receipt["status"] == "stale"
    assert receipt["df"]["ok"] is False
    assert receipt["df"]["use_percent"] == 96.0


def test_disk_below_high_water_is_ok(hermetic_repo, monkeypatch) -> None:
    repo_root, tasks_dir = hermetic_repo
    monkeypatch.setattr(hygiene.shutil, "disk_usage", lambda _path: _fake_usage(100, 50, 50))

    receipt = hygiene.hygiene_check(reader=_reader_clean(), high_water_percent=95, **_base_kwargs(repo_root, tasks_dir))

    assert receipt["status"] == "verified"
    assert receipt["df"]["ok"] is True


def test_disk_measurement_failure_is_non_fatal(hermetic_repo, monkeypatch) -> None:
    repo_root, tasks_dir = hermetic_repo

    def _raise(_path):
        raise OSError("no such filesystem")

    monkeypatch.setattr(hygiene.shutil, "disk_usage", _raise)

    receipt = hygiene.hygiene_check(reader=_reader_clean(), **_base_kwargs(repo_root, tasks_dir))

    assert receipt["status"] == "verified"
    assert receipt["df"]["ok"] is None


def _fake_usage(total: int, used: int, free: int):
    import shutil as _shutil

    return _shutil._ntuple_diskusage(total, used, free)


# --- gh reader ---------------------------------------------------------------


def test_gh_reader_hides_stderr_and_treats_malformed_output_as_unavailable(monkeypatch) -> None:
    def nonzero(args, **_kwargs):
        return subprocess.CompletedProcess(args, 1, stdout="", stderr="private issue title: sensitive")

    monkeypatch.setattr(hygiene.subprocess, "run", nonzero)
    with pytest.raises(hygiene.GhUnavailable) as excinfo:
        hygiene._gh_issue(PRIVATE, BOARD)
    assert "sensitive" not in str(excinfo.value)

    def malformed(args, **_kwargs):
        return subprocess.CompletedProcess(args, 0, stdout="not json", stderr="")

    monkeypatch.setattr(hygiene.subprocess, "run", malformed)
    with pytest.raises(hygiene.GhUnavailable):
        hygiene._gh_issue(PRIVATE, BOARD)


def test_gh_reader_rejects_mismatched_issue_number(monkeypatch) -> None:
    def wrong_number(args, **_kwargs):
        return subprocess.CompletedProcess(args, 0, stdout=json.dumps({"number": 1, "body": "x"}), stderr="")

    monkeypatch.setattr(hygiene.subprocess, "run", wrong_number)
    with pytest.raises(hygiene.GhUnavailable):
        hygiene._gh_issue(PRIVATE, BOARD)
