"""Branch-pinned verdict recorder failure and serialization tests (#8509)."""

from __future__ import annotations

import hashlib
import json
import os
import shlex
import subprocess
import zlib
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import pytest

from scripts.common.git_context import GIT_REDIRECT_ENV_KEYS
from scripts.review import record_cf_verdict as recorder

SHA = "a" * 40
OTHER = "b" * 40
BRANCH = "codex/42"
REPOSITORY = "owner/repo"


@pytest.fixture(autouse=True)
def recorder_matcher(synthetic_opsec):
    from tests.opsec_fixtures import synthetic_rules

    rules = synthetic_rules(rule="3-absolute-path", level=3, pattern=r"(?<![<\w:])/[A-Za-z][^\s`'\"<>),;\]}|*]*")
    (synthetic_opsec / "rules.json").write_text(json.dumps(rules))


@pytest.fixture
def citation_checkout(tmp_path):
    root = tmp_path / "checkout"
    worktree = root / ".worktrees/dispatch/cursor/review"
    for checkout in (root, worktree):
        for name in ("scripts/unit.py", "tests/test_unit.py", "scripts/before.py", "scripts/after.py"):
            path = checkout / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text("# citation fixture\n" * 20)
        (checkout / "a").mkdir()
    return root, worktree


def task(**updates):
    data = {
        "repository": REPOSITORY,
        "worktree_branch": BRANCH,
        "worktree_base_sha": SHA,
        "model": "gpt-6.1-sol",
        "agent": "codex",
        "started_at": "2026-09-23T12:00:00.000001+00:00",
        "status": "done",
    }
    data.update(updates)
    return data


def write_task(root: Path, *, task_id="review-one", reply="VERDICT: APPROVE", **updates):
    root.mkdir(parents=True, exist_ok=True)
    (root / task_id).parent.mkdir(parents=True, exist_ok=True)
    (root / f"{task_id}.json").write_text(json.dumps(task(**updates)))
    (root / f"{task_id}.result").write_text(reply)


@pytest.mark.parametrize(
    "reply,expected",
    [
        ("VERDICT: APPROVE", "APPROVED"),
        ("VERDICT: APPROVED", "APPROVED"),
        ("VERDICT: REQUEST_CHANGES", "CHANGES_REQUESTED"),
        ("VERDICT: CHANGES_REQUESTED", "CHANGES_REQUESTED"),
        ("VERDICT: BLOCKED", "BLOCKED"),
    ],
)
def test_token_normalization(reply, expected):
    assert recorder.normalize_verdict(reply) == expected


def test_full_nested_task_id_is_safe_and_loadable(tmp_path):
    write_task(tmp_path, task_id="codex/review-one")
    loaded, reply = recorder._task("codex/review-one", tmp_path)
    assert loaded["status"] == "done"
    assert reply == "VERDICT: APPROVE"
    with pytest.raises(recorder.RecordError, match="invalid task id"):
        recorder._task("codex/../review-one", tmp_path)


def test_repo_root_timeout_fails_closed(monkeypatch):
    def timeout(*args, **kwargs):
        assert kwargs["timeout"] == 30
        raise subprocess.TimeoutExpired(args[0], kwargs["timeout"])

    monkeypatch.setattr(recorder.subprocess, "run", timeout)
    with pytest.raises(recorder.RecordError, match="Git repository lookup timed out after 30 seconds"):
        recorder._repo_root()


@pytest.mark.parametrize("reply", ["No verdict", "VERDICT: APPROVE\nVERDICT: BLOCKED"])
def test_missing_or_ambiguous_verdict_refused(reply):
    with pytest.raises(recorder.RecordError, match="missing or ambiguous"):
        recorder.normalize_verdict(reply)


@pytest.mark.parametrize(
    "updates,reply,reason",
    [
        ({"status": "running"}, "VERDICT: APPROVE", "not done"),
        ({"worktree_branch": None}, "VERDICT: APPROVE", "--branch"),
        ({"worktree_base_sha": None}, "VERDICT: APPROVE", "reviewed SHA"),
        (
            {"agent": "cursor", "resolved_model_known": False, "resolved_model": "unknown"},
            "VERDICT: APPROVE",
            "Cursor reviewer model unknown",
        ),
        ({}, "VERDICT: APPROVE\nVERDICT: BLOCKED", "ambiguous"),
        ({}, "No verdict", "missing"),
        # #9583: a model the catalog gives no review role never approves, on any harness.
        ({"agent": "claude", "model": "claude-fable-5-1"}, "VERDICT: APPROVE", "holds no review"),
        ({"agent": "claude", "model": "claude-fable-5-1[1m]"}, "VERDICT: APPROVE", "holds no review"),
        (
            {
                "agent": "cursor",
                "resolved_model_known": True,
                "resolved_model": "claude-fable-5-1-thinking-high",
                "resolved_model_source": "cursor-stream-json",
            },
            "VERDICT: APPROVE",
            "is not a formal reviewer on this harness",
        ),
        ({"agent": "codex", "model": "gpt-6-astra"}, "VERDICT: APPROVE", "retired in the model catalog"),
    ],
)
def test_task_refusals_before_network(tmp_path, updates, reply, reason):
    tasks = tmp_path / "tasks"
    write_task(tasks, reply=reply, **updates)
    with pytest.raises(recorder.RecordError, match=reason):
        recorder.record("review-one", task_root=tasks, lock_root=tmp_path / "locks")


@pytest.mark.parametrize("risk", [None, "low", "medium", "high", "critical"])
@pytest.mark.parametrize(
    "agent,model,family", [("claude", "claude-opus-5-5", "anthropic"), ("codex", "gpt-6.1-sol", "openai")]
)
def test_formal_reviewer_still_admits_opus_and_sol(agent, model, family, risk):
    recorder._require_formal_reviewer(
        {"review_risk": risk}, agent=agent, requested=model, reported=model, model=model, family=family
    )


def setup_record(monkeypatch, tmp_path, *, head=SHA, branch=BRANCH, families=None, status_error=False):
    tasks = tmp_path / "tasks"
    write_task(tasks)
    comments = []
    calls = {"posts": 0, "statuses": 0}

    def fake_json(args, *, input_text=None):
        from scripts.publish.github import Request

        if isinstance(args, Request):
            if args.verb == "issue-comment-json":
                input_text = json.dumps({"body": args.fields["body"]})
                args = ["gh", "api", "-X", "POST"]
            elif args.verb == "read-comment":
                args = ["gh", "api", "issues/comments/" + str(args.fields["number"])]
            else:
                raise AssertionError(args.verb)
        if args[:3] == ["gh", "pr", "view"]:
            return {"number": 42, "headRefOid": head, "headRefName": branch, "state": "OPEN"}
        if args[:3] == ["gh", "pr", "list"]:
            return [{"number": 42, "headRefOid": head, "headRefName": branch}]
        if args[:4] == ["gh", "api", "-X", "POST"]:
            calls["posts"] += 1
            item = {
                "id": calls["posts"],
                "body": json.loads(input_text)["body"],
                "user": {"login": "fleet"},
                "author_association": "MEMBER",
                "created_at": "2026-09-23T13:00:00Z",
                "updated_at": "2026-09-23T13:00:00Z",
            }
            comments.append(item)
            return item
        if args[:2] == ["gh", "api"] and "issues/comments/" in args[2]:
            return comments[-1]
        raise AssertionError(args)

    monkeypatch.setattr(recorder, "_run_json", fake_json)
    monkeypatch.setattr(
        recorder,
        "author_families",
        lambda repository, number, task_root: families if families is not None else {"google"},
    )
    monkeypatch.setattr(recorder.GitHubAdapter, "identity", lambda self: "fleet")
    monkeypatch.setattr(recorder.GitHubAdapter, "comments", lambda self, repository, number: list(comments))

    def fake_status(**kwargs):
        calls["statuses"] += 1
        if status_error:
            raise RuntimeError("status write failed")

    monkeypatch.setattr(recorder, "post_commit_status", fake_status)
    return tasks, comments, calls


def test_head_and_branch_mismatch_refused(monkeypatch, tmp_path):
    tasks, _, _ = setup_record(monkeypatch, tmp_path, head=OTHER)
    with pytest.raises(recorder.RecordError, match="head moved"):
        recorder.record("review-one", pr_number=42, task_root=tasks, lock_root=tmp_path / "locks")
    tasks, _, _ = setup_record(monkeypatch, tmp_path, branch="other/branch")
    with pytest.raises(recorder.RecordError, match="branch does not match"):
        recorder.record("review-one", pr_number=42, task_root=tasks, lock_root=tmp_path / "locks")


def test_same_family_refused(monkeypatch, tmp_path):
    tasks, _, _ = setup_record(monkeypatch, tmp_path, families={"google", "openai"})
    with pytest.raises(recorder.RecordError, match="equals an author family"):
        recorder.record("review-one", pr_number=42, task_root=tasks, lock_root=tmp_path / "locks")


def test_rerun_same_task_reconciles_status_without_new_comment(monkeypatch, tmp_path):
    tasks, comments, calls = setup_record(monkeypatch, tmp_path)
    first = recorder.record("review-one", pr_number=42, task_root=tasks, lock_root=tmp_path / "locks")
    second = recorder.record("review-one", pr_number=42, task_root=tasks, lock_root=tmp_path / "locks")
    assert first["comment"] == "posted"
    assert second["comment"] == "existing"
    assert calls == {"posts": 1, "statuses": 2}
    assert len(comments) == 1
    assert comments[0]["body"].splitlines()[-1].startswith("<!-- cf-verdict v1 sha=")


def test_status_failure_keeps_comment_and_reports_partial(monkeypatch, tmp_path):
    tasks, comments, _ = setup_record(monkeypatch, tmp_path, status_error=True)
    result = recorder.record("review-one", pr_number=42, task_root=tasks, lock_root=tmp_path / "locks")
    assert result["comment"] == "posted"
    assert result["status"].startswith("failed:")
    assert len(comments) == 1


def test_override_for_flagged_comment_still_posts_clean_status(monkeypatch, tmp_path, synthetic_opsec):
    """Both publications pass the real gate; the override covers only the flagged comment (#9678)."""
    from scripts.fleet_comms import review_publisher
    from scripts.opsec import prepublish as gate
    from tests.opsec_fixtures import TOKEN, synthetic_rules

    rules = json.loads((synthetic_opsec / "rules.json").read_text())
    rules.update({k: v for k, v in synthetic_rules().items() if k == "1"})
    (synthetic_opsec / "rules.json").write_text(json.dumps(rules))
    monkeypatch.setattr(gate, "primary_root", lambda cwd=None: tmp_path)
    monkeypatch.setenv("LU_OPSEC_OVERRIDE", "synthetic false positive")
    tasks, comments, _ = setup_record(monkeypatch, tmp_path)
    write_task(tasks, reply="VERDICT: APPROVE\n" + TOKEN)
    sent = []

    def transport(argv, **kwargs):
        sent.append(argv)
        return subprocess.CompletedProcess(argv, 0, stdout="{}", stderr="")

    bookkeeping = recorder._run_json

    def comment_through_gate(args, *, input_text=None):
        if getattr(args, "verb", None) == "issue-comment-json":
            assert recorder.request_run(args, runner=transport, capture_output=True, text=True).returncode == 0
        return bookkeeping(args, input_text=input_text)

    monkeypatch.setattr(recorder, "_run_json", comment_through_gate)
    monkeypatch.setattr(
        recorder,
        "post_commit_status",
        lambda **kwargs: review_publisher.post_commit_status(**kwargs, runner=transport),
    )
    result = recorder.record("review-one", pr_number=42, task_root=tasks, lock_root=tmp_path / "locks")
    assert result["comment"] == "posted" and result["status"] == "posted"
    assert len(sent) == 2 and TOKEN in comments[0]["body"]
    (row,) = [json.loads(line) for line in (tmp_path / "batch_state/opsec/overrides.jsonl").read_text().splitlines()]
    assert row["rule_ids"] == ["synthetic-rule"] and row["destination"] == "github.com/" + REPOSITORY


def test_concurrent_recorders_for_same_sha_serialize(monkeypatch, tmp_path):
    tasks, comments, calls = setup_record(monkeypatch, tmp_path)
    with ThreadPoolExecutor(max_workers=2) as executor:
        futures = [
            executor.submit(recorder.record, "review-one", pr_number=42, task_root=tasks, lock_root=tmp_path / "locks")
            for _ in range(2)
        ]
        results = [future.result() for future in futures]
    assert {result["comment"] for result in results} == {"posted", "existing"}
    assert calls["posts"] == 1
    assert len(comments) == 1


def test_two_tasks_on_one_sha_each_get_a_comment(monkeypatch, tmp_path):
    tasks, comments, calls = setup_record(monkeypatch, tmp_path)
    write_task(
        tasks, task_id="review-two", reply="VERDICT: CHANGES_REQUESTED", started_at="2026-09-23T12:00:01.000001+00:00"
    )
    recorder.record("review-one", pr_number=42, task_root=tasks, lock_root=tmp_path / "locks")
    recorder.record("review-two", pr_number=42, task_root=tasks, lock_root=tmp_path / "locks")
    assert len(comments) == 2
    assert calls["posts"] == 2


def test_mixed_or_unknown_author_family_refused(monkeypatch, tmp_path):
    tasks = tmp_path / "tasks"
    tasks.mkdir()

    def commit(trailer):
        return {"commit": {"message": f"work\n\nX-Agent: {trailer}"}}

    monkeypatch.setattr(
        recorder, "_pages", lambda args: [commit("codex/gpt-6.1-sol"), commit("agy/gemini-3.8-flash-high")]
    )
    assert recorder.author_families(REPOSITORY, 42, tasks) == {"openai", "google"}
    monkeypatch.setattr(recorder, "_pages", lambda args: [commit("cursor/task-without-record")])
    with pytest.raises(recorder.RecordError, match="provenance unavailable"):
        recorder.author_families(REPOSITORY, 42, tasks)


