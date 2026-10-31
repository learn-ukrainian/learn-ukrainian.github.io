"""Round-four regression evidence for Design B; synthetic fixtures only."""
from __future__ import annotations

import importlib.util
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

from scripts.opsec import prepublish as gate
from scripts.opsec.gh_snapshot import admit
from scripts.publish import github as pub
from tests.opsec_fixtures import CATALOG, ROOT, recorded_approval


@pytest.fixture(autouse=True)
def catalog(monkeypatch):
    monkeypatch.setattr(gate, "catalog", lambda: CATALOG)
    monkeypatch.delenv("AGENT_NO_MERGE", raising=False)


# The actual REST/search argv families from every refused caller in the review,
# plus the fresh inventory. GET fields in worktree_git are now query parameters.
READ_CALLERS = [
    ("scripts/dispatch.py", ["api", "repos/unit/public/issues/1"]),
    ("scripts/build/cf_preflight.py", ["api", "repos/{owner}/{repo}/issues/1/comments", "--paginate"]),
    ("scripts/build/cf_preflight.py", ["api", "repos/unit/public/pulls/1/reviews", "--paginate"]),
    ("scripts/orchestration/worktree_git.py", ["api", "repos/unit/public/pulls?head=unit%3Abranch&state=all&per_page=100", "-X", "GET", "--paginate", "--slurp"]),
    ("scripts/orchestration/worktree_git.py", ["api", "-X", "GET", "repos/unit/public/pulls/1"]),
    ("scripts/orchestration/merge_closeout.py", ["api", "-X", "GET", "repos/unit/public/pulls/1"]),
    ("scripts/gh_merge_queue_status.py", ["api", "repos/unit/public/actions/runs?event=merge_group&per_page=100"]),
    ("scripts/github_rest_cache.py", ["api", "--method", "GET", "-i", "https://api.github.com/repos/unit/public/pulls/1", "-H", 'If-None-Match: "fixture"']),
    ("scripts/orchestration/stale_task_records.py", ["api", "repos/unit/public/pulls?state=closed&page=1&per_page=100"]),
    ("scripts/fleet/hramatka_hygiene_check.py", ["api", "repos/unit/public/issues/1"]),
    ("scripts/orchestration/task_family/git_safety.py", ["api", "--paginate", "--slurp", "repos/unit/public/branches?per_page=100"]),
    ("agents_extensions/shared/hooks/guard-pr-merge.py", ["api", "repos/unit/public/branches/main/protection"]),
    ("agents_extensions/shared/skills/track-completion/scripts/track_completion.py", ["api", "repos/{owner}/{repo}/actions/runs/1"]),
    ("agents_extensions/shared/skills/track-completion/scripts/track_completion.py", ["api", "repos/{owner}/{repo}/compare/" + "a" * 40 + "..." + "b" * 40]),
    ("scripts/deploy/vendor_atlas_tree.py", ["api", "repos/unit/public/releases/assets/1", "-H", "Accept: application/octet-stream"]),
    ("scripts/ci/cache_hygiene.py", ["api", "repos/unit/public/actions/caches?per_page=100&page=1"]),
    ("scripts/ci/ci_timings.py", ["api", "repos/unit/public/actions/runs/1/jobs?per_page=100&page=1"]),
]


@pytest.mark.parametrize("caller,args", READ_CALLERS)
def test_listed_rest_read_reaches_transport(caller, args, tmp_path):
    assert (ROOT / caller).is_file()
    calls = []
    def spy(argv, **kwargs):
        calls.append(argv)
        return subprocess.CompletedProcess(argv, 0, "{}", "")
    # Cached pagination links returned by GitHub can be absolute API URLs.
    result = gate.checked_run(["gh", *args], cwd=tmp_path, env={}, runner=spy)
    assert result.returncode == 0 and calls == [["gh", *args]]


