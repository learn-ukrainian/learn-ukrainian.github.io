from __future__ import annotations

import json
import time
from pathlib import Path
from urllib.parse import parse_qs

import pytest

from scripts.orchestration import pr_freeze

REPO = "example/repo"
# The freeze is off by default (#11272); the behavior tests opt in explicitly.
OPT_IN = {pr_freeze.THRESHOLD_ENV: "15"}


def _fetch(count):
    calls = []

    def fetch(repo):
        calls.append(repo)
        return count

    return fetch, calls


def test_refuses_at_threshold(tmp_path: Path) -> None:
    fetch, _ = _fetch(15)
    decision = pr_freeze.evaluate(REPO, environ=OPT_IN, fetch=fetch, cache_file=tmp_path / "c.json")
    assert decision.refused
    line = decision.refusal_line(REPO)
    assert "15 open PRs" in line
    assert "Land your own open PRs first" in line


def test_env_override(tmp_path: Path) -> None:
    fetch, calls = _fetch(20)
    env = {pr_freeze.THRESHOLD_ENV: "25"}
    assert not pr_freeze.evaluate(REPO, environ=env, fetch=fetch, cache_file=tmp_path / "c.json").refused
    assert calls == [REPO]
    disabled = pr_freeze.evaluate(
        REPO,
        environ={pr_freeze.THRESHOLD_ENV: "0"},
        fetch=fetch,
        cache_file=tmp_path / "disabled.json",
    )
    assert not disabled.refused
    assert disabled.threshold == 0
    assert disabled.open_prs is None
    assert calls == [REPO]
    assert pr_freeze.threshold_from_env({pr_freeze.THRESHOLD_ENV: "15"}) == 15
    assert pr_freeze.threshold_from_env({pr_freeze.THRESHOLD_ENV: "0"}) == 0
    assert pr_freeze.threshold_from_env({pr_freeze.THRESHOLD_ENV: "-3"}) == 0


def test_default_is_off() -> None:
    """No override, a blank value or junk leaves the freeze disabled (#11272)."""
    assert pr_freeze.DEFAULT_THRESHOLD == 0
    assert pr_freeze.threshold_from_env({}) == 0
    assert pr_freeze.threshold_from_env({pr_freeze.THRESHOLD_ENV: ""}) == 0
    assert pr_freeze.threshold_from_env({pr_freeze.THRESHOLD_ENV: "junk"}) == 0


def test_default_admits_many_open_prs_without_counting(tmp_path: Path) -> None:
    fetch, calls = _fetch(500)
    decision = pr_freeze.evaluate(REPO, environ={}, fetch=fetch, cache_file=tmp_path / "c.json")
    assert not decision.refused
    assert decision.threshold == 0
    assert decision.open_prs is None
    assert decision.warning is None
    assert calls == []


@pytest.mark.parametrize("threshold, count, refused", [(3, 2, False), (3, 3, True), (3, 4, True)])
def test_explicit_opt_in_refuses_at_n(tmp_path: Path, threshold: int, count: int, refused: bool) -> None:
    fetch, _ = _fetch(count)
    env = {pr_freeze.THRESHOLD_ENV: str(threshold)}
    decision = pr_freeze.evaluate(REPO, environ=env, fetch=fetch, cache_file=tmp_path / "c.json")
    assert decision.refused is refused
    assert decision.threshold == threshold


def test_fails_open_with_warning(tmp_path: Path) -> None:
    def broken(repo):
        raise RuntimeError("network down")

    decision = pr_freeze.evaluate(REPO, environ=OPT_IN, fetch=broken, cache_file=tmp_path / "c.json")
    assert not decision.refused
    assert decision.warning == "open-PR freeze check skipped: open_pr_count_unavailable"


def test_branch_exempt_only_with_open_pr(tmp_path: Path) -> None:
    fetch, _ = _fetch(30)
    cache = tmp_path / "c.json"
    with_pr = pr_freeze.evaluate(
        REPO, branch="codex/fix-1", environ=OPT_IN, fetch=fetch, has_open_pr=lambda r, b: True, cache_file=cache
    )
    assert not with_pr.refused
    no_pr = pr_freeze.evaluate(
        REPO, branch="codex/new", environ=OPT_IN, fetch=fetch, has_open_pr=lambda r, b: False, cache_file=cache
    )
    assert no_pr.refused

    def broken(repo, branch):
        raise RuntimeError("lookup failed")

    unknown = pr_freeze.evaluate(
        REPO, branch="codex/x", environ=OPT_IN, fetch=fetch, has_open_pr=broken, cache_file=cache
    )
    assert not unknown.refused
    assert unknown.warning == "open-PR freeze check skipped: branch_pr_lookup_unavailable"


