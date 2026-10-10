"""Pull-request pipeline tests. Fixtures only: no live GitHub client."""

from __future__ import annotations

import json
import os
import time
from datetime import UTC, datetime, timedelta

import pytest
from fastapi.testclient import TestClient
from jsonschema import Draft202012Validator

from scripts.api import main as api_main
from scripts.api.fleet_board import activity as activity_mod
from scripts.api.fleet_board import prs as prs_mod
from scripts.orchestration import merge_queue_keeper as keeper
from scripts.orchestration.integration_sweep import lookup_verdict

client = TestClient(api_main.app, raise_server_exceptions=False)

NOW = datetime(2026, 10, 9, 10, 0, tzinfo=UTC)
SHA = "a" * 40
OTHER = "b" * 40
LOGIN = "fleet"
REPO = "example/repo"


@pytest.fixture(autouse=True)
def _no_network(monkeypatch: pytest.MonkeyPatch) -> None:
    def boom() -> None:
        raise AssertionError("network")

    monkeypatch.setattr(prs_mod, "_client", boom)
    monkeypatch.delenv("FLEET_STALE_PR_STATE", raising=False)
    prs_mod.clear_github_cache()


def _comment(sha: str, *, verdict: str = "APPROVED") -> dict[str, str | dict[str, str]]:
    started = "2026-10-09T08:00:00.000001+00:00"
    marker = (
        f"<!-- cf-verdict v1 sha={sha} task=review-one started={started} "
        f"verdict={verdict} model=gpt-6.1-sol family=openai -->"
    )
    body = (
        "### Cross-family review\n"
        f"head: {sha}\n"
        "Reviewer family: openai\n"
        f"VERDICT: {verdict}\n"
        "Reviewer model: gpt-6.1-sol\n"
        "Task id: review-one\n\n"
        "<details><summary>Reviewer's reply</summary>\n\n"
        "noted\n\n"
        "</details>\n\n"
        f"{marker}"
    )
    return {
        "id": f"review-{sha[:8]}",
        "body": body,
        "user": {"login": LOGIN},
        "author_association": "OWNER",
        "created_at": "2026-10-09T08:00:00Z",
        "updated_at": "2026-10-09T08:00:00Z",
    }


def _check(name: str, sha: str = SHA, *, status: str = "completed", conclusion: str = "success") -> dict[str, str]:
    return {
        "name": name,
        "head_sha": sha,
        "status": status,
        "conclusion": conclusion,
        "started_at": "2026-10-09T00:00:00Z",
    }


def _green(sha: str = SHA) -> tuple[dict[str, str], ...]:
    return (_check("CI Gate", sha), _check("Analyze (python)", sha))


def _pull(
    number: int = 42,
    sha: str = SHA,
    *,
    title: str = "Add a lesson",
    draft: bool = False,
    head_ref: str = "feature",
    base_ref: str = "main",
    labels: tuple[dict[str, str], ...] = (),
    body: str = "",
    merge_state: str | None = "CLEAN",
    epics: tuple[str, ...] = (),
    commit_at: str | None = None,
) -> prs_mod.Pull:
    return prs_mod.Pull(
        number=number,
        title=title,
        draft=draft,
        head_sha=sha,
        head_ref=head_ref,
        base_ref=base_ref,
        labels=labels,
        body=body,
        merge_state=merge_state,
        epics=epics,
        commit_at=commit_at,
    )


def _view(
    *pulls: prs_mod.Pull, queued: dict[int, bool] | None = None, login: str | None = LOGIN, **kwargs: object
) -> prs_mod.GithubView:
    comments = kwargs.pop("comments", None)
    if comments is None:
        comments = {pull.number: (_comment(pull.head_sha),) for pull in pulls}
    checks = kwargs.pop("checks", None)
    if checks is None:
        checks = {pull.head_sha: _green(pull.head_sha) for pull in pulls}
    return prs_mod.GithubView(
        repo=REPO,
        login=login,
        default_branch=kwargs.pop("default_branch", "main"),  # type: ignore[arg-type]
        pulls=pulls,
        comments=comments,  # type: ignore[arg-type]
        checks=checks,  # type: ignore[arg-type]
        queued={pull.number: False for pull in pulls} if queued is None else queued,
        **kwargs,  # type: ignore[arg-type]
    )


def _mq(**kwargs: object) -> prs_mod.MqSnapshot:
    return prs_mod.MqSnapshot(
        usable=kwargs.pop("usable", True),  # type: ignore[arg-type]
        keeper=kwargs.pop("keeper", {"queued": {}, "drops": {}}),  # type: ignore[arg-type]
        grants=kwargs.pop("grants", {}),  # type: ignore[arg-type]
        since=kwargs.pop("since", {}),  # type: ignore[arg-type]
    )


def _rows(*pulls: prs_mod.Pull, **kwargs: object) -> list[dict]:
    activity = kwargs.pop("activity", None)
    view_kwargs = {
        key: kwargs.pop(key)
        for key in ("queued", "login", "comments", "checks", "files", "queue_failed", "default_branch")
        if key in kwargs
    }
    return prs_mod.assemble_prs(
        _view(*pulls, **view_kwargs),
        _mq(**kwargs),
        now=NOW,
        activity=activity,  # type: ignore[arg-type]
    )


