"""Closed grammar and immutable payload adversarial tests; synthetic data only."""

from __future__ import annotations

import io
import json
import os
import re
import shutil
import statistics
import subprocess
import sys
import time
import zipfile
from importlib.resources import files
from pathlib import Path

import pytest
from lu_machinery.opsec import prepublish as gate
from lu_machinery.opsec.gh_snapshot import admit
from lu_machinery.publish import github as pub
from lu_machinery.review.record_cf_verdict import build_comment as _recovery_build_comment

from tests.common.github_cache_isolation import isolate_github_client_cache
from tests.opsec_fixtures import CATALOG, ROOT, TOKEN, recorded_approval

# Product fixtures retained from the machinery test consumers (C-5048).

_git_REAL_RUN = subprocess.run


def _git_git_env() -> dict[str, str]:
    return {
        key: value
        for key, value in os.environ.items()
        if not key.startswith("GIT_") and (not key.startswith("PRE_COMMIT")) and (key != "AGENT_NO_MERGE")
    }


def _git_run(args: list[str], cwd: Path, check: bool = True) -> subprocess.CompletedProcess[str]:
    return _git_REAL_RUN(args, cwd=cwd, capture_output=True, text=True, check=check, timeout=30, env=_git_git_env())


def _git_init_repo(repo_root: Path) -> None:
    repo_root.mkdir(parents=True)
    remote = repo_root.parent / f"{repo_root.name}-origin.git"
    _git_run(["git", "init", "--bare", str(remote)], cwd=repo_root.parent)
    _git_run(["git", "init", "--initial-branch=main", str(repo_root)], cwd=repo_root.parent)
    _git_run(["git", "config", "user.email", "test@example.com"], cwd=repo_root)
    _git_run(["git", "config", "user.name", "Test User"], cwd=repo_root)
    (repo_root / "README.md").write_text("# test\n", encoding="utf-8")
    _git_run(["git", "add", "README.md"], cwd=repo_root)
    _git_run(["git", "commit", "-m", "initial"], cwd=repo_root)
    _git_run(["git", "remote", "add", "origin", str(remote)], cwd=repo_root)
    _git_run(["git", "push", "-u", "origin", "main"], cwd=repo_root)


_recovery_HEAD = "a" * 40

_recovery_TESTED = "c" * 40


def _recovery_evidence(head=_recovery_HEAD):
    return {
        "pr": 42,
        "head": head,
        "run_id": 123,
        "job_ids": [456],
        "tested_sha": _recovery_TESTED,
        "queue_group_diff": {
            "base_sha": "d" * 40,
            "head_sha": _recovery_TESTED,
            "paths": ["lu_machinery/earlier-pr.py", "lu_machinery/this-pr.py"],
        },
        "failure_evidence": "Job log confirms runner checkout failure",
        "unrelated_to_diff": "Failure precedes execution of changed code",
    }


_recovery_NEW_HEAD = "b" * 40


class _recovery_Transport:
    def __init__(self):
        self.head = _recovery_HEAD
        self.proof = _recovery_evidence()
        self.approved = True
        self.attempt = 1
        self.status = "completed"
        self.conclusion = "failure"
        self.event = "merge_group"
        self.failed_ids = [456]
        self.removed = True
        self.future_commit = False
        self.removal_head = _recovery_HEAD
        self.removal_date = "2026-10-09T11:00:00Z"
        self.removal_failure = False
        self.removal_history = None
        self.removal_page_size = 100
        self.removal_reason = "removed by actor"
        self.timeline_count = None
        self.removal_reads = []
        self.pushes = []
        self.associations = None
        self.proof_login = "driver"
        self.proof_association = "MEMBER"
        self.failure = False
        self.moved = False
        self.pull_reads = 0
        self.writes = []
        self.queued = False
        self.files = [[{"filename": "lu_machinery/example.py"}]]
        self.compare_rows = {
            "base_commit": {"sha": "d" * 40},
            "merge_base_commit": {"sha": "d" * 40},
            "status": "ahead",
            "files": [{"filename": "lu_machinery/earlier-pr.py"}, {"filename": "lu_machinery/this-pr.py"}],
        }
        self.candidate_record = {
            "base_sha": "d" * 40,
            "head_sha": _recovery_TESTED,
            "head_ref": "refs/heads/gh-readonly-queue/main/pr-42-" + "e" * 40,
            "run_id": 123,
            "run_attempt": 1,
        }

    def __call__(self, argv, **kwargs):
        if argv[1:3] == ["pr", "view"]:
            assert "isInMergeQueue" not in argv[argv.index("--json") + 1].split(",")
            data = {
                "number": 42,
                "isDraft": False,
                "mergeStateStatus": "CLEAN",
                "headRefOid": self.head,
                "headRefName": "codex/fixture",
                "state": "OPEN",
                "isCrossRepository": False,
                "baseRefName": "main",
            }
        elif argv[1:3] == ["pr", "checks"]:
            data = []
        elif argv[1:5] == ["api", "--method", "POST", "graphql"]:
            payload = json.loads(Path(argv[6]).read_text())
            query = payload["query"]
            if query.startswith("mutation"):
                assert "enqueuePullRequest" in query
                self.writes.append(argv)
                if self.failure:
                    raise subprocess.TimeoutExpired(argv, 60)
                self.queued = True
                return subprocess.CompletedProcess(
                    argv, 0, json.dumps({"data": {"enqueuePullRequest": {"mergeQueueEntry": {"position": 1}}}}), ""
                )
            if "mergeQueueEntry" in query:
                data = {
                    "number": 42,
                    "state": "OPEN",
                    "headRefOid": self.head,
                    "headRefName": "codex/fixture",
                    "isInMergeQueue": self.queued,
                    "mergeQueueEntry": {"headCommit": {"oid": _recovery_TESTED}},
                }
                return subprocess.CompletedProcess(
                    argv, 0, json.dumps({"data": {"repository": {"pullRequest": data}}}), ""
                )
            if "timelineItems" in query:
                self.removal_reads.append(payload)
                if self.removal_failure:
                    return subprocess.CompletedProcess(argv, 1, "", "lookup failed")
                events = (
                    self.removal_history
                    if self.removal_history is not None
                    else [
                        {
                            "beforeCommit": {
                                "oid": self.removal_head,
                                "committedDate": "2099-01-01T00:00:00Z"
                                if self.future_commit
                                else "2026-10-09T10:00:00Z",
                            }
                            if self.removal_head
                            else None,
                            "createdAt": self.removal_date,
                            "reason": self.removal_reason,
                        }
                    ]
                    if self.removed
                    else []
                )
                if "first:100" in query:
                    start = int(payload["variables"].get("cursor") or 0)
                    nodes = events[start : start + self.removal_page_size]
                    end = start + len(nodes)
                    removals = {
                        "nodes": nodes,
                        "totalCount": self.timeline_count if self.timeline_count is not None else len(events),
                        "pageInfo": {"hasNextPage": end < len(events), "endCursor": str(end) if nodes else None},
                    }
                else:
                    removals = {"nodes": events[-1:]}
                pull = {"headRefOid": self.head, "pushes": {"nodes": self.pushes}, "removals": removals}
                return subprocess.CompletedProcess(
                    argv, 0, json.dumps({"data": {"repository": {"pullRequest": pull}}}), ""
                )
            data = {
                "data": {
                    "repository": {
                        "pullRequest": {
                            "headRefOid": self.head,
                            "isMergeQueueEnabled": True,
                            "id": "PR_fixture_42",
                            "viewerMergeHeadlineText": "change (#42)",
                            "viewerMergeBodyText": "change",
                        }
                    }
                }
            }
        elif argv[1] == "api":
            endpoint = next(arg for arg in argv if arg.startswith("repos/") or arg.split("?", 1)[0] == "user").split(
                "?", 1
            )[0]
            if endpoint.endswith("/comments"):
                approval = {
                    "body": _recovery_build_comment(
                        sha=self.head,
                        task_id="review",
                        started="2026-10-09T10:00:00.000001+00:00",
                        verdict="APPROVED" if self.approved else "CHANGES_REQUESTED",
                        model="claude-opus-5-5",
                        family="anthropic",
                        reply="VERDICT: APPROVE",
                    ),
                    "user": {"login": "driver"},
                    "author_association": "MEMBER",
                    "created_at": "2026-10-09T10:00:01Z",
                    "updated_at": "2026-10-09T10:00:01Z",
                }
                comments = [approval]
                if self.proof is not None:
                    comments.append(
                        {
                            "id": 789,
                            "body": "<!-- ci-recovery-evidence " + json.dumps(self.proof) + " -->",
                            "user": {"login": self.proof_login},
                            "author_association": self.proof_association,
                        }
                    )
                data = [comments]
            elif endpoint.endswith("/files"):
                data = self.files
            elif endpoint.endswith("/timeline"):
                data = (
                    [[{"id": 987, "event": "removed_from_merge_queue", "created_at": "2026-10-09T11:00:00Z"}]]
                    if self.removed
                    else [[]]
                )
                if self.future_commit:
                    data[0].append(
                        {"event": "committed", "sha": self.head, "committer": {"date": "2099-01-01T00:00:00Z"}}
                    )
            elif endpoint.endswith("/jobs"):
                data = [{"jobs": [{"id": job, "conclusion": "failure"} for job in self.failed_ids]}]
            elif endpoint.endswith("/runs/123"):
                data = {
                    "id": 123,
                    "status": self.status,
                    "conclusion": self.conclusion,
                    "head_sha": _recovery_TESTED,
                    "event": self.event,
                    "head_branch": "gh-readonly-queue/main/pr-42-" + "e" * 40,
                    "run_attempt": self.attempt,
                    "pull_requests": self.associations
                    if self.associations is not None
                    else []
                    if self.event == "merge_group"
                    else [{"number": 42, "head": {"sha": self.head}}],
                }
            elif endpoint.endswith("/actions/runs/123/artifacts"):
                data = {
                    "total_count": 1,
                    "artifacts": [{"name": "ci-queue-candidate", "id": 77, "expired": False, "size_in_bytes": 1024}],
                }
            elif endpoint.endswith("/actions/artifacts/77/zip"):
                with io.BytesIO() as buffer:
                    with zipfile.ZipFile(buffer, "w") as archive:
                        archive.writestr("queue-candidate.json", json.dumps(self.candidate_record))
                    kwargs["stdout"].write(buffer.getvalue())
                return subprocess.CompletedProcess(argv, 0, "", "")
            elif "/compare/" in endpoint:
                data = self.compare_rows
            elif endpoint.endswith("/pulls/42"):
                self.pull_reads += 1
                data = {
                    "state": "open",
                    "head": {"sha": _recovery_NEW_HEAD if self.moved and self.pull_reads > 1 else self.head},
                }
            elif endpoint == "user":
                data = {"login": "driver"}
            else:
                pytest.fail(f"unexpected read {endpoint}")
        else:
            self.writes.append(argv)
            if self.failure:
                raise subprocess.TimeoutExpired(argv, 60)
            if argv[1:3] == ["pr", "merge"]:
                self.queued = True
            return subprocess.CompletedProcess(argv, 0, "", "")
        return subprocess.CompletedProcess(argv, 0, json.dumps(data), "")


@pytest.fixture
def gh_shim_sandbox(tmp_path, monkeypatch):
    """Stage the installed publisher and its dependency closure with synthetic policy."""
    from tests import opsec_fixtures

    root = tmp_path / "public-fixture"
    root.mkdir()
    installed = files("lu_machinery")
    package = root / "lu_machinery"
    package.mkdir()
    with monkeypatch.context() as fixture_names:
        fixture_names.setattr(opsec_fixtures, "machinery_package", lambda: "lu_machinery")
        opsec_fixtures.copy_publisher_scripts(installed, package)
    workflow = root / ".github/workflows/ci.yml"
    workflow.parent.mkdir(parents=True)
    shutil.copy2(ROOT / ".github/workflows/ci.yml", workflow)
    deploy_paths = root / "scripts/curriculum/deploy_paths.v1.json"
    deploy_paths.parent.mkdir(parents=True)
    shutil.copy2(ROOT / "scripts/curriculum/deploy_paths.v1.json", deploy_paths)
    marker = root / "curriculum/l2-uk-en/curriculum.yaml"
    marker.parent.mkdir(parents=True)
    marker.write_text("")
    shim = package / "agent_runtime/shims/gh"
    shim.parent.mkdir(parents=True)
    shutil.copy2(installed.joinpath("agent_runtime/shims/gh"), shim)
    (package / "lib").mkdir(exist_ok=True)
    shutil.copy2(installed.joinpath("lib/project_interpreter.sh"), package / "lib/project_interpreter.sh")
    (package / "config").mkdir()
    (package / "config/fleet_repos.yaml").write_text(json.dumps({"repos": CATALOG}))
    (root / ".venv").symlink_to(Path(sys.executable).parent.parent, target_is_directory=True)
    tooling = opsec_fixtures.make_tooling(tmp_path / "private-fixture/tools/public_opsec_scan")
    env = {key: value for key, value in os.environ.items() if not key.startswith(("GIT_", "PRE_COMMIT", "LU_OPSEC"))}
    git = shutil.which("git", path=os.defpath)
    subprocess.run([git, "init", "-q", str(root)], env=env, check=True, timeout=30)
    subprocess.run(
        [git, "-C", str(root), "remote", "add", "origin", "https://github.com/unit/public.git"],
        env=env,
        check=True,
        timeout=30,
    )
    return root, shim, tooling

READ_COMMANDS = [
    ['ruleset', 'list', '--repo', 'unit/public'],
    ['api', 'repos/unit/public/rulesets'],
    ['api', 'repos/unit/public/merge-queue/entries'],
    ['run', 'watch', '1', '--compact', '--exit-status'],
    ['api', 'graphql', '-f', 'query=query($name:String!){repository(owner:"unit",name:$name){name}}', '-f', 'name=public'],
    ['issue', 'view', '1'],
    ['issue', 'list'],
    ['issue', 'status'],
    ['run', 'view'],
    ['run', 'list'],
    ['run', 'watch', '1'],
    ['run', 'download'],
    ['workflow', 'list'],
    ['workflow', 'view'],
    ['repo', 'view'],
    ['repo', 'list'],
    ['release', 'view'],
    ['release', 'list'],
    ['release', 'download'],
    ['auth', 'status'],
    ['gist', 'view', '1'],
    ['gist', 'list'],
    ['label', 'list'],
    ['search', 'prs', '1'],
]


