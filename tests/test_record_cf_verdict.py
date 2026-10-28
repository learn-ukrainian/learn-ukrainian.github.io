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
from tempfile import TemporaryDirectory

import pytest

from scripts.common.git_context import GIT_REDIRECT_ENV_KEYS, sanitized_git_env
from scripts.common.scratch import ensure_scratch_root
from scripts.orchestration.fleet_repos import FleetRepo
from scripts.review import record_cf_verdict as recorder
from tests.claude_route_accounts import HOST_ACCOUNT
from tests.test_verdict_parser import CAPACITY_OUTLINES, FROZEN_CONTAINER_CASES, OVERLAP_QUOTE

SHA = "a" * 40
OTHER = "b" * 40
BRANCH = "codex/42"
REPOSITORY = "owner/repo"


@pytest.mark.parametrize("archived", [False, True])
@pytest.mark.parametrize("status", ["running", "done", "dry_run"])
def test_admitted_unknown_history_requires_non_dry_run_task(tmp_path, monkeypatch, archived, status):
    tasks = tmp_path / "tasks"
    records = tasks / recorder.ARCHIVE_DIR_NAME if archived else tasks
    records.mkdir(parents=True)
    receipt = {
        "repository": REPOSITORY,
        "head_branch": BRANCH,
        "head_sha": SHA,
        "history_remote_head_sha": SHA,
        "review_plan": "red_team",
        "unknown_history": [OTHER],
        "check": "structural",
        "applicable": True,
        "assumed_model": None,
        "reviewer": {"review_mode": "red_team"},
    }
    (records / "author.json").write_text(json.dumps({"status": status, "authoring_review_admission": receipt}))
    monkeypatch.setattr(recorder, "_facts_git", lambda *_a, **_k: f"{SHA}\n{OTHER}\n".encode())
    allowed = recorder.admitted_unknown_history(
        repository=REPOSITORY, branch=BRANCH, head_sha=SHA, task_root=tasks, repo_root=tmp_path
    )
    assert allowed == (() if status == "dry_run" else (OTHER,))


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
        (
            '```json\n{"schema_version":"code-review-findings.v1",'
            '"overall":{"correctness":"correct","explanation":"Reviewed the diff.","confidence":0.9},'
            '"findings":[]}\n```\n\n`VERDICT: APPROVE` for `0123456789abcdef`',
            "APPROVED",
        ),
    ],
)
def test_token_normalization(reply, expected):
    assert recorder.normalize_verdict(reply) == expected


@pytest.mark.parametrize("newline", ["\n", "\r\n", "\r"], ids=["lf", "crlf", "cr"])
@pytest.mark.parametrize("case,reply,expected", FROZEN_CONTAINER_CASES, ids=[c[0] for c in FROZEN_CONTAINER_CASES])
def test_container_visibility_reaches_recorder_before_any_forge_effect(
    tmp_path, monkeypatch, case, reply, expected, newline
):
    response = reply.replace("\n", newline)
    normalized = {"BLOCKED": "BLOCKED", "REQUEST_CHANGES": "CHANGES_REQUESTED"}
    observed = []
    original = recorder._review_verdict_and_count

    def observe(text):
        result = original(text)
        observed.append(result)
        return result

    def stop_before_forge(*_args):
        raise recorder.RecordError("synthetic stop before forge")

    monkeypatch.setattr(recorder, "_review_verdict_and_count", observe)
    monkeypatch.setattr(recorder, "_pr", stop_before_forge)
    write_task(tmp_path / "tasks", reply=response)
    if expected:
        assert recorder.normalize_verdict(response) == normalized[expected[0]]
        reason = "synthetic stop before forge"
    else:
        with pytest.raises(recorder.RecordError, match="missing or ambiguous"):
            recorder.normalize_verdict(response)
        reason = "missing or ambiguous"
    with pytest.raises(recorder.RecordError, match=reason):
        recorder.record("review-one", task_root=tmp_path / "tasks", lock_root=tmp_path / "locks")
    assert observed == ([(normalized[expected[0]], "unknown")] if expected else [])


def test_recorder_parser_failure_precedes_forge_effects(tmp_path, monkeypatch):
    from markdown_it import MarkdownIt

    def unavailable(*_args):
        raise RuntimeError("synthetic parser unavailable")

    monkeypatch.setattr(MarkdownIt, "parse", unavailable)
    monkeypatch.setattr(recorder, "_pr", lambda *_a: pytest.fail("parser failure must precede forge access"))
    write_task(tmp_path / "tasks")
    with pytest.raises(RuntimeError, match="synthetic parser unavailable"):
        recorder.record("review-one", task_root=tmp_path / "tasks", lock_root=tmp_path / "locks")


@pytest.mark.parametrize("newline", ["\n", "\r\n", "\r"])
@pytest.mark.parametrize("outline", CAPACITY_OUTLINES, ids=["inline", "indented"])
@pytest.mark.parametrize("prefix", ["", "VERDICT: REQUEST_CHANGES\n\n"])
def test_capacity_failure_precedes_recorder_forge_effects(tmp_path, monkeypatch, newline, outline, prefix):
    response = (prefix + outline + "```\nVERDICT: APPROVE\n```\n").replace("\n", newline)
    monkeypatch.setattr(recorder, "_pr", lambda *_a: pytest.fail("capacity failure must precede forge access"))
    with pytest.raises(ValueError, match="CommonMark verdict visibility nesting limit"):
        recorder.normalize_verdict(response)
    write_task(tmp_path / "tasks", reply=response)
    with pytest.raises(ValueError, match="CommonMark verdict visibility nesting limit"):
        recorder.record("review-one", task_root=tmp_path / "tasks", lock_root=tmp_path / "locks")


@pytest.mark.parametrize("newline", ["\n", "\r\n", "\r"])
@pytest.mark.parametrize(
    "reply,expected",
    [
        (OVERLAP_QUOTE, None),
        (OVERLAP_QUOTE + "\nVERDICT: BLOCKED\n", "BLOCKED"),
        (OVERLAP_QUOTE.replace("> para\nVERDICT", "> para\n\nVERDICT"), "APPROVED"),
        ("- " * 9 + "x\n\n```\nVERDICT: APPROVE\n```\n", None),
        ("- " * 9 + "x\n\n```\nVERDICT: APPROVE\n```\n\nVERDICT: APPROVE\n", "APPROVED"),
    ],
)
def test_overlap_and_supported_depth_recorder_controls(tmp_path, monkeypatch, newline, reply, expected):
    response = reply.replace("\n", newline)
    effects = []

    def stop_before_forge(*_args):
        effects.append("forge boundary")
        raise recorder.RecordError("synthetic stop before forge")

    monkeypatch.setattr(recorder, "_pr", stop_before_forge)
    write_task(tmp_path / "tasks", reply=response)
    if expected:
        assert recorder.normalize_verdict(response) == expected
    else:
        with pytest.raises(recorder.RecordError, match="missing or ambiguous"):
            recorder.normalize_verdict(response)
    with pytest.raises(
        recorder.RecordError, match="synthetic stop before forge" if expected else "missing or ambiguous"
    ):
        recorder.record("review-one", task_root=tmp_path / "tasks", lock_root=tmp_path / "locks")
    assert effects == (["forge boundary"] if expected else [])


def test_full_nested_task_id_is_safe_and_loadable(tmp_path):
    write_task(tmp_path, task_id="codex/review-one")
    loaded, reply = recorder._task("codex/review-one", tmp_path)
    assert loaded["status"] == "done"
    assert reply == "VERDICT: APPROVE"
    with pytest.raises(recorder.RecordError, match="invalid task id"):
        recorder._task("codex/../review-one", tmp_path)


@pytest.mark.parametrize("storage", ["hot", "archived", "replaced"])
@pytest.mark.parametrize("rewrite", ["overwrite", "replace", "normalize_newlines"])
def test_terminal_result_rewrite_refused_before_publication(tmp_path, monkeypatch, storage, rewrite):
    """Accidental sidecar edits cannot publish a settled task's altered verdict (#10447)."""
    tasks, comments, calls = setup_record(monkeypatch, tmp_path)
    records = tasks / "archive" if storage == "archived" else tasks
    original = b"VERDICT: REQUEST_CHANGES\r\nA finding.\r\n"
    if storage == "replaced":
        # A force-new task reuses the hot name while the previous result is archived.
        write_task(tasks / "archive", reply="VERDICT: APPROVE")
    write_task(records, result_sha256=hashlib.sha256(original).hexdigest(), result_file="ignored.result")
    if storage == "archived":
        (tasks / "review-one.json").rename(tasks / "unused.json")
    sidecar = records / "review-one.result"
    sidecar.write_bytes(original)
    altered = original.replace(b"\r\n", b"\n") if rewrite == "normalize_newlines" else b"VERDICT: APPROVE"
    if rewrite == "replace":
        replacement = records / "replacement.result"
        replacement.write_bytes(altered)
        replacement.replace(sidecar)
    else:
        sidecar.write_bytes(altered)
    before = {suffix: (records / f"review-one.{suffix}").read_bytes() for suffix in ("json", "result")}

    with pytest.raises(recorder.RecordError, match=r"terminal_result_digest_mismatch.*review-one.*writer unknown"):
        recorder.record("review-one", pr_number=42, task_root=tasks, lock_root=tmp_path / "locks")

    assert comments == [] and calls == {"posts": 0, "statuses": 0}
    assert before == {suffix: (records / f"review-one.{suffix}").read_bytes() for suffix in before}


@pytest.mark.parametrize("storage", ["hot", "archived", "replaced"])
@pytest.mark.parametrize("hash_state", ["matching", "absent", "null"])
def test_terminal_result_hash_preserves_publication(tmp_path, monkeypatch, storage, hash_state):
    tasks, comments, calls = setup_record(monkeypatch, tmp_path)
    checkout = tmp_path / "checkout"
    source = checkout / "scripts" / "unit.py"
    source.parent.mkdir(parents=True)
    source.write_text("value = 1\n")
    monkeypatch.setattr(recorder, "_repo_root", lambda: checkout)
    original = f"VERDICT: APPROVE\r\nSee {source}:1\r\n".encode()
    records = tasks / "archive" if storage == "archived" else tasks
    if storage == "replaced":
        write_task(tasks / "archive", reply="VERDICT: REQUEST_CHANGES", result_sha256="0" * 64)
    updates = (
        {}
        if hash_state == "absent"
        else {"result_sha256": hashlib.sha256(original).hexdigest() if hash_state == "matching" else None}
    )
    write_task(records, result_file="ignored.result", **updates)
    if storage == "archived":
        (tasks / "review-one.json").rename(tasks / "unused.json")
    sidecar = records / "review-one.result"
    sidecar.write_bytes(original)

    result = recorder.record("review-one", pr_number=42, task_root=tasks, lock_root=tmp_path / "locks")

    assert result["verdict"] == "APPROVED"
    assert calls == {"posts": 1, "statuses": 1}
    assert "VERDICT: APPROVE\nSee scripts/unit.py:1\n" in comments[0]["body"]
    assert sidecar.read_bytes() == original


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


