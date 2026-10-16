from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
from pathlib import Path
from types import SimpleNamespace

import pytest

from scripts.orchestration import pr_freeze

REPO = "example/repo"


def _fetch(count):
    calls = []

    def fetch(repo):
        calls.append(repo)
        return count

    return fetch, calls


def test_refuses_at_threshold(tmp_path: Path) -> None:
    fetch, _ = _fetch(15)
    decision = pr_freeze.evaluate(REPO, environ={}, fetch=fetch, cache_file=tmp_path / "c.json")
    assert decision.refused
    line = decision.refusal_line(REPO)
    assert "15 open PRs" in line
    assert "Land your own open PRs first" in line


def test_admits_below_threshold(tmp_path: Path) -> None:
    fetch, _ = _fetch(14)
    assert not pr_freeze.evaluate(REPO, environ={}, fetch=fetch, cache_file=tmp_path / "c.json").refused


def test_env_override(tmp_path: Path) -> None:
    fetch, _ = _fetch(20)
    env = {pr_freeze.THRESHOLD_ENV: "25"}
    assert not pr_freeze.evaluate(REPO, environ=env, fetch=fetch, cache_file=tmp_path / "c.json").refused
    env = {pr_freeze.THRESHOLD_ENV: "0"}
    assert not pr_freeze.evaluate(REPO, environ=env, fetch=fetch, cache_file=tmp_path / "c.json").refused
    assert pr_freeze.threshold_from_env({pr_freeze.THRESHOLD_ENV: "junk"}) == 15


def test_fails_open_with_warning(tmp_path: Path) -> None:
    def broken(repo):
        raise RuntimeError("network down")

    decision = pr_freeze.evaluate(REPO, environ={}, fetch=broken, cache_file=tmp_path / "c.json")
    assert not decision.refused
    assert decision.warning == "open-PR freeze check skipped: open_pr_count_unavailable"


def test_branch_exempt_only_with_open_pr(tmp_path: Path) -> None:
    fetch, _ = _fetch(30)
    cache = tmp_path / "c.json"
    with_pr = pr_freeze.evaluate(
        REPO, branch="codex/fix-1", environ={}, fetch=fetch, has_open_pr=lambda r, b: True, cache_file=cache
    )
    assert not with_pr.refused
    no_pr = pr_freeze.evaluate(
        REPO, branch="codex/new", environ={}, fetch=fetch, has_open_pr=lambda r, b: False, cache_file=cache
    )
    assert no_pr.refused

    def broken(repo, branch):
        raise RuntimeError("lookup failed")

    unknown = pr_freeze.evaluate(REPO, branch="codex/x", environ={}, fetch=fetch, has_open_pr=broken, cache_file=cache)
    assert not unknown.refused
    assert unknown.warning == "open-PR freeze check skipped: branch_pr_lookup_unavailable"


def test_cache_reused_within_ttl(tmp_path: Path) -> None:
    fetch, calls = _fetch(3)
    cache = tmp_path / "c.json"
    clock = iter([100.0, 130.0, 200.0, 200.0])
    for _ in range(3):
        pr_freeze.cached_open_pr_count(REPO, fetch=fetch, cache_file=cache, ttl_s=60, now=lambda: next(clock))
    assert len(calls) == 2


@pytest.mark.parametrize(
    ("kwargs", "expected"),
    [
        ({}, True),
        ({"pr": 12}, False),
        ({"cwd": "/some/worktree"}, False),
        ({"review": True}, False),
        ({"reused_worktree": True}, False),
        ({"mode": "read-only"}, False),
        ({"repo_role": "private-infra"}, False),
    ],
)
def test_only_new_public_implementation_jobs_gated(kwargs, expected) -> None:
    base = {"mode": "workspace-write", "repo_role": "public-monorepo", "pr": None, "cwd": None, "review": False}
    base.update(kwargs)
    assert pr_freeze.opens_new_pr(**base) is expected