@pytest.fixture(autouse=True)
def _isolate_github_client_cache(tmp_path, monkeypatch):
    yield from isolate_github_client_cache(tmp_path, monkeypatch)


@pytest.fixture(autouse=True)
def catalog(monkeypatch):
    monkeypatch.setattr(gate, "catalog", lambda: CATALOG)
    monkeypatch.delenv("AGENT_NO_MERGE", raising=False)


def stub_parent_epic(monkeypatch):
    """Accept any parent epic and skip the link step; the epic check and the link have their own proof."""
    monkeypatch.setattr(pub, "_parent_epic_node", lambda *args: "PARENT_NODE")
    monkeypatch.setattr(pub, "_link_created_issue", lambda *args: None)


def spy(calls, *, comment_edit=False, merge=False):
    def send(args, **kwargs):
        if comment_edit and args[:4] == ["gh", "api", "--method", "GET"]:
            endpoint = args[4].split("?", 1)[0]
            if endpoint == "user" or endpoint == "repos/unit/public/issues/comments/7":
                document = {"login": "unit"} if endpoint == "user" else {"id": 7, "body": "previous", "user": {"login": "unit"}}
                return subprocess.CompletedProcess(args, 0, json.dumps(document), "")
        if merge and args[:4] == ["gh", "api", "--method", "GET"] and args[4].split("?", 1)[0] in {
            "repos/unit/public/issues/1/comments", "repos/unit/public/pulls/1/files", "user"
        }:
            # pr-merge reads the recorded review seats (#12020): an exact-head approval (#12031), and the PR's files.
            endpoint = args[4].split("?", 1)[0]
            if endpoint.endswith("/files"):
                seats = [[{"filename": "lu_machinery/example.py"}]]
            else:
                seats = [[recorded_approval("a" * 40)]] if args[4].startswith("repos/") else {"login": "unit"}
            return subprocess.CompletedProcess(args, 0, json.dumps(seats), "")
        if (
            args[:3] == ["gh", "pr", "view"]
            and "--json" in args
            and args[args.index("--json") + 1] in {"number,isDraft,headRefOid", "number,isDraft,headRefOid,mergeStateStatus"}
        ):
            return subprocess.CompletedProcess(
                args, 0, json.dumps({"number": int(args[3]), "isDraft": False, "mergeStateStatus": "CLEAN", "headRefOid": "a" * 40}), ""
            )
        if (
            args[:3] == ["gh", "pr", "checks"]
            and "--json" in args
            and args[args.index("--json") + 1] == "name,bucket,state,workflow"
        ):
            return subprocess.CompletedProcess(args, 0, "[]", "")
        if (
            merge and args[:5] == ["gh", "api", "--method", "POST", "graphql"]
            and "viewerMergeHeadlineText" in Path(args[6]).read_text()
        ):
            pull = {
                "id": "PR_fixture_1",
                "headRefOid": "a" * 40,
                "isMergeQueueEnabled": True,
                "viewerMergeHeadlineText": "clean (#1)",
                "viewerMergeBodyText": "* clean",
            }
            return subprocess.CompletedProcess(args, 0, json.dumps({"data": {"repository": {"pullRequest": pull}}}), "")
        if merge and args[:3] == ["gh", "pr", "view"] and "id,headRefOid,isCrossRepository,baseRefName,labels" in args:
            # A queue-enabled base: pr-merge proves the head is not yet queued before it enqueues.
            identity = {"id": "PR_fixture_1", "headRefOid": "a" * 40, "isCrossRepository": False, "baseRefName": "main", "labels": []}
            return subprocess.CompletedProcess(args, 0, json.dumps(identity), "")
        if (
            merge and args[:5] == ["gh", "api", "--method", "POST", "graphql"]
            and json.loads(Path(args[6]).read_text())["query"] == pub.GQL_READS["queue-status"]
        ):
            pull = {"headRefOid": "a" * 40, "isInMergeQueue": False}
            return subprocess.CompletedProcess(args, 0, json.dumps({"data": {"repository": {"pullRequest": pull}}}), "")
        if (
            merge and args[:5] == ["gh", "api", "--method", "POST", "graphql"]
            and json.loads(Path(args[6]).read_text())["query"] == pub.QUEUE_ENTRY_QUERY
        ):
            # pr-merge proves the reviewed head's queue entry after the enqueue (machinery #281).
            pull = {
                "headRefOid": "a" * 40,
                "isInMergeQueue": True,
                "mergeQueueEntry": {"headCommit": {"oid": "a" * 40}},
                "autoMergeRequest": None,
            }
            return subprocess.CompletedProcess(args, 0, json.dumps({"data": {"repository": {"pullRequest": pull}}}), "")
        record = {"argv": args, "env": kwargs.get("env", {})}
        for flag in ("--body-file", "--notes-file", "--input"):
            if flag in args:
                record[flag] = Path(args[args.index(flag) + 1]).read_bytes()
        if "--" in args:
            record["artifacts"] = {
                Path(p).name: Path(p).read_bytes() for p in args[args.index("--") + 1 :] if Path(p).is_file()
            }
        calls.append(record)
        return subprocess.CompletedProcess(args, 0, "{}", "")

    return send


VERBS = [
    ("issue-create", {"title": "clean", "body": "clean", "labels": ["unit"], "parent": 10453}),
    ("issue-edit", {"number": 1, "title": "clean", "body": "clean", "milestone": "unit"}),
    ("issue-comment", {"number": 1, "body": "clean"}),
    ("issue-comment-json", {"number": 1, "body": "clean"}),
    ("comment-edit", {"comment_id": 7, "body": "clean"}),
    ("issue-close", {"number": 1, "comment": "clean"}),
    ("pr-create", {"title": "clean", "body": "clean", "base": "main", "head": "unit"}),
    ("pr-edit", {"number": 1, "title": "clean", "add_labels": ["unit"], "remove_labels": ["old"]}),
    ("pr-comment", {"number": 1, "body": "clean"}),
    ("pr-review", {"number": 1, "verdict": "request-changes", "body": "clean"}),
    ("pr-merge", {"number": 1, "subject": "clean", "body": "clean"}),
    ("pr-disarm", {"number": 1}),
    ("pr-dequeue", {"node_id": "UNIT_NODE"}),
    ("release-create", {"tag": "unit", "title": "clean", "notes": "clean"}),
    ("release-edit", {"tag": "unit", "title": "clean", "notes": "clean", "draft": False}),
    ("label-create", {"name": "unit", "color": "aabbcc", "description": "clean"}),
    ("label-edit", {"name": "unit", "new_name": "new", "description": "clean"}),
    ("milestone-create", {"title": "clean", "description": "clean"}),
    ("milestone-edit", {"number": 1, "title": "clean", "description": "clean"}),
    ("commit-status", {"sha": "a" * 40, "state": "success", "context": "unit", "description": "clean"}),
    ("issue-link", {"parent_id": "PARENT", "child_id": "CHILD"}),
    ("issue-unlink", {"parent_id": "PARENT", "child_id": "CHILD"}),
]


@pytest.mark.parametrize("verb,fields", VERBS)
def test_each_typed_verb_delivers_fixed_payload(synthetic_opsec, verb, fields, github_transport, monkeypatch):
    stub_parent_epic(monkeypatch)
    calls = []
    sender = spy(calls, merge=verb == "pr-merge")
    expected_requests = {
        "issue-create": [("POST", "repos/unit/public/issues", {"title": "clean", "body": "clean", "labels": ["unit"]})],
        "pr-create": [("POST", "repos/unit/public/pulls", {"title": "clean", "body": "clean", "head": "unit", "base": "main", "draft": False})],
        "pr-edit": [
            ("GET", "repos/unit/public/issues/1/labels", None),
            ("PATCH", "repos/unit/public/issues/1", {"title": "clean", "labels": ["unit"]}),
        ],
        "issue-close": [
            ("POST", "repos/unit/public/issues/1/comments", {"body": "clean"}),
            ("PATCH", "repos/unit/public/issues/1", {"state": "closed"}),
        ],
        "comment-edit": [
            ("GET", "repos/unit/public/issues/comments/7?per_page=100", None),
            ("GET", "user?per_page=100", None),
            ("PATCH", "repos/unit/public/issues/comments/7", {"body": "clean"}),
        ],
    }
    if verb in expected_requests:
        from lu_machinery.common.github_client import Response

        def transport(method, endpoint, headers, body, timeout):
            if verb == "comment-edit" and method == "GET":
                payload = {"login": "unit"} if endpoint.startswith("user?") else {"id": 7, "body": "previous", "user": {"login": "unit"}}
            else:
                payload = [{"name": "old"}] if method == "GET" else {}
            return Response(200, {}, json.dumps(payload).encode())

        requests = github_transport(transport)
        original_transport = pub._run_transport

        def observe(command, **kwargs):
            calls.append({"argv": command})
            return original_transport(command, **kwargs)

        monkeypatch.setattr(pub, "_run_transport", observe)
        sender = None
    assert pub.publish(verb, repo="unit/public", runner=sender, **fields).returncode == 0
    assert len(calls) == (3 if verb == "comment-edit" else 1)
    if verb in expected_requests:
        assert [
            (method, endpoint, json.loads(body) if body is not None else None)
            for method, endpoint, _headers, body, _timeout in requests
        ] == expected_requests[verb]


TEXT_CASES = [
    (verb, fields, key) for verb, fields in VERBS for key in fields if pub.SCHEMAS[verb][1][key] in {"text", "texts"}
]


@pytest.mark.parametrize("verb,fields,key", TEXT_CASES)
@pytest.mark.parametrize("payload", [TOKEN, TOKEN + "/unit", "--" + TOKEN, "123/" + TOKEN, "unit\n" + TOKEN])
def test_every_public_field_blocks_even_word_shaped(synthetic_opsec, verb, fields, key, payload, monkeypatch):
    stub_parent_epic(monkeypatch)
    fields = dict(fields)
    fields[key] = [payload] if pub.SCHEMAS[verb][1][key] == "texts" else payload
    calls = []
    with pytest.raises(pub.gate.PublishBlocked) as error:
        pub.publish(verb, repo="unit/public", runner=spy(calls, merge=verb == "pr-merge"), **fields)
    assert not calls and TOKEN not in str(error.value)
    assert "field=" in str(error.value) and "line=" in str(error.value)


@pytest.mark.parametrize("verb,fields", VERBS)
def test_closed_schema_rejects_payload_passthrough(verb, fields):
    with pytest.raises(gate.PublishBlocked, match="unknown publisher field"):
        pub.publish(
            verb,
            repo="unit/public",
            arbitrary_argv=["--body", TOKEN],
            runner=lambda *a, **k: pytest.fail("send"),
            **fields,
        )


@pytest.mark.parametrize(
    "fields",
    [
        {"number": "1"},
        {"number": True},
        {"number": -1},
        {"number": 1, "body": "x", "body_file": "x"},
        {"number": 1, "repo": "github.com/unit/private/extra"},
    ],
)
def test_schema_refuses_invalid_operands(fields):
    with pytest.raises(gate.PublishBlocked):
        pub.publish("issue-edit", runner=lambda *a, **k: pytest.fail("send"), **fields)


@pytest.mark.parametrize("verb", ["issue-comment", "pr-comment", "pr-review", "pr-merge", "pr-create", "comment-edit"])
@pytest.mark.parametrize("source_kind", ["absolute", "relative", "stdin"])
def test_body_inputs_are_frozen_and_transport_paths_not_scanned(
    synthetic_opsec, tmp_path, monkeypatch, verb, source_kind
):
    original = gate.check_texts
    body = tmp_path / "clean.md"
    body.write_bytes(b"clean\nexact UTF-8 \xc3\xa9\r\n")
    expected = body.read_bytes()

    scanned = []

    def check(dest, texts, **kw):
        scanned.extend(texts)
        original(dest, texts, **kw)
        body.write_text(TOKEN)

    monkeypatch.setattr(gate, "check_texts", check)
    fields = {"body_file": str(body) if source_kind == "absolute" else body.name if source_kind == "relative" else "-"}
    if verb == "pr-create":
        fields.update(title="clean", base="main", head="unit")
    elif verb == "comment-edit":
        fields["comment_id"] = 7
    else:
        fields["number"] = 1
    if verb == "pr-review":
        fields["verdict"] = "approve"
    calls = []
    pub.publish(verb, repo="unit/public", cwd=tmp_path, stdin=expected, runner=spy(calls, comment_edit=verb == "comment-edit", merge=verb == "pr-merge"), **fields)
    if verb == "pr-merge":
        # Queue admission carries only identity/head; the supplied body is still frozen and scanned.
        assert expected.decode("utf-8") in scanned
        assert TOKEN not in "".join(scanned)
        assert json.loads(calls[0]["--input"])["variables"] == {"id": "PR_fixture_1", "head": "a" * 40}
        assert not Path(calls[0]["argv"][calls[0]["argv"].index("--input") + 1]).exists()
        return
    flag = "--input" if verb == "comment-edit" else "--body-file"
    sent = calls[0][flag]
    if verb == "comment-edit":
        sent = json.loads(sent)["body"].encode("utf-8")
    assert sent == expected
    assert not Path(calls[0]["argv"][calls[0]["argv"].index(flag) + 1]).exists()


@pytest.mark.parametrize("comment_id", [0, -1, True, "7", None, 1.5, "7/../../issues/1"])
def test_comment_edit_invalid_id_cannot_mutate(comment_id):
    with pytest.raises(gate.PublishBlocked, match="invalid publisher field comment_id"):
        pub.publish("comment-edit", repo="unit/public", comment_id=comment_id, body="clean",
                    runner=lambda *a, **k: pytest.fail("send"))


@pytest.mark.parametrize("fields", [
    {"body": "clean"}, {"comment_id": 7},
    {"comment_id": 7, "body": "clean", "body_file": "reply.md"},
    {"comment_id": 7, "body": "clean", "number": 1},
])
def test_comment_edit_missing_or_conflicting_fields_cannot_mutate(fields):
    with pytest.raises(gate.PublishBlocked):
        pub.publish("comment-edit", repo="unit/public", **fields,
                    runner=lambda *a, **k: pytest.fail("send"))