def test_current_head_approval_counts_and_an_older_head_does_not() -> None:
    assert lookup_verdict([_comment(SHA)], SHA, LOGIN).state == "APPROVED"
    approved = _rows(_pull(), since={f"42:{SHA}": "2026-10-09T08:00:00Z"})
    assert approved[0]["cf"] == {"verdict": "APPROVED", "at_head": True}
    assert approved[0]["stale_green"] is True
    assert approved[0]["minutes"] == 120

    stale_head = _rows(
        _pull(),
        comments={42: (_comment(OTHER),)},
        since={f"42:{SHA}": "2026-10-09T08:00:00Z"},
    )
    assert stale_head[0]["cf"] == {"verdict": "CF-stale", "at_head": False}
    assert stale_head[0]["stale_green"] is False
    assert stale_head[0]["minutes"] is None


def test_held_pr_is_not_stale_even_when_it_has_been_ready_for_hours() -> None:
    rows = _rows(
        _pull(labels=({"name": "hold"},)),
        since={f"42:{SHA}": "2026-10-09T08:00:00Z"},
    )
    assert rows[0]["keeper"] == {"hold": True, "reason": "hold"}
    assert rows[0]["stale_green"] is False
    assert rows[0]["minutes"] is None
    assert rows[0]["ci"] == "green"
    assert rows[0]["gate"] == "green"


def test_under_the_threshold_reports_minutes_without_the_flag() -> None:
    rows = _rows(_pull(), since={f"42:{SHA}": "2026-10-09T09:01:00Z"})
    assert rows[0]["stale_green"] is False
    assert rows[0]["minutes"] == 59
    assert rows[0]["ready_since"] == "2026-10-09T09:01:00Z"


def test_flake_deny_holds_and_a_grant_is_reported() -> None:
    key = f"42:{SHA}"
    denied = _rows(
        _pull(),
        keeper={"queued": {}, "drops": {key: 1}},
        grants={key: {"decision": "deny", "at": "2026-10-09T09:00:00Z"}},
        since={key: "2026-10-09T08:00:00Z"},
    )
    assert denied[0]["mq"] == "dropped"
    assert denied[0]["keeper"] == {"hold": True, "reason": "requeue-denied"}
    assert denied[0]["flake_grant"] == {"decision": "deny", "used": False, "at": "2026-10-09T09:00:00Z"}
    assert denied[0]["stale_green"] is False

    granted = _rows(
        _pull(),
        keeper={"queued": {}, "drops": {key: 1}, "requeued": {}},
        grants={key: {"decision": "grant"}},
    )
    assert granted[0]["keeper"] == {"hold": False, "reason": None}
    assert granted[0]["flake_grant"] == {"decision": "grant", "used": False, "at": None}
    assert granted[0]["mq"] == "dropped"

    spent = _rows(
        _pull(),
        keeper={"queued": {}, "drops": {key: 2}, "requeued": {key: "2026-10-09T09:30:00Z"}},
        grants={key: {"decision": "grant"}},
    )
    assert spent[0]["keeper"]["reason"] == (
        "RECOVERY_ALLOWANCE_SPENT: first=re-enqueue (legacy) at=2026-10-09T09:30:00Z run=unknown"
    )
    assert spent[0]["flake_grant"]["used"] is True
    assert spent[0]["flake_grant"]["at"] == "2026-10-09T09:30:00Z"


def test_ci_gate_is_separate_from_a_red_analyze_check() -> None:
    checks = {
        SHA: (
            _check("CI Gate"),
            _check("Analyze (python)", conclusion="failure"),
        )
    }
    rows = _rows(_pull(), checks=checks)
    assert rows[0]["ci"] == "red"
    assert rows[0]["gate"] == "green"


def test_lockfile_pr_reuses_the_keeper_codeql_rule() -> None:
    checks = (
        _check("CI Gate"),
        {
            "name": "CodeQL",
            "head_sha": SHA,
            "status": "completed",
            "conclusion": "neutral",
            "started_at": "2026-10-09T00:00:00Z",
            "app": {"id": keeper.CODEQL_APP_ID, "slug": keeper.CODEQL_APP},
        },
    )
    waiting = _rows(_pull(), checks={SHA: checks})
    assert waiting[0]["ci"] == "pending"
    ready = _rows(_pull(), checks={SHA: checks}, files={42: ({"filename": "uv.lock"},)})
    assert ready[0]["ci"] == "green"
    assert ready[0]["gate"] == "green"


def test_stacked_base_is_the_open_pr_on_the_base_branch() -> None:
    rows = _rows(
        _pull(number=6, sha=OTHER, head_ref="feature-a", base_ref="main"),
        _pull(number=7, head_ref="feature-b", base_ref="feature-a"),
        _pull(number=8, sha="c" * 40, head_ref="feature-c", base_ref="missing"),
        comments={
            6: (_comment(OTHER),),
            7: (_comment(SHA),),
            8: (_comment("c" * 40),),
        },
        checks={
            OTHER: _green(OTHER),
            SHA: _green(SHA),
            "c" * 40: _green("c" * 40),
        },
        queued={6: True, 7: False, 8: False},
    )
    by_number = {row["number"]: row for row in rows}
    assert by_number[6]["stacked_base"] is None
    assert by_number[6]["mq"] == "queued"
    assert by_number[7]["stacked_base"] == {"number": 6, "ref": "feature-a", "state": "open", "mq": "queued"}
    assert by_number[8]["stacked_base"] == {"number": None, "ref": "missing", "state": None, "mq": None}