def test_dispatch_refuses_before_any_side_effect(monkeypatch, capsys, tmp_path) -> None:
    """End-to-end: a frozen new-PR dispatch exits 3 and leaves no task record."""
    from scripts import delegate

    monkeypatch.setenv(pr_freeze.THRESHOLD_ENV, "15")
    monkeypatch.setattr(pr_freeze, "fetch_open_pr_count", lambda repo: 30)
    monkeypatch.setenv("XDG_CACHE_HOME", str(tmp_path / "cache"))
    monkeypatch.setattr(delegate, "tasks_dir", lambda: tmp_path / "tasks")

    def no_side_effects(*a, **k):
        raise AssertionError("side effect reached before the freeze check")

    monkeypatch.setattr(delegate, "_state_path", no_side_effects)
    monkeypatch.setattr(delegate, "_archive_task_artifacts", no_side_effects)
    argv = [
        "delegate.py",
        "dispatch",
        "--agent",
        "codex",
        "--task-id",
        "freeze-probe",
        "--mode",
        "workspace-write",
        "--worktree",
        "--prompt",
        "implement a thing",
    ]
    monkeypatch.setattr(sys, "argv", argv)
    rc = delegate.main()
    err = capsys.readouterr().err
    assert rc == 3, err
    assert "Land your own open PRs first" in err
    assert not (tmp_path / "tasks").exists()


def test_helper_allows_existing_pr_branch(monkeypatch) -> None:
    from scripts import delegate

    monkeypatch.setenv(pr_freeze.THRESHOLD_ENV, "15")
    monkeypatch.setattr(pr_freeze, "fetch_open_pr_count", lambda repo: 30)
    monkeypatch.setattr(pr_freeze, "branch_has_open_pr", lambda repo, branch: True)
    monkeypatch.setenv(pr_freeze.CACHE_ENV, "0")
    repo = SimpleNamespace(github=REPO, role="public-monorepo")
    args = argparse.Namespace(
        mode="workspace-write", branch="codex/fix-1", pr=None, cwd=None, worktree=None,
        force_new=True, task_id="retry-probe",
    )
    assert delegate._check_open_pr_freeze(args, repo) is None


def test_branch_lookup_encodes_head(monkeypatch) -> None:
    seen = []

    def fake_get(endpoint):
        seen.append(endpoint)
        return [{"number": 1}]

    monkeypatch.setattr(pr_freeze, "_gh_get", fake_get)
    assert pr_freeze.branch_has_open_pr(REPO, "codex/fix+123&x#y%z")
    assert seen[0].endswith("head=example%3Acodex%2Ffix%2B123%26x%23y%25z")


def test_force_new_without_prior_record_is_still_refused(monkeypatch, capsys, tmp_path) -> None:
    from scripts import delegate

    monkeypatch.setenv(pr_freeze.THRESHOLD_ENV, "15")
    monkeypatch.setattr(pr_freeze, "fetch_open_pr_count", lambda repo: 30)
    monkeypatch.setenv("XDG_CACHE_HOME", str(tmp_path / "cache"))
    monkeypatch.setattr(delegate, "tasks_dir", lambda: tmp_path / "tasks")
    repo = SimpleNamespace(github=REPO, role="public-monorepo")
    args = argparse.Namespace(
        mode="workspace-write", branch=None, pr=None, cwd=None, worktree="auto", force_new=True, task_id="fresh-id"
    )
    assert delegate._check_open_pr_freeze(args, repo) == 3
    assert not (tmp_path / "tasks").exists()

    (tmp_path / "tasks").mkdir()
    (tmp_path / "tasks" / "fresh-id.json").write_text("{}")
    assert delegate._check_open_pr_freeze(args, repo) == 3