@pytest.mark.parametrize("interface", ["python", "cli"])
def test_comment_edit_same_id_exact_body_and_failure_cleanup(synthetic_opsec, interface):
    body = "clean\r\nexact UTF-8 é\n--body=literal"
    calls = []

    def send(argv, **kwargs):
        if argv[3] == "GET":
            document = {"login": "unit"} if argv[4].startswith("user?") else {"id": 7, "body": "previous", "user": {"login": "unit"}}
            return subprocess.CompletedProcess(argv, 0, json.dumps(document), "")
        assert argv[:6] == ["gh", "api", "--method", "PATCH", "repos/unit/public/issues/comments/7", "--input"]
        payload_path = Path(argv[6])
        assert json.loads(payload_path.read_bytes()) == {"body": body}
        calls.append(payload_path)
        return subprocess.CompletedProcess(argv, 1, "", "fixture failure")

    if interface == "python":
        result = pub.publish("comment-edit", repo="unit/public", comment_id=7, body=body, runner=send)
        assert result.returncode == 1
    else:
        assert pub.main(["comment-edit", "--repo", "unit/public", "--comment-id", "7", "--body", body], runner=send) == 1
    assert len(calls) == 1 and not calls[0].exists()


@pytest.mark.parametrize("interface", ["python", "cli"])
@pytest.mark.parametrize("target,identity,status", [
    ({"id": 7, "body": "<!-- cf-verdict v1 verdict=CHANGES_REQUESTED -->", "user": {"login": "unit"}}, {"login": "unit"}, 0),
    ({"id": 7, "body": "clean", "user": {"login": "other"}}, {"login": "unit"}, 0),
    ({"id": 8, "body": "clean", "user": {"login": "unit"}}, {"login": "unit"}, 0),
    ({"id": 7, "body": None, "user": {"login": "unit"}}, {"login": "unit"}, 0),
    ({"id": 7, "body": "clean", "user": {}}, {"login": "unit"}, 0),
    ({"id": 7, "body": "clean", "user": {"login": "unit"}}, {}, 0),
    ({}, {}, 1),
    ([], [], 0),
])
def test_comment_edit_cannot_erase_verdict_or_mutate_unproved_owner(synthetic_opsec, interface, target, identity, status):
    writes = []

    def send(argv, **kwargs):
        if argv[3] == "GET":
            document = identity if argv[4].startswith("user?") else target
            return subprocess.CompletedProcess(argv, status, json.dumps(document), "fixture read failure")
        writes.append(argv)
        return subprocess.CompletedProcess(argv, 0, "{}", "")

    if interface == "python":
        with pytest.raises(gate.PublishBlocked):
            pub.publish("comment-edit", repo="unit/public", comment_id=7, body="replacement", runner=send)
    else:
        assert pub.main(["comment-edit", "--repo", "unit/public", "--comment-id", "7", "--body", "replacement"], runner=send) == 2
    assert writes == []


@pytest.mark.parametrize("verb", ["release-create", "release-upload", "gist-create"])
@pytest.mark.parametrize("content", [b"clean\n", TOKEN.encode(), b"\x1f\x8b\xffbinary"])
def test_artifacts_explicit_names_utf8_scanned_binary_releases_work(synthetic_opsec, tmp_path, verb, content):
    source = tmp_path / "source"
    source.write_bytes(content)
    fields = {"files" if verb == "gist-create" else "assets": [pub.Asset(source, "unit.bin")]}
    if verb != "gist-create":
        fields.update(repo="unit/public", tag="unit")
    calls = []
    if content == TOKEN.encode() or (verb == "gist-create" and content.startswith(b"\x1f")):
        with pytest.raises(gate.PublishBlocked):
            pub.publish(verb, runner=spy(calls), **fields)
        assert not calls
    else:
        pub.publish(verb, runner=spy(calls), **fields)
        assert calls[0]["artifacts"]["unit.bin"] == content


@pytest.mark.parametrize("verb", ["release-create", "release-upload", "gist-create"])
def test_artifact_names_block_and_files_are_not_reread(synthetic_opsec, tmp_path, monkeypatch, verb):
    source = tmp_path / "unit.bin"
    source.write_bytes(b"\xffunit" if verb != "gist-create" else b"clean")
    fields = {} if verb == "gist-create" else {"repo": "unit/public", "tag": "unit"}
    key = "files" if verb == "gist-create" else "assets"
    with pytest.raises(gate.PublishBlocked):
        pub.publish(verb, **fields, **{key: [pub.Asset(source, TOKEN)]}, runner=lambda *a, **k: pytest.fail("send"))
    original = gate.check_texts
    expected = source.read_bytes()

    def mutate(*a, **k):
        original(*a, **k)
        source.write_bytes(TOKEN.encode())

    monkeypatch.setattr(gate, "check_texts", mutate)
    calls = []
    pub.publish(verb, **fields, **{key: [pub.Asset(source)]}, runner=spy(calls))
    assert calls[0]["artifacts"]["unit.bin"] == expected


@pytest.mark.parametrize(
    "verb,fields",
    [
        ("issue-close", {"number": 1}),
        ("pr-review", {"number": 1, "verdict": "approve"}),
        ("pr-disarm", {"number": 1}),
    ],
)
def test_no_text_verbs_work_without_private_tooling(verb, fields, monkeypatch):
    monkeypatch.setattr(gate, "private_tooling", lambda: pytest.fail("must not load matcher"))
    calls = []
    pub.publish(verb, repo="unit/public", runner=spy(calls), **fields)
    assert len(calls) == 1


@pytest.mark.parametrize("payload", ["123", "a" * 40, "word/word", "--flag"])
def test_text_shape_never_disables_fail_closed(tmp_path, monkeypatch, payload):
    monkeypatch.setattr(gate, "private_tooling", lambda: tmp_path / "absent")
    with pytest.raises(gate.PublishBlocked, match="unavailable"):
        pub.publish(
            "issue-comment",
            number=1,
            body=payload,
            repo="unit/public",
            env={"LU_OPSEC_OVERRIDE": "reason"},
            runner=lambda *a, **k: pytest.fail("send"),
        )


@pytest.mark.parametrize("group", ["issue", "pr"])
@pytest.mark.parametrize("flag", ["--title", "-t", "--body", "--body-file", "--repo"])
@pytest.mark.parametrize("fake_verb", ["list", "view", "status"])
def test_round3_value_flag_hiding_real_verb_never_sends(group, flag, fake_verb):
    with pytest.raises(gate.PublishBlocked):
        gate.checked_run(
            ["gh", group, flag, fake_verb, "create", "--body", TOKEN],
            env={"GH_REPO": "unit/public"},
            runner=lambda *a, **k: pytest.fail("send"),
        )


@pytest.mark.parametrize("flag", ["-p", "-q", "--jq", "--header"])
def test_round3_api_endpoint_hiding_is_refused(flag):
    with pytest.raises(gate.PublishBlocked):
        gate.checked_run(
            [
                "gh",
                "api",
                flag,
                "graphql",
                "repos/unit/public/issues/1/comments",
                "-f",
                "body=" + TOKEN,
                "-f",
                "query={x}",
            ],
            runner=lambda *a, **k: pytest.fail("send"),
        )


@pytest.mark.parametrize(
    "args",
    [
        ["api", "--method", "GET", "-X", "POST", "repos/unit/public/issues?title=" + TOKEN],
        ["api", "graphql", "-f", "query=mutation{deleteIssue(input:{issueId:fixture}){clientMutationId}}"],
        ["alias", "list"],
        ["extension", "exec", "unit"],
        ["unit-alias", "view"],
        ["gist", "create", "--public", "unit.md"],
        ["workflow", "run", "ci.yml", "--json"],
    ],
)
def test_api_alias_extension_nonrepo_and_implicit_stdin_refused(args):
    with pytest.raises(gate.PublishBlocked):
        gate.checked_run(
            ["gh", *args], env={"GH_REPO": "unit/private"}, input=TOKEN, runner=lambda *a, **k: pytest.fail("send")
        )


@pytest.mark.parametrize("args", READ_COMMANDS)
def test_native_reads_preserve_original_arguments(args, tmp_path):
    calls = []
    gate.checked_run(["gh", *args], cwd=tmp_path, env={}, runner=spy(calls))
    assert [call["argv"] for call in calls] == [["gh", *args]]
    assert admit(args, cwd=tmp_path, environment={}).argv == args


@pytest.mark.parametrize("args", READ_COMMANDS)
@pytest.mark.parametrize(
    "extra",
    [
        ["--unknown"],
        ["--body", TOKEN],
        ["--json"],
        ["--web=true"],
        ["extra", "positional", "operands"],
        ["--", "create"],
    ],
)
def test_read_argument_errors_belong_to_native_gh(args, extra, tmp_path):
    calls = []
    if args[0] == "api" and extra in [["--unknown"], ["--body", TOKEN], ["--json"], ["--web=true"]]:
        with pytest.raises(gate.PublishBlocked):
            admit([*args, *extra], cwd=tmp_path, environment={})
    else:
        gate.checked_run(["gh", *args, *extra], cwd=tmp_path, env={}, runner=spy(calls))
        assert [call["argv"] for call in calls] == [["gh", *args, *extra]]


@pytest.mark.parametrize(
    "selectors,environment,allowed",
    [
        (["-R", "unit/public", "--repo", "unit/private"], {}, True),
        (["-R", "unit/private", "--repo", "unit/public"], {}, False),
        (["--repo=unit/private"], {"GH_REPO": "unit/public"}, True),
        ([], {"GH_REPO": "unit/private"}, True),
        ([], {"GH_REPO": "unit/private", "GH_HOST": "other.invalid"}, False),
        (["-R", "unit/private"], {"GH_REPO": "unit/private"}, False),
    ],
)
def test_private_destination_last_selector_and_resource_url(selectors, environment, allowed, tmp_path):
    target = "https://github.com/unit/public/issues/1" if len(selectors) == 2 else "1"
    args = ["gh", "issue", "comment", target, *selectors, "--body", TOKEN]
    calls = []
    if allowed:
        gate.checked_run(args, env=environment, cwd=tmp_path, runner=spy(calls))
        assert len(calls) == 1
    else:
        with pytest.raises(gate.PublishBlocked):
            gate.checked_run(args, env=environment, cwd=tmp_path, runner=spy(calls))
        assert not calls


@pytest.mark.parametrize(
    "operation,fields",
    [
        ("membership", {"number": 1}),
        ("queue-removal", {"number": 1}),
        ("queue-removal", {"number": 1, "cursor": 'cursor") { mutation {x} }'}),
        ("queue-snapshot", {"branches": ['unit") { mutation {x} }']}),
            ("squash-text", {"number": 1}),
    ],
)
def test_specific_graphql_reads_keep_variables_as_data(operation, fields):
    calls = []
    pub.read(operation, repo="unit/public", runner=spy(calls), **fields)
    payload = json.loads(calls[0]["--input"])
    assert payload["query"].startswith("query(")
    assert "--method" in calls[0]["argv"]


@pytest.mark.parametrize(
    "operation,fields",
    [
        ("identity", {}),
        ("issue", {"number": 1}),
        ("comments", {"number": 1}),
        ("checks", {"sha": "a" * 40}),
        ("commit", {"sha": "a" * 40}),
        ("runs", {"start": "2026-01-01", "end": "2026-01-02"}),
    ],
)
def test_specific_rest_reads_are_fixed_get_without_matcher(operation, fields, monkeypatch):
    monkeypatch.setattr(gate, "private_tooling", lambda: pytest.fail("matcher"))
    calls = []
    pub.read(operation, repo="unit/public", runner=spy(calls), **fields)
    assert calls[0]["argv"][2:4] == ["--method", "GET"]


def test_single_commit_read_is_bound_to_the_exact_sha():
    """#10531: app-bot authorship proof is read live from GitHub for one exact commit."""
    calls = []
    pub.read("commit", repo="unit/public", runner=spy(calls), sha="a" * 40)
    assert calls[0]["argv"][2:5] == ["--method", "GET", f"repos/unit/public/commits/{'a' * 40}?per_page=100"]


@pytest.mark.parametrize("sha", [None, "a" * 40])
def test_run_search_keeps_legacy_range_and_projects_optional_exact_sha(sha):
    """F3: bind the target at GitHub without changing existing range callers."""
    calls = []
    fields = {"start": "2026-01-01", "end": "2026-01-02"}
    if sha is not None:
        fields["sha"] = sha
    pub.request_run(pub.Request("read-runs", repo="unit/public", paginate=True, slurp=True, **fields), runner=spy(calls))
    selector = "" if sha is None else "&head_sha=" + sha
    assert calls[0]["argv"] == [
        "gh", "api", "--method", "GET",
        "repos/unit/public/actions/runs?event=merge_group&created=2026-01-01..2026-01-02"
        + selector + "&per_page=100", "--paginate", "--slurp",
    ]


@pytest.mark.parametrize("extra", [
    {"sha": "a" * 39}, {"sha": "g" * 40}, {"sha": "a" * 40 + "&status=success"},
    {"sha": None}, {"head_sha": "a" * 40}, {"sha": "a" * 40, "event": "push"},
    {"sha": "a" * 40, "endpoint": "user"}, {"sha": "a" * 40, "argv": ["--jq", "."]},
])
def test_run_search_rejects_selector_injection_and_unapproved_fields(extra):
    """The new selector cannot add arbitrary endpoint, event, argv or query authority."""
    with pytest.raises(gate.PublishBlocked):
        pub.read("runs", repo="unit/public", start="2026-01-01", end="2026-01-02",
                 runner=lambda *a, **k: pytest.fail("send"), **extra)


@pytest.mark.parametrize(
    "operation,fields",
    [
        ("comments", {"number": "1/comments?x=unit"}),
        ("checks", {"sha": "unit?x=y"}),
        ("commit", {"sha": "unit/check-runs"}),
        ("graphql", {"query": "mutation{x}"}),
        ("subissue-batch", {"cursors": {"unit": None}, "body_roots": set()}),
        ("membership", {"number": 1, "query": "mutation{x}"}),
        ("default-head", {"number": 1}),
        ("squash-text", {"number": 1, "query": "mutation{x}"}),
    ],
)
def test_typed_reads_refuse_arbitrary_documents_paths_and_fields(operation, fields):
    with pytest.raises(gate.PublishBlocked):
        pub.read(operation, repo="unit/public", runner=lambda *a, **k: pytest.fail("send"), **fields)