@pytest.fixture
def real_commit_set(monkeypatch, tmp_path):
    """Build Git objects and PR commit listings without mocking the merge proof."""
    repo = tmp_path / "git-repo"
    repo.mkdir()
    monkeypatch.chdir(repo)
    for key in os.environ:
        if key.startswith("GIT_"):
            monkeypatch.delenv(key, raising=False)
    monkeypatch.setenv("GIT_CONFIG_GLOBAL", os.devnull)
    monkeypatch.setenv("GIT_CONFIG_NOSYSTEM", "1")

    def git(*args, check=True):
        return subprocess.run(["git", *args], cwd=repo, capture_output=True, text=True, check=check, timeout=30)

    def commit(path, content, message):
        (repo / path).write_text(content)
        git("add", path)
        git("commit", "-m", message)
        return git("rev-parse", "HEAD").stdout.strip()

    def build(case):
        git("init", "-b", "base")
        git("config", "user.name", "Fixture Author")
        git("config", "user.email", "fixture@example.invalid")
        git("config", "core.hooksPath", os.devnull)
        root = commit("shared.txt", "original\n", "root\n\nX-Agent: claude/claude-opus-5-5")
        git("checkout", "-b", "head")
        conflict = case in {"conflict_resolution", "union_resolution"}
        author = commit("shared.txt" if conflict else "head.txt", "authored\n", "work\n\nX-Agent: codex/gpt-6.1-sol")
        git("checkout", "base")
        base = commit(
            "shared.txt" if conflict else "base.txt", "base fix\n", "base fix\n\nX-Agent: claude/claude-opus-5-5"
        )
        git("checkout", "head")
        if case == "ordinary_untrailered":
            commit("extra.txt", "unattributed\n", "ordinary commit")
        elif case == "nonbase_merge":
            git("checkout", "-b", "other", root)
            commit("other.txt", "other branch\n", "other work\n\nX-Agent: agy/gemini-3.8-flash-high")
            git("checkout", "head")
            git("merge", "--no-ff", "other", "-m", "merge other branch")
        elif conflict:
            assert git("merge", "--no-ff", "base", "-m", "update branch", check=False).returncode == 1
            resolution = "authored\nbase fix\n" if case == "union_resolution" else "authored resolution\n"
            commit("shared.txt", resolution, "resolved merge")
        elif case != "all_trailered":
            git("merge", "--no-ff", "--no-commit", "base")
            if case == "dirty_merge":
                commit("extra.txt", "authored during merge\n", "update branch")
            else:
                git("commit", "-m", "update branch")
            tree = git("rev-parse", "HEAD^{tree}").stdout.strip()
            if case == "reversed_parents":
                head = git("commit-tree", tree, "-p", base, "-p", author, "-m", "reversed merge").stdout.strip()
                git("update-ref", "refs/heads/head", head)
            elif case == "octopus_merge":
                head = git(
                    "commit-tree", tree, "-p", author, "-p", base, "-p", root, "-m", "octopus merge"
                ).stdout.strip()
                git("update-ref", "refs/heads/head", head)
            elif case == "older_base_merge":
                git("checkout", "base")
                base = commit("later.txt", "later base\n", "later\n\nX-Agent: claude/claude-opus-5-5")
                git("checkout", "head")
        head = git("rev-parse", "HEAD").stdout.strip()
        commits = [
            {
                "sha": sha,
                "commit": {
                    "message": git("show", "--no-patch", "--format=%B", sha).stdout,
                    "tree": {"sha": git("show", "--no-patch", "--format=%T", sha).stdout.strip()},
                },
                "parents": [{"sha": parent} for parent in git("show", "--no-patch", "--format=%P", sha).stdout.split()],
            }
            for sha in git("rev-list", "--reverse", f"{base}..{head}").stdout.splitlines()
        ]
        monkeypatch.setattr(recorder, "_pages", lambda args: commits)

        def base_lookup(args, **kwargs):
            assert args == ["gh", "pr", "view", "42", "--repo", REPOSITORY, "--json", "baseRefOid"]
            return {"baseRefOid": base}

        monkeypatch.setattr(recorder, "_run_json", base_lookup)
        return git, commits, head, base

    return build


@pytest.mark.parametrize(
    "case,accepted",
    [
        ("all_trailered", True),
        ("clean_update_merge", True),
        ("conflict_resolution", False),
        ("nonbase_merge", False),
        ("ordinary_untrailered", False),
        ("dirty_merge", False),
        ("reversed_parents", False),
        ("octopus_merge", False),
        ("older_base_merge", True),
    ],
)
def test_author_commit_sets_with_real_git(real_commit_set, tmp_path, case, accepted):
    real_commit_set(case)
    if accepted:
        assert recorder.author_families(REPOSITORY, 42, tmp_path) == {"openai"}
    else:
        with pytest.raises(recorder.RecordError, match="missing explicit X-Agent"):
            recorder.author_families(REPOSITORY, 42, tmp_path)


def test_clean_update_merge_records_exact_head_review(real_commit_set, monkeypatch, tmp_path):
    _, _, head, base = real_commit_set("clean_update_merge")
    author_families = recorder.author_families
    tasks, comments, calls = setup_record(monkeypatch, tmp_path, head=head)
    write_task(tasks, worktree_base_sha=head, model="claude-opus-5-5", agent="claude")
    monkeypatch.setattr(recorder, "author_families", author_families)
    fake_json = recorder._run_json

    def with_base(args, **kwargs):
        if isinstance(args, list) and args[-2:] == ["--json", "baseRefOid"]:
            return {"baseRefOid": base}
        return fake_json(args, **kwargs)

    monkeypatch.setattr(recorder, "_run_json", with_base)
    monkeypatch.setattr(recorder, "_repo_root", lambda: Path.cwd())
    result = recorder.record("review-one", pr_number=42, task_root=tasks, lock_root=tmp_path / "locks")
    assert result["head"] == head
    assert result["verdict"] == "APPROVED"
    assert calls == {"posts": 1, "statuses": 1}
    assert f"sha={head}" in comments[0]["body"]


@pytest.mark.parametrize("missing", ["commit", "base"])
def test_clean_merge_missing_objects_refuses(real_commit_set, monkeypatch, tmp_path, missing):
    _, commits, _, _ = real_commit_set("clean_update_merge")
    if missing == "commit":
        commits[-1]["sha"] = "c" * 40
    else:
        monkeypatch.setattr(recorder, "_run_json", lambda args: {"baseRefOid": "c" * 40})
    reason = "base object not available locally; fetch and retry" if missing == "base" else "missing explicit X-Agent"
    with pytest.raises(recorder.RecordError, match=reason):
        recorder.author_families(REPOSITORY, 42, tmp_path)


@pytest.mark.parametrize("base", [None, "main", "", {"sha": SHA}])
def test_clean_merge_unknown_base_refuses(real_commit_set, monkeypatch, tmp_path, base):
    real_commit_set("clean_update_merge")
    monkeypatch.setattr(recorder, "_run_json", lambda args: {"baseRefOid": base})
    with pytest.raises(recorder.RecordError, match="PR base SHA unavailable"):
        recorder.author_families(REPOSITORY, 42, tmp_path)


@pytest.mark.parametrize("sha", [None, "main", "--help"])
def test_clean_merge_missing_or_invalid_sha_refuses(real_commit_set, tmp_path, sha):
    _, commits, _, _ = real_commit_set("clean_update_merge")
    commits[-1]["sha"] = sha
    with pytest.raises(recorder.RecordError, match="missing explicit X-Agent"):
        recorder.author_families(REPOSITORY, 42, tmp_path)


@pytest.mark.parametrize("trailer", ["X-Agent:", "X-Agent: codex/unknown model", "X-Agent: codex/unknown-task"])
def test_clean_merge_bad_attribution_is_not_exempted(real_commit_set, tmp_path, trailer):
    _, commits, _, _ = real_commit_set("clean_update_merge")
    commits[-1]["commit"]["message"] += f"\n{trailer}\n"
    with pytest.raises(recorder.RecordError):
        recorder.author_families(REPOSITORY, 42, tmp_path)


def test_clean_merge_still_refuses_same_family_reviewer(real_commit_set, monkeypatch, tmp_path):
    _, _, head, base = real_commit_set("clean_update_merge")
    author_families = recorder.author_families
    tasks, _, calls = setup_record(monkeypatch, tmp_path, head=head)
    write_task(tasks, worktree_base_sha=head)
    monkeypatch.setattr(recorder, "author_families", author_families)
    fake_json = recorder._run_json
    monkeypatch.setattr(
        recorder,
        "_run_json",
        lambda args, **kwargs: (
            {"baseRefOid": base}
            if isinstance(args, list) and args[-2:] == ["--json", "baseRefOid"]
            else fake_json(args, **kwargs)
        ),
    )
    with pytest.raises(recorder.RecordError, match="reviewer family equals an author family"):
        recorder.record("review-one", pr_number=42, task_root=tasks, lock_root=tmp_path / "locks")
    assert calls == {"posts": 0, "statuses": 0}


@pytest.mark.parametrize("failure", [OSError("Git unavailable"), subprocess.TimeoutExpired("git", 30)])
def test_clean_merge_git_unavailable_refuses(real_commit_set, monkeypatch, tmp_path, failure):
    real_commit_set("clean_update_merge")

    def fail(*args, **kwargs):
        raise failure

    monkeypatch.setattr(recorder.subprocess, "run", fail)
    with pytest.raises(recorder.RecordError, match="missing explicit X-Agent"):
        recorder.author_families(REPOSITORY, 42, tmp_path)


def test_only_exempt_merges_prove_no_author_family(real_commit_set, tmp_path):
    _, commits, _, _ = real_commit_set("clean_update_merge")
    commits[:] = commits[-1:]
    with pytest.raises(recorder.RecordError, match="no attributed author commits"):
        recorder.author_families(REPOSITORY, 42, tmp_path)


@pytest.mark.parametrize("target", ["merge", "first_parent"])
def test_git_replace_cannot_hide_authored_merge_changes(real_commit_set, tmp_path, target):
    git, commits, head, base = real_commit_set("dirty_merge")
    parents = git("show", "--no-patch", "--format=%P", head).stdout.split()
    clean_tree = git("merge-tree", "--write-tree", *parents).stdout.strip()
    clean = git("commit-tree", clean_tree, "-p", parents[0], "-p", parents[1], "-m", "clean").stdout.strip()
    if target == "merge":
        git("replace", head, clean)
    else:
        tree = commits[-1]["commit"]["tree"]["sha"]
        helper = git("commit-tree", tree, "-p", parents[0], "-m", "unlisted helper").stdout.strip()
        git("replace", parents[0], helper)
    assert not recorder._is_clean_base_merge(commits[-1], base)
    with pytest.raises(recorder.RecordError, match="missing explicit X-Agent"):
        recorder.author_families(REPOSITORY, 42, tmp_path)


def test_local_merge_driver_cannot_launder_conflict_resolution_or_execute(real_commit_set, tmp_path):
    git, commits, _, base = real_commit_set("conflict_resolution")
    parents = [parent["sha"] for parent in commits[-1]["parents"]]
    assert git("merge-tree", "--write-tree", *parents, check=False).returncode == 1
    marker = tmp_path / "driver-ran"
    git("config", "merge.evil.driver", f"printf 'authored resolution\\n' > %A; touch {shlex.quote(str(marker))}")
    attributes = Path(git("rev-parse", "--git-path", "info/attributes").stdout.strip())
    attributes.write_text("shared.txt merge=evil\n")
    # The unisolated command both launders the resolution and runs the shell.
    assert git("merge-tree", "--write-tree", *parents).stdout.strip() == commits[-1]["commit"]["tree"]["sha"]
    assert marker.exists()
    marker.unlink()
    assert not recorder._is_clean_base_merge(commits[-1], base)
    assert not marker.exists()
    with pytest.raises(recorder.RecordError, match="missing explicit X-Agent"):
        recorder.author_families(REPOSITORY, 42, tmp_path)
    assert not marker.exists()


@pytest.mark.parametrize("source", ["count", "parameters", "global", "system"])
def test_injected_git_config_cannot_execute_merge_driver(real_commit_set, monkeypatch, tmp_path, source):
    git, commits, _, base = real_commit_set("conflict_resolution")
    attributes = tmp_path / "injected-attributes"
    attributes.write_text("shared.txt merge=evil\n")
    marker = tmp_path / "driver-ran"
    settings = {
        "core.attributesFile": str(attributes),
        "merge.evil.driver": f"printf 'authored resolution\\n' > %A; touch {shlex.quote(str(marker))}",
    }
    if source == "count":
        monkeypatch.setenv("GIT_CONFIG_COUNT", str(len(settings)))
        for index, (key, value) in enumerate(settings.items()):
            monkeypatch.setenv(f"GIT_CONFIG_KEY_{index}", key)
            monkeypatch.setenv(f"GIT_CONFIG_VALUE_{index}", value)
    elif source == "parameters":
        monkeypatch.setenv(
            "GIT_CONFIG_PARAMETERS",
            git("rev-parse", "--sq-quote", *(f"{key}={value}" for key, value in settings.items())).stdout.strip(),
        )
    else:
        config = tmp_path / "injected-config"
        config.write_text(
            f'[core]\n\tattributesFile = {attributes}\n[merge "evil"]\n'
            f"\tdriver = {json.dumps(settings['merge.evil.driver'])}\n"
        )
        monkeypatch.setenv(f"GIT_CONFIG_{source.upper()}", str(config))
        if source == "system":
            monkeypatch.delenv("GIT_CONFIG_NOSYSTEM")
    parents = [parent["sha"] for parent in commits[-1]["parents"]]
    assert git("merge-tree", "--write-tree", *parents).stdout.strip() == commits[-1]["commit"]["tree"]["sha"]
    assert marker.exists()
    marker.unlink()
    assert not recorder._is_clean_base_merge(commits[-1], base)
    assert not marker.exists()


@pytest.mark.parametrize("source", ["info", "worktree", "global_config", "xdg"])
def test_local_attributes_cannot_launder_conflict_resolution(real_commit_set, monkeypatch, tmp_path, source):
    git, commits, _, base = real_commit_set("union_resolution")
    parents = [parent["sha"] for parent in commits[-1]["parents"]]
    assert git("merge-tree", "--write-tree", *parents, check=False).returncode == 1
    if source == "info":
        attributes = Path(git("rev-parse", "--git-path", "info/attributes").stdout.strip())
    elif source == "worktree":
        attributes = Path.cwd() / ".gitattributes"
    else:
        attributes = tmp_path / "xdg/git/attributes"
        attributes.parent.mkdir(parents=True)
        if source == "global_config":
            config = tmp_path / "global-config"
            config.write_text(f"[core]\n\tattributesFile = {attributes}\n")
            monkeypatch.setenv("GIT_CONFIG_GLOBAL", str(config))
        else:
            monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / "xdg"))
    attributes.write_text("shared.txt merge=union\n")
    assert git("merge-tree", "--write-tree", *parents).stdout.strip() == commits[-1]["commit"]["tree"]["sha"]
    assert not recorder._is_clean_base_merge(commits[-1], base)


@pytest.mark.parametrize(
    "key",
    [
        *GIT_REDIRECT_ENV_KEYS,
        "GIT_CONFIG_COUNT",
        "GIT_CONFIG_PARAMETERS",
        "GIT_ATTR_SOURCE",
        "GIT_TEMPLATE_DIR",
        "GIT_TRACE",
    ],
)
def test_inherited_git_environment_cannot_redirect_merge_proof(real_commit_set, monkeypatch, tmp_path, key):
    _, commits, _, base = real_commit_set("clean_update_merge")
    injected = tmp_path / "injected"
    monkeypatch.setenv(key, "invalid" if key in {"GIT_CONFIG_COUNT", "GIT_CONFIG_PARAMETERS"} else str(injected))
    # Even malformed settings cannot deny or redirect an otherwise valid proof.
    assert recorder._is_clean_base_merge(commits[-1], base)
    assert not injected.exists()