@pytest.mark.parametrize("archived", [False, True])
@pytest.mark.parametrize("prior_mode", ["read-only", "workspace-write"])
def test_force_new_record_cannot_exempt_fresh_branch(monkeypatch, capsys, tmp_path, archived, prior_mode) -> None:
    """A retained record is not evidence that the retry reuses a checkout or PR."""
    from scripts import delegate

    monkeypatch.setenv(pr_freeze.THRESHOLD_ENV, "15")
    monkeypatch.setattr(pr_freeze, "fetch_open_pr_count", lambda repo: 30)
    monkeypatch.setenv("XDG_CACHE_HOME", str(tmp_path / "cache"))
    monkeypatch.setattr(delegate, "tasks_dir", lambda: tmp_path / "tasks")
    task_id = "retry-probe"
    record = delegate._archived_state_path(task_id) if archived else delegate._state_path_no_create(task_id)
    record.parent.mkdir(parents=True)
    record.write_text(json.dumps({"task_id": task_id, "mode": prior_mode, "status": "done", "branch": "codex/reaped"}))
    before = record.read_bytes()

    def no_side_effects(*a, **k):
        raise AssertionError("fresh-branch retry reached a side effect while frozen")

    monkeypatch.setattr(delegate, "_state_path", no_side_effects)
    monkeypatch.setattr(delegate, "_archive_task_artifacts", no_side_effects)
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "delegate.py", "dispatch", "--agent", "codex", "--task-id", task_id,
            "--mode", "workspace-write", "--worktree", "--force-new", "--prompt", "implement a thing",
        ],
    )
    assert delegate.main() == 3
    assert "Land your own open PRs first" in capsys.readouterr().err
    assert record.read_bytes() == before


@pytest.mark.parametrize("failure", ["count", "branch", "client_cache"])
def test_dispatch_warning_omits_raw_diagnostics(monkeypatch, capsys, tmp_path, failure) -> None:
    from scripts import delegate

    sentinel = "SYNTHETIC_PRIVATE_DIAGNOSTIC"

    def broken(*a, **k):
        raise OSError(sentinel)

    monkeypatch.setenv(pr_freeze.THRESHOLD_ENV, "15")
    monkeypatch.setenv("XDG_CACHE_HOME", str(tmp_path / "cache"))
    if failure == "count":
        monkeypatch.setattr(pr_freeze, "fetch_open_pr_count", broken)
    elif failure == "client_cache":
        # Exercise the actual count-fetch path through the client boundary.
        from scripts.common import github_client

        monkeypatch.setattr(github_client, "run", broken)
    else:
        monkeypatch.setattr(pr_freeze, "fetch_open_pr_count", lambda repo: 30)
        monkeypatch.setattr(pr_freeze, "branch_has_open_pr", broken)
    repo = SimpleNamespace(github=REPO, role="public-monorepo")
    args = argparse.Namespace(
        mode="workspace-write",
        branch=sentinel if failure == "branch" else None,
        pr=None,
        cwd=None,
        worktree="auto",
    )
    assert delegate._check_open_pr_freeze(args, repo) is None
    output = capsys.readouterr()
    reason = "branch_pr_lookup_unavailable" if failure == "branch" else "open_pr_count_unavailable"
    assert reason in output.err
    assert sentinel not in output.err + output.out


def test_fresh_explicit_worktree_path_is_still_refused(monkeypatch, tmp_path) -> None:
    from scripts import delegate

    monkeypatch.setenv(pr_freeze.THRESHOLD_ENV, "15")
    monkeypatch.setattr(pr_freeze, "fetch_open_pr_count", lambda repo: 30)
    monkeypatch.setenv("XDG_CACHE_HOME", str(tmp_path / "cache"))
    repo = SimpleNamespace(github=REPO, role="public-monorepo")
    fresh = tmp_path / "dispatch" / "codex" / "fresh-name"
    args = argparse.Namespace(mode="workspace-write", branch=None, pr=None, cwd=None, worktree=str(fresh))
    assert delegate._check_open_pr_freeze(args, repo) == 3
    assert not fresh.exists()

    fresh.mkdir(parents=True)
    (fresh / ".git").write_text("gitdir: elsewhere\n")
    assert delegate._check_open_pr_freeze(args, repo) is None