def test_publisher_cli_closed_schema_and_stdin(synthetic_opsec, monkeypatch):
    calls = []
    monkeypatch.setattr(pub, "_run_transport", spy(calls))
    assert (
        pub.main(["issue-comment", "--repo", "unit/public", "--number", "1", "--body", "clean"], runner=spy(calls)) == 0
    )
    with pytest.raises(SystemExit) as exc:
        pub.main(["issue-comment", "--number", "1", "--raw-argv", "unit"])
    assert exc.value.code == 2
    monkeypatch.setattr(sys, "stdin", type("Input", (), {"buffer": io.BytesIO(TOKEN.encode())})())
    assert pub.main(["issue-comment", "--repo", "unit/public", "--number", "1", "--body-file", "-"]) == 2
    assert len(calls) == 1


LINK_QUERY = "mutation($p:ID!,$c:ID!){addSubIssue(input:{issueId:$p,subIssueId:$c}){issue{number}}}"
LINK_PAYLOAD = json.dumps({"query": LINK_QUERY, "variables": {"p": "PARENT", "c": "CHILD"}}).encode()
LINK_ARGV = ["issue-link", "--repo", "unit/public", "--parent-id", "PARENT", "--child-id", "CHILD"]


UNLINK_QUERY = "mutation($p:ID!,$c:ID!){removeSubIssue(input:{issueId:$p,subIssueId:$c}){issue{number}}}"
UNLINK_PAYLOAD = json.dumps({"query": UNLINK_QUERY, "variables": {"p": "PARENT", "c": "CHILD"}}).encode()
UNLINK_ARGV = ["issue-unlink", "--repo", "unit/public", "--parent-id", "PARENT", "--child-id", "CHILD"]


def test_issue_unlink_cli_and_api_pin_argv_and_frozen_payload(synthetic_opsec):
    calls = []
    assert pub.main(UNLINK_ARGV, runner=spy(calls)) == 0
    result = pub.publish("issue-unlink", repo="unit/public", parent_id="PARENT", child_id="CHILD", runner=spy(calls))
    assert result.returncode == 0
    assert len(calls) == 2
    for call in calls:
        frozen = Path(call["argv"][6])
        assert call["argv"] == ["gh", "api", "--method", "POST", "graphql", "--input", str(frozen)]
        assert frozen.name == "request.json"
        assert call["--input"] == UNLINK_PAYLOAD
        assert call["env"]["GH_HOST"] == "github.com"
        assert not frozen.exists()


@pytest.mark.parametrize("missing", ["parent_id", "child_id"])
def test_issue_unlink_requires_both_node_ids(missing):
    fields = {"parent_id": "PARENT", "child_id": "CHILD"}
    fields.pop(missing)
    with pytest.raises(gate.PublishBlocked, match="required publisher field missing"):
        pub.publish("issue-unlink", repo="unit/public", runner=lambda *a, **k: pytest.fail("send"), **fields)


@pytest.mark.parametrize("key", ["parent_id", "child_id"])
@pytest.mark.parametrize("value", ["", None, 1, True, "NODE,replaceParent:true", "NODE}", "NODE\n", "NODE/other"])
def test_issue_unlink_refuses_malformed_node_ids(key, value):
    fields = {"parent_id": "PARENT", "child_id": "CHILD", key: value}
    with pytest.raises(gate.PublishBlocked, match=f"invalid publisher field {key}"):
        pub.publish("issue-unlink", repo="unit/public", runner=lambda *a, **k: pytest.fail("send"), **fields)


@pytest.mark.parametrize("extra", [{"replace_parent": True}, {"query": "mutation{x}"}, {"body": "clean"}])
def test_issue_unlink_refuses_extra_fields(extra):
    with pytest.raises(gate.PublishBlocked, match="unknown publisher field"):
        pub.publish(
            "issue-unlink",
            repo="unit/public",
            parent_id="PARENT",
            child_id="CHILD",
            runner=lambda *a, **k: pytest.fail("send"),
            **extra,
        )


@pytest.mark.parametrize("extra", [["--replace-parent"], ["--query", "mutation{x}"], ["--body", "clean"]])
def test_issue_unlink_cli_refuses_unknown_options(extra):
    with pytest.raises(SystemExit) as exc:
        pub.main([*UNLINK_ARGV, *extra], runner=lambda *a, **k: pytest.fail("send"))
    assert exc.value.code == 2


def test_issue_link_replace_parent_sends_typed_boolean_variable(synthetic_opsec):
    calls = []
    assert pub.main([*LINK_ARGV, "--replace-parent"], runner=spy(calls)) == 0
    payload = json.loads(calls[0]["--input"])
    assert payload["query"] == (
        "mutation($p:ID!,$c:ID!,$r:Boolean!)"
        "{addSubIssue(input:{issueId:$p,subIssueId:$c,replaceParent:$r}){issue{number}}}"
    )
    assert payload["variables"] == {"p": "PARENT", "c": "CHILD", "r": True}


@pytest.mark.parametrize("flags", [[], ["--no-replace-parent"]])
def test_issue_link_without_replace_parent_is_byte_identical(synthetic_opsec, flags):
    calls = []
    assert pub.main([*LINK_ARGV, *flags], runner=spy(calls)) == 0
    pub.publish(
        "issue-link", repo="unit/public", parent_id="PARENT", child_id="CHILD", replace_parent=False, runner=spy(calls)
    )
    assert [call["--input"] for call in calls] == [LINK_PAYLOAD, LINK_PAYLOAD]


@pytest.mark.parametrize(
    "fields",
    [
        {"parent_id": "PARENT,replaceParent:true", "child_id": "CHILD"},
        {"parent_id": "PARENT", "child_id": "CHILD}"},
        {"parent_id": "", "child_id": "CHILD"},
    ],
)
def test_issue_link_replace_parent_keeps_node_validation(fields):
    with pytest.raises(gate.PublishBlocked, match=r"invalid publisher field (parent|child)_id"):
        pub.publish(
            "issue-link", repo="unit/public", replace_parent=True, runner=lambda *a, **k: pytest.fail("send"), **fields
        )


@pytest.mark.parametrize("value", ["true", 1, None, "replaceParent:true"])
def test_issue_link_replace_parent_refuses_non_boolean_values(value):
    with pytest.raises(gate.PublishBlocked, match="invalid publisher field replace_parent"):
        pub.publish(
            "issue-link",
            repo="unit/public",
            parent_id="PARENT",
            child_id="CHILD",
            replace_parent=value,
            runner=lambda *a, **k: pytest.fail("send"),
        )


@pytest.mark.parametrize(
    "extra", [["--replace-parent=true"], ["--replace-parent", "--reparent"], ["--replace-parent", "--query", "x"]]
)
def test_issue_link_cli_refuses_valued_or_unknown_options(synthetic_opsec, extra):
    assert pub.main([*LINK_ARGV, "--replace-parent"], runner=spy([])) == 0
    with pytest.raises(SystemExit) as exc:
        pub.main([*LINK_ARGV, *extra], runner=lambda *a, **k: pytest.fail("send"))
    assert exc.value.code == 2


def test_real_matcher_absolute_body_binary_assets_and_overhead(tmp_path, monkeypatch):
    from tests.test_opsec_prepublish import real_tooling

    tooling = real_tooling()
    monkeypatch.setattr(gate, "private_tooling", lambda: tooling)
    body = tmp_path / "clean.md"
    body.write_text("a" * 10_240)
    asset = tmp_path / "unit.gz"
    asset.write_bytes(b"\x1f\x8b\xffunit")
    calls = []
    timings = []
    for _ in range(20):
        start = time.perf_counter()
        pub.publish("issue-comment", number=1, body_file=body, repo="unit/public", runner=spy(calls))
        timings.append((time.perf_counter() - start) * 1000)
    median = statistics.median(timings)
    print(f"typed writes real matcher median 20 x 10KB: {median:.3f} ms")
    assert median < 200 and len(calls) == 20
    pub.publish("release-upload", repo="unit/public", tag="unit", assets=[pub.Asset(asset)], runner=spy(calls))
    assert calls[-1]["artifacts"]["unit.gz"] == asset.read_bytes()


@pytest.mark.parametrize("body", [TOKEN, "clean\nexact UTF-8 é\n"])
def test_real_cli_with_spy_and_raw_shim_refusal(gh_shim_sandbox, tmp_path, body):
    root, shim, _ = gh_shim_sandbox
    executable = tmp_path / "real-gh"
    output = tmp_path / "outbound"
    executable.write_text(f"""#!{sys.executable}
import sys
from pathlib import Path
args = sys.argv[1:]
assert '--input' in args and args[args.index('--input')+1]=='-'
import json
payload=json.load(sys.stdin)
Path({str(output)!r}).write_bytes(payload['body'].encode())
print('HTTP/2.0 201 Created\\r\\nX-RateLimit-Remaining: 100\\r\\nX-RateLimit-Reset: 2000000000\\r\\n\\r\\n{{}}')
""")
    executable.chmod(0o755)
    source = tmp_path / "body.md"
    source.write_text(body)
    env = {"PATH": os.defpath, "AGENT_REAL_GH": str(executable),
           "LEARN_UKRAINIAN_PRIMARY_REPO_ROOT": str(root), "LU_PRODUCT_ROOT": str(root)}
    raw = subprocess.run(
        [str(shim), "issue", "comment", "1", "--body-file", str(source)],
        cwd=root,
        env=env,
        capture_output=True,
        text=True,
        timeout=10,
    )
    assert raw.returncode == 2 and not output.exists()
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "lu_machinery.publish",
            "issue-comment",
            "--number",
            "1",
            "--repo",
            "unit/public",
            "--body-file",
            str(source),
        ],
        cwd=root,
        env=env,
        capture_output=True,
        text=True,
        timeout=10,
    )
    if body == TOKEN:
        assert result.returncode == 2 and not output.exists()
        assert "field=body line=1" in result.stderr and TOKEN not in result.stderr
    else:
        assert result.returncode == 0, result.stderr
        assert output.read_bytes() == body.encode()


@pytest.mark.parametrize(
    "verb,fields", [("pr-merge", {"number": 1}), ("pr-review", {"number": 1, "verdict": "approve"})]
)
def test_production_transport_retains_worker_merge_approval_guard(synthetic_opsec, tmp_path, verb, fields):
    executable = tmp_path / "real-gh"
    output = tmp_path / "outbound"
    executable.write_text(f"#!/bin/sh\nprintf sent > '{output}'\n")
    executable.chmod(0o755)
    if verb == "pr-merge":
        with pytest.raises(gate.PublishBlocked, match="AGENT_NO_MERGE"):
            pub.publish(
                verb,
                repo="unit/public",
                env={"AGENT_NO_MERGE": "1"},
                runner=lambda *a, **k: pytest.fail("send"),
                **fields,
            )
        assert not output.exists()
        return
    result = pub.publish(
        verb,
        repo="unit/public",
        env={"PATH": os.defpath, "AGENT_REAL_GH": str(executable), "AGENT_NO_MERGE": "1"},
        capture_output=True,
        text=True,
        **fields,
    )
    assert result.returncode == 1 and not output.exists()


def test_production_override_logs_once_and_defers_frozen_write(synthetic_opsec, tmp_path, monkeypatch):
    monkeypatch.setattr(gate, "primary_root", lambda cwd=None: tmp_path)
    executable = tmp_path / "real-gh"
    state = tmp_path / "attempts"
    source = tmp_path / "body"
    source.write_text(TOKEN)
    executable.write_text(f"""#!{sys.executable}
import json,os,sys
from pathlib import Path
assert 'LU_OPSEC_OVERRIDE' not in os.environ
args=sys.argv[1:]
body=json.load(sys.stdin)['body']
state=Path({str(state)!r})
rows=json.loads(state.read_text()) if state.exists() else []
rows.append(body)
state.write_text(json.dumps(rows))
Path({str(source)!r}).write_text('changed')
if len(rows)==1:
    print('HTTP/2.0 429 Too Many Requests\\r\\nRetry-After: 60\\r\\n\\r\\n{{}}')
    sys.exit(1)
""")
    executable.chmod(0o755)
    result = pub.publish(
        "issue-comment",
        number=1,
        body_file=source,
        repo="unit/public",
        capture_output=True,
        text=True,
        env={
            "PATH": os.defpath,
            "AGENT_REAL_GH": str(executable),
            "LU_OPSEC_OVERRIDE": "synthetic retry",
            "AGENT_GH_SECONDARY_RATE_LIMIT_BACKOFF_SECONDS": "0",
            "AGENT_GH_SECONDARY_RATE_LIMIT_RETRIES": "1",
        },
    )
    assert result.returncode == 75, result.stderr
    assert json.loads(result.stdout)["error"] == "github_rate_limited"
    assert json.loads(state.read_text()) == [TOKEN]
    log = tmp_path / "batch_state/opsec/overrides.jsonl"
    assert len(log.read_text().splitlines()) == 1 and TOKEN not in log.read_text()


@pytest.mark.parametrize("verb,selector", [("issue-comment", {"number": 1}), ("comment-edit", {"comment_id": 7})])
def test_checker_exception_is_typed_and_never_sends(monkeypatch, verb, selector):
    def broken(*a, **k):
        raise RuntimeError(TOKEN)

    monkeypatch.setattr(gate, "check_texts", broken)
    with pytest.raises(gate.PublishBlocked, match="checker unavailable") as error:
        pub.publish(
            verb, repo="unit/public", **selector, body="clean", runner=lambda *a, **k: pytest.fail("send")
        )
    assert TOKEN not in str(error.value)


def test_issue_create_refuses_unreadable_acceptance_criterion_before_publishing(synthetic_opsec):
    body = "## Acceptance\n\n- [ ] **AC-01**: the lifecycle reads a dash, not a colon\n"
    with pytest.raises(gate.PublishBlocked, match="ACCEPTANCE_CRITERIA_REFUSED: line 3"):
        pub.publish("issue-create", repo="unit/public", title="clean", body=body, runner=lambda *a, **k: pytest.fail("send"))


def test_issue_create_without_parent_is_refused_before_publishing(synthetic_opsec, capsys):
    with pytest.raises(gate.PublishBlocked, match="PARENT_REQUIRED"):
        pub.publish("issue-create", repo="unit/public", title="clean", body="clean", runner=lambda *a, **k: pytest.fail("send"))
    code = pub.main(
        ["issue-create", "--repo", "unit/public", "--title", "clean", "--body", "clean"],
        runner=lambda *a, **k: pytest.fail("send"),
    )
    assert code == 2
    assert capsys.readouterr().err == (
        "issue-create requires --parent <stream epic issue number>; the new issue is linked to it. "
        "Nothing was created.\n"
    )