@pytest.mark.parametrize("case", ["clean_update_merge", "conflict_resolution", "dirty_merge"])
def test_merge_proof_never_writes_shared_objects(real_commit_set, tmp_path, case):
    git, commits, _, base = real_commit_set(case)
    objects = Path(git("rev-parse", "--git-path", "objects").stdout.strip())

    def snapshot():
        return {str(path.relative_to(objects)): path.read_bytes() for path in objects.rglob("*") if path.is_file()}

    before = snapshot()
    assert recorder._is_clean_base_merge(commits[-1], base) == (case == "clean_update_merge")
    assert snapshot() == before
    if case == "conflict_resolution":
        # Conflict blobs/trees do not already exist: prove this fixture detects
        # the writes that the former shared-repository implementation performed.
        parents = [parent["sha"] for parent in commits[-1]["parents"]]
        assert git("merge-tree", "--write-tree", *parents, check=False).returncode == 1
        assert snapshot() != before


@pytest.mark.parametrize("layout", ["directory", "gitfile", "linked_worktree"])
def test_merge_proof_discovers_objects_without_git(real_commit_set, monkeypatch, tmp_path, layout):
    git, commits, _, base = real_commit_set("clean_update_merge")
    objects = Path.cwd() / ".git/objects"
    if layout == "linked_worktree":
        checkout = tmp_path / "linked"
        git("worktree", "add", "--detach", str(checkout))
        git("config", "extensions.worktreeConfig", "true")
        subprocess.run(
            ["git", "-C", str(checkout), "config", "--worktree", "merge.default", "evil"], check=True, timeout=30
        )
    elif layout == "gitfile":
        checkout = Path.cwd()
        git_dir = tmp_path / "separate-git"
        (checkout / ".git").rename(git_dir)
        (checkout / ".git").write_text("gitdir: ../separate-git\n")
        objects = git_dir / "objects"
    else:
        checkout = Path.cwd()
    subdir = checkout / "nested/child"
    subdir.mkdir(parents=True)
    monkeypatch.chdir(subdir)
    assert recorder._merge_proof_object_store() == objects.resolve()
    assert recorder._is_clean_base_merge(commits[-1], base)


@pytest.mark.parametrize("marker", [None, "not a git pointer", "gitdir: missing", "gitdir: missing\nsecond line"])
def test_merge_proof_missing_checkout_refuses(monkeypatch, tmp_path, marker):
    monkeypatch.chdir(tmp_path)
    if marker is not None:
        (tmp_path / ".git").write_text(marker)
    with pytest.raises(OSError):
        recorder._merge_proof_object_store()
    entry = {"sha": SHA, "commit": {"tree": {"sha": SHA}}, "parents": [{"sha": SHA}, {"sha": OTHER}]}
    assert not recorder._is_clean_base_merge(entry, OTHER)


@pytest.mark.parametrize("source", ["info/grafts", "environment"])
@pytest.mark.parametrize("target", ["merge", "base_ancestry"])
def test_git_grafts_cannot_hide_authored_or_nonbase_merges(real_commit_set, monkeypatch, tmp_path, source, target):
    case = "dirty_merge" if target == "merge" else "nonbase_merge"
    git, commits, head, base = real_commit_set(case)
    entry = commits[-1]
    parents = [parent["sha"] for parent in entry["parents"]]
    tree = entry["commit"]["tree"]["sha"]
    if target == "merge":
        helper = git("commit-tree", tree, "-p", parents[0], "-m", "unlisted helper").stdout.strip()
        graft = f"{head} {helper} {base}\n"
    else:
        root = git("show", "--no-patch", "--format=%P", base).stdout.strip()
        graft = f"{base} {parents[1]} {root}\n"
    if source == "info/grafts":
        graft_file = Path(git("rev-parse", "--git-path", "info/grafts").stdout.strip())
    else:
        graft_file = tmp_path / "custom-grafts"
        monkeypatch.setenv("GIT_GRAFT_FILE", str(graft_file))
    graft_file.parent.mkdir(parents=True, exist_ok=True)
    graft_file.write_text(graft)
    if target == "merge":
        assert git("show", "--no-patch", "--format=%P", head).stdout.split() == [helper, base]
        assert git("merge-tree", "--write-tree", helper, base).stdout.strip() == tree
    else:
        assert git("merge-base", "--is-ancestor", parents[1], base, check=False).returncode == 0
    assert not recorder._is_clean_base_merge(entry, base)
    if target == "merge":
        # A listing forged to agree with grafted parents still fails raw binding.
        entry["parents"] = [{"sha": helper}, {"sha": base}]
        assert not recorder._is_clean_base_merge(entry, base)
    with pytest.raises(recorder.RecordError, match="missing explicit X-Agent"):
        recorder.author_families(REPOSITORY, 42, tmp_path)


def test_hash_mismatched_loose_object_cannot_hide_authored_merge_changes(real_commit_set):
    git, commits, _, base = real_commit_set("dirty_merge")
    entry = commits[-1]
    parent = entry["parents"][0]["sha"]
    raw = git("cat-file", "commit", parent).stdout
    original_tree = raw.splitlines()[0][5:]
    forged = raw.replace(original_tree, entry["commit"]["tree"]["sha"], 1).encode()
    body = b"commit " + str(len(forged)).encode() + b"\0" + forged
    object_path = Path.cwd() / ".git/objects" / parent[:2] / parent[2:]
    object_path.chmod(0o600)
    object_path.write_bytes(zlib.compress(body))
    assert not recorder._is_clean_base_merge(entry, base)


def test_git_commit_graph_cannot_fake_base_ancestry(real_commit_set, monkeypatch, tmp_path):
    git, commits, _, base = real_commit_set("nonbase_merge")
    second_parent = commits[-1]["parents"][1]["sha"]
    assert git("merge-base", "--is-ancestor", second_parent, base, check=False).returncode == 1
    # Git reads command-line tips from raw objects; poison an intermediate base
    # ancestor so graph-backed ancestry traversal encounters the forged record.
    git("checkout", "base")
    Path("later.txt").write_text("later base fix\n")
    git("add", "later.txt")
    git("commit", "-m", "later base fix\n\nX-Agent: claude/claude-opus-5-5")
    base_tip = git("rev-parse", "HEAD").stdout.strip()
    monkeypatch.setattr(recorder, "_run_json", lambda args: {"baseRefOid": base_tip})
    git("config", "core.commitGraph", "true")
    git("config", "commitGraph.generationVersion", "1")
    git("commit-graph", "write", "--reachable")
    graph_path = Path(git("rev-parse", "--git-path", "objects/info/commit-graph").stdout.strip())
    graph = bytearray(graph_path.read_bytes())
    assert graph[:6] == b"CGPH\x01\x01"  # Version 1, SHA-1.
    chunks = {
        bytes(graph[offset : offset + 4]): int.from_bytes(graph[offset + 4 : offset + 12], "big")
        for offset in range(8, 8 + graph[6] * 12, 12)
    }
    count = int.from_bytes(graph[chunks[b"OIDF"] + 255 * 4 : chunks[b"OIDF"] + 256 * 4], "big")
    oids = [bytes(graph[chunks[b"OIDL"] + i * 20 : chunks[b"OIDL"] + (i + 1) * 20]).hex() for i in range(count)]
    # Git's documented CDAT record: tree OID, first parent index, second parent index.
    parent_offset = chunks[b"CDAT"] + oids.index(base) * 36 + 20
    graph[parent_offset : parent_offset + 4] = oids.index(second_parent).to_bytes(4, "big")
    # Keep generation numbers consistent with the forged edges (the new parent
    # has generation 2), preventing pruning before Git reaches that parent.
    for sha, generation in [(base, 3), (base_tip, 4)]:
        offset = chunks[b"CDAT"] + oids.index(sha) * 36 + 28
        time_bits = int.from_bytes(graph[offset : offset + 4], "big") & 3
        graph[offset : offset + 4] = ((generation << 2) | time_bits).to_bytes(4, "big")
    graph[-20:] = hashlib.sha1(graph[:-20]).digest()
    graph_path.chmod(0o600)
    graph_path.write_bytes(graph)
    assert git("merge-base", "--is-ancestor", second_parent, base_tip, check=False).returncode == 0
    assert not recorder._is_clean_base_merge(commits[-1], base_tip)
    with pytest.raises(recorder.RecordError, match="missing explicit X-Agent"):
        recorder.author_families(REPOSITORY, 42, tmp_path)


@pytest.mark.parametrize("field", ["first_parent", "second_parent", "parent_order", "tree"])
def test_clean_merge_github_raw_object_mismatch_refuses(real_commit_set, tmp_path, field):
    git, commits, _, _ = real_commit_set("clean_update_merge")
    entry = commits[-1]
    if field == "parent_order":
        entry["parents"].reverse()
    elif field == "tree":
        parent = entry["parents"][0]["sha"]
        entry["commit"]["tree"]["sha"] = git("show", "--no-patch", "--format=%T", parent).stdout.strip()
    else:
        parent_index = 0 if field == "first_parent" else 1
        entry["parents"][parent_index]["sha"] = git("rev-parse", "base^").stdout.strip()
    with pytest.raises(recorder.RecordError, match="missing explicit X-Agent"):
        recorder.author_families(REPOSITORY, 42, tmp_path)


@pytest.mark.parametrize(
    "metadata",
    [
        {"parents": None},
        {"parents": "not a list"},
        {"parents": [None, {"sha": SHA}]},
        {"parents": [{"sha": "main"}, {"sha": SHA}]},
        {"parents": [{"sha": SHA}, {"sha": None}]},
        {"commit": {"message": "update branch"}},
        {"commit": {"message": "update branch", "tree": None}},
        {"commit": {"message": "update branch", "tree": {"sha": "--help"}}},
    ],
)
def test_clean_merge_missing_or_malformed_github_metadata_refuses(real_commit_set, tmp_path, metadata):
    _, commits, _, _ = real_commit_set("clean_update_merge")
    commits[-1].update(metadata)
    with pytest.raises(recorder.RecordError, match="missing explicit X-Agent"):
        recorder.author_families(REPOSITORY, 42, tmp_path)


@pytest.mark.parametrize("failure", [None, "timeout", "missing_base", "metadata_mismatch", "conflict"])
def test_all_merge_proof_calls_are_isolated_and_cleaned_up(real_commit_set, monkeypatch, tmp_path, failure):
    _, commits, _, _ = real_commit_set("conflict_resolution" if failure == "conflict" else "clean_update_merge")
    if failure == "metadata_mismatch":
        commits[-1]["commit"]["tree"]["sha"] = "c" * 40
    original_run = subprocess.run
    calls = []
    proof_dirs = set()

    def guarded_run(args, **kwargs):
        assert args[0] == "git"
        env = kwargs["env"]
        assert {key for key in env if key.startswith("GIT_")} == {
            "GIT_DIR",
            "GIT_CONFIG_NOSYSTEM",
            "GIT_CONFIG_GLOBAL",
            "GIT_ATTR_NOSYSTEM",
            "GIT_NO_LAZY_FETCH",
        }
        assert all(env[key] == "1" for key in ("GIT_CONFIG_NOSYSTEM", "GIT_ATTR_NOSYSTEM", "GIT_NO_LAZY_FETCH"))
        proof_dir = Path(env["GIT_DIR"])
        assert proof_dir.is_dir() and proof_dir != Path.cwd() / ".git"
        assert not Path(env["GIT_CONFIG_GLOBAL"]).exists()
        assert (proof_dir / "config").read_text() == (
            "[core]\n\trepositoryformatversion = 0\n\tbare = true\n"
            f"\tcommitGraph = false\n\tattributesFile = {os.devnull}\n"
        )
        assert list((proof_dir / "refs").iterdir()) == []
        assert not (proof_dir / "info").exists()
        assert not (proof_dir / "index").exists()
        assert not (proof_dir / "commondir").exists()
        assert (proof_dir / "objects/info/alternates").read_text() == json.dumps(
            str(Path.cwd() / ".git/objects")
        ) + "\n"
        proof_dirs.add(proof_dir)
        calls.append(args[1:])
        if failure == "timeout" and args[1] == "merge-tree":
            raise subprocess.TimeoutExpired(args, 30)
        if failure == "missing_base" and args[1:3] == ["cat-file", "-e"]:
            return subprocess.CompletedProcess(args, 1, "", "missing base")
        return original_run(args, **kwargs)

    monkeypatch.setattr(recorder.subprocess, "run", guarded_run)
    if failure:
        reason = (
            "base object not available locally; fetch and retry"
            if failure == "missing_base"
            else "missing explicit X-Agent"
        )
        with pytest.raises(recorder.RecordError, match=reason):
            recorder.author_families(REPOSITORY, 42, tmp_path)
    else:
        assert recorder.author_families(REPOSITORY, 42, tmp_path) == {"openai"}
    expected = ["cat-file", "cat-file", "merge-base", "merge-tree"]
    if failure == "metadata_mismatch":
        expected = ["cat-file"]
    elif failure == "missing_base":
        expected = ["cat-file", "cat-file"]
    assert [call[0] for call in calls] == expected
    assert len(proof_dirs) == 1
    assert not next(iter(proof_dirs)).exists()


@pytest.mark.parametrize("commit,base", [("head", SHA), (SHA, "base")])
def test_clean_merge_proof_requires_literal_shas(commit, base):
    entry = {"sha": commit, "commit": {"tree": {"sha": SHA}}, "parents": [{"sha": SHA}, {"sha": OTHER}]}
    assert not recorder._is_clean_base_merge(entry, base)


@pytest.mark.parametrize(
    "trailer,expected",
    [
        ("kimi/k2", {"moonshot"}),
        ("codex/gpt-6-luna", {"openai"}),
        ("cursor/grok-4.7", {"xai"}),
    ],
)
def test_author_family_resolves_model_with_harness_fallback(monkeypatch, tmp_path, trailer, expected):
    def commit(value):
        return {"commit": {"message": f"work\n\nX-Agent: {value}"}}

    monkeypatch.setattr(recorder, "_pages", lambda args: [commit(trailer)])
    assert recorder.author_families(REPOSITORY, 42, tmp_path) == expected


def test_unknown_harness_model_is_refused(monkeypatch, tmp_path):
    monkeypatch.setattr(
        recorder,
        "_pages",
        lambda args: [{"commit": {"message": "work\n\nX-Agent: unknownharness/x"}}],
    )
    with pytest.raises(recorder.RecordError):
        recorder.author_families(REPOSITORY, 42, tmp_path)


def test_cursor_auto_union_family_is_refused(monkeypatch, tmp_path):
    monkeypatch.setattr(
        recorder,
        "_pages",
        lambda args: [{"commit": {"message": "work\n\nX-Agent: cursor/auto"}}],
    )
    with pytest.raises(recorder.RecordError, match="mixed or unknown"):
        recorder.author_families(REPOSITORY, 42, tmp_path)