def test_epic_and_state_filters() -> None:
    rows = _rows(
        _pull(number=1, sha="d" * 40, body="Closes #123", epics=("123",)),
        _pull(number=2, sha="e" * 40, labels=({"name": "hold"},), epics=("99",)),
        comments={1: (_comment("d" * 40),), 2: (_comment("e" * 40),)},
        checks={"d" * 40: _green("d" * 40), "e" * 40: (_check("CI Gate", "e" * 40, conclusion="failure"),)},
    )
    assert [row["number"] for row in prs_mod.filter_prs(rows, epic="epic:123")] == [1]
    assert [row["number"] for row in prs_mod.filter_prs(rows, epic="99")] == [2]
    assert [row["number"] for row in prs_mod.filter_prs(rows, state="held")] == [2]
    assert [row["number"] for row in prs_mod.filter_prs(rows, state="red")] == [2]
    assert prs_mod.filter_prs(rows, state="nope") == []
    assert [row["number"] for row in prs_mod.filter_prs(rows, epic="123", state="open")] == [1]


def _rest_pull(number: int, sha: str, head: str, base: str) -> dict:
    return {
        "number": number,
        "title": f"Change {number}",
        "draft": False,
        "body": "",
        "labels": [],
        "mergeable_state": "clean",
        "head": {"sha": sha, "ref": head},
        "base": {"sha": "f" * 40, "ref": base},
    }


class _Result:
    def __init__(self, value: object, headers: dict[str, str] | None = None, error: str | None = None) -> None:
        self.value = value
        self.headers = headers or {}
        self.error = error
        self.stale = False
        self.age_seconds = 0
        self.status = 200 if error is None else 500


class _Client:
    def __init__(self, pages: list[list[dict]]) -> None:
        self.pages = pages
        self.calls: list[tuple[str, str]] = []

    def request(
        self,
        method: str,
        endpoint: str,
        payload: dict | None = None,
        timeout: float = 20,
        allow_stale: bool = False,
        **_kwargs: object,
    ) -> _Result:
        path = endpoint.split("?", 1)[0]
        self.calls.append((method, path))
        if method == "POST":
            assert payload is not None
            assert "isInMergeQueue" in payload["query"]
            assert "statusCheckRollup" not in payload["query"]
            return _Result(
                {
                    "data": {
                        "repository": {
                            "pullRequests": {
                                "pageInfo": {"hasNextPage": False, "endCursor": None},
                                "nodes": [
                                    {"number": 7, "isInMergeQueue": False},
                                    {"number": 8, "isInMergeQueue": True},
                                ],
                            }
                        }
                    }
                }
            )
        if path.endswith("/pulls"):
            page = self.pages.pop(0)
            headers = {}
            if self.pages:
                headers["link"] = '<repos/example/repo/pulls?page=2>; rel="next"'
            return _Result(page, headers)
        if path == "user":
            return _Result({"login": LOGIN})
        if path == f"repos/{REPO}":
            return _Result({"default_branch": "main"})
        if path.endswith("/comments"):
            return _Result([])
        if path.endswith("/check-runs"):
            sha = path.split("/commits/", 1)[1].split("/", 1)[0]
            runs = list(_green(sha))
            return _Result({"total_count": len(runs), "check_runs": runs})
        if "/commits/" in path:
            return _Result({"commit": {"committer": {"date": "2026-10-09T07:30:00Z"}}})
        raise AssertionError(path)


def test_loader_uses_rest_for_pulls_and_graphql_only_for_the_queue() -> None:
    fake = _Client(
        [
            [_rest_pull(7, SHA, "feature", "main")],
            [_rest_pull(8, OTHER, "next", "main")],
        ]
    )
    view = prs_mod._fetch_github(REPO, fake)
    methods = [method for method, _path in fake.calls]
    assert methods.count("POST") == 1
    assert "GET" in methods
    assert {pull.number for pull in view.pulls} == {7, 8}
    assert view.queued == {7: False, 8: True}
    assert view.failed is False
    assert view.default_branch == "main"
    assert {pull.commit_at for pull in view.pulls} == {"2026-10-09T07:30:00Z"}
    rows = prs_mod.assemble_prs(view, _mq(since={}), now=NOW)
    assert {row["number"] for row in rows} == {7, 8}
    assert all(row["ci"] == "green" for row in rows)