def test_registered_fleet_repository_without_stream_registry_receives_issue(synthetic_opsec, monkeypatch, capsys):
    """A registered fleet repository with no stream registry of its own can receive an issue."""
    catalog = {
        **CATALOG,
        "labs": {
            "github": "unit/labs",
            "default": False,
            "local_name": "labs-fixture",
            "role": "public-labs",
            "verdict_recorder": False,
        },
    }
    monkeypatch.setattr(gate, "catalog", lambda: catalog)
    scanned = []
    original = gate.check_texts

    def record(destination, texts, **kwargs):
        scanned.append(destination)
        return original(destination, texts, **kwargs)

    monkeypatch.setattr(gate, "check_texts", record)
    calls = []
    code = pub.main(
        ["issue-create", "--repo", "unit/labs", "--title", "clean", "--body", "clean"],
        runner=spy(calls),
    )
    captured = capsys.readouterr()
    assert code == 0, captured.err
    assert calls and calls[0]["argv"][:5] == ["gh", "issue", "create", "--repo", "unit/labs"]
    assert not any(part.startswith("--parent") for part in calls[0]["argv"])
    assert scanned == ["github.com/unit/labs"]
    assert "requires --parent" not in captured.err


def test_unregistered_repository_cannot_receive_publisher_issue(synthetic_opsec, capsys):
    """A repository absent from fleet_repos.yaml is refused before any write."""
    calls = []
    code = pub.main(
        ["issue-create", "--repo", "unit/stranger", "--title", "clean", "--body", "clean"],
        runner=spy(calls),
    )
    captured = capsys.readouterr()
    assert code == 2 and not calls
    assert "REPO_REFUSED" in captured.err
    assert "requires --parent" not in captured.err


def test_scanned_label_list_is_frozen(synthetic_opsec, monkeypatch):
    stub_parent_epic(monkeypatch)
    labels = ["unit"]
    original = gate.check_texts

    def mutate(*a, **k):
        original(*a, **k)
        labels[0] = TOKEN

    monkeypatch.setattr(gate, "check_texts", mutate)
    calls = []
    pub.publish(
        "issue-create", repo="unit/public", title="clean", body="clean", labels=labels, parent=10453, runner=spy(calls)
    )
    assert "--label=unit" in calls[0]["argv"] and TOKEN not in " ".join(calls[0]["argv"])


def test_verified_host_is_pinned_in_transport(synthetic_opsec):
    calls = []
    pub.publish(
        "issue-comment",
        repo="github.com/unit/private",
        number=1,
        body=TOKEN,
        env={"GH_HOST": "other.invalid", "GH_REPO": "unit/public"},
        runner=spy(calls),
    )
    assert calls[0]["env"]["GH_HOST"] == "github.com"
    assert calls[0]["argv"][calls[0]["argv"].index("--repo") + 1] == "unit/private"


@pytest.mark.parametrize(
    "consumer",
    [
        "bridge",
        "decision",
        "review-audit",
        "verify",
        "verdict",
        "review-publisher",
        "settle",
        "closeout",
        "keeper",
        "stream",
        "practice",
        "dataset",
        "manifest",
        "fmu",
    ],
)
def test_each_inventory_publisher_uses_module_and_never_sends_blocked_text(
    synthetic_opsec, publisher_transport, tmp_path, monkeypatch, consumer
):
    """Blocked text never reaches transport; the recorder can publish a scanned skeleton."""
    import importlib

    stub_parent_epic(monkeypatch)

    from lu_machinery.publish.github import Request

    monkeypatch.setenv("GH_REPO", "unit/public")
    calls = []
    payloads = []
    comments = []
    real_run = subprocess.run

    def transport(args, **kwargs):
        if args[:3] == ["gh", "release", "view"]:
            return subprocess.CompletedProcess(args, 1, "", "missing")
        if args[:3] == ["gh", "repo", "view"]:
            return subprocess.CompletedProcess(args, 0, '{"defaultBranchRef":{"name":"trunk"}}', "")
        if args[0] == "git":
            if consumer == "verdict":
                return real_run(args, **kwargs)
            return subprocess.CompletedProcess(args, 0, "https://github.com/unit/public.git", "")
        calls.append(args)
        if "--input" in args:
            payload = json.loads(Path(args[args.index("--input") + 1]).read_bytes())
            payloads.append(payload)
            assert TOKEN not in json.dumps(payload)
            if consumer == "verdict" and "repos/unit/public/issues/1/comments" in args:
                comment = {
                    "id": 101,
                    "body": payload["body"],
                    "user": {"login": "unit"},
                    "author_association": "MEMBER",
                    "created_at": "2026-01-01T00:00:01Z",
                    "updated_at": "2026-01-01T00:00:01Z",
                }
                comments.append(comment)
                return subprocess.CompletedProcess(args, 0, json.dumps(comment), "")
        if consumer == "verdict" and any(str(arg).startswith("repos/unit/public/pulls/1/files") for arg in args):
            # A readable file list: an unreadable one now keeps the second seat required (machinery #365).
            return subprocess.CompletedProcess(args, 0, json.dumps([[{"filename": "scripts/example.py", "status": "modified"}]]), "")
        if consumer == "verdict" and "repos/unit/public/issues/comments/101?per_page=100" in args:
            assert len(comments) == 1
            return subprocess.CompletedProcess(args, 0, json.dumps(comments[0]), "")
        return subprocess.CompletedProcess(args, 0, "{}", "")

    monkeypatch.setattr(subprocess, "run", transport)
    monkeypatch.setattr(pub.github_client, "run", transport)
    # Practice and dataset publishers send through the installed release.  # TRANSITIONAL-PKG3-B2
    monkeypatch.setattr(importlib.import_module("lu_machinery.common.github_client"), "run", transport)  # TRANSITIONAL-PKG3-B2
    artifact = tmp_path / "unit.gz"
    artifact.write_bytes(b"\xffunit")

    def invoke():
        if consumer == "bridge":
            assert not importlib.import_module("lu_machinery.ai_agent_bridge._github")._gh_comment(1, TOKEN)
        elif consumer == "decision":
            module = importlib.import_module("scripts.audit.check_decisions")
            assert (
                module.create_issue({"id": "unit", "title": TOKEN, "expires": "2026-01-01", "date": "2026-01-01"})
                is None
            )
        elif consumer == "review-audit":
            importlib.import_module("scripts.audit.check_review_issues")._comment_issue(1, TOKEN)
        elif consumer == "verify":
            importlib.import_module("lu_machinery.verify_review")._post_summary(1, {"final_disposition": TOKEN})
        elif consumer == "verdict":
            module = importlib.import_module("lu_machinery.review.record_cf_verdict")
            from lu_machinery.orchestration.fleet_repos import FleetRepo
            from lu_machinery.review import target_resolution

            real_run(["git", "init", "-q"], cwd=tmp_path, check=True, capture_output=True, timeout=30)
            real_run(
                ["git", "remote", "add", "origin", "https://github.com/unit/public.git"],
                cwd=tmp_path, check=True, capture_output=True, timeout=30,
            )
            repos = {"unit": FleetRepo("unit", "unit/public", tmp_path.name, "test", True)}
            monkeypatch.setattr(module, "load_fleet_repos", lambda: repos)
            monkeypatch.setattr(target_resolution, "load_fleet_repos", lambda: repos)
            monkeypatch.setattr(module, "_repo_root", lambda: tmp_path)
            # Exercise publication blocking independently of path rewriting.
            monkeypatch.setattr(module, "absolute_path_spans", lambda text: [])
            task = {
                "repository": "unit/public",
                "worktree_branch": "unit",
                "worktree_base_sha": "a" * 40,
                # The review seat's harness: the recorder qualifies the reviewer by route and model (#9739).
                "agent": "codex",
                "model": "gpt-6.1-sol",
                "started_at": "2026-01-01T00:00:00+00:00",
            }
            monkeypatch.setattr(
                module, "_task", lambda *a: (task, "VERDICT: APPROVE\n" + TOKEN + "\nHarmless reviewer prose.")
            )
            monkeypatch.setattr(module, "_pr", lambda *a: {"number": 1, "headRefName": "unit", "headRefOid": "a" * 40})
            # The recorder's complete-authorship entry point (#9739): an Anthropic-authored PR.
            facts = module.BranchReviewFacts(
                repository="unit/public",
                base_tip_sha="b" * 40,
                head_sha="a" * 40,
                merge_base_sha="b" * 40,
                commits=(module.CommitAttribution(None, "anthropic", "trailer-model"),),
                existing_families=frozenset({"anthropic"}),
                incoming_writer=None,
                incoming_family=None,
                changed_paths=(),
                owned_paths=(),
                subject_seats=frozenset(),
                subject_families=frozenset(),
                subject_evidence=(),
            )
            monkeypatch.setattr(module, "pr_review_facts", lambda *a, **k: facts)
            monkeypatch.setattr(module.GitHubAdapter, "identity", lambda *a: "unit")
            monkeypatch.setattr(module.GitHubAdapter, "comments", lambda *a: [])
            receipt = module.record("unit-review", pr_number=1, task_root=tmp_path, lock_root=tmp_path / "locks")
            assert receipt["head"] == "a" * 40
            assert receipt["verdict"] == "APPROVED"
            assert receipt["comment"] == receipt["status"] == "posted"
        elif consumer == "review-publisher":
            importlib.import_module("lu_machinery.fleet_comms.review_publisher").post_pr_comment(
                repository="unit/public", pr_number=1, body=TOKEN, runner=transport
            )
        elif consumer == "settle":
            module = importlib.import_module("lu_machinery.orchestration.dispatch_settle")
            monkeypatch.setattr(module, "_find_pr", lambda *a: (None, None))
            module.push_and_maybe_open_pr(tmp_path, "unit", open_pr=True, title=TOKEN, body="clean")
        elif consumer == "closeout":
            importlib.import_module("lu_machinery.orchestration.task_closeout").GhGitHubAdapter(tmp_path).update_issue_body(
                "unit/public", 1, TOKEN
            )
        elif consumer == "keeper":
            importlib.import_module("lu_machinery.orchestration.merge_queue_keeper").GitHub(tmp_path, "unit/public").comment(
                1, TOKEN
            )
        elif consumer == "stream":
            # Membership has no public text; fixed mutation succeeds without the matcher.
            importlib.import_module("lu_machinery.orchestration.issue_stream_audit")._gh_json(
                Request("issue-link", repo="unit/public", parent_id="PARENT", child_id="CHILD"), cwd=tmp_path
            )
        elif consumer == "practice":
            importlib.import_module("scripts.practice_deck.publish").upload_release_asset(
                artifact, repo="unit/public", release_tag="unit", asset_name=TOKEN
            )
        elif consumer in {"dataset", "practice"}:
            artifact.rename(tmp_path / TOKEN)
            importlib.import_module("scripts.open_dataset.publish").upload_release_asset(
                tmp_path / TOKEN, repo="unit/public", release_tag="unit"
            )
        elif consumer == "manifest":
            importlib.import_module("scripts.lexicon.publish_manifest").upload_release_asset(
                artifact, repo="unit/public", release_tag="unit", asset_name=TOKEN
            )
        elif consumer == "fmu":
            artifact.rename(tmp_path / TOKEN)
            importlib.import_module("scripts.lexicon.admit_fmu_boosters")._publish_asset(tmp_path / TOKEN)
        else:
            raise AssertionError(f"unknown consumer {consumer}")

    if consumer in {"bridge", "decision", "stream", "verdict"}:
        invoke()
    else:
        with pytest.raises((RuntimeError, ValueError)) as error:
            invoke()
        assert "blocked" in str(error.value)
    if consumer == "verdict":
        expected = (
            f"### Cross-family review\nhead: {'a' * 40}\nReviewer family: openai\nVERDICT: APPROVED\n"
            "Reviewer model: gpt-6.1-sol\nReview score: absent\nTask id: unit-review\n\nWithheld findings: unknown\n"
            "Findings are held privately.\n\n"
            f"<!-- cf-verdict v1 sha={'a' * 40} task=unit-review started=2026-01-01T00:00:00.000000+00:00 "
            "verdict=APPROVED model=gpt-6.1-sol family=openai -->"
        )
        assert len(calls) == 4
        assert all(args[:2] == ["gh", "api"] for args in calls)
        assert "repos/unit/public/pulls/1/files?per_page=100" in calls[0]
        assert "repos/unit/public/issues/1/comments" in calls[1]
        assert "repos/unit/public/issues/comments/101?per_page=100" in calls[2]
        assert f"repos/unit/public/statuses/{'a' * 40}" in calls[3]
        assert comments[0]["body"] == expected
        assert payloads == [
            {"body": expected},
            {
                "state": "success", "context": "fleet/cross-family-review",
                "description": "VERDICT: APPROVED openai unit-review",
            },
        ]
        gate.check_texts("github.com/unit/public", [expected], environment={})
        assert TOKEN not in expected and "Harmless reviewer prose." not in expected
    elif consumer == "stream":
        assert len(calls) == 1
        assert calls[0][:2] == ["gh", "api"]
        assert payloads[0]["query"].startswith("mutation($p:ID!,$c:ID!){addSubIssue")
    elif consumer in {"dataset", "practice"}:
        # Creating the clean release is allowed; uploading the blocked filename is not.
        assert len(calls) == 1 and calls[0][:3] == ["gh", "release", "create"]
    else:
        assert calls == []


@pytest.mark.parametrize("host,allowed", [("github.com", True), ("other.invalid", False)])
def test_raw_rest_private_exemption_requires_actual_endpoint_host(host, allowed):
    calls = []
    args = ["gh", "api", "repos/unit/private/issues/1/comments", "-f", "body=" + TOKEN, "--hostname", host]
    if allowed:
        gate.checked_run(args, runner=spy(calls))
        assert len(calls) == 1
    else:
        with pytest.raises(gate.PublishBlocked):
            gate.checked_run(args, runner=spy(calls))
        assert not calls


@pytest.mark.parametrize(
    "args,expected", [(["run", "watch", "1", "--compact"], 7), (["issue", "comment", "1", "--body", TOKEN], 2), (["api", "graphql", "-f", "query=mutation{deleteIssue(input:{issueId:fixture}){clientMutationId}}"], 2)]
)
def test_raw_entry_main_exact_admission(args, expected, tmp_path, monkeypatch, capsys):
    from lu_machinery.opsec import gh_entry

    executable = tmp_path / "real-gh"
    executable.write_text('#!/bin/sh\nprintf "%s\\n" "$@" > "' + str(tmp_path / "argv") + '"\nprintf "native gh error\\n" >&2\nexit 7\n')
    executable.chmod(0o755)
    monkeypatch.setattr(sys, "argv", ["entry", str(executable), str(files("lu_machinery").joinpath("agent_runtime/shims/gh")), *args])
    monkeypatch.setenv("GH_REPO", "unit/public")
    assert gh_entry.main() == expected
    stderr = capsys.readouterr().err
    assert TOKEN not in stderr
    if expected == 7:
        assert stderr == "native gh error\n"
        assert (tmp_path / "argv").read_text().splitlines() == args


