"""Hermetic tests for scripts.fleet.pr_identity — the one shared open-PR probe.

No live `gh` or network calls: the gh subprocess boundary is always faked, and
git runs only against throwaway repos under tmp_path.  Includes the #7127
identity-agreement contract: for the SAME gh answer, the reaper
(``post_task_reap._no_open_pr_for_branch``) and the gate
(``hramatka_hygiene_check._branch_has_open_pr``) must derive from one binding
and differ only in their fail-closed direction.
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
from scripts.fleet import post_task_reap, pr_identity

BRANCH = "kimi/some-task"
REPO = "octo/fleet"

_OPEN_ROW = {
    "number": 7127,
    "state": "OPEN",
    "headRefName": BRANCH,
    "isCrossRepository": False,
}


def _gh_result(stdout: str, returncode: int = 0):
    return subprocess.CompletedProcess(args=[], returncode=returncode, stdout=stdout, stderr="")


# --- probe tri-state semantics ----------------------------------------------


def _probe_with(monkeypatch, result: Any):
    def _fake_run(*_args: Any, **_kwargs: Any):
        if isinstance(result, BaseException):
            raise result
        return result

    monkeypatch.setattr(pr_identity, "_run_gh", _fake_run)
    return pr_identity.probe_open_pr_for_branch(
        repo_root=Path("/nonexistent"),
        repo=REPO,
        branch=BRANCH,
    )


def test_probe_true_only_for_a_well_formed_open_same_repo_row(monkeypatch) -> None:
    assert _probe_with(monkeypatch, _gh_result(json.dumps([_OPEN_ROW]))) == (True, None)


def test_probe_false_for_a_provably_empty_answer(monkeypatch) -> None:
    assert _probe_with(monkeypatch, _gh_result("[]")) == (False, None)


def test_probe_empty_stdout_means_empty_list_not_unknown(monkeypatch) -> None:
    """Both prior implementations read empty stdout as []; keep that precedent."""
    assert _probe_with(monkeypatch, _gh_result("")) == (False, None)


@pytest.mark.parametrize(
    ("label", "payload"),
    [
        ("null body", "null"),
        ("object not list", "{}"),
        ("null row", "[null]"),
        ("empty row", "[{}]"),
        ("row is a string", '["open"]'),
        ("malformed json", "not json"),
    ],
)
def test_probe_reports_untrusted_payloads_as_unknown(monkeypatch, label: str, payload: str) -> None:
    """`[{}]` and `[null]` are successful-but-untrusted shapes: a partially
    understood response is an unknown, and unknowns never prove absence."""
    has_open, error = _probe_with(monkeypatch, _gh_result(payload))
    assert has_open is None, label
    assert error, label


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
        ("number not int", {**_OPEN_ROW, "number": "7127"}),
        ("number bool", {**_OPEN_ROW, "number": True}),
        ("number non-positive", {**_OPEN_ROW, "number": 0}),
    ],
)
def test_probe_reports_rows_that_do_not_bind_to_this_branch_as_unknown(
    monkeypatch, label: str, row
) -> None:
    """A same-named branch on a fork, or after a rename, must not read as
    proven-absent either: every unbound row makes the answer unknown."""
    has_open, error = _probe_with(monkeypatch, _gh_result(json.dumps([row])))
    assert has_open is None, label
    assert error, label


def test_probe_one_bad_row_poisons_a_good_one(monkeypatch) -> None:
    has_open, error = _probe_with(monkeypatch, _gh_result(json.dumps([_OPEN_ROW, {}])))
    assert has_open is None
    assert error


def test_probe_reports_nonzero_exit_as_unknown(monkeypatch) -> None:
    has_open, error = _probe_with(monkeypatch, _gh_result(json.dumps([_OPEN_ROW]), returncode=1))
    assert has_open is None
    assert error
    # OPSEC: the failure stays structural; gh stderr never lands in reports.
    assert "stderr" not in error


def test_probe_reports_timeout_as_unknown(monkeypatch) -> None:
    has_open, error = _probe_with(monkeypatch, subprocess.TimeoutExpired(cmd="gh", timeout=1))
    assert has_open is None
    assert error


def test_probe_reports_missing_gh_as_unknown(monkeypatch) -> None:
    has_open, error = _probe_with(monkeypatch, OSError("gh missing"))
    assert has_open is None
    assert error


def test_probe_refuses_to_run_without_branch_or_repo(monkeypatch) -> None:
    called: list[Any] = []

    def _fail_run(*_args: Any, **_kwargs: Any):
        called.append(1)
        raise AssertionError("gh must not run without an explicit identity")

    monkeypatch.setattr(pr_identity, "_run_gh", _fail_run)

    has_open, error = pr_identity.probe_open_pr_for_branch(
        repo_root=Path("/nonexistent"), repo=REPO, branch=None
    )
    assert has_open is None
    assert "branch" in error

    has_open, error = pr_identity.probe_open_pr_for_branch(
        repo_root=Path("/nonexistent"), repo=None, branch=BRANCH
    )
    assert has_open is None
    assert "repository" in error

    assert called == []


def test_probe_binds_the_query_to_the_explicit_identity(monkeypatch) -> None:
    seen: dict[str, Any] = {}

    def _fake_run(cmd: list[str], **_kwargs: Any):
        seen["cmd"] = cmd
        return _gh_result("[]")

    monkeypatch.setattr(pr_identity, "_run_gh", _fake_run)
    pr_identity.probe_open_pr_for_branch(
        repo_root=Path("/nonexistent"), repo=REPO, branch=BRANCH
    )

    cmd = seen["cmd"]
    assert cmd[:3] == ["gh", "pr", "list"]
    assert cmd[cmd.index("--repo") + 1] == REPO
    assert cmd[cmd.index("--head") + 1] == BRANCH
    assert cmd[cmd.index("--state") + 1] == "open"
    assert cmd[cmd.index("--json") + 1] == "number,state,headRefName,isCrossRepository"


# --- resolve_repo_slug --------------------------------------------------------


def _git(args: list[str], cwd: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(args, cwd=cwd, capture_output=True, text=True, check=True, timeout=30)


@pytest.mark.parametrize(
    ("url", "expected"),
    [
        ("https://github.com/octo/fleet.git", "octo/fleet"),
        ("https://github.com/octo/fleet", "octo/fleet"),
        ("git@github.com:octo/fleet.git", "octo/fleet"),
        ("ssh://git@github.com/octo/fleet.git", "octo/fleet"),
        ("/tmp/hermetic-origin.git", None),
        ("https://gitlab.com/octo/fleet.git", None),
    ],
)
def test_resolve_repo_slug_parses_github_remotes(tmp_path, url: str, expected: str | None) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    _git(["git", "init"], cwd=repo)
    _git(["git", "remote", "add", "origin", url], cwd=repo)

    assert pr_identity.resolve_repo_slug(repo) == expected


def test_resolve_repo_slug_fails_closed_without_a_checkout(tmp_path) -> None:
    assert pr_identity.resolve_repo_slug(tmp_path / "missing") is None


# --- identity agreement: one probe, two fail-closed directions (#7127) -------


def test_both_callers_consult_the_one_shared_probe_module() -> None:
    assert post_task_reap.pr_identity is hygiene.pr_identity is pr_identity


@pytest.mark.parametrize(
    ("probe_answer", "gate_expected", "reaper_no_open_expected", "reaper_error_expected"),
    [
        ((True, None), True, False, None),
        ((False, None), False, True, None),
        ((None, "gh pr list failed (exit 1)"), False, False, "PR guard unavailable"),
    ],
)
def test_directions_fail_closed_per_caller(
    monkeypatch, probe_answer, gate_expected: bool, reaper_no_open_expected: bool, reaper_error_expected
) -> None:
    """The probe's answer maps onto each caller's own fail-closed direction:
    only a PROVEN absence permits the reaper to proceed; the gate exempts a
    worktree only on a PROVEN open PR."""
    monkeypatch.setattr(pr_identity, "resolve_repo_slug", lambda _root: REPO)
    monkeypatch.setattr(pr_identity, "probe_open_pr_for_branch", lambda **_kwargs: probe_answer)

    assert hygiene._branch_has_open_pr(Path("/nonexistent"), BRANCH) is gate_expected

    no_open, error = post_task_reap._no_open_pr_for_branch(
        repo_root=Path("/nonexistent"), branch=BRANCH
    )
    assert no_open is reaper_no_open_expected
    if reaper_error_expected is None:
        assert error is None
    else:
        assert reaper_error_expected in error


def test_reaper_treats_unresolvable_repository_identity_as_unknown(monkeypatch) -> None:
    monkeypatch.setattr(pr_identity, "resolve_repo_slug", lambda _root: None)

    no_open, error = post_task_reap._no_open_pr_for_branch(
        repo_root=Path("/nonexistent"), branch=BRANCH
    )

    assert no_open is False
    assert "PR guard unavailable" in error
    assert "no explicit repository" in error


def _drive_both_over_one_gh_answer(monkeypatch, result: Any):
    """Run the REAL reaper and gate predicates over ONE shared gh answer."""
    def _fake_run(*_args: Any, **_kwargs: Any):
        if isinstance(result, BaseException):
            raise result
        return result

    monkeypatch.setattr(pr_identity, "_run_gh", _fake_run)
    monkeypatch.setattr(pr_identity, "resolve_repo_slug", lambda _root: REPO)

    gate_has_open = hygiene._branch_has_open_pr(Path("/nonexistent"), BRANCH)
    reaper_no_open, reaper_error = post_task_reap._no_open_pr_for_branch(
        repo_root=Path("/nonexistent"), branch=BRANCH
    )
    return gate_has_open, reaper_no_open, reaper_error


@pytest.mark.parametrize(
    ("label", "payload", "outcome"),
    [
        ("open row", json.dumps([_OPEN_ROW]), "proven_open"),
        ("empty list", "[]", "proven_absent"),
        ("empty row", "[{}]", "unknown"),
        ("null row", "[null]", "unknown"),
        ("non-list", "{}", "unknown"),
        ("malformed json", "not json", "unknown"),
    ],
)
def test_identity_agreement_on_one_gh_answer(monkeypatch, label: str, payload: str, outcome: str) -> None:
    """The #7127 contract: both predicates derive from one binding.  A proven
    open PR exempts (gate) and retains (reaper); a proven absence is the ONLY
    answer under which the reaper may proceed; everything else — including
    malformed `{}` rows — fails closed in BOTH directions at once."""
    gate_has_open, reaper_no_open, reaper_error = _drive_both_over_one_gh_answer(
        monkeypatch, _gh_result(payload)
    )

    if outcome == "proven_open":
        assert gate_has_open is True, label
        assert reaper_no_open is False, label
        assert reaper_error is None, label
    elif outcome == "proven_absent":
        assert gate_has_open is False, label
        assert reaper_no_open is True, label
        assert reaper_error is None, label
    else:
        assert gate_has_open is False, label
        assert reaper_no_open is False, label
        assert "PR guard unavailable" in (reaper_error or ""), label


def test_identity_agreement_on_transport_failures(monkeypatch) -> None:
    for failure in (
        _gh_result("[]", returncode=1),
        subprocess.TimeoutExpired(cmd="gh", timeout=1),
        OSError("gh missing"),
    ):
        gate_has_open, reaper_no_open, reaper_error = _drive_both_over_one_gh_answer(
            monkeypatch, failure
        )
        assert gate_has_open is False
        assert reaper_no_open is False
        assert "PR guard unavailable" in (reaper_error or "")


def test_each_caller_binds_its_own_explicit_repository(monkeypatch) -> None:
    """The gate pins the public repo; the reaper binds the checkout's own
    origin.  Both flow into the probe's --repo scope, never gh's cwd guess."""
    seen: list[dict[str, Any]] = []

    def _fake_probe(**kwargs: Any):
        seen.append(kwargs)
        return False, None

    monkeypatch.setattr(pr_identity, "probe_open_pr_for_branch", _fake_probe)
    monkeypatch.setattr(pr_identity, "resolve_repo_slug", lambda _root: REPO)

    hygiene._branch_has_open_pr(Path("/nonexistent"), BRANCH)
    post_task_reap._no_open_pr_for_branch(repo_root=Path("/nonexistent"), branch=BRANCH)

    assert [call["repo"] for call in seen] == [hygiene.PUBLIC_REPOSITORY, REPO]
    assert all(call["branch"] == BRANCH for call in seen)