@pytest.mark.parametrize("model,family", [("claude-opus-5-5", "anthropic"), ("gpt-6.1-sol", "openai")])
def test_formal_reviewer_still_admits_opus_and_sol(model, family):
    recorder._require_formal_reviewer(cursor=False, reported=model, model=model, family=family)


def facts_for(families, *, changed_paths=(), subject_seats=frozenset()):
    """Branch facts for recorder tests that do not exercise Git enumeration."""
    return recorder.BranchReviewFacts(
        repository=REPOSITORY,
        base_tip_sha=OTHER,
        head_sha=SHA,
        merge_base_sha=OTHER,
        commits=tuple(
            recorder.CommitAttribution(
                None,
                family,
                "trailer-model",
                author_models=(
                    {"openai": "gpt-6-luna", "google": "gemini-3.8-flash-high", "anthropic": "claude-opus-5-5"}.get(
                        family, "gpt-6-luna"
                    ),
                ),
            )
            for family in sorted(families)
        ),
        existing_families=frozenset(families),
        incoming_writer=None,
        incoming_family=None,
        changed_paths=tuple(changed_paths),
        owned_paths=(),
        subject_seats=frozenset(subject_seats),
        subject_families=frozenset(),
        subject_evidence=(),
    )


def setup_record(monkeypatch, tmp_path, *, head=SHA, branch=BRANCH, families=None, status_error=False):
    tasks = tmp_path / "tasks"
    write_task(tasks)
    comments = []
    calls = {"posts": 0, "statuses": 0}
    # These unit tests replace Git facts; integration coverage uses real catalog
    # resolution and independent object stores in authoring_review_feasibility.
    catalog = {**recorder.load_fleet_repos(), "unit": FleetRepo("unit", REPOSITORY, "unit", "test")}
    monkeypatch.setattr(recorder, "load_fleet_repos", lambda: catalog)
    monkeypatch.setattr(recorder, "resolve_review_repository", lambda root, _key, **_kwargs: root)

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
        "pr_review_facts",
        lambda repository, number, **kwargs: facts_for(families if families is not None else {"google"}),
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


def red_team_task(
    tasks, tmp_path, *, prompt="Adversarial red-team review: find failures and missing tests.", **updates
):
    path = tmp_path / "red-team.md"
    path.write_text(prompt, encoding="utf-8")
    write_task(tasks, review_mode="red_team", prompt_sha256=hashlib.sha256(prompt.encode()).hexdigest(), **updates)
    return path


@pytest.mark.parametrize(
    "scope",
    [
        {"review_language_lane": True},
        {"language_lane": True},
        {"research_task_family": "ukrainian-review"},
        {"review_profile": "ukrainian"},
        {"research_track": "l2-uk-b1"},
    ],
)
def test_red_team_ukrainian_task_refused_before_publication(monkeypatch, tmp_path, scope):
    tasks, comments, calls = setup_record(monkeypatch, tmp_path)
    prompt = red_team_task(tasks, tmp_path, sources_mcp_call_count=3, **scope)
    with pytest.raises(recorder.RecordError, match="RED_TEAM_REFUSED: Ukrainian-language reviews stay cross-family"):
        recorder.record(
            "review-one", pr_number=42, task_root=tasks, lock_root=tmp_path / "locks", red_team_prompt=prompt
        )
    assert comments == [] and calls == {"posts": 0, "statuses": 0}


@pytest.mark.parametrize("archived", [False, True])
@pytest.mark.parametrize(
    "agent,reviewer_id,author_id",
    [
        ("cursor", "claude-impl-x", "impl-x"),
        ("claude", "codex/author-one", "author-one"),
        ("cursor", " CLAUDE-IMPL-X ", "impl-x"),
        ("claude", "codex/gpt-6.1-sol", "gpt-6.1-sol"),
    ],
)
def test_red_team_cross_seat_author_task_refused_before_publication(
    monkeypatch, tmp_path, archived, agent, reviewer_id, author_id
):
    from dataclasses import replace

    tasks, comments, calls = setup_record(monkeypatch, tmp_path)
    model = "Grok 4.7 256K High" if agent == "cursor" else "claude-opus-5-5"
    prompt = red_team_task(
        tasks,
        tmp_path,
        agent=agent,
        model=model,
        resolved_model=model,
        resolved_model_known=True,
        resolved_model_source="cursor-stream-json",
    )
    # Keep the loadable filename separate from the task's stored identity.
    path = tasks / "review-one.json"
    data = json.loads(path.read_text())
    data["task_id"] = reviewer_id
    path.write_text(json.dumps(data))
    if archived:
        (tasks / "archive").mkdir()
        for suffix in ("json", "result"):
            (tasks / f"review-one.{suffix}").rename(tasks / "archive" / f"review-one.{suffix}")
    write_task(tasks, task_id=author_id, model="gpt-6.1-sol")
    authors = recorder._attribute_commit_authors(
        {"sha": SHA, "commit": {"message": f"work\n\nX-Agent: codex/gpt-6-luna\nX-Agent: codex/{author_id}"}},
        repository=REPOSITORY,
        task_root=tasks,
        base_sha=lambda: OTHER,
    )
    assert authors[1].task_id == author_id
    facts = replace(facts_for({"openai"}), commits=authors)
    monkeypatch.setattr(recorder, "pr_review_facts", lambda *_a, **_k: facts)
    with pytest.raises(recorder.RecordError, match="SELF_REVIEW_DETECTED"):
        recorder.record(
            "review-one", pr_number=42, task_root=tasks, lock_root=tmp_path / "locks", red_team_prompt=prompt
        )
    assert comments == [] and calls == {"posts": 0, "statuses": 0}


@pytest.mark.parametrize("families", [{"openai"}, {"google", "openai"}, {"cursor", "openai"}])
def test_same_family_red_team_records_and_reconciles(monkeypatch, tmp_path, families):
    tasks, comments, calls = setup_record(monkeypatch, tmp_path, families=families)
    prompt = red_team_task(tasks, tmp_path)
    for expected in ("posted", "existing"):
        result = recorder.record(
            "review-one", pr_number=42, task_root=tasks, lock_root=tmp_path / "locks", red_team_prompt=prompt
        )
        assert result["comment"] == expected
        assert result["review_mode"] == "red_team"
    assert calls == {"posts": 1, "statuses": 2}
    body = comments[0]["body"]
    assert body.startswith("### Adversarial red-team review\nReview mode: red_team\n")
    assert body.endswith("review_mode=red_team -->")
    from scripts.orchestration.integration_sweep import lookup_verdict

    verdict = lookup_verdict(comments, SHA, "fleet")
    assert verdict.state == "APPROVED"
    assert verdict.review_mode == "red_team"


@pytest.mark.parametrize("profile", ["infra", "unknown"])
def test_red_team_non_code_profile_refused_before_publication(monkeypatch, tmp_path, profile):
    tasks, comments, calls = setup_record(monkeypatch, tmp_path)
    prompt = red_team_task(tasks, tmp_path, review_profile=profile)
    with pytest.raises(recorder.RecordError, match="RED_TEAM_REFUSED: code review requires"):
        recorder.record(
            "review-one", pr_number=42, task_root=tasks, lock_root=tmp_path / "locks", red_team_prompt=prompt
        )
    assert comments == [] and calls == {"posts": 0, "statuses": 0}


@pytest.mark.parametrize("verdict", ["CHANGES_REQUESTED", "REQUEST_CHANGES", "BLOCKED"])
@pytest.mark.parametrize(
    "head,prior_mode,mode",
    [
        (SHA, "cross_family", "red_team"),
        (OTHER, "cross_family", "red_team"),
        (SHA, "red_team", "red_team"),
        (SHA, "cross_family", "cross_family"),
    ],
)
def test_red_team_outside_rejection_publication_guard(monkeypatch, tmp_path, verdict, head, prior_mode, mode):
    tasks, comments, calls = setup_record(monkeypatch, tmp_path)
    prompt = red_team_task(tasks, tmp_path) if mode == "red_team" else None
    comments.append(
        {
            "body": recorder.build_comment(
                sha=head,
                task_id="prior-review",
                started="2026-09-23T11:00:00.000001+00:00",
                verdict=recorder.normalize_verdict(f"VERDICT: {verdict}"),
                model="claude-opus-5-5",
                family="anthropic",
                reply=f"VERDICT: {verdict}",
                review_mode=prior_mode,
            )
        }
    )
    if head == SHA and prior_mode == "cross_family" and mode == "red_team":
        with pytest.raises(
            recorder.RecordError, match="RED_TEAM_REFUSED: outside-family rejection exists for this head"
        ):
            recorder.record(
                "review-one", pr_number=42, task_root=tasks, lock_root=tmp_path / "locks", red_team_prompt=prompt
            )
        assert calls == {"posts": 0, "statuses": 0}
    else:
        result = recorder.record(
            "review-one", pr_number=42, task_root=tasks, lock_root=tmp_path / "locks", red_team_prompt=prompt
        )
        assert result["verdict"] == "APPROVED"
        assert calls == {"posts": 1, "statuses": 1}


def recorded_verdict(sha, verdict, *, task_id="prior-review", mode="cross_family", edited=False):
    """A trusted verdict comment the keeper reads, as the recorder posts it (``edited`` changes it later)."""
    body = recorder.build_comment(
        sha=sha,
        task_id=task_id,
        started="2026-09-23T11:00:00.000001+00:00",
        verdict=verdict,
        model="claude-opus-5-5",
        family="anthropic",
        reply=f"VERDICT: {verdict}",
        review_mode=mode,
    )
    stamp = "2026-09-23T11:30:00Z"
    return {
        "body": body,
        "user": {"login": "fleet"},
        "author_association": "MEMBER",
        "created_at": stamp,
        "updated_at": "2026-09-23T11:45:00Z" if edited else stamp,
    }