def test_raw_entry_masks_unexpected_failure(tmp_path, monkeypatch, capsys):
    from lu_machinery.opsec import gh_entry

    executable = tmp_path / "real-gh"
    executable.write_text('#!/bin/sh\nprintf "HTTP/2.0 200 OK\\r\\nX-RateLimit-Remaining: 100\\r\\nX-RateLimit-Reset: 2000000000\\r\\n\\r\\n{}"\n')
    executable.chmod(0o755)
    monkeypatch.setattr(sys, "argv", ["entry", str(executable), "unit-shim", "pr", "list"])

    def broken(*a, **k):
        raise RuntimeError(TOKEN)

    monkeypatch.setattr(gh_entry, "admit", broken)
    assert gh_entry.main() == 2
    assert TOKEN not in capsys.readouterr().err


@pytest.mark.parametrize(
    "environment,explicit,origin,expected",
    [
        ({}, None, "https://github.com/unit/public.git", "github.com/unit/public"),
        ({"GH_REPO": "unit/private"}, None, "unit/public", "github.com/unit/private"),
        ({"GH_REPO": "unit/private"}, "unit/public", "unit/private", "github.com/unit/public"),
        ({}, None, "not-a-repository", "unknown"),
    ],
)
def test_repository_resolution_is_exact_and_ordered(environment, explicit, origin, expected, tmp_path):
    from lu_machinery.opsec.gh_snapshot import repository

    def local_read(args, **kwargs):
        return subprocess.CompletedProcess(args, 0, origin, "")

    assert repository(tmp_path, environment, explicit, local_read) == expected


def test_repository_read_failure_is_unknown(tmp_path):
    from lu_machinery.opsec.gh_snapshot import repository

    def broken(*a, **k):
        raise OSError(TOKEN)

    assert repository(tmp_path, {}, reader=broken) == "unknown"


@pytest.mark.parametrize(
    "path", ["/dev/null", "unit/../unit", "unit/extra/public/extra", "https://github.com/unit/private/issues/1"]
)
def test_repository_prefix_never_grants_private_exemption(path):
    assert not gate.is_private(gate.normalize_repository(path))


def test_real_matcher_cli_overhead_median_20_writes(gh_shim_sandbox, tmp_path):
    import shutil

    from tests.test_opsec_prepublish import real_tooling

    source = real_tooling()
    root, _shim, tooling = gh_shim_sandbox
    shutil.copyfile(source / "matcher.py", tooling / "matcher.py")
    shutil.copyfile(source / "rules.json", tooling / "rules.json")
    executable = tmp_path / "real-gh"
    executable.write_text('#!/bin/sh\nprintf "HTTP/2.0 200 OK\\r\\nX-RateLimit-Remaining: 5000\\r\\nX-RateLimit-Reset: 2000000000\\r\\n\\r\\n{}"\n')
    executable.chmod(0o755)
    body = tmp_path / "clean.md"
    body.write_text("a" * 10_240)
    timings = []
    for _ in range(20):
        start = time.perf_counter()
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "lu_machinery.publish",
                "issue-comment",
                "--repo",
                "unit/public",
                "--number",
                "1",
                "--body-file",
                str(body),
            ],
            cwd=root,
            env={"PATH": os.defpath, "AGENT_REAL_GH": str(executable),
                 "LEARN_UKRAINIAN_PRIMARY_REPO_ROOT": str(root), "LU_PRODUCT_ROOT": str(root)},
            capture_output=True,
            text=True,
            timeout=10,
        )
        assert result.returncode == 0, result.stderr
        timings.append((time.perf_counter() - start) * 1000)
    median = statistics.median(timings)
    print(f"CLI writes real matcher median 20 x 10KB: {median:.3f} ms")
    assert median < 200


@pytest.mark.parametrize(
    "reference",
    [
        "http://github.com/unit/public/issues/1",
        "https://github.com/unit/public/issues/1?unit",
        "https://github.com/unit/private/../public/issues/1",
        "ssh://unit/public/1",
        "unit:branch",
    ],
)
def test_raw_private_reference_cannot_hide_a_public_resource(reference):
    with pytest.raises(gate.PublishBlocked):
        gate.checked_run(
            ["gh", "issue", "comment", reference, "--repo", "unit/private", "--body", TOKEN],
            runner=lambda *a, **k: pytest.fail("send"),
        )


@pytest.mark.parametrize(
    "path",
    [
        "repos/unit/private/../../public/issues/1",
        "repos/unit/private/%2e%2e/public/issues/1",
        "repos/unit/private/issues/%2funit",
        "repositories/1/issues/1",
        "https://api.github.com/repos/unit/private/issues/1",
    ],
)
def test_raw_private_api_exemption_rejects_opaque_and_traversing_paths(path):
    with pytest.raises(gate.PublishBlocked):
        gate.checked_run(
            ["gh", "api", path, "-f", "body=" + TOKEN],
            env={"GH_REPO": "unit/private"},
            runner=lambda *a, **k: pytest.fail("send"),
        )


def test_release_download_stdout_operand_is_valid_read():
    calls = []
    gate.checked_run(
        ["gh", "release", "download", "unit", "-p", "unit.gz", "-O", "-", "--repo", "unit/public"], runner=spy(calls)
    )
    assert len(calls) == 1


@pytest.mark.parametrize(
    "args",
    [["pr-review", "--verdict", TOKEN], ["issue-comment", "--number", TOKEN], ["issue-comment", "--unknown", TOKEN]],
)
def test_cli_parse_errors_never_echo_values(args, capsys):
    with pytest.raises(SystemExit) as error:
        pub.main(args)
    assert error.value.code == 2
    stderr = capsys.readouterr().err
    assert TOKEN not in stderr and "OPSEC:" in stderr


@pytest.mark.parametrize("command", ["version", "--version"])
def test_exact_cli_version_read_needs_no_matcher(command):
    calls = []
    gate.checked_run(["gh", command], runner=spy(calls))
    assert len(calls) == 1
    with pytest.raises(gate.PublishBlocked):
        gate.checked_run(["gh", command, "--body", TOKEN], runner=lambda *a, **k: pytest.fail("send"))


def test_transport_timeout_and_checked_failure(tmp_path):
    with pytest.raises(subprocess.TimeoutExpired):
        pub._run_transport([sys.executable, "-c", "import time; time.sleep(30)"], timeout=0.05, capture_output=True)
    with pytest.raises(subprocess.CalledProcessError) as failure:
        pub._run_transport(
            [sys.executable, "-c", "import sys; print('unit'); sys.exit(3)"], check=True, capture_output=True, text=True
        )
    assert failure.value.returncode == 3 and failure.value.output == "unit\n"


def test_catalog_c_safe_loader_matches_safe_loader(tmp_path, monkeypatch):
    import yaml

    monkeypatch.undo()

    root = tmp_path / "catalog-root"
    target = root / "lu_machinery/config/fleet_repos.yaml"
    target.parent.mkdir(parents=True)
    content = "repos:\n  public:\n    github: unit/public\n    default: true\n"
    target.write_text(content)
    monkeypatch.setattr(gate, "_PACKAGE", root / "lu_machinery")
    assert gate.catalog() == yaml.safe_load(content)["repos"]
    with pytest.raises(gate.PublishBlocked):
        target.write_text("!!python/object:unit {}")
        gate.catalog()


def test_mutated_artifact_name_is_validated_before_snapshot(tmp_path, synthetic_opsec):
    source = tmp_path / "unit.bin"
    source.write_bytes(b"\xffunit")
    asset = pub.Asset(source)
    asset.name = "../unit.bin"
    calls = []
    with pytest.raises(gate.PublishBlocked, match="invalid artifact name"):
        pub.publish("release-upload", repo="unit/public", tag="unit", assets=[asset], runner=spy(calls))
    assert not calls


@pytest.mark.parametrize("fields", [{}, {"base": "main"}, {"head": "unit"}, {"base": "", "head": "unit"}])
def test_pr_creation_cannot_publish_implicit_branch_names(fields):
    calls = []
    with pytest.raises(gate.PublishBlocked):
        pub.publish("pr-create", repo="unit/public", title="clean", body="clean", runner=spy(calls), **fields)
    assert not calls


def test_9794_issue_parent_read_selects_typed_parent_repository(github_transport):
    from lu_machinery.common.github_client import Response

    issue = {
        "number": 1,
        "state": "open",
        "html_url": "https://github.com/unit/public/issues/1",
        "repository_url": "https://api.github.com/repos/unit/public",
    }
    parent_document = {
        "number": 7,
        "html_url": "https://github.com/other/stream/issues/7",
        "repository_url": "https://api.github.com/repos/other/stream",
    }

    def transport(method, endpoint, headers, body, timeout):
        assert method == "GET" and body is None
        payload = parent_document if endpoint.endswith("/parent") else issue
        return Response(200, {}, json.dumps(payload).encode())

    calls = github_transport(transport)
    result = pub.read("issue-parent", repo="unit/public", number=1, capture_output=True, text=True)
    assert result.returncode == 0
    parent = json.loads(result.stdout)["data"]["repository"]["issue"]["parent"]
    assert parent["number"] == 7
    assert parent["url"] == "https://github.com/other/stream/issues/7"
    assert parent["repository"]["nameWithOwner"] == "other/stream"
    assert [call[1] for call in calls] == [
        "repos/unit/public/issues/1",
        "repos/unit/public/issues/1/parent",
    ]


def test_keeper_issue_search_includes_unlabelled_open_issues():
    calls = []

    def send(argv, **kwargs):
        calls.append(argv)
        return subprocess.CompletedProcess(argv, 0, '[[{"number":11208,"body":"tests/test_unit.py::test_one"}]]', '')

    result = pub.read("issues", repo="unit/public", paginate=True, slurp=True, runner=send, env={})
    assert json.loads(result.stdout) == [[{"number": 11208, "body": "tests/test_unit.py::test_one"}]]
    assert calls == [["gh", "api", "--method", "GET", "repos/unit/public/issues?state=open&per_page=100", "--paginate", "--slurp"]]


def test_enqueue_returns_without_global_cleanup_inventory(synthetic_opsec, tmp_path, monkeypatch, capsys):
    """Global cleanup must not delay fresh enqueue or already-queued reconciliation."""
    _init_repo = _git_init_repo
    HEAD = _recovery_HEAD
    Transport = _recovery_Transport

    # Exercise the production closed read encoder and client, not an invented gh PR field.
    from tests.test_github_client import client, response

    row = {"number": 42, "state": "open", "head": {"sha": HEAD, "ref": "codex/fixture"},
           "base": {"ref": "main"}, "labels": []}
    store, calls = client(tmp_path / "typed-client", [response(row), response({"data": {"repository": {
        "pullRequest": {"isInMergeQueue": True, "mergeQueueEntry": {"headCommit": {"oid": "c" * 40}}}
    }}})])
    with monkeypatch.context() as patch:
        patch.setattr(pub.github_client, "GitHubClient", lambda **_kwargs: store)
        actual = pub.read("queue-status", repo="unit/public", number=42, branch="main",
                          capture_output=True, text=True)
    assert actual.returncode == 0, actual.stderr
    pull = json.loads(actual.stdout)["data"]["repository"]["pullRequest"]
    assert pull["headRefOid"] == HEAD and pull["isInMergeQueue"] is True
    assert pull["mergeQueueEntry"]["headCommit"]["oid"] != pull["headRefOid"]
    assert [call[1].split("?")[0] for call in calls] == ["repos/unit/public/pulls/42", "graphql"]

    for case in ("partial", "moved", "failed", "unknown", "already-queued"):
        root = tmp_path / case
        _init_repo(root)
        sender = Transport()
        sender.removed = False
        sender.queued = case == "already-queued"

        def transport(argv, sender=sender, case=case, **kwargs):
            graphql = argv[1:5] == ["api", "--method", "POST", "graphql"]
            query = json.loads(Path(argv[argv.index("--input") + 1]).read_text())["query"] if graphql else ""
            enqueue = query.startswith("mutation")
            if enqueue:
                if case == "unknown":
                    sender.failure = True
                elif case == "failed":
                    sender.writes.append(argv)
                    return subprocess.CompletedProcess(argv, 1, "raw refusal", "raw error")
            result = sender(argv, **kwargs)
            if enqueue:
                result.stdout, result.stderr = "raw enqueue success", "raw transport note"
            # The publisher proves the queue entry at the reviewed head right after the enqueue
            # (machinery #281); the head moves only once that proof has been read.
            if case == "moved" and query == pub.QUEUE_ENTRY_QUERY:
                sender.head = "b" * 40
            return result

        if case == "unknown":
            with pytest.raises(subprocess.TimeoutExpired):
                pub.publish("pr-merge", repo="unit/public", number=42, match_head=HEAD,
                            cwd=root, runner=transport)
            assert len(sender.writes) == 1
            assert not (root / "batch_state/enqueue-cleanup").exists()
            assert "enqueue-cleanup" not in capsys.readouterr().err
            continue
        result = pub.publish("pr-merge", repo="unit/public", number=42, match_head=HEAD,
                             cwd=root, runner=transport)
        if case == "failed":
            assert result.returncode == 1
            assert (result.stdout, result.stderr) == ("raw refusal", "raw error")
            assert len(sender.writes) == 1
        else:
            assert result.returncode == 0
            assert len(sender.writes) == (0 if case == "already-queued" else 1)
            if case == "already-queued":
                assert (result.stdout, result.stderr) == (b"", b"")
            else:
                assert (result.stdout, result.stderr) == ("raw enqueue success", "raw transport note")
        assert not hasattr(result, "enqueue_cleanup")
        assert not (root / "batch_state/enqueue-cleanup").exists()
        assert "enqueue-cleanup" not in capsys.readouterr().err


# --- issue-transfer (C-4682) ---------------------------------------------------------------

TRANSFER_CATALOG = {
    **CATALOG,
    "second": {"github": "unit/second", "role": "public-content", "local_name": "second-fixture"},
    "elsewhere": {"github": "other/private", "role": "private-infra", "local_name": "other-fixture"},
    "unroled": {"github": "unit/unroled", "role": "monorepo", "local_name": "unroled-fixture"},
}