def test_mixed_xai_and_moonshot_author_families_are_returned(monkeypatch, tmp_path):
    def commit(trailer):
        return {"commit": {"message": f"work\n\nX-Agent: {trailer}"}}

    monkeypatch.setattr(
        recorder,
        "_pages",
        lambda args: [commit("grok/grok-4.7"), commit("kimi/k2")],
    )
    assert recorder.author_families(REPOSITORY, 42, tmp_path) == {"xai", "moonshot"}


def test_author_task_record_resolves_task_id_trailer(monkeypatch, tmp_path):
    tasks = tmp_path / "tasks"
    write_task(tasks, task_id="author-task", model="gpt-6.1-sol", agent="agy")
    monkeypatch.setattr(
        recorder,
        "_pages",
        lambda args: [{"commit": {"message": "feat: work\n\nX-Agent: agy/author-task"}}],
    )
    assert recorder.author_families(REPOSITORY, 42, tasks) == {"openai"}


def test_archived_review_task_and_reply_are_loadable(tmp_path):
    """#8625: a review archived before its verdict was recorded can still be published."""
    tasks = tmp_path / "tasks"
    write_task(tasks / "archive", task_id="review-old", reply="VERDICT: APPROVE")
    loaded, reply = recorder._task("review-old", tasks)
    assert (loaded["status"], reply) == ("done", "VERDICT: APPROVE")
    # The hot record wins when both exist.
    write_task(tasks, task_id="review-old", reply="VERDICT: REQUEST_CHANGES")
    assert recorder._task("review-old", tasks)[1] == "VERDICT: REQUEST_CHANGES"


def test_archived_author_task_record_resolves_task_id_trailer(monkeypatch, tmp_path):
    """#8625: an old author task moved into tasks/archive/ still proves its family."""
    tasks = tmp_path / "tasks"
    write_task(tasks / "archive", task_id="author-task", model="gpt-6.1-sol", agent="agy")
    monkeypatch.setattr(
        recorder,
        "_pages",
        lambda args: [{"commit": {"message": "feat: work\n\nX-Agent: agy/author-task"}}],
    )
    assert recorder.author_families(REPOSITORY, 42, tasks) == {"openai"}


@pytest.mark.parametrize("trailer", ["codex/../../package", "kimi/../invalid"])
def test_invalid_author_model_is_rejected_before_task_file_read(monkeypatch, tmp_path, trailer):
    tasks = tmp_path / "tasks"
    harness, model = trailer.split("/", 1)
    decoy = tasks / f"{model}.json"
    decoy.parent.mkdir(parents=True, exist_ok=True)
    decoy.write_text(json.dumps({"repository": REPOSITORY, "agent": harness, "model": "gpt-6.1-sol"}))
    attempted_reads = []
    original_read_text = Path.read_text

    def track_reads(path, *args, **kwargs):
        if path.resolve() == decoy.resolve():
            attempted_reads.append(path)
        return original_read_text(path, *args, **kwargs)

    monkeypatch.setattr(Path, "read_text", track_reads)
    monkeypatch.setattr(
        recorder,
        "_pages",
        lambda args: [{"commit": {"message": f"feat: work\n\nX-Agent: {trailer}"}}],
    )
    with pytest.raises(recorder.RecordError, match="author model unknown"):
        recorder.author_families(REPOSITORY, 42, tasks)
    assert attempted_reads == []


def test_kimi_task_record_conflict_is_checked_before_single_family_fallback(monkeypatch, tmp_path):
    tasks = tmp_path / "tasks"
    write_task(tasks, task_id="author-task", model="gpt-6.1-sol", agent="codex")
    monkeypatch.setattr(
        recorder,
        "_pages",
        lambda args: [{"commit": {"message": "feat: work\n\nX-Agent: kimi/author-task"}}],
    )
    with pytest.raises(recorder.RecordError, match="provenance conflicts"):
        recorder.author_families(REPOSITORY, 42, tasks)


@pytest.mark.parametrize("harness", ["codex", "agy", "claude"])
def test_missing_task_record_fails_closed_for_multifamily_harnesses(monkeypatch, tmp_path, harness):
    monkeypatch.setattr(
        recorder,
        "_pages",
        lambda args: [{"commit": {"message": f"feat: work\n\nX-Agent: {harness}/impl-missing-task"}}],
    )
    with pytest.raises(recorder.RecordError, match="author task provenance unavailable"):
        recorder.author_families(REPOSITORY, 42, tmp_path)


@pytest.mark.parametrize(
    "text,expected",
    [
        ("/checkout/.worktrees/dispatch/cursor/review/scripts/unit.py", "scripts/unit.py"),
        ("/checkout/scripts/unit.py:12:3", "scripts/unit.py:12:3"),
        ("`/checkout/scripts/unit.py:12`", "`scripts/unit.py:12`"),
        ("```\n/checkout/scripts/unit.py:12\n```", "```\nscripts/unit.py:12\n```"),
        ("[source](/checkout/scripts/unit.py:12)", "[source](scripts/unit.py:12)"),
        ("/checkout, then /checkout/scripts/unit.py.", "., then /checkout/scripts/unit.py."),
        ("/checkout/.worktrees/dispatch/cursor/review", "."),
        ("/checkout/scripts", "scripts"),
        ("/checkout/missing.py:12", "/checkout/missing.py:12"),
        ("No paths; scripts/unit.py:12", "No paths; scripts/unit.py:12"),
        ("/outside/private.py:12", "/outside/private.py:12"),
        ("/checkout-other/private.py", "/checkout-other/private.py"),
        ("/else/checkout/scripts/unit.py", "/else/checkout/scripts/unit.py"),
        ("/checkout/../private.py", "/checkout/../private.py"),
        ("/checkout/scripts/cafe\u0301.py", "/checkout/scripts/cafe\u0301.py"),
        ("https://example.test/checkout/scripts/unit.py", "https://example.test/checkout/scripts/unit.py"),
    ],
)
def test_repository_relative_reply_preserves_citations_and_outside_text(text, expected, citation_checkout):
    root, worktree = citation_checkout
    text, expected = (value.replace("/checkout", str(root)) for value in (text, expected))
    review = {"worktree_path": str(worktree)}
    assert recorder.repository_relative_reply(text, task=review, primary_root=root) == expected


@pytest.mark.parametrize(
    "checkout",
    [
        {"worktree_path": "/checkout/.worktrees/dispatch/cursor/review"},
        {"worktree_path": "/checkout/.worktrees/dispatch/cursor/review", "cwd": "/review/scripts"},
        {"worktree_path": "/checkout/.worktrees/dispatch/cursor/review", "cwd": "/"},
        {"worktree_path": "/checkout"},
    ],
)
def test_repository_relative_reply_uses_recorded_checkout(checkout, citation_checkout):
    root, _ = citation_checkout
    checkout = {key: value.replace("/checkout", str(root)) for key, value in checkout.items()}
    assert (
        recorder.repository_relative_reply(
            f"{checkout['worktree_path']}/scripts/unit.py:12", task=checkout, primary_root=root
        )
        == "scripts/unit.py:12"
    )


@pytest.mark.parametrize("checkout", ["/review", "/checkout-other", "/else/checkout"])
def test_repository_relative_reply_refuses_roots_outside_primary(checkout, citation_checkout):
    root, _ = citation_checkout
    text = f"{checkout}/scripts/unit.py {root}/scripts/unit.py"
    assert recorder.repository_relative_reply(text, task={"worktree_path": checkout}, primary_root=root) == (
        f"{checkout}/scripts/unit.py scripts/unit.py"
    )


def test_repository_relative_reply_refuses_worktree_root_resolving_outside_primary(tmp_path, citation_checkout):
    root, _ = citation_checkout
    worktree = root / ".worktrees" / "review"
    worktree.parent.mkdir(parents=True, exist_ok=True)
    outside = tmp_path / "outside/scripts/unit.py"
    outside.parent.mkdir(parents=True)
    outside.write_text("# outside\n")
    worktree.symlink_to(tmp_path / "outside", target_is_directory=True)
    text = f"{worktree}/scripts/unit.py {root}/scripts/unit.py"
    assert recorder.repository_relative_reply(text, task={"worktree_path": str(worktree)}, primary_root=root) == (
        f"{worktree}/scripts/unit.py scripts/unit.py"
    )


@pytest.mark.parametrize("checkout", ["primary", "worktree"])
@pytest.mark.parametrize(
    "suffix",
    [
        pytest.param("/\uff0e\uff0e/private/unit.py", id="fullwidth-dots"),
        pytest.param("/.\u200b./private/unit.py", id="zero-width-dots"),
        pytest.param("/\u2024\u2024/private/unit.py", id="one-dot-leaders"),
        pytest.param("/\u2025/private/unit.py", id="two-dot-leader"),
        pytest.param("/a.py\uff0fsrv\uff0fdata\uff0fx", id="fullwidth-slashes"),
        pytest.param("/a.py\uff3csrv\uff3cdata\uff3cx", id="fullwidth-backslashes"),
        pytest.param("/a.py\uff5c/srv/data/x", id="fullwidth-pipe"),
        pytest.param("/a.py\ufe54/srv/data/x", id="small-semicolon"),
        *[
            pytest.param(
                f"/a{separator}{ignorable}\u0338/../../private/unit.py",
                id=f"composing-{name}{'-zero-width' if ignorable else ''}",
            )
            for separator, name in [("<", "less-than"), (">", "greater-than"), ("=", "equals")]
            for ignorable in ["", "\u200b"]
        ],
    ],
)
def test_repository_relative_reply_unicode_paths_still_refuse_real_scanner(checkout, suffix, monkeypatch):
    from scripts.opsec import prepublish as gate
    from tests.test_opsec_prepublish import real_tooling

    tooling = real_tooling()
    monkeypatch.setattr(gate, "private_tooling", lambda: tooling)
    primary = gate.primary_root()
    worktree = primary / ".worktrees/dispatch/cursor/review"
    root = primary if checkout == "primary" else worktree
    reply = f"VERDICT: APPROVE\n`{root}{suffix}:12`"
    rewritten = recorder.repository_relative_reply(reply, task={"worktree_path": str(worktree)}, primary_root=primary)
    for text in (reply, rewritten):
        with pytest.raises(gate.PublishBlocked, match="OPSEC blocked"):
            gate.check_texts("github.com/unit/public", [text], tooling=tooling, environment={})
    assert rewritten == reply


@pytest.mark.parametrize(
    "changed_text",
    ["\u2026", "\u00a0", "\u200b", "\uff0f", "\u0661", "cafe\u0301", "<\u0338", ">\u200b\u0338", "=\u0338"],
)
@pytest.mark.parametrize("position", ["before", "between", "after"])
@pytest.mark.parametrize("ending", ["\n", "\r\n", "\r", "\u2028", ""])
def test_repository_relative_reply_preserves_whole_normalization_changed_line(
    changed_text, position, ending, citation_checkout
):
    root, _ = citation_checkout
    paths = "/checkout/scripts/unit.py /checkout/tests/test_unit.py"
    changed_line = {
        "before": f"{changed_text} {paths}",
        "between": f"/checkout/scripts/unit.py {changed_text} /checkout/tests/test_unit.py",
        "after": f"{paths} {changed_text}",
    }[position] + ending
    assert recorder.normalize_for_scan(changed_line) != changed_line
    # Stable neighboring lines still rewrite; preserve all text and line endings
    # on the altered line, even when the change is outside both path tokens.
    text = f"/checkout/scripts/before.py\n{changed_line}"
    expected = f"scripts/before.py\n{changed_line}"
    if ending:
        text += "/checkout/scripts/after.py"
        expected += "scripts/after.py"
    assert recorder.repository_relative_reply(
        text.replace("/checkout", str(root)), task={}, primary_root=root
    ) == expected.replace("/checkout", str(root))


@pytest.mark.parametrize(
    "checkout", [{"cwd": "/"}, {"cwd": "/review"}, {"worktree_path": "/"}, {"worktree_path": "/repo"}]
)
def test_repository_relative_reply_refuses_cwd_and_ancestor_roots(checkout, citation_checkout):
    root, _ = citation_checkout
    text = "/review/unit.py /repo/outside/unit.py /repo/checkout/scripts/unit.py"
    assert recorder.repository_relative_reply(
        text.replace("/repo/checkout", str(root)), task=checkout, primary_root=root
    ) == ("/review/unit.py /repo/outside/unit.py scripts/unit.py")


def test_repository_relative_reply_refuses_filesystem_root_as_primary():
    text = "/outside/unit.py"
    assert recorder.repository_relative_reply(text, task={}, primary_root=Path("/")) == text


def test_repository_relative_reply_refuses_resolved_ancestor_root(tmp_path, citation_checkout):
    root, _ = citation_checkout
    alias = tmp_path / "alias"
    alias.symlink_to(tmp_path, target_is_directory=True)
    text = f"{alias}/outside/unit.py {root}/scripts/unit.py"
    assert recorder.repository_relative_reply(text, task={"worktree_path": str(alias)}, primary_root=root) == (
        f"{alias}/outside/unit.py scripts/unit.py"
    )


@pytest.mark.parametrize("separator", list("|=\\*;&<>\"'()[]{},"))
def test_repository_relative_reply_uses_scanner_boundaries(separator, citation_checkout):
    root, worktree = citation_checkout
    for outside in ("/outside/x", "/outside/../x"):
        text = f"{worktree}/a{separator}{outside}"
        expected = text if separator in "=\\&([{" else f"a{separator}{outside}"
        assert (
            recorder.repository_relative_reply(text, task={"worktree_path": str(worktree)}, primary_root=root)
            == expected
        )


@pytest.mark.parametrize("checkout", [None, "relative", 123])
def test_repository_relative_reply_ignores_invalid_checkout(checkout, citation_checkout):
    root, _ = citation_checkout
    assert (
        recorder.repository_relative_reply(
            f"/outside/unit.py {root}/scripts/unit.py",
            task={"worktree_path": checkout},
            primary_root=root,
        )
        == "/outside/unit.py scripts/unit.py"
    )


def test_repository_relative_reply_keeps_symlink_escapes(monkeypatch, tmp_path, citation_checkout):
    root, _ = citation_checkout
    outside = tmp_path / "private/unit.py"
    outside.parent.mkdir()
    outside.write_text("# outside\n" * 20)
    (root / "escape").symlink_to(tmp_path / "private")
    text = f"`{root}/escape/unit.py:12`"
    assert recorder.repository_relative_reply(text, task={}, primary_root=root) == text
    (root / "inside").symlink_to(root / "scripts")
    assert recorder.repository_relative_reply(f"{root}/inside/unit.py", task={}, primary_root=root) == "inside/unit.py"

    def unavailable(*args, **kwargs):
        raise OSError("private diagnostic")

    monkeypatch.setattr(Path, "resolve", unavailable)
    assert recorder.repository_relative_reply(text, task={}, primary_root=root) == text


