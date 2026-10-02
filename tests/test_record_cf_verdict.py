"""Branch-pinned verdict recorder failure and serialization tests (#8509)."""

from __future__ import annotations

import json
import subprocess
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import pytest

from scripts.review import record_cf_verdict as recorder

SHA = "a" * 40
OTHER = "b" * 40
BRANCH = "codex/42"
REPOSITORY = "owner/repo"


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
    ],
)
def test_task_refusals_before_network(tmp_path, updates, reply, reason):
    tasks = tmp_path / "tasks"
    write_task(tasks, reply=reply, **updates)
    with pytest.raises(recorder.RecordError, match=reason):
        recorder.record("review-one", task_root=tasks, lock_root=tmp_path / "locks")


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
        ("/checkout, then /checkout/scripts/unit.py.", "., then scripts/unit.py."),
        ("No paths; scripts/unit.py:12", "No paths; scripts/unit.py:12"),
        ("/outside/private.py:12", "/outside/private.py:12"),
        ("/checkout-other/private.py", "/checkout-other/private.py"),
        ("/else/checkout/scripts/unit.py", "/else/checkout/scripts/unit.py"),
        ("/checkout/../private.py", "/checkout/../private.py"),
        ("https://example.test/checkout/scripts/unit.py", "https://example.test/checkout/scripts/unit.py"),
    ],
)
def test_repository_relative_reply_preserves_citations_and_outside_text(text, expected):
    review = {"worktree_path": "/checkout/.worktrees/dispatch/cursor/review"}
    assert recorder.repository_relative_reply(text, task=review, primary_root=Path("/checkout")) == expected


@pytest.mark.parametrize("checkout", [{"cwd": "/review"}, {"worktree_path": "/review", "cwd": "/review/scripts"}])
def test_repository_relative_reply_uses_recorded_checkout(checkout):
    assert recorder.repository_relative_reply(
        "/review/scripts/unit.py:12", task=checkout, primary_root=Path("/checkout")
    ) == "scripts/unit.py:12"


@pytest.mark.parametrize("checkout", [None, "relative", 123])
def test_repository_relative_reply_ignores_invalid_checkout(checkout):
    assert recorder.repository_relative_reply(
        "/outside/unit.py /checkout/scripts/unit.py", task={"worktree_path": checkout}, primary_root=Path("/checkout")
    ) == "/outside/unit.py scripts/unit.py"


def test_repository_relative_reply_keeps_symlink_escapes(monkeypatch, tmp_path):
    root = tmp_path / "checkout"
    root.mkdir()
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
        ("VERDICT: APPROVE\n`/checkout/.worktrees/dispatch/cursor/review/scripts/unit.py:12`\n"
         "```\n/checkout/tests/test_unit.py:3\n```", False),
        ("VERDICT: APPROVE", False),
        ("VERDICT: APPROVE\n/checkout/scripts/unit.py /outside/private.py:12", True),
        ("VERDICT: APPROVE\n/checkout-other/private.py", True),
        ("VERDICT: APPROVE\n/checkout/../private.py", True),
        ("VERDICT: APPROVE\n/checkout/scripts/unit.py\nSENTINEL-HOST-TOKEN", True),
    ],
)
def test_record_fixture_dry_run_through_publication_scanner(monkeypatch, tmp_path, synthetic_opsec, capsys, reply, refused):
    """Run the recorder and typed publisher with only the GitHub transport faked."""
    from scripts.publish import github
    from tests.opsec_fixtures import synthetic_rules

    rules = synthetic_rules()
    rules["1"]["patterns"].append({"id": "synthetic-host-path", "regex": r"(?<![<\w:])/[A-Za-z][^\s`]*"})
    (synthetic_opsec / "rules.json").write_text(json.dumps(rules))
    real_json = recorder._run_json
    tasks, comments, calls = setup_record(monkeypatch, tmp_path)
    fake_json = recorder._run_json
    write_task(tasks, reply=reply, worktree_path="/checkout/.worktrees/dispatch/cursor/review")
    monkeypatch.setattr(recorder, "_repo_root", lambda: Path("/checkout"))

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
        assert "publish_blocked" in diagnostic and "class=1" in diagnostic
        assert reply not in diagnostic
        assert "/outside" not in diagnostic and "/checkout" not in diagnostic and "SENTINEL-HOST-TOKEN" not in diagnostic
        assert calls == {"posts": 0, "statuses": 0}
        record = recorder.record
        monkeypatch.setattr(
            recorder, "record", lambda task_id, **kwargs: record(task_id, task_root=tasks, lock_root=tmp_path / "locks", **kwargs)
        )
        assert recorder.main(["--task-id", "review-one", "--pr", "42"]) == 1
        output = capsys.readouterr()
        assert "class=1" in output.out
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
    write_task(tasks, agent="cursor", model="auto", **{"resolved_model_source": "cursor-stream-json", **updates})


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