class FakeTransferGitHub:
    """A synthetic GitHub with two repositories, issue #7 in unit/public and REST transfer redirects."""

    def __init__(self):
        self.repositories = {
            "unit/public": {"id": "R_PUBLIC", "nameWithOwner": "unit/public", "visibility": "PUBLIC",
                            "viewerPermission": "ADMIN", "isArchived": False, "labels": ["machinery", "triage"]},
            "unit/private": {"id": "R_PRIVATE", "nameWithOwner": "unit/private", "visibility": "PRIVATE",
                             "viewerPermission": "WRITE", "isArchived": False, "labels": ["bug", "machinery"]},
        }
        self.issues = {("unit/public", 7): {"node_id": "I_SOURCE", "state": "open", "labels": ["machinery", "triage"]}}
        self.redirects = {}
        self.mutations = []
        self.mutation_result = None
        self.failing_reads = set()
        self.failing_label_reads = set()
        self.after_mutation = None
        self.redirect_lag = 0
        self.stale = None

    def reply(self, args, code, document):
        return subprocess.CompletedProcess(args, code, json.dumps(document) if code == 0 else "", "" if code == 0 else "gh: failed")

    @staticmethod
    def page(labels, cursor, total=None):
        # One label per page proves the cursor loop reads every page.
        start = int(cursor or 0)
        return {"totalCount": len(labels) if total is None else total,
                "pageInfo": {"hasNextPage": start + 1 < len(labels), "endCursor": str(start + 1)},
                "nodes": [{"name": name} for name in labels[start:start + 1]]}

    def __call__(self, args, **kwargs):
        if args[:5] == ["gh", "api", "--method", "POST", "graphql"]:
            document = json.loads(Path(args[6]).read_text())
            if document["query"].startswith("mutation"):
                return self.transfer(args, document)
            variables = document["variables"]
            repository = f"{variables['owner']}/{variables['name']}"
            if "issue(number:" in document["query"]:
                # GraphQL never follows a transfer: only an issue's current repository answers.
                key = (repository, variables["number"])
                issue = self.issues.get(key)
                if key in self.failing_label_reads or issue is None:
                    return self.reply(args, 1, None)
                labels = self.page(issue["labels"], variables["cursor"], issue.get("totalCount"))
                return self.reply(args, 0, {"data": {"repository": {"issue": {"id": issue["node_id"], "labels": labels}}}})
            if repository in self.failing_reads or repository not in self.repositories:
                return self.reply(args, 1, None)
            live = dict(self.repositories[repository])
            labels = self.page(live.pop("labels"), variables["cursor"], live.pop("totalCount", None))
            return self.reply(args, 0, {"data": {"repository": {**live, "labels": labels}}})
        if args[:4] == ["gh", "api", "--method", "GET"]:
            match = re.fullmatch(r"repos/([a-z]+/[a-z]+)/issues/(\d+)", args[4].split("?", 1)[0])
            key = (match[1], int(match[2]))
            if key in self.failing_reads:
                return self.reply(args, 1, None)
            if self.stale and key == self.stale[0] and self.redirect_lag > 0:
                # GitHub can still serve the pre-transfer issue right after the mutation.
                self.redirect_lag -= 1
                issue, (repository, number) = self.stale[1], key
            else:
                key = self.redirects.get(key, key)
                issue = self.issues.get(key)
                if issue is None:
                    return self.reply(args, 1, None)
                repository, number = key
            document = {
                "number": number, "node_id": issue["node_id"], "state": issue["state"],
                "html_url": f"https://github.com/{repository}/{'pull' if issue.get('pull') else 'issues'}/{number}",
                "repository_url": f"https://api.github.com/repos/{repository}",
            }
            if issue.get("pull"):
                document["pull_request"] = {}
            return self.reply(args, 0, document)
        pytest.fail(f"unexpected GitHub call {args[:5]}")

    def transfer(self, args, document):
        self.mutations.append(document)
        if self.mutation_result is not None:
            return self.mutation_result(args)
        variables = document["variables"]
        source = next(key for key, issue in self.issues.items() if issue["node_id"] == variables["issue"])
        target = next(name for name, row in self.repositories.items() if row["id"] == variables["repository"])
        moved = self.issues.pop(source)
        self.stale = (source, dict(moved))
        kept = [label for label in moved["labels"] if label in self.repositories[target]["labels"]]
        self.issues[(target, 42)] = {"node_id": "I_MOVED", "state": moved["state"], "labels": kept}
        self.redirects[source] = (target, 42)
        if self.after_mutation:
            self.after_mutation()
        issue = {"id": "I_MOVED", "number": 42, "url": f"https://github.com/{target}/issues/42",
                 "repository": {"nameWithOwner": target}}
        return self.reply(args, 0, {"data": {"transferIssue": {"issue": issue}}})


@pytest.fixture
def transfer(monkeypatch, tmp_path):
    monkeypatch.setattr(gate, "catalog", lambda: TRANSFER_CATALOG)
    probes = []

    def probe(url):
        probes.append(url)
        return {"url": url, "final_url": url, "status": 404 if "/private/" in url else 200, "error": None}

    monkeypatch.setattr(pub, "_anonymous_probe", probe)
    fake = FakeTransferGitHub()
    fake.sleeps = []
    monkeypatch.setattr(pub, "_transfer_sleep", fake.sleeps.append)
    fake.probes, fake.receipts = probes, tmp_path / "receipts"

    def run(**fields):
        fields = {"repo": "public", "number": 7, "destination": "infra-private", **fields}
        return pub.publish("issue-transfer", runner=fake, receipt_dir=str(fake.receipts), capture_output=True,
                           text=True, **fields)

    fake.run = run
    return fake


def _receipts(directory):
    return [json.loads(path.read_text()) for path in sorted(directory.glob("*.json"))]


def test_issue_transfer_moves_one_issue_with_one_mutation_and_a_private_receipt(transfer):
    result = transfer.run()
    assert result.returncode == 0
    assert len(transfer.mutations) == 1
    mutation = transfer.mutations[0]
    assert "createLabelsIfMissing:false" in mutation["query"]
    assert mutation["variables"] == {"issue": "I_SOURCE", "repository": "R_PRIVATE"}
    (receipt,) = _receipts(transfer.receipts)
    assert json.loads(result.stdout) == receipt
    assert receipt["outcome"] == "transferred" and receipt["mutations_sent"] == 1
    assert receipt["source"]["url"] == "https://github.com/unit/public/issues/7"
    assert receipt["destination"] == {"alias": "infra-private", "repository": "unit/private", "number": 42,
                                      "url": "https://github.com/unit/private/issues/42", "node_id": "I_MOVED"}
    assert receipt["labels"] == {"source": ["machinery", "triage"], "destination_issue": ["machinery"],
                                 "dropped": ["triage"], "predicted_dropped": ["triage"]}
    assert [row["status"] for row in receipt["probes"]] == [200, 404]
    assert "does not prove confidentiality" in receipt["probe_note"]
    assert oct(transfer.receipts.stat().st_mode & 0o777) == "0o700"
    assert all(oct(path.stat().st_mode & 0o777) == "0o600" for path in transfer.receipts.iterdir())


def test_issue_transfer_second_call_is_idempotent_without_a_mutation(transfer):
    assert transfer.run().returncode == 0
    second = transfer.run(repo="unit/public")
    assert second.returncode == 0
    assert len(transfer.mutations) == 1
    receipt = json.loads(second.stdout)
    assert receipt["outcome"] == "already-transferred" and receipt["mutations_sent"] == 0
    assert receipt["destination"]["url"] == "https://github.com/unit/private/issues/42"


def test_issue_transfer_already_moved_closed_issue_is_still_idempotent(transfer):
    assert transfer.run().returncode == 0
    transfer.issues[("unit/private", 42)]["state"] = "closed"
    assert transfer.run().returncode == 0
    assert len(transfer.mutations) == 1


def test_issue_transfer_dry_run_reports_label_drops_without_a_mutation(transfer):
    result = transfer.run(dry_run=True)
    assert result.returncode == 0 and transfer.mutations == []
    receipt = json.loads(result.stdout)
    assert receipt["outcome"] == "dry-run" and receipt["labels"]["predicted_dropped"] == ["triage"]


@pytest.mark.parametrize(
    "fields,reason",
    [
        ({"repo": "unit/unregistered"}, "not exactly one repository registered"),
        ({"repo": "unknown-alias"}, "not exactly one repository registered"),
        ({"destination": "unknown-alias"}, "not exactly one repository registered"),
        ({"destination": "elsewhere"}, "same owner"),
        ({"destination": "public"}, "destination is the source"),
        ({"repo": "unit/public", "destination": "public"}, "destination is the source"),
        ({"repo": "infra-private", "destination": "public"}, "private-role repository never moves"),
        ({"repo": "unit/private", "destination": "second"}, "private-role repository never moves"),
        ({"destination": "unroled"}, "no public-/private- role"),
    ],
)
def test_issue_transfer_static_refusals_read_nothing(transfer, fields, reason):
    with pytest.raises(gate.PublishBlocked, match=reason):
        pub.publish("issue-transfer", **{"repo": "public", "number": 7, "destination": "infra-private", **fields},
                    receipt_dir=str(transfer.receipts), runner=lambda *a, **k: pytest.fail("read or write"))
    assert not transfer.receipts.exists()


@pytest.mark.parametrize("fields", [{"destination": "unit/private"}, {"repo": "-x"}, {"number": 0}, {"dry_run": "yes"}])
def test_issue_transfer_schema_refuses_malformed_fields(fields):
    with pytest.raises(gate.PublishBlocked, match="invalid publisher field"):
        pub.publish("issue-transfer", **{"repo": "public", "number": 7, "destination": "infra-private", **fields},
                    runner=lambda *a, **k: pytest.fail("send"))


def _drift(fake, side, **values):
    fake.repositories[side].update(values)


@pytest.mark.parametrize(
    "change,reason",
    [
        (lambda f: _drift(f, "unit/private", visibility="PUBLIC"), "destination repository's live visibility"),
        (lambda f: _drift(f, "unit/public", visibility="PRIVATE"), "source repository's live visibility"),
        (lambda f: _drift(f, "unit/private", visibility="INTERNAL"), "destination repository's live visibility"),
        (lambda f: _drift(f, "unit/public", nameWithOwner="unit/renamed"), "source repository's live identity"),
        (lambda f: _drift(f, "unit/private", viewerPermission="READ"), "cannot write to the destination"),
        (lambda f: _drift(f, "unit/public", viewerPermission=None), "cannot write to the source"),
        (lambda f: _drift(f, "unit/private", isArchived=True), "destination repository is archived"),
        (lambda f: _drift(f, "unit/private", totalCount=9), "repository read was unreadable"),
        (lambda f: _drift(f, "unit/public", id=None), "repository read was unreadable"),
        (lambda f: f.failing_reads.add("unit/private"), "repository read was unreadable"),
        (lambda f: f.issues.clear(), "source issue is missing"),
        (lambda f: f.failing_reads.add(("unit/public", 7)), "source issue is missing"),
        (lambda f: f.issues[("unit/public", 7)].update(state="closed"), "source issue is closed"),
        (lambda f: f.issues[("unit/public", 7)].update(pull=True), "is a pull request"),
        (lambda f: f.issues[("unit/public", 7)].update(node_id="bad id"), "source issue is missing, unreadable"),
        (lambda f: f.issues[("unit/public", 7)].update(totalCount=3), "labels are unreadable or incomplete"),
        (lambda f: f.failing_label_reads.add(("unit/public", 7)), "labels are unreadable or incomplete"),
        (lambda f: _drift(f, "unit/private", labels=["machinery", "machinery"]), "repository read was unreadable"),
        (lambda f: _drift(f, "unit/private", labels=["machinery", "Machinery"]), "repository read was unreadable"),
    ],
)
def test_issue_transfer_fresh_read_refusals_never_mutate(transfer, change, reason):
    change(transfer)
    with pytest.raises(gate.PublishBlocked, match=reason):
        transfer.run()
    assert transfer.mutations == []
    (receipt,) = _receipts(transfer.receipts)
    assert receipt["outcome"] == "refused" and receipt["mutations_sent"] == 0 and reason in receipt["detail"]


def test_issue_transfer_refuses_a_redirect_to_another_repository(transfer):
    moved = transfer.issues.pop(("unit/public", 7))
    transfer.issues[("unit/second", 3)] = moved
    transfer.redirects[("unit/public", 7)] = ("unit/second", 3)
    with pytest.raises(gate.PublishBlocked, match="redirects to a repository other than the destination"):
        transfer.run()
    assert transfer.mutations == []


@pytest.mark.parametrize(
    "result",
    [
        lambda args: subprocess.CompletedProcess(args, 1, "", "gh: timeout"),
        lambda args: subprocess.CompletedProcess(args, 0, "not json", ""),
        lambda args: subprocess.CompletedProcess(args, 0, json.dumps({"errors": [{"type": "FORBIDDEN"}]}), ""),
        lambda args: (_ for _ in ()).throw(subprocess.TimeoutExpired(args, 60)),
    ],
)
def test_issue_transfer_ambiguous_mutation_result_is_never_retried(transfer, result, capsys):
    transfer.mutation_result = result
    outcome = transfer.run()
    assert outcome.returncode == pub.TRANSFER_UNSETTLED == 3
    assert len(transfer.mutations) == 1
    receipt = json.loads(outcome.stdout)
    assert receipt["outcome"] == "ambiguous" and receipt["mutations_sent"] == 1
    assert "do not retry" in capsys.readouterr().err


@pytest.mark.parametrize(
    "break_after",
    [
        lambda f: f.failing_reads.add(("unit/public", 7)),
        lambda f: f.failing_label_reads.add(("unit/private", 42)),
        lambda f: f.issues[("unit/private", 42)].update(node_id="I_OTHER"),
        lambda f: f.issues[("unit/private", 42)].update(totalCount=5),
    ],
)
def test_issue_transfer_failed_verification_is_unsettled_without_a_second_mutation(transfer, break_after):
    transfer.after_mutation = lambda: break_after(transfer)
    outcome = transfer.run()
    assert outcome.returncode == 3 and len(transfer.mutations) == 1
    assert json.loads(outcome.stdout)["outcome"] == "unverified"