@pytest.mark.parametrize(
    "reply,refused",
    [
        (
            "VERDICT: APPROVE\n`/checkout/.worktrees/dispatch/cursor/review/scripts/unit.py:12`\n"
            "```\n/checkout/tests/test_unit.py:3\n```",
            False,
        ),
        ("VERDICT: APPROVE", False),
        ("VERDICT: APPROVE\n/checkout/scripts/unit.py /outside/private.py:12", True),
        ("VERDICT: APPROVE\n/checkout-other/private.py", True),
        ("VERDICT: APPROVE\n/checkout/../private.py", True),
        ("VERDICT: APPROVE\n/checkout/\uff0e\uff0e/private.py", True),
        ("VERDICT: APPROVE\n/checkout/.\u200b./private.py", True),
        ("VERDICT: APPROVE\n/checkout/a.py\uff0fsrv\uff0fdata\uff0fx", True),
        ("VERDICT: APPROVE\n/checkout/scripts/unit.py\nSENTINEL-HOST-TOKEN", True),
        *[
            (f"VERDICT: APPROVE\n/checkout/scripts/unit.py{separator}/outside/x", True)
            for separator in "|=\\*;&<>\"'()[]{}"
        ],
    ],
)
def test_record_fixture_dry_run_through_publication_scanner(
    monkeypatch, tmp_path, synthetic_opsec, capsys, reply, refused, citation_checkout
):
    """Run the recorder and typed publisher with only the GitHub transport faked."""
    from scripts.publish import github

    root, worktree = citation_checkout
    reply = reply.replace("/checkout", str(root))
    rules = json.loads((synthetic_opsec / "rules.json").read_text())
    rules["1"] = {"patterns": [{"id": "synthetic-rule", "regex": "SENTINEL-HOST-TOKEN"}]}
    rules["1"]["patterns"].append({"id": "synthetic-host-path", "regex": r"(?<![<\w:])/[A-Za-z][^\s`]*"})
    # Cover an outside path after '<' without mistaking the comment's HTML
    # closing tags for filesystem paths.
    rules["1"]["patterns"].append({"id": "synthetic-markup-path", "regex": r"(?<=<)/outside/[^\s`]*"})
    (synthetic_opsec / "rules.json").write_text(json.dumps(rules))
    real_json = recorder._run_json
    tasks, comments, calls = setup_record(monkeypatch, tmp_path)
    fake_json = recorder._run_json
    write_task(tasks, reply=reply, worktree_path=str(worktree))
    monkeypatch.setattr(recorder, "_repo_root", lambda: root)

    def route(args, **kwargs):
        if isinstance(args, github.Request) and args.verb == "issue-comment-json":
            return real_json(args, **kwargs)
        return fake_json(args, **kwargs)

    def transport(argv, **kwargs):
        payload = json.loads(Path(argv[argv.index("--input") + 1]).read_text())
        posted = fake_json(github.Request("issue-comment-json", repo=REPOSITORY, number=42, body=payload["body"]))
        return subprocess.CompletedProcess(argv, 0, stdout=json.dumps(posted), stderr="")

    monkeypatch.setattr(recorder, "_run_json", route)
    monkeypatch.setattr(github, "_send", transport)
    if refused:
        with pytest.raises(recorder.RecordError) as error:
            recorder.record("review-one", pr_number=42, task_root=tasks, lock_root=tmp_path / "locks")
        diagnostic = str(error.value)
        assert "publish_blocked" in diagnostic and "class=" in diagnostic
        assert reply not in diagnostic
        assert (
            "/outside" not in diagnostic and "/checkout" not in diagnostic and "SENTINEL-HOST-TOKEN" not in diagnostic
        )
        assert calls == {"posts": 0, "statuses": 0}
        record = recorder.record
        monkeypatch.setattr(
            recorder,
            "record",
            lambda task_id, **kwargs: record(task_id, task_root=tasks, lock_root=tmp_path / "locks", **kwargs),
        )
        assert recorder.main(["--task-id", "review-one", "--pr", "42"]) == 1
        output = capsys.readouterr()
        assert "class=" in output.out
        assert "/checkout" not in output.out + output.err
        assert "/outside" not in output.out + output.err and "SENTINEL-HOST-TOKEN" not in output.out + output.err
        assert calls == {"posts": 0, "statuses": 0}
    else:
        receipt = recorder.record("review-one", pr_number=42, task_root=tasks, lock_root=tmp_path / "locks")
        assert receipt["comment"] == "posted" and receipt["status"] == "posted"
        assert calls == {"posts": 1, "statuses": 1}
        body = comments[0]["body"]
        assert "/checkout" not in body
        if "unit.py" in reply:
            assert "`scripts/unit.py:12`" in body and "```\ntests/test_unit.py:3\n```" in body


def test_task_record_agent_conflict_is_checked_for_agy(monkeypatch, tmp_path):
    tasks = tmp_path / "tasks"
    write_task(tasks, task_id="author-task", model="claude-opus-5", agent="claude")
    monkeypatch.setattr(
        recorder,
        "_pages",
        lambda args: [{"commit": {"message": "feat: work\n\nX-Agent: agy/author-task"}}],
    )
    with pytest.raises(recorder.RecordError, match="provenance conflicts"):
        recorder.author_families(REPOSITORY, 42, tasks)


def test_comment_truncation_retains_marker():
    body = recorder.build_comment(
        sha=SHA,
        task_id="review-one",
        started="2026-09-23T12:00:00.000001+00:00",
        verdict="APPROVED",
        model="gpt-6.1-sol",
        family="openai",
        reply="x" * 70_000,
    )
    assert len(body.encode()) <= recorder.MAX_COMMENT_BYTES
    assert "[Review reply truncated" in body
    assert recorder.parse_marker(body)["task"] == "review-one"


@pytest.fixture(autouse=True)
def _synthetic_publishing_rules(synthetic_opsec, publisher_transport, monkeypatch):
    """Use synthetic private tooling and an explicit destination for send spies."""
    monkeypatch.setenv("GH_REPO", "unit/public")


def cursor_receipt(tasks, **updates):
    """A Cursor review dispatched with the formal Grok slug."""
    write_task(
        tasks, agent="cursor", model="grok-4.7-high", **{"resolved_model_source": "cursor-stream-json", **updates}
    )


def test_cursor_display_name_receipt_records_the_concrete_slug_and_family(monkeypatch, tmp_path):
    tasks, comments, _ = setup_record(monkeypatch, tmp_path)
    cursor_receipt(tasks, resolved_model="Grok 4.7 256K High", resolved_model_known=True)
    result = recorder.record("review-one", pr_number=42, task_root=tasks, lock_root=tmp_path / "locks")
    assert result["comment"] == "posted"
    assert "Reviewer family: xai" in comments[0]["body"]
    assert "Reviewer model: grok-4.7" in comments[0]["body"]
    assert "model=grok-4.7 family=xai" in comments[0]["body"]


@pytest.mark.parametrize("model", ["Composer 2.5", "composer-2.5"])
def test_an_attested_composer_receipt_is_refused_because_the_resolver_never_selects_it(monkeypatch, tmp_path, model):
    """#9488: Composer is unpinned on the formal Cursor endpoint, so its verdict is not recorded."""
    tasks, comments, _ = setup_record(monkeypatch, tmp_path)
    cursor_receipt(tasks, resolved_model=model, resolved_model_known=True)
    with pytest.raises(recorder.RecordError, match="reviewer model unknown"):
        recorder.record("review-one", pr_number=42, task_root=tasks, lock_root=tmp_path / "locks")
    assert comments == []


@pytest.mark.parametrize(
    "updates,reason",
    [
        ({"resolved_model": "Composer 2.5", "resolved_model_known": False}, "Cursor reviewer model unknown"),
        ({"resolved_model": "Composer 2.5"}, "Cursor reviewer model unknown"),
        ({"resolved_model": "auto", "resolved_model_known": True}, "reviewer family unknown"),
        ({"resolved_model": "unknown", "resolved_model_known": True}, "reviewer family unknown"),
        ({"resolved_model": "unattested-harness", "resolved_model_known": True}, "reviewer family unknown"),
        ({"resolved_model": "", "resolved_model_known": True}, "reviewer model unknown"),
        ({"resolved_model": None, "resolved_model_known": True}, "reviewer model unknown"),
        ({"resolved_model": "Composer 2", "resolved_model_known": True}, "reviewer model unknown"),
        ({"resolved_model": "Composer 2.5 Fast", "resolved_model_known": True}, "reviewer model unknown"),
        ({"resolved_model": "Composer 3", "resolved_model_known": True}, "reviewer model unknown"),
    ],
)
def test_cursor_receipts_without_an_attested_concrete_model_are_still_refused(monkeypatch, tmp_path, updates, reason):
    tasks, comments, _ = setup_record(monkeypatch, tmp_path)
    cursor_receipt(tasks, **updates)
    with pytest.raises(recorder.RecordError, match=reason):
        recorder.record("review-one", pr_number=42, task_root=tasks, lock_root=tmp_path / "locks")
    assert comments == []


@pytest.mark.parametrize("model", ["Composer 2.5", "composer-2.5"])
@pytest.mark.parametrize(
    "source",
    [
        {"resolved_model_source": "unattested-harness"},
        {"resolved_model_source": ""},
        {"resolved_model_source": None},
        {"resolved_model_source": "pending"},
        {"resolved_model_source": "unknown"},
        {"resolved_model_source": "other"},
        {"resolved_model_source": ["cursor-stream-json"]},
        {"__drop_source__": True},
    ],
)
def test_cursor_receipt_without_a_runtime_reported_source_is_refused(monkeypatch, tmp_path, model, source):
    tasks, comments, _ = setup_record(monkeypatch, tmp_path)
    updates = {"resolved_model": model, "resolved_model_known": True, **source}
    drop = updates.pop("__drop_source__", False)
    cursor_receipt(tasks, **updates)
    if drop:  # an absent source, not just a null one
        path = tasks / "review-one.json"
        data = json.loads(path.read_text())
        del data["resolved_model_source"]
        path.write_text(json.dumps(data))
    with pytest.raises(recorder.RecordError, match="Cursor reviewer model unattested"):
        recorder.record("review-one", pr_number=42, task_root=tasks, lock_root=tmp_path / "locks")
    assert comments == []


@pytest.mark.parametrize("source", sorted(recorder.RUNTIME_REPORTED_MODEL_SOURCES))
def test_cursor_display_name_receipt_accepts_each_runtime_reported_source(monkeypatch, tmp_path, source):
    tasks, comments, _ = setup_record(monkeypatch, tmp_path)
    cursor_receipt(tasks, resolved_model="Grok 4.7 256K High", resolved_model_known=True, resolved_model_source=source)
    assert (
        recorder.record("review-one", pr_number=42, task_root=tasks, lock_root=tmp_path / "locks")["comment"]
        == "posted"
    )
    assert "model=grok-4.7 family=xai" in comments[0]["body"]


def test_cursor_receipt_with_a_non_ascii_look_alike_name_is_refused(monkeypatch, tmp_path):
    tasks, comments, _ = setup_record(monkeypatch, tmp_path)
    cursor_receipt(tasks, resolved_model="Compo\u017fer 2.5", resolved_model_known=True)
    with pytest.raises(recorder.RecordError, match="reviewer model unknown"):
        recorder.record("review-one", pr_number=42, task_root=tasks, lock_root=tmp_path / "locks")
    assert comments == []


# --- #9714: runtime-attested Claude Opus 5.5 High through Cursor ---------------


def opus_receipt(tasks, **updates):
    """A Cursor review dispatched with the formal Opus slug."""
    write_task(
        tasks,
        agent="cursor",
        model="claude-opus-5-5-high",
        **{"resolved_model_source": "cursor-stream-json", **updates},
    )


@pytest.mark.parametrize("source", sorted(recorder.RUNTIME_REPORTED_MODEL_SOURCES))
@pytest.mark.parametrize("display", ["Claude Opus 5.5 300K High", "Claude Opus 5.5 1M High"])
def test_runtime_reported_cursor_opus_high_records_the_catalog_id(monkeypatch, tmp_path, display, source):
    tasks, comments, _ = setup_record(monkeypatch, tmp_path, families={"openai"})
    opus_receipt(tasks, resolved_model=display, resolved_model_known=True, resolved_model_source=source)
    result = recorder.record("review-one", pr_number=42, task_root=tasks, lock_root=tmp_path / "locks")
    assert result["comment"] == "posted"
    assert "Reviewer model: claude-opus-5-5" in comments[0]["body"]
    assert "model=claude-opus-5-5 family=anthropic" in comments[0]["body"]


@pytest.mark.parametrize(
    "resolved_model",
    [
        "claude-opus-5-5",  # a bare slug names no variant
        "claude-opus-5-5-high",  # the dispatch slug is not the runtime's report
        "claude-opus-5-5-high-fast",
        "Claude Opus 5.5 300K High Fast",
        "Claude Opus 5.5 1M High Fast",
        "Claude Opus 5.5 1M",
        "Claude Opus 5.5 1M Extra High",
        "Claude Opus 5.5 1M Max",
        "Claude Opus 5.5 300K Medium",
        "Claude Opus 5.5 High",
        "Claude Opus 5 1M High",
        "Claude Opus 5.5 300\u212a High",  # KELVIN SIGN look-alike
        "Claude Opus 5.5 300K High\n",
        "Claude Sonnet 5 300K High",
        "Claude Fable 5.1 300K High",
    ],
)
def test_a_cursor_claude_receipt_that_is_not_opus_5_5_high_is_refused(monkeypatch, tmp_path, resolved_model):
    tasks, comments, _ = setup_record(monkeypatch, tmp_path, families={"openai"})
    cursor_receipt(tasks, resolved_model=resolved_model, resolved_model_known=True)
    with pytest.raises(recorder.RecordError, match="reviewer model unknown"):
        recorder.record("review-one", pr_number=42, task_root=tasks, lock_root=tmp_path / "locks")
    assert comments == []


@pytest.mark.parametrize(
    "updates,reason",
    [
        # The live shape of a Cursor run before its runtime reports: requested slug only.
        (
            {"resolved_model": "unattested-harness", "resolved_model_known": False, "resolved_model_source": "pending"},
            "Cursor reviewer model unknown",
        ),
        ({"resolved_model": "Claude Opus 5.5 300K High"}, "Cursor reviewer model unknown"),
        (
            {
                "resolved_model": "Claude Opus 5.5 300K High",
                "resolved_model_known": True,
                "resolved_model_source": "pending",
            },
            "Cursor reviewer model unattested",
        ),
        (
            {
                "resolved_model": "Claude Opus 5.5 300K High",
                "resolved_model_known": True,
                "resolved_model_source": "other",
            },
            "Cursor reviewer model unattested",
        ),
    ],
)
def test_a_requested_only_or_unattested_cursor_opus_receipt_is_refused(monkeypatch, tmp_path, updates, reason):
    tasks, comments, _ = setup_record(monkeypatch, tmp_path, families={"openai"})
    opus_receipt(tasks, **updates)
    with pytest.raises(recorder.RecordError, match=reason):
        recorder.record("review-one", pr_number=42, task_root=tasks, lock_root=tmp_path / "locks")
    assert comments == []