def retargeted_review(monkeypatch, tmp_path):
    """A real branch whose PR base was cut after its OpenAI commit, leaving only a Claude tip in ``cut..head``."""
    repo, origin = tmp_path / "pr-repo", tmp_path / "pr-origin.git"
    env = {key: value for key, value in os.environ.items() if not key.startswith("GIT_")}
    env.update(
        GIT_AUTHOR_NAME="t",
        GIT_AUTHOR_EMAIL="t@example.invalid",
        GIT_COMMITTER_NAME="t",
        GIT_COMMITTER_EMAIL="t@example.invalid",
        GIT_CONFIG_GLOBAL=os.devnull,
        GIT_CONFIG_NOSYSTEM="1",
    )

    def run(*args):
        command = ["git", "-C", str(repo), *args]
        return subprocess.run(command, check=True, capture_output=True, text=True, env=env, timeout=30).stdout.strip()

    repo.mkdir()
    run("init", "-q")
    run("commit", "-q", "--allow-empty", "-m", "root\n\nX-Agent: claude/claude-opus-5-5")
    run("init", "-q", "--bare", str(origin))
    run("--git-dir", str(origin), "symbolic-ref", "HEAD", "refs/heads/main")
    run("remote", "add", "origin", str(origin))
    run("push", "-q", "origin", "HEAD:refs/heads/main")
    run("commit", "-q", "--allow-empty", "-m", "work\n\nX-Agent: codex/gpt-6.1-sol")
    cut = run("rev-parse", "HEAD")
    run("commit", "-q", "--allow-empty", "-m", "tip\n\nX-Agent: claude/claude-opus-5-5")
    head = run("rev-parse", "HEAD")
    listing = [
        {
            "sha": head,
            "commit": {
                "message": run("show", "--no-patch", "--format=%B", head),
                "tree": {"sha": run("rev-parse", f"{head}^{{tree}}")},
            },
            "parents": [{"sha": cut}],
        }
    ]
    return repo, cut, head, listing


@pytest.mark.parametrize(
    "mode,state",
    [
        *((mode, rejection) for mode in ("cross_family", "red_team") for rejection in ("CHANGES_REQUESTED", "BLOCKED")),
        # The keeper reads an edited marker at this head as unknown and lands no APPROVE (F4).
        ("cross_family", "edited"),
        ("red_team", "edited"),
        # An unresolvable X-Agent trailer excludes no family, so no reviewer is provably outside it (F1).
        ("cross_family", "unresolved-author"),
        # A task id without a task record is unresolved on a single-family harness too (F5).
        ("cross_family", "unresolved-kimi"),
        # The PR's base is never the authorship range: one cut after the OpenAI commit hides nothing (F6).
        ("cross_family", "retargeted-base"),
        # A red team refuses an unresolved author too; --review-author-model cannot name its model (F9).
        ("red_team", "unresolved-author"),
    ],
)
def test_same_head_approve_after_rejection_is_refused_in_every_mode(monkeypatch, tmp_path, mode, state):
    from dataclasses import replace

    from scripts.orchestration import integration_sweep as sweep

    if state == "retargeted-base":
        pr_review_facts = recorder.pr_review_facts
        repo, cut, head, listing = retargeted_review(monkeypatch, tmp_path)
        tasks, comments, calls = setup_record(monkeypatch, tmp_path, head=head)
        write_task(tasks, worktree_base_sha=head)
        monkeypatch.setattr(recorder, "pr_review_facts", pr_review_facts)
        monkeypatch.setattr(recorder, "resolve_review_repository", lambda *_a, **_k: repo)
        monkeypatch.setattr(recorder, "_pages", lambda _request: listing)
        fake_json = recorder._run_json

        def retargeted(args, **kwargs):
            # GitHub reports the PR's base as ``cut``; the recorder must not read it.
            if isinstance(args, list) and args[:3] == ["gh", "pr", "view"] and "baseRefOid" in args[-1]:
                return {"baseRefName": "cut", "baseRefOid": cut, "headRefOid": head}
            return fake_json(args, **kwargs)

        monkeypatch.setattr(recorder, "_run_json", retargeted)
        with pytest.raises(recorder.RecordError, match="differs from the local base\\.\\.head enumeration"):
            recorder.record("review-one", pr_number=42, task_root=tasks, lock_root=tmp_path / "locks")
        assert comments == [] and calls == {"posts": 0, "statuses": 0}
        return
    tasks, comments, calls = setup_record(monkeypatch, tmp_path)
    # An explicit comparison model satisfies the red-team seat rule for an author without a model.
    author_model = {"review_author_model": "claude-opus-5-5"} if state == "unresolved-author" else {}
    prompt = red_team_task(tasks, tmp_path, **author_model) if mode == "red_team" else None
    kwargs = dict(pr_number=42, task_root=tasks, lock_root=tmp_path / "locks", red_team_prompt=prompt)
    if state in {"unresolved-author", "unresolved-kimi"}:
        harness = "kimi" if state == "unresolved-kimi" else "claude"
        author = recorder._attribute_commit(
            {"sha": SHA, "commit": {"message": f"change\n\nX-Agent: {harness}/cto-not-a-model"}},
            repository=REPOSITORY,
            task_root=tasks,
            base_sha=lambda: OTHER,
        )
        facts = replace(facts_for({author.family}), commits=(author,))
        monkeypatch.setattr(recorder, "pr_review_facts", lambda *_a, **_k: facts)
        with pytest.raises(recorder.RecordError, match=r"AUTHOR_UNRESOLVED.*no reviewer can be proved outside"):
            recorder.record("review-one", **kwargs)
        assert comments == [] and calls == {"posts": 0, "statuses": 0}
        return
    edited = state == "edited"
    verdict = "APPROVED" if edited else state
    comments.append(recorded_verdict(SHA, verdict, mode=mode, edited=edited))
    reason = "keeper reads this head's verdict as unknown" if edited else "only an APPROVE at a new head clears it"
    with pytest.raises(recorder.RecordError, match=reason):
        recorder.record("review-one", **kwargs)
    assert len(comments) == 1 and calls == {"posts": 0, "statuses": 0}
    # The keeper reads the same head the same way: the rejection or unknown state stands.
    assert sweep.lookup_verdict(comments, SHA, "fleet").state == ("unknown" if edited else verdict)
    # A rejection or edit at an earlier head is cleared by an APPROVE at the new head.
    comments[0] = recorded_verdict(OTHER, verdict, mode=mode, edited=edited)
    assert recorder.record("review-one", **kwargs)["verdict"] == "APPROVED"
    assert sweep.lookup_verdict(comments, SHA, "fleet").state == "APPROVED"


@pytest.mark.parametrize(
    "risk,security,prior_heads,refused",
    [
        (None, False, 2, False),
        (None, False, 3, True),
        ("high", False, 3, True),
        # The review task's own --risk critical never raises a non-security diff past 3 rounds (F3).
        ("critical", False, 3, True),
        # A security-sensitive diff reaches 5 rounds whatever risk the task recorded.
        ("low", True, 4, False),
        (None, True, 5, True),
    ],
)
def test_verdict_beyond_review_budget_is_refused(monkeypatch, tmp_path, risk, security, prior_heads, refused):
    tasks, comments, calls = setup_record(monkeypatch, tmp_path)
    write_task(tasks, **({"review_risk": risk, "options": {"risk": risk}} if risk else {}))
    changed = ("scripts/review/record_cf_verdict.py",) if security else ("docs/readme.md",)
    facts = facts_for({"google"}, changed_paths=changed)
    monkeypatch.setattr(recorder, "pr_review_facts", lambda *_a, **_k: facts)
    comments.extend(recorded_verdict(f"{index:x}" * 40, "CHANGES_REQUESTED") for index in range(1, prior_heads + 1))
    # More verdicts at a head already reviewed open no new round.
    comments.append(recorded_verdict("1" * 40, "CHANGES_REQUESTED", task_id="second-seat"))
    kwargs = dict(pr_number=42, task_root=tasks, lock_root=tmp_path / "locks")
    if refused:
        with pytest.raises(recorder.RecordError, match=r"REVIEW_BUDGET_EXHAUSTED.*budget end is never approval"):
            recorder.record("review-one", **kwargs)
        assert calls == {"posts": 0, "statuses": 0}
    else:
        assert recorder.record("review-one", **kwargs)["verdict"] == "APPROVED"


@pytest.mark.parametrize("body", [None, "<!-- cf-verdict v1 unreadable -->"])
def test_red_team_unreadable_marker_history_refused(monkeypatch, tmp_path, body):
    tasks, comments, calls = setup_record(monkeypatch, tmp_path)
    prompt = red_team_task(tasks, tmp_path)
    comments.append({"body": body})
    with pytest.raises(recorder.RecordError):
        recorder.record(
            "review-one", pr_number=42, task_root=tasks, lock_root=tmp_path / "locks", red_team_prompt=prompt
        )
    assert calls == {"posts": 0, "statuses": 0}


@pytest.mark.parametrize("status", ["spawning", "running", "queued", "done"])
@pytest.mark.parametrize("head,mode", [(SHA, "cross_family"), (OTHER, "cross_family"), (SHA, "red_team")])
def test_red_team_outside_review_in_flight_publication_guard(monkeypatch, tmp_path, status, head, mode):
    tasks, comments, calls = setup_record(monkeypatch, tmp_path)
    prompt = red_team_task(tasks, tmp_path)
    write_task(
        tasks,
        task_id="outside-review",
        review=True,
        agent="claude",
        model="claude-opus-5-5",
        status=status,
        worktree_base_sha=head,
        review_mode=mode,
        started_at="2026-09-23T11:00:00.000001+00:00",
    )
    kwargs = dict(pr_number=42, task_root=tasks, lock_root=tmp_path / "locks", red_team_prompt=prompt)
    if status != "done" and head == SHA and mode == "cross_family":
        with pytest.raises(
            recorder.RecordError, match="RED_TEAM_REFUSED: outside-family review in flight for this head"
        ):
            recorder.record("review-one", **kwargs)
        assert comments == [] and calls == {"posts": 0, "statuses": 0}
    else:
        assert recorder.record("review-one", **kwargs)["status"] == "posted"
        assert calls == {"posts": 1, "statuses": 1}


@pytest.mark.parametrize("repository", ["OWNER/REPO", "owner/repo", "other/repo"])
@pytest.mark.parametrize(
    "head_field", ["pinned_head", "worktree_base_sha", "review_head", "review_head_sha", "pr_head_sha", "head_sha"]
)
def test_red_team_pr_only_review_head_fields_and_repository_match(monkeypatch, tmp_path, repository, head_field):
    tasks, comments, calls = setup_record(monkeypatch, tmp_path)
    prompt = red_team_task(tasks, tmp_path)
    updates = {"worktree_base_sha": None, head_field: SHA}
    write_task(tasks, task_id="outside-review", repository=repository, pr=42, status="running", **updates)
    kwargs = dict(pr_number=42, task_root=tasks, lock_root=tmp_path / "locks", red_team_prompt=prompt)
    if repository != "other/repo":
        with pytest.raises(
            recorder.RecordError, match="RED_TEAM_REFUSED: outside-family review in flight for this head"
        ):
            recorder.record("review-one", **kwargs)
        assert comments == [] and calls == {"posts": 0, "statuses": 0}
    else:
        assert recorder.record("review-one", **kwargs)["status"] == "posted"
        assert calls == {"posts": 1, "statuses": 1}