def test_github_cache_reuses_a_short_lived_read(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[str] = []
    view = _view(_pull())

    def fake(repo: str, _client: object) -> prs_mod.GithubView:
        calls.append(repo)
        return view

    monkeypatch.setattr(prs_mod, "_fetch_github", fake)
    monkeypatch.setattr(prs_mod, "_client", lambda: object())
    assert prs_mod.load_github_view(REPO, now=0, ttl=30) is not None
    assert prs_mod.load_github_view(REPO, now=10, ttl=30).age_s == 10
    assert calls == [REPO]
    prs_mod.load_github_view(REPO, now=30, ttl=30)
    assert calls == [REPO, REPO]


class _BlindIdentity(_Client):
    def request(
        self,
        method: str,
        endpoint: str,
        payload: dict | None = None,
        timeout: float = 20,
        allow_stale: bool = False,
        **kwargs: object,
    ) -> _Result:
        path = endpoint.split("?", 1)[0]
        if path in {"user", f"repos/{REPO}"}:
            return _Result(None, error="denied")
        return super().request(method, endpoint, payload, timeout, allow_stale, **kwargs)


def test_failed_identity_and_repository_reads_are_unavailable_and_not_cached(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls: list[int] = []

    def factory() -> _BlindIdentity:
        calls.append(1)
        return _BlindIdentity([[_rest_pull(7, SHA, "feature", "topic")]])

    monkeypatch.setattr(prs_mod, "_client", factory)
    monkeypatch.setenv("FLEET_GITHUB_REPO", REPO)
    monkeypatch.delenv("FLEET_MQ_STATE_DIR", raising=False)
    first_rows, first_sources, _events = prs_mod.collect_pipeline()
    assert first_sources[0].status == "unavailable"
    assert [row["number"] for row in first_rows] == [7]
    assert first_rows[0]["ci"] == "green"
    assert first_rows[0]["cf"] == {"verdict": "unknown", "at_head": False}
    assert first_rows[0]["stacked_base"] is None
    prs_mod.collect_pipeline()
    assert calls == [1, 1]


def test_a_failed_read_is_not_cached(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[int] = []
    failed = _view(_pull(), queue_failed=True, failed=True)

    def fake(_repo: str, _client: object) -> prs_mod.GithubView:
        calls.append(1)
        return failed

    monkeypatch.setattr(prs_mod, "_fetch_github", fake)
    monkeypatch.setattr(prs_mod, "_client", lambda: object())
    prs_mod.load_github_view(REPO, now=0, ttl=30)
    prs_mod.load_github_view(REPO, now=1, ttl=30)
    assert calls == [1, 1]


def _write_state(
    tmp_path,
    *,
    keeper_name: str = "keeper.json",
    keeper_body: dict | None = None,
    requeue: dict | None = None,
    approved: dict | None = None,
) -> None:
    if keeper_body is not None:
        (tmp_path / keeper_name).write_text(json.dumps(keeper_body), encoding="utf-8")
    if requeue is not None:
        (tmp_path / "requeue.json").write_text(json.dumps({"version": 1, "requeue": requeue}), encoding="utf-8")
    if approved is not None:
        (tmp_path / "stale-approved.json").write_text(
            json.dumps({"version": 1, "approved": approved}), encoding="utf-8"
        )


def test_state_dir_supplies_the_gate_and_the_ready_time(tmp_path, monkeypatch: pytest.MonkeyPatch) -> None:
    key = f"42:{SHA}"
    moment = prs_mod.utc_now()
    since = (moment - timedelta(minutes=90)).strftime("%Y-%m-%dT%H:%M:%SZ")
    _write_state(
        tmp_path,
        keeper_name="merge_queue_keeper.json",
        keeper_body={"queued": {}, "drops": {key: 1}},
        requeue={key: {"decision": "deny"}},
        approved={key: {"since": since}},
    )
    monkeypatch.setenv("FLEET_GITHUB_REPO", REPO)
    monkeypatch.setenv("FLEET_MQ_STATE_DIR", str(tmp_path))
    monkeypatch.setattr(prs_mod, "load_github_view", lambda repo, **_kwargs: _view(_pull()))

    rows, sources, _events = prs_mod.collect_pipeline()
    assert rows[0]["keeper"]["reason"] == "requeue-denied"
    assert rows[0]["flake_grant"]["decision"] == "deny"
    assert rows[0]["stale_green"] is False
    assert sources[0].status == "ok"
    assert sources[1].status == "ok"
    assert tmp_path.name not in json.dumps(rows)
    assert "mq-state" not in json.dumps({"sources": [item.as_dict() for item in sources]})


def test_old_keeper_file_is_stale_and_a_missing_dir_is_unavailable(tmp_path) -> None:
    path = tmp_path / "keeper.json"
    path.write_text(json.dumps({"queued": {}, "drops": {}}), encoding="utf-8")
    old = time.time() - 1000
    os.utime(path, (old, old))
    report, snapshot = prs_mod.read_mq_state({"FLEET_MQ_STATE_DIR": str(tmp_path)})
    assert report.status == "stale"
    assert report.age_s is not None and report.age_s > prs_mod.MQ_FRESH_S
    assert snapshot.usable is True

    missing, empty = prs_mod.read_mq_state({"FLEET_MQ_STATE_DIR": str(tmp_path / "absent")})
    assert missing.status == "unavailable"
    assert empty.usable is False
    unset, _snapshot = prs_mod.read_mq_state({})
    assert unset.status == "not_configured"


def test_missing_keeper_state_is_unavailable_and_hold_stays_unknown(tmp_path) -> None:
    report, snapshot = prs_mod.read_mq_state({"FLEET_MQ_STATE_DIR": str(tmp_path)})
    assert report.status == "unavailable"
    assert snapshot.usable is False
    ready = prs_mod.assemble_prs(
        _view(_pull()),
        snapshot,
        now=NOW,
    )
    assert ready[0]["keeper"] == {"hold": None, "reason": None}
    assert ready[0]["stale_green"] is False
    assert ready[0]["minutes"] is None
    held = prs_mod.assemble_prs(
        _view(_pull(labels=({"name": "hold"},))),
        snapshot,
        now=NOW,
    )
    assert held[0]["keeper"] == {"hold": True, "reason": "hold"}

    gate_only = tmp_path / "gate-only"
    gate_only.mkdir()
    (gate_only / "requeue.json").write_text(json.dumps({"version": 1, "requeue": {}}), encoding="utf-8")
    again, empty = prs_mod.read_mq_state({"FLEET_MQ_STATE_DIR": str(gate_only)})
    assert again.status == "unavailable"
    assert empty.usable is False


def test_github_errors_stay_http_200(monkeypatch: pytest.MonkeyPatch, tmp_path) -> None:
    monkeypatch.setenv("FLEET_GITHUB_REPO", REPO)
    monkeypatch.setenv("FLEET_MQ_STATE_DIR", str(tmp_path))

    def explode(_repo: str, **_kwargs: object) -> prs_mod.GithubView:
        raise prs_mod.GithubReadError("no-such-host:9")

    monkeypatch.setattr(prs_mod, "load_github_view", explode)
    response = client.get("/api/fleet/v1/prs")
    assert response.status_code == 200
    body = response.json()
    assert body["data"] == {"prs": []}
    github = next(item for item in body["sources"] if item["name"] == "github")
    assert github["status"] == "unavailable"
    assert github["error"] == "unavailable"
    assert "no-such-host" not in response.text
    assert tmp_path.name not in response.text

    def crash(_repo: str, **_kwargs: object) -> prs_mod.GithubView:
        raise RuntimeError("no-such-host:9")

    monkeypatch.setattr(prs_mod, "load_github_view", crash)
    again = client.get("/api/fleet/v1/prs/42")
    assert again.status_code == 200
    assert again.json()["data"] == {"pr": None}
    assert "no-such-host" not in again.text


def test_route_filters_and_schema(monkeypatch: pytest.MonkeyPatch, tmp_path) -> None:
    key = f"42:{SHA}"
    moment = prs_mod.utc_now()
    since = (moment - timedelta(minutes=90)).strftime("%Y-%m-%dT%H:%M:%SZ")
    _write_state(tmp_path, keeper_body={"queued": {}, "drops": {}}, approved={key: {"since": since}})
    monkeypatch.setenv("FLEET_GITHUB_REPO", REPO)
    monkeypatch.setenv("FLEET_MQ_STATE_DIR", str(tmp_path))
    monkeypatch.setenv("FLEET_PR_STALE_MIN", "60")
    held = _pull(number=7, sha=OTHER, title="[hold] wait", labels=({"name": "hold"},), epics=("12",))
    ready = _pull(epics=("12",))
    monkeypatch.setattr(
        prs_mod,
        "load_github_view",
        lambda repo, **_kwargs: _view(
            ready,
            held,
            comments={42: (_comment(SHA),), 7: (_comment(OTHER),)},
            checks={SHA: _green(SHA), OTHER: _green(OTHER)},
            queued={42: False, 7: False},
        ),
    )

    listed = client.get("/api/fleet/v1/prs", params={"epic": "12", "state": "stale"})
    assert listed.status_code == 200
    payload = listed.json()
    assert [row["number"] for row in payload["data"]["prs"]] == [42]
    assert payload["data"]["prs"][0]["stale_green"] is True
    assert payload["data"]["prs"][0]["minutes"] >= 89
    assert payload["schema"] == "fleet.v1.prs"
    assert tmp_path.name not in listed.text

    schema = client.get("/api/fleet/v1/schema")
    documents = schema.json()["data"]["endpoints"]
    Draft202012Validator(documents["fleet.v1.prs"]).validate(payload)
    detail = client.get("/api/fleet/v1/prs/42")
    assert detail.status_code == 200
    assert detail.json()["data"]["pr"]["head_sha"] == SHA
    Draft202012Validator(documents["fleet.v1.pr"]).validate(detail.json())
    missing = client.get("/api/fleet/v1/prs/99")
    assert missing.status_code == 200
    assert missing.json()["data"]["pr"] is None
    Draft202012Validator(documents["fleet.v1.pr"]).validate(missing.json())


def test_unset_repository_is_not_configured(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("FLEET_GITHUB_REPO", raising=False)
    monkeypatch.delenv("GH_REPO", raising=False)
    monkeypatch.delenv("GITHUB_REPOSITORY", raising=False)
    monkeypatch.delenv("FLEET_MQ_STATE_DIR", raising=False)
    response = client.get("/api/fleet/v1/prs")
    assert response.status_code == 200
    by_name = {item["name"]: item for item in response.json()["sources"]}
    assert by_name["github"]["status"] == "not_configured"
    assert by_name["mq_state"]["status"] == "not_configured"
    assert by_name["stale_prs"]["status"] == "not_configured"
    assert response.json()["data"]["prs"] == []


def _note(**kwargs: object) -> activity_mod.PrActivity:
    return activity_mod.PrActivity(**kwargs)  # type: ignore[arg-type]


def test_hours_idle_uses_the_latest_commit_verdict_or_merge_event() -> None:
    quiet = _rows(_pull(), comments={42: ()})
    assert quiet[0]["hours_idle"] is None
    assert quiet[0]["idle_24h"] is False
    assert quiet[0]["idle_48h"] is False

    from_verdict = _rows(_pull(commit_at="2026-10-08T10:00:00Z"))
    assert from_verdict[0]["hours_idle"] == 2.0
    assert from_verdict[0]["idle_24h"] is False

    day = _rows(_pull(commit_at="2026-10-08T10:00:00Z"), comments={42: ()})
    assert day[0]["hours_idle"] == 24.0
    assert day[0]["idle_24h"] is True
    assert day[0]["idle_48h"] is False

    two_days = _rows(_pull(commit_at="2026-10-07T10:00:00Z"), comments={42: ()})
    assert two_days[0]["hours_idle"] == 48.0
    assert two_days[0]["idle_48h"] is True

    merged = _rows(
        _pull(commit_at="2026-10-07T10:00:00Z"),
        activity={42: _note(merge_event_at=datetime(2026, 10, 9, 9, 0, tzinfo=UTC))},
    )
    assert merged[0]["hours_idle"] == 1.0
    assert merged[0]["idle_24h"] is False


def test_blocker_precedence_and_a_stacked_pr_is_never_ready() -> None:
    red = (
        _check("CI Gate", conclusion="failure"),
        _check("Analyze (python)", conclusion="failure"),
    )
    stacked = _rows(
        _pull(base_ref="feature-a", merge_state="DIRTY", head_ref="cursor/child"),
        checks={SHA: red},
        comments={42: (_comment(SHA, verdict="CHANGES_REQUESTED"),)},
        since={f"42:{SHA}": "2026-10-09T08:00:00Z"},
    )
    assert stacked[0]["blocker"] == {"kind": "stacked_base", "number": None, "state": "unmerged"}
    assert stacked[0]["stale_green"] is False
    assert stacked[0]["minutes"] is None
    assert stacked[0]["ready_since"] is None
    assert stacked[0]["owner_lane"] == "cursor"

    conflict = _rows(_pull(merge_state="DIRTY"), checks={SHA: red})
    assert conflict[0]["blocker"] == {"kind": "conflict"}

    failing = _rows(_pull(), checks={SHA: red})
    assert failing[0]["blocker"] == {"kind": "failing_check", "checks": ["Analyze (python)", "CI Gate"]}

    changes = _rows(_pull(), comments={42: (_comment(SHA, verdict="CHANGES_REQUESTED"),)})
    assert changes[0]["blocker"] == {"kind": "cf_changes"}
    assert _rows(_pull())[0]["blocker"] == {"kind": "none"}

    closed = _rows(
        _pull(base_ref="feature-a", head_ref="cursor/child"),
        activity={42: _note(base_number=6, base_state="closed")},
        since={f"42:{SHA}": "2026-10-09T08:00:00Z"},
    )
    assert closed[0]["blocker"] == {"kind": "stacked_base", "number": 6, "state": "closed"}
    assert closed[0]["stale_green"] is False

    ready = _rows(_pull(head_ref="cursor/feature"), since={f"42:{SHA}": "2026-10-09T08:00:00Z"})
    assert ready[0]["blocker"] == {"kind": "none"}
    assert ready[0]["stale_green"] is True
    assert ready[0]["owner_lane"] == "cursor"


def test_owner_lane_prefers_the_recorded_lane() -> None:
    rows = _rows(
        _pull(head_ref="cursor/feature"),
        activity={42: _note(owner_lane="codex")},
    )
    assert rows[0]["owner_lane"] == "codex"
    plain = _rows(_pull(head_ref="feature"))
    assert plain[0]["owner_lane"] is None


def test_open_base_pr_is_the_stacked_blocker() -> None:
    rows = _rows(
        _pull(number=6, sha=OTHER, head_ref="feature-a", base_ref="main"),
        _pull(number=7, head_ref="cursor/feature-b", base_ref="feature-a"),
        comments={6: (_comment(OTHER),), 7: (_comment(SHA),)},
        checks={OTHER: _green(OTHER), SHA: _green(SHA)},
        since={f"7:{SHA}": "2026-10-09T08:00:00Z"},
    )
    child = next(row for row in rows if row["number"] == 7)
    assert child["blocker"] == {"kind": "stacked_base", "number": 6, "state": "open"}
    assert child["stacked_base"]["number"] == 6
    assert child["stale_green"] is False
    assert child["owner_lane"] == "cursor"
    parent = next(row for row in rows if row["number"] == 6)
    assert parent["blocker"] == {"kind": "none"}


@pytest.mark.parametrize("board_signals", [False, True])
def test_now_lists_idle_pull_requests_and_stats_cover_fourteen_days(
    tmp_path, monkeypatch: pytest.MonkeyPatch, board_signals: bool,
) -> None:
    from scripts.api.fleet_board import router as router_mod
    from scripts.api.fleet_board.sources import report
    from scripts.api.fleet_board.view import Board

    board_alert = {
        "severity": "bad", "kind": "dead_driver", "title": "Driver stopped",
        "summary": "process is not alive", "target": {"type": "epic", "id": "alpha"},
    }
    if board_signals:
        monkeypatch.setattr(
            router_mod, "load_board",
            lambda: Board((report("roster_snapshot", "ok"),), [], [], [board_alert]),
        )
    measurements = [
        {"name": name, "value": 7, "status": "ok"}
        for name in ("disk_pct", "memory_pct", "drivers_live", "probe_status")
    ]
    if board_signals:
        monkeypatch.setattr(
            router_mod, "load_stats", lambda: ({"stats": measurements}, (report("stats", "ok"),)),
        )
    fresh = _pull(number=1, sha="d" * 40, head_ref="cursor/fresh", commit_at="2026-10-09T09:00:00Z")
    day = _pull(number=2, sha="e" * 40, head_ref="codex/day", commit_at="2026-10-08T10:00:00Z")
    older = _pull(number=3, sha="f" * 40, head_ref="codex/older", commit_at="2026-10-07T09:00:00Z")
    record = {
        "version": 1,
        "activity": {"3": {"merge_event_at": "2026-10-07T10:00:00Z", "owner_lane": "agy"}},
        "throughput": [
            {"date": "2026-10-09", "repo": REPO, "owner_lane": "cursor", "opened": 2, "merged": 1},
            {"date": "2026-10-08", "repo": REPO, "owner_lane": "codex", "opened": 1, "merged": 0},
            {"date": "2026-09-01", "repo": REPO, "owner_lane": "cursor", "opened": 9, "merged": 9},
            {"date": "2026-10-09", "repo": "example/other", "owner_lane": None, "opened": 1, "merged": 1},
        ],
    }
    path = tmp_path / "record.json"
    path.write_text(json.dumps(record), encoding="utf-8")
    monkeypatch.setenv("FLEET_STALE_PR_STATE", str(path))
    monkeypatch.setenv("FLEET_GITHUB_REPO", REPO)
    monkeypatch.delenv("FLEET_MQ_STATE_DIR", raising=False)
    monkeypatch.setattr(prs_mod, "utc_now", lambda: NOW)
    monkeypatch.setattr(
        prs_mod,
        "load_github_view",
        lambda repo, **_kwargs: _view(
            fresh,
            day,
            older,
            comments={1: (), 2: (), 3: ()},
            checks={"d" * 40: _green("d" * 40), "e" * 40: _green("e" * 40), "f" * 40: _green("f" * 40)},
            queued={1: False, 2: False, 3: False},
        ),
    )

    now = client.get("/api/fleet/v1/now")
    assert now.status_code == 200
    attention = now.json()["data"]["attention"]
    if board_signals:
        assert attention[0] == board_alert
        attention = attention[1:]
    assert [row["number"] for row in attention] == [3, 2]
    if board_signals:
        assert {row["name"] for row in now.json()["sources"]} == {
            "roster_snapshot", "github", "mq_state", "stale_prs",
        }
    assert attention[0]["idle_48h"] is True
    assert attention[0]["owner_lane"] == "agy"
    assert attention[1]["idle_48h"] is False
    assert attention[1]["hours_idle"] == 24.0
    assert path.name not in now.text

    stats = client.get("/api/fleet/v1/stats")
    assert stats.status_code == 200
    body = stats.json()
    assert body["schema"] == "fleet.v1.stats"
    if board_signals:
        assert body["data"]["stats"] == measurements
    assert {row["name"] for row in body["sources"]} == {"stats", "github", "mq_state", "stale_prs"}
    assert body["data"]["window_days"] == 14
    by_repo = {row["repo"]: row for row in body["data"]["by_repo"]}
    assert set(by_repo) == {REPO, "example/other"}
    assert by_repo[REPO]["backlog"] == 3
    assert len(by_repo[REPO]["days"]) == 14
    assert by_repo[REPO]["days"][-1] == {"date": "2026-10-09", "opened": 2, "merged": 1}
    assert by_repo[REPO]["days"][-2] == {"date": "2026-10-08", "opened": 1, "merged": 0}
    assert by_repo[REPO]["days"][0]["date"] == "2026-09-26"
    assert sum(day["opened"] for day in by_repo[REPO]["days"]) == 3
    by_lane = {row["owner_lane"]: row for row in body["data"]["by_lane"]}
    assert by_lane["cursor"]["backlog"] == 1
    assert by_lane["codex"]["backlog"] == 1
    assert by_lane["agy"]["backlog"] == 1
    assert by_lane[None]["backlog"] == 0
    assert by_lane[None]["days"][-1] == {"date": "2026-10-09", "opened": 1, "merged": 1}
    assert "2026-09-01" not in stats.text

    schema = client.get("/api/fleet/v1/schema")
    documents = schema.json()["data"]["endpoints"]
    Draft202012Validator(documents["fleet.v1.now"]).validate(now.json())
    Draft202012Validator(documents["fleet.v1.stats"]).validate(body)
    listed = client.get("/api/fleet/v1/prs")
    Draft202012Validator(documents["fleet.v1.prs"]).validate(listed.json())


def test_missing_or_malformed_state_record_degrades(tmp_path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("FLEET_GITHUB_REPO", REPO)
    monkeypatch.delenv("FLEET_MQ_STATE_DIR", raising=False)
    monkeypatch.setattr(prs_mod, "utc_now", lambda: NOW)
    monkeypatch.setattr(
        prs_mod,
        "load_github_view",
        lambda repo, **_kwargs: _view(
            _pull(head_ref="cursor/feature", commit_at="2026-10-08T10:00:00Z"),
            comments={42: ()},
        ),
    )

    missing = client.get("/api/fleet/v1/stats")
    assert missing.status_code == 200
    stale = next(item for item in missing.json()["sources"] if item["name"] == "stale_prs")
    assert stale["status"] == "not_configured"
    assert missing.json()["data"]["by_repo"][0]["backlog"] == 1
    assert missing.json()["data"]["by_repo"][0]["days"][-1]["opened"] == 0

    monkeypatch.setenv("FLEET_STALE_PR_STATE", str(tmp_path / "absent.json"))
    absent = client.get("/api/fleet/v1/stats")
    assert absent.status_code == 200
    absent_source = next(item for item in absent.json()["sources"] if item["name"] == "stale_prs")
    assert absent_source["status"] == "unavailable"
    assert absent.json()["data"]["by_repo"][0]["backlog"] == 1
    assert tmp_path.name not in absent.text

    bad = tmp_path / "record.json"
    bad.write_text('{"version": 1, "activity": {"nope": {}}}', encoding="utf-8")
    monkeypatch.setenv("FLEET_STALE_PR_STATE", str(bad))
    broken = client.get("/api/fleet/v1/prs")
    assert broken.status_code == 200
    source = next(item for item in broken.json()["sources"] if item["name"] == "stale_prs")
    assert source == {"name": "stale_prs", "status": "unavailable", "age_s": None, "error": "unavailable"}
    assert broken.json()["data"]["prs"][0]["hours_idle"] == 24.0
    assert broken.json()["data"]["prs"][0]["owner_lane"] == "cursor"
    assert bad.name not in broken.text

    old = NOW.timestamp() - 1000
    good = {
        "version": 1,
        "throughput": [
            {"date": "2026-10-09", "repo": REPO, "owner_lane": "cursor", "opened": 4, "merged": 2}
        ],
    }
    bad.write_text(json.dumps(good), encoding="utf-8")
    os.utime(bad, (old, old))
    aged = client.get("/api/fleet/v1/stats")
    aged_source = next(item for item in aged.json()["sources"] if item["name"] == "stale_prs")
    assert aged_source["status"] == "stale"
    assert aged_source["age_s"] > activity_mod.STALE_PR_FRESH_S
    assert aged.json()["data"]["by_lane"][0]["days"][-1]["merged"] == 2
    assert bad.name not in aged.text


@pytest.mark.parametrize("keeper_available", [False, True])
def test_idle_and_throughput_preserve_keeper_readiness(tmp_path, monkeypatch: pytest.MonkeyPatch, keeper_available: bool) -> None:
    key = f"42:{SHA}"
    state = tmp_path / "queue"
    state.mkdir()
    _write_state(state, keeper_body={"queued": {}, "drops": {}}, approved={key: {"since": "2026-10-09T08:00:00Z"}})
    if not keeper_available:
        # Keep the ready timestamp while omitting the keeper authority.
        (state / "keeper.json").rename(state / "unused.json")
    activity = tmp_path / "activity.json"
    activity.write_text(json.dumps({
        "version": 1,
        "throughput": [{"date": "2026-10-09", "repo": REPO, "owner_lane": "codex", "opened": 2, "merged": 1}],
    }), encoding="utf-8")
    monkeypatch.setenv("FLEET_GITHUB_REPO", REPO)
    monkeypatch.setenv("FLEET_MQ_STATE_DIR", str(state))
    monkeypatch.setenv("FLEET_STALE_PR_STATE", str(activity))
    monkeypatch.setattr(prs_mod, "utc_now", lambda: NOW)
    monkeypatch.setattr(prs_mod, "load_github_view", lambda *_args, **_kwargs: _view(
        _pull(head_ref="codex/topic", commit_at="2026-10-07T10:00:00Z"),
        comments={42: ()},
    ))
    rows, sources, events = prs_mod.collect_pipeline(now=NOW)
    row = rows[0]
    assert row["hours_idle"] == 48.0
    assert row["idle_48h"] is True
    assert row["keeper"]["hold"] is (False if keeper_available else None)
    assert row["stale_green"] is False
    assert sources[1].status == ("ok" if keeper_available else "unavailable")
    assert activity_mod.attention_rows(rows)[0]["number"] == 42
    stats = activity_mod.build_stats(rows, events, now=NOW)
    assert stats["by_repo"][0]["backlog"] == 1
    assert stats["by_repo"][0]["days"][-1]["merged"] == 1

    approved = prs_mod.assemble_prs(_view(_pull()), prs_mod.read_mq_state(now=NOW)[1], now=NOW)
    assert approved[0]["stale_green"] is keeper_available
    assert approved[0]["minutes"] == (120 if keeper_available else None)