def test_relative_worktree_resolves_against_target_repo(monkeypatch, tmp_path) -> None:
    from scripts import delegate

    monkeypatch.setenv(pr_freeze.THRESHOLD_ENV, "15")
    monkeypatch.setattr(pr_freeze, "fetch_open_pr_count", lambda repo: 30)
    monkeypatch.setenv("XDG_CACHE_HOME", str(tmp_path / "cache"))
    repo = SimpleNamespace(github=REPO, role="public-monorepo")
    target_root = tmp_path / "target"
    target_root.mkdir()
    other_cwd = tmp_path / "elsewhere"
    decoy = other_cwd / "wt" / "new-target"
    decoy.mkdir(parents=True)
    (decoy / ".git").write_text("gitdir: x\n")
    monkeypatch.chdir(other_cwd)
    args = argparse.Namespace(mode="workspace-write", branch=None, pr=None, cwd=None, worktree="wt/new-target")
    assert delegate._check_open_pr_freeze(args, repo, target_root) == 3

    real = target_root / "wt" / "new-target"
    real.mkdir(parents=True)
    (real / ".git").write_text("gitdir: x\n")
    assert delegate._check_open_pr_freeze(args, repo, target_root) is None


_REFUSALS = {
    "rate_refusal_reset_only": (75, json.dumps({"error": "github_rate_limited", "reset_at": 1790000000})),
    "generic_non_zero": (1, json.dumps({"error": "github_http_error", "reset_at": None, "status": 502})),
    "empty_output": (0, ""),
    "malformed_output": (0, "not json"),
    "refusal_json_with_zero_rc": (0, json.dumps({"error": "github_rate_limited", "reset_at": None})),
}


def _client(monkeypatch, responses):
    """Route the shared client to canned results; ``responses`` is a list consumed in order."""
    from scripts.common import github_client

    calls = []

    def run(command, **kwargs):
        calls.append(command[-1])
        returncode, stdout = responses[min(len(calls), len(responses)) - 1]
        return subprocess.CompletedProcess(command, returncode, stdout, "")

    monkeypatch.setattr(github_client, "run", run)
    return calls


@pytest.mark.parametrize("shape", _REFUSALS)
def test_refused_count_read_is_unavailable_not_admitted(monkeypatch, tmp_path, shape) -> None:
    calls = _client(monkeypatch, [_REFUSALS[shape]])
    decision = pr_freeze.evaluate(REPO, branch="codex/x", environ={}, cache_file=tmp_path / "c.json")
    assert decision.refused is None
    assert decision.unavailable
    assert decision.open_prs is None
    assert decision.warning == "open-PR freeze check skipped: open_pr_count_unavailable"
    assert len(calls) == 1  # no branch lookup, no retry after the refusal
    assert not (tmp_path / "c.json").exists()


@pytest.mark.parametrize("shape", _REFUSALS)
def test_refused_branch_lookup_is_unavailable_not_admitted(monkeypatch, tmp_path, shape) -> None:
    fetch, _ = _fetch(30)
    calls = _client(monkeypatch, [_REFUSALS[shape]])
    decision = pr_freeze.evaluate(REPO, branch="codex/x", environ={}, fetch=fetch, cache_file=tmp_path / "c.json")
    assert decision.refused is None
    assert decision.unavailable
    assert decision.open_prs == 30
    assert decision.warning == "open-PR freeze check skipped: branch_pr_lookup_unavailable"
    assert len(calls) == 1


def test_successful_reads_keep_known_decisions(monkeypatch, tmp_path) -> None:
    count = json.dumps({"total_count": 30, "incomplete_results": False})
    calls = _client(monkeypatch, [(0, count), (0, json.dumps([{"number": 1}]))])
    exempt = pr_freeze.evaluate(REPO, branch="codex/x", environ={}, cache_file=tmp_path / "c.json")
    assert (exempt.refused, exempt.unavailable, exempt.warning) == (False, False, None)
    assert len(calls) == 2
    calls = _client(monkeypatch, [(0, count), (0, "[]")])
    frozen = pr_freeze.evaluate(REPO, branch="codex/y", environ={}, cache_file=tmp_path / "d.json")
    assert (frozen.refused, frozen.unavailable, frozen.open_prs) == (True, False, 30)
    calls = _client(monkeypatch, [(0, json.dumps({"total_count": 3, "incomplete_results": False}))])
    below = pr_freeze.evaluate(REPO, branch="codex/z", environ={}, cache_file=tmp_path / "e.json")
    assert (below.refused, below.unavailable) == (False, False)
    assert len(calls) == 1