@pytest.mark.parametrize("args,read", [
    (["api", "repos/unit/public/issues/1", "-X", "POST"], False),
    (["api", "repos/unit/public/issues/1", "--method=GET", "-X=POST"], False),
    (["api", "repos/unit/public/issues/1", "-XGET"], True),
    (["api", "repos/unit/public/issues/1", "--field=x=y"], False),
    (["api", "repos/unit/public/issues/1", "--raw-field=x=y"], False),
    (["api", "repos/unit/public/issues/1", "--input=-"], False),
    (["api", "repos/unit/public/issues/1", "-f", "x=y"], False),
    (["api", "repos/unit/public/issues/1", "-F", "x=y"], False),
    (["api", "graphql", "-f", "query=query{x}"], True),
    (["api", "repos/unit/public/unknown/endpoint"], True),
    (["api", "https://other.invalid/repos/unit/public/issues/1"], False),
    (["release", "delete-asset", "v1", "fixture-asset"], False),
    (["release", "delete-asset", "v1", "fixture-asset", "-y"], False),
    (["repo", "set-default", "unit/public"], False),
    (["repo", "set-default", "--unset"], False),
    (["repo", "set-default", "--view", "--view=false", "unit/public"], False),
    (["repo", "set-default", "--view"], True),
    (["release", "verify-asset", "v1", "fixture-asset"], True),
    (["release", "view", "delete-asset"], True),
    (["repo", "view", "set-default"], True),
    (["repo", "read-file", "delete-asset"], True),
    (["repo", "read-dir", "set-default"], True),
    (["pr", "list", "--search", "delete-asset set-default update-branch"], True),
    (["pr", "list", "--limit", "invalid"], True),
    (["run", "watch", "1", "--compact"], True),
])
def test_native_reads_preserve_semantics_and_public_writes_remain_refused(args, read, tmp_path):
    """Retired read inventories must not refuse GET/query forms or admit public writes/uploads."""
    calls = []

    def transport(argv, **kwargs):
        calls.append(argv)
        return subprocess.CompletedProcess(argv, 7, "native output", "native diagnostic")

    if read:
        result = gate.checked_run(["gh", *args], cwd=tmp_path, env={}, runner=transport)
        assert calls == [["gh", *args]]
        assert (result.returncode, result.stdout, result.stderr) == (7, "native output", "native diagnostic")
    else:
        with pytest.raises(gate.PublishBlocked):
            gate.checked_run(["gh", *args], cwd=tmp_path, env={}, runner=transport)
        assert calls == []


@pytest.mark.parametrize("flag", ["-t", "-t=true", "-t=false", "-t=1", "-ttrue", "-t1", "-at", "--show-token", "--show-token=true", "--show-token=false", "--show-token=1"])
def test_auth_token_flag_spellings_refused(flag, tmp_path):
    for args in (["auth", "status", flag], ["auth", "status", flag, "--active"], ["-R", "unit/private", "auth", "status", flag]):
        with pytest.raises(gate.PublishBlocked):
            admit(args, cwd=tmp_path, environment={})


@pytest.mark.parametrize("repo", ["unit/public", "unit/private"])
@pytest.mark.parametrize("state", ["draft", "red", "pending", "unknown", "ready"])
def test_merge_readiness_applies_to_public_and_private(synthetic_opsec, repo, state):
    writes = []
    reads = []
    def spy(args, **kwargs):
        if args[1:3] == ["pr", "view"]:
            reads.append(args)
            body = {"number": 1, "isDraft": state == "draft", "headRefOid": "a" * 40}
            if "headRefOid,statusCheckRollup" in args:
                body["statusCheckRollup"] = [{
                    "__typename": "CheckRun", "name": "CI Gate",
                    "status": "IN_PROGRESS" if state == "pending" else "COMPLETED",
                    "conclusion": {"red": "FAILURE", "pending": "", "unknown": "UNKNOWN"}.get(state, "SUCCESS"),
                }]
        elif args[1:3] == ["pr", "checks"]:
            reads.append(args)
            body = [{"name": "CI Gate", "bucket": {"red": "fail", "pending": "pending", "unknown": "unrecognised"}.get(state, "pass")}]
        elif args[1:5] == ["api", "--method", "POST", "graphql"]:
            reads.append(args)
            body = {"data": {"repository": {"pullRequest": {
                "headRefOid": "a" * 40, "isMergeQueueEnabled": False,
                "viewerMergeHeadlineText": "clean (#1)", "viewerMergeBodyText": "clean"}}}}
        elif args[1:4] == ["api", "--method", "GET"]:
            reads.append(args)
            if "/pulls/1/files" in args[4]:
                body = [[{"filename": "scripts/example.py"}]]
            else:
                body = [[recorded_approval("a" * 40)]] if "/issues/1/comments" in args[4] else {"login": "unit"}
        else:
            writes.append(args)
            return subprocess.CompletedProcess(args, 0, "", "")
        return subprocess.CompletedProcess(args, 0, json.dumps(body), "")
    if state == "ready":
        assert pub.publish("pr-merge", repo=repo, number=1, runner=spy, env={}).returncode == 0
        assert len(writes) == 1 and "--match-head-commit=" + "a" * 40 in writes[0]
    else:
        with pytest.raises(gate.PublishBlocked):
            pub.publish("pr-merge", repo=repo, number=1, runner=spy, env={})
        assert writes == []
    # Read the head-bound checks; ready merges also read the default squash text
    # the recorded review seats (#12020), here an exact-head approval (#12031), and the PR's files (#12181).
    assert len(reads) == (7 if state == "ready" else 3)