@pytest.mark.parametrize("status", ["spawning", "running", "queued", "done", "needs_finalize"])
@pytest.mark.parametrize("repository_fields", [{}, {"repository": None}])
@pytest.mark.parametrize(
    "head,mode", [(SHA, "cross_family"), (SHA.upper(), "cross_family"), (OTHER, "cross_family"), (SHA, "red_team")]
)
def test_red_team_worktree_prep_publication_guard(monkeypatch, tmp_path, status, repository_fields, head, mode):
    tasks, comments, calls = setup_record(monkeypatch, tmp_path)
    prompt = red_team_task(tasks, tmp_path)
    # The provisional row has no repository identity, review flag or top-level head.
    (tasks / "outside-review.json").write_text(
        json.dumps(
            {
                "task_id": "outside-review",
                "status": status,
                "review_mode": mode,
                "worktree_prep": {"base_sha": head},
                **repository_fields,
            }
        )
    )
    before = {path.name: path.read_bytes() for path in tasks.iterdir()}
    kwargs = dict(pr_number=42, task_root=tasks, lock_root=tmp_path / "locks", red_team_prompt=prompt)
    if status in {"spawning", "running", "queued"} and head.lower() == SHA and mode == "cross_family":
        with pytest.raises(
            recorder.RecordError, match="RED_TEAM_REFUSED: outside-family review in flight for this head"
        ):
            recorder.record("review-one", **kwargs)
        assert comments == [] and calls == {"posts": 0, "statuses": 0}
        assert {path.name: path.read_bytes() for path in tasks.iterdir()} == before
    else:
        assert recorder.record("review-one", **kwargs)["status"] == "posted"
        assert calls == {"posts": 1, "statuses": 1}


@pytest.mark.parametrize(
    "broken", ["missing", "invalid-json", "non-object", "read-error", "invalid-head", "glob-error"]
)
def test_red_team_unreadable_task_ledger_refuses_publication(monkeypatch, tmp_path, broken):
    tasks, comments, calls = setup_record(monkeypatch, tmp_path)
    prompt = red_team_task(tasks, tmp_path)
    if broken == "missing":
        original = Path.iterdir

        def unreadable(path):
            if path == tasks:
                raise FileNotFoundError("ledger missing")
            return original(path)

        monkeypatch.setattr(Path, "iterdir", unreadable)
    elif broken == "glob-error":
        original = Path.glob

        def unreadable(path, *args, **kwargs):
            if path == tasks:
                assert list(path.iterdir())  # The directory is readable; glob still fails.
                raise OSError("ledger glob failed")
            return original(path, *args, **kwargs)

        monkeypatch.setattr(Path, "glob", unreadable)
    elif broken == "invalid-head":
        write_task(tasks, task_id="broken", pr=42, status="running", pinned_head=[], worktree_base_sha=None)
    else:
        (tasks / "broken.json").write_text("{" if broken == "invalid-json" else "[]")
        if broken == "read-error":
            original = Path.read_text

            def unreadable(path, *args, **kwargs):
                if path.name == "broken.json":
                    raise OSError("ledger unreadable")
                return original(path, *args, **kwargs)

            monkeypatch.setattr(Path, "read_text", unreadable)
    with pytest.raises(recorder.RecordError, match="RED_TEAM_REFUSED: task ledger unavailable"):
        recorder.record(
            "review-one", pr_number=42, task_root=tasks, lock_root=tmp_path / "locks", red_team_prompt=prompt
        )
    assert comments == [] and calls == {"posts": 0, "statuses": 0}


@pytest.mark.parametrize("kind", ["implementation", "other-repository"])
def test_red_team_in_flight_unrelated_tasks_do_not_refuse(monkeypatch, tmp_path, kind):
    tasks, comments, calls = setup_record(monkeypatch, tmp_path)
    prompt = red_team_task(tasks, tmp_path)
    write_task(
        tasks,
        task_id="unrelated",
        status="running",
        review=kind != "implementation",
        repository=REPOSITORY if kind == "implementation" else "other/repo",
    )
    assert (
        recorder.record(
            "review-one", pr_number=42, task_root=tasks, lock_root=tmp_path / "locks", red_team_prompt=prompt
        )["status"]
        == "posted"
    )
    assert len(comments) == 1 and calls == {"posts": 1, "statuses": 1}


@pytest.mark.parametrize("archived", [False, True])
@pytest.mark.parametrize("explicit", [None, "gpt-6-luna", "gpt-6.1-sol"])
def test_red_team_unknown_history_and_validated_current_author(monkeypatch, tmp_path, archived, explicit):
    from dataclasses import replace

    tasks, comments, calls = setup_record(monkeypatch, tmp_path)
    records = tasks / "archive" if archived else tasks
    write_task(records, task_id="current-author", model="gpt-6-luna")
    current = recorder._attribute_commit(
        {"sha": SHA, "commit": {"message": "change\n\nX-Agent: codex/current-author"}},
        repository=REPOSITORY,
        task_root=tasks,
        base_sha=lambda: OTHER,
    )
    history = recorder.CommitAttribution(OTHER, "unknown", "unresolved-author")
    facts = replace(facts_for({"unknown", "openai"}), commits=(history, current))
    monkeypatch.setattr(recorder, "pr_review_facts", lambda *_a, **_k: facts)
    prompt = red_team_task(tasks, tmp_path, review_author_model=explicit)
    kwargs = dict(pr_number=42, task_root=tasks, lock_root=tmp_path / "locks", red_team_prompt=prompt)
    # A conflict with validated evidence is refused first; otherwise the unresolved commit is refused in a
    # red team too, since --review-author-model cannot name a model for it (C-2902 F9).
    reason = "RED_TEAM_REFUSED: conflicting author identity" if explicit == "gpt-6.1-sol" else "AUTHOR_UNRESOLVED"
    with pytest.raises(recorder.RecordError, match=reason):
        recorder.record("review-one", **kwargs)
    assert facts.commits[0].family == "unknown"
    assert comments == [] and calls == {"posts": 0, "statuses": 0}


@pytest.mark.parametrize("case", ["missing", "unreadable", "ordinary", "digest_mismatch", "unbound", "mode_conflict"])
def test_red_team_prompt_required_and_bound_before_publication(monkeypatch, tmp_path, case):
    tasks, comments, calls = setup_record(monkeypatch, tmp_path, families={"openai"})
    prompt = red_team_task(tasks, tmp_path)
    options = {"red_team_prompt": prompt}
    if case == "missing":
        options = {}
    elif case == "unreadable":
        options["red_team_prompt"] = tmp_path / "missing.md"
    elif case == "ordinary":
        prompt = red_team_task(tasks, tmp_path, prompt="Review the patch.")
    elif case == "digest_mismatch":
        prompt.write_text("A different red-team prompt.")
    elif case == "unbound":
        write_task(tasks, review_mode="red_team")
    else:
        options["review_mode"] = "cross_family"
    with pytest.raises(recorder.RecordError, match=r"prompt|mode conflicts"):
        recorder.record("review-one", pr_number=42, task_root=tasks, lock_root=tmp_path / "locks", **options)
    assert comments == []
    assert calls == {"posts": 0, "statuses": 0}


def test_explicit_red_team_flag_accepts_task_with_bound_mode_and_prompt(monkeypatch, tmp_path):
    tasks, comments, _ = setup_record(monkeypatch, tmp_path, families={"openai"})
    prompt = red_team_task(tasks, tmp_path)
    write_task(tasks, review_mode="red_team", prompt_sha256=hashlib.sha256(prompt.read_bytes()).hexdigest())
    recorder.record(
        "review-one",
        pr_number=42,
        task_root=tasks,
        lock_root=tmp_path / "locks",
        review_mode="red_team",
        red_team_prompt=prompt,
    )
    assert "review_mode=red_team" in comments[0]["body"]


def test_red_team_effective_prompt_digest_is_supported(monkeypatch, tmp_path):
    tasks, comments, _ = setup_record(monkeypatch, tmp_path, families={"openai"})
    prompt = red_team_task(tasks, tmp_path)
    write_task(
        tasks,
        review_mode="red_team",
        prompt_sha256="b" * 64,
        effective_prompt_sha256=hashlib.sha256(prompt.read_bytes()).hexdigest(),
    )
    recorder.record("review-one", pr_number=42, task_root=tasks, lock_root=tmp_path / "locks", red_team_prompt=prompt)
    assert "review_mode=red_team" in comments[0]["body"]


@pytest.mark.parametrize("mode", ["anything", None, {}, []])
def test_invalid_task_review_mode_refuses_before_publication(monkeypatch, tmp_path, mode):
    tasks, comments, calls = setup_record(monkeypatch, tmp_path)
    write_task(tasks, review_mode=mode)
    with pytest.raises(recorder.RecordError, match="unsupported review mode"):
        recorder.record("review-one", pr_number=42, task_root=tasks, lock_root=tmp_path / "locks")
    assert comments == []
    assert calls == {"posts": 0, "statuses": 0}


def test_red_team_prompt_does_not_implicitly_enable_mode(monkeypatch, tmp_path):
    tasks, comments, _ = setup_record(monkeypatch, tmp_path)
    prompt = tmp_path / "red-team.md"
    prompt.write_text("Adversarial red-team review.")
    with pytest.raises(recorder.RecordError, match="requires review_mode=red_team"):
        recorder.record(
            "review-one", pr_number=42, task_root=tasks, lock_root=tmp_path / "locks", red_team_prompt=prompt
        )
    assert comments == []


@pytest.mark.parametrize("model", ["unknown@local.invalid", "LU Unknown", "auto"])
def test_unknown_red_team_reviewer_cannot_self_certify(monkeypatch, tmp_path, model):
    # A resolved author: an unknown one is refused before the reviewer is judged (C-2902 F9).
    tasks, comments, calls = setup_record(monkeypatch, tmp_path, families={"openai"})
    prompt = red_team_task(tasks, tmp_path, model=model)
    with pytest.raises(recorder.RecordError, match=r"reviewer (model|family) unknown|reviewer not qualified"):
        recorder.record(
            "review-one", pr_number=42, task_root=tasks, lock_root=tmp_path / "locks", red_team_prompt=prompt
        )
    assert comments == []
    assert calls == {"posts": 0, "statuses": 0}


@pytest.mark.parametrize("scope", ["subject", "risk"])
def test_red_team_keeps_qualification_gates(monkeypatch, tmp_path, scope):
    tasks, comments, _ = setup_record(monkeypatch, tmp_path)
    if scope == "subject":
        monkeypatch.setattr(recorder, "pr_review_facts", lambda *a, **k: facts_for({"openai"}, subject_seats={"codex"}))
        updates = {}
    else:
        monkeypatch.setattr(recorder, "pr_review_facts", lambda *a, **k: facts_for({"anthropic"}))
        updates = {"agent": "claude", "model": "claude-sonnet-5-5", "review_risk": "critical"}
    prompt = red_team_task(tasks, tmp_path, **updates)
    with pytest.raises(recorder.RecordError, match="not qualified"):
        recorder.record(
            "review-one", pr_number=42, task_root=tasks, lock_root=tmp_path / "locks", red_team_prompt=prompt
        )
    assert comments == []