@pytest.mark.parametrize(
    "requested,attested",
    [
        ("claude-opus-5-5-high", "Grok 4.7 256K High"),
        ("grok-4.7-high", "Claude Opus 5.5 300K High"),
    ],
)
def test_a_cursor_run_attesting_another_admitted_seat_than_requested_is_refused(
    monkeypatch, tmp_path, requested, attested
):
    tasks, comments, _ = setup_record(monkeypatch, tmp_path, families={"openai"})
    write_task(
        tasks,
        agent="cursor",
        model=requested,
        resolved_model=attested,
        resolved_model_known=True,
        resolved_model_source="cursor-stream-json",
    )
    with pytest.raises(recorder.RecordError, match="Cursor reviewer model mismatch"):
        recorder.record("review-one", pr_number=42, task_root=tasks, lock_root=tmp_path / "locks")
    assert comments == []


def test_a_cursor_grok_run_requested_as_grok_still_records(monkeypatch, tmp_path):
    tasks, comments, _ = setup_record(monkeypatch, tmp_path)
    write_task(
        tasks,
        agent="cursor",
        model="grok-4.7-high",
        resolved_model="Grok 4.7 256K High",
        resolved_model_known=True,
        resolved_model_source="cursor-stream-json",
    )
    result = recorder.record("review-one", pr_number=42, task_root=tasks, lock_root=tmp_path / "locks")
    assert result["comment"] == "posted"
    assert "model=grok-4.7 family=xai" in comments[0]["body"]


def test_a_cursor_opus_verdict_on_an_anthropic_authored_change_is_refused(monkeypatch, tmp_path):
    tasks, comments, _ = setup_record(monkeypatch, tmp_path, families={"anthropic"})
    opus_receipt(tasks, resolved_model="Claude Opus 5.5 300K High", resolved_model_known=True)
    with pytest.raises(recorder.RecordError, match="reviewer family equals an author family"):
        recorder.record("review-one", pr_number=42, task_root=tasks, lock_root=tmp_path / "locks")
    assert comments == []


def terminal_cursor_receipt(tasks, *, requested, attested, **updates):
    """A finished Cursor task as delegate leaves it: ``model`` overwritten by the report."""
    fields = {
        "agent": "cursor",
        "model": attested,
        "resolved_model": attested,
        "resolved_model_known": True,
        "resolved_model_source": "cursor-stream-json",
        "substitution": {
            "requested_provider": "cursor",
            "requested_model": requested,
            "actual_provider": "cursor",
            "actual_model": attested,
            "actual_model_known": True,
            "substituted": True,
            "source": "cursor-stream-json",
            "marker": None,
        },
    }
    write_task(tasks, **{**fields, **updates})


@pytest.mark.parametrize(
    "requested,attested",
    [
        ("claude-opus-5-5-high", "Grok 4.7 256K High"),
        ("grok-4.7-high", "Claude Opus 5.5 300K High"),
    ],
)
def test_a_terminal_cursor_run_attesting_another_seat_than_requested_is_refused(
    monkeypatch, tmp_path, requested, attested
):
    tasks, comments, _ = setup_record(monkeypatch, tmp_path, families={"openai"})
    terminal_cursor_receipt(tasks, requested=requested, attested=attested)
    with pytest.raises(recorder.RecordError, match="Cursor reviewer model mismatch"):
        recorder.record("review-one", pr_number=42, task_root=tasks, lock_root=tmp_path / "locks")
    assert comments == []


@pytest.mark.parametrize(
    "requested,attested,recorded",
    [
        ("claude-opus-5-5-high", "Claude Opus 5.5 300K High", "model=claude-opus-5-5 family=anthropic"),
        ("grok-4.7-high", "Grok 4.7 256K High", "model=grok-4.7 family=xai"),
    ],
)
def test_a_terminal_cursor_run_attesting_its_requested_seat_records(
    monkeypatch, tmp_path, requested, attested, recorded
):
    tasks, comments, _ = setup_record(monkeypatch, tmp_path, families={"openai"})
    terminal_cursor_receipt(tasks, requested=requested, attested=attested)
    result = recorder.record("review-one", pr_number=42, task_root=tasks, lock_root=tmp_path / "locks")
    assert result["comment"] == "posted"
    assert recorded in comments[0]["body"]


def test_a_terminal_cursor_opus_verdict_on_an_anthropic_authored_change_is_refused(monkeypatch, tmp_path):
    tasks, comments, _ = setup_record(monkeypatch, tmp_path, families={"anthropic"})
    terminal_cursor_receipt(tasks, requested="claude-opus-5-5-high", attested="Claude Opus 5.5 300K High")
    with pytest.raises(recorder.RecordError, match="reviewer family equals an author family"):
        recorder.record("review-one", pr_number=42, task_root=tasks, lock_root=tmp_path / "locks")
    assert comments == []


@pytest.mark.parametrize(
    "substitution,reason",
    [
        ("claude-opus-5-5-high", "request metadata malformed"),
        (["claude-opus-5-5-high"], "request metadata malformed"),
        ({"requested_model": "claude-opus-5-5-high"}, "request metadata malformed"),
        (
            {"requested_provider": "claude", "requested_model": "claude-opus-5-5-high"},
            "request metadata malformed",
        ),
        ({"requested_provider": "cursor"}, "request metadata malformed"),
        ({"requested_provider": "cursor", "requested_model": None}, "request metadata malformed"),
        ({"requested_provider": "cursor", "requested_model": ""}, "request metadata malformed"),
        ({"requested_provider": "cursor", "requested_model": " grok-4.7-high"}, "request metadata malformed"),
        ({"requested_provider": "cursor", "requested_model": ["grok-4.7-high"]}, "request metadata malformed"),
        # The runtime's own report is not a request.
        (
            {"requested_provider": "cursor", "requested_model": "Claude Opus 5.5 300K High"},
            "request unknown",
        ),
    ],
)
def test_terminal_cursor_request_metadata_that_names_no_cursor_pin_is_refused(
    monkeypatch, tmp_path, substitution, reason
):
    tasks, comments, _ = setup_record(monkeypatch, tmp_path, families={"openai"})
    terminal_cursor_receipt(
        tasks, requested="claude-opus-5-5-high", attested="Claude Opus 5.5 300K High", substitution=substitution
    )
    with pytest.raises(recorder.RecordError, match=reason):
        recorder.record("review-one", pr_number=42, task_root=tasks, lock_root=tmp_path / "locks")
    assert comments == []


def test_a_pinned_model_disagreeing_with_the_substitution_request_is_refused(monkeypatch, tmp_path):
    tasks, comments, _ = setup_record(monkeypatch, tmp_path, families={"openai"})
    terminal_cursor_receipt(
        tasks, requested="claude-opus-5-5-high", attested="Claude Opus 5.5 300K High", model="grok-4.7-high"
    )
    with pytest.raises(recorder.RecordError, match="Cursor reviewer request ambiguous"):
        recorder.record("review-one", pr_number=42, task_root=tasks, lock_root=tmp_path / "locks")
    assert comments == []


@pytest.mark.parametrize("attested", ["Claude Opus 5.5 300K High", "Grok 4.7 256K High"])
def test_an_overwritten_model_without_request_metadata_is_refused(monkeypatch, tmp_path, attested):
    tasks, comments, _ = setup_record(monkeypatch, tmp_path, families={"openai"})
    write_task(
        tasks,
        agent="cursor",
        model=attested,
        resolved_model=attested,
        resolved_model_known=True,
        resolved_model_source="cursor-stream-json",
    )
    with pytest.raises(recorder.RecordError, match="Cursor reviewer request unknown"):
        recorder.record("review-one", pr_number=42, task_root=tasks, lock_root=tmp_path / "locks")
    assert comments == []


def nested_cursor_substitution(*, routed, attested):
    """Delegate's terminal record for a native request routed onto Cursor before spawn."""
    from scripts.delegate import _merge_agent_substitution, _remember_agent_substitution

    sink = {}
    _remember_agent_substitution(
        sink,
        source="budget-guard",
        requested_agent="claude",
        requested_model="claude-opus-5-5",
        actual_agent="cursor",
        actual_model=routed,
        how="mapped",
    )
    # The Cursor adapter's own receipt for this invocation (adapters/cursor.py ``parse``).
    runtime = {
        "requested_provider": "cursor",
        "requested_model": routed,
        "actual_provider": "cursor",
        "actual_model": attested,
        "actual_model_known": True,
        "substituted": attested != routed,
        "source": "cursor-stream-json",
        "marker": None,
    }
    return _merge_agent_substitution(sink["record"], runtime)


def nested_cursor_receipt(tasks, *, routed, attested, substitution=None):
    write_task(
        tasks,
        agent="cursor",
        model=attested,
        resolved_model=attested,
        resolved_model_known=True,
        resolved_model_source="cursor-stream-json",
        substitution=substitution or nested_cursor_substitution(routed=routed, attested=attested),
    )


@pytest.mark.parametrize(
    "routed,attested,recorded",
    [
        ("claude-opus-5-5-high", "Claude Opus 5.5 300K High", "model=claude-opus-5-5 family=anthropic"),
        ("grok-4.7-high", "Grok 4.7 256K High", "model=grok-4.7 family=xai"),
    ],
)
def test_a_nested_cursor_receipt_attesting_its_routed_seat_records(monkeypatch, tmp_path, routed, attested, recorded):
    tasks, comments, _ = setup_record(monkeypatch, tmp_path, families={"openai"})
    substitution = nested_cursor_substitution(routed=routed, attested=attested)
    # The outer routing record names the native preference, not the Cursor pin.
    assert (substitution["kind"], substitution["requested_model"]) == ("agent-substitution", "claude-opus-5-5")
    nested_cursor_receipt(tasks, routed=routed, attested=attested, substitution=substitution)
    result = recorder.record("review-one", pr_number=42, task_root=tasks, lock_root=tmp_path / "locks")
    assert result["comment"] == "posted"
    assert recorded in comments[0]["body"]


def test_a_nested_cursor_opus_request_with_a_grok_report_is_refused(monkeypatch, tmp_path):
    tasks, comments, _ = setup_record(monkeypatch, tmp_path, families={"openai"})
    nested_cursor_receipt(tasks, routed="claude-opus-5-5-high", attested="Grok 4.7 256K High")
    with pytest.raises(recorder.RecordError, match="Cursor reviewer model mismatch"):
        recorder.record("review-one", pr_number=42, task_root=tasks, lock_root=tmp_path / "locks")
    assert comments == []


def test_a_nested_cursor_opus_verdict_on_an_anthropic_authored_change_is_refused(monkeypatch, tmp_path):
    tasks, comments, _ = setup_record(monkeypatch, tmp_path, families={"anthropic"})
    nested_cursor_receipt(tasks, routed="claude-opus-5-5-high", attested="Claude Opus 5.5 300K High")
    with pytest.raises(recorder.RecordError, match="reviewer family equals an author family"):
        recorder.record("review-one", pr_number=42, task_root=tasks, lock_root=tmp_path / "locks")
    assert comments == []


def _drop(key):
    return lambda record: record.pop(key)


def _set(key, value, *, nested=False):
    return lambda record: (record["runtime_attribution"] if nested else record).__setitem__(key, value)


@pytest.mark.parametrize(
    "mutate",
    [
        pytest.param(_drop("runtime_attribution"), id="routing-record-without-runtime-receipt"),
        pytest.param(_set("runtime_attribution", "claude-opus-5-5-high"), id="runtime-receipt-not-a-record"),
        pytest.param(_set("actual_agent", "claude"), id="routed-off-cursor"),
        pytest.param(_set("actual_model", "grok-4.7-high"), id="routed-slug-contradicts-launch"),
        pytest.param(_set("requested_model", "grok-4.7-high", nested=True), id="launch-contradicts-routed-slug"),
        pytest.param(_set("requested_provider", "claude", nested=True), id="runtime-request-off-cursor"),
        pytest.param(_set("actual_provider", "claude", nested=True), id="runtime-ran-off-cursor"),
        pytest.param(_set("actual_model", "Grok 4.7 256K High", nested=True), id="receipt-contradicts-report"),
        pytest.param(_set("actual_model", None, nested=True), id="receipt-without-report"),
        pytest.param(_set("kind", "agent-substitution", nested=True), id="doubly-nested-routing-record"),
    ],
)
def test_malformed_nested_cursor_request_metadata_is_refused(monkeypatch, tmp_path, mutate):
    tasks, comments, _ = setup_record(monkeypatch, tmp_path, families={"openai"})
    substitution = nested_cursor_substitution(routed="claude-opus-5-5-high", attested="Claude Opus 5.5 300K High")
    mutate(substitution)
    nested_cursor_receipt(
        tasks, routed="claude-opus-5-5-high", attested="Claude Opus 5.5 300K High", substitution=substitution
    )
    with pytest.raises(recorder.RecordError, match="Cursor reviewer request metadata malformed"):
        recorder.record("review-one", pr_number=42, task_root=tasks, lock_root=tmp_path / "locks")
    assert comments == []


def cursor_receipt_shape(tasks, shape, *, requested, attested, **updates):
    """Each delegate producer shape for a Cursor review requested as ``requested``."""
    if shape == "pinned":
        fields = {
            "agent": "cursor",
            "model": requested,
            "resolved_model": attested,
            "resolved_model_known": True,
            "resolved_model_source": "cursor-stream-json",
        }
        write_task(tasks, **{**fields, **updates})
    elif shape == "terminal":
        terminal_cursor_receipt(tasks, requested=requested, attested=attested, **updates)
    else:
        write_task(
            tasks,
            agent="cursor",
            model=attested,
            resolved_model=attested,
            resolved_model_known=True,
            resolved_model_source="cursor-stream-json",
            substitution=nested_cursor_substitution(routed=requested, attested=attested),
            **updates,
        )


CURSOR_SHAPES = ["pinned", "terminal", "nested"]


