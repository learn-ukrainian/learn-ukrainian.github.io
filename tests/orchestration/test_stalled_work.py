"""Stalled-work behavior with fixture task records, fake Git and fake GitHub."""

from __future__ import annotations

import argparse
import copy
import json
import subprocess
from datetime import UTC, datetime, timedelta
from types import SimpleNamespace

import pytest

from scripts.fleet_comms.authority import AuthorityService
from scripts.orchestration import stalled_work as mod
from scripts.review.record_cf_verdict import build_comment

NOW = datetime(2026, 10, 20, 18, tzinfo=UTC)
SLUG = "example/public"
BASE, LOCAL, REMOTE = "a" * 40, "b" * 40, "c" * 40


@pytest.fixture
def host(tmp_path, monkeypatch):
    tasks = tmp_path / "tasks"
    tasks.mkdir()
    target = mod.stale.FetchTarget("fixture", "https://github.com/example/public.git")
    facts = mod.stale.RepoFacts(SLUG, tmp_path, target, {"main": BASE}, {})
    prs, comments, calls, closed = [], {}, [], []
    unpublished = {LOCAL}
    merged = {BASE}

    def git(args, **kwargs):
        calls.append(args)
        assert args[0] in {"rev-list", "rev-parse"}, args
        if args[0] == "rev-parse":
            output = LOCAL
        elif "--count" in args:
            output = "1"
        elif args[2] in merged:
            output = ""
        elif any(arg.startswith("--glob=") for arg in args):
            output = args[2] if args[2] in unpublished else ""
        else:
            output = args[2]
        return subprocess.CompletedProcess(["git", *args], 0, output, "")

    def gh(args):
        if getattr(args, "verb", None) == "read-identity":
            return json.dumps({"login": "fleet"})
        if getattr(args, "verb", None) == "read-comments":
            return json.dumps([comments.get(args.fields["number"], [])])
        assert args[:3] == ["gh", "pr", "list"]
        return json.dumps(prs)

    monkeypatch.setattr(mod.stale, "collect_repo_facts", lambda *a: facts)
    monkeypatch.setattr(mod.stale, "fleet_fetch_target", lambda *a: target)
    monkeypatch.setattr(mod.stale, "_git", git)
    monkeypatch.setattr(mod.stale, "gh_pull_page", lambda slug, page: closed if page == 1 else [])

    def record(task="one", **changes):
        data = {
            "task_id": task,
            "initiator": "codex-devops",
            "agent": "claude",
            "repository": SLUG,
            "status": "needs_finalize",
            "worktree_branch": "codex/fix",
            "worktree_path": str(tmp_path / "missing"),
            "finished_at": (NOW - timedelta(hours=3)).isoformat(),
            "worktree_base_sha": BASE,
            "final_branch_head_commit": LOCAL,
            "commits_ahead": 1,
        }
        data.update(changes)
        path = tasks / f"{task}.json"
        path.write_text(json.dumps(data))
        return path

    def scan():
        return mod.scan(
            tasks, {SLUG: tmp_path}, now=NOW, adapter_factory=lambda path: mod.GitHubAdapter(path, runner=gh)
        )

    return SimpleNamespace(**locals())


def pr(host, sha=REMOTE):
    host.prs.append({"number": 42, "headRefName": "codex/fix", "headRefOid": sha})
    return host.prs[-1]


def rejection(host, *, hours=3, sha=REMOTE, verdict="CHANGES_REQUESTED", login="fleet", mode="cross_family"):
    stamp = (NOW - timedelta(hours=hours)).isoformat(timespec="microseconds")
    body = build_comment(
        sha=sha,
        task_id=f"review-{hours}-{verdict}",
        started=stamp,
        verdict=verdict,
        model="claude-opus-5-5",
        family="anthropic",
        reply="VERDICT: " + verdict,
        review_mode=mode,
    )
    host.comments.setdefault(42, []).append(
        {
            "body": body,
            "user": {"login": login},
            "author_association": "OWNER",
            "created_at": stamp,
            "updated_at": stamp,
        }
    )


@pytest.mark.parametrize("status", ["needs_finalize", "failed", "timeout", "timed_out", "timed-out"])
def test_unpushed_commit_is_returned_to_dispatch_owner(host, status):
    path = host.record(status=status)
    before = path.read_bytes()
    host.facts.local_branches["codex/fix"] = LOCAL
    report = host.scan()
    assert report["errors"] == []
    assert report["rows"] == [
        {
            "task_id": "one",
            "lane": "codex-devops",
            "repository": SLUG,
            "kind": "unpushed",
            "commit": LOCAL,
            "pr": None,
            "since": "2026-10-20T15:00:00+00:00",
            "age_hours": 3.0,
        }
    ]
    assert path.read_bytes() == before