def test_worker_merge_guard_and_changed_head_refuse_before_write():
    with pytest.raises(gate.PublishBlocked, match="AGENT_NO_MERGE"):
        pub.publish("pr-merge", repo="unit/private", number=1, env={"AGENT_NO_MERGE": "1"}, runner=lambda *a, **k: pytest.fail("send"))


@pytest.mark.parametrize("verb,fields,expected", [
    ("pr-update-branch", {"number": 1}, ["pr", "update-branch", "1"]),
    ("pr-ready", {"number": 1}, ["pr", "ready", "1"]),
    ("pr-close", {"number": 1}, ["pr", "close", "1"]),
    ("issue-reopen", {"number": 1}, ["issue", "reopen", "1"]),
    ("run-rerun", {"number": 123}, ["run", "rerun", "123"]),
    ("run-cancel", {"number": 123}, ["run", "cancel", "123"]),
    ("workflow-run", {"workflow": "ci.yml", "ref": "unit", "inputs": {}}, ["workflow", "run", "ci.yml"]),
])
def test_no_text_driver_operations(verb, fields, expected, monkeypatch, tmp_path, synthetic_opsec, github_transport):
    calls = []
    def spy(args, **kwargs):
        calls.append(args)
        return subprocess.CompletedProcess(args, 0, "", "")
    sender = spy
    expected_requests = {
        "pr-update-branch": [("PUT", "repos/unit/public/pulls/1/update-branch", {})],
        "pr-close": [("PATCH", "repos/unit/public/pulls/1", {"state": "closed"})],
        "issue-reopen": [("PATCH", "repos/unit/public/issues/1", {"state": "open"})],
    }
    if verb in expected_requests:
        from scripts.common.github_client import Response

        def transport(method, endpoint, headers, body, timeout):
            return Response(200, {}, b"{}")

        requests = github_transport(transport)
        original_transport = pub._run_transport

        def observe(command, **kwargs):
            calls.append(command)
            return original_transport(command, **kwargs)

        monkeypatch.setattr(pub, "_run_transport", observe)
        sender = None
    if verb == "run-rerun":
        from tests.test_ci_recovery import Transport
        sender = Transport()
        calls = sender.writes
        monkeypatch.setattr(pub.recovery, "ledger_path", lambda cwd: tmp_path / "ci-recovery.sqlite3")
    pub.publish(verb, repo="unit/public", cwd=tmp_path, runner=sender, env={}, **fields)
    assert calls[0][1:4] == expected
    assert calls[0][calls[0].index("--repo") + 1] == "unit/public"
    if verb == "run-rerun":
        assert "--failed" in calls[0]
    with pytest.raises(gate.PublishBlocked):
        pub.publish(verb, repo="unit/public", body="arbitrary", runner=spy, **fields)
    assert len(calls) == 1
    if verb in expected_requests:
        assert [
            (method, endpoint, json.loads(body) if body is not None else None)
            for method, endpoint, _headers, body, _timeout in requests
        ] == expected_requests[verb]


@pytest.mark.parametrize("fields", [
    {"workflow": "unknown.yml", "ref": "main"},
    {"workflow": "ci.yml", "ref": "main", "inputs": {"body": "anything"}},
    {"workflow": "ci.yml", "ref": "--flag"},
])
def test_workflow_closed_names_and_inputs(fields):
    with pytest.raises(gate.PublishBlocked):
        pub.publish("workflow-run", repo="unit/public", runner=lambda *a, **k: pytest.fail("send"), **fields)