@pytest.mark.parametrize("shape", CURSOR_SHAPES)
@pytest.mark.parametrize("risk", [None, "critical"])
@pytest.mark.parametrize(
    "requested,attested",
    [
        ("auto", "Claude Opus 5.5 300K High"),
        ("claude-opus-5-5-high-fast", "Claude Opus 5.5 300K High"),
        ("claude-opus-5-5", "Claude Opus 5.5 300K High"),
        ("claude-opus-5-5", "Grok 4.7 256K High"),
        ("auto", "Grok 4.7 256K High"),
        ("grok-4.7", "Grok 4.7 256K High"),
        ("composer-2.5", "Grok 4.7 256K High"),
    ],
)
def test_a_cursor_request_outside_the_formal_dispatch_pins_is_refused_before_publication(
    monkeypatch, tmp_path, shape, risk, requested, attested
):
    tasks, comments, calls = setup_record(monkeypatch, tmp_path, families={"openai"})
    assert requested not in recorder.FORMAL_CURSOR_REVIEW_DISPATCH_MODELS
    cursor_receipt_shape(tasks, shape, requested=requested, attested=attested, review_risk=risk)
    with pytest.raises(recorder.RecordError, match="is not a formal Cursor review dispatch pin"):
        recorder.record("review-one", pr_number=42, task_root=tasks, lock_root=tmp_path / "locks")
    assert comments == []
    assert calls == {"posts": 0, "statuses": 0}


@pytest.mark.parametrize("shape", CURSOR_SHAPES)
@pytest.mark.parametrize(
    "updates,reason",
    [
        ({"review_risk": "critical"}, "unqualified at code/critical review"),
        ({"review_risk": "critical", "review_profile": "infra"}, "unqualified at infra/critical review"),
        ({"review_risk": "high"}, "unqualified at code/high review"),
        # A security-sensitive owned path raises the effective risk to critical.
        ({"owned_paths": ["scripts/review/record_cf_verdict.py"]}, "unqualified at code/critical review"),
        ({"review_risk": "low", "owned_paths": ["scripts/agent_runtime"]}, "unqualified at code/critical review"),
    ],
)
def test_an_attested_cursor_grok_verdict_above_its_qualified_risk_is_refused_before_publication(
    monkeypatch, tmp_path, shape, updates, reason
):
    tasks, comments, calls = setup_record(monkeypatch, tmp_path, families={"openai"})
    cursor_receipt_shape(tasks, shape, requested="grok-4.7-high", attested="Grok 4.7 256K High", **updates)
    with pytest.raises(recorder.RecordError, match=reason):
        recorder.record("review-one", pr_number=42, task_root=tasks, lock_root=tmp_path / "locks")
    assert comments == []
    assert calls == {"posts": 0, "statuses": 0}


@pytest.mark.parametrize("shape", CURSOR_SHAPES)
@pytest.mark.parametrize(
    "updates",
    [{}, {"review_risk": "low"}, {"review_risk": "medium"}, {"review_profile": "infra"}, {"owned_paths": ["docs"]}],
)
def test_an_attested_cursor_grok_verdict_below_critical_still_records(monkeypatch, tmp_path, shape, updates):
    tasks, comments, calls = setup_record(monkeypatch, tmp_path, families={"openai"})
    cursor_receipt_shape(tasks, shape, requested="grok-4.7-high", attested="Grok 4.7 256K High", **updates)
    result = recorder.record("review-one", pr_number=42, task_root=tasks, lock_root=tmp_path / "locks")
    assert (result["comment"], result["status"]) == ("posted", "posted")
    assert "model=grok-4.7 family=xai" in comments[0]["body"]
    assert calls == {"posts": 1, "statuses": 1}


@pytest.mark.parametrize("shape", CURSOR_SHAPES)
@pytest.mark.parametrize("updates", [{}, {"review_risk": "high"}, {"review_risk": "critical"}])
def test_an_attested_cursor_opus_verdict_records_through_critical_risk(monkeypatch, tmp_path, shape, updates):
    tasks, comments, calls = setup_record(monkeypatch, tmp_path, families={"openai"})
    cursor_receipt_shape(
        tasks, shape, requested="claude-opus-5-5-high", attested="Claude Opus 5.5 300K High", **updates
    )
    result = recorder.record("review-one", pr_number=42, task_root=tasks, lock_root=tmp_path / "locks")
    assert (result["comment"], result["status"]) == ("posted", "posted")
    assert "model=claude-opus-5-5 family=anthropic" in comments[0]["body"]
    assert calls == {"posts": 1, "statuses": 1}


@pytest.mark.parametrize(
    "updates,reason",
    [
        ({"review_risk": "extreme"}, "review risk invalid"),
        ({"review_risk": ""}, "review risk invalid"),
        ({"review_risk": 4}, "review risk invalid"),
        ({"review_risk": ["low"]}, "review risk invalid"),
        ({"review_profile": "folk"}, "review profile invalid"),
        ({"review_profile": ""}, "review profile invalid"),
        ({"review_profile": ["code"]}, "review profile invalid"),
        ({"owned_paths": "scripts"}, "review owned paths invalid"),
        ({"owned_paths": [1]}, "review owned paths invalid"),
        ({"owned_paths": [""]}, "review owned paths invalid"),
    ],
)
@pytest.mark.parametrize("cursor", [False, True])
def test_invalid_persisted_review_qualification_is_refused_before_publication(
    monkeypatch, tmp_path, updates, reason, cursor
):
    tasks, comments, calls = setup_record(monkeypatch, tmp_path, families={"anthropic"} if not cursor else {"openai"})
    if cursor:
        cursor_receipt_shape(tasks, "terminal", requested="grok-4.7-high", attested="Grok 4.7 256K High", **updates)
    else:
        write_task(tasks, **updates)
    with pytest.raises(recorder.RecordError, match=reason):
        recorder.record("review-one", pr_number=42, task_root=tasks, lock_root=tmp_path / "locks")
    assert comments == []
    assert calls == {"posts": 0, "statuses": 0}


@pytest.mark.parametrize(
    "updates,reason",
    [
        ({"agent": "claude", "model": "claude-sonnet-5-5", "review_risk": "critical"}, "Sonnet is excluded"),
        ({"agent": "claude", "model": "claude-sonnet-5-5", "review_risk": "high"}, "unqualified at code/high"),
        ({"agent": "grok", "model": "grok-4.7"}, "is not a formal reviewer on this harness"),
        ({"agent": "kimi", "model": "kimi-k3"}, "is not a formal reviewer on this harness"),
        # Gemini reviews Ukrainian only: no code-profile seat runs it.
        ({"agent": "agy", "model": "gemini-3.8-flash-high"}, "no catalog review seat"),
        ({"agent": "codex", "model": "claude-opus-5-5"}, "no catalog review seat"),
        ({"agent": "cursor-x", "model": "gpt-6.1-sol"}, "no catalog review seat"),
        (
            {
                "agent": "cursor",
                "model": "grok-4.7-high",
                "resolved_model": "Grok 4.7 256K High",
                "resolved_model_known": True,
                "resolved_model_source": "cursor-stream-json",
                "review_profile": "ukrainian",
            },
            "is not a Ukrainian reviewer",
        ),
    ],
)
def test_a_native_or_off_profile_verdict_the_resolver_never_qualifies_is_refused(
    monkeypatch, tmp_path, updates, reason
):
    tasks, comments, calls = setup_record(monkeypatch, tmp_path, families={"openai"})
    write_task(tasks, **updates)
    with pytest.raises(recorder.RecordError, match=reason):
        recorder.record("review-one", pr_number=42, task_root=tasks, lock_root=tmp_path / "locks")
    assert comments == []
    assert calls == {"posts": 0, "statuses": 0}


@pytest.mark.parametrize(
    "agent,model,families,recorded",
    [
        ("agy", "gemini-3.8-flash-high", {"openai"}, "family=google"),
        ("codex", "gpt-6.1-sol", {"google"}, "family=openai"),
        ("claude", "claude-opus-5-5", {"google"}, "family=anthropic"),
    ],
)
def test_a_ukrainian_profile_verdict_from_an_admitted_language_seat_records(
    monkeypatch, tmp_path, agent, model, families, recorded
):
    tasks, comments, _ = setup_record(monkeypatch, tmp_path, families=families)
    write_task(tasks, agent=agent, model=model, review_profile="ukrainian")
    assert recorder.record("review-one", pr_number=42, task_root=tasks, lock_root=tmp_path / "locks")["comment"] == (
        "posted"
    )
    assert recorded in comments[0]["body"]


# --- #9714: author provenance through delegate-normalized X-Agent trailers ------


def producer_trailer_commit(agent, task_id):
    from scripts.delegate import _x_agent_trailer

    return {"commit": {"message": f"feat: work\n\n{_x_agent_trailer(agent, task_id)}"}}


def cursor_author(tasks, task_id, resolved_model, *, archive=False, **updates):
    fields = {
        "agent": "cursor",
        "model": resolved_model,
        "resolved_model": resolved_model,
        "resolved_model_known": True,
        "resolved_model_source": "cursor-stream-json",
    }
    write_task(tasks / "archive" if archive else tasks, task_id=task_id, **{**fields, **updates})


@pytest.mark.parametrize(
    "agent,task_id,record,expected",
    [
        # Canonical agent-prefixed records signed with the stripped trailer.
        ("cursor", "cursor-9714-opus-finish", {"resolved_model": "Claude Opus 5.5 300K High"}, {"anthropic"}),
        ("cursor", "cursor-9714-live-shape", {"resolved_model": "Claude Opus 5.5 300K High"}, {"anthropic"}),
        ("codex", "codex-9712-stream", {"model": "gpt-6.1-sol"}, {"openai"}),
        ("cursor", "cursor/9714-nested", {"resolved_model": "Grok 4.7 256K High"}, {"xai"}),
        # Legacy unprefixed records still resolve.
        ("cursor", "9714-legacy", {"resolved_model": "Grok 4.7 256K High"}, {"xai"}),
        ("codex", "impl-9712-legacy", {"model": "gpt-6.1-sol"}, {"openai"}),
        # A model keyword in the title never decides the family; the run does.
        ("cursor", "cursor-9714-opus-finish", {"resolved_model": "Grok 4.7 256K High"}, {"xai"}),
        ("codex", "codex-9712-claude-stream", {"model": "gpt-6.1-sol"}, {"openai"}),
        ("claude", "claude-9712-codex-sonnet", {"model": "claude-opus-5-5"}, {"anthropic"}),
    ],
)
@pytest.mark.parametrize("archive", [False, True])
def test_producer_normalized_trailer_resolves_the_recorded_run(
    monkeypatch, tmp_path, agent, task_id, record, expected, archive
):
    tasks = tmp_path / "tasks"
    if agent == "cursor":
        cursor_author(tasks, task_id, record["resolved_model"], archive=archive)
    else:
        write_task(tasks / "archive" if archive else tasks, task_id=task_id, agent=agent, **record)
    monkeypatch.setattr(recorder, "_pages", lambda args: [producer_trailer_commit(agent, task_id)])
    assert recorder.author_families(REPOSITORY, 42, tasks) == expected


@pytest.mark.parametrize(
    "trailer",
    ["cursor/9714-opus-finish", "codex/9712-claude-stream", "codex/gpt-6.1-sol-fix-thing", "claude/opus-review"],
)
def test_a_task_title_without_a_record_never_guesses_a_family(monkeypatch, tmp_path, trailer):
    tasks = tmp_path / "tasks"
    tasks.mkdir()
    monkeypatch.setattr(recorder, "_pages", lambda args: [{"commit": {"message": f"feat: work\n\nX-Agent: {trailer}"}}])
    with pytest.raises(recorder.RecordError, match="author task provenance unavailable"):
        recorder.author_families(REPOSITORY, 42, tasks)


@pytest.mark.parametrize(
    "trailer,expected",
    [
        ("claude/claude-opus-5-5", {"anthropic"}),
        ("codex/gpt-6.1-sol", {"openai"}),
        ("cursor/grok-4.7-high", {"xai"}),
        ("cursor/claude-opus-5-5-high", {"anthropic"}),
        ("agy/gemini-3.8-flash-high", {"google"}),
    ],
)
def test_a_legacy_concrete_model_trailer_without_a_record_still_resolves(monkeypatch, tmp_path, trailer, expected):
    monkeypatch.setattr(recorder, "_pages", lambda args: [{"commit": {"message": f"feat: work\n\nX-Agent: {trailer}"}}])
    assert recorder.author_families(REPOSITORY, 42, tmp_path) == expected


def test_canonical_and_legacy_records_that_disagree_are_refused(monkeypatch, tmp_path):
    tasks = tmp_path / "tasks"
    cursor_author(tasks, "cursor-9714-dup", "Claude Opus 5.5 300K High")
    cursor_author(tasks, "9714-dup", "Grok 4.7 256K High")
    monkeypatch.setattr(recorder, "_pages", lambda args: [producer_trailer_commit("cursor", "cursor-9714-dup")])
    with pytest.raises(recorder.RecordError, match="conflicts across task records"):
        recorder.author_families(REPOSITORY, 42, tasks)


@pytest.mark.parametrize(
    "legacy",
    [{"agent": "codex", "model": "gpt-6.1-sol"}, {"agent": "cursor", "repository": "other/repo"}],
    ids=["foreign-agent", "foreign-repository"],
)
def test_a_foreign_record_behind_a_normalized_trailer_is_refused(monkeypatch, tmp_path, legacy):
    tasks = tmp_path / "tasks"
    cursor_author(tasks, "cursor-9714-foreign", "Grok 4.7 256K High")
    write_task(tasks, task_id="9714-foreign", **{"resolved_model_known": True, **legacy})
    monkeypatch.setattr(recorder, "_pages", lambda args: [producer_trailer_commit("cursor", "cursor-9714-foreign")])
    with pytest.raises(recorder.RecordError, match="provenance conflicts with commit trailer"):
        recorder.author_families(REPOSITORY, 42, tasks)


@pytest.mark.parametrize(
    "updates",
    [
        {"resolved_model_known": False, "resolved_model": "unattested-harness", "resolved_model_source": "pending"},
        {"resolved_model": "auto"},
    ],
    ids=["unattested", "auto"],
)
def test_an_unattested_canonical_cursor_record_is_refused(monkeypatch, tmp_path, updates):
    tasks = tmp_path / "tasks"
    cursor_author(tasks, "cursor-9714-opus-unknown", **{"resolved_model": "Claude Opus 5.5 300K High", **updates})
    monkeypatch.setattr(
        recorder, "_pages", lambda args: [producer_trailer_commit("cursor", "cursor-9714-opus-unknown")]
    )
    with pytest.raises(recorder.RecordError, match="author family"):
        recorder.author_families(REPOSITORY, 42, tasks)


AUTHOR_SOURCES_WITHOUT_A_RUNTIME_REPORT = [
    pytest.param({"__drop__": True}, id="absent"),
    pytest.param({"resolved_model_source": None}, id="null"),
    pytest.param({"resolved_model_source": ""}, id="empty"),
    pytest.param({"resolved_model_source": "pending"}, id="pending"),
    pytest.param({"resolved_model_source": "unknown"}, id="unknown"),
    pytest.param({"resolved_model_source": "unattested-harness"}, id="unattested-harness"),
    pytest.param({"resolved_model_source": "models_dev_cached_alias"}, id="catalog-alias"),
    pytest.param({"resolved_model_source": ["cursor-stream-json"]}, id="list"),
]