def _unavailable_count(monkeypatch, tmp_path, payload, calls_expected=1):
    calls = _client(monkeypatch, [(0, json.dumps(payload))])
    decision = pr_freeze.evaluate(REPO, branch="codex/x", environ={}, cache_file=tmp_path / "c.json")
    assert decision.refused is None
    assert decision.unavailable
    assert decision.warning == "open-PR freeze check skipped: open_pr_count_unavailable"
    assert len(calls) == calls_expected
    assert not (tmp_path / "c.json").exists()


@pytest.mark.parametrize(
    "payload",
    [
        {"total_count": 0, "incomplete_results": True},
        {"total_count": 30, "incomplete_results": True},
        {"total_count": 0},
        {"total_count": 0, "incomplete_results": None},
        {"total_count": True, "incomplete_results": False},
        {"total_count": -1, "incomplete_results": False},
        {"total_count": "3", "incomplete_results": False},
        {"total_count": 3.0, "incomplete_results": False},
    ],
)
def test_incomplete_or_malformed_count_is_unavailable_not_admitted(monkeypatch, tmp_path, payload) -> None:
    _unavailable_count(monkeypatch, tmp_path, payload)


@pytest.mark.parametrize(
    "payload",
    [
        [{"error": "github_rate_limited"}],
        [{"message": "Bad credentials"}],
        [None],
        ["x"],
        [{"number": True}],
        [{"number": 1}, {"error": "github_http_error"}],
    ],
)
def test_malformed_branch_list_is_unavailable_not_exempt(monkeypatch, tmp_path, payload) -> None:
    fetch, _ = _fetch(30)
    calls = _client(monkeypatch, [(0, json.dumps(payload))])
    decision = pr_freeze.evaluate(REPO, branch="codex/x", environ={}, fetch=fetch, cache_file=tmp_path / "c.json")
    assert decision.refused is None
    assert decision.unavailable
    assert decision.warning == "open-PR freeze check skipped: branch_pr_lookup_unavailable"
    assert len(calls) == 1


def test_count_and_branch_reads_survive_a_process_failure(monkeypatch, tmp_path) -> None:
    from scripts.common import github_client

    def broken(command, **kwargs):
        raise subprocess.TimeoutExpired("gh", 20)

    monkeypatch.setattr(github_client, "run", broken)
    decision = pr_freeze.evaluate(REPO, branch="codex/x", environ={}, cache_file=tmp_path / "c.json")
    assert decision.refused is None
    assert decision.warning == "open-PR freeze check skipped: open_pr_count_unavailable"


# --- Round 3: one strict parse-or-unavailable choke point per payload kind (#10792) -------------
#
# Every consumption of a count or a branch list (live read, cached read, injected reader) goes
# through the same whitelist validators. The matrices below cross payload kind x malformation and
# assert both the unavailable outcome and the exact number of requests made.

_COUNT_OK = {"total_count": 30, "incomplete_results": False}

_BAD_COUNT_DOCUMENTS = {
    "list_container": [],
    "list_wrapping_valid_object": [_COUNT_OK],
    "json_null": None,
    "scalar_int": 30,
    "scalar_string": "30",
    "scalar_bool": True,
    "empty_object": {},
    "missing_total_count": {"incomplete_results": False},
    "null_total_count": {"total_count": None, "incomplete_results": False},
    "bool_total_count": {"total_count": False, "incomplete_results": False},
    "negative_total_count": {"total_count": -1, "incomplete_results": False},
    "string_total_count": {"total_count": "30", "incomplete_results": False},
    "float_total_count": {"total_count": 30.0, "incomplete_results": False},
    "nested_total_count": {"total_count": {"value": 30}, "incomplete_results": False},
    "list_total_count": {"total_count": [30], "incomplete_results": False},
    "missing_incomplete": {"total_count": 30},
    "null_incomplete": {"total_count": 30, "incomplete_results": None},
    "string_incomplete": {"total_count": 30, "incomplete_results": "false"},
    "int_incomplete": {"total_count": 30, "incomplete_results": 0},
    "true_incomplete": {"total_count": 30, "incomplete_results": True},
    "nested_error_object": {"error": {"message": "x", "status": 502}},
    "message_error_object": {"message": "API rate limit exceeded", "documentation_url": "https://example.invalid"},
}