def test_detached_worktree_commit_is_detected(host):
    tree = host.tmp_path / "tree"
    tree.mkdir()
    (tree / ".git").write_text("fixture")
    host.record(worktree_path=str(tree))
    # The classifier's dirtiness probe is separate from commit reachability.
    host.monkeypatch.setattr(mod.stale.worktree_claims, "worktree_is_dirty", lambda path: False)
    assert host.scan()["rows"][0]["commit"] == LOCAL


def test_pushed_dispatch_without_pr_is_detected(host):
    host.record(status="done", final_branch_head_commit=REMOTE)
    host.facts.remote_heads["codex/fix"] = REMOTE
    assert host.scan()["rows"][0]["kind"] == "no_open_pr"


def test_squash_merged_dispatch_is_not_stalled(host):
    host.record(status="done", final_branch_head_commit=REMOTE)
    host.facts.remote_heads["codex/fix"] = REMOTE
    host.closed.append(
        {
            "number": 41,
            "merged_at": NOW.isoformat(),
            "updated_at": NOW.isoformat(),
            "merge_commit_sha": BASE,
            "head": {"ref": "codex/fix", "sha": REMOTE, "repo": {"full_name": SLUG}},
        }
    )
    assert host.scan()["rows"] == []


def test_incomplete_merged_pr_evidence_is_unknown(host):
    host.record(status="done")
    host.facts.remote_heads["codex/fix"] = REMOTE

    def unavailable(*args):
        raise RuntimeError("unavailable")

    host.monkeypatch.setattr(mod.stale, "gh_pull_page", unavailable)
    assert host.scan()["errors"] == [f"{SLUG}: merged PR evidence incomplete"]


@pytest.mark.parametrize("case", ["pr", "merged", "young", "old", "abandoned", "abandon_receipt", "review"])
def test_exclusions(host, case):
    changes = {"status": "done", "final_branch_head_commit": REMOTE}
    host.facts.remote_heads["codex/fix"] = REMOTE
    if case == "pr":
        pr(host)
    elif case == "merged":
        host.merged.add(REMOTE)
    elif case in {"young", "old"}:
        changes["finished_at"] = (NOW - timedelta(hours=1 if case == "young" else 14 * 24)).isoformat()
    elif case == "abandoned":
        changes["status"] = "terminal_abandon"
    elif case == "abandon_receipt":
        changes["worktree_abandon"] = {"schema": "terminal-abandon.v1", "disposition": "ABANDON"}
    elif case == "review":
        changes["review"] = True
    host.record(**changes)
    assert host.scan()["rows"] == []


def test_existing_remote_branch_can_still_hold_unpushed_local_work(host):
    host.record()
    host.facts.remote_heads["codex/fix"] = REMOTE
    host.facts.local_branches["codex/fix"] = LOCAL
    pr(host)
    assert host.scan()["rows"][0]["kind"] == "unpushed"


def test_renamed_local_branch_retains_recorded_work(host):
    host.record()
    host.facts.local_branches["codex/renamed"] = LOCAL
    assert host.scan()["rows"][0]["commit"] == LOCAL


def test_rejection_of_current_head_without_live_task_is_detected(host):
    host.record(status="done")
    pr(host)
    rejection(host)
    report = host.scan()
    assert report["errors"] == []
    assert report["rows"][0]["kind"] == "changes_requested"
    assert report["rows"][0]["pr"] == 42
    assert report["rows"][0]["age_hours"] == 3


@pytest.mark.parametrize(
    "case",
    [
        "new_head",
        "new_approval",
        "young",
        "live_branch",
        "live_pr",
        "live_review",
        "untrusted",
        "red_team",
        "recent_repair",
    ],
)
def test_rejection_exclusions(host, case):
    host.record(status="done")
    p = pr(host)
    rejection(
        host,
        hours=1 if case == "young" else 3,
        login="stranger" if case == "untrusted" else "fleet",
        mode="red_team" if case == "red_team" else "cross_family",
    )
    if case == "new_head":
        p["headRefOid"] = LOCAL
    elif case == "new_approval":
        rejection(host, hours=1, verdict="APPROVED")
    elif case.startswith("live_"):
        host.record(
            "repair",
            status="running",
            finished_at=(NOW - timedelta(days=20)).isoformat(),
            **{"pr": 42, "worktree_branch": "other"}
            if case == "live_pr"
            else {"review_branch": "codex/fix", "worktree_branch": "other"}
            if case == "live_review"
            else {"worktree_branch": "codex/fix"},
        )
    elif case == "recent_repair":
        host.record("repair", status="failed", finished_at=(NOW - timedelta(minutes=5)).isoformat())
    assert host.scan()["rows"] == []


def test_unowned_pr_goes_to_cto(host):
    pr(host)
    rejection(host)
    row = host.scan()["rows"][0]
    assert (row["task_id"], row["lane"]) == ("unknown", "claude-cto")