def test_rerecording_same_task_in_another_mode_refuses(monkeypatch, tmp_path):
    tasks, comments, calls = setup_record(monkeypatch, tmp_path)
    recorder.record("review-one", pr_number=42, task_root=tasks, lock_root=tmp_path / "locks")
    prompt = red_team_task(tasks, tmp_path)
    with pytest.raises(recorder.RecordError, match="edited or conflicts"):
        recorder.record(
            "review-one", pr_number=42, task_root=tasks, lock_root=tmp_path / "locks", red_team_prompt=prompt
        )
    assert len(comments) == 1
    assert calls == {"posts": 1, "statuses": 1}


def test_rerun_same_task_reconciles_status_without_new_comment(monkeypatch, tmp_path):
    tasks, comments, calls = setup_record(monkeypatch, tmp_path)
    first = recorder.record("review-one", pr_number=42, task_root=tasks, lock_root=tmp_path / "locks")
    second = recorder.record("review-one", pr_number=42, task_root=tasks, lock_root=tmp_path / "locks")
    assert first["comment"] == "posted"
    assert second["comment"] == "existing"
    assert first["review_mode"] == second["review_mode"] == "cross_family"
    assert calls == {"posts": 1, "statuses": 2}
    assert len(comments) == 1
    assert comments[0]["body"].splitlines()[-1].startswith("<!-- cf-verdict v1 sha=")


def test_status_failure_keeps_comment_and_reports_partial(monkeypatch, tmp_path):
    tasks, comments, _ = setup_record(monkeypatch, tmp_path, status_error=True)
    result = recorder.record("review-one", pr_number=42, task_root=tasks, lock_root=tmp_path / "locks")
    assert result["comment"] == "posted"
    assert result["status"].startswith("failed:")
    assert len(comments) == 1


def test_flagged_comment_withholds_prose_despite_override(monkeypatch, tmp_path, synthetic_opsec):
    """Both publications pass the gate without granting the recorder an override."""
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
    assert len(sent) == 2 and TOKEN not in comments[0]["body"]
    assert "Withheld findings: unknown\nFindings are held privately." in comments[0]["body"]
    assert not (tmp_path / "batch_state/opsec/overrides.jsonl").exists()


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


def test_mixed_and_unknown_author_families_are_retained(monkeypatch, tmp_path):
    tasks = tmp_path / "tasks"
    tasks.mkdir()

    def commit(trailer):
        return {"commit": {"message": f"work\n\nX-Agent: {trailer}"}}

    write_task(tasks, task_id="author-one", model="gpt-6.1-sol")
    write_task(tasks / "archive", task_id="author-two", model="gemini-3.8-flash-high", agent="agy")
    monkeypatch.setattr(
        recorder,
        "_pages",
        lambda args: [commit("codex/author-one\nX-Agent: agy/author-two"), commit("agy/gemini-3.8-flash-high")],
    )
    assert recorder.author_families(REPOSITORY, 42, tasks) == {"openai", "google"}
    monkeypatch.setattr(recorder, "_pages", lambda args: [commit("cursor/task-without-record")])
    assert recorder.author_families(REPOSITORY, 42, tasks) == {"unknown"}


@pytest.mark.parametrize("trailer", ["", "X-Agent: acp/unknown", "X-Agent: cursor/unknown"])
def test_unknown_git_identity_cannot_self_certify_author(monkeypatch, tmp_path, trailer):
    unknown = {"name": "LU Unknown", "email": "unknown@local.invalid"}
    entry = {"commit": {"message": f"work\n\n{trailer}", "author": unknown, "committer": unknown}}
    monkeypatch.setattr(recorder, "_pages", lambda args: [entry])
    if trailer:
        assert recorder.author_families(REPOSITORY, 42, tmp_path) == {"unknown"}
    else:
        with pytest.raises(recorder.RecordError, match="missing explicit X-Agent"):
            recorder.author_families(REPOSITORY, 42, tmp_path)
    assert recorder.resolve_family(unknown["name"]) == "unknown"
    assert recorder.resolve_author_family(unknown["email"]) == "unknown"


@pytest.mark.parametrize("model", ["LU Unknown", "unknown@local.invalid"])
def test_unknown_identity_cannot_be_a_formal_reviewer(monkeypatch, tmp_path, model):
    tasks, comments, calls = setup_record(monkeypatch, tmp_path)
    write_task(tasks, model=model)
    with pytest.raises(recorder.RecordError, match=r"reviewer (model|family) unknown"):
        recorder.record("review-one", pr_number=42, task_root=tasks, lock_root=tmp_path / "locks")
    assert comments == []
    assert calls == {"posts": 0, "statuses": 0}


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
        # Origin serves ``base`` as its default branch: every branch review is attributed from it.
        remote = tmp_path / "origin.git"
        git("init", "-q", "--bare", str(remote))
        git("--git-dir", str(remote), "symbolic-ref", "HEAD", "refs/heads/base")
        git("remote", "add", "origin", str(remote))
        git("push", "-q", "origin", f"{base}:refs/heads/base")

        def base_lookup(args, **kwargs):
            assert args == ["gh", "pr", "view", "42", "--repo", REPOSITORY, "--json", "baseRefOid"]
            return {"baseRefOid": base}

        monkeypatch.setattr(recorder, "_run_json", base_lookup)
        return git, commits, head, base

    return build


@pytest.mark.parametrize(
    "case,families",
    [
        ("all_trailered", {"openai"}),
        ("clean_update_merge", {"openai"}),
        ("conflict_resolution", None),
        # A clean merge of two commits of the PR's own range authors nothing.
        ("nonbase_merge", {"openai", "google"}),
        ("ordinary_untrailered", None),
        ("dirty_merge", None),
        ("reversed_parents", {"openai"}),
        ("octopus_merge", None),
        ("older_base_merge", {"openai"}),
    ],
)
def test_author_commit_sets_with_real_git(real_commit_set, tmp_path, case, families):
    real_commit_set(case)
    if families is not None:
        assert recorder.author_families(REPOSITORY, 42, tmp_path) == families
    else:
        with pytest.raises(recorder.RecordError, match="missing explicit X-Agent"):
            recorder.author_families(REPOSITORY, 42, tmp_path)


@pytest.mark.parametrize(
    "case,families",
    [
        ("clean", {"openai", "anthropic"}),
        ("hand_edit", None),
        ("parent_outside_range", None),
    ],
)
def test_sync_merge_of_range_commits_needs_no_attribution(real_commit_set, monkeypatch, tmp_path, case, families):
    git, _, head, base = real_commit_set("all_trailered")

    def round_commit(branch, path, trailer):
        git("checkout", "-b", branch, head)
        Path(path).write_text(f"{branch}\n")
        git("add", path)
        git("commit", "-m", f"{branch}\n\nX-Agent: {trailer}")
        return git("rev-parse", "HEAD").stdout.strip()

    outside = round_commit("round-a", "a.txt", "claude/claude-opus-5-5")
    round_commit("round-b", "b.txt", "codex/gpt-6.1-sol")
    git("merge", "--no-ff", "--no-commit", "round-a")
    if case == "hand_edit":
        Path("extra.txt").write_text("authored during the merge\n")
        git("add", "extra.txt")
    git("commit", "-m", "sync PR branch")
    listing = [
        {
            "sha": sha,
            "commit": {
                "message": git("show", "--no-patch", "--format=%B", sha).stdout,
                "tree": {"sha": git("show", "--no-patch", "--format=%T", sha).stdout.strip()},
            },
            "parents": [{"sha": parent} for parent in git("show", "--no-patch", "--format=%P", sha).stdout.split()],
        }
        for sha in git("rev-list", "--reverse", f"{base}..HEAD").stdout.splitlines()
    ]
    if case == "parent_outside_range":
        listing = [entry for entry in listing if entry["sha"] != outside]
    monkeypatch.setattr(recorder, "_pages", lambda args: listing)
    if families is not None:
        assert recorder.author_families(REPOSITORY, 42, tmp_path) == families
    else:
        with pytest.raises(recorder.RecordError, match="missing explicit X-Agent"):
            recorder.author_families(REPOSITORY, 42, tmp_path)


def test_clean_update_merge_records_exact_head_review(real_commit_set, monkeypatch, tmp_path):
    _, _, head, _ = real_commit_set("clean_update_merge")
    pr_review_facts = recorder.pr_review_facts
    tasks, comments, calls = setup_record(monkeypatch, tmp_path, head=head)
    write_task(tasks, worktree_base_sha=head, model="claude-opus-5-5", agent="claude")
    monkeypatch.setattr(recorder, "pr_review_facts", pr_review_facts)
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


@pytest.mark.parametrize("trailer", ["X-Agent:", "X-Agent: codex/unknown model"])
def test_clean_merge_bad_attribution_is_not_exempted(real_commit_set, tmp_path, trailer):
    _, commits, _, _ = real_commit_set("clean_update_merge")
    commits[-1]["commit"]["message"] += f"\n{trailer}\n"
    with pytest.raises(recorder.RecordError):
        recorder.author_families(REPOSITORY, 42, tmp_path)


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
def test_merge_proof_missing_checkout_refuses(monkeypatch, marker):
    # The autouse scratch override follows basetemp, which can live inside Git.
    # This context owns its isolation and needs the fleet root outside the checkout.
    monkeypatch.delenv("LU_SCRATCH_ROOT", raising=False)
    with TemporaryDirectory(prefix="verdict-missing-checkout-", dir=ensure_scratch_root()) as isolated:
        checkout = Path(isolated)
        # The pre-push basetemp has a repository ancestor. Prove absence independently.
        probe = subprocess.run(
            ["git", "rev-parse", "--git-common-dir"],
            cwd=checkout,
            env=sanitized_git_env(),
            capture_output=True,
            text=True,
            check=False,
            timeout=10,
        )
        assert probe.returncode == 128 and "not a git repository" in probe.stderr
        monkeypatch.chdir(checkout)
        if marker is not None:
            (checkout / ".git").write_text(marker)
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
    if target == "merge":
        with pytest.raises(recorder.RecordError, match="missing explicit X-Agent"):
            recorder.author_families(REPOSITORY, 42, tmp_path)
    else:
        # Base ancestry stays unproven; the merge is exempt only as a sync merge of range commits.
        assert recorder.author_families(REPOSITORY, 42, tmp_path) == {"openai", "google"}


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
    assert recorder.author_families(REPOSITORY, 42, tmp_path) == {"openai", "google"}


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
        # A task id without a task record is unresolved on a single-family harness too (C-2902 F5).
        ("kimi/k2", {"unknown"}),
        ("codex/gpt-6-luna", {"openai"}),
        ("cursor/grok-4.7", {"xai"}),
    ],
)
def test_author_family_resolves_model_with_harness_fallback(monkeypatch, tmp_path, trailer, expected):
    def commit(value):
        return {"commit": {"message": f"work\n\nX-Agent: {value}"}}

    monkeypatch.setattr(recorder, "_pages", lambda args: [commit(trailer)])
    assert recorder.author_families(REPOSITORY, 42, tmp_path) == expected