@pytest.mark.parametrize("shape", _BAD_COUNT_DOCUMENTS)
def test_count_document_matrix_is_unavailable_with_one_request(monkeypatch, tmp_path, shape) -> None:
    calls = _client(monkeypatch, [(0, json.dumps(_BAD_COUNT_DOCUMENTS[shape]))])
    decision = pr_freeze.evaluate(REPO, branch="codex/x", environ={}, cache_file=tmp_path / "c.json")
    assert (decision.refused, decision.open_prs) == (None, None)
    assert decision.warning == "open-PR freeze check skipped: open_pr_count_unavailable"
    assert len(calls) == 1
    assert not (tmp_path / "c.json").exists()


def _bad_cached_counts(now: float) -> dict:
    return {
        "bool_false": {"count": False, "at": now},
        "bool_true": {"count": True, "at": now},
        "negative": {"count": -1, "at": now},
        "string": {"count": "3", "at": now},
        "null": {"count": None, "at": now},
        "float": {"count": 3.0, "at": now},
        "list": {"count": [3], "at": now},
        "missing_count": {"at": now},
        "missing_at": {"count": 3},
        "null_at": {"count": 3, "at": None},
        "bool_at": {"count": 3, "at": True},
        "string_at": {"count": 3, "at": "now"},
        "future_at": {"count": 3, "at": now + 10_000},
        "list_record": [3],
        "scalar_record": 3,
        "null_record": None,
    }


_BAD_CACHED_SHAPES = list(_bad_cached_counts(0.0))


@pytest.mark.parametrize("shape", _BAD_CACHED_SHAPES)
def test_invalid_cache_record_is_a_miss_followed_by_a_live_read(tmp_path, shape) -> None:
    """A fresh cached ``count=false`` or ``count=-1`` once admitted with zero reads."""
    cache = tmp_path / "c.json"
    cache.write_text(json.dumps(_bad_cached_counts(time.time())[shape]))
    fetch, calls = _fetch(30)
    decision = pr_freeze.evaluate(REPO, environ={}, fetch=fetch, cache_file=cache)
    assert (decision.refused, decision.open_prs, decision.unavailable) == (True, 30, False)
    assert len(calls) == 1
    assert json.loads(cache.read_text())["count"] == 30  # the bad record was replaced by the live count


@pytest.mark.parametrize("shape", _BAD_CACHED_SHAPES)
def test_invalid_cache_record_with_a_failed_live_read_is_unavailable(tmp_path, shape) -> None:
    cache = tmp_path / "c.json"
    cache.write_text(json.dumps(_bad_cached_counts(time.time())[shape]))

    def broken(repo):
        raise RuntimeError("down")

    decision = pr_freeze.evaluate(REPO, environ={}, fetch=broken, cache_file=cache)
    assert (decision.refused, decision.unavailable, decision.open_prs) == (None, True, None)


@pytest.mark.parametrize("raw", ["", "not json", "{", "\x00", "[1,"])
def test_unparseable_cache_file_is_a_miss(tmp_path, raw) -> None:
    cache = tmp_path / "c.json"
    cache.write_text(raw)
    fetch, calls = _fetch(3)
    decision = pr_freeze.evaluate(REPO, environ={}, fetch=fetch, cache_file=cache)
    assert (decision.refused, decision.open_prs) == (False, 3)
    assert len(calls) == 1


def test_valid_fresh_cache_record_still_answers_without_a_read(tmp_path) -> None:
    cache = tmp_path / "c.json"
    cache.write_text(json.dumps({"count": 30, "at": time.time() - 5}))
    fetch, calls = _fetch(0)
    decision = pr_freeze.evaluate(REPO, environ={}, fetch=fetch, cache_file=cache)
    assert (decision.refused, decision.open_prs, decision.unavailable) == (True, 30, False)
    assert calls == []
    cache.write_text(json.dumps({"count": 30, "at": time.time() - 500}))  # stale: a read, not a pass
    pr_freeze.evaluate(REPO, environ={}, fetch=fetch, cache_file=cache)
    assert len(calls) == 1