@pytest.mark.parametrize("workflow", ["ci.yml", "deploy-pages.yml", "stale-branch-cleanup.yml"])
@pytest.mark.parametrize("inputs", [None, {}])
@pytest.mark.parametrize("entrypoint", ["publisher", "cli"])
def test_named_workflow_run_no_inputs(workflow, inputs, entrypoint, synthetic_opsec):
    calls = []

    def spy(args, **kwargs):
        calls.append(args)
        return subprocess.CompletedProcess(args, 0, "", "")

    if entrypoint == "cli":
        args = ["workflow-run", "--repo", "unit/public", "--workflow", workflow, "--ref", "main"]
        if inputs is not None:
            args += ["--inputs", json.dumps(inputs)]
        assert pub.main(args, runner=spy) == 0
    else:
        fields = {} if inputs is None else {"inputs": inputs}
        result = pub.publish(
            "workflow-run", repo="unit/public", workflow=workflow, ref="main", runner=spy, **fields
        )
        assert result.returncode == 0
    assert calls == [["gh", "workflow", "run", workflow, "--repo", "unit/public", "--ref=main"]]


@pytest.mark.parametrize("workflow", ["ci.yml", "deploy-pages.yml", "stale-branch-cleanup.yml"])
@pytest.mark.parametrize("invalid", [
    {"inputs": {"force": "true"}},
    {"repo": "owner/repo?unexpected=true"},
    {"ref": "--flag"},
    {"ref": "main\nother"},
])
def test_workflow_invalid_fields_refuse_before_send(workflow, invalid):
    fields = {"repo": "unit/public", "workflow": workflow, "ref": "main", **invalid}

    def sender(*args, **kwargs):
        pytest.fail("send")

    with pytest.raises(gate.PublishBlocked):
        pub.publish("workflow-run", runner=sender, **fields)
    args = ["workflow-run"]
    for key, value in fields.items():
        args.append("--" + key + "=" + (json.dumps(value) if key == "inputs" else value))
    assert pub.main(args, runner=sender) == 2


def test_unknown_workflow_cli_refuses_before_send():
    with pytest.raises(SystemExit) as error:
        pub.main(
            ["workflow-run", "--repo", "unit/public", "--workflow", "unknown.yml", "--ref", "main"],
            runner=lambda *a, **k: pytest.fail("send"),
        )
    assert error.value.code == 2


def test_checkout_only_in_real_dispatch_directory(tmp_path):
    worktree = tmp_path / ".worktrees/dispatch/unit/task"
    worktree.mkdir(parents=True)
    def git_reader(args, **kwargs):
        return subprocess.CompletedProcess(args, 0, str(worktree), "")
    assert not admit(["pr", "checkout", "1"], cwd=worktree, environment={}, reader=git_reader).write
    with pytest.raises(gate.PublishBlocked):
        admit(["pr", "checkout", "1"], cwd=worktree, environment={},
              reader=lambda args, **kwargs: subprocess.CompletedProcess(args, 0, str(tmp_path), ""))
    with pytest.raises(gate.PublishBlocked):
        admit(["pr", "checkout", "1"], cwd=tmp_path, environment={})
    link = tmp_path / ".worktrees/dispatch/unit/link"
    link.symlink_to(worktree, target_is_directory=True)
    with pytest.raises(gate.PublishBlocked):
        admit(["pr", "checkout", "1"], cwd=link, environment={})


def test_private_write_pins_repo_even_with_second_remote(tmp_path):
    env = {k: v for k, v in os.environ.items() if not k.startswith(("GIT_", "GH_"))}
    for args in (["init", "-q", str(tmp_path)], ["-C", str(tmp_path), "remote", "add", "origin", "https://github.com/unit/private.git"], ["-C", str(tmp_path), "remote", "add", "upstream", "https://github.com/unit/public.git"]):
        subprocess.run(["git", *args], env=env, check=True, timeout=10)
    frozen = admit(["issue", "comment", "1", "--body", "fixture"], cwd=tmp_path, environment=env)
    assert frozen.destination == "github.com/unit/private"
    assert frozen.argv[frozen.argv.index("--repo") + 1] == "github.com/unit/private"


def test_invalid_asset_cli_name_is_masked_exit_two(capsys):
    with pytest.raises(SystemExit) as error:
        pub.main(["release-upload", "--repo", "unit/public", "--tag", "unit", "--assets", "invalid#name"])
    assert error.value.code == 2
    assert "invalid#name" not in capsys.readouterr().err


def test_hook_recognises_typed_merge(monkeypatch):
    spec = importlib.util.spec_from_file_location("r5_guard", ROOT / "agents_extensions/shared/hooks/guard-pr-merge.py")
    guard = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(guard)
    for prefix in (sys.executable, "/fixture/bin/python"):
        args = guard._merge_args([prefix, "-m", "scripts.publish", "pr-merge", "--repo", "unit/private", "--number", "1"])
        assert guard._pr_selector(args) == "1" and guard._repo_option(args) == "unit/private"