def unreported_cursor_author(tasks, task_id, resolved_model, source):
    source = dict(source)
    drop = source.pop("__drop__", False)
    cursor_author(tasks, task_id, resolved_model, **source)
    if drop:
        path = tasks / f"{task_id}.json"
        data = json.loads(path.read_text())
        del data["resolved_model_source"]
        path.write_text(json.dumps(data))


@pytest.mark.parametrize("source", AUTHOR_SOURCES_WITHOUT_A_RUNTIME_REPORT)
@pytest.mark.parametrize("task_id", ["cursor-9714-grok-author", "9714-legacy-author"])
def test_a_cursor_author_record_without_a_runtime_reported_source_is_refused(monkeypatch, tmp_path, source, task_id):
    tasks = tmp_path / "tasks"
    unreported_cursor_author(tasks, task_id, "Grok 4.7 256K High", source)
    monkeypatch.setattr(recorder, "_pages", lambda args: [producer_trailer_commit("cursor", task_id)])
    with pytest.raises(recorder.RecordError, match="Cursor author model is not a runtime report"):
        recorder.author_families(REPOSITORY, 42, tasks)


@pytest.mark.parametrize("source", sorted(recorder.RUNTIME_REPORTED_MODEL_SOURCES))
def test_a_cursor_author_record_with_each_runtime_reported_source_resolves(monkeypatch, tmp_path, source):
    tasks = tmp_path / "tasks"
    cursor_author(tasks, "cursor-9714-opus-author", "Claude Opus 5.5 300K High", resolved_model_source=source)
    monkeypatch.setattr(recorder, "_pages", lambda args: [producer_trailer_commit("cursor", "cursor-9714-opus-author")])
    assert recorder.author_families(REPOSITORY, 42, tasks) == {"anthropic"}


def record_against_cursor_author(monkeypatch, tmp_path, source):
    """Publish a Sol verdict whose PR author is a real Cursor task record."""
    real_author_families = recorder.author_families
    tasks, comments, calls = setup_record(monkeypatch, tmp_path)
    monkeypatch.setattr(recorder, "author_families", real_author_families)
    unreported_cursor_author(tasks, "cursor-9714-opus-critical", "Grok 4.7 256K High", source)
    monkeypatch.setattr(
        recorder, "_pages", lambda args: [producer_trailer_commit("cursor", "cursor-9714-opus-critical")]
    )
    return tasks, comments, calls


@pytest.mark.parametrize("source", AUTHOR_SOURCES_WITHOUT_A_RUNTIME_REPORT)
def test_an_unreported_cursor_author_blocks_publication(monkeypatch, tmp_path, source):
    tasks, comments, calls = record_against_cursor_author(monkeypatch, tmp_path, source)
    with pytest.raises(recorder.RecordError, match="Cursor author model is not a runtime report"):
        recorder.record("review-one", pr_number=42, task_root=tasks, lock_root=tmp_path / "locks")
    assert comments == []
    assert calls == {"posts": 0, "statuses": 0}


def test_a_live_shape_cursor_author_still_admits_an_independent_verdict(monkeypatch, tmp_path):
    tasks, comments, calls = record_against_cursor_author(
        monkeypatch, tmp_path, {"resolved_model_source": "cursor-stream-json"}
    )
    result = recorder.record("review-one", pr_number=42, task_root=tasks, lock_root=tmp_path / "locks")
    assert (result["comment"], result["status"]) == ("posted", "posted")
    assert "model=gpt-6.1-sol family=openai" in comments[0]["body"]
    assert calls == {"posts": 1, "statuses": 1}


@pytest.fixture
def real_recorder_matcher(monkeypatch):
    from scripts.opsec import prepublish as gate
    from tests.test_opsec_prepublish import real_tooling

    tooling = real_tooling()
    monkeypatch.setattr(gate, "private_tooling", lambda: tooling)
    return tooling


def assert_rendered_path_refusal(reply, rewritten, tooling):
    from scripts.opsec import prepublish as gate

    for text in (reply, rewritten):
        comment = recorder.build_comment(
            sha=SHA,
            task_id="review-one",
            started="2026-10-02T00:00:00+00:00",
            verdict="APPROVED",
            model="gpt-6.1-sol",
            family="openai",
            reply=text,
        )
        with pytest.raises(gate.PublishBlocked, match="rule=3-absolute-path"):
            gate.check_texts("github.com/unit/public", [comment], tooling=tooling, environment={})


@pytest.mark.parametrize("checkout", ["primary", "worktree"])
@pytest.mark.parametrize("separator", ["=", "\\", "&", "(", "[", "{"])
@pytest.mark.parametrize("traversal", ["/../../", "../../"])
def test_scanner_span_preserves_ascii_traversal(
    citation_checkout, tmp_path, real_recorder_matcher, checkout, separator, traversal
):
    root, worktree = citation_checkout
    cited_root = root if checkout == "primary" else worktree
    # Materialize the safe prefix and separator-bearing component so strict
    # resolution alone cannot hide the tokenizer disagreement from earlier rounds.
    (cited_root / f"a{separator}").mkdir()
    (tmp_path / "sibling/tools").mkdir(parents=True)
    reply = f"VERDICT: APPROVE\n{cited_root}/a{separator}{traversal}sibling/tools"
    rewritten = recorder.repository_relative_reply(reply, task={"worktree_path": str(worktree)}, primary_root=root)
    assert rewritten == reply
    assert_rendered_path_refusal(reply, rewritten, real_recorder_matcher)


@pytest.mark.parametrize("suffix", [":12", ":12:3"])
@pytest.mark.parametrize("checkout", ["primary", "worktree"])
def test_suffixed_file_symlink_outside_refuses(citation_checkout, tmp_path, real_recorder_matcher, suffix, checkout):
    root, worktree = citation_checkout
    outside = tmp_path / "outside.py"
    outside.write_text("# outside\n" * 20)
    cited_root = root if checkout == "primary" else worktree
    (cited_root / "link.py").symlink_to(outside)
    reply = f"VERDICT: APPROVE\n`{cited_root}/link.py{suffix}`"
    rewritten = recorder.repository_relative_reply(reply, task={"worktree_path": str(worktree)}, primary_root=root)
    assert rewritten == reply
    assert_rendered_path_refusal(reply, rewritten, real_recorder_matcher)


@pytest.mark.parametrize("checkout", ["primary", "worktree"])
@pytest.mark.parametrize("target_kind", ["file", "directory", "missing"])
def test_interpreter_symlink_citation_rewrites(
    citation_checkout, tmp_path, real_recorder_matcher, checkout, target_kind
):
    from scripts.opsec import prepublish as gate

    root, worktree = citation_checkout
    target = tmp_path / "interpreter"
    if target_kind == "file":
        target.write_text("# external interpreter fixture\n")
    elif target_kind == "directory":
        target.mkdir()
    cited_root = root if checkout == "primary" else worktree
    interpreter = cited_root / ".venv/bin/python"
    interpreter.parent.mkdir(parents=True)
    interpreter.symlink_to(target, target_is_directory=target_kind == "directory")
    reply = f"VERDICT: APPROVE\n`{interpreter}`"

    rewritten = recorder.repository_relative_reply(reply, task={"worktree_path": str(worktree)}, primary_root=root)

    assert rewritten == "VERDICT: APPROVE\n`.venv/bin/python`"
    gate.check_texts("github.com/unit/public", [rewritten], tooling=real_recorder_matcher, environment={})


@pytest.mark.parametrize("checkout", ["primary", "worktree"])
@pytest.mark.parametrize("suffix", ["", ":12", ":12:3"])
def test_symlinked_parent_escape_stays_absolute(citation_checkout, tmp_path, real_recorder_matcher, checkout, suffix):
    root, worktree = citation_checkout
    outside = tmp_path / "outside"
    outside.mkdir()
    (outside / "python").write_text("# outside fixture\n")
    cited_root = root if checkout == "primary" else worktree
    (cited_root / "escape").symlink_to(outside, target_is_directory=True)
    reply = f"VERDICT: APPROVE\n`{cited_root}/escape/python{suffix}`"

    rewritten = recorder.repository_relative_reply(reply, task={"worktree_path": str(worktree)}, primary_root=root)

    assert rewritten == reply
    assert_rendered_path_refusal(reply, rewritten, real_recorder_matcher)


@pytest.mark.parametrize("checkout", ["primary", "worktree"])
def test_outside_symlinked_parent_into_checkout_stays_absolute(
    citation_checkout, tmp_path, real_recorder_matcher, checkout
):
    root, worktree = citation_checkout
    cited_root = root if checkout == "primary" else worktree
    alias = tmp_path / "alias"
    alias.symlink_to(cited_root, target_is_directory=True)
    reply = f"VERDICT: APPROVE\n`{alias}/scripts/unit.py`"

    rewritten = recorder.repository_relative_reply(reply, task={"worktree_path": str(worktree)}, primary_root=root)

    assert rewritten == reply
    assert_rendered_path_refusal(reply, rewritten, real_recorder_matcher)


@pytest.mark.parametrize("outside_first", [True, False])
def test_neighboring_outside_span_survives_real_scanner(citation_checkout, real_recorder_matcher, outside_first):
    root, worktree = citation_checkout
    inside = f"`{worktree}/scripts/unit.py:12:3`"
    outside = f"`{root.parent}/outside/private.py:12`"
    citations = [outside, inside] if outside_first else [inside, outside]
    reply = "VERDICT: APPROVE\n" + " ".join(citations)
    rewritten = recorder.repository_relative_reply(reply, task={"worktree_path": str(worktree)}, primary_root=root)
    assert rewritten == reply.replace(inside, "`scripts/unit.py:12:3`")
    assert_rendered_path_refusal(reply, rewritten, real_recorder_matcher)


@pytest.mark.parametrize("prefix", ["<", ">", "="])
def test_rewrite_reverts_normalization_unstable_line(citation_checkout, real_recorder_matcher, prefix):
    root, _ = citation_checkout
    path = root / "\u0338unit.py"
    path.write_text("# fixture\n")
    line = f"{prefix}{path}"
    assert recorder.normalize_for_scan(line) == line
    assert recorder.normalize_for_scan(f"{prefix}{path.name}") != f"{prefix}{path.name}"
    reply = f"{root}/scripts/before.py\n{line}\n{root}/scripts/after.py"
    rewritten = recorder.repository_relative_reply(reply, task={}, primary_root=root)
    assert rewritten == f"scripts/before.py\n{line}\nscripts/after.py"
    assert_rendered_path_refusal(reply, rewritten, real_recorder_matcher)


def test_ordinary_denominator_real_scanner(citation_checkout, real_recorder_matcher):
    from scripts.opsec import prepublish as gate

    root, worktree = citation_checkout
    reply = (
        f"VERDICT: APPROVE\n{worktree}\n{root}\n{root}/scripts\n"
        f"`{worktree}/scripts/unit.py:12:3`\n"
        f"```\n{root}/tests/test_unit.py:3\n```\n"
        f"[source]({root}/scripts/unit.py:12)"
    )
    rewritten = recorder.repository_relative_reply(reply, task={"worktree_path": str(worktree)}, primary_root=root)
    assert rewritten == (
        "VERDICT: APPROVE\n.\n.\nscripts\n`scripts/unit.py:12:3`\n"
        "```\ntests/test_unit.py:3\n```\n[source](scripts/unit.py:12)"
    )
    gate.check_texts("github.com/unit/public", [rewritten], tooling=real_recorder_matcher, environment={})


@pytest.mark.parametrize(
    "citation", ["missing.py", "missing.py:12", "scripts:12", "scripts/unit.py:0", "scripts/unit.py:12:x"]
)
def test_ambiguous_or_nonexistent_citation_refuses(citation_checkout, real_recorder_matcher, citation):
    root, _ = citation_checkout
    reply = f"VERDICT: APPROVE\n`{root}/{citation}`"
    rewritten = recorder.repository_relative_reply(reply, task={}, primary_root=root)
    assert rewritten == reply
    assert_rendered_path_refusal(reply, rewritten, real_recorder_matcher)


def test_existing_suffixed_filename_is_ambiguous(citation_checkout, real_recorder_matcher):
    root, _ = citation_checkout
    (root / "scripts/unit.py:12").write_text("# different file\n")
    reply = f"VERDICT: APPROVE\n`{root}/scripts/unit.py:12`"
    rewritten = recorder.repository_relative_reply(reply, task={}, primary_root=root)
    assert rewritten == reply
    assert_rendered_path_refusal(reply, rewritten, real_recorder_matcher)


def test_matcher_refusal_prevents_record_transport(monkeypatch, tmp_path, synthetic_opsec):
    tasks, _, calls = setup_record(monkeypatch, tmp_path)
    (synthetic_opsec / "rules.json").write_text("invalid")
    with pytest.raises(recorder.RecordError, match="publish_blocked"):
        recorder.record("review-one", pr_number=42, task_root=tasks, lock_root=tmp_path / "locks")
    assert calls == {"posts": 0, "statuses": 0}


@pytest.mark.parametrize("separator", ["=", "\\", "&", "(", "[", "{"])
def test_complete_separator_filename_can_rewrite(citation_checkout, real_recorder_matcher, separator):
    from scripts.opsec import prepublish as gate

    root, _ = citation_checkout
    path = root / f"a{separator}b.py"
    path.write_text("# fixture\n")
    reply = f"`{path}:12:3`"
    rewritten = recorder.repository_relative_reply(reply, task={}, primary_root=root)
    assert rewritten == f"`{path.name}:12:3`"
    gate.check_texts("github.com/unit/public", [rewritten], tooling=real_recorder_matcher, environment={})


@pytest.mark.parametrize("kind", ["dangling-suffix", "file-root", "special-file"])
def test_ambiguous_filesystem_identity_stays_verbatim(citation_checkout, kind):
    import os

    root, _ = citation_checkout
    if kind == "dangling-suffix":
        (root / "scripts/unit.py:12").symlink_to(root / "missing")
        reply = f"`{root}/scripts/unit.py:12`"
    elif kind == "file-root":
        root = root / "scripts/unit.py"
        reply = f"`{root}`"
    else:
        path = root / "fifo"
        os.mkfifo(path)
        reply = f"`{path}`"
    assert recorder.repository_relative_reply(reply, task={}, primary_root=root) == reply


def test_missing_path_rule_refuses_even_when_all_lines_normalize(monkeypatch, tmp_path, synthetic_opsec):
    from tests.opsec_fixtures import synthetic_rules

    tasks, _, calls = setup_record(monkeypatch, tmp_path)
    write_task(tasks, reply="\u00a0VERDICT: APPROVE\n\u200b/checkout/scripts/unit.py")
    (synthetic_opsec / "rules.json").write_text(json.dumps(synthetic_rules()))
    with pytest.raises(recorder.RecordError, match="absolute-path rule unavailable/incompatible"):
        recorder.record("review-one", pr_number=42, task_root=tasks, lock_root=tmp_path / "locks")
    assert calls == {"posts": 0, "statuses": 0}