@pytest.mark.parametrize(
    "initiator,lane",
    [
        ("codex-infra", "codex-infra"),
        ("claude-epics", "claude-epics"),
        ("grok-devops", "grok-devops"),
        ("claude-monitor", "muse-monitor"),
        ("codex-monitor", "muse-monitor"),
        ("grok-curriculum-upgrade", "grok-core"),
        ("unrecognized", "claude-cto"),
        ("codex", "claude-cto"),
        ("session-123", "claude-cto"),
        (None, "claude-cto"),
    ],
)
def test_dispatch_owner_uses_registry_and_retired_seat_succession(host, initiator, lane):
    host.record(initiator=initiator)
    host.facts.local_branches["codex/fix"] = LOCAL
    assert host.scan()["rows"][0]["lane"] == lane


def test_failed_fetch_is_unknown_and_cannot_route(host):
    host.record()
    host.facts.fetch_error = "unavailable"
    report = host.scan()
    assert report["rows"] == []
    assert report["errors"] == [f"{SLUG}: git repository evidence unavailable"]
    with pytest.raises(ValueError, match="incomplete"):
        mod.route(report, cycle=1, service=None)


def test_malformed_record_is_visible(host):
    (host.tasks / "broken.json").write_text("{")
    assert host.scan()["errors"] == ["task record broken.json: JSONDecodeError"]


def test_route_is_idempotent_per_lane_and_cycle_with_real_authority(host):
    host.record()
    host.facts.local_branches["codex/fix"] = LOCAL
    report = host.scan()
    second = copy.deepcopy(report["rows"][0])
    second.update(task_id="two", lane="claude-infra")
    report["rows"].append(second)
    with AuthorityService(root=host.tmp_path / "fleet") as service:
        first = mod.route(report, cycle=1, service=service)
        report["rows"].reverse()
        report["rows"][0]["age_hours"] += 0.1
        assert mod.route(report, cycle=1, service=service) == first
        again = mod.route(report, cycle=2, service=service)
        assert set(again).isdisjoint(first)
        messages = [service.get_message(mid) for mid in first]
        assert [message.recipient for message in messages] == ["claude-infra", "codex-devops", "claude-cto"]


def test_tick_cadence_and_retry(host):
    args = argparse.Namespace(state_file=host.tmp_path / "state.json", route=False, cadence_seconds=1800)
    calls = []

    def run(args, *, now):
        calls.append(now)
        return {"rows": [], "errors": []}

    host.monkeypatch.setattr(mod, "run", run)
    assert mod.tick(args, now=NOW)["errors"] == []
    assert mod.tick(args, now=NOW + timedelta(minutes=5))["skipped"] == "cadence"
    args.route = True
    assert mod.tick(args, now=NOW + timedelta(minutes=5))["errors"] == []
    assert mod.tick(args, now=NOW + timedelta(minutes=30))["errors"] == []
    assert len(calls) == 3
    args.state_file.unlink()
    host.monkeypatch.setattr(mod, "run", lambda *a, **k: {"errors": ["unknown"]})
    assert mod.tick(args, now=NOW)["errors"] == ["unknown"]
    assert not args.state_file.exists()


def test_untrusted_copy_cannot_delay_a_trusted_rejection(host):
    host.record(status="done")
    pr(host)
    rejection(host)
    spoof = copy.deepcopy(host.comments[42][0])
    spoof["user"]["login"] = "stranger"
    spoof["created_at"] = NOW.isoformat()
    spoof["updated_at"] = NOW.isoformat()
    host.comments[42].append(spoof)
    assert host.scan()["rows"][0]["age_hours"] == 3


def test_cli_report_only_and_tick_enable_flag(host, capsys):
    calls = []

    def run(args, *, now):
        calls.append(args.route)
        return {"errors": [], "rows": []}

    host.monkeypatch.setattr(mod, "run", run)
    host.monkeypatch.setenv("LU_STALLED_WORK_ROUTE_ENABLED", "1")
    assert mod.main(["stalled"]) == 0
    assert calls == [False]
    assert mod.main(["stalled", "--tick", "--state-file", str(host.tmp_path / "state")]) == 0
    assert calls == [False, True]
    assert '"errors": []' in capsys.readouterr().out


@pytest.mark.parametrize("state", [[], {"route": "1"}, {"report": -1}])
def test_invalid_checkpoint_does_not_run_scan(host, state):
    path = host.tmp_path / "cadence.json"
    path.write_text(json.dumps(state))
    args = argparse.Namespace(state_file=path, route=False, cadence_seconds=1800)
    with pytest.raises(ValueError, match="checkpoint malformed"):
        mod.tick(args, now=NOW)


@pytest.mark.parametrize(
    "options,env", [(["--cadence-minutes", "0"], {}), ([], {"LU_STALLED_WORK_ROUTE_ENABLED": "yes"})]
)
def test_invalid_config(host, options, env):
    for key, value in env.items():
        host.monkeypatch.setenv(key, value)
    with pytest.raises(SystemExit) as exc:
        mod.main(["stalled", *options])
    assert exc.value.code == 2
