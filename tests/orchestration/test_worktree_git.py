"""Git, GitHub and activity-probe helpers kept from the retired worktree reaper.

The tests moved here with the helpers they cover in
:mod:`scripts.orchestration.worktree_git`: pull-request lookup and parsing,
branch pruning, the control-plane root, the active-task probe, worker
liveness, ownership claims and the switched-branch merge proof that
preservation still consumes. The hermetic repository fixtures at the end are
shared with the ignored-output and regenerable-output suites.
"""

from __future__ import annotations

import contextlib
import json
import os
import shutil
import sqlite3
import subprocess
import sys
from pathlib import Path
from typing import Any

import pytest

from scripts.fleet import ignored_task_output as output
from scripts.orchestration import reaper_lifecycle, worktree_claims
from scripts.orchestration import worktree_git as wg
from scripts.orchestration.task_record_store import task_record_path
from tests.worktree_prep_helpers import exited_process_identity

_REAL_RUN = subprocess.run
_REAL_ACTIVE_TASK_IDS = wg._active_task_ids
_REPO_TEMPLATE: Path | None = None


def git_env() -> dict[str, str]:
    return {
        key: value
        for key, value in os.environ.items()
        if not key.startswith("GIT_") and not key.startswith("PRE_COMMIT") and key != "AGENT_NO_MERGE"
    }


def git(cwd: Path, *args: str) -> str:
    proc = _REAL_RUN(
        ["git", *args],
        cwd=cwd,
        capture_output=True,
        text=True,
        check=False,
        env=git_env(),
    )
    assert proc.returncode == 0, proc.stderr or proc.stdout
    return (proc.stdout or "").strip()


def _build_repo(tmp_path: Path, name: str = "repo") -> Path:
    repo = tmp_path / name
    remote = tmp_path / ("origin.git" if name == "repo" else f"{name}-origin.git")
    git(tmp_path, "init", "--bare", str(remote))
    git(tmp_path, "init", "--initial-branch=main", str(repo))
    git(repo, "config", "user.email", "tester@example.com")
    git(repo, "config", "user.name", "Test User")
    (repo / ".gitignore").write_text(".worktrees/\nbatch_state/\n", encoding="utf-8")
    (repo / "README.md").write_text("base\n", encoding="utf-8")
    git(repo, "add", ".gitignore", "README.md")
    git(repo, "commit", "-m", "base")
    git(repo, "remote", "add", "origin", str(remote))
    git(repo, "push", "-u", "origin", "main")
    return repo


@pytest.fixture(scope="module", autouse=True)
def _repo_template(tmp_path_factory: pytest.TempPathFactory):
    """Bootstrap Git once per worker; test repos still have independent objects and refs."""
    global _REPO_TEMPLATE
    template_root = tmp_path_factory.mktemp("worktree-git-repo-template")
    _build_repo(template_root)
    _REPO_TEMPLATE = template_root
    yield
    _REPO_TEMPLATE = None


def init_repo(tmp_path: Path, name: str = "repo") -> Path:
    assert _REPO_TEMPLATE is not None
    repo = tmp_path / name
    remote = tmp_path / ("origin.git" if name == "repo" else f"{name}-origin.git")
    shutil.copytree(_REPO_TEMPLATE / "repo", repo)
    shutil.copytree(_REPO_TEMPLATE / "origin.git", remote)
    git(repo, "remote", "set-url", "origin", str(remote))
    return repo


def add_worktree(
    repo: Path,
    branch: str,
    *,
    path: Path | None = None,
    base: str = "main",
) -> Path:
    worktree = path or repo / ".worktrees" / branch.replace("/", "-")
    worktree.parent.mkdir(parents=True, exist_ok=True)
    git(repo, "worktree", "add", "-b", branch, str(worktree), base)
    return worktree


def patch_gh(
    monkeypatch: pytest.MonkeyPatch,
    states_by_branch: dict[str, list[dict[str, Any]]],
) -> list[str]:
    calls: list[str] = []

    def _resolve_head(cwd: Path, branch: str, item: dict[str, Any]) -> str | None:
        head = item.get("headRefOid")
        if head:
            return head
        proc = _REAL_RUN(
            ["git", "rev-parse", f"refs/heads/{branch}"],
            cwd=cwd,
            capture_output=True,
            text=True,
            check=False,
            env=git_env(),
        )
        return proc.stdout.strip() if proc.returncode == 0 else None

    def _ancestor(cwd: Path, sha: str, head: str) -> bool:
        if sha == head:
            return True
        proc = _REAL_RUN(
            ["git", "merge-base", "--is-ancestor", sha, head],
            cwd=cwd,
            capture_output=True,
            text=True,
            check=False,
            env=git_env(),
        )
        return proc.returncode == 0

    def fake_run(args: list[str], **kwargs: Any) -> subprocess.CompletedProcess[str]:
        if args and args[0] == "gh":
            if args[1:3] == ["search", "prs"]:
                sha = args[3]
                calls.append(f"search:{sha}")
                payload = []
                for branch, items in states_by_branch.items():
                    for item in items:
                        head = _resolve_head(kwargs["cwd"], branch, item)
                        if head is None or not _ancestor(kwargs["cwd"], sha, head):
                            continue
                        payload.append({"number": item.get("number"), "state": item.get("state")})
                return subprocess.CompletedProcess(args, 0, json.dumps(payload), "")
            branch = args[args.index("--head") + 1]
            calls.append(branch)
            payload = [dict(item) for item in states_by_branch.get(branch, [])]
            for item in payload:
                if item.get("headRefOid") or item.get("state") == "OPEN":
                    continue
                head = _REAL_RUN(
                    ["git", "rev-parse", f"refs/heads/{branch}"],
                    cwd=kwargs["cwd"],
                    capture_output=True,
                    text=True,
                    check=True,
                    env=git_env(),
                ).stdout.strip()
                item["headRefOid"] = head
            return subprocess.CompletedProcess(args, 0, json.dumps(payload), "")
        return _REAL_RUN(args, **kwargs)

    monkeypatch.setattr(wg, "_run_gh", fake_run)
    return calls