def test_fresh_cache_count_below_total_is_not_used(tmp_path: Path) -> None:
    """A fresh cache of count 14 and total 21 must not pass a threshold of 15."""
    cache = tmp_path / "c.json"
    cache.write_text(json.dumps({"count": 14, "total": 21, "at": time.time()}))
    calls: list[str] = []

    def fetch(repo: str) -> pr_freeze.OpenPrCounts:
        calls.append(repo)
        return pr_freeze.OpenPrCounts(total=21, counted=21)

    decision = pr_freeze.evaluate(REPO, environ=OPT_IN, fetch=fetch, cache_file=cache)
    assert calls == [REPO]
    assert decision.open_prs == 21
    assert decision.total_open == 21
    assert decision.open_prs == decision.total_open
    assert decision.refused
    assert decision.warning in (None, "")
    stored = json.loads(cache.read_text())
    assert stored["count"] == 21
    assert stored["total"] == 21


def test_unequal_fetched_counts_are_not_used(tmp_path: Path) -> None:
    """A fetched counted value below the total is not the freeze count."""
    calls: list[str] = []

    def fetch(repo: str) -> pr_freeze.OpenPrCounts:
        calls.append(repo)
        return pr_freeze.OpenPrCounts(total=21, counted=14)

    normalized = pr_freeze._as_counts(pr_freeze.OpenPrCounts(total=21, counted=14))
    assert normalized.counted == 21
    assert normalized.total == 21
    decision = pr_freeze.evaluate(REPO, environ=OPT_IN, fetch=fetch, cache_file=tmp_path / "c.json")
    assert calls == [REPO]
    assert decision.open_prs == 21
    assert decision.total_open == 21
    assert decision.open_prs == decision.total_open
    assert decision.refused
    assert decision.warning in (None, "")


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


def test_branch_lookup_encodes_head(monkeypatch) -> None:
    seen = []

    def fake_get(endpoint):
        seen.append(endpoint)
        return [{"number": 1}]

    monkeypatch.setattr(pr_freeze, "_gh_get", fake_get)
    assert pr_freeze.branch_has_open_pr(REPO, "codex/fix+123&x#y%z")
    assert seen[0].endswith("head=example%3Acodex%2Ffix%2B123%26x%23y%25z")


def _issued_search_query(endpoint: str) -> str:
    path, _, query = endpoint.partition("?")
    assert path == "search/issues", endpoint
    parsed = parse_qs(query, strict_parsing=True)
    assert parsed["per_page"] == ["1"]
    return parsed["q"][0]


def test_decision_path_issues_one_non_dependabot_search(monkeypatch, tmp_path: Path) -> None:
    """One search. Its total_count is the counted number. Page length is not."""
    payload = {
        "total_count": 16,
        "items": [{"number": 1}, {"number": 2}],
    }
    assert payload["total_count"] != len(payload["items"])
    seen: list[str] = []

    def fake_get(endpoint: str):
        seen.append(endpoint)
        return payload

    monkeypatch.setattr(pr_freeze, "_gh_get", fake_get)
    decision = pr_freeze.evaluate(REPO, environ=OPT_IN, cache_file=tmp_path / "c.json")
    assert seen == [pr_freeze._open_pr_search_endpoint(REPO)]
    assert len(seen) == 1
    assert _issued_search_query(seen[0]) == f"repo:{REPO} is:pr is:open -author:app/dependabot"
    assert decision.refused
    assert decision.open_prs == payload["total_count"]
    assert decision.total_open == payload["total_count"]
    assert decision.open_prs != len(payload["items"])
    assert decision.warning in (None, "")
    line = decision.refusal_line(REPO)
    assert "16 open PRs" in line
    assert "16 counted" in line
    assert "Land your own open PRs first" in line