@pytest.mark.parametrize("caller,name,fields", [
    ("scripts/github_graphql_budget.py", "budget", {}),
    ("scripts/gh_merge_queue_status.py", "membership", {"number": 1}),
    ("scripts/fleet/hramatka_scope_gate.py", "issue-scope", {"number": 1}),
    ("scripts/work/sources_public.py", "issue-states", {"numbers": [1, 2]}),
    ("scripts/fleet_comms/efficiency_metrics.py", "merge-facts", {"batch": [("unit/public", 1)]}),
    ("scripts/ci/cache_hygiene.py", "pr-bases", {"cursor": None}),
])
def test_named_read_callers_have_closed_endpoint_plans(caller, name, fields):
    assert (ROOT / caller).is_file()
    sent = []
    def spy(args, **kwargs):
        sent.append(args)
        if "graphql" in args:
            document = json.loads(Path(args[args.index("--input") + 1]).read_text())
            assert document["query"].lstrip().startswith("query")
            assert "mutation" not in document["query"]
        return subprocess.CompletedProcess(args, 0, json.dumps(_named_rest_fixture(args)), "")
    assert pub.read(name, repo="unit/public", runner=spy, env={}, **fields).returncode == 0
    expected_counts = {"budget": 1, "membership": 1, "issue-scope": 2, "issue-states": 2, "merge-facts": 1, "pr-bases": 2}
    assert len(sent) == expected_counts[name]
    if name != "membership":
        assert all("graphql" not in args and args[args.index("--method") + 1] == "GET" for args in sent)
    with pytest.raises(gate.PublishBlocked):
        pub.read(name, repo="unit/public", runner=spy, query="mutation{x}", **fields)
    assert len(sent) == expected_counts[name]


def _named_rest_fixture(args):
    endpoint = args[args.index("GET") + 1] if "GET" in args else ""
    if endpoint == "rate_limit":
        return {"resources": {"graphql": {"limit": 5000, "remaining": 4999, "used": 1, "reset": 2000}}}
    if endpoint.startswith("search/issues?"):
        return {"total_count": 0, "incomplete_results": False}
    if "/pulls?" in endpoint:
        return []
    if "/pulls/" in endpoint:
        return {"merged_at": None}
    if endpoint.endswith("/parent"):
        return {"number": 2, "html_url": "https://github.com/unit/public/issues/2", "repository_url": "https://api.github.com/repos/unit/public"}
    if "/issues/" in endpoint:
        return {"number": 1, "state": "open", "html_url": "https://github.com/unit/public/issues/1", "repository_url": "https://api.github.com/repos/unit/public", "body": "", "labels": []}
    return {}


@pytest.mark.parametrize("command", [
    ["read", "issue", "--repo", "unit/public", "--number", "1"],
    ["read", "budget"],
    ["read", "membership-head", "--repo", "unit/public", "--number", "1", "--branch", "main"],
    ["read", "issue-states", "--repo", "unit/public", "--numbers", "[1,2]"],
])
def test_named_read_shell_cli(command):
    calls = []
    def spy(args, **kwargs):
        calls.append(args)
        return subprocess.CompletedProcess(args, 0, json.dumps(_named_rest_fixture(args)), "")
    assert pub.main(command, runner=spy) == 0
    assert len(calls) == (2 if "issue-states" in command else 1)
    assert all(args[:2] == ["gh", "api"] for args in calls)


@pytest.mark.parametrize("repo", ["unit/public", "unit/private"])
@pytest.mark.parametrize("state", ["draft", "red", "pending", "ready"])
def test_hook_judges_publisher_readiness(repo, state, monkeypatch, capsys):
    spec = importlib.util.spec_from_file_location("r5_hook", ROOT / "agents_extensions/shared/hooks/guard-pr-merge.py")
    guard = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(guard)
    monkeypatch.setattr(guard, "_read_payload", lambda: {"tool_input": {"command": f".venv/bin/python -m scripts.publish pr-merge --repo {repo} --number 1"}})
    reads = []
    def snapshot(pr, target, cwd=None):
        reads.append((pr, target))
        return {"isDraft": state == "draft"}, (["CI Gate"] if state == "red" else [], ["CI Gate"] if state == "pending" else [])
    monkeypatch.setattr(guard, "_pr_snapshot", snapshot)
    assert guard.main() == (0 if state == "ready" else 2)
    assert reads == [("1", repo)]