def test_unknown_harness_model_is_retained(monkeypatch, tmp_path):
    monkeypatch.setattr(
        recorder,
        "_pages",
        lambda args: [{"commit": {"message": "work\n\nX-Agent: unknownharness/x"}}],
    )
    assert recorder.author_families(REPOSITORY, 42, tmp_path) == {"unknown"}


@pytest.mark.parametrize(
    "selector",
    [
        "auto",
        "AUTO",
        "Auto",
        " auto ",
        "default",
        "DEFAULT",
        "Default",
        " default ",
        "cursor:auto",
        "CURSOR:AUTO",
        "Cursor:Auto",
        " cursor:auto ",
        "cursor/auto",
        "CURSOR/AUTO",
        "Cursor/Auto",
        " cursor/auto ",
        "cursor:default",
        "CURSOR:DEFAULT",
        "Cursor:Default",
        " cursor:default ",
        "cursor/default",
        "CURSOR/DEFAULT",
        "Cursor/Default",
        " cursor/default ",
    ],
)
def test_committed_cursor_auto_family_is_cursor(monkeypatch, tmp_path, selector):
    monkeypatch.setattr(
        recorder,
        "_pages",
        lambda args: [{"commit": {"message": f"work\n\nX-Agent: cursor/{selector.strip()}"}}],
    )
    assert recorder.author_families(REPOSITORY, 42, tmp_path) == {"cursor"}


def test_author_task_record_resolves_task_id_trailer(monkeypatch, tmp_path):
    tasks = tmp_path / "tasks"
    write_task(tasks, task_id="author-task", model="gpt-6.1-sol", agent="agy")
    monkeypatch.setattr(
        recorder,
        "_pages",
        lambda args: [{"commit": {"message": "feat: work\n\nX-Agent: agy/author-task"}}],
    )
    assert recorder.author_families(REPOSITORY, 42, tasks) == {"openai"}


@pytest.mark.parametrize(
    "harness,model,has_record,expected",
    [
        ("codex", "impl-8512-claude-exclude", True, "openai"),  # AC-02
        ("claude", "claude-opus-5-5", False, "anthropic"),  # AC-03
        ("codex", "gpt-6.1-sol", False, "openai"),  # AC-03
        ("codex", "impl-8512-claude-exclude", False, "unknown"),  # AC-04
        ("claude", "grok-4.7-adapter-fix", False, "unknown"),
        ("claude-infra", "glm-adapter-review", False, "unknown"),
        ("codex", "gpt-6.1-sol-claude-port", False, "unknown"),
        ("codex", "gpt-6.1-sol-high-adapter-fix", False, "unknown"),
        ("claude-infra", "glm", False, "zhipu"),
        ("claude", "grok-4.7-adapter-fix", True, "openai"),
        ("claude-infra", "glm-adapter-review", True, "openai"),
        ("codex", "gpt-6.1-sol-claude-port", True, "openai"),
    ],
)
def test_author_task_record_precedes_family_tokens(monkeypatch, tmp_path, harness, model, has_record, expected):
    tasks = tmp_path / "tasks"
    if has_record:
        write_task(tasks, task_id=model, model="gpt-6.1-sol", agent=harness)
    monkeypatch.setattr(
        recorder,
        "_pages",
        lambda args: [{"commit": {"message": f"feat: work\n\nX-Agent: {harness}/{model}"}}],
    )
    assert recorder.author_families(REPOSITORY, 42, tasks) == {expected}


@pytest.mark.parametrize("effort", ["", "-low", "-medium", "-high", "-xhigh", "-max"])
@pytest.mark.parametrize("context", ["", "[1m]"])
@pytest.mark.parametrize(
    "harness,model,expected",
    [
        ("codex", "gpt-6.1-sol", "openai"),
        ("claude", "claude-opus-5-5", "anthropic"),
        ("claude-infra", "glm", "zhipu"),
        ("codex", "openai/gpt-6.1-sol", "openai"),
    ],
)
def test_model_trailer_preserves_effort_and_context_forms(
    monkeypatch, tmp_path, harness, model, expected, effort, context
):
    monkeypatch.setattr(
        recorder,
        "_pages",
        lambda args: [{"commit": {"message": f"work\n\nX-Agent: {harness}/{model}{effort}{context}"}}],
    )
    assert recorder.author_families(REPOSITORY, 42, tmp_path) == {expected}


def test_archived_review_task_and_reply_are_loadable(tmp_path, monkeypatch):
    """#8625: a review archived before its verdict was recorded can still be published."""
    from scripts.review import record

    tasks = tmp_path / "tasks"
    write_task(tasks / "archive", task_id="review-old", reply="VERDICT: APPROVE")
    loaded, reply = recorder._task("review-old", tasks)
    assert (loaded["status"], reply) == ("done", "VERDICT: APPROVE")
    # The hot record wins when both exist.
    write_task(tasks, task_id="review-old", reply="VERDICT: REQUEST_CHANGES")
    assert recorder._task("review-old", tasks)[1] == "VERDICT: REQUEST_CHANGES"

    # Attempt records retain the original result path after both files move.
    task_id = "review-attempt"
    hot = tasks / f"{task_id}.json"
    cold = tasks / "archive" / hot.name
    binding = {"review_id": "review-one", "attempt_id": "attempt-one", "manifest_sha256": "a" * 64}
    prompt_hash = "b" * 64
    identity = {"agent": "claude", "model": "claude-opus-5-5"}
    monkeypatch.setattr(record, "_render_prompt_sha256", lambda *args: (prompt_hash, ""))
    for digest in (prompt_hash, "<prompt_sha256>"):
        data = f'reviewer:\n  prompt_sha256: "{digest}"\n'.encode()
        task = {
            **identity,
            "task_id": task_id,
            "status": "done",
            "review_attempt": binding,
            "prompt_sha256": prompt_hash,
            "result_file": str(hot.with_suffix(".result")),
            "result_sha256": hashlib.sha256(data).hexdigest(),
        }
        hot.write_text(json.dumps(task))
        hot.with_suffix(".result").write_bytes(data)
        for path in (hot, cold):
            if path == cold:
                hot.replace(cold)
                hot.with_suffix(".result").replace(cold.with_suffix(".result"))
            assert record._read_dispatch_record(task_id, tasks) == (task, path)
            assert record.resolve_reviewer_identity(task_id, tasks) == {
                "model": "claude-opus-5-5",
                "harness": "claude",
                "family": "anthropic",
            }
            assert record.dispatch_prompt_sha256(task_id, tasks, **binding) == prompt_hash
            expected = f'reviewer:\n  prompt_sha256: "{prompt_hash}"\n'.encode()
            assert (
                record.attested_return(
                    data,
                    task_id=task_id,
                    tasks_dir=tasks,
                    manifest_path=tmp_path / "manifest",
                    root=tmp_path,
                    **binding,
                )
                == expected
            )
            for changed in (
                {"status": "running"},
                {"result_sha256": "c" * 64},
                {"result_file": str(tmp_path / "unrelated.result")},
                {"review_attempt": {**binding, "attempt_id": "superseded"}},
            ):
                path.write_text(json.dumps({**task, **changed}))
                with pytest.raises(record.RecordError, match=record.REVIEW_RETURN_TASK_MISMATCH):
                    record._verify_task_return(data, task_id, tasks, **binding)
            path.write_text(json.dumps(task))
            path.with_suffix(".result").write_bytes(b"different bytes")
            with pytest.raises(record.RecordError, match=record.REVIEW_RETURN_TASK_MISMATCH):
                record._verify_task_return(data, task_id, tasks, **binding)
            path.with_suffix(".result").write_bytes(data)

    # Malformed or superseded hot records never fall through to a valid archive.
    hot.write_text("[]")
    with pytest.raises(record.RecordError, match=str(hot)):
        record.resolve_reviewer_identity(task_id, tasks)
    assert record.dispatch_prompt_sha256(task_id, tasks, **binding) is None
    hot.write_text(json.dumps({**task, "review_attempt": {**binding, "attempt_id": "superseded"}}))
    assert record._read_dispatch_record(task_id, tasks)[1] == hot
    assert record.dispatch_prompt_sha256(task_id, tasks, **binding) is None
    with pytest.raises(record.RecordError, match=record.REVIEW_RETURN_TASK_MISMATCH):
        record._verify_task_return(data, task_id, tasks, **binding)
    hot.unlink()
    cold.write_text("[]")
    with pytest.raises(record.RecordError, match=str(cold)):
        record.resolve_reviewer_identity(task_id, tasks)
    cold.write_text(json.dumps({**task, "model": "unlisted-model"}))
    with pytest.raises(record.RecordError):
        record.resolve_reviewer_identity(task_id, tasks)
    cold.unlink()
    with pytest.raises(record.RecordError, match="unreadable"):
        record.resolve_reviewer_identity(task_id, tasks)
    assert record.dispatch_prompt_sha256(task_id, tasks, **binding) is None
    with pytest.raises(record.RecordError, match=record.REVIEW_RETURN_TASK_MISMATCH):
        record._verify_task_return(data, task_id, tasks, **binding)


@pytest.mark.parametrize("storage", ["missing", "hot", "archived"])
def test_model_named_author_task_retains_validated_record_ids(tmp_path, storage):
    tasks = tmp_path / "tasks"
    if storage != "missing":
        write_task(
            tasks / "archive" if storage == "archived" else tasks,
            task_id="gpt-6.1-sol",
            model="gpt-6.1-sol",
            agent="codex",
        )
        path = (tasks / "archive" if storage == "archived" else tasks) / "gpt-6.1-sol.json"
        data = json.loads(path.read_text())
        data["task_id"] = " CODEX/Original Author! "
        path.write_text(json.dumps(data))
    attribution = recorder._attribute_commit(
        {"sha": SHA, "commit": {"message": "work\n\nX-Agent: codex/gpt-6.1-sol"}},
        repository=REPOSITORY,
        task_root=tasks,
        base_sha=lambda: OTHER,
    )
    if storage == "missing":
        assert attribution.task_id is None and attribution.record_task_id is None
    else:
        assert attribution.task_id == "gpt-6.1-sol"
        assert attribution.record_task_id == "original-author"


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