def _fleet_layout(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> tuple[Path, Path]:
    """Public primary plus its ``infra-private`` sibling checkout, laid out as layout A does (#8624)."""
    public = init_repo(tmp_path, "learn-ukrainian")
    sibling = init_repo(tmp_path, "learn-ukrainian-infra-private")
    monkeypatch.setattr(worktree_claims, "public_primary_root", lambda: public)
    return public, sibling


def _malformed_catalog(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Point the real loader at a syntactically invalid ``fleet_repos.yaml`` (no mock of the loader)."""
    from scripts.orchestration import fleet_repos

    bad = tmp_path / "malformed_fleet_repos.yaml"
    bad.write_text("repos: {infra-private: [unclosed\n", encoding="utf-8")
    monkeypatch.setattr(fleet_repos, "_CONFIG_PATH", bad)


def test_control_plane_root_falls_back_to_primary_on_malformed_catalog_yaml(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The read-only probes keep working on a malformed catalog instead of crashing."""
    _public, sibling = _fleet_layout(tmp_path, monkeypatch)
    _malformed_catalog(tmp_path, monkeypatch)

    assert wg.control_plane_root(sibling) == wg.primary_checkout_root(sibling)


# --- Active-task probe --


def _probe_fixture(repo, monkeypatch, failure, *, status="done", pid=None):
    """Use the actual HTTP probe with a bound local record and controlled failure."""
    import urllib.request

    task_id = "probe-fallback"
    branch = f"codex/{task_id}"
    worktree = add_worktree(repo, branch, path=repo / ".worktrees" / "dispatch" / "codex" / task_id)
    record = {"task_id": task_id, "worktree_path": str(worktree), "status": status, "pid": pid}
    task_file = repo / "batch_state" / "tasks" / f"{task_id}.json"
    task_file.parent.mkdir(parents=True, exist_ok=True)
    task_file.write_text(json.dumps(record))

    def fail(*_args, **_kwargs):
        raise failure

    monkeypatch.setattr(urllib.request, "urlopen", fail)
    monkeypatch.setattr(wg, "_active_task_ids", _REAL_ACTIVE_TASK_IDS)
    monkeypatch.setattr(wg, "_live_cwd_paths", lambda _repo: set())
    patch_gh(monkeypatch, {branch: []})
    return worktree, task_file, record


@pytest.mark.parametrize("payload", [{}, {"tasks": None}, {"tasks": [None]}, {"tasks": [{}]}, []])
def test_active_probe_rejects_malformed_http_payload(monkeypatch, payload):
    import urllib.request

    response = contextlib.nullcontext(type("Response", (), {"read": lambda _: json.dumps(payload).encode()})())
    monkeypatch.setattr(urllib.request, "urlopen", lambda *_args, **_kwargs: response)
    monkeypatch.setattr(wg, "_active_task_ids", _REAL_ACTIVE_TASK_IDS)
    probe = wg._read_active_task_probe()
    assert isinstance(probe, wg._ActiveTaskProbeFailure)
    assert "ValueError" in probe.reason
    assert not probe.fallback_allowed


def test_active_probe_reads_working_monitor(monkeypatch):
    import urllib.request

    response = contextlib.nullcontext(type("Response", (), {"read": lambda _: b'{"tasks": [{"task_id": "live"}]}'})())
    monkeypatch.setattr(urllib.request, "urlopen", lambda *_args, **_kwargs: response)
    assert _REAL_ACTIVE_TASK_IDS() == {"live"}


@pytest.mark.parametrize("layout", ["dispatch", "legacy"])
def test_active_probe_missing_record_leaves_activity_unknown(tmp_path, monkeypatch, layout):
    repo = init_repo(tmp_path)
    worktree, task_file, _ = _probe_fixture(repo, monkeypatch, TimeoutError("deadline"))
    task_file.unlink()
    if layout == "legacy":
        worktree = add_worktree(repo, "codex/legacy", path=repo / ".worktrees" / "legacy")
    info = next(info for info in wg.list_git_worktrees(repo) if info.path == worktree)

    active_ids, error = wg._resolve_activity_probe(repo, info, wg._read_active_task_probe())

    assert active_ids is None
    assert error is None
    rows = [json.loads(line) for line in reaper_lifecycle.journal_path(repo).read_text().splitlines()]
    assert rows[-1]["event"] == "activity-probe-unattributed"
    assert rows[-1]["source"] == "no_local_task_record"
    assert "active_task_probe_timeout" in rows[-1]["reason"]


# --- Branch pruning --


def test_prune_branch_refuses_branch_checked_out_in_another_worktree(
    tmp_path: Path,
) -> None:
    repo = init_repo(tmp_path)
    branch = "codex/checked-out-during-prune"
    worktree = add_worktree(repo, branch)
    expected_head = git(repo, "rev-parse", branch)

    error = wg._prune_branch(
        repo,
        branch,
        force=True,
        expected_head=expected_head,
    )

    assert error is not None
    assert git(repo, "rev-parse", branch) == expected_head
    assert git(worktree, "branch", "--show-current") == branch


# --- Pull-request lookup --


def _gh_stdout(payload: str, returncode: int = 0):
    return subprocess.CompletedProcess(args=[], returncode=returncode, stdout=payload, stderr="")


@pytest.mark.parametrize(
    ("label", "payload"),
    [
        ("null row", "[null]"),
        ("empty row", "[{}]"),
        ("row without state", '[{"number": 1}]'),
        ("row is a string", '["OPEN"]'),
        ("blank state", '[{"state": "", "number": 1}]'),
        ("scalar payload", "123"),
        ("mapping payload", "{}"),
        ("string payload", '"open"'),
        ("null payload", "null"),
    ],
)
def test_query_pr_states_reports_unreadable_rows_as_an_error(monkeypatch, label, payload) -> None:
    """A row the parser cannot read is an UNKNOWN, never an absence.

    Silently skipping made `[null]` / `[{}]` parse as "no open PR", and every
    caller reads an empty list as permission to DELETE the worktree. That was
    a destructive fail-open on malformed input.
    """
    monkeypatch.setattr(wg, "_github_owner_repo", lambda _root: None)
    monkeypatch.setattr(wg, "_run_gh", lambda *_a, **_k: _gh_stdout(payload))

    states, error = wg._query_pr_states(Path("/nonexistent"), "some/branch")

    assert states == [], label
    assert error is not None, label


def test_query_pr_states_still_reports_a_genuinely_empty_list(monkeypatch) -> None:
    """An empty list is a real answer (no PR), not an unknown -- cleanup must
    still be possible or nothing would ever be cleaned up."""
    monkeypatch.setattr(wg, "_github_owner_repo", lambda _root: None)
    monkeypatch.setattr(wg, "_run_gh", lambda *_a, **_k: _gh_stdout("[]"))

    states, error = wg._query_pr_states(Path("/nonexistent"), "some/branch")

    assert states == []
    assert error is None


def test_query_pr_states_parses_a_well_formed_row(monkeypatch) -> None:
    payload = json.dumps([{"number": 7120, "state": "OPEN", "headRefOid": "abc123"}])
    monkeypatch.setattr(wg, "_github_owner_repo", lambda _root: None)
    monkeypatch.setattr(wg, "_run_gh", lambda *_a, **_k: _gh_stdout(payload))

    states, error = wg._query_pr_states(Path("/nonexistent"), "some/branch")

    assert error is None
    assert [(s.number, s.state, s.head_sha) for s in states] == [(7120, "OPEN", "abc123")]


@pytest.mark.parametrize(
    ("label", "payload"),
    [
        ("state present but no number", '[{"state": "CLOSED"}]'),
        ("unrecognised state enum", '[{"state": "NOT_A_GH_PR_STATE", "number": 7126}]'),
        ("state is not a string", '[{"state": [], "number": 7126}]'),
        ("number is a bool", '[{"state": "CLOSED", "number": true}]'),
        ("number is zero", '[{"state": "CLOSED", "number": 0}]'),
        ("number is a string", '[{"state": "CLOSED", "number": "7126"}]'),
    ],
)
def test_query_pr_states_rejects_incomplete_rows(monkeypatch, label, payload) -> None:
    """An incomplete or unrecognised row is ambiguous, and ambiguity must not
    read as "no open PR" -- callers treat that as permission to DELETE."""
    monkeypatch.setattr(wg, "_github_owner_repo", lambda _root: None)
    monkeypatch.setattr(wg, "_run_gh", lambda *_a, **_k: _gh_stdout(payload))

    states, error = wg._query_pr_states(Path("/nonexistent"), "some/branch")

    assert states == [], label
    assert error is not None, label


@pytest.mark.parametrize("state", ["OPEN", "MERGED", "CLOSED"])
def test_query_pr_states_accepts_every_real_gh_state(monkeypatch, state) -> None:
    """The tightened validation must not reject legitimate answers, or
    nothing would ever be cleaned up."""
    payload = json.dumps([{"number": 7126, "state": state, "headRefOid": "abc"}])
    monkeypatch.setattr(wg, "_github_owner_repo", lambda _root: None)
    monkeypatch.setattr(wg, "_run_gh", lambda *_a, **_k: _gh_stdout(payload))

    states, error = wg._query_pr_states(Path("/nonexistent"), "some/branch")

    assert error is None
    assert [(s.number, s.state) for s in states] == [(7126, state)]


def test_gh_json_calls_drop_force_color(monkeypatch, tmp_path: Path) -> None:
    """FORCE_COLOR / CLICOLOR_FORCE must not reach a gh call that parses JSON."""
    monkeypatch.setenv("FORCE_COLOR", "1")
    monkeypatch.setenv("CLICOLOR_FORCE", "1")
    monkeypatch.setenv("NO_COLOR", "already")
    captured: list[dict[str, str]] = []

    def fake_run(args, **kwargs):
        captured.append(kwargs["env"])
        if args[0] == "gh":
            colored = kwargs["env"].get("FORCE_COLOR") or kwargs["env"].get("CLICOLOR_FORCE") not in {None, "0"}
            uncolored = not colored and kwargs["env"].get("NO_COLOR") == "1"
            stdout = "[]" if uncolored else "\x1b[32m[]\x1b[0m"
            return subprocess.CompletedProcess(args, 0, stdout, "")
        return subprocess.CompletedProcess(args, 0, "", "")

    monkeypatch.setattr(wg.subprocess, "run", fake_run)
    monkeypatch.setattr(wg, "safe_git", fake_run)

    git_proc = wg._run(["git", "status"], cwd=tmp_path)
    direct = wg._run(["gh", "pr", "list"], cwd=tmp_path)

    assert git_proc.returncode == 0
    assert direct.returncode == 0
    assert captured[0]["FORCE_COLOR"] == "1"
    assert captured[0]["CLICOLOR_FORCE"] == "1"
    assert "FORCE_COLOR" not in captured[1]
    assert captured[1]["NO_COLOR"] == "1"
    assert captured[1]["CLICOLOR_FORCE"] == "0"

    transport_env: list[dict[str, str]] = []

    def fake_transport(command, **kwargs):
        transport_env.append(kwargs["env"])
        return subprocess.CompletedProcess(command, 0, b"[]", b"")

    monkeypatch.setattr(wg.github_client, "_transport_process", fake_transport)
    states, error = wg._query_pr_states_graphql(tmp_path, "grok/impl-9889")

    assert transport_env
    assert "FORCE_COLOR" not in transport_env[0]
    assert "CLICOLOR_FORCE" not in transport_env[0]
    assert transport_env[0]["NO_COLOR"] == "1"
    assert error is None
    assert states == []


@pytest.mark.parametrize(
    ("stdout", "unknown"),
    [("", True), ("[]", False)],
    ids=["empty-stdout", "empty-list"],
)
def test_graphql_pr_list_empty_stdout_is_unknown(monkeypatch, tmp_path: Path, stdout: str, unknown: bool) -> None:
    """A blank ``gh pr list`` body is not ``[]``. Only a JSON list is "no PR"."""
    monkeypatch.setattr(wg, "_run_gh", lambda *_args, **_kwargs: _gh_stdout(stdout))

    states, error = wg._query_pr_states_graphql(tmp_path, "grok/impl-9889")

    assert states == []
    assert (error is not None) is unknown
    if unknown:
        assert error is not None and "empty" in error


def test_colored_gh_json_stays_fail_closed(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setenv("FORCE_COLOR", "1")
    monkeypatch.setenv("CLICOLOR_FORCE", "1")
    monkeypatch.setattr(
        wg,
        "_run_gh",
        lambda *_args, **_kwargs: subprocess.CompletedProcess([], 0, "\x1b[32m[]\x1b[0m", ""),
    )

    states, error = wg._query_pr_states_graphql(tmp_path, "grok/impl-9889")

    assert states == []
    assert error is not None and "invalid JSON" in error


def _patch_gh_transports(
    monkeypatch,
    *,
    rest: subprocess.CompletedProcess[str],
    graphql: subprocess.CompletedProcess[str],
) -> list[list[str]]:
    """Route gh traffic: REST (`gh api`) and GraphQL (`gh pr list/view`) get
    independent canned answers; the origin remote parses to a GitHub slug."""
    gh_calls: list[list[str]] = []

    monkeypatch.setattr(
        wg,
        "_configured_origin_url",
        lambda _root: b"git@github.com:learn-ukrainian/learn-ukrainian.github.io.git\n",
    )

    def fake_run(args: list[str], **kwargs: Any) -> subprocess.CompletedProcess[str]:
        if args[:2] == ["gh", "api"]:
            gh_calls.append(args)
            return subprocess.CompletedProcess(args, rest.returncode, rest.stdout, rest.stderr)
        if args[:2] == ["gh", "pr"]:
            gh_calls.append(args)
            return subprocess.CompletedProcess(args, graphql.returncode, graphql.stdout, graphql.stderr)
        return _REAL_RUN(args, **kwargs)

    monkeypatch.setattr(wg, "_run", fake_run)
    monkeypatch.setattr(wg, "_run_gh", fake_run)
    return gh_calls


@pytest.mark.parametrize(
    ("stdout", "unknown"),
    [
        ("", True),
        ("[]", False),
        ("[[]]", False),
        ("[[null]]", True),
        ("[[{}]]", True),
        ('[[null], [{"number": 1, "state": "open", "merged_at": None, "head": {"sha": "abc"}}]]', True),
    ],
    ids=["empty-stdout", "no-pages", "empty-page", "null-row", "empty-object", "null-then-object"],
)
def test_rest_pr_lookup_empty_stdout_and_unusable_rows_are_unknown(
    monkeypatch, tmp_path: Path, stdout: str, unknown: bool
) -> None:
    """Blank REST output, ``null`` and a non-object are unknown, not "no PR"."""
    monkeypatch.setattr(wg, "_github_owner_repo", lambda _root: ("owner", "repo"))
    monkeypatch.setattr(wg, "_run_gh", lambda *_args, **_kwargs: _gh_stdout(stdout))

    states, error = wg._query_pr_states_rest(tmp_path, "codex/task")

    assert (error is not None) is unknown
    if unknown:
        assert states == []
        assert error is not None
    else:
        assert error is None
        assert states == []


def test_query_pr_states_rest_answer_is_used_when_graphql_is_down(monkeypatch) -> None:
    calls = _patch_gh_transports(
        monkeypatch,
        rest=_gh_stdout(
            json.dumps(
                [
                    [
                        {
                            "number": 8536,
                            "state": "closed",
                            "merged_at": "2026-09-22T10:00:00Z",
                            "head": {"sha": "rest-sha"},
                        }
                    ]
                ]
            )
        ),
        graphql=_gh_stdout("GraphQL: API rate limit exceeded", returncode=1),
    )

    states, error = wg._query_pr_states(Path("/nonexistent"), "codex/task")

    assert error is None
    assert [(s.number, s.state, s.head_sha) for s in states] == [(8536, "MERGED", "rest-sha")]
    assert all(call[1] == "api" for call in calls)


def test_query_pr_states_rest_pages_preserve_later_closed_head(monkeypatch) -> None:
    first = [
        {"number": number, "state": "closed", "merged_at": None, "head": {"sha": f"sha-{number}"}}
        for number in range(1, 101)
    ]
    later = [{"number": 101, "state": "closed", "merged_at": None, "head": {"sha": "held-head"}}]
    calls = _patch_gh_transports(
        monkeypatch,
        rest=_gh_stdout(json.dumps([first, later])),
        graphql=_gh_stdout("down", returncode=1),
    )

    states, error = wg._query_pr_states(Path("/nonexistent"), "codex/task")

    assert error is None
    assert len(states) == 101
    assert states[-1].state == "CLOSED" and states[-1].head_sha == "held-head"
    assert "--paginate" in calls[0] and "--slurp" in calls[0]


def test_query_pr_states_falls_back_to_graphql_when_rest_fails(monkeypatch) -> None:
    calls = _patch_gh_transports(
        monkeypatch,
        rest=_gh_stdout("Not Found", returncode=1),
        graphql=_gh_stdout(json.dumps([{"number": 8536, "state": "OPEN", "headRefOid": "gql-sha"}])),
    )

    states, error = wg._query_pr_states(Path("/nonexistent"), "codex/task")

    assert error is None
    assert [(s.number, s.state, s.head_sha) for s in states] == [(8536, "OPEN", "gql-sha")]
    assert [call[1] for call in calls] == ["api", "pr"]


def test_query_pr_states_fails_closed_when_both_transports_fail(monkeypatch) -> None:
    _patch_gh_transports(
        monkeypatch,
        rest=_gh_stdout("rest down", returncode=1),
        graphql=_gh_stdout("graphql down", returncode=1),
    )

    states, error = wg._query_pr_states(Path("/nonexistent"), "codex/task")

    assert states == []
    assert error is not None
    assert "REST PR lookup failed" in error
    assert "gh pr list failed" in error


def test_parse_rest_pr_item_maps_merged_at_to_merged() -> None:
    parsed, err = wg._parse_rest_pr_item(
        {"number": 7, "state": "closed", "merged_at": "2026-09-22T00:00:00Z", "head": {"sha": "x"}}
    )
    assert err is None
    assert (parsed.number, parsed.state, parsed.head_sha) == (7, "MERGED", "x")

    parsed, err = wg._parse_rest_pr_item({"number": 7, "state": "closed", "merged_at": None, "head": {}})
    assert err is None
    assert (parsed.number, parsed.state, parsed.head_sha) == (7, "CLOSED", None)

    parsed, err = wg._parse_rest_pr_item({"number": 7, "state": "bogus", "merged_at": None})
    assert parsed is None
    assert err is not None


# --- Worker liveness and ownership claims --


@pytest.mark.parametrize("claim_state", ["live", "dead", "unknown"])
def test_write_claim_pid_replacement_ignores_stale_task_identity(tmp_path, monkeypatch, claim_state):
    from scripts.orchestration import dead_worker_state

    repo = init_repo(tmp_path)
    task_id = "replacement-claim"
    dead_pid, dead_start = exited_process_identity()
    claim_pid = dead_pid if claim_state == "dead" else os.getpid()
    stale_pid = os.getpid() if claim_state == "dead" else dead_pid
    task_dir = repo / "batch_state" / "tasks"
    task_dir.mkdir(parents=True, exist_ok=True)
    task_file = task_dir / f"{task_id}.json"
    task_file.write_text(
        json.dumps(
            {
                "pid": stale_pid,
                "worker_identity": {
                    **dead_worker_state.capture_worker_identity(stale_pid),
                    "start_time": dead_start if stale_pid == dead_pid else -1,
                },
            }
        )
    )
    db_path = task_dir / "write-ownership.sqlite3"
    with sqlite3.connect(db_path) as conn:
        conn.execute("CREATE TABLE write_claims (task_id TEXT, pid INTEGER)")
        conn.execute("INSERT INTO write_claims VALUES (?, ?)", (task_id, claim_pid))
    before_task = task_file.read_bytes()
    before_ledger = db_path.read_bytes()
    monkeypatch.setenv("LEARN_UKRAINIAN_OWNERSHIP_LEDGER", str(db_path))
    if claim_state == "unknown":
        monkeypatch.setattr(dead_worker_state, "_pid_namespace", lambda *_args: "pid:[999999]")
        monkeypatch.setattr(dead_worker_state, "_proc_pid_namespace", lambda: "pid:[999999]")

    reason = wg._has_active_ownership_claim(repo, task_id)

    assert reason == (None if claim_state == "dead" else "active write claim task-id=replacement-claim")
    assert task_file.read_bytes() == before_task
    assert db_path.read_bytes() == before_ledger


def test_namespace_unknown_worker_is_not_gone():
    record = {
        "pid": 999_999_998,
        "status": "crashed",
        "worker_identity": {
            "pid": 999_999_998,
            "host_pid": 999_999_998,
            "start_time": 123,
            "pid_namespace": "pid:[999999]",
            "recorder_pid_namespace": "pid:[999999]",
        },
    }
    assert wg._task_pid_alive(record) is True
    assert wg._pid_proven_absent(record) is False


# --- Switched-branch merge proof and origin identity --


def save(tasks, record):
    path = tasks / f"{record['task_id']}.json"
    path.write_text(json.dumps(record))
    return path


def _real_switched_checkout(tmp_path, monkeypatch):
    """Switched cohort on a real linked worktree. The origin parser is not mocked."""
    from tests.orchestration.test_merge_closeout import git, init_repo

    repo = init_repo(tmp_path)
    tree = repo / ".worktrees/dispatch/cursor/switched-proof"
    tree.parent.mkdir(parents=True)
    git(repo, "worktree", "add", "-b", "cursor/old-gate", str(tree), "main")
    tasks = repo / "batch_state/tasks"
    tasks.mkdir(parents=True)
    monkeypatch.setenv("LU_TASKS_DIR", str(tasks))
    monkeypatch.setattr(wg, "_live_cwd_paths", lambda _repo: set())
    monkeypatch.setattr(wg, "_active_task_ids", lambda: set())
    creator_head = git(tree, "rev-parse", "HEAD")
    git(tree, "commit", "--allow-empty", "-m", "later round")
    middle = git(tree, "rev-parse", "HEAD")
    git(tree, "checkout", "-b", "cursor/fresh-gate")
    git(tree, "commit", "--allow-empty", "-m", "switched")
    merged_head = git(tree, "rev-parse", "HEAD")
    git(tree, "push", "-u", "origin", "cursor/fresh-gate")
    git(repo, "merge", "--no-ff", "cursor/fresh-gate", "-m", "merge switched PR")
    git(repo, "push", "origin", "main")
    creator = {
        "task_id": "cursor-creator",
        "agent": "cursor",
        "run_nonce": "creation-nonce",
        "status": "needs_finalize",
        "worktree_reused": False,
        "worktree_path": str(tree),
        "worktree_branch": "cursor/old-gate",
        "final_branch_head_commit": creator_head,
        "keep_worktree": False,
        "pid": 999_999_981,
    }
    creator["ignored_output_baseline"] = output.creation_inventory(
        tree, primary=repo, task_id=creator["task_id"], run_nonce=creator["run_nonce"]
    )
    successors = [
        {
            "task_id": "cursor-round-1",
            "agent": "cursor",
            "run_nonce": "round-1",
            "status": "needs_finalize",
            "worktree_reused": True,
            "worktree_path": str(tree),
            "worktree_branch": "cursor/old-gate",
            "final_branch_head_commit": middle,
            "keep_worktree": False,
            "pid": 999_999_982,
        },
        {
            "task_id": "cursor-round-2",
            "agent": "cursor",
            "run_nonce": "round-2",
            "status": "done",
            "worktree_reused": True,
            "worktree_path": str(tree),
            "worktree_branch": "cursor/old-gate",
            "final_branch_head_commit": merged_head,
            "keep_worktree": False,
            "pid": 999_999_983,
        },
    ]
    for record in (creator, *successors):
        save(tasks, record)
    cohort = [(tasks / f"{record['task_id']}.json", record) for record in (creator, *successors)]
    return repo, tree, tasks, cohort, merged_head


def _merged_gh(monkeypatch, *, head: str, branch: str) -> list[list[str]]:
    """Answer every gh read as the merged head. Does not replace the origin parser."""
    calls: list[list[str]] = []
    page = {
        "number": 10548,
        "state": "closed",
        "merged_at": "2026-01-02T03:04:05Z",
        "head": {"ref": branch, "sha": head},
    }
    listed = [{"number": 10548, "state": "MERGED", "headRefOid": head}]

    def fake_run_gh(args, **_kwargs):
        calls.append(list(args))
        if "--paginate" in args:
            return subprocess.CompletedProcess(args, 0, json.dumps([[page]]), "")
        if args[1:3] == ["api", "-X"]:
            return subprocess.CompletedProcess(args, 0, json.dumps(page), "")
        if args[1:3] == ["pr", "list"]:
            return subprocess.CompletedProcess(args, 0, json.dumps(listed), "")
        if args[1:3] == ["pr", "view"]:
            payload = {"number": 10548, "state": "MERGED", "headRefName": branch, "headRefOid": head}
            return subprocess.CompletedProcess(args, 0, json.dumps(payload), "")
        if args[1:3] == ["search", "prs"]:
            return subprocess.CompletedProcess(args, 0, "[]", "")
        return subprocess.CompletedProcess(args, 1, "", "unexpected gh invocation")

    monkeypatch.setattr(wg, "_run_gh", fake_run_gh)
    return calls


@pytest.mark.parametrize(
    "origin",
    [
        "https://notgithub.com/unrelated/repo.git",
        "https://notgithub.com/unrelated/repo",
        "git@notgithub.com:unrelated/repo.git",
        "git@notgithub.com:unrelated/repo",
        "ssh://git@notgithub.com/unrelated/repo.git",
        "ssh://git@notgithub.com/unrelated/repo",
        "https://prefix.github.com/unrelated/repo.git",
        "https://github.com/bad owner/repo.git",
        "https://github.com/-bad/repo.git",
        "https://github.com/unrelated/repo?.git",
    ],
)
def test_real_origin_parser_refuses_non_github_host_and_illegal_slug(tmp_path, origin):
    """The configured origin is read from git. A lookalike host or a bad slug is not a repository."""
    from tests.orchestration.test_merge_closeout import git, init_repo

    repo = init_repo(tmp_path)
    git(repo, "remote", "set-url", "origin", origin)
    assert wg._github_owner_repo(repo) is None


def test_lookalike_github_host_does_not_prove_switched_checkout(tmp_path, monkeypatch):
    """A host that only contains the GitHub name must not query that embedded owner/repo."""
    from tests.orchestration.test_merge_closeout import git

    repo, tree, _tasks, cohort, merged_head = _real_switched_checkout(tmp_path, monkeypatch)
    git(repo, "remote", "set-url", "origin", "https://notgithub.com/unrelated/repo.git")
    calls = _merged_gh(monkeypatch, head=merged_head, branch="cursor/fresh-gate")
    assert wg._switched_branch_merge_proven(repo, tree, cohort) is False
    assert not any("unrelated/repo" in " ".join(call) for call in calls)
    assert tree.exists()


def _assert_unproven_path_cannot_authorize_removal(repo, tree, cohort, doubtful):
    """An unproven path must not resolve a repository or prove the switched merge."""
    assert wg._checkout_pr_repository(doubtful) is None
    assert wg._switched_branch_merge_proven(repo, doubtful, cohort) is False
    assert tree.exists() and doubtful.exists()


def test_symlinked_checkout_cannot_authorize_switched_removal(tmp_path, monkeypatch):
    from tests.orchestration.test_merge_closeout import git

    repo, tree, _tasks, cohort, merged_head = _real_switched_checkout(tmp_path, monkeypatch)
    git(repo, "remote", "set-url", "origin", "https://github.com/acme/widget.git")
    _merged_gh(monkeypatch, head=merged_head, branch="cursor/fresh-gate")
    link = tmp_path / "linked-checkout"
    link.symlink_to(tree, target_is_directory=True)
    _assert_unproven_path_cannot_authorize_removal(repo, tree, cohort, link)


def test_forged_gitdir_cannot_authorize_switched_removal(tmp_path, monkeypatch):
    from tests.orchestration.test_merge_closeout import git

    repo, tree, _tasks, cohort, merged_head = _real_switched_checkout(tmp_path, monkeypatch)
    git(repo, "remote", "set-url", "origin", "https://github.com/acme/widget.git")
    _merged_gh(monkeypatch, head=merged_head, branch="cursor/fresh-gate")
    forged = tmp_path / "forged-checkout"
    forged.mkdir()
    (forged / ".git").write_text(f"gitdir: {repo}/.git/worktrees/does-not-exist\n", encoding="utf-8")
    _assert_unproven_path_cannot_authorize_removal(repo, tree, cohort, forged)


def _hide_worktree_gitdir_behind_symlink(repo, tree, other_origin: str, *, absolute=False):
    """Rewrite the checkout gitdir to ``.git/jump/../worktrees/<id>``.

    ``jump`` is a symlink to another repository's worktree metadata. Lexical
    collapse names ``repo``. Git follows ``jump`` and reports ``other_origin``.
    """
    from pathlib import Path

    from tests.orchestration.test_merge_closeout import git

    original = (tree / ".git").read_text(encoding="utf-8").strip()
    prefix = "gitdir:"
    assert original.startswith(prefix)
    admin = Path(original[len(prefix) :].strip())
    other = repo.parent / "other-primary"
    git(repo.parent, "init", "--initial-branch=main", str(other))
    git(other, "remote", "add", "origin", other_origin)
    alternates = other / ".git" / "objects" / "info"
    alternates.mkdir(parents=True, exist_ok=True)
    (alternates / "alternates").write_text(f"{repo / '.git' / 'objects'}\n", encoding="utf-8")
    shutil.copytree(repo / ".git" / "refs", other / ".git" / "refs", dirs_exist_ok=True)
    packed = repo / ".git" / "packed-refs"
    if packed.is_file():
        shutil.copy(packed, other / ".git" / "packed-refs")
    other_admin = other / ".git" / "worktrees" / admin.name
    shutil.copytree(admin, other_admin)
    (other_admin / "commondir").write_text("../..\n", encoding="utf-8")
    (other_admin / "gitdir").write_text(f"{tree / '.git'}\n", encoding="utf-8")
    (repo / ".git" / "jump").symlink_to(other / ".git" / "worktrees", target_is_directory=True)
    relative = str(repo / ".git") if absolute else os.path.relpath(repo / ".git", tree)
    (tree / ".git").write_text(
        f"gitdir: {relative}/jump/../worktrees/{admin.name}\n",
        encoding="utf-8",
    )
    return other


@pytest.mark.parametrize("absolute", [False, True])
def test_dotdot_hidden_symlink_gitdir_cannot_authorize_switched_removal(tmp_path, monkeypatch, absolute):
    """A ``..`` that hides a symlink must not query primary A or prove the merge.

    Git follows ``jump`` into the other primary. The proof has to refuse before
    it asks for A's pull request.
    """
    from tests.orchestration.test_merge_closeout import git

    repo, tree, _tasks, cohort, merged_head = _real_switched_checkout(tmp_path, monkeypatch)
    git(repo, "remote", "set-url", "origin", "https://github.com/acme/widget.git")
    other = _hide_worktree_gitdir_behind_symlink(
        repo, tree, "https://github.com/other/elsewhere.git", absolute=absolute
    )
    assert git(tree, "remote", "get-url", "origin") == "https://github.com/other/elsewhere.git"
    assert git(tree, "rev-parse", "--path-format=absolute", "--git-common-dir") == str(other / ".git")
    calls = _merged_gh(monkeypatch, head=merged_head, branch="cursor/fresh-gate")
    assert wg._proven_linked_worktree_primary(tree) is None
    assert wg._checkout_pr_repository(tree) is None
    assert wg._switched_branch_merge_proven(repo, tree, cohort) is False
    assert not any("acme/widget" in " ".join(call) or "other/elsewhere" in " ".join(call) for call in calls)
    _assert_unproven_path_cannot_authorize_removal(repo, tree, cohort, tree)


@pytest.mark.parametrize(
    "origin",
    [
        "https://github.com:abc/acme/widget.git",
        "https://github.com:99999/acme/widget.git",
        "https://github.com:-1/acme/widget.git",
        "https://github.com:65536/acme/widget",
        "https://github.com:80abc/acme/widget.git",
        "ssh://git@github.com:notaport/acme/widget.git",
        "https://user:token@github.com:abc/acme/widget.git",
    ],
)
def test_malformed_origin_port_is_unknown(origin):
    """A port GitHub's URL parser cannot read is an unknown origin, not an exception."""
    assert wg._parse_github_origin(origin) is None


def test_copied_common_directory_with_trailing_space_cannot_authorize_removal(tmp_path, monkeypatch):
    from tests.orchestration.test_merge_closeout import git

    repo, tree, _tasks, cohort, merged_head = _real_switched_checkout(tmp_path, monkeypatch)
    git(repo, "remote", "set-url", "origin", "https://github.com/acme/widget.git")
    copied = repo / ".git "
    shutil.copytree(repo / ".git", copied)
    admin = repo / ".git/worktrees/switched-proof"
    (admin / "commondir").write_text(f"{copied}\n", encoding="utf-8")
    raw = subprocess.run(
        ["git", "rev-parse", "--path-format=absolute", "--git-common-dir"],
        cwd=tree,
        capture_output=True,
        check=True,
        timeout=30,
    ).stdout
    assert raw == os.fsencode(copied) + b"\n"
    assert git(tree, "config", "--get", "remote.origin.url") == "https://github.com/acme/widget.git"
    calls = _merged_gh(monkeypatch, head=merged_head, branch="cursor/fresh-gate")
    _assert_unproven_path_cannot_authorize_removal(repo, tree, cohort, tree)
    assert calls == []


def test_unregistered_copied_worktree_cannot_authorize_removal(tmp_path, monkeypatch):
    from tests.orchestration.test_merge_closeout import git

    repo, tree, _tasks, cohort, merged_head = _real_switched_checkout(tmp_path, monkeypatch)
    git(repo, "remote", "set-url", "origin", "https://github.com/acme/widget.git")
    copied = tree.parent / "unregistered"
    shutil.copytree(tree, copied)
    calls = _merged_gh(monkeypatch, head=merged_head, branch="cursor/fresh-gate")
    _assert_unproven_path_cannot_authorize_removal(repo, tree, cohort, copied)
    assert calls == []


@pytest.mark.parametrize("command", ["rev-parse", "config", "worktree"])
@pytest.mark.parametrize("fault", ["nonzero", "unreadable", "text", "empty", "extra", "unterminated"])
def test_git_identity_failure_refuses_before_pr_or_removal(tmp_path, monkeypatch, command, fault):
    from tests.orchestration.test_merge_closeout import git

    repo, tree, _tasks, cohort, merged_head = _real_switched_checkout(tmp_path, monkeypatch)
    git(repo, "remote", "set-url", "origin", "https://github.com/acme/widget.git")
    original = wg.safe_git
    calls = _merged_gh(monkeypatch, head=merged_head, branch="cursor/fresh-gate")

    def probe(args, **kwargs):
        if args[0] != command:
            return original(args, **kwargs)
        if fault == "unreadable":
            raise OSError("identity output unavailable")
        proc = original(args, **kwargs)
        if fault == "nonzero":
            return subprocess.CompletedProcess(args, 128, proc.stdout, b"refused")
        stdout = {
            "text": "unexpected decoded output",
            "empty": b"",
            "extra": proc.stdout + b"unexpected\n\n",
            "unterminated": proc.stdout[:-1],
        }[fault]
        return subprocess.CompletedProcess(args, 0, stdout, b"")

    monkeypatch.setattr(wg, "safe_git", probe)
    _assert_unproven_path_cannot_authorize_removal(repo, tree, cohort, tree)
    assert calls == []


@pytest.mark.parametrize("origin", [" https://github.com/acme/widget.git", "https://github.com/acme/widget.git "])
def test_origin_whitespace_is_not_normalized(tmp_path, monkeypatch, origin):
    from tests.orchestration.test_merge_closeout import git

    repo, tree, _tasks, cohort, merged_head = _real_switched_checkout(tmp_path, monkeypatch)
    git(repo, "config", "remote.origin.url", origin)
    calls = _merged_gh(monkeypatch, head=merged_head, branch="cursor/fresh-gate")
    _assert_unproven_path_cannot_authorize_removal(repo, tree, cohort, tree)
    assert calls == []


def test_worktree_origin_override_cannot_authorize_primary_pr(tmp_path, monkeypatch):
    from tests.orchestration.test_merge_closeout import git

    repo, tree, _tasks, cohort, merged_head = _real_switched_checkout(tmp_path, monkeypatch)
    git(repo, "config", "remote.origin.url", "https://github.com/acme/widget.git")
    git(repo, "config", "extensions.worktreeConfig", "true")
    git(tree, "config", "--worktree", "remote.origin.url", "https://github.com/other/elsewhere.git")
    calls = _merged_gh(monkeypatch, head=merged_head, branch="cursor/fresh-gate")
    _assert_unproven_path_cannot_authorize_removal(repo, tree, cohort, tree)
    assert calls == []


def test_git_only_resolver_never_reads_pointer_files(tmp_path, monkeypatch):
    from pathlib import Path

    from tests.orchestration.test_merge_closeout import git

    repo, tree, _tasks, _cohort, _merged_head = _real_switched_checkout(tmp_path, monkeypatch)
    git(repo, "config", "remote.origin.url", "https://github.com/acme/widget.git")

    def refuse(*_args, **_kwargs):
        pytest.fail("the identity resolver read a pointer file")

    monkeypatch.setattr(Path, "read_text", refuse)
    monkeypatch.setattr(Path, "read_bytes", refuse)
    assert wg._checkout_pr_repository(tree) == repo


# --- Hermetic repository fixtures shared with the output suites --


@pytest.fixture
def hermetic_repo(monkeypatch, tmp_path):
    """A fresh git repository with an origin and a task directory; PR lookups answer MERGED."""
    repo_root = tmp_path / "repo"
    tasks_dir = tmp_path / "tasks"
    tasks_dir.mkdir(parents=True)
    monkeypatch.setenv("LU_TASKS_DIR", str(tasks_dir))
    _init_repo(repo_root)
    monkeypatch.setattr(wg, "_live_cwd_paths", lambda _repo: set())
    monkeypatch.setattr(wg, "_active_task_ids", lambda: set())

    def merged_pr(_repo: Path, branch: str | None):
        if branch is None:
            return [], None
        proc = _run(["git", "rev-parse", f"refs/heads/{branch}"], cwd=repo_root)
        head = (proc.stdout or "").strip() if proc.returncode == 0 else None
        return [wg.PullRequestState(1, "MERGED", head)], None

    monkeypatch.setattr(wg, "_query_pr_states", merged_pr)
    return repo_root, tasks_dir


def _run(args: list[str], cwd: Path, check: bool = True) -> subprocess.CompletedProcess[str]:
    return _REAL_RUN(args, cwd=cwd, capture_output=True, text=True, check=check, timeout=30, env=git_env())


def _init_repo(repo_root: Path) -> None:
    repo_root.mkdir(parents=True)
    remote = repo_root.parent / f"{repo_root.name}-origin.git"
    _run(["git", "init", "--bare", str(remote)], cwd=repo_root.parent)
    _run(["git", "init", "--initial-branch=main", str(repo_root)], cwd=repo_root.parent)
    _run(["git", "config", "user.email", "test@example.com"], cwd=repo_root)
    _run(["git", "config", "user.name", "Test User"], cwd=repo_root)
    (repo_root / "README.md").write_text("# test\n", encoding="utf-8")
    _run(["git", "add", "README.md"], cwd=repo_root)
    _run(["git", "commit", "-m", "initial"], cwd=repo_root)
    _run(["git", "remote", "add", "origin", str(remote)], cwd=repo_root)
    _run(["git", "push", "-u", "origin", "main"], cwd=repo_root)


def _add_dispatch_worktree(repo_root: Path, agent: str, task_id: str) -> Path:
    branch = f"{agent}/{task_id}"
    _run(["git", "branch", branch], cwd=repo_root)
    path = repo_root / ".worktrees" / "dispatch" / agent / task_id
    path.parent.mkdir(parents=True, exist_ok=True)
    _run(["git", "worktree", "add", str(path), branch], cwd=repo_root)
    return path


def _add_worktree_at(repo_root: Path, path: Path, branch: str) -> Path:
    _run(["git", "branch", branch], cwd=repo_root)
    path.parent.mkdir(parents=True, exist_ok=True)
    _run(["git", "worktree", "add", str(path), branch], cwd=repo_root)
    return path


def _write_task_state(tasks_dir: Path, task_id: str, status: str, worktree_path: Path, *, agent: str = "kimi") -> None:
    state = {"task_id": task_id, "agent": agent, "status": status, "worktree_path": str(worktree_path)}
    (tasks_dir / f"{task_id}.json").write_text(json.dumps(state), encoding="utf-8")


def _reuse_cohort(
    repo_root: Path, tasks_dir: Path, *, creator_task: str, successor_task: str, leaf: str = "shared-leaf"
) -> Path:
    """A checkout created by one task and reused by another (default: a non-canonical leaf)."""
    branch = "codex/shared-reused"
    worktree = _add_worktree_at(repo_root, repo_root / ".worktrees" / "dispatch" / "codex" / leaf, branch)
    # The continuation proof needs a positive PID that provably no longer exists.
    finished = subprocess.Popen([sys.executable, "-c", "pass"])
    finished.wait()
    for task_id, reused in ((creator_task, False), (successor_task, True)):
        state: dict[str, Any] = {
            "task_id": task_id,
            "agent": "codex",
            "status": "done",
            "worktree_path": str(worktree),
            "worktree_branch": branch,
            "worktree_reused": reused,
            "run_nonce": f"nonce-{task_id}",
            "pid": finished.pid,
        }
        if not reused:
            state["ignored_output_baseline"] = output.creation_inventory(
                worktree, primary=repo_root, task_id=task_id, run_nonce=state["run_nonce"]
            )
        task_record_path(tasks_dir, task_id).write_text(json.dumps(state), encoding="utf-8")
    return worktree