def test_review_publisher_default_uses_guarded_transport(synthetic_opsec, tmp_path, monkeypatch):
    from scripts.fleet_comms import review_publisher
    calls = []
    executable = tmp_path / "real-gh"
    executable.write_text("#!/bin/sh\nexit 0\n")
    executable.chmod(0o755)
    monkeypatch.setenv("AGENT_REAL_GH", str(executable))
    def send(args, **kwargs):
        calls.append(args)
        return subprocess.CompletedProcess(args, 0, "https://example.invalid/comment/1", "")
    monkeypatch.setattr(pub, "_run_transport", send)
    assert review_publisher.post_pr_comment(repository="unit/public", pr_number=1, body="fixture") == "https://example.invalid/comment/1"
    assert len(calls) == 1 and calls[0][1:3] == ["pr", "comment"]
    assert "--body-file" in calls[0]


def test_issue_count_fixed_read_positive_and_existing_reads_unchanged(tmp_path, monkeypatch):
    calls = []
    query_paths = []
    scratch = tmp_path / "managed-scratch"
    scratch.mkdir()
    monkeypatch.setattr(pub, "ensure_scratch_root", lambda: scratch)
    def transport(command, **kwargs):
        query_path = Path(command[command.index("--input") + 1])
        assert query_path.parent.parent == scratch
        query_paths.append(query_path)
        document = json.loads(query_path.read_text())
        calls.append(document)
        return subprocess.CompletedProcess(command, 0, '{"data":{"repository":{"issues":{"totalCount":612}}}}', '')
    result = pub.read("issue-count", repo="unit/public", runner=transport, cwd=tmp_path, env={}, capture_output=True, text=True)
    assert json.loads(result.stdout)["data"]["repository"]["issues"]["totalCount"] == 612
    assert calls == [{"query": "query($owner:String!,$name:String!){repository(owner:$owner,name:$name){issues(states:OPEN){totalCount}}}",
                      "variables": {"owner": "unit", "name": "public"}}]
    assert "issue-count" not in pub.GQL_READS and "issue-count" not in pub.REST_READS
    assert all(not path.exists() for path in query_paths)
    assert list(scratch.iterdir()) == []


@pytest.mark.parametrize("response", ['{}', '{"data":{"repository":null}}', '{"data":{"repository":{"issues":{"totalCount":true}}}}',
                                     '{"data":{"repository":{"issues":{"totalCount":-1}}}}',
                                     '{"data":{"repository":{"issues":{"totalCount":3}}},"errors":[{"message":"private"}]}'])
def test_issue_count_malformed_refused(response):
    with pytest.raises(gate.PublishBlocked, match="malformed issue count response"):
        pub.read("issue-count", repo="unit/private", runner=lambda command, **k: subprocess.CompletedProcess(command, 0, response, ''), env={})


def test_issue_count_unknown_repository_or_fields_refused():
    for fields in [{"repo": "unit/unknown"}, {"repo": "unit/public", "number": 1}]:
        with pytest.raises(gate.PublishBlocked):
            pub.read("issue-count", **fields, runner=lambda *a, **k: pytest.fail("must not send"), env={})


def test_issue_count_cli_prints_validated_json(capsys):
    response = '{"data":{"repository":{"issues":{"totalCount":42}}}}'
    assert pub.main(['read', 'issue-count', '--repo', 'unit/public'], runner=lambda command, **k: subprocess.CompletedProcess(command, 0, response, '')) == 0
    assert json.loads(capsys.readouterr().out)['data']['repository']['issues']['totalCount'] == 42


def test_issue_count_uses_fixed_read_output_contract():
    import io
    response = '{"data":{"repository":{"issues":{"totalCount":42}}}}'
    def transport(command, **kwargs):
        return subprocess.CompletedProcess(command, 0, response, '')
    result = pub.read('issue-count', repo='unit/public', runner=transport, env={}, capture_output=True)
    assert isinstance(result.stdout, bytes)
    assert json.loads(result.stdout)['data']['repository']['issues']['totalCount'] == 42
    output = io.StringIO()
    result = pub.read('issue-count', repo='unit/public', runner=transport, env={}, text=True, stdout=output)
    assert result.returncode == 0
    assert json.loads(output.getvalue())['data']['repository']['issues']['totalCount'] == 42