@pytest.mark.parametrize("harness", ["codex", "agy", "claude", "cursor"])
def test_missing_task_record_retains_unknown_for_multifamily_harnesses(monkeypatch, tmp_path, harness):
    monkeypatch.setattr(
        recorder,
        "_pages",
        lambda args: [{"commit": {"message": f"feat: work\n\nX-Agent: {harness}/impl-missing-task"}}],
    )
    assert recorder.author_families(REPOSITORY, 42, tmp_path) == {"unknown"}


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
    monkeypatch.setattr(recorder, "_repo_root", lambda: tmp_path)
    monkeypatch.setattr(recorder, "resolve_review_repository", lambda _root, _key, **_kwargs: root)

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
        receipt = recorder.record("review-one", pr_number=42, task_root=tasks, lock_root=tmp_path / "locks")
        assert receipt["comment"] == "posted" and receipt["status"] == "posted"
        body = comments[0]["body"]
        assert "Withheld findings: unknown\nFindings are held privately." in body
        assert reply not in body and "<details>" not in body
        assert "/outside" not in body and str(root) not in body and "SENTINEL-HOST-TOKEN" not in body
        assert recorder.parse_marker(body)["sha"] == SHA
        assert calls == {"posts": 1, "statuses": 1}
        record = recorder.record
        monkeypatch.setattr(
            recorder,
            "record",
            lambda task_id, **kwargs: record(task_id, task_root=tasks, lock_root=tmp_path / "locks", **kwargs),
        )
        assert recorder.main(["--task-id", "review-one", "--pr", "42"]) == 0
        output = capsys.readouterr()
        assert json.loads(output.out)["comment"] == "existing"
        assert "/checkout" not in output.out + output.err
        assert "/outside" not in output.out + output.err and "SENTINEL-HOST-TOKEN" not in output.out + output.err
        assert calls == {"posts": 1, "statuses": 2}
    else:
        receipt = recorder.record("review-one", pr_number=42, task_root=tasks, lock_root=tmp_path / "locks")
        assert receipt["comment"] == "posted" and receipt["status"] == "posted"
        assert calls == {"posts": 1, "statuses": 1}
        body = comments[0]["body"]
        assert "/checkout" not in body
        if "unit.py" in reply:
            assert "`scripts/unit.py:12`" in body and "```\ntests/test_unit.py:3\n```" in body


def test_comment_truncation_retains_marker():
    reply = ("é`<!-- cf-verdict` " * 5_000) + "尾"
    body = recorder.build_comment(
        sha=SHA,
        task_id="review-one",
        started="2026-09-23T12:00:00.000001+00:00",
        verdict="APPROVED",
        model="gpt-6.1-sol",
        family="openai",
        reply=reply,
    )
    assert len(body.encode()) <= recorder.MAX_COMMENT_BYTES
    assert "[Review reply truncated" in body
    assert body.encode().decode("utf-8") == body
    assert "é`&lt;!-- cf-verdict` " in body
    assert body.count(recorder.MARKER_PREFIX) == 1
    assert body.splitlines()[-1].startswith(recorder.MARKER_PREFIX)
    assert recorder.MARKER_PREFIX not in body.split("</details>", 1)[0]
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
        ({"resolved_model": "auto", "resolved_model_known": True}, "reviewer model unknown"),
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


@pytest.mark.parametrize(
    "citation", ["missing.py", "missing.py:12", "scripts:12", "scripts/unit.py:0", "scripts/unit.py:12:x"]
)
def test_ambiguous_or_nonexistent_citation_refuses(citation_checkout, real_recorder_matcher, citation):
    root, _ = citation_checkout
    reply = f"VERDICT: APPROVE\n`{root}/{citation}`"
    rewritten = recorder.repository_relative_reply(reply, task={}, primary_root=root)
    assert rewritten == reply
    assert_rendered_path_refusal(reply, rewritten, real_recorder_matcher)


def test_matcher_refusal_prevents_record_transport(monkeypatch, tmp_path, synthetic_opsec):
    tasks, _, calls = setup_record(monkeypatch, tmp_path)
    (synthetic_opsec / "rules.json").write_text("invalid")
    with pytest.raises(recorder.RecordError, match="publish_blocked"):
        recorder.record("review-one", pr_number=42, task_root=tasks, lock_root=tmp_path / "locks")
    assert calls == {"posts": 0, "statuses": 0}


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


# --- #9739 A1: GitHub's listing must equal the local base..head enumeration ----------------------


@pytest.mark.parametrize("case", ["all_trailered", "clean_update_merge"])
def test_pr_review_facts_bind_the_github_listing_to_rev_list(real_commit_set, monkeypatch, tmp_path, case):
    _, commits, head, base = real_commit_set(case)
    monkeypatch.setattr(
        recorder, "_run_json", lambda args, **kwargs: {"baseRefName": "base", "baseRefOid": base, "headRefOid": head}
    )

    facts = recorder.pr_review_facts(REPOSITORY, 42, head_sha=head, task_root=tmp_path, repo_root=Path.cwd())
    assert facts.existing_families == {"openai"}
    assert sorted(commit.sha for commit in facts.commits) == sorted(entry["sha"] for entry in commits)

    differing = [[*commits, {**commits[0], "sha": "c" * 40}], *([commits[:-1]] if len(commits) > 1 else [])]
    for listing in differing:
        monkeypatch.setattr(recorder, "_pages", lambda args, listing=listing: listing)
        with pytest.raises(recorder.RecordError, match=r"differs from the local base\.\.head enumeration"):
            recorder.pr_review_facts(REPOSITORY, 42, head_sha=head, task_root=tmp_path, repo_root=Path.cwd())
    with pytest.raises(recorder.RecordError, match="head moved"):
        recorder.pr_review_facts(REPOSITORY, 42, head_sha=OTHER, task_root=tmp_path, repo_root=Path.cwd())


def test_recorder_reads_review_subjects_and_risk_from_the_review_task(monkeypatch, tmp_path):
    tasks, _, _ = setup_record(monkeypatch, tmp_path)
    seen = {}

    def facts(repository, number, **kwargs):
        seen.update(kwargs)
        return facts_for({"anthropic"}, subject_seats=kwargs["subject_seats"])

    monkeypatch.setattr(recorder, "pr_review_facts", facts)
    write_task(tasks, review_subject_seats=["codex"], review_risk="critical")
    with pytest.raises(recorder.RecordError, match="subject exclusion"):
        recorder.record("review-one", pr_number=42, task_root=tasks, lock_root=tmp_path / "locks")
    assert seen["subject_seats"] == ("codex",)
    write_task(tasks, review_subject_seats="codex")
    with pytest.raises(recorder.RecordError, match="review_subject_seats malformed"):
        recorder.record("review-one", pr_number=42, task_root=tasks, lock_root=tmp_path / "locks")


@pytest.mark.parametrize("reply", ["**VERDICT: APPROVE**", "## **VERDICT**: **APPROVE**"])
def test_markdown_approval_records_on_actual_boundary(monkeypatch, tmp_path, reply):
    tasks, _comments, calls = setup_record(monkeypatch, tmp_path)
    write_task(tasks, reply=reply)
    result = recorder.record("review-one", pr_number=42, task_root=tasks, lock_root=tmp_path / "locks")
    assert result["verdict"] == "APPROVED"
    assert calls == {"posts": 1, "statuses": 1}


@pytest.mark.parametrize("reply", ["```\nVERDICT: APPROVE\n```", "    VERDICT: APPROVE", "\tVERDICT: APPROVE"])
def test_code_example_refuses_publication(monkeypatch, tmp_path, reply):
    tasks, _comments, calls = setup_record(monkeypatch, tmp_path)
    write_task(tasks, reply=reply)
    with pytest.raises(recorder.RecordError, match="missing or ambiguous"):
        recorder.record("review-one", pr_number=42, task_root=tasks, lock_root=tmp_path / "locks")
    assert calls == {"posts": 0, "statuses": 0}


def test_fenced_change_request_does_not_contaminate_real_approval():
    assert recorder.normalize_verdict("```\nVERDICT: REQUEST_CHANGES\n```\nVERDICT: APPROVE") == "APPROVED"


def test_non_commonmark_indentation_refuses_before_publication(monkeypatch, tmp_path):
    tasks, _comments, calls = setup_record(monkeypatch, tmp_path)
    write_task(tasks, reply="\u00a0VERDICT: APPROVE\n\u200b/checkout/scripts/unit.py")
    with pytest.raises(recorder.RecordError, match="missing or ambiguous"):
        recorder.record("review-one", pr_number=42, task_root=tasks, lock_root=tmp_path / "locks")
    assert calls == {"posts": 0, "statuses": 0}


@pytest.mark.parametrize(
    "selector",
    [
        "auto",
        "AUTO",
        "Auto",
        " auto ",
        "default",
        "DEFAULT",
        "Default",
        " default ",
        "cursor:auto",
        "CURSOR:AUTO",
        "Cursor:Auto",
        " cursor:auto ",
        "cursor/auto",
        "CURSOR/AUTO",
        "Cursor/Auto",
        " cursor/auto ",
        "cursor:default",
        "CURSOR:DEFAULT",
        "Cursor:Default",
        " cursor:default ",
        "cursor/default",
        "CURSOR/DEFAULT",
        "Cursor/Default",
        " cursor/default ",
    ],
)
@pytest.mark.parametrize("resolved", [None, "Grok 4.7 256K High"])
def test_cursor_auto_task_attribution_preserves_selector(monkeypatch, tmp_path, selector, resolved):
    tasks = tmp_path / "tasks"
    write_task(
        tasks,
        task_id="author-auto",
        agent="cursor",
        model=selector,
        resolved_model_known=resolved is not None,
        resolved_model=resolved,
    )
    monkeypatch.setattr(
        recorder, "_pages", lambda args: [{"commit": {"message": "work\n\nX-Agent: cursor/author-auto"}}]
    )
    assert recorder.author_families(REPOSITORY, 42, tasks) == {"cursor"}


@pytest.mark.parametrize("harness", ["ox-alpha", "acp", "unmapped", "grok", "codex"])
@pytest.mark.parametrize("selector", ["auto", "DEFAULT"])
def test_non_cursor_auto_author_attribution_stays_unknown(monkeypatch, tmp_path, harness, selector):
    monkeypatch.setattr(
        recorder, "_pages", lambda args: [{"commit": {"message": f"work\n\nX-Agent: {harness}/{selector}"}}]
    )
    assert recorder.author_families(REPOSITORY, 42, tmp_path) == {"unknown"}


@pytest.mark.parametrize("harness", ["ox-alpha", "acp", "unmapped"])
def test_non_cursor_auto_incoming_writer_is_not_admitted(harness):
    with pytest.raises(recorder.BranchFactsError, match="incoming writer family unknown"):
        recorder.incoming_writer_family(harness, "auto")