@pytest.mark.parametrize("value", [False, True, -1, "3", None, 3.0, [3], {"n": 3}])
def test_injected_count_reader_result_is_validated_too(tmp_path, value) -> None:
    fetch, calls = _fetch(value)
    decision = pr_freeze.evaluate(REPO, environ={}, fetch=fetch, cache_file=tmp_path / "c.json")
    assert (decision.refused, decision.open_prs) == (None, None)
    assert decision.warning == "open-PR freeze check skipped: open_pr_count_unavailable"
    assert len(calls) == 1
    assert not (tmp_path / "c.json").exists()


_BAD_PULL_LISTS = {
    "number_zero": [{"number": 0}],
    "number_negative": [{"number": -1}],
    "number_string": [{"number": "5"}],
    "number_float": [{"number": 5.0}],
    "number_null": [{"number": None}],
    "number_false": [{"number": False}],
    "number_list": [{"number": [5]}],
    "number_object": [{"number": {"v": 5}}],
    "number_missing": [{"id": 5}],
    "valid_then_zero": [{"number": 5}, {"number": 0}],
    "two_elements_for_per_page_1": [{"number": 5}, {"number": 6}],
    "object_container": {"number": 5},
    "object_wrapping_list": {"items": [{"number": 5}]},
    "json_null": None,
    "scalar_string": "[]",
    "scalar_int": 5,
    "nested_list": [[{"number": 5}]],
    "bare_int_element": [5],
    "nested_error_object": [{"error": {"message": "x"}}],
    "message_object": {"message": "Not Found", "documentation_url": "https://example.invalid"},
}


@pytest.mark.parametrize("shape", _BAD_PULL_LISTS)
def test_branch_list_matrix_is_unavailable_never_exempt(monkeypatch, tmp_path, shape) -> None:
    """``[{"number": 0}]`` and ``[{"number": -1}]`` once granted the existing-PR exemption."""
    fetch, _ = _fetch(30)
    calls = _client(monkeypatch, [(0, json.dumps(_BAD_PULL_LISTS[shape]))])
    decision = pr_freeze.evaluate(REPO, branch="codex/x", environ={}, fetch=fetch, cache_file=tmp_path / "c.json")
    assert (decision.refused, decision.open_prs) == (None, 30)
    assert decision.warning == "open-PR freeze check skipped: branch_pr_lookup_unavailable"
    assert len(calls) == 1


@pytest.mark.parametrize("value", [1, 0, "yes", "", None, [], [{"number": 5}], {"number": 5}])
def test_injected_branch_reader_result_must_be_a_bool(tmp_path, value) -> None:
    fetch, _ = _fetch(30)
    decision = pr_freeze.evaluate(
        REPO, branch="codex/x", environ={}, fetch=fetch, has_open_pr=lambda repo, branch: value,
        cache_file=tmp_path / "c.json",
    )
    assert (decision.refused, decision.open_prs) == (None, 30)
    assert decision.warning == "open-PR freeze check skipped: branch_pr_lookup_unavailable"


@pytest.mark.parametrize("value", [True, False])
def test_injected_branch_reader_bool_keeps_its_meaning(tmp_path, value) -> None:
    fetch, _ = _fetch(30)
    decision = pr_freeze.evaluate(
        REPO, branch="codex/x", environ={}, fetch=fetch, has_open_pr=lambda repo, branch: value,
        cache_file=tmp_path / "c.json",
    )
    assert (decision.refused, decision.unavailable) == (not value, False)


def test_branch_list_empty_and_single_valid_pull_keep_their_meaning(monkeypatch, tmp_path) -> None:
    fetch, _ = _fetch(30)
    _client(monkeypatch, [(0, "[]")])
    frozen = pr_freeze.evaluate(REPO, branch="codex/x", environ={}, fetch=fetch, cache_file=tmp_path / "c.json")
    assert (frozen.refused, frozen.unavailable) == (True, False)
    _client(monkeypatch, [(0, json.dumps([{"number": 1, "state": "open", "head": {"ref": "x"}}]))])
    exempt = pr_freeze.evaluate(REPO, branch="codex/x", environ={}, fetch=fetch, cache_file=tmp_path / "c.json")
    assert (exempt.refused, exempt.unavailable) == (False, False)