def test_issue_transfer_mutation_returning_another_repository_is_unverified(transfer):
    def elsewhere(args):
        issue = {"id": "I_X", "number": 5, "url": "https://example.invalid/x", "repository": {"nameWithOwner": "unit/x"}}
        return subprocess.CompletedProcess(args, 0, json.dumps({"data": {"transferIssue": {"issue": issue}}}), "")

    transfer.mutation_result = elsewhere
    outcome = transfer.run()
    receipt = json.loads(outcome.stdout)
    assert outcome.returncode == 3 and len(transfer.mutations) == 1
    assert receipt["outcome"] == "unverified" and receipt["destination"]["url"] is None
    assert transfer.probes == ["https://github.com/unit/public/issues/7"]


@pytest.mark.parametrize("where", ["inside", "shared", "relative"])
def test_issue_transfer_receipt_directory_must_be_private_and_outside_the_repository(transfer, tmp_path, where):
    from scripts.publish import github as product_publisher
    directory = {"inside": str(ROOT / "receipts"), "shared": str(tmp_path / "shared"), "relative": "receipts"}[where]
    if where == "shared":
        (tmp_path / "shared").mkdir(mode=0o755)
        (tmp_path / "shared").chmod(0o755)
    with pytest.raises(product_publisher.gate.PublishBlocked, match="receipt directory"):
        product_publisher.publish("issue-transfer", repo="public", number=7, destination="infra-private", receipt_dir=directory,
                    runner=lambda *a, **k: pytest.fail("read or write"))
    assert not (ROOT / "receipts").exists()


def test_issue_transfer_cli_exit_codes(transfer, capsys):
    argv = ["issue-transfer", "--repo", "public", "--number", "7", "--destination", "infra-private",
            "--receipt-dir", str(transfer.receipts)]
    assert pub.main([*argv, "--dry-run"], runner=transfer) == 0
    assert json.loads(capsys.readouterr().out)["outcome"] == "dry-run"
    assert pub.main([*argv[:-4], "--destination", "unit/private"], runner=transfer) == 2
    transfer.mutation_result = lambda args: subprocess.CompletedProcess(args, 1, "", "gh: failed")
    assert pub.main(argv, runner=transfer) == 3
    assert len(transfer.mutations) == 1


def test_issue_transfer_dry_run_on_a_moved_issue_sends_no_probe(transfer):
    assert transfer.run().returncode == 0
    probes = len(transfer.probes)
    result = transfer.run(dry_run=True)
    assert result.returncode == 0 and len(transfer.mutations) == 1
    receipt = json.loads(result.stdout)
    assert receipt["outcome"] == "already-transferred" and receipt["probes"] == [] and receipt["dry_run"] is True
    assert len(transfer.probes) == probes


def test_issue_transfer_failed_probe_after_the_mutation_is_unsettled(transfer, monkeypatch):
    monkeypatch.setattr(pub, "_anonymous_probe", lambda url: {"url": url, "final_url": None, "status": None,
                                                              "error": "TimeoutError"})
    outcome = transfer.run()
    receipt = json.loads(outcome.stdout)
    assert outcome.returncode == 3 and len(transfer.mutations) == 1
    assert receipt["outcome"] == "unverified" and receipt["detail"] == "an anonymous probe failed"


@pytest.mark.parametrize("failure", ["stdout", "cleanup"])
def test_issue_transfer_local_failure_after_the_mutation_exits_unsettled(transfer, monkeypatch, failure):
    if failure == "stdout":
        class Closed(io.StringIO):
            def write(self, text):
                raise BrokenPipeError

        monkeypatch.setattr(sys, "stdout", Closed())
    else:
        def refuse_cleanup(self, *args):
            raise PermissionError

        monkeypatch.setattr(pub.tempfile.TemporaryDirectory, "__exit__", refuse_cleanup)
    argv = ["issue-transfer", "--repo", "public", "--number", "7", "--destination", "infra-private",
            "--receipt-dir", str(transfer.receipts)]
    assert pub.main(argv, runner=transfer) == 3
    assert len(transfer.mutations) == 1
    (receipt,) = _receipts(transfer.receipts)
    assert receipt["mutations_sent"] == 1 and receipt["outcome"] in {"transferred", "unverified"}


def test_issue_transfer_scratch_failure_reserves_no_receipt(transfer, monkeypatch):
    def unavailable():
        raise OSError("scratch")

    monkeypatch.setattr(pub, "ensure_scratch_root", unavailable)
    with pytest.raises(OSError):
        transfer.run()
    assert transfer.mutations == [] and not transfer.receipts.exists()


def test_issue_transfer_receipt_is_created_in_the_checked_directory(transfer, tmp_path, monkeypatch):
    # A parent symlink swapped after the path check cannot move the receipt into a checkout.
    outside, checkout = tmp_path / "outside", tmp_path / "checkout"
    for root in (outside, checkout):
        (root / "receipts").mkdir(parents=True, mode=0o700)
    link = tmp_path / "link"
    link.symlink_to(outside)
    monkeypatch.setattr(pub, "_transfer_checkouts", lambda: [checkout.resolve()])
    real_open = os.open

    def swap_then_open(path, flags, *args, **kwargs):
        if flags & os.O_DIRECTORY:
            link.unlink()
            link.symlink_to(checkout)
        return real_open(path, flags, *args, **kwargs)

    monkeypatch.setattr(pub.os, "open", swap_then_open)
    with pytest.raises(gate.PublishBlocked, match="outside the repository"):
        pub.publish("issue-transfer", repo="public", number=7, destination="infra-private",
                    receipt_dir=str(link / "receipts"), runner=lambda *a, **k: pytest.fail("read or write"))
    assert not list((checkout / "receipts").iterdir()) and not list((outside / "receipts").iterdir())


@pytest.mark.parametrize("lag,code", [(6, 0), (len(pub.TRANSFER_VERIFY_DELAYS), 3)])
def test_issue_transfer_verification_waits_out_a_lagging_redirect_without_a_second_mutation(transfer, lag, code):
    transfer.redirect_lag = lag
    outcome = transfer.run()
    receipt = json.loads(outcome.stdout)
    assert outcome.returncode == code and len(transfer.mutations) == 1
    reads = min(lag + 1, len(pub.TRANSFER_VERIFY_DELAYS))
    assert receipt["verification_reads"] == reads and transfer.sleeps == list(pub.TRANSFER_VERIFY_DELAYS[:reads])
    if code == 0:
        assert receipt["outcome"] == "transferred" and receipt["labels"]["dropped"] == ["triage"]
    else:
        assert receipt["outcome"] == "unverified"
        assert receipt["detail"] == "the source URL does not resolve to the returned issue"
        assert sum(transfer.sleeps) == 180


def test_ruleset_merge_queue_changes_only_the_named_parameter(synthetic_opsec, capsys):
    """A ruleset write that edits another field, or reports success when the read-back differs, would ship.

    The defect is a merge-queue edit that also changes enforcement, another rule, an unnamed
    parameter, or a ruleset field the verb does not know how to preserve.
    """
    from scripts.publish import github as publisher

    assert [name for name in publisher.SCHEMAS if "ruleset" in name] == ["ruleset-merge-queue"]
    parameters = {
        "check_response_timeout_minutes": 60,
        "grouping_strategy": "ALLGREEN",
        "max_entries_to_build": 2,
        "max_entries_to_merge": 4,
        "merge_method": "SQUASH",
        "min_entries_to_merge": 1,
        "min_entries_to_merge_wait_minutes": 0,
    }
    document = {
        "id": 20977023,
        "name": "main-merge-queue",
        "target": "branch",
        "source_type": "Repository",
        "source": "unit/public",
        "enforcement": "active",
        "node_id": "NODE",
        "created_at": "2026-01-01T00:00:00Z",
        "updated_at": "2026-01-01T00:00:00Z",
        "_links": {"self": {"href": "https://api.github.com/repos/unit/public/rulesets/20977023"}},
        "current_user_can_bypass": "never",
        "bypass_actors": [],
        "conditions": {"ref_name": {"exclude": [], "include": ["refs/heads/main"]}},
        "rules": [{"type": "deletion"}, {"type": "merge_queue", "parameters": parameters}],
    }
    endpoint = "repos/unit/public/rulesets/20977023"

    def serve(document, *, apply):
        calls, sent = [], {}
        state = json.loads(json.dumps(document))

        def runner(args, **kwargs):
            method = args[args.index("--method") + 1]
            assert args[args.index("--method") + 2] == endpoint
            calls.append(method)
            if method == "GET":
                return subprocess.CompletedProcess(args, 0, json.dumps(state), "")
            if method == "PUT":
                sent["body"] = json.loads(Path(args[args.index("--input") + 1]).read_text())
                if apply:
                    state.update(sent["body"])
                return subprocess.CompletedProcess(args, 0, "", "")
            raise AssertionError(method)

        return runner, calls, sent

    runner, calls, sent = serve(document, apply=True)
    assert publisher.main(
        ["ruleset-merge-queue", "--repo", "unit/public", "--ruleset", "20977023",
         "--min-entries-to-merge-wait-minutes", "10"],
        runner=runner,
    ) == 0
    report = json.loads(capsys.readouterr().out)
    expected = {**parameters, "min_entries_to_merge_wait_minutes": 10}
    body = sent["body"]
    assert calls == ["GET", "PUT", "GET"]
    assert set(body) == {"name", "target", "enforcement", "bypass_actors", "conditions", "rules"}
    assert body["enforcement"] == "active" and body["conditions"] == document["conditions"]
    assert body["rules"][0] == {"type": "deletion"}
    assert body["rules"][1]["parameters"] == expected
    assert report == {"merge_queue": expected, "repo": "unit/public", "ruleset": 20977023}

    def refused(args, **kwargs):
        raise AssertionError("transport")

    with pytest.raises(publisher.gate.PublishBlocked, match="unknown publisher field"):
        publisher.publish(
            "ruleset-merge-queue", repo="unit/public", ruleset=20977023,
            min_entries_to_merge_wait_minutes=10, enforcement="disabled", runner=refused,
        )
    with pytest.raises(publisher.gate.PublishBlocked, match="invalid publisher field min_entries_to_merge_wait_minutes"):
        publisher.publish(
            "ruleset-merge-queue", repo="unit/public", ruleset=20977023,
            min_entries_to_merge_wait_minutes=361, runner=refused,
        )
    with pytest.raises(publisher.gate.PublishBlocked, match="explicit merge queue fields"):
        publisher.publish("ruleset-merge-queue", repo="unit/public", ruleset=20977023, runner=refused)
    with pytest.raises(SystemExit) as exc:
        publisher.main(
            ["ruleset-merge-queue", "--repo", "unit/public", "--ruleset", "20977023",
             "--min-entries-to-merge-wait-minutes", "10", "--enforcement", "disabled"],
            runner=refused,
        )
    assert exc.value.code == 2

    def before_put(document):
        calls = []

        def runner(args, **kwargs):
            method = args[args.index("--method") + 1]
            calls.append(method)
            if method == "PUT":
                raise AssertionError("put")
            return subprocess.CompletedProcess(args, 0, json.dumps(document), "")

        return runner, calls

    preserved = json.loads(json.dumps(document))
    preserved["future_field"] = True
    runner, calls = before_put(preserved)
    with pytest.raises(publisher.gate.PublishBlocked, match="does not preserve"):
        publisher.publish(
            "ruleset-merge-queue", repo="unit/public", ruleset=20977023,
            min_entries_to_merge_wait_minutes=10, runner=runner,
        )
    assert calls == ["GET"]

    missing = json.loads(json.dumps(document))
    del missing["rules"][1]["parameters"]["max_entries_to_build"]
    runner, calls = before_put(missing)
    with pytest.raises(publisher.gate.PublishBlocked, match="not on this ruleset"):
        publisher.publish(
            "ruleset-merge-queue", repo="unit/public", ruleset=20977023,
            max_entries_to_build=2, runner=runner,
        )
    assert calls == ["GET"]

    duplicate = json.loads(json.dumps(document))
    duplicate["rules"].append({"type": "merge_queue", "parameters": dict(parameters)})
    runner, calls = before_put(duplicate)
    with pytest.raises(publisher.gate.PublishBlocked, match="no single merge_queue rule"):
        publisher.publish(
            "ruleset-merge-queue", repo="unit/public", ruleset=20977023,
            min_entries_to_merge_wait_minutes=10, runner=runner,
        )
    assert calls == ["GET"]

    runner, calls, sent = serve(document, apply=False)
    assert publisher.main(
        ["ruleset-merge-queue", "--repo", "unit/public", "--ruleset", "20977023",
         "--min-entries-to-merge-wait-minutes", "10"],
        runner=runner,
    ) == 3
    assert calls == ["GET", "PUT", "GET"] and "Do not retry" in capsys.readouterr().err
    assert sent["body"]["rules"][1]["parameters"]["min_entries_to_merge_wait_minutes"] == 10

    def readback(second_get):
        calls = []

        def runner(args, **kwargs):
            method = args[args.index("--method") + 1]
            calls.append(method)
            if method == "GET" and calls.count("GET") == 1:
                return subprocess.CompletedProcess(args, 0, json.dumps(document), "")
            if method == "PUT":
                return subprocess.CompletedProcess(args, 0, "", "")
            if method == "GET":
                return second_get(args)
            raise AssertionError(method)

        return runner, calls

    def rate_limited(args):
        return subprocess.CompletedProcess(
            args, 75, json.dumps({"error": "github_rate_limited", "reset_at": 1}), "",
        )

    runner, calls = readback(rate_limited)
    assert publisher.main(
        ["ruleset-merge-queue", "--repo", "unit/public", "--ruleset", "20977023",
         "--min-entries-to-merge-wait-minutes", "10"],
        runner=runner,
    ) == 3
    assert calls == ["GET", "PUT", "GET"] and "Do not retry" in capsys.readouterr().err

    def broken(args):
        raise RuntimeError("read-back transport")

    runner, calls = readback(broken)
    assert publisher.main(
        ["ruleset-merge-queue", "--repo", "unit/public", "--ruleset", "20977023",
         "--min-entries-to-merge-wait-minutes", "10"],
        runner=runner,
    ) == 3
    assert calls == ["GET", "PUT", "GET"] and "Do not retry" in capsys.readouterr().err

    with pytest.raises(SystemExit) as exc:
        publisher.main(["ruleset-merge-queue", "--help"])
    assert exc.value.code == 0
    assert "A rate limit on that read-back is exit 3, not 75" in capsys.readouterr().out