@pytest.mark.parametrize("remaining", [54, 5])
@pytest.mark.parametrize("head", [SHA, OTHER])
def test_10016_quota_does_not_change_exact_head_verdict_qualification(monkeypatch, tmp_path, remaining, head):
    from scripts.fleet import credit_lane

    reads = []
    monkeypatch.setattr(
        credit_lane,
        "read_routing_budget",
        lambda **_: (
            reads.append(True)
            or {
                "agents": {"codex": {"remaining_pct": remaining}},
                "diagnostics": {"stale": False},
            }
        ),
    )
    facts = facts_for({"google"})
    route = recorder.structural_review_route(facts, risk="critical", claude_account=HOST_ACCOUNT)
    assert route.selected is not None and route.selected.capacity.remaining_pct is None
    tasks, _, _ = setup_record(monkeypatch, tmp_path, head=head)
    if head == SHA:
        result = recorder.record("review-one", pr_number=42, task_root=tasks, lock_root=tmp_path / "locks")
        assert result["head"] == SHA
    else:
        with pytest.raises(recorder.RecordError, match="head moved"):
            recorder.record("review-one", pr_number=42, task_root=tasks, lock_root=tmp_path / "locks")
    assert reads == []


@pytest.mark.parametrize("mode", ["cross_family", "red_team"])
@pytest.mark.parametrize(
    "verdict,state", [("APPROVED", "success"), ("BLOCKED", "failure"), ("CHANGES_REQUESTED", "failure")]
)
def test_status_description_labels_red_team_and_preserves_default(monkeypatch, tmp_path, mode, verdict, state):
    tasks, comments, _ = setup_record(monkeypatch, tmp_path)
    kwargs = {}
    if mode == "red_team":
        kwargs["red_team_prompt"] = red_team_task(tasks, tmp_path)
    write_task(
        tasks,
        reply=f"VERDICT: {verdict}",
        **(
            {
                "review_mode": mode,
                "prompt_sha256": hashlib.sha256(kwargs["red_team_prompt"].read_text().encode()).hexdigest(),
            }
            if kwargs
            else {}
        ),
    )
    statuses = []
    monkeypatch.setattr(recorder, "post_commit_status", lambda **fields: statuses.append(fields))
    recorder.record("review-one", pr_number=42, task_root=tasks, lock_root=tmp_path / "locks", **kwargs)
    assert statuses == [
        {
            "repository": REPOSITORY,
            "head_sha": SHA,
            "state": state,
            "context": "fleet/cross-family-review",
            "description": ("review_mode=red_team " if mode == "red_team" else "")
            + f"VERDICT: {verdict} openai review-one",
        }
    ]
    assert ("review_mode=red_team" in comments[0]["body"]) == (mode == "red_team")


def test_red_team_label_survives_status_description_truncation(monkeypatch, tmp_path):
    tasks, _, _ = setup_record(monkeypatch, tmp_path)
    task_id = "review-" + "x" * 150
    prompt = tmp_path / "prompt.md"
    prompt.write_text("Adversarial red-team review.")
    write_task(
        tasks, task_id=task_id, review_mode="red_team", prompt_sha256=hashlib.sha256(prompt.read_bytes()).hexdigest()
    )
    statuses = []
    monkeypatch.setattr(recorder, "post_commit_status", lambda **fields: statuses.append(fields))
    recorder.record(task_id, pr_number=42, task_root=tasks, lock_root=tmp_path / "locks", red_team_prompt=prompt)
    assert statuses[0]["description"].startswith("review_mode=red_team VERDICT: APPROVED")
    assert len(statuses[0]["description"]) == 140


@pytest.mark.parametrize("archived", [False, True])
@pytest.mark.parametrize(
    "agent,model,resolved,author_model",
    [
        ("codex", "gpt-6.1-sol", None, "gpt-6.1-sol"),
        ("claude", "gpt-6.1-sol[1m]", None, "gpt-6.1-sol"),
        ("cursor", "gpt-6.1-sol", "Grok 4.7 256K High", "gpt-6.1-sol"),
        ("cursor", "gpt-6.1-sol", "Grok 4.7 256K High", "grok-4.7"),
    ],
)
def test_red_team_recorded_and_resolved_model_refused_before_publication(
    monkeypatch, tmp_path, archived, agent, model, resolved, author_model
):
    from dataclasses import replace

    tasks, comments, calls = setup_record(monkeypatch, tmp_path, families={"openai"})
    records = tasks / "archive" if archived else tasks
    write_task(records, task_id="author-one", agent="codex", model=f"{author_model}[1m]")
    authors = recorder._attribute_commit_authors(
        {"sha": SHA, "commit": {"message": "change\n\nX-Agent: claude/claude-opus-5-5\nX-Agent: codex/author-one"}},
        repository=REPOSITORY,
        task_root=tasks,
        base_sha=lambda: OTHER,
    )
    assert authors[1].author_models == (f"{author_model}[1m]",)
    facts = replace(facts_for({author.family for author in authors}), commits=authors)
    monkeypatch.setattr(recorder, "pr_review_facts", lambda *_a, **_k: facts)
    prompt = red_team_task(
        tasks,
        tmp_path,
        agent=agent,
        model=model,
        resolved_model=resolved,
        resolved_model_known=True,
        resolved_model_source="cursor-stream-json",
    )
    with pytest.raises(recorder.RecordError, match="RED_TEAM_REFUSED: reviewer model equals a branch author model"):
        recorder.record(
            "review-one", pr_number=42, task_root=tasks, lock_root=tmp_path / "locks", red_team_prompt=prompt
        )
    assert comments == [] and calls == {"posts": 0, "statuses": 0}


@pytest.mark.parametrize("archived", [False, True])
@pytest.mark.parametrize("explicit", [None, "gpt-6-luna", "gpt-6.1-sol"])
def test_red_team_no_validated_author_requires_comparison_model(monkeypatch, tmp_path, archived, explicit):
    from dataclasses import replace

    tasks, comments, calls = setup_record(monkeypatch, tmp_path, families={"openai"})
    records = tasks / "archive" if archived else tasks
    write_task(records, task_id="author-one", model="unlisted-model")
    attribution = recorder._attribute_commit(
        {"sha": SHA, "commit": {"message": "change\n\nX-Agent: codex/author-one"}},
        repository=REPOSITORY,
        task_root=tasks,
        base_sha=lambda: OTHER,
    )
    facts = replace(facts_for({"openai"}), commits=(attribution,))
    monkeypatch.setattr(recorder, "pr_review_facts", lambda *_a, **_k: facts)
    prompt = red_team_task(tasks, tmp_path, review_author_model=explicit)
    kwargs = dict(pr_number=42, task_root=tasks, lock_root=tmp_path / "locks", red_team_prompt=prompt)
    # The author's task model is not in the catalog, so its family is unknown: a comparison model
    # passes the seat rule but the unresolved author is still refused (C-2902 F9).
    reason = {
        None: "RED_TEAM_REFUSED: no validated author model; supply --review-author-model",
        "gpt-6-luna": "AUTHOR_UNRESOLVED",
    }.get(explicit, "RED_TEAM_REFUSED: reviewer model equals a branch author model")
    with pytest.raises(recorder.RecordError, match=reason):
        recorder.record("review-one", **kwargs)
    assert comments == [] and calls == {"posts": 0, "statuses": 0}


@pytest.mark.parametrize("archived", [False, True])
@pytest.mark.parametrize("recorded", ["gpt-6-luna", "Auto"])
def test_author_task_seat_models_retain_recorded_and_resolved_identity(tmp_path, archived, recorded):
    tasks = tmp_path / "tasks"
    records = tasks / "archive" if archived else tasks
    write_task(
        records,
        task_id="author-one",
        agent="cursor",
        model=recorded,
        resolved_model="Grok 4.7 256K High",
        resolved_model_known=True,
    )
    attribution = recorder._attribute_commit(
        {"sha": SHA, "commit": {"message": "change\n\nX-Agent: cursor/author-one"}},
        repository=REPOSITORY,
        task_root=tasks,
        base_sha=lambda: OTHER,
    )
    expected = ("gpt-6-luna", "grok-4.7") if recorded == "gpt-6-luna" else ("grok-4.7",)
    assert attribution.author_models == expected
    for reviewer in expected:
        assert recorder.red_team_seat_refusal((reviewer,), author_models=attribution.author_models) == (
            "RED_TEAM_REFUSED: reviewer model equals a branch author model"
        )


@pytest.mark.parametrize("case", ["clean_update_merge", "conflict_resolution"])
@pytest.mark.parametrize("archived", [False, True])
@pytest.mark.parametrize("model", ["gpt-6.1-sol", "claude-opus-5-5", None, "unlisted-model"])
def test_merge_author_model_is_bound_to_named_task(real_commit_set, tmp_path, case, archived, model):
    git, entries, _, base = real_commit_set(case)
    git("commit", "--amend", "-m", "merge repair\n\nX-Agent: codex/merge-repair")
    head = git("rev-parse", "HEAD").stdout.strip()
    entry = {
        "sha": head,
        "commit": {"message": git("show", "-s", "--format=%B", head).stdout},
        "parents": entries[-1]["parents"],
    }
    tasks = tmp_path / "tasks"
    records = tasks / "archive" if archived else tasks
    write_task(records, task_id="merge-repair", agent="codex", model=model)
    attributed = recorder._attribute_commit(entry, repository=REPOSITORY, task_root=tasks, base_sha=lambda: base)
    assert attributed.source == ("task-record-archived" if archived else "task-record")
    assert attributed.task_id == "merge-repair"
    assert attributed.author_models == ((model,) if model in {"gpt-6.1-sol", "claude-opus-5-5"} else ())
    assert attributed.family == {"gpt-6.1-sol": "openai", "claude-opus-5-5": "anthropic"}.get(model, "unknown")


def test_unknown_history_excludes_all_possible_author_families():
    from dataclasses import replace

    from scripts.review.reviewer_resolver import resolve_reviewer

    facts = replace(
        facts_for({"unknown", "openai"}),
        commits=(
            recorder.CommitAttribution(OTHER, "unknown", "unknown_historical", authorship="unknown_historical"),
            recorder.CommitAttribution(SHA, "openai", "task-record", author_models=("gpt-6-luna",)),
        ),
    )
    assert {
        "anthropic",
        "openai",
        "google",
        "xai",
        "cursor",
        "moonshot",
        "poolside",
        "unknown",
    } <= facts.excluded_families
    assert facts.receipt()["excluded_families"] == sorted(facts.excluded_families)
    default = resolve_reviewer(facts.resolver_inputs(risk="critical", claude_account=HOST_ACCOUNT))
    assert default.selected is None
    assert default.trace and all(row.status not in {"eligible", "selected"} for row in default.trace)
    red_team = resolve_reviewer(
        facts.resolver_inputs(risk="critical", claude_account=HOST_ACCOUNT), review_mode="red_team"
    )
    assert red_team.selected is not None
    assert red_team.review_mode == "red_team"
    assert red_team.limitation
    assert red_team.selected.concrete_model != "gpt-6-luna"
